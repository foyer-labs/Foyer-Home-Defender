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
export function entityTargets(hass: HomeAssistant, domains: string[]): Target[] {
  return sorted(
    Object.values(hass.states)
      .filter((e) => domains.includes(e.entity_id.split(".")[0]))
      .map((e) => ({ id: e.entity_id, name: friendly(hass, e.entity_id) })),
  );
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

/** Domains that have at least one service, for the call_service action. */
export function serviceDomains(hass: HomeAssistant): string[] {
  return Object.keys(hass.services ?? {}).sort();
}

/** The services of one domain. */
export function domainServices(hass: HomeAssistant, domain: string): string[] {
  return Object.keys(hass.services?.[domain] ?? {}).sort();
}
