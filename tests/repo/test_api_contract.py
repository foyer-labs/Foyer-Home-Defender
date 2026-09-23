"""The API documents say what the code answers (SPEC §9.2.2, decision 121).

``docs/api/openapi.yaml`` describes the device endpoint and
``docs/api/asyncapi.yaml`` the MQTT contract, both at contract version ``v1``.
A document nobody checks is false within two releases, so this compares both
with the code: every action, field, section, scope, reason and result word.

Pure, like the rest of the suite that runs without Home Assistant: the
modules that hold the contract's names import ``homeassistant``, so they are
read with ``ast`` rather than imported. Only ``core.models`` is imported.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import yaml

from custom_components.foyer.core.models import (
    ACT_SCOPES,
    READ_SCOPES,
    MqttDetail,
    Reason,
)

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "docs/api/openapi.yaml"
ASYNCAPI = ROOT / "docs/api/asyncapi.yaml"
PACKAGED = ROOT / "custom_components/foyer/api/openapi.yaml"
DEVICE_API = ROOT / "custom_components/foyer/api/device_api.py"
ENDPOINT = ROOT / "custom_components/foyer/api/endpoint.py"
MQTT = ROOT / "custom_components/foyer/runtime/mqtt.py"
SYSTEM = ROOT / "custom_components/foyer/runtime/system.py"

# Reasons a device is never answered with, and why. Anything else in the
# enum must be in the document, so a reason added to the code and forgotten
# here fails this test.
NOT_SENT = {
    # A wrong token is answered 401 with no body; the reason is the log's.
    "bad_token",
    # Raised by a timer after the arming was answered, never in an answer.
    "arm_hold_expired",
    # Automatic rules and their countdowns: no device action reaches them.
    "nothing_to_cancel",
    "unknown_rule",
    "unknown_suspension",
}
# Reasons only the HTTP endpoint gives: scopes, the unlock, the clear-text
# confirmation, and the zone that exclude/include names. MQTT has none of
# those.
ENDPOINT_ONLY = {
    "scope_not_granted",
    "unlock_required",
    "plain_http_not_confirmed",
    "unknown_zone",
}
# Added by the endpoint around every section, not by the section's builder.
ENVELOPE = {"success", "reason"}


# --- reading the documents ------------------------------------------------------


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _deref(doc: dict[str, Any], node: Any) -> Any:
    """Follow ``$ref`` pointers inside the same document."""
    while isinstance(node, dict) and "$ref" in node:
        target: Any = doc
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        node = target
    return node


def _schema(doc: dict[str, Any], name: str) -> dict[str, Any]:
    return doc["components"]["schemas"][name]


def _properties(doc: dict[str, Any], node: Any, seen: set[int] | None = None) -> set:
    """Every property name in a schema, however deep, through refs and
    compositions: what a device may meet anywhere in that answer."""
    seen = set() if seen is None else seen
    node = _deref(doc, node)
    if not isinstance(node, dict) or id(node) in seen:
        return set()
    seen.add(id(node))
    names: set[str] = set()
    for name, child in (node.get("properties") or {}).items():
        names.add(name)
        names |= _properties(doc, child, seen)
    for key in ("items", "additionalProperties"):
        if isinstance(node.get(key), dict):
            names |= _properties(doc, node[key], seen)
    for key in ("oneOf", "anyOf", "allOf"):
        for child in node.get(key, ()):
            names |= _properties(doc, child, seen)
    return names


def _enum(doc: dict[str, Any], name: str) -> set[str]:
    return set(_schema(doc, name)["enum"])


# --- reading the code -----------------------------------------------------------


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _assigned(tree: ast.Module, name: str) -> ast.expr:
    for node in tree.body:
        if isinstance(node, ast.AnnAssign | ast.Assign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                assert node.value is not None
                return node.value
    raise AssertionError(f"{name} is not assigned at module level")


def _function(tree: ast.Module, name: str) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and (
            node.name == name
        ):
            return node
    raise AssertionError(f"{name} is not defined")


def _keys(tree: ast.Module, *functions: str) -> set[str]:
    """The string keys a builder writes: dict literals and ``x["k"] = …``."""
    keys: set[str] = set()
    for name in functions:
        for node in ast.walk(_function(tree, name)):
            if isinstance(node, ast.Dict):
                keys |= {
                    k.value
                    for k in node.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)
                }
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript) and isinstance(
                        target.slice, ast.Constant
                    ):
                        keys.add(target.slice.value)
    return keys


def _gets(tree: ast.Module, *functions: str) -> set[str]:
    """The fields a handler reads from a request: ``data.get("k")``."""
    fields: set[str] = set()
    for name in functions:
        for node in ast.walk(_function(tree, name)):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "data"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                fields.add(node.args[0].value)
    return fields


def _reasons_used(tree: ast.AST) -> set[str]:
    return {
        Reason[node.attr].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Reason"
    }


def _device_api() -> dict[str, Any]:
    tree = _tree(DEVICE_API)

    def dict_keys(name: str) -> set[str]:
        # The values are DeviceScope members, which literal_eval cannot read.
        node = _assigned(tree, name)
        assert isinstance(node, ast.Dict)
        return {ast.literal_eval(k) for k in node.keys if k is not None}

    return {
        "tree": tree,
        "version": ast.literal_eval(_assigned(tree, "CONTRACT_VERSION")),
        "actions": dict_keys("ACTION_SCOPES")
        | set(ast.literal_eval(_assigned(tree, "SESSION_ACTIONS"))),
        "sections": dict_keys("SECTIONS"),
        "max_rows": ast.literal_eval(_assigned(tree, "MAX_LOG_ROWS")),
        "default_rows": ast.literal_eval(_assigned(tree, "DEFAULT_LOG_ROWS")),
    }


def _results() -> set[str]:
    tree = _tree(MQTT)
    return {
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id.startswith("RESULT_")
    }


# --- the documents themselves ---------------------------------------------------


def test_the_packaged_copy_is_the_document():
    """The integration serves its own copy to the API page; docs/ is not
    installed by HACS. They are the same bytes."""
    assert PACKAGED.read_bytes() == OPENAPI.read_bytes()


def test_both_documents_parse_at_the_contract_version():
    version = _device_api()["version"]
    openapi = _load(OPENAPI)
    asyncapi = _load(ASYNCAPI)
    assert openapi["openapi"].startswith("3.1")
    assert asyncapi["asyncapi"].startswith("3.0")
    assert openapi["info"]["version"] == version
    assert asyncapi["info"]["version"] == version


# --- the endpoint: openapi.yaml -------------------------------------------------


def test_every_action_is_documented_and_nothing_else():
    doc = _load(OPENAPI)
    actions = _device_api()["actions"]
    assert _enum(doc, "Action") == actions
    body = doc["paths"]["/api/foyer/device"]["post"]["requestBody"]
    request = _deref(doc, body["content"]["application/json"]["schema"])
    documented: set[str] = set()
    for variant in request["oneOf"]:
        action = _deref(doc, variant)["properties"]["action"]
        documented |= {action["const"]} if "const" in action else set(action["enum"])
    assert documented == actions


def test_every_request_field_the_endpoint_reads_is_documented():
    doc = _load(OPENAPI)
    read = _gets(_device_api()["tree"], "command", "_arm", "_disarm") | _gets(
        _tree(ENDPOINT), "post"
    )
    request = _schema(doc, "DeviceRequest")
    assert _properties(doc, request) == read


def test_the_sections_are_the_code_s():
    doc = _load(OPENAPI)
    api = _device_api()
    assert _enum(doc, "Section") == api["sections"]
    params = doc["paths"]["/api/foyer/device/{section}"]["get"]["parameters"]
    by_name = {p["name"]: p for p in params}
    assert set(_deref(doc, by_name["section"]["schema"])["enum"]) == api["sections"]
    assert by_name["limit"]["schema"]["maximum"] == api["max_rows"]
    assert by_name["limit"]["schema"]["default"] == api["default_rows"]
    rows = _schema(doc, "LogSection")["properties"]["rows"]
    assert rows["maxItems"] == api["max_rows"]


def test_the_section_answers_match_their_builders():
    doc = _load(OPENAPI)
    tree = _device_api()["tree"]
    pairs = {
        "ZonesSection": _keys(tree, "zones_section"),
        "BatteriesSection": _keys(tree, "batteries_section"),
        "LogSection": _keys(tree, "async_log_section"),
        # What a device may read of it: no names, no services (review).
        "HealthSection": _keys(tree, "health_section"),
    }
    for schema, built in pairs.items():
        assert _properties(doc, _schema(doc, schema)) - ENVELOPE == built, schema


def test_a_refused_section_has_the_reasons_of_the_code():
    doc = _load(OPENAPI)
    refusal = _schema(doc, "SectionRefusal")["properties"]["reason"]["enum"]
    code = _reasons_used(_function(_device_api()["tree"], "read_refusal"))
    assert set(refusal) == code


def test_the_result_and_the_state_message_match_their_builders():
    doc = _load(OPENAPI)
    result = _schema(doc, "DeviceResult")
    top = set(result["properties"])
    zone_ref = set(_schema(doc, "ZoneRef")["properties"])
    assert top | zone_ref == _keys(_tree(ENDPOINT), "device_result")
    state = _keys(_tree(MQTT), "state_payload", "_countdown")
    assert _properties(doc, _schema(doc, "StateMessage")) == state
    session = set(_schema(doc, "SessionResult")["properties"])
    assert session == {"success", "reason", "until"}


def test_the_scopes_are_the_code_s():
    doc = _load(OPENAPI)
    assert _enum(doc, "Scope") == {str(s) for s in READ_SCOPES | ACT_SCOPES}


def test_every_reason_a_device_can_receive_is_documented():
    """The document lists every Reason but the few a device is never sent,
    and those are named above with why."""
    doc = _load(OPENAPI)
    everything = {r.value for r in Reason}
    assert everything >= NOT_SENT, "a reason named as not sent no longer exists"
    assert _enum(doc, "Reason") == everything - NOT_SENT
    # And nothing the endpoint's own code answers with is among the unsent.
    assert not _reasons_used(_device_api()["tree"]) & NOT_SENT
    assert not _reasons_used(_tree(ENDPOINT)) & NOT_SENT


def test_last_result_is_the_closed_four():
    results = _results()
    assert len(results) == 4
    assert _enum(_load(OPENAPI), "LastResult") == results
    assert _enum(_load(ASYNCAPI), "LastResult") == results


def test_the_detail_levels_are_the_code_s():
    levels = {d.value for d in MqttDetail}
    assert _enum(_load(OPENAPI), "DetailLevel") == levels
    assert _enum(_load(ASYNCAPI), "DetailLevel") == levels


# --- the broker: asyncapi.yaml --------------------------------------------------


def test_the_mqtt_command_is_the_code_s():
    doc = _load(ASYNCAPI)
    tree = _tree(MQTT)
    compared = {
        node.comparators[0].value
        for node in ast.walk(_function(tree, "command_event"))
        if isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and node.left.id == "action"
        and isinstance(node.comparators[0], ast.Constant)
    }
    assert _enum(doc, "Action") == compared | {"status"}
    fields = _gets(tree, "command_event", "_async_command")
    assert set(_schema(doc, "Command")["properties"]) == fields


def test_the_mqtt_state_at_each_level_is_the_code_s():
    doc = _load(ASYNCAPI)
    built = _keys(_tree(MQTT), "state_payload", "_countdown")
    full = _properties(doc, _schema(doc, "StateFull"))
    standard = _properties(doc, _schema(doc, "StateStandard"))
    minimal = _properties(doc, _schema(doc, "StateMinimal"))
    assert full == built
    assert full - standard == {"open_zones"}
    assert standard - minimal == {"scenario", "areas"}
    messages = doc["channels"]["state"]["messages"]
    assert len(messages) == len(MqttDetail)


def test_the_mqtt_reasons_are_the_endpoint_s_less_its_own():
    openapi = _enum(_load(OPENAPI), "Reason")
    asyncapi = _enum(_load(ASYNCAPI), "Reason")
    assert openapi >= ENDPOINT_ONLY
    assert asyncapi == openapi - ENDPOINT_ONLY


def test_the_health_section_reads_only_what_the_page_builds():
    """health_section picks fields out of the page's health status with
    ``.get``; a field renamed there would turn into null here with nothing
    failing (review)."""
    tree = _device_api()["tree"]
    picked: set[str] = set()
    for node in ast.walk(_function(tree, "health_section")):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            picked.add(node.args[0].value)
    built = _keys(_tree(SYSTEM), "_health_status")
    assert picked - {"id"} <= built | {"id"}, picked - built
