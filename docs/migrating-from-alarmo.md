# Migrating from Alarmo

**English** · [Italiano](migrating-from-alarmo.it.md)

Nobody with forty configured sensors remaps them by hand to try something new,
so Foyer can read an existing [Alarmo](https://github.com/nielsfaber/alarmo)
configuration and bring it in. This page is for a house that already runs
Alarmo: what the importer reads, what it makes of it, what it leaves to you,
and what to check before you trust the result. Read it before you press
anything.

---

## What it is

**A best-effort tool that reports what it could not convert, not a guaranteed
migration.** It reads `.storage/alarmo.storage`, the file Alarmo keeps its
configuration in. That file is Alarmo's internal format: its author may change
it in any release, without notice and without fault, because it was never
offered as an interface to anybody. So the importer is careful about what it
accepts, and says everything it did not do.

- **It reads only the storage versions it was checked against, and refuses any
  other by name.** Today that is storage format 6.1 to 6.3, which Alarmo 1.9.5
  to 1.10.19 write. The file carries no Alarmo release number, only its
  storage version, so that is what a refusal names. Nothing is brought across
  from a file it refuses.
- **It refuses a file whose shape is wrong rather than bring half of it**, and
  says where in the file it stopped. A section with more than 1,000 entries, or
  a file over 4 MB, is refused the same way.
- **A field it does not know is a line in the report, not a refusal**: whatever
  that field does in Alarmo was not brought across, and the report names it.
- **There is no upload.** The file is read from the Home Assistant the panel is
  talking to, so the importer only ever looks at this house's Alarmo.

## Where it is, and who may use it

*Settings* → the *Import from Alarmo* card. It has two buttons: *Read from
Alarmo*, and — once there is something to apply — *Apply*.

| Step | What it needs |
|---|---|
| *Read from Alarmo* (the preview) | *Edit the configuration*. It writes nothing, so it asks no code. |
| *Apply* | *Edit the configuration*, and your code when Foyer asks for one to change the configuration. If the import would create people, *Manage users and codes* as well, because bringing people in is a change to who can command the house however it is made. |

A Home Assistant administrator is never refused for want of a permission, but
the code still applies to them. An *Apply* refused for a missing permission or
a wrong code leaves a row in the log, like any refused change.

## Preview, then apply

*Read from Alarmo* shows what the import would do before anything is written:

- **What would be added** — the areas, new scenarios, existing scenarios that
  would also arm what is brought in, people (without codes), response
  profiles, and how many zones, switched off until confirmed.
- **What to know before you apply** — the report, one line for every choice
  the importer made on your behalf and everything it could not bring.
- Any problem the configuration would have after the import, the same checks
  every edit goes through. While there is one, *Apply* stays unavailable.

*Apply* stores exactly what the preview showed, and nothing it did not. It is
refused — with a message asking you to read again — if anything the preview was
computed from has changed since: Alarmo's file, Foyer's configuration (an edit
from another tab, say), or the name or presence of one of the sensors the file
lists. It is never refused because a sensor's *state* changed, because a
motion sensor does that every time somebody walks past.

An import is a configuration change like any other. It goes through the same
validation, it is refused while an armed area or a running scenario depends on
something it would change, and it leaves a row in the log.

### It adds; it does not replace

Everything is brought in **beside what is already here**. Nothing you already
have is removed or rewritten, with one exception described below (an existing
scenario may be extended to arm the new areas).

- A sensor that is already one of Foyer's zones is left exactly as it is.
- A person whose name is already on *Users* is left exactly as they are.
- A name already taken by an area, zone or scenario gets a number, and the
  report says so.

## What it converts

| Alarmo | Foyer |
|---|---|
| **An area** | One Foyer area — or several, when its sensors were watched in different modes. In Foyer a scenario arms whole areas, so "the motion sensor only in Away, the doors in every mode" becomes two areas that the Away scenario arms together and the Home scenario arms one of. The report names every split. |
| **A sensor** | A zone, in the area that matches its modes, named after the entity's name in Home Assistant. A `door`, `window`, `motion` or `other` sensor becomes *Delayed* if it had an entry delay in any of its modes, *Instant* if not, or *24h* if it was always on. An `environmental` sensor becomes *Technical* and a `tamper` sensor *Tamper* — both watch all the time, as those kinds must, and the report says so when Alarmo had them only in some modes. |
| **A mode you had switched on** | A scenario that arms every area watched in that mode, and reports that mode to Home Assistant. If you already have one scenario reporting the same mode, that scenario is extended to arm the new areas instead, so HomeKit and voice assistants keep working: a second one would make *Whole house* refuse the mode. |
| **Exit and entry delays, siren time** | Wherever Alarmo had several values and Foyer has room for one, the longest, because a delay too short locks somebody out of their own house with the siren going. A value past Foyer's limit takes the limit: 300 s for exit and entry delays, 900 s for the siren. A siren that sounded until somebody disarmed also becomes 900 s. Each such choice is a report line. |
| **What happens to a sensor open at arming** | *If open when arming*: *Arm after closing* for a sensor that armed the house when it closed; *Ignore* for one allowed to be open; *Exclude automatically* for one excluded automatically in every mode it was watched in; *Block arming* otherwise — including a sensor excluded in some modes and not others, because Foyer has one policy per zone and that is the safe half. |
| **A person** | A Foyer user, enabled or not as they were, **without a code**. Allowed to arm: *Arm* and *Change scenario*. Allowed to disarm: *Disarm*. An override code: *Force arming*. Limited to some areas: limited to the areas those became. |
| **An action automation that sounds a siren or works a switch** | A response profile per Alarmo area, which starts as a copy of your default profile — so an imported area still notifies whoever the default did — plus those sirens and switches. Alarmo's `armed`, `disarmed`, `triggered`, `untriggered`, `arm_failure` and `pending` become the moments *Armed*, *Disarmed*, *Alarm*, *Alarm over*, *Arming failed* and *Entry delay started*. A siren is brought only when it sounds at the alarm itself with no tone or duration of its own; brought across otherwise, it would become the full siren for the full time. |

The new scenarios carry their own exit delay and siren duration, taken from the
Alarmo modes they came from. A scenario that was extended keeps its own
settings, and they now apply to the imported areas too; if it has its own exit
delay or siren duration, the report says so. If it answers with a response
profile of its own and an imported area was given one, that area no longer
inherits the scenario's, and the report says that as well.

## What it does not convert

Each of these is a line in the report, not a guess:

- **Codes.** None, ever — see [below](#people-arrive-without-a-code).
- **Notifications.** A notification that arrives somewhere unintended is worse
  than one you set up again. In Foyer, notifications go to contacts, on the
  *Contacts* page; see [notification channels](notification-channels.md).
- **Other automations**: any switched off in Alarmo; any started by an entity's
  state or by the start of arming, which a response profile has no moment for;
  any limited to some modes, unless those include every mode brought in,
  because a Foyer profile answers for an area whatever the scenario; any for an area that did not come across. A siren
  switched off by an automation is not needed, because Foyer stops its sirens
  itself at a disarm and when the siren time runs out. Any action that is not a
  siren or a switch is dropped from the automation and named.
- **Sensor groups.** A group needs its members switched on, and every zone
  brought in starts switched off. Make it on the *Verification groups* page
  once the zones are confirmed; the report gives each group's count, members
  and window.
- **Alarmo's settings**, when switched on: a code to arm, a code to change
  mode, a code to disarm, disarm when the siren time runs out, re-arm past open
  sensors, and MQTT. Foyer's own [settings](settings.md) are left as they are.
- **A sensor Foyer cannot use**: one that is not a `binary_sensor`, `cover`,
  `lock`, `switch` or `input_boolean`; one not watched in any mode its area had
  switched on; one in an area missing from the file. An area left with no
  sensor, or with no mode switched on, does not become a Foyer area.
- **What a zone cannot carry.** A sensor that sounded the alarm when it became
  unavailable is a fault in Foyer instead — it blocks arming and is reported,
  but does not sound. A sensor that had to stay triggered for some seconds
  first: Foyer acts on the first trigger. A sensor that stopped an arming the
  moment it opened during the exit delay: Foyer checks it when you press arm
  and when the delay runs out. A sensor Alarmo let you arm with open as long as
  it closed before the exit delay ended: with *Block arming* it must be closed
  when you press arm.

A sensor named in the file that does not exist in Home Assistant right now
still becomes a zone, and the report names it. Like every imported zone it
arrives switched off; once it is confirmed and switched on, it shows as a
fault until the entity is back. A sensor
that was switched off in Alarmo comes across too, and the report says so:
confirming its trigger does not oblige you to switch it on.

## Every zone arrives switched off

Alarmo's file does not say, sensor by sensor, which state means an alarm: it
reads `on`, `open` and `unlocked` as alarm for every sensor. In Foyer every
zone declares its own trigger, and a normally-closed contact reads the other
way round from a normally-open one, so the importer has nothing it could carry
across as a confirmed trigger. Each zone arrives with **Foyer's own proposal**
for its trigger, read from the kind of sensor — the same proposal the zone
wizard makes — **not confirmed, and switched off**.

The *Zones* page marks such a zone *Trigger to confirm* and explains why when
you open it. It cannot be switched on until somebody has tested the sensor,
corrected the trigger if it is wrong, and ticked *I have checked this against
the real sensor*. This is enforced by validation on every path that stores a
configuration — the editor, a restore, a second import — not only by the page.
A wrong trigger is a zone that never fires, found out during a break-in; see
[zones](zones.md).

A sensor that goes unavailable is a fault in Foyer: it blocks arming and is
reported. The report says so too.

## People arrive without a code

Alarmo keeps its codes as hashes in its own format, and Foyer does not take a
credential from another system on trust: the file's codes are read only to
check that they are text, and then never again. Everybody brought in needs a
new code on the *Users* page before they can disarm with one.

**The report's first line says so**, every time — even when nobody new was
brought in, in which case it says that the people who can disarm are the ones
already on *Users*. If a person was limited to areas that did not come across,
they may use none until you widen it there. If an extended scenario is limited
to some people, the people brought in are not among them until you add them on
*Scenarios*.

## What to check afterwards

After *Apply*, the card says what comes next. In order:

- [ ] **Confirm every zone against its sensor.** Open, close or walk past it,
      watch the state change, correct the trigger if it is wrong, tick the
      confirmation and switch the zone on. [Diagnostics](simulator.md#diagnostics-am-i-looking-at-the-right-sensor)
      shows the raw state beside Foyer's reading of it.
- [ ] **Give every person brought in a code** on *Users*, and check their
      permissions and areas.
- [ ] **Rebuild notifications** as contacts on *Contacts*, and check that each
      imported response profile notifies whoever it should on *Response
      profiles*; see [response profiles](response-profiles.md).
- [ ] **Remake sensor groups** on *Verification groups*, once their members are
      confirmed.
- [ ] **Read every scenario** on *Scenarios*: what it arms, its exit delay, its
      siren duration.
- [ ] **Walk the house** with a [walk test](simulator.md#walk-test--which-zones-never-saw-you),
      and see which zones never noticed you.
- [ ] **Rehearse a night in the [simulator](simulator.md#the-simulator)**
      before you arm for real.

## Running both side by side

Both can be installed at the same time, but **do not point them at the same
sensors**: you would have two systems deciding what an open window means,
arming and disarming independently of each other. Try Foyer on a few zones, or
on a test installation, and move the rest when it has earned it.

The importer is built for exactly that. It brings the zones in switched off, so
nothing is watched twice until you decide. As the card itself puts it: until
Foyer's zones are confirmed, keep Alarmo watching the house — but never arm
both on the same sensors.
