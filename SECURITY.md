# Security policy

Foyer Home Defender is an intruder alarm. A defect in it is not a bug report
like any other: it is somebody's house standing open while they believe it is
not. This page says how to tell the author about one, and — just as
importantly — what this software does not claim to defend against, so that
nobody spends time on an attack that is already documented as out of scope.

## Reporting a vulnerability

Use GitHub's **private vulnerability reporting**:
[open a private advisory](https://github.com/foyer-labs/Foyer-Home-Defender/security/advisories/new).
It is enabled on this repository, the report is visible only to the
maintainers, and it keeps the discussion in one place until there is a fix.

Please do not open a public issue for anything in the list below. Everything
else — a crash, a wrong translation, an entity that does not appear — belongs
in an ordinary issue, where more people can help.

What helps most in a report: the version, what you expected the alarm to do,
what it did, and the smallest configuration that shows it. The diagnostics
download is anonymised and is usually enough.

**In scope**, roughly in order of how much they matter:

- arming, disarming or acknowledging **without the code the policy requires**,
  or on an area or scenario the person is not allowed;
- making the alarm **stay quiet** when it should sound: an alarm that can be
  suppressed from outside, a notification that can be stopped by somebody who
  should not be able to stop it, a way to disarm a **perimeter** area from an
  automatic rule;
- **reading what should not be readable**: a code or its hash in an API
  response, a log row, an event, the diagnostics download or a backup;
- defeating the **lockout** of repeated wrong codes, or the rule that a device
  must be declared before it may command anything;
- anything that lets a **non-administrator** Home Assistant user do what the
  configuration says only an administrator may.

**Out of scope**, deliberately and permanently:

- **A Home Assistant administrator.** They can read `.storage`, disable the
  integration, call any service and delete the log database. Foyer's codes
  protect against household members, guests, cleaners, non-admin Home
  Assistant users and whoever finds an unlocked wall tablet. They do not
  protect against the person who owns the installation, and no version of
  Foyer will claim otherwise.
- **Anything that needs physical access to the Home Assistant host.**
- **The transports.** Foyer orchestrates `notify.*` services; what a push, an
  SMS or a voice call does with a message belongs to that integration.
- **The acknowledgement webhook, when you have switched it on.** It is an
  unauthenticated URL by design — that is how a voice provider feeds a DTMF
  keypress back — so whoever holds it can acknowledge an alarm in progress.
  It is off by default, the id is long and random, and the trade is stated
  where you switch it on and in `docs/notification-channels.md`.
- **An automatic rule acting without a code.** A rule is authorised when
  somebody with `edit_config` saves it, not when it fires; `docs/automation-rules.md`
  says so plainly, and what restrains it is the kill switch, the guards and
  the rule that a perimeter area is never disarmed automatically.
- **Presence as an identity.** A phone is not a credential. This is why
  automatic disarming is off by default and why a perimeter area is never
  opened by a rule; the attack is described rather than defended against.

Foyer is **not a certified alarm system** and not a fire alarm system. It does
not meet EN 50131 or CEI 79-3, and a smoke detector wired into Home Assistant
does not replace certified, interconnected smoke alarms.

## Supported versions

This is a beta with one author. **The latest release is the supported one**; a
fix goes into the next release rather than backwards into older tags. The
[changelog](CHANGELOG.md) says what changed in behaviour, because for a
security system "fixes" is not an answer when the thing being updated guards
somebody's house.

## What happens after a report

There is no service-level agreement to make and none is offered. What there is
in practice: an acknowledgement that the report arrived, a fix or a clear
"this is out of scope and here is why", and — if it is a real vulnerability —
a release, a changelog entry that says what it was, and credit in the advisory
unless you would rather not be named.
