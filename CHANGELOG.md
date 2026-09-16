# Changelog

All notable changes are recorded here. The project follows
[Semantic Versioning](https://semver.org). For a security system the changelog
is what lets you decide whether to take an update, so entries say what changed
in behaviour, not just "fixes".

## [0.1.0-alpha.4] — Phase 1, part 2: technical channel, incidents, groups, chime

**Pre-release, for testing only.** Still not for protecting a house: no sirens
or response profiles, no event log, no codes.

### Changed — read this if you run an alpha
- Stored configuration moves from schema 2.2 to 3.1. Nothing that works today
  changes: no groups, no cross-zone, one detection to alarm, no chime.
  **Do not go back to an earlier alpha afterwards**: it refuses the new file
  on purpose, because it would otherwise keep your technical zones and
  silently never act on them.
- **Technical zones (smoke, gas, water) are accepted again**, now that their
  channel exists. A technical zone in fault blocks arming its area like any
  zone, unless "Allow arming while in fault" is set on it.
- The notification action also announces a technical alarm.
- A triggered alarm is now one *incident*: zones that trigger later join it
  instead of starting anything new. Disarming acknowledges it.

### Added
- **Technical alarm channel**: `binary_sensor.foyer_technical_alarm` and
  `sensor.foyer_technical_cause`. Live whether armed or not, never reported
  through any alarm panel, not cleared by disarming: it clears once
  acknowledged *and* back to normal. Foyer is not a fire alarm system, and the
  zone editor says so wherever a technical zone is configured.
- **Incidents**: `sensor.foyer_incident` with the zones and areas involved; an
  Acknowledge button on the overview and on every card. A zone that joins
  after the acknowledgement asks for a new one.
- **Verification groups** (panel page 13): an alarm confirmed when N of M
  zones detect within a window, members optionally silent until then.
  **Cross-zone** on a zone is the same engine as a 2-of-2 group, and
  **activations needed** counts detections of one zone. Only detections that
  would alarm at once count: coming home through the entry delay never does.
- **Chime**: a zone opening where its area is not armed plays a sound or
  speaks the zone name on media players and sirens, with quiet hours and an
  option for the exit delay; `switch.foyer_chime` silences it. Set up in the
  new Settings page. Sending it to a phone or to Telegram instead comes with
  the next part, which adds the `notify` action.

## [0.1.0-alpha.3] — deleting from the panel works

**Pre-release, for testing only**, like the previous alphas.

### Fixed
- Deleting an area, a zone or a scenario from the panel never worked: the
  command was rejected by Home Assistant before reaching Foyer. It now works,
  and the refusals it can meet are shown under the form — an area that still
  has zones, an area used by a scenario, an area that is not disarmed.
- A configuration change that Home Assistant rejects, for any reason, now says
  so under the form instead of doing nothing silently.

## [0.1.0-alpha.2] — cross-area followers

**Pre-release, for testing only**, like alpha.1: still no sirens, log,
technical channel or codes.

### Added
- A follower zone can follow delayed zones in **other areas** ("Also follows"
  in the zone editor). With areas grouped by function — perimeter, interior
  day, interior night — the hall sensor is in a different area from the front
  door; following it, the hall inherits the running entry delay instead of
  sounding the alarm as you walk in. Stored configuration moves to schema 2.2;
  existing followers keep following their own area only.

## [0.1.0-alpha.1] — Phase 1, part 1: zones, areas, scenarios, state machine

**Pre-release, for testing only.** Still not for protecting a house: no sirens
or response profiles, no event log, no technical channel, no codes. Parts 2–4
of Phase 1 follow as further alpha pre-releases; 0.1.0 is Phase 1 complete.

### Changed — read this if you run 0.0.1
- **Alarm state now survives a restart.** It is saved on every change in
  `.storage/foyer.state`. A state file that cannot be read stops the integration
  from loading rather than starting disarmed.
- Your stored configuration is migrated from schema 1.1 to 2.1 and behaves as
  before: your zone becomes an explicit instant zone that blocks arming while
  open, and your area keeps exit and entry delays of 0 s. An older Foyer will
  refuse the migrated file instead of misreading it.
- A triggered area no longer stays triggered forever: after the siren cutoff
  (180 s by default, at most 900 s) it returns to the state it was in before,
  keeping an alarm memory until someone disarms.
- An area's own `alarm_control_panel` now arms **only that area**. Scenarios are
  armed from the new master panel, the scenario select, the panel or the card.
- The notification action also announces a failed arming and an automatic
  bypass.

### Added
- Areas, zones and scenarios, any number, edited from the sidebar panel with
  every change validated by the backend. Changes that touch an armed area or
  the running scenario are refused until it is disarmed.
- Zone types instant, delayed, follower, 24h, tamper, panic and key, as presets
  over explicit, editable properties. Triggers by state, by number (with
  hysteresis, optionally from an attribute) and by event or tag. The zone
  wizard proposes a trigger from the entity's type and refuses to save it
  unconfirmed, in the backend as well as in the page.
- Exit and entry delays, follower zones, arm policies block, auto_bypass,
  arm_after_closing (with a per-zone wait limit) and ignore, forced arming as a
  distinct command, supervision by heartbeat.
- Key zones: a switch, tag or remote that arms or disarms.
- Entities: `alarm_control_panel.foyer_master`, `select.foyer_scenario`, a
  binary sensor per zone, ready-to-arm (overall and per area), zone fault, open
  zones and a countdown per area.
- Panel pages Overview, Areas, Zones and Scenarios, each with its help, which
  now remembers per Home Assistant user whether it is open.

## [0.0.1] — Phase 0, walking skeleton

Not for protecting a house: there are no codes, and alarm state is not kept
across a restart.

### Added
- Config flow: one area, one scenario, one zone with an explicitly confirmed
  trigger state. Unavailable and unknown cannot be chosen as trigger states.
- Configuration stored in `.storage/foyer.config` with a schema version and a
  migration hook.
- Pure decision engine, `decide(snapshot, event, config, now)`.
- `alarm_control_panel.foyer_<area>`: arm and disarm go through the engine.
  Arming is refused while the zone is open or unavailable, and the refusal
  names the zone.
- The zone triggers the armed area.
- A persistent notification on armed, disarmed and zone fault.
- Sidebar panel with a live status screen and its help section.
- `foyer-card`: area state and an arm button.
- English and Italian throughout.
