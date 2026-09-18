// foyer-card: an area's (or the master's) state, its countdown, and arm/disarm
// (SPEC §15.3). The card decides nothing (INV-2): it sends a command, the
// engine accepts or refuses, and the card renders the answer.
//
// Two layouts in this phase. `full` is the alarm dashboard: every area with
// its state and countdown, the scenario selector, and the zones that would
// stop it arming, each with a way out. `compact` is one row for the top of an
// existing dashboard: the state and one action. The keypad of §15.3 belongs
// to Phase 2, because a keypad without codes to check is decoration.
import { LitElement, css, html, nothing, type PropertyValues } from "lit";

import { loadStrings, t, type Strings } from "../shared/i18n";
import { stateStyles } from "../shared/styles";
import type {
  AreaState,
  CommandResult,
  FoyerStatus,
  HomeAssistant,
  StatusArea,
} from "../shared/types";

type Layout = "full" | "compact";

interface FoyerCardConfig {
  type: string;
  entity?: string;
  layout?: Layout;
}

const ENTITY_PREFIX = "alarm_control_panel.foyer_";
const MASTER = "alarm_control_panel.foyer_master";

class FoyerCard extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
    _strings: { state: true },
    _status: { state: true },
    _busy: { state: true },
    _feedback: { state: true },
    _tick: { state: true },
  };

  hass?: HomeAssistant;
  private _config?: FoyerCardConfig;
  private _strings?: Strings;
  private _status?: FoyerStatus;
  private _busy = false;
  private _feedback?: string;
  private _tick = 0;
  private _offset = 0;
  private _language?: string;
  private _unsubscribe?: Promise<() => Promise<void>>;
  private _timer?: number;

  static getStubConfig(hass: HomeAssistant): FoyerCardConfig {
    // The master if it exists: a card that shows the whole house is the one
    // most people want first.
    const entities = Object.keys(hass.states).filter((id) => id.startsWith(ENTITY_PREFIX));
    return {
      type: "custom:foyer-card",
      entity: entities.includes(MASTER) ? MASTER : entities[0],
      layout: "full",
    };
  }

  static getConfigElement(): HTMLElement {
    return document.createElement("foyer-card-editor");
  }

  setConfig(config: FoyerCardConfig): void {
    this._config = config;
  }

  getCardSize(): number {
    return this._layout === "compact" ? 1 : 3;
  }

  private get _layout(): Layout {
    return this._config?.layout === "compact" ? "compact" : "full";
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => {
      if (this._area?.timer || this._isMaster) this._tick += 1;
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
      loadStrings(this.hass).then((strings) => (this._strings = strings));
    }
    if (!this._unsubscribe && this.isConnected) {
      this._unsubscribe = this.hass.connection.subscribeMessage<FoyerStatus>(
        (status) => {
          this._offset = Date.parse(status.now) - Date.now();
          this._status = status;
        },
        { type: "foyer/subscribe" },
      );
      this._unsubscribe.catch(() => (this._unsubscribe = undefined));
    }
  }

  private get _isMaster(): boolean {
    return this._config?.entity === MASTER;
  }

  private get _area(): StatusArea | undefined {
    return this._status?.areas.find((a) => a.entity_id === this._config?.entity);
  }

  private async _run(command: Record<string, unknown>): Promise<void> {
    if (!this.hass) return;
    this._busy = true;
    this._feedback = undefined;
    try {
      const result = await this.hass.callWS<CommandResult>(command);
      if (!result.success) {
        this._feedback = t(this._strings, `reason.${result.reason ?? "unknown"}`, {
          zones: result.blocking_zones.map((z) => z.name).join(", "),
        });
      }
    } catch (err) {
      this._feedback = String((err as Error)?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const s = this._strings;
    if (!s || !this.hass) return nothing;
    void this._tick;
    const entityId = this._config?.entity;
    if (!entityId) return this._message(t(s, "card.no_entity"));
    if (!this.hass.states[entityId]) {
      return this._message(t(s, "card.entity_missing", { entity: entityId }));
    }
    if (this._layout === "compact") return this._renderCompact(s);
    return this._isMaster ? this._renderMaster(s) : this._renderArea(s);
  }

  // --- compact: state, one action, and the scenario (§15.3) ------------------------

  private _renderCompact(s: Strings) {
    const status = this._status;
    if (!status) return this._message(t(s, "common.loading"));
    const area = this._area;
    const master = this._isMaster || !area;
    const state = master ? status.master.state : area!.state;
    const memory = master ? status.areas.some((a) => a.memory) : area!.memory;
    const active = status.scenarios.find((sc) => sc.id === status.active_scenario_id);
    const name = master ? (active?.name ?? t(s, "overview.master")) : area!.name;
    const armed = master
      ? status.areas.some((a) => a.state !== "disarmed" || a.memory)
      : area!.state !== "disarmed" || area!.memory;
    const countdown = master
      ? status.areas.find((a) => a.timer && a.timer.kind !== "siren")
      : area;
    return html`
      <ha-card>
        <div class="content compact">
          <div class="head">
            <div class="name">${name}</div>
            <span class="state ${state}">${t(s, `state.${state}`)}</span>
            ${memory
              ? html`<span class="state memory">${t(s, "overview.memory")}</span>`
              : nothing}
          </div>
          ${countdown ? this._countdown(s, countdown) : nothing}
          <div class="buttons">
            ${master
              ? html`<select
                  ?disabled=${this._busy}
                  aria-label=${t(s, "card.scenario")}
                  @change=${(e: Event) => {
                    const id = (e.target as HTMLSelectElement).value;
                    if (id) void this._run({ type: "foyer/arm", scenario_id: id });
                  }}
                >
                  <option value="" ?selected=${!active}>${t(s, "card.pick_scenario")}</option>
                  ${status.scenarios.map(
                    (sc) => html`<option .value=${sc.id} ?selected=${sc.id === active?.id}>
                      ${sc.name}
                    </option>`,
                  )}
                </select>`
              : area!.state === "disarmed"
                ? html`<button
                    class="primary"
                    ?disabled=${this._busy}
                    @click=${() => this._run({ type: "foyer/arm", area_id: area!.id })}
                  >
                    ${t(s, "card.arm")}
                  </button>`
                : nothing}
            ${armed
              ? html`<button
                  ?disabled=${this._busy}
                  @click=${() =>
                    this._run(
                      master
                        ? { type: "foyer/disarm" }
                        : { type: "foyer/disarm", area_ids: [area!.id] },
                    )}
                >
                  ${t(s, "card.disarm")}
                </button>`
              : nothing}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
  }

  private _renderArea(s: Strings) {
    const area = this._area;
    if (!area) return this._message(t(s, "common.loading"));
    const canDisarm = area.state !== "disarmed" || area.memory;
    return html`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(s)} ${this._head(area.name, area.state, area.memory)}
          ${this._countdown(s, area)} ${this._renderBlocking(s, area)}
          <div class="buttons">
            ${area.state === "disarmed"
              ? html`<button
                  class="primary"
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/arm", area_id: area.id })}
                >
                  ${t(s, "card.arm")}
                </button>`
              : nothing}
            ${canDisarm
              ? html`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/disarm", area_ids: [area.id] })}
                >
                  ${t(s, "card.disarm")}
                </button>`
              : nothing}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
  }

  /** The zones that stop this area arming, each with a way out (§5.4, §16).
   *
   * Excluding a zone from the card is the same command the panel sends; the
   * engine decides whether it may be excluded at all (INV-2).
   */
  private _renderBlocking(s: Strings, area: StatusArea) {
    if (area.state !== "disarmed" || area.ready) return nothing;
    const zones = this._status?.zones ?? [];
    const blocking = [...area.blocking.fault, ...area.blocking.open]
      .map((id) => zones.find((z) => z.id === id))
      .filter((zone): zone is NonNullable<typeof zone> => Boolean(zone));
    if (!blocking.length) return nothing;
    return html`
      <div class="blocking">
        ${blocking.map(
          (zone) => html`<div class="row">
            <span>${zone.name}</span>
            ${zone.bypassable
              ? html`<button
                  class="link"
                  ?disabled=${this._busy}
                  @click=${() =>
                    this._run({ type: "foyer/bypass", zone_id: zone.id, bypass: true })}
                >
                  ${t(s, "zones.bypass")}
                </button>`
              : nothing}
          </div>`,
        )}
      </div>
    `;
  }

  private _renderMaster(s: Strings) {
    const status = this._status;
    if (!status) return this._message(t(s, "common.loading"));
    const memory = status.areas.some((a) => a.memory);
    const active = status.scenarios.find((sc) => sc.id === status.active_scenario_id);
    const anyArmed = status.areas.some((a) => a.state !== "disarmed" || a.memory);
    return html`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(s)}
          ${this._head(active?.name ?? t(s, "overview.master"), status.master.state, memory)}
          <div class="areas">
            ${status.areas.map(
              (area) => html`<div class="row">
                <span class="area-name">${area.name}</span>
                <span class="state ${area.state}">${t(s, `state.${area.state}`)}</span>
                ${area.memory
                  ? html`<span class="state memory">${t(s, "overview.memory")}</span>`
                  : nothing}
                ${this._countdown(s, area)}
              </div>`,
            )}
          </div>
          ${this._renderNotReady(s)}
          <div class="buttons">
            ${status.scenarios.map(
              (sc) => html`<button
                class=${sc.id === status.active_scenario_id ? "primary" : ""}
                ?disabled=${this._busy}
                @click=${() => this._run({ type: "foyer/arm", scenario_id: sc.id })}
              >
                ${sc.name}
              </button>`,
            )}
            ${anyArmed
              ? html`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/disarm" })}
                >
                  ${t(s, "card.disarm")}
                </button>`
              : nothing}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
  }

  /** Every zone that would stop some area arming, with a way out (§15.3).
   *
   * On the master's card, because that is the card somebody looks at before
   * leaving the house — and "it would not arm and did not say why" is the
   * complaint this list exists to prevent.
   */
  private _renderNotReady(s: Strings) {
    const status = this._status;
    if (!status) return nothing;
    const blocking = new Map<string, string[]>();
    for (const area of status.areas) {
      if (area.state !== "disarmed" || area.ready) continue;
      for (const id of [...area.blocking.fault, ...area.blocking.open]) {
        blocking.set(id, [...(blocking.get(id) ?? []), area.name]);
      }
    }
    if (!blocking.size) return nothing;
    return html`
      <div class="blocking">
        <div class="blocking-hd">${t(s, "card.not_ready")}</div>
        ${[...blocking.entries()].map(([id, areas]) => {
          const zone = status.zones.find((z) => z.id === id);
          if (!zone) return nothing;
          return html`<div class="row">
            <span>${t(s, "card.zone_in", { zone: zone.name, areas: areas.join(", ") })}</span>
            ${zone.bypassable && !zone.bypassed
              ? html`<button
                  class="link"
                  ?disabled=${this._busy}
                  @click=${() =>
                    this._run({ type: "foyer/bypass", zone_id: zone.id, bypass: true })}
                >
                  ${t(s, "zones.bypass")}
                </button>`
              : nothing}
          </div>`;
        })}
      </div>
    `;
  }

  // The technical alarm and the open incident show on every card, whatever
  // area it shows (§5.5): each with its own acknowledgement, never merged.
  private _renderAlerts(s: Strings) {
    const status = this._status;
    if (!status) return nothing;
    const names = new Map(status.zones.map((z) => [z.id, z.name]));
    const technical = status.technical ?? [];
    const incident = status.incident;
    return html`
      ${technical.length
        ? html`<div class="alert technical" role="alert">
            <span>${t(s, "card.technical", { zones: technical.map((a) => a.name).join(", ") })}</span>
            ${technical.some((a) => !a.acknowledged)
              ? html`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/acknowledge", target: "technical" })}
                >
                  ${t(s, "common.acknowledge")}
                </button>`
              : nothing}
          </div>`
        : nothing}
      ${incident
        ? html`<div class="alert incident" role="alert">
            <span>
              ${t(s, "card.incident", {
                zones: incident.zone_ids.map((z) => names.get(z) ?? z).join(", "),
              })}
            </span>
            ${incident.acknowledged
              ? nothing
              : html`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/acknowledge", target: "incident" })}
                >
                  ${t(s, "common.acknowledge")}
                </button>`}
          </div>`
        : nothing}
    `;
  }

  private _head(name: string, state: AreaState, memory: boolean) {
    const s = this._strings;
    return html`
      <div class="head">
        <div class="name">${name}</div>
        <span class="state ${state}">${t(s, `state.${state}`)}</span>
        ${memory ? html`<span class="state memory">${t(s, "overview.memory")}</span>` : nothing}
      </div>
    `;
  }

  private _countdown(s: Strings, area: StatusArea, named = false) {
    if (!area.timer || area.timer.kind === "siren") return nothing;
    const seconds = Math.max(
      0,
      Math.round((Date.parse(area.timer.due) - (Date.now() + this._offset)) / 1000),
    );
    const text = t(s, `timer.${area.timer.kind}`, { seconds });
    return html`<div class="countdown">
      ${named ? t(s, "card.area_countdown", { area: area.name, countdown: text }) : text}
    </div>`;
  }

  private _renderFeedback() {
    return this._feedback
      ? html`<div class="feedback" role="alert">${this._feedback}</div>`
      : nothing;
  }

  private _message(text: string) {
    return html`<ha-card><div class="content">${text}</div></ha-card>`;
  }

  static override styles = [
    stateStyles,
    css`
      .content {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .head {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
      }
      .name {
        font-size: 18px;
        font-weight: 500;
        flex: 1;
      }
      .countdown {
        font-size: 15px;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
      }
      .blocking {
        margin: 8px 0 0;
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      .blocking .row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 2px 0;
      }
      .areas {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .areas .row {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }
      .area-name {
        /* Keep the name on one line: the state chip and the countdown wrap
           below it rather than squeezing it to two words a line. */
        flex: 1 0 auto;
        min-width: 40%;
        font-size: 14px;
      }
      .blocking-hd {
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 4px;
      }
      .content.compact {
        padding: 12px 16px;
        gap: 8px;
      }
      .content.compact .head .name {
        font-size: 16px;
      }
      select {
        font: inherit;
        font-size: 14px;
        padding: 9px 10px;
        border-radius: 8px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
      }
      .blocking .link {
        background: none;
        border: 0;
        padding: 0;
        color: var(--primary-color);
        font: inherit;
        cursor: pointer;
      }
      .buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      button {
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 10px 16px;
        font: inherit;
        font-weight: 500;
        cursor: pointer;
        background: var(--card-background-color);
        color: var(--primary-text-color);
      }
      button.primary {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      button[disabled] {
        opacity: 0.5;
        cursor: default;
      }
      .feedback {
        color: var(--error-color);
        font-size: 14px;
      }
      .alert {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 12px;
        padding: 8px 12px;
        border-radius: 8px;
        border-left: 4px solid var(--error-color, #d32f2f);
        background: var(--secondary-background-color);
        font-weight: 500;
      }
      .alert.incident {
        border-left-color: var(--warning-color, #c77700);
      }
      .alert span {
        flex: 1;
      }
      .alert button {
        padding: 6px 12px;
      }
    `,
  ];
}

if (!customElements.get("foyer-card")) customElements.define("foyer-card", FoyerCard);


// --- the visual editor (§15.3) ------------------------------------------------------
//
// Two things to choose: which panel the card shows, and how much of it. The
// editor writes the same YAML a person would write by hand, so switching
// between the two never loses anything.

class FoyerCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
    _strings: { state: true },
  };

  hass?: HomeAssistant;
  private _config: FoyerCardConfig = { type: "custom:foyer-card" };
  private _strings?: Strings;
  private _language?: string;

  setConfig(config: FoyerCardConfig): void {
    this._config = config;
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (!changed.has("hass") || !this.hass) return;
    if (this.hass.language !== this._language) {
      this._language = this.hass.language;
      loadStrings(this.hass).then((strings) => (this._strings = strings));
    }
  }

  private _emit(changes: Partial<FoyerCardConfig>): void {
    this._config = { ...this._config, ...changes };
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      }),
    );
  }

  override render() {
    const s = this._strings;
    if (!s || !this.hass) return nothing;
    const panels = Object.keys(this.hass.states)
      .filter((id) => id.startsWith(ENTITY_PREFIX))
      .sort();
    return html`
      <div class="editor">
        <label>
          <span>${t(s, "card.editor_entity")}</span>
          <select
            @change=${(e: Event) => this._emit({ entity: (e.target as HTMLSelectElement).value })}
          >
            ${panels.map(
              (id) => html`<option .value=${id} ?selected=${id === this._config.entity}>
                ${id === MASTER
                  ? t(s, "card.editor_master")
                  : String(this.hass!.states[id]?.attributes.friendly_name ?? id)}
              </option>`,
            )}
          </select>
        </label>
        <label>
          <span>${t(s, "card.editor_layout")}</span>
          <select
            @change=${(e: Event) =>
              this._emit({ layout: (e.target as HTMLSelectElement).value as Layout })}
          >
            ${(["full", "compact"] as Layout[]).map(
              (layout) => html`<option
                .value=${layout}
                ?selected=${layout === (this._config.layout ?? "full")}
              >
                ${t(s, `card.layout_${layout}`)}
              </option>`,
            )}
          </select>
        </label>
        <p class="hint">${t(s, "card.editor_hint")}</p>
      </div>
    `;
  }

  static override styles = css`
    .editor {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 8px 0;
    }
    label {
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 13px;
      font-weight: 500;
    }
    select {
      font: inherit;
      font-size: 14px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color);
      color: var(--primary-text-color);
    }
    .hint {
      margin: 0;
      font-size: 12.5px;
      font-weight: 400;
      color: var(--secondary-text-color);
    }
  `;
}

if (!customElements.get("foyer-card-editor")) {
  customElements.define("foyer-card-editor", FoyerCardEditor);
}


// Listed in the dashboard's "add card" picker.
declare global {
  interface Window {
    customCards?: { type: string; name: string; description?: string; preview?: boolean }[];
  }
}
window.customCards = window.customCards ?? [];
if (!window.customCards.some((c) => c.type === "foyer-card")) {
  window.customCards.push({ type: "foyer-card", name: "Foyer Home Defender", preview: true });
}
