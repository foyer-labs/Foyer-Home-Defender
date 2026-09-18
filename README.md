<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><strong>English</strong> · <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.it.md">Italiano</a></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center"><em>A real intruder alarm panel for Home Assistant: areas that arm on their own, scenarios you define yourself, zones that say what "triggered" means for them, a keypad by the door, and a log that tells you the truth.</em></p>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?sort=semver&label=version" alt="Latest version"></a>
  <img src="https://img.shields.io/badge/status-beta-yellow" alt="Beta">
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant 2025.1 or later">
  <img src="https://img.shields.io/badge/HACS-custom%20repository-41BDF5" alt="HACS custom repository">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licence-Apache--2.0-blue" alt="Apache-2.0"></a>
</p>

> ### Status: beta. The alarm core works, it asks for a code, and there can be a keypad by the door.
>
> It can protect a house, and it is doing so. **Physical arming has landed**:
> keypads, NFC tags, RFID badges and remotes, a full `foyer.*` service contract
> and MQTT in both directions — so a keypad can tell *that code is wrong* from
> *the kitchen window is open* instead of beeping the same way at both. Codes,
> users, permissions and lockout arrived in the release before. What is still
> missing is the simulator, the walk test and escalation.

**Try it if** you already have door, window or motion sensors in Home
Assistant, you want one panel with real arming scenarios instead of a folder of
automations, you want to arm from the wall rather than from a phone, and you are
willing to run a beta on a house that has other locks on it.

