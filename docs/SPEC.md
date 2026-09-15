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

The README must credit Alarmo as prior art and state plainly how Foyer differs.

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
| Backend | Python 3.12+, Home Assistant 2025.1+ | Matches HA's own floor |
| Config storage | HA `Store` helper (`.storage/foyer.config`) | Backed up with HA, versioned, migration-friendly |
| Log storage | dedicated SQLite via `aiosqlite` | Independent retention; unaffected by recorder purge |
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
| `silent` | bool | triggers response without local sounders |
| `trigger_count` | int | N activations within `trigger_window` before alarming (default 1, at most 10). Only activations that would alarm at once count, as in a group (§4.8) |
| `trigger_window` | seconds | 1–3600, default 60 |
| `cross_zone_id` | uuid \| null | a second zone that confirms this one within `cross_zone_window`: the pair is a 2-of-2 group that does **not** suppress its members, symmetric whichever end declares it (§4.8) |
| `cross_zone_window` | seconds | 1–3600, default 60; a pair declared from both ends has one window |
| `allow_arm_when_faulted` | bool | default false; a zone in fault does not block arming (§5.4, INV-4) |
| `supervision_timeout` | seconds \| null | per zone, **off (null) by default**. No report from the entity within this window — a heartbeat counts even when the state has not changed (Home Assistant's `last_reported`) — ⇒ fault (INV-4). Set it per sensor, longer than that sensor's own reporting interval; leave it off for sensors that report only when they change |
| `battery_entity_id` | str \| null | optional, for diagnostics and low-battery faults |
| `response_profile_id` | uuid \| null | null = inherit from area |
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
B are disarmed; areas in both stay armed and now belong to B; areas of B not
yet armed go through their exit delay; areas armed on their own, outside any
scenario, are left exactly as they are. A switch is refused while any area it
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
| `disarmed` | `arm_request` accepted | `arming` | exit delay starts; skipped if delay is 0 |
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
| `triggered` | siren cutoff elapsed | the pre-trigger state | sounders stop; alarm memory stays set until disarm. Triggered from `armed` or `entry` → `armed`; from `disarmed` (an `always_on` zone) → `disarmed`, never armed by the cutoff; from `arming` → `arming` resumes with its original exit deadline and the normal expiry checks |
| `disarmed` with alarm memory | `disarm_request` accepted | `disarmed` | clears the memory; the only transition allowed from `disarmed` by a disarm |
| any | `always_on` zone triggers | `triggered` | including from `disarmed` |
| any | supervision/availability fault | `fault` overlay | `fault` is a flag alongside the state, not a replacement |

### 5.3 Timers

| Timer | Owner | Default | Bound |
|---|---|---|---|
| exit delay | scenario override ?? area default (no per-zone exit delay: the exit timer belongs to the area) | 30 s | 0–300 s |
| entry delay | zone, else area | 30 s | 0–300 s |
| siren cutoff | global | 180 s | **hard max 900 s** (EN 50131 reference for external sounders) |
| escalation steps | response profile | — | |
| supervision | zone, per sensor | off | 60 s – 7 days |
| walk test auto-exit | global | 15 min | mandatory, non-disableable |

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
| Actions | Its own response profile, its own escalation, independent of any intrusion incident in progress |
| Coexistence | A technical alarm and an intrusion incident can be active at the same time and never merge |
| Faults | A technical zone in fault blocks arming its area like any zone (INV-4), unless it is marked `allow_arm_when_faulted` (decision 48) |

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
  restarted; a light not yet on comes on.
- The escalation policy is the one belonging to the **highest-severity**
  contributing profile. This is what the `severity` field on a response profile
  (an integer the user orders) exists for, and it is used for nothing else.
- **One acknowledgement closes the whole incident.** Disarming an area the
  incident touched is an acknowledgement, as it is for escalation (§7.2).
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

The UI must always show the *effective* profile and where it was inherited from,
otherwise the behaviour looks arbitrary.

### 6.1 Trigger moments

A profile can attach actions to three distinct moments, not just alarms:

| Moment | Events |
|---|---|
| **Alarm** | `entry_started`, `triggered`, `siren_cutoff`, `alarm_cleared` |
| **State change** | `armed`, `disarmed`, `arm_failed`, `forced_arm`, `zone_bypassed`, `code_rejected`, `lockout` |
| **System** | `zone_fault`, `low_battery`, `ha_restarted`, `walk_test_started`, `walk_test_ended` |

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
| `call_service` | **arbitrary HA service**: domain, service, target, data (YAML editor) |
| `delay` | wait N seconds before the next action in the list |

`call_service` is the escape hatch that keeps the user out of the automation
editor for anything Foyer does not model natively.

### 6.3 Conditions

Each action may carry **at most two** conditions. This bound is deliberate — it
is the line between a response engine and a reimplementation of Home Assistant
automations.

| Condition | Shape |
|---|---|
| time window | `after: HH:MM`, `before: HH:MM`, correctly handling windows that cross midnight |
| entity state | `entity_id`, `operator: is / is_not`, `state: str` |

Conditions are evaluated by `core/conditions.py`, which is pure and receives
entity states from the snapshot — so the simulator evaluates them identically.

### 6.4 Templates

Message templates support a fixed, documented variable set — not arbitrary Jinja
over the whole state machine:

`{{ zone }}` `{{ area }}` `{{ scenario }}` `{{ user }}` `{{ channel }}`
`{{ time }}` `{{ date }}` `{{ state }}` `{{ open_zones }}` `{{ reason }}`
`{{ incident_zones }}` — every zone that has joined the current incident (§5.6)

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

It needs no special case for walk test: during a walk test the area is genuinely
armed, so its zones are monitored and no chime fires.

"Monitored" is read **per area**, however the area came to be armed or not —
an area can be armed on its own, outside any scenario (§4.6.1). An area
counting down its exit delay is not yet monitoring; whether its zones chime
then is a setting, off by default, because the door you leave by is expected
to open (decision 55).

Configuration is one global block plus one switch per zone, the way real panels
do it — not a response profile, which would be disproportionate for a checkbox:

| Setting | Notes |
|---|---|
| Targets | one or more `media_player` or `siren` entities |
| Mode | **single sound**, or **spoken zone name** via `tts.speak` — "Front door", "Garage shutter". In Home Assistant the second costs the same as the first and tells you *what* opened from the next room |
| Volume | |
| Quiet hours | a window in which chime is suppressed |
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
| `duress_code_hash` | optional; disarms normally but raises a silent `duress` event |
| `ha_user_id` | optional link to a Home Assistant user |
| `permissions` | see 8.3 |
| `allowed_area_ids` | null = all |
| `allowed_scenario_ids` | null = all |
| `valid_from` / `valid_until` | optional, for guest codes |
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

**Channels that identify the user:** Home Assistant UI with `ha_user_id` linked,
a per-user NFC tag, a per-user RFID badge. **Channels that do not:** a shared
keypad, a generic MQTT device, an automation. On a non-identifying channel the
code *is* the identity, so the per-user exemption cannot apply and the code is
always required. The configuration UI must state this next to the setting,
otherwise it reads as a bug.

### 8.3 Permissions

`arm` · `disarm` · `force_arm` · `bypass_zone` · `change_scenario` ·
`edit_config` · `view_log` · `test_actions` · `walk_test` · `manage_users`

### 8.4 Lockout

After `N` failed code attempts (default 5) within `W` seconds (default 300), the
originating channel is locked for `L` seconds (default 300), exponentially
increasing on repetition. A lockout:

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
rather than a silent failure.

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
  "fault": false, "last_result": "ok"|"blocked"|"bad_code"|"locked_out" }
