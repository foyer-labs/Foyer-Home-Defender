# Notification channels

Recipes for the transports an escalation reaches people through, and what each
one is honestly worth when the house is being broken into.

Three things are worth reading before configuring anything:

- **Foyer implements no transport.** Home Assistant already has `notify.*`
  integrations for push, SMS, voice calls and messaging. Foyer orchestrates
  them: it decides who is told, in what order, and when to stop. Whatever a
  channel needs — a phone number, a chat id, a priority — it takes untouched
  and hands to the service.
- **Every internet-dependent channel fails at exactly the wrong moment.**
  Somebody who cuts the power or the fibre has cut the push notification, the
  Telegram message and the Twilio call with it. `docs/resilience.md` says this
  at length; the short version is a UPS on the router and at least one local
  GSM channel somewhere in the list.
- **Test every channel from page 6.** The button beside each one really sends.
  The failure this prevents is discovering during the emergency that the
  emergency channel was misconfigured, and it is the reason the button exists
  at all.

---

## Choosing the order

A contact's channels are an ordered list, highest priority first, and an
escalation step names the channel it wants. A list that reads well:

| Step | Channel | Why |
|---|---|---|
| +0 s | Companion app push | Free, instant, and it can carry the button that stops everything |
| +60 s | SMS through a local GSM modem | Survives the fibre being cut, and needs no account anywhere |
| +120 s | A second person's push | The first phone may be in a pocket at a concert |
| +300 s | Voice call | The only channel that wakes somebody asleep |

The rule behind the table: put the channel that survives a cut internet
connection **somewhere in the list**, not at the bottom. A list whose first
three steps all depend on the same router is one step long.

---

## Home Assistant Companion app

The channel most households already have, and the only one in this document
that Foyer can hand an acknowledgement button to.

**Service:** `notify.mobile_app_<device>`, created by the app itself when it
signs in. If the service is missing, the phone has not completed setup.

**Actionable notifications.** Tick *Can carry an acknowledge button* on the
channel. Foyer then sends the notification with an action whose id is
`FOYER_ACKNOWLEDGE`, and listens for the `mobile_app_notification_action`
event the app fires when it is pressed. Nothing else is needed: no automation,
no blueprint. The acknowledgement goes through the same check every other one
does, and the log records the contact and the channel that answered.

**iOS critical alerts.** An alarm at four in the morning is exactly what they
exist for: they sound through Focus, Do Not Disturb and the silent switch. Put
this in the channel's extra data:

```yaml
push:
  sound:
    name: default
    critical: 1
    volume: 1.0
```

The phone asks for permission the first time one arrives, and refuses them
silently until it is granted — so send a test from page 6 while the phone is in
your hand, not while the house is being burgled.

**Android.** The equivalent is a high-importance channel plus
`ttl: 0` and `priority: high`, which keeps the notification out of the
battery-saving queue:

```yaml
ttl: 0
priority: high
channel: Foyer alarm
importance: high
```

---

## Pushover

**Integration:** `pushover`. **Service:** `notify.pushover`.

Priority 2 is the one worth configuring: the message repeats until the person
acknowledges it *in Pushover*, which is a second acknowledgement in a second
place and has nothing to do with Foyer's. Use it for the step that must not be
missed, and keep an ordinary priority for the earlier ones.

```yaml
priority: 2
retry: 60      # seconds between repeats, at least 30
expire: 600    # give up after this long
sound: siren
```

Pushover refuses priority 2 without both `retry` and `expire`, so a channel
missing either fails at the moment it is used. Test it.

---

## Twilio SMS

**Integration:** `twilio` plus `twilio_sms`. **Service:** `notify.twilio_sms`.

The target is the destination number in international form, `+39…`. Costs a
fraction of a cent per message and arrives on any phone, including one with no
data connection — but it goes through Twilio, over the internet, from this
house: it dies with the fibre exactly like the push did.

---

## Twilio voice call

**Integration:** `twilio_call`. **Service:** `notify.twilio_call`.

A call is the only channel in this document that reliably wakes somebody.
Twilio reads the message with its own text-to-speech, or fetches TwiML from a
URL you host.

