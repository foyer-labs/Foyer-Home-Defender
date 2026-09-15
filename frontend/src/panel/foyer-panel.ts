// The Foyer sidebar panel: a shell with a toolbar, one tab per page and the
// "About this section" help above every page (SPEC §15.1, §15.2). Live state
// arrives over foyer/subscribe; configuration is read and written over the
// admin-only foyer/config commands, which validate everything server-side.
import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";

import { brandSymbol } from "../shared/brand";
import { loadStrings, t, type Strings } from "../shared/i18n";
import { formStyles, stateStyles } from "../shared/styles";
import type {
  CommandResult,
  ConfigMeta,
  EditResult,
  FoyerConfig,
  FoyerStatus,
  HomeAssistant,
  PageId,
} from "../shared/types";
import type { PanelContext } from "./context";
import "./pages/overview";
import "./pages/areas";
import "./pages/zones";
import "./pages/scenarios";

const PAGES: PageId[] = ["overview", "areas", "zones", "scenarios"];
const CONFIG_PAGES: PageId[] = ["areas", "zones", "scenarios"];

// One line per setting in each page's help (translations: help.<page>.items).
const HELP_ITEMS: Record<PageId, string[]> = {
  overview: ["area", "master", "scenario", "not_ready", "memory"],
  areas: ["own_state", "entry", "exit", "reports_as"],
  zones: ["trigger", "type", "entry_mode", "arm_policy", "hold", "always_on", "supervision"],
  scenarios: ["areas", "reports_master", "switching", "exit_override", "siren"],
};

interface Prefs {
  help?: Record<string, boolean>;
  help_hidden?: boolean;
}