```

Published retained on change and on request. Keypad adapters map `last_result`
to their own beep and LED vocabulary.

**Topics are configurable**, not fixed. The `foyer/<install_id>/` prefix is a
default, overridable per installation: people run more than one site against one
broker, and people have an existing topic hierarchy they are not going to
restructure for a new integration. Cheap to allow now, tedious to retrofit.

### 9.3 Shipped adapters (blueprints)

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
| **Suspension** | until a date and time · skip the next occurrence only · a global switch |

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
   raises an explicit warning in the UI naming the attack above.
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
  user_id      TEXT, user_name TEXT,    -- name denormalised: survives user deletion
  channel      TEXT, device_id TEXT,
  outcome      TEXT,                    -- ok | blocked | bad_code | failed
  detail       TEXT                     -- JSON
);
CREATE INDEX idx_ts ON events(ts);
CREATE INDEX idx_cat_ts ON events(category, ts);
CREATE INDEX idx_area_ts ON events(area_id, ts);
CREATE INDEX idx_user_ts ON events(user_id, ts);
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
disableable and is meant to be switched on only while diagnosing.

### 10.3 Retention and export

Retention is configurable per category, default 30 days, with a purge task on a
daily schedule. Export produces CSV or JSON honouring the currently applied
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

Every simulation run is logged (category `system`) with its inputs, so a
configuration change can be justified after the fact.

### 11.3 Walk test

The area is genuinely armed and zone states are genuinely real, but **all actions
are inhibited**. The user walks the house and the panel records, live, which
zones detected them — highlighting zones that never reacted. This is the only way
to find a misaimed PIR or a dead battery before it matters.

Mandatory safeguards:

- an automatic exit timeout (default 15 minutes, not disableable),
- a permanent, unmissable banner in the panel and on every card while active,
- entry and exit logged with the user who started it,
- a notification on start and on end,
- `always_on` zones (tamper, technical, panic) remain **fully live** — walk test
  must never silence a smoke detector.

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
mains failure. In the Foyer model that is simply a zone of type `technical`, so
this costs almost no code — what it needs is the **concept**: a mains failure
raises `system_power_lost`, notifies immediately, is logged, and can drive a
response profile. It must never be confused with a quiet night.

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

Two rules:

- **The heartbeat carries no data by default.** A ping saying "armed, Night,
  nobody home" would be a channel telling a third party exactly when the house is
  empty. An optional payload may be offered, off by default, behind an explicit
  warning.
- **Foyer watches the watchdog.** Repeated failures to reach the endpoint are
  themselves reported locally: being unable to reach the internet means no
  internet-based notification would go out either, and the panel should say so.

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
  dump of configuration and state: no codes, no hashes, no personal names,
  entity ids redacted to stable placeholders. This is what turns a GitHub issue
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
| `alarm_control_panel.foyer_<area>` | area | real area state; supports arm/disarm with code |
| `alarm_control_panel.foyer_master` | 1 | aggregated state, reports the active scenario's `ha_master_state`; the surface voice assistants and HomeKit see |
| `select.foyer_scenario` | 1 | active scenario by name; the persistent record of *which* scenario is running |
| `binary_sensor.foyer_zone_<zone>` | zone | normalised zone state (`on` = triggered), with attributes for bypass, fault, last trigger |
| `binary_sensor.foyer_ready_to_arm` | 1 + per area | whether arming would succeed right now |
| `binary_sensor.foyer_fault` | 1 | any zone in fault |
| `sensor.foyer_open_zones` | 1 | count, with the list as an attribute |
| `sensor.foyer_last_event` | 1 | last significant event, for dashboards |
| `sensor.foyer_countdown` | per area | remaining exit/entry seconds |
| `button.foyer_acknowledge` | 1 | acknowledge an ongoing escalation |
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
| 3 | Zones | Filterable list + zone detail: entity, type preset, trigger spec, delays, arm policy, bypass, profile, supervision |
| 4 | Scenarios | Create scenarios, choose areas, HA state mapping, default profile, allowed users |
| 5 | Response profiles | Profiles, action list, per-action conditions, escalation steps |
| 6 | Contacts | Address book, prioritised channels, quiet hours, escalation policies, per-channel test |
| 7 | Users & codes | Users, codes, permissions, area/scenario scope, validity, duress code, per-user policy |
| 8 | Arming devices | Keypads, NFC tags, remotes; MQTT mapping; feedback configuration |
| 9 | Test & diagnostics | Four tabs: diagnostics · simulator · walk test · action test |
| 10 | Log | Filter by date, area, zone, user, category, outcome; CSV/JSON export |
| 11 | Settings | Global defaults, siren duration and cutoff, log retention per category, language, config backup/restore |
| 12 | Automation rules | Presence and time rules (§9.4), guards, grace period, suspensions and expected-visitor windows, next scheduled action |
| 13 | Verification groups | N-of-M groups (§4.8): members, threshold, window, group profile |
| 14 | System health | Mains power, notification channel health, watchdog status, faults, diagnostics download (§12) |

Plus a **first-run wizard**: create the first area → map three zones with
confirmed trigger specs → create one scenario → create one user with a code →
send a test notification. An empty panel on first open is how projects lose users
in the first five minutes.

**Config backup/restore** (JSON export/import) is not optional: nobody who has
configured forty zones will do it twice.

### 15.2 Contextual help

Every panel page opens with a collapsible **"About this section"** panel above its
content. This is not decoration: an alarm panel has settings whose effect is not
guessable from their label (`arm policy`, `follower`, `cross-zone`, `supervision
timeout`), and a user who guesses wrong finds out during a burglary.

| Aspect | Decision |
|---|---|
| Content | One short paragraph on what the section does, then a compact list — one line per setting — saying **what changes if you change it** |
| Source | `translations/panel/<lang>.json` under `help.<page>`, next to the file Home Assistant itself reads, so it follows the Home Assistant user's language automatically and a translator gets it with no extra machinery. Not in `translations/<lang>.json`: hassfest validates that file against a closed schema and rejects a top-level `help` key (decision 35) |
| State | Expanded on first visit, then remembers the user's choice **per Home Assistant user** (stored in Foyer config, not `localStorage`) so it follows them from desktop to wall tablet |
| Global toggle | A `?` button in the panel toolbar shows or hides every help panel at once |
| Deep link | A "Learn more" link to the matching page under `docs/` |

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
| `foyer-hd-icon.svg` | Home Assistant sidebar panel icon | **24 px, single colour, `currentColor`.** No gradient, no fill colours, no opacity ladder — a *separate drawing*, carrying the shield outline, one arch and a solid doorway. The faded arches vanish at this size, so they are not in this file |
| `foyer-hd-symbol-dark-bg.svg`<br>`foyer-hd-symbol-light-bg.svg` | Panel header, card header, loading state | Full colour, transparent ground, 32 px and up |
| `foyer-hd-app.svg` → `foyer-hd-app-512.png`, `-192.png` | HACS listing, repository social preview, favicon | Dark rounded tile, symbol scaled to 0.84 for a proper safe margin |
| `foyer-hd-lockup-dark-bg.svg` / `-light-bg.svg` (+ PNG) | README header, documentation | Two files, not one recoloured |

### 17.2 Rules that keep it coherent

- **The sidebar icon is redrawn, never scaled.** It renders at 24 px and inherits
  the theme colour, so it cannot use amber or the opacity ladder that make the
  256 px version work. Shrinking the colour version produces grey mush.
- **The subtitle carries no font dependency.** "HOME DEFENDER" is stored as
  outlines (Poppins Medium, converted), letter-spaced so that it spans exactly the
  width of the FOYER wordmark above it. Nothing in the repository depends on a
  font being installed.
- **Stroke weight is constant at 3.2** in the 64-unit grid (3.4 in the monochrome
  icon, to survive downscaling), with round joins throughout.

## 18. Documentation plan

| File | Content |
|---|---|
| `README.md` | What it is, honest comparison with Alarmo, screenshots, install, quick start, **security model summary**, licence |
| `docs/security-model.md` | The full threat model (INV-6), what codes protect against, what an HA admin can do, why the log is audit-useful but not tamper-proof |
| `docs/getting-started.md` | Wizard walkthrough, first area, first zones, first scenario |
| `docs/zones.md` | Zone types, trigger specs, NC vs NO contacts, supervision, cross-zone verification |
| `docs/response-profiles.md` | Inheritance, actions, conditions, templates |
| `docs/notification-channels.md` | Recipes: Companion app + critical alerts, Pushover priority 2, Twilio SMS, Twilio voice, GSM modem, Telegram, Signal |
| `docs/resilience.md` | Cut power and cut fibre; UPS on the router; why a local GSM channel is the only one that survives |
| `docs/keypads.md` | Hardware comparison, the MQTT contract, writing your own adapter |
| `docs/reusing-existing-sensors.md` | Reusing an existing alarm's sensors: native panel integrations, programmable relay outputs, wired-bus sniffing, 433 MHz reception via rtl_433 or an RF bridge, and why 868 MHz encrypted systems (Ajax, Verisure, Inim Air) cannot be sniffed. Includes the honest caveats: wireless sensors sleep for minutes after a detection, passive reception loses supervision, and tampering with a monitored panel may void the contract |
| `docs/automation-rules.md` | Presence-based arming, the guards, suspensions and expected-visitor windows, and an unhedged explanation of why automatic disarming is restricted |
| `docs/brand.md` | The asset set, the palette, and the rule that the sidebar icon is redrawn rather than scaled |
| `docs/privacy.md` | What the log contains, the GDPR household exemption, and the point at which it stops applying — logging a cleaner, a B&B guest or an employee |
| `docs/system-health.md` | Mains power and UPS, notification channel health, the external watchdog and its limits, and RF interference detection stated plainly as a heuristic |
| `docs/choosing-sensors.md` | What makes a sensor suitable for alarm use rather than automation: tamper, supervision interval, magnet defeat, radio band. Why a layered zone beats a better sensor, and why the cheapest real upgrade is usually a second sensor in a verification group rather than a more expensive contact |
| `docs/migrating-from-alarmo.md` | What the importer converts, what it cannot, and what to check afterwards |
| `docs/simulator.md` | How to read a decision trace |
| `docs/troubleshooting.md` | Zone never triggers (check the trigger spec), false alarms, faults |

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
- Technical channel tests: a technical zone fires while disarmed; **disarming does
  not clear it**; it never changes any `alarm_control_panel` state; it never joins
  an intrusion incident.
- Group tests: N-of-M within the window, expiry of the window, member profiles
  applied below threshold, group profile applied at threshold, and the cross-zone
  field producing identical results to the equivalent 2-of-2 group — the assertion
  that keeps the two configuration surfaces on one engine.
- Chime fires only while the zone is unmonitored by the active scenario, and never
  during a walk test.
- A test asserting the watchdog payload is empty unless explicitly enabled.
- RF interference tests: N zones on one radio going unavailable inside the window
  raises the event; the same pattern with the coordinator ALSO unavailable reports
  a coordinator failure instead; zones spread across two radios do not trigger it;
  and a Zigbee event never notifies through a Zigbee target.
- A test asserting diagnostics output contains no code hashes and no personal names.
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

**Scoped honestly, and this wording belongs in the README.** It reads
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
