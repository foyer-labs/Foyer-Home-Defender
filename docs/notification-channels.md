# Notification channels

**English** · [Italiano](notification-channels.it.md)

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
  Telegram message and the Twilio call with it.
  [resilience.md](resilience.md) is the document that says what to do about
  it; the short version is a UPS on the router and at least one local GSM
  channel somewhere in the list.
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

**Set the list up with the house disarmed.** While any area is armed, a
contact that a profile the house could answer with names — at once or as an
escalation step — cannot be changed, switched off or deleted: the number, the
service, the quiet hours and the person it is linked to all decide who hears
the alarm. Every one of its channels counts, because a step that names none,
or names one switched off, goes over the first channel still enabled. A
rule's contacts are not held: they hear the rule, not the alarm.

**A note on the service names below.** The Companion app, Pushover and the GSM
modem create a service with a fixed name. The rest are YAML `notify:`
platforms, whose service is named after the `name:` you give the platform —
leave it out and Home Assistant creates `notify.notify` instead. The names
here assume you set `name:` to match, and the dropdown on page 6 shows you
what this installation really has.

---

## Home Assistant Companion app

The channel most households already have, and the only one in this document
whose button comes back to Foyer.

**Service:** `notify.mobile_app_<device>`, created by the app itself when it
signs in. If the service is missing, the phone has not completed setup.

**Actionable notifications.** Tick *Can carry an acknowledge button* on the
channel. Foyer then sends the notification with an action whose id is
`FOYER_ACKNOWLEDGE`, and listens for the `mobile_app_notification_action`
event the app fires when it is pressed. Nothing else is needed: no automation,
no blueprint. The acknowledgement goes through the same check every other one
does, and the log records the contact the notification had gone to.

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

**What comes back.** The action carries which alarm it belongs to and which
contact it was sent to, and Foyer reads them from the event and from
`action_data`, whichever the app fills in. An answer that arrives with neither
still acknowledges: it acknowledges **both** the intrusion incident and the
technical channel, for the same reason `button.foyer_acknowledge` does — the
person pressed a button that says "I have seen it", and guessing which alarm
they meant is how a smoke detector closes a burglary.

**Android.** These five keys keep the notification out of the battery-saving
queue and out of the notification drawer's quiet pile:

```yaml
ttl: 0
priority: high
channel: Foyer alarm
importance: high
media_stream: alarm_stream_max
```

The last one is the part that matters at four in the morning, and the part
that is not simply "delivered promptly": it plays the notification at alarm
volume, through the silent switch and through Do Not Disturb. The app asks for
the Do Not Disturb permission the first time, in its own settings, so — again
— send a test from page 6 with the phone in your hand.

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
TwiML gathers a digit and posts to Foyer's acknowledgement webhook.

```xml
<Response>
  <Gather numDigits="1" action="https://example.org/api/webhook/YOUR_ID" method="POST">
    <Say language="en-GB">Foyer alarm. Press 1 to acknowledge.</Say>
  </Gather>
</Response>
```

**Foyer does not read the digit.** The POST itself is the acknowledgement:
whichever key was pressed, and whatever else can reach that URL, answers the
alarm. `<Gather>` only posts when a key is pressed, which is what makes the
recipe work — but it is worth knowing that the digit is not a second check.

By default this acknowledges the intrusion incident. To answer the technical
channel instead — a call placed about the smoke detector — put it in the
action's query string, which is the part of the URL you control:
`…/api/webhook/YOUR_ID?target=technical`.

And if this installation has raised the code policy for acknowledging (page 7;
it needs no code by default), then neither this nor the button in a push
notification can answer at all: a webhook carries no code. Leave that one
operation codeless, or do not rely on these two paths.

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
- the address is shown once, when it is generated — the whole URL when Home
  Assistant knows its external address, the path otherwise, for you to put
  that address in front of — and Foyer cannot show it again. Copy it into the
  voice provider then. To see it again, generate a new one on page 6, which
  stops the old one at once;
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

## A notify entity is not a notify service

