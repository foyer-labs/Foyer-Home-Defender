# Resilience

What survives when somebody cuts the power, and what does not.

This is the shortest honest summary of everything below: **a project that
promises alarm notifications over the internet alone is making a promise it
cannot keep.** Every push notification, every Telegram message and every
Twilio call travels over a connection that stops when the router stops, and
the router stops when the power does. Somebody who wants your alarm to stay
quiet does not need to defeat it. They need to find the meter cupboard.

Foyer cannot fix this. What it can do is say so, tell you the moment it
happens over a route that still works, and make sure something outside the
house notices when it goes quiet.

---

## The attack, plainly

It takes about ninety seconds and no skill at all.

1. **The power goes off** at the meter or the consumer unit, both of which are
   very often outside the front door or in an unlocked cupboard.
2. **The router dies immediately.** It has no battery. Home Assistant may well
   die with it.
3. **Every internet-dependent channel is now gone.** The push notification
   cannot leave. The Telegram message cannot leave. The voice call cannot be
   placed.
4. **The sirens are silent** if they were mains-powered, which most are.

Nothing about this is theoretical, and nothing about it is sophisticated. It
is the reason professional panels have a battery, a sounder with its own
battery, and a GSM dialler.

The fibre-cutting version is the same story with one step removed: the power
stays on, Home Assistant keeps running, the sirens still sound, and every
message still fails to leave.

---

## The four things that actually help

In order of how much they buy for what they cost.

### 1. A UPS on the router — and on whatever runs Home Assistant

This is the single highest-value thing on this page.

A small UPS keeping the router, the modem and the Home Assistant machine alive
for thirty minutes converts the attack above from "the alarm went silent" into
"the alarm called me and told me the power went out". Thirty minutes is far
longer than the event.

Two details worth getting right:

- **The modem as well as the router.** On fibre and cable these are often two
  boxes and only one is behind the UPS.
- **Home Assistant needs one too.** A running router with nothing to speak
  through is half the job.

A UPS also gives you the mains sensor: over NUT, or through a smart plug, it
becomes an entity, and [page 14](system-health.md#mains-power-and-the-ups)
turns a power cut into a notification that goes out while the battery still
has thirty minutes in it.

### 2. One channel that does not need the internet

A USB GSM modem with its own SIM, driven by Home Assistant's `sms`
integration, is the only notification channel in this document that survives
the fibre being cut. It costs about the same as one good door contact.

Put it in a contact's channel list, at any position — an escalation that
starts with a push and falls back to SMS after sixty seconds is the usual
shape, and it means the SMS is only ever sent when the push was not answered.
See [notification-channels.md](notification-channels.md).

Its own limits, since this page is for stating them:

- It needs mains power like everything else, so it belongs behind the UPS.
- It needs cellular coverage where it sits, which is usually a cupboard.
- A determined attacker with a jammer defeats it, which is a different class
  of person from the one who found the meter cupboard.

Test it from page 6. A GSM modem that was misconfigured is exactly the failure
the test button exists to prevent.

### 3. An external watchdog

Foyer pings a URL you choose; if it stops, that service tells you. It is the
only answer to the fact that a dead system cannot report its own death.

The power cut above stops the pings within one interval, and the alert comes
from somewhere that is not your house. This is not a substitute for the UPS —
it tells you afterwards rather than at the time — but it is free, it takes two
minutes to set up, and it is the only thing on this page that works when Home
Assistant itself is what failed.

Set it up on [page 14](system-health.md#the-external-watchdog). **Host it
somewhere else.** A watchdog running on the same machine, or on another
machine in the same house, dies with it and protects nothing.

### 4. Sounders that are not on the affected radio

Two separate points that both come back to the same idea.

A siren that runs on mains power stops when the power does. A siren with its
own battery does not, and a self-powered external sounder is what a
professional installation uses for precisely this reason.

And a siren on the Zigbee network is useless in the one case
[radio interference](system-health.md#radio-interference) describes — Foyer
will not even try to use it then, and will say so. A wired sounder, or one on
a different radio, is what is left.

---

## What Foyer does about it

| Failure | What Foyer does |
|---|---|
| Mains lost | `system_power_lost` at once, at alarm severity, over whatever channel still works. A profile can act on it. |
| Home Assistant dies | The pings stop and the external watchdog alerts. On the way back, the gap is logged: the log never implies the house was covered when it was not. |
| Internet lost | Three failed pings and Foyer reports it locally — the earliest warning that no internet-based notification would go out. |
| A channel breaks | Found by the sweep or by a failed send, shown on the Contacts page, and announced over a channel that still works. |
| The radio goes quiet | Reported, and not answered through that radio. |

All of it is on [page 14](system-health.md), and none of it touches the
intrusion state machine.

---

## What Foyer cannot do about it

Said once, plainly, because the rest of this page reads better with it in
mind:

- **It cannot notify you over a connection that does not exist.** Nothing can.
- **It cannot sound a siren that has no power.**
- **It cannot keep running when Home Assistant is not running.** The restart
  gap is logged precisely because the alternative is a system implying it was
  watching when it was not.
- **Nobody is monitoring.** Foyer notifies the people you listed, over
  transports it does not own. An escalation that reaches nobody is an outcome
  the household has to have planned for — which usually means one contact who
  is not in the house.

Foyer is not a certified alarm system, and none of the above is a defect to be
fixed in a later version. They are the shape of building an alarm out of
consumer hardware on a house's own network and power, and the honest thing to
do with them is document them.

---

## A sensible baseline

For a household that wants one answer rather than a menu:

1. A UPS covering the router, the modem and Home Assistant.
2. A USB GSM modem as the second channel of at least one contact.
3. An external watchdog on healthchecks.io or Uptime Kuma, pinged every
   fifteen minutes.
4. The UPS's own status as the mains entity on page 14.
5. One self-powered external sounder, not on a radio.
6. At least one contact who does not live in the house.

That is perhaps a hundred and fifty euros of hardware, and it is the
difference between an alarm that goes quiet when somebody opens the meter
cupboard and one that calls you while it is happening.
