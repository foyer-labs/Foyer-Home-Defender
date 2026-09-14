// The Foyer sidebar panel. Phase 0: a single status screen, live over
// foyer/subscribe, with its "About this section" help (SPEC §15.2).
import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";

import { brandSymbol } from "../shared/brand";
import { loadStrings, t, type Strings } from "../shared/i18n";
import { stateStyles } from "../shared/styles";
import type { FoyerStatus, HomeAssistant } from "../shared/types";

const PAGE = "overview";
const HELP_ITEMS = ["area", "scenario", "zone"] as const;

class FoyerPanel extends LitElement {
  static override properties = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    _strings: { state: true },
    _status: { state: true },
    _error: { state: true },
    _helpOpen: { state: true },
  };

  hass?: HomeAssistant;
  narrow = false;
  private _strings?: Strings;
  private _status?: FoyerStatus;
  private _error?: string;
  // Expanded on first visit. Remembering the choice per HA user belongs to the
  // Foyer config (not localStorage) and arrives with the configuration pages.
  private _helpOpen = true;
  private _language?: string;
  private _unsubscribe?: Promise<() => Promise<void>>;

  override connectedCallback(): void {
    super.connectedCallback();
    if (this.hass) this._subscribe();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsub) => unsub()).catch(() => undefined);
    this._unsubscribe = undefined;
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (!changed.has("hass") || !this.hass) return;
    if (this.hass.language !== this._language) {
      this._language = this.hass.language;
      loadStrings(this.hass)
        .then((strings) => (this._strings = strings))
        .catch((err) => (this._error = String(err?.message ?? err)));
    }
    if (!this._unsubscribe && this.isConnected) this._subscribe();
  }

  private _subscribe(): void {
    if (!this.hass || this._unsubscribe) return;
    this._unsubscribe = this.hass.connection.subscribeMessage<FoyerStatus>(
      (status) => {
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
  }

  override render() {
    const s = this._strings;
    return html`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="symbol" aria-hidden="true"
          >${unsafeSVG(brandSymbol(Boolean(this.hass?.themes?.darkMode)))}</span
        >
        <div class="title">${t(s, "common.brand")}</div>
        ${this._status ? html`<span class="live">${t(s, "common.live")}</span>` : nothing}
      </div>
      <main>
        ${s ? this._renderBody(s) : nothing}
      </main>
    `;
  }

  private _renderBody(s: Strings) {
    return html`
      <div class="warning" role="note">${t(s, "overview.phase0_warning")}</div>
      ${this._renderHelp(s)}
      <h1>${t(s, "overview.heading")}</h1>
      ${this._error ? html`<p class="error">${this._error}</p>` : nothing}
      ${this._status ? this._renderStatus(s, this._status) : this._error
        ? nothing
        : html`<p class="muted">${t(s, "common.loading")}</p>`}
    `;
  }

  private _renderHelp(s: Strings) {
    const base = `help.${PAGE}`;
    return html`
      <section class="help" ?data-open=${this._helpOpen}>
        <button
          class="help-hd"
          aria-expanded=${this._helpOpen ? "true" : "false"}
          @click=${() => (this._helpOpen = !this._helpOpen)}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
          <span>${t(s, `${base}.title`)}</span>
          <span class="sr-only">${t(s, "help.toggle")}</span>
          <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon>
        </button>
        ${this._helpOpen
          ? html`<div class="help-body">
              <p>${t(s, `${base}.intro`)}</p>
              <dl>
                ${HELP_ITEMS.map(
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

  private _renderStatus(s: Strings, status: FoyerStatus) {
    const scenario = status.scenarios.find((sc) => sc.id === status.active_scenario_id);
    return html`
      <div class="grid">
        ${status.areas.map(
          (area) => html`
            <ha-card>
              <div class="label">${t(s, "overview.area")}</div>
              <div class="name">${area.name}</div>
              <span class="state ${area.state}">${t(s, `state.${area.state}`)}</span>
              ${area.entity_id ? html`<div class="meta">${area.entity_id}</div>` : nothing}
            </ha-card>
          `,
        )}
        <ha-card>
          <div class="label">${t(s, "overview.scenario")}</div>
          <div class="name">${scenario ? scenario.name : t(s, "overview.scenario_none")}</div>
        </ha-card>
        ${status.zones.map((zone) => {
          const kind = zone.fault ? "fault" : zone.open ? "open" : "closed";
          return html`
            <ha-card>
              <div class="label">${t(s, "overview.zone")}</div>
              <div class="name">${zone.name}</div>
              <span class="state ${kind}">${t(s, `zone_status.${kind}`)}</span>
              <div class="meta">
                ${zone.entity_id} ·
                ${t(s, "overview.entity_state", { state: zone.state ?? "—" })}
              </div>
            </ha-card>
          `;
        })}
      </div>
    `;
  }

  static override styles = [
    stateStyles,
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
      main {
        max-width: 960px;
        margin: 0 auto;
        padding: 16px;
      }
      h1 {
        font-size: 18px;
        font-weight: 500;
        margin: 8px 0 12px;
      }
      .warning {
        border-left: 3px solid var(--warning-color, #c77700);
        background: var(--card-background-color);
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 16px;
        font-size: 13.5px;
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
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 12px;
      }
      ha-card {
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;
      }
      .label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--secondary-text-color);
      }
      .name {
        font-size: 18px;
        font-weight: 500;
      }
      .meta {
        font-size: 12px;
        color: var(--secondary-text-color);
        font-family: var(--code-font-family, monospace);
        overflow-wrap: anywhere;
      }
      .muted {
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
