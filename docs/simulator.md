# The simulator, and how to read a decision trace

The point of an alarm you configured yourself is that you can check it before
trusting it. This page is about the two tabs of **Test & diagnostics** that do
the checking without setting anything off: the live zone table, and the
simulator.

Both only read. Neither can change what is armed, and neither can run an
action. They need permission to read the log and nothing more — if you may see
who disarmed at 03:14, you may certainly see that the kitchen window is a
delayed zone with a thirty-second entry delay.

---

## Diagnostics: am I looking at the right sensor?

This is the first question after an installation and the one that is hardest to
answer from the configuration pages, because they show what you *meant*. The
table shows what is actually there, one row per mapped zone.

| Column | What it answers |
|---|---|
| **Entity** | Which Home Assistant entity is behind this zone. A zone whose entity was renamed shows no state at all, and the entity is listed separately above the table — this is by far the commonest silent failure |
| **State** | What that entity says right now, raw |
| **Trigger evaluation** | Whether Foyer would count that as *triggered*, read through this zone's own trigger |
| **Last change** | When the state last moved — not when the sensor last checked in |
| **Health** | Reachable, or the reason it is not |
| **Battery** | The level its battery entity reports, and whether that counts as low |
| **Signal** | The radio quality, where the integration exposes one |
| **Supervision** | The window within which this sensor has to report something |
| **Arming** | Whether this zone would stop its area arming, and which of the two reasons |

### Why "trigger evaluation" is a separate column from "state"

Because `on` does not mean alarm. A normally-closed magnetic contact reads `off`
when the door is *open*, and a zone configured for it alarms on `off`. A table
that showed only the raw state would look calm while the zone was firing, and a
table that assumed `on` would be wrong on half the contacts people own.

So the column is the engine's own reading, through the trigger you confirmed in
the zone editor. If it says *would not trigger* while you are standing in front
of an open door, the trigger is wrong — and that is the bug you came here to
find, rather than one you find during a burglary.

### Why "arming" is a separate column from "health"

A zone can be perfectly healthy and still stop the house arming: it is open and
its arm policy is *block*. And a zone can be in fault — unreachable, or silent
past its supervision window — which blocks for a different reason and needs a
different fix. The column says which, so the answer is "close the patio door"
or "the garage sensor has fallen off the network", not "something is wrong".

This column is the same function the engine uses when it refuses an arming
for a fault or an open zone, so it cannot say *ready* where a zone would
block; a code, a permission or a running walk test can still refuse the
request.

### Batteries

A zone may name the entity that reports its battery. Two different things can
then be wrong with it, and they are deliberately treated differently:

- **A low battery warns and never blocks.** A contact reporting 15 % is still
  seeing the door. A house of forty battery zones that cannot be armed the
  morning one of them dips is an alarm that gets switched off — so instead, the
  moment is raised once on the way down, and *every* arming attempt says which
  zones went under guard on a dying cell. If you would rather not trust one,
  exclude it from that arming: it is an ordinary manual exclusion and it ends
  when you disarm.
- **A battery entity that cannot be read at all is a fault, and blocks.** A
  battery sensor that has gone silent is a radio that has gone silent, and the
  contact beside it is the next thing to stop reporting.

What counts as low is one setting for the installation, on page 11, 20 % by
default. A battery `binary_sensor` is read by Home Assistant's own convention
instead, where `on` means low.

### Arming devices

Keypads, tags and remotes get a table of their own below the zones. A keypad
cannot block arming, so it has no business in a column about arming; and a
keypad that speaks only over MQTT has no entity at all, which the table says
rather than showing it as healthy. A tag whose entity has gone unavailable is
exactly the kind of thing this page exists to surface.

---

## The simulator

> **Nothing here is executed.** The simulator calls the same decision engine the
> alarm calls, with a made-up world and a made-up clock, and then simply never
> hands the result to the part that would run the sirens.

That sentence is a structural guarantee rather than a promise. The engine is a
pure function — it performs no action, reaches no Home Assistant state and
reads no clock it was not handed — so "run it and throw the answer away" is the
whole of the implementation. A test asserts that the simulator and the runtime
reach an identical decision from identical inputs; if that test ever fails, the
bug is a second evaluation path somewhere, never the trace.

### What you set

- **A scenario**, or none. *None* is a real question too: a 24h zone, a tamper
  and a smoke detector all answer on a disarmed house.
- **A date and time.** This is what a time condition is read against. The same
  configuration at 19:32 and at 23:32 is two different answers, and the field
  is how you check both.
- **Zones forced into a state**, each at a chosen number of seconds **after
  the house has finished arming** — not after the start of the run, because
  the run begins by arming and an offset from the start would put the zone
  inside the exit delay. Zero therefore means what you mean by it: armed, and
  then this happens. The offset exists because a verification group reaching
  two of two, or a second zone joining an incident, happen *in sequence*, and
  two zones forced at the same instant can never show either.
