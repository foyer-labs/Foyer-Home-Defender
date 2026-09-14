// foyer-card: shows the area state and sends an arm command (SPEC §15.3).
// The card decides nothing (INV-2): it calls the alarm_control_panel service,
// the engine accepts or refuses, and the card renders the outcome.
import { LitElement, css, html, nothing, type PropertyValues } from "lit";

import { loadStrings, t, type Strings } from "../shared/i18n";
import { stateStyles } from "../shared/styles";
import type {
  AreaState,
  FoyerStatus,
  HassServiceError,
  HomeAssistant,
} from "../shared/types";

interface FoyerCardConfig {
  type: string;
  entity?: string;
}

const ENTITY_PREFIX = "alarm_control_panel.foyer_";

// Home Assistant alarm states -> Foyer area states, for display.
function areaState(haState: string): AreaState {
  if (haState === "triggered") return "triggered";
  if (haState.startsWith("armed_")) return "armed";
  return "disarmed";
}

class FoyerCard extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
    _strings: { state: true },
    _status: { state: true },
    _busy: { state: true },
    _feedback: { state: true },
  };

  hass?: HomeAssistant;
  private _config?: FoyerCardConfig;
  private _strings?: Strings;
  private _status?: FoyerStatus;
  private _busy = false;
  private _feedback?: string;
  private _rejection?: HassServiceError;
  private _language?: string;
  private _unsubscribe?: Promise<() => Promise<void>>;

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

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsub) => unsub()).catch(() => undefined);
    this._unsubscribe = undefined;
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (!changed.has("hass") || !this.hass) return;
    if (this.hass.language !== this._language) {
      this._language = this.hass.language;
      loadStrings(this.hass).then((strings) => (this._strings = strings));
      // A rejection already on screen follows the new language too.
      if (this._rejection) this._showRejection(this._rejection);
    }
    // Scenario names come from Foyer; the area state itself comes from the
    // entity, like any other alarm card.
    if (!this._unsubscribe && this.isConnected) {
      this._unsubscribe = this.hass.connection.subscribeMessage<FoyerStatus>(
        (status) => (this._status = status),
        { type: "foyer/subscribe" },
      );
      this._unsubscribe.catch(() => (this._unsubscribe = undefined));
    }
  }

  private get _area() {
    return this._status?.areas.find((a) => a.entity_id === this._config?.entity);
  }

  private get _scenario() {
    const area = this._area;
    return area ? this._status?.scenarios.find((s) => s.areas.includes(area.id)) : undefined;
  }

  private async _arm(): Promise<void> {
    const scenario = this._scenario;
    if (!this.hass || !this._config?.entity || !scenario) return;
    this._busy = true;
    this._feedback = undefined;
    this._rejection = undefined;
    try {
      await this.hass.callService(
        "alarm_control_panel",
        `alarm_arm_${scenario.ha_master_state.replace(/^armed_/, "")}`,
        {},
        { entity_id: this._config.entity },
      );
    } catch (err) {
      this._rejection = err as HassServiceError;
      await this._showRejection(this._rejection);
    } finally {
      this._busy = false;
    }
  }

  // The engine's reason, translated by Home Assistant from the integration's
  // "exceptions" strings in the user's language: "Cannot arm: zone open: …".
  private async _showRejection(err: HassServiceError): Promise<void> {
    let text = "";
    if (this.hass && err.translation_domain && err.translation_key) {
      await this.hass.loadBackendTranslation("exceptions", err.translation_domain);
      text = this.hass.localize(
        `component.${err.translation_domain}.exceptions.${err.translation_key}.message`,
        err.translation_placeholders,
      );
    }
    this._feedback = text || err.message || String(err);
  }

  override render() {
    const s = this._strings;
    if (!s || !this.hass) return nothing;
    const entityId = this._config?.entity;
    if (!entityId) return this._message(t(s, "card.no_entity"));
    const entity = this.hass.states[entityId];
    if (!entity) return this._message(t(s, "card.entity_missing", { entity: entityId }));

    const state = areaState(entity.state);
    const scenario = this._scenario;
    return html`
      <ha-card>
        <div class="content">
          <div class="head">
            <div class="name">${this._area?.name ?? entityId}</div>
            <span class="state ${state}">${t(s, `state.${state}`)}</span>
          </div>
          ${scenario
            ? html`<button
                class="arm"
                ?disabled=${this._busy || state !== "disarmed"}
                @click=${this._arm}
              >
                ${t(s, "card.arm", { scenario: scenario.name })}
              </button>`
            : nothing}
          ${this._feedback
            ? html`<div class="feedback" role="alert">${this._feedback}</div>`
            : nothing}
        </div>
      </ha-card>
    `;
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
        justify-content: space-between;
        gap: 12px;
      }
      .name {
        font-size: 18px;
        font-weight: 500;
      }
      .arm {
        align-self: flex-start;
        border: 0;
        border-radius: 8px;
        padding: 10px 16px;
        font: inherit;
        font-weight: 500;
        cursor: pointer;
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      .arm[disabled] {
        opacity: 0.5;
        cursor: default;
      }
      .feedback {
        color: var(--error-color);
        font-size: 14px;
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
