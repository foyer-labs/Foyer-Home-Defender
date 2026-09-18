<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><strong>English</strong> · <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.it.md">Italiano</a></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?include_prereleases&sort=semver&label=version" alt="Latest version"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant 2025.1 or later">
  <img src="https://img.shields.io/badge/HACS-custom%20repository-41BDF5" alt="HACS custom repository">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licence-Apache--2.0-blue" alt="Apache-2.0"></a>
</p>

Foyer Home Defender turns Home Assistant into a real intruder alarm panel: areas
with their own armed state, arming scenarios you define yourself, zones that say
what "triggered" means for them, a response engine, an auditable event log, and —
in later phases — identified users, physical keypads and a simulator that lets
you check the configuration before you trust it.

> ### Status: Phase 1 complete — the alarm core
>
> A house can be protected with it. Think twice before it is the *only* thing
> protecting one: **there are no users and no codes yet**, so anyone who can
> reach Home Assistant can disarm it. Codes arrive in the next phase.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-en.png" alt="The Foyer panel: two areas armed by one scenario, one counting down its entry delay, and the zones that are not ready" width="900">
</p>

## What it does today

- **Areas with their own armed state**, each with its own
  `alarm_control_panel` entity, plus a master that aggregates them.
- **Scenarios you define**: *Night, ground floor only*, *Garage only*, *Dog at
  home*. Not four fixed modes.
- **Zones that declare their own trigger.** Normally-closed and normally-open
  contacts behave in opposite ways; Foyer proposes a trigger from the entity's
  device class and makes you confirm it, because a wrong guess produces an
  alarm that never fires.
- **Eight zone presets** over editable properties: instant, delayed, follower,
  24h, tamper, technical, panic, and key zones that arm or disarm instead of
  alarming.
- **Exit and entry delays**, four arm policies for a zone that is open when you
  arm (block, exclude it, wait for it to close, ignore), forced arming, manual
  and timed exclusion, a siren cutoff with alarm memory.
- **A separate channel for smoke, gas and water.** It is live whether the house
  is armed or not, it never touches `alarm_control_panel` — where *triggered*
  means "burglary" to HomeKit, Google and Alexa — and disarming does not clear
  it.
- **Incidents, not per-zone alarms.** A real break-in trips several zones; they
  become one incident, with one acknowledgement, instead of three sets of
  notifications at the worst possible moment.
- **Verification groups**, N of M within a window, with the members keeping
  their own response: one detector notifies, two sound the siren.
- **Response profiles**: ten actions — notification, siren, light, camera,
  scene, switch, spoken message, call any Home Assistant service, wait — each
  with up to two conditions, inherited area → scenario → default.
- **Chime** when a zone opens while its area is not watching it, to a speaker,
  a siren or a phone, with quiet hours per target.
- **An event log** in a database of Foyer's own, which the Home Assistant
  recorder's ten-day purge cannot touch: what happened, where, through which
  channel, whether each action actually worked, and who changed what.
- **State that survives a restart**, including a running delay and a sounding
  siren — and the gap itself is recorded, so the log never implies the house
  was covered when it was not.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-log-en.png" alt="The log page: arming, an alarm, a refused arming that names the zone, the restart gap, and a notification that failed" width="900">
</p>

## Not yet, and it matters

- **No users, no codes, no permissions.** Anyone with access to Home Assistant
  can arm and disarm, and the log records the channel rather than the person.
  Phase 2.
- **No simulator and no walk test.** You cannot yet ask "what would happen if
  the kitchen window opened right now?" without opening it. Phase 3.
- **No escalation.** Notifications go to a `notify` service directly; they do
  not climb from push to SMS to a phone call until somebody acknowledges.
  Phase 4.
- **No keypad support, no MQTT.** Phase 2.

The full design, including the phases, is in
[docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md);
what changed in each release is in
[CHANGELOG.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CHANGELOG.md).

## Next to Alarmo

