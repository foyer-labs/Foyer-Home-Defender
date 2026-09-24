# Foyer Home Defender — Design Specification

> **Status:** v0.1 — design frozen for implementation
> **Domain:** `foyer`
> **License:** Apache-2.0
> **Language:** code, entities, services, documentation in English. UI fully localised (en, it) from day one.
> **Target:** Home Assistant custom integration distributed via HACS.

This document is the single source of truth for the project. Every implementation
session must start by reading it. It is written to be handed to an AI coding agent
as well as to a human contributor.

---

## 1. What this is

Foyer Home Defender turns Home Assistant into a real intruder alarm system: not a
collection of automations, but a configurable alarm panel with areas, arming
scenarios, zone semantics, a response engine, identified users, physical keypads,
an auditable event log, and — uniquely — a simulator that lets you verify the
configuration before trusting it.

### 1.1 Goals

- Behave like a real alarm panel, using the vocabulary of real alarm panels.
- Be configurable entirely from a UI, with no YAML required.
- Be generic: work with any Home Assistant entity, any notification channel,
  any keypad, without hard-coding vendors.
- Be verifiable: the user must be able to prove the configuration is correct
  *without* setting off sirens or waiting for a burglary.
- Be honest about what it protects against and what it does not.

### 1.2 Non-goals

- It is not a certified alarm system and must never be presented as one.
  EN 50131 grade compliance is explicitly out of scope.
- It does not replace a monitored professional installation.
- It does not implement notification transports. Home Assistant already has
  `notify.*` integrations for push, SMS, voice calls and messaging. Foyer
  orchestrates them; it does not reimplement them.
- It does not implement a general-purpose automation engine. Complex conditional
  logic belongs in Home Assistant automations, driven by the events Foyer emits.

### 1.3 Prior art and positioning

