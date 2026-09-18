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
import "./pages/profiles";
import "./pages/groups";
import "./pages/users";
import "./pages/devices";
import "./pages/log";
import "./pages/settings";
import "./wizard";

// In the order of SPEC §15.1: 1–5, then 13, 10 and 11.
const PAGES: PageId[] = [
  "overview",
  "areas",
  "zones",
  "scenarios",
  "profiles",
  "groups",
  "users",
  "devices",
  "log",
  "settings",
];
const CONFIG_PAGES: PageId[] = [
  "areas",
  "zones",
  "scenarios",
  "profiles",
  "groups",
  "users",
  "devices",
  "settings",
];

// One line per setting in each page's help (translations: help.<page>.items).
const HELP_ITEMS: Record<PageId, string[]> = {
  overview: ["area", "master", "scenario", "not_ready", "memory", "technical", "incident"],
  areas: ["own_state", "entry", "exit", "reports_as"],
  zones: [
    "trigger",
    "type",
    "entry_mode",
    "arm_policy",
    "hold",
    "always_on",
    "supervision",
    "verification",
  ],
  scenarios: ["areas", "reports_master", "switching", "exit_override", "siren"],
  profiles: ["inheritance", "moments", "conditions", "severity", "silent"],
  groups: ["threshold", "members", "suppress", "derived"],
  users: ["own_code", "policy", "identified", "duress", "lockout", "scope"],
  devices: ["declared", "device_id", "identifies", "topics", "detail", "last_result"],
  log: ["category", "zone_disarmed", "incident", "user", "export"],
  settings: ["targets", "mode", "quiet", "during_exit", "response", "retention", "backup", "language"],
};

/** The code, when there is one. An absent key means "nothing typed", which is
 * not the same as an empty string: one is a request without a code, the other
 * is a wrong code. */
function withCode(code?: string): Record<string, string> {
  return code === undefined || code === "" ? {} : { code };
}

