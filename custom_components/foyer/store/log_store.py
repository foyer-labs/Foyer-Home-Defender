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
import contextlib
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
from ..core.privacy import ERASED_COLUMNS, PersonRef, redact_detail

_LOGGER = logging.getLogger(__name__)

DB_FILENAME = "foyer-log.db"
EVENT_FOYER = "foyer_event"

# How many rows one query returns unless the caller says otherwise. The panel
# pages through; a filter that matches a year of zone activity must not try to
# cross the WebSocket in one message.
DEFAULT_LIMIT = 200
MAX_LIMIT = 1000

# How many rows one person's export may carry. The same order as the
# filtered export of §10.3, because it is the same export: a subject
# access request that came back cut short says so, as that one does.
PERSON_EXPORT_ROWS = 10000

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


async def async_delete_database(hass: HomeAssistant, path: str | None = None) -> bool:
    """Delete the log database, with the two files SQLite keeps beside it.

    Called when somebody removes the integration and the installation said to
    take the log with it (§16, part 2 decision 9). The write-ahead log and the
    shared-memory file are not optional extras: leaving a ``-wal`` behind is
    leaving the last rows of the history in the configuration directory, which
    is precisely what the person asking for this did not want.
    """
    target = path or hass.config.path(DB_FILENAME)

    def _delete() -> bool:
        import os

        gone = False
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(target + suffix)
            except FileNotFoundError:
                continue
            except OSError:
                _LOGGER.exception("Foyer could not delete %s", target + suffix)
                continue
            gone = True
        return gone

    return await hass.async_add_executor_job(_delete)