[Alarmo](https://github.com/nielsfaber/alarmo) (Apache-2.0) is the reference
implementation in this space and covers arming modes, per-sensor delays, an
action engine, users with codes, MQTT and a Lovelace card. Foyer is written from
scratch and does not copy its code. It differentiates on three axes that Alarmo
does not address:

| Differentiator | Why it matters |
|---|---|
| **User-defined scenarios, unlimited** | Alarmo is bound to Home Assistant's four fixed arm modes. Real installations need "Night, ground floor only", "Garage only", "Dog at home". |
| **Simulator and walk test** | Nobody can currently answer "what would happen if the kitchen window opened right now, in this scenario, at this hour?" without actually opening it. |
| **Escalation with acknowledgement** | Notifications that keep escalating across channels and people until a human acknowledges. This is what a real dialler does and what Home Assistant has no ready-made answer for. |

This section is where the comparison lives, and the only place. The README is a
front door, not a positioning document: it describes Foyer on its own terms and
names no other product, except one neutral line pointing at the importer of
§20.2 (decision 148).

---

## 2. Non-negotiable invariants

These are architectural constraints. Violating any of them breaks a headline
feature and requires a rewrite, not a patch. They must be respected in every
phase, including Phase 0.

### INV-1 — The decision engine is a pure function

```
decide(system_snapshot, event, config, now) -> Decision
```

`Decision` is a data structure describing what *should* happen: the state
transitions, the actions to run, the notifications to send. It executes nothing,
performs no I/O, touches no Home Assistant state, and reads no clock or random
source that is not passed in as an argument.

A separate **executor** layer consumes a `Decision` and performs the side
effects. A separate **scheduler** layer owns timers.

Consequence: the simulator is the same `decide()` called with a fabricated
snapshot and a fabricated clock, and its output is therefore guaranteed truthful.
Without this separation, the simulator either lies or fires real sirens.

### INV-2 — Codes are verified in the backend only

Lovelace cards run in the user's browser. Any PIN check performed in the frontend
is decoration: a user with Home Assistant access can call
`alarm_control_panel.alarm_disarm` from Developer Tools and bypass it entirely.

Therefore: every service and every WebSocket command that changes alarm state or
configuration validates the code server-side and rejects the request when it is
missing or wrong. The card is a keypad that transmits a code; it never decides.

Codes are stored as bcrypt hashes, never in plaintext, never returned by any API.

### INV-3 — State survives restarts

Area states, active scenario, bypassed zones, pending timers and escalation
progress are persisted and restored when Home Assistant restarts. An alarm that
disarms itself because of a core update is worthless.

The restart gap must be logged explicitly (`system_unavailable` from T1 to T2) so
the log does not silently imply the house was covered.

A decision's log rows are written, and its actions started, before its state
reaches the disk: a slow disk must never stand between a trigger and its
siren. So a process killed in the milliseconds between the two can leave a
row describing a state that was never saved. The next start restores the
state that was, and its restart-gap row says when the house stopped being
watched: the log never claims coverage the state did not have (decision
146).

### INV-4 — Unknown is a fault, not calm

A zone entity in `unavailable` or `unknown`, or whose last heartbeat exceeded its
configured supervision window, is a **fault**. It must:

- block arming (unless the zone is explicitly configured to allow it),
- raise a `zone_fault` event and notification,
- be visible in the diagnostics page,

and it must never be silently treated as "closed" or "no motion".

### INV-5 — Never assume `on` means alarm

Every zone declares its own trigger condition. NC and NO magnetic contacts behave
in opposite ways; a default of "on = triggered" produces installations that never
fire. There is no global default; the zone wizard proposes one based on the
entity's `device_class` and the user confirms it.

### INV-6 — Threat model is stated, not implied

The README contains a "Security model" section stating plainly:

> Foyer's codes protect against household members, guests, cleaners, non-admin
> Home Assistant users and anyone who finds an unlocked wall tablet. They do
> **not** protect against a Home Assistant administrator, who can read
> `.storage`, disable the integration or call any service directly. Foyer is not
> a certified alarm system.

### 2.1 Stated principles

Not invariants — breaking one of these does not disable a feature and does not
require a rewrite — but decisions the project keeps making, written once so
that the next channel does not have to rediscover them.

#### P-1 — Outward, Foyer says the least that works

Every channel that publishes to something Foyer does not control starts at the
minimum needed to make it work. Anything that adds the state of the house is an
explicit option, off by default, with the reason written next to it.

The reasoning is always the same: a message leaving the house is read by
whoever holds the other end, and "armed, Night, nobody home" tells a third
party exactly when to come. It is the reason the external watchdog's heartbeat
is empty (decision 29), and the reason the retained MQTT message starts at
`minimal` (decision 83). The channels of Phase 4 and Phase 5 — notification
transports, a DTMF webhook, an export — meet the same rule already written
rather than arriving at it again by accident, which is how §9.2 came to list
the open windows by name in the first place.

This does not apply to what stays inside: the panel, the card, the log and the
entities are Foyer talking to its own household, and there the rule is the
opposite — say everything, because a system that hides what it knows is the
failure this project exists to avoid.

Two things are kept from view even inside. **Credentials**: the panel says
that a code, a device's token, the acknowledgement webhook or the watchdog URL
exists, and never reads one back; a token and the webhook's address are shown
once, in the answer that generates them, and never again (decisions 128–130).
Inside is read by more people than the one who set the credential — whoever
holds `edit_config`, whoever finds the tablet — and a credential shown there
can be carried out of the house. And **`duress`**: its row is read on the log
page and in an export, never where a glance would find it, because the person
who asked for help may be standing beside whoever made them (§8.1, decision
133).

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Lovelace card  (foyer-card)        TypeScript / Lit        │
│  variants: full · compact · badge · keypad                  │
└──────────────┬──────────────────────────────────────────────┘
               │ HA service calls + entity state
┌──────────────┴──────────────────────────────────────────────┐
│  Sidebar panel  (SPA, 11 pages + first-run wizard)          │
│  TypeScript / Lit, built with Vite, served by the component │
└──────────────┬──────────────────────────────────────────────┘
               │ Home Assistant WebSocket API (foyer/* commands)
┌──────────────┴──────────────────────────────────────────────┐
│  Backend  (Python, custom_components/foyer)                  │
│                                                              │
│   api/          WebSocket command handlers                   │
│   store/        config storage (.storage) + SQLite log       │
│   core/                                                      │
│     engine.py   decide()  ← PURE, no I/O, no HA imports      │
│     models.py   dataclasses for config and snapshot          │
│     machine.py  per-area state machine (pure transitions)    │
│   runtime/                                                   │
│     executor.py runs a Decision (actions, notifications)     │
│     scheduler.py timers: exit/entry/siren/escalation         │
│     watcher.py  subscribes to entity state changes           │
│     mqtt.py     keypad contract in/out                       │
│   entity/       alarm_control_panel, select, binary_sensor,  │
│                 sensor, button                               │
│   security/     codes (bcrypt), permissions, lockout         │
└──────────────────────────────────────────────────────────────┘
```

**Hard rule:** `core/` must not import `homeassistant.*`. It is plain Python over
plain dataclasses, unit-testable without a Home Assistant instance. This is what
makes INV-1 enforceable rather than aspirational.

### 3.1 Repository layout

```
foyer-home-defender/
├── custom_components/foyer/
│   ├── __init__.py  manifest.json  config_flow.py  const.py
│   ├── core/        engine.py  machine.py  models.py  conditions.py
│   ├── runtime/     executor.py  scheduler.py  watcher.py  mqtt.py
│   ├── store/       config_store.py  log_store.py  migrations/
│   ├── security/    codes.py  permissions.py  lockout.py
│   ├── api/         websocket.py  services.py  services.yaml
│   ├── entity/      alarm_panel.py  scenario_select.py  zone.py  sensors.py
│   ├── translations/  en.json  it.json   (Home Assistant: config flow, entities, errors)
│   │   └── panel/     en.json  it.json   (panel, card, help, notifications)
│   └── frontend/    (built panel + card bundles, committed)
├── frontend/        panel and card sources (TypeScript, Vite)
├── blueprints/      keypad adapters (Ring v2, Zigbee generic, NFC tag)
├── docs/            SPEC.md  security-model.md  reusing-existing-sensors.md ...
├── tests/           pytest, engine test suite
├── hacs.json  LICENSE  NOTICE  README.md
```

### 3.2 Technology

| Layer | Choice | Rationale |
|---|---|---|
| Backend | Python 3.14+, Home Assistant 2026.6+ | The first release whose webhook list is for administrators only: before it, any signed-in account could read the address that stops an alarm (§7.2, decision 147) |
| Config storage | HA `Store` helper (`.storage/foyer.config`) | Backed up with HA, versioned, migration-friendly |
| Log storage | dedicated SQLite, stdlib `sqlite3` in an executor thread | Independent retention; unaffected by recorder purge. No new dependency: this is what Home Assistant's own recorder does, and an alarm that fails to load because a wheel could not be fetched at first setup is a failure mode worth not having (decision 72) |
| Password hashing | `bcrypt` | Already a Home Assistant dependency |
| Frontend | TypeScript + Lit + Vite | Matches HA frontend conventions; small bundles |
| Panel registration | `panel_custom` / `async_register_built_in_panel` | Standard sidebar SPA pattern |
| MQTT | optional dependency | Keypad contract works without it via services |

Configuration is **UI-only**. No YAML schema is offered; this matches the
direction of Home Assistant and avoids maintaining two configuration paths.

---

## 4. Domain model

### 4.1 Hierarchy

```
Zone  ──belongs to──▶  Area  ──referenced by──▶  Scenario
                         │
                         └── has its own armed/disarmed state
```

- A **zone** is one Home Assistant entity plus alarm semantics.
- An **area** is a group of zones with an independent armed state and its own
  `alarm_control_panel` entity.
- A **scenario** is a named preset that arms a chosen set of areas.
- A **master** `alarm_control_panel` aggregates all areas.

### 4.2 Zone

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `name` | str | |
| `entity_id` | str | any domain: `binary_sensor`, `sensor`, `cover`, `lock`, `switch`, `input_boolean`, `device_tracker`, `person`, `event`, `tag` |
| `area_id` | uuid | exactly one area |
| `type` | enum | preset, see 4.3 — a label recording which preset the zone started from; the engine never reads it |
| `channel` | enum | `intrusion` \| `technical` \| `key` — which machine the zone feeds: the intrusion state machine, the technical channel (§5.5), or arming commands (§4.7) |
| `entry_mode` | enum | `instant` \| `delayed` \| `follower` — what an intrusion zone does when it triggers in an armed area (§5.2) |
| `alarm_kind` | enum | `intrusion` \| `tamper` \| `panic` — what an intrusion trigger means, for events and the log |
| `trigger` | TriggerSpec | how "triggered" is determined — see 4.4 |
| `entry_delay` | seconds \| null | null = inherit from area |
| `follows` | list[uuid] | follower only: delayed zones, **in any area**, whose running entry window this zone also inherits. Empty = only its own area's window (the default) |
| `arm_policy` | enum | `block` (default) \| `auto_bypass` \| `arm_after_closing` \| `ignore` — what happens if open at arming. `arm_after_closing` holds the area in `arming` once the exit delay has elapsed and completes the moment the zone closes — both conditions — for the person who presses arm and *then* pulls the patio door shut; if the zone is still open `arm_hold_timeout` after the exit delay, arming fails as for `block` |
| `arm_hold_timeout` | seconds \| null | only with `arm_after_closing`: how long after the exit delay the zone may stay open before arming fails as `block`; null = the global default (300 s, bounds 60–1800) |
| `chime` | bool | sound a chime when this zone opens while its area is **not monitoring it** (§6.6) |
| `group_id` | uuid \| null | membership of an N-of-M verification group (§4.8). Derived: membership is stored once, as the group's `members` |
| `bypassable` | bool | may the user manually exclude it |
| `always_on` | bool | true for 24h/tamper/technical zones |
| `silent` | bool | the response runs without the action kinds the global silent list names (§6.2, decision 66) |
| `trigger_count` | int | N activations within `trigger_window` before alarming (default 1, at most 10). Only activations that would alarm at once count, as in a group (§4.8) |
| `trigger_window` | seconds | 1–3600, default 60 |
| `cross_zone_id` | uuid \| null | a second zone that confirms this one within `cross_zone_window`: the pair is a 2-of-2 group that does **not** suppress its members, symmetric whichever end declares it (§4.8) |
| `cross_zone_window` | seconds | 1–3600, default 60; a pair declared from both ends has one window |
| `allow_arm_when_faulted` | bool | default false; a zone in fault does not block arming (§5.4, INV-4) |
| `supervision_timeout` | seconds \| null | per zone, **off (null) by default**. No report from the entity within this window — a heartbeat counts even when the state has not changed (Home Assistant's `last_reported`) — ⇒ fault (INV-4). Set it per sensor, longer than that sensor's own reporting interval; leave it off for sensors that report only when they change |
| `battery_entity_id` | str \| null | optional, for diagnostics and low-battery faults |
| `camera_entity_ids` | list[str] | ordered, empty by default: the cameras that show this zone and the rooms around it. A notification set to show the zone's cameras attaches these (§6.2.1, decision 91) |
| `response_profile_id` | uuid \| null | read **only for this zone's own alarm** (§6, decision 61); null = the area answers |
| `enabled` | bool | |

### 4.3 Zone types (presets)

Types are **UI sugar only**. They pre-fill the properties above; the engine reads
only properties. Every property remains editable after choosing a type. The
table below says which properties each type sets; validation rejects
combinations that make no sense (an always-on zone with an entry delay, a key
zone that is always on).

The division that matters is **not** "always on or not" — it is **intrusion or
non-intrusion**. Tamper and panic are security events; smoke, gas and flood have
nothing to do with a burglary and must never reach the intrusion state machine
(§5.5).

| Type | Channel |
|---|---|
| `instant`, `delayed`, `follower`, `24h`, `tamper`, `panic` | intrusion |
| `technical` | **technical** — separate channel, separate entities, separate acknowledgement |
| `key` | neither: it commands, it does not alarm |

| Type | Pre-filled behaviour | Properties it sets |
|---|---|---|
| `instant` | fires immediately when the area is armed | `channel=intrusion`, `entry_mode=instant` |
| `delayed` | grants entry delay (front door) | `channel=intrusion`, `entry_mode=delayed` |
| `follower` | inherits the entry delay if it triggers *after* a delayed zone in the same area within the entry window — or, via `follows`, after a delayed zone it follows in another area; instant otherwise (hallway PIR) | `channel=intrusion`, `entry_mode=follower` |
| `24h` | `always_on = true`; fires even when disarmed | `channel=intrusion`, `always_on=true`, `bypassable=false` |
| `tamper` | `always_on = true`, dedicated tamper semantics and events | `channel=intrusion`, `alarm_kind=tamper`, `always_on=true`, `bypassable=false` |
| `technical` | `always_on = true`, non-intrusion alarm (smoke, gas, flood) | `channel=technical`, `always_on=true`, `bypassable=false` |
| `panic` | `always_on = true`, `silent` configurable, manual activation | `channel=intrusion`, `alarm_kind=panic`, `always_on=true`, `bypassable=false` |
| `key` | does **not** trigger; its state change arms or disarms — see 4.7 | `channel=key`, `arm_policy=ignore` |

### 4.4 TriggerSpec

```python
TriggerSpec = StateTrigger | NumericTrigger | EventTrigger

StateTrigger:   states: list[str]          # e.g. ["on"] or ["open", "opening"]
NumericTrigger: operator: "gt"|"lt"|"eq"   # attribute optional
                value: float
                hysteresis: float
EventTrigger:   event_type: str | None     # for `event` / `tag` domains
```

How each domain is read:

| Domain | Trigger | Fires |
|---|---|---|
| `event` | `EventTrigger` with `event_type` required | on each new event whose `event_type` attribute matches |
| `tag` | `EventTrigger` with no `event_type` | on every scan — a tag has one event |
| any other | `StateTrigger` or `NumericTrigger` | while the state (or the number, with its hysteresis) is in the trigger condition |

Event triggers are momentary: an event zone is never "open" at arming. A
change out of `unavailable` is Home Assistant restoring the last event at
startup, not a new event, and does not fire.

The zone creation wizard proposes a `TriggerSpec` from the entity's
`device_class` and current state, and requires explicit confirmation (INV-5).

### 4.5 Area

| Field | Type | Notes |
|---|---|---|
| `id`, `name` | | |
| `default_entry_delay` | seconds | inherited by zones with `entry_delay = null` |
| `default_exit_delay` | seconds | |
| `response_profile_id` | uuid \| null | null = inherit from scenario |
| `require_code_to_arm` | bool \| null | null = inherit from global policy |
| `require_code_to_disarm` | bool \| null | |
| `ha_state_when_armed` | enum | which `alarm_control_panel` state this area reports when armed |
| `is_perimeter` | bool | marks the area as the outer defence ring. Automatic disarming can never act on a perimeter area (§9.5) |

### 4.6 Scenario

| Field | Type | Notes |
|---|---|---|
| `id`, `name`, `icon` | | |
| `areas` | list[uuid] | which areas this scenario arms |
| `ha_master_state` | enum | `armed_home` \| `armed_away` \| `armed_night` \| `armed_vacation` \| `armed_custom_bypass` — what the **master** panel reports, so voice assistants and HomeKit keep working |
| `response_profile_id` | uuid \| null | default profile for this scenario |
| `exit_delay_override` | seconds \| null | |
| `siren_duration_override` | seconds \| null | a night scenario may reasonably sound for less than a daytime one |
| `require_code_to_arm` | bool \| null | |
| `require_code_to_disarm` | bool \| null | |
| `allowed_user_ids` | list[uuid] \| null | null = everyone with permission |

Multiple scenarios may map to the same `ha_master_state`. The exact scenario is
always available on the `select.foyer_scenario` entity and in the log.

#### 4.6.1 Arming entry points

Areas have independent state (§4.1), so arming can target one area or a
scenario, and the two must not be confused:

| Entry point | Arms | Disarms |
|---|---|---|
| `alarm_control_panel.foyer_<area>` | **only that area**, outside any scenario, in the one mode it reports (`ha_state_when_armed`) | only that area |
| `alarm_control_panel.foyer_master` | the scenario whose `ha_master_state` is the requested mode — **refused when two or more scenarios share that mode**; the master advertises only unambiguous modes | every area |
| `select.foyer_scenario`, the panel, the card | the chosen scenario | — (disarm is a separate command) |

**Switching scenario while armed** (A → B): areas armed by A and absent from
B are disarmed; areas in both stay armed and now belong to B, keeping any
alarm memory, because nothing armed them again (§5.2); areas of B not yet
armed go through their exit delay and start clean; areas armed on their own,
outside any scenario, are left exactly as they are. A switch is refused while any area it
would touch is in `entry` or `triggered`: changing scenario must never silence
an alarm without a disarm.

The scenario stays active while any area it armed is still armed. An area
armed on its own does not change the active scenario.

### 4.7 Key zones

A zone of type `key` maps a state change to an arming command:

```
on_activate:   arm(scenario_id) | disarm | toggle
on_deactivate: none | disarm
identity:      user_id | null    # who the log attributes the action to
```

This covers key switches, NFC tags and remotes that are wired as entities rather
than through the MQTT contract.

`disarm` acts on **every** area, as the master's disarm does. `toggle`
disarms every area if any area is armed, and otherwise arms its scenario. A key
zone commands; it never alarms, and a refused arm is recorded, never silent.
A key zone's first reading after it is created is its baseline, not a turn of
the key: saving a key zone whose switch is already on does not arm the house.

### 4.8 Verification groups (N-of-M)

A group alarms only when **at least N of its M member zones** trigger within a
window. It is the strongest tool against false alarms in large spaces — an open
plan with three PIRs, a garden with two beams.

```
Group: { id, name, area_id, members[], n, window_seconds,
         response_profile_id, suppress_members: bool }
```

**Members keep their own profile.** This is what makes the mechanism worth having:
give the member zones a quiet profile and the group a loud one, and a single PIR
in the open plan sends a notification while two PIRs within sixty seconds sound
the siren. Graduated response, with no new machinery — it falls out of the
existing profile inheritance plus the `severity` field (§5.6).

`suppress_members: true` is available for the pure-suppression case, where member
zones produce nothing at all until the group is satisfied. It is not the default:
a single sensor detecting a real intruder and producing complete silence is
indistinguishable from the system working.

What a member does and what counts (decisions 51–53):

- A member that is not suppressed **alarms normally** on its own: its area
  goes to `triggered` (or `entry`) and an incident opens. The satisfied group
  adds its own record and, with profiles, its own response.
- Only an activation that would alarm **at once** counts towards a group: an
  instant or 24h zone, a follower with no window to inherit, anything in an
  area already triggered. An activation the entry delay absorbs — the delayed
  zone that opens it, a follower that inherits it — acts normally and never
  counts, so coming home can never satisfy a group. With `suppress_members`,
  it is the would-alarm activation that is held back, and released if the
  group is satisfied in time.
- Members may sit in **different areas**; each counts only while its own area
  watches it, and acts in its own area. The group's `area_id` is where it is
  shown and, with profiles, where its profile inherits from.
- A zone belongs to one group or cross-zone pair at most, or its activation
  would count twice.

#### Relationship with cross-zone verification

`cross_zone_id` on a zone (§4.2) stays exactly as it is in the UI: one field on
the zone, for the common case of one sensor confirming another. Behind it,
**the engine evaluates it through the group code as a degenerate 2-of-2 group.**
One engine to write, one to test, one representation in the simulator trace; two
ways to configure it, chosen by how complex the case is.

The pair is **symmetric** — A pointing at B forms {A, B}, B need not point
back — and it **does not suppress** its members: each zone still alarms on
its own, and the pair records the confirmation (decision 50). A cross-zone
field is therefore a confirmation, not a filter; the suppressing case is an
explicit group with `suppress_members`. `trigger_count` on a zone is the same
engine again: a window over one zone that counts repeats instead of
distinct zones.

#### Simulator requirement

The decision trace must show group state, not just the zone:

```
19:32:04  Zone "Open plan PIR 1" → motion
          Group "Open plan": 1 of 2 within 60 s → not satisfied
          Applied zone profile "Silent"
19:32:31  Zone "Open plan PIR 2" → motion
          Group "Open plan": 2 of 2 within 60 s → SATISFIED
          Applied group profile "Full"
```

---

## 5. State machine

One instance per area. The master panel is a **derived** aggregation, never an
independent state holder.

### 5.1 Area states

`disarmed` · `arming` · `armed` · `entry` · `triggered` · `fault`

`armed` is reported to Home Assistant as the area's configured
`ha_state_when_armed`. `entry` maps to HA's `pending`.

### 5.2 Transitions

| From | Event | To | Notes |
|---|---|---|---|
| `disarmed` | `arm_request` accepted | `arming` | exit delay starts; skipped if delay is 0. Alarm memory the area still holds is cleared, with `alarm_cleared`: the area starts clean |
| `arming` | exit delay elapsed | `armed` | zones still open with `arm_policy = auto_bypass` are bypassed and logged |
| `arming` | `disarm_request` accepted | `disarmed` | |
| `arming` | zone with `arm_policy = block` still open at expiry | `disarmed` | arming fails, `arm_failed` event |
| `armed` | instant zone triggers | `triggered` | |
| `armed` | delayed zone triggers | `entry` | entry delay starts |
| `armed` | follower zone triggers, no active entry window | `triggered` | |
| `armed` | follower zone triggers, entry window active | `entry` | inherits remaining delay |
| `armed` | follower zone triggers, a zone in its `follows` opened an entry window still running in another area | `entry` | inherits that window's deadline, not a new delay; with several, the earliest. The follower's area must be disarmed too, or it expires into `triggered` |
| `entry` | entry delay elapsed | `triggered` | |
| `entry` | `disarm_request` accepted | `disarmed` | the normal homecoming path |
| `entry` | instant zone triggers | `triggered` | entry delay does not protect other zones |
| `triggered` | `disarm_request` accepted | `disarmed` | stops sirens and escalation |
| `triggered` | siren cutoff elapsed | the pre-trigger state | sounders stop; alarm memory stays set until the area is disarmed or armed again. Triggered from `armed` or `entry` → `armed`; from `disarmed` (an `always_on` zone) → `disarmed`, never armed by the cutoff; from `arming` → `arming` resumes with its original exit deadline and the normal expiry checks, and keeps the memory: resuming an arming is not arming again |
| `disarmed` with alarm memory | `disarm_request` accepted | `disarmed` | clears the memory; the only transition allowed from `disarmed` by a disarm |
| any | `always_on` zone triggers | `triggered` | including from `disarmed` |
| any | supervision/availability fault | `fault` overlay | `fault` is a flag alongside the state, not a replacement |

**Alarm memory lasts until the area is disarmed or armed again** (decisions
140, 141). It is there so that somebody learns an alarm happened while nobody
was looking. An arming starts a new watch, and a memory carried into it would
describe an earlier night on a house armed since — which is why real panels
clear it at the next arming. It is cleared when an arming is accepted, for
each area that arming takes out of `disarmed`, with `alarm_cleared` as a
disarm raises it (§6.1) — whoever or whatever armed, an automatic rule
included. Nothing else that looks like arming clears it: a refused arming
leaves it, the cutoff resuming an interrupted arming is not a new one, an
area that stays armed through a scenario switch was not armed again, and a
walk test is not a watch (§11.3). An arming accepted and then failed when its
exit delay ends (`arm_failed`) has cleared it already, and it does not come
back. Nor does an arming accepted in the decision that ends a walk test: that
decision's response is still held back, so its `alarm_cleared` would reach
nobody, and a memory nobody has seen must not vanish on the way (decision
144); the next disarm or arming clears it. Clearing the memory is not taking
note of the alarm: the incident and its escalation go on until somebody
acknowledges it or disarms (§5.6).

### 5.3 Timers

| Timer | Owner | Default | Bound |
|---|---|---|---|
| exit delay | scenario override ?? area default (no per-zone exit delay: the exit timer belongs to the area) | 30 s | 0–300 s |
| entry delay | zone, else area | 30 s | 0–300 s |
| siren cutoff | global | 180 s | **hard max 900 s** (EN 50131 reference for external sounders) |
| escalation steps | response profile | — | |
| supervision | zone, per sensor | off | 60 s – 7 days |
| walk test auto-exit | global | 15 min without a detection | 1–60 min; never later than 3 h from the start; mandatory, non-disableable |

### 5.4 Arming preconditions

On `arm_request`, before entering `arming`, the engine evaluates every zone in
every target area:

1. Zones in fault (INV-4) ⇒ **block**, unless the zone is marked
   `allow_arm_when_faulted`.
2. Open zones with `arm_policy = block` ⇒ **block**, listing them in the failure
   reason so the UI and keypad can say *which* zone.
3. Open zones with `arm_policy = auto_bypass` ⇒ arm, bypass them, log each
   bypass, notify. Bypassed zones **rejoin automatically** when they close.
4. Open zones with `arm_policy = ignore` ⇒ arm normally.

A blocked arming can be overridden by a **forced arm** request, which is a
distinct command, requires the `force_arm` permission, and is logged as such.
Forced arming is never the default and never implicit.

A zone can also be excluded **by hand**, from the panel, the card or a service
(§16, "timed temporary bypass"). Two rules, both chosen to match real panels
(decision 70):

- an exclusion **without a duration** lasts for this arming and ends when the
  area is disarmed;
- an exclusion **with a duration** outlives the disarm and ends when its time is
  up, announcing the zone's return — because a zone excluded and forgotten is
  exactly the window somebody comes through.

Closing the zone never cancels a manual exclusion; that is what it was excluded
for. An automatic bypass, by contrast, rejoins the moment the zone closes.

### 5.5 The technical alarm channel

Non-intrusion zones (`technical`: smoke, gas, flood, temperature) run on a
**completely separate channel** with its own state, its own memory and its own
acknowledgement. It never touches `alarm_control_panel`.

The reason is concrete, not architectural purity. `triggered` on an
`alarm_control_panel` entity means one thing to Home Assistant, HomeKit, Google
and Alexa: *someone has broken in*. Route a smoke detector through it and those
systems announce a burglary while the kitchen is on fire.

| Property | Behaviour |
|---|---|
| State | `binary_sensor.foyer_technical_alarm` plus `sensor.foyer_technical_cause` naming the zone |
| When active | **Always.** Arming state is irrelevant; a technical zone is live whether the house is armed, disarmed or arming |
| Disarming | **Does not silence it.** Disarming is an intrusion command and has no authority here |
| Clearing | Requires an explicit acknowledgement **and** the underlying entity returning to normal. Until both, the state and its memory persist and stay visible on every card. One acknowledgement acts on every technical alarm pending at that moment (decision 49) |
| Actions | Its own response profile — the zone's, else a dedicated global technical profile, else the default (§6, decision 62) — its own escalation, independent of any intrusion incident in progress |
| Coexistence | A technical alarm and an intrusion incident can be active at the same time and never merge |
| Faults | A technical zone in fault blocks arming its area like any zone (INV-4), unless it is marked `allow_arm_when_faulted` (decision 48) |
| First reading | As for every zone (§4.7), the first reading is a baseline: a detector already detecting when its zone is saved alarms only once it has returned to normal and detects again. The zone editor says so (decision 56) |

**Mandatory documentation statement, non-negotiable:** Foyer is not a fire alarm
system. A smoke detector wired into Home Assistant does not replace certified,
interconnected smoke alarms, and no part of the UI or documentation may imply
that it does.

### 5.6 Incidents

During a real break-in several zones trigger in sequence: the window, then the
hall, then the stairs. Treating each as a separate alarm produces three
escalations — three pushes, three SMS, three calls, to three contacts, at the one
moment when the household needs to understand what is happening.

So an **incident** is the unit, not the zone:

- The first intrusion trigger **opens an incident** — the transition to
  `triggered`, not the start of an entry delay, which is the normal way home.
  When an entry delay runs out, the zones of that entry route contribute.
- Every subsequent trigger **joins it**, adding its zone to the incident and
  updating the notification text rather than starting anything new. A zone
  that joins after the incident was acknowledged clears the acknowledgement:
  whoever acknowledged what looked like the cat must hear that a second zone
  went. The history of acknowledgements is kept (decision 54).
- Actions are the **union**, deduplicated: a siren already sounding is not
  restarted; a light not yet on comes on. A message is not a siren: a
  notification answering a zone joining goes out again for every zone that
  joins, because "updating the notification text" is what joining does
  (decision 100).
- The escalation policy is the one belonging to the **highest-severity**
  contributing profile. This is what the `severity` field on a response profile
  (an integer the user orders) exists for, and it is used for nothing else.
- **One acknowledgement closes the whole incident.** Disarming an area the
  incident touched is an acknowledgement, as it is for escalation (§7.2);
  disarming an area it did not touch is not — whoever disarms the bedrooms in
  the morning has not seen the alarm on the perimeter (decision 57). Arming is
  never one, even when it clears the area's alarm memory (§5.2): arming asks
  no code by default, and a lamp switched off is not somebody who has seen the
  alarm.
- The incident closes when it is acknowledged *and* every contributing area is
  disarmed or has returned to `armed`. A trigger after that opens a new incident.

Technical alarms (§5.5) never join an intrusion incident — different channel,
different acknowledgement, by definition a different event.

Every incident gets an id that appears on every related log row, so the log can be
read as "what happened that night" rather than as scattered rows.

---

## 6. Response profiles

A response profile is a reusable, named list of actions. Profiles are resolved by
inheritance with override:

```
zone.response_profile_id
  ?? area.response_profile_id
  ?? scenario.response_profile_id
  ?? global default profile
```

**The area is the unit of response** (decision 61). The chain above starts at
the zone for one thing only: a zone's **own alarm** — the trigger, the entry it
opens, the verification group it satisfies. Everything else that happens in an
area — armed, disarmed, a fault, an exclusion — answers with the area's chain,
area → scenario → global default. That is one rule to hold in mind when asking
"why did it sound?", and it is exactly where a zone profile is needed: quiet
member profiles and a loud group profile are what make a group's response
graduated (§4.8).

A satisfied **group** answers with the group's own profile, falling back to its
area's chain. The **technical channel** answers with the zone's own profile, then
a dedicated global technical profile, then the default (§5.5, decision 62): a
smoke detector must not respond differently depending on how the house is armed,
and the scenario is meaningless to it.

The UI must always show the *effective* profile and where it was inherited from,
otherwise the behaviour looks arbitrary.

### 6.1 Trigger moments

A profile can attach actions to three distinct moments, not just alarms:

| Moment | Events |
|---|---|
| **Alarm** | `entry_started`, `triggered`, `siren_cutoff`, `alarm_cleared`, `alarm_ended` |
| **State change** | `armed`, `disarmed`, `arm_failed`, `forced_arm`, `zone_bypassed`, `code_rejected`, `lockout`, `duress` |
| **System** | `zone_fault`, `low_battery`, `ha_restarted`, `walk_test_started`, `walk_test_ended` |

`alarm_ended` belongs to one area and is raised once for each area an
alarm touched, when that area's siren cutoff runs or when it is disarmed
with its alarm memory set — and never on an ordinary disarm. It is the
moment for "switch the light off when the alarm is over", which an area's
profile can answer; the acknowledgement of the incident belongs to no area
and cannot serve (decision 105).

`alarm_cleared` belongs to one area too, and is raised when that area's alarm
memory is cleared: by a disarm, whether the siren is still sounding or its
cutoff ran hours ago, or by the next arming of that area (§5.2, decision
140). It is not `alarm_ended`: the alarm can be over long before anybody comes
home and clears it. It is the moment for "switch off the lamp that says an
alarm happened while you were out" (decision 108).

`duress` is raised once for every request made with a duress code (§8.1),
whatever it asked for. It belongs to no area, so only the global default
profile answers it. It always runs silent: the action kinds on the global
silent list are left out, as for a silent zone (§6.2), because a siren
answering a code nobody may know was used would tell the room exactly that. A
persistent notification is the wrong answer too — it appears on every Home
Assistant screen, the wall tablet included — and the profile editor says so.
`duress` never escalates and is never held back by a walk test (decision
132).

### 6.2 Action catalogue

| Action | Parameters |
|---|---|
| `notify` | contact ids or group, title/message templates, attachments, actionable buttons |
| `siren` | entity ids, duration, tone if supported |
| `light` | entity ids, brightness, colour, flash pattern |
| `camera` | snapshot or record, duration, attach to notification |
| `scene` | scene entity |
| `switch` | entity ids, on/off, optional auto-revert after N seconds |
| `tts` | media players, message template |
| `call_service` | **arbitrary HA service**: domain, service, target, data |
| `delay` | wait N seconds before the next action in the list |
| `persistent_notification` | a Home Assistant notification, with no contact book behind it — the tenth kind, and the one Phase 0 already used (decision 71) |

`call_service` is the escape hatch that keeps the user out of the automation
editor for anything Foyer does not model natively.

Four rules the catalogue depends on:

- A `delay` holds the rest of *that moment's* sequence. It is **state, not a
  task**: a restart in the middle of a sequence resumes it, and a `switch` with
  an auto-revert is switched back even if Home Assistant restarted meanwhile
  (decision 65). Without that, a restart during an alarm leaves a siren sounding
  for ever.
- A `siren` never sounds beyond the siren cutoff (§5.3), and a disarm or the
  cutoff stops what it started.
- A `camera` writes its file under a **configurable folder, `media/foyer` by
  default, and never under `www`**, which Home Assistant serves without
  authentication. That folder must be in `allowlist_external_dirs`: Home
  Assistant refuses to write outside it, and so does every transport that
  sends a file.
- **A notification names the transport it is attaching a picture for**
  (decision 90). There is no shared key: the Companion app reads `image` and
  is happy with a link to `/api/camera_proxy/<entity>`, because it is signed
  in and fetches the live picture itself, and nothing is written to disk.
  Telegram reads `photo` and needs a **file**, because its own server does the
  fetching, from outside the house and with no session — a relative proxy path
  is unreachable to it by construction. A transport discards a key it does not
  know without a word, so guessing is indistinguishable from working until the
  night it matters. For the file transports Foyer takes the snapshot at the
  moment of the notification, bounded, and sends the message without the
  picture if the camera does not answer: losing the attachment is a
  disappointment, losing the notification is not something a camera decides.
- A `silent` zone (§4.2) runs its response without the action kinds a **global
  list** names — `siren`, `tts` and the chime by default (decision 66). Silence
  belongs to the zone: another zone contributing to the same incident still
  sounds.

#### 6.2.1 The zone's cameras in a notification

The kitchen window opens: the household wants the kitchen camera, and the one
in the room next door, so that the picture says *where* the problem is rather
than that there is one. The cameras therefore belong to the zone
(`camera_entity_ids`, §4.2), not to the notification, and a notification can
ask for "the cameras of the zones that raised this" (decision 91).

**Which images an action carries is a choice on the action**, one selector
with three values (decision 92):

| Images | What is attached |
|---|---|
| `none` | nothing |
| `fixed` | the one camera the action names, exactly as before this section existed |
| `zone` | the cameras of the zones behind this alarm, as below |

Existing actions keep what they had — `fixed` where they name a camera,
`none` otherwise — so a migration changes nothing anybody receives. A new
notify action starts at `zone`. A zone with no cameras sends the text alone,
and the zone editor says so where the cameras are chosen.

With `zone`:

- **Every zone that has joined the incident** (§5.6) contributes its cameras,
  in the order the zones joined and then the order each zone lists them,
  each camera once (decision 93). A burglar goes from the window to the hall;
  the notification shows both, not only the way in.
- **At most four cameras per notification** (decision 95). Past four, the
  message says how many were left out. The bound is what keeps "every zone,
  every time" from becoming a wall of pictures.
- **Every notification repeats all of them, fresh** (decision 95): the first
  message, each zone joining, each escalation step (§7.2). What the house
  looks like *now* is the point of a picture, and a step two minutes later
  with the photograph from two minutes earlier would be the wrong one.
- **One notification per camera** (decision 94). The Companion app shows one
  image per notification, so the first message carries the text and the
  acknowledgement buttons exactly as without cameras, and each camera follows
  as its own notification carrying only its picture and the camera's name.
  The transport rules of decision 90 apply to each: a live
  `/api/camera_proxy/` link for the app, a snapshot file for Telegram.
- **Only at the moments that are an alarm** (decision 96): `triggered`, a zone
  joining the incident, each escalation step, and the technical channel
  (`technical_raised`, with the cameras of the technical zones pending —
  seeing the kitchen when the smoke detector goes is worth as much as seeing
  it when the window does). **Never at `entry_started`**: an entry delay is the
  household coming home (§5.6), and photographing every homecoming and
  sending it out of the house is what P-1 exists to stop. At any other moment
  a `zone` action sends its text alone, and the profile editor says so.
- **A camera never costs the message** (decision 90, again): a camera that
  does not answer in time costs its own picture and nothing else; the text
  notification, which is the one the acknowledgement and the channel health
  of §12.2 are counted on, always goes first.

INV-1 holds as it does for every action: `decide()` names the cameras in the
`Decision`, the executor fetches the pictures, and the simulator's trace
lists which cameras each notification would have carried without taking a
picture of anything.

### 6.3 Conditions

Each action may carry **at most two** conditions. This bound is deliberate — it
is the line between a response engine and a reimplementation of Home Assistant
automations.

| Condition | Shape |
|---|---|
| time window | `after: HH:MM`, `before: HH:MM`, correctly handling windows that cross midnight |
| entity state | `entity_id`, `operator: is / is_not`, `state: str` |

Two conditions combine with **and** or **or**, chosen by the user (decision 64):
"only at night *and* only if nobody is home" is the common case, but "either"
is worth the one selector. An entity that cannot be read satisfies nothing —
the same reasoning as INV-4.

Conditions are evaluated by `core/conditions.py`, which is pure and receives
entity states from the snapshot — so the simulator evaluates them identically.

### 6.4 Templates

Message templates support a fixed, documented variable set — not arbitrary Jinja
over the whole state machine:

`{{ zone }}` `{{ area }}` `{{ scenario }}` `{{ user }}` `{{ channel }}`
`{{ time }}` `{{ date }}` `{{ state }}` `{{ open_zones }}` `{{ reason }}`
`{{ incident_zones }}` — every zone that has joined the current incident (§5.6)
`{{ operation }}` — what a request made with a duress code asked for: the
operation of §8.2, or for a command that is none of them the name its
service in §14.1 or its device `action` in §9.2.2 gives it (`disarm`,
`bypass_zone`, `unlock`, `export_log`…). A duress message that cannot say
what the person was made to do tells its contact half of it (decision 134)

### 6.5 Profile severity

Each profile carries a `severity` integer, ordered by the user. It has exactly one
use: deciding which escalation policy an incident adopts when profiles of
different strength contribute to it (§5.6). It never affects a profile running on
its own.

### 6.6 Chime

A chime sounds when a zone opens **while it is not monitored by the active
scenario**. Not "while disarmed" — that narrower wording would leave a hole
precisely in the partial scenarios this project exists for: with *Windows only*
armed, the internal door is unmonitored and a chime there is just as useful as
with the system off.

No zone chimes during a walk test. An area the test armed is monitoring its
zones; an area it could not arm, or left disarmed because of its alarm memory
(§11.3), is not, and its chime is held back with every other action the test
inhibits.

"Monitored" is read **per area**, however the area came to be armed or not —
an area can be armed on its own, outside any scenario (§4.6.1). An area
counting down its exit delay is not yet monitoring; whether its zones chime
then is a setting, off by default, because the door you leave by is expected
to open (decision 55).

Configuration is one global block plus one switch per zone, the way real panels
do it — not a response profile, which would be disproportionate for a checkbox:

| Setting | Notes |
|---|---|
| Targets | one or more `media_player` or `siren` entities, **and `notify` targets** — a `notify.*` service (Companion app, Telegram, …) or a `notify` entity — which receive the zone name as a message (decision 60). Free channels the household already has; quiet hours apply to them as well |
| Mode | **single sound**, or **spoken zone name** via `tts.speak` — "Front door", "Garage shutter". In Home Assistant the second costs the same as the first and tells you *what* opened from the next room |
| Volume | |
| Quiet hours | a window in which chime is suppressed. **Each target may carry a window of its own**, which replaces the global one: the speakers all day, the phone only between nine and ten (decision 68) |
| During the exit delay | whether zones chime while their area counts down to armed; off by default |
| Per zone | the `chime` boolean on the zone (§4.2) |

Exposed as `switch.foyer_chime` so it can be silenced from a card, a keypad or an
automation.

---

## 7. Contacts and escalation

### 7.1 Contact

| Field | Notes |
|---|---|
| `id`, `name` | |
| `channels` | ordered list, highest priority first |
| `quiet_hours` | optional window during which only high-severity events reach this contact |
| `linked_user_id` | optional link to a Foyer user, so "who acknowledged" is known |

A **channel** is `{ kind, service, target, data }` where `service` is any
`notify.*` service present in the installation. Foyer does not know or care
whether that service is Twilio, Pushover, a GSM modem or Telegram — it is
discovered from the service registry and presented in a dropdown.

A contact that a profile in use by an armed area names — at once or as an
escalation step — cannot be changed, switched off or deleted until every area
is disarmed (§15.1, decision 138). Every field counts: the number, the
service, the quiet hours and the person it is linked to all decide who hears
the alarm. So do all of its channels, because a notification that names none,
or names one switched off, goes over the contact's first enabled channel.

Documented recipes live in `docs/notification-channels.md` and cover, at minimum:
Home Assistant Companion (with actionable notifications and iOS critical alerts),
Pushover priority 2, Twilio SMS, Twilio voice call, `sms` via a USB GSM modem,
Telegram and Signal.

### 7.2 Escalation

An escalation policy is an ordered list of steps:

```
step 0:  t+0s    notify contact "Luca" via channel 0 (push)
step 1:  t+60s   notify contact "Luca" via channel 1 (SMS)
step 2:  t+120s  notify contact "Partner" via channel 0, and voice-call Luca
step 3:  t+300s  notify contact "Neighbour"
```

The policy **stops immediately** on acknowledgement. Acknowledgement arrives
from any of:

- pressing an action button in an actionable push notification,
- disarming the system through any channel,
- a DTMF keypress captured by the voice-call provider and fed back through a
  webhook or service call,
- an explicit `foyer.acknowledge` service call.

Every acknowledgement records **who** and **through which channel**. An
escalation that runs to the last step without acknowledgement is logged as
`escalation_exhausted`, which is itself an event a profile can act on.

**The DTMF webhook is a credential.** A Home Assistant webhook is not
authenticated, so whoever holds its address can acknowledge an alarm in
progress. It does not exist until somebody switches it on; its id is
generated by the backend, never chosen by a caller; switching it off forgets
it. Its address is shown once, in the answer to the command that generates
it — the full URL when Home Assistant knows its external address, the path
otherwise — and no API returns it afterwards: the panel says only whether it
is on (decisions 128, 129). To see it again, generate a new one, which
replaces the old at once and has to be given to the voice provider again. A
Home Assistant administrator can still read it from `.storage`: that is
INV-6's boundary, not a leak.

### 7.3 Resilience note (documentation requirement)

`docs/resilience.md` must state clearly that every internet-dependent channel
fails precisely when an intruder cuts power or the fibre, and must recommend a
UPS on the router plus at least one local GSM channel as a fallback. A project
that promises alarm notifications over the internet alone is making a promise it
cannot keep.

---

## 8. Users, codes and permissions

### 8.1 User

| Field | Notes |
|---|---|
| `id`, `name` | |
| `code_hash` | bcrypt; write-only through the API, never returned |
| `duress_code_hash` | optional; acts exactly as the ordinary code, for every operation, and raises a silent `duress` event each time it is used |
| `ha_user_id` | optional link to a Home Assistant user |
| `permissions` | see 8.3 |
| `allowed_area_ids` | null = all. It narrows every operation that acts on an area — arming an area or a scenario, excluding a zone, disarming, the master's disarm of every area included. A walk test acts on the whole house and is not narrowed (§8.3) |
| `allowed_scenario_ids` | null = all |
| `valid_from` / `valid_until` | optional, for guest codes |
| `code_exempt_when_identified` | off by default; skip the code on channels that identify this user (§8.2, decision 79) |
| `enabled` | |

**Every user has their own code.** This is not a convenience: a shared code makes
"who disarmed at 03:14?" unanswerable, and the audit log — one of the reasons this
project exists — becomes decorative. Two consequences follow:

- **Codes must be unique across users.** Saving a code that already belongs to
  another user is rejected at save time. Without this check the first matching
  hash wins and the log attributes the action to the wrong person. The rejection
  message must not reveal *whose* code it collided with.
- **Code length is a global setting, not per user.** A keypad has to know how many
  digits to collect before validating. Configurable 4–12, default 6. The UI warns
  that a 4-digit code has roughly 10 000 combinations and leans entirely on
  lockout for safety.

The duress code is likewise per user and follows the same uniqueness rule,
including against ordinary codes.

**A duress code is its owner's code, and says so only to the log**
(decisions 131–134). It is accepted wherever the ordinary code is — arming,
disarming, excluding a zone, acknowledging, a walk test, unlocking an API
device, the panel's configuration and log commands, a service, a keypad, the
card — and does exactly what the ordinary code would: the same permissions,
the same answer, the same lockout counter, the same acknowledgement of an
incident. Nothing in the answer the person at the keypad, the panel or the
card sees or hears is different, and nothing a glance at the house's screens
would find is different either (below). The panel keeps it for its two minutes like any other
code (§15.1), because forgetting it sooner would be a difference somebody
could see.

What differs is one occurrence, `duress`, raised once for every request that
carried the duress code, whatever the request asked for and whether or not it
was granted — a locked-out channel and a device refusing an action outside
its scopes included. Somebody made to open the house is as easily made to
switch off the siren, stop the escalation or delete a contact, and a person
asking for help has asked, whatever the answer. A request a device refuses
before the engine hears it hands the engine the duress and nothing else: it
neither counts towards the lockout nor clears it, exactly as the ordinary
code would not. The occurrence names the operation (§6.4) and belongs to no
area and to no incident: an incident is on every card, and the person
standing beside the intruder would watch it open. It never escalates, runs
silent, and is answered by the global default profile (§6.1).

The `duress` row is read on the log page and in an export, and nowhere a
glance would find it: never `sensor.foyer_last_event`, never among the
Overview's recent events, never in an API device's `log` section, and it
sends no `changed: log` notice — the wall tablet the code was typed on shows
all of them. Like
every row it is also fired on Home Assistant's bus as `foyer_event`, which is
how a Home Assistant automation answers duress; an automation that shows
security rows somewhere in the house must leave it out. Emptying the log with a
duress code does not erase that request's own `duress` row: it is written
again after the clear, beside the row that records the clear, and the answer
counts the rows removed exactly as the ordinary code's would (decision 145).
Offering one's own duress code as a new code is not a use of it: it raises no `duress`, and is
refused and counted as a failed attempt, as any code already in use is
(§8.4).

### 8.2 Code policy resolution

```
code_required(operation) =
      global default for that operation
   → overridden by scenario/area setting
   → overridden by per-user setting  (ONLY on channels that identify the user)
   → otherwise: code required
```

Defaults, matching real panels:

| Operation | Default |
|---|---|
| arm | no code |
| disarm | code required |
| change scenario while armed | code required |
| force arm | code required |
| bypass a zone | code required |
| edit configuration | code required |
| enter walk test | code required |
| run a real action test | code required |
| acknowledge an alarm | **no code** (decision 77) |

Two rules the resolution needs that the arrows above do not carry:

- **The strictest explicit setting wins** when an area and a scenario disagree.
  Arming a scenario touches several areas at once, so if any area involved — or
  the scenario — requires a code, it is required; if none of them is set, the
  global default decides. The failure of this rule is one code too many; the
  failure of the opposite rule is an area its owner deliberately protected,
  opened because a permissive scenario included it (decision 80). The UI names
  the area that is asking.
- **The policy is inert while no enabled user holds a code.** No code can be
  verified then, so enforcing it would make the alarm unusable rather than
  safer. The panel and the card say so plainly while it lasts; from the first
  user created the policy applies in full (decision 78). That is also why,
  while any area is armed, an edit that would leave nobody with a usable code
  is refused (§15.1): a house armed asking for a code to disarm is disarmed
  with one.

**Entering a walk test asks for a code for the reason disarming does.** A
walk test holds back the answer of the whole house (§8.3), so its code is what
stands between the unlocked wall tablet and a quiet house. An installation may
lower it like any other entry, and should know what that buys: a request
nobody identified is checked against nobody's permissions, so with no code
asked, any caller that can reach a Foyer service or `switch.foyer_walk_test`
can start one (decision 137).

**A Home Assistant administrator is asked for the code like anybody else**
when the policy asks for one (decision 101). Being an administrator is not
an identification: the unlocked wall tablet INV-6 names is almost always
signed in as one. What the administrator keeps is §8.4's: never locked out.

**And a way back in that cannot go unnoticed** (decisions 109, 110). An
administrator who holds no code, in a house where others do, could otherwise
change nothing; one whose own Foyer user was disabled, or has run past its
validity window, could not undo it. The integration's **Configure** step in
Home Assistant — open to administrators only — recovers access: it asks for
which Home Assistant account (Home Assistant does not tell an integration who
opened the step; only administrators' accounts are offered, and choosing
another administrator buys nothing INV-6 does not already give — anybody
else is given a way in from the Users page, with the permissions that takes)
and for a new code. The Foyer user linked to that account
is enabled, its validity window is removed and the code is set; an account
with no linked user gets a new one, with every permission. The code follows
§8.1's uniqueness rule. It is never quiet: a `security` row, a Home Assistant
notification, and a message to every enabled contact, each naming the
account — said once the change has been written, because a recovery
announced and then not saved would tell the household about a code that does
not exist. One that could not be written leaves its row, marked failed, and
nothing else.

**Channels that identify the user:** Home Assistant UI with `ha_user_id` linked,
a per-user NFC tag, a per-user RFID badge. **Channels that do not:** a shared
keypad, a generic MQTT device, an automation. On a non-identifying channel the
code *is* the identity, so the per-user exemption cannot apply and the code is
always required. The configuration UI must state this next to the setting,
otherwise it reads as a bug.

The Home Assistant UI includes Home Assistant's own alarm card and the
`alarm_control_panel` actions a signed-in account calls, and there Home
Assistant decides before Foyer does: an entity that says arming needs a code
is refused a codeless arming by Home Assistant itself, for everybody, before
Foyer can see that the person asking is exempt. So Foyer's panels say arming
needs a code only while the policy asks for one and no enabled user has the
exemption switched on (§13, decision 136). An
automation calling the same actions identifies nobody, and Foyer asks it for
the code whenever the policy does.

### 8.3 Permissions

`arm` · `disarm` · `force_arm` · `bypass_zone` · `change_scenario` ·
`edit_config` · `view_log` · `test_actions` · `walk_test` · `manage_users`

`manage_users` owns people, and everything that decides what a person may
do or which key opens the house as whom: a person, a tag, the person a key
switch acts as, and the list of people allowed to use a scenario. Any change
that touches one of them — saved, deleted, restored or imported — needs
`manage_users` as well as `edit_config`; otherwise `edit_config` is a way to
hand oneself, or somebody else, what `manage_users` withholds (decisions
111, 112).

**`walk_test` reaches further than its name** (decision 137). A walk test is
walked through the whole house, so it arms every disarmed area that can arm —
whatever the person's `allowed_area_ids`, and except an area still holding
alarm memory (§11.3) — and until it ends no area answers an ordinary
detection, including an area somebody else had armed. It ends fifteen minutes
after the last detection by default, and never later than three hours after
it started. Whoever holds `walk_test` can therefore keep an armed house quiet
without holding `disarm`. This is kept on purpose, not overlooked. What
restrains it is that the test is never quiet about itself — a code by default
(§8.2), a banner on every screen, a notification at the start and at the end,
both log rows naming the person — and that `always_on` zones, an incident
already open and `duress` stay live (§11.3). The README's security model says
so as plainly as it says what a code does not protect against. It is not
among the permissions a person added on the Users page starts with — only the
first person, created by the first-run wizard, and the recovery of §8.2 hold
every permission — and the Users page warns, when it is ticked, that it can
keep an armed house quiet without `disarm`: it is given deliberately, as
`edit_config` and `manage_users` are.

### 8.4 Lockout

After `N` failed code attempts (default 5) within `W` seconds (default 300), the
originating channel is locked for `L` seconds (default 300), exponentially
increasing on repetition. The originating channel is counted per device for a
declared device, per source address for the device endpoint's missing or
wrong tokens —
a right token is never refused for its address (§9.2.1) — and **per Home
Assistant account** for the panel, the card and the
services: one account guessing codes locks itself out, not the household
(decision 103). A code offered when saving a person that is already in use —
somebody else's, or that person's own other code — counts as a failed attempt
(decision 104). A lockout:

- raises a `lockout` event that response profiles can act on (a tamper attempt on
  the keypad is a genuine alarm signal),
- is recorded in the log with the channel and device identifier,
- never locks out the Home Assistant admin path, to avoid self-lockout.

---

## 9. Arming channels

### 9.1 Service contract

```yaml
foyer.arm:
  scenario_id: str            # or scenario_name
  code: str | None
  user_id: str | None         # for identified, codeless channels
  channel: str                # ha_ui | keypad | nfc | mqtt | api | automation
  device_id: str | None       # which keypad, for the log and lockout
  force: bool = false
  skip_exit_delay: bool = false

foyer.disarm:        code, user_id, channel, device_id, area_ids?
foyer.bypass_zone:   zone_id, code, user_id, channel
foyer.acknowledge:   alarm_id?, user_id?, channel
foyer.walk_test:     enable: bool, code, duration?
foyer.simulate:      (see §11)
```

All commands return a structured result: `{ success, reason, blocking_zones[],
bypassed_zones[], state }` so a keypad adapter can give meaningful feedback
rather than a silent failure. One function builds it, shared by the services,
the WebSocket commands and the MQTT bridge: two paths that answered different
shapes would eventually be two paths, one of which had no check.

Three rules the contract needs that the shape above does not carry:

- **`device_id` names a registered device, and an unregistered one is refused**
  (decision 81). It is not a Home Assistant device id; it is what the device
  is declared as on page 8.
- **`channel` may only be claimed as `api` or `automation`.** A physical or
  identifying channel is a property of a registered device, never a claim a
  message makes, or an automation would buy the exemption of §8.2 by typing a
  word.
- **`user_id` is a claim, and the log says so** (decision 88). It grants
  nothing — claiming to be somebody brings their restrictions, never their
  exemptions — but arming needs no code by default, so a caller could otherwise
  write a name into the log that nothing established. Every row whose person
  was named by the request rather than established by a code or a token carries
  `attributed: claimed`, and the log page shows it beside the name. The
  capability stays, because an adapter needs a way to say who acted; what goes
  is the log's silence about the difference. A wrong answer to "who disarmed at
  03:14?" is worse than no answer. It grants nothing on any service, those
  that read the log or the configuration included: a permission comes from a
  code or a linked account, never from an id somebody typed (decision 102).
- **A refusal nobody reads is raised.** A caller that does not ask for the
  response is answered with an error rather than a result it will never look
  at; one that asks gets the structured result, refusal and all (decision
  106).
- **`skip_exit_delay` needs no permission of its own** (decision 85): whoever
  may arm may arm at once, and it uncovers nothing — it closes sooner. It does
  turn every delayed zone into an instant one, so the `armed` row records that
  it happened, and "why did it sound while I was still in the hall?" has an
  answer.

`foyer.walk_test` and `foyer.test_action` are **not registered until Phase 3**
builds them (decision 86). A service that exists and does nothing answers its
caller with silence, and silence is the answer that gets mistaken for success.

### 9.2 MQTT contract

Inbound (device → Foyer):

```
foyer/<install_id>/command
{ "action": "arm"|"disarm"|"status", "scenario": "night",
  "code": "1234", "device_id": "keypad_hall" }
```

Outbound (Foyer → device), for LEDs, beeps and displays:

```
foyer/<install_id>/state
{ "master": "armed_night", "scenario": "night",
  "areas": { "ground": "armed", "upstairs": "disarmed" },
  "countdown": { "kind": "exit"|"entry", "remaining": 22 },
  "ready_to_arm": false, "open_zones": ["Kitchen window"],
  "fault": false,
  "last_result": "ok"|"blocked"|"bad_code"|"locked_out",
  "last_reason": "zone_open"|"device_not_registered"|… |null }
```

Published retained on change and on request. Keypad adapters map `last_result`
to their own beep and LED vocabulary.

**The answer is two fields, and the first one never grows** (decision 87).
`last_result` is this closed set of four for ever, so an adapter written today
never meets a word it does not recognise — a keypad that goes quiet exactly
when something new happens is worse than one that says "blocked". Beside it,
`last_reason` carries the precise reason from the same stable set the services
return (§9.1), and an adapter that wants to tell "a window is open" from "I am
not a registered device" reads that one. A simple keypad reads the first and
never changes; an evolved one reads both. `last_reason` is a stable identifier
and never a name, so it belongs at every detail level, including the one that
says nothing about the house.

**How much of that message is published is a setting, in three steps, and it
starts at the least** (decision 83). The message is retained, on a broker that
is often shared, so whatever is in it is told to whoever connects next —
including "the house is armed and nobody is in", and, at the top level, which
window is open. That is the reasoning of decision 29 applied where it applies
again.

| Level | Carries |
|---|---|
| `minimal` (default) | master state, countdown, `ready_to_arm`, `fault`, `last_result`, and **how many** zones block arming |
| `standard` | adds the active scenario and the per-area states, by name |
| `full` | adds the open zones by name: the message above, as written |

Inbound, **`device_id` is not optional** (decision 81): anybody who can publish
to a topic can publish a command, so the name a message gives is the only thing
separating a keypad from a stranger — and the only thing that keeps the lockout
of §8.4 countable per device.

**Topics are configurable**, not fixed. The `foyer/<install_id>/` prefix is a
default, overridable per installation: people run more than one site against one
broker, and people have an existing topic hierarchy they are not going to
restructure for a new integration. Cheap to allow now, tedious to retrofit.

### 9.2.1 The device endpoint

MQTT travels in the clear unless the broker is set up with TLS, and on the
broker a keypad is only the name it gives (decision 81). A second transport
for keypads is therefore offered: an HTTP endpoint of Foyer's own, where each
keypad authenticates with a **token of its own** (decision 97).

Be precise about what the token buys, because it is easy to believe it buys
more. **The token authenticates the device; it does not encrypt anything.**
Over plain HTTP the token and the code typed on the keypad cross the network
exactly as readable as over plain MQTT. Confidentiality comes from TLS —
HTTPS for this endpoint, TLS with per-client credentials on the broker, or
ESPHome's native API, which is encrypted and can call `foyer.arm` and
`foyer.disarm` already. `docs/keypads.md` says all three, in that order of
simplicity.

**One transport per keypad** (decision 98). A keypad is declared on page 8
with `transport: mqtt | http`, and uses that one and no other. A command that
names an `http` keypad's `device_id` over MQTT or through a service call is
refused, recorded under `security` and notified as an unknown device is
(§9.3): otherwise whoever knows the name reaches the house through the broker
and the token protects nothing.

**Keypads only** (decision 99). A `tag` (§9.3) carries no code and is its
person's identity; a tag over this endpoint would make the token by itself
the key to the house, readable to anybody listening when the request is not
encrypted. Tags stay `tag`/`event` entities. On a keypad the code is still the
identity and still required by the policy (§8.2); a stolen or intercepted
token disarms nothing without a code, and the lockout of §8.4 counts per
device as it always has.

```
POST /api/foyer/device                      Authorization: Bearer <token>
{ "action": "arm"|"disarm"|"status", "scenario": "night", "code": "1234" }
→ the structured result of §9.1, with last_result / last_reason (§9.2)

GET  /api/foyer/device/state                Authorization: Bearer <token>
→ text/event-stream: the state message of §9.2, on connect and on every change
```

- **The token names the device.** A request carries no `device_id`, and one it
  carries anyway is ignored: the token is the identity of the device, the
  code the identity of the person.
- **The state stream is the MQTT message** of §9.2, at the same detail level
  (`minimal` by default, decision 83), pushed on every change so a countdown
  and an alarm arrive at once rather than at the next poll. A comment line
  every thirty seconds keeps a connection alive through proxies.
- **The token is a credential**, as the acknowledgement webhook (§7.2) and the
  watchdog URL (§12.3) are, and is kept as one: 32 random bytes, shown once
  when it is generated, stored as a SHA-256 hash — a random token needs no slow hash, a
  guessed code does — compared in constant time, and never returned by any
  API, written to a log row, put in a backup or the diagnostics dump, or set
  by a restore.
  Generating one invalidates the previous token at once and closes its open
  streams. Generating and revoking are `edit_config` operations with a code,
  as saving the keypad is: the token alone disarms nothing.
- **A wrong or missing token** answers 401 with no detail, and is counted per
  source address: past the lockout thresholds of §8.4 a wrong or missing
  token from that address is refused for the lockout period, the lockout is
  recorded under `security`, and it is notified once — a token-guessing loop
  is a tamper signal like a keypad's.
- **A right token is never refused for its address** (decision 135). The
  token is checked first, and the address's lockout applies only to a request
  whose token is missing or wrong. Behind NAT, a reverse proxy or one IPv6
  /64, a real keypad shares its address with whoever is guessing, and refusing
  the address locked the household out of its own keypad. A token is 32
  random bytes and cannot be guessed, so letting it through costs the lockout
  nothing: the lockout is a tamper signal and a brake on the log, not what
  keeps a token safe. Every row such a request causes says the address was
  locked, so the log shows a keypad sharing its address with somebody
  guessing; the request neither spends nor clears the address's counter.
- **Plain HTTP is accepted, and said** (decision 97). Foyer knows whether a
  request arrived encrypted, including behind a reverse proxy Home Assistant
  trusts. A keypad whose requests arrive in the clear carries a permanent
  warning on page 8 — its token and its codes can be read on the network —
  and every row it causes records that the request was not encrypted. Many DIY
  keypads cannot do TLS at all; refusing them would take the feature away from
  exactly the people who asked for it, and saying so plainly is the project's
  answer everywhere else.
- **The channel is `keypad`**, as for an MQTT keypad: nothing about the
  transport makes it a channel that identifies a person (§8.2).

### 9.2.2 API devices: reading the house, and acting on it

The endpoint of §9.2.1 was built for a keypad. It is widened into the one way
a device of the household's own — a touch display in the hall, a relay that
lights an "armed" lamp, an ESP32 or Arduino module — reads what Foyer knows
and, when it is allowed to, acts on it. Every such device is an **API
device**: declared on page 8 with `transport: http`, holding a token of its
own (§9.2.1), and allowed exactly what its **scopes** say (decision 115).

**Scopes are the device's own, and every one is off until it is switched
on.** A device never goes beyond them, whatever code is typed on it.

| Scope | Kind | What it gives |
|---|---|---|
| `status` | read | the state message of §9.2: armed or not, which scenario, countdowns, ready to arm, alarm |
| `zones` | read | every zone with its state: open, closed, in fault, excluded |
| `batteries` | read | battery levels and tamper, per zone and per device |
| `health` | read | the system health of §12: mains, notification channels, watchdog, radios |
| `log` | read | the log, paged, newest first |
| `arm` | act | arm, restricted to the scenarios and areas chosen on the device |
| `disarm` | act | disarm, restricted to the areas chosen on the device |
| `exclude` | act | exclude a zone from the next arming, and include it again |
| `acknowledge` | act | take note of an alarm or a technical alarm (§7.2) |

**Without a code, a device only reads** (decision 116). Every action needs a
code, arming included, even where the policy of §8.2 asks none: a device on
the network has no way of being the person standing in front of the panel,
and the token alone must never be what arms or disarms the house — it
crosses the network readable whenever the request is not encrypted (decision
99). The code is the identity, as on a keypad: the action is attributed to
its owner, checked against their permissions and scope, counted against the
device's lockout when it is wrong (§8.4), and refused beyond the device's own
scopes even when its owner could do more. A relay that only lights a lamp
holds `status` and nothing else. The keypads already on the endpoint keep
working as they do, under the same rule: they carry `status`, `arm` and
`disarm`, and always ask for a code.

**Each read scope is `free` or `after a code`, per device** (decision 117).
A free scope is read with the token alone. A scope after a code is read only
while the device is **unlocked**: somebody typed a valid code on it. The
default is `status` free and everything else after a code, because a device
in the hall is read by whoever walks past it, and "the back window is open"
is the sentence a burglar wants.

**The unlock** (decision 118):
- lasts as long as the device says — **from 30 seconds to 10 minutes,**
  chosen per device, two minutes by default — counted from its last use,
  and ends at once with every arming or disarming made through the device;
- is a `POST` with `action: unlock` and the code, and a wrong code counts
  against the device's lockout like any other (§8.4);
- reads only what the person whose code it was may read: `log` needs their
  `view_log`, and the names in it appear only then. A free `log` scope shows
  events with no person's name in them;
- leaves a row under `security` — which device, whose code, until when —
  because a display that shows the house after a code is a place where
  somebody read it.

**Plain HTTP stays accepted and said** (decision 119), as decision 97 does:
a module that cannot do TLS keeps working, the warning on page 8 stays, and
every row records that the request was not encrypted. Reading any scope
beyond `status` in the clear takes an explicit confirmation on page 8 — what
that scope says about the house crosses the network readable — and the
confirmation is recorded in the log. An action in the clear needs none: it
carries a code, as the keypads of decision 97 always have.

**How the data travels** (decision 120). A microcontroller has little memory,
so nothing large is pushed:

```
GET  /api/foyer/device/state                 (§9.2.1, unchanged)
→ text/event-stream: the state message on connect and on every change,
  plus one-line notices:  event: changed   data: zones | batteries | health | log

POST /api/foyer/device                       Authorization: Bearer <token>
{ "action": "arm", "scenario": "night", "code": "…" }
{ "action": "arm", "area": "garage", "code": "…" }
{ "action": "disarm", "areas": ["ground"], "code": "…" }
{ "action": "exclude" | "include", "zone": "kitchen_window", "code": "…" }
{ "action": "acknowledge", "target": "incident" | "technical", "code": "…" }
{ "action": "unlock", "code": "…" }  → { "success", "reason", "until" }
{ "action": "lock" }                 → ends the unlock at once

GET  /api/foyer/device/zones                 Authorization: Bearer <token>
GET  /api/foyer/device/batteries
GET  /api/foyer/device/health
GET  /api/foyer/device/log?before=<cursor>&limit=<≤50>
```

- The state keeps arriving on the stream, so a lamp lights the instant the
  house arms. A section is read with its own small request; the stream says
  when one has changed, and a device that does not show it ignores the
  notice.
- A section the device may not read answers `403` with a stable reason:
  `scope_not_granted`, `unlock_required`, or `plain_http_not_confirmed`. The
  §9.1 result, `last_result` and `last_reason` of §9.2 are unchanged for
  every action.
- Zone names follow the detail level of decision 83 in the stream, as they
  always have. The sections themselves carry names — they are read only by a
  device given that scope, and after a code unless the owner chose otherwise.
- The log is paged by an opaque cursor, at most fifty rows a request, and is
  the same rows the log page shows (§10), after the privacy sweeps of §10.4 —
  less the `duress` rows, which a device in the hall never shows (§8.1); a
  `duress` row sends no `changed: log` notice either.

**The contract is written down, versioned and tested** (decision 121). The
endpoint and the stream are described in `docs/api/openapi.yaml`, the MQTT
contract of §9.2 in `docs/api/asyncapi.yaml`, both at contract version `v1`.
A change that would break a device written against `v1` is a new version,
and says so in the changelog. A test in CI compares both documents with the
code — every action, field, reason and scope — so the documents cannot drift
from what the endpoint answers. What is documented is only what a device may
rely on: the panel's WebSocket commands are internal and are not.

**An API page in the panel, for administrators** (decision 122) renders
`openapi.yaml` with Swagger UI, so the contract can be read and tried from
the browser with a device token pasted in. The library is bundled with the
frontend and loaded only when that page opens: nothing is fetched from the
internet, and nothing is served unauthenticated — a public documentation page
would tell a scanner that an alarm lives on this host, which §9.2.1 already
refuses to do when no keypad uses the endpoint.

### 9.3 Arming devices, and the adapters

Every device that commands the alarm is **declared before it may** (decision
81): a `device_id` this installation does not carry is refused, whatever code
it brings, the refusal is recorded under `security`, and it is raised as a Home
Assistant notification — once per device, so a keypad configured with the wrong
name does not bury the notification that matters. The reason is narrow: the
lockout of §8.4 counts per channel *and* per device, so a caller free to invent
a device id is a caller who is never locked out.

A device is one of two kinds, and the kind decides everything that follows
(decision 84):

| Kind | Carries a code | Channel | Identity |
|---|---|---|---|
| `keypad` | yes, and the code *is* the identity (§8.2) | `keypad` | whoever typed |
| `tag` | **no** — an NFC tag, an RFID badge, a remote | `nfc` | the user it names |

A `tag` is backed by a `tag.*` or `event.*` entity and is read exactly as an
event zone is (§4.4): a new timestamp is a scan, a change out of `unavailable`
is Home Assistant restoring the last one at startup, and a device never read
before records a baseline rather than arming the house. It carries `token=True`
— possession is the credential — so the code policy cannot reach it, while the
permissions, the validity window and the scope of the person it names apply in
full.

**A tag always names a person, and validation enforces it** (decision 82).
§8.2 calls it a *per-user* NFC tag, and that is the only reason it counts as a
channel that identifies; a token nobody owns is a shared credential, which is a
keypad by another name and must be configured as one, with a code. An
anonymous tag was considered and refused: the household that wants a remote
belonging to the house rather than to a person creates a user named for the
house, with the permissions it should have — and has then said so explicitly,
instead of leaving a field blank. The editor states, where somebody is deciding
whether to carry one, the sentence this section has always made: a stolen tag
arms and disarms without knowing any code.

#### How an adapter reaches an installation

HACS installs `custom_components/` and nothing else, so a blueprint in this
repository does not arrive anywhere on its own. **Every shipped adapter
therefore carries a one-click import link** — the `my.home-assistant.io`
blueprint-import redirect, which opens the import dialogue on the reader's own
installation — in `docs/keypads.md`, which the README links. Copying the file by hand
still works and is documented beside it; it is simply not the step a reader is
asked to take first, because it is the step at which people stop.

#### Shipped adapters (blueprints)

- **Ring Alarm Keypad v2** over Z-Wave JS — full mapping including LED ring,
  beeps, exit/entry countdown and the dedicated arm-mode keys.
- **Generic Zigbee keypad** over Zigbee2MQTT — documented mapping plus a note
  that Tuya-family clones vary by firmware revision and must be verified
  individually.
- **NFC tag / remote** via `tag` and `event` entities — including the security
  note that a stolen tag arms and disarms without knowing any code.

### 9.4 Automatic arming rules

Presence-driven arming is a genuine channel — the system acts as a user would —
so it lives here, with `channel: auto_rule` and the rule's name recorded on every
event. It is a **closed rule model**, not an automation engine: the same boundary
drawn in §6.3 applies.

#### Rule model

| Element | Options |
|---|---|
| **Trigger** | `absence` — every selected person `not_home` for N minutes · `presence` — a selected person arrives · `time` — at HH:MM on chosen weekdays · `entity` — an entity holds a state for N minutes |
| **Action** | arm a scenario · disarm named areas · switch to another scenario |
| **Active window** | weekdays plus a time range; the rule simply does not exist outside it |
| **Guards** | only if currently disarmed · only if every zone is ready · only if no interior zone has detected motion for N minutes |
| **Grace period** | an actionable notification with a countdown and a **Cancel** button before the action runs (default 120 s for arming, 0 for disarming) |
| **Open zones** | off by default: arming fails while a zone is open, and the rule arms by itself the moment it closes · on: arm anyway, **excluding the open zones that are bypassable** (decision 126) |
| **Suspension** | until a date and time · skip the next occurrence only · a global switch |

#### When the house is not ready

Everybody has left and the bathroom window is open. The rule does not force
anything nobody chose, and it does not stay quiet either:

- **The countdown names the open zones** (decision 125): "Empty house: arming
  Away in 2 minutes — Bathroom window is open, and it cannot arm until it is
  closed", or "…and it will be excluded" when the rule excludes open zones.
  Zone names already leave the house in every alarm notification; this adds
  nothing new to what a phone receives.
- **The rule's contacts are told the outcome** (decision 124), through quiet
  hours, because the house is uncovered: "not armed — Bathroom window is
  open; it will arm by itself when you close it", then "armed now —
  Bathroom window was closed" when it does; or "armed, excluding Bathroom
  window" when the rule excludes open zones. The words follow what actually
  happened, never what was planned. A rule triggered by an instant — a time,
  an arrival — has one turn: refused, it says it will not try again until
  its next time, and does not (decision 127). An arming the rule started
  that fails when its exit delay ends is told as well.
- **Excluding open zones is the rule's own opt-in** (decision 126), off by
  default and warned about when switched on: it is a forced arming nobody
  typed a code for. It excludes only zones that are open **and** bypassable;
  a zone that may not be bypassed, or one in fault or unavailable (INV-4: a
  fault is never "all quiet"), still refuses the arming. What it excludes
  is watched again the moment it closes, as a forced arming's is, and
  the log records a `forced_arm` with the rule's name. It covers what is open
  when the rule arms and nothing after: a zone that opens during the exit
  delay fails the arming as it always does.

#### The asymmetry between arming and disarming

These two are not equally safe and the product must not pretend they are.

**Automatic arming** carries a moderate, manageable risk: a flat phone battery or
a dropped Wi-Fi connection can make the system believe the house is empty and arm
it with someone inside. The guards above plus the cancellable grace notification
reduce this to an annoyance.

**Automatic disarming on presence is a genuine security hole**, and it is why
professional systems do not offer it. Presence in Home Assistant is inferred from
a phone: a stolen phone disarms the house, GPS drift of 200 metres disarms the
house, a cloned MAC address on the home network disarms the house. This is not
theoretical — it is the most banal attack against a DIY alarm.

The chosen position, which the implementation must enforce rather than merely
document:

1. Automatic **arming** is fully supported.
2. Automatic **disarming** exists but is **disabled by default**, and enabling it
   raises an explicit warning in the UI naming the attack above. The setting
   cannot change while any area is armed (§15.1); a phone lost while the house
   is armed is answered by `switch.foyer_auto_arming`, a suspension, or
   switching the rule off, none of which is refused.
3. Automatic disarming can only target areas where `is_perimeter` is false. **A
   perimeter area is never disarmed by a rule.** Whoever walks in on a stolen
   phone still finds every external door and window protected. This is a hard
   constraint in the engine, not a UI default the user can talk their way past.

A regression test must assert point 3 directly: a disarm rule naming a perimeter
area produces a `Decision` that does not disarm it.

#### Suspension, and the boiler engineer

The recurring real-world case: the house will be empty tomorrow morning, but a
technician is being let in remotely. Auto-arming would arm the house around them.
Two mechanisms, both cheap, and both wanted:

- **Rule suspension** — suspend a named rule until a date and time, or skip its
  next occurrence. Three clicks from the panel or the card.
- **Expected visitor window** — a first-class concept: a named window
  (`09:00–13:00 tomorrow · "Boiler engineer"`) during which automatic arming is
  suspended, optionally applying a reduced scenario instead (perimeter only, say).
  Mechanically it is the same suspension; the difference is that in six months the
  log says *why*, which a bare "rule suspended" never will.

#### Entities and logging

- `switch.foyer_auto_arming` — global kill switch, so the whole mechanism can be
  driven from a dashboard, an automation or a keypad.
- `sensor.foyer_next_auto_action` — what will happen next and when, with the rule
  name and any active suspension as attributes.
- Every rule evaluation that *acts* is logged under `arming` with
  `channel: auto_rule`; every rule that was *blocked by a guard* is logged under
  `system`, because "why did it not arm last night?" is a question users ask.
- Cancelling a grace countdown is logged with the user who cancelled.

### 9.5 Hardware guidance (documentation)

`docs/keypads.md` compares Ring Keypad v2 (most complete, needs a Z-Wave stick,
English legends, patchy availability in Europe), Zigbee keypads with RFID
(cheap, firmware quality varies sharply between clones), Frient/Develco (solid,
fewer keys), wall tablets (rich UI, always-on cost), NFC tags (≈1 €, and the only
cheap channel that identifies the user) and DIY ESPHome builds (community links,
not maintained by this project in v1).

---

## 10. Event log

### 10.1 Storage

Dedicated SQLite database, independent of Home Assistant's recorder — whose
default purge of 10 days would otherwise silently destroy the 30-day requirement.

```sql
CREATE TABLE events (
  id           INTEGER PRIMARY KEY,
  ts           INTEGER NOT NULL,        -- epoch ms, UTC
  category     TEXT NOT NULL,
  event_type   TEXT NOT NULL,
  severity     TEXT NOT NULL,           -- info | warning | alarm
  area_id      TEXT, zone_id TEXT, scenario_id TEXT,
  incident_id  TEXT,                    -- §5.6: every row of one night's alarm
  user_id      TEXT, user_name TEXT,    -- name denormalised: survives user deletion
  channel      TEXT, device_id TEXT,
  outcome      TEXT,                    -- ok | blocked | bad_code | failed
  detail       TEXT                     -- JSON
);
CREATE INDEX idx_ts ON events(ts);
CREATE INDEX idx_cat_ts ON events(category, ts);
CREATE INDEX idx_area_ts ON events(area_id, ts);
CREATE INDEX idx_user_ts ON events(user_id, ts);
CREATE INDEX idx_incident ON events(incident_id);
```

`user_name` is denormalised on purpose: deleting a user must not erase the
history of what that user did.

### 10.2 Categories and default verbosity

| Category | Typical volume/day | Default |
|---|---|---|
| `arming` — arm, disarm, scenario change, who/where/outcome | tens | **on** |
| `alarm` — entry, trigger, escalation, acknowledgement | few | **on** |
| `action` — every action executed, with success or failure of the service call | tens | **on** |
| `config` — who changed what, with a diff summary | few | **on** |
| `security` — bypass, failed codes, lockout, duress, forced arm | few | **on** |
| `system` — zone fault, low battery, HA restart, restart gap, walk test | few | **on** |
| `zone_armed` — zone state changes while armed | hundreds | **on** |
| `zone_disarmed` — zone state changes while disarmed | **thousands** | **off** |

The last row is the trap: a living-room PIR produces thousands of transitions a
day. Logging them for 30 days buries every event that matters. It stays
disableable and is meant to be switched on only while diagnosing. A chime is
filed there too: it sounds exactly when a zone opens unmonitored, which is the
same volume class.

A **refused** request is a row of its own, in the category of the request —
`arm_rejected` under `arming`, `bypass_rejected` under `security` — carrying
the reason and the blocking zones. "Why did it not arm last night?" is a
question users ask, and silence is the worst possible answer.

### 10.3 Retention and export

Retention is configurable per category, 30 days for every category by
default, with a purge task on a daily schedule. A category that is switched
off writes nothing from then on; the rows it has already written stay until
their days are up. Export produces CSV or JSON honouring the currently applied
filters. Deleting the log is an `edit_config` operation and is itself logged —
though `docs/security-model.md` must state honestly that an HA admin with
filesystem access can delete the database outright, so the log is
audit-*useful*, not tamper-*proof*.

Every log write also emits a Home Assistant event (`foyer_event`) so external
log collectors and user automations can subscribe. The SQLite store remains the
source of truth for the panel.

### 10.4 Personal data in the log

*Practical information, not legal advice.*

The log records who was in the house, when they arrived and when they left, for
thirty days. That is personal data about **everyone in the household**, not only
about whoever installed the system.

Under GDPR the **household exemption** (Art. 2(2)(c)) covers processing for
"purely personal or household activity", and a family's own alarm log falls inside
it. **It stops falling inside it the moment the log records somebody else** — the
cleaner whose arrivals and departures are kept for a month, the boiler engineer,
the babysitter. It does not apply at all to the B&B, holiday let or small office
installations that will certainly appear once this is published.

There is also an internal tension to resolve: `user_name` is denormalised into
every row (§10.1) *specifically* so that deleting a user does not erase the
history of what they did. That is right for audit and wrong for erasure, so the
two operations must be separate.

| Capability | Behaviour |
|---|---|
| **Delete a person's history** | A distinct action from "delete user". Removes or pseudonymises that person's rows while leaving the events themselves intact, so the record of *what happened* survives the removal of *who* |
| **Timed pseudonymisation** | Optional and off by default: after N days, rows keep a stable opaque identifier instead of a name. Data minimisation applied automatically rather than on request |
| **Export one person's data** | Their rows in a readable format, for a subject access request |
| **Retention** | Already per category (§10.2), with a short preset offered for installations with domestic staff |
| **Documentation** | `docs/privacy.md` explains what the log contains, the household exemption, and when it stops applying |

The UI must state plainly that timed pseudonymisation trades away the ability to
answer "who disarmed that night" for rows older than N days — which is the very
question the log exists to answer. It is a real trade, not a free safety feature.

---

## 11. Test and simulation

Four distinct features, sharing one page with four tabs.

### 11.1 Live zone diagnostics

Table of every mapped zone: friendly name, backing entity, live state, resolved
trigger evaluation (would this count as triggered right now?), last state change,
availability, battery level, signal quality where exposed, supervision status,
and a "blocks arming" flag. Answers the most common post-installation question:
*am I actually looking at the right sensor, and does it work?*

### 11.2 Simulator

The differentiating feature. The user:

- sees all real zones and overrides their states **virtually**,
- picks a hypothetical scenario and a hypothetical date/time,
- optionally overrides the states of entities used in conditions,
- runs the simulation.

Output is the full decision chain, step by step:

```
19:32  Zone "Kitchen window" → open
       Area "Ground floor" is armed (scenario: Night)
       Zone type: delayed → entry delay 30s starts
20:02  Entry delay expired, no disarm
       → state: triggered
       Effective profile: "Full" (inherited from area "Ground floor")
       Actions evaluated:
         ✓ siren.indoor            (no conditions)
         ✓ light.hall  flash       (condition: time 22:00–07:00 → NOT MET, skipped)
         ✓ notify → Luca (push)    escalation step 0
         ⏱ escalation step 1 at +60s → Luca (SMS)
         ⏱ escalation step 2 at +120s → Partner (push) + voice call Luca
```

**Nothing is executed.** This is guaranteed structurally by INV-1: the simulator
calls the same `decide()` the runtime calls, with a fabricated snapshot and a
fabricated clock, and simply never hands the `Decision` to the executor.

A code given for a rehearsal is checked like any other. A duress code raises
`duress` for the request that carried it (§8.1), and the rehearsal then runs
as the ordinary code would: a trace that showed it would put it on the screen
the code was typed at.

Every simulation run is logged (category `system`) with its inputs, so a
configuration change can be justified after the fact.

### 11.3 Walk test

Every disarmed area that can arm is genuinely armed — whoever started the
test, whatever their `allowed_area_ids` — and zone states are genuinely real,
but **all actions are inhibited**, in every area: an area already armed when
the test began stays armed, and does not answer either until the test ends
(§8.3). The user walks the house and the panel records, live, which
zones detected them — highlighting zones that never reacted. This is the only way
to find a misaimed PIR or a dead battery before it matters.

Mandatory safeguards:

- an automatic exit, not disableable: 15 minutes without a detection by
  default (1–60), and never later than three hours after the start (§5.3),
- a permanent, unmissable banner in the panel and on every card while active,
- entry and exit logged with the user who started it,
- a notification on start and on end,
- `always_on` zones (tamper, technical, panic) remain **fully live** — walk test
  must never silence a smoke detector.
- an incident already open when the test began stays live: its sounders, its
  cutoff and its escalation carry on, because nothing that belongs to an
  incident is held back. It does not grow: an ordinary zone that trips during
  the test is recorded as a walk detection, not as a zone joining it.
- a `duress` occurrence (§8.1) is never held back, whether the duress code
  started the test, ended it or disarmed during it: a walk test inhibits the
  house, not a person asking for help. It is silent by definition, so it
  cannot spoil the walk (decision 132).
- **No arming while it runs.** Its end disarms the areas the test armed,
  except one in alarm or holding its memory, which only a person's disarm may
  end, and leaves every other area as it found it. An arming accepted during
  the test would either be undone by that end or answer nothing until it, so
  it is refused, with its own reason, until the test has ended (decision
  107).
- **A walk test does not arm an area holding alarm memory.** Such an area is
  not armed by the test, and keeps its memory: the test arms for a walk, not
  for a watch, so it is not the arming that clears it (§5.2). Its own
  `alarm_cleared` would be held back with every other action, and the end of
  the test would read the memory as an alarm still in progress. Its zones are
  still walked (decision 141).

### 11.4 Real action test

A test button next to every action and every contact channel: sound the siren for
three seconds, actually send the test push, actually place the test call. It
really executes, so it requires explicit confirmation, requires the
`test_actions` permission, and is logged as a test. This prevents the worst
possible discovery — that the emergency channel was misconfigured, found out
during the emergency.

---

## 12. System health and resilience

An alarm that cannot tell you it has stopped working has stopped working. This
section is the answer to the failure modes that silently defeat every DIY alarm:
the power goes out, the notification channel breaks, or Home Assistant dies.

**System health is a separate concept from zones.** "The mains are down" is not an
intrusion and must not enter the intrusion queue (§5.6) — it belongs alongside the
technical channel (§5.5), as a condition of the system itself.

### 12.1 Mains power and UPS

A UPS exposed over NUT, or a smart plug, already provides a `binary_sensor` for
mains failure. Foyer reads it as a system-health input chosen on page 14, not
as a zone, so this costs almost no code — what it needs is the **concept**: a
mains failure raises `system_power_lost`, notifies immediately, is logged,
and can drive a response profile. It never opens an incident. It must never
be confused with a quiet night.

Documented alongside it in `docs/resilience.md`: a burglar cuts the power. Without
a UPS on the router, every internet-dependent notification channel dies with it,
which is why §7.3 recommends a local GSM channel.

### 12.2 Notification channel health

Foyer periodically verifies that every configured channel is still real:

- the `notify.*` service still exists in the service registry (integrations get
  removed, renamed, or fail to load after an update),
- the GSM modem is present and registered on the network,
- the last send actually succeeded.

A broken channel is surfaced on the Contacts page and, when it participates in an
escalation policy, **announced through a different channel**. Warning you about a
dead channel over the dead channel is the joke that writes itself.

### 12.3 External watchdog

Foyer periodically calls a **configurable URL** — works with healthchecks.io,
Uptime Kuma, Cronitor or any endpoint, tied to no vendor. If Home Assistant dies,
crashes or loses connectivity, the pings stop and the external service raises the
alarm. It is the only answer to the fundamental problem that a dead system cannot
report its own death.

Three rules:

- **The heartbeat carries no data by default.** A ping saying "armed, Night,
  nobody home" would be a channel telling a third party exactly when the house is
  empty. An optional payload may be offered, off by default, behind an explicit
  warning.
- **Foyer watches the watchdog.** Repeated failures to reach the endpoint are
  themselves reported locally: being unable to reach the internet means no
  internet-based notification would go out either, and the panel should say so.
- **The URL is a credential, written and never read back** (decision 130).
  Whoever holds a ping URL can keep the check green for ever, which silences
  the one thing that reports Foyer's own death. No API returns it — the panel
  included, which anybody holding `edit_config` reads without a code — and the
  panel says only whether one is set. A save that leaves the URL out, or
  sends it empty, keeps the stored one rather than clearing it; a new URL
  replaces it; switching the watchdog off keeps it too. An error is stored
  with the URL taken out.

Documented limits, so they do not arrive as issues: a watchdog hosted on the same
infrastructure dies with it and protects nothing; and the external service cannot
distinguish "Home Assistant is down" from "the line is down" — which is fine,
because both mean the alarm can no longer call you.

Pleasing consequence, combined with §12.1: a power cut kills Home Assistant *and*
the router, the heartbeat stops, and the external service tells you — which is how
you find out, from somewhere else, that the power went out at home.

### 12.4 Repairs and diagnostics

- Persistent problems — a zone unreachable for days, a broken notification channel,
  a watchdog that has never succeeded — are raised as **Home Assistant repair
  issues**, so they appear in Settings where a user sees them without opening the
  Foyer panel.
- Home Assistant's standard **download diagnostics** button produces an anonymised
  dump of configuration and state: no codes, no hashes, no credentials — the
  webhook id, the watchdog URL, a device's token — no personal names, entity
  ids redacted to stable placeholders. This is what turns a GitHub issue
  into something answerable instead of five rounds of questions.

### 12.5 RF interference detection

Neither Zigbee nor Z-Wave lets Home Assistant measure jamming directly. But
jamming has an unmistakable signature: **many zones on the same radio go
unavailable within seconds of each other.**

One sensor going quiet is a flat battery. Eight going quiet in the same minute is
a radio event.

```
if  N or more zones sharing one radio integration
    become unavailable within T seconds
    and the coordinator itself is still reachable
then raise rf_interference_suspected
```

| Parameter | Default | Notes |
|---|---|---|
| `n_zones` | 4 | or 40% of the zones on that radio, whichever is lower |
| `window` | 60 s | |
| Scope | per radio integration | Zigbee and Z-Wave counted separately; a Zigbee outage says nothing about Z-Wave |

**The coordinator check is what makes this useful rather than noisy.** If the
coordinator entity is itself unavailable, this is a coordinator or network failure,
not interference, and it is reported as such. A PoE coordinator dies with its
switch; that is a different fault with a different fix, and conflating the two
would teach the user to ignore both.

Response depends on arming state, as in professional panels, where jamming is
treated as a tamper condition:

| State | Response |
|---|---|
| Armed | Alarm-grade: raises an incident-capable event a response profile can act on |
| Disarmed | Warning: notification, log entry, repair issue |

On an armed house the radios and the thresholds — the zone count, the window
and the time a suspicion must last before it is raised — decide whether an
incident opens, as a zone's trigger does, so they cannot change while any area
is armed (§15.1). The mains, the watchdog and the channel checks never open
an incident, and stay free.

One rule that is easy to miss and that defeats the whole feature if missed:
**notify over a channel that does not depend on the affected radio.** Announcing a
Zigbee blackout through a Zigbee siren is not a notification.

**Stated honestly in the documentation:** this is a heuristic, not jamming
detection. A coordinator crash, a firmware update, a Zigbee channel change or a
power cut to a room full of mains-powered routers all produce the same signature.
That is why the event is called *suspected*, and why its first line reports how
many zones, on which radio, and whether the coordinator is still answering —
enough for the user to tell the cases apart.

## 13. Home Assistant entities exposed

| Entity | Per | Purpose |
|---|---|---|
| `alarm_control_panel.foyer_<area>` | area | real area state; arms and disarms that area. Whether a code is needed is Foyer's answer (§8.2) |
| `alarm_control_panel.foyer_master` | 1 | aggregated state, reports the active scenario's `ha_master_state`; the surface voice assistants and HomeKit see |
| `select.foyer_scenario` | 1 | active scenario by name; the persistent record of *which* scenario is running |
| `binary_sensor.foyer_zone_<zone>` | zone | normalised zone state (`on` = triggered), with attributes for bypass, fault, last trigger |
| `binary_sensor.foyer_ready_to_arm` | 1 + per area | whether arming would succeed right now |
| `binary_sensor.foyer_fault` | 1 | any zone in fault |
| `sensor.foyer_open_zones` | 1 | count, with the list as an attribute |
| `sensor.foyer_last_event` | 1 | last significant event, for dashboards — never a `duress` (§8.1) |
| `sensor.foyer_countdown` | per area | remaining exit/entry seconds |
| `button.foyer_acknowledge` | 1 | acknowledge an ongoing escalation. Acknowledging needs no code by default (decision 77), so the button exists; it honours the policy and refuses when an installation has raised it |
| `switch.foyer_walk_test` | 1 | walk test on/off, reflecting the timeout |
| `binary_sensor.foyer_technical_alarm` | 1 | the technical channel (§5.5), independent of arming |
| `sensor.foyer_technical_cause` | 1 | which technical zone is in alarm |
| `sensor.foyer_incident` | 1 | the open incident id, with contributing zones and severity as attributes |
| `switch.foyer_chime` | 1 | chime on/off (§6.6) |
| `switch.foyer_auto_arming` | 1 | global kill switch for automatic rules (§9.4) |
| `sensor.foyer_next_auto_action` | 1 | what will happen next and when |
| `binary_sensor.foyer_rf_interference` | per radio | correlated unavailability suspected on that radio (§12.5) |
| `binary_sensor.foyer_system_health` | 1 | any of: zone fault, mains lost, broken notification channel, watchdog unreachable — with the causes as attributes |

Master aggregation rule: `triggered` if any area is triggered; else `entry` if any
is in entry; else `arming` if any is arming; else `armed` if **any** area is armed
(a partially armed house is not a disarmed house); else `disarmed`.
When the result is `armed`, the master reports the active scenario's
`ha_master_state` only while exactly that scenario's areas are armed; any other
armed set — an extra area armed on its own, or one of the scenario's areas
that failed to arm — is reported as `armed_custom_bypass`. The exact scenario
is always on `select.foyer_scenario`.

**What the panels tell Home Assistant about codes** (decision 136).
`code_arm_required` is one answer for everybody, and Home Assistant acts on it
before Foyer sees the request: while it is true, a codeless arming is refused
by Home Assistant itself. So it is false while any enabled user has the
exemption of §8.2 switched on: Home Assistant then passes every arming on, and
the backend answers it, `code_required` included, with the log's row for a
refusal (INV-2). Otherwise it is true when an arming the panel offers asks a
code to arm — for the master, as soon as one mode it can still arm asks
(decision 143) — so Home Assistant's more-info dialog and tile buttons, which
ask for a code only when it is true, keep asking. The price is known: a mode
of the master that needs no code is then refused by Home Assistant until a
code is passed, from an automation too, which arms it through Foyer's own
service instead. A panel refusing a codeless arming for lack of a code says
where one can be typed: Foyer's card, the panel, and Home Assistant's alarm
panel card while the panel is disarmed — that card offers arming only then.
`code_format` follows the policy, and the master's reads every area and
scenario as well as the global default, so the alarm panel card keeps its
field wherever a code may be asked. The voice assistants read the same
attribute: while it is false Alexa is offered the panel and Google Assistant
stops asking for its PIN before arming, still sending the PIN it keeps.

---

## 14. Services and events

### 14.1 Services

`foyer.arm` · `foyer.disarm` · `foyer.bypass_zone` · `foyer.unbypass_zone` ·
`foyer.acknowledge` · `foyer.walk_test` · `foyer.test_action` ·
`foyer.simulate` · `foyer.export_log` · `foyer.export_config` ·
`foyer.import_config`

Every state-changing service accepts `code`, `user_id`, `channel`, `device_id`
and returns a structured result (§9.1).

### 14.2 Events

`foyer_event` carries every logged event, so automations can subscribe with a
single trigger and filter on `category` / `event_type`. Documented event types
mirror the trigger moments in §6.1.

---

## 15. Frontend

### 15.1 Panel pages

| # | Page | Content |
|---|---|---|
| 1 | Overview | State of each area, active scenario, not-ready zones, recent events, quick arm/disarm |
| 2 | Areas | Create areas, assign zones, area defaults and code policy |
| 3 | Zones | Filterable list + zone detail: entity, type preset, trigger spec, delays, arm policy, bypass, profile, supervision, the zone's cameras |
| 4 | Scenarios | Create scenarios, choose areas, HA state mapping, default profile, allowed users |
| 5 | Response profiles | Profiles, action list, per-action conditions, escalation steps |
| 6 | Contacts | Address book, prioritised channels, quiet hours, escalation policies, per-channel test, the acknowledgement webhook — its address shown once (§7.2) |
| 7 | Users & codes | Users, codes, permissions, area/scenario scope, validity, duress code, per-user policy |
| 8 | Arming devices | Keypads, NFC tags, remotes; MQTT mapping or the device endpoint and its token (§9.2.1); feedback configuration |
| 9 | Test & diagnostics | Four tabs: diagnostics · simulator · walk test · action test |
| 10 | Log | Filter by date, area, zone, user, category, outcome; CSV/JSON export |
| 11 | Settings | Global defaults, siren duration and cutoff, log retention per category, the language of the messages Foyer sends out, config backup/restore |
| 12 | Automation rules | Presence and time rules (§9.4), guards, grace period, suspensions and expected-visitor windows, next scheduled action |
| 13 | Verification groups | N-of-M groups (§4.8): members, threshold, window, group profile |
| 14 | System health | Mains power, notification channel health, watchdog status and settings (its URL written, never read back, §12.3), faults, diagnostics download (§12) |

Plus a **first-run wizard**: create the first area → map three zones with
confirmed trigger specs → create one scenario → create one user with a code →
send a test notification. An empty panel on first open is how projects lose users
in the first five minutes.

**A code typed in the panel is kept for a short while and then forgotten**
(decision 114): so that twenty saves do not ask for it twenty times, and so
that the unlocked wall tablet INV-6 names does not keep it for whoever comes
next. It is forgotten after two minutes unused, after every arming or
disarming, and when the panel is closed. The card keeps no code at all
beyond the command it was typed for.

**An armed house keeps the answer and the codes it was armed with**
(decision 138). While any area is not disarmed, an edit that would change how
the house answers an alarm, or what it asks a code for, is refused and says
why. Refused, besides the armed areas themselves, their zones and groups and
the scenario that is running:

- the siren duration, the global `arm_hold_timeout`, the default entry and
  exit delays and the walk test's auto-exit window (§5.3);
- the default and technical profiles, the silent list and the camera folder;
- every profile an armed area could answer with — its own, its scenario's,
  its zones' and groups', the default, the technical channel's and its
  zones', and the one an escalation is running;
- every contact such a profile names, which can be neither changed, switched
  off nor deleted (§7.1);
- the code policy, the code length and the lockout, and what any area or
  scenario asks a code for — a disarmed area and a scenario that is not
  running included, because the strictest-wins rule of §8.2 reads them for a
  command that touches the armed area (decision 142);
- whether a rule may disarm (§9.4);
- the radios and thresholds that decide whether interference opens an
  incident (§12.5).

Otherwise whoever holds `edit_config` could lower the guard of a house nobody
disarmed, and nothing in the log would read as a disarm. What does not change
the answer stays free: the language of messages, the log and its retention,
personal data in the log, the chime, the battery threshold, the backup
download, the mains, the watchdog, the channel health checks and how long a
problem lasts before it becomes a repair issue, and whether the first-run
wizard is done.

**Who may command the house stays editable while it is armed** (decision
139). A person, their code, their permissions and exemption, a tag, a keypad,
its token and its scopes, an API device, the MQTT settings, the
acknowledgement webhook and the automatic rules can be added, changed or
revoked: taking a guest's code or a lost phone's rule away from the other
side of the world is the edit an armed house needs most, and the recovery of
§8.2 writes a person too. Every command they carry still meets the code
policy, and changing that policy is among the edits refused above. The one
refusal among them is an edit that would leave nobody holding a usable code,
because §8.2 then switches the whole policy off — the policy changed by
another route. A key switch's person and a running scenario's list of people
wait for the disarm with the zone and the scenario they belong to; the person
themselves can be disabled at once. A disarmed area can still be programmed
while others stay armed, except what it asks a code for.

**Config backup/restore** (JSON export/import) is not optional: nobody who has
configured forty zones will do it twice. The exported document carries its
schema version: a restore migrates an older one through the same steps a real
upgrade uses, refuses one written by a newer major version rather than reading
it half-way, and then goes through validation and the guard above like any
other edit: while an area is armed it is refused exactly where the same change
made on its own page would be. The download is never refused for an armed
area; it asks for `edit_config` and the code, as it always has. A restore that
adds, removes or changes a person, a tag, or the person a key switch acts as
needs `manage_users` as well as `edit_config`, as the Alarmo importer's does:
otherwise `edit_config` was a way to hand oneself every permission, or
somebody else's key (decision 111).

**The language setting is not the panel's.** The panel follows each Home
Assistant user's own language, so a second selector for it would be a bug
generator. What it sets is the language of what Foyer *sends out* —
notifications, the zone name the chime speaks — which the house has one of
even when the phone reading it does not (decision 73).

### 15.2 Contextual help

Every panel page opens with a collapsible **"About this section"** panel above its
content. This is not decoration: an alarm panel has settings whose effect is not
guessable from their label (`arm policy`, `follower`, `cross-zone`, `supervision
timeout`), and a user who guesses wrong finds out during a burglary.

| Aspect | Decision |
|---|---|
| Content | One short paragraph on what the section does, then a compact list — one line per setting — saying **what changes if you change it** |
| Source | `translations/panel/<lang>.json` under `help.<page>`, next to the file Home Assistant itself reads, so it follows the Home Assistant user's language automatically and a translator gets it with no extra machinery. Not in `translations/<lang>.json`: hassfest validates that file against a closed schema and rejects a top-level `help` key (decision 35) |
| State | Expanded on first visit, then remembers the user's choice **per Home Assistant user** (stored in Foyer config, not `localStorage`) so it follows them from desktop to wall tablet. **Except the Overview**, which starts collapsed: it is the page opened to arm or disarm in a hurry, and on a phone the help pushed the controls off the screen (decision 113) |
| Global toggle | A `?` button in the panel toolbar shows or hides every help panel at once |
| Deep link | A "Learn more" link to the matching page under `docs/`, in the panel's language when that page has a translation (`<page>.it.md`), in English otherwise. A page gets its link when its document exists, never before: a link that 404s is worse than none (decision 149) |

Division of labour: the help panel explains the **section**, the hint under a
field explains the **field**. Neither repeats the other.

Cost to accept knowingly: this roughly doubles the translation surface, and every
behavioural change now has to be reflected in two English strings and two Italian
ones as well as in `docs/`. The mitigation is a hard brevity rule — two or three
sentences plus the list, with everything longer living in `docs/` behind the link.
Help text that outgrows the panel is a sign the setting itself is too complicated.

### 15.3 Card

One custom card, `foyer-card`, with a `layout` option:

| Layout | Content |
|---|---|
| `full` | Area states, scenario selector, keypad, not-ready zone list, countdown |
| `compact` | State + arm/disarm + scenario dropdown |
| `badge` | Colour-coded state only, for embedding in existing dashboards |
| `keypad` | PIN pad only, for a wall tablet |

Requirements: a visual editor, correct behaviour in both HA themes, a visible
countdown during exit and entry delays, clear feedback on rejection (wrong code,
blocked by zone X, locked out), and an unmissable walk-test banner. The card
never decides anything (INV-2); it sends the code and renders the result.

---

## 16. Roadmap

Each phase produces something installable and usable. No phase anticipates the
next one's features.

### Phase 0 — Walking skeleton (de-risk the stack)

Prove the full technical chain end to end with the minimum possible code:
one hard-coded area, one zone, one scenario, one action.

- Integration loads via a config flow; `.storage` config read and written.
- `core/engine.decide()` exists as a pure function with a real unit test.
- One `alarm_control_panel` entity arms and disarms.
- Sidebar panel registers with the final icon (§17), builds, loads, and reads live
  data over the WebSocket API.
- `foyer-card` renders state and sends an arm command.
- The `translations/` mechanism works end to end in `en` and `it`, including one
  `help.<page>` entry, so no English string is ever hard-coded into a component.
- CI: pytest + lint + frontend build.

**Acceptance:** installable from a local HACS repo; arming from the card changes
the entity state and the panel reflects it live.

### Phase 1 — Alarm core

Zones (all 8 type presets with editable properties), areas with independent
state, scenarios, the complete state machine with delays, arming preconditions
and bypass, response profiles with inheritance and the two conditions, the action
catalogue including `call_service`, state persistence across restart, the SQLite
log with its categories, panel pages 1–5 and 10–11 each with its help panel
(§15.2), the first-run wizard, card layouts `full` and `compact`.

Also in Phase 1, because each of these touches the state machine and retrofitting
them later means reworking it: the **technical alarm channel** (§5.5), the
**incident model** with profile severity (§5.6), **verification groups** and the
cross-zone field built on them (§4.8, panel page 13), **chime** (§6.6),
`arm_after_closing` as an arm policy, per-scenario siren duration, and
**timed temporary bypass** — excluding a zone for a set duration, with automatic
return and notification, because a zone excluded and forgotten is exactly the
window somebody will come through.

**Acceptance:** a real house can be protected with it.

### Phase 2 — Security and arming channels

Users, bcrypt codes, permissions, per-user and per-operation code policy, duress
code, lockout, the service and MQTT contracts with structured results, the Ring
Keypad v2 and generic Zigbee blueprints, NFC tag and remote support, panel pages
7–8, card layouts `badge` and `keypad`.

**Acceptance:** arming and disarming from a physical keypad with correct feedback,
with the log attributing every action to a person and a channel.

### Phase 3 — Test and simulation

Live diagnostics, the simulator with its full decision trace, walk test with its
safeguards, real action testing, panel page 9.

**Acceptance:** a user can verify a forty-zone configuration without triggering
anything.

### Phase 4 — Contacts and escalation

The contact address book with prioritised channels, escalation policies,
acknowledgement across all four paths, quiet hours, `escalation_exhausted`
handling, panel page 6, the notification-channel recipe documentation.

Automatic arming rules (§9.4) land here too, not earlier: the cancellable grace
countdown is the same actionable-notification machinery that acknowledgement
needs, and building it twice would be waste. Includes the guards, suspensions,
expected-visitor windows, `switch.foyer_auto_arming`,
`sensor.foyer_next_auto_action` and panel page 12.

**Acceptance:** an unacknowledged alarm escalates from push to SMS to voice call
across multiple people, and stops the instant someone acknowledges. An empty house
arms itself after the configured delay, announces it first with a cancellable
countdown, and skips the morning the boiler engineer is expected.

---

### Phase 5 — Hardening and release readiness

Not features: the difference between a repository and something a stranger can
rely on.

- **System health** (§12) in full: mains power, notification channel health, the
  external watchdog, RF interference detection including the rule that its
  notification must not route through the affected radio, repair issues,
  anonymised diagnostics, panel page 14.
- **Privacy tooling** (§10.4): targeted history deletion, optional timed
  pseudonymisation, per-person export, `docs/privacy.md`.
- **Clean uninstall**: entities removed from the registry, timers stopped, MQTT
  subscriptions closed, and the user explicitly asked whether to keep or delete
  the log database. Without it, ghost entities and an orphaned SQLite file are
  left growing in the configuration directory.
- **Alarmo import** (§20.2).
- **Contributor infrastructure** (§20.3).
- **Zone cameras and the device endpoint** (§6.2.1, §9.2.1), added after the
  third part and before the documentation, so that the documents describe
  them rather than being rewritten for them.
- **API devices and the API contract** (§9.2.2): scopes, reading the house,
  the unlock, `docs/api/`, and the API page. Before the documentation, for
  the same reason (decision 123).
- **The disclaimers, last of all** (§20.4). The wording that says what this is
  and what it is not, everywhere somebody meets it rather than only in the
  licence — agreed, and accepted with a tick before setup (decisions 150–155).

**Acceptance:** a person who has never spoken to the author can install it, hit a
problem, and produce an issue that is answerable.

## 17. Visual identity

The mark extends the existing **Foyer** symbol — three nested arches receding into
the distance, a lit arched doorway, a threshold line — by enclosing it in a
shield. Direction: *shield frame*, chosen for immediate legibility as a security
product, which matters more for a project nobody has heard of yet than an internal
geometric echo would.

| Token | Value | Role |
|---|---|---|
| Ink | `#0D1014` | Ground on dark, stroke on light |
| Paper | `#E8ECF2` | Stroke on dark, ground on light |
| Amber | `#F0A835` | The doorway — the only warm, filled element |

Amber never inverts. On a light ground the wordmark flips to ink and the amber
shifts only to `#B4780F` for contrast; the doorway stays amber in every colour
rendition.

### 17.1 Asset set

| File | Where it appears | Constraint |
|---|---|---|
| `foyer-hd-icon.svg` | The `foyer:shield` icon, for dashboards | **24 px, single colour, `currentColor`.** No gradient, no fill colours, no opacity ladder — a *separate drawing*, carrying the shield outline, one arch and a solid doorway. The faded arches vanish at this size, so they are not in this file. **Not the sidebar icon:** see below |
| `foyer-hd-symbol-dark-bg.svg`<br>`foyer-hd-symbol-light-bg.svg` | Panel header, card header, loading state | Full colour, transparent ground, 32 px and up |
| `foyer-hd-app.svg` → `foyer-hd-app-512.png`, `-192.png` | HACS listing, repository social preview, favicon | Dark rounded tile, symbol scaled to 0.84 for a proper safe margin |
| `foyer-hd-lockup-dark-bg.svg` / `-light-bg.svg` (+ PNG) | README header, documentation | Two files, not one recoloured |

### 17.2 Rules that keep it coherent

- **The sidebar panel icon is an mdi icon**, `mdi:shield-home`, and this is a
  concession, not a preference (decision 74). A custom icon set is registered
  by a JavaScript module; Home Assistant resolves a custom icon exactly once,
  and when the sidebar draws before that module has run — which is what the
  companion app does when it starts from a cached page — it falls back to a
  legacy element and never retries, leaving an empty square for ever. The
  Foyer shield is drawn as an inline SVG in the panel header and the card,
  where the modules are certainly loaded, and `foyer:shield` stays registered
  for anyone who wants it on a dashboard of their own.
- **The `foyer:shield` drawing is redrawn, never scaled.** It renders at 24 px
  and inherits the theme colour, so it cannot use amber or the opacity ladder
  that make the 256 px version work. Shrinking the colour version produces
  grey mush.
- **The subtitle carries no font dependency.** "HOME DEFENDER" is stored as
  outlines (Poppins Medium, converted), letter-spaced so that it spans exactly the
  width of the FOYER wordmark above it. Nothing in the repository depends on a
  font being installed.
- **Stroke weight is constant at 3.2** in the 64-unit grid (3.4 in the monochrome
  icon, to survive downscaling), with round joins throughout.

## 18. Documentation plan

**The README is a front door, not a manual** (decision 148). `README.md` and
`README.it.md` are short pages — roughly 150–200 lines each, pictures included
— that make somebody want to use Foyer and able to start it: what it is, what
the household gets, what it looks like, how to start, the security model in
one paragraph, and where to read more. The reasoning lives in the documents
below, each linked from the feature it explains. The two READMEs carry the
same sections, the same claims and the same pictures in their own language.
**Neither compares Foyer with any other product**: no table, no "compared
with", no "if you want X use Y". The importer of §20.2 may appear as one
neutral line among the features, linking its document; §1.3 is where prior
art is discussed.

**Every document added from Phase 5 part 4 on is written in English and in
Italian** (`<name>.md` and `<name>.it.md`), with a link to the other language
at the top (decision 149). The documents written before it stay in English,
and the Italian README says so where it links them.

| File | Content |
|---|---|
| `README.md`, `README.it.md` | The front door: one-line pitch, a picture, what the household gets (each point linking its document), getting started in a few lines, the **security model in one paragraph** (INV-6), the documentation index, a factual status line, contributing, security reporting, licence |
| `docs/README.md` (+ `.it.md`) | The index of `docs/`: every document, one line each, and which panel page it explains |
| `docs/security-model.md` (+ `.it.md`) | The full threat model (INV-6): what codes protect against and what they do not, what a Home Assistant administrator can do regardless, the duress code, the walk test's reach, credentials shown once, how the configuration can be checked rather than trusted, why the log is audit-useful but not tamper-proof |
| `docs/getting-started.md` (+ `.it.md`) | Requirements, install (HACS and manual), the config flow and the first-run wizard: first area, first zones, first scenario, first person with a code, first test notification; the first fifteen minutes |
| `docs/settings.md` (+ `.it.md`) | The Settings page, one setting at a time: the global defaults, siren duration and cutoff, the language of outgoing messages, the log's categories and retention, backup and restore, the importer, what removing the integration takes with it — each pointing at the document with the detail |
| `docs/card.md` (+ `.it.md`) | The card: its four layouts, its editor, how it asks for a code and forgets it, what it shows during a delay, an alarm and a walk test |
| `docs/zones.md` (+ `.it.md`) | Zone types, trigger specs, NC vs NO contacts, supervision, arm policies, exclusions, key zones, the technical channel, chime, cross-zone verification and groups |
| `docs/response-profiles.md` (+ `.it.md`) | Inheritance (the area is the unit of response), incidents, moments, actions, conditions, templates including `{{ operation }}`, silent zones, cameras |
| `docs/notification-channels.md` | Recipes: Companion app + critical alerts, Pushover priority 2, Twilio SMS, Twilio voice, GSM modem, Telegram, Signal |
| `docs/resilience.md` | Cut power and cut fibre; UPS on the router; why a local GSM channel is the only one that survives |
| `docs/keypads.md` | Hardware comparison, the MQTT contract, writing your own adapter |
| `docs/reusing-existing-sensors.md` (+ `.it.md`) | Reusing an existing alarm's sensors: native panel integrations, programmable relay outputs, wired-bus sniffing, 433 MHz reception via rtl_433 or an RF bridge, and why 868 MHz encrypted systems (Ajax, Verisure, Inim Air) cannot be sniffed. Includes the honest caveats: wireless sensors sleep for minutes after a detection, passive reception loses supervision, and tampering with a monitored panel may void the contract |
| `docs/automation-rules.md` | Presence-based arming, the guards, suspensions and expected-visitor windows, and an unhedged explanation of why automatic disarming is restricted |
| `docs/brand.md` (+ `.it.md`) | The asset set, the palette, and the rule that the sidebar icon is redrawn rather than scaled |
| `docs/privacy.md` | What the log contains, the GDPR household exemption, and the point at which it stops applying — logging a cleaner, a B&B guest or an employee |
| `docs/system-health.md` | Mains power and UPS, notification channel health, the external watchdog and its limits, and RF interference detection stated plainly as a heuristic |
| `docs/choosing-sensors.md` (+ `.it.md`) | What makes a sensor suitable for alarm use rather than automation: tamper, supervision interval, magnet defeat, radio band. Why a layered zone beats a better sensor, and why the cheapest real upgrade is usually a second sensor in a verification group rather than a more expensive contact |
| `docs/migrating-from-alarmo.md` (+ `.it.md`) | What the importer converts, what it cannot, and what to check afterwards (imported zones start disabled until their trigger is confirmed); running both side by side |
| `docs/simulator.md` | How to read a decision trace |
| `docs/troubleshooting.md` (+ `.it.md`) | Zone never triggers (the trigger spec, first paragraph), false alarms, faults, the refusals people meet (armed-house edits, codes, lockouts), the card missing after an install, how to open an answerable issue |
| `docs/faq.md` (+ `.it.md`) | The questions people ask: who can disarm, Home Assistant's own cards and voice assistants, the administrator with no code, working without internet, updates, why not automations alone |

---

## 19. Testing requirements

- `core/` has unit tests with **no Home Assistant instance**: state machine
  transitions, delay arithmetic, follower-zone inheritance, arming
  preconditions, profile inheritance resolution, condition evaluation including
  midnight-crossing time windows, cross-zone verification, trigger counting.
- Property-style tests for the master aggregation rule.
- Restart persistence test: arm, serialise, restore, assert identical state.
- Security tests: code verification rejects on wrong code, missing code, expired
  user, insufficient permission, locked-out channel; codes never appear in any
  API response or log row.
- Automatic-rule tests: guards block correctly, a suspension window suppresses the
  action, a grace cancellation aborts it, and — asserted directly — **a disarm rule
  never disarms an area flagged `is_perimeter`**.
- A test that every user-visible string resolves through `translations/`, and that
  `en.json` and `it.json` carry the same key set — in both `translations/` and
  `translations/panel/` — so a missing help translation fails CI rather than
  shipping an English panel to an Italian user.
- Incident tests: a second trigger joins the open incident rather than starting an
  escalation; actions are unioned without restarting a running siren; the
  highest-severity contributing profile supplies the escalation; one
  acknowledgement closes everything; a trigger after closure opens a new incident.
- Alarm memory tests: a disarm and an accepted arming each clear it and raise
  `alarm_cleared` once per area; a refused arming, the cutoff resuming an
  arming, an area staying armed through a scenario switch and a walk test
  leave it; an arming that clears it acknowledges no incident and stops no
  escalation.
- Duress tests: a duress code raises `duress` on every operation, accepted or
  refused, and the answer is identical to the ordinary code's; the response
  runs silent and is not held back by a walk test; the row never reaches
  `sensor.foyer_last_event`, the Overview's recent events, a device's `log`
  section or its `changed: log` notice.
- Armed-edit tests: every global setting is classified as kept while armed or
  free, so a new one cannot arrive unclassified; each kept setting, a profile
  in use and a contact it names are refused while an area is armed and
  accepted once every area is disarmed; revoking a person's code while armed
  is accepted, and so is the recovery of §8.2; removing the last usable code
  while armed is refused.
- Technical channel tests: a technical zone fires while disarmed; **disarming does
  not clear it**; it never changes any `alarm_control_panel` state; it never joins
  an intrusion incident.
- Group tests: N-of-M within the window, expiry of the window, member profiles
  applied below threshold, group profile applied at threshold, and the cross-zone
  field producing identical results to the equivalent 2-of-2 group — the assertion
  that keeps the two configuration surfaces on one engine.
- Chime fires only while the zone is unmonitored by the active scenario, and never
  during a walk test.
- Walk test reach: a person limited to one area, without `disarm`, starts a
  walk test and every disarmed area that can arm arms; a detection in an area
  somebody else had armed is recorded and nothing answers it, so narrowing
  `walk_test` stays a decision rather than an accident (§8.3).
- A test asserting the watchdog payload is empty unless explicitly enabled.
- RF interference tests: N zones on one radio going unavailable inside the window
  raises the event; the same pattern with the coordinator ALSO unavailable reports
  a coordinator failure instead; zones spread across two radios do not trigger it;
  and a Zigbee event never notifies through a Zigbee target.
- A test asserting diagnostics output contains no code hashes, no credentials —
  the webhook id, the watchdog URL, a device's token — and no personal names;
  that no configuration read returns the webhook id or the watchdog URL; and
  that a save without a watchdog URL, or switching the watchdog off, keeps the
  stored one.
- Zone camera tests: a `zone` notification carries the cameras of every zone
  in the incident, each once and at most four; each escalation step repeats
  them; `entry_started` never carries one; a `fixed` action is unchanged by
  the migration; a camera that fails costs only its own picture.
- Device endpoint tests: a request without the right token is refused and
  counted per address; a request with the right token from a locked address
  is served on every route, leaves the address's counter as it was, and its
  rows say the address was locked; an `http` keypad's `device_id` is refused
  over MQTT and through a service; a tag cannot be given a token; the token
  never appears in any response, row, backup or dump; a plain-HTTP request is
  served and recorded as not encrypted; a new token invalidates the old one
  and its stream.
- A regression test asserting that `core/` imports nothing from
  `homeassistant.*` — this is what keeps INV-1 true over time.

---

## 20. Release readiness and project lifecycle

### 20.1 Continuous integration

Set up in Phase 0, when it costs half an hour:

- **`hassfest`** and **HACS validation** on every push. These are in practice the
  entry requirement for the default HACS repository; without them the project is
  only ever installable as a custom repository.
- pytest, ruff and the frontend build on every push.
- **Semantic versioning** and a maintained changelog. For a security system, the
  changelog is what lets a user decide whether to take an update — "fixes" is not
  an answer when the thing being updated guards their house.

### 20.2 Importing from Alarmo

A tool that reads an existing Alarmo configuration and converts it into Foyer
areas, zones and scenarios, reporting everything it could not map.

This is the strongest adoption lever the project has: nobody with forty configured
sensors remaps them by hand to try something new, however much better it is.

**Scoped honestly, and this wording belongs in `docs/migrating-from-alarmo.md`**,
which the README's one line about the importer links (decision 148). It reads
`.storage/alarmo.*`, an internal format its author may change in any release,
without notice and without fault. It is therefore a **best-effort tool that
reports what it could not convert**, never a guaranteed migration. Framed any
other way it becomes a permanent source of issues that are nobody's bug.

### 20.3 Contributor infrastructure

- Issue templates that ask up front for version, logs and the diagnostics download
  (§12.4), so the first reply is an answer rather than a question.
- `CONTRIBUTING.md` covering the development setup, the `core/` purity rule
  (INV-1) and the test expectations.
- A documented flow for adding a language that touches no code: copy
  `translations/en.json` and `translations/panel/en.json`, translate both, open a
  pull request. CI already enforces matching key sets (§19).

### 20.4 Disclaimers, and what this software is not

**Agreed after the documentation, and written below** (decisions 150–155).
Apache-2.0 already disclaims
warranty and liability, and §1.2, §5.5 and INV-6 already state parts of this
in the places where the decision is being made. What is missing is one settled
wording, said everywhere a person actually meets the product rather than only
in a licence file nobody opens.

The distinction the wording has to carry:

> Foyer automates actions on rules — arming, disarming, sounding, notifying —
> the way an alarm does. It is **not a professional alarm system**, it is not
> professional hardware, and nothing about it is certified.

What follows from that, and what the wording has to say plainly:

- **No certification and no standard.** EN 50131, CEI 79-3 and their
  equivalents are not met and are not aimed at. An insurance policy or a
  tender that names a grade is not satisfied by this (§1.2).
- **No monitored centre.** Nobody is watching. Foyer notifies the people the
  household lists, over transports it does not own, and an escalation that
  reaches nobody is an outcome the household has to have planned for (§7.3).
- **Consumer hardware, and a house's own network and power.** Detection is
  only as good as sensors somebody bought, a radio somebody else designed and
  a router that goes off with the power. The failure modes are documented
  rather than defended against (§12, `docs/resilience.md`).
- **Not a fire alarm system**, already non-negotiable in §5.5 and repeated
  here because it is the one that could kill somebody.
- **It depends on Home Assistant**, and stops when Home Assistant stops. The
  restart gap is logged (INV-3) precisely because the alternative is a system
  implying it was watching when it was not.
- **The household is the operator.** Foyer executes the configuration it was
  given; verifying that configuration is what the simulator, the walk test and
  the action test exist for (§11), and the honest claim is "it does what you
  configured", never "it will protect you".

Where it has to appear, at minimum: both READMEs, `docs/security-model.md`,
the first-run wizard, the panel's own about/help surface, `SECURITY.md`, and
the HACS listing. Where it must **not** appear: as a modal nobody reads twice,
or as small print that contradicts a headline sentence elsewhere. The project's
own rule applies to this too — state the limit where the person is deciding,
in the same voice as everything else.

One thing to settle when the wording is: whether the strongest sentences
belong to the reader ("do not rely on this alone") or to the author ("this is
not offered as a certified alarm"). They are not the same promise, and the
document should make one of them on purpose.

**Settled: both, the author's first** (decision 150). The author says what is
offered and what is not; the reader is then told what not to do. The text, in
full, everywhere it appears:

> Foyer is offered as software that automates actions on rules, not as an
> alarm system. It is not certified (EN 50131, CEI 79-3), not monitored, not a
> fire alarm, and comes with no warranty and no promise of support
> (Apache-2.0, sections 7 and 8). Do not rely on it alone to protect people or
> property: keep certified smoke alarms, and a professional installation where
> a policy or a risk calls for one.

> Foyer è offerto come software che automatizza azioni su regole, non come
> impianto d'allarme. Non è certificato (EN 50131, CEI 79-3), non è
> sorvegliato, non è un sistema antincendio, ed è fornito senza garanzie né
> impegno di supporto (Apache-2.0, sezioni 7 e 8). Non affidarti solo a lui per
> proteggere persone o beni: tieni rilevatori di fumo certificati, e un
> impianto professionale dove una polizza o un rischio lo richiedono.

**Where it is read** (decisions 151, 152):

- **The config flow's first step**, with a tick, *I have read this and accept
  it*: nothing is set up until it is ticked. The entry keeps the version of
  the text accepted and when — Home Assistant does not say which account
  opened the flow, so "when" is all there is to keep — and the installation's
  first log rows include `config_disclaimer_accepted`. A new version of the
  text asks again.
- **An installation older than the tick** gets a repair card with the same
  text and the same tick, which records the acceptance the same way. The alarm
  keeps working until somebody ticks it: an alarm switched off by an update to
  its documentation would be a worse outcome than the one the text warns about.
- The Overview's help panel, the READMEs, `docs/security-model.md` and
  `SECURITY.md` carry the same text. The first-run wizard does not: the config
  flow before it already asked, with a tick, and "Not now" skips the wizard.
  HACS shows the README.

**The project around it** (decisions 153–155): Foyer is the personal,
non-commercial project of one individual publishing as Foyer Labs; there is
no company behind it. Support is best effort, with no promise of an answer or
a fix (`SUPPORT.md`); a donation is a gift and buys neither. That is also
what keeps it inside the exclusions the EU's product-liability and
cyber-resilience rules make for free software supplied outside a commercial
activity — which is a reason to keep it that way, not a legal opinion.

## 21. Decision log

| # | Decision | Rationale |
|---|---|---|
| 1 | Custom integration + SPA panel + Lovelace card | Only architecture that supports many configuration pages with direct access to HA state |
| 2 | Written from scratch, Alarmo as benchmark | Alarmo's four fixed arm modes are structural; three real gaps remain |
| 3 | Zones → Areas (independent state) → Scenarios | Matches professional panels; enables partial arming |
| 4 | Panel per area + master + scenario select | Unlimited scenarios without losing voice assistants and HomeKit |
| 5 | Zone types as presets over editable properties | Guides the novice, does not cage the expert |
| 6 | Per-zone arm policy, default `block` | Auto-bypass everywhere breeds silent unprotected windows |
| 7 | Response profiles with inheritance | Kills the zones × scenarios × actions matrix |
| 8 | Conditions limited to time window + entity state | The boundary against reimplementing HA automations |
| 9 | Contact book with prioritised channels + escalation with acknowledgement | Transports already exist in HA; orchestration does not |
| 10 | Per-operation code policy with per-user override on identified channels only | On a shared keypad the code *is* the identity |
| 11 | Generic service + MQTT contract, with adapters | Keypad models churn every six months; the contract does not |
| 12 | Dedicated SQLite log | Recorder's 10-day default purge would destroy the 30-day requirement |
| 13 | Diagnostics + simulator + walk test + action test | The verification story is the project's strongest differentiator |
| 14 | One code per user, unique across users | A shared code makes the audit log decorative |
| 15 | Auto-arming yes; auto-disarming off by default and never on a perimeter area | Presence is inferred from a phone, and a stolen phone must not open the house |
| 16 | Collapsible per-section help, sourced from the translation files | Several settings have effects that are not guessable from their label |
| 17 | Shield frame around the existing Foyer mark | Immediate legibility as security beats an internal geometric echo for an unknown project |
| 18 | Technical alarms on a fully separate channel | `triggered` on an `alarm_control_panel` means burglary to HomeKit, Google and Alexa — a smoke detector must not say it |
| 19 | Incidents, not per-zone alarms, with profile severity for merging | A real break-in trips several zones; three escalations at once is phone spam at the worst possible moment |
| 20 | Verification groups N-of-M, members keeping their own profile | Graduated response for free: one PIR notifies, two sound the siren |
| 21 | Cross-zone stays a simple zone field, evaluated by the group engine | Easy case stays easy to configure; one engine to test and one trace to read |
| 22 | Chime keyed to "unmonitored by the active scenario", not "disarmed" | The narrow wording would leave a hole exactly in the partial scenarios this project exists for |
| 23 | Chime can speak the zone name instead of a tone | In Home Assistant it costs the same and tells you *what* opened |
| 24 | `arm_after_closing` as a fourth arm policy | For the person who presses arm and *then* pulls the patio door shut |
| 25 | Per-scenario siren duration; configurable MQTT topics | Nearly free now, tedious to retrofit |
| 26 | Timed temporary bypass | A zone excluded and forgotten is the window somebody comes through |
| 27 | System health as a concept distinct from zones | "The mains are down" is not an intrusion and must not enter the intrusion queue |
| 28 | Notification channel health, announced over a *different* channel | Warning you about a dead channel over the dead channel is the joke that writes itself |
| 29 | External watchdog: configurable URL, empty payload, failures reported locally | A dead system cannot report its own death; and a heartbeat carrying state would tell a third party when the house is empty |
| 30 | Repair issues and anonymised diagnostics | Turns a GitHub issue into something answerable |
| 31 | Full privacy tooling: targeted deletion, optional pseudonymisation, per-person export | The household exemption stops covering the log the moment it records the cleaner |
| 32 | hassfest and HACS validation from Phase 0 | In practice the entry requirement for the default HACS repository |
| 33 | Alarmo import as an explicitly best-effort tool | Reads an internal format that may change without notice and without fault |
| 34 | RF interference detected by correlated unavailability, gated on the coordinator still answering | Jamming cannot be measured from Home Assistant, but many zones on one radio falling silent at once is its signature — and the coordinator check is what separates it from a dead switch |
| 35 | Panel, card, help and notification strings in `translations/panel/<lang>.json`, served over `foyer/translations` | hassfest validates `translations/<lang>.json` against a closed schema with no room for them; a subdirectory keeps one translation home without breaking the CI gate for the default HACS repository (decision 32) |
| 36 | Zone roles are explicit properties (`channel`, `entry_mode`, `alarm_kind`); the type is only the preset that filled them | "The engine reads only properties" needs properties that say what a follower, a technical zone or a key is; without them the type silently becomes behaviour |
| 37 | Siren cutoff returns an area to its pre-trigger state | An `always_on` zone fires on a disarmed house; a cutoff that always re-arms would arm it |
| 38 | No per-zone exit delay | The exit timer belongs to the area; a zone-level value had no defined meaning |
| 39 | Supervision counts heartbeats, per sensor, off by default | Sensors report at different intervals and some only on change: the window must be set sensor by sensor, and "no change" would fault a door that stays shut |
| 40 | An area's own panel arms only that area; scenarios arm from the master, the select, the panel and the card | Independent area state is the point of areas; an area button that armed a whole scenario would trap people in other rooms |
| 41 | The master refuses a mode shared by two scenarios | Guessing which scenario "arm night" means is how a house ends up half armed without anyone knowing |
| 42 | Switching scenario disarms what only the old one armed, and never silences an alarm | A scenario defines what is armed; a switch that left the old areas armed would not be a switch |
| 43 | The master reports `armed_custom_bypass` whenever the armed set differs from the active scenario | HomeKit and voice assistants must not be told "night" when what is armed is not Night |
| 44 | A key zone's disarm and toggle act on every area | A key has no area to choose; it behaves like the master |
| 45 | `arm_after_closing` waits for the exit delay and the closure, with a per-zone cap | Completing on closure alone would arm while the person is still walking to the other door; holding forever leaves a house that believes it is arming and protects nothing |
| 46 | Event triggers match `event_type`; no subtype | Home Assistant event entities have no standard subtype attribute and a tag has only the scan; a field nobody can fill meaningfully is removed rather than kept |
| 47 | A follower can follow delayed zones in other areas, by explicit choice | Areas are grouped by function (perimeter, interior day, interior night), so the front door and the hall sensor sit in different areas; a same-area-only follower would sound the alarm the moment you walk in |
| 48 | A technical zone in fault blocks arming like any zone, unless `allow_arm_when_faulted` | INV-4 has no exception for the technical channel; the per-zone flag is the way out, chosen knowingly, for the flood sensor with a dead battery on the morning you leave |
| 49 | One technical acknowledgement acts on every pending technical alarm | The same rule as the incident: one person, one button, everything they have seen |
| 50 | Cross-zone is symmetric and does not suppress its members | A pair is a pair whichever end declares it; and a filter that silences a lone sensor is the explicit `suppress_members` group, never the default |
| 51 | A non-suppressed group member alarms normally on its own | "Members keep their own profile": the area state is the area's, and the profile decides whether a lone member is only a notification |
| 52 | Only activations that would alarm at once count towards a group or a trigger count | Coming home through the entry delay must never satisfy a group; otherwise the group profile fires on every homecoming |
| 53 | Group members may sit in different areas; each acts in its own | Areas are grouped by function (decision 47): a perimeter window confirmed by an interior PIR is the common case |
| 54 | An incident opens at `triggered`; disarming acknowledges it; a zone joining after the acknowledgement clears it | An entry delay is the normal way home, not an incident; §7.2 already makes disarm an acknowledgement; and a second zone after "it was the cat" must be heard |
| 55 | Chime is read per area; chiming during the exit delay is a setting, off by default | Decision 40 makes per-area arming possible; the door you leave by is expected to open |
| 56 | A technical zone's first reading is a baseline too, stated in the zone editor | One rule for every zone; the case is a detector saved while already detecting, and the editor is where the user is at that moment |
| 57 | Only disarming an area the incident touched acknowledges it | Acknowledgement means someone has seen the alarm; disarming an unrelated area proves nothing of the kind, and in Phase 4 it would stop an escalation nobody saw |
| 58 | The part 2 schema is a major version (3.1), though additive | An older build reading it would keep technical zones and never act on them; refusing the file is the only safe downgrade |
| 59 | `button.foyer_acknowledge` is deferred to Phase 2 | A button cannot carry a code: whether it may exist depends on the acknowledgement's code policy, which is Phase 2's to set |
| 60 | The chime can also go to `notify` targets (app, Telegram) | The user wants the free channels the house already has, not only speakers; built with the `notify` action in Phase 1 part 3, which discovers and calls the same services |
| 61 | The area is the unit of response; a zone's profile is read only for its own alarm | One rule to hold in mind when asking why it sounded, and the zone profile is kept exactly where graduated response needs it (§4.8) |
| 62 | The technical channel has its own global default profile | A smoke detector must not answer differently depending on how the house is armed, and a scenario is meaningless to a channel that is always live |
| 63 | The default profile notifies `triggered` too | Phase 0 had no notification on an alarm at all; an alarm that says nothing is the worst failure there is |
| 64 | An action's two conditions combine with a selectable *and* / *or* | "Only at night and only if nobody is home" is the common case, but one selector buys the other half |
| 65 | Action delays and auto-reverts are persisted timers | A restart mid-alarm must not leave a siren sounding for ever or a sequence half-run; INV-3 lists pending timers |
| 66 | What a `silent` zone suppresses is a global list of action kinds | Which actions make a noise is an installation's business, not something to fix in code |
| 67 | Camera files go to a configurable folder, `media/foyer` by default, never `www`; notifications attach the camera proxy | `www` is served without authentication, and the inside of a house is not something to publish |
| 68 | A chime target may carry quiet hours of its own | The chime on a phone rings for every door opened; the speakers do not need the same window |
| 69 | Manual bypass needs no code until Phase 2, but runs through the check | The same reasoning as decision 6, and Phase 2 then changes policy rather than plumbing |
| 70 | A manual bypass without a duration ends at the disarm; a timed one survives until it expires | What real panels do, and it keeps the timed form meaningful: a two-hour exclusion must not vanish at the next disarm |
| 71 | `persistent_notification` is a tenth action kind | It is what Phase 0 did; the 3.1 → 4.1 migration moves it into the default profile so no installation loses a notification it already had |
| 72 | The log uses the stdlib `sqlite3` in an executor thread, not `aiosqlite` | It is what the recorder itself does, and it adds no dependency: an alarm integration that fails to load because a wheel could not be fetched at first setup is a failure mode worth not having |
| 73 | The "language" setting is the language of what Foyer *sends*, not of the panel | The panel already follows each Home Assistant user; a second selector for the same thing would be a bug generator, while the house's own language has nowhere else to live |
| 74 | The sidebar panel icon is `mdi:shield-home` | Home Assistant resolves a custom icon once and never retries, so a sidebar drawn before the icon module has run keeps an empty square for ever — which is what the companion app does |
| 75 | The first-run wizard continues from the config flow instead of replacing it | The config flow already makes an area, a zone and a scenario, so a new installation is never empty; a wizard that started again would duplicate all three |
| 76 | The log's own row for a refusal, and the incident id as a column | "Why did it not arm last night?" needs an answer, and an incident id inside a JSON detail field cannot be filtered on |
| 77 | Acknowledging needs no code by default, and `button.foyer_acknowledge` therefore exists | §7.2 already acknowledges from an actionable push notification, which carries no code; demanding one on a button would be theatre at the worst possible moment. It stays a policy entry, so an installation can raise it — and then the button refuses, visibly, rather than lying |
| 78 | The code policy is inert until an enabled user holds a code | Failing closed with zero codes protects nothing and makes the alarm unusable; the alpha installations upgrading into this phase would find a house they could not disarm |
| 79 | The per-user exemption is the user's switch, off by default, and no administrator is exempt automatically | What makes the exemption safe is the identification, not the role — and the unlocked wall tablet INV-6 names is almost always signed in as an administrator |
| 80 | Where an area and a scenario disagree, the strictest explicit setting wins | §8.2 puts them on one step; the failure of this rule is one code too many, the failure of the other is a deliberately protected area opened by a permissive scenario |
| 81 | A device is declared before it may command, and an unknown one is refused, logged and notified | The lockout counts per channel and device, so a caller free to invent a device id is a caller who is never locked out — and a refusal nobody sees is how a keypad set up with the wrong name stays broken for a month |
| 82 | A tag always names a person, and never answers to a typed name | §8.2 calls it a *per-user* tag, which is the whole of why it identifies; and a token that answered to a name anybody could type would be an identity with no code in front of it |
| 83 | The retained MQTT state message has three levels and starts at the least | It is retained on a broker that is often shared, so everything in it is told to whoever connects next — the same reasoning as the watchdog's empty payload (decision 29) |
| 84 | The channel is the registered device's, never the message's claim | Otherwise an automation buys the per-user exemption of §8.2, or chooses which lockout counter to spend, by typing a word |
| 85 | `skip_exit_delay` needs no permission of its own, and is recorded | It uncovers nothing; it closes sooner. But it turns every delayed zone into an instant one, and "why did it sound while I was still in the hall?" must have an answer |
| 86 | `foyer.walk_test` and `foyer.test_action` are registered when Phase 3 builds them | A service that exists and does nothing answers its caller with silence, which is the answer that gets mistaken for success |
| 87 | `last_result` is four words for ever, and `last_reason` carries the precise why | An adapter written today must never meet a word it does not know: a keypad that goes quiet when something new happens is worse than one that says "blocked" — and the detail is still there for whoever wants it |
| 88 | A `user_id` nothing established marks its log row `attributed: claimed` | Arming needs no code, so a caller could otherwise write a name the log had no reason to believe; a wrong answer to "who disarmed at 03:14?" is worse than no answer, and the capability is worth keeping |
| 89 | P-1: outward, every channel starts at the least that works | The watchdog and the MQTT message reached that conclusion separately, and §9.2 reached the opposite one first; a principle written once is what stops the next channel rediscovering it by accident |
| 90 | A notification with a camera names the transport the attachment is for, rather than Foyer guessing from the service | The service name is not the transport: a Telegram bot may be called anything, and the guess fails silently because every transport ignores the keys it does not know. The user picked the app; asking which one is one field, and the alternative is a picture that never arrives and never says why |
| 91 | Cameras belong to the zone, as an ordered list | The picture has to say where: the kitchen window wants the kitchen and the room next door, and that is a property of the window, not of every notification that might mention it |
| 92 | Which images a notification carries is a selector on the action — none, fixed, zone — and existing actions keep what they had | Changing what arrives on somebody's phone without their touching anything is a failure the migration must not introduce; new actions start where the feature is useful |
| 93 | A `zone` notification shows the cameras of every zone in the incident, each once | The intruder moves from the window to the hall; a picture of the way in alone shows where they were, not where they are |
| 94 | One notification per camera, the first carrying the text and the buttons | The Companion app shows one image per notification; a composite would put a file on disk for the one transport that needs none, and the acknowledgement must stay on the message that is always sent |
| 95 | Every notification repeats all the cameras, fresh, at most four | What the house looks like now is the point of a picture; the bound keeps "every zone, every time" from burying the message it came with |
| 96 | Zone cameras only at alarm moments and on the technical channel, never at `entry_started` | An entry delay is the household coming home; photographing every homecoming and sending it out of the house is what P-1 exists to stop |
| 97 | A device endpoint with a token per keypad; plain HTTP accepted and said, never hidden | The token authenticates the device, which MQTT's claimed name cannot; confidentiality is TLS's job, and refusing keypads that cannot do TLS would take the feature from the people who asked for it |
| 98 | One transport per keypad: MQTT or the endpoint, never both | A token the broker can route around by using the device's name protects nothing |
| 99 | Only keypads use the endpoint, never tags | On a keypad the code is still the identity and the token disarms nothing alone; a tag's token would be the key to the house, readable on the wire whenever the request is not encrypted |
| 100 | A notification answering a zone joining is sent for every zone that joins | The union of §5.6 keeps a siren from restarting; applied to messages it swallowed the patio's notification because the hall's had gone, and §6.2.1 promises the cameras again at each join |
| 101 | An unlinked Home Assistant administrator is asked for the code when the policy asks | Being an administrator identifies nobody, and the wall tablet INV-6 names is signed in as one; the administrator keeps only §8.4's "never locked out" |
| 102 | A claimed `user_id` grants nothing, on any service | Decision 88 said so; the configuration and log services had let a typed id carry that person's permissions |
| 103 | The panel, the card and the services count wrong codes per Home Assistant account | One counter for the whole channel let any account, with no permission at all, lock the household out by typing five wrong codes |
| 104 | A code that is somebody else's, offered when saving a person, counts as a wrong code | Otherwise the uniqueness check of §8.1 is a way of testing codes against the household without limit |
| 105 | `alarm_ended` is a per-area moment: siren cutoff or a disarm with alarm memory, never an ordinary disarm | "Switch it off when the alarm is over" needs a moment an area's profile hears; the incident's acknowledgement belongs to no area, and `disarmed` fires every evening |
| 106 | A refused service raises when the caller does not ask for its response | An automation that does not read the result took a wrong code for success and carried on as if the house were disarmed |
| 107 | Arming is refused while a walk test runs | The test arms every area it can and its end disarms what it armed; an arming accepted in between could be undone without a word |
| 108 | `alarm_cleared` is raised when a disarm clears an area's alarm memory | §6.1 named it and nothing raised it; an alarm is often over long before anybody clears it, and "the lamp that says something happened" needs the second moment, not the first |
| 109 | An administrator recovers access from the integration's Configure step, loudly | Decision 101 left an administrator with no code no way in; INV-6 says they can do anything anyway, so the recovery exists — and is logged, notified in Home Assistant and sent to every contact, so it is never the quiet way round a code |
| 110 | The recovery enables the account's linked user, removes its validity window and sets its code, or creates the user with every permission; only administrators' accounts are offered | An administrator whose own user was disabled could not undo it; Home Assistant does not say who opened the step, so it asks for the account — and a way in for anybody else is the Users page's, with its permissions |
| 111 | A restore that touches people, tags or a key switch's person needs `manage_users` | `edit_config` alone let a backup file grant any permission, or give somebody's tag to somebody else; the Alarmo importer already asked for it |
| 112 | Every change that touches people — a person, a tag, a key switch's person, a scenario's allowed people — needs `manage_users`, however it is made | Decision 111 closed the restore; the editor still let `edit_config` alone give a key switch to somebody or put somebody on a scenario's list |
| 113 | The Overview's help panel starts collapsed | It is the page opened to arm or disarm in a hurry; on a phone the help pushed the controls off the screen |
| 114 | The panel forgets a typed code after two minutes unused, after every arming or disarming, and when it closes | Kept for the whole visit, it let whoever came to the unlocked wall tablet next disarm or reconfigure without typing it |
| 115 | A device on the endpoint is allowed what its own scopes say, all off until switched on | A display, a relay and an ESP32 module need different things; one fixed set would give each of them too much or too little |
| 116 | Without a code an API device only reads; every action needs a code, arming included | The token crosses the network readable when the request is not encrypted, and must never be what arms or disarms the house; a relay that lights a lamp needs no more than reading |
| 117 | Each read scope is free or after a code, per device; `status` free and the rest after a code by default | A device in the hall is read by whoever walks past it; the lamp's relay must still read the state with no keypad at all |
| 118 | The unlock lasts 30 s to 10 min, chosen per device, ends with every arming or disarming, reads only what its code's owner may, and leaves a row | The same reasoning as decision 114, with a length that fits a display on a wall and a module that polls |
| 119 | Plain HTTP stays accepted; any scope beyond `status` on a device in the clear needs an explicit, logged confirmation | Decision 97 kept the modules that cannot do TLS; what those scopes say about the house is worth one deliberate tick |
| 120 | The state is streamed; each section is a small request, announced on the stream when it changes | A microcontroller has little memory; a lamp must still light at once |
| 121 | `docs/api/openapi.yaml` and `asyncapi.yaml`, contract `v1`, checked against the code in CI | A document nobody checks is false within two releases; the panel's WebSocket commands are internal and stay out |
| 122 | Swagger UI on an administrators' page of the panel, bundled, loaded only there | Trying the contract from a browser helps whoever builds a device; a public page would advertise the alarm to a scanner |
| 123 | API devices land in Phase 5, before the documentation | So the documents describe them rather than being rewritten for them |
| 124 | A rule's contacts are told the outcome of its arming — not armed and why, armed later, or armed excluding zones — through quiet hours | The household had left; a rule that could not arm told nobody who was not looking at Home Assistant |
| 125 | The countdown names the open zones and says what will happen to them | "It will arm in two minutes" was a promise the open window was about to break, sent to the only people who could still shut it |
| 126 | A rule may arm excluding open zones — opt-in, bypassable zones only, never a fault | Some households want the house armed with the window open; a forced arming nobody chose must be the rule's owner's deliberate choice, and a silent sensor is never excluded by it |
| 127 | A rule triggered by an instant is not retried when the zone that refused it closes, and its message says so | Its one turn has gone; arming the house at noon for "23:00 yesterday" is a surprise, and a message promising a retry that never comes is worse |
| 128 | No API returns a configuration credential: the configuration says whether the acknowledgement webhook and the watchdog URL are set, never what they are | Reading the configuration needs `edit_config` and no code, so whoever held it could copy the URL that stops an alarm or the one that keeps a dead house looking alive; §9.2.1 already said neither is ever returned |
| 129 | The webhook's address is shown once, in the answer that generates it — the full URL when Home Assistant knows its external address, the path otherwise; to see it again, generate a new one | The keypad token's rule: an address the panel can read back is one the next person at the tablet can read, and the one moment it is shown should give something that can be pasted as it is |
| 130 | The watchdog URL is written and never read back; a save that leaves it out or sends it empty, or switching the watchdog off, keeps it; a new one replaces it | The panel no longer holds it to send back, and a save that cleared it would stop the heartbeat quietly — the failure §12.3 exists to report |
| 131 | A duress code acts as its owner's code wherever a code is read, and raises `duress` once for every request it comes with, accepted or refused; a request refused before the engine hands it the duress and nothing else | Somebody made to open the house is as easily made to switch off the siren, stop the escalation or delete a contact; a person asking for help has asked, whatever the answer. The lockout must see the duress code exactly as it sees the ordinary one |
| 132 | `duress` belongs to no area and no incident, is answered by the default profile, always runs silent, never escalates, and is never held back by a walk test | An incident is on every card; a siren answering it would tell the room; a walk test inhibits the house, not a person — and the coerced person may be made to start one |
| 133 | The `duress` row is read on the log page, in an export and on Home Assistant's bus as `foyer_event`, never among the Overview's recent events, in `sensor.foyer_last_event`, in a device's `log` section or its change notice | "Nothing visible differs" has to hold on the tablet the code was typed on, and that tablet shows all four; an automation answering duress needs the bus |
| 134 | `{{ operation }}` joins the template variables, naming the command a duress code was used for | A duress message that cannot say what the person was made to do tells its contact half of it; "edit the configuration" for somebody made to export the log tells them the wrong half |
| 135 | A right token always passes the device endpoint's per-address lockout; the lockout refuses only a missing or wrong token; the rows a right token causes from a locked address say so, and the request neither spends nor clears the address's counter | Behind NAT, a reverse proxy or one IPv6 /64 a real keypad shares its address with whoever is guessing, and was locked out with them; a token of 32 random bytes cannot be guessed, so the lockout loses nothing |
| 136 | A panel says arming needs a code only while the policy asks for one and nobody is exempt; its refusal of a codeless arming says where to type one; the master's `code_format` reads every area and scenario | Home Assistant refuses on that one answer before Foyer knows who is asking, so an exempt person could not arm from Home Assistant's card; always false, the more-info dialog and the tiles would stop asking everybody else for the code |
| 137 | `walk_test` keeps its whole-house reach — every area whatever `allowed_area_ids`, those armed by somebody else included — and the reach is written in §8.2, §8.3 and the README, and the Users page warns when it is granted | A walk test is walked through the whole house, so it arms and quiets every area whoever starts it; what restrains it is that it is never quiet about itself, and a permission that can quiet an armed house has to be granted knowing that |
| 138 | While any area is armed, an edit that changes the response or the code policy is refused: siren, delays, response defaults, the profiles in use and the contacts they name, the code policy and lockout, automatic disarming, radios | The guard covered areas, zones, groups, the running scenario, the profiles in use and three settings; the siren, the disarm policy and the contact who would be called could still be changed under a house nobody had disarmed, and the log would show no disarm |
| 139 | People, codes, tags, keypads, API devices, the webhook and the rules stay editable while armed; only an edit leaving nobody with a usable code is refused | Revoking a guest's code or a lost phone's rule from abroad, and the administrator's recovery, are needed most while the house is armed; with no usable code the policy switches itself off (decision 78), which is a policy change by another route |
| 140 | An accepted arming clears the alarm memory of the areas it takes out of `disarmed`, raising `alarm_cleared` — an automatic rule's arming included — and acknowledges nothing | Real panels clear the memory at the next arming, and a memory carried into a new watch describes an earlier night; the incident is another matter — arming needs no code by default, and only an acknowledgement or a disarm is somebody who has seen the alarm |
| 141 | A refused arming, the cutoff resuming one, an area staying armed through a switch and a walk test leave the memory; a walk test does not arm an area that holds it | None of them is somebody arming that area again, and a memory nobody has seen must not vanish on the way — a walk test least of all, whose own `alarm_cleared` would be held back with every other action |
| 142 | While any area is armed, what any area or scenario asks a code for cannot change, in either direction — a disarmed area and a scenario that is not running included | They take part in the strictest-wins rule of §8.2 for every command that touches the armed area: lowered on the garage or on an idle scenario, they opened the armed floor without a code |
| 143 | The master tells Home Assistant arming needs a code as soon as one mode it can still arm asks for one, nobody being exempt | The household chose Home Assistant's dialog asking over a codeless mode arming bare from it; that mode arms from an automation through Foyer's own service |
| 144 | An arming accepted in the decision that ends a walk test keeps the alarm memory | That decision's response is still held back, so its `alarm_cleared` would reach nobody; the next disarm or arming clears it |
| 145 | Emptying the log with a duress code keeps that request's `duress` row | The one request a coerced person cannot refuse must not erase its own record; the count of rows removed is the ordinary code's, so nothing on the screen differs |
| 146 | A decision's rows are written before its state is saved, and a process killed between the two is left to the restart-gap row | A slow disk must never delay a siren; the next start restores the state that was, and the gap row says when the house stopped being watched |
| 147 | The minimum Home Assistant is 2026.6 | Earlier releases list every webhook to any signed-in account, and one of them stops an alarm in progress |
| 148 | The READMEs are a short front door, and compare Foyer with no other product; everything else they said moves into `docs/` | A thousand-line README was a manual nobody reads to the end, and a comparison table describes a product by somebody else's; the reasoning is worth keeping, in the documents where the person deciding a setting finds it. The importer keeps one neutral line, and §1.3 keeps the prior art |
| 149 | Documents from Phase 5 part 4 on are written in English and Italian, and the panel's "Learn more" opens the Italian one when the panel speaks Italian | The panel and both READMEs are already bilingual; a help link that drops an Italian household into English at the moment it is deciding a setting undoes that. The older documents stay English until somebody translates them, and the link falls back to them |
| 150 | The disclaimer speaks as the author first, then to the reader, in one text used everywhere | "Not offered as an alarm system" is the author's promise about what is offered; "do not rely on it alone" is what the reader has to do about it. Either alone leaves half unsaid |
| 151 | It is accepted with a tick in the config flow's first step, and the entry keeps the version and the date | Where the decision to install is made, and a tick is an act a button is not. The account is not kept because Home Assistant does not tell an integration who opened the flow |
| 152 | An installation older than the tick gets a repair card, and keeps working until it is ticked | The acceptance matters; an alarm that stopped because its documentation changed would be the failure the text warns about |
| 153 | Support is best effort, with no promise of an answer or a fix, and says so in `SUPPORT.md`, the issue forms and the README | A promise nobody made is still read into silence; saying it once, where a person asks, costs nothing and sets the expectation |
| 154 | Issues labelled `needs info` close by themselves after 14 days without the author; nothing else closes by itself | The one wait that is the reporter's; a real defect the maintainer has not reached must not vanish on a timer |
| 155 | Foyer is the personal, non-commercial project of one individual publishing as Foyer Labs; donations are gifts and buy no support or priority | That is what it is, and the exclusions for free software supplied outside a commercial activity depend on it staying so |
