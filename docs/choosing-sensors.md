# Choosing sensors

**English** · [Italiano](choosing-sensors.it.md)

This page is assembled from manufacturer and integration documentation. None
of it has been tested on hardware by this project.

A sensor bought to switch a lamp and a sensor trusted to guard a door are
often the same box, but they are asked different questions. The lamp needs
to know that somebody walked in. The alarm also needs to know that the
sensor is still there, still powered, still heard, and still the thing that
was fitted. This page is for whoever is buying sensors for Foyer, or
deciding which of the ones already in the house to trust. It describes
categories and what to look for in a datasheet, not models. For sensors that
belong to an existing alarm, see
[reusing an existing alarm's sensors](reusing-existing-sensors.md).

---

## What to look for

| Property | Why it matters to an alarm | Where it lands in Foyer |
|---|---|---|
| Tamper switch | Says the case was opened or the sensor pulled off the wall | A second zone, of type *Tamper* |
| Supervision interval | Says the sensor is alive when nothing is happening | *Silence limit (seconds)* on the zone |
| Resistance to magnet defeat | A contact that can be held shut from outside guards nothing | Nothing in Foyer can fix this; it is chosen at purchase |
| Radio | Decides what a jammer, a dead router or a crowded band does to it | [Radio interference](system-health.md#radio-interference) |
| Battery reporting | A cell dies quietly unless something reports it | *Battery entity* on the zone |
| PIR pet immunity and blind time | Decide the false alarms and the second detection that never comes | *Activations needed*, verification groups |

### Tamper

A sensor with a tamper switch reports when its cover is opened or it is
pulled from its mounting. Where the integration exposes it, it arrives in
Home Assistant as its own entity, a `binary_sensor` with device class
`tamper`, next to the one for the door or the motion.

Map it as its own zone. Foyer proposes the *Tamper* type for that device
class: always on, never excluded, alarming whether the house is armed or
not, and logged as a tamper rather than an intrusion. Keeping it separate
from the contact means the log says *which* happened, and an intruder who
removes the sensor while the house is disarmed is still heard.

Two consequences to know before the first battery change. Opening the case
sets it off, armed or not; with its area disarmed, switch the tamper zone off
(*Enabled*) first and on again after — a disabled zone is ignored completely,
and a zone cannot be edited while its area is armed. And a walk test does
not list it: always-on zones are live rather than under test.

### Supervision interval

Some sensors report on a schedule even when nothing changes — a check-in, or
a heartbeat. That is what lets an alarm tell "the door is closed" from "the
sensor is gone". A sensor that reports only when it changes cannot be told
apart from a dead one until the door opens and nothing arrives.

Foyer counts those check-ins. With a *Silence limit (seconds)* set on the
zone, an entity that reports nothing for longer than the limit is a fault:
it blocks arming unless the zone allows it, raises `zone_fault`, and shows as
*Fault: silent too long* on *Test & diagnostics*. A report counts even when
the state did not change, because Foyer reads Home Assistant's
`last_reported` rather than the time of the last change. The limit is off by
default and may be set from 60 seconds to 7 days, per zone.

When choosing, prefer a sensor whose documentation states a check-in
interval, and set the limit comfortably longer than it. For a sensor that
reports only on change, leave the limit off: it would fault a door that stays
shut. Details in [zones](zones.md).

### Magnet defeat

A magnetic contact is a switch held by a magnet. A second magnet held against
the frame from outside can keep it closed while the door opens. What reduces
the risk:

- **Recessed contacts**, fitted inside the frame and the door, where there is
  no surface to hold a magnet against and nothing to see.
- **Contacts designed to notice a foreign magnet.** Some are; the
  manufacturer says so if it is.
- **A second layer** that does not care about magnets, which is the argument
  of the last section.

### Radio band and mesh

| Radio | What the category offers | What to know |
|---|---|---|
| Zigbee | 2.4 GHz mesh; mains-powered devices usually route for the battery ones | Shares the band with Wi-Fi. A mesh relies on its routers having power |
| Z-Wave | Sub-gigahertz mesh, frequency by region | A separate band from Wi-Fi and Zigbee |
| 433 MHz | Cheap, simple, long range; many devices one-way and unencrypted | Often no check-in and no acknowledgement; see [reusing](reusing-existing-sensors.md#three-things-the-radio-path-loses) |
| Wi-Fi | No extra hub | Depends on the router and its power; hard on batteries |

Any radio can be jammed. Home Assistant cannot measure jamming, but Foyer
watches for its signature — many zones on one radio going unavailable at
once, with the coordinator still answering — and treats it as an alarm while
armed: [radio interference](system-health.md#radio-interference). That check
works only for sensors that *do* go unavailable when they stop being heard,
which is one more reason to prefer a radio with check-ins.

Spreading a house across two radios is not a weakness: a jammer or an outage
on one leaves the other.

### Battery reporting

Name the sensor's battery entity on the zone (*Battery entity*): a percentage
`sensor`, or a battery `binary_sensor`, where `on` means low. A low battery
warns and never blocks arming; a battery entity that cannot be read at all is
a fault and does block. The threshold is *Low battery below* on the
*Settings* page, 20 % by default. The reasoning is in
[batteries](simulator.md#batteries).

### PIRs: pet immunity and blind time

**Pet immunity.** Some PIRs are made to ignore an animal up to a stated
weight, and only when mounted at the height and angle the manual gives. A pet
that climbs the stairs or the sofa can still be seen. A PIR that is not
pet-immune in a house with a dog is a false alarm waiting for the first
night.

**Blind time.** A battery PIR commonly ignores movement for a period after
it has reported one, to save its cell; the manual gives the time. During it,
somebody can walk the whole room and send nothing. This matters to Foyer in
one place worth writing down: *Activations needed* on a zone counts
detections of that zone within its window, and below the count the zone does
nothing at all. A PIR asked for two detections within 60 seconds, with a blind
time of three minutes, never sends the second one, and never alarms. Keep
*Activations needed* at 1 on such a PIR, and confirm with a second sensor
instead.

---

## Why a layered zone beats a better sensor

Every sensor has one way to be defeated: a magnet, a jammer, a blind time, a
dead cell, a dog. A more expensive sensor narrows that way; it does not
remove it. A second sensor of a *different* kind, watching the same route,
is defeated by something else. A contact on the window and a PIR in the room
behind it are beaten by a magnet and a slow walk, not by either alone.

In Foyer that is two zones — often in two areas, a perimeter and an interior
— and a way of saying they confirm each other.

### The cheapest real upgrade

Usually it is a second sensor in a
[verification group](zones.md#verification-groups), not a better contact.

A group alarms when enough of its members detect within its window: two of
two, two of three. By default its members still alarm on their own, and the
group adds its confirmation and its own response profile. That is what makes
the answer graduated: give the members a quiet profile and the group a loud
one, and a single PIR sends a notification while two within a minute sound
the siren. The false alarm from one sensor stops costing a siren, and the
real intruder, who crosses more than one, still gets it. For one sensor
confirming another, *Cross-zone verification* on the zone does the same with
one field.

Two rules shape how to place the second sensor:

- **Only detections that would alarm at once count.** Opening the entry door
  and walking through during the entry delay never satisfies a group, so
  coming home cannot set off the loud profile.
- **A zone belongs to one group or pair at most**, or its detection would
  count twice.

*Members produce nothing below the threshold* exists and is off by default,
because a single sensor facing a real intruder would then produce silence.

---

## Not covered here yet

- Recommended models, and anything checked on real hardware.
- Glass-break, vibration and shock sensors, curtain PIRs and outdoor beams.
- Wired sensors on a Home Assistant input, and end-of-line resistors.
- Which integrations expose a sensor's tamper, check-in and battery as
  entities.
- Sirens, and what makes one suitable for an alarm.
- Mounting: heights, angles, and what a PIR should not face.
