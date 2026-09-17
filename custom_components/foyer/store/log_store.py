"""The event log: a SQLite database of Foyer's own (SPEC §10.1-10.3).

Separate from Home Assistant's recorder on purpose: the recorder's default
ten-day purge would quietly destroy the thirty-day requirement, and an alarm
whose history disappears after a fortnight cannot answer the one question it
exists to answer.

Three rules this module is built around.

**A log failure never delays the alarm path.** Writing is a hand-off: the
event loop puts rows on a queue and returns, and a worker task writes them in
an executor thread. If the disk is full, the database is locked or the file is
gone, the exception is logged and the alarm keeps running. A house that stops
being protected because it could not write a row is worse than one that cannot
remember.

**Nothing here decides anything.** What category a row belongs to, how severe
it is and whether a request was refused are decided in ``core/journal.py``,
which is pure. This module stores what it is given.

**The stdlib, not a dependency.** ``sqlite3`` in an executor thread is what
Home Assistant's own recorder does, and it is what ``aiosqlite`` does
internally. An alarm integration that fails to load because a wheel could not
be fetched at first setup is a failure mode worth not having (SPEC §3.2 named
aiosqlite; this is the deliberate substitution).
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta
import json
import logging
import sqlite3
import threading
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from ..core.journal import LogRow
from ..core.models import LogCategory, LogSettings

_LOGGER = logging.getLogger(__name__)

DB_FILENAME = "foyer-log.db"
EVENT_FOYER = "foyer_event"

# How many rows one query returns unless the caller says otherwise. The panel
# pages through; a filter that matches a year of zone activity must not try to
# cross the WebSocket in one message.
DEFAULT_LIMIT = 200
MAX_LIMIT = 1000

# The schema of SPEC §10.1, plus ``incident_id``: §5.6 requires the incident
# id on every related row, and a row buried in the JSON detail cannot be
# filtered on. ``ts`` is epoch milliseconds in UTC, as the spec says.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id           INTEGER PRIMARY KEY,
  ts           INTEGER NOT NULL,
  category     TEXT NOT NULL,
  event_type   TEXT NOT NULL,
  severity     TEXT NOT NULL,
  area_id      TEXT, zone_id TEXT, scenario_id TEXT,
  incident_id  TEXT,
  user_id      TEXT, user_name TEXT,
  channel      TEXT, device_id TEXT,
  outcome      TEXT,
  detail       TEXT
);
CREATE INDEX IF NOT EXISTS idx_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_cat_ts ON events(category, ts);
CREATE INDEX IF NOT EXISTS idx_area_ts ON events(area_id, ts);
CREATE INDEX IF NOT EXISTS idx_user_ts ON events(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_incident ON events(incident_id);
"""

_COLUMNS = (
    "ts",
    "category",
    "event_type",
    "severity",
    "area_id",
    "zone_id",
    "scenario_id",
    "incident_id",
    "user_id",
    "user_name",
    "channel",
    "device_id",
    "outcome",
    "detail",
)

_INSERT = (
    f"INSERT INTO events ({', '.join(_COLUMNS)}) "
    f"VALUES ({', '.join('?' for _ in _COLUMNS)})"
)


def _epoch_ms(value: datetime) -> int:
    return int(dt_util.as_utc(value).timestamp() * 1000)


def _row_values(row: LogRow) -> tuple[Any, ...]:
    return (
        _epoch_ms(row.ts),
        str(row.category),
        row.event_type,
        str(row.severity),
        row.area_id,
        row.zone_id,
        row.scenario_id,
        row.incident_id,
        row.user_id,
        row.user_name,
        row.channel,
        row.device_id,
        row.outcome,
        json.dumps(dict(row.detail), default=str) if row.detail else None,
    )


def row_to_dict(row: LogRow) -> dict[str, Any]:
    """One row as the panel, the ``foyer_event`` bus event and CSV see it."""
    return {
        "ts": dt_util.as_utc(row.ts).isoformat(),
        "category": str(row.category),
        "event_type": row.event_type,
        "severity": str(row.severity),
        "area_id": row.area_id,
        "zone_id": row.zone_id,
        "scenario_id": row.scenario_id,
        "incident_id": row.incident_id,
        "user_id": row.user_id,
        "user_name": row.user_name,
        "channel": row.channel,
        "device_id": row.device_id,
        "outcome": row.outcome,
        "detail": dict(row.detail),
    }


