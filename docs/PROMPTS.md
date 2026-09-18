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

**Complete and accepted**, in four parts, released as `v0.1.0-alpha.11`
(configuration schema 4.2). The acceptance is `tests/ha/test_acceptance.py`,
and the user ran the whole of it on their own installation: every point passed
except the technical channel, which they could not exercise physically and
which is covered by tests.

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

1. Zones, areas, scenarios, state machine, delays, arm policies, persistence —
   with panel pages 1–4 (overview, areas, zones, scenarios) and the card
   updated for the new states.
2. Technical channel, incidents, verification groups (page 13), chime (with
   its block of the settings page).
3. Response profiles (page 5), conditions, action catalogue, timed bypass.
4. The SQLite log (page 10), settings (page 11), the first-run wizard, config
   backup/restore, card layouts full and compact.

Phase 2 overflows a session too, and splits in two:

1. Identity and codes: users, the per-operation code policy, permissions,
   lockout, panel page 7, and the card's keypad — after which a person with a
   code can arm and disarm, and the log says who.
2. The physical channels: the service and MQTT contracts, panel page 8, the
   shipped keypad adapters and the card's badge layout — after which the
   keypad by the door works.

Each panel page ships in the part that builds its feature. Do not split by
layer — backend first, then frontend — because that produces two halves
neither of which can be verified until both are done: a part is finished only
when it can be used on a real Home Assistant, not only tested. The appendices
below are the authoritative scope of each part.

---

## Session appendices

A fresh session knows the spec but not what earlier sessions decided or
discovered. When a phase (or part of one) is run, paste in this order: the
session preamble, the phase prompt, then the appendix for that session below,
then any shared block the appendix names. Each appendix is written at the end
of the session before it.

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

### Phase 1 decisions (paste after the appendix, in every session from Phase 1 part 2 on)