[Alarmo](https://github.com/nielsfaber/alarmo) is the reference implementation
in this space, and a good one: arming modes, per-sensor delays, an action
engine, users with codes, MQTT and a Lovelace card. Foyer is written from
scratch and does not copy its code. It aims at three things Alarmo does not do:

| | Foyer | Alarmo |
|---|---|---|
| **Arming scenarios** | Any number, each arming a chosen set of areas — *ships today* | Home Assistant's four fixed modes |
| **Simulator and walk test** | Planned, Phase 3: the same engine, a fabricated clock, nothing executed | — |
| **Escalation with acknowledgement** | Planned, Phase 4: push, then SMS, then a call, stopping when a human answers | — |

Alarmo is a finished, widely used integration; Foyer is an alpha. If you need an
alarm today and codes matter to you, use Alarmo.

## Security model

Foyer's codes — once they exist — protect against household members, guests,
cleaners, non-admin Home Assistant users and anyone who finds an unlocked wall
tablet. They do **not** protect against a Home Assistant administrator, who can
read `.storage`, disable the integration or call any service directly. The event
log is audit-*useful*, not tamper-*proof*, for the same reason.

**Foyer is not a certified alarm system**, and **it is not a fire alarm
system**: a smoke detector wired into Home Assistant does not replace certified,
interconnected smoke alarms.

## Install

1. In HACS, open the menu → *Custom repositories*, add this repository's URL
   with category *Integration*.
2. Install *Foyer Home Defender* and restart Home Assistant.
3. *Settings → Devices & services → Add integration → Foyer Home Defender*.
   Name the first area and scenario, pick the first zone entity, then confirm
   the states in which it counts as triggered. Check them against the real
   sensor: open the door, walk past the detector, watch its state.
4. A **Foyer** entry appears in the sidebar, and a short wizard finishes the
   setup: more zones, the scenario, and a test notification so you know the
   channel works.

Requires Home Assistant 2025.1 or later.

> **While Foyer is in alpha, every release is published as a GitHub
> pre-release**, and HACS shows the commit rather than the version number for
> repositories that have none marked stable. To see and pick the version names,
> enable the *pre-release* switch entity HACS creates for this repository
> (*Settings → Devices & services → Entities*, search for "pre release"; it is
> disabled by default). From the first beta, releases will be published
> normally.

### The card

Pick *Foyer Home Defender* in the dashboard's card picker, or write it by hand:

```yaml
type: custom:foyer-card
entity: alarm_control_panel.foyer_master   # or alarm_control_panel.foyer_<area>
layout: full                               # or compact
```

The card is loaded automatically; no dashboard resource needs adding. It decides
nothing by itself: it sends a command and renders the answer, including the name
of the zone that refused it.

> **If the card is missing from the picker**, or a dashboard says *Custom
> element doesn't exist: foyer-card*, **reload the page once** with
> Ctrl+Shift+R (Cmd+Shift+R on a Mac). Home Assistant writes the card's script
> tag into the page it renders, so a page that was loaded before Foyer was
> installed — or before it was updated — does not have it, and reconnecting
> after a restart does not fetch a new one. In the companion app, reset the
> frontend cache from its own settings, or close and reopen the app.
> To check that the file itself is there, open
> `https://<your-home-assistant>/foyer_static/foyer-card.js`: it should show
> JavaScript.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-en.png" alt="The card in its full and compact layouts" width="900">
</p>

## Development

```
custom_components/foyer/   the integration (HACS installs this directory as is)
  core/                    pure decision engine: no Home Assistant imports, ever
  runtime/ entity/ api/    Home Assistant-facing layers
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

`core/` must never import `homeassistant`: it is what keeps the decision engine
a pure function, and therefore what will make the simulator's trace truthful.
CI enforces it; if that check fails, the fix is the code, never the test.

To add a language, copy `translations/en.json` and `translations/panel/en.json`
to the new language code, translate, and open a pull request. CI fails if the
key sets differ.

## Licence

Apache-2.0. See [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) and [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
