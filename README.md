<p align="center">
  <img src="docs/logo/foyer-hd-lockup-light-bg.png" alt="Foyer Home Defender" width="360">
</p>

# Foyer Home Defender

Foyer Home Defender turns Home Assistant into a real intruder alarm panel: areas
with their own armed state, user-defined arming scenarios, zone semantics, a
response engine, identified users, physical keypads, an auditable event log, and
a simulator that lets you check the configuration before you trust it.

> **Status: Phase 0 — walking skeleton. This does not protect anything yet.**
> It wires one area, one zone, one scenario and one action end to end, to prove
> the technical chain: config flow → stored configuration → pure decision engine
> → `alarm_control_panel` entity → sidebar panel and Lovelace card. There are no
> users or codes: **anyone who can reach Home Assistant can disarm it.** Alarm
> state is not kept across a restart yet; after a restart the area is disarmed.
> Do not rely on it.

The full design is in [docs/SPEC.md](docs/SPEC.md).

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
   Name the area and the scenario, pick the zone entity, then confirm the states
   in which it counts as triggered. Check them against the real sensor: open the
   door, walk past the sensor, and watch its state.
4. A **Foyer** entry appears in the sidebar. To add the card to a dashboard, pick
   *Foyer Home Defender* in the card picker, or use:

   ```yaml
   type: custom:foyer-card
   entity: alarm_control_panel.foyer_<area>
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

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