- **Entities used in conditions, and the people an automatic rule watches.**
  Only the ones your configuration actually reads — "only if nobody is home"
  can be rehearsed both ways, and so can "everybody has left". Leave one empty
  to use what it really says right now.

**If your installation asks for a code to arm**, the simulator asks for one
too. The premise is a real arming, run through the real engine, and §8.2 has no
exemption for a rehearsal — inventing one would be a second authorisation path,
which is exactly what this feature is built to avoid. The trace says so on its
first line and the page offers the field. Nothing is executed either way.
A code typed there is a real code, checked and counted like any other: a
duress code raises its silent `duress` for the request, and the rehearsal then
runs as the ordinary code would, so the trace never shows it.

The house starts disarmed whatever it is really doing, with your sensors'
real current readings underneath your overrides. If a window is genuinely open,
the simulator will tell you the arming would be refused, which is a useful
answer rather than an obstacle: force it closed and ask again.

Two things about the house are **not** hypothetical and come with the run: the
automatic-rule kill switch, and any suspension in force. So "would it arm
tomorrow morning, with the boiler engineer expected?" is a question the
simulator can answer — and a rule that fires at 23:00 on weekdays can be
rehearsed at eleven on a Monday morning by setting the clock to it. What the
trace says about a rule, including the guard that would block it, is read off
the same decision the runtime would act on (§9.4).

### Reading the trace

A worked example, of the case that is hardest to reason about:

```
21:32:00  Area "Ground floor": Disarmed → Arming · exit delay until 21:32:05
21:32:05  Area "Ground floor": Arming → Armed
          Profile "Full", inherited from the area
21:33:00  Zone "Open plan PIR 1" → on
          Area "Ground floor": Armed → Triggered · siren until 21:36:00
          Group "Open plan": 1 of 2 within 60 s → not satisfied
          Incident opened 20260914-193300-1
            Profile "Silent", inherited from the zone
            ✓ Notify Luca
          ⏱ siren cutoff at 21:36:00
21:33:30  Zone "Open plan PIR 2" → on
          Group "Open plan": 2 of 2 within 60 s → SATISFIED
          Zone joined the incident 20260914-193300-1
            Profile "Full", inherited from the group
            ✓ Indoor siren
            ✗ Hall lights — condition not met: time 22:00-07:00
            ✗ Push to the NAS — condition not met: binary_sensor.nobody_home is on
            ✗ Landing lights — held back by a delay earlier in the sequence
            ✓ escalation step 0 → Luca (Push)
          ⏱ escalation step 1 at +60s → Luca (SMS)
          ⏱ escalation step 2 at +120s → Partner (Push)
21:36:00  Area "Ground floor": Triggered → Armed
          Siren cutoff
```

Four kinds of line, and each is there for a reason.

**What happened.** The zone that moved, the area that changed state, and which
timer is now running and until when. The timer is the engine's own — if the
line says the siren stops at 21:36, that is the siren's timer, not a number
worked out for the display.

**Group state, not just the zone.** A group is the strongest tool there is
against false alarms, and it is also the one whose behaviour is least visible:
one sensor does one thing, two sensors do another. The trace shows the
arithmetic on every activation — *1 of 2 within 60 s* — so you can see the
window filling and see it expire.

