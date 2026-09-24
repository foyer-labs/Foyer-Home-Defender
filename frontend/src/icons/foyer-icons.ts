// Registers the "foyer:" icon set, so `foyer:shield` can be used on any
// dashboard. Loaded on every page (add_extra_js_url).
//
// The sidebar panel does *not* use it: Home Assistant resolves a custom icon
// once, and if this module has not run yet — the companion app starting from
// a cached page — it falls back to a legacy element and never retries, which
// leaves an empty square in the sidebar. The sidebar uses an mdi icon; the
// Foyer shield is drawn directly, as an inline SVG, in the panel header,
// where our own modules are certainly loaded.
import { ICON_PATH, ICON_VIEWBOX } from "./icon-path";

interface CustomIconSet {
  getIcon(name: string): Promise<{ path: string; viewBox?: string } | undefined>;
  getIconList(): Promise<{ name: string }[]>;
}

declare global {
  interface Window {
    customIcons?: Record<string, CustomIconSet>;
  }
}

const ICONS: Record<string, string> = { shield: ICON_PATH };

window.customIcons = window.customIcons ?? {};
window.customIcons["foyer"] = {
  getIcon: async (name) =>
    name in ICONS ? { path: ICONS[name], viewBox: ICON_VIEWBOX } : undefined,
  getIconList: async () => Object.keys(ICONS).map((name) => ({ name })),
};
