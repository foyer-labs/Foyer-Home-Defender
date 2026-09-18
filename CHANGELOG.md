# Changelog

All notable changes are recorded here. The project follows
[Semantic Versioning](https://semver.org). For a security system the changelog
is what lets you decide whether to take an update, so entries say what changed
in behaviour, not just "fixes".

## [0.1.0-alpha.13] — codes, and somebody to attribute them to

**Pre-release, for testing only.** **Configuration schema 4.2 → 5.1, a major
step**: a 4.x build reading this document would find users it knows nothing
about, ignore every code in it and run the house with no codes at all, so it
refuses the file instead. Back up before updating if you want a way back.

This is the release that removes the sentence at the top of the README. Until
now anyone who could reach Home Assistant could disarm the alarm.

### Added
- **Users, each with their own code** (SPEC §8.1), stored as bcrypt hashes that
  no API returns in any shape — not in the configuration, not in a backup, not
  in the log. A code may not belong to two people: a shared one makes "who
  disarmed at 03:14?" unanswerable, and the refusal does not say whose code it
  collided with. Code length is global, 4–12 digits, six by default, because a
  keypad has to know how many digits to collect before it validates anything.
- **A duress code per person.** It disarms exactly as the ordinary code does
  and raises a silent event a response profile can answer. Nothing the person
  at the keypad can see is different.
- **A code policy per operation** (§8.2), with the defaults of that table:
  arming needs nothing, disarming, forcing, changing scenario while armed,
  excluding a zone and editing the configuration need a code. An area or a
  scenario can ask for more, never for less — where they disagree the strictest
  explicit setting wins, and the panel names the area that is asking.
- **Permissions** (§8.3), enforced on every service and every WebSocket
  command, not only in the panel: a permission the interface hides is still
  refused when the command is sent by hand from Developer Tools.
- **Lockout** (§8.4): repeated wrong codes shut that keypad for a while, longer
  each time, and it survives a restart — a lockout a restart clears is an
  invitation to restart Home Assistant. It raises an event a response profile
  can act on, because somebody guessing at a keypad is a tamper signal. The
  Home Assistant admin path is never locked: nobody may shut themselves out of
  their own house.
- **Panel page 7**, with the people, the policy table, the code length and the
  lockout settings, and its own help panel.
- **The card's keypad**: a new `keypad` layout for a wall tablet, and the same
  pad folded into `full`. It collects digits and transmits them; it never
  checks one (INV-2). It opens by itself when the backend says a code is
  needed, and learns how many digits to collect from the backend.
- **`button.foyer_acknowledge`**, deferred from Phase 1 because a button cannot
  carry a code. Acknowledging needs none by default — §7.2 already acknowledges
  from a push notification, which carries no code either — so the button
  exists, and refuses visibly if an installation raises the policy.
- **Per-area and per-scenario code settings**, `allowed_user_ids` on a
  scenario, and an identity on a key zone, so the log can say whose key was
  turned. A key switch carries no code and never could, exactly as §9.3 says of
  an NFC tag: it authenticates by possession, and the permissions of the user
  it names still decide whether the turn is accepted.
- The first-run wizard now creates the first person and their code, linked to
  the Home Assistant account doing the setting up.

### Changed
- **Phase 1 decision 6 ends.** Forcing an arming and changing scenario while
  armed follow §8.2 from now on, which means they ask for a code. So do
  disarming, excluding a zone and editing the configuration.
- **…but the whole policy is inert until somebody holds a code.** An
  installation upgrading into this version behaves exactly as it did, and says
  so plainly in the panel and on page 7, until the first user with a code
  exists. Enforcing a policy with no codes to verify would not protect a house;
  it would only make it impossible to disarm, which is how an alarm teaches its
  owner to remove it.
- **The log finally has a person in it.** `user_id` and `user_name` are filled
  on everything a request causes, and `user_name` is kept even after the user
  is deleted, so removing somebody does not erase the history of what they did.
  A refused code is a row of its own under `security`, naming nobody.
- Reading the configuration and the log now needs a permission rather than
  being admin-only and open-to-all respectively. A Foyer user linked to a Home
  Assistant account is subject to Foyer's rules; with none linked, the rule is
  the one used since Phase 0 — an administrator, and nobody else. An
  administrator is never refused the *configuration* for want of a permission
  (INV-6 says they can read `.storage` anyway, and the alternative is an owner
  locked out of their own settings), but the code still applies to them.
- Home Assistant's own alarm card now shows a keypad when the policy asks for a
  code, because the entity says so.

## [0.1.0-alpha.12] — a front page, and the second review

**Pre-release, for testing only.** No schema change.

### Changed
- **A `follower` zone is called *Percorso* in the Italian panel**, which is what
  Italian alarm panels call it: the zone along the way in, which only alarms if
  a delayed zone opened first. It was left in English, and the Italian README
  had invented a word that no installer would recognise. The hint under the
  field now says what the zone *is*, in both languages, instead of only how it
  behaves.
- **Both READMEs are rewritten as what they actually are: the page HACS shows.**
  A line that says what this is before anything else, an honest "try it if /
  not yet, if", what it does in six bullets with the rest folded away, why this
  is not a folder of automations, a comparison with Alarmo that now says where
  Alarmo wins, how to check the work rather than trust it, what you need, the
  first fifteen minutes, and the questions people actually ask. The Italian one
  says plainly that Foyer does not meet CEI 79-3 / EN 50131 where an insurance
  policy requires it.
- A fourth screenshot, and a better one: the zone editor at the moment it
  refuses to save a trigger you have not confirmed against the real sensor.

### Fixed
- The overview printed one time in the browser's locale — `09:30 PM` — beside
  times in the Home Assistant user's — `21:30`. Same page, two clocks.

### Added
- Tests that throw seventeen malformed items at the configuration API and
  assert what comes back: a refusal with a translatable code, never a
  traceback, and a stored configuration that did not move. Settings that would
  break the alarm are in there too.
- The translation guard added in `alpha.10` now sees past a comment inside the
  values passed to a string, which was hiding one call from it.

## [0.1.0-alpha.11] — arming anyway, from the card

**Pre-release, for testing only.** No schema change.

### Added
- **The card offers a forced arm when a zone refuses.** It named the zone and
  stopped there, leaving the only way forward as excluding each zone by hand —
  from the thing on the wall, while leaving the house. It now offers *Arm
  anyway*, the same command the panel offers, on the same two refusals a force
  can get past: zones open and zones in fault. Forced arming stays explicit and
  is recorded under `security` as `forced_arm`, with the zones it excluded.

### Fixed
- The README now says what to do when the card is missing from the picker or a
  dashboard reports *Custom element doesn't exist*. Home Assistant writes a
  card's script tag into the page it renders, so a page loaded before Foyer was
  installed does not have it and reconnecting does not fetch a new one: one
  hard reload is the answer. Two tests rule Foyer's side out — the module is
  registered, and the file is really served.

## [0.1.0-alpha.10] — the delays the Areas table stopped showing

**Pre-release, for testing only.** No schema change.

### Fixed
- **Areas, Scenarios and Verification groups printed the word "Seconds" where
  the number belonged.** `alpha.8` added a "Seconds" label for the Settings page
  and gave it the name of the string those tables fill with a value, which had
  been `{n} s`. Both languages were equally wrong, the key still existed, and
  nothing noticed.
- A test now notices: every call that passes values to a translation must
  target a string with somewhere to put them, and every placeholder in a string
  must be filled by the code that uses it. Reintroducing this bug now fails CI.

## [0.1.0-alpha.9] — what the first real read of the log found

**Pre-release, for testing only.** No schema change.

### Changed
- **Saving a setting is no longer recorded as an outage.** Every configuration
  change reloads the integration, and the gap that leaves is a fraction of a
  second — but it was logged as *"Foyer was not running"*, in warning, next to
  the change that caused it. A gap is now measured rather than described: under
  a minute, after a reload, it is *"Foyer reloaded"* and an ordinary info row;
  above that, or after a real restart, it stays the warning that INV-3 requires.
  The integration being disabled and re-enabled by hand is still an outage,
  because the gap says so.
- **A configuration change now says what changed**, not only which field:
  *Area "Windows and doors" · Default exit delay: 30 → 45*, in the row's summary
  and in full when it is opened. Values too long to print — a profile's action
  list, a trigger's states — still say only that they changed, because a row
  that contains the configuration is a row nobody reads.
- The rest of a row's detail is shown as a labelled list rather than as raw
  JSON.

## [0.1.0-alpha.8] — what the end-of-phase review found

**Pre-release, for testing only.** No schema change: this is `alpha.7` with
four defects fixed, and it is the version worth testing.

### Fixed
- **Log retention never ran on most installations.** The purge was on a daily
  timer, and every configuration change reloads the integration and restarts
  that timer: a house touched more often than once a day would have kept every
  row for ever. It now also runs at each start.
- **The language setting did nothing.** It is the language of what Foyer
  *sends out* — notifications, the spoken zone name — and the executor was
  still reading Home Assistant's. Left empty it still follows Home Assistant,
  and now it follows it as messages are sent rather than as Foyer was loaded,
  so changing Home Assistant's language no longer needs a reload.
- **The overview asked the log a question every second** while a countdown was
  running. It now reloads its recent events when something has happened.
- **An attribute-only report was recorded as zone activity.** A battery level
  arriving is not a door opening. A row is written when the state moved, or
  when what Foyer makes of it moved — which is what a numeric trigger crossing
  its band does without changing the state at all.
- The log page is open to every user, but its category filters came from the
  administrators-only configuration: a non-admin saw the page with no filters.
- A failed notification was labelled "Notification sent" in the log. The event
  says what was attempted; the outcome column says how it went.
- The alarm-memory banner no longer reads "Alarm memory in Upstairs: ." when
  the zones that caused it are no longer known.

### Added
- A refresh button on the log page, and the first-run wizard's entity picker no
  longer stops at the first two hundred entities.
- Screenshots and a version badge in the README, which is the page HACS shows.

## [0.1.0-alpha.7] — Phase 1, part 4: the event log, the wizard, the card

**Pre-release, for testing only.** It is, however, the end of Phase 1: with
this release a real house can be protected, and the acceptance for that is
written down as a test suite rather than as a claim. Still missing before it
should guard anything valuable: users and codes (Phase 2), the simulator and
walk test (Phase 3), and escalation across contacts (Phase 4).

### Changed — read this if you run an alpha
- Stored configuration moves from schema 4.1 to **4.2**, a *minor* step: an
  older 4.1 build reading this document ignores the keys added here and
  protects exactly what it protected before. Nothing is lost by going back.
- **The sidebar icon is now an mdi shield.** It was a custom Foyer icon, and
  Home Assistant resolves a custom icon exactly once: when the sidebar is drawn
  before the module that registers it has run — which is what the companion app
  does when it starts from a cached page — it gave up and left an empty square
  for ever. The Foyer shield stays in the panel header and on the card, where
  it is always drawn.

### Added
- **The event log** (panel page 10), in a SQLite database of Foyer's own, next
  to your configuration and never touched by Home Assistant's recorder — whose
  ten-day purge would quietly destroy a thirty-day requirement. It records
  arming and disarming with the channel they came through, alarms and incidents,
  every action with whether it actually worked, configuration changes with a
  summary of what moved, refusals with the zone that blocked them, and zone
  activity. Filter by date, area, zone, category, severity and outcome; one
  click shows a whole incident; export exactly what the filters show as CSV or
  JSON.
  - **Zone activity while disarmed is off by default.** One motion sensor
    produces thousands of rows a day and buries everything that matters. Switch
    it on while diagnosing, and off again afterwards.
  - Every row also fires the `foyer_event` bus event, so an automation or an
    external collector needs one trigger and no database.
  - **The restart gap is recorded** as `system_unavailable`, from the last
    moment Foyer is known to have been running to the moment it came back. The
    log never implies the house was covered when it was not.
  - A log failure never delays the alarm: rows are queued and written by a
    worker, and a full disk costs you the row, never the siren.
- **`sensor.foyer_last_event`**, for a dashboard: the last thing worth showing,
  which is not the thousandth motion of the day.
- **Settings** (page 11) gains the defaults new areas start from, the siren
  cutoff and the arm-after-closing wait, **per-category log retention** (thirty
  days each by default), **configuration backup and restore**, and the language
  of the messages Foyer *sends out* — notifications and the spoken zone name.
  The panel itself has always followed each Home Assistant user's own language
  and still does.
  - A restore migrates an older backup through the same steps a real upgrade
    uses, refuses one written by a newer major version rather than reading it
    half-way, and is then validated and refused if it would change an armed
    area — like any other edit.
- **The first-run wizard**, which continues from the config flow instead of
  starting again: the area it made, two more zones with their triggers
  confirmed one by one, the scenario, and a notification actually sent so you
  know the channel works. The user-and-code step is shown and skipped, in as
  many words: codes are Phase 2, and a wizard that implied otherwise would be
  lying about what protects the house.
- **Card layouts `full` and `compact`**, with a visual editor. `full` is the
  card to look at before leaving: every area with its state and countdown, the
  scenarios, and the zones that would stop it arming, each with a way out.
  `compact` is one row for the top of an existing dashboard. The keypad
  layouts wait for codes, in Phase 2.
- **The overview shows recent events**, which page 1 has always promised and
  which only became possible now there is a log to read them from.
- **A zone can be excluded for any number of minutes.** It offered one hour and
  eight hours, which does not cover "twenty minutes while the window airs the
  room" — and a duration you cannot choose is one you round up.

### Fixed
- The alarm-memory banner no longer reads "Alarm memory in Upstairs: ." when
  the zones that caused it are no longer known.

## [0.1.0-alpha.6] — what the first real use of page 5 found

**Pre-release, for testing only**, like the alphas before it. No schema change:
this is `alpha.5` with the configuration screens made usable.

### Fixed
- **A notification target could not be picked from the list.** The panel built
  every picker from Home Assistant's *entities*, but the Companion app and
  Telegram are *services*, which are not entities: there was nothing to suggest
  and the field had to be typed by hand. Both are now read and offered
  together. The same blind spot left the chime's target list without any
  notify target at all, so **the chime on the phone could not be configured**
  from the panel that was built for it.
- **Calling a service** now suggests the domains your installation has, and
  then that domain's services.
- **The action editor's layout**: the entity list took a single cell beside two
  small fields, which with a house's worth of switches left the row tall and
  the other fields floating at the top. It now takes a row of its own, scrolls
  inside itself, and above eight entities offers a search that matches every
  word in any order. What is already chosen stays visible whatever you type.
- **A siren's duration says seconds**, and says that it is capped at the siren
  cutoff. It was a bare number, and the natural guess was minutes.
- **A siren's tone is a list of that siren's own tones**, read from the device,
  instead of a free text field; a siren that declares none says so.
- An action answering many moments no longer prints all of them into its
  collapsed row.
- **The README's logo and links were broken inside HACS**, where a relative
  path resolves against Home Assistant instead of GitHub.

### Added
- An Italian README, since the interface has been in Italian from the first day.

## [0.1.0-alpha.5] — Phase 1, part 3: response profiles, actions, bypass

**Pre-release, for testing only.** Still not for protecting a house: no event
log, no codes, no escalation across contacts.

### Changed — read this if you run an alpha
- Stored configuration moves from schema 3.1 to 4.1. **Do not go back to an
  earlier alpha afterwards**: it refuses the new file on purpose, because it
  would otherwise find profiles it does not understand and run no action at all.
- The notification you have today is not lost: the migration turns it into a
  **"Default" response profile** with exactly the moments it already had. One
  moment is added, deliberately: **an alarm now sends a notification**, which
  Phase 0 never did.
- A zone excluded by hand no longer rejoins the moment it closes. Being closed
  again is why it was excluded; it comes back when the area is disarmed, or
  when the duration you gave it runs out.

### Added
- **Response profiles** (panel page 5): a named list of actions, each with the
  moments it answers and up to two conditions. The **area is the unit of
  response** — area, then scenario, then the global default — and a zone's own
  profile is read only for its own alarm, which is what makes a verification
  group's graduated response work: one detector notifies, two sound the siren.
- **Ten actions**: notification to a `notify` service or entity, Home Assistant
  notification, siren, light, camera, scene, switch, spoken message, call any
  service, and wait. A wait holds the rest of the sequence and **survives a
  restart**, as does a switch's automatic return: a restart during an alarm
  never leaves a siren sounding for ever.
- **Conditions**: a time window that may cross midnight, and one entity's
  state, combined with *and* or *or*. Anything more complex belongs in a Home
  Assistant automation subscribed to `foyer_event`.
- **Templates** over a fixed, documented set of variables — the zone, the area,
  the scenario, the time, every zone in the incident — with no arbitrary Jinja.
- **Severity** on a profile, recorded on every zone that joins an incident, so
  Phase 4's escalation can take the strongest.
- **Silent zones**: the response runs without the action kinds the settings
  name (siren, spoken message and chime by default). Silence belongs to the
  zone: another zone in the same incident still sounds.
- **Manual and timed exclusion of a zone**, from the panel, the card and the
  WebSocket API. Without a duration it lasts for this arming; with one the zone
  comes back on its own and says so, because a zone excluded and forgotten is
  exactly the window somebody comes through.
- **A dedicated technical profile** in the settings: smoke, gas and flood
  answer with it whatever the house is doing.
- **The chime reaches `notify` targets too** — the Companion app, Telegram —
  and each target may carry quiet hours of its own, so the speakers can chime
  all day while the phone only chimes between nine and ten.
- A notification can carry the **camera picture**, through Home Assistant's
  authenticated proxy. Snapshots and recordings are written under a
  configurable folder, `media/foyer` by default and never `www`, which is
  served to anyone who guesses the URL.

### Not yet
- Escalation across contacts, acknowledgement by push button, actionable
  notifications: Phase 4. A notification goes to one service, once.
- The event log, so what an action did is not yet recorded anywhere but in
  Home Assistant's own logs. That is part 4.

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
