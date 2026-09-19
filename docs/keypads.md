# Keypads, tags and remotes

How to arm and disarm Foyer from something other than a phone, and what each
piece of hardware is honestly worth.

Three things are worth reading before you buy anything:

- **Foyer does not talk to keypads. It offers a contract.** Keypad models churn
  every six months; the contract does not. Anything that can call a Home
  Assistant service or publish to an MQTT broker can arm this house.
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
or call the service.

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
  "state": { /* the whole live state, as the panel sees it */ }
}
```

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
5. Follow the panel entity's state (or the MQTT state topic) for anything the
   device shows when nobody has touched it — the house can be armed from a
   phone, and a keypad that only knows what it was told itself will be wrong
   within a day.

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
