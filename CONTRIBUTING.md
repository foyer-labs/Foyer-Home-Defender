# Contributing to Foyer Home Defender

Thank you for looking. This page says how the project is built, what a change
has to carry to be merged, and — because it is the contribution that needs no
Python at all — exactly how to add a language.

## Before you start

Foyer is a beta with one author. There is no promised turnaround on issues or
pull requests: everything gets read, and some of it takes a while. For anything
bigger than a small fix, open an issue first and say what you have in mind, so
that neither of us spends an evening on something that collides with the
design.

The design is written down in [docs/SPEC.md](docs/SPEC.md), with the reasoning
behind the decisions that look arbitrary until you know why. It is long on
purpose. If a change contradicts it, the pull request is the place to say so
and why — the specification has been wrong before, and a numbered decision log
at the end records every time it changed its mind.

## Licence of a contribution

Foyer is Apache-2.0. A contribution you submit is licensed under the same
terms, as section 5 of the [licence](LICENSE) already provides: there is no
separate agreement to sign and no sign-off line to add. Submit only what you
have the right to submit.

## The rule that is never bent: `core/` is pure

`custom_components/foyer/core/` decides what should happen and does nothing
else. `decide(snapshot, event, config, now)` returns a `Decision`; it performs
no I/O, reads no clock or random source it was not handed, and imports nothing
from `homeassistant`. A separate executor performs the side effects and a
separate scheduler owns the timers.

This is not tidiness. It is what makes the simulator truthful: the simulator is
the same `decide()` called with a made-up world and a made-up clock, and it
fires nothing because the engine cannot fire anything. An engine that reached
for Home Assistant would make every simulation either a lie or a real siren.

`tests/core/test_purity.py` enforces it, and the CI job that runs the pure
suite has no Home Assistant installed at all. **If that test fails, the fix is
the code, never the test.**

The same holds for the pure halves of `store/` (schema, migrations, editing)
and for `security/`: they are listed in the purity test and exercised by the
pure suite.

## Where things are

```
custom_components/foyer/   the integration (HACS installs this directory as is)
  core/                    pure decision engine: no Home Assistant imports, ever
  runtime/ entity/ api/    Home Assistant-facing layers
  security/                bcrypt codes, and who a request comes from
  store/                   .storage persistence, schema migrations, the log
  translations/            en.json, it.json (Home Assistant) and panel/ (UI, help)
  frontend/                built panel and card bundles, committed
frontend/                  TypeScript + Lit sources, built with Vite
blueprints/                keypad and tag adapters (imported by hand, not by HACS)
scripts/                   build helpers, such as the icon generator
docs/                      the specification, the user documents, the API contracts, screenshots
tests/core, tests/repo     run without Home Assistant installed
tests/ha                   run inside Home Assistant's test harness
```

## Development setup

You need Python 3.12 or later and, for the panel and the card, Node 24.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux, macOS: source .venv/bin/activate
pip install pytest bcrypt ruff tzdata   # tzdata: Windows has no time zone database
pytest                                  # the pure suite: engine, stores, translations
ruff check . && ruff format --check .
```

The integration tests run inside Home Assistant's own test harness, which needs
Linux (WSL works) and the Python Home Assistant itself requires — 3.14 for the
2026.6 floor:

```bash
pip install pytest-homeassistant-custom-component
pytest -p pytest_homeassistant_custom_component -o asyncio_mode=auto \
  -o asyncio_default_fixture_loop_scope=function tests/ha
```

Foyer depends on Home Assistant's `frontend` integration, so the harness also
needs the `home-assistant-frontend` package at the version Home Assistant pins
in its frontend `manifest.json`. `.github/workflows/ci.yml` shows how CI
installs it, and the older pins the lowest supported version needs.

The frontend lives in `frontend/` and builds into
`custom_components/foyer/frontend/`, which is committed because HACS installs
that directory as it is:

```bash
cd frontend
npm ci
npm run build
```

CI checks that the committed bundles match the sources, so rebuild and commit
them with any frontend change.

**Do not run Prettier on this repository.** It is not Prettier-formatted, and
the default width rewrites every frontend file. `ruff format` is the formatter
for Python, and CI checks it.

## What a pull request has to carry

- **A change to `core/` comes with a test in `tests/core/`** that runs with no
  Home Assistant installed. The engine is the part of this project a house
  leans on; a behaviour nobody wrote down as a test is a behaviour the next
  change is free to break.
- **A change to the Home Assistant layer** — entities, services, WebSocket
  commands, the executor — comes with a test in `tests/ha/` where one is
  practical.
- **No word a person reads is written in code.** Every string in the panel,
  the card, the help panels and the notifications comes from
  `custom_components/foyer/translations/`, in English and in Italian. The
  backend returns stable identifiers and the frontend turns them into words.
  CI fails if the language files carry different keys; a key built at run
  time, such as `state.${x}`, is checked only loosely, so check it by hand.
- **A code is verified in the backend only.** A change that checks a code, a
  permission or a policy in the panel or the card is decoration: anybody with
  Home Assistant access can call the service directly.
- **Commit messages say why.** The diff already says what changed.
- **A change in behaviour is in `CHANGELOG.md`**, in words a household can use
  to decide whether to take the update.

A defect that lets somebody disarm without a code, keep the alarm quiet when it
should sound, or read what should not be readable is not a pull request to
open in public. [SECURITY.md](SECURITY.md) says where it goes.

## Adding a language

No code, and no Python needed. A language is two files:

| File | What it holds |
|---|---|
| `custom_components/foyer/translations/<code>.json` | What Home Assistant itself shows: the setup dialog, entity names, errors, repair issues |
| `custom_components/foyer/translations/panel/<code>.json` | Everything else: the panel, the card, the help panels, and the notifications Foyer sends |

`<code>` is Home Assistant's own code for the language — `es`, `fr`, `de`,
`pt-BR`, as in the file names under Home Assistant's own translations.

1. Copy `translations/en.json` to `translations/<code>.json`, and
   `translations/panel/en.json` to `translations/panel/<code>.json`.
2. Translate the **values**, never the keys. Leave anything in braces exactly
   as it is — `{zone}`, `{rows}`, `{area}` are filled in when the text is
   shown, and a translated placeholder is a hole in the sentence.
3. Set `language.self` in the panel file to the language's name in itself —
   `Español`, not `Spanish`. It is what appears in the list of languages
   Foyer can send its messages in, on the Settings page.
4. Run the translation checks, if you can:

   ```bash
   pip install pytest bcrypt tzdata
   pytest tests/repo/test_translations.py
   ```

   They fail if a key is missing or extra, if a placeholder differs from the
   English one, if a string is empty, or if one of the two files is missing.
5. Open a pull request with both files. CI runs the same checks and tells you
   what you missed, if anything. Home Assistant's own validator reads only the
   English file of a custom integration, so these tests are what stands
   between a new language and a missing key.

The panel follows each Home Assistant user's own language automatically, and
falls back to English for a language it does not have. Once the files are in,
somebody whose Home Assistant speaks Spanish sees Foyer in Spanish without
touching a setting.

A partial translation is not something CI will let through, on purpose: a
panel that is half in one language and half in another hides exactly the
sentence that explains a setting. If you only have time for part of it, open
the pull request as a draft and say so.
