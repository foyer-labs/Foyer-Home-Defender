# Settings

**English** · [Italiano](settings.it.md)

The *Settings* page holds what applies to the whole installation rather than
to one area, zone or person: the defaults every area starts from, where every
response ends, the chime, what the log keeps, personal data in the log, the
configuration backup, the importer, and the language Foyer writes its messages
in. This document walks the page in the order the panel shows it and says, for
each setting, what changes if you change it, its default and its bounds, and
where the detail lives. It is for whoever holds `edit_config`, which every
save on this page needs, with a code whenever the policy asks one for editing
the configuration — it does by default.

Most fields save the moment you leave them, and a save reloads the
integration; the chime is the one block with its own *Save* and *Cancel*. A
refused save is said under the card it belongs to, and the field goes back to
the stored value.

Two things are not on this page even though they are global. The code policy,
the code length and the lockout are on the *Users* page, beside the people
they apply to; [the security model](security-model.md) explains them. The
mains, the watchdog, the channel checks and the radios are on *System health*;
see [system-health.md](system-health.md).

---

## While an area is armed

An armed house keeps the answer and the codes it was armed with. While any
area is not disarmed — armed, arming, in its entry delay or triggered — an
edit that would change how the house answers an alarm, or what it asks a code
for, is refused and says why. Otherwise whoever holds `edit_config` could
lower the guard of a house nobody disarmed, and nothing in the log would read
as a disarm.

Every global setting is on one side of that line or the other, and a test
fails if a new one arrives on neither, so a setting added later cannot land on
the free side because nobody thought about it.

| Kept until every area is disarmed | Free at any time |
|---|---|
| *Sirens sound for*, *Wait for it to close, at most*, *Default entry delay*, *Default exit delay*, *Walk test timeout* | *Low battery below* |
| *Default profile*, *Technical profile*, *A silent zone suppresses*, *Camera folder* | The chime, all of it |
| The code policy, the code length and the lockout (*Users* page) | The log: categories, retention, the short preset |
| Whether an automatic rule may disarm (*Automatic rules* page) | Personal data in the log, including the uninstall switch |
| The radios and interference thresholds (*System health* page) | *Language of messages* |
| | The backup download |
| | Whether the first-run wizard is done |

The two cards whose fields are kept say so at the top while an area is armed.
The *Automatic rules*, *Users* and *System health* pages hold the others, and
refuse them in the same way. Profiles an armed area could answer with, and the
contacts they name, are kept too; [response-profiles.md](response-profiles.md)
says which.

---

## Defaults

*What new areas start with, and the limits that apply to every area.*

| Setting | Default | Bounds | Armed |
|---|---|---|---|
| *Sirens sound for* | 180 s | 1–900 s | kept |
| *Wait for it to close, at most* | 300 s | 60–1800 s | kept |
| *Default entry delay* | 30 s | 0–300 s in the panel | kept |
| *Default exit delay* | 30 s | 0–300 s in the panel | kept |
| *Low battery below* | 20 % | 1–100 % | free |
| *Walk test timeout* | 900 s | 60–3600 s | kept |

**Sirens sound for** is the siren cutoff: how long an area stays triggered
before its sounders stop and it returns to the state it was in before the
alarm. The ceiling of 900 seconds is the EN 50131 reference for outdoor
sirens, and no value above it is accepted. A scenario may set a shorter or
longer time of its own within the same bound — a night scenario may
reasonably sound for less than a daytime one — and a disarm stops the sirens
sooner. The alarm memory stays after the cutoff until the area is disarmed or
armed again.

**Wait for it to close, at most** applies only to zones whose arm policy is
*Arm after closing*: how long after the exit delay such a zone may stay open
before the arming fails as if the zone had blocked it. A zone can carry its
own value; this is what it uses when it does not. See [zones](zones.md).

**Default entry delay** and **Default exit delay** are what the backend gives
an area saved without delays of its own. The *Areas* page does not send one
that way: it starts every new area at 30 s for both, whatever these settings
say, so set a new area's delays there. The panel offers 0–300 s for both;
each area's own delays are held to 0–300 s when saved. Existing areas keep
theirs; a zone can override
the entry delay and a scenario the exit delay. See [zones](zones.md).