def _stored_to_dict(record: sqlite3.Row) -> dict[str, Any]:
    detail = record["detail"]
    return {
        "id": record["id"],
        "ts": dt_util.utc_from_timestamp(record["ts"] / 1000).isoformat(),
        "category": record["category"],
        "event_type": record["event_type"],
        "severity": record["severity"],
        "area_id": record["area_id"],
        "zone_id": record["zone_id"],
        "scenario_id": record["scenario_id"],
        "incident_id": record["incident_id"],
        "user_id": record["user_id"],
        "user_name": record["user_name"],
        "channel": record["channel"],
        "device_id": record["device_id"],
        "outcome": record["outcome"],
        "detail": json.loads(detail) if detail else {},
    }


class LogStore:
    """Owns the database file, the write queue and the daily purge."""

    def __init__(self, hass: HomeAssistant, path: str | None = None) -> None:
        self.hass = hass
        self.path = path or hass.config.path(DB_FILENAME)
        self._queue: asyncio.Queue[LogRow] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None
        self._connection: sqlite3.Connection | None = None
        # sqlite3 connections are shared across Home Assistant's executor
        # threads, so every use of one is serialised here.
        self._lock = threading.Lock()
        # Held while a batch is being written, so a reader that flushes first
        # waits for a write already in flight instead of racing past it.
        self._writing = asyncio.Lock()
        self._failed = False

    # --- lifecycle -----------------------------------------------------------

    async def async_setup(self) -> None:
        await self.hass.async_add_executor_job(self._open)
        self._worker = self.hass.async_create_background_task(
            self._run(), "foyer log writer"
        )

    async def async_close(self) -> None:
        """Stop writing, then flush what is queued: a row already decided on
        belongs in the log even if Home Assistant is going down."""
        if self._worker is not None:
            self._worker.cancel()
            self._worker = None
        async with self._writing:
            pending = self._drain()
            if pending:
                await self._async_insert(pending)
        await self.hass.async_add_executor_job(self._close)

    def _open(self) -> None:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        # WAL keeps a reader (the panel) from blocking the writer (an alarm).
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.executescript(_SCHEMA)
        connection.commit()
        self._connection = connection

    def _close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    # --- writing -------------------------------------------------------------

    @callback
    def async_write(self, rows: Iterable[LogRow], settings: LogSettings) -> None:
        """Queue rows and fire ``foyer_event`` for each (§10.3).

        Returns immediately: this is called from the alarm path. A category
        the user switched off is dropped here, before the queue, so a
        disabled ``zone_disarmed`` costs nothing at all.
        """
        for row in rows:
            if not settings.is_enabled(str(row.category)):
                continue
            data = row_to_dict(row)
            # Every write also reaches the bus, so external collectors and
            # user automations need one trigger and no database (§10.3).
            self.hass.bus.async_fire(EVENT_FOYER, data)
            self._queue.put_nowait(row)

    async def _run(self) -> None:
        while True:
            first = await self._queue.get()
            async with self._writing:
                await self._async_insert([first, *self._drain()])

    def _drain(self) -> list[LogRow]:
        rows: list[LogRow] = []
        while True:
            try:
                rows.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                return rows

    async def _async_insert(self, rows: Sequence[LogRow]) -> None:
        try:
            await self.hass.async_add_executor_job(self._insert, rows)
        except Exception:
            # Never raised at the caller: the alarm path put these rows here
            # and has long since moved on. Say it loudly and keep running.
            if not self._failed:
                _LOGGER.exception("Foyer could not write to its event log")
                self._failed = True

    def _insert(self, rows: Sequence[LogRow]) -> None:
        with self._lock:
            if self._connection is None:
                return
            self._connection.executemany(_INSERT, [_row_values(r) for r in rows])
            self._connection.commit()
        self._failed = False

    # --- reading -------------------------------------------------------------

    async def async_flush(self) -> None:
        """Write what is still queued, then return.

        Reading waits for the writer; the alarm path never does. Without this
        the panel could ask for the log in the same breath as the event that
        produced a row and be shown yesterday's answer.
        """
        async with self._writing:
            pending = self._drain()
            if pending:
                await self._async_insert(pending)

    async def async_query(self, **filters: Any) -> dict[str, Any]:
        return await self.hass.async_add_executor_job(lambda: self._query(**filters))

    def _query(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        categories: Sequence[str] | None = None,
        severity: str | None = None,
        area_id: str | None = None,
        zone_id: str | None = None,
        user_id: str | None = None,
        incident_id: str | None = None,
        outcome: str | None = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> dict[str, Any]:
        where, params = self._where(
            start=start,
            end=end,
            categories=categories,
            severity=severity,
            area_id=area_id,
            zone_id=zone_id,
            user_id=user_id,
            incident_id=incident_id,
            outcome=outcome,
        )
        limit = max(1, min(int(limit), MAX_LIMIT))
        with self._lock:
            if self._connection is None:
                return {"rows": [], "total": 0}
            total = self._connection.execute(
                f"SELECT COUNT(*) FROM events{where}",
                params,
            ).fetchone()[0]
            records = self._connection.execute(
                # Newest first, and by id within the same millisecond, so the
                # order a decision produced is the order it is read back in.
                f"SELECT * FROM events{where} ORDER BY ts DESC, id DESC "
                "LIMIT ? OFFSET ?",
                (*params, limit, max(0, int(offset))),
            ).fetchall()
        return {
            "rows": [_stored_to_dict(record) for record in records],
            "total": int(total),
        }

    def _where(self, **filters: Any) -> tuple[str, list[Any]]:
        """The WHERE clause. Every value is bound, never interpolated."""
        clauses: list[str] = []
        params: list[Any] = []
        if (start := filters.get("start")) is not None:
            clauses.append("ts >= ?")
            params.append(_epoch_ms(start))
        if (end := filters.get("end")) is not None:
            clauses.append("ts <= ?")
            params.append(_epoch_ms(end))
        if categories := filters.get("categories"):
            known = [c for c in categories if c in {x.value for x in LogCategory}]
            if not known:
                # A filter nobody can satisfy, rather than one that matches
                # everything: an empty result is the honest answer.
                return " WHERE 0", []
            clauses.append(f"category IN ({', '.join('?' for _ in known)})")
            params.extend(known)
        for column in ("severity", "area_id", "zone_id", "user_id", "outcome"):
            if (value := filters.get(column)) is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        if (incident := filters.get("incident_id")) is not None:
            clauses.append("incident_id = ?")
            params.append(incident)
        return (f" WHERE {' AND '.join(clauses)}" if clauses else ""), params

    async def async_last(self) -> dict[str, Any] | None:
        """The newest row, for ``sensor.foyer_last_event``."""
        result = await self.async_query(limit=1)
        rows = result["rows"]
        return rows[0] if rows else None

    # --- retention -----------------------------------------------------------

    async def async_purge(self, settings: LogSettings, now: datetime) -> int:
        """Delete what is older than each category's retention (§10.3)."""
        cutoffs = {
            category.value: _epoch_ms(
                now - timedelta(days=settings.retention(category.value))
            )
            for category in LogCategory
        }
        return await self.hass.async_add_executor_job(self._purge, cutoffs)

    def _purge(self, cutoffs: Mapping[str, int]) -> int:
        with self._lock:
            if self._connection is None:
                return 0
            removed = 0
            for category, cutoff in cutoffs.items():
                cursor = self._connection.execute(
                    "DELETE FROM events WHERE category = ? AND ts < ?",
                    (category, cutoff),
                )
                removed += cursor.rowcount
            self._connection.commit()
        return removed

    async def async_clear(self) -> int:
        """Empty the log. An edit_config operation, and itself logged (§10.3)."""
        return await self.hass.async_add_executor_job(self._clear)

    def _clear(self) -> int:
        with self._lock:
            if self._connection is None:
                return 0
            removed = self._connection.execute("DELETE FROM events").rowcount
            self._connection.commit()
            self._connection.execute("VACUUM")
        return removed

    async def async_count(self) -> int:
        result = await self.async_query(limit=1)
        return result["total"]


# --- export (§10.3) ----------------------------------------------------------

# The columns of the CSV, in the order the log is read in. ``detail`` is kept
# as JSON in its own column rather than spread out: an export is for reading
# elsewhere, and a column set that changes with the rows is not a table.
CSV_COLUMNS = (
    "ts",
    "category",
    "event_type",
    "severity",
    "outcome",
    "area_id",
    "zone_id",
    "scenario_id",
    "incident_id",
    "user_name",
    "channel",
    "device_id",
    "detail",
)


def export_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    """Exactly the rows the current filters show, as CSV (§10.3)."""
    import csv
    import io

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        writer.writerow(
            [
                json.dumps(row.get("detail") or {}, default=str, sort_keys=True)
                if column == "detail"
                else (row.get(column) if row.get(column) is not None else "")
                for column in CSV_COLUMNS
            ]
        )
    return out.getvalue()


def export_json(rows: Sequence[Mapping[str, Any]]) -> str:
    return json.dumps(list(rows), indent=2, default=str)
