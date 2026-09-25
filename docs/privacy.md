# The log is about people

**English** · [Italiano](privacy.it.md)

*Practical information, not legal advice.*

Foyer's event log records who was in the house, when they arrived and when they
left, for thirty days by default. That is personal data about **everyone in the
household**, not only about whoever installed the system — and, sooner or
later, about people who are not in the household at all.

This page says what is in the log, where the household exemption stops
covering it, and what Foyer gives you to do something about it.

---

## What a row contains

One row per event, in Foyer's own SQLite database — `foyer-log.db` in your
Home Assistant configuration directory, deliberately not the recorder, whose
ten-day purge would quietly destroy a thirty-day requirement.

| Column | What it says |
|---|---|
| `ts` | when, to the millisecond, in UTC |
| `category`, `event_type`, `severity`, `outcome` | what happened, and whether it worked |
| `area_id`, `zone_id`, `scenario_id`, `incident_id` | where, and which night it belongs to |
| `user_id`, `user_name` | **who** |
| `channel`, `device_id` | **how** they arrived: the hall keypad, a tag, the app |
| `detail` | a small JSON document — which zones, which profile, what a configuration change altered |

Two of those are more revealing than they look. `device_id` names the keypad
somebody used, and in most houses a particular person uses a particular one;
`channel` distinguishes the person who types a code at the door from the one
who disarms from their phone in bed. Both are "who" once you know the
household, which is why erasing a person takes them as well (below).

**`user_name` is written into every row on purpose.** It is not a reference to
the users page, it is a copy of the name. That is what makes deleting a user
safe — the history of what they did survives them — and it is exactly what
makes erasure a separate operation rather than a side effect.

**Every row also goes on the Home Assistant event bus** as `foyer_event`, so
automations and external log collectors can subscribe. Anything that listened
has its own copy, and nothing Foyer does here reaches it. If you forward
`foyer_event` to something outside the house, that copy is yours to manage.

---

## The household exemption, and where it stops

Under the GDPR, Article 2(2)(c) puts processing carried out "in the course of a
purely personal or household activity" outside the regulation altogether. A
family's own alarm log, kept on their own hardware, read by them, is inside
that exemption. Nobody has to do anything.

**It stops applying the moment the log records somebody else.** Not when you
publish it, not when you share it — when it records them.

- The **cleaner** who comes on Tuesdays, whose arrivals and departures are kept
  for a month.
- The **boiler engineer** let in for a morning, and the tag that was made for
  them.
- The **babysitter**, the dog walker, the neighbour who waters the plants.

And it does not apply **at all** to installations that are not a household:

- a **B&B** or a **holiday let**, where every guest is a data subject and the
  log is a record of when strangers came and went from their room;
- a **small office**, **shop** or **workshop**, where the log is attendance
  data about employees — which in several European countries is regulated
  well beyond the GDPR, by rules about monitoring people at work, and in Italy
  in particular by Article 4 of the Workers' Statute. Ask before you install
  it, not after.

What follows from that is not a licence banner. It is three practical things:
keep less, be able to hand somebody their own data, and be able to take them
out.

---

## Keep less: retention, and the short preset

Retention is already per category, on **page 11 — Settings**, thirty days
everywhere by default, purged daily.

Beside those fields is a **shorten to seven days** button. It sets `arming`,
`alarm`, `action`, `security` and `config` to seven days — `action` among them
because it records who acknowledged an alarm — and **leaves the other three
alone**: `system` and the two `zone_*` categories carry faults, restarts and
door states, which name nobody and are what you read when you want to know why
a sensor did not react three weeks ago. There is nothing to be gained by
shortening those and something real to lose.

Seven days is what an installation with domestic staff usually wants: long
enough to answer "what happened last weekend", short enough that nobody's
movements are on file for a month.

---

## Hand somebody their own data

**Page 10 — Log**, at the bottom: choose a person, and export their rows as
CSV or JSON. The file is named after them, because it is a file you give to
them.

The selection is deliberately **wide**. It carries:

- every row where they are the actor (`user_id`),
- every row naming a **tag that is theirs** — a refused scan is about them,
- every row naming a **contact linked to them** — an escalation that reached
  them on their phone is about them.

A subject access request is about somebody's personal data, not about the rows
whose `user_id` column happens to match, so an export that stopped at the first
of those three would be an answer that left out half the subject.

**Exporting needs the `view_log` permission, and the block it sits in needs
`manage_users`** — the person count above the buttons is part of the erasure,
which is what `manage_users` owns. In practice one person does both. There is
no way for somebody to fetch their own rows without being trusted with the log,
and that is a deliberate limit rather than an oversight: the log is the security
record of a house, and opening a read of it to everyone who appears in it would
be a larger hole than the one it closes. In a household this is not a problem —
the request is made to whoever set the system up, who exports the file and hands
it over. **In a B&B, a let or an office it is an arrangement somebody has to
make**, and making it is part of running one.

---

## Take somebody out

Same page, same block: **erase their history**.

This is *not* deleting their user account, and the difference is the whole
point. Deleting a user removes the account and leaves the history of what they
did, because `user_name` was copied into every row precisely so that it would.
Erasing a person's history does the opposite: the events stay exactly where
they are, and the person comes out of them.

What it does to each of their rows:

- `user_id`, `user_name`, `channel` and `device_id` are emptied;
- their name is taken out of the `detail` document of those rows wherever it
  appears — as a whole word, so a person called Ed does not take `added` and
  `enabled` with them;