class FoyerPanel extends LitElement {
  static override properties = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    route: { attribute: false },
    _strings: { state: true },
    _status: { state: true },
    _config: { state: true },
    _meta: { state: true },
    _error: { state: true },
    _page: { state: true },
    _prefs: { state: true },
    _tick: { state: true },
  };

  hass?: HomeAssistant;
  narrow = false;
  route?: { path?: string };
  private _strings?: Strings;
  private _status?: FoyerStatus;
  private _config?: FoyerConfig;
  private _meta?: ConfigMeta;
  private _error?: string;
  private _page: PageId = "overview";
  private _prefs: Prefs = {};
  private _tick = 0;
  private _offset = 0; // server clock minus browser clock, in ms
  private _language?: string;
  private _unsubscribe?: Promise<() => Promise<void>>;
  private _timer?: number;

  override connectedCallback(): void {
    super.connectedCallback();
    if (this.hass) this._start();
    // Countdowns move once a second; nothing else needs a clock.
    this._timer = window.setInterval(() => {
      if (this._status?.areas.some((a) => a.timer)) this._tick += 1;
    }, 1000);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsub) => unsub()).catch(() => undefined);
    this._unsubscribe = undefined;
    window.clearInterval(this._timer);
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (!changed.has("hass") || !this.hass) return;
    if (this.hass.language !== this._language) {
      this._language = this.hass.language;
      loadStrings(this.hass)
        .then((strings) => (this._strings = strings))
        .catch((err) => (this._error = String(err?.message ?? err)));
    }
    if (!this._unsubscribe && this.isConnected) this._start();
  }

  private get _isAdmin(): boolean {
    return Boolean(this.hass?.user?.is_admin);
  }

  private _start(): void {
    if (!this.hass || this._unsubscribe) return;
    this._unsubscribe = this.hass.connection.subscribeMessage<FoyerStatus>(
      (status) => {
        this._offset = Date.parse(status.now) - Date.now();
        this._status = status;
        this._error = undefined;
      },
      { type: "foyer/subscribe" },
    );
    this._unsubscribe.catch((err) => {
      this._unsubscribe = undefined;
      this._error =
        err?.code === "not_loaded"
          ? t(this._strings, "common.not_loaded")
          : t(this._strings, "common.connection_error", {
              error: String(err?.message ?? err),
            });
    });
    this.hass
      .callWS<Prefs>({ type: "foyer/prefs" })
      .then((prefs) => (this._prefs = prefs))
      .catch(() => undefined);
    if (this._isAdmin) this._loadConfig();
  }

  private async _loadConfig(): Promise<void> {
    if (!this.hass) return;
    const result = await this.hass.callWS<{ config: FoyerConfig; meta: ConfigMeta }>({
      type: "foyer/config",
    });
    this._config = result.config;
    this._meta = result.meta;
  }

  // --- commands, shared with the pages through the context ------------------------

  private _context(): PanelContext | undefined {
    const hass = this.hass;
    if (!hass || !this._strings || !this._status) return undefined;
    return {
      hass,
      strings: this._strings,
      status: this._status,
      config: this._config,
      meta: this._meta,
      isAdmin: this._isAdmin,
      now: () => Date.now() + this._offset,
      navigate: (page) => (this._page = page),
      arm: (target) =>
        hass.callWS<CommandResult>({ type: "foyer/arm", ...target }),
      disarm: (areaIds) =>
        hass.callWS<CommandResult>({
          type: "foyer/disarm",
          ...(areaIds ? { area_ids: areaIds } : {}),
        }),
      save: async (kind, item, triggerConfirmed = false) => {
        const result = await hass.callWS<EditResult>({
          type: "foyer/config/save",
          kind,
          item,
          trigger_confirmed: triggerConfirmed,
        });
        if (result.success) await this._reloadConfigSoon();
        return result;
      },
      remove: async (kind, id) => {
        const result = await hass.callWS<EditResult>({
          type: "foyer/config/delete",
          kind,
          item_id: id,
        });
        if (result.success) await this._reloadConfigSoon();
        return result;
      },
    };
  }

  // A saved change reloads the integration; read the configuration back once
  // it is up again, so the page shows what the backend actually stored.
  private async _reloadConfigSoon(): Promise<void> {
    for (let attempt = 0; attempt < 10; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      try {
        await this._loadConfig();
        return;
      } catch {
        // not loaded yet: try again
      }
    }
  }

  // --- help (§15.2) -------------------------------------------------------------

  private _helpOpen(page: PageId): boolean {
    // Expanded on first visit, then whatever this Home Assistant user chose.
    return this._prefs.help?.[page] ?? true;
  }

  private _savePrefs(prefs: Prefs): void {
    this._prefs = {
      ...this._prefs,
      ...prefs,
      help: { ...this._prefs.help, ...prefs.help },
    };
    this.hass
      ?.callWS({ type: "foyer/prefs/set", prefs })
      .catch(() => undefined);
  }

  // --- rendering ----------------------------------------------------------------

  override render() {
    const s = this._strings;
    const hidden = Boolean(this._prefs.help_hidden);
    return html`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="symbol" aria-hidden="true"
          >${unsafeSVG(brandSymbol(Boolean(this.hass?.themes?.darkMode)))}</span
        >
        <div class="title">${t(s, "common.brand")}</div>
        ${this._status ? html`<span class="live">${t(s, "common.live")}</span>` : nothing}
        <button
          class="help-toggle"
          aria-pressed=${hidden ? "false" : "true"}
          title=${t(s, "help.global_toggle")}
          aria-label=${t(s, "help.global_toggle")}
          @click=${() => this._savePrefs({ help_hidden: !hidden })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
        </button>
      </div>
      ${s ? this._renderTabs(s) : nothing}
      <main>${s ? this._renderBody(s) : nothing}</main>
    `;
  }

  private _renderTabs(s: Strings) {
    const pages = this._isAdmin ? PAGES : PAGES.filter((p) => !CONFIG_PAGES.includes(p));
    if (pages.length < 2) return nothing;
    return html`
      <nav class="tabs" role="tablist">
        ${pages.map(
          (page) => html`
            <button
              role="tab"
              aria-selected=${page === this._page ? "true" : "false"}
              @click=${() => (this._page = page)}
            >
              ${t(s, `nav.${page}`)}
            </button>
          `,
        )}
      </nav>
    `;
  }

  private _renderBody(s: Strings) {
    if (this._error) return html`<p class="error">${this._error}</p>`;
    const ctx = this._context();
    if (!ctx) return html`<p class="muted">${t(s, "common.loading")}</p>`;
    const page = this._page;
    return html`
      ${this._prefs.help_hidden ? nothing : this._renderHelp(s, page)}
      ${this._renderPage(page, ctx)}
    `;
  }

  private _renderPage(page: PageId, ctx: PanelContext) {
    // _tick is read so a running countdown re-renders the page every second.
    void this._tick;
    switch (page) {
      case "areas":
        return html`<foyer-page-areas .ctx=${ctx}></foyer-page-areas>`;
      case "zones":
        return html`<foyer-page-zones .ctx=${ctx}></foyer-page-zones>`;
      case "scenarios":
        return html`<foyer-page-scenarios .ctx=${ctx}></foyer-page-scenarios>`;
      default:
        return html`<foyer-page-overview .ctx=${ctx}></foyer-page-overview>`;
    }
  }

  private _renderHelp(s: Strings, page: PageId) {
    const base = `help.${page}`;
    const open = this._helpOpen(page);
    return html`
      <section class="help" ?data-open=${open}>
        <button
          class="help-hd"
          aria-expanded=${open ? "true" : "false"}
          @click=${() => this._savePrefs({ help: { [page]: !open } })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
          <span>${t(s, `${base}.title`)}</span>
          <span class="sr-only">${t(s, "help.toggle")}</span>
          <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon>
        </button>
        ${open
          ? html`<div class="help-body">
              <p>${t(s, `${base}.intro`)}</p>
              <dl>
                ${HELP_ITEMS[page].map(
                  (item) => html`
                    <dt>${t(s, `${base}.items.${item}.term`)}</dt>
                    <dd>${t(s, `${base}.items.${item}.text`)}</dd>
                  `,
                )}
              </dl>
            </div>`
          : nothing}
      </section>
    `;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      :host {
        display: block;
        min-height: 100vh;
        background: var(--primary-background-color);
        color: var(--primary-text-color);
      }
      .toolbar {
        display: flex;
        align-items: center;
        gap: 12px;
        height: var(--header-height, 56px);
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color));
        color: var(--app-header-text-color, var(--text-primary-color));
        border-bottom: var(--app-header-border-bottom, none);
        box-sizing: border-box;
      }
      .symbol svg {
        width: 32px;
        height: 32px;
        display: block;
      }
      .title {
        font-size: 20px;
        font-weight: 400;
        flex: 1;
      }
      .live {
        font-size: 12px;
        opacity: 0.85;
      }
      .help-toggle {
        border: 0;
        background: transparent;
        color: inherit;
        cursor: pointer;
        padding: 6px;
        border-radius: 50%;
        opacity: 0.7;
      }
      .help-toggle[aria-pressed="true"] {
        opacity: 1;
      }
      .tabs {
        display: flex;
        gap: 4px;
        padding: 0 16px;
        overflow-x: auto;
        background: var(--card-background-color);
        border-bottom: 1px solid var(--divider-color);
      }
      .tabs button {
        font: inherit;
        font-size: 14px;
        font-weight: 500;
        padding: 12px 14px;
        border: 0;
        border-bottom: 2px solid transparent;
        background: transparent;
        color: var(--secondary-text-color);
        cursor: pointer;
        white-space: nowrap;
      }
      .tabs button[aria-selected="true"] {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color);
      }
      main {
        max-width: 1100px;
        margin: 0 auto;
        padding: 16px;
      }
      .help {
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-left: 3px solid var(--primary-color);
        border-radius: 8px;
        margin-bottom: 18px;
        overflow: hidden;
      }
      .help-hd {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        padding: 12px 16px;
        border: 0;
        background: transparent;
        color: var(--primary-text-color);
        font: inherit;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        text-align: left;
      }
      .help-hd .chev {
        margin-left: auto;
        color: var(--secondary-text-color);
        transition: transform 0.15s;
      }
      .help:not([data-open]) .chev {
        transform: rotate(-90deg);
      }
      .help-body {
        padding: 0 16px 16px;
        font-size: 13.5px;
      }
      .help-body p {
        margin: 0 0 12px;
        color: var(--secondary-text-color);
        max-width: 72ch;
      }
      dl {
        display: grid;
        grid-template-columns: minmax(120px, 190px) 1fr;
        gap: 6px 16px;
        margin: 0;
      }
      dt {
        font-weight: 500;
      }
      dd {
        margin: 0;
        color: var(--secondary-text-color);
      }
      .error {
        color: var(--error-color);
      }
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
      }
      @media (max-width: 560px) {
        dl {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    `,
  ];
}

if (!customElements.get("foyer-panel")) customElements.define("foyer-panel", FoyerPanel);