```
Binding decisions taken by the user in Phase 1. The spec has been amended to
match (SPEC §21, decisions 36-60); this list is the quick reference. None of
them may be "fixed back" without asking.

 1. Zone type is a preset label only. The engine reads explicit properties:
    channel (intrusion | technical | key), entry_mode (instant | delayed |
    follower), alarm_kind (intrusion | tamper | panic). Validation rejects
    combinations that make no sense.
 2. Siren cutoff returns an area to its pre-trigger state: disarmed stays
    disarmed with alarm memory; armed or entry -> armed; arming resumes with
    the normal expiry checks. Disarm clears memory and is accepted on a
    disarmed area that holds it.
 3. arm_after_closing completes when the exit delay has elapsed AND the zone
    has closed; if still open after a cap it fails like block. The cap is per
    zone (arm_hold_timeout), inheriting a global default of 300 s (60-1800).
 4. An area's own alarm_control_panel arms only that area, outside any
    scenario. Scenarios are armed from the master, select.foyer_scenario, the
    panel and the card.
 5. Zone-level exit_delay is dropped. Exit delay = scenario override ?? area.
 6. Forced arm and scenario change while armed need no code until Phase 2.
    Forced arm stays a distinct command and is recorded as forced.
 7. The master's arm_<mode> is refused when two scenarios share the mode, and
    the master only advertises unambiguous modes.
 8. Switching scenario A -> B while armed: areas armed by A and absent from B
    are disarmed, shared ones stay armed, B's new ones go through their exit
    delay; areas armed on their own are untouched. Refused while any affected
    area is in entry or triggered.
 9. The master reports armed_custom_bypass whenever the armed set differs from
    the active scenario's areas; select.foyer_scenario keeps the scenario.
10. Supervision resets on any report (HA last_reported), not only on a state
    change.
11. EventTrigger: event.* fires on each new event whose event_type attribute
    matches; tag.* fires on every scan. There is no subtype (removed from
    the spec by the user).
15. Supervision is set per sensor and is off by default; there is no
    per-zone exit delay.
16. A follower inherits its own area's entry window and, through its
    `follows` list, the running entry window of the delayed zones it follows
    in other areas (same deadline; the earliest if several). Areas are meant
    to be grouped by function (perimeter, interiors), not by room.
12. A key zone's disarm and toggle act on every area; toggle disarms all if
    any area is armed, otherwise arms its scenario.
13. Each panel page ships in the part that builds its feature (see "If a
    phase turns out too big").
14. A zone's first readable value is its baseline, not an activation (so a
    newly saved key zone already "on" does not arm the house).

Taken in part 2 (SPEC decisions 48-59):
17. A technical zone in fault blocks arming its area like any zone, unless
    allow_arm_when_faulted.
18. One technical acknowledgement acts on every technical alarm pending then.
19. An incident opens at triggered, never at entry_started; the zones of an
    expired entry route contribute.
20. Disarming an area the incident touched acknowledges the incident, and
    only such an area: disarming an area it never touched does not.
21. A zone joining after the acknowledgement clears it (history kept).
22. Cross-zone is symmetric (A->B forms {A,B}) and never suppresses: each
    zone still alarms alone. Suppression is only an explicit group's
    suppress_members.
23. A non-suppressed group member alarms normally (area -> triggered/entry,
    incident opens); the satisfied group adds its own Occurrence.
24. Only activations that would alarm at once count towards a group or a
    trigger_count; entry-absorbed ones act normally and never count.
25. Group members may be in different areas; each acts in its own and
    counts only while its area watches it.
26. Chime is read per area; chiming during the exit delay is a global
    setting, off by default.
27. Until response profiles exist, technical_raised has a persistent
    notification (added to the Phase 0 action by the 2.2 -> 3.1 migration);
    part 3 must move it into the technical default profile.
28. Group membership is stored once, on the group (members); a zone's
    group_id is derived.
29. A technical zone's first reading is a baseline like any zone's (decision
    14); the zone editor tells the user to save it while the detector is quiet.
31. Schema 3.1 (major bump, though additive): an older build must refuse the
    file rather than ignore technical zones.
32. button.foyer_acknowledge is deferred to Phase 2 (see carry-overs).

Taken in part 3 (SPEC decisions 61-71):
33. The AREA is the unit of response: area -> scenario -> global default. A
    zone's own profile is read only for its own alarm (triggered,
    entry_started, a group it satisfies). One rule, and it is where
    graduated response needs it.
34. The technical channel answers with the zone's profile, else a dedicated
    global technical profile, else the default. Never the scenario's.
35. The default profile notifies `triggered` too (Phase 0 did not).
36. An action's two conditions combine with a selectable and/or.
37. Action delays and switch auto-reverts are persisted timers, like every
    other timer: data in the runtime state, one wake-up.
38. What a `silent` zone suppresses is a global list of action kinds
    (siren, tts, chime by default), not a per-action flag.
39. Camera files go to a configurable folder, media/foyer by default, never
    www. A notification attaches /api/camera_proxy/<entity>, not a file.
40. Each chime target may carry quiet hours of its own, replacing the
    global window.
41. Manual bypass needs no code until Phase 2, and still runs through
    check_code (Operation.BYPASS_ZONE).
42. A manual bypass without a duration ends when the area is disarmed; one
    with a duration survives the disarm until it expires. Closing the zone
    never cancels either.
43. persistent_notification is a tenth action kind, so the Phase 0
    notification survives the 3.1 -> 4.1 migration unchanged.

Engine and runtime shape after part 1 (do not work around it):
- decide(snapshot, event, config, now) returns a Decision holding the
  COMPLETE next RuntimeState; the runtime persists it verbatim in
  .storage/foyer.state (saved on every change, alive stamp every 5 min).
- Timers are data (Timer on AreaRuntime); the scheduler wakes once at
  core.engine.next_wakeup() and sends Tick. New timers (bypass expiry,
  action delays, group windows) must follow the same pattern.
- Every decision emits Occurrences (moment, area, zone, scenario, zone_ids,
  channel, detail). They are the single source for notifications today, for
  response profiles in part 3 and for log rows in part 4. New behaviour adds
  Occurrences; it never bypasses them.
- Configuration is stored as schema 3.1 in .storage/foyer.config; every
  schema change is a new step in store/migrations with a test that migrates a
  real previous document. Config edits go through store/editing.py (pure,
  validated) and reload the entry; edits touching an armed area or the
  running scenario are refused (core.validation.edit_conflicts).
- The status subscription is bound to the SIGNAL_UPDATE dispatcher signal so
  it survives reloads.
- Tests: tests/core and tests/repo run with no Home Assistant; tests/ha run in
  WSL (see project memory) on HA 2025.1.4 and the latest release.

Added in part 2:
- RuntimeState also holds technical (the technical channel, never in an
  AreaRuntime), incident + incident_seq, windows (verification activations)
  and chime_enabled. The state file keeps version 1.1; new keys are read
  with defaults, so an older file restores safely.
- core/verification.py is the ONE windowed engine for groups, cross-zone
  pairs (derived id "cross:<a>+<b>") and trigger counts. Windows expire
  through next_wakeup like timers. A test asserts cross-zone == 2-of-2.
- Incident contributors carry profile_id and severity (None until part 3)
  and the incident carries actions_started (empty until part 3): fill them,
  do not reshape them. Every occurrence in an incident's area carries
  incident_id; the technical channel's never do.
- Occurrence gained incident_id and group_id; ActionIntent gained params
  (the chime's targets travel in the Decision, the executor looks up
  nothing).
- SystemSnapshot carries the installation's timezone; core/clock.py has
  in_daily_window() for quiet hours, to be reused by part 3's time
  conditions.
- Operation.ACKNOWLEDGE runs through check_code for both acknowledgements
  (foyer/acknowledge with target incident | technical).

Added in part 3:
- core/response.py is the ONE place that turns Occurrences into
  ActionIntents: it resolves the profile, evaluates the conditions, renders
  the templates and produces the complete instruction. The executor looks
  nothing up. New behaviour adds to the plan; it never calls a service
  directly.
- core/conditions.py and core/templates.py are pure and are what the
  simulator (Phase 3) will show in its trace: response.condition_summary()
  already says WHY an action was skipped.
- RuntimeState gained pending_runs (a sequence a delay holds), running
  (what an action switched on and must switch off), bypass_until and
  run_seq. All four go through next_wakeup like any timer.
- Incident contributors now carry profile_id and severity, filled as each
  zone joins; Incident.actions_started is filled by the planner, which is
  what deduplicates a siren already sounding (SPEC §5.6).
- The stored configuration is schema 4.1: `actions` is gone and `profiles`
  replaces it, settings gained default_profile_id, technical_profile_id,
  silent_suppresses and camera_dir, and chime targets are objects with
  their own quiet hours.
- The panel has pages Overview, Areas, Zones, Scenarios, Response profiles,
  Verification groups and Settings (chime plus the response block).

Taken in part 4 (SPEC decisions 72-76):
44. The event log uses the stdlib `sqlite3` in an executor thread, not
    aiosqlite. It is what Home Assistant's recorder does, and it adds no
    dependency: an integration that fails to load because a wheel could not
    be fetched at first setup is a failure mode an alarm does not need.
    SPEC §3.2 was amended.
45. The "language" setting of §15.1 is the language of what Foyer SENDS
    (notifications, the spoken zone name), never the panel's: the panel
    follows each Home Assistant user. Default: the system language.
46. The first-run wizard continues from the config flow, which keeps
    creating one area, one zone and one scenario. `settings.wizard_done`
    (installation state, not a preference) hides it once it is finished or
    dismissed; the 4.1 -> 4.2 migration sets it true, because an
    installation that already has zones is not a first run.
47. Log retention is 30 days for every category, the letter of §10.3, and
    `zone_disarmed` is the one category off by default (§10.2).
48. The sidebar panel icon is `mdi:shield-home`. Home Assistant resolves a
    custom icon once and never retries, so a sidebar drawn before the icon
    module has run keeps an empty square for ever — which is what the
    companion app does from a cached page. `foyer:shield` stays registered
    for dashboards; the shield is drawn inline in the panel and the card.
49. The log's schema is §10.1 plus an `incident_id` column: §5.6 wants the
    incident id on every related row and a JSON field cannot be filtered on.
    A refused request gets a row of its own, in the category of the request.

Engine and runtime shape after part 4 (do not work around it):
- core/journal.py is pure and is the ONE place that says what a row IS: its
  category, its severity, its event type and its outcome. A test asserts
  every Moment has a category and a severity, so a moment added later
  cannot vanish from the log. New behaviour adds to the tables.
- store/log_store.py owns the database (`<config>/foyer-log.db`), the write
  queue and the daily purge. Writing is a hand-off: the alarm path queues
  and returns. Reading flushes first, under the same lock the writer holds.
- FoyerSystem.async_record(rows) is how anything reaches the log; it also
  keeps `last_row` for sensor.foyer_last_event. Config edits are recorded in
  api/websocket.py `_apply`, with store/editing.config_diff for the summary.
- The stored configuration is schema 4.2 (minor, additive): settings gained
  `log` (per-category enabled + retention_days, read sparse so a category
  nobody touched follows §10.2), `default_entry_delay`, `default_exit_delay`,
  `language` and `wizard_done`.
- The panel has all of pages 1-5, 10, 11 and 13, plus the wizard, and the
  card has layouts full and compact with a visual editor.
- tests/ha/test_acceptance.py is the Phase 1 acceptance, written against the
  WebSocket API rather than the engine: keep it passing, and add to it when a
  later phase changes what "a real house can be protected" means.
```

