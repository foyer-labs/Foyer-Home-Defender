# Documentation

**English** · [Italiano](README.it.md)

Every document about using Foyer Home Defender, one line each, and the panel
page whose *Learn more* link opens it. The design itself, with the reasoning
behind every decision, is in [SPEC.md](SPEC.md).

## Starting

| Document | What it covers | Panel page |
|---|---|---|
| [Getting started](getting-started.md) | Requirements, install, the config flow, the first-run wizard, the first fifteen minutes, the Overview | *Overview* |
| [The card](card.md) | `foyer-card`: its four layouts, how it asks for a code, what it shows during a delay, an alarm and a walk test | — |
| [Questions people ask](faq.md) | Who can disarm, Home Assistant's own cards and voice assistants, the administrator with no code, working without internet | — |
| [Migrating from Alarmo](migrating-from-alarmo.md) | What the importer converts, what it cannot, and what to check afterwards | — |

## Setting it up

| Document | What it covers | Panel page |
|---|---|---|
| [Zones, areas and scenarios](zones.md) | Zone types, triggers, NC and NO contacts, delays, arm policies, exclusions, supervision, the technical channel, chime, verification groups | *Areas*, *Zones*, *Scenarios*, *Verification groups* |
| [Response profiles](response-profiles.md) | Which profile answers, moments, incidents, actions, conditions, templates, pictures, escalation | *Response profiles* |
| [Notification channels](notification-channels.md) | Recipes: Companion app, Pushover, Twilio SMS and voice, a GSM modem, Telegram, Signal; answering a duress code | *Contacts* |
| [Security model](security-model.md) | What codes protect against and what they do not, permissions, the duress code, credentials, what an administrator can do | *Users* |
| [Keypads, tags and remotes](keypads.md) | The service, MQTT and HTTP contracts, API devices, the shipped adapters, the hardware | *Arming devices*, *API* |
| [Automation rules](automation-rules.md) | Arming on presence, time or an entity; guards, suspensions, and why automatic disarming is restricted | *Automatic rules* |
| [Settings](settings.md) | Global defaults, the log, backup and restore, the language of messages, removing the integration | *Settings* |

## Checking it, and living with it

| Document | What it covers | Panel page |
|---|---|---|
| [Simulator](simulator.md) | Diagnostics, the simulator and its decision trace, the walk test, the action test | *Test & diagnostics* |
| [System health](system-health.md) | Mains power, notification channels, the external watchdog, radio interference, repair issues, diagnostics | *System health* |
| [Resilience](resilience.md) | What survives a power cut or a cut fibre, and the four things that help | — |
| [Privacy](privacy.md) | What the log contains, the household exemption and where it stops, erasing and exporting a person | *Log* |
| [Troubleshooting](troubleshooting.md) | A zone that never triggers, false alarms, faults, the refusals people meet, opening an answerable issue | — |

## Hardware

| Document | What it covers |
|---|---|
| [Choosing sensors](choosing-sensors.md) | What makes a sensor fit for an alarm rather than for automation |
| [Reusing existing sensors](reusing-existing-sensors.md) | Bringing an existing alarm's sensors into Home Assistant, and the caveats |

## The project

| Document | What it covers |
|---|---|
| [Visual identity](brand.md) | The mark, the palette, the asset set |
| [API contract](api/openapi.yaml) · [MQTT contract](api/asyncapi.yaml) | The device endpoint and the MQTT messages, version v1 |
| [Support](../SUPPORT.md) | What to expect from an issue: best effort, with no promise of an answer or a fix |
| [Contributing](../CONTRIBUTING.md) · [Security policy](../SECURITY.md) · [Changelog](../CHANGELOG.md) | How to contribute, how to report a vulnerability, what changed in each release |

Every document above is in English and Italian. The design (SPEC), the API
contracts and the project files — support, contributing, security policy,
changelog — are in English only.
