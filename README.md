<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><strong>English</strong> · <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.it.md">Italiano</a></p>

# Foyer Home Defender

Foyer Home Defender turns Home Assistant into a real intruder alarm panel: areas
with their own armed state, user-defined arming scenarios, zone semantics, a
response engine, identified users, physical keypads, an auditable event log, and
a simulator that lets you check the configuration before you trust it.

> **Status: Phase 1 in progress — the alarm core. Not yet something to rely on.**
> Areas, zones, scenarios, verification groups and response profiles are
> configured from the sidebar panel. The state machine has exit and entry
> delays, instant, delayed, follower, 24h, tamper and panic zones, arm
> policies, forced arming, manual and timed exclusion of a zone, a siren cutoff
> with alarm memory, and alarm state that survives a restart. Smoke, gas and
> water run on their own channel, which disarming cannot silence. An alarm now
> sounds sirens, flashes lights, records a camera and sends notifications.
> What is still missing matters: there is **no event log**, so the panel cannot
> yet tell you what happened last night; notifications go to one service and do
> not escalate until somebody answers; and there are no users or codes, so
> **anyone who can reach Home Assistant can disarm it.**

The full design is in [docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md).

## Prior art, and how Foyer differs

[Alarmo](https://github.com/nielsfaber/alarmo) is the reference implementation
in this space, and a good one: arming modes, per-sensor delays, an action engine,
users with codes, MQTT and a Lovelace card. Foyer is written from scratch and does
not copy its code. It aims at three things Alarmo does not do:

- **Unlimited user-defined scenarios.** Alarmo is bound to Home Assistant's four
  fixed arm modes. Real houses need "Night, ground floor only", "Garage only",
  "Dog at home".
- **A simulator and a walk test.** Answer "what would happen if the kitchen
  window opened now, in this scenario, at this hour?" without opening it.
- **Escalation with acknowledgement.** Notifications that escalate across
  channels and people until a human acknowledges.

None of these exist yet. They arrive in later phases (SPEC §16).

## Security model

Foyer's codes protect against household members, guests, cleaners, non-admin
Home Assistant users and anyone who finds an unlocked wall tablet. They do
**not** protect against a Home Assistant administrator, who can read
`.storage`, disable the integration or call any service directly. Foyer is not
a certified alarm system.

Codes arrive in Phase 2. Until then there is nothing to protect against anyone.

**Foyer is not a fire alarm system.** A smoke detector wired into Home Assistant
does not replace certified, interconnected smoke alarms.

## Install (custom HACS repository)

1. In HACS, open the menu → *Custom repositories*, add this repository's URL
   with category *Integration*.
2. Install *Foyer Home Defender* and restart Home Assistant.
3. *Settings → Devices & services → Add integration → Foyer Home Defender*.
   Name the first area and scenario, pick the first zone entity, then confirm the
   states in which it counts as triggered. Check them against the real sensor:
   open the door, walk past the sensor, and watch its state.
4. A **Foyer** entry appears in the sidebar. Add the other areas, zones and
   scenarios there (administrators only). To add the card to a dashboard, pick
   *Foyer Home Defender* in the card picker, or use:

   ```yaml
   type: custom:foyer-card
   entity: alarm_control_panel.foyer_<area>   # or alarm_control_panel.foyer_master
   ```

   The card is loaded automatically; no dashboard resource needs adding.

Requires Home Assistant 2025.1 or later.

## Development

```
custom_components/foyer/   the integration (HACS installs this directory as is)
  core/                    pure decision engine: no Home Assistant imports, ever
  runtime/ entity/ api/    Home Assistant-facing layers
  store/                   .storage persistence and schema migrations
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

To add a language, copy `translations/en.json` and `translations/panel/en.json`
to the new language code, translate, and open a pull request. CI fails if the
key sets differ.

## Licence

Apache-2.0. See [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) and [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
