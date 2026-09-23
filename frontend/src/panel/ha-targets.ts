// What Home Assistant can be pointed at, for the pickers on pages 5 and 11.
//
// A notification target is the awkward case: `notify.mobile_app_luca` is a
// *service*, not an entity, so a picker built from `hass.states` alone finds
// nothing on most installations. These helpers read the service registry as
// well, and both are offered in one list — the backend accepts either, and the
// executor works out which it is at call time.
import type { HomeAssistant } from "../shared/types";

export interface Target {
  id: string;
  name: string;
}

function friendly(hass: HomeAssistant, entityId: string): string {
  const state = hass.states[entityId];
  return String(state?.attributes?.friendly_name ?? entityId);
}

function sorted(targets: Target[]): Target[] {
  const seen = new Map<string, Target>();
  for (const target of targets) {
    if (!seen.has(target.id)) seen.set(target.id, target);
  }
  return [...seen.values()].sort((a, b) => a.id.localeCompare(b.id));
}

/** Every entity in one of `domains`. */
// Lists already built from this `states` object. Home Assistant replaces the
// object when anything changes, so identity is freshness: an editor that
// re-rendered every second during a countdown, and on every keystroke,
// sorted every entity in the house each time (second review).
const built = new WeakMap<object, Map<string, Target[]>>();

export function entityTargets(hass: HomeAssistant, domains: string[]): Target[] {
  let lists = built.get(hass.states);
  if (!lists) {
    lists = new Map();
    built.set(hass.states, lists);
  }
  const key = domains.join(",");
  let list = lists.get(key);
  if (!list) {
    list = sorted(
      Object.values(hass.states)
        .filter((e) => domains.includes(e.entity_id.split(".")[0]))
        .map((e) => ({ id: e.entity_id, name: friendly(hass, e.entity_id) })),
    );
    lists.set(key, list);
  }
  return list;
}

/** Every way to send a notification: `notify` entities and `notify` services. */
export function notifyTargets(hass: HomeAssistant): Target[] {
  const services = Object.keys(hass.services?.notify ?? {})
    // `notify.notify` is whatever the installation happens to make default and
    // `notify.send_message` addresses an entity: neither is a target to pick.
    .filter((name) => name !== "send_message")
    .map((name) => ({ id: `notify.${name}`, name: `notify.${name}` }));
  return sorted([...entityTargets(hass, ["notify"]), ...services]);
}

/** Targets for the chime: speakers, sirens, and anything that notifies. */
export function chimeTargets(hass: HomeAssistant, domains: string[]): Target[] {
  const others = domains.filter((domain) => domain !== "notify");
  return sorted([
    ...entityTargets(hass, others),
    ...(domains.includes("notify") ? notifyTargets(hass) : []),
  ]);
}

/** What a zone may name as its battery (§4.2): a sensor reporting a
 * percentage, or a battery binary_sensor where `on` means low. Narrowed by
 * device_class where the integration sets one, because an installation has
 * hundreds of sensors and four of them are batteries — but anything the
 * backend accepts is still offered, since plenty of templates set no class. */
export function batteryTargets(hass: HomeAssistant): Target[] {
  const all = entityTargets(hass, ["sensor", "binary_sensor"]);
  const isBattery = (target: Target) =>
    hass.states[target.id]?.attributes.device_class === "battery";
  // The likely ones first, in one flat list rather than two: an installation
  // has hundreds of sensors and four of them are batteries, but plenty of
  // template sensors set no device_class and would otherwise be unreachable.
  return [...all.filter(isBattery), ...all.filter((t) => !isBattery(t))];
}

/** Domains that have at least one service, for the call_service action. */
export function serviceDomains(hass: HomeAssistant): string[] {
  return Object.keys(hass.services ?? {}).sort();
}

/** The services of one domain. */
export function domainServices(hass: HomeAssistant, domain: string): string[] {
  return Object.keys(hass.services?.[domain] ?? {}).sort();
}

/** A state as the Home Assistant user reads it, with the raw value beside
 * it when the two differ: "Open (on)". A door sensor's `on` means open and a
 * moisture sensor's `on` means wet, and a trigger confirmed against "on"
 * alone is confirmed against a word nobody sees anywhere else in Home
 * Assistant (UX review; INV-5 is only as good as what the person reads).
 * The raw value stays, because it is what the trigger actually stores. */
export function stateLabel(hass: HomeAssistant, entityId: string, state: string): string {
  const entity = hass.states[entityId];
  let label = state;
  if (entity && hass.formatEntityState) {
    try {
      label = hass.formatEntityState(entity, state);
    } catch {
      label = state;
    }
  }
  return label && label !== state ? `${label} (${state})` : state;
}
