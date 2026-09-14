# Foyer Home Defender — build prompts for Claude Code

Six prompts, one per phase. Each produces something installable. Do not run a
later prompt before the earlier one's acceptance criteria pass — the phases are
ordered so that each one's foundations are already tested when the next begins.

`docs/SPEC.md` is the source of truth. These prompts scope and sequence the work;
they never restate the spec, and where they appear to disagree with it, the spec
wins and the disagreement is a bug in this file worth reporting.

---

## How to run a session

Start **every** session — including a continuation — by pasting the preamble
below, then the phase prompt. A fresh Claude Code session knows nothing about the
previous one.

### Session preamble (paste first, every time)

```
Read docs/SPEC.md in full before writing any code. It is the source of truth for
this project and it is long; read all of it, not the parts that look relevant.

Six invariants in §2 are non-negotiable. They are not style preferences — each one,
if broken, disables a headline feature and requires a rewrite rather than a patch:

  INV-1  core/ is pure. decide() takes a snapshot and returns a Decision. It
         executes nothing, performs no I/O, reads no clock it was not given, and
         imports nothing from homeassistant.*. A separate executor performs side
         effects; a separate scheduler owns timers. This is what makes the
         simulator structurally honest rather than hopeful.
  INV-2  Codes are verified in the backend only. Every service and every
         WebSocket command that changes state or configuration validates the code
         server-side. Cards transmit; they never decide.
  INV-3  State survives restarts, and the restart gap is logged.
  INV-4  unavailable / unknown / supervision timeout is a FAULT, never "all quiet".
  INV-5  Never assume on means alarm. Every zone declares its own trigger state.
  INV-6  The threat model is stated in the README, not implied.

Working rules for this session:
- Work on a branch named for the phase. Commit in small, working increments with
  messages that say why, not what.
- Write the test before or alongside the code for anything in core/. core/ must be
  testable with no Home Assistant instance running.
- If the spec is ambiguous or self-contradictory, stop and ask. Do not choose for
  me and carry on — an ambiguity resolved silently in a security system is how a
  wrong assumption gets buried under a thousand lines.
- Do not implement anything belonging to a later phase, even when it is one line
  away. Scope discipline is what keeps each phase verifiable.
- At the end, report: what you built, what you did not build and why, and anything
  in the spec you think is wrong.
```

---

## Phase 0 — Walking skeleton

**Purpose: de-risk the stack, not deliver features.** The chain Python →
WebSocket API → sidebar SPA → Lovelace card is where a custom Home Assistant
integration gets stuck: panel registration, the frontend build, authentication,
reload behaviour. Prove it end to end with the least code possible, before there
are eleven pages riding on it.

```
Build Phase 0 of Foyer Home Defender: a walking skeleton that proves the whole
technical chain with one hard-coded area, one zone, one scenario and one action.

Deliver:

1. custom_components/foyer/ loading via a config flow, with the repository layout
   and technology choices from SPEC §3. manifest.json, hacs.json, Apache-2.0
   LICENSE and NOTICE.
2. core/engine.py exposing decide(snapshot, event, config, now) -> Decision as a
   pure function, with real unit tests that run without Home Assistant. Even at
   this size it must be genuinely pure: the CI check that core/ imports nothing
   from homeassistant.* ships in this phase, not later.
3. Config persistence through the HA Store helper, with a schema version and a
   migration hook that is empty but wired.
4. One alarm_control_panel entity that arms and disarms through the engine.
5. A sidebar panel registered with docs/logo/foyer-hd-icon.svg, built with Vite,
   that loads and reads live state over a foyer/* WebSocket command.
6. foyer-card rendering that state and sending an arm command.
7. translations/en.json and it.json wired end to end, including one help.<page>
   entry, so that no English string is ever hard-coded in a component. CI fails if
   the two files' key sets diverge.
8. CI: hassfest, HACS validation, pytest, ruff, frontend build.

Done when: installable from a local HACS custom repository; arming from the card
changes the entity state; the panel reflects it live without a reload; CI is green.

Do not build: areas beyond the one, zone types, delays, profiles, users, codes,
MQTT, the log, or any panel page beyond a single screen showing state.
```

