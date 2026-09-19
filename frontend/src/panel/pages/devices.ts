// Page 8 — Arming devices (SPEC §9.3, §15.1). Keypad models churn every six
// months; the contract does not. Anything that can call a service or publish
// to a broker can arm this house — provided it is declared here first.
//
// That last clause is the page (part 2 decision 1). This is a white list, not
// an address book: a device this configuration does not carry is refused,
// whatever code it brings, because the lockout of §8.4 counts per device and a
// caller free to invent one is a caller who is never locked out.
//
// The other thing this page has to say out loud is §9.3's own sentence: a
// stolen tag arms and disarms without knowing any code. It is written where
// somebody is deciding whether to keep a tag in their wallet, not in a
// document they will not read.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  DeviceConfig,
  MqttConfig,
  Problem,
  SettingsConfig,
} from "../../shared/types";
import { problemText, type PanelContext } from "../context";

const EMPTY: DeviceConfig = {
  name: "",
  kind: "keypad",
  ref: "",
  entity_id: null,
  event_type: null,
  user_id: null,
  command: "toggle",
  scenario_id: null,
  enabled: true,
};

/** The entity domains a tag or a remote can arrive on (§4.4, §9.3). */
const TOKEN_DOMAINS = ["tag.", "event."];

class FoyerPageDevices extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _problems: { state: true },
    _busy: { state: true },
    _mqtt: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: DeviceConfig;
  private _problems: Problem[] = [];
  private _busy = false;
  private _mqtt?: MqttConfig;

  private _edit(device?: DeviceConfig): void {
    this._draft = device ? structuredClone(device) : structuredClone(EMPTY);
    this._problems = [];
  }

  private _set<K extends keyof DeviceConfig>(key: K, value: DeviceConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private _setKind(kind: DeviceConfig["kind"]): void {
    // A keypad has no entity and no owner; a tag has no name anybody could
    // type. Clearing the other kind's fields here keeps the editor honest
    // rather than letting the backend refuse a shape nobody meant.
    if (kind === "keypad") {
      this._draft = {
        ...this._draft!,
        kind,
        entity_id: null,
        event_type: null,
        user_id: null,
        ref: this._draft?.ref || "",
      };
    } else {
      this._draft = { ...this._draft!, kind, ref: null };
    }
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("device", this._draft);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  private async _delete(): Promise<void> {
    if (!this.ctx || !this._draft?.id) return;
    this._busy = true;
    try {
      const result = await this.ctx.remove("device", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  private _mqttDraft(): MqttConfig {
    return this._mqtt ?? { ...this.ctx!.config!.settings.mqtt };
  }

  private async _saveMqtt(): Promise<void> {
    if (!this.ctx || !this._mqtt) return;
    this._busy = true;
    try {
      const settings: Partial<SettingsConfig> = {
        ...this.ctx.config!.settings,
        mqtt: this._mqtt,
      };
      const result = await this.ctx.saveSettings(settings);
      this._problems = result.problems;
      if (result.success) this._mqtt = undefined;
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const devices = ctx.config.devices ?? [];
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "devices.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${t(s, "devices.add")}
          </button>
        </div>
        ${devices.length
          ? html`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${t(s, "field.name")}</th>
                    <th>${t(s, "field.kind")}</th>
                    <th>${t(s, "devices.reaches")}</th>
                    <th>${t(s, "devices.identifies")}</th>
                    <th>${t(s, "field.enabled")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${devices.map((device) => this._row(s, device))}
                </tbody>
              </table>
            </div>`
          : html`<div class="empty">${t(s, "devices.none")}</div>`}
        <div class="card-bd">
          <p class="note">${t(s, "devices.white_list")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
      ${this._renderMqtt(s)}
    `;
  }

  private _row(s: Strings, device: DeviceConfig) {
    const ctx = this.ctx!;
    const owner = (ctx.config?.users ?? []).find((u) => u.id === device.user_id);
    return html`<tr
      class="clickable"
      aria-selected=${this._draft?.id === device.id ? "true" : "false"}
      @click=${() => this._edit(device)}
    >
      <td><strong>${device.name}</strong></td>
      <td>${t(s, `device_kind.${device.kind}`)}</td>
      <td class="mono">${device.kind === "keypad" ? device.ref : device.entity_id}</td>
      <td>
        ${device.kind === "tag"
          ? html`<span class="pill ok">${owner?.name ?? "—"}</span>`
          : html`<span class="pill idle">${t(s, "devices.code_is_identity")}</span>`}
      </td>
      <td>${t(s, device.enabled ? "common.yes" : "common.no")}</td>
    </tr>`;
  }

  private _renderEditor(s: Strings, draft: DeviceConfig) {
    const ctx = this.ctx!;
    const users = ctx.config?.users ?? [];
    const scenarios = ctx.config?.scenarios ?? [];
    const entities = Object.keys(ctx.hass.states)
      .filter((id) => TOKEN_DOMAINS.some((domain) => id.startsWith(domain)))
      .sort();
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "devices.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.name")}</span>
              <input
                .value=${draft.name}
                @input=${(e: Event) =>
                  this._set("name", (e.target as HTMLInputElement).value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.kind")}</span>
              <select
                @change=${(e: Event) =>
                  this._setKind(
                    (e.target as HTMLSelectElement).value as DeviceConfig["kind"],
                  )}
              >
                ${(["keypad", "tag"] as const).map(
                  (kind) => html`<option .value=${kind} ?selected=${kind === draft.kind}>
                    ${t(s, `device_kind.${kind}`)}
                  </option>`,
                )}
              </select>
              <span class="hint">${t(s, `devices.kind_hint_${draft.kind}`)}</span>
            </label>
          </div>

          ${draft.kind === "keypad"
            ? html`<div class="grid-form">
                <label class="field">
                  <span class="lbl">${t(s, "field.ref")}</span>
                  <input
                    .value=${draft.ref ?? ""}
                    placeholder="keypad_hall"
                    @input=${(e: Event) =>
                      this._set("ref", (e.target as HTMLInputElement).value)}
                  />
                  <span class="hint">${t(s, "devices.ref_hint")}</span>
                </label>
              </div>`
            : html`
                <div class="banner warn">
                  <strong>${t(s, "devices.stolen_tag")}</strong>
                  <span>${t(s, "devices.stolen_tag_hint")}</span>
                </div>
                <div class="grid-form">
                  <label class="field">
                    <span class="lbl">${t(s, "field.entity_id")}</span>
                    <select
                      @change=${(e: Event) =>
                        this._set(
                          "entity_id",
                          (e.target as HTMLSelectElement).value || null,
                        )}
                    >
                      <option value="" ?selected=${!draft.entity_id}>—</option>
                      ${entities.map(
                        (id) => html`<option .value=${id} ?selected=${id === draft.entity_id}>
                          ${id}
                        </option>`,
                      )}
                    </select>
                    <span class="hint">${t(s, "devices.entity_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${t(s, "field.event_type")}</span>
                    <input
                      .value=${draft.event_type ?? ""}
                      @input=${(e: Event) =>
                        this._set(
                          "event_type",
                          (e.target as HTMLInputElement).value || null,
                        )}
                    />
                    <span class="hint">${t(s, "devices.event_type_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${t(s, "field.user_id")}</span>
                    <select
                      @change=${(e: Event) =>
                        this._set("user_id", (e.target as HTMLSelectElement).value || null)}
                    >
                      <option value="" ?selected=${!draft.user_id}>—</option>
                      ${users.map(
                        (u) => html`<option .value=${u.id ?? ""} ?selected=${u.id === draft.user_id}>
                          ${u.name}
                        </option>`,
                      )}
                    </select>
                    <span class="hint">${t(s, "devices.owner_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${t(s, "field.command")}</span>
                    <select
                      @change=${(e: Event) =>
                        this._set(
                          "command",
                          (e.target as HTMLSelectElement).value as DeviceConfig["command"],
                        )}
                    >
                      ${(["toggle", "arm", "disarm"] as const).map(
                        (command) => html`<option
                          .value=${command}
                          ?selected=${command === draft.command}
                        >
                          ${t(s, `key_command.${command}`)}
                        </option>`,
                      )}
                    </select>
                  </label>
                  ${draft.command === "disarm"
                    ? nothing
                    : html`<label class="field">
                        <span class="lbl">${t(s, "field.scenario_id")}</span>
                        <select
                          @change=${(e: Event) =>
                            this._set(
                              "scenario_id",
                              (e.target as HTMLSelectElement).value || null,
                            )}
                        >
                          <option value="" ?selected=${!draft.scenario_id}>—</option>
                          ${scenarios.map(
                            (sc) => html`<option
                              .value=${sc.id ?? ""}
                              ?selected=${sc.id === draft.scenario_id}
                            >
                              ${sc.name}
                            </option>`,
                          )}
                        </select>
                      </label>`}
                </div>
              `}

          <div class="hr"></div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${draft.enabled}
              @change=${(e: Event) =>
                this._set("enabled", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "field.enabled")}
              <span class="hint">${t(s, "devices.enabled_hint")}</span>
            </span>
          </label>

          ${this._problems.length
            ? html`<ul class="problems">
                ${this._problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
              </ul>`
            : nothing}
        </div>
        <div class="card-ft">
          <button class="btn" @click=${() => (this._draft = undefined)}>
            ${t(s, "common.cancel")}
          </button>
          ${draft.id
            ? html`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                ${t(s, "common.delete")}
              </button>`
            : nothing}
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${t(s, "common.save")}
          </button>
        </div>
      </div>
    `;
  }

  private _renderMqtt(s: Strings) {
    const mqtt = this._mqttDraft();
    const set = <K extends keyof MqttConfig>(key: K, value: MqttConfig[K]) => {
      this._mqtt = { ...mqtt, [key]: value };
    };
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "devices.mqtt")}</h2>
        </div>
        <div class="card-bd">
          <p class="note">${t(s, "devices.mqtt_note")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${mqtt.enabled}
              @change=${(e: Event) =>
                set("enabled", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "devices.mqtt_enabled")}
              <span class="hint">${t(s, "devices.mqtt_enabled_hint")}</span>
            </span>
          </label>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.command_topic")}</span>
              <input
                .value=${mqtt.command_topic}
                placeholder=${t(s, "devices.topic_command_example")}
                @input=${(e: Event) =>
                  set("command_topic", (e.target as HTMLInputElement).value)}
              />
              <span class="hint">${t(s, "devices.topic_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.state_topic")}</span>
              <input
                .value=${mqtt.state_topic}
                placeholder=${t(s, "devices.topic_state_example")}
                @input=${(e: Event) =>
                  set("state_topic", (e.target as HTMLInputElement).value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.detail")}</span>
              <select
                @change=${(e: Event) =>
                  set("detail", (e.target as HTMLSelectElement).value as MqttConfig["detail"])}
              >
                ${(["minimal", "standard", "full"] as const).map(
                  (level) => html`<option .value=${level} ?selected=${level === mqtt.detail}>
                    ${t(s, `mqtt_detail.${level}`)}
                  </option>`,
                )}
              </select>
              <span class="hint">${t(s, `devices.detail_hint_${mqtt.detail}`)}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.qos")}</span>
              <select
                @change=${(e: Event) =>
                  set("qos", Number((e.target as HTMLSelectElement).value))}
              >
                ${[0, 1, 2].map(
                  (level) => html`<option .value=${String(level)} ?selected=${level === mqtt.qos}>
                    ${level}
                  </option>`,
                )}
              </select>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${mqtt.retain}
              @change=${(e: Event) => set("retain", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "field.retain")}
              <span class="hint">${t(s, "devices.retain_hint")}</span>
            </span>
          </label>
          <div class="hr"></div>
          <div class="grid-form">
            <div class="field">
              <span class="lbl">${t(s, "devices.inbound")}</span>
              <pre class="sample">${INBOUND}</pre>
            </div>
            <div class="field">
              <span class="lbl">${t(s, "devices.outbound")}</span>
              <pre class="sample">${OUTBOUND[mqtt.detail]}</pre>
              <span class="hint">${t(s, "devices.last_result_hint")}</span>
            </div>
          </div>
        </div>
        <div class="card-ft">
          <button
            class="btn primary"
            ?disabled=${this._busy || !this._mqtt}
            @click=${this._saveMqtt}
          >
            ${t(s, "common.save")}
          </button>
        </div>
      </div>
    `;
  }

  static override styles = [
    formStyles,
    stateStyles,
    css`
      .sample {
        margin: 0;
        padding: 10px 12px;
        border-radius: 8px;
        background: var(--secondary-background-color);
        font-family: var(--code-font-family, monospace);
        font-size: 12px;
        line-height: 1.5;
        overflow-x: auto;
        white-space: pre;
      }
      .mono {
        font-family: var(--code-font-family, monospace);
        font-size: 12px;
      }
      /* The one sentence on this page that has to stop somebody: §9.3 says a
         stolen tag arms and disarms without knowing any code, and it is read
         while deciding whether to carry one. Plain text would not stop
         anybody. */
      .banner {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 8px;
        background: var(--warning-color, #f0a835);
        color: #0d1014;
      }
    `,
  ];
}

const INBOUND = `{
  "action": "arm",
  "scenario": "Night",
  "code": "123456",
  "device_id": "keypad_hall"
}`;

const OUTBOUND: Record<MqttConfig["detail"], string> = {
  minimal: `{
  "master": "armed_night",
  "countdown": { "kind": "exit", "remaining": 22 },
  "ready_to_arm": false,
  "blocking_zones": 1,
  "fault": false,
  "last_result": "ok"
}`,
  standard: `{
  "master": "armed_night",
  "countdown": null,
  "ready_to_arm": true,
  "blocking_zones": 0,
  "fault": false,
  "last_result": "ok",
  "scenario": "Night",
  "areas": { "Ground floor": "armed" }
}`,
  full: `{
  "master": "armed_night",
  "countdown": null,
  "ready_to_arm": false,
  "blocking_zones": 1,
  "fault": false,
  "last_result": "blocked",
  "scenario": "Night",
  "areas": { "Ground floor": "armed" },
  "open_zones": ["Bathroom window"]
}`,
};

customElements.define("foyer-page-devices", FoyerPageDevices);