**Not yet, if** you want something finished, or you need escalation across
channels, a simulator or a walk test — [Alarmo](https://github.com/nielsfaber/alarmo)
has years of use behind it, and a large installed base is a kind of testing this
project has not had yet.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-en.png" alt="The Foyer panel: two areas armed by one scenario, one counting down its entry delay, the zones that are not ready, and the last few events" width="900">
</p>

## What it does

- **Areas that arm on their own.** Each has its own `alarm_control_panel`
  entity and its own state; a master aggregates them. The ground floor can be
  armed while you are upstairs.
- **Arming scenarios you define.** *Night, ground floor only*. *Garage only*.
  *Dog at home*. Any number of them, not four fixed modes.
- **A keypad by the door, a tag in your pocket.** Ring and Zigbee keypads, NFC
  tags, RFID badges and remotes arm and disarm the house through a documented
  service contract and an optional MQTT contract in both directions. A device is
  declared before it may command anything, and the refusal it gets back is
  structured — *wrong code*, *locked out*, *blocked by the kitchen window* — so
  the hardware can say which, and the log names the person, the channel and the
  device.
- **A code for each person.** Stored as a hash and checked in the backend
  only — a card is a keypad that transmits a code, never something that
  decides. Which operations ask for one is yours to set, an area or a scenario
  can ask for more, and every row of the log says who did it. Plus a duress
  code that disarms normally and raises a silent alarm, and a lockout after
  repeated wrong codes.
- **Zones that declare their own trigger.** Normally-closed and normally-open
  contacts behave in opposite ways, so Foyer proposes a trigger from the
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
- **An event log in a database of its own**, which the recorder's ten-day purge
  cannot touch: what happened, where, through which channel, whether each
  action actually worked, and who changed what.

<details>
<summary><strong>The rest of what is already there</strong></summary>

- **Eight zone presets** over editable properties: instant, delayed, follower
  (only alarms if a delayed zone opened first), 24h, tamper, technical, panic,
  and key zones that arm or disarm instead of alarming.
- **Exit and entry delays**, and four things a zone can do when it is open as
  you arm: block, exclude itself, wait for you to close it, or be ignored.
- **Forced arming** as a distinct, recorded command, and manual exclusion of a
  zone — with a duration, after which it comes back and says so, because a zone
  excluded and forgotten is exactly the window somebody comes through.
- **A siren cutoff with alarm memory**: the sounders stop, the fact that it
  fired does not.
- **Verification groups**, N of M within a window, with the members keeping
  their own response: one detector notifies, two sound the siren.
- **Response profiles**: ten actions — notification, siren, light, camera,
  scene, switch, spoken message, call any Home Assistant service, wait — each
  with up to two conditions, inherited area, then scenario, then default.
- **Chime** when a zone opens while its area is not watching it, to a speaker,
  a siren or a phone, with quiet hours per target.
- **State that survives a restart**, including a delay half-run and a siren
  mid-sounding.
- **Permissions per person**, enforced on every service and every WebSocket
  command rather than only in the interface, with a validity window for guest
  codes and a scope limited to chosen areas or scenarios.
- **`skip_exit_delay`**, for the last person out who is already outside. It
  needs no permission of its own, and it is recorded on the arming row, because
  it turns every delayed zone into an instant one.
- **A panel in English and Italian**, with contextual help on every page, and a
  card with `full`, `compact`, `keypad` and `badge` layouts — `badge` being
  colour and state only, with nothing to press, for dropping into a dashboard of
  your own.

</details>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-zone-en.png" alt="The zone editor asking which states count as triggered, and requiring confirmation against the real sensor" width="900">
</p>

## Arming from the wall

Foyer does not talk to keypads. It offers a contract, because keypad models
churn every six months and a contract does not. Anything that can call a Home
Assistant service or publish to an MQTT broker can arm this house.

- **Natively:** NFC tags, RFID badges and remotes. Point Foyer at a `tag.*` or
  `event.*` entity, say whose it is and what a scan does. No automation in
  between, and the log names the person — which is the whole point of a channel
  that identifies rather than one that asks for a code.
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

**A device is declared before it may command anything.** An unknown device is
refused whatever code it brings, and the refusal is logged and raised. This is
not tidiness: the lockout counts failed codes per channel *and* per device, so a
caller free to invent a device name is a caller who is never locked out. For the
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

The contract, the hardware comparison and how to write your own adapter are in
[docs/keypads.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/keypads.md).
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

- **No simulator and no walk test.** You cannot yet ask "what would happen if
  the kitchen window opened right now, in this scenario, at this hour?" without
  opening it, and `foyer.walk_test` is deliberately not registered rather than
  registered and silent. *Next release.*
- **No escalation, and no contact list.** Notifications go to a `notify`
  service directly; they do not climb from push to SMS to a phone call until
  somebody acknowledges. *After that.*
- **No automatic rules.** Arming on a schedule, on presence or on a condition
  of your own is still an automation you write, calling `foyer.arm`.
  *After that.*
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
| **Arming scenarios** | Any number, each arming a chosen set of areas | Home Assistant's four fixed modes |
| **Areas with independent state** | Yes: one `alarm_control_panel` each, plus a master | One panel, sensors grouped per mode |
| **Smoke, gas, water** | A separate channel, live while disarmed, never `triggered` on an alarm entity | Ordinary sensors |
| **One incident per break-in** | Yes, with one acknowledgement | An alarm per sensor |
| **Users, codes, permissions** | Yes: one code each, per-operation policy, duress code, lockout | Yes, per-user codes |
| **Keypads, tags, MQTT** | Yes: a service contract and MQTT both ways, devices declared before they may command, three blueprints | Yes |
| **What a refused command tells the device** | A stable reason and the blocking zones by name | Success or failure |
| **Maturity** | Beta. One author, months old | Years of use, a large installed base |
| **Simulator, walk test** | Planned, not written | — |

If you need an alarm that thousands of houses have already shaken the bugs out
of, use Alarmo. Foyer is a beta, and the honest difference between the two
columns above is time.

## How you can check it rather than trust it

- **The part that decides is a pure function.** "This zone opened, this area is
  armed, what now?" is answered by code that cannot reach Home Assistant, has
  no clock of its own and cannot perform an action; it is tested on its own,
  and CI refuses a commit that lets Home Assistant in. That same constraint is
  what will make the simulator's answer truthful rather than optimistic.
- **A gap in coverage is written down.** If Home Assistant was down for two
  hours, the log says so, with the duration. It never implies you were
  protected when you were not.
- **Every action reports whether it worked.** A siren that did not sound and a
  notification that did not send are rows in the log, marked failed — not
  silence.
- **The changelog says what changed in behaviour**, not "various fixes",
  because that is what you need in order to decide whether to take an update.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-log-en.png" alt="The log: arming, an alarm, an arming refused with the zone that blocked it, the restart gap, a configuration change with its old and new value, and a notification that failed" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-users-en.png" alt="Users and codes: two people with their permissions, scope and validity, and the table of which operations ask for a code" width="900">
</p>

## Security model

Foyer's codes protect against household members, guests, cleaners, non-admin
Home Assistant users and anyone who finds an unlocked wall tablet. They do **not** protect against a Home Assistant administrator, who can
read `.storage`, disable the integration or call any service directly. The
event log is audit-*useful*, not tamper-*proof*, for the same reason.

**Foyer is not a certified alarm system.** EN 50131 grade compliance is
explicitly out of scope, and it does not replace a monitored professional
installation.

**Foyer is not a fire alarm system.** A smoke detector wired into Home
Assistant does not replace certified, interconnected smoke alarms.

## What you need

- Home Assistant 2025.1 or later. Developed and tested against 2025.1 and the
  current release.
- At least one door, window or motion sensor already working in Home
  Assistant.
- A `notify.*` service that works. Foyer orchestrates notifications; it does
  not implement them.
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
   asks for one, and the panel says so where you cannot miss it.
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
4. A **Foyer** entry appears in the sidebar, and a short wizard finishes the
   setup.

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

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-en.png" alt="The card in its full and compact layouts" width="620">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-keypad-en.png" alt="The keypad layout for a wall tablet, and the same pad opened inside the full layout" width="620">
</p>

## Questions people ask

<details>
<summary>Can I run Foyer and Alarmo at the same time?</summary>

Both can be installed, but do not point them at the same sensors: you would
have two systems deciding what an open window means, arming and disarming
independently of each other. Try Foyer on a few zones, or on a test
installation, and move the rest when it has earned it.

</details>

<details>
<summary>Who can disarm it?</summary>

Whoever holds a code, and only for what their permissions allow. Until you
create the first user, nobody is asked for anything and anyone with access to
Home Assistant can disarm — the panel says so plainly while that lasts. A
person can be exempted from typing their code on channels that already know who
they are, such as the Home Assistant interface signed in as them; on a shared
keypad the code *is* the identity, so the exemption cannot apply there.

</details>

<details>
<summary>Does it work without internet?</summary>

Yes. Foyer makes no outbound connection of its own, and needs no cloud account
and no broker. Whether your *notifications* survive a cut line is a different
question, and the honest answer is that a push notification does not — which is
why escalation across channels is on the roadmap, and why a local channel is
worth having.

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

Its configuration, its saved alarm state and its entities go with it. The event
log database is deliberately left on disk: whether to delete thirty days of
history is a question you should be asked, and being asked it properly is on
the roadmap.

</details>

<details>
<summary>Is it available in my language?</summary>

English and Italian today, panel, card and contextual help included. Adding a
language touches no code: copy two JSON files, translate, open a pull request.
CI fails if the two files' key sets differ, so a half-translated panel cannot
ship.

</details>

## If something goes wrong

Open an [issue](https://github.com/foyer-labs/Foyer-Home-Defender/issues). Say
which version of Foyer and of Home Assistant, what you expected, and what the
log page shows — the row usually contains the answer, so a screenshot of it is
worth more than a description. English or Italian, whichever you prefer.

To be told when the simulator lands, watch the repository: releases are
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
tests/core, tests/repo     run without Home Assistant installed
tests/ha                   run inside Home Assistant's test harness
```

```bash
pip install pytest ruff
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
the fix is the code, never the test.

The whole design, including the reasoning behind decisions that look arbitrary
until you know why, is in
[docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md).

## Licence

Apache-2.0. See [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) and [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
