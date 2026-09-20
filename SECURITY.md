# Security policy

Foyer Home Defender is a Home Assistant integration that does what an alarm
does: it arms, it disarms, it sounds things and it notifies people, on rules
somebody configured. It is not a professional alarm system, it is not
certified, and nothing here is offered as one. What it is instead is code that
somebody's house leans on a bit, which is a good enough reason to have a page
saying where to send a defect and what is deliberately out of scope.

## Reporting a vulnerability

Use GitHub's **private vulnerability reporting**:
[open a private advisory](https://github.com/foyer-labs/Foyer-Home-Defender/security/advisories/new).
It is enabled on this repository, the report is visible only to the
maintainers, and it keeps the discussion in one place until there is a fix.

Please do not open a public issue for anything in the list below. Everything
else — a crash, a wrong translation, an entity that does not appear — belongs
in an ordinary issue, where more people can help.

What helps most in a report: the version, what you expected to happen, what
happened instead, and the smallest configuration that shows it. The
diagnostics download is anonymised and is usually enough.

**Worth reporting privately**, roughly in order of how much they matter:

- arming, disarming or acknowledging **without the code the policy requires**,
  or on an area or scenario the person is not allowed;
- making it **stay quiet** when it should not: a response that can be
  suppressed from outside, a notification that can be stopped by somebody who
  should not be able to stop it, a way to disarm a **perimeter** area from an
  automatic rule;
- **reading what should not be readable**: a code or its hash in an API
  response, a log row, an event, the diagnostics download or a backup;
- defeating the **lockout** of repeated wrong codes, or the rule that a device
  must be declared before it may command anything;
- anything that lets a **non-administrator** Home Assistant user do what the
  configuration says only an administrator may.

**Out of scope**, deliberately and permanently — not because these do not
matter, but because they are properties of what this is rather than defects
in it:

- **A Home Assistant administrator.** They can read `.storage`, disable the
  integration, call any service and delete the log database. Foyer's codes are
  there to stop household members, guests, the cleaner, non-admin Home
  Assistant users and whoever finds an unlocked wall tablet. They are not
  there to stop the person who owns the installation, and no version of this
  will claim otherwise.
- **Anything that needs physical access to the Home Assistant host.**
- **The transports.** Foyer orchestrates `notify.*` services; what a push, an
  SMS or a voice call does with a message belongs to that integration.
- **The acknowledgement webhook, when you have switched it on.** It is an
  unauthenticated URL by design — that is how a voice provider feeds a DTMF
  keypress back — so whoever holds it can acknowledge an alarm in progress.
  It is off by default, the id is long and random, and the trade is stated
  where you switch it on and in `docs/notification-channels.md`.
- **An automatic rule acting without a code.** A rule is authorised when
  somebody with `edit_config` saves it, not when it fires;
  `docs/automation-rules.md` says so plainly, and what restrains it is the
  kill switch, the guards and the rule that a perimeter area is never disarmed
  automatically.
- **Presence as an identity.** A phone is not a credential. This is why
  automatic disarming is off by default and why a perimeter area is never
  opened by a rule; the attack is described rather than defended against.

## What this is not

Worth saying here as well as in the READMEs, because this page is the one
people find from the repository's front door.

Foyer is not certified and does not aim to be: EN 50131, CEI 79-3 and their
equivalents are out of scope, and an insurance policy or a tender that names a
grade is not satisfied by it. Nobody is monitoring anything — it notifies the
people the household listed, over transports it does not own. Detection is only
as good as sensors somebody bought, on a radio somebody else designed, behind
a router that goes off with the power. And it is not a fire alarm system: a
smoke detector wired into Home Assistant does not replace certified,
interconnected smoke alarms.

None of that makes it useless; it makes it a tool with a shape. The simulator,
the walk test and the action test exist so that the honest claim can be "it
does what you configured", which is a different promise from "it will protect
you".

## Supported versions

This is a beta with one author. **The latest release is the supported one**; a
fix goes into the next release rather than backwards into older tags. The
[changelog](CHANGELOG.md) says what changed in behaviour, because "fixes" is
not much of an answer when you are deciding whether to update the thing that
watches your front door.

## What happens after a report

There is no service-level agreement to make and none is offered. What there is
in practice: an acknowledgement that the report arrived, a fix or a clear
"this is out of scope and here is why", and — if it is a real vulnerability —
a release, a changelog entry that says what it was, and credit in the advisory
unless you would rather not be named.
