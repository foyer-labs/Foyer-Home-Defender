# Reusing an existing alarm's sensors

**English** · [Italiano](reusing-existing-sensors.it.md)

This page is assembled from manufacturer and integration documentation. None
of it has been tested on hardware by this project.

Many houses already have an alarm: contacts on the doors, PIRs in the
corners, a panel in a cupboard. This page is for whoever wants Foyer to read
those sensors rather than buy new ones. It describes the ways a sensor that
belongs to another system can reach Home Assistant, what each way costs, and
how the entity that comes out of it becomes a Foyer zone. Choosing new
sensors is a separate page: [choosing sensors](choosing-sensors.md).

Foyer reads Home Assistant entities and nothing else. Every path below ends
in the same place — an entity, usually a `binary_sensor` — and the question
each one answers is how honest that entity is about the sensor behind it.

---

## Four ways in

| Path | What reaches Home Assistant | The catch |
|---|---|---|
| A native integration for the panel | The panel's own view of every zone, over its network module or its maker's cloud | Only what the integration exposes, as quickly as it polls |
| A programmable output wired to an input | One contact per output: "armed", "alarm", "zone 3 open" | One wire, one fact; you choose which facts |
| Listening to the wired bus | Whatever the bus carries | Electrical risk, and it may break a maintenance contract |
| Receiving the sensors' own radio | Each sensor's transmissions, heard by a receiver of yours | Only unencrypted radios, and no supervision |

### A native integration for the panel

Some panels have an integration in Home Assistant itself. Each one needs the
panel's network module or a cloud account, and each exposes zones in its own
way. These exist in Home Assistant's integration list; read the page for
yours before buying anything, because the module and the firmware matter:

