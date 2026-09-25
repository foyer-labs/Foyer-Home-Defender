# Changelog

All notable changes are recorded here. Versions are numbered in the style of
[Semantic Versioning](https://semver.org), but while 1.x is young a release
may change behaviour, a service, a contract or the stored configuration
without a new major version. For a security system the changelog is what lets
you decide whether to take an update, so entries say what changed in
behaviour, not just "fixes", and whatever needs something from you comes
first, under *Changed — read these before you update*.

## [1.0.7] — disarm every area

The stored configuration moves to schema 8.5. The step is additive: an older
release reading a rule set to every area finds its list empty and refuses to
act on it, which disarms less, never more.

### Added
- **A disarm rule can name every area.** *Every area* means the areas the
  house has when the rule acts, so one added later is included and one
  deleted does not leave the rule half-broken. The perimeter areas are still
  left armed, as always.

### Changed
- **The *Action* column of the rules table wraps** instead of growing with
  every area a disarm rule names, so the other columns stay readable.

## [1.0.6] — entities you can find

Nothing changes in how the alarm behaves.

### Changed
- **Choosing entities no longer means scrolling rows of tick-boxes.** The
  people an *Absence* or *Presence* rule watches, the entity of an *Entity
  state* rule and the devices outside the UPS are now a list: type a name or
  an id, pick from the suggestions, *Add*; each entity chosen shows its name,
  its id and what it reads right now, with *Remove* beside it. An id that is
  not in Home Assistant is not taken, and one that has since disappeared
  says so.

## [1.0.5] — the mains from a plain UPS

The stored configuration moves to schema 8.4. The step is additive: an older
release reading it ignores the new setting and keeps its mains sensor.

### Added
- **The mains can be known from devices outside the UPS.** A plain UPS keeps
  Home Assistant running and says nothing; a smart plug or an energy monitor
  plugged in outside it goes unavailable when the power goes. On *System
  health*, *How Foyer knows the mains* now offers *Devices outside the UPS*:
  pick one or more, and when every one of them has been silent for the delay
  (two minutes by default) it is a power cut; one answering again is the
  power back. A device silent when Home Assistant starts counts only once it
  has answered, so a restart is never a power cut. The documentation says how
  long Wi-Fi and Zigbee integrations take to mark a device unavailable.
- **The mains fields suggest Home Assistant's entities** as you type a name
  or an id, instead of being plain text.

## [1.0.4] — notifications that say what happened

### Changed — read these before you update
- **Some template variables now come in words.** `{{ reason }}`,
  `{{ state }}`, `{{ channel }}` and `{{ operation }}` used to write
  identifiers — `zone_open`, `armed`, `automation`, `disarm` — and now write
  them in the language of outgoing messages: *a zone is open*, *Armed*,
  *Automation*, *Disarm*. `{{ user }}`, when nobody acted in person, now names
  what did (*Automatic rule*, *Automation*) instead of staying empty. A
  message that relied on the identifiers will read differently.

### Added
- **`{{ event }}`**, the moment in words — *Armed*, *Alarm*, *Zone fault* —
  so a notification can say what happened, and one action serving several
  moments can tell them apart.
- **Ready-made notifications.** *From a template* on the *Response profiles*
  page asks which contacts to reach and opens a new profile, not yet saved,
  with five notifications: 🚨 alarm, 🔥 technical alarm, 🔒 armed,
  🔓 disarmed and ⚠️ warnings. The same five are in the documentation as a
  table to copy from.

## [1.0.3] — snapshots on Home Assistant OS

### Fixed
- **Camera snapshots are written on Home Assistant OS.** The default camera
  folder, `media/foyer`, was taken as `<config>/media/foyer`; on Home
  Assistant OS the media folder is `/media`, and only the media folders are
  allowed by default, so every snapshot was refused — and with it every
  picture sent to Telegram, which needs a file. A camera folder that starts
  with `media` now means Home Assistant's own media folder, wherever the
  installation keeps it, and the snapshots appear under *Media*. The setting
  does not change; the Companion app, which needs no file, was never
  affected.
- **Home Assistant no longer reports a blocking call** from Foyer's
  translations: the list of languages is read once, when the integration
  loads, instead of from the disk on every request of the panel.

## [1.0.2] — pictures reach a Telegram chat

### Fixed
- **Camera pictures now reach a Telegram chat set up from the UI.** Home
  Assistant has deprecated the YAML `notify.telegram` service, so a Telegram
  chat is now a notify entity, and a notify entity carries only a title and a
  message: the alarm's text arrived and every picture was dropped without a
  word. With *Telegram — a photo file* as the attachment, Foyer now sends each
  picture through `telegram_bot.send_photo`, after the text. This covers both
  *The cameras of the zones behind the alarm* and *Always the same camera*. A picture that fails is logged and
  costs nothing but itself.
- **Any other notify entity says in the log that it received no picture**,
  instead of skipping it in silence.

## [1.0.1] — the sidebar names the product

Nothing changes in how the alarm behaves.

### Changed
- **The sidebar entry reads *Home Defender*** instead of *Foyer*: Foyer is the
  brand, Home Defender the product. The messages that send you to the panel
  name it the same way.

## [1.0.0] — the first stable release

The same alarm as 1.0.0-rc.2: nothing changes in how it behaves. It is a
first release, not a promise that nothing will change: more fixes will follow
soon, and some may change behaviour, the services, the device endpoint and
MQTT contracts or the stored configuration without waiting for a 2.0. Any
such change is listed first, under *Changed — read these before you update*,
in the release that makes it; one that breaks a device written for the v1
contract is also published as a new contract version, as the contract
documents say.

### Changed
- The manifest names the integration's owner (`codeowners`), which HACS
  requires before an integration joins its default list.

## [1.0.0-rc.2] — every document in Italian, and an icon

No change in how the alarm behaves. The configuration, the services and the
device and MQTT contracts are as in 1.0.0-rc.1.

### Added
- **Every document for people who use Foyer is now in Italian as well**:
  keypads and API devices, automatic rules, notification channels, privacy,
  resilience, the simulator and system health joined the others. With the
  panel in Italian, *Learn more* now opens the Italian document on all fifteen
  pages instead of eight.
- **The integration has an icon and a logo**, in
  `custom_components/foyer/brand/`, for Home Assistant's integration pages
  and for HACS. They are rendered from the existing symbol and lockup by
  `scripts/build_brand_images.py`.
- **The READMEs show what you can build yourself** — a lamp, a display, an
  ESP32 or Arduino keypad — against the v1 contract, and where it is written.

### Fixed
- The external watchdog's warning in *System health* said that, switched on,
  the ping carries only how many areas are armed. It carries three values:
  how many areas are armed, how many there are, and whether anything is
  wrong. The code did not change; the sentence did.
- Documents that no longer matched the code: five Android notification keys
  counted as four, a channel check described as future work that system
  health already does, three limits of the log pseudonym counted as two, four
  things about automatic rules counted as three, three service fields counted
  as two, and the simulator's *Silence limit* column and siren line named as
  they are not in the panel.

## [1.0.0-rc.1] — the fix phase

The defects found while the documentation was written, corrected. This is
the release candidate for 1.0. The stored configuration keeps its schema.

### Changed — read these before you update
- **A scenario limited by *Who may use it* now needs somebody established.**
  While codes are in force, a request that identifies nobody — a codeless
  arming from an automation, or a `user_id` a message only claims — is
  refused with *A code is required* for arming, forcing or switching to it.
  Give such an automation a code, or remove the list. An automatic rule still
  arms it, and so does a key zone whose *Acts as* names a person on the list.
- **The first zone the config flow creates takes the type proposed for its
  sensor**: a door becomes *Delayed*, a smoke detector *Technical*. It was
  always *Instant*.
- **A walk test is always announced.** When no profile answers its start or
  end with a message, Foyer puts up a Home Assistant notification itself.
- **An administrator's account is never locked out on the `foyer.*`
  services either**, as on the panel and the card. It is still asked for the
  code, and the export, import and action-test services still check its
  permissions.
- **A *Lock for* longer than an hour is honoured.** Every lockout used to stop
  at an hour whatever was set.
- **A *duress* row is written, and fired as `foyer_event`, even with the
  *Security* log category switched off**; so are the recovery of access and
  the accepted disclaimer.

### Fixed
- The action test switched a switch-driven siren, or one that takes no
  duration, on and never off; it is now switched off after its three seconds.
- The first-run wizard could create a person without a code and then say
  that person held one. The step now asks for the code.
- The zone editor had no field for the person a key zone acts as; it has one
  now, *Acts as*.
- The Areas page ignored the Settings default delays; a new area now starts
  from them, and the defaults are held to 0–300 s.
- An event or tag zone that had never fired was a fault and blocked its area
  from arming.
- The rows of the actions a request set off now carry, like the request's own
  rows, that it arrived unencrypted or from an address locked for wrong
  tokens.
- A refusal for a missing code, a permission, a validity window, an area or a
  scenario was recorded with the outcome *wrong code*; it is now *blocked*.
- An undeclared device on the action-test, export and import services was
  refused without a row or a notice.
- A person could be linked, around the Users page, to an account Home
  Assistant runs itself (Home Assistant Cloud's); the backend now refuses it.
- The Alarmo preview listed the people it would bring in to somebody without
  *Manage users and codes*.
- An exempt person out of their validity window still made Home Assistant's
  dialogs stop asking everybody for a code.
- The Overview's lock ignored the code for switching scenario; the card now
  says when no code is in force, and its compact layout clears its scenario
  menu during an entry delay or an alarm; the Areas editor shows an armed
  area's profile from the scenario that armed it.
- Panel texts that described what the code does not do, and the wizard's
  *Not now*, which closes it for good and now says *Don't show again*.

## [0.1.0-beta.24] — what Foyer is, and what to expect

The disclaimer SPEC §20.4 left open is agreed, and asked for before setup.
The support policy is written down where people ask. The stored
configuration keeps its schema.

### Changed — read these before you update
- **Adding the integration starts with *Before you start*:** what Foyer is
  and is not, with a tick, *I have read this and accept it*. Nothing is set
  up until it is ticked. The integration keeps which version of the text was
  accepted and when, and Foyer's log records it as *Disclaimer accepted*.
- **An installation set up before this gets a card in Settings → Repairs**
  with the same text and tick. **The alarm keeps working until somebody ticks
  it**; nothing is refused meanwhile.

### Added
- The same text in the Overview's help, both READMEs, the security model and
  `SECURITY.md` (decisions 150–152).
- `SUPPORT.md`: best effort, with no promise of an answer, a fix or a date;
  only the latest release; a donation buys neither support nor priority. The
  issue form asks you to confirm you have read it and troubleshooting.
- Issues labelled `needs info` close by themselves after fourteen days
  without an answer from their author; nothing else closes by itself.

## [0.1.0-beta.23] — the documentation

The README becomes a short front page, and what it used to carry moves into
`docs/`, where each panel page's *Learn more* now leads. Nothing in what the
alarm does changes; the stored configuration keeps its schema.

### Added
- **Documents for every panel page**, each in English and Italian:
  [security model](docs/security-model.md), [getting started](docs/getting-started.md),
  [zones, areas and scenarios](docs/zones.md),
  [response profiles](docs/response-profiles.md), [settings](docs/settings.md),
  [the card](docs/card.md), [troubleshooting](docs/troubleshooting.md),
  [questions people ask](docs/faq.md),
  [migrating from Alarmo](docs/migrating-from-alarmo.md),
  [visual identity](docs/brand.md), [choosing sensors](docs/choosing-sensors.md),
  [reusing existing sensors](docs/reusing-existing-sensors.md), and an
  [index](docs/README.md). The two hardware documents are assembled from
  manufacturer and integration documentation, not tested on hardware, and
  say so at the top.

### Changed
- **Every panel page has a *Learn more* link**, and it opens the Italian
  document when the panel speaks Italian and one exists. Before, only six
  pages had one.
- **The READMEs are a front page**: what Foyer is, what it looks like, how to
  start, the security model in one paragraph, and the documentation index.
  They no longer compare Foyer with any other product.

### Fixed — in the documents
- `docs/keypads.md` said that `skip_exit_delay` turns every delayed zone into
  an instant one. It does not: it arms with no exit delay, so every zone is
  watched at once, and a delayed zone still starts its entry delay.
- `docs/keypads.md` said that every row a right token causes from a locked
  address carries the address, and every row of a device in the clear says it
  was not encrypted. The rows that record the request do; the rows of the
  actions it sets off do not.
- `docs/privacy.md` said the seven-day preset leaves the `action` category
  alone. It shortens it too, because `action` records who acknowledged.
- `docs/keypads.md` called the *Unencrypted* warning permanent; it goes the
  moment a request from that device arrives encrypted.
- `docs/simulator.md` said the action test sounds a siren for three seconds
  whatever its configured duration. That holds for a siren that accepts a
  duration; one driven by a switch, or one that takes none, stays on until it
  is switched off. It also said the diagnostics' *Arming* column cannot say
  ready where arming would refuse: it reads faults and open zones, and a code,
  a permission or a running walk test can still refuse.

## [0.1.0-beta.22] — what the third review left open

The questions beta.21 left for the household, answered: SPEC decisions
128–147. Credentials stop coming back to the panel, a duress code is heard
whatever it is used for, an armed house keeps the answer and the codes it was
armed with, and an arming starts a clean watch. The stored configuration keeps
its schema.

### Changed — read these before you update
- **Home Assistant 2026.6 or later is required.** Earlier releases list every
  webhook to any signed-in account, and the acknowledgement webhook stops an
  alarm in progress (decision 147).
- **The acknowledgement webhook's address is shown once**, when you switch it
  on or press *Generate a new address* on the Contacts page — the full URL
  when Home Assistant knows its external address, the path otherwise. Copy it
  into the voice provider then; to see it again, generate a new one, which
  stops the old one at once. **If you switched the webhook on before beta.13,
  generate a new address**: older log rows printed it in full, and anyone who
  read or exported them may still hold it. Foyer now takes it out of those
  rows when the log opens.
- **The watchdog URL is never shown again once saved.** Page 14 says one is
  set and takes a new one typed over it; saving with the field empty, or
  switching the watchdog off, keeps it. The panel's `foyer/config` read carries
  `settings.ack_webhook_enabled` and `health.watchdog.url_set` instead of the
  id and the URL.
- **A duress code raises the silent `duress` event on every request it comes
  with** — arming, excluding, acknowledging, a walk test, the automatic rules,
  unlocking an API device, the panel's configuration and log commands,
  services — accepted or refused, a locked channel included. It is answered by
  the global default profile only and **always runs silent**: the kinds on the
  silent list (siren, TTS and chime by default) are left out, and the profile
  editor warns against a Home Assistant notification. It is never held back by
  a walk test. Its row stays on the log page, in exports and on the bus as
  `foyer_event`, but no longer appears among the Overview's recent events, in
  `sensor.foyer_last_event` or in an API device's log; switching the security
  log category off also stops its `foyer_event`. The row names what the
  request asked for, and a new template variable `{{ operation }}` lets a
  message say it. Emptying the log with a duress code keeps that request's own
  duress row.
- **While any area is armed, an edit that changes the answer or the codes is
  refused**: siren duration, the hold after the exit delay, the default
  delays, the walk test timeout, the default and technical profiles, the
  silent list, the camera folder, *Allow rules to disarm*, the code policy,
  code length and lockout, what any area or scenario asks a code for (a
  disarmed area and an idle scenario included), the radios and their
  thresholds, every profile the house could answer with, and any contact such
  a profile names. People, codes, tags, keypads, API devices, MQTT, the
  webhook and the automatic rules stay editable, except an edit that would
  leave nobody with a usable code. A restore is refused exactly where the same
  change would be.
- **Arming clears alarm memory**, with *Alarm memory cleared*, as a disarm
  does — an automatic rule's arming included — for each area it takes out of
  disarmed. It is not taking note of the alarm: the incident and its
  escalation carry on. A refused arming, the cutoff resuming an arming, an area
  staying armed through a scenario switch, a walk test, and an arming made as a
  walk test ends all keep the memory.
- **Home Assistant's alarm panels say arming needs a code only while nobody
  has the per-person exemption on.** Then the pop-up dialog and tile buttons
  stop asking, the exempt person arms with none, and anybody else is refused
  by Foyer with a message saying where to type the code. Alexa and Google
  Assistant read the same attribute. The *Whole house* panel says a code is
  needed as soon as one mode it can arm asks; a mode needing none then arms
  from an automation through Foyer's own `foyer.arm` service.
- **A keypad or API device with its right token is never refused because its
  address is locked** for wrong tokens; the rows it causes say the address was
  locked.
- **The walk test's reach is stated where it is granted**, unchanged: it arms
  every area it can whatever the person's areas, and keeps every area quiet,
  one somebody else armed included, for up to three hours. The Users page
  warns while *Walk test* is ticked.

### Added
- A one-time address box with a Copy button, and a confirmed *Generate a new
  address*, on the Contacts page.
- Notices on the Settings, code policy, automatic disarming and radio forms
  while an area is armed, and help entries on Settings, Contacts and Profiles.
- The log page shows a duress row's operation and target in words, and
  *Yes/No* for flags such as *address locked* and *encrypted*.

### Fixed
- A warning that a notification channel broke could report its own send and
  mark the next channel broken in turn, one after another; it is now counted
  with the next real send or channel sweep.
- A decision started from inside another — a zone or rule watching one of
  Foyer's own entities — recorded its rows and ran its actions before the one
  that caused it.
- A zone changing during the last save before a reload was decided by the
  system going away; nothing more is decided once a reload begins.
- `sensor.foyer_last_event` showed the event before the one that had just
  happened.
- The test button beside a channel now counts as a real send: a tested
  channel stops reading "never used", and a failed test counts.
- The `device_unlocked` row now records a request that was not encrypted.
- A watchdog error no longer keeps a host name that carries the token, and a
  URL that is not `http(s)` is refused when typed.
- A radio added on the System health page could not be saved.
- Arming over alarm memory kept the memory but forgot which zones had alarmed.
- The card's keypad layout offers *Arm* while an area holds alarm memory, as
  the other layouts do.
- The *Whole house* panel showed no code field where only an area or a
  scenario asked for one, and an area's panel none where its scenario asks a
  code to disarm.
- When the shared counter of many addresses sending wrong tokens locks, the
  notification says so instead of naming the address `*`.
- The built-in duress message no longer leaves an empty place for the area,
  and a switch answering duress no longer writes a visible cutoff row.
- The walk test's texts no longer say it arms and disarms every area, or that
  the zones of an area it left out cannot detect anything.

## [0.1.0-beta.21] — the third review

A full review of the code, engine to card, looking for bugs. Everything it
found that could be fixed without a decision on behaviour is fixed here; what
needs one is left for a later release. No schema change.

### Changed — read these before you update
- **Changing which entity a zone watches asks you to confirm the trigger
  again** (INV-5). The same trigger on another entity is one nobody has read
  against that entity's states: a lock's `locked`/`unlocked` never matches
  `on`, and the alarm would never fire.
- **Linking a contact to a different person needs `manage_users`**, like
  handing over a tag: an acknowledgement from that contact counts as that
  person.
- **The `action` category joins the seven-day preset.** Its rows say who
  acknowledged an alarm, so they name people like the other four.
- **A channel you switch off keeps its fault.** Switched back on, it shows
  the fault it was in rather than a channel nothing is known about.
- **New installations' default profile also announces a second zone joining
  an alarm** (`incident_joined`). An existing installation is not changed;
  add the moment to your profile if you want the whole story.
- **The stored configuration and state are now written private and atomic**,
  as Home Assistant writes its own credentials: the files hold code hashes
  and the keypad token's hash, and a power cut mid-write must leave the
  previous version whole.
- **The Zones page works for a person holding `edit_config`** who is not a
  Home Assistant administrator. Picking an entity was refused for them, so
  they could open the page and never add a zone.

### Fixed — the engine
- A verification group spanning an armed and a disarmed area, with member
  suppression on, was held for ever: the member in the disarmed area could
  never count. The PIR watching the armed area now acts on its own, as it
  does when the other member is excluded or in fault.
- Alarm memory was wiped without a disarm when the siren cutoff resumed an
  arming that then failed on an open zone. It now stays until somebody
  disarms, as §5.2 says.
- A walk test armed an area still holding alarm memory, then read that
  memory as "in alarm" when it ended and left the house armed with somebody
  inside. Such an area is left alone; its zones are still walked.
- Disarming an area armed on its own while a scenario ran was judged by that
  scenario's rules — refused to a person allowed the area but not the
  scenario. The scenario now has a say only over the areas it armed.
- Once the siren's own duration had run out, a later zone joining the same
  incident did not sound it again: the incident still counted it as running.
- A notification naming a channel the person has since switched off went to
  nobody. It now goes over their next enabled channel.
- A refused request that merely claimed a name (`user_id` with no code) is
  logged with the same `attributed: claimed` note as an accepted one.
- The simulator's trace explained an action skipped for a jammed radio, a
  walk test or a broken channel as skipped for no reason.

### Fixed — around the engine
- The executor is started before the state is saved, so a slow disk never
  stands between a decision and its sirens.
- Rows queued while Home Assistant reloaded the integration — the row
  recording the configuration save itself, most often — could be dropped
  when the log closed. The log is now closed last, after every listener, and
  a write in flight finishes.
- A setup that failed while starting a transport left the system running
  behind it. It is stopped before the error is raised.
- An acknowledgement button pressed on a stale notification, with the house
  quiet, wrote a refusal in the alarm log. It is ignored, as the DTMF webhook
  already did.
- A backup taken with the watchdog on could not be restored on an
  installation with no watchdog URL yet; the watchdog is restored off, and
  comes back when its URL is entered. A backup whose `config` is not a map,
  or whose lists are not lists, is refused instead of raising.
- A code colliding with somebody else's during admin recovery counts as a
  wrong code, so the recovery form is not an oracle over other people's
  codes.
- A configuration command carrying no code no longer wakes the engine with
  an empty attempt.
- A service refused by validation raised "?" as its reason; it now names the
  first problem.
- The names in a CSV export are exported as text: a zone named
  `=HYPERLINK(...)` is not a formula.

### Fixed — the panel and the card
- A second command asking for a code while a prompt was open took the prompt
  over and left the first command waiting for ever, with its page busy. The
  first is now answered "cancelled", and the page behind the prompt is inert
  so the keyboard cannot reach it.
- A settings change the backend refused, or whose prompt you cancelled,
  stayed on screen and was sent again with the next unrelated save; the
  refusal appeared under the wrong cards. The stored value comes back, and
  the message sits under the card you changed. Emptying the pseudonymisation
  days no longer saves zero.
- Settings and broker saves merged over the configuration as this panel last
  read it, writing another administrator's change back out. They are merged
  over the configuration as it is now.
- The master card showed an *Arm* button with no scenarios configured, which
  sent a request with no target.
- The automatic-disarming switch on the Rules page was disabled for a person
  holding `edit_config` although the backend accepted them.
- A panel whose subscription was refused retried on every state change.

## [0.1.0-beta.20] — when everybody leaves and a window is open

An automatic rule that met an open window used to fail quietly: the house
stayed disarmed, and the people who had just left heard nothing unless
somebody had added a notification to the response profile. SPEC §9.4 "When
the house is not ready", decisions 124–127. The stored configuration moves
to schema 8.3, additive.

### Changed — read this before you update
- **The contacts of an automatic rule now hear how its arming went**,
  through their quiet hours. A rule that could not arm, or armed with zones
  excluded, sends a second message after its countdown. One that armed as
  announced sends nothing more.

### Added
- **The countdown names what is not ready.** For example: "Nobody seems to
  be in, so “Empty house” will arm Away — but Bathroom window is not ready,
  and it cannot arm until it is." It says instead that the zone will be
  excluded when the rule excludes open zones.
- **The outcome, in words that follow what happened:**
  - not armed, naming the zones, and "it will arm by itself as soon as they
    are";
  - then "arming now" once they are;
  - armed excluding what was open;
  - an arming that failed at the end of its exit delay because a zone
    opened while everybody was leaving.

  A rule triggered by an instant (a time, an arrival) has one turn: it says
  it will not try again until its next time, and does not. A scenario
  switch is told in a switch's words.
- **"Arm anyway, excluding open zones"**, an option on each rule, off by
  default and warned about when switched on:
  - it excludes only the zones that are open and may be excluded;
  - a zone in fault or unavailable, or one that may not be excluded, still
    refuses the arming;
  - it covers what is open when the rule arms and nothing after;
  - an excluded zone is watched again as soon as it closes;
  - the log records a forced arming with the rule's name.

### Fixed
- A rule refused by a zone that may not be excluded never tried again. It
  now waits for that zone like any other.
- The hint beside **Arm without these zones** said the zones stay unwatched
  until you disarm. They are watched again as soon as they close.

## [0.1.0-beta.19] — API devices, and a documented contract

The device endpoint of beta.13 was built for a keypad. It is now the way any
device of your own reads the house and, when it is allowed to, acts on it: a
touch display in the hall, a relay that lights an "armed" lamp, an ESP32 or
Arduino module. SPEC §9.2.2, decisions 115–123. The stored configuration
moves to schema 8.2, additive: an 8.1 build reads it and ignores the new
fields.

### Changed — read these before you update
- **A keypad on the endpoint always asks for a code,** arming included, even
  where your code policy asks none (decision 116). The token alone must
  never be what arms the house: it crosses the network readable whenever the
  request is not encrypted.
- **A keypad on the endpoint can no longer take note of an alarm** until you
  give it that permission on the *Arming devices* page. Keypads already
  there keep reading the state, arming and disarming, which is what the
  update gives them. MQTT keypads are not affected.

### Added
- **Permissions per device.** On the *Arming devices* page, each device on
  the endpoint gets its own list of what it may read and do, every item off
  until you switch it on.
  - It may read: the state, the zones, batteries and tamper, system health,
    and the log.
  - It may do: arm (only the scenarios and areas you choose), disarm (only
    the areas you choose), exclude or include a zone again, and take note of
    an alarm.
- **Reading free or after a code.** Each reading is either free or needs a
  code typed on the device. A code unlocks it for 30 seconds to 10 minutes,
  as you choose, and within what the code's owner may see. Every unlock is
  recorded in the log. By default only the state is free.
- **Plain HTTP stays accepted.** Readings beyond the state travel
  unencrypted only if you tick the confirmation for that device.
- **Sections and notices.** The zones, batteries, health and log are each a
  small request of their own. The state stream says when one of them has
  changed, so an ESP32 reads only what it shows.
- **The contract, written down and tested:**
  - [`docs/api/openapi.yaml`](docs/api/openapi.yaml) for the endpoint and
    [`docs/api/asyncapi.yaml`](docs/api/asyncapi.yaml) for MQTT, at contract
    version `v1`;
  - a CI test compares both with the code, so they cannot drift;
  - an *API* page in the panel, for administrators, shows the contract with
    Swagger UI and lets you try requests with a device token. The library
    is bundled with the integration, loads only on that page, and nothing
    is fetched from outside the house;
  - [`docs/keypads.md`](docs/keypads.md) now documents the endpoint and API
    devices, with worked requests.

### Fixed before release
A security review of the feature found five things, each closed and tested:
- arming a scenario that leaves armed areas out disarmed them without the
  device's disarm permission;
- an unlock survived its owner being disabled;
- the log, the zones, the batteries and the health read after a code were
  not limited to the permission to view the log and to the person's areas;
- the stream announced changes a locked device could not read;
- the health section carried people's names and phone services.

## [0.1.0-beta.18] — easier to set up, and to arm with a code

A full review of the panel and the card for usability, and of every string
in both languages. Reviewers read and used the panel and the card in both
languages, light and dark, down to a 220 px wide card, and others verified
the fixes. The stored configuration stays at schema 8.1.

### Changed — read these before you update
- **The panel forgets a code** two minutes after it was last used, after
  every arming or disarming, and when the panel closes. Until now it kept a
  code that had worked for the whole visit, so whoever came next to an
  unlocked wall tablet could disarm or reconfigure without typing it
  (decision 114). Expect to be asked again during a long configuration.
- **The words changed**, in both languages, to one term per idea:
  - in English, *Exclude / Include again*, *Whole house* (also the name of
    the whole-house alarm entity in Home Assistant; its entity id is
    unchanged), *siren*, *Automatic rules*;
  - in Italian, always *inserire / disinserire*, *prendere atto*,
    *escludere / includere*, *tastierino*, *impianto*, *registro*.

  Automations that match on a displayed name rather than an entity id
  should be checked.

### Added
- **A code prompt that says what it is for, and who asks.** "Code to arm
  Away", and, when an area's or a scenario's own setting asked, "Upstairs
  asks for a code". The engine now reports which setting asked (§8.2).
- **The Overview arms a scenario with a button of its own**, says whether
  the house is ready, and shows a lock on the scenarios that ask for a code.
  Arming one area alone is behind *Just one area…*.
- **The scenario editor has its code settings** and the list of people
  allowed to use it, which had been in the model since Phase 1 with no page
  to set them.
- **Deleting asks first**, beside the button, on every page; a new code is
  typed twice.
- **The card:**
  - the keypad opens by itself during an entry delay when disarming asks for
    a code;
  - it names what the code is for and labels the confirm key with the
    action;
  - it shows until when a lockout lasts;
  - smoke and open incidents now show on the compact layout and the badge
    too.

### Fixed
- **The first-run wizard threw away a person typed in its user step**
  unless a second button was pressed. It could also save a threshold or a
  trigger nobody had seen (INV-5): it now sends those zones to the Zones
  page.
- **The panel resent a wrong code** with the next command, spending the
  lockout without anybody typing.
- **On the card, digits typed for one command could go with another**: a
  banner button, a second action, or a Clear that forgot what the digits
  were for.
- **During a forced arm the card's most obvious button repeated the refused
  arm** and spent the code.
- **A keypad for one area lost every button** while a different area was in
  alarm.
- **A delete question moved to the next item opened**, where one click
  deleted something nobody had chosen.
- Italian meanings that were wrong (*Armatura automatica*, *Pastiglia*,
  *Ritenuto*, "nessuno viene chiesto") and gender agreements; specification
  references and promises of protection taken out of what a household reads.
- The Overview's help starts collapsed, so on a phone the controls are on
  the screen (decision 113).

## [0.1.0-beta.17] — manage_users, wherever people are touched

One open item from beta.16, closed. The stored configuration stays at schema
8.1.

### Changed — read this before you update
- **Changing who may do what needs `manage_users`, from any page.** Beta.16
  asked for it when a restored backup changed people; the editor still let
  `edit_config` alone give a key switch to somebody or add a name to the
  people allowed to use a scenario. Now every save, deletion or restore that
  touches a person, a tag, the person a key switch acts as, or a scenario's
  list of people asks for `manage_users` as well (decision 112). Renaming a
  scenario or moving a zone still needs `edit_config` only.

## [0.1.0-beta.16] — a way back in, and what a restore may touch

Beta.15 asked an administrator for the code like anybody else and left four
questions open. They are settled in SPEC §21 (decisions 108–111) and built
here. The stored configuration stays at schema 8.1.

### Changed — read these before you update
- **Restoring a backup that changes people needs `manage_users`** as well as
  `edit_config`. That means a backup that adds, removes or changes a person,
  a tag, or the person a key switch acts as. `edit_config` alone was a way to
  give yourself every permission through a file, or to hand somebody's tag
  to somebody else. A restore that leaves people alone still needs
  `edit_config` only. This applies to the panel and to
  `foyer.import_config`.

### Added
- **Recovering access, from Home Assistant.** An administrator who holds no
  code, in a house where others do, could change nothing after beta.15. The
  same was true of one whose own Foyer user had been disabled or had run past
  its validity window. **Settings → Devices & services → Foyer → Configure**
  now recovers access for an administrator's account:
  - it enables that account's Foyer user, removes its validity window and
    sets a new code;
  - an account with no Foyer user gets one, with every permission.

  It is never quiet. Once the change is written, it is recorded in the
  `security` log, shown as a Home Assistant notification and sent to every
  contact, through quiet hours, naming the account. Home Assistant does not
  tell an integration who opened the step, so the step asks which account;
  only administrators' accounts are offered.
- **`alarm_cleared`**, a moment raised when a disarm clears an area's alarm
  memory, even hours after the siren stopped. It is the moment for switching
  off a lamp that says an alarm happened while you were out.
  `alarm_ended` still marks the end of the alarm itself.

### Fixed
- **Downloading a backup without a code seemed to do nothing.** Beta.15 asks
  for the code, but a refusal went to a list the backup card never showed.
  The card now says it, beside its buttons.
- The settings page no longer stops drawing when the list of message
  languages does not arrive.

## [0.1.0-beta.15] — what the second review left to decide

No new features beyond one moment. Beta.14 fixed what the second full review
found and left a handful of questions that were decisions rather than
defects; they are settled in SPEC §21 (decisions 100–107) and built here. A
dedicated review of the dashboard card found five more defects, fixed below.
The stored configuration stays at schema 8.1.

### Changed — read these before you update
- **A Home Assistant administrator is asked for the code** to change the
  configuration, when the code policy asks for one — like anybody else.
  Being an administrator identifies nobody: the unlocked wall tablet is
  almost always signed in as one. Reading pages still asks for nothing, and
  an administrator is still never locked out. If you are the only person
  with a code, the panel now asks for yours when you save, and when you
  download a backup.
- **A `user_id` named in a service call grants nothing**, on any service —
  `foyer.export_log`, `foyer.export_config` and `foyer.import_config`
  included. It is still recorded as a claim in the log. An automation that
  read the log by naming a person must now send that person's code.

### Added
- **`alarm_ended`**, a moment for each area an alarm touched: raised when its
  siren cutoff runs, or when it is disarmed during the alarm — never on an
  ordinary disarm. It is the moment for "switch the light off when the alarm
  is over". The Alarmo importer now maps `untriggered` to it, instead of to
  every disarm.

### Fixed
- **The card sent digits left on the pad with the next button pressed**,
  including Cancel on an automatic countdown, Acknowledge and End walk
  test: refused as a wrong code, counted towards the lockout, or acting in
  the name of whoever typed them. Banner buttons no longer take the pad's
  digits, and typed digits are forgotten after 30 seconds without a key and
  when the card leaves the screen.
- **The card's keypad on the whole house showed no countdown** during an
  entry delay.
- **A renamed master entity broke the card**: the keypad showed
  "disarmed" and the full layout never loaded.
- **The card's badge said "arming"** for a rule about to disarm, and lost the
  area's name when narrow.
- **Once the device endpoint's shared counter was locked**, further guesses
  left no trace. They are now counted and written as one `security` row a
  minute: how many, from how many addresses.
- The card shows until when a lockout lasts, takes digits, Backspace and
  Enter from a keyboard, says in your language when a command did not
  arrive, and its editor no longer looks set when it is not.
- Rows for a refused device, and the new summary row, show "Refused" in the
  log like every other refusal, rather than a raw word the filter could not
  find.
- Configuration rows about contacts and automatic rules name the field that
  changed, not its value: a notify service is named after somebody's phone,
  and a rule's trigger names the people it watches.
- Internal: one gate for the configuration and the log, shared by the panel
  and the services; one path for wrong codes and one for tags and key
  switches, each with tests that pin the merge changed nothing.

## [0.1.0-beta.14] — what a second full review found

No new features. Six reviewers read the whole repository again after beta.13
— the pure engine, the response and log support, the Home Assistant layer,
the API and its security, the stored documents, the panel — and four more
checked the fixes. **Take this one**: several of the defects below are the
kind an alarm must not have. The stored configuration stays at schema 8.1.

### Changed — read these before you update
- **A refused `foyer.*` service now raises an error when the caller does not
  ask for its response.** An automation calling `foyer.disarm` without
  `response_variable` took a wrong code, a lockout or an open window for
  success and carried on. A caller that asks for the response still gets the
  structured result of §9.1, refusal included. An automation that relied on a
  refusal passing silently will now stop, and say why.
- **Wrong codes on the panel and through the services count per Home
  Assistant account.** One shared counter let any account, even one with no
  permissions, lock the whole household out of the panel and of every
  automation by typing five wrong codes.
- **Arming during a walk test is refused** with its own reason. It used to be
  accepted — every area is already armed by the test — and the end of the
  test then disarmed the house its owner believed armed.
- **Each zone joining an incident sends its notification again**, and
  notifications now wait for their transport's answer: a channel that accepts
  and then fails (a revoked Telegram token, a refused push) is no longer
  counted as sent, so the test button, channel health and the retry see it.
  Actions run beside the request that caused them, so no keypad, service or
  panel waits for a notification.
- **A code that belongs to somebody else**, offered when saving a person,
  now counts like a wrong code, and is checked only once the rest of the
  person is valid: the check could be used to test codes without limit.

### Fixed — the ones that mattered most
- **After a restart, disarming switched off a smoke sounder.** The flag that
  keeps a technical sounder out of a disarm and of the intrusion siren
  cutoff was not saved.
- **An automatic disarming rule could close an alarm still in progress**: after
  the siren cutoff an area is armed again with its incident unacknowledged,
  and the rule's disarm acknowledged it — the stolen-phone case §9.4 exists
  for.
- **The device endpoint could be locked for every keypad**, correct token
  included, by anybody who filled its sixty-four per-address counters first.
- **The warning about a broken channel reached nobody** when the person's
  first channel was the broken one, though their second worked.
- **A suppressing verification group with a member excluded** held its last
  working detector back for ever.
- **Re-enabling a key zone, a rule, or saving a time rule after its hour** acted
  at once; a new button's first press was lost. Only a change out of
  `unavailable` is a restore.
- **An action could write camera pictures under `www`**, which Home Assistant
  serves without authentication.
- **An empty "mains lost" state list was saved as `on`**, so the mains alarm
  of a power sensor could never fire.

### Fixed — also
- The repair cards measured in days never appeared on a quiet house; the
  first configuration save after every start logged an error; the last save
  on unload did not happen; neither the log nor the timers can now keep a
  stored decision's actions from running; the state file is no longer
  rewritten for sensor attributes nothing reads.
- Log exports reach ten thousand rows again; the log's privacy sweeps
  overwrite what they remove instead of leaving it in the file; the
  configuration log records people, contacts and rules — by id, never by
  name, number or code — and says when a webhook id or the watchdog URL is
  replaced.
- Invented device names are capped and shown as text, never as a link; a
  name of a token keypad used on the broker is never lost among them.
- The simulator shows who a notification reached and the siren time the
  engine used; `{{ user }}` names the person (not a claimed one); a smoke
  sounder takes the global siren time; bypass durations are bounded.
- The panel: a dropdown or checkbox could show a value different from the
  one saved; a PIN typed for one person stayed in the field for another and
  was not sent; a switch left wrong by a refused save now goes back and says
  why; tests run only what is saved; clearing the log asks for the code;
  emptied number fields no longer turn into their default or zero; hidden
  fields left by a change of zone channel or rule trigger are cleared; times
  follow the house's time zone; every list opens from the keyboard; words
  the log and the simulator showed as raw keys are translated.
- The Alarmo importer says that an automation run "when the alarm ends" now
  runs at every disarm, and when an extended scenario's own delays apply to
  the imported areas.

## [0.1.0-beta.13] — where it happened, and a keypad that proves which it is

Two additions before the documentation (§6.2.1, §9.2.1): the alarm shows the
cameras of the zones that raised it, and a keypad can speak to Foyer's own
endpoint with a token instead of giving its name on a broker. **The stored
configuration moves to schema 8.1, a major step**, and going back to beta.12
afterwards is refused on purpose: an older build would not know that a keypad
belongs to the endpoint, and would accept its name over MQTT — exactly the way
round the token that this release closes. The reasoning is in
`store/schema.py`, beside the others. Nothing anybody already receives
changes: a notification that named a camera keeps it, every other keeps
sending none, and every keypad stays on the broker until somebody moves it.

### Added
- **The zone's cameras** (page 3). A zone lists, in order, the cameras that
  show it and the rooms around it. A notification can now say which pictures
  it carries: none, always the same camera, or **the cameras of the zones
  behind the alarm** — every zone that has joined the incident, in the order
  they went, each camera once, at most four, and the message says how many
  were left out. A new notification starts there.
- **One notification per camera, after the text.** The text goes first with
  its acknowledgement button, exactly as before, and it is the one channel
  health is counted on; each camera follows as its own notification with its
  picture and its name — a live link for the Companion app, a snapshot for
  Telegram. A camera that does not answer costs its own picture and nothing
  else. Only push and chat channels receive pictures: an SMS or a voice call
  gets the text alone, not four more texts or four more calls. The pictures
  never carry the channel's `tag`, under which the app would replace the text
  and its button.
- **Every notification repeats the cameras, fresh**: the first message, each
  zone joining, each escalation step. **Only at an alarm** — a trigger, a zone
  joining, a satisfied verification group, an escalation step, a technical
  alarm with the cameras of the technical zones pending — and **never when an
  entry delay starts**, because that is somebody coming home and a photograph
  of every homecoming sent out of the house is what Foyer's first principle
  exists to stop. The profile editor says at which of an action's moments it
  sends its text alone, and the simulator lists which cameras each
  notification would carry, without taking a picture of anything.
- **The device endpoint** (page 8): `POST /api/foyer/device` and a
  Server-Sent Events stream at `/api/foyer/device/state`, each keypad with a
  token of its own. **The token authenticates the keypad; it does not encrypt
  anything.** The code is still required and still the identity of whoever
  typed it, the channel is `keypad`, the lockout counts per keypad as it
  always has. The stream is the MQTT state message at the same detail level,
  `minimal` by default, pushed the moment anything changes; the answer to a
  command is the §9.1 result with that same message as its state, never the
  panel's whole status. A keypad uses the broker or the endpoint, never both:
  **an endpoint keypad's name over MQTT or in a service call is refused**, told
  exactly what an unknown device is told, and recorded and notified as what it
  was.
- **The token** is 32 random bytes, shown once when it is generated, kept only
  as a fingerprint, never in a backup, the diagnostics, a log row or the panel,
  and never set by a restore. Generating one invalidates the old at once and
  closes its streams; generating and revoking need `edit_config` and a code.
- **A wrong or missing token** is answered 401 and nothing else, counted per
  source address through the same lockout as a wrong code — an IPv6 host by
  its /64 — and a locked address is refused, recorded and notified once. The
  endpoint answers 404 in an installation where no keypad uses it.
- **Plain HTTP is served, and said.** Foyer judges encryption as Home
  Assistant does, including behind a reverse proxy it trusts. A keypad whose
  last request arrived in the clear carries a warning on page 8 until one
  arrives encrypted, across a restart, and every row it causes says so.

### Changed
- **Each zone joining an incident now sends its notification.** An action on
  "a zone joined the incident" went out for the first zone to join and never
  again: the rule that keeps a siren from restarting was swallowing messages
  too. Sirens, lights and switches are still started once per incident; a
  notification repeats for every zone that joins.
- **A configuration save refuses to run while the previous one is being
  applied**, and says so. Between a save and the reload it causes, a second
  edit was built from the document the running system still held and could
  write the first one's change back out — a revoked token restored by
  renaming a zone a second later.

### Fixed
- **Replacing the watchdog URL or the acknowledgement webhook left no trace in
  the log.** The configuration row now redacts all three credentials — those
  two and a keypad's token — and still says each one changed. Before this
  release the webhook id and the watchdog URL were written into the row in
  full whenever they changed.
- **The duress moment was offered in the profile editor under its raw key**,
  in both languages.
- **A device retrying every fifty seconds left one row in all** instead of one
  a minute, because a suppressed report refreshed the timer that suppressed
  it.
- **Two notifications taking the same camera in the same second wrote one
  file**, and one of the two pictures arrived empty.

## [0.1.0-beta.12] — the way in, and the way to help

The third part of Phase 5 (§20.2, §20.3): a way in for a house that already
runs Alarmo, and a way to report a defect that arrives answerable. **The stored
configuration moves to schema 7.4, a minor step**: a zone gains one field that
records whether its trigger was confirmed, every zone already stored is, and a
7.3 build reading this document ignores it. The reasoning is in
`store/schema.py`, beside the others.

### Added
- **Import from Alarmo**, on page 11. It reads Alarmo's configuration from
  this Home Assistant's own `.storage/alarmo.storage` and brings its areas,
  sensors, modes and people in **beside what is already here**. It is a
  best-effort tool and says so: that file is Alarmo's internal format, which
  may change in any release without notice and without anybody being at
  fault, so the importer reads only the storage versions it was checked
  against — 6.1 to 6.3, written by Alarmo 1.9.5 to 1.10.19 — refuses any other
  by name, refuses a file whose shape is wrong rather than bring half of it,
  and lists everything it could not convert. It shows what it would do first;
  **Apply** stores exactly that, and is refused if the file, the configuration,
  or the name or presence of one of Alarmo's sensors changed in between —
  never because a sensor moved while somebody was reading. It is a configuration change like any other:
  `edit_config` with a code, `manage_users` too because it creates people, the
  same validation, refused while an area it would change is armed, and a row
  in the log.
- What it makes of Alarmo, in short: one Foyer area per Alarmo area and set
  of modes its sensors were watched in; one scenario per mode you had switched
  on, or the existing scenario for that master state extended with the new
  areas, so HomeKit's "away" keeps working; the longest delay or siren time
  wherever Alarmo had several and Foyer has room for one; a siren sounded when
  the alarm triggers, and switches, into a response profile that starts as a
  copy of your default one. Notifications, groups and
  the rest are report lines, not guesses.
- **Imported zones arrive switched off, with their trigger unconfirmed.**
  Alarmo reads `on`, `open` and `unlocked` as alarm for every sensor, which is
  the assumption INV-5 exists to refuse. Each zone carries Foyer's own proposal
  and a notice on page 3, and cannot be switched on until somebody confirms it
  — enforced by validation on every path that stores a configuration, not
  only by the editor.
- **Nobody arrives with a code.** Alarmo keeps its codes as hashes in its own
  format, and Foyer does not take a credential from another system on trust;
  the report says in its first line that every person brought in needs a new
  one.
- **Issue templates.** The bug form asks for the Foyer and Home Assistant
  versions, Foyer's own log and the diagnostics download, and says where each
  is — but requires only the versions, because a Foyer that did not load has
  no diagnostics button. Blank issues are off, and the chooser leads with the
  private advisory. A pull-request template carries the checklist.
- **`CONTRIBUTING.md`**: the development setup, the `core/` purity rule, what a
  pull request has to carry, and the two files a translator copies.

### Fixed
- **Adding a language touched code**, whatever the README said. The
  translation test pinned English and Italian and failed on a third file
  without naming it, and the list of languages Foyer can send messages in was
  written in the Settings page. Languages are now the files on disk, each
  file names its own language, and every one is checked against English.
- **Page 10's help panel had no "Learn more" link**, though `docs/privacy.md`
  was written for it in the previous release.

## [0.1.0-beta.11] — what a full review found

No new features. Five reviewers read the whole repository — the pure engine,
the Home Assistant layer, the API and its authorisation, the stored documents
and their migrations, the panel — and this is the result. **Take this one.**
Three of the defects below break something the specification calls
non-negotiable, and one of them made a shipped feature impossible to turn on.

### Fixed — the three that mattered most
- **An automatic rule could disarm a perimeter area** (§9.4 point 3). The
  guard that keeps a rule off the perimeter works out what a scenario switch
  would drop, and it was reading the areas as they are now against the active
  scenario as it was when the decision began. Anything that switched scenario
  earlier in the same turn left it finding nothing to refuse, and the arming
  that followed disarmed the perimeter itself. This is the constraint the
  specification says is enforced in the engine rather than in the UI.
- **Disarming silenced the technical channel** (§5.5). A smoke, gas or flood
  response carries the area of the zone that raised it, so disarming that
  area — or the intrusion siren cutoff — stopped its sounder and abandoned the
  rest of its sequence. Disarming is an intrusion command and has no authority
  there; a running action now knows which channel it belongs to.
- **A satisfied verification group's profile never reached the incident**
  (§4.8, §5.6). The group was resolved and then ignored, so the incident
  adopted a quiet member profile's escalation — or none at all, when the
  member profile had no steps. The graduated response the feature exists for
  was not happening.

### Fixed — settings that unmade themselves
- **Automatic disarming could never be switched on.** Every settings save
  rebuilt the settings object field by field, and this one was not in the
  list, so it fell back to `False` — and any unrelated save turned it off
  again.
- A partial **code policy** or **log settings** payload reset every field it
  did not mention, including retentions the household had lengthened.
- A configuration document written by a newer **minor** version — additive by
  contract — failed to load at all instead of ignoring the one key it did not
  know. A rollback bricked the integration rather than surviving it.

### Fixed — the alarm itself
- An **exhausted escalation** started again from step 0 every time another
  zone joined the same break-in: push, SMS, the neighbour, once per zone.
- A sequence held by a **delay** outlived the siren cutoff and started the
  bell afterwards, on a house that was armed again, for its whole duration.
- A **silent zone** was not silent on `incident_opened` or `incident_joined`,
  which is the natural place to put one siren per incident. An incident is
  silent when every zone that has joined it is.
- A verification **group whose members are switched off** can never be
  satisfied; a suppressing one held back every alarm its survivors raised, for
  ever. It now suppresses nothing, and page 13 says the group is incomplete.
- `unavailable` and `unknown` satisfied an `is not` condition. An entity that
  cannot be read satisfies nothing (INV-4).
- **Low batteries are persisted**, so a flat cell is announced once rather
  than at every restart and every configuration save.
- Retention bounds are checked where a **restored backup** passes as well: nought
  days is not a short retention, it is a purge that empties a category daily.

### Fixed — the Home Assistant layer
- **Half the entities the engine reads were subscribed to by nobody**: the
  mains sensor, every zone's battery entity, each radio's coordinator and
  every entity an action's condition reads. A power cut was noticed at the
  next door opening.
- A wrong code on a **configuration or log command** counted towards no
  lockout and left no row — an unlimited, silent oracle over the code space.
  It now spends the same counter, and raises the same `lockout` moment a
  response profile can answer, as a code typed on a keypad.
- A backup no longer carries the **acknowledgement webhook id** or the
  **watchdog URL** out, and a restored document can no longer choose either.
  Both are credentials: the first is an unauthenticated URL that stops an
  alarm, the second keeps a dead installation looking alive.
- Saving an **arming device of kind "tag"** now asks for `manage_users`. A tag
  carries no code and commands as whoever it names, so minting one was a way
  for `edit_config` to become `disarm`.
- A request that raced an entry reload was answered **success** while nothing
  happened; a pending automatic rule spun the scheduler through startup; a
  save from an unloaded instance could land on its replacement's state; an
  entity whose property raised took the state save and the log rows with it;
  and a wake-up that raised stopped the scheduler permanently.
- The pseudonymisation sweep of §10.4 reached no configuration rows, because a
  row records the Home Assistant account and the sweep searched for the Foyer
  one.

### Fixed — the panel
- Nine event types printed as their own identifier, `duress` among them, and
  every automatic-arming, lockout and walk-test row printed `detail.rule`,
  `detail.strike`, `detail.pending_id`. A detail with no label now reads as
  its own name.
- Eleven CSS classes were used with no rule behind them: every "small" button
  rendered full size, editor footers sat flush against the card edge,
  separators separated nothing.
- The first escalation step is Step 1. A zone gaining "always on" loses the
  chime the same tick hides. The `duress` moment can be answered from the
  profile editor at all. A refused entity proposal says so. A refused visitor
  window keeps what was typed. Two pages print times in the Home Assistant
  user's language rather than the browser's.

### Raised, not changed
Two contradictions between what the code does and what the project says it
does. Both are decisions rather than defects, and the README and this
changelog will say which way they went once they are settled: whether an
unlinked Home Assistant administrator should be asked for a code, and whether
a `user_id` a service call merely claims should carry that person's
permissions.

## [0.1.0-beta.10] — the log is about people, and leaving takes what it brought

Privacy tooling (§10.4) and clean uninstall (§16): the second part of Phase 5.
**The stored configuration moves to schema 7.3, a minor step** — everything in
it is additive, and a 7.2 build reading this document is a build that never
pseudonymises an old row and never takes the log database with it, which is
exactly what it did yesterday. Upgrading changes nothing until somebody
switches something on.

The reason this part exists is one sentence in §10.4: the log records who was
in the house, when they arrived and when they left. In a family that is
nobody's business but yours. It stops being that the moment the log records
the cleaner, the boiler engineer or the babysitter — and it never was that for
a B&B, a holiday let or a small office.

### Added
- **Export one person's rows** (§10.4), on page 10, as CSV or JSON, in a file
  named after them. The selection is wide on purpose: what they did, plus the
  rows where they are the subject rather than the actor — a tag of theirs
  refused, an escalation that reached them. It is a second caller of the
  export of §10.3, not a second export.
- **Erase one person's history**, which is deliberately not "delete a user".
  Deleting a user leaves the history of what they did, because the name is
  copied into every row precisely so that it does. Erasing empties the name,
  the account, the channel and the device on their rows, and takes their name
  out of the JSON detail — and leaves every event exactly where it was. The
  log still answers "what happened on the night of the fourteenth" and no
  longer answers "who". A preview says how many rows each key found before
  anybody presses anything, and the erasure records itself without naming the
  person it erased.
- **Timed pseudonymisation**, off by default. After N days a row keeps a
  stable opaque identifier instead of a name. The panel says, before you
  switch it on and again in the confirmation, that this trades away the answer
  to "who disarmed that night" for every older row — which is the very
  question the log exists to answer. It runs beside the retention purge, never
  on the alarm path, and switching it on and switching it off are both
  recorded.
- **A seven-day retention preset** for installations with domestic staff,
  touching only the categories that name people and leaving actions, faults
  and door states where they are.
- **Clean uninstall** (§16). Removing the integration now takes its entities
  and devices out of both registries, the sidebar panel, its repair issues,
  the notifications it put up, and **the retained MQTT message** — which
  otherwise outlives the integration and goes on telling whoever connects to
  that broker next what the house was doing. The log database goes only if a
  switch on page 11 says so; it is off, because §16 says to ask rather than
  guess and keeping is the answer that destroys nothing. Camera snapshots are
  never deleted and are named in the documentation instead.
- **`docs/privacy.md`**: what a row contains, where the household exemption
  stops, and what to do about it. Practical information, and it says so.

### Changed
- The configuration schema moves from 7.2 to 7.3, additively. Every person
  gains a stable identifier, minted once and never recomputed.
- **A configuration row now records the Foyer person** behind the Home
  Assistant account that saved it, when the two are linked. They were two
  different namespaces, so a question about a person could not reach anything
  they had ever changed from the panel.
- Both READMEs say where this came from — most people who arrive already own
  the sensors — and `SECURITY.md` opens with what this is: an integration that
  does what an alarm does, not a certified alarm system.
- Every screenshot in both READMEs is recaptured from one configuration, in
  each language's own words.
- The rules page no longer says "1 people away for 10 min", and the code
  policy no longer lists `operation.cancel_auto_action` untranslated.

## [0.1.0-beta.9] — an alarm that can say it has stopped working

System health (§12): the first part of Phase 5. **The stored configuration
moves to schema 7.2, a minor step** — the whole block is additive, and a 7.1
build reading this document is a build with no watchdog, no mains entity and
no radios, which is exactly what it was yesterday. Upgrading changes nothing
until somebody switches a part of it on: the watchdog needs a URL, the mains
needs an entity and the state that means failure, and interference detection
needs a coordinator entity named per radio.

### Added
- **Mains power** (§12.1). Name the entity your UPS or smart plug exposes and
  which of its states means the mains has failed — asked rather than guessed,
  for the same reason every zone's trigger state is asked. A failure raises
  `system_power_lost` at once, at alarm severity, and a response profile can
  act on it. It never touches an `alarm_control_panel`.
- **Notification channel health** (§12.2). Every configured channel is checked
  every quarter of an hour against the service registry, and after every real
  send. A service removed, renamed or failing to load after an update is
  broken at once; two failed sends in a row are broken too, and any success
  clears it. The warning goes out over a channel that still works, and the
  moment `notification_channel_down` carries which one that is.
- **An external watchdog** (§12.3). A URL of your choosing, pinged every
  fifteen minutes. **The heartbeat carries nothing**: the payload option is
  off, and even switched on it says how many areas are armed and never which
  scenario, which areas or which zones are open. Three failures in a row and
  Foyer says so locally, because being unable to reach the endpoint means no
  internet-based notification would go out either.
- **Radio interference detection** (§12.5), stated as the heuristic it is.
  Four zones on one radio — or 40% of that radio's zones, whichever is lower —
  going quiet inside sixty seconds, with the coordinator still answering, and
  still true sixty seconds later. Disarmed it is a warning; armed it opens an
  incident, as jamming does in a professional panel. **Foyer does not act
  through the affected radio**, and the message says which actions were
  skipped and why.
- **Repair issues** (§12.4). A zone unreachable for two days, a broken
  channel, a watchdog that has never succeeded, suspected interference, a
  coordinator that has been gone for an hour and a power cut that has lasted
  an hour all appear in Settings ▸ Repairs, where somebody meets them without
  opening the Foyer panel. Each one can be marked as seen.
- **Anonymised diagnostics** (§12.4). Home Assistant's own download button now
  answers: the shape of the installation, with no names, no codes, no hashes,
  no URLs and no real entity ids. Built as an allow-list, so a field added
  later cannot leak by being forgotten, and entity ids become placeholders
  numbered from the configuration's own order — stable across two downloads,
  and not hashes.
- **`binary_sensor.foyer_system_health`** with the causes as attributes, and
  **`binary_sensor.foyer_rf_interference_<radio>`** per radio (§13).
- **Panel page 14 — System health**, with its help panel. The condition on
  top, readable by whoever may read the log; the configuration under it, which
  is `edit_config` and its code policy.
- **Ten new moments** a response profile can answer, all logged under
  `system`: the power going and coming back, a channel going and coming back,
  the watchdog going and coming back, interference suspected and over, and a
  coordinator going and coming back.
- **`docs/system-health.md`** and **`docs/resilience.md`** — the second of
  which §7.3 has been owed since Phase 4: cut power and cut fibre, a UPS on
  the router, and why a local GSM channel is the only one that survives.

### Changed
- The configuration schema moves from 7.1 to 7.2, additively.
- **The default response profile gains four moments on upgrade**: the power
  going out, a channel breaking, the watchdog going deaf and interference
  being suspected. This is the one thing the migration changes about an
  existing configuration, and it is decision 71's precedent — an installation
  upgrading into this phase would otherwise gain a power cut it is never told
  about. They are ordinary ticks on page 5 and a household that finds them
  noisy unticks them.
- The `notify` executor now reports, per contact channel, whether each send
  succeeded, which is what channel health counts.
- A broken channel now appears on the Contacts page as well as page 14, and
  the message that says a channel is broken is never routed through it.
  Everything else still tries a channel Foyer believes is broken: two failed
  sends can be a provider with a hiccup, and being wrong about a channel must
  never be the reason an alarm reached nobody.
- Every help panel gains the "Learn more" link §15.2 has asked for since
  Phase 1, on the five pages whose document exists.

## [0.1.0-beta.8] — the house arms itself, and says so first

Automatic arming rules (§9.4): the second half of Phase 4. **The stored
configuration moves to schema 7.1, a major step** — everything in it is
additive, but a 6.x build reading this document would ignore the rules and,
worse, would not know which area is the perimeter, so a rule it gained later
could disarm the one ring that is never disarmed by a rule. Both failures are
silent, so the file is refused instead. Upgrading migrates in one step and
changes nothing: no rules, automatic disarming off, no area marked as the
perimeter until you mark one.

### Added
- **Automatic arming rules** (panel page 12). A closed model, not an
  automation engine: four triggers — everybody away for N minutes, somebody
  arrives, a time on chosen weekdays, an entity holding a state — three
  actions, an active window outside which the rule does not exist, and three
  guards. A rule acts as a user would, through the same arming path, and every
  row it writes carries its name and the channel `auto_rule`.
- **A cancellable countdown before it acts.** The rule announces itself to the
  contacts it names, with a **Cancel** button in the push — the same
  actionable-notification machinery the acknowledgement uses, with a different
  action id. Press it and the rule waits until its condition becomes true
  again; press nothing and it acts, and the guards are evaluated a second time
  first, because two minutes is long enough for somebody to come home.
- **Guards, and a log row when one stops a rule.** Only if currently disarmed,
  only if every zone is ready, only if no interior zone has moved for N
  minutes — the last one catches somebody asleep upstairs with a flat phone.
  A blocked rule is written to the log under `system`: "why did it not arm
  last night?" is a question people ask, and silence is the worst answer.
- **Suspensions, and the expected-visitor window.** Skip the next occurrence,
  suspend until a date and time, or name a window — "Boiler engineer,
  09:00–13:00" — which can put a reduced scenario in place of what the
  suspended rule would have armed. Mechanically the same thing; the difference
  is that in six months the log still says why.
- **`switch.foyer_auto_arming`**, the global kill switch, which also cancels
  whatever is counting down, and **`sensor.foyer_next_auto_action`**, whose
  state is the action — `arm`, `disarm`, `switch`, `idle` — with the instant,
  the rule and any suspension as attributes. It reports what is *scheduled*,
  not what will certainly happen: the guards are evaluated when the rule acts.
- **`is_perimeter` on an area** (page 2). The outer defence ring.
- **The countdown on the card, with its Cancel button** — on every layout
  that can be pressed, and on the badge, which presses nothing, as a chip
  with the seconds on it. A card bound to one area still shows it: a rule
  arms a scenario, and a hall panel that stayed quiet while the house armed
  itself would be the silence the walk-test banner is everywhere to avoid.
- **The simulator reaches the rules.** Pick a hypothetical Tuesday at 23:00,
  override the people a rule watches, and read the trace. The kill switch and
  the suspensions in force come with it, so "would it arm tomorrow morning,
  with the engineer expected?" has an answer; everything the trace says about
  a rule is read off the same Decision the runtime acts on.
- **`docs/automation-rules.md`**: presence-based arming from the start, the
  guards, the two kinds of trigger and what each does when a guard clears,
  suspensions, and an unhedged section on why automatic disarming is
  restricted.

### Security
- **Automatic disarming is off until you turn it on, and never touches a
  perimeter area.** Presence in Home Assistant is inferred from a phone: a
  stolen phone disarms the house, GPS drift of 200 metres disarms the house, a
  cloned MAC address on the home network disarms the house. Enabling it is a
  deliberate act beside that paragraph. The perimeter constraint is enforced
  in the engine, with a test asserting it on the `Decision` — a `disarm` rule
  leaves those areas out, and a scenario change that would drop one leaves it
  armed instead.
- **A scenario change counts as disarming** whenever it would leave an armed
  area disarmed — including an `arm` action, which is the same call and does
  the same thing when a scenario is already running. Both meet the switch and
  the perimeter constraint, so "arm Night" is not a way round either.
- **A rule never silences an alarm.** While an area it would disarm is in
  entry or already triggered, the rule is blocked and the log says so:
  disarming an area the incident touched acknowledges the incident and stops
  the escalation, and a phone walking through the door is not a person saying
  they have seen it. §4.6.1 already refused a scenario switch for the same
  reason.
- **An unreadable person is never read as an arrival or an absence.** A
  tracker that restarted or a phone off the network leaves the rule exactly as
  it was, which is INV-4 applied to people: a presence rule can disarm a
  house, and `unavailable` is not evidence of anybody.
- **Stopping the rules is an operation.** Cancelling a countdown, suspending
  and the kill switch all go through one entry in the code policy, which needs
  no code by default — a push carries none — and can be raised, and then they
  refuse where somebody can see it. The rules themselves are outside the
  policy: nobody is there to be asked, and the authorisation happened when
  somebody with `edit_config` saved the rule. `docs/automation-rules.md` says
  so plainly.

### Fixed
- The `exceptions` entries in `translations/` are mappings, as Home Assistant
  requires. Three of them were plain strings, which hassfest refuses and
  `async_get_exception_message` cannot read; the repository's own test now
  checks the shape rather than only the key set.

## [0.1.0-beta.7] — until somebody answers

Escalation: a notification that keeps looking for a person instead of firing
once and hoping. **The stored configuration moves to schema 6.1, a major
step**: a 5.x build reading it would find notifications that name contacts,
know nothing about contacts, and send nothing at all — so it refuses the file
instead. Upgrading migrates in one step and changes nothing an installation
already had: the address book starts empty, every notify action keeps the
service it names, and nothing escalates until somebody writes a step.

### Added
- **Contacts, with channels in order of priority** (panel page 6). A person
  rather than a service: push first, SMS next, a voice call after that. Every
  channel names a `notify.*` service, chosen from what this installation
  really has, with whatever that transport needs — Foyer orchestrates transports, it does not implement
  them.
- **Escalation steps.** A step is an ordinary notification with a time on it,
  added to the response profile that answers the alarm. At +0 s it reaches the
  first person, at +60 s the next channel, at +120 s somebody else; it stops
  the instant anybody acknowledges. An incident escalates with the policy of
  its highest-severity contributing profile, and the technical channel
  escalates on its own, which a disarm has no authority over.
- **Acknowledgement from all four paths of §7.2.** The service and the button
  already existed, and disarming an area the alarm touched already counted.
  New: a button inside an actionable push notification, which comes back
  through Home Assistant's own event, and a DTMF keypress fed back by a voice
  provider to a webhook. Every acknowledgement records who and through which
  channel — and when a push went to a contact who names no Foyer user, the row
  says the contact and the channel rather than inventing a person.
- **`escalation_exhausted`**, raised when the last step goes out with nobody
  having answered. It was the only moment left that no phase raised; a profile
  can act on it, and the panel's list of moments that nothing produces is now
  empty.
- **Quiet hours on a contact.** A window during which only what is loud enough
  gets through, on the log's own scale of info / warning / alarm and defaulting
  to alarm: a break-in reaches them at four in the morning and a successful
  arming does not. It never silences the alarm for the household, only for that
  contact.
- **A test button beside every contact channel** (§11.4). The other half of the
  one Phase 3 put beside every action: the same call the real notification
  makes, the same permission, the same code, and the same row in the log marked
  as a test.
- **The simulator's trace shows the escalation.** Which contacts a notification
  reached, who its quiet hours held back, and the steps still ahead with their
  timings — read off the decision the engine produced rather than worked out a
  second time for the display.
- **`escalation_skipped`**, a warning row and a notification naming the steps
  that did not go out and why — swallowed by a restart, or reaching a contact
  who is inside their quiet hours and nobody else. It is a record rather than
  a moment a profile can answer, and it exists because an escalation that
  quietly reached nobody is the silence this feature was built to end.
- **`docs/notification-channels.md`**: recipes for the Companion app with
  actionable notifications and iOS critical alerts, Pushover priority 2, Twilio
  SMS and voice with the DTMF gather, a USB GSM modem, Telegram and Signal —
  and what each is honestly worth when the fibre has been cut.

### Changed
- **`foyer.acknowledge` and `foyer.test_action` take new fields.** The first
  accepts `via` and `contact_id`, which are recorded and grant nothing; the
  second accepts `contact_id` and `channel_id` to test one channel of one
  contact. Existing calls behave exactly as before.
- **A notify action names contacts or a service, never both.** Both forms stay,
  for ever: nobody's configuration is rewritten, and page 6 is where a contact
  is made out of a service by hand.
- **A send to a contact's channel is retried once**, a few seconds later, for
  the transport that is not ready yet after a restart. The retry runs on its
  own, so the alarm does not wait for it, and after that the escalation
  carries on at its own times.
- **Escalation steps that fell due while Home Assistant was down are not
  sent.** They are recorded as skipped, with the gap that swallowed them and
  the steps it took, and the steps still ahead carry on at their own times: a
  notification four hours late is worse than none. A reload's second is not an
  outage, so the step it interrupted still goes out.

### Security
- **The DTMF webhook is an unauthenticated URL, and it does not exist until you
  switch it on.** Home Assistant webhooks are open to whoever holds the
  address, so anybody who has it — or intercepts it — can acknowledge an alarm
  in progress and stop the escalation on its way to the next person. It can do
  nothing else: not arm, not disarm, not read the log. The id is generated by
  the backend and switching the webhook off forgets it, so switching it on
  again hands out a new one. The threat is stated on the page, in the README's
  security model and in `docs/notification-channels.md`.

## [0.1.0-beta.6] — the banner, actually visible

Five defects in yesterday's release, four of them found by looking at the
walk test page rather than by reading it. No schema change and no migration.

### Fixed
- **The walk test banner had no CSS at all.** The element §11.3 calls a
  permanent, unmissable banner — the one standing between "every response is
  held back" and a household that has forgotten — rendered as bare black text
  flush against the left edge, with its icon orphaned above it and the end
  button wrapped underneath. It now has the warning colour behind it, full
  width, on every page, with what stays live said underneath in the same box.
  A safeguard that looks like an unstyled error page is a safeguard people
  learn to scroll past.
- **The walk test page repeated its own banner.** "Walk test running", the
  sentence about 24h, tamper, technical and panic zones staying live, and an
  End button, all twice, in the top third of one screen. The banner owns the
  warning and the ending; the page owns the instruction.
- **The missed-zone count had no singular.** It read `1 zone(s) have not
  reacted yet` in English — parentheses and all, on screen — and
  `1 zone non hanno ancora reagito` in Italian, in the red box that is the
  whole point of the page, and in the case that is commonest on a second walk.
- **The keypad card offered Disarm on a disarmed house.** The `keypad` layout
  rendered that button unconditionally, where `compact` and `full` both gate
  it on something being armed, so a wall tablet showed a button whose only
  possible outcome is `invalid_state`. The same layout also titled itself
  "Whole house" while a named scenario was running, where the full layout
  names the scenario — on the one surface where somebody stands and asks what
  the house is doing.
- **The event log's writer was asked to stop and never waited for.** On
  unload, `cancel()` only scheduled the cancellation, so the writer could
  still be running — and still holding the lock the flush on the next line
  wants — after the entry had finished unloading. Every configuration save
  reloads the entry, so this ran several times in an evening of setting a
  house up.

### Added
- **A screenshot of the walk test**, in both languages, on both front pages.
  The two keypad screenshots are recaptured with data belonging to one
  language at a time; the English one used to show "whole house" beside a
  scenario named "Notte".

Foyer is not a certified alarm system and is not a fire alarm system.

## [0.1.0-beta.5] — walk the house, and press the button before the night you need it

Phase 3, part two. The other half of the verification story: you can now find
out which zones never saw you without a siren sounding, and prove your
emergency notification works by pressing a button rather than by waiting for
an emergency.

### Added
- **The walk test** (panel page 9, *Test & diagnostics* → *Walk test*). Every
  area that can arm is armed for real and every sensor is read for real; what
  is held back is the response. Walk the house and the page fills in live with
  the zones that detected you — and, the point of the whole feature, lists
  first the ones that never did. A door nobody opened and a PIR pointing at
  the wrong wall look identical in that list, and only you can tell them
  apart; a dead battery shows up beside it.

  **`always_on` zones stay fully live.** 24h, tamper, technical and panic
  zones respond in full, alarm included. A walk test never silences a smoke
  detector, and that is the sentence the test suite is written against.

  A detection is recorded and moves nothing else: no `triggered`, no incident,
  no alarm memory, and `alarm_control_panel.foyer_master` never tells HomeKit,
  Google or Alexa that somebody has broken in. Forty zones walked would
  otherwise leave forty alarms in the log and alarm memory on every one.

  Leaving it disarms exactly the areas it armed, and never one that was
  already armed before it started — and never one that is in alarm or holds
  its memory. A disarm stops the sirens and acknowledges the incident, so the
  safeguard that keeps `always_on` zones live would otherwise switch off the
  alarm it had protected, fifteen minutes later, with nobody having seen it.
  The row says which areas were left armed and why.
- **The safeguards, none of them optional.** An automatic exit that cannot be
  switched off — fifteen minutes without a detection by default, each
  detection pushing it back so a large house can be walked in one pass, and an
  absolute cap that ends it whatever happens. A permanent banner in the panel
  and on **every** card layout, `badge` included, saying when it ends and what
  is still live. Entry and exit in the log with the person who started it. A
  notification on start and on end. The reason all four exist is the same: for
  as long as a walk test runs, a real intrusion produces nothing at all.
- **The real action test** (page 9 → *Action test*, and a *Test* button beside
  every action on page 5). It **really executes** — the siren really sounds,
  the notification really sends — because the failure it prevents is
  discovering during the emergency that the emergency channel was
  misconfigured. So it asks for explicit confirmation, requires the
  `test_actions` permission and a code, and leaves a row in the log marked as
  a **test** rather than as the alarm it imitates. A siren under test sounds
  for three seconds whatever its configured duration.
- **`foyer.walk_test` and `foyer.test_action`** are registered at last
  (decision 86 held them back until the phase that builds them). Both answer
  in the structured shape of §9.1, like every other service.
- **`switch.foyer_walk_test`** (§13), reflecting the timeout: `ends_at`,
  the two deadlines behind it, who started it and which zones have detected
  so far. Like `button.foyer_acknowledge`, it cannot carry a code, so it
  honours the policy and refuses visibly when an installation asks for one.
- **The walk test timeout is a setting** (page 11), bounded in code: there is
  no value that switches the auto-exit off.

### Changed
- **The wizard's test notification goes through the real action test.** It
  used to call the `notify` service straight from the browser, which tested
  the browser's session rather than Foyer's path and left no trace. It is now
  verified server-side and recorded as a test like every other one.
- **A blocked area does not stop a walk test.** It arms what it can, names the
  zones that kept an area out, and says plainly that those zones cannot have
  detected anything. A window left open must not stop somebody finding out
  that the garage PIR is dead.

### Permissions
- `foyer/walk_test` and `foyer.walk_test` need the `walk_test` permission and,
  by default, a code (§8.2). They are state-changing requests, so the engine
  resolves both, and the permission bites in full — administrator or not.
- `foyer/test_action` and `foyer.test_action` need `test_actions` and a code.
  They change no alarm state and press a button a Home Assistant
  administrator could press from Developer Tools anyway, so they are gated
  where the configuration commands are gated.

### Not in this release, on purpose
- **A test button beside every *contact channel*.** §11.4 asks for both; the
  contact book is Phase 4's, so that half arrives with page 6. What exists
  today is a test for every configured action, and a direct test of any
  `notify` service or entity — which is what the wizard now uses.

Configuration schema **5.4**, a minor step: the walk test's timeout is one
number in the settings, and the two moments the default profile gains announce
a walk test a 5.3 build cannot enter at all. Foyer is not a certified alarm
system and is not a fire alarm system.

## [0.1.0-beta.4] — ask what would happen, without anything happening

Phase 3, part one. The feature this project exists for: you can now rehearse a
configuration instead of trusting it, and read what every zone is actually
doing rather than what you meant it to do.

### Added
- **The simulator** (panel page 9, *Test & diagnostics* → *Simulator*). Pick a
  scenario, a date and time, and force zones into states at chosen seconds
  after the start; read back the whole decision chain. Which area changed
  state and which timer started, which verification group filled up and by how
  much, when an incident opened and when a second zone joined it, which
  profile answered and **where it was inherited from**, which actions ran, and
  which did not with the reason — a condition that was not met and which one,
  a siren already sounding, a zone that is silent, or a delay still holding the
  rest of the sequence.

  **Nothing is executed, structurally.** It calls the same `decide()` the
  running alarm calls, with a fabricated world and a fabricated clock, and
  never hands the result to the executor. A test asserts that the simulator
  and the runtime reach an identical decision from identical inputs; a test in
  Home Assistant registers a service and asserts nothing called it, because
  "no action was configured" and "nothing ran" look the same in a log.

  Every run is recorded under `system` with its inputs, so a configuration
  change can be justified afterwards. New command `foyer/simulate`.

  The arming the run uses as its premise goes through §8.2 like any other
  arming: if the installation asks for a code to arm, the simulator asks for
  one. §8.2 has no entry for a rehearsal, and an exemption invented here would
  be a second authorisation path — which is the one thing this feature exists
  to avoid.
- **Live zone diagnostics** (page 9 → *Diagnostics*). Every mapped zone with
  its backing entity, live state, **resolved trigger evaluation** — would Foyer
  count this as triggered right now, read through that zone's own trigger —
  last state change, availability, battery, radio quality where the entity
  exposes one, supervision window, and whether it blocks arming and for which
  of the two reasons. Entities a zone or a device names that Home Assistant
  does not have are listed separately: a renamed entity is the commonest
  silent failure there is. Arming devices get a table of their own below the
  zones. New command `foyer/diagnostics`.
- **A zone can name the entity that reports its battery**, and the
  `low_battery` moment is raised. What counts as low is one setting for the
  installation, 20 % by default (page 11); a battery `binary_sensor` is read
  by Home Assistant's own convention, where `on` means low.
- **Every arming attempt says which zones are on a low battery**, on every
  channel — the panel, the card and the structured result a service call or a
  keypad gets back. The panel offers to exclude them from that arming in one
  press, which is an ordinary manual exclusion and ends when you disarm.
- **`docs/simulator.md`**: how to read a decision trace, and what is worth
  rehearsing before trusting a configuration.

### Changed
- **A low battery warns and never blocks arming, and is not a fault.** A
  contact reporting 15 % is still seeing the door, and a house of forty
  battery zones that cannot be armed the morning one of them dips is an alarm
  that gets switched off.
- **A battery entity that cannot be read *is* a fault and blocks**, like any
  other unreadable entity (INV-4). A battery sensor that has gone silent is a
  radio that has gone silent, and the contact beside it is the next thing to
  stop reporting. Only zones that name a battery entity are affected; nothing
  else changes for an installation that names none.

### Fixed
- **The "ready to arm" reading could disagree with arming itself.** The read
  model behind `binary_sensor.foyer_ready_to_arm`, the panel's per-area
  *ready* flag and page 9's *blocks arming* column trusted the stored set of
  active zones, while a real decision refreshes every zone's trigger from the
  world before deciding anything. Between an entity changing and the decision
  it causes, the two could differ — the reading said ready, the arming
  refused. Both now read the world through the same function.

### Permissions
- `foyer/diagnostics` and `foyer/simulate` only read, and are gated as reads:
  `view_log`, and no code. §8.2 asks for a code to *edit* the configuration,
  and demanding one to open a page teaches a household to keep the code on a
  sticky note beside the tablet. What these two reveal is what the log
  reveals.

### Not in this release, on purpose
- **The walk test and the real action test**, with their tabs on page 9.
  `foyer.walk_test` and `foyer.test_action` stay unregistered rather than
  registered and silent (decision 86).

Configuration schema **5.3**, a minor step: a zone's battery entity and the
threshold it is read against are additive, and a 5.2 build ignoring both never
warns about a battery — which is exactly what it did yesterday. Foyer is not a
certified alarm system and is not a fire alarm system.

## [0.1.0-beta.3] — the picture, and the page you were on

Three defects found by using it rather than by reading it, and one of them
has been in every release since cameras landed.

### Fixed
- **The camera folder was created unusable.** `os.makedirs` takes `exist_ok`
  as its third argument and was being given `True` as its *second* — the
  mode — so the folder came out as `0o001`: no read, no write, for anybody.
  Every snapshot into a newly created folder failed, at the moment of the
  alarm. No test had ever run the camera action; one does now, and it
  asserts the folder can be written to. If you have a broken `media/foyer`
  from an earlier release, delete it and Foyer will make it properly.
- **Saving anything in the panel sent you back to the dashboard.** Every
  accepted edit reloads the integration, a reload unloads it first, and
  unloading removed the sidebar panel — so for that moment the page you were
  standing on did not exist, and Home Assistant did what it does with a page
  that does not exist. The panel is now registered once per Home Assistant
  run and removed when the integration is removed.
- **The card's keypad had no key to press.** It collected digits and left you
  there: the design assumed you would press the action button again, and said
  so nowhere. The pad now grows a confirm key while a command is waiting for
  a code, and it repeats that exact command. The key is labelled with what it
  will do — *Arm*, *Disarm*, *Exclude*, *Arm anyway (forced)* — which also
  answers the question it used to raise, because "a code is required" with no
  object reads as though arming wanted one. Arming does not. Forcing past an
  open zone does, and so does excluding a zone; both lower the guard (§8.2).

### Changed
- **A notification says which app its camera picture is for.** The Companion
  app reads `image` and is happy with a link to the authenticated camera
  proxy, with no file written. Telegram reads `photo` and needs a file,
  because its own server fetches the picture from outside the house with no
  session and cannot follow that link. Foyer asks rather than guessing from
  the service name — a bot may be called anything, and every transport
  discards a key it does not know in silence, so a guess that fails fails
  invisibly. Existing notify actions keep the Companion behaviour.

  For the file transports the snapshot is taken at the moment of the
  notification, and the message goes without the picture if the camera does
  not answer. The camera folder must be in `allowlist_external_dirs`.

### Specification
- **Decision 90**, and §6.2 now states the attachment rule in both
  directions instead of describing only the proxy link.

Configuration schema unchanged (5.2). Foyer is not a certified alarm system
and is not a fire alarm system.

## [0.1.0-beta.2] — what the log knows, and what it only heard

A small release, and two of the three entries change a contract published
yesterday. If you have already written an MQTT adapter against `0.1.0-beta.1`,
read the first one.

### Changed
- **The MQTT answer is two fields** (SPEC §9.2). `last_result` goes back to the
  four words the specification always had — `ok`, `blocked`, `bad_code`,
  `locked_out` — and stays those four for ever, so an adapter written today
  never meets a word it does not recognise. The precise reason moves to a new
  field beside it, `last_reason` (`zone_open`, `device_not_registered`,
  `user_not_valid`, …), `null` when the command succeeded. Beta 1 published
  `unknown_device` inside `last_result`; it is now `last_result: "blocked"`
  with `last_reason: "device_not_registered"`. A keypad that goes quiet exactly
  when something new happens is worse than one that says "blocked".
- **A name nothing established is marked as such in the log.** A service call
  may pass `user_id`, and arming needs no code, so a caller could write a name
  into the log that nothing verified. The row keeps the name — attribution is
  worth having — and now carries `attributed: claimed`, shown beside it on the
  log page. A code or a tag still produces an unmarked row. A wrong answer to
  "who disarmed at 03:14?" is worse than no answer.
- **The blueprints import with one button.** Each adapter in `docs/keypads.md`
  carries a Home Assistant import link, because HACS installs the integration
  and not blueprints, and "copy the file into the right folder" is the step at
  which people stop. Copying by hand still works and is documented beside it.

### Fixed
- **Saving anything on the Settings page reset the code length and the lockout
  numbers** to their defaults. Present since codes landed in `0.1.0-alpha.13`:
  if you had set a code length other than six and then touched Settings, the
  card and the keypad went back to collecting six digits — and a code that
  never validates is five wrong attempts away from a lockout. Check
  *Users & codes* if this is you. Found in review, with a regression test.
- **A misconfigured device could bury the security log.** An undeclared device
  wrote a row on every message; it now writes one, then at most one a minute
  per device. The notification was already one per device.
- **MQTT published a retained message on every motion a detector reported**,
  usually saying exactly what it already said. It now publishes when the
  message would differ, and always in answer to a command.
- **A broker that did not answer could hold up Foyer's own start.** The
  subscription is started beside the setup now, never inside it: the alarm
  loads whether or not the broker is there.
- **`foyer.export_log` asked for a code**, while the panel's own log page does
  not. Reading the log asks for the `view_log` permission and nothing else —
  you must still say who you are, since a service call carries no signed-in
  account.
- The warning on the arming devices page — *a stolen tag arms and disarms
  without knowing any code* — was rendering as ordinary paragraph text, directly
  above the field where you choose whose tag it is. It is an amber banner now,
  like every other warning in the panel.
- The shipped keypad blueprints resent their feedback when only an attribute of
  the panel entity had changed, waking a battery keypad for nothing.

### Specification
- **P-1, a stated principle**: outward, every channel starts at the least that
  works, and anything that adds the state of the house is an explicit option.
  The watchdog's empty heartbeat and the MQTT message's `minimal` default had
  reached that conclusion separately, and §9.2 had first reached the opposite
  one. Written once, so Phase 4's transports meet it already made.
- **A tag must name a person**, now stated with the alternative that was
  considered and refused: a household wanting a remote that belongs to the
  house creates a user named for the house, and has then said so.

## [0.1.0-beta.1] — the keypad by the door

**The first beta, and the first release that is not a pre-release.** Phase 2 is
complete: the house can be armed and disarmed from physical hardware, and the
log says who did it, from where, and on which device.

**Configuration schema 5.1 → 5.2, a minor step.** Arming devices and the MQTT
settings are additive, and a 5.1 build reading this document simply has no
physical channels — which is what it had. Nothing it protected goes
unprotected, so a downgrade is safe.

### Added
- **The `foyer.*` service contract** (SPEC §9.1): `arm`, `disarm`,
  `bypass_zone`, `unbypass_zone`, `acknowledge`, `export_log`, `export_config`,
  `import_config`. Every state-changing service takes a code, a user, a channel
  and a device and returns the structured result — success, reason, the zones
  that blocked it by name, and the whole live state — so an adapter can tell a
  wrong code from arming blocked by an open window. One function builds that
  answer for the services, the WebSocket commands and MQTT alike.
- **The MQTT contract, in both directions** (§9.2), with configurable topics,
  off until you switch it on. A keypad publishes a command and reads the
  retained state back for its LEDs, beeps and countdown.
- **Arming devices, panel page 8**: keypads, NFC tags and remotes, declared
  before they may command anything, with the MQTT settings and a preview of the
  message Foyer will actually publish.
- **Tags and remotes, natively.** A `tag.*` or `event.*` entity, the person it
  belongs to and what a scan does. No automation needed, and the log names the
  person — which is the whole reason a tag counts as a channel that identifies.
- **Three blueprints**: Ring Alarm Keypad v2 over Z-Wave JS with the LED ring
  and the exit and entry countdowns, a generic Zigbee keypad over Zigbee2MQTT,
  and tags and remotes for the cases the native path deliberately will not
  cover. Plus `docs/keypads.md`: what each piece of hardware is honestly worth,
  the full contract, and how to write your own adapter.
- **Card layout `badge`**: colour-coded state only, for embedding in a
  dashboard of your own. Nothing to press, so a stray tap cannot disarm a
  house; it still shows a running countdown and an alarm in memory.
- **`skip_exit_delay`**, for the last person out who is already outside. No
  permission of its own — whoever may arm may arm at once — and recorded on the
  `armed` row, because it turns every delayed zone into an instant one.

### Changed
- **A device must be declared before it may command.** This is the one
  behavioural change to read twice: an unknown `device_id` is refused whatever
  code it brings, recorded under `security`, and raised as a notification. The
  reason is the lockout — it counts per channel *and* per device, so a caller
  free to invent a device id is a caller who is never locked out. Nothing
  existing breaks: before this release there was no channel that sent one.
- **The retained MQTT message says the least by default.** It sits on a broker
  that is often shared, and whatever is in it is told to whoever connects next.
  Three levels: `minimal` (no names at all), `standard` (scenario and areas),
  `full` (the contract as specified, open zones by name).
- **The channel is the device's, not the message's.** A caller may declare
  itself `api` or `automation`; `keypad` and `nfc` come from the device
  register, or the request is refused. Otherwise an automation could buy the
  per-user code exemption by typing a word.
- **Releases stop being pre-releases from here.** HACS only offers releases
  that are not pre-releases, and shows a commit hash for a repository that has
  none. The per-repository "show beta versions" switch is no longer needed.

### Fixed
- A tag's entity was not being watched, so a scan arrived only after a restart.
  Found by writing the acceptance test rather than by reasoning about it.

### Not built
- `foyer.walk_test` and `foyer.test_action` are listed in §14.1 and are
  registered by Phase 3, which builds them. A service that exists and does
  nothing answers its caller with silence, and silence is the answer that gets
  mistaken for success.

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
