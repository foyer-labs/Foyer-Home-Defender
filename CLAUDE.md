# Foyer Home Defender — working agreement

A Home Assistant custom integration that turns Home Assistant into a real intruder
alarm system: areas with independent state, user-defined arming scenarios, zone
semantics, a response engine, identified users, physical keypads, an auditable log,
and a simulator that lets the configuration be verified before it is trusted.

Apache-2.0. Code, entities, services and documentation in English; the UI is fully
localised (en, it) from day one.

## Read this first, every session

**`docs/SPEC.md` is the source of truth.** Read it in full before writing any code
— all of it, not the parts that look relevant. It is long on purpose: it carries
the reasoning behind decisions that look arbitrary until you know why.

`docs/PROMPTS.md` holds the phase prompts. Do not work from it unprompted: each
session is given exactly one phase, and doing work from a later phase is a defect
even when it is one line away.

`docs/panel-prototype.html` is a navigable mockup of every panel page. Open it
before building UI.

## The six invariants

These are not style preferences. Each one, if broken, disables a headline feature
and needs a rewrite rather than a patch.

**INV-1 — `core/` is pure.**
`decide(snapshot, event, config, now) -> Decision` executes nothing, performs no
I/O, reads no clock it was not given, and imports nothing from `homeassistant.*`.
A separate executor performs side effects; a separate scheduler owns timers. This
is what makes the simulator structurally honest instead of hopeful. CI enforces the
import rule — if that test fails, the fix is the code, never the test.

**INV-2 — Codes are verified in the backend only.**
Every service and every WebSocket command that changes state or configuration
validates the code server-side. Cards transmit a code; they never decide. A PIN
check in the frontend is decoration — anyone with Home Assistant access calls the
service directly from Developer Tools.

**INV-3 — State survives restarts.**
Area states, active scenario, bypasses, pending timers and escalation progress are
persisted and restored. The restart gap is logged explicitly, so the log never
implies the house was covered when it was not.

**INV-4 — `unavailable` is a fault, never "all quiet".**
An entity that is unavailable, unknown, or past its supervision window is a fault:
it blocks arming, raises an event, and is visible in diagnostics. It is never
silently treated as "closed" or "no motion".

**INV-5 — Never assume `on` means alarm.**
Every zone declares its own trigger state. NC and NO contacts behave in opposite
ways, and a wrong default produces an alarm that never fires — discovered too late.

**INV-6 — The threat model is stated, not implied.**
The README says plainly what codes protect against and what they do not, and that
Foyer is neither a certified alarm system nor a fire alarm system.

## How to work here

- One phase per session. Do not implement anything belonging to a later phase.
- Branch per phase. Small, working commits; messages say *why*, not *what*.
- Tests alongside the code for anything in `core/`. `core/` must be testable with
  no Home Assistant instance running.
- **If the spec is ambiguous or self-contradictory, stop and ask.** Do not choose
  and carry on. An ambiguity resolved silently in a security system is how a wrong
  assumption ends up buried under a thousand lines.
- Configuration is UI-only. No YAML schema — that would mean maintaining two
  configuration paths.
- No user-visible string is hard-coded in a component; everything goes through
  `translations/`. CI fails when `en.json` and `it.json` key sets diverge.
- At the end of a session, report three things: what you built, what you did not
  build and why, and anything in the spec you believe is wrong.

## Things that are easy to get wrong here

- The technical channel (smoke, gas, flood) is **not** the intrusion channel. It
  never touches `alarm_control_panel`, it is live regardless of arming, and
  disarming does not clear it. `triggered` on an alarm panel entity means
  *burglary* to HomeKit, Google and Alexa.
- Alarms are grouped into **incidents**, not handled per zone. A real break-in
  trips several zones; three parallel escalations is phone spam at the worst
  possible moment.
- Cross-zone verification and N-of-M groups are **one engine**, two ways to
  configure it. A test asserts the two paths give identical results.
- Automatic disarming can never act on an area flagged `is_perimeter`. Enforced in
  the engine, not in the UI, with a regression test that asserts it directly.
- The external watchdog heartbeat carries **no payload** by default. A ping saying
  "armed, nobody home" tells a third party when the house is empty.