---

## Phase 1 — Alarm core

The largest phase, and the one that makes the project real: at the end of it a
house can actually be protected. Everything here touches the state machine, which
is why several items that look like features (technical channel, incidents,
groups, chime) sit in this phase rather than later — retrofitting any of them
means reworking the machine.

```
Build Phase 1 of Foyer Home Defender: the complete alarm core.

Scope, all per SPEC:
- Zones (§4.2, §4.3): all eight type presets as UI sugar over editable properties,
  TriggerSpec in all three forms (§4.4), the zone wizard proposing a trigger from
  device_class and REQUIRING confirmation (INV-5).
- Areas with independent state (§4.5), scenarios (§4.6), key zones (§4.7).
- Verification groups N-of-M (§4.8), with the zone's cross-zone field evaluated
  by the same group engine as a degenerate 2-of-2 group. One engine, two ways to
  configure it. A test must assert the two paths produce identical results.
- The full state machine (§5): transitions, timers with their bounds, arming
  preconditions and all four arm policies including arm_after_closing, forced arm
  as a distinct permissioned command, alarm memory after siren cutoff.
- The technical alarm channel (§5.5): entirely separate state, entities, memory
  and acknowledgement. It never touches alarm_control_panel, it is live whether
  armed or not, and disarming does not clear it.
- Incidents (§5.6): the first trigger opens one, later triggers join it, actions
  union without restarting what is already running, the highest-severity
  contributing profile supplies the escalation, one acknowledgement closes it.
- Response profiles (§6) with inheritance, the nine actions including the
  call_service escape hatch, the two conditions and no more (§6.3), templates
  (§6.4), profile severity (§6.5), chime (§6.6).
- Timed temporary bypass, with automatic return and notification.
- State persistence across restart with the restart gap logged (INV-3).
- The SQLite event log (§10.1–10.3) with its categories, per-category retention,
  incident ids on rows, and CSV/JSON export.
- Panel pages 1–5, 10–11 and 13, each with its collapsible help panel (§15.2),
  sourced from the translation files.
- The first-run wizard (§15.1) and JSON config backup/restore.
- Card layouts full and compact.

Done when: a real house can be protected with it. Specifically: multiple areas arm
independently on a scenario; a delayed zone grants entry delay while an instant one
does not; an open zone blocks, bypasses, waits or is ignored per its policy; a
group produces graduated response; two zones in one break-in produce one incident;
a smoke detector fires while disarmed and survives a disarm; every state change is
in the log with who and through which channel; and Home Assistant can be restarted
mid-armed without losing the alarm.

Do not build: users, codes, permissions, keypads, MQTT, the simulator, walk test,
contacts, escalation or automatic rules. Notifications in this phase go to a
notify service directly, with no contact book and no escalation.
```

---

## Phase 2 — Security and arming channels

```
Build Phase 2 of Foyer Home Defender: identity, codes and physical arming.

Scope, all per SPEC §8 and §9:
- Users (§8.1): one code per user, bcrypt-hashed, never returned by any API.
  Codes unique across users, rejected at save time without revealing whose code
  it collided with. Global code length. Per-user duress code under the same
  uniqueness rule.
- Code policy resolution (§8.2) with the per-user override applying ONLY on
  channels that identify the user. On a shared keypad the code is the identity, so
  the exemption cannot apply — and the configuration UI must say so where the
  setting is, not in the documentation, or it reads as a bug.
- Permissions (§8.3) enforced on every service AND every WebSocket command, not
  only in the UI.
- Lockout (§8.4) with exponential backoff, raising an event a profile can act on,
  and never locking out the Home Assistant admin path.
- The service contract (§9.1) with structured results, and the MQTT contract
  (§9.2) in both directions, with configurable topics and the outbound feedback
  that lets a keypad distinguish a wrong code from arming blocked by an open zone.
- Shipped adapters (§9.3): Ring Alarm Keypad v2 over Z-Wave JS with LED, beeps and
  countdown; a generic Zigbee keypad over Zigbee2MQTT; NFC tags and remotes via
  tag and event entities.
- Panel pages 7 and 8. Card layouts badge and keypad.

Security tests are part of the deliverable, not a follow-up: wrong code, missing
code, expired user, insufficient permission and locked-out channel are each
rejected; and no code or hash appears in any API response, log row or diagnostic.

Done when: arming and disarming from a physical keypad works with correct feedback
on the keypad itself, and the log attributes every action to a person and a channel.

Do not build: the simulator, walk test, contacts, escalation, or automatic rules.
```

