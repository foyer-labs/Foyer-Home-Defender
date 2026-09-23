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
//
// And, since §9.2.1, a third: a token authenticates a keypad and encrypts
// nothing. A keypad whose requests arrive in the clear carries a warning here
// for as long as that is true, because its token and the codes typed on it
// can be read on the network.
//
// And, since §9.2.2, a fourth: a device on the endpoint — a display, a relay,
// a module — is allowed exactly what its scopes say, every one off until it
// is ticked here. Reading can be free; acting never is (decision 116).
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  DeviceConfig,
  DeviceScope,
  MqttConfig,
  Problem,
  SettingsConfig,
} from "../../shared/types";
import {
  problemText,
  type PanelContext,
  activateOnKey,
  revealEditor,
  revealProblems,
  whenNumber,
} from "../context";
import "../delete-button";

// What a new device, or one read from a backend older than scopes, starts
// with (decision 115): nothing at all, and `status` free should it be ticked.
function apiDefaults(): Pick<
  DeviceConfig,
  | "scopes"
  | "free_scopes"
  | "arm_scenario_ids"
  | "arm_area_ids"
  | "disarm_area_ids"
  | "unlock_seconds"
  | "clear_text_confirmed"
> {
  return {
    scopes: [],
    free_scopes: ["status"],
    arm_scenario_ids: null,
    arm_area_ids: null,
    disarm_area_ids: null,
    unlock_seconds: 120,
    clear_text_confirmed: false,
  };
}