### Phase 1, part 2

```
Scope for THIS session: Phase 1, part 2 — the technical channel, incidents,
verification groups (with cross-zone and trigger counting on the same
engine), chime, panel page 13 and the chime settings. Parts 3 and 4 are
separate sessions. Paste "Phase 1 decisions" after this appendix.

Continue on branch phase-1. Commit as Foyer Labs <foyerlabs@gmail.com>.

1. Technical channel (SPEC §5.5), a separate machine, not an area state:
   - Lift the part-1 refusal: validation currently rejects channel
     "technical" (problem channel_not_available) and the panel greys the
     type out. Only lift it once the channel below works end to end.
   - Its own runtime state inside RuntimeState (persisted, INV-3): which
     technical zones are in alarm, which are in memory, which are
     acknowledged. It never appears in AreaRuntime, never reaches
     master_state() and never changes any alarm_control_panel.
   - Live whatever the arming state: disarmed, arming, armed, entry,
     triggered.
   - Disarming has no authority over it. Clearing needs BOTH an explicit
     acknowledgement AND the entity back to normal; until both, the alarm
     and its memory persist and are visible on every card and on the
     overview page.
   - Entities: binary_sensor.foyer_technical_alarm and
     sensor.foyer_technical_cause (the zone name).
   - An acknowledgement command over WebSocket and a panel/card button. The
     code policy for it is a Phase 2 question; until then it follows the
     Phase 1 rule (no code), and the engine must still route it through the
     code check so Phase 2 only changes policy, not plumbing.
   - Occurrences for technical alarm raised, acknowledged and cleared, so
     part 3 can attach a technical response profile and part 4 can log them.
   - A technical alarm and an intrusion incident can be active at once and
     never merge.
   - The mandatory statement that Foyer is not a fire alarm system appears in
     the zone editor wherever a technical zone is configured.
   OPEN QUESTION for the user before building: does a technical zone in
   fault (INV-4) block intrusion arming? INV-4 says every zone fault blocks
   arming; a flooded-basement sensor with a dead battery blocking "Away" may
   or may not be what they want.

2. Incidents (SPEC §5.6):
   - The first intrusion trigger opens an incident; later triggers join it
     (zone added, notification text updated, nothing restarted).
   - Every related Occurrence carries the incident id, so part 4 can put it on
     every log row.
   - Persisted (INV-3); exposed as sensor.foyer_incident with contributing
     zones and severity as attributes.
   - One acknowledgement closes the whole incident. It closes when
     acknowledged AND every contributing area is disarmed or back to armed;
     a trigger after that opens a new incident.
   - Severity: the incident records, for part 3 to fill, the effective
     profile of each contributing zone; "highest-severity contributing
     profile supplies the escalation" becomes real in part 3 (profiles) and
     Phase 4 (escalation). Shape the data now so neither needs a migration of
     the incident model.
   - Action union without restarting what runs is an executor concern that
     lands with the actions in part 3; the incident must already record which
     actions it has started.
   - Technical alarms never join an intrusion incident.
   OPEN QUESTIONS for the user before building: does an entry delay starting
   open the incident, or only the transition to triggered? Does disarming
   count as the acknowledgement (§7.2 says so for escalation)?

3. Verification groups, cross-zone and trigger counting — ONE engine
   (SPEC §4.8, §4.2):
   - Group {id, name, area_id, members[], n, window_seconds,
     response_profile_id, suppress_members}. response_profile_id is stored
     only when part 3 can act on it; until then a satisfied group emits its
     own Occurrence, and suppress_members decides whether members act alone.
   - Zone fields added: group_id, cross_zone_id, cross_zone_window,
     trigger_count (default 1), trigger_window.
   - cross_zone_id is evaluated by the group code as a degenerate 2-of-2
     group. A test asserts that a zone with cross_zone_id and the equivalent
     explicit 2-of-2 group produce identical Decisions.
   - trigger_count/trigger_window reuse the same windowed-activation state.
   - Window state is persisted and expires by the Timer/next_wakeup pattern.
   - Occurrences carry group state ("1 of 2 within 60 s, not satisfied" /
     "SATISFIED") for the Phase 3 simulator trace.
   OPEN QUESTIONS for the user before building: is cross-zone symmetric (A
   needs B and B needs A) or one-way? Does a cross-zone zone act alone at
   all, i.e. is it suppress_members=true? (The prototype help says "a single
   zone alone will never fire".)

4. Chime (SPEC §6.6):
   - Fires when a zone with chime=true opens while it is not monitored,
     meaning its area is not armed — however that area came to be armed or
     not (decision 4 makes per-area arming possible). No special case for walk
     test: a walk-test area is armed.
   - Global block: targets (media_player or siren), mode single sound or
     spoken zone name via tts.speak, volume, quiet hours; per-zone chime bool.
   - switch.foyer_chime to silence it.
   - The chime is an ActionIntent from decide(); the executor plays it.
   - Its settings need a UI in this part (decision 13): the chime block of
     page 11, the rest of page 11 stays in part 4.

5. Panel page 13 (verification groups) with its help panel, and the chime
   settings, both through translations/panel/<lang>.json in en and it.

6. Storage: schema 2.2 -> 3.1 (additive, but a major bump so that an
   older build refuses the file rather than ignore technical zones; decided
   by the user) with a migration test from a real 2.2 document
   (0.1.0-alpha.2 already took 2.2 for follows); runtime state
   additions default safely on an older .storage/foyer.state.

7. Tests from SPEC §19 for this part: incidents (join, no restart, highest
   severity recorded, one ack closes, new incident after closure), technical
   (fires disarmed, disarm does not clear, never touches any
   alarm_control_panel, never joins an incident), groups (N-of-M in window,
   window expiry, member vs group Occurrences, cross-zone == 2-of-2), trigger
   counting, chime only while unmonitored.
```

