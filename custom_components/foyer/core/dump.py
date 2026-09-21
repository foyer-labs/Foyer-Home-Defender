"""The anonymised diagnostics dump (SPEC §12.4). Pure, like everything here.

What this exists for: "this turns a GitHub issue into something answerable
instead of five rounds of questions." What it must never do is make somebody
choose between getting help and publishing the shape of their house.

So the rule is inverted from the usual one. Nothing is included unless it is
named here — an allow-list, not a list of things to strip — because a field
added to a config dataclass in six months would otherwise walk straight into
the next person's issue thread. Names, codes, hashes, URLs, phone numbers,
chat ids, topics and targets are not in the list.

Entity ids become stable placeholders, and "stable" means one thing
precisely (part 1 decision 11): two downloads from the same installation
give the same placeholder while the configuration is unchanged, so an issue
thread can say ``binary_sensor.zone_3`` twice and mean the same zone. They
are numbered from the order of Foyer's own configuration objects, not
hashed: a hash of an entity id is verifiable by anybody who guesses the id,
which is obfuscation wearing anonymity's coat, and §12.4 asks for a dump
with no hashes in it.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .health import causes, configured_channels
from .models import FoyerConfig, RuntimeState, SystemSnapshot


class Placeholders:
    """Stable names for everything in one installation.

    Built by walking the configuration in its stored order, which is the
    order the panel shows and the order a restore writes back. Two dumps of
    an unchanged installation therefore agree; two installations do not, and
    cannot be made to — there is no shared vocabulary for "the third zone of
    a house you have never seen".
    """

    def __init__(self, config: FoyerConfig) -> None:
        self.ids: dict[str, str] = {}
        self.entities: dict[str, str] = {}
        for prefix, items in (
            ("area", config.areas),
            ("zone", config.zones),
            ("scenario", config.scenarios),
            ("profile", config.profiles),
            ("group", config.groups),
            ("person", config.users),
            ("contact", config.contacts),
            ("device", config.devices),
            ("rule", config.rules),
            ("radio", config.health.radios),
        ):
            for index, item in enumerate(items, start=1):
                self.ids[item.id] = f"{prefix}_{index}"
        # A zone's entity is named after the zone, which is what makes the
        # dump readable: "binary_sensor.zone_3 is in fault" is a sentence
        # somebody can answer.
        for zone in config.zones:
            self.entity(zone.entity_id, hint=self.ids.get(zone.id, "zone"))
            if zone.battery_entity_id:
                self.entity(
                    zone.battery_entity_id,
                    hint=f"{self.ids.get(zone.id, 'zone')}_battery",
                )

    def of(self, object_id: str | None) -> str | None:
        if not object_id:
            return None
        return self.ids.get(object_id, "unknown")

    def entity(self, entity_id: str | None, hint: str | None = None) -> str | None:
        """The placeholder for one entity id, keeping its domain.

        The domain stays because it is not private and it is most of what
        makes a dump readable: ``cover.zone_4`` tells a reader at once that
        somebody is using a garage door as a zone, which is exactly the kind
        of thing an issue is about.
        """
        if not entity_id:
            return None
        if entity_id in self.entities:
            return self.entities[entity_id]
        domain, _, _ = entity_id.partition(".")
        name = hint or f"entity_{len(self.entities) + 1}"
        placeholder = f"{domain or 'entity'}.{name}"
        self.entities[entity_id] = placeholder
        return placeholder


def anonymised(
    config: FoyerConfig,
    state: RuntimeState,
    snapshot: SystemSnapshot | None = None,
) -> dict[str, Any]:
    """The whole dump: shape, settings and condition, and no personal data."""
    names = Placeholders(config)
    return {
        "areas": [
            {
                "id": names.of(area.id),
                "entry_delay": area.default_entry_delay,
                "exit_delay": area.default_exit_delay,
                "ha_state_when_armed": area.ha_state_when_armed,
                "is_perimeter": area.is_perimeter,
                "state": state.area(area.id).state.value,
                "has_timer": state.area(area.id).timer is not None,
                "memory": state.area(area.id).memory,
            }
            for area in config.areas
        ],
        "zones": [
            {
                "id": names.of(zone.id),
                "area": names.of(zone.area_id),
                "entity": names.entity(zone.entity_id),
                "type": zone.type.value,
                "channel": zone.channel.value,
                "entry_mode": zone.entry_mode.value,
                "alarm_kind": zone.alarm_kind.value,
                "arm_policy": zone.arm_policy.value,
                "trigger": type(zone.trigger).__name__,
                "always_on": zone.always_on,
                "silent": zone.silent,
                "bypassable": zone.bypassable,
                "enabled": zone.enabled,
                "trigger_confirmed": zone.trigger_confirmed,
                "supervision_timeout": zone.supervision_timeout,
                "has_battery_entity": bool(zone.battery_entity_id),
                "in_fault": zone.id in state.faults,
                "active": zone.id in state.active_zones,
                "bypassed": zone.id in state.bypassed,
            }
            for zone in config.zones
        ],
        "scenarios": [
            {
                "id": names.of(scenario.id),
                "areas": [names.of(a) for a in scenario.areas],
                "ha_master_state": scenario.ha_master_state,
                "active": scenario.id == state.active_scenario_id,
            }
            for scenario in config.scenarios
        ],
        "profiles": [
            {
                "id": names.of(profile.id),
                "severity": profile.severity,
                "actions": [
                    {
                        "kind": action.kind.value,
                        "moments": sorted(m.value for m in action.moments),
                        "conditions": len(action.conditions),
                        "escalation_offset": action.escalation_offset,
                        # The parameters are where a phone number, a chat id,
                        # a media file name or a free-text message lives, so
                        # what travels is their shape: which keys were set.
                        "params": sorted(action.params),
                        "targets": [names.entity(e) for e in _targets(action.params)],
                    }
                    for action in profile.actions
                ],
            }
            for profile in config.profiles
        ],
        "groups": [
            {
                "id": names.of(group.id),
                "area": names.of(group.area_id),
                "members": [names.of(m) for m in group.members],
                "n": group.n,
                "window": group.window_seconds,
                "suppress_members": group.suppress_members,
            }
            for group in config.groups
        ],
        # Counts, never names. "Who is in this house" is the single most
        # personal thing Foyer stores, and it is never the answer to a bug.
        "users": {
            "count": len(config.users),
            "enabled": sum(1 for u in config.users if u.enabled),
            "with_code": sum(1 for u in config.users if bool(u.code_hash)),
            "with_duress_code": sum(
                1 for u in config.users if bool(u.duress_code_hash)
            ),
            "linked_to_ha": sum(1 for u in config.users if u.ha_user_id),
        },
        "contacts": [
            {
                "id": names.of(contact.id),
                "enabled": contact.enabled,
                "has_quiet_hours": bool(contact.quiet_start and contact.quiet_end),
                "quiet_min_severity": contact.quiet_min_severity.value,
                "channels": [
                    {
                        "kind": channel.kind.value,
                        # The integration, not the address: "notify.telegram"
                        # says what somebody is using, the chat id says who.
                        "domain": channel.service.partition(".")[0],
                        "actionable": channel.actionable,
                        "enabled": channel.enabled,
                        "has_target": bool(channel.target),
                        "extra_keys": sorted(channel.data),
                    }
                    for channel in contact.channels
                ],
            }
            for contact in config.contacts
        ],
        "devices": [
            {
                "id": names.of(device.id),
                "kind": device.kind.value,
                "enabled": device.enabled,
                "has_entity": bool(device.entity_id),
                "names_a_user": bool(device.user_id),
            }
            for device in config.devices
        ],
        "rules": [
            {
                "id": names.of(rule.id),
                "trigger": rule.trigger.kind.value,
                "action": rule.action.value,
                "watches": len(rule.trigger.entity_ids),
                "grace_seconds": rule.grace_seconds,
                "guards": sorted(
                    key
                    for key, value in (
                        ("only_when_disarmed", rule.guards.only_when_disarmed),
                        ("only_when_ready", rule.guards.only_when_ready),
                        ("quiet_minutes", rule.guards.quiet_minutes is not None),
                    )
                    if value
                ),
                "enabled": rule.enabled,
            }
            for rule in config.rules
        ],
        "settings": {
            "siren_duration": config.settings.siren_duration,
            "entry_delay": config.settings.default_entry_delay,
            "exit_delay": config.settings.default_exit_delay,
            "arm_hold_timeout": config.settings.arm_hold_timeout,
            "low_battery_threshold": config.settings.low_battery_threshold,
            "walk_test_timeout": config.settings.walk_test_timeout,
            "allow_auto_disarm": config.settings.allow_auto_disarm,
            "silent_suppresses": list(config.settings.silent_suppresses),
            # A language, not a location, and it explains a whole class of
            # "the notification came out in English" reports.
            "language": config.settings.language,
            "ack_webhook_enabled": bool(config.settings.ack_webhook_id),
            "mqtt_enabled": config.settings.mqtt.enabled,
            "mqtt_detail": config.settings.mqtt.detail.value,
            "code_length": config.settings.security.code_length,
            "code_policy": {
                "arm": config.code_policy.arm,
                "disarm": config.code_policy.disarm,
                "acknowledge": config.code_policy.acknowledge,
                "edit_config": config.code_policy.edit_config,
            },
        },
        "health": _health(config, state, snapshot, names),
        "runtime": {
            "incident_open": state.incident is not None,
            "incident_contributors": (
                len(state.incident.contributors) if state.incident else 0
            ),
            "technical_alarms": len(state.technical),
            "escalations": [e.kind.value for e in state.escalations],
            "pending_runs": len(state.pending_runs),
            "running_actions": len(state.running),
            "walk_test": state.walk_test is not None,
            "auto_arming": state.auto_arming,
            "pending_rules": len(state.pending_rules),
            "suspensions": len(state.suspensions),
            "lockouts": len(state.lockouts),
            "bypassed": len(state.bypassed),
        },
    }


def _targets(params: Mapping[str, Any]) -> tuple[str, ...]:
    value = params.get("entity_ids") or params.get("entity_id") or ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def _health(
    config: FoyerConfig,
    state: RuntimeState,
    snapshot: SystemSnapshot | None,
    names: Placeholders,
) -> dict[str, Any]:
    health = state.health
    return {
        "causes": (
            [c.value for c in causes(health, config, snapshot)] if snapshot else []
        ),
        "mains": {
            "configured": bool(config.health.mains_entity_id),
            "entity": names.entity(config.health.mains_entity_id),
            "lost_states": list(config.health.mains_lost_states),
            "lost": health.mains_lost_since is not None,
        },
        "watchdog": {
            "enabled": config.health.watchdog.enabled,
            # Never the URL. A healthchecks.io ping URL *is* the credential:
            # anybody who has it can keep the check green for ever, which is
            # to say, silence the one thing that reports Foyer's own death.
            "url_set": bool(config.health.watchdog.url),
            "interval": config.health.watchdog.interval,
            "timeout": config.health.watchdog.timeout,
            "payload": config.health.watchdog.payload,
            "failures": health.watchdog.failures,
            "ever_ok": health.watchdog.ever_ok,
            "down": health.watchdog.down_since is not None,
        },
        "channels": [
            {
                "channel": names.of(key.partition(":")[0]),
                "fault": (
                    health.channel(key).fault.value
                    if health.channel(key).fault
                    else None
                ),
                "failures": health.channel(key).failures,
                "checked": health.channel(key).present is not None,
            }
            for key in configured_channels(config)
        ],
        "radios": [
            {
                "id": names.of(radio.id),
                "domain": (radio.coordinator_entity_id or "").partition(".")[0] or None,
                "coordinator_set": bool(radio.coordinator_entity_id),
                "coordinator": names.entity(radio.coordinator_entity_id),
                "enabled": radio.enabled,
                "n_zones": radio.n_zones,
                "window": radio.window,
                "suspected": health.radio(radio.id).suspected_since is not None,
                "confirmed": health.radio(radio.id).confirmed,
                "coordinator_down": (
                    health.radio(radio.id).coordinator_down_since is not None
                ),
            }
            for radio in config.health.radios
        ],
        "rf": {
            "zones": config.health.rf_zones,
            "window": config.health.rf_window,
            "confirm": config.health.rf_confirm,
        },
        "quiet_zones": len(health.quiet_since),
    }
