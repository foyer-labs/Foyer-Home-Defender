# Changelog

All notable changes are recorded here. The project follows
[Semantic Versioning](https://semver.org). For a security system the changelog
is what lets you decide whether to take an update, so entries say what changed
in behaviour, not just "fixes".

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