---

## Phase 3 — Test and simulation

The project's strongest differentiator, and the phase that pays back INV-1.

```
Build Phase 3 of Foyer Home Defender: the verification tooling (SPEC §11).

- Live zone diagnostics (§11.1): every mapped zone with live state, the resolved
  trigger evaluation, last change, availability, battery, supervision status and
  whether it currently blocks arming.
- The simulator (§11.2): virtual zone state overrides, a hypothetical scenario,
  a hypothetical clock, and overrides for entities used in conditions. Output is
  the full decision chain — which zone, which delay, which effective profile and
  where it was inherited from, which actions ran, which were skipped AND WHY, and
  the future escalation steps with their timings. Group evaluation appears in the
  trace, not just the zone. Incident opening and joining appear in the trace.

  This MUST be the same decide() the runtime calls, with a fabricated snapshot and
  clock, whose Decision is simply never handed to the executor. If you find
  yourself writing a second evaluation path for the simulator, stop: INV-1 has
  been broken somewhere upstream and that is the bug to fix.

- Walk test (§11.3): genuinely armed, real sensor states, all response actions
  inhibited, recording which zones detected and highlighting those that never did.
  With the mandatory safeguards: automatic exit timeout that cannot be disabled, an
  unmissable banner in the panel and on every card, entry and exit logged with the
  user, notification on start and end, and 24h, tamper, technical and panic zones
  remaining fully live.
- Real action test (§11.4): a test button beside every action and every contact
  channel. It really executes, so it requires confirmation, requires the
  test_actions permission, and is logged as a test.
- Panel page 9 with its four tabs.

Done when: a forty-zone configuration can be verified without triggering anything,
and the trace explains a skipped action well enough to act on.
```

---

## Phase 4 — Contacts, escalation and automatic rules

These two land together because they share one mechanism: the actionable
notification with a countdown and a button. Building it twice would be waste.

```
Build Phase 4 of Foyer Home Defender: escalation and automatic arming.

Contacts and escalation (SPEC §7):
- The contact book: people, channels in priority order discovered from the
  notify.* service registry, quiet hours, optional link to a Foyer user.
- Escalation policies as ordered steps, stopping immediately on acknowledgement.
- Acknowledgement through all four paths: an action button in a push notification,
  disarming through any channel, a DTMF keypress fed back by webhook, and the
  foyer.acknowledge service. Every acknowledgement records who and through which
  channel.
- escalation_exhausted as an event profiles can act on.
- Panel page 6, and docs/notification-channels.md with working recipes for the
  Companion app including iOS critical alerts, Pushover priority 2, Twilio SMS,
  Twilio voice, a USB GSM modem, Telegram and Signal.

Automatic arming rules (SPEC §9.4):
- The closed rule model: triggers, actions, active window, guards, grace period,
  suspensions, expected-visitor windows.
- switch.foyer_auto_arming and sensor.foyer_next_auto_action.
- Rules that ACT are logged under arming with channel auto_rule; rules BLOCKED by
  a guard are logged under system, because "why did it not arm last night?" is a
  question people ask.
- Automatic disarming is off by default, warns explicitly when enabled, and can
  never act on an area flagged is_perimeter. Enforce that in the engine, not the
  UI, and write the regression test that asserts it directly: a disarm rule naming
  a perimeter area produces a Decision that does not disarm it.
- Panel page 12.

Done when: an unacknowledged alarm escalates from push to SMS to voice call across
several people and stops the instant someone acknowledges; and an empty house arms
itself after the configured delay, announces it first with a cancellable countdown,
and skips the morning the boiler engineer is expected.
```

