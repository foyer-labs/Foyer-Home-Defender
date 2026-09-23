# Keypads, tags and remotes

How to arm and disarm Foyer from something other than a phone, and what each
piece of hardware is honestly worth.

Three things are worth reading before you buy anything:

- **Foyer does not talk to keypads. It offers a contract.** Keypad models churn
  every six months; the contract does not. Anything that can call a Home
  Assistant service, publish to an MQTT broker or make an HTTP request to
  Foyer's own endpoint can arm this house.
- **A device is declared before it may command anything.** Add it under
  *Arming devices* first. A device this installation does not carry is refused
  whatever code it brings, and the refusal is logged and shown. This is not
  tidiness: the lockout counts failed codes per channel *and per device*, so a
  caller free to invent a device name is a caller who is never locked out.
- **A shared keypad cannot know who is typing.** The code is the only identity
  it has, which is why every person has their own code. A tag or a badge is the
  opposite: it identifies a person and carries no code at all.

---

## Choosing the hardware

| | Ring Alarm Keypad v2 | Zigbee keypad with RFID | Frient / Develco | Wall tablet | NFC tag | ESPHome build |
|---|---|---|---|---|---|---|
| **Radio** | Z-Wave | Zigbee | Zigbee | Wi-Fi | — | Wi-Fi / ESP-NOW |
| **Cost** | €60–90 | €20–40 | €70–100 | €80–200 | ≈ €1 | €20–50 |
| **Feedback** | LED ring, beeps, countdown | Varies sharply | Beeps, few LEDs | Anything | None | Anything |
| **Identifies the person** | No — the code does | No — the code does | No | Yes, if signed in | **Yes** | Depends |
| **Panic keys** | Police, fire, medical | Usually one | Usually one | On screen | No | Your choice |
| **Battery** | Rechargeable, months | AA/AAA, months–years | Years | Mains | — | Mains |
| **The catch** | English legends, patchy availability in Europe, needs a Z-Wave stick | Firmware quality varies between clones sold under one picture | Fewer keys, no RFID | Always-on cost, screen wake delay | Nothing to type: possession is the credential | Yours to maintain |

**The honest summary.** The Ring Keypad v2 is the most complete thing you can
buy: it is the only one in this table that can show an exit countdown, three
distinct armed states and a panic key set without help. Zigbee keypads are a
quarter of the price and a coin flip on firmware. A wall tablet is the richest
option and the one people actually use, because it is the same surface as the
rest of the house. And an NFC tag is a euro, needs no battery, and is the only
cheap channel that says *who*.

