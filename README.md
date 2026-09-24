<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><strong>English</strong> · <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.it.md">Italiano</a></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center"><em>An intruder alarm panel for the sensors you already have in Home Assistant — with a simulator that tells you what it would do before you trust it.</em></p>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?sort=semver&include_prereleases&label=version" alt="Latest version"></a>
  <img src="https://img.shields.io/badge/status-release%20candidate-yellow" alt="Release candidate">
  <img src="https://img.shields.io/badge/Home%20Assistant-2026.6%2B-41BDF5" alt="Home Assistant 2026.6 or later">
  <img src="https://img.shields.io/badge/HACS-custom%20repository-41BDF5" alt="HACS custom repository">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licence-Apache--2.0-blue" alt="Apache-2.0"></a>
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml"><img src="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
</p>

The door contact that switches on the hall light and the motion sensor that
runs the night light are the sensors a burglar alarm is made of. Foyer turns
them into one: areas that arm on their own, arming scenarios you name
yourself, a response that keeps looking for somebody until they answer — and
a way to check all of it without setting anything off.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-en.png" alt="The Foyer panel: two areas armed by one scenario, one counting down its entry delay, the zones that are not ready, and the last few events" width="900">
</p>

## What you get

- **Areas and scenarios of your own.** Each area arms on its own and has its
  own alarm panel entity; *Night, ground floor only*, *Garage only* or *Dog at
  home* is a scenario, as many as the house needs.
  [Getting started](docs/getting-started.md)
- **Zones that say what "triggered" means.** Normally-closed and normally-open
  contacts behave in opposite ways, so every zone's trigger is confirmed
  against the real sensor, and a sensor that goes `unavailable` is a fault,
  never "all quiet". [Zones](docs/zones.md)
- **Ask before you trust.** A simulator that rehearses a night without
  anything happening, a walk test that shows which zones never saw you, and a
  test button that really sounds the siren. [Simulator](docs/simulator.md)
- **One incident per break-in, and a notification that keeps looking.** The
  window, the hall and the stairs become one incident with one
  acknowledgement; push now, SMS in a minute, a second person after that,
  until somebody answers. [Response profiles](docs/response-profiles.md) ·
  [Notification channels](docs/notification-channels.md)
- **A code for each person, checked in the backend only.** Permissions per
  person, a duress code that works as the ordinary one and raises a silent
  alarm, a lockout after repeated wrong codes, and a log that names who did
  what. [Security model](docs/security-model.md)
- **Keypads, tags and devices of your own.** Ring and Zigbee keypads, NFC tags
  and remotes, over services, MQTT or Foyer's own HTTP endpoint, with a
  refusal that says which zone is open. [Keypads](docs/keypads.md)