### Phase 1, part 3

```
Scope for THIS session: Phase 1, part 3 — response profiles, conditions, the
action catalogue, templates, severity, silent zones, manual and timed
bypass, and panel page 5. Part 4 is a separate session. Paste "Phase 1
decisions" after this appendix.

Context from part 2 (released as v0.1.0-alpha.4):
- Continue on branch phase-1, which is where master and the tag sit. Commit
  as Foyer Labs <foyerlabs@gmail.com>; it is already in the repo's local git
  config. Never commit with any other identity.
- Stored configuration is schema 3.1; the runtime state file is 1.1 and
  grows by keys read with defaults. Every schema change is a new step in
  store/migrations with a test that migrates a real previous document.
- The technical channel, incidents, verification groups and the chime exist
  and are tested: build profiles ON them, do not rebuild them. What part 2
  deliberately left for this part is marked in the code: Contributor
  .profile_id / .severity, Incident.actions_started, and the group's
  response_profile_id, which is not stored yet.
- Until this part, the only response is the Phase 0 persistent notification,
  whose moments now include technical_raised (part 2 decision 10, added by
  the 2.2 -> 3.1 migration). Moving it into the default profiles must keep
  every one of those notifications working, technical included.
- Home Assistant integration tests do not run on Windows. See the project
  memory for the WSL environments (HA 2025.1.4 and latest) and the hassfest
  checkout; CI runs all of it on every push.
- The panel has pages Overview, Areas, Zones, Scenarios, Verification groups
  and Settings (its chime block only). Page 5 joins them here.

1. Response profiles (SPEC §6):
   - Inheritance zone -> area -> scenario -> global default; groups (part 2)
     and the technical channel have their own. Add response_profile_id to
     zones, areas, scenarios and groups now.
   - The UI always shows the effective profile and where it was inherited
     from.
   - Moments per §6.1. Some are produced only later and must be selectable
     but documented as such: code_rejected and lockout (Phase 2),
     walk_test_started/ended and low_battery (Phase 3), escalation_exhausted
     (Phase 4).
   - severity (§6.5): an integer the user orders; it decides which profile an
     incident adopts, nothing else.
   - The Phase 0 NotificationAction (a persistent notification on armed,
     disarmed, zone_fault, arm_failed, zone_bypassed) is migrated into the
     global default profile so behaviour is unchanged, with a migration test.
     "triggered" has no notification today; the default profile should add
     one — ask the user.

2. The nine actions (§6.2): notify (to a notify.* service directly: no
   contact book, no escalation, no actionable buttons until Phase 4), siren
   (duration never beyond the siren cutoff, stopped on cutoff and disarm),
   light, camera (snapshot/record, attachable to notify), scene, switch
   (optional auto-revert), tts, call_service (domain, service, target, data;
   YAML editor), delay.
   - decide() produces the plan; the executor only executes. Delays and
     auto-reverts are timers owned by the scheduler, as data in the runtime
     state (INV-1, INV-3).
   - Within an incident actions are unioned and deduplicated: a siren already
     sounding is not restarted, a light not yet on comes on (§5.6).
   - The executor reports success/failure of every call, for the "action" log
     category in part 4.
   - silent zones (§4.2): the response runs without local sounders.
   - The CHIME gains notify targets here (§6.6, decision 60): the user wants
     the chime on the Companion app and Telegram as well as on speakers,
     because those channels are free and already in the house. Part 2 built
     the chime for media_player and siren only; extend ChimeSettings.targets
     to notify.* services and notify entities, sending the zone name, with
     the same quiet hours and the same switch.foyer_chime. Reuse whatever
     the notify action uses to discover and call them: one path, not two.
   OPEN QUESTION for the user: must a pending delay step survive a restart
   (INV-3 lists "escalation progress", not action sequences)?
   OPEN QUESTION for the user: a chime on the phone fires on every door
   opened while the house is disarmed. Offer it per target (speakers always,
   phone only in some hours), or leave it to quiet hours alone?

3. Conditions (§6.3): at most two per action; time window (after/before,
   crossing midnight) and entity state (is / is_not). core/conditions.py,
   pure, reading entity states from the snapshot — so the snapshot must also
   carry the entities that conditions reference. Tests include midnight.

4. Templates (§6.4): exactly the fixed variable set, including
   incident_zones; no arbitrary Jinja.

5. Bypass:
   - Manual bypass and unbypass of a zone (zone.bypassable enforced) from the
     panel, the card and a WebSocket command; services foyer.bypass_zone and
     foyer.unbypass_zone belong to the Phase 2 service contract.
   - Timed temporary bypass: a duration, automatic return as a Timer, and a
     notification (Occurrence) on return (§16 Phase 1).
   - Manual bypasses are a new BypassReason next to auto_bypass and forced.
   OPEN QUESTION for the user: §8.2 says bypass requires a code by default.
   Fail closed until Phase 2 (bypass unusable), or codeless like decision 6?

6. Panel page 5 (response profiles) with its help panel, en and it.

7. Storage migration with a test from a real previous document.

8. Tests from SPEC §19 for this part: profile inheritance resolution;
   conditions including windows crossing midnight; groups giving graduated
   response — member profiles below the threshold, the group profile at it
   (the Phase 1 "a group produces graduated response" acceptance item needs
   this part); incident action union without restarting a running siren and
   the highest-severity profile adopted; timed bypass returning on time,
   including across a restart; silent zones never reaching a sounder.
```

