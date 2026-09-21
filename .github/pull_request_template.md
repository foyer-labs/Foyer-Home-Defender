## Why

<!-- What was wrong, or what was missing, and how you found it. The diff says what changed. -->

## Checklist

- [ ] A change under `custom_components/foyer/core/` comes with a test in `tests/core/` that runs without Home Assistant.
- [ ] Any text a person reads is in both `translations/panel/en.json` and `translations/panel/it.json` (or the Home Assistant files), never in a component or in Python.
- [ ] `ruff check .` and `ruff format --check .` pass. Prettier has **not** been run.
- [ ] If the frontend changed, `npm run build` was run and the rebuilt bundles are committed.
- [ ] If behaviour changed, `CHANGELOG.md` says so in words a household can use to decide whether to take the update.
