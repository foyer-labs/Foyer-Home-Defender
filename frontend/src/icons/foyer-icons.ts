// Registers the "foyer:" icon set so the sidebar can show the Foyer shield.
// Loaded on every page (add_extra_js_url), before the panel itself is opened.
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