### Phase 1, part 4

```
Scope for THIS session: Phase 1, part 4 — the event log, panel pages 10 and
11, the first-run wizard, config backup/restore and the card layouts full
and compact. After it, run the Phase 1 acceptance ("a real house can be
protected with it", every bullet of the Phase 1 "Done when"). Paste "Phase 1
decisions" after this appendix.

Context from part 3 (schema 4.1):
- Response profiles, the nine actions plus persistent_notification,
  conditions, templates, silent zones and manual and timed bypass exist and
  are tested. Build the log ON them: the executor already returns an
  ActionResult per intent (ok / error), which is the `action` category of
  §10.2, and every Occurrence already carries its incident id.
- The settings page (11) already has the chime block and the response
  block; part 4 adds the global defaults, log retention and backup/restore
  beside them.
- The notify action exists, so the wizard's "send a test notification" step
  has something to call.
- A pending delay, a running siren and a timed bypass are all in
  .storage/foyer.state; the log must not duplicate them, only record what
  happened.

1. Event log (SPEC §10.1-10.3):
   - Dedicated SQLite through aiosqlite with the §10.1 schema and indices.
     Check first that aiosqlite can be declared in manifest.json for both HA
     versions tested; if not, ask before substituting anything.
   - Rows come from Occurrences plus: refused requests (outcome blocked /
     failed with the reason), executor results (category action), config
     edits with who and a diff summary (category config), and raw zone state
     changes (zone_armed on by default, zone_disarmed OFF by default).
   - The restart gap: every HA_RESTARTED Occurrence carries down_since, up_at
     and cause (ha_start | reload); log it as system_unavailable from T1 to T2.
     INV-3 is only complete once this lands.
   - Incident ids from part 2 on every related row; channel on every row;
     user_name denormalised (users arrive in Phase 2; the column exists now).
   - Per-category retention (default 30 days), daily purge, CSV/JSON export
     honouring the current filters, deleting the log is an edit_config
     operation and is itself logged.
   - Every write also fires the foyer_event HA event (§10.3, §14.2).
   - A log failure must never block or delay the alarm path.
   - sensor.foyer_last_event.

2. Page 10 (log): filters by date, area, zone, user, category, outcome;
   export. Page 11 (settings): global defaults (siren duration, the
   arm_after_closing wait default, default delays for new areas), log
   retention per category, backup/restore; the chime block already exists
   from part 2. The WebSocket command foyer/config/settings exists since
   part 1. §15.1 lists "language" on page 11: the UI follows each Home
   Assistant user's language today — ask the user what that setting is for.

3. First-run wizard (§15.1): area -> three zones with confirmed triggers ->
   one scenario -> (user with a code: Phase 2, skip and say so) -> send a
   test notification (part 3's notify action). Decide with the user how it
   relates to the config flow, which today seeds one area, zone and scenario.

4. Config backup/restore: JSON export of the stored document with its schema
   version; import goes through store/migrations, then validation, then the
   armed-area guard, never around them. Admin only now; the
   foyer.export_config / foyer.import_config services and their code check
   belong to Phase 2's service contract.

5. Card layouts full and compact (§15.3) with a visual editor. full: area
   states, scenario selector, not-ready list, countdown (keypad needs codes:
   Phase 2). compact: state, arm/disarm, scenario dropdown. Clear feedback on
   refusal naming the zone; both HA themes.

6. Tests: log categories and default verbosity, retention purge, export
   filters, restart gap row, incident ids on rows, foyer_event fired,
   restore refusing an invalid or newer-major document.
```

