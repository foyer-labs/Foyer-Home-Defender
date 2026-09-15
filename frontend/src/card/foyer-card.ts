// foyer-card: an area's (or the master's) state, its countdown, and arm/disarm
// (SPEC §15.3). The card decides nothing (INV-2): it sends a command, the
// engine accepts or refuses, and the card renders the answer. The full and
// compact layouts arrive with the rest of the card work (Phase 1, part 4).
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

interface FoyerCardConfig {
  type: string;
  entity?: string;
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
    const entity = Object.keys(hass.states).find((id) => id.startsWith(ENTITY_PREFIX));
    return { type: "custom:foyer-card", entity };
  }

  setConfig(config: FoyerCardConfig): void {
    this._config = config;
  }

  getCardSize(): number {
    return 3;
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
    return this._isMaster ? this._renderMaster(s) : this._renderArea(s);
  }

  private _renderArea(s: Strings) {
    const area = this._area;
    if (!area) return this._message(t(s, "common.loading"));
    const canDisarm = area.state !== "disarmed" || area.memory;
    return html`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(s)} ${this._head(area.name, area.state, area.memory)}
          ${this._countdown(s, area)}
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
          ${status.areas.map((area) => this._countdown(s, area, true))}
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