/** Drop empty filters: "everything" is an absent key, not an empty string. */
function prune(query: object): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(query).filter(
      ([, value]) =>
        value !== null && value !== undefined && value !== "" &&
        !(Array.isArray(value) && value.length === 0),
    ),
  );
}

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
  // The code of whoever is using the panel, held in memory for this visit
  // only — never stored, never put in a URL. It is re-sent with each command
  // that needs one, because the backend verifies every single time (INV-2).
  private _code?: string;
  private _asking?: { resolve: (code?: string) => void; retry: boolean };
  private _haUsers?: { id: string; name: string }[];
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

  /** Who may see the configuration pages (§8.3).
   *
   * A Home Assistant administrator, as since Phase 0, or a Foyer user holding
   * edit_config — which is the point of having permissions at all. Hiding a
   * page is a courtesy either way: the backend refuses the command (INV-2). */
  private get _canConfigure(): boolean {
    const me = this._status?.security.me;
    return this._isAdmin || Boolean(me?.permissions.includes("edit_config"));
  }

  /** Ask for a code and resolve once it is typed, or once the user gives up. */
  private _askForCode(retry: boolean): Promise<string | undefined> {
    return new Promise((resolve) => {
      this._asking = { resolve, retry };
      this.requestUpdate();
    });
  }

  private _answerCode(code?: string): void {
    const asking = this._asking;
    this._asking = undefined;
    this._code = code;
    this.requestUpdate();
    asking?.resolve(code);
  }

  /** Run a command, and ask for a code if the backend says one is needed.
   *
   * The panel never decides whether a code is required: it sends the command,
   * and the refusal that comes back is what opens the keypad (INV-2). */
  private async _coded<T extends { success: boolean; reason?: string | null }>(
    run: (code?: string) => Promise<T>,
  ): Promise<T> {
    let result = await run(this._code);
    for (let attempt = 0; attempt < 3; attempt++) {
      if (result.success) return result;
      if (result.reason !== "code_required" && result.reason !== "bad_code") return result;
      const code = await this._askForCode(result.reason === "bad_code");
      if (code === undefined) return result;
      result = await run(code);
    }
    return result;
  }

  private _start(): void {
    if (!this.hass || this._unsubscribe) return;
    this._unsubscribe = this.hass.connection.subscribeMessage<FoyerStatus>(
      (status) => {
        this._offset = Date.parse(status.now) - Date.now();
        this._status = status;
        this._error = undefined;
        // Who is connected only becomes known with the first status, and it
        // is what says whether the configuration may be read at all (§8.3).
        if (!this._config && this._canConfigure) this._loadConfig().catch(() => undefined);
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
    if (this._isAdmin) {
      // For linking a person to a Home Assistant account (§8.2). Best effort:
      // page 7 simply offers no list if this is refused.
      this.hass
        .callWS<{ id: string; name: string; system_generated: boolean }[]>({
          type: "config/auth/list",
        })
        .then((users) => (this._haUsers = users.filter((u) => !u.system_generated)))
        .catch(() => undefined);
    }
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
      haUsers: this._haUsers,
      now: () => Date.now() + this._offset,
      navigate: (page) => (this._page = page),
      arm: (target) =>
        this._coded((code) =>
          hass.callWS<CommandResult>({ type: "foyer/arm", ...target, ...withCode(code) }),
        ),
      disarm: (areaIds) =>
        this._coded((code) =>
          hass.callWS<CommandResult>({
            type: "foyer/disarm",
            ...(areaIds ? { area_ids: areaIds } : {}),
            ...withCode(code),
          }),
        ),
      acknowledge: (target) =>
        this._coded((code) =>
          hass.callWS<CommandResult>({
            type: "foyer/acknowledge",
            target,
            ...withCode(code),
          }),
        ),
      saveChime: (chime) => this._edit("chime", { type: "foyer/config/chime", chime }),
      saveSettings: (settings) =>
        this._edit("settings", {
          type: "foyer/config/settings",
          settings: { ...this._config?.settings, ...settings },
        }),
      queryLog: (query) =>
        hass.callWS({ type: "foyer/log/query", ...prune(query) }),
      exportLog: (query, format) =>
        hass.callWS({ type: "foyer/log/export", format, ...prune(query) }),
      clearLog: async () => {
        const result = await hass.callWS<{ success: boolean; removed: number }>({
          type: "foyer/log/clear",
        });
        return result;
      },
      exportConfig: () => hass.callWS({ type: "foyer/config/export" }),
      importConfig: (document) =>
        this._edit("config", { type: "foyer/config/import", document }),
      bypass: (zoneId, bypass, seconds) =>
        this._coded((code) =>
          hass.callWS<CommandResult>({
            type: "foyer/bypass",
            zone_id: zoneId,
            bypass,
            ...(seconds ? { seconds } : {}),
            ...withCode(code),
          }),
        ),
      saveUser: (user, codes) =>
        this._edit("user", { type: "foyer/user/save", user, ...codes }),
      saveSecurity: (code_policy, security) =>
        this._edit("settings", {
          type: "foyer/config/security",
          code_policy,
          security,
        }),
      save: (kind, item, triggerConfirmed = false) =>
        this._edit(kind, {
          type: "foyer/config/save",
          kind,
          item,
          trigger_confirmed: triggerConfirmed,
        }),
      remove: (kind, id) =>
        this._edit(kind, { type: "foyer/config/delete", kind, item_id: id }),
    };
  }

  // Every configuration write goes through here. A request that fails outright
  // (connection lost, integration reloading, command rejected) comes back as a
  // problem the page shows, never as a silent no-op.
  private async _edit(kind: string, message: Record<string, unknown>): Promise<EditResult> {
    let result: EditResult;
    try {
      // Editing the configuration needs a code too (§8.2), and the backend is
      // what says so: this asks only when it has refused for that reason.
      result = await this._coded((code) =>
        this.hass!.callWS<EditResult>({ ...message, ...withCode(code) }),
      );
    } catch (err) {
      const detail = String((err as { message?: string })?.message ?? err);
      return {
        success: false,
        problems: [{ code: "request_failed", kind, ref: null, field: null, detail }],
      };
    }
    if (result.success) await this._reloadConfigSoon();
    return result;
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
      ${this._asking && s ? this._renderCodeDialog(s) : nothing}
    `;
  }

  private _renderCodeDialog(s: Strings) {
    const length = this._status?.security.code_length ?? 6;
    const submit = (event: Event) => {
      event.preventDefault();
      const input = (event.target as HTMLFormElement).elements.namedItem(
        "code",
      ) as HTMLInputElement;
      this._answerCode(input.value);
    };
    return html`
      <div class="scrim" @click=${() => this._answerCode(undefined)}></div>
      <form class="code-dialog" @submit=${submit} @click=${(e: Event) => e.stopPropagation()}>
        <h2>${t(s, "code.title")}</h2>
        <p>${this._asking?.retry ? t(s, "code.wrong") : t(s, "code.prompt", { n: length })}</p>
        <input
          name="code"
          type="password"
          inputmode="numeric"
          autocomplete="off"
          maxlength=${length}
          autofocus
        />
        <div class="row">
          <button type="button" class="btn" @click=${() => this._answerCode(undefined)}>
            ${t(s, "common.cancel")}
          </button>
          <button type="submit" class="btn primary">${t(s, "common.ok")}</button>
        </div>
      </form>
    `;
  }

  private _renderTabs(s: Strings) {
    const pages = this._canConfigure
      ? PAGES
      : PAGES.filter((p) => !CONFIG_PAGES.includes(p));
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
    // The first-run wizard sits above whatever page is open until it is
    // finished or dismissed: it is about the installation, not about a page.
    const wizard =
      this._canConfigure && this._config && !this._config.settings.wizard_done
        ? html`<foyer-wizard
            .ctx=${ctx}
            @wizard-done=${() => void this._loadConfig()}
          ></foyer-wizard>`
        : nothing;
    return html`
      ${wizard} ${this._prefs.help_hidden ? nothing : this._renderHelp(s, page)}
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
      case "profiles":
        return html`<foyer-page-profiles .ctx=${ctx}></foyer-page-profiles>`;
      case "groups":
        return html`<foyer-page-groups .ctx=${ctx}></foyer-page-groups>`;
      case "users":
        return html`<foyer-page-users .ctx=${ctx}></foyer-page-users>`;
      case "devices":
        return html`<foyer-page-devices .ctx=${ctx}></foyer-page-devices>`;
      case "log":
        return html`<foyer-page-log .ctx=${ctx}></foyer-page-log>`;
      case "settings":
        return html`<foyer-page-settings .ctx=${ctx}></foyer-page-settings>`;
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
      /* The code dialog: over everything, because nothing else can happen
         until it is answered — the command that opened it is waiting. */
      .scrim {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.55);
        z-index: 10;
      }
      .code-dialog {
        position: fixed;
        z-index: 11;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: min(320px, calc(100vw - 32px));
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 20px;
        border-radius: 12px;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
      }
      .code-dialog h2 {
        margin: 0;
        font-size: 18px;
      }
      .code-dialog p {
        margin: 0;
        color: var(--secondary-text-color);
        font-size: 14px;
      }
      .code-dialog input {
        font-size: 24px;
        letter-spacing: 8px;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid var(--divider-color);
        background: var(--primary-background-color);
        color: var(--primary-text-color);
      }
      .code-dialog .row {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
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