**The DTMF keypress.** §7.2 of the specification lists "a key press during the
call" among the four ways to acknowledge, and this is how it is wired: the
TwiML gathers a digit and posts it to Foyer's acknowledgement webhook.

```xml
<Response>
  <Gather numDigits="1" action="https://example.org/api/webhook/YOUR_ID" method="POST">
    <Say language="en-GB">Foyer alarm. Press 1 to acknowledge.</Say>
  </Gather>
</Response>
```

**Read this before switching the webhook on.** A Home Assistant webhook is
**not authenticated**. Whoever holds that URL — or intercepts it, since the
phone provider and every hop in between sees it — can acknowledge an alarm in
progress, which means stopping the escalation on its way to your neighbour.
That is the whole of what it can do: it cannot disarm, arm, read the log or
change the configuration. Foyer's position is stated rather than implied:

- the webhook does not exist until you switch it on, on page 6;
- the id is generated by the backend, long and random, and is the only thing
  protecting the URL;
- switching it off forgets the id, so switching it on again hands out a new
  one rather than reviving an address somebody may still hold;
- give the address to the voice provider and to nothing else, over HTTPS.

If that trade is not worth it — and for many households it is not — leave it
off and acknowledge from the push notification, the card, the keypad or
`foyer.acknowledge`. The escalation stops just as completely.

---

## `sms` — a USB GSM modem

**Integration:** `sms` (Gammu). **Service:** `notify.sms`.

The only channel in this document that does not depend on the internet at all.
A €20 USB dongle and a prepaid SIM, and the message leaves the house over the
mobile network — which is still standing when the fibre is cut and, with a UPS
on the Home Assistant machine, when the power is.

Worth knowing before buying:

- the dongle must be supported by Gammu; the Huawei E173 / E3531 family is the
  usual safe answer;
- a prepaid SIM that is never used gets disconnected by most operators after a
  few months. Send yourself a test message from page 6 occasionally: it is also
  the only way to know the SIM still has credit;
- the modem is a serial device. `/dev/ttyUSB0` moves between reboots, so point
  the integration at `/dev/serial/by-id/…` instead.

This is the channel §7.3 recommends every installation have one of.

---

## Telegram

**Integration:** `telegram_bot`. **Service:** `notify.telegram`.

Free, instant, and it carries pictures — which is why the `notify` action asks
which transport a camera attachment is for. Telegram's own server fetches the
picture from outside the house with no session of its own, so it needs a
**file**; the Companion app, which is signed in, is happy with a link to the
camera proxy. Choosing the wrong one produces a message with no picture and no
explanation.

A Telegram bot cannot start a conversation: message the bot once from each
phone that should receive alerts, or the messages go nowhere.

---

## Signal

**Integration:** `signal_messenger`, which needs a
[signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api)
container running somewhere on your network. **Service:**
`notify.signal`.

The most private option here — the message is end-to-end encrypted and Signal
keeps nothing — at the cost of the only setup in this document that involves
running another service and registering a phone number to it. Worth it for
households that already use Signal; not worth it as a first channel.

---

## What Foyer sends

A notification carries the message the action renders, with the fixed variable
set of §6.4 — `{{ zone }}`, `{{ area }}`, `{{ incident_zones }}` and the rest —
and whatever the channel's own extra data adds. Nothing about the house is put
in a message you did not write: the principle of §2.1 is that everything
leaving the house starts at the minimum that works, because a message is read
by whoever holds the other end.

The one thing Foyer adds by itself is the acknowledge action, and only on a
channel declared able to carry one.

---

## When a send fails

The step is recorded as failed in the log, under `action`, with the error the
transport gave — and Foyer retries it once, a few seconds later, for the
service that is not ready yet after a restart. After that the escalation
carries on at its own times: a channel that is dead stays dead, and the next
step is what reaches somebody.

Checking that a channel is *still* real — that the service still exists, that
the modem is still registered, that the last send worked — is system health,
and it lands with the rest of §12. Until then, the test button on page 6 is how
you find out, and it is worth pressing after every Home Assistant update that
touches an integration you notify through.