class LogStore:
    """Owns the database file, the write queue and the daily purge."""

    def __init__(self, hass: HomeAssistant, path: str | None = None) -> None:
        self.hass = hass
        self.path = path or hass.config.path(DB_FILENAME)
        self._queue: asyncio.Queue[LogRow] = asyncio.Queue()
        # Rows the worker has taken off the queue but not yet written. They
        # live here rather than in a local, so a reader that flushes while the
        # worker is between the queue and the lock still sees them.
        self._holding: list[LogRow] = []
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
            worker, self._worker = self._worker, None
            worker.cancel()
            # Waited for, not merely asked to stop. `cancel()` only schedules
            # the cancellation, so without this the writer is still running
            # when the entry finishes unloading — and it may still be holding
            # `_writing`, which the flush below is about to want. Every
            # configuration save reloads the entry, so "usually collected a
            # moment later" is a race that runs several times an evening.
            with contextlib.suppress(asyncio.CancelledError):
                await worker
        async with self._writing:
            await self._flush_locked()
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
            self._holding.append(await self._queue.get())
            async with self._writing:
                await self._flush_locked()

    async def _flush_locked(self) -> None:
        """Write everything outstanding. The caller holds ``_writing``."""
        rows = [*self._holding, *self._drain()]
        self._holding.clear()
        if rows:
            await self._async_insert(rows)

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
            await self._flush_locked()

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

    # --- personal data (SPEC 10.4) -------------------------------------------

    def _person_where(self, ref: PersonRef, *, wide: bool) -> tuple[str, list[Any]]:
        """Which rows are this person's.

        ``wide`` is the export (part 2 decision 7): a subject access request is
        about personal data, not about the rows whose ``user_id`` matches, so
        it also takes the rows naming a tag that is theirs and a contact linked
        to them — the rows where they are the subject rather than the actor.
        Narrow is the erasure, which acts on what they did and on the
        configuration rows about their account.

        A configuration row about a person carries their id in the JSON detail
        rather than in a column, because the columns say who *acted*. It is
        matched on the text this module itself wrote, which is why the fragment
        is spelled the way ``json.dumps`` spells it.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if ref.user_id:
            clauses.append("user_id = ?")
            params.append(ref.user_id)
        for name in ref.names:
            # Case-insensitively, and on the stored name: a row written before
            # this person was a Foyer user, or under a name they have since
            # changed, carries the name and another id or none at all (part 2
            # decision 12).
            clauses.append("user_name IS NOT NULL AND lower(user_name) = lower(?)")
            params.append(name)
        if ref.item_id:
            clauses.append("category = 'config' AND instr(detail, ?) > 0")
            params.append('"item_id": "' + ref.item_id + '"')
        if wide:
            if ref.device_ids:
                marks = ", ".join("?" for _ in ref.device_ids)
                clauses.append("device_id IN (" + marks + ")")
                params.extend(ref.device_ids)
            for contact_id in ref.contact_ids:
                clauses.append("instr(detail, ?) > 0")
                params.append('"contact_id": "' + contact_id + '"')
        if not clauses:
            # A filter nobody can satisfy rather than one that matches
            # everything: an erasure with nothing to match on must erase
            # nothing at all.
            return " WHERE 0", []
        # The whole group in one pair of brackets, because callers append
        # " AND ts < ?" to this and SQL binds AND tighter than OR: without
        # them the time condition would apply to the last clause alone, and
        # the daily sweep would pseudonymise rows written this morning.
        return " WHERE (" + " OR ".join("(" + c + ")" for c in clauses) + ")", params

    async def async_person_count(self, ref: PersonRef) -> dict[str, int]:
        """How many rows each key finds, before anybody presses the button.

        The panel shows this: whoever is about to erase somebody sees what is
        about to happen instead of trusting it (part 2 decision 12).
        """
        await self.async_flush()
        return await self.hass.async_add_executor_job(self._person_count, ref)

    def _person_count(self, ref: PersonRef) -> dict[str, int]:
        empty = {"by_id": 0, "by_name": 0, "total": 0, "wide": 0}
        with self._lock:
            connection = self._connection
            if connection is None:
                return empty

            def count(where: str, params: Sequence[Any]) -> int:
                return int(
                    connection.execute(
                        "SELECT COUNT(*) FROM events" + where, tuple(params)
                    ).fetchone()[0]
                )

            by_id = count(" WHERE user_id = ?", [ref.user_id]) if ref.user_id else 0
            by_name = (
                count(
                    " WHERE user_name IS NOT NULL AND lower(user_name) = lower(?)"
                    " AND (user_id IS NULL OR user_id != ?)",
                    [ref.names[0], ref.user_id or ""],
                )
                if ref.names
                else 0
            )
            narrow, narrow_params = self._person_where(ref, wide=False)
            wide, wide_params = self._person_where(ref, wide=True)
            return {
                "by_id": by_id,
                "by_name": by_name,
                "total": count(narrow, narrow_params),
                "wide": count(wide, wide_params),
            }

    async def async_person_rows(
        self, ref: PersonRef, *, limit: int = PERSON_EXPORT_ROWS
    ) -> dict[str, Any]:
        """Every row that is about this person, for a subject access request."""
        await self.async_flush()
        return await self.hass.async_add_executor_job(
            self._person_rows, ref, int(limit)
        )

    def _person_rows(self, ref: PersonRef, limit: int) -> dict[str, Any]:
        where, params = self._person_where(ref, wide=True)
        with self._lock:
            if self._connection is None:
                return {"rows": [], "total": 0}
            total = self._connection.execute(
                "SELECT COUNT(*) FROM events" + where, tuple(params)
            ).fetchone()[0]
            records = self._connection.execute(
                "SELECT * FROM events" + where + " ORDER BY ts DESC, id DESC LIMIT ?",
                (*params, limit),
            ).fetchall()
        return {
            "rows": [_stored_to_dict(record) for record in records],
            "total": int(total),
        }

    async def async_erase_person(
        self, ref: PersonRef, *, pseudonym: str | None = None
    ) -> int:
        """Take a person out of the log, leaving every event where it is.

        This is the distinction §10.4 exists for: ``user_name`` is denormalised
        so that deleting a *user* does not erase the history of what they did,
        which is right for audit and wrong for erasure. So the two operations
        are separate, and this is the other one.
        """
        await self.async_flush()
        return await self.hass.async_add_executor_job(
            self._erase_person, ref, pseudonym
        )

    def _erase_person(self, ref: PersonRef, pseudonym: str | None) -> int:
        where, params = self._person_where(ref, wide=False)
        if where == " WHERE 0":
            return 0
        columns = ", ".join(column + " = ?" for column in ERASED_COLUMNS)
        values: list[Any] = [None for _ in ERASED_COLUMNS]
        if pseudonym:
            values[0] = values[1] = pseudonym
        with self._lock:
            if self._connection is None:
                return 0
            # The detail is redacted row by row, because what has to come out
            # of it is a name inside a JSON document and no UPDATE can see
            # that. Everything else is one statement.
            records = self._connection.execute(
                "SELECT id, detail FROM events" + where + " AND detail IS NOT NULL",
                tuple(params),
            ).fetchall()
            redacted = []
            for record in records:
                try:
                    detail = json.loads(record["detail"])
                except ValueError:  # pragma: no cover - written by this module
                    continue
                clean = redact_detail(detail, ref.names)
                if clean != detail:
                    redacted.append((json.dumps(clean, default=str), record["id"]))
            if redacted:
                self._connection.executemany(
                    "UPDATE events SET detail = ? WHERE id = ?", redacted
                )
            cursor = self._connection.execute(
                "UPDATE events SET " + columns + where, (*values, *params)
            )
            self._connection.commit()
        return int(cursor.rowcount)

    async def async_pseudonymise(
        self, people: Sequence[PersonRef], before: datetime
    ) -> int:
        """The daily sweep: rows older than the cutoff keep an identifier.

        Beside the purge and never on the write path, for the reason this
        module exists to respect — a log operation must not delay the alarm by
        a millisecond. It is idempotent by construction: a row already carrying
        a pseudonym no longer matches the id or the name it was written with.
        """
        return await self.hass.async_add_executor_job(
            self._pseudonymise, people, _epoch_ms(before)
        )

    def _pseudonymise(self, people: Sequence[PersonRef], before: int) -> int:
        changed = 0
        with self._lock:
            if self._connection is None:
                return 0
            for ref in people:
                if not ref.pseudonym or ref.empty:
                    continue
                where, params = self._person_where(ref, wide=False)
                if where == " WHERE 0":
                    continue
                cursor = self._connection.execute(
                    "UPDATE events SET user_id = ?, user_name = ?"
                    + where
                    + " AND ts < ?",
                    (ref.pseudonym, ref.pseudonym, *params, before),
                )
                changed += cursor.rowcount
            self._connection.commit()
        return changed

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