---

## Phase 5 — Hardening and release readiness

Not features. The difference between a repository and something a stranger can
rely on.

```
Build Phase 5 of Foyer Home Defender: system health, privacy and release readiness.

System health (SPEC §12) — treat it as a concept distinct from zones: none of this
is an intrusion and none of it may enter the intrusion queue.
- Mains power and UPS (§12.1), raising system_power_lost.
- Notification channel health (§12.2): the notify service still exists, the modem
  is registered, the last send succeeded. A broken channel is surfaced on the
  Contacts page and, when it is part of an escalation policy, announced through a
  DIFFERENT channel — warning someone about a dead channel over the dead channel
  is the joke that writes itself.
- The external watchdog (§12.3): a configurable URL, empty payload by default,
  optional state payload only behind an explicit warning that it tells a third
  party when the house is empty. Foyer also reports locally when it repeatedly
  cannot reach the endpoint.
- Repair issues and anonymised diagnostics (§12.4). Test that the diagnostic
  output contains no code hashes and no personal names.
- Panel page 14.

Privacy (SPEC §10.4): targeted deletion of one person's history as an action
distinct from deleting the user, optional timed pseudonymisation off by default,
per-person export, and docs/privacy.md explaining the household exemption and the
point at which it stops applying.

Clean uninstall: entities removed from the registry, timers stopped, MQTT
subscriptions closed, and the user explicitly asked whether to keep or delete the
log database.

Alarmo import (§20.2): reads an existing Alarmo configuration and converts it to
Foyer areas, zones and scenarios, REPORTING everything it could not map. It reads
an internal storage format that may change in any upstream release, without notice
and without fault, so build it as an explicitly best-effort tool and say so in the
README and in docs/migrating-from-alarmo.md. Never present it as a guaranteed
migration.

Contributor infrastructure (§20.3): issue templates demanding version, logs and
the diagnostics download; CONTRIBUTING.md covering the dev setup, the core/ purity
rule and test expectations; a documented no-code flow for adding a language.

Documentation (§18) complete, with docs/security-model.md stating the threat model
plainly (INV-6) and the non-negotiable statement that Foyer is not a fire alarm
system and does not replace certified interconnected smoke alarms.

Done when: a person who has never spoken to the author can install it, hit a
problem, and file an issue that is answerable without five rounds of questions.
```

---

## If a phase turns out too big

Phase 1 is the one most likely to overflow a working session. Split it in this
order, each part still leaving something that runs:

1. Zones, areas, scenarios, state machine, delays, arm policies, persistence.
2. Technical channel, incidents, verification groups, chime.
3. Response profiles, conditions, action catalogue, timed bypass.
4. The SQLite log, panel pages, wizard, cards.

Do not split it by layer — backend first, then frontend — because that produces
two halves neither of which can be verified until both are done.

---

## Session appendices

A fresh session knows the spec but not what earlier sessions decided or
discovered. When a phase (or part of one) is run, paste in this order: the
session preamble, the phase prompt, then the appendix for that session below.
Each appendix is written at the end of the session before it.

### Phase 1, part 1

