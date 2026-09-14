// Every user-visible string comes from translations/panel/<lang>.json, fetched
// from the backend over foyer/translations. Components never contain text.
import type { HomeAssistant } from "./types";

export type Strings = Record<string, unknown>;

const cache = new Map<string, Promise<Strings>>();

export function loadStrings(hass: HomeAssistant): Promise<Strings> {
  const language = hass.language;
  let pending = cache.get(language);
  if (!pending) {
    pending = hass
      .callWS<{ language: string; strings: Strings }>({
        type: "foyer/translations",
        language,
      })
      .then((result) => result.strings);
    // A failed load must be retried next time, not cached forever.
    pending.catch(() => cache.delete(language));
    cache.set(language, pending);
  }
  return pending;
}

/** Look up a dotted key and fill {placeholders}. A missing key renders as the key. */
export function t(
  strings: Strings | undefined,
  key: string,
  params: Record<string, string | number> = {},
): string {
  let node: unknown = strings;
  for (const part of key.split(".")) {
    if (node && typeof node === "object" && part in node) {
      node = (node as Record<string, unknown>)[part];
    } else {
      return key;
    }
  }
  if (typeof node !== "string") return key;
  return node.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}