const READ_SCOPES: DeviceScope[] = ["status", "zones", "batteries", "health", "log"];
const ACT_SCOPES: DeviceScope[] = ["arm", "disarm", "exclude", "acknowledge"];
const MIN_UNLOCK = 30;
const MAX_UNLOCK = 600;

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
  transport: "mqtt",
  ...apiDefaults(),
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
    _mqttProblems: { state: true },
    _token: { state: true },
    _tokenProblems: { state: true },
    _confirmToken: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: DeviceConfig;
  private _problems: Problem[] = [];
  private _busy = false;
  private _mqtt?: MqttConfig;
  private _mqttProblems: Problem[] = [];
  // A token just generated, shown once and then forgotten: leaving the
  // editor, or opening another keypad, loses it for good (§9.2.1).
  private _token?: { deviceId: string; value: string };
  private _tokenProblems: Problem[] = [];
  private _confirmToken?: "replace" | "revoke";

  private _edit(device?: DeviceConfig): void {
    // Not while a save or a delete is on its way: its answer would land in
    // this editor, closing it or showing the other item's problems here.
    if (this._busy) return;
    this._draft = device
      ? { ...apiDefaults(), ...structuredClone(device) }
      : structuredClone(EMPTY);
    this._problems = [];
    this._token = undefined;
    this._tokenProblems = [];
    this._confirmToken = undefined;
    void revealEditor(this);
  }

  private async _tokenAction(revoke: boolean): Promise<void> {
    const id = this._draft?.id;
    this._confirmToken = undefined;
    if (!this.ctx || !id) return;
    this._busy = true;
    try {
      const result = await this.ctx.deviceToken(id, revoke);
      // The answer can arrive after somebody has opened another keypad: it
      // belongs to the one it was asked for, and to no other editor.
      if (this._draft?.id !== id) return;
      this._tokenProblems = result.problems;
      this._token =
        result.success && result.token ? { deviceId: id, value: result.token } : undefined;
      if (result.success) {
        this._draft = { ...this._draft, has_token: !revoke };
      }
    } finally {
      this._busy = false;
    }
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
      // A tag never speaks on the endpoint (decision 99): the connection
      // select is not even shown for one, so it must not carry a hidden
      // `http` the backend would refuse.
      this._draft = { ...this._draft!, kind, ref: null, transport: "mqtt", scopes: [] };
    }
  }

  private _setTransport(transport: DeviceConfig["transport"]): void {
    // Scopes live on the endpoint alone (decision 115): on the broker the
    // device is a name anybody can give, and the backend refuses a scope
    // there. Back on the endpoint they are chosen again, deliberately.
    this._draft = {
      ...this._draft!,
      transport,
      ...(transport === "mqtt" ? { scopes: [], clear_text_confirmed: false } : {}),
    };
  }

  private _toggle(key: "scopes" | "free_scopes", scope: DeviceScope, on: boolean): void {
    const draft = this._draft!;
    const list = draft[key].filter((item) => item !== scope);
    if (on) list.push(scope);
    const next = { ...draft, [key]: list };
    // The confirmation of decision 119 is about the scopes ticked now. With
    // none beyond `status` left it is dropped, so ticking one again asks for
    // it again rather than finding it already given.
    if (!next.scopes.some((item) => item !== "status")) next.clear_text_confirmed = false;
    this._draft = next;
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("device", this._draft);
      this._problems = result.problems;
      if (!result.success) void revealProblems(this);
      if (result.success) {
        this._draft = undefined;
        // The token was shown for the editor it was generated in, and that
        // editor is closed: it goes from memory too.
        this._token = undefined;
      }
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
      this._mqttProblems = result.problems;
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
 tabindex="0"
 @keydown=${activateOnKey}
      aria-selected=${this._draft?.id === device.id ? "true" : "false"}
      @click=${() => this._edit(device)}
    >
      <td><strong>${device.name}</strong></td>
      <td>${t(s, `device_kind.${device.kind}`)}</td>
      <td class="mono">
        ${device.kind === "keypad" ? device.ref : device.entity_id}
        ${device.kind === "keypad"
          ? html`<span class="pill idle">${t(s, `transport.${device.transport}`)}</span>`
          : nothing}
        ${this._inClear(device)
          ? html`<span class="pill warn">${t(s, "devices.in_clear_pill")}</span>`
          : nothing}
      </td>
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
    const entities = this._tagEntities(ctx.hass.states);
    return html`
      <div class="card editor">
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
                  (kind) => html`<option .value=${kind} .selected=${live(kind === draft.kind)}>
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
                    <span class="hint"
                      >${t(
                        s,
                        draft.transport === "http"
                          ? "devices.ref_hint_http"
                          : "devices.ref_hint",
                      )}</span
                    >
                  </label>
                  <label class="field">
                    <span class="lbl">${t(s, "field.transport")}</span>
                    <select
                      @change=${(e: Event) =>
                        this._setTransport(
                          (e.target as HTMLSelectElement).value as DeviceConfig["transport"],
                        )}
                    >
                      ${(["mqtt", "http"] as const).map(
                        (transport) => html`<option
                          .value=${transport}
                          .selected=${live(transport === draft.transport)}
                        >
                          ${t(s, `transport.${transport}`)}
                        </option>`,
                      )}
                    </select>
                    <span class="hint">${t(s, `devices.transport_hint_${draft.transport}`)}</span>
                    ${draft.transport === "mqtt" &&
                    this.ctx?.config?.devices.find((d) => d.id === draft.id)?.has_token
                      ? html`<span class="hint warn-text">${t(s, "devices.token_dropped")}</span>`
                      : nothing}
                  </label>
                </div>
                ${draft.transport === "http"
                  ? html`${this._renderToken(s, draft)} ${this._renderScopes(s, draft)}`
                  : nothing}`
            : html`
                ${this.ctx?.config?.devices.find((d) => d.id === draft.id)?.has_token
                  ? html`<p class="hint warn-text">${t(s, "devices.token_dropped")}</p>`
                  : nothing}
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
                      <option value="" .selected=${live(!draft.entity_id)}>—</option>
                      ${entities.map(
                        (id) => html`<option .value=${id} .selected=${live(id === draft.entity_id)}>
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
                      <option value="" .selected=${live(!draft.user_id)}>—</option>
                      ${users.map(
                        (u) => html`<option .value=${u.id ?? ""} .selected=${live(u.id === draft.user_id)}>
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
                          .selected=${live(command === draft.command)}
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
                          <option value="" .selected=${live(!draft.scenario_id)}>—</option>
                          ${scenarios.map(
                            (sc) => html`<option
                              .value=${sc.id ?? ""}
                              .selected=${live(sc.id === draft.scenario_id)}
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
              .checked=${live(draft.enabled)}
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
          <button
            class="btn"
            @click=${() => {
              this._draft = undefined;
              this._token = undefined;
            }}
          >
            ${t(s, "common.cancel")}
          </button>
          ${draft.id
            ? html`<foyer-delete-button
                .strings=${s}
                .name=${draft.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>`
            : nothing}
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${t(s, "common.save")}
          </button>
        </div>
      </div>
    `;
  }

  // Worked out when Home Assistant's states change, not on every render:
  // the page re-renders every second while any countdown runs, and this
  // sorted every entity in the house each time (second review).
  private _tagCache?: { states: object; ids: string[] };

  private _tagEntities(states: Record<string, unknown>): string[] {
    if (this._tagCache?.states !== states) {
      this._tagCache = {
        states,
        ids: Object.keys(states)
          .filter((id) => TOKEN_DOMAINS.some((domain) => id.startsWith(domain)))
          .sort(),
      };
    }
    return this._tagCache.ids;
  }

  private _inClear(device: DeviceConfig): boolean {
    return (
      device.kind === "keypad" &&
      device.transport === "http" &&
      !!device.id &&
      (this.ctx?.status.devices_in_clear ?? []).includes(device.id)
    );
  }

  // The endpoint keypad's token (§9.2.1): what it is for, the one moment it
  // can be read, and — for as long as it is true — that it is being sent in
  // the clear.
  private _renderToken(s: Strings, draft: DeviceConfig) {
    const stored = this.ctx?.config?.devices.find((d) => d.id === draft.id);
    // A token belongs to a keypad saved on the endpoint: generating one for a
    // keypad the backend still holds on the broker would be refused.
    const ready = !!stored && stored.transport === "http";
    const shown = this._token && this._token.deviceId === draft.id ? this._token : undefined;
    return html`<div class="token">
      ${this._inClear(draft)
        ? html`<div class="banner warn" role="alert">
            <strong>${t(s, "devices.in_clear")}</strong>
            <span>${t(s, "devices.in_clear_hint")}</span>
          </div>`
        : nothing}
      <p class="note">${t(s, "devices.token_note")}</p>
      ${shown
        ? html`<div class="once" role="status">
            <span class="lbl">${t(s, "devices.token_once")}</span>
            <code class="mono secret">${shown.value}</code>
            <span class="hint">${t(s, "devices.token_once_hint")}</span>
          </div>`
        : html`<p class="hint">
            ${!ready
              ? t(s, "devices.token_save_first")
              : draft.has_token
                ? t(s, "devices.token_exists")
                : t(s, "devices.token_none")}
          </p>`}
      ${ready
        ? html`<div class="actions">
            ${this._confirmToken
              ? html`<span class="hint">${t(s, "devices.token_confirm")}</span>
                  <button
                    class="btn danger"
                    ?disabled=${this._busy}
                    @click=${() => this._tokenAction(this._confirmToken === "revoke")}
                  >
                    ${t(s, this._confirmToken === "revoke"
                      ? "devices.token_revoke"
                      : "devices.token_replace")}
                  </button>
                  <button class="btn" @click=${() => (this._confirmToken = undefined)}>
                    ${t(s, "common.cancel")}
                  </button>`
              : html`<button
                    class="btn"
                    ?disabled=${this._busy}
                    @click=${() =>
                      // A keypad that has a token stops working the moment
                      // it is replaced or revoked: asked first (second
                      // review). The first token has nothing to break.
                      draft.has_token
                        ? (this._confirmToken = "replace")
                        : this._tokenAction(false)}
                  >
                    ${t(s, draft.has_token ? "devices.token_replace" : "devices.token_generate")}
                  </button>
                  ${draft.has_token
                    ? html`<button
                        class="btn danger"
                        ?disabled=${this._busy}
                        @click=${() => (this._confirmToken = "revoke")}
                      >
                        ${t(s, "devices.token_revoke")}
                      </button>`
                    : nothing}`}
          </div>`
        : nothing}
      ${this._tokenProblems.length
        ? html`<ul class="problems">
            ${this._tokenProblems.map((p) => html`<li>${problemText(s, p)}</li>`)}
          </ul>`
        : nothing}
      <div class="endpoint-samples">
        <div class="field">
          <span class="lbl">${t(s, "devices.endpoint_request")}</span>
          <pre class="sample">${ENDPOINT_REQUEST}</pre>
        </div>
        <div class="field">
          <span class="lbl">${t(s, "devices.endpoint_stream")}</span>
          <pre class="sample">${ENDPOINT_STREAM}</pre>
          <span class="hint">${t(s, "devices.endpoint_stream_hint")}</span>
        </div>
      </div>
    </div>`;
  }

  // What an API device may read and do (§9.2.2). Written for whoever is
  // deciding what the display in the hall should show a passer-by, so every
  // line says what it gives away rather than what it is called.
  private _renderScopes(s: Strings, draft: DeviceConfig) {
    const config = this.ctx?.config;
    const granted = (scope: DeviceScope) => draft.scopes.includes(scope);
    const beyondStatus = draft.scopes.some((scope) => scope !== "status");
    // The unlock matters only while something is read after a code.
    const afterCode = READ_SCOPES.some(
      (scope) => granted(scope) && !draft.free_scopes.includes(scope),
    );
    const areas = (config?.areas ?? []).map((a) => ({ id: a.id ?? "", name: a.name }));
    const scenarios = (config?.scenarios ?? []).map((sc) => ({ id: sc.id ?? "", name: sc.name }));
    return html`<fieldset class="scopes">
      <legend>${t(s, "field.scopes")}</legend>
      <p class="note">${t(s, "devices.scopes_note")}</p>
      ${draft.scopes.length
        ? nothing
        : html`<p class="hint warn-text">${t(s, "devices.scopes_none")}</p>`}

      <h3>${t(s, "devices.scopes_read")}</h3>
      <p class="hint">${t(s, "devices.scopes_read_hint")}</p>
      ${READ_SCOPES.map(
        (scope) => html`<div class="scope-row">
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(granted(scope))}
              @change=${(e: Event) =>
                this._toggle("scopes", scope, (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, `devices.scope.${scope}`)}
              <span class="hint">${t(s, `devices.scope_hint.${scope}`)}</span>
            </span>
          </label>
          <label class="check free">
            <input
              type="checkbox"
              ?disabled=${!granted(scope)}
              .checked=${live(draft.free_scopes.includes(scope))}
              @change=${(e: Event) =>
                this._toggle("free_scopes", scope, (e.target as HTMLInputElement).checked)}
            />
            <span>${t(s, "field.free_scopes")}</span>
          </label>
        </div>`,
      )}
      ${granted("log") && draft.free_scopes.includes("log")
        ? html`<p class="hint">${t(s, "devices.free_log_hint")}</p>`
        : nothing}
      ${afterCode
        ? html`<label class="field unlock">
            <span class="lbl">${t(s, "field.unlock_seconds")}</span>
            <input
              type="number"
              min=${MIN_UNLOCK}
              max=${MAX_UNLOCK}
              step="1"
              .value=${String(draft.unlock_seconds)}
              @change=${(e: Event) => whenNumber(e, (n) => this._set("unlock_seconds", n))}
            />
            <span class="hint">${t(s, "devices.unlock_hint")}</span>
          </label>`
        : nothing}

      <h3>${t(s, "devices.scopes_act")}</h3>
      <p class="hint">${t(s, "devices.scopes_act_hint")}</p>
      ${ACT_SCOPES.map(
        (scope) => html`<label class="check">
            <input
              type="checkbox"
              .checked=${live(granted(scope))}
              @change=${(e: Event) =>
                this._toggle("scopes", scope, (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, `devices.scope.${scope}`)}
              <span class="hint">${t(s, `devices.scope_hint.${scope}`)}</span>
            </span>
          </label>
          ${scope === "arm" && granted("arm")
            ? html`<div class="reach">
                ${this._reach(s, "arm_scenario_ids", "devices.reach_all_scenarios", scenarios, draft)}
                ${this._reach(s, "arm_area_ids", "devices.reach_whole_house", areas, draft)}
              </div>`
            : nothing}
          ${scope === "disarm" && granted("disarm")
            ? html`<div class="reach">
                ${this._reach(s, "disarm_area_ids", "devices.reach_whole_house", areas, draft)}
              </div>`
            : nothing}`,
      )}

      ${beyondStatus
        ? html`<div class="clear-text">
            <label class="check">
              <input
                type="checkbox"
                .checked=${live(draft.clear_text_confirmed)}
                @change=${(e: Event) =>
                  this._set("clear_text_confirmed", (e.target as HTMLInputElement).checked)}
              />
              <span>
                ${t(s, "field.clear_text_confirmed")}
                ${this._inClear(draft)
                  ? html`<span class="pill warn">${t(s, "devices.in_clear_pill")}</span>`
                  : nothing}
                <span class="hint">${t(s, "devices.clear_text_hint")}</span>
                ${this._inClear(draft)
                  ? html`<span class="hint warn-text">${t(s, "devices.clear_text_now")}</span>`
                  : nothing}
              </span>
            </label>
          </div>`
        : nothing}
    </fieldset>`;
  }

  // Where an arm or a disarm through the device may reach. Null is
  // everywhere its code's owner may go — which stays the other limit either
  // way (§8.3); a list, even an empty one, is exactly what is ticked.
  private _reach(
    s: Strings,
    field: "arm_scenario_ids" | "arm_area_ids" | "disarm_area_ids",
    everywhere: string,
    known: { id: string; name: string }[],
    draft: DeviceConfig,
  ) {
    const chosen = draft[field];
    // An area or a scenario deleted since is still listed, ticked, so that
    // it can be unticked: the backend refuses the save while it is there.
    const options = [
      ...known,
      ...(chosen ?? [])
        .filter((id) => !known.some((item) => item.id === id))
        .map((id) => ({ id, name: id })),
    ];
    return html`<div class="field">
      <span class="lbl">${t(s, `field.${field}`)}</span>
      <label class="check">
        <input
          type="radio"
          name=${field}
          .checked=${live(chosen === null)}
          @change=${() => this._set(field, null)}
        />
        <span>${t(s, everywhere)}</span>
      </label>
      <label class="check">
        <input
          type="radio"
          name=${field}
          .checked=${live(chosen !== null)}
          @change=${() => this._set(field, chosen ?? [])}
        />
        <span>${t(s, "devices.reach_only")}</span>
      </label>
      ${chosen !== null
        ? html`<div class="choices">
              ${options.map(
                (item) => html`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${live(chosen.includes(item.id))}
                    @change=${(e: Event) =>
                      this._set(
                        field,
                        (e.target as HTMLInputElement).checked
                          ? [...chosen, item.id]
                          : chosen.filter((id) => id !== item.id),
                      )}
                  />
                  <span>${item.name}</span>
                </label>`,
              )}
            </div>
            ${chosen.length
              ? nothing
              : html`<span class="hint warn-text">${t(s, "devices.reach_none")}</span>`}`
        : nothing}
    </div>`;
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
              .checked=${live(mqtt.enabled)}
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
                  (level) => html`<option .value=${level} .selected=${live(level === mqtt.detail)}>
                    ${t(s, `mqtt_detail.${level}`)}
                  </option>`,
                )}
              </select>
              <span class="hint">${t(s, `devices.detail_hint_${mqtt.detail}`)}</span>
              <span class="hint">${t(s, "devices.detail_shared_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.qos")}</span>
              <select
                @change=${(e: Event) =>
                  set("qos", Number((e.target as HTMLSelectElement).value))}
              >
                ${[0, 1, 2].map(
                  (level) => html`<option .value=${String(level)} .selected=${live(level === mqtt.qos)}>
                    ${level}
                  </option>`,
                )}
              </select>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(mqtt.retain)}
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
          ${this._mqttProblems.length
            ? html`<ul class="problems">
                ${this._mqttProblems.map((p) => html`<li>${problemText(s, p)}</li>`)}
              </ul>`
            : nothing}
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
      .token {
        margin-top: 12px;
      }
      .warn-text {
        color: var(--warning-color, #c77700);
      }
      .endpoint-samples {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 16px;
      }
      .endpoint-samples .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
      }
      .endpoint-samples .lbl {
        font-weight: 500;
      }
      .once {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 8px;
        border: 1px solid var(--primary-color);
        background: var(--secondary-background-color);
      }
      .once .lbl {
        font-weight: 500;
      }
      .secret {
        overflow-wrap: anywhere;
        user-select: all;
        font-size: 13px;
      }
      .scopes h3 {
        font-size: 14px;
        font-weight: 500;
        margin: 16px 0 2px;
      }
      /* A read scope and its "without a code" beside it, on one line while
         there is room: the pair is one decision about one piece of the house. */
      .scope-row {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start;
        gap: 0 24px;
      }
      .scope-row > label.check:first-child {
        flex: 1 1 280px;
      }
      .scope-row .free {
        flex: 0 0 auto;
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      .reach {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 8px 16px;
        margin: 0 0 8px 28px;
      }
      .reach .field {
        display: flex;
        flex-direction: column;
        font-size: 13px;
      }
      .reach .lbl {
        font-weight: 500;
      }
      .reach label.check {
        padding: 2px 0;
        font-size: 13px;
      }
      .choices {
        margin-left: 28px;
      }
      input[type="radio"] {
        width: 18px;
        height: 18px;
        padding: 0;
      }
      /* Beside a long hint a box would otherwise shrink to a dot. */
      .scopes input[type="checkbox"],
      .scopes input[type="radio"] {
        flex: none;
      }
      .unlock {
        max-width: 320px;
        margin: 8px 0 0;
      }
      .clear-text {
        margin-top: 16px;
        padding-top: 8px;
        border-top: 1px solid var(--divider-color);
      }
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

// The two routes of §9.2.1, as a keypad's firmware would use them. The
// token is a placeholder: the real one is shown once, above, and nowhere else.
const ENDPOINT_REQUEST = `POST /api/foyer/device
Authorization: Bearer <token>

{ "action": "arm", "scenario": "Night", "code": "123456" }`;

const ENDPOINT_STREAM = `GET /api/foyer/device/state
Authorization: Bearer <token>

data: {"master": "arming", "countdown": {"kind": "exit", "remaining": 30}, …}

: keepalive`;

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
