"""The configuration's credentials, through Home Assistant (§7.2, §12.3,
decisions 128-130).

Reading the configuration needs `edit_config` and no code, so it says whether
the acknowledgement webhook and the watchdog URL are set and never what they
are. The webhook's address is shown once, in the answer that generates it;
the watchdog URL is written and never read back, and a save that does not
carry one keeps it. And the `config` rows written before beta.13, which
printed the webhook's id, lose it when the log opens.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import time

from homeassistant.components import webhook
import pytest
from yarl import URL

from custom_components.foyer.api.backup import backup_document, restore
from custom_components.foyer.const import DOMAIN
from custom_components.foyer.core.dump import anonymised
from custom_components.foyer.runtime.system import _without_url
from custom_components.foyer.store import log_store

from .conftest import ZONE
from .test_part2 import _ws
from .test_phase2 import CODE, _make_user

PING = "https://hc-ping.example/9f8c-secret-token"


def _system(hass):
    return hass.data[DOMAIN]


async def _config(client) -> dict:
    return (await _ws(client, {"type": "foyer/config"}))["config"]


async def _save_watchdog(hass, client, **watchdog) -> dict:
    """Page 14's save: the block as foyer/config gave it — `url_set` and all —
    with what somebody changed on top."""
    health = (await _config(client))["health"]
    health["watchdog"] = {**health["watchdog"], **watchdog}
    result = await _ws(client, {"type": "foyer/config/health", "health": health})
    await hass.async_block_till_done()
    return result


async def _last_health_row(hass) -> dict:
    system = _system(hass)
    await system.log.async_flush()
    rows = (await system.log.async_query(categories=["config"], limit=200))["rows"]
    return max(
        (r for r in rows if r["detail"].get("kind") == "health"),
        key=lambda r: r["id"],
    )


@pytest.fixture
async def secrets(hass, hass_ws_client, loaded):
    """The webhook switched on and the watchdog pinging PING."""
    client = await hass_ws_client(hass)
    await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    assert (await _save_watchdog(hass, client, enabled=True, url=PING))["success"]
    system = _system(hass)
    assert system.config.health.watchdog.url == PING
    webhook_id = system.config.settings.ack_webhook_id
    assert webhook_id
    return client, webhook_id


# --- no configuration read returns either (decision 128) ---------------------------


async def test_the_configuration_says_whether_each_is_set_never_what(hass, secrets):
    client, webhook_id = secrets
    config = await _config(client)
    assert config["settings"]["ack_webhook_enabled"] is True
    assert "ack_webhook_id" not in config["settings"]
    assert config["health"]["watchdog"]["url_set"] is True
    assert "url" not in config["health"]["watchdog"]

    system = _system(hass)
    await system.log.async_flush()
    for name, document in (
        ("foyer/config", config),
        ("foyer/health", await _ws(client, {"type": "foyer/health"})),
        ("foyer/status", await _ws(client, {"type": "foyer/status"})),
        ("foyer/log/query", await _ws(client, {"type": "foyer/log/query"})),
        ("backup", backup_document(system.config)),
        ("diagnostics", anonymised(system.config, system.state)),
    ):
        text = json.dumps(document, default=str)
        assert webhook_id not in text, name
        assert PING not in text, name


async def test_nothing_is_set_on_a_fresh_installation(hass, hass_ws_client, loaded):
    config = await _config(await hass_ws_client(hass))
    assert config["settings"]["ack_webhook_enabled"] is False
    assert config["health"]["watchdog"]["url_set"] is False


async def test_a_backup_keeps_the_shape_it_always_had(hass, secrets):
    """The credentials present and empty, as every backup before this one
    had them, and no flag describing this installation; a restore still
    keeps the installation's own."""
    _client, webhook_id = secrets
    system = _system(hass)
    document = backup_document(system.config)
    settings = document["config"]["settings"]
    watchdog = document["config"]["health"]["watchdog"]
    assert settings["ack_webhook_id"] is None
    assert "ack_webhook_enabled" not in settings
    assert watchdog["url"] == ""
    assert "url_set" not in watchdog

    result = restore(system, document)
    assert result.config is not None, result.problems
    assert result.config.settings.ack_webhook_id == webhook_id
    assert result.config.health.watchdog.url == PING
    assert result.config.health.watchdog.enabled is True


# --- the webhook's address, shown once (decision 129) ------------------------------


