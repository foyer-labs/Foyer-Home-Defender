<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><strong>English</strong> · <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.it.md">Italiano</a></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center"><em>An alarm panel for the sensors you already have. Areas with a state each, arming scenarios you define yourself, zones that say what "triggered" means for them — and a simulator that tells you what would happen, before you find out the hard way.</em></p>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?sort=semver&include_prereleases&label=version" alt="Latest version"></a>
  <img src="https://img.shields.io/badge/status-beta-yellow" alt="Beta">
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant 2025.1 or later">
  <img src="https://img.shields.io/badge/HACS-custom%20repository-41BDF5" alt="HACS custom repository">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licence-Apache--2.0-blue" alt="Apache-2.0"></a>
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml"><img src="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
</p>

> ### Status: beta. It works, it guards the author's house, and you can ask it what it would do before you trust it.
>
> Three things answer that question for you. The **simulator** rehearses a
> decision with nothing actually happening. The **walk test** arms the house
> for real, holds every response back, and tells you which zones never saw you
> walk past them. The **action test** really does sound the siren, so a
> misconfigured emergency channel is something you find out on a Tuesday
> afternoon rather than at three in the morning. (A walk test never silences a
> smoke detector: 24h, tamper, technical and panic zones stay fully live.)
>
> The rest — codes and users, keypads and tags, escalation until somebody
> answers, and the house arming itself when everybody leaves — is in the
> [changelog](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CHANGELOG.md).

**Try it if** you already have door, window or motion sensors in Home
Assistant, you want one panel with arming scenarios of your own instead of a
folder of automations, you would rather check a configuration than hope it is
right, and you are willing to run a beta on a house that has other locks on it.