- **Smoke, gas and water on a separate channel.** Live whether the house is
  armed or not, and never reported as a break-in. [Zones](docs/zones.md#the-technical-channel)
- **A house that arms itself when everybody leaves**, after a countdown you
  can cancel. Automatic disarming is off by default and never touches the
  perimeter. [Automatic rules](docs/automation-rules.md)
- **An alarm that says when it has stopped working.** Mains power, every
  notification channel, an external watchdog and radio interference.
  [System health](docs/system-health.md)
- **A log of its own, thirty days by default**, with the tools to hand
  somebody their data or take them out of it. [Privacy](docs/privacy.md)
- An existing Alarmo configuration can be brought across.
  [Migrating from Alarmo](docs/migrating-from-alarmo.md)

<table>
  <tr>
    <td width="50%"><img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-zone-en.png" alt="The zone editor asking which states count as triggered, and requiring confirmation against the real sensor"></td>
    <td width="50%"><img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-walktest-en.png" alt="A walk test running: a banner saying every response is held back and what stays live, and the zone that never reacted at the top of the table"></td>
  </tr>
</table>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-en.png" alt="The card in its full and compact layouts during an entry delay: every area with its state, the countdown, and the keypad that opens by itself because disarming asks for a code" width="420">
</p>

## Before you install

> Foyer is offered as software that automates actions on rules, not as an
> alarm system. It is not certified (EN 50131, CEI 79-3), not monitored, not a
> fire alarm, and comes with no warranty and no promise of support
> (Apache-2.0, sections 7 and 8). Do not rely on it alone to protect people or
> property: keep certified smoke alarms, and a professional installation where
> a policy or a risk calls for one.

Setting Foyer up asks you to tick that you have read it.

## Get started

You need Home Assistant 2026.6 or later, one door, window or motion sensor
that already works, and a working `notify.*` service. No cloud account, and
no broker unless a device of yours speaks MQTT.

1. In HACS, add this repository as a *Custom repository*, category
   *Integration*, install *Foyer Home Defender* and restart Home Assistant.
2. *Settings → Devices & services → Add integration → Foyer Home Defender*:
   accept the text above, then confirm the states in which your first zone
   counts as triggered.
3. Open **Foyer** in the sidebar: a five-step wizard finishes the setup.

[Getting started](docs/getting-started.md) covers the manual install, the
wizard and the first fifteen minutes; [the card](docs/card.md) puts the alarm
on a dashboard.

## Security in one paragraph

Foyer's codes protect against household members, guests, cleaners, non-admin
Home Assistant users and anyone who finds an unlocked wall tablet. They do
**not** protect against a Home Assistant administrator, who can read
`.storage`, disable the integration or call any service directly — which is
also why the log is audit-useful rather than tamper-proof. Whoever may start a
walk test may keep an armed house quiet until it ends, so that permission is
given as *Disarm* is. Foyer is not a certified alarm system, and not a fire
alarm system. [The security model](docs/security-model.md) says the rest.

## Documentation

| | |
|---|---|
| [Getting started](docs/getting-started.md) | Install, the wizard, the first fifteen minutes, the Overview |
| [Zones, areas and scenarios](docs/zones.md) | Triggers, NC and NO contacts, delays, arm policies, verification groups, the technical channel |
| [Response profiles](docs/response-profiles.md) | What happens, when, and why it sounded |
| [Notification channels](docs/notification-channels.md) | Recipes, from the Companion app to a GSM modem |
| [Security model](docs/security-model.md) | What codes protect against, and what they do not |
| [Simulator](docs/simulator.md) | Diagnostics, the simulator, the walk test and the action test |
| [All documents](docs/README.md) | Keypads, automatic rules, system health, resilience, privacy, settings, the card, troubleshooting, FAQ… |

## Status

Release candidate for 1.0: it becomes 1.0.0 once people other than its
author have used it for some weeks without a serious problem. Foyer is the
personal, non-commercial project of one person, published
as Foyer Labs; there is no company behind it. Every release is an ordinary
GitHub release that HACS offers by version. The stored configuration carries a schema
version and is migrated forward on update, and the
[changelog](CHANGELOG.md) says what changed in behaviour, release by release.
What comes next, and what each step has to prove, is in
[the roadmap](docs/SPEC.md#16-roadmap); watch the repository to be told when a
release lands.

## Contributing, security, licence

Issues and pull requests are welcome, in English or Italian, and are
answered on a best-effort basis, with no promise of a reply or a fix
([SUPPORT.md](SUPPORT.md));
[CONTRIBUTING.md](CONTRIBUTING.md) explains the development setup and the one
rule never bent, and adding a language touches no code. A security problem
belongs in a [private advisory](https://github.com/foyer-labs/Foyer-Home-Defender/security/advisories/new),
not an issue — see [SECURITY.md](SECURITY.md).

<p align="center">
  <a href="https://www.buymeacoffee.com/foyerlabs" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-green.png" alt="Buy Me a Coffee" height="60"></a>
</p>

A donation is a thank-you and buys neither support nor priority.

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