| Integration | What it needs, according to its documentation |
|---|---|
| [Envisalink](https://www.home-assistant.io/integrations/envisalink/) | A DSC or Honeywell panel with an EVL-3 or EVL-4 board; zones become binary sensors |
| [Elk-M1](https://www.home-assistant.io/integrations/elkm1/) | An Elk M1 panel, usually over its Ethernet board; zones become binary sensors once the panel is set to transmit zone changes |
| [Risco](https://www.home-assistant.io/integrations/risco/) | A Risco panel, over the cloud or a local connection; what each zone looks like depends on which |
| [Satel Integra](https://www.home-assistant.io/integrations/satel_integra/) | An Integra panel with an ETHM-1 Plus module; zones and outputs become binary sensors |
| [Total Connect](https://www.home-assistant.io/integrations/totalconnect/) | A Resideo/Honeywell panel on Total Connect 2.0; cloud only, polled every 30 seconds |
| [Verisure](https://www.home-assistant.io/integrations/verisure/) | A Verisure account; cloud polling; door and window sensors become binary sensors |

Two things to read on the integration's page before trusting a zone to it:

- **Local or cloud.** A cloud integration hears about a door when it next
  polls, and stops hearing anything when the internet does. A detection that
  arrives thirty seconds late arrives thirty seconds into the house.
- **What happens when the connection drops.** In Foyer an entity that is
  `unavailable` or `unknown` is a fault, never "all quiet": it blocks arming
  unless the zone allows it, raises `zone_fault` and shows on the *Test &
  diagnostics* page. One integration usually carries every zone, so a lost
  connection faults all of them at once, which is the honest answer.

If your panel is not in that list, community projects may exist for it. They
are outside what this page can speak for.

### A programmable output wired to an input

Most wired panels have programmable outputs (often called PGM) that switch
when something happens: the panel is armed, an alarm is sounding, a zone is
open. Wire one to an input Home Assistant can read — a dry-contact input
module, or a GPIO pin on a board running ESPHome
([GPIO binary sensor](https://esphome.io/components/binary_sensor/gpio/)) —
and the output becomes a `binary_sensor`.

This is the least intrusive path: the panel keeps working exactly as it
did, and Home Assistant only watches a contact the panel was designed to
drive. What it cannot do is give you every zone: one output is one fact, and
panels have only a few. The panel's installation manual says what kind of
output each one is and what it may drive; wire to that, not to a guess.

### Listening to the wired bus

The keypads of a wired panel talk to it over a bus, and the zones' states
cross that bus. A board connected to it can read them. It is possible, and it
carries three risks worth weighing before a screwdriver comes out:

- **Electrical.** The bus carries the panel's power. A wrong connection can
  damage the panel, the board, or both.
- **The panel may notice.** A device on the bus that the panel did not
  enrol can load the bus or be reported as a fault or a tamper.
- **The contract.** If the panel is monitored or maintained by a company,
  tampering with it may void the contract. Read it, or ask, first.

### Receiving the sensors' own radio

Many cheap wireless sensors transmit on 433 MHz without encryption, and a
receiver of yours can hear them as well as the panel does:

- [rtl_433](https://github.com/merbanan/rtl_433) turns an inexpensive
  software-defined radio into a receiver for the 433.92 MHz, 868 MHz and
  other ISM bands, with decoders for many devices, door and window sensors
  among them. It can publish what it decodes to MQTT, and an
  [MQTT binary sensor](https://www.home-assistant.io/integrations/binary_sensor.mqtt/)
  turns a message into an entity.
- An **RF bridge** — a board with a 433 MHz receiver, such as one running
  ESPHome with its
  [remote_receiver](https://esphome.io/components/remote_receiver/)
  component — decodes the simpler fixed-code protocols and exposes each code
  as a binary sensor.

Two details of the MQTT binary sensor decide how honest the entity is, and
both are in its documentation:

- **A sensor that sends only "open".** Some contacts transmit one code when
  they open and nothing when they close. `off_delay` returns the entity to
  `off` after a set time, so the zone sees a pulse. A window left open then
  reads closed after the delay, and arming does not stop for it.
- **`expire_after`** makes the entity `unavailable` when nothing has arrived
  for a set time. Foyer reads that as a fault. On a sensor that transmits
  only when it changes, it would fault a door that stays shut; leave it off
  there, for the reason the silence limit below is left off.

#### Why encrypted systems cannot be read this way

Some wireless alarms encrypt their radio. Ajax, for example, states that its
Jeweller radio works at 868 MHz and that every transfer is
[encrypted with a proprietary algorithm based on AES](https://ajax.systems/jeweller/).
A receiver outside such a system has no decoder to run: reading those
sensors would mean breaking the encryption of an alarm rather than listening
to a sensor. For systems like these, the native integration, where one
exists, or a programmable output is the way in.

---

## Three things the radio path loses

**Wireless sensors sleep after a detection.** A battery PIR commonly
ignores movement for a while after it has reported one, to save its cell,
and the manual gives the time. A second transmission during that time does
not come. [Choosing sensors](choosing-sensors.md) says what that does to
*Activations needed*.

**Passive reception loses supervision.** A panel that enrols its sensors
usually expects a periodic check-in from each and treats a missing one as a
fault. A receiver of yours hears the sensor only when it transmits, and a
sensor that transmits only when it changes says nothing while it is working
— and nothing when its battery is dead or somebody has taken it off the
wall. From Home Assistant the two look the same.

**A jammed 433 MHz sensor does not go `unavailable`.** Foyer's
[radio interference](system-health.md#radio-interference) check counts zones
on one radio going unavailable together. An MQTT entity fed by a receiver
keeps its last state when the messages stop, so jamming this band leaves
nothing for that check to count.

---

## Mapping the result onto a Foyer zone

Whatever the path, the zone is made the same way, on the *Zones* page. The
detail is in [zones](zones.md); what matters for a borrowed sensor is below.

| Setting | What to choose |
|---|---|
| *Entity* | The `binary_sensor` the path produced. A zone may also watch a `sensor`, `cover`, `lock`, `switch`, `input_boolean`, `event` and a few others |
| *Trigger* | The state that means open or detected, checked against the real sensor. A panel's zone, a PGM input and an RF code do not agree on whether `on` is open: a normally-closed input reads the opposite of a normally-open one. Open the door, watch the state, then tick *I have checked this against the real sensor* |
| *Type* | By where the sensor is: *Delayed* for the door you come in by, *Instant* or *Follower* for the rest |
| *Silence limit (seconds)* | See below |
| *Battery entity* | If the path gives one: for diagnostics and the [battery warning](simulator.md#batteries) |

### The tamper as its own zone

If the path exposes the sensor's tamper — a panel integration that reports
it as its own entity, or a decoder that reports it in the message — map it
as a second zone of type *Tamper*. Foyer proposes that type for a
`binary_sensor` whose device class is `tamper`. A tamper zone is always on,
cannot be excluded, and alarms even while the house is disarmed, which is
the point: a sensor pulled open is an alarm whoever is at home.

### Supervision

The *Silence limit (seconds)* is off by default. When it is set, a zone
whose entity reports nothing for longer than the limit is a fault. Any
report counts, even one that changes nothing: Foyer reads Home Assistant's
`last_reported`, which the
[state object documentation](https://www.home-assistant.io/docs/configuration/state_object/)
describes as updated whenever the state is written, whether or not it
changed. The limit may be set from 60 seconds to 7 days.

- **A 433 MHz contact that reports only on change: leave it off.** A door
  that stays closed for a week sends nothing for a week, and a limit would
  fault it.
- **A sensor that checks in on a schedule:** set the limit longer than that
  schedule, sensor by sensor. Through the MQTT binary sensor, a check-in that
  repeats the same state reaches Home Assistant only with
  `force_update: true`; without it, the entity is not written and the limit
  would fault a healthy sensor — use the sensor's own `expire_after`
  instead, longer than the check-in interval.
- **A panel integration:** whether it writes an unchanged state on every
  poll is up to the integration. Set a generous limit and watch the *Health*
  column on *Test & diagnostics* for a day. If the zone shows *Fault: silent
  too long* while the sensor is fine, the integration does not report
  unchanged states, and the limit belongs off.

Then check the whole thing without setting anything off: the
[diagnostics table and the simulator](simulator.md), and a walk test to find
the sensor that never saw you.

---

## Not covered here yet

- Step-by-step instructions for any particular panel, receiver or bridge.
- Which 433 MHz sensors rtl_433 decodes, and whether they report tamper,
  battery or a periodic check-in.
- Panels with no integration in Home Assistant, and the community projects
  for them.
- Whether a given panel integration writes unchanged states on every poll.
- Running the existing panel and Foyer armed at the same time.
- Wiring diagrams for programmable outputs and inputs.
