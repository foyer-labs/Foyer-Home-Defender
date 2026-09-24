# Automation rules

Letting the house arm itself, and the reasons it is allowed to do far less in
the other direction.

Everything here is configured on **page 12 — Automation rules**. Three things
are worth reading before writing a rule:

- **This is a closed rule model, not an automation engine.** Four triggers,
  three actions, one active window, three guards. Anything more complicated
  belongs in a Home Assistant automation subscribed to the `foyer_event`
  event — which can do anything at all, including calling `foyer.arm`.
- **A rule acts as a user would.** It goes through the same arming path a
  person goes through: the same preconditions, the same refusals, the same log.
  Every row it writes carries the rule's name and the channel `auto_rule`.
- **A rule is outside the code policy, deliberately.** An installation that
  requires a code to arm or disarm still has its rules act: nobody is standing
  there to be asked, and the authorisation happened earlier, when somebody
  with `edit_config` saved the rule. What restrains a rule is the switch, the
  guards and the perimeter constraint below — never a code no rule can type.
  Stopping the rules, though, *is* an operation: cancelling a countdown,
  suspending, and the kill switch all ask the same policy entry, which needs
  no code by default and can be raised.
- **Automatic arming and automatic disarming are not equally safe**, and Foyer
  does not pretend they are. The asymmetry is enforced in the engine rather
  than written on a screen. It has [its own section](#why-automatic-disarming-is-restricted)
  below, which does not soften anything.

---

## The rule model

| Element | Options |
|---|---|
| **Trigger** | `absence` — every selected person `not_home` for N minutes · `presence` — a selected person arrives · `time` — at HH:MM on chosen weekdays · `entity` — an entity holds a state for N minutes |
| **Action** | arm a scenario · disarm named areas · switch to another scenario |
| **Active window** | weekdays plus a time range; outside it the rule does not exist |
| **Guards** | only if currently disarmed · only if every zone is ready · only if no interior zone has moved for N minutes |
| **Grace period** | an actionable notification with a countdown and a **Cancel** button before the action runs. 120 s for an arming, 0 for a disarming, up to 900 s |
| **Open zones** | off by default: an open zone stops the arming, and the rule arms by itself once it closes · on: **Arm anyway, excluding open zones** — only the open zones that may be excluded. [Below](#when-the-house-is-not-ready) |
| **Suspension** | until a date and time · skip the next occurrence · a named expected-visitor window · the global switch |

### Presence-based arming, from the start

The common rule, and the one worth building first:

1. Create a contact on page 6 with the Companion app as an **actionable**
   channel. The editor refuses to save a countdown that names no contact at
   all; what it cannot check is whether the contact's channel can carry a
   button. An SMS-only contact hears the countdown and cannot stop it from
   the message — the Cancel button on page 12 and on the card still does.
2. On page 12, add a rule: trigger **Absence**, the people it watches, and a
   number of minutes. Five is enough for a phone that loses the network at the
   end of the drive; thirty is enough that nobody's afternoon nap arms the
   house around them.
3. Choose the scenario it arms.
4. Leave the first two guards on — a new rule has them on already. The
   third, "no interior motion for N minutes", is a number you type and is off
   until you do: it is the one that catches somebody asleep upstairs with a
   flat phone, so it is worth typing.
5. Leave the grace period at 120 s and name the contacts it announces to.

What happens then, in order:

- every phone leaves; the timer starts when the last one goes;
- N minutes later the rule wants to act, and the guards are evaluated;
- the countdown starts and the push goes out: *"Nobody seems to be in, so Arm
  when empty will arm Away. Cancel to stop it."* — and the same countdown, with
  the same button, appears on page 12 and on every card, because two minutes is
  not long enough to go looking for the right screen;
- two minutes later, if nobody pressed anything, **the guards are evaluated
  again** — two minutes is long enough for somebody to come home — and the
  house arms;
- the log gets an `armed` row under `arming`, on channel `auto_rule`, with the
  rule's name on it.

If somebody presses **Cancel**, the rule stops and does not announce itself
again until its condition goes false and true once more: somebody has to come
home before "the house is empty" is news again.

### Triggers that stay true, and triggers that happen once

This distinction decides what a blocked rule does next, and it is the one
thing about the model worth holding in mind:

| Trigger | Kind | A guard blocks it, then clears |
|---|---|---|
| `absence` | a condition | the rule acts as soon as the guard clears — shut the window and the house arms |
| `entity` | a condition | the same |
| `time` | an instant | the occurrence is missed. 23:00 happens once; a window shut at 23:02 is not another 23:00 |
| `presence` | an instant | the same: that arrival has been and gone |

A `time` rule that arms "some time after eleven, whenever the window is
finally shut" would be a different rule from the one somebody wrote.

### The guards

| Guard | What it catches |
|---|---|
| Only if currently disarmed | The house is already armed, or somebody is walking out through an exit delay |
| Only if every zone is ready | An open window, or a zone in fault. With it on, the rule does not start at all; with it off, the countdown starts anyway and says what is not ready — [below](#when-the-house-is-not-ready) |
| Only if no interior motion for N minutes | The flat phone battery: somebody is in the house, and their phone is not telling anybody |

The third one reads the zones themselves — an interior zone that is active
now, or whose entity changed inside the window. Areas marked as the perimeter
are left out of it: a front door contact is not evidence that anybody is in.
**With no area marked as the perimeter, every intrusion zone counts as
interior**, so the front door opening holds the guard for N minutes. Mark the
perimeter on page 2 and the guard reads what it is meant to read.

**A blocked rule is always logged**, under `system`, with the guard that
blocked it. "Why did it not arm last night?" is a question people ask, and
silence is the worst possible answer. For a condition — `absence`, `entity` —
the row is written once, when the block begins, because the rule is
re-evaluated at every wake-up and a row a minute would bury the log. For a
`time` or an arrival, every blocked occurrence gets its own row: Monday's is
not an answer to Tuesday's.

### When the house is not ready

Everybody has left and the bathroom window is open. What happens depends on
the "ready" guard.

**With "Only if every zone is ready" on** — as a new rule has it — the rule
does not start. There is no countdown and no message; the log gets one
`auto_blocked` row under `system`, and the rule starts its countdown as soon
as the window is shut.

**With it off**, the countdown starts anyway and says what is wrong:

- **The countdown names the open zone.** *"Nobody seems to be in, so “Arm
  when empty” will arm Away — but Bathroom window is not ready, and it cannot
  arm until it is. Cancel to stop it."* A zone in fault is named the same
  way.
- **By default the rule forces nothing.** When the countdown ends with the
  window still open, the arming is refused and the house stays disarmed.
  The rule does not retry on a timer: it arms by itself as soon as the
  window closes, after a new countdown.
- **The rule's contacts are told the outcome** — the same contacts its
  countdown goes to. First *"“Arm when empty” could not arm Away: not ready
  — Bathroom window. It will arm by itself as soon as they are."*, then,
  under the title *Foyer: arming now*, a message saying the zones that were
  not ready are ready. An arming refused for anything else gets *"could not
  arm Away. The log says why."* An arming that went as the countdown
  announced gets no second message.
- **These messages go through quiet hours.** The countdown does not — it is
  held like any other warning — but the outcome is about a house the
  household believes armed and is not, and that reaches them at any hour.

A `time` rule — and any rule triggered by an instant, such as an arrival —
is the exception, as it is for the guards: its occurrence happened once,
and a window shut at 23:02 is not another 23:00. Its message says so
instead: *"…not ready — Bathroom window. It will not try again until its
next time."* An arming the rule started that fails at the end of the exit
delay, because a zone opened while everybody was leaving, is told as well:
the exclusion covers only what was open when the rule armed.

#### Arm anyway, excluding open zones

A rule can be told to arm with the window open. The option is **Arm anyway,
excluding open zones**, beside the guards. It is off by default, and the
panel warns when it is switched on: it is a forced arming nobody types a
code for, and the house arms with that window uncovered.

- **The countdown says so**: *"…— Bathroom window is open and will be
  excluded. Cancel to stop it."*
- **It excludes only zones that are open and may be excluded.** A zone whose
  **May be excluded** is off still stops the arming, and the rule waits for
  it to close like any other.
- **It never excludes a zone in fault or unavailable.** A sensor that has
  gone silent is not "all quiet" (INV-4), and nobody chose to leave it
  uncovered: the arming is refused and the contacts are told, as above.
- **What it excludes is watched again the moment it closes**, as with any
  forced arming: shut the window after the house is armed and it is part of
  the armed house again.
- **It is logged as a forced arming**: a `forced_arm` row naming the
  excluded zones, on channel `auto_rule` with the rule's name. The contacts
  are told *"“Arm when empty” armed Away excluding what was open: Bathroom
  window. Each is watched again as soon as it closes."*

It does nothing when **Only if every zone is ready** is on: that guard stops
the rule before any countdown, so there is never an open zone to exclude.
The panel says so beside the option.

#### Each zone's own arm policy still comes first

Only zones whose **If open when arming** is **Block arming** stop an arming,
so only those are named in the countdown or excluded by the rule. The
others behave as they do for a person arming by hand:

| The zone's policy | With the window open when the rule arms |
|---|---|
| **Block arming** | named in the countdown; refused, or excluded by the rule's option |
| **Exclude automatically** | excluded by its own policy and announced, and included again by itself once closed — not held until disarm |
| **Arm after closing** | the arming goes ahead; after the exit delay it waits for the zone to close, and fails if it stays open too long |
| **Ignore** | arms regardless; the zone fires the next time it opens |

### The active window

Outside its window a rule **does not exist**: it is not blocked, it is not
suspended, and nothing is written about it. A rule with a window of
22:00–06:00 is not a rule that spends the day being stopped.

---

## Suspensions, and the boiler engineer

The recurring case: the house will be empty tomorrow morning, but somebody is
being let in. Automatic arming would arm the house around them.

Three ways to stop it, all on page 12 and none of them a configuration change:

- **Skip the next occurrence** — one click. The rule sits out one turn and is
  back the moment after.
- **Suspend until** a date and time.
- **An expected-visitor window** — a named period, "09:00–13:00 tomorrow,
  Boiler engineer", optionally with a **reduced scenario** applied instead.

The three are mechanically the same thing. The difference is what the log
says in six months: *Boiler engineer* answers the question, and *rule
suspended* never will. That is the whole reason the named window exists as a
first-class concept rather than a checkbox.

### What "apply instead" does, exactly

A reduced scenario **substitutes**: it replaces the suspended rule's action at
the moment that rule would have acted. It does not arm anything when the
window opens and does nothing when it closes.

That is deliberate, and the reason is the section below. If the window armed
something at its opening, then on a house that was already armed more than
that, opening the window would have to **disarm** — and an expected visitor is
not an authorisation to open the house.

Suspensions live with the runtime state, not with the configuration: they
expire on their own, they need no `edit_config` permission, and setting one is
three clicks from the panel the evening before.

---

## Why automatic disarming is restricted

Automatic **arming** carries a moderate, manageable risk. A flat phone battery
or a dropped Wi-Fi connection can make the system believe the house is empty
and arm it with somebody inside. The guards plus the cancellable countdown
reduce that to an annoyance.

Automatic **disarming on presence is a genuine security hole**, and it is why
professional systems do not offer it. Presence in Home Assistant is inferred
from a phone:

- **a stolen phone disarms the house.** Whoever took it does not need a code,
  a key or a moment's hesitation: they need to walk up to the door;
- **GPS drift of 200 metres disarms the house.** Phones do this in cities,
  under cloud, in car parks and next to large buildings — routinely;
- **a cloned MAC address on the home network disarms the house.** A network
  device tracker believes whatever the network tells it.

This is not theoretical. It is the most banal attack there is against a DIY
alarm, and it needs no skill at all.

So:

1. Automatic **arming** is fully supported.
2. Automatic **disarming exists and is disabled by default.** Turning it on is
   a deliberate act on page 12, beside the paragraph above. It cannot be
   turned on or off while any area is armed, because it decides whether the
   armed house can be opened with no code at all. A phone lost while the
   house is armed is answered by `switch.foyer_auto_arming`, a suspension or
   switching the rule off, none of which is refused.
3. **A perimeter area is never disarmed by a rule.** Mark an area as the
   perimeter on page 2, and no rule can open it, whatever the rule says.
   Whoever walks in on a stolen phone still finds every external door and
   window protected.

Point 3 is a hard constraint in the engine, not a default somebody can talk
their way past, and a regression test asserts it directly on the Decision
rather than through the screen.

Two consequences worth knowing:

- **A "switch to another scenario" action counts as disarming** whenever it
  would leave an armed area disarmed. Switching scenario drops the areas the
  old scenario armed and the new one does not name, so a rule that switches
  can open part of the house without ever saying the word. It needs the same
  switch turned on — and a perimeter area it would have dropped simply stays
  armed, outside any scenario, which the master panel then reports as
  `armed_custom_bypass`.
- **A `disarm` rule that names only perimeter areas is refused when you save
  it**, because it could never do anything. A `switch` or an `arm` that would
  drop only perimeter areas is not refused at save time — what it would drop
  depends on what is armed at the time — and simply drops nothing.

A `time` rule that disarms — "open the bedrooms at 07:00 on weekdays" —
carries none of the phone-shaped risk above. It is still behind the same
switch, because a disarm is a disarm and the mechanism should be chosen rather
than inherited; the warning the panel shows beside it names the attack that
rule really has, which is an hour anybody watching the house can learn.

---

## The entities, and the log

| Entity | What it is for |
|---|---|
| `switch.foyer_auto_arming` | The global kill switch. Off stops every rule and cancels whatever is counting down — a fortnight away, a house full of guests, a weekend when the rules would be wrong |
| `sensor.foyer_next_auto_action` | What happens next: `arm`, `disarm`, `switch`, or `idle`. The instant, the rule's name and any suspension are attributes |

`sensor.foyer_next_auto_action` reports what is **scheduled**, not what will
certainly happen: the guards are evaluated at the moment the rule acts. A
sensor that tried to predict them would be a second opinion able to contradict
the engine, and the row under `system` is where the real answer lives.

What the log records:

| Row | Category | When |
|---|---|---|
| `armed` / `disarmed`, `channel: auto_rule`, with the rule's name | `arming` | A rule acted |
| `auto_pending` | `system` | A countdown started, naming any zone that was not ready |
| `auto_outcome` | `system` | The rule's contacts were told an arming did not go as announced: not armed, armed later, or armed with zones excluded |
| `forced_arm`, `channel: auto_rule`, with the rule's name | `security` | A rule armed excluding open zones, which it names |
| `auto_cancelled` | `system` | Somebody pressed Cancel, with who and through which path |
| `auto_blocked` | `system` | A guard, a suspension or the switch stopped a rule |
| `auto_suspension_set` / `auto_suspension_cleared` | `system` | A suspension was created, used, lifted or expired |
| `auto_arming_switched` | `system` | The kill switch moved, whoever moved it |
| `arm_failed`, `channel: auto_rule` | `arming` | An arming or a switch the rule asked for was refused — an open window with the "ready" guard off. A refused **disarm** writes `auto_blocked` instead, and a rule asking for something already true (the house is already in that scenario) writes nothing |

---

## Things that are easy to get wrong

- **A countdown announced to nobody.** The editor refuses to save one: a grace
  period whose notification reaches no contact is a delay, not a chance to
  stop it.
- **Quiet hours still apply** to the countdown's notification. A contact whose
  quiet window is on, with a threshold above a warning, does not hear it — and
  the countdown still runs. Give at least one contact a channel that gets
  through, or set the grace period to 0 and know that it acts at once. The
  message that follows an arming that did not go as announced is the
  exception: it goes through quiet hours.
- **A person entity Home Assistant cannot read is never taken as absence.** An
  `unknown` or `unavailable` person is not evidence that nobody is in, which is
  the same rule INV-4 applies to zones.
- **A `presence` rule created while somebody is at home has not seen them
  arrive.** The first evaluation is a baseline, exactly as it is for a key
  zone or an NFC tag.
- **No rule acts during a walk test.** The house is armed for a test and
  somebody is walking through it; a rule that disarmed halfway through would
  end the one check that finds a misaimed PIR.
- **A countdown that fell due while Home Assistant was down acts at startup**,
  and the row says it was late. It is the one place where Foyer does the thing
  rather than dropping it, and the reason is that an arming missed is a house
  left open while everybody believes it is closed. An *occurrence* that fell
  in the same gap — 23:00 passing with nothing running — is recorded and
  missed instead: it never announced itself, and arming at half past midnight
  without having told anybody is not a kindness.
- **A rule never silences an alarm.** While an area it would disarm is in
  entry or already triggered, the rule is blocked and the log says so.
  Disarming an area the incident touched acknowledges the incident and stops
  the escalation (§7.2) — a person may do that, and an inference from a phone
  walking through the door may not.
- **A rule's arming clears alarm memory, and acknowledges nothing.** Like any
  arming (§5.2), it clears the memory of the areas it takes out of disarmed,
  and the *Alarm memory cleared* row carries the rule's name. An incident
  nobody has acknowledged stays open and its escalation carries on: a rule
  has seen nothing. An area that stays armed through a rule's scenario
  switch — the perimeter it may not disarm included — keeps its memory,
  because nothing armed it again. So does an area a rule arms the instant a
  walk test ends: the response to that instant is still held back, and an
  *Alarm memory cleared* nobody hears would take the memory away unseen, so
  the next disarm or arming clears it instead.
- **An arming the house refused is not retried on a timer.** If a window was
  open — or a zone in fault, or an open zone the rule could not exclude — the
  rule tries again when the areas it wants are ready, and not before. Anything else it was refused for waits like a rule that has had its
  turn: until its condition goes false and true again.

---

## Rehearsing a rule before trusting it

Page 9's simulator takes a hypothetical date and time. A rule that fires at
23:00 on weekdays can be rehearsed at eleven on a Monday morning: set the
clock, override the people to `not_home` — they are offered in the entity
overrides beside the entities an action's conditions read — and read the
trace.

Two things to know about a rehearsal. The house always starts **disarmed**,
because the question is hypothetical; but the kill switch and the suspensions
in force are real and come with it, so "would it arm tomorrow morning, with
the engineer expected?" has an answer. And the horizon is at most an hour: a
rule that waits longer than that for its condition cannot mature inside a
trace, so rehearse it with a shorter number of minutes and put the real one
back afterwards.

What the trace shows about a rule — that it would act, that a guard would
block it, that a suspension covers it — is read off the same `Decision` the
runtime acts on. Nothing predicts it a second time, so the rehearsal and the
night cannot disagree.