async def test_the_address_is_shown_in_the_answer_that_generates_it(
    hass, hass_ws_client, loaded
):
    client = await hass_ws_client(hass)
    first = await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    held = _system(hass).config.settings.ack_webhook_id
    assert first["success"]
    assert first["path"] == f"/api/webhook/{held}"
    # No external address known: the path alone, for the household to put
    # its own in front of.
    assert first["url"] is None

    # Switching it on again is how a lost address is replaced: a new one,
    # and the old one stops answering at once.
    second = await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    replaced = _system(hass).config.settings.ack_webhook_id
    assert replaced != held
    assert second["path"] == f"/api/webhook/{replaced}"
    assert held not in hass.data[webhook.DOMAIN]
    assert replaced in hass.data[webhook.DOMAIN]

    # The log says it was generated, never what it is.
    await _system(hass).log.async_flush()
    rows = (await _ws(client, {"type": "foyer/log/query", "categories": ["config"]}))[
        "rows"
    ]
    generated = [r for r in rows if r["event_type"] == "config_new_webhook"]
    assert len(generated) == 2
    assert all(
        r["detail"]["changes"]["settings"]["ack_webhook_id"] == [] for r in generated
    )
    assert held not in json.dumps(rows) and replaced not in json.dumps(rows)


async def test_switching_it_off_answers_with_no_address(hass, hass_ws_client, loaded):
    client = await hass_ws_client(hass)
    await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    off = await _ws(client, {"type": "foyer/ack_webhook", "enabled": False})
    await hass.async_block_till_done()
    assert off["success"]
    assert "path" not in off and "url" not in off
    await _system(hass).log.async_flush()
    rows = (await _ws(client, {"type": "foyer/log/query", "categories": ["config"]}))[
        "rows"
    ]
    assert any(r["event_type"] == "config_forget_webhook" for r in rows)


async def test_with_an_external_address_the_answer_is_the_whole_url(
    hass, hass_ws_client, loaded
):
    """Something that can be pasted into the voice provider as it is."""
    await hass.config.async_update(external_url="https://foyer.example.org")
    client = await hass_ws_client(hass)
    answer = await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    held = _system(hass).config.settings.ack_webhook_id
    assert answer["url"] == f"https://foyer.example.org/api/webhook/{held}"
    assert answer["path"] == f"/api/webhook/{held}"


async def test_an_internal_address_is_never_offered(hass, hass_ws_client, loaded):
    """A voice provider calls from the internet: an address on the
    household's own network would acknowledge nothing on the night."""
    await hass.config.async_update(internal_url="http://192.168.1.10:8123")
    client = await hass_ws_client(hass)
    answer = await _ws(client, {"type": "foyer/ack_webhook", "enabled": True})
    await hass.async_block_till_done()
    assert answer["url"] is None
    assert answer["path"].startswith("/api/webhook/")


async def test_a_refused_request_shows_no_address(hass, hass_ws_client, loaded):
    client = await hass_ws_client(hass)
    await _make_user(
        hass, client, new_code=CODE, permissions=["arm", "disarm", "edit_config"]
    )
    # Somebody holds a code now, so switching the webhook on asks for it
    # (§8.2): refused without it and with a wrong one.
    for code in ({}, {"code": "000000"}):
        answer = await _ws(
            client, {"type": "foyer/ack_webhook", "enabled": True, **code}
        )
        assert answer["success"] is False
        assert "path" not in answer and "url" not in answer
        assert "/api/webhook/" not in json.dumps(answer)
    assert _system(hass).config.settings.ack_webhook_id is None
    answer = await _ws(
        client, {"type": "foyer/ack_webhook", "enabled": True, "code": CODE}
    )
    await hass.async_block_till_done()
    assert answer["success"] and answer["path"].startswith("/api/webhook/")


# --- the watchdog URL, written and never read back (decision 130) ------------------


async def test_a_save_that_leaves_the_url_out_keeps_it(hass, secrets):
    client, _webhook_id = secrets
    # What page 14 sends when nobody typed a URL: none, and the flag it was
    # given, which is not a setting and is ignored.
    assert (await _save_watchdog(hass, client, interval=600))["success"]
    watchdog = _system(hass).config.health.watchdog
    assert watchdog.url == PING and watchdog.enabled and watchdog.interval == 600
    # The row says what changed, and the URL did not.
    changes = (await _last_health_row(hass))["detail"]["changes"]["health"]
    assert "watchdog.url" not in changes


@pytest.mark.parametrize("sent", ["", "   ", None])
async def test_a_save_that_sends_it_empty_keeps_it(hass, secrets, sent):
    client, _webhook_id = secrets
    assert (await _save_watchdog(hass, client, url=sent, timeout=20))["success"]
    watchdog = _system(hass).config.health.watchdog
    # Null in particular, which read as it came became the string "None":
    # a URL that is set and pings nothing.
    assert watchdog.url == PING and watchdog.enabled


async def test_switching_the_watchdog_off_keeps_its_url(hass, secrets):
    client, _webhook_id = secrets
    assert (await _save_watchdog(hass, client, enabled=False))["success"]
    watchdog = _system(hass).config.health.watchdog
    assert watchdog.enabled is False and watchdog.url == PING
    assert (await _config(client))["health"]["watchdog"]["url_set"] is True
    # Back on without typing it again.
    assert (await _save_watchdog(hass, client, enabled=True))["success"]
    assert _system(hass).config.health.watchdog.enabled is True