**Not yet, if** you want something that has been shaken out on thousands of
houses rather than a few — [Alarmo](https://github.com/nielsfaber/alarmo) has
years of use behind it, and for an installation that simply has to work today
it is the prudent choice.

**What it needs:** Home Assistant 2025.1, one sensor that already works, and a
`notify.*` service. No cloud account, no broker unless you ask for one, and no
outbound connection of Foyer's own.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-en.png" alt="The Foyer panel: two areas armed by one scenario, one counting down its entry delay, the zones that are not ready, and the last few events" width="900">
</p>

## Where this came from

Most people who end up here already have the hardware and do not know it.

You put a contact sensor on the front door because you wanted the hall light
to come on. You put one on the bedroom window because you wanted to be told
you had left it open before the rain started. You put a PIR in the corridor for the
night light, and another in the kitchen because the extractor fan should
notice somebody is cooking. Two winters later the house is full of exactly the
sensors a burglar alarm is made of, and they are being used to switch lamps.

Then you ask what an alarm costs. Somebody comes round, quotes a figure that
makes you blink, and proposes to drill holes for a contact on the front door
and a PIR in the hall — which is to say, for the two sensors already screwed
to your doorframe. And then there is a monthly subscription, because the
keypad has to phone somebody.

So the thing that is missing is not the hardware. It is the discipline around
it: areas that arm separately instead of one all-or-nothing switch, an entry
delay that survives a restart, a zone that declares what "open" means for it
rather than assuming `on`, one incident instead of nine notifications at once,
a log you can still read in three weeks, and some way to check the whole lot
without setting anything off at two in the morning.

That is what this is. It costs an evening of configuration, and if you already
own the sensors you have already paid for most of it.

**What it is honestly not:** a certified system, a monitored one, or
professional hardware. Nobody is watching, no grade is met, and detection is
only as good as the sensors somebody bought for a light switch. What it can be
— with a UPS on the router, one notification channel that survives the fibre
being cut, and a second sensor where a single one would be lonely — is a very
good result for the money, on a house that is already smart.

## What it does

- **Areas that arm on their own.** Each has its own `alarm_control_panel`
  entity and its own state; a *Whole house* panel aggregates them. The ground
  floor can be armed while you are upstairs.
- **Arming scenarios you define.** *Night, ground floor only*. *Garage only*.
  *Dog at home*. Any number of them, not four fixed modes. The Overview arms
  one with a button of its own — *Arm “Night”* — and says beside it whether
  the house is ready or which zones are not; arming a single area outside any
  scenario is the exception, behind *Just one area…*.
- **A keypad by the door, a tag in your pocket.** Ring and Zigbee keypads, NFC
  tags, RFID badges and remotes arm and disarm the house through a documented
  service contract, an optional MQTT contract in both directions, or Foyer's
  own HTTP endpoint with a token per device. A device is
  declared before it may command anything, and the refusal it gets back is
  structured — *wrong code*, *locked out*, *blocked by the kitchen window* — so
  the hardware can say which, and the log names the person, the channel and the
  device.
- **A code for each person.** Stored as a hash and checked in the backend
  only — a card is a keypad that transmits a code, never something that
  decides. Which operations ask for one is yours to set, an area or a scenario
  can ask for more, and every row of the log says who did it. When the panel
  asks, it says what the code is for — *Code to disarm Ground floor* — and
  which area or scenario is asking; it forgets the code after two minutes
  unused, after every arming or disarming, and when the panel closes. Plus a
  duress code that disarms normally and raises a silent alarm, and a lockout
  after repeated wrong codes.
- **Zones that declare their own trigger.** Normally-closed and normally-open
  contact sensors behave in opposite ways, so Foyer proposes a trigger from the
  entity's device class and then makes you confirm it against the real sensor.
  A wrong guess here is an alarm that never fires, and you find out during the
  burglary.
- **Smoke, gas and water on a separate channel.** Live whether the house is
  armed or not, never touching `alarm_control_panel` — where *triggered* means
  "someone has broken in" to HomeKit, Google and Alexa — and disarming does not
  clear it.
- **One incident, not one alarm per zone.** A real break-in trips the window,
  then the hall, then the stairs. They become a single incident with a single
  acknowledgement, instead of three notification storms at the worst possible
  moment.
- **A notification that keeps looking for somebody.** An address book of
  people rather than services, each with their channels in order of priority,
  and steps at the times you choose: push now, SMS in a minute, a second
  person two minutes later. It stops the instant anybody acknowledges — from
  the button in the push notification, by disarming, from a key pressed during
  the voice call, or from `foyer.acknowledge` — and every acknowledgement
  records who and through which channel. If nobody does, the last step says so
  as an event of its own. Quiet hours let a break-in through and hold back the
  rest.
- **An event log in a database of its own**, which the recorder's ten-day purge
  cannot touch: what happened, where, through which channel, whether each
  action actually worked, and who changed what.
- **The log is about people, and it can let one go.** Hand somebody every row
  that names them, as a file. Take a person out of the log without losing a
  single event — the record of *what happened* survives the removal of *who*.
  Shorten retention on the categories that name people, or let names age out
  on their own, having been told plainly what that costs.
- **A simulator that answers "what would happen if…" without anything
  happening.** Pick a scenario and an hour, force a window open a minute in,
  and read the whole decision, including the actions that would *not* have run
  and why. [Below](#asking-what-would-happen-without-anything-happening), with
  an example.
- **A walk test that tells you which zones never saw you.** The house is armed
  for real and every response is held back — except 24h, tamper, technical and
  panic zones, which stay fully live, because a walk test must never silence a
  smoke detector. It ends itself, and it says so on every screen while it
  runs. [Below](#walking-the-house-and-pressing-the-button).
- **The house can arm itself, and tell you before it does.** Rules on
  presence, a time of day or an entity's state, with safety checks that stop them —
  only if disarmed, only if every zone is ready, only if nothing has moved
  inside for N minutes. Each one announces itself first with a push carrying a
  **Cancel** button, and a suspension named "Boiler engineer, 09:00–13:00"
  keeps the house open for the morning somebody is expected — so that in six
  months the log still says why.
  [Below](#letting-the-house-arm-itself).
- **A test button beside every action and every contact channel, and it
  really executes.** Sound the siren for three seconds, actually send the
  notification to that person through that transport. The failure this
  prevents is discovering during the emergency that the emergency channel was
  misconfigured. Confirmed, permissioned, and logged as a test.
- **Foyer checks that Foyer still works.** The mains, every notification
  channel, an external watchdog that raises the alarm from outside the house
  when the pings stop, and many zones on one radio going quiet at once. An
  alarm that cannot tell you it has stopped working has stopped working.
- **Test & diagnostics: a live table of every zone**, with the one column the
  configuration pages cannot show you — whether Foyer would count that sensor
  as *triggered right now*, read through that zone's own trigger. Plus whether
  it would block arming and for which of the two reasons, its battery, its
  radio, and when it last actually moved.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-contacts-en.png" alt="The Contacts page: three people with their channels in order of priority, the four steps of an escalation with the time between them, and the four ways to stop it" width="900">
</p>

<details>
<summary><strong>The rest of what is already there</strong></summary>

- **Eight zone presets** over editable properties: instant, delayed, follower
  (only alarms if a delayed zone opened first), 24h, tamper, technical, panic,
  and key zones that arm or disarm instead of alarming.
- **Exit and entry delays**, and four things a zone can do when it is open as
  you arm: block, exclude itself, wait for you to close it, or be ignored.
- **Forced arming** as a distinct, recorded command, and manual exclusion of a
  zone — with a duration, after which it is included again and says so,
  because a zone excluded and forgotten is exactly the window somebody comes
  through.
- **A siren cutoff with alarm memory**: the siren stops, the fact that it
  fired does not.
- **Verification groups**, N of M within a window, with the members keeping
  their own response: one detector notifies, two sound the siren.
- **Response profiles**: ten actions — notification, siren, light, camera,
  scene, switch, spoken message, call any Home Assistant service, wait — each
  with up to two conditions, inherited area, then scenario, then default.
  Two moments come after an alarm: *Alarm over*, when the siren cutoff runs
  or the area is disarmed during the alarm, and *Alarm memory cleared*, when
  a disarm or the next arming of that area clears the memory, even hours
  later — the one for switching off the lamp that says something happened
  while you were out. Arming again is not taking note of the alarm: an
  incident nobody has acknowledged stays open, and its escalation carries
  on, until somebody acknowledges it or disarms.
- **A picture with the alarm**, and you say which app it is for. The Companion
  app gets a link to the live camera through Home Assistant's authenticated
  proxy, with no file written; Telegram gets a still, because its server does
  the fetching from outside your house and cannot follow that link. Foyer asks
  which one rather than guessing from the service name, because a transport
  drops a key it does not recognise in silence — and "I attached a camera and
  nothing arrived" is how you find out, months later.
- **Chime** when a zone opens while its area is not watching it, to a speaker,
  a siren or a phone, with quiet hours per target.
- **State that survives a restart**, including a delay half-run and a siren
  mid-sounding.
- **Permissions per person**, enforced on every service and every WebSocket
  command rather than only in the interface, with a validity window for guest
  codes and a scope limited to chosen areas or scenarios. An area or a
  scenario says whether it asks for a code to arm and to disarm — *Code
  required*, *No code*, or *As the global policy*, and where the two disagree
  the one that asks wins — and a scenario can be limited to the people ticked
  under *Who may use it*. Anything that changes people — a person, a tag, the
  person a key switch acts as, a scenario's list of people — needs *Manage
  users and codes* as well as *Edit the configuration*, from any page and in a
  restored backup.
- **`skip_exit_delay`**, for the last person out who is already outside. It
  needs no permission of its own, and it is recorded on the arming row, because
  it turns every delayed zone into an instant one.
- **A panel in English and Italian**, with contextual help on every page, a
  Delete that asks first, in place beside the button, and a card with `full`, `compact`, `keypad` and `badge` layouts — `badge` being
  colour and state only, with nothing to press, for dropping into a dashboard of
  your own.

</details>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-zone-en.png" alt="The zone editor asking which states count as triggered, and requiring confirmation against the real sensor" width="900">
</p>

## Asking what would happen, without anything happening

The simulator calls the same decision engine the alarm calls, with a made-up
world and a made-up clock, and then never hands the result to the part that
would run the sirens — a structural guarantee rather than a promise, for
[the reason set out below](#how-you-can-check-it-rather-than-trust-it).

Pick a scenario and an hour, force zones into a state at chosen offsets, and
read what would happen — including the actions that would *not* have run, each
with the reason:

```
21:32:00  Area "Ground floor": Disarmed → Arming · exit delay until 21:32:30
21:32:30  Area "Ground floor": Arming → Armed
            Profile "Default", inherited from the global default
            ✓ Home Assistant notification
21:33:30  Zone "Living room PIR" → on
          Area "Ground floor": Armed → Triggered · siren until 21:36:30
          Group "Living room": 1 of 2 within 60 s → not satisfied
          Incident opened 20260914-213330-1
            Profile "Silent", inherited from the zone
            ✓ Notify Ruth
          ⏱ siren cutoff at 21:36:30
21:34:00  Zone "Hallway PIR" → on
          Group "Living room": 2 of 2 within 60 s → SATISFIED
          Zone joined the incident 20260914-213330-1
            Profile "Full", inherited from the group
            ✓ Indoor siren
            ✗ Hall lights — condition not met: time 22:00-07:00
            ✗ Landing lights — held back by a delay earlier in the sequence
          ⏱ the rest of this sequence at 21:34:30
21:36:30  Area "Ground floor": Triggered → Armed
          Siren cutoff
```

One detector on its own is *Silent*; two within the window are *Full*. That is
what graduated response looks like before a burglar shows you.

Two limits, because they are the difference between a useful tool and a false
sense of one. It rehearses the **decision**, not the transport: it will tell you
a notification would be sent to a given target, not that the target works. And
it does not replace a walk test — forcing a zone into a state proves what the
engine does about it, and proves nothing about whether the hallway PIR is aimed
at the hallway. That is the next section's job.

How to read a trace, and what is worth rehearsing before you trust a
configuration: [docs/simulator.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/simulator.md).

## Letting the house arm itself

Every phone leaves. Five minutes later the safety checks run — nothing open,
nothing moving inside, the house disarmed — and a push arrives on those
phones: *Nobody seems to be in, so “Arm when empty” will arm Away. Cancel
to stop it.* Two minutes. Press Cancel and it does not; press nothing and it
does, and the log says which rule armed the house.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-rules-en.png" alt="The Automation rules page: a rule that arms when everybody has been away for ten minutes, with its guards and its two-minute grace period, an expected-visitor window for the boiler engineer, and the automatic disarming card naming the attack it protects against and the perimeter area a rule may never disarm" width="900">
</p>

The safety checks are the part worth configuring. A rule stopped by one is
written to the log under *System*, because *"why did it not arm last night?"* is a
question people ask and silence is the worst possible answer. And the morning
somebody is expected, a named window — "Boiler engineer, 09:00–13:00" — holds
the rules back, and can put the perimeter alone in place of what they would
have armed.

Turn off the check that every zone is ready, and an open window no longer
holds the rule back quietly: the countdown names it and says the house cannot
arm until it is closed, and the rule arms by itself once it is. The rule's
contacts are told what came of it — not armed and why, then arming now —
even in their quiet hours. A rule can instead be set to **Arm anyway,
excluding open zones**: off by default, it excludes only open zones that
may be excluded, never one in fault, and the log records it as a forced
arming.

**Arming and disarming are not treated as equally safe.** Automatic disarming
exists, is off until you turn it on, and can never act on an area you marked
as the perimeter. Presence in Home Assistant is inferred from a phone: a
stolen phone, 200 metres of GPS drift or a cloned MAC address on your network
all look exactly like you coming home. Whoever walks in on a stolen phone
still finds every external door and window armed — enforced in the engine,
with a test that asserts it, not a default on a screen.
[docs/automation-rules.md](docs/automation-rules.md) says the rest without
softening it.

## Walking the house, and pressing the button

The simulator answers *what would the alarm do*. Two things it cannot answer:
whether that PIR is aimed at the hallway, and whether your notification
actually arrives. Those need the house and the channel themselves.

**The walk test** arms every area for real and reads every sensor for real —
and holds the whole response back. Walk from room to room and the page fills
in live. What matters is not the zones that detected you but the ones that
never did, which are listed first: a door nobody opened and a PIR pointing at
the wrong wall look identical there — and a sensor that has simply stopped
reporting is marked as a fault beside them, which is the one case of the three
the list can tell apart for you.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-walktest-en.png" alt="A walk test running: a banner saying every response is held back and what stays live, and the zone that never reacted at the top of the table while the four that did carry the time they first saw somebody" width="900">
</p>

Three things about it that are not optional, because for as long as it runs a
real intrusion produces nothing:

- **24h, tamper, technical and panic zones stay fully live.** A walk test
  never silences a smoke detector.
- **It ends itself.** Fifteen minutes without a detection by default, each
  detection pushing that back so a large house can be walked in one pass, and
  an absolute cap that ends it whatever happens. There is no setting that
  switches the auto-exit off.
- **It says so everywhere.** A banner in the panel and on every card layout —
  including `badge`, which has nothing to press and shows it anyway — plus a
  notification when it starts and when it ends, and both in the log with the
  person who started it.

A detection during a walk test is recorded and moves nothing else: no alarm,
no incident, no alarm memory, and nothing tells HomeKit or Alexa that somebody
has broken in. Leaving disarms exactly the areas the walk test armed.

**The action test** is a button beside every action, and it really executes.
That is the point: the failure it prevents is discovering during the emergency
that the emergency channel was misconfigured. It asks first, needs the
`test_actions` permission and a code, sounds a siren for three seconds
whatever its configured duration, and leaves a row in the log marked as a
test — never as the alarm it imitates.

## When the alarm itself stops working

An alarm that cannot tell you it has stopped working has stopped working. Four
failures silently defeat a do-it-yourself alarm, and in every one of them the
house looks perfectly quiet: the power goes out, the notification channel
breaks, the radio goes quiet, or Home Assistant dies.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-health-en.png" alt="The System health page: mains power present, the watchdog reporting every fifteen minutes with an empty payload, and every notification channel with its last successful send or the fact that it has never been used" width="900">
</p>

- **Mains power.** Name your UPS sensor and which of its states means failure —
  a UPS says `on` for a power cut and a power sensor says `off`, so Foyer asks
  rather than guesses. A failure notifies at once and is never a quiet night.
- **Notification channels**, checked every quarter of an hour and after every
  real send. A `notify` service somebody removed in an update is found before
  the night it matters, and the warning goes out **over a channel that still
  works** — a warning sent over the dead channel would reach nobody.
- **An external watchdog.** Foyer pings a URL you choose; if Home Assistant
  dies the pings stop and that service raises the alarm, which is the only
  answer to a dead system being unable to report its own death. The heartbeat
  **carries nothing**: a ping saying "armed, nobody home" would tell a third
  party exactly when to come. And the URL is kept as a credential — whoever
  holds it can keep the check green for ever — so once saved it is never
  shown again: a new one is typed over it.
- **Radio interference**, *suspected* and never claimed. Many zones on one
  radio going quiet within seconds is its signature — and also the signature
  of a coordinator crash, a firmware update, a channel change and a power cut
  to a room of mains-powered routers. Foyer counts them per radio, gates it on
  the coordinator still answering, waits a minute to see if it is still true,
  and then **does not act through that radio**: announcing a Zigbee blackout
  through a Zigbee siren is not a notification.

None of it is an intrusion, so none of it ever touches an
`alarm_control_panel` — with one exception: on an armed house, confirmed
interference opens an incident, as jamming does in a professional panel.
Persistent problems also become Home Assistant repair issues, in Settings,
where somebody meets them without opening the Foyer panel.

[docs/system-health.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/system-health.md)
has the detail and states the heuristic as a heuristic;
[docs/resilience.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/resilience.md)
is the shorter and more uncomfortable one: what survives when somebody cuts
the power, why a UPS on the router is the highest-value thing you can buy, and
why a local GSM channel is the only one that survives the fibre being cut.

## The log is about people

The log records who was in the house, when they arrived and when they left. In
a family that is nobody's business but yours — the GDPR's household exemption
covers it and there is nothing to do. **It stops covering it the moment the log
records somebody else**: the cleaner whose arrivals are kept for a month, the
boiler engineer, the babysitter. And it does not apply at all to the B&B, the
holiday let or the small office.

So, on the *Log* page, under *One person's data*:

- **Export one person's rows** as CSV or JSON, in a file named after them.
  Wide on purpose: what they did, plus what the house did to them — their tag
  refused, an escalation that reached them.
- **Erase their history**, which is not the same as deleting their user. Deleting
  a user leaves the history of what they did, because the name is copied into
  every row precisely so that it does. Erasing empties the name, the account,
  the channel and the device on their rows and leaves every event where it
  was: the log still answers *what happened on the night of the fourteenth*,
  and no longer answers *who*. It is itself recorded, without naming them.

And on the *Settings* page, under *Personal data in the log*:

- **A seven-day retention preset** that touches only the categories naming
  people, leaving actions, faults and door states alone — those name nobody and
  are what you read when a sensor did not react three weeks ago.
- **Timed pseudonymisation** (*Replace names in older rows*), off by default,
  which after N days replaces names
  with a stable identifier. The panel says before you switch it on that it
  trades away the answer to *who disarmed that night* for every older row —
  which is the very question the log exists to answer. A real trade, not a
  free safety feature, and it cannot be undone by switching it off again.

[docs/privacy.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/privacy.md)
is the practical version: what a row contains, where the exemption stops, and
what to do about it. It is information, not legal advice.

## Arming from the wall

Foyer does not talk to keypads. It offers a contract, because keypad models
churn every six months and a contract does not. Anything that can call a Home
Assistant service, publish to an MQTT broker or make an HTTP request to
Foyer's own endpoint can arm this house.

- **Natively:** NFC tags, RFID badges and remotes. Point Foyer at a `tag.*` or
  `event.*` entity, say whose it is and what a scan does. No automation in
  between, and the log names the person — which is the whole point of a channel
  that identifies rather than one that asks for a code.

  A tag carries no code, and the editor says so where somebody is deciding
  whether to keep one in their wallet:

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-tag-en.png" alt="The tag editor: a warning that a stolen tag arms and disarms without knowing any code, above the field that says whose tag it is" width="900">
</p>

- **Through the service contract:** `foyer.arm`, `foyer.disarm`,
  `bypass_zone`, `unbypass_zone`, `acknowledge`, and the export and import of
  configuration and log. Every state-changing call takes a code, a user and a
  device, and returns a structured answer: `success`, a stable `reason`
  (`bad_code`, `locked_out`, `zone_open`, `not_permitted`, …), the zones that
  blocked it *by name*, and the whole live state. That is what lets a keypad
  give two different refusals instead of one, and a household that hears one
  sound for both will retype a code that was never the problem.
- **Over MQTT, in both directions**, with configurable topics and off until you
  switch it on. The device publishes a command; Foyer publishes the state back,
  retained, so a keypad that has just rebooted knows what the house is doing.
  The retained message says the *least* by default — a broker is often somebody
  else's machine, and "armed, nobody home" is told to whoever connects next.
  Three levels, and you raise it knowingly.
- **Over Foyer's own HTTP endpoint**, for a device that should not be just a
  name on a broker: each one holds a token of its own, shown once. The token
  says which device is asking and encrypts nothing, so over plain HTTP it and
  the codes typed on the device can be read on the network. Such a device is
  still served, and marked *Unencrypted* under *Arming devices* and in every
  log row it causes.

**API devices.** The same endpoint serves a touch display in the hall, a relay
that lights an "armed" lamp, or an ESP32 or Arduino module of your own. Each
reads and does only what is ticked for it, every permission off to begin with.
Reading the state of the alarm can be free; the zones, batteries, system health
and log are read, by default, only for a short while after somebody types a
valid code on the device, and only what that person may see. Every action,
arming included and on keypads too, needs a code typed on the device: the token
alone never arms or disarms anything. The contract is written down in
[docs/api/openapi.yaml](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/api/openapi.yaml),
as version v1, and a test in CI compares it with the code; administrators can
read it and try it with a device's token on the panel's *API* page.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-api-device-en.png" alt="A device on the endpoint and what it may read and do: the state readable without a code, the zones, batteries and log only after a code, arming and disarming allowed, excluding zones and taking note not, and the confirmation that these readings cross the network unencrypted" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-api-en.png" alt="The API page for administrators: the device contract, version v1, rendered with Swagger UI, with the Authorize button for a device token and the three routes of the endpoint" width="900">
</p>

**A device is declared before it may command anything.** An unknown device is
refused whatever code it brings, and the refusal is logged and raised. This is
not tidiness: the lockout counts failed codes per device — and per Home
Assistant account on the panel, the card and the services — so a caller free to
invent a device name is a caller who is never locked out. For the
same reason `keypad` and `nfc` are properties of a registered device, never a
word a message can claim about itself.

Three blueprints ship with the repository — Ring Alarm Keypad v2 over Z-Wave JS
with its LED ring and countdowns, a generic Zigbee keypad over Zigbee2MQTT, and
one for tags and remotes doing what the native path deliberately will not. Two
warnings, plainly: Ring has published no LED mapping, so the indicator numbers
in that blueprint are community work you should verify against your own firmware
with `zwave_js.set_value`; and Tuya-family Zigbee clones vary by firmware
revision, so two keypads sold under the same photograph can send different
action names. In both cases the arming still works — what a wrong value breaks
is only what the keypad shows you.

Each one imports into your own Home Assistant with one button, in
[docs/keypads.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/keypads.md) —
which also holds the contract (services, MQTT, the endpoint and API devices),
the hardware comparison and how to write your own adapter.

A keypad should never be your only way in: batteries die, radios jam, brokers
stop. Keep the panel and the card.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-devices-en.png" alt="Arming devices: two keypads and a tag, each declared before it may command anything, and the MQTT contract with the message it will actually publish" width="900">
</p>

## "I could do this with automations"

You could, and the first version works. What costs the next six months is the
rest of it: an entry delay that survives a Home Assistant restart halfway
through; a sensor that went `unavailable` three weeks ago and has been quietly
reading as "closed" ever since; the three separate notification storms a real
break-in produces because every zone fired its own automation; and the evening
you want to answer *was the kitchen actually armed at 02:14?* and the recorder
purged it ten days ago.

Foyer is those parts. Your automations are still welcome: it emits an event for
everything it records, and it can call any service you like.

## Not yet, and it matters

- **No ESPHome keypad of our own.** DIY builds fit the contract like anything
  else, but this project does not maintain one in v1.

The order is fixed and written down, with what each step has to prove before it
counts as done: [the roadmap](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md#16-roadmap).

## Compared with Alarmo

[Alarmo](https://github.com/nielsfaber/alarmo) is the reference implementation
in this space, and a good one. Foyer is written from scratch and does not copy
its code. Where they differ today:

| | Foyer | Alarmo |
|---|---|---|
| **Escalation until somebody answers** | Contacts with channels in priority order, steps at times you choose, stopped by any of four acknowledgements | Notifications and actions with delays; nothing that tries a second person, and nothing to acknowledge |
| **Arming itself, safely** | Rules with safety checks and a cancellable countdown; disarming off by default, and never on an area you marked as the perimeter | Arming and disarming on presence, via automations |
| **Simulator** | Yes: the same engine, a made-up world and a made-up clock, and a trace saying why each action would or would not have run | — |
| **Walk test** | Yes: really armed, every response held back, and the zones that never reacted listed first. 24h, tamper, technical and panic zones stay live | — |
| **Action test** | Yes: really sounds the siren or sends the message, with confirmation, and logged as a test | — |
| **Arming scenarios** | Any number, each arming a chosen set of areas | Home Assistant's four fixed modes |
| **Areas with independent state** | Yes: one `alarm_control_panel` each, plus *Whole house* | One panel, sensors grouped per mode |
| **Smoke, gas, water** | A separate channel, live while disarmed, never `triggered` on an alarm entity | Can be always-on, but on the same panel: smoke puts the alarm entity into `triggered`, which means *burglary* to HomeKit |
| **A sensor that goes `unavailable`** | A fault: it blocks arming, shows in diagnostics and is in the log. Never read as "all quiet" | Read as whatever state it last had |
| **State across a restart** | Areas, timers mid-delay, escalation progress and the gap itself, all recorded | Arming state |
| **One incident per break-in** | Yes, with one acknowledgement | An alarm per sensor |
| **Users, codes, permissions** | Yes: one code each, per-operation policy, duress code, lockout | Yes, per-user codes |
| **Keypads, MQTT** | Yes, and a refused command comes back with a stable reason and the blocking zones by name, so a keypad can sound different for *wrong code* and *kitchen window open* | Yes |
| **NFC tags and remotes** | Native, declared on a page and bound to a person, with no automation to write | Via automations |
| **Verification groups (N of M)** | Yes, with the members keeping their own response | — |
| **Installing it** | HACS custom repository | The default HACS store |
| **Maturity** | Beta. One author, months old | Years of use, a large installed base |

If you need an alarm that thousands of houses have already shaken the bugs out
of, use Alarmo. Foyer is a beta, and the honest difference between the two
columns above is time.

### Bringing an Alarmo configuration across

Nobody with forty configured sensors remaps them by hand to try something new,
so Foyer can read Alarmo's configuration and bring it in, from **Settings →
Import from Alarmo**. Read what it is before you use it.

**It is a best-effort tool, not a migration.** It reads
`.storage/alarmo.storage`, which is Alarmo's internal format: its author may
change it in any release, without notice and without fault, because it was
never offered as an interface to anybody. So the importer tells you everything
it could not convert, and it refuses a file written in a storage version it
has not been checked against — by name — rather than guess. Today that is
storage 6.1 to 6.3, which Alarmo 1.9.5 to 1.10.19 write.

It shows you what it would do before it writes anything, and adds to what is
already here rather than replacing it:

- **Areas, sensors and modes** become Foyer areas, zones and scenarios — one
  scenario per mode you had switched on that watches something, or, when you
  already have a scenario reporting that mode to Home Assistant, that one arms
  the new areas as well, so voice assistants and HomeKit keep working. Where
  Alarmo had several delays and
  Foyer has room for one, it takes the longest; where a value is past Foyer's
  limit — a siren that sounded for half an hour — it takes the limit. Either
  way, the report says so.
- **Every zone arrives switched off.** Alarmo reads `on` as alarm for every
  sensor, which is exactly the assumption Foyer is built to refuse, so each
  zone carries Foyer's own proposal and watches nothing until you have
  confirmed its trigger on the *Zones* page.
- **People come across without a code, always.** Alarmo keeps its codes as
  hashes in its own format, and Foyer does not take a credential from another
  system on trust, so everybody needs a new one on the *Users* page before they can
  disarm with it. The report says so in its first line.
- **Sirens and switches** come across into a response profile. Notifications,
  groups and the other things Foyer cannot bring are listed in the report, not
  guessed at: a
  notification that arrives somewhere unintended is worse than one you set up
  again.

## How you can check it rather than trust it

Three of these you can do this evening: rehearse a night in the
[simulator](#asking-what-would-happen-without-anything-happening),
[walk the house](#walking-the-house-and-pressing-the-button) and see which
zones never noticed you, and press the test button beside your siren. The rest
are structural, and they are why the first three are worth believing.

- **The part that decides is a pure function.** "This zone opened, this area is
  armed, what now?" is answered by code that cannot reach Home Assistant, has
  no clock of its own and cannot perform an action; it is tested on its own,
  and CI refuses a commit that lets Home Assistant in. That is what makes the
  simulator's answer truthful rather than optimistic: it is the same function,
  given a made-up world, and a test asserts that it and the running alarm reach
  an identical decision from identical inputs.
- **A gap in coverage is written down.** If Home Assistant was down for two
  hours, the log says so, with the duration. It never implies you were
  protected when you were not.
- **A name nothing verified is marked as such.** Arming needs no code, and a
  service call may simply state who is acting — so a row could otherwise credit
  a person on nothing but the caller's word. The name is kept, because
  attribution is worth having, and the row is marked *(not verified)* beside
  it. A
  code or a tag produces an unmarked row. A wrong answer to "who disarmed at
  03:14?" is worse than no answer.
- **Every action reports whether it worked.** A siren that did not sound and a
  notification that did not send are rows in the log, marked failed — not
  silence.
- **The changelog says what changed in behaviour**, not "various fixes",
  because that is what you need in order to decide whether to take an update.

All three verification tools, and how to read what they tell you:
[docs/simulator.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/simulator.md).

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-log-en.png" alt="The log: arming, an alarm, an arming refused with the zone that blocked it, the restart gap, a configuration change with its old and new value, and a notification that failed" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-users-en.png" alt="Users and codes: two people with their permissions, scope and validity, and the table of which operations ask for a code" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-arm-code-en.png" alt="Arming from the Overview: the prompt says what the code is for, Code to arm Away, and which area asks for it, Upstairs" width="900">
</p>

## What the codes are for, and what they are not

Foyer's codes are there to stop the people who are *in* your house from
disarming it: household members, guests, the cleaner, a non-admin Home
Assistant user, whoever picks up the wall tablet you left unlocked. They are
not there to stop **you**. A Home Assistant administrator can read `.storage`,
disable the integration or call any service directly, so no code in Foyer means
anything to them — and the event log is audit-*useful* rather than
tamper-*proof* for exactly the same reason.

That is the honest boundary, and it is worth knowing before you rely on it.
Foyer is an integration that does what an alarm does; it is not a certified
alarm system, it does not meet EN 50131 or any equivalent grade, and it does
not replace a monitored professional installation.

**The acknowledgement webhook, if you switch it on, is an unauthenticated
URL.** It exists so a voice provider can feed back the key somebody pressed
during a call. Home Assistant webhooks are open to whoever holds the address,
so anybody who has it — or intercepts it — can acknowledge an alarm in
progress, which stops the escalation on its way to the next person. It cannot
arm, disarm, read the log or change anything. It does not exist until you
switch it on, the id is generated and random, the panel shows its address
once — when it is generated — and switching it off forgets it; to see it
again, you generate a new one.
[The details](docs/notification-channels.md#twilio-voice-call).

**And it is not a fire alarm system.** The technical channel is genuinely
useful — it is live whether the house is armed or not, and disarming has no
authority over it — but a smoke detector wired into Home Assistant does not
replace certified, interconnected smoke alarms. Buy those separately. They are
not expensive, and this is the one item on the page where being wrong is not
about a burglary.

## What you need

- Home Assistant 2025.1 or later. Developed and tested against 2025.1 and the
  current release.
- At least one door, window or motion sensor already working in Home
  Assistant.
- A `notify.*` service that works. Foyer orchestrates notifications; it does
  not implement them, and
  [docs/notification-channels.md](docs/notification-channels.md) has a recipe
  for each of the usual ones — including which survive a cut fibre.
- A siren, a switch or a smart plug, if you want noise. Optional.
- A keypad, an NFC tag or a remote, if you want to arm from the wall.
  Optional — and an MQTT broker only if the device you choose speaks MQTT.

Nothing else: no cloud account, no broker unless you ask for one, no outbound
connection of Foyer's own.

## The first fifteen minutes

1. Install from HACS as a custom repository (below), restart, and add the
   integration. You get one area, one scenario and one zone.
2. **Check the trigger against the real sensor.** Open the door, walk past the
   detector, watch the state change. This is the one step worth doing slowly.
3. **Create yourself a user with a code.** Until somebody holds one, nothing
   asks for one, and the panel says so where you cannot miss it. From then on
   the panel asks you for it wherever the policy asks for one, administrator
   or not.
4. Send the test notification the wizard offers. If it does not arrive, nothing
   else in Foyer matters.
5. Arm, walk in, let the entry delay run out, and let it fire — once, on
   purpose, while you are standing there. Then open the log and read what it
   says about the last two minutes, and who it credits.

## Install

1. In HACS, open the menu → *Custom repositories*, add this repository's URL
   with category *Integration*.
2. Install *Foyer Home Defender* and restart Home Assistant.
3. *Settings → Devices & services → Add integration → Foyer Home Defender*.
   Name the first area and scenario, pick the first zone entity, then confirm
   the states in which it counts as triggered.
4. A **Foyer** entry appears in the sidebar, and a wizard of five short steps
   finishes the setup: *Area*, *Zones*, *Scenario*, *User and code*, *Test
   notification*. Before *Finish* it lists what the five steps did not cover,
   each with the page that does.

Since `0.1.0-beta.1`, releases are published normally rather than as GitHub
pre-releases, so HACS offers them with their version names. If you enabled the
*pre-release* switch entity for this repository during the alpha, you no longer
need it.

<details>
<summary>The card is missing from the picker, or "Custom element doesn't exist"</summary>

Reload the page once with Ctrl+Shift+R (Cmd+Shift+R on a Mac). Home Assistant
writes a card's script tag into the page it renders, so a page that was loaded
before Foyer was installed — or before it was updated — does not have it, and
reconnecting after a restart does not fetch a new one. In the companion app,
reset the frontend cache from its settings, or close and reopen the app. To
check that the file itself is there, open
`https://<your-home-assistant>/foyer_static/foyer-card.js`: it should show
JavaScript.

</details>

### The card

Pick *Foyer Home Defender* in the dashboard's card picker, or write it by hand:

```yaml
type: custom:foyer-card
entity: alarm_control_panel.foyer_master   # or alarm_control_panel.foyer_<area>
layout: full                               # full, compact, keypad or badge
```

No dashboard resource needs adding. The card decides nothing by itself: it
sends a command and renders the answer, including the name of the zone that
refused it and the way past it.

*Full* and *Compact* open the keypad when a code is asked for; *Keypad*
always shows it, and an entry delay that will want a code opens it by itself.
Above the digits it says what they are for — *Code to arm Away*, *Code to
disarm Ground floor* — and they go only with that command: any other button
sends without them. Typed digits are forgotten after 30 seconds without a key,
and when the card leaves the screen. During an entry delay or an alarm the
scenario buttons step aside, because the one thing left to do is disarm.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-en.png" alt="The card in its full and compact layouts during an entry delay: every area with its state, the countdown, and the keypad that opens by itself because disarming asks for a code" width="620">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-keypad-en.png" alt="The keypad layout for a wall tablet: three digits of a code typed, the entry delay running, and the button that ends it" width="620">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-code-en.png" alt="The keypad waiting for a code: the caption says Code to arm Away, three digits are typed, and the confirm key reads Arm Away" width="620">
</p>

## Questions people ask

<details>
<summary>Can I run Foyer and Alarmo at the same time?</summary>

Both can be installed, but do not point them at the same sensors: you would
have two systems deciding what an open window means, arming and disarming
independently of each other. Try Foyer on a few zones, or on a test
installation, and move the rest when it has earned it. The
[importer](#bringing-an-alarmo-configuration-across) is built for exactly
that: it brings the zones in switched off, so nothing is watched twice until
you decide.

</details>

<details>
<summary>Who can disarm it?</summary>

Whoever holds a code, and only for what their permissions allow. Until you
create the first user, nobody is asked for anything and anyone with access to
Home Assistant can disarm — the panel says so plainly while that lasts. A
person can be exempted from typing their code on channels that already know who
they are, such as the Home Assistant interface signed in as them; on a shared
keypad the code *is* the identity, so the exemption cannot apply there.

Being a Home Assistant administrator identifies nobody, though: the
unlocked wall tablet is almost always signed in as one, so the panel asks an
administrator for the code like anybody else, whenever the policy asks for
one.

</details>

<details>
<summary>Can I arm from Home Assistant's own cards, or by voice?</summary>

Yes, and Foyer answers, as it does everywhere else. What Home Assistant asks
for first depends on one thing Foyer tells it: that arming needs a code. That
is said only while your policy asks for a code to arm and nobody has the
exemption above switched on, because Home Assistant would refuse everybody who
typed none, the exempt person included. While it is said, Home Assistant's
pop-up dialog and a tile's arm buttons ask for the code themselves. Once
somebody is exempt they stop asking: that person arms with no code, and
anybody else is refused by Foyer, with a row in the log and a message saying
where a code can be typed — Home Assistant's *Alarm panel* card, which shows
a code field wherever a code may be asked, Foyer's card, or the panel.

Voice assistants read the same answer. Alexa is offered a panel only while
arming it needs no code, sends none, and does not wait for Foyer's answer, so
a refusal shows only in the panel's state and in the log. Google Assistant
asks for its PIN before arming only while a code is needed, and sends the PIN
stored in its own configuration either way: if that is somebody's Foyer code,
the arming is in their name; if it is not, it is a wrong code, and counts
towards the lockout.

</details>

<details>
<summary>I am the administrator and I have no code</summary>

In a house where others hold one, or when your own Foyer user was disabled or
ran past its validity window, you recover access from **Settings → Devices &
services → Foyer → Configure**. It enables your Foyer user, removes its
validity window and sets a new code; an account with no Foyer user gets one,
with every permission. Only administrators' accounts are offered. It is never
quiet: the recovery is written in the log, shown as a Home Assistant
notification and sent to every contact, naming the account. Anybody else is
given a way in from the *Users* page.

</details>

<details>
<summary>Does it work without internet?</summary>

Yes. Foyer makes no outbound connection of its own, and needs no cloud account
and no broker. Whether your *notifications* survive a cut line is a different
question, and the honest answer is that a push notification does not — which is
why an escalation is a list of channels rather than one, and why at least one
local channel, such as a USB GSM modem, belongs somewhere in that list.

</details>

<details>
<summary>Will my configuration survive an update?</summary>

Yes. The stored configuration is versioned and migrated step by step, and every
changelog entry says whether the schema moved. Going *back* across a major
schema step is refused on purpose rather than half-read: an older build that
silently ignored what it did not understand could silently stop protecting
something.

</details>

<details>
<summary>What happens if I remove the integration?</summary>

Its configuration, its saved alarm state, every entity and device it created,
the sidebar panel, its repair issues, the notifications it put up and its
retained MQTT message — a retained message outlives the integration and would
keep telling whoever connects to that broker next what the house was doing.

The event log database goes only if you said so, with a switch on the *Settings* page that
is off by default. Home Assistant's own confirmation is the last dialogue
there is, so the question is asked in advance, and keeping thirty days of
history is the only answer that cannot destroy something nobody meant to
destroy. The file is `foyer-log.db` in your configuration directory.

Camera snapshots are never deleted. They are photographs of the inside of your
house, in a folder you chose, which may hold files that were never Foyer's —
so removing them is left to you.
[docs/privacy.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/privacy.md)
says all of this again, in the place somebody looks for it.

</details>

<details>
<summary>Is it available in my language?</summary>

English and Italian today, panel, card and contextual help included. Adding a
language touches no code: copy two JSON files, translate, open a pull request.
CI fails if the two files' key sets differ, so a half-translated panel cannot
ship. [CONTRIBUTING.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CONTRIBUTING.md#adding-a-language)
names the two files and the one line that is not a straight translation.

</details>

## If something goes wrong

Open an [issue](https://github.com/foyer-labs/Foyer-Home-Defender/issues/new/choose) —
the form asks for what follows, and says where to find each part. Say
which version of Foyer and of Home Assistant, what you expected, and what the
log page shows — the row usually contains the answer, so a screenshot of it is
worth more than a description. English or Italian, whichever you prefer.

Attaching Home Assistant's **Download diagnostics**, from the integration's
page in Settings, usually turns an issue into one answer rather than five
questions. It is anonymised on purpose: no names, no codes, no hashes, no
URLs, and entity ids replaced by stable placeholders, so it carries the shape
of the installation and nothing about the people in it.

To be told when the next phase lands, watch the repository: releases are
announced there, and the [changelog](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CHANGELOG.md)
says what changed in behaviour every time.

## Development

```
custom_components/foyer/   the integration (HACS installs this directory as is)
  core/                    pure decision engine: no Home Assistant imports, ever
  runtime/ entity/ api/    Home Assistant-facing layers
  security/                bcrypt codes, and who a request comes from
  store/                   .storage persistence, schema migrations, the log
  translations/            en.json, it.json (Home Assistant) and panel/ (UI, help)
  frontend/                built panel and card bundles, committed
frontend/                  TypeScript + Lit sources, built with Vite
blueprints/                keypad and tag adapters (copied by hand, not by HACS)
docs/                      the specification, the keypad and notification contracts, screenshots
tests/core, tests/repo     run without Home Assistant installed
tests/ha                   run inside Home Assistant's test harness
```

```bash
pip install pytest ruff bcrypt
pytest                       # pure suite: engine, purity check, translations
ruff check . && ruff format --check .
cd frontend && npm ci && npm run build   # rebuilds custom_components/foyer/frontend
```

The integration tests need Linux or WSL:

```bash
pip install pytest-homeassistant-custom-component
pytest -p pytest_homeassistant_custom_component -o asyncio_mode=auto tests/ha
```

`core/` must never import `homeassistant`. CI enforces it; if that check fails,
the fix is the code, never the test. [CONTRIBUTING.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CONTRIBUTING.md)
says what else a pull request has to carry.

The whole design, including the reasoning behind decisions that look arbitrary
until you know why, is in
[docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md).

## Reporting a security problem

A way to disarm without a code, a way to make the alarm stay quiet, a way to
read somebody's log — those are worth telling the author about before they are
public. GitHub's **private vulnerability reporting** is open on this
repository: [open a private advisory](https://github.com/foyer-labs/Foyer-Home-Defender/security/advisories/new).
Anything that is not a vulnerability belongs in an ordinary issue, where more
people can help.

[SECURITY.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/SECURITY.md)
says what is in scope, and what is deliberately out of it: an administrator of
your Home Assistant can read `.storage`, disable the integration and call any
service, and no version of Foyer will defend against that.

<p align="center">
  <a href="https://www.buymeacoffee.com/foyerlabs" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-green.png" alt="Buy Me a Coffee" height="60"></a>
</p>

## Licence

Apache-2.0. See [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) and [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