**Which profile answered, and where it came from.** This is the line that
explains a response that otherwise looks arbitrary. A zone's own profile
answers its own alarm; a satisfied group answers with the group's; everything
else answers from the area, then the scenario, then the global default. In the
example above, one PIR on its own is *Silent* (the zone's profile) and two
within the window are *Full* (the group's) — which is graduated response, and
you can see it happen.

**Every action, including the ones that did not run.** A tick means it ran. A
cross means it did not, with the reason:

| Reason | What it means |
|---|---|
| **condition not met: …** | Which condition failed, spelled out. A time window is shown as its hours; an entity condition as the entity and the state it wanted |
| **held back by a delay earlier in the sequence** | Not skipped — it is going to run, and the ⏱ line says when |
| **already running for this incident, not restarted** | A siren already sounding is not restarted when a second zone joins (§5.6) |
| **every contact it names is inside their quiet hours** | The notification named contacts and the window held all of them back. Nobody would be told, so nothing was sent |
| **this zone is silent and suppresses it** | The zone is marked silent, and this action is one of the kinds a silent zone does not run |
| **nothing is configured for this moment** | The profile answered, and it has no actions for this moment. Shown only where that is itself the finding — a satisfied group with an empty profile is why the siren stayed quiet |

**Who is being told, and who is next.** A notification says which contacts it
reached and through which channel, and the ⏱ escalation lines say who comes
after that and when. They are read off the decision the engine produced, not
worked out again for the display: what the trace shows is the schedule the
house would really keep, and it stops at the first acknowledgement exactly as
the real one does. A contact inside their quiet hours is named too, as held
back rather than as reached.

**What is still to come.** The ⏱ lines: a siren cutoff, the rest of a sequence
a delay is holding, the escalation steps still ahead. Each is announced once,
at the moment it is scheduled, rather than repeated under every later step.

### Things worth rehearsing before you trust a configuration

- **Coming home.** Force the delayed zone your route goes through, then the
  follower after it. The follower must inherit the running entry window, not
  start an alarm. If it goes straight to triggered, its `follows` list is
  wrong — and you find out now rather than at the front door.
- **An action with a condition, at both hours.** Run it at 19:00 and at 23:00.
  The whole point of the clock field.
- **A group.** Force one member, then the other thirty seconds later, then try
  again with ninety seconds between them and watch the window expire.
- **The scenario you actually use at night.** The most useful answer the
  simulator gives is often the first line: *cannot arm, zone in fault*.

### Every run is logged

Under `system`, with its inputs — the scenario, the clock, the zones you forced
and when. Six months later, "why is the hall on a different profile?" has an
answer that includes the run that justified the change.

### Limits, stated plainly

- **A run is bounded.** Fifteen minutes of simulated time from the moment the
  house is armed, by default, and a
  cap on how many decisions it may take to get there. When it stops with
  something of its own still running — an area counting down, a sequence a
  delay is holding — it says so rather than ending as though the house had gone
  quiet.
- **It rehearses the decision, not the transport.** It tells you a notification
  would be sent to a given target; it does not tell you the target works. That
  is what the real action test is for — the tab beside this one.
- **It does not replace a walk test.** Forcing a zone into a state proves what
  the engine does about it. It proves nothing about whether the PIR in the
  hallway is aimed at the hallway. That is the next tab along.

## The two tabs that act

The simulator and the diagnostics table only look. The other two tabs on page
9 do something, and they are how you answer the two questions a rehearsal
cannot.

### Walk test — which zones never saw you

Every area that can arm is armed for real, every sensor is read for real, and
the response is held back. Walk the house; the table fills in.

Read it from the top. The zones listed first are the ones that have **not**
reacted, and they are the finding: a door nobody opened and a PIR pointing at
the wrong wall look identical there, so walk the ones you expected to trip
again before you conclude anything. A zone in fault is marked as such in the
same row, because it could not have reacted.

Six things worth knowing before you start one:

- **24h, tamper, technical and panic zones stay fully live**, alarm included.
  A walk test never silences a smoke detector. They are also left out of the
  table: they are live rather than under test, and nobody sets off the smoke
  detector to prove it works.
- **A detection moves nothing.** No alarm, no incident, no alarm memory, and
  nothing tells HomeKit, Google or Alexa that somebody has broken in. Forty
  zones walked would otherwise leave forty alarms in the log.
- **It ends itself, and you cannot stop it ending.** The timeout runs from the
  last detection, so a large house can be walked in one pass, and an absolute
  cap ends it whatever happens. While it runs, a real intrusion produces
  nothing — which is why the banner is on every screen, why its start and end
  are announced (by the profile, or by a Home Assistant notification Foyer
  puts up itself when no profile action sends one), and why entry and exit
  are both in the log with your name.
- **An area that cannot arm stays out**, and the page names the zones that
  kept it out. Its other zones are still recorded when they detect you; the
  zone holding the area open cannot change until it is closed, so close the
  window and run it again rather than reading that row as a dead sensor.
- **So does an area still holding alarm memory.** The test arms for a walk,
  not for a watch, so it is not the arming that clears the memory, and the
  area keeps it after the test. Its zones are still recorded when they
  detect you. Disarm the area first if you want it walked armed.
- **It covers the whole house, whoever starts it.** Every disarmed area that
  can arm is armed, including areas outside your own, and an area somebody
  else armed stays armed but stops answering too until the test ends. The
  `walk_test` permission can therefore keep an armed house quiet without
  `disarm` — fifteen minutes after the last detection by default, never more
  than three hours per test, and nothing stops it being started again as soon
  as it ends — so it is given as `disarm` is, and it asks for a
  code by default. The Users page says so beside the permission.

### Action test — press the button before the night you need it

A test button beside every action, and it really executes: the siren really
sounds — for three seconds, after which Foyer switches it off, whether it
takes a duration or is driven by a switch — and
the notification really sends. It asks first, it needs the `test_actions`
permission and a code, and every run leaves a row in the log marked as a test.

It is worth the noise for one reason. The worst way to discover that a
notification service was renamed, or that the phone that was going to be
called has left the household, is at the moment the alarm is trying to use it.

The same button sits beside each action on page 5, where you have just
finished configuring it and are wondering whether it arrives.