async def test_a_new_url_replaces_the_stored_one(hass, secrets):
    client, _webhook_id = secrets
    other = "https://uptime.example/api/push/another-token"
    assert (await _save_watchdog(hass, client, url=other))["success"]
    assert _system(hass).config.health.watchdog.url == other
    row = await _last_health_row(hass)
    assert row["detail"]["changes"]["health"]["watchdog.url"] == []
    assert other not in json.dumps(row)


def test_the_url_is_taken_out_of_an_error_in_every_form_it_comes_back_in():
    """aiohttp writes the URL back the way yarl normalised it — a lower-case
    host, the default port dropped — and some messages carry only its path,
    which is where the token is."""
    typed = "https://HC-Ping.Example:443/9f8c-secret?check=1"
    normalised = str(URL(typed))
    assert normalised != typed
    for message in (
        f"cannot connect to {typed}",
        f"cannot connect to {normalised}",
        f"400, message='Bad Request', url='{normalised}'",
        "GET /9f8c-secret?check=1 refused",
    ):
        cleaned = _without_url(message, typed)
        assert "9f8c-secret" not in cleaned, (message, cleaned)
        assert "<url>" in cleaned
    # A URL with no path takes nothing else out of the message.
    assert _without_url("Timeout at /", "https://hc-ping.example") == "Timeout at /"


async def test_a_ping_error_in_the_normalised_form_is_stored_without_it(
    hass, loaded, hass_ws_client, aioclient_mock
):
    typed = "https://HC-Ping.Example:443/9f8c-secret"
    client = await hass_ws_client(hass)
    aioclient_mock.get(typed, exc=OSError(f"cannot connect to {URL(typed)}"))
    assert (await _save_watchdog(hass, client, enabled=True, url=typed, failures=1))[
        "success"
    ]
    await _system(hass)._async_watchdog()
    await hass.async_block_till_done()
    error = _system(hass).state.health.watchdog.last_error
    assert error and "9f8c-secret" not in error


# --- the rows written before beta.13 ------------------------------------------------

LEAKED = "0123456789abcdef0123456789abcdef"

# What config_diff wrote up to beta.12, and what it has written since.
OLD_ROWS = (
    {
        "kind": "settings",
        "changes": {
            "settings": {"ack_webhook_id": [None, LEAKED], "siren_duration": [180, 240]}
        },
    },
    {"kind": "settings", "changes": {"settings": {"ack_webhook_id": [LEAKED, None]}}},
    {"kind": "settings", "changes": {"settings": {"ack_webhook_id": []}}},
    {"kind": "zone", "changes": {"zones": {"added": ["Hall"]}}},
)


def _seed(path: str) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(log_store._SCHEMA)
    now = int(time.time() * 1000)
    connection.executemany(
        "INSERT INTO events (ts, category, event_type, severity, outcome, detail) "
        "VALUES (?, 'config', 'config_save', 'info', 'ok', ?)",
        [(now, json.dumps(detail)) for detail in OLD_ROWS],
    )
    connection.commit()
    connection.close()


async def test_rows_that_printed_the_webhook_id_lose_it_when_the_log_opens(
    hass, hass_ws_client, entry
):
    """Read with view_log — less than it takes to read the configuration the
    id is no longer returned from — until retention purged them."""
    path = hass.config.path(log_store.DB_FILENAME)
    await hass.async_add_executor_job(_seed, path)
    hass.states.async_set(ZONE, "off", {"friendly_name": "Front door"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    rows = (await _ws(client, {"type": "foyer/log/query", "categories": ["config"]}))[
        "rows"
    ]
    assert LEAKED not in json.dumps(rows)
    settings = [
        r["detail"]["changes"]["settings"]
        for r in rows
        if r["detail"]["kind"] == "settings"
    ]
    # Every row still says the webhook changed, in the shape written since;
    # nothing else in them moved.
    assert [s["ack_webhook_id"] for s in settings] == [[], [], []]
    assert any(s.get("siren_duration") == [180, 240] for s in settings)
    assert any(r["detail"]["kind"] == "zone" for r in rows)

    # Nor is it left in the file, or in the write-ahead log beside it.
    def _on_disk() -> bytes:
        return b"".join(
            Path(path + suffix).read_bytes()
            for suffix in ("", "-wal")
            if Path(path + suffix).exists()
        )

    assert LEAKED.encode() not in await hass.async_add_executor_job(_on_disk)


def test_the_scrub_is_idempotent():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(log_store._SCHEMA)
    connection.executemany(
        "INSERT INTO events (ts, category, event_type, severity, detail) "
        "VALUES (0, 'config', 'config_save', 'info', ?)",
        [(json.dumps(detail),) for detail in OLD_ROWS],
    )
    assert log_store._scrub_webhook_ids(connection) == 2
    assert log_store._scrub_webhook_ids(connection) == 0
    details = [
        json.loads(r["detail"]) for r in connection.execute("SELECT detail FROM events")
    ]
    assert details[0]["changes"]["settings"] == {
        "ack_webhook_id": [],
        "siren_duration": [180, 240],
    }
    assert details[3] == OLD_ROWS[3]