Both appear in the dropdown, and they are not equivalent. A `notify.*`
**service** takes a title, a target and whatever extra data the transport
understands — which is what carries an iOS critical alert, a Telegram photo or
the acknowledge button. A notify **entity** takes a message and a title and
nothing else; everything else is dropped, and Foyer says so in the Home
Assistant log rather than letting it vanish.

So: for a channel that needs to do more than say a sentence, pick the service.
Page 6 says the same thing beside the tick-box.

## What Foyer sends

A notification carries the message the action renders, with the fixed variable
set of §6.4 — `{{ zone }}`, `{{ area }}`, `{{ incident_zones }}` and the rest —
and whatever the channel's own extra data adds. Nothing about the house is put
in a message you did not write: the principle of §2.1 is that everything
leaving the house starts at the minimum that works, because a message is read
by whoever holds the other end.

The one thing Foyer adds by itself is the acknowledge action, and only on a
channel declared able to carry one.

## Answering a duress code

A duress code does everything its owner's ordinary code does, and each time it
is used Foyer raises one silent event, `duress` — for a disarm, but just as
much for an arming, an excluded zone, a walk test, a settings page, a device
unlocked or a request that was refused. Whoever is standing beside the person
typing it sees nothing different; the message is the only place it shows.

Four things decide how to answer it:

- **Only the default profile answers `duress`.** It belongs to no area and to
  no incident, so an area's or a scenario's profile is never asked. Put the
  action on the profile chosen as the default under *Settings*.
- **Nothing answers it until you add an action.** The profile a new
  installation starts with does not: its only action is a Home Assistant
  notification.
- **A Home Assistant notification is the wrong answer.** It appears on every
  Home Assistant screen, the wall tablet the code was typed at included. So is
  anything the house does out loud: `duress` always runs silent, and the kinds
  on the silent list — the siren, speech and the chime by default — are left
  out of its answer whatever the profile says. The profile editor warns about
  both.
- **Send it to somebody outside the house**, through a contact or a `notify.*`
  service, with a message that says what happened:

```
{{ user }} used a duress code at {{ time }}: {{ operation }} {{ area }}
```

`{{ operation }}` names what the person was made to do — `disarm`, `arm`,
`bypass_zone`, `edit_config`, `export_log`, `unlock`, and for a switch the way
it went: `walk_test` and `end_walk_test`, `auto_arming_on` and
`auto_arming_off`, `chime_on` and `chime_off` — and `{{ area }}`,
`{{ scenario }}` and `{{ zone }}` what the request named. It never escalates:
there is nothing to acknowledge, so choose a channel that reaches somebody the
first time. A request made with it again two minutes later is a second
message, because it is a second thing the person was made to do.

The `duress` row is on the log page and in an export, and nowhere a glance
would find it: not on the Overview, not in `sensor.foyer_last_event`, not in
an API device's log. It is on Home Assistant's event bus as `foyer_event`,
like every row, which is how an automation of yours can answer it too — and
why an automation that shows security events somewhere in the house must
leave `duress` out.

The bus hears only what the log writes. A `duress` row is written, and sent
as `foyer_event`, even with the `security` category switched off under
*Settings*; with a log that could not be opened there is no `duress` row and
no `foyer_event` for it either. The default profile's answer does not depend
on the log, and is the one to rely on.

What a duress answer sends is judged by the channel sweep alone
([system health](system-health.md#notification-channel-health)): a channel it
finds broken is still reported, up to a quarter of an hour later rather than
seconds after the code was typed.

---

## When a send fails

The step is recorded as failed in the log, under `action`, with the error the
transport gave — and a send to a contact's channel is retried once, a few
seconds later, for the service that is not ready yet after a restart. (A
notification that names a service directly, rather than a contact, is not
retried.) The retry runs on its own, so the alarm does not wait for it, and
the escalation carries on at its own times: a channel that is dead stays dead,
and the next step is what reaches somebody.

Checking that a channel is *still* real — that the service still exists, that
the modem is still registered, that the last send worked — is
[system health](system-health.md#notification-channel-health)'s job, and it
does it on its own. The test button on page 6 is still worth pressing after
every Home Assistant update that touches an integration you notify through.
