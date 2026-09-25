# Questions people ask

**English** · [Italiano](faq.it.md)

This page collects the questions people ask before installing Foyer and during
their first weeks with it. Every answer is short and links the document that
explains it properly. If something has already gone wrong,
[troubleshooting](troubleshooting.md) is the better place to start.

---

## I already have the sensors. Why would I want an alarm?

Most people who end up here already own the hardware and have never thought of
it that way.

You put a contact sensor on the front door because you wanted the hall light to
come on. You put one on the bedroom window so you would be told it was open
before the rain started. You put a PIR in the corridor for the night light, and
another in the kitchen so the extractor fan would notice somebody cooking. Two
winters later the house is full of exactly the sensors a burglar alarm is made
of, and they are being used to switch lamps.

Then you ask what an alarm costs. Somebody comes round, quotes a figure that
makes you blink, and proposes to drill holes for a contact on the front door and
a PIR in the hall: the two sensors already screwed to your doorframe. And then
there is a monthly subscription, because the keypad has to phone somebody.

So what is missing is not the hardware. It is the discipline around it: areas
that arm separately instead of one all-or-nothing switch, an entry delay that
survives a restart, a zone that declares what "open" means for it rather than
assuming `on`, one incident instead of nine notifications at once, a log you can
still read in three weeks, and a way to check the whole lot without setting
anything off at two in the morning. That is what Foyer adds, and it takes an
evening of configuration. [Getting started](getting-started.md) walks through
that evening.

## Couldn't I do this with automations?

You could, and the first version works. What takes the next six months is
everything else, and Foyer is built around exactly those parts:

- **A restart halfway through an entry delay.** Foyer saves area states, running
  delays, a siren's cutoff and escalation progress on every change and restores them when Home
  Assistant starts again. The log records the gap, so it never implies the house
  was watched while Home Assistant was down.
- **A sensor that went `unavailable` three weeks ago** and has been read as
  "closed" ever since. In Foyer an entity that is `unavailable` or `unknown` is a
  fault: it blocks arming, is logged and shows up in diagnostics. See
  [zones](zones.md).
- **Three notification storms from one break-in**, because every zone fired its
  own automation. Foyer groups the zones of one break-in into one incident, with
  one escalation and one acknowledgement. See
  [response profiles](response-profiles.md).
- **"Was the kitchen actually armed at 02:14?"**, asked after Home Assistant's
  recorder has purged that night (it keeps ten days by default). Foyer keeps its
  own log in a separate database, thirty days per category by default. See
  [privacy](privacy.md) for what it contains.

Your automations are still welcome. Every row Foyer writes to its log is also
fired on Home Assistant's event bus as `foyer_event`, so an automation can
listen for any of them. And a response profile can call any Home Assistant
service through its `call_service` action.

## Who can disarm it?

Whoever holds a code, and only where their permissions allow: the *Disarm*
permission, and only in the areas their person is allowed. The code is checked
by Foyer's backend, never by the card or the panel, so calling the service
directly from Home Assistant does not get around it.

Until the first person with a code exists, nothing asks for a code and anybody
with access to Home Assistant can disarm. The panel says so on the Overview for
as long as that lasts, because enforcing a code nobody holds would only make the
house impossible to disarm.

A person can be exempted from typing their code where Home Assistant already
knows who they are: the Home Assistant interface, signed in as their own linked
account. On a shared keypad the code *is* the identity, so the exemption never
applies there. A tag declared under *Arming devices* acts as the person it names
without any code, which is why the tag editor warns that a stolen tag arms and
disarms.

Being a Home Assistant administrator identifies nobody: the unlocked wall tablet
is almost always signed in as one. So an administrator is asked for the code
like anybody else whenever the policy asks for one. What an administrator keeps
is that wrong codes never lock them out of the panel, the card, Home
Assistant's own alarm panels or the `foyer.*` services. The full picture is in the
[security model](security-model.md).

## Can I arm from Home Assistant's own cards, or by voice?

Yes. Home Assistant's alarm cards, the more-info dialog, tiles and voice
assistants all talk to Foyer's alarm panel entities (one per area, plus
*Whole house*), and Foyer answers each request as it does everywhere else.