**Low battery below** decides when a numeric battery entity counts as low. A
low battery warns and never blocks arming, which is why this one stays free
while armed; a battery `binary_sensor` is read by its own `on` instead. See
[simulator.md](simulator.md#batteries).

**Walk test timeout** is how long a walk test runs without a detection before
it ends itself. Each detection pushes it back, and a cap of three hours from
the start ends it whatever happens. The automatic end is mandatory, so no
value here switches it off. It is kept while armed because a walk test quiets
areas somebody else armed as well. See
[simulator.md](simulator.md#walk-test--which-zones-never-saw-you).

---

## Response

*Where every inheritance chain ends, and what a silent zone keeps quiet.*
Everything in this card is kept while an area is armed.

- **Default profile** — what every area, zone and scenario inherits unless it
  overrides it, and the only profile that answers a moment belonging to no
  area, such as a duress code being used. A new installation starts with one,
  created when Foyer is set up.
- **Technical profile** — what smoke, gas and flood zones answer with when the
  zone has no profile of its own, whatever the house is doing: a detector must
  not answer differently depending on how the house is armed. Empty, the
  default profile answers.
- **Camera folder** — where camera snapshots and recordings are written,
  relative to the configuration folder, `media/foyer` by default. An absolute
  path, `..` and any folder under `www` are refused, because Home Assistant
  serves `www` without authentication and the inside of a house is not
  something to publish. The folder must also be in Home Assistant's
  `allowlist_external_dirs`, or nothing can be written there.
- **A silent zone suppresses** — the action kinds a zone marked silent runs
  its response without: *Siren*, *Spoken message* and *Chime* by default, any action kind
  allowed. Silence belongs to the zone; another zone joining the same incident
  still sounds.

The inheritance chain, the silent list and the cameras are explained in
[response-profiles.md](response-profiles.md).

---

## Chime

*Sounds when a zone with the chime switched on opens while its area is not
armed* — per area, so with only the perimeter armed an internal door still
chimes. The whole block is free while armed, and it is saved with its own
*Save* button.

- **Play on** — media players, sirens, and `notify` services or entities.
  Nothing chimes until one is ticked. Each target may carry *Quiet from* /
  *until* of its own, which replaces the global window for that target.
- **Mode** — *Single sound*, or *Speak the zone name* through the
  *Text-to-speech* entity chosen beside it. With a single sound, *Media to
  play* is what a media player plays. In either mode, a siren sounds for one
  second if it supports a set duration, and is skipped otherwise.
- **Volume** — per cent, 0–100. Empty leaves the player's volume as it is.
- **Quiet from** / **until** — no chime inside this window, which may cross
  midnight. Empty: never quiet.
- **Also during the exit delay** — off by default, so the door you leave by
  does not chime while its area counts down.

Each zone has its own chime switch, and `switch.foyer_chime` silences the
chime without touching these settings. No zone chimes during a walk test. See
[zones](zones.md).

---

## Event log

*Which categories are recorded, and for how long each is kept.* Free while
armed.

Each of the eight categories — *Arming*, *Alarm*, *Action*, *Configuration*,
*Security*, *System*, *Zone activity (armed)*, *Zone activity (disarmed)* —
has a switch and a retention in days: 30 by default, 1 to 3650. Every
category is on by default except *Zone activity (disarmed)*, which a
living-room PIR fills with thousands of rows a day; switch it on while
diagnosing and off again after.

A category switched off writes nothing from then on. The rows it has already
written stay until their days are up. Switching off *Security* has a
consequence worth reading before you do it: wrong codes, lockouts and duress
codes are no longer recorded, and no `foyer_event` is sent for them, so an
automation answering a duress code stops hearing it. The default profile
still answers it.

**Shorten to 7 days** sets *Arming*, *Alarm*, *Action*, *Security* and
*Configuration* to seven days and leaves the other three alone. It is offered
for homes with domestic staff: those are the categories that name people,
and the others carry faults and door states, which name nobody and are what
you read when a sensor did not react three weeks ago. See
[privacy.md](privacy.md#keep-less-retention-and-the-short-preset).

---

## Personal data in the log

Two settings of the installation; erasing or exporting one person's rows is
done on the *Log* page. Free while armed. See [privacy.md](privacy.md).

- **Replace names in older rows** — off by default. On, rows older than the
  chosen number of days (1–365, starting at 30) keep a stable identifier
  instead of a name. It trades away the answer to "who disarmed that night"
  for every one of those rows, which is the question the log exists to answer,
  and it cannot be undone: switching it off brings no name back. The panel asks
  you to confirm before switching it on, because the first sweep runs at the
  next start and saving any setting is one. Switching it on and off are both
  recorded. See
  [privacy.md](privacy.md#or-let-it-happen-by-itself-timed-pseudonymisation).
- **Delete the log database if Foyer is removed** — off by default. See
  [Removing the integration](#removing-the-integration) below.

---

## Configuration backup

*Nobody who has configured forty zones will do it twice.*

**Export JSON** downloads the whole configuration as one file. It is never
refused because an area is armed; it asks for `edit_config` and the code, like
any configuration command. The file carries the schema version it was written
with, and the card shows the version of the configuration stored now.

A backup never contains a credential. Codes and duress codes are left out as
hashes and as anything else; so are a keypad's token, the acknowledgement
webhook's address and the watchdog URL. A backup is a file that leaves the
machine, and a code hash in it would be a guessing exercise done offline. It
does carry each person's pseudonymisation identifier, so that a restore does
not detach the rows already pseudonymised; and it does not carry the log.

**Restore from a file…** replaces the configuration with the file's:

- A file from an older schema is brought up to date by the same steps a real
  upgrade uses. One written by a newer major version is refused rather than
  half-read.
- It then goes through the same validation as any edit, and while an area is
  armed it is refused exactly where the same change made on its own page would
  be.
- A restore that adds, removes or changes a person, a tag, the person a key
  switch acts as, or the people allowed to use a scenario needs `manage_users`
  as well as `edit_config`. Otherwise `edit_config` would be a way to hand
  oneself every permission, or somebody else's key.
- Credentials stay the installation's, because nothing in a file can set one.
  A person already here under the same id keeps their codes; a person new to
  this installation arrives with none. A keypad on the device endpoint already
  here keeps its token; any other waits for one to be generated on *Arming
  devices*. The webhook and the watchdog URL stay as they are, and a watchdog
  the file says is on comes back only once a URL is stored.
- A zone this installation holds with its trigger unconfirmed stays
  unconfirmed unless the file changes its trigger: editing a file to say
  `true` is not somebody checking the sensor.

The same export and restore are the `foyer.export_config` and
`foyer.import_config` services, with the same checks.

**Will my configuration survive an update?** Yes. The stored configuration is
versioned and migrated step by step on upgrade, and every changelog entry says
whether the schema moved. Going *back* across a major schema step is refused on
purpose rather than half-read: an older build that silently ignored what it did
not understand could silently stop protecting something.

---

## Import from Alarmo

Reads Alarmo's configuration from this Home Assistant and brings its areas,
sensors, modes and people in beside what is already here. **Read from Alarmo**
shows what it would create and everything it could not bring across; nothing
is written until you press **Apply**. Zones arrive switched off until you
confirm each trigger on the *Zones* page, and nobody arrives with a code. The
apply goes through the same validation and the same armed-area refusal as a
restore. What it converts, what it cannot, and what to check afterwards are
in [migrating-from-alarmo.md](migrating-from-alarmo.md).

---

## Language of messages

**Language of messages** is the language of what Foyer sends out — the words
it writes itself in notifications, their buttons, and the Home Assistant
notifications it puts up. It is not the panel's language: the panel follows
each Home Assistant user's own, so a second selector for it would be a bug
generator, while the house has one language for its messages even when the
phone reading one does not. *As Home Assistant*, the default, follows the
language Home Assistant runs in, read at the moment of sending. The list is
the languages Foyer ships. A message you wrote yourself in a response profile
is sent as you wrote it. Free while armed.

---

## Removing the integration

Removing Foyer from *Devices & services* takes with it its configuration, its
saved alarm state, every entity and device it created, the sidebar panel, its
repair issues, the notifications it put up and its retained MQTT message — a
retained message outlives the integration and would keep telling whoever
connects to that broker next what the house was doing.

The event log database goes only if you said so beforehand, with **Delete the
log database if Foyer is removed** on this page, off by default. Home
Assistant's own confirmation is the last dialogue there is, so the question is
asked in advance, and keeping is the answer that cannot destroy something
nobody meant to destroy. Left off, the file stays in the configuration
directory as `foyer-log.db`.

Camera snapshots are never deleted. They are pictures of the inside of the
house, in a folder you chose, which may hold files that were never Foyer's, so
removing them is left to you. [privacy.md](privacy.md#when-foyer-is-removed)
has the detail.

---

## The first-run wizard

Whether the first-run wizard is done is stored with these settings, but it is
not a field on this page. The wizard sets it when it is finished or dismissed,
and it belongs to the installation rather than to whoever opens the panel. It
is free while armed. See [getting-started.md](getting-started.md).

---

## Not covered here yet

- Screenshots of the page.
- The *Users* page's code policy, code length and lockout fields, beyond the
  pointer above.