- a configuration row recording a change to *their account* loses the link
  back to it, while keeping the name of whoever made the change. That row is
  somebody else's record of what they did, and a person asking to be forgotten
  is not asking for another person's audit trail to be blanked.

What it leaves untouched: the time, the area, the zone, the event, the
incident. **The log still answers "what happened on the night of the
fourteenth" and no longer answers "who".**

Two things it does not reach, said here rather than left to be discovered:

- **A name somebody else put in an object's name.** If an administrator called
  a tag "Ana's tag", the row recording *that* change is the administrator's,
  not Ana's, and it keeps its text. Rename the object and the next row carries
  the new name; the old row is history of what the administrator did.
- **A row whose account is not Foyer's.** Erasure searches by the Foyer
  account, by the Home Assistant account linked to it, and by the name on rows
  that carry no account at all. Somebody who appears in the log only under a
  Home Assistant account that is not linked to their Foyer user is not found —
  link the two on page 7 and they are.

Before it runs, the panel shows how many rows were found and by which key —
their account, or their name alone. The second number is not noise: a row
written before they were a Foyer user, or under a name they have since changed,
carries the name and another id, and matching on the account alone would leave
the oldest rows — the ones somebody is most likely to ask about — with the name
still in them.

There is a checkbox: **keep a stable identifier instead of forgetting**. Off by
default. On, the rows keep an opaque `person-…` identifier that still links
their rows to each other, so "the same person acted on both nights" survives.
That is minimisation, not erasure, and somebody asking to be forgotten is
usually asking for the other one. Ask them.

And be honest about what the identifier protects against. It says nothing by
itself, but **the table that maps it back to a name is in the configuration** —
it is a field on each person, and it travels in a configuration backup, so that
restoring one does not detach every row already written. So a pseudonym hides a
name from whoever reads the log; it hides nothing from whoever can read
`.storage` or holds a backup, which is the same boundary `docs/security-model.md`
draws around everything else here.

**The erasure is itself recorded**, under `config`, with who performed it and
how many rows it touched — and **without naming the person**. (The one case
where the row does carry the name is somebody erasing themselves, because the
row names whoever performed it.) Deleting the
whole log is recorded (§10.3) and so is this, but a row that recorded an
erasure by naming the person erased would leave behind the very thing it was
asked to remove.

It needs the `manage_users` permission and a code.

---

## Or let it happen by itself: timed pseudonymisation

**Page 11 — Settings**, under *Personal data in the log*. Off by default.

Switched on with a delay of N days, a sweep runs once a day — and once at
every start, because an installation that restarts more often than daily would
otherwise never run it at all — and replaces the name on every row older than N
days with that person's stable identifier, in the columns and inside the
detail. Rows newer than N days are untouched. Saving any setting restarts the
integration, so the first sweep happens seconds after you switch it on: the
panel asks you to confirm before it does.

**Read this before switching it on.** It trades away the ability to answer
*"who disarmed that night"* for every row older than the delay — which is the
question the log exists to answer, and the reason every person in this system
has their own code instead of sharing one. It is a real trade, not a free
safety feature, and Foyer will not present it as one.

It is also irreversible. Switching it off stops the sweep; it brings no name
back. Both switching it on and switching it off are recorded, with who did it.

Three limits worth knowing:

- It works from the **users page**: it can only replace a name with the
  identifier of somebody this installation still has. Rows naming a person who
  has since been deleted from the configuration keep their name. If you are
  going to delete somebody, erase their history first — that operation reaches
  those rows and this one does not.
- It finds the same rows the erasure finds, and misses the same ones: a person
  whose Home Assistant account is not linked to their Foyer user on page 7.
- It does not reach the copies that left. Anything that subscribed to
  `foyer_event` kept what it was given.

---

## What a backup carries

The configuration backup on page 11 carries the **pseudonymisation setting**
and each person's identifier, so restoring a backup does not silently switch
the protection off, and does not mint new identifiers that would detach every
row already pseudonymised from every row written after.

It does **not** carry the log. Nothing you do here can be undone by restoring a
backup, which is correct: an erasure that a restore could reverse would not be
an erasure.

---

## When Foyer is removed

On page 11 there is one more switch: **delete the log database if Foyer is
removed**. Off by default.

It has to be a switch rather than a question asked at the time, because Home
Assistant's own "are you sure" is the last dialogue there is — an integration
being removed cannot put up one of its own. So the question is asked in
advance, and the answer for anybody who never gave one is *keep*, because §16
of the specification says to ask rather than guess and keeping is the answer
that destroys nothing.

If you leave it off, the file stays where it was: `foyer-log.db` in the
configuration directory, with its `-wal` and `-shm` companions. Delete it by
hand whenever you like.

What removal takes with it either way: every entity and device from the
registries, the sidebar panel, the repair issues, the notifications Foyer put
up, and the **retained MQTT message** — a retained message outlives the
integration that published it and would go on telling whoever connects to that
broker next what the house was doing when Foyer last spoke.

What it does **not** take: **camera snapshots**. Foyer writes them under
`media/foyer` by default, and they are photographs of the inside of a house —
the one thing on this page nobody thinks to look for. The folder is
configurable, may point anywhere and may hold files that were never Foyer's, so
removing them is left to you. Go and look.

---

## What Foyer's log is not

It is **audit-useful, not tamper-proof**. A Home Assistant administrator with
filesystem access can delete the database outright, and nothing here changes
that; `docs/security-model.md` says so at more length. The log's purpose is to
answer honest questions afterwards, not to survive somebody determined to
rewrite it.