What Home Assistant asks for first depends on one thing Foyer tells it: whether
arming needs a code. Foyer says yes only while your code policy asks for one to
arm (it does not, by default) and nobody could use the exemption above: it
counts only for a person who has it switched on, is enabled, is linked to a
Home Assistant account and is inside their validity window.
The reason is that Home Assistant acts on that answer before Foyer sees who is
asking: while it is yes, Home Assistant refuses every arming that comes without
a code, the exempt person's included.

- **While Foyer says a code is needed**, the dialog and a tile's arm buttons ask
  for it. *Whole house* says so as soon as one mode it can still arm asks for a
  code, so a mode that needs none is then refused by Home Assistant until a code
  is typed, even from an automation. Give that automation the code, or arm the
  scenario with Foyer's own `foyer.arm` service.
- **While somebody can use the exemption**, Home Assistant asks for nothing. The exempt
  person arms with no code; anybody else Foyer wants a code from is refused by
  Foyer, with a row in the log and a message saying where to type one: Foyer's
  card, the Home Defender panel, or Home Assistant's *Alarm panel* card, which shows
  a code field wherever a code may be asked but offers arming only while the
  panel is disarmed.
- **Changing mode while the house is armed** is a change of scenario, which asks
  for a code by default even where arming does not. The dialog asks for a code
  only while arming is said to need one, so where only the change asks, type the
  code in Foyer's card or the panel.

Voice assistants read the same answer. Alexa is offered a panel only while
arming it needs no code; it sends none and does not wait for Foyer's answer,
so a refusal shows only in the panel's state and in the log. Google Assistant asks for its PIN before arming only
while a code is needed, but sends the PIN stored in its own configuration
whether it asked or not: if that PIN is somebody's Foyer code, the request is
made in their name; if not, it is a wrong code and counts towards the lockout.

A voice assistant acts as the Home Assistant account it is linked with, for
whoever is speaking. Linked through an exempt person's account, it hands that
exemption to anybody within earshot, and a Google PIN that is a Foyer code does
the same. How to link one safely is in the
[security model](security-model.md). The card is described in [card](card.md).

## I am the administrator and I have no code

This happens in a house where others hold codes, or when your own Foyer person
was disabled or has run past its validity window. Recover access from
**Settings → Devices & services → Foyer Home Defender → Configure**.

Choose your Home Assistant account and type a new code. Only administrators'
accounts are listed, because Home Assistant does not tell Foyer who opened the
window. The person linked to that account is enabled, its validity window is
removed and its code is replaced; an account with no linked person gets a new
one, with every permission. The code must have the length set in Foyer and must
not already belong to anybody; offering one that does counts as a wrong code.

It is never quiet. The recovery is written in the log, shown as a Home
Assistant notification and sent to every enabled contact, each naming the
account. Anybody who is not an administrator is given a way in from the *Users*
page.

## Does it work without internet?

Yes. Foyer needs no cloud account and no MQTT broker, and makes no outbound
connection of its own except the external watchdog's ping, and only once you
have given it a URL (see [system health](system-health.md#the-external-watchdog)).

Whether your *notifications* survive a cut line is a different question. A push
notification does not. That is why an escalation is a list of channels rather
than one, and why at least one local channel, such as a USB GSM modem, belongs
somewhere in that list. [Resilience](resilience.md) explains what survives a
power cut or a cut fibre, and [notification channels](notification-channels.md)
has the recipes.

## Will my configuration survive an update?

Yes: the stored configuration is versioned and migrated on update, and
[settings](settings.md) explains how, including why going back to an older
release can be refused.

## What happens if I remove the integration?

Its configuration, entities, sidebar panel and retained MQTT message go with it.
The log database stays unless you switched on the option to delete it, and
camera snapshots are never deleted; [privacy](privacy.md#when-foyer-is-removed)
has the whole list.

## Is it available in my language?

English and Italian today, including the panel, the card, the contextual help
and the messages Foyer sends. Adding a language touches no code:
[CONTRIBUTING](../CONTRIBUTING.md#adding-a-language) names the two files to
translate.

## Can I run Foyer next to another alarm integration on the same sensors?

Not on the same sensors: [migrating from Alarmo](migrating-from-alarmo.md#running-both-side-by-side)
explains why, and how to move over gradually.

## Is there an ESPHome keypad?

Not one this project maintains in v1. A DIY ESPHome build fits the contract like
any other keypad: it can publish to the MQTT topic, call `foyer.arm` and
`foyer.disarm`, or talk to Foyer's device endpoint.
[Keypads](keypads.md#choosing-the-hardware) compares the hardware and describes
all three routes.