### Phase 2, part 1

```
Scope for THIS session: Phase 2, part 1 — identity and codes. Users, their
codes, the per-operation code policy, permissions, lockout, panel page 7,
and the card's keypad. Part 2 (the service and MQTT contracts, arming
devices and the shipped adapters) is a separate session. Paste "Phase 2
decisions" after this appendix.

Context from Phase 1, which is complete and accepted (v0.1.0-alpha.11,
configuration schema 4.2):
- Every state-changing path already runs through check_code(Operation).
  There are no users, so CodePolicy has every operation False and the engine
  fails closed: a request that needs a code is refused because no code can be
  verified. This part fills that in; it does not build new plumbing.
- The log has a user_id and a user_name column, both empty, and user_name is
  denormalised on purpose: deleting a user must not erase the history of what
  that user did (§10.1). Filling them is part of this session.
- The panel's config commands are admin-only (websocket_api.require_admin);
  the log query and export are open to any signed-in user. Both become
  permission checks here (§8.3): edit_config and view_log.
- core/ is pure and must stay so: bcrypt hashing belongs in security/, and
  the engine is told whether a code verified, never given the code.

1. Users and codes (SPEC §8.1):
   - bcrypt hashes, written through the API and never returned by it — not
     in foyer/config, not in the log, not in a diagnostic.
   - One code per user, UNIQUE across users and against every duress code.
     Rejected at save time, and the message must not reveal whose code it
     collided with.
   - Global code length (4-12, default 6), because a keypad has to know how
     many digits to collect before validating. The UI states what a 4-digit
     code is worth.
   - Per-user duress code: disarms normally and raises a silent `duress`
     event. Same uniqueness rule.
   - valid_from / valid_until for guest codes, allowed_area_ids,
     allowed_scenario_ids, enabled.

2. Code policy resolution (§8.2), with the defaults of that table. The
   per-user override applies ONLY on channels that identify the user; on a
   shared keypad the code IS the identity, so the exemption cannot apply.
   The configuration UI must say that where the setting is, not in the
   documentation, or it reads as a bug.

3. Permissions (§8.3) enforced on every service and every WebSocket command,
   not only in the UI. A permission the UI hides must still be refused when
   the command is sent by hand.

4. Lockout (§8.4): N failures in W seconds locks that channel for L, growing
   exponentially on repetition; raises an event a response profile can act
   on; recorded with the channel and device; and never locks out the Home
   Assistant admin path, so nobody can lock themselves out of their own house.

5. Panel page 7 (users and codes) with its help panel, and the settings
   block for the global policy and the code length.

6. The card: layout `keypad`, and the keypad inside layout `full` (§15.3).
   INV-2 is the whole point: the card collects digits and transmits them, the
   backend decides, and the card renders the answer — wrong code, blocked by
   zone X, locked out.

7. The fields Phase 1 deliberately left out, with a storage migration:
   require_code_to_arm / require_code_to_disarm on areas and scenarios,
   allowed_user_ids on scenarios (§4.5, §4.6), and user_id on a key zone's
   identity (§4.7), so the log can attribute what a key turn did.

8. Security tests are part of this deliverable, not a follow-up (§19): wrong
   code, missing code, expired user, insufficient permission and locked-out
   channel each rejected; a code or hash never present in any API response,
   log row or diagnostic; and the audit test that says who disarmed.

Ask the user before writing code, one at a time, with the alternatives and
your recommendation:
- What the code policy for ACKNOWLEDGE should be. §8.2 does not list it, and
  whether button.foyer_acknowledge may exist at all depends on the answer
  (decision 59: a button cannot carry a code).
- Decision 6 ends here: forced arm and changing scenario while armed move to
  the §8.2 defaults, which require a code. It changes behaviour for anyone
  already running an alpha, so it belongs in the changelog — confirm it.
- Whether an administrator using the panel, whose Home Assistant user is
  linked to a Foyer user, should be exempt from typing a code (§8.2 allows
  the per-user exemption on identifying channels, and the panel is one).

Done when: a person with a code arms and disarms from the panel, the card and
a wall tablet; a wrong code is refused and, repeated, locks that channel out;
and the log says who did what, through which channel.

Do not build: MQTT, the keypad adapters, the simulator, walk test, contacts,
escalation or automatic rules.
```