DIY ESPHome keypads are a live community topic and are not maintained by this
project in v1. They fit the contract like anything else: publish to the topic,
call the service, or talk to the [device endpoint](#the-device-endpoint).

---

## The service contract

Every state-changing service takes the same four identity fields and answers
with the same structured result.

```yaml
action: foyer.arm
data:
  scenario_name: Night        # or scenario_id, or area_id, or mode
  code: "123456"
  device_id: keypad_hall      # the name it is declared under, not an HA device id
response_variable: answer
```

```jsonc
// answer
{
  "success": false,
  "reason": "zone_open",
  "blocking_zones": [{ "id": "…", "name": "Kitchen window" }],
  "bypassed_zones": [],
  "low_battery_zones": [{ "id": "…", "name": "Garage shutter" }],
  "state": { /* the whole live state, as the panel sees it */ }
}
```

`low_battery_zones` is not a refusal and never blocks: it names the zones this
arming would put under guard on a battery that is running out, and it is on
*every* arming attempt rather than once, so an adapter with a display or a
second beep can pass the warning on. Excluding one is an ordinary
`foyer.bypass_zone`. An adapter that ignores the field behaves exactly as it
did before the field existed.

`reason` is a stable identifier, never a sentence: `bad_code`, `code_required`,
`locked_out`, `zone_open`, `zone_fault`, `not_permitted`, `user_not_valid`,
`device_not_registered`, `invalid_state`, `unknown_scenario`. An adapter maps
them to its own beeps; the panel and the card translate them for people.

The services: `foyer.arm`, `foyer.disarm`, `foyer.bypass_zone`,
`foyer.unbypass_zone`, `foyer.acknowledge`, `foyer.export_log`,
`foyer.export_config`, `foyer.import_config`.

Two fields deserve a sentence each.

**`channel`** may only say `api` or `automation`. Anything physical —
`keypad`, `nfc` — is a property of a *registered device*, never a claim a
message makes. Otherwise an automation could buy the per-user code exemption
by typing a word.

**`user_id`** is attribution, and grants nothing. Claiming to be somebody
brings their restrictions, never their exemptions: their permissions still
apply, and a code is still required wherever the policy asks for one.

**`skip_exit_delay`** arms with no time to leave. It needs no permission of its
own — whoever may arm may arm at once — but it turns every delayed zone into
an instant one, so the log records that it happened.

---

## The MQTT contract

Switched off until you switch it on, under *Arming devices*. A broker is often
somebody else's machine.

### Inbound — device to Foyer

Default topic `foyer/<install id>/command`, configurable.

```json
{
  "action": "arm",
  "scenario": "Night",
  "code": "123456",
  "device_id": "keypad_hall"
}
```

`action` is `arm`, `disarm`, `acknowledge` or `status`. `status` commands
nothing; it asks Foyer to publish the state again, which is what a keypad
wants after it reboots. `arm` also accepts `force` and `skip_exit_delay`;
`disarm` accepts `area_ids`.

**`device_id` is not optional over MQTT.** Anybody who can publish to the topic
can publish a command, so the name a message gives is the only thing separating
the hall keypad from a stranger. A message without one, or with a name this
installation does not carry, is refused, logged, and raised as a Home Assistant
notification — once per device, so a misconfigured keypad retrying every thirty
seconds does not bury the notification that matters.

### Outbound — Foyer to device

Default topic `foyer/<install id>/state`, published **retained** on every
change and on request.

At the default level, `minimal`:

```json
{
  "master": "armed_night",
  "countdown": { "kind": "exit", "remaining": 22 },
  "ready_to_arm": false,
  "blocking_zones": 1,
  "fault": false,
  "last_result": "blocked",
  "last_reason": "zone_open"
}
```

`standard` adds `scenario` and `areas`, by name. `full` adds `open_zones`, by
name — the contract as §9.2 writes it.

**Why the default is the least.** The message is retained, on a broker that is
often shared with other integrations, other households or a cloud bridge.
Whatever is in it is told to whoever connects next, including "the house is
armed and nobody is in", and — at `full` — which window is open. That is the
same reasoning the external watchdog uses for its empty heartbeat. Raise the
level knowingly.

**Two fields, and the first never grows.** `last_result` is one of `ok`,
`blocked`, `bad_code`, `locked_out` — this set, for ever, so an adapter written
today never meets a word it does not recognise. `last_reason` beside it carries
the precise reason, from the same stable set the services return
(`zone_open`, `device_not_registered`, `user_not_valid`, …) and is `null` when
the command succeeded.

Map `last_result` to your beeps and your LED; read `last_reason` only if you
want to tell *a window is open* from *I am not a registered device*. Both are
the last command's, whichever keypad sent it: with two keypads in a house, read
them in response to your own command rather than as a standing fact.

---

## The device endpoint

An HTTP endpoint of Foyer's own, for a device that would rather not be a name
on a broker: each device on it holds a **token of its own**. It is used by
keypads, and by the displays, relays and modules described in the next
section. Declare the device under *Arming devices*, choose the endpoint as its
transport, save it, then generate its token.

**The token authenticates the device; it does not encrypt anything.** Over
plain HTTP the token and every code typed on the device cross the network as
readable as over plain MQTT. If you want the codes kept private, in order of
simplicity: serve Home Assistant over HTTPS (or behind a reverse proxy it
trusts); use TLS with per-client credentials on the broker; or use ESPHome's
native API, which is encrypted and can call `foyer.arm` and `foyer.disarm`
already.

- **The token names the device.** A request carries no `device_id`, and one it
  carries anyway is ignored. The token is shown once, when it is generated;
  Foyer keeps only a fingerprint of it and cannot show it again. Generating a
  new one invalidates the old one at once and closes its open connections.
  Generating and revoking ask for a code, as saving the device does.
- **One transport per device.** A device on the endpoint is refused over MQTT
  and in service calls, recorded and notified as an unknown device is —
  otherwise whoever knows its name reaches the house without the token.
- **A wrong or missing token** is answered `401`, with no detail, and counted
  per source address: past the lockout thresholds a wrong or missing token
  from that address is refused for the lockout period without being counted
  again, the lockout is recorded under `security`, and it is notified once.
- **A right token is never refused for its address.** Behind the same router,
  reverse proxy or IPv6 /64 as somebody guessing, a device with its right
  token keeps working while that address is locked out: a token is 32 random
  bytes, and nobody guesses one. Every row its requests cause in the log
  carries the address and says it was locked, so a device sharing its address
  with a guesser shows up there. Its requests neither add to the address's
  count nor clear it.
- **Plain HTTP is accepted, and said.** A device whose last request arrived
  unencrypted carries a permanent *Unencrypted* warning under *Arming devices*,
  and every row of the log it causes records that the request was not
  encrypted. Many home-made devices cannot do TLS at all; refusing them would
  take the feature away from the people who asked for it.
- **Tags are not allowed on it.** A tag carries no code, so on the endpoint the
  token by itself would be the key to the house. Tags stay `tag.*` and
  `event.*` entities.
- Where no enabled device uses the endpoint, every route answers `404`, as if
  it did not exist.

## API devices: displays, relays and modules of your own

Every device on the endpoint is an **API device**, and may do exactly what its
**scopes** say — a touch display in the hall, a relay that lights an "armed"
lamp, an ESP32 or Arduino module, and the keypads already there. The scopes
are set per device under *Arming devices*, **every one off until you switch it
on**, and the device never goes beyond them, whatever code is typed on it.

| Scope | Kind | What it gives |
|---|---|---|
| `status` | read | the state message: armed or not, which scenario, countdowns, ready to arm, alarm |
| `zones` | read | every zone with its state: open, closed, in fault, excluded |
| `batteries` | read | battery levels and tamper, per zone and per device |
| `health` | read | system health: mains, notification channels, watchdog, radios |
| `log` | read | the log, a page at a time, newest first |
| `arm` | act | arm, only the scenarios and areas chosen for the device (*Whole house* by default, as far as the code allows) |
| `disarm` | act | disarm, only the areas chosen for the device |
| `exclude` | act | *Exclude* a zone from the next arming, and *Include again* |
| `acknowledge` | act | acknowledge an alarm or a technical alarm |

A relay that only lights a lamp holds `status` and nothing else. A keypad
declared on the endpoint before scopes existed carries `status`, `arm` and
`disarm`.

**Every action needs a code**, arming included, even where the house would arm
without one from the panel or a service: the token crosses the network
readable whenever the request is not encrypted, and must never be what arms or
disarms the house. That applies to keypads on the endpoint too — they always
ask for a code. The code is the identity, as on any keypad: the action is made
in the name of whoever the code belongs to, within that person's permissions,
never beyond the device's scopes even when that person could do more, and a
wrong code counts towards the device's lockout.

**Reading is free or after a code, per scope and per device.** A free scope is
read with the token alone. A scope after a code is read only while the device
is **unlocked**. By default `status` is free and everything else is after a
code, because a display in the hall is read by whoever walks past it, and
*the back window is open* is the sentence a burglar wants.

**The unlock:**

- starts with `{"action": "unlock", "code": "…"}`; a wrong code counts
  towards the lockout like any other;
- lasts as long as the device says — from 30 seconds to 10 minutes, two
  minutes by default — counted from the last time the device was used;
- ends at once with `{"action": "lock"}`, with every arming or disarming made
  through the device, and with a Home Assistant restart;
- shows only what the person whose code it was may see: the log after a code
  needs that person's permission to view the log, and only then carries
  names. A free `log` scope shows what happened and never who. Zones,
  batteries and the log read after a code cover only the areas that person
  may reach;
- ends, too, when that person is disabled or past their validity window, and
  when the device is disabled or given a new token;
- leaves a line in the log under `security`: which device, whose code, for how
  long.

**Over plain HTTP, a device reads nothing beyond `status`** until you tick *I
know these readings cross the network unencrypted* on that device. Until then
a section answers `403 plain_http_not_confirmed`; over HTTPS the tick changes
nothing. Ticking it leaves a line in the log.

### How the data travels

A microcontroller has little memory, so nothing large is pushed. The state
arrives on a stream, so a lamp lights the moment the house arms; each section
is a small request of its own, and the stream says when one has changed.

```
GET  /api/foyer/device/state      the stream (Server-Sent Events)
POST /api/foyer/device            one action per request, JSON, at most 4 KB
GET  /api/foyer/device/zones
GET  /api/foyer/device/batteries
GET  /api/foyer/device/health
GET  /api/foyer/device/log?before=<cursor>&limit=<1–50>
```

Every request carries `Authorization: Bearer <token>`.

On the stream, a device holding `status` receives the state message on
connect and whenever it changes — the MQTT state message, at the same detail
level (`minimal` by default), with this device's own `last_result` and
`last_reason`. For each section it holds a scope for, it receives a one-line
notice when that section changes; a device that does not show the section
ignores it. A comment line every thirty seconds keeps the connection open
through proxies.

A relay that lights a lamp while the house is armed only listens:

```
GET /api/foyer/device/state
Authorization: Bearer <token>

data: {"master": "arming", "countdown": {"kind": "exit", "remaining": 30}, "ready_to_arm": true, "blocking_zones": 0, "fault": false, "last_result": null, "last_reason": null}

data: {"master": "armed_away", "countdown": null, "ready_to_arm": true, "blocking_zones": 0, "fault": false, "last_result": null, "last_reason": null}

event: changed
data: zones

: keepalive
```

A display that shows the zones after somebody types a code:

```
GET /api/foyer/device/zones
→ 403 {"success": false, "reason": "unlock_required"}

POST /api/foyer/device
{"action": "unlock", "code": "123456"}
→ 200 {"success": true, "reason": null, "until": "2026-09-23T10:02:00+00:00"}

GET /api/foyer/device/zones
→ 200 {"success": true, "reason": null, "zones": [
        {"id": "z_kitchen_window", "name": "Kitchen window", "area_id": "ground",
         "type": "instant", "enabled": true, "open": true, "fault": null, "excluded": false}, …]}
```

The actions are `status`, `arm` (with `scenario` or `area`), `disarm`
(optionally with `areas`), `exclude` and `include` (with `zone`),
`acknowledge` (with `target`: `incident` or `technical`), `unlock` and `lock`.
Every action but `unlock` and `lock` answers with the structured result of the
services, with `last_result` and `last_reason` as on MQTT; a refusal is still a
`200`, and the answer is in `success` and `reason`. An action outside the
device's scopes is refused with `scope_not_granted`, one without a code with
`code_required`.

A section the device may not read answers `403` with one of four reasons:

- `scope_not_granted` — the device does not hold that scope;
- `unlock_required` — the scope is after a code and the device is not
  unlocked, or the person whose code unlocked it has since been disabled or
  is past their validity dates;
- `plain_http_not_confirmed` — the request arrived unencrypted and the tick
  above is not set;
- `not_permitted` — the log, after a code, and the code's owner may not read
  the log.

Switching scenario while another is armed disarms the areas the new one
leaves out, so it needs the device's `disarm` scope for those areas as well
as `arm`.

The log is paged by an opaque cursor: send the `next` of one answer as
`before` in the next request, at most fifty rows at a time.

### The full contract

The endpoint and its stream are described in
[`docs/api/openapi.yaml`](api/openapi.yaml), and the MQTT contract in
[`docs/api/asyncapi.yaml`](api/asyncapi.yaml), both at contract version **v1**.
A change that would break a device written against v1 is a new version, and
the changelog says so; a test compares both documents with the code on every
change. The panel's own WebSocket commands are internal and are not part of
the contract: a device must not rely on them.

Home Assistant administrators also have an **API** page in the panel, which
renders the same document with Swagger UI. Press *Authorize*, paste the token
of a device declared under *Arming devices*, then *Try it out*. These are real
requests to your house, made as that device: an arming with a real code arms
it, a wrong code counts towards the lockout, and every action is in the log.
The page is served only inside the panel, and fetches nothing from the
internet.

---

## The shipped adapters

Three blueprints live under `blueprints/automation/foyer/`. **HACS installs the
integration, not blueprints**, so each one carries its own import button below:
it opens the blueprint import dialogue on your own Home Assistant, and you
press *Preview* then *Import*. (The button is the official
`my.home-assistant.io` redirect: it forwards you to your own installation and
nothing else. If you would rather not use it, copy the file into
`config/blueprints/automation/foyer/` and reload automations.)

### Ring Alarm Keypad v2 over Z-Wave JS

[![Open your Home Assistant instance and show the blueprint import dialog](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffoyer-labs%2FFoyer-Home-Defender%2Fblob%2Fmaster%2Fblueprints%2Fautomation%2Ffoyer%2Fring_keypad_v2_zwave_js.yaml)

`ring_keypad_v2_zwave_js.yaml`. Reads the keypad's Entry Control notification —
which key, and the digits typed before it — calls `foyer.arm` or `foyer.disarm`
and answers the LED ring, including the exit and entry countdowns, driven by
the area's own `sensor.foyer_countdown_*`.

**Verify the indicator numbers on your own firmware.** Ring has published no
mapping; the values in the blueprint's `variables` block are community work,
gathered in one place so you can correct them in one place. Test one with
Developer Tools → Actions → `zwave_js.set_value` before you trust the feedback.
Everything the blueprint does with Foyer works whether or not they are right;
what breaks with a wrong number is only what the keypad shows you.

### Generic Zigbee keypad over Zigbee2MQTT

[![Open your Home Assistant instance and show the blueprint import dialog](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffoyer-labs%2FFoyer-Home-Defender%2Fblob%2Fmaster%2Fblueprints%2Fautomation%2Ffoyer%2Fzigbee_keypad_z2m.yaml)

`zigbee_keypad_z2m.yaml`. Reads the keypad's Zigbee2MQTT message (`action` plus
`action_code`) and publishes `arm_mode` back so the display follows the house.

**Tuya-family clones vary by firmware revision and must be verified one by
one.** Two keypads sold under the same photograph can send different action
names, put the code in a different field, or send nothing until they are paired
in a particular order. Watch your own keypad's topic in Zigbee2MQTT first, then
correct the action names in the blueprint's `variables` block. This is not a
defect in the blueprint; it is what that market is.

### NFC tags and remotes

[![Open your Home Assistant instance and show the blueprint import dialog](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffoyer-labs%2FFoyer-Home-Defender%2Fblob%2Fmaster%2Fblueprints%2Fautomation%2Ffoyer%2Fnfc_tag_and_remote.yaml)

`nfc_tag_and_remote.yaml` — **and you probably do not need it.** Foyer reads
tags and remotes natively: add one under *Arming devices*, choose its `tag.*`
or `event.*` entity, say whose it is and what it does. Foyer then handles the
scan itself, with that person's permissions, their validity window and a log
row that names them.

The blueprint is for what the configuration deliberately will not do: a tag
that works only between certain hours, one that acts only if somebody is home,
a button that forces the arming past an open window.

---

## Writing your own adapter

1. Declare the device under *Arming devices* and note the identifier.
2. Trigger on whatever your hardware produces.
3. Call `foyer.arm` / `foyer.disarm` with `code` and `device_id`, and take the
   `response_variable`.
4. Map `success` and `reason` to your hardware's own vocabulary. Give the
   refusals at least two sounds: "not right" and "not now" are different
   problems, and a household that hears one sound for both will retype a code
   that was never the problem.
5. Follow the panel entity's state (or the MQTT state topic, or the endpoint's
   state stream) for anything the device shows when nobody has touched it —
   the house can be armed from a phone, and a keypad that only knows what it
   was told itself will be wrong within a day.

---

## What a keypad cannot do

- **It cannot check a code.** No adapter, blueprint or card decides anything;
  they transmit and render. A check anywhere else is decoration, because
  anyone with Home Assistant access can call the service directly.
- **It cannot be trusted about who is pressing it.** On a shared keypad the
  code is the identity. The per-user "skip the code" exemption can never apply
  there, and the configuration says so where the setting is.
- **It cannot be your only way in.** Batteries die, radios jam, brokers stop,
  and every one of those fails silently until the moment you are standing in
  the rain. Keep the panel and the card reachable as well, and do not let the
  keypad by the door be the whole plan.
