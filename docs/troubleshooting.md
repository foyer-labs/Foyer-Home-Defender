# Troubleshooting

**English** · [Italiano](troubleshooting.it.md)

This page is for the household that set Foyer up and has met something it did
not expect: a zone that stays silent, an alarm nobody caused, an arming or an
edit refused, a notification that never arrived. Each entry says what the
software does, why, and the way past it. It is built from the changelog, from
the decisions in the [specification](SPEC.md) that were born of real problems,
and from the refusals the code actually returns — not from field reports.

The log page answers most of these questions before this page does. Every
refusal is a row of its own, with its reason and the zones behind it, because
"why did it not arm last night?" is a question people ask.

---

## A zone never triggers

Start with the zone's **trigger**: the states in which Foyer counts it as
triggered, confirmed by you in the zone editor under *When is this zone
triggered?*. Foyer never assumes that `on` means alarm. A normally-closed
magnetic contact reads `off` when the door is open, a normally-open one reads
`on`, and a lock reads `unlocked`; a zone whose trigger names the wrong state
never fires, and nothing about it looks wrong until the night it matters. Open
*Test & diagnostics*, open the door or walk past, press *Refresh* while the
sensor is still triggered — the table is a snapshot and does not update by
itself — and read the *Trigger evaluation* column
([how to read it](simulator.md#diagnostics-am-i-looking-at-the-right-sensor)).
If it says *Would not* while the door is open, the trigger is wrong: correct
the states on the *Zones* page and tick *I have checked this against the real
sensor* again. The zone editor does not change the entity of an existing
zone: to watch another entity, create the zone again, and confirm its trigger
then.

If the trigger is right, work down this list.

- **The entity was renamed.** A zone points at an entity id. When Home
  Assistant no longer has it, *Test & diagnostics* lists the entity above the
  table, its row reads *No such entity*, and the zone is in fault — *Fault:
  not reachable* — which blocks arming its area. Foyer does not follow a
  rename: give the entity its old id back in Home Assistant, or delete the
  zone and create it again on the new id. If the zone has *Allow arming while in fault*
  ticked, the area arms anyway, and that zone watches nothing.
- **The zone is switched off.** *A disabled zone is ignored completely*: the
  table shows it as *Disabled*. Zones brought in by the importer on the
  *Settings* page arrive switched off, marked *Trigger to confirm* on the
  *Zones* page, because their trigger is a proposal read from the sensor's
  type rather than something anybody checked; they cannot be switched on
  until the trigger is confirmed. See
  [migrating an existing configuration](migrating-from-alarmo.md).
- **Its area is not watching it.** An intrusion zone alarms only while its own
  area is armed. A disarmed area — one left out of the running scenario and
  not armed on its own included — and an area still counting down its exit
  delay are not monitoring their zones; there, a zone opening can only chime. Only zones
  with *Always on (24h)* ticked — 24h, tamper and panic zones by default — and
  technical zones answer whatever the area is doing.
- **It was already open.** A zone that is triggered when its area arms does
  not fire until it closes and opens again: with *If open when arming* set to
  *Ignore*, "it fires the next time it opens". The same is true of the first
  reading of a new zone, which is its baseline rather than an event — a zone
  saved while its door is open, or a detector saved while it is detecting,
  alarms only once it has returned to normal and triggered again.
- **It is excluded.** An excluded zone does not alarm. *Excluded by hand*
  without a duration lasts until the area is disarmed; with a duration it
  outlives the disarm and is included again when its time is up. Closing the
  zone never ends a manual exclusion — *Include again* does. Zones excluded
  at arming or by a forced arming are watched again as soon as they close.
- **It needs more than one activation.** *Activations needed* above 1 means
  the zone does nothing until it has triggered that many times within its
  window, and a PIR held `on` counts once. Only activations that would alarm
  at once are counted: a delayed zone's first opening still starts its entry
  delay. A verification group with *Members produce nothing below the
  threshold* holds a member back too, until enough members to reach the
  threshold detect within the window.
- **It is an event or a tag.** An `event` entity needs its *Event type* — the
  button that counts — and fires only on a new event of that type; a `tag`
  fires on every scan and takes no type. The table shows *On scan only* for
  both, because a momentary zone is never "open". An entity coming back from
  `unavailable` at a restart is Home Assistant restoring its last event, and
  does not fire.
- **The sensor stopped reporting and nobody noticed.** With *Silence limit*
  empty — the default — a sensor that stops reporting without its integration
  marking it unavailable keeps showing its last state, and Foyer cannot tell
  "closed" from "gone". Set the limit on each sensor that reports on a
  schedule, longer than its own reporting interval; past it, the zone is in
  fault (*Fault: silent too long*). Leave it off for sensors that report only
  when they change.

To see whether a zone moves at all while the house is disarmed, switch on the
*Zone activity (disarmed)* log category in *Settings* for as long as you are
looking, then off again: a motion sensor fills it with thousands of rows a
day. The [simulator](simulator.md) rehearses what the engine does with a
zone; the walk test on the same page proves the sensor sees you.

---

## False alarms

Read the incident on the log page first: every zone that joined it, in the
order it joined, under one incident id. Then:

- **One sensor is not enough evidence.** *Activations needed* on the zone
  makes it wait for several activations within a window. A verification group
  on the *Verification groups* page confirms an alarm when a set number of its
  members detect within a window; by default each member still alarms on its
  own and the group adds its confirmation, so the graduated answer comes from
  giving the members a quieter response profile than the group's. With
  *Members produce nothing below the threshold*, a lone member does nothing
  while enough other members are readable and watched — including a real
  intruder seen by only one of several working sensors, which is why it is
  off by default. When too few members are left able to count, a lone member
  alarms on its own. *Cross-zone verification* on a zone is the same engine
  as a group of two: it records the confirmation and silences neither zone.
  Only activations that would alarm at once count, so coming home through the
  entry delay never satisfies a group.
- **The hall sensor alarmed as you came in.** A *Follower* zone inherits the
  entry delay only if one is running: its own area's, or one opened by a
  delayed zone it is told to follow under *Also follows*. When the front door
  and the hall sensor sit in different areas, tick the front door there. Its
  own area must be disarmed as well, or that area's inherited delay runs out
  into an alarm. Rehearse the route in the simulator before relying on it.
- **The entry delay is too short.** A zone's *Entry delay* left empty
  inherits the area's default, 30 seconds unless changed, at most 300. A
  delayed zone whose delay is 0 fires at once.
- **Somebody armed with no exit delay.** `skip_exit_delay` on `foyer.arm` arms
  at once. Whoever is still inside then meets armed zones straight away: the
  front door starts its entry delay, and an instant sensor in the hall alarms.
  The *Armed* row records that the exit delay was skipped.
- **A zone was switched back on while it was triggered.** Only a new zone's
  first reading is a baseline (and a key zone's, when it is switched back
  on). A zone that was in use, switched off and
  switched on again while detecting counts as triggering at that moment — for
  a 24h, tamper, panic or technical zone, that is an alarm.
- **A battery was changed in a tamper-protected sensor.** Opening its case
  trips its tamper switch, and a *Tamper* zone alarms whatever the house is
  doing, disarmed included. Switch that zone off on the *Zones* page, with its
  area disarmed, for as long as the case is open, and switch it on again
  afterwards.
- **Foyer restarted.** A zone that was closed when Foyer stopped and is open
  when it comes back has opened, as far as the engine can know. The log's
  *Foyer was not running* row says from when to when the house was not
  watched.
- **An alarm with no zone in it.** Radio interference confirmed on an armed
  house opens an incident with no zone, because no zone did it — the radio did.
  [System health](system-health.md#radio-interference) explains what it
  counts and the four ordinary events that look exactly like it.

---

## Faults: a zone that cannot be read

A zone is in fault when its entity is `unavailable` or `unknown` or missing,
when a numeric trigger reads something that is not a number, when it has been
silent past its *Silence limit*, or when its battery entity cannot be read.
An `event` or `tag` entity reading `unknown` has simply never fired, and is
not a fault; `unavailable` still is. A fault is never "all quiet": it blocks arming the zone's area, it is
announced as *Zone fault*, and *Test & diagnostics* shows *Blocks: fault*.
When the zone's own entity has been unavailable or unknown for two days (by
default), it also becomes a Home Assistant repair issue; a silence-limit fault,
a reading that is not a number, an unreadable battery entity or a zone already
unreadable when Foyer started does not raise one.

- **Allow arming while in fault**, on the zone, lets its area arm regardless.
  Leave it off unless you know why: that zone then watches nothing while the
  house believes it is armed. It exists for the flood sensor with a dead
  battery on the morning you leave.
- **Arm without these zones**, on the *Overview* or the card, arms and excludes
  the faulted zones for this arming. It is a forced arming: it needs the
  `force_arm` permission, which a person added on the *Users* page does not
  start with, a code by default, and every zone it excludes must be *May be
  excluded*. It is logged as a forced arming.
- **Batteries.** A zone's battery entity is read two ways, on purpose. A low
  battery — below *Low battery below*, 20 % by default, or a battery
  `binary_sensor` that is `on` — warns and never blocks: the arming goes ahead
  and says which zones went under guard on a dying cell. A battery entity that
  cannot be read at all is a fault and blocks, because a battery sensor gone
  silent is a radio gone silent.

Many zones on one radio going unavailable together is a radio event rather
than many faults: [System health](system-health.md#radio-interference).

---

## Arming refused

Every refusal names its reason, and the ones about zones name the zones. The
texts below are the panel's; Home Assistant's own dialogs and a service call
show the same reason in their own words.

| What you see | What it means | The way past |
|---|---|---|
| *Not armed — still open: …* | A zone whose *If open when arming* is *Block arming* is open | Close it; or exclude it first; or *Arm without these zones*. *Exclude automatically* and *Ignore* never refuse; *Arm after closing* waits |
| *Arming failed: zone still open: …* | An *Arm after closing* zone stayed open past *Wait for it to close, at most* (300 s by default) after the exit delay | Close it sooner, or raise the limit |
| *Not armed — not responding: …* | A zone in fault | See [Faults](#faults-a-zone-that-cannot-be-read) |
| *Cannot force arming: these zones may not be excluded: …* | A forced arming met a zone that is not *May be excluded* | Close or repair it |
| *A code is required.* | The code policy, an area or a scenario asks for one; or the scenario has a *Who may use it* list and the request established nobody — a codeless arming, or a `user_id` merely claimed — which is refused while codes are in force even where arming asks no code | Type it: the panel and the card ask by themselves. From Home Assistant's own cards, see below |
| *That code is not right.* | The code matched nobody | Retype it; every wrong code counts towards the lockout |
| *Too many wrong codes…* | Locked out, see below | Wait, or use another channel |
| *Your Foyer user does not have permission for this.* | The person lacks the permission (arming, forced arming, changing scenario…) | Tick it on the *Users* page |
| *That code belongs to a user who is disabled or outside their validity period.* | A guest code past its date, or a person switched off | The *Users* page |
| *You are not allowed to act on that area.* / *…use that scenario.* | The person's areas or scenarios, or the scenario's *Who may use it*, leave them out | The *Users* or *Scenarios* page |
| *A walk test is running. End it first, then arm…* | Arming is refused while a walk test runs: its end disarms the areas it armed, and would undo yours | *End walk test*, which asks for a code by default, then arm. Its end disarms the areas the test armed, except one in alarm or left holding alarm memory by a 24h or tamper zone during the test, which only a person's disarm ends, and leaves every other area as it found it |
| *An alarm is in progress. Disarm before changing scenario.* | Switching scenario while an area it would touch is in its entry delay or in alarm | Disarm first: changing scenario never silences an alarm |
| *More than one scenario is linked to this arming mode…* | Two scenarios share one mode, so *Whole house* cannot tell which is meant | Arm the scenario itself, from the panel, the card or `select.foyer_scenario`. The *Scenarios* page says *Shared with another scenario* |
| *The area's current state does not allow this…* | Already armed, arming or in alarm — or that scenario is already running with nothing left to arm | Nothing to do |
| *That device is not one of this system's arming devices…* | A `device_id` not declared on *Arming devices* | Declare it, see below |
| *Foyer was reloading, so nothing was done. Try again.* | Every configuration save reloads Foyer; the request arrived in between | Try again |

**Locked out.** After five wrong codes within 300 seconds, codes from that
channel are refused for 300 seconds; each further lockout doubles, up to an
hour — or up to the configured length, if that is longer — and the doubling
starts again after a day without one. All three
numbers are on the *Users* page. A correct code ends the run of failures but
not a lockout already running. What is locked is narrow: the panel, the card
and Home Assistant's own alarm panels share one counter **per Home Assistant
account**, so one account guessing locks itself out and nobody else; `foyer.*`
service calls keep a counter of their own per account, and calls with no user
behind them, such as automations, share one; a keypad counts per device; the
device endpoint counts a missing or wrong token per source address, and a
device with its right token is never refused for its address. A Home
Assistant **administrator is never locked out of the panel, the card, Home
Assistant's own alarm panels or the `foyer.*` services called from their
account** — the attempts are counted and logged, and the account stays open —
so nobody can shut themselves out of their own house. The card says
until when; the panel says *Codes from this account are blocked until …*.

**Home Assistant's own cards refuse a codeless arming.** Home Assistant asks
Foyer one question for everybody — does arming need a code? — and acts on it
before Foyer sees who is asking. Foyer answers yes while the policy asks for
a code to arm and nobody could use *Skip the code where this person is
identified* — it counts only for an enabled person, linked to a Home Assistant
account and inside their validity window; *Whole house* answers yes as soon as one mode it can still arm
asks for one. Then Home Assistant's dialog and tile buttons ask for the code,
and a mode that needs none is refused by Home Assistant until a code is typed —
from an automation too, which arms it through `foyer.arm` instead. When
somebody can use the exemption, those buttons stop asking, and a person Foyer does want a
code from is refused with *A code is required to arm*, and told where it can
be typed: Foyer's card, the Foyer panel, or Home Assistant's *Alarm panel*
card while the panel is disarmed, which is the only time that card offers
arming. The [FAQ](faq.md) covers Home Assistant's cards and voice assistants
in full.

**An unknown device.** Every keypad, tag and remote is declared on *Arming
devices* before it may command anything, and a `device_id` the installation
does not carry is refused whatever code it brings — otherwise a caller could
invent a new device name for every guess and never reach the lockout. The
refusal leaves a *Device refused* row under *Security* and a Home Assistant
notification, *Foyer: unknown device*. A keypad declared on the device
endpoint answers only there: its name over MQTT or in a service call is
refused the same way, and the notification says the name was used on the
wrong path. See [keypads](keypads.md).

**"Why did it not arm last night?"** Filter the log by that night:

- *Arming refused* under *Arming*, with the reason and the zones, when the
  request was refused as it was made;
- *Arming failed*, when an accepted arming met a zone still open or in fault
  as its exit delay ended; whenever an automatic rule's arming was refused for
  any reason other than the house already being armed that way, with the
  rule's name; and when a tag or a key zone failed to arm;
- *Code rejected* under *Security*, when the refusal was about who was asking —
  a wrong code, a lockout, a permission or an area — with the reason in the
  row's detail. Its outcome reads *Wrong code* only when a code was typed and
  was wrong; a code that was needed and not given, a permission, a validity
  window, an area or a scenario reads *Refused*;
- *Automatic action held back* under *System*, when an automatic rule was
  stopped by one of its safety checks, a suspension or the kill switch. See
  [automation rules](automation-rules.md).

---

## Edits refused while the house is armed

While any area is not disarmed, the house keeps what it was armed with. An
edit that would change how it answers an alarm, or what it asks a code for,
is refused and names what it touched:

- the armed areas, their zones and verification groups, and the scenario that
  is running;
- the siren duration, *Wait for it to close, at most*, the default entry and
  exit delays and the walk test timeout;
- the default and technical profiles, the silent list and the camera folder;
- every response profile an armed area could answer with, and every contact
  such a profile names, which can be neither changed, switched off nor
  deleted;
- the code policy, the code length and the lockout, and what any area or
  scenario asks a code for — a disarmed area and a scenario that is not
  running included, because they take part in commands that touch the armed
  area;
- *Allow rules to disarm*, and the radios and thresholds on *System health*.

Otherwise whoever holds `edit_config` could lower the guard of a house nobody
disarmed, and nothing in the log would read as a disarm. A restore is refused
exactly where the same change made on its own page would be.

What stays free: people, their codes, permissions and exemption, tags,
keypads and their tokens, API devices, MQTT, the acknowledgement webhook and
the automatic rules — taking a guest's code away from the other side of the
world is the edit an armed house needs most — and the language, the log, the
chime, the battery threshold, the backup download, the mains, the watchdog
and the channel checks. A disarmed area can be programmed while others stay
armed, except what it asks a code for.

One edit among the free ones is refused: *An area is armed, and this would
leave nobody with a usable code…* With no usable code the policy switches
itself off, which would lower the guard by another route. Give somebody else
a code first, or disarm.

---

## Codes

**Nobody is asked for a code.** While no enabled person holds a code inside
their validity window, the code policy is inert: nothing could be verified,
so enforcing it would only make the alarm impossible to disarm. The
*Overview* says so — anyone with access to Home Assistant can disarm — and so
does the *Users* page. It lasts until the first person with a code is saved,
and it comes back if the only person holding one is disabled or runs past
their validity window.

**An administrator is asked for a code.** Being a Home Assistant
administrator identifies nobody: the unlocked wall tablet is almost always
signed in as one. So the panel asks an administrator for the code wherever
the policy asks, a configuration save included. What an administrator keeps
is that wrong codes never lock them out of the panel, the card, Home
Assistant's own alarm panels or the `foyer.*` services. An administrator who holds no code, in a
house where others do, or whose own Foyer user was disabled or ran out,
recovers access from **Settings → Devices & services → Foyer Home Defender →
Configure**: it enables that account's Foyer user, removes its validity
window and sets a new code, or creates a user with every permission. It is
never quiet: a row in the log, a Home Assistant notification and a message to
every enabled contact, each naming the account. The [FAQ](faq.md) and the
[security model](security-model.md) say why it exists and what it does not
change.

**A new code is refused as already in use.** Codes are unique across people,
duress codes included, so the log can say who acted. The refusal never says
whose code it is, and it **counts as a wrong code** against your account's
lockout — otherwise saving a person would be a way of testing codes against
the household without limit. Offering one of a person's two stored codes as
their other one — the duress code as the new ordinary code, say — is refused
and counted the same way.

**Asked again for a code you typed a moment ago.** The panel forgets a code two
minutes after its last use, at every arming or disarming, and when it closes;
the card keeps none beyond the command it was typed for.

---

## Notifications that do not arrive

- **Press the test button first.** *Test this channel* on the *Contacts* page
  sends through the stored channel, as an alarm would. A test that fails, or
  never arrives, is the answer, found before the night it matters.
- **Read the channel on System health.** *Healthy*, *Never used*, *Service
  missing* or *Sends failing*. A channel nothing has sent over yet is *Never
  used*, not healthy: only a send proves it delivers. See
  [notification channel health](system-health.md#notification-channel-health).
- **Check that something sends it.** A new installation's default profile
  answers with a Home Assistant notification and nothing else. A message to a
  phone, and every escalation step, is a notify action added to a response
  profile for the moments you want; the wizard's test notification adds none.
- **A notify entity is not a notify service.** An entity takes a title and a
  message and drops everything else — the acknowledge button, a critical
  alert, a picture. See
  [notification channels](notification-channels.md#a-notify-entity-is-not-a-notify-service).
- **Pictures.** The notification's *How to attach it* names the transport: the
  Companion app fetches a live link through Home Assistant's camera proxy;
  Telegram needs a file, written to the *Camera folder* (`media/foyer` by
  default, never `www`), which must be in `allowlist_external_dirs` or nothing
  is written. With *The cameras of the zones behind the alarm*, pictures go
  only at an alarm, never when an entry delay starts, and to a contact only
  over a push or chat channel; *Always the same camera* attaches its one picture to the
  notification itself, at whatever moment the action runs. A camera that does not answer costs
  its own picture, never the text.
- **Quiet hours.** Inside a contact's *Quiet hours*, only what reaches
  *Minimum severity to get through* gets through. The simulator's trace says
  when every contact a notification names was held back this way.

---

## The card is missing from the picker, or "Custom element doesn't exist"

Reload the page once with Ctrl+Shift+R (Cmd+Shift+R on a Mac). Home Assistant
writes a card's script tag into the page it renders, so a page loaded before
Foyer was installed — or before it was updated — does not have it, and
reconnecting after a restart does not fetch a new one. In the companion app,
reset the frontend cache from its settings, or close and reopen the app. To
check that the file itself is there, open
`https://<your-home-assistant>/foyer_static/foyer-card.js`: it should show
JavaScript. No dashboard resource needs adding. [The card](card.md) describes
the rest.

## HACS showed a commit instead of a version

Up to `0.1.0-alpha.13` every version was published as a GitHub pre-release,
and HACS offers only releases that are not pre-releases: for a repository with
none, it falls back to the default branch and shows the commit. Since
`0.1.0-beta.1` versions are published normally, so HACS sees them, shows them
by name and offers updates by itself. If you switched on the *pre-release*
switch entity HACS creates for this repository, you can switch it off.

## The sidebar shows a plain shield

On purpose: `mdi:shield-home`, because Home Assistant resolves a custom icon
once and never retries, and the companion app starting from a cached page
would keep an empty square for ever. The Foyer shield is in the panel's
header; see [brand](brand.md).

---

## Opening an issue that can be answered

Open an [issue](https://github.com/foyer-labs/Foyer-Home-Defender/issues/new/choose);
the form asks for what follows and says where to find each part:

- **which version** of Foyer (in HACS) and of Home Assistant (*Settings →
  About*);
- **what you expected**, and what happened instead;
- **what the log page shows** around that moment. The row usually carries the
  answer — a refusal holds its reason and the zones behind it — so a
  screenshot of it is worth more than a description. For a zone that never
  triggers, add its row on *Test & diagnostics*;
- **Download diagnostics**, from *Settings → Devices & services → Foyer Home
  Defender → ⋮*. It usually turns five questions into one answer. It carries
  the shape of the installation and nothing about the people in it: no names
  of people, areas or zones, no codes or hashes, no watchdog URL, webhook id
  or keypad token, no phone numbers, chat ids, message text or MQTT topics,
  and real entity ids replaced by stable placeholders such as
  `binary_sensor.zone_3`. It carries no log rows and no trigger states,
  which is why the two screenshots above still matter. If the button is
  missing because Foyer did not load, say so: that is the most important fact
  in the report.

English or Italian, whichever you prefer.

A way past a code, a way to keep the alarm quiet, a way to read a credential
or somebody's log is a vulnerability, not an issue:
[SECURITY.md](../SECURITY.md) says how to report it privately.