### Phase 2, part 2

```
Scope for THIS session: Phase 2, part 2 — the physical channels. The service
contract, MQTT in both directions, panel page 8, the shipped adapters and the
card's badge layout. After it, run the Phase 2 acceptance ("arming and
disarming from a physical keypad with correct feedback, with the log
attributing every action to a person and a channel"). Paste "Phase 2
decisions" after this appendix.

Context from part 1: users, codes, the code policy, permissions and lockout
exist and are tested. Build on them; a channel added here authenticates
through the same check, never around it.

1. The service contract (§9.1): foyer.arm, foyer.disarm, foyer.bypass_zone,
   foyer.unbypass_zone, foyer.acknowledge, foyer.walk_test (Phase 3 fills it),
   foyer.test_action (Phase 3), foyer.export_log, foyer.export_config,
   foyer.import_config. Every state-changing service takes code, user_id,
   channel and device_id and returns the structured result of §9.1, the same
   shape foyer/arm and foyer/disarm already return over the WebSocket, so a
   keypad adapter can give a meaningful answer instead of a silent failure.

2. The MQTT contract (§9.2) in both directions, with CONFIGURABLE topics:
   people run more than one site against one broker. Outbound is published
   retained on change and on request, and carries enough for a keypad to
   distinguish a wrong code from arming blocked by an open zone — that
   distinction is the point of the whole contract.

3. Panel page 8 (arming devices) with its help panel: keypads, NFC tags and
   remotes, the MQTT mapping and the feedback configuration.

4. The shipped adapters as blueprints (§9.3): Ring Alarm Keypad v2 over
   Z-Wave JS including the LED ring, the beeps and the countdown; a generic
   Zigbee keypad over Zigbee2MQTT with the note that Tuya-family clones vary
   by firmware and must be verified one by one; NFC tags and remotes through
   tag and event entities, including the security note that a stolen tag
   arms and disarms without knowing any code. Plus docs/keypads.md (§9.5).

5. Card layout `badge` (§15.3): colour-coded state only, for embedding.

6. Tests: the structured result is identical from a service and from the
   WebSocket; a bad code over MQTT is refused and answered as a bad code;
   topics are honoured as configured; an unauthenticated MQTT message can do
   nothing a code would not allow.
```

### Phase 2 decisions (paste after the appendix, in every session from part 2 on)