```
Scope for THIS session: Phase 1, part 1 only, as listed under "If a phase turns
out too big" in docs/PROMPTS.md — zones, areas, scenarios, the state machine,
delays, arm policies and persistence. Parts 2–4 are separate sessions. The full
Phase 1 prompt above is context for the design, so that part 1 does not paint
later parts into a corner; it is not this session's to-do list.

Context from Phase 0 (released as v0.0.1, accepted on a real Home Assistant):
- Work on a new branch phase-1 from master.
- Commit as Foyer Labs <foyerlabs@gmail.com>; it is already set in the repo's
  local git config. Never commit with any other identity.
- INV-3 was knowingly deferred from Phase 0: today area state lives in memory
  and a restart disarms everything. Persisting state, and logging the restart
  gap once the log exists, is the first thing this phase must fix.
- Panel, card, help and notification strings live in
  translations/panel/<lang>.json, not translations/<lang>.json, because
  hassfest rejects extra top-level keys there (SPEC §15.2, decision 35).
- Real installations already exist with the Phase 0 stored config, schema
  version 1.1 in .storage/foyer.config. They must be migrated through the
  existing hook in store/migrations, with a test, never silently broken or
  reset.
- The Phase 0 code policy (no code for arm or disarm, enforced fail-closed in
  the engine) stays as it is: codes and users are Phase 2.
- Home Assistant integration tests do not run on Windows. See the project
  memory for the WSL environments (HA 2025.1.4 and latest) and the hassfest
  checkout; CI runs all of it on every push.
```

### Phase 1, part 2

```
Scope for THIS session: Phase 1, part 2 only — the technical channel (§5.5),
incidents with profile severity (§5.6), verification groups with the
cross-zone field built on them (§4.8) and panel page 13, and chime (§6.6).
Trigger counting (trigger_count / trigger_window, §4.2) also lands here: it
is windowed activation counting and must share the group engine's
machinery rather than grow a second one. Parts 3-4 are separate sessions.

Context from part 1 (branch phase-1):
- Continue on branch phase-1. Commit as Foyer Labs <foyerlabs@gmail.com>.
- The user resolved these spec ambiguities before part 1; they are binding
  and the spec has not yet been amended to match:
  1. Zone type is a preset label only. The engine reads explicit
     properties: channel (intrusion | technical | key), entry_mode
     (instant | delayed | follower), alarm_kind (intrusion | tamper | panic).
  2. Siren cutoff returns an area to its pre-trigger state (disarmed stays
     disarmed with alarm memory; armed/entry -> armed; arming resumes).
     Disarm clears memory and is accepted on a disarmed area holding it.
  3. arm_after_closing completes when the exit delay has elapsed AND the
     zone has closed; it fails like block after a cap, per zone with a
     global default of 300 s.
  4. An area's own alarm_control_panel arms only that area, outside any
     scenario. Scenarios are armed from the master, select.foyer_scenario,
     the panel and the card.
  5. Zone-level exit_delay is dropped. Exit = scenario override ?? area.
  6. Forced arm and scenario change need no code until Phase 2.
  7. The master's arm_<mode> is refused when two scenarios share the mode.
  8. Switching scenario A -> B while armed disarms areas armed by A that B
     does not list; areas armed on their own are untouched.
  9. The master reports armed_custom_bypass whenever the armed set differs
     from the active scenario's areas.
  10. Supervision resets on any report (HA last_reported), not only on a
      state change.
  11. EventTrigger: event.* matches the event_type attribute; tag.* fires
      on every scan; subtype is refused by validation for now.
  12. A key zone's disarm and toggle act on every area.
- The technical type exists as a preset but validation refuses channel
  "technical" (problem channel_not_available) and the panel greys it out,
  because a stored smoke detector that does nothing is worse than none.
  Part 2 lifts that refusal when the channel exists.
- Engine shape: decide() returns the complete RuntimeState, persisted
  verbatim in .storage/foyer.state; timers are data (Timer on AreaRuntime)
  and the scheduler wakes at core.engine.next_wakeup(). Every decision emits
  Occurrences (moment + area/zone/scenario/channel/detail): these become log
  rows in part 4 and the input of response profiles in part 3. Incidents
  should hang off them, not bypass them.
- Panel pages 1-4 already exist (the user moved 2-4 into part 1). Part 4
  keeps the log, settings (page 11), the first-run wizard, backup/restore,
  pages 5 and 10, and the card layouts full and compact.
- Config edits reload the entry; the status subscription is bound to a
  dispatcher signal so it survives. Edits touching an armed area or the
  running scenario are refused (core.validation.edit_conflicts).
```