```
Binding decisions taken by the user in Phase 2. Fill this block as they are
taken, exactly as "Phase 1 decisions" was filled: the next session must not
re-litigate them.

Inherited from Phase 1, and binding here:
- decision 6 ended: forced arm and changing scenario follow §8.2.
- decision 59: button.foyer_acknowledge exists only if acknowledging needs no
  code; otherwise §13 is amended, with the user's agreement.
- Releases stop being GitHub pre-releases from the first beta, which is where
  the end of Phase 2 is expected to land: HACS only offers releases that are
  not pre-releases, and shows a commit hash for a repository that has none.

Taken in part 1, before any code:
 1. ACKNOWLEDGE needs no code by DEFAULT, but stays an entry of the code
    policy like every other operation, so an installation can raise it.
    button.foyer_acknowledge therefore exists (§13 unchanged, decision 59
    resolved): it honours the policy, and refuses with `code_required` —
    logged — if the installation has raised it. The reason it is not
    required by default: §7.2 already acknowledges from an actionable push
    notification, which carries no code, so demanding one on the panel's
    button would be theatre at the worst possible moment.
 2. Decision 6 ends, and the §8.2 defaults are written by the migration —
    but the whole policy is INERT while the installation has no enabled user
    holding a code. No code can be verified then, so enforcing it would only
    make the alarm unusable, not safer; failing closed with zero codes
    protects nothing. The panel and the card say so plainly while it lasts
    ("no users yet: codes are not enforced"). From the first user created,
    the policy applies in full, with no further step.
 3. The per-user exemption of §8.2 is a switch on the USER ("do not ask me
    for a code on channels that identify me"), off by default, offered to
    anyone with a linked Home Assistant user — not only to administrators:
    what makes the exemption safe is the identification, not the role. The
    editor states what it costs, because the wall tablet INV-6 names is
    almost always signed in as an administrator. There is no automatic
    exemption for admins.
 4. When an area and a scenario disagree about whether an operation needs a
    code, THE STRICTEST EXPLICIT SETTING WINS: if any area involved, or the
    scenario, says a code is required, it is required; if none of them is
    set, the global default decides. §8.2 puts area and scenario on the same
    step and does not say which one wins. The failure of this rule is one
    code too many; the failure of the opposite rule is an area the owner
    deliberately protected, opened because a permissive scenario included it.
    The UI names the area that is asking.
```

### Carry-overs from Phase 1 into later phases

```
Paste the relevant block after that phase's prompt. These are things Phase 1
deliberately left for the phase that owns them.

Phase 2 (security and arming channels):
- Releases become ordinary GitHub releases from the first beta, instead of
  pre-releases: HACS only offers releases that are not pre-releases, and shows
  the commit for a repository that has none, which is unreadable for a user.
  The user chose to stay on pre-releases while the product is alpha.
- The log's `user_id` / `user_name` columns exist and are empty: fill them
  once users exist, and add the `view_log` permission to foyer/log/query and
  foyer/log/export (open to any signed-in user today) and `edit_config` to
  foyer/log/clear and foyer/config/import (admin-only today).
- The wizard's "user and code" step is shown and explicitly skipped; build it
  when codes land.
- The foyer.export_log / foyer.export_config / foyer.import_config services
  of §14.1 were not built: the panel does all three over the WebSocket API,
  and the services belong with Phase 2's service contract and its code check.
- The wizard's test notification calls the `notify` service directly from the
  browser. Once §11.4's real action test exists (Phase 3) it should go
  through it, so the test is logged as a test.
- Area fields require_code_to_arm / require_code_to_disarm and scenario
  fields require_code_to_arm / require_code_to_disarm / allowed_user_ids
  (§4.5, §4.6) were not added in Phase 1: add them with the code policy
  resolution (§8.2), with a storage migration.
- Decision 6 ends here: force arm and change scenario go to the §8.2
  defaults (code required). Say so in the changelog; it changes behaviour.
- Permissions force_arm, bypass_zone, change_scenario, edit_config enforced
  on every WebSocket command. Config commands are admin-only today; they
  become edit_config + code.
- Key zones get identity: user_id (§4.7) for the log.
- WebSocket foyer/arm and foyer/disarm already return the §9.1 structured
  result; the foyer.* services must return the same shape. skip_exit_delay
  is part of the contract.
- The acknowledgement commands from parts 2 and 3 get their code policy.
  Operation.ACKNOWLEDGE already runs through check_code (no code today); §8.2
  does not list it, so ask the user for its default.
- button.foyer_acknowledge (§13) was deferred here (decision 59): a button
  cannot carry a code. Build it only if acknowledging needs no code;
  otherwise amend §13 to drop it, with the user's agreement.
- The card's keypad (layout keypad, and the keypad in layout full).

Phase 3 (test and simulation):
- battery_entity_id on zones (§4.2) and the low_battery moment were not
  added in Phase 1; they belong with diagnostics (§11.1).
- The simulator calls core.engine.decide() with a fabricated snapshot and
  clock and uses core.engine.next_wakeup() to step time; it must never grow
  its own evaluation path.
- Walk test: areas genuinely armed, actions inhibited, always_on zones
  fully live; chime stays silent because the area is armed.

Phase 4 (contacts, escalation, automatic rules):
- is_perimeter on areas (§4.5) was not added in Phase 1; add it with the
  automatic rules and the regression test that a disarm rule never disarms a
  perimeter area.
- Escalation adopts the incident's highest-severity contributing profile
  (parts 2 and 3 record it).

Phase 5 (hardening and release readiness):
- The "Learn more" deep link in every help panel (§15.2) was left out
  because the docs/ pages it points to do not exist yet; add the links with
  the documentation.
```
