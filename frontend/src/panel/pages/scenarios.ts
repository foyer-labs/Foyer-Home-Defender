// Page 4 — Scenarios (SPEC §4.6, §15.1): named presets over areas, each
// reporting one fixed Home Assistant mode on the master panel.
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type { Problem, ScenarioConfig } from "../../shared/types";
import {
  optionalNumber,
  problemText,
  type PanelContext,
  activateOnKey,
  revealEditor,
  revealProblems,
  explainInUse,
} from "../context";
import "../delete-button";
import { codeFields } from "../code-fields";
import { profileField } from "../profile-picker";

const NEW_SCENARIO: ScenarioConfig = {
  name: "",
  areas: [],
  ha_master_state: "armed_away",
  icon: null,
  exit_delay_override: null,
  siren_duration_override: null,
  response_profile_id: null,
  require_code_to_arm: null,
  require_code_to_disarm: null,
  allowed_user_ids: null,
};

class FoyerPageScenarios extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _problems: { state: true },
    _busy: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: ScenarioConfig;
  private _problems: Problem[] = [];
  private _busy = false;

  private _edit(scenario?: ScenarioConfig): void {
    // Not while a save or a delete is on its way: its answer would land in
    // this editor, closing it or showing the other item's problems here.
    if (this._busy) return;
    this._draft = scenario ? structuredClone(scenario) : { ...NEW_SCENARIO, areas: [] };
    this._problems = [];
    void revealEditor(this);
  }

  private _set<K extends keyof ScenarioConfig>(key: K, value: ScenarioConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("scenario", this._draft);
      this._problems = result.problems;
      if (!result.success) void revealProblems(this);
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  private async _delete(): Promise<void> {
    if (!this.ctx || !this._draft?.id) return;
    this._busy = true;
    try {
      const result = await this.ctx.remove("scenario", this._draft.id);
      this._problems = explainInUse(this.ctx.strings, this.ctx.config, result.problems);
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const areas = new Map(ctx.config.areas.map((a) => [a.id, a.name]));
    const modes = ctx.config.scenarios.map((sc) => sc.ha_master_state);
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "scenarios.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${t(s, "scenarios.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${t(s, "field.name")}</th>
                <th>${t(s, "field.areas")}</th>
                <th>${t(s, "field.ha_master_state")}</th>
                <th>${t(s, "field.exit_delay_override")}</th>
                <th>${t(s, "field.siren_duration_override")}</th>
              </tr>
            </thead>
            <tbody>
              ${ctx.config.scenarios.map(
                (sc) => html`<tr
                  class="clickable"
 tabindex="0"
 @keydown=${activateOnKey}
                  aria-selected=${this._draft?.id === sc.id ? "true" : "false"}
                  @click=${() => this._edit(sc)}
                >
                  <td>
                    <strong>${sc.name}</strong>
                    ${sc.id === ctx.status.active_scenario_id
                      ? html`<span class="state armed">${t(s, "scenarios.active")}</span>`
                      : nothing}
                  </td>
                  <td>
                    ${sc.areas.map((a) => html`<span class="tag">${areas.get(a) ?? a}</span>`)}
                  </td>
                  <td>
                    <span>${t(s, `ha_state.${sc.ha_master_state}`)}</span>
                    ${modes.filter((m) => m === sc.ha_master_state).length > 1
                      ? html`<div class="hint">${t(s, "scenarios.shared_mode")}</div>`
                      : nothing}
                  </td>
                  <td>
                    ${sc.exit_delay_override == null
                      ? t(s, "scenarios.area_default")
                      : t(s, "common.seconds", { n: sc.exit_delay_override })}
                  </td>
                  <td>
                    ${sc.siren_duration_override == null
                      ? t(s, "scenarios.global_default")
                      : t(s, "common.seconds", { n: sc.siren_duration_override })}
                  </td>
                </tr>`,
              )}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
    `;
  }

  private _renderEditor(s: Strings, draft: ScenarioConfig) {
    const ctx = this.ctx!;
    const meta = ctx.meta;
    const toggleArea = (id: string, on: boolean) =>
      this._set(
        "areas",
        on ? [...draft.areas, id] : draft.areas.filter((a) => a !== id),
      );
    return html`
      <div class="card editor">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "scenarios.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.name")}</span>
              <input
                .value=${draft.name}
                @input=${(e: Event) => this._set("name", (e.target as HTMLInputElement).value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.ha_master_state")}</span>
              <select
                @change=${(e: Event) =>
                  this._set("ha_master_state", (e.target as HTMLSelectElement).value)}
              >
                ${(meta?.ha_states ?? []).map(
                  (mode) =>
                    html`<option .value=${mode} .selected=${live(mode === draft.ha_master_state)}>
                      ${t(s, `ha_state.${mode}`)}
                    </option>`,
                )}
              </select>
              <span class="hint">${t(s, "scenarios.mode_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.exit_delay_override")}</span>
              <input
                type="number"
                min="0"
                max=${meta?.bounds.exit_delay?.[1] ?? 300}
                placeholder=${t(s, "scenarios.area_default")}
                .value=${draft.exit_delay_override == null ? "" : String(draft.exit_delay_override)}
                @input=${(e: Event) =>
                  this._set(
                    "exit_delay_override",
                    optionalNumber((e.target as HTMLInputElement).value),
                  )}
              />
              <span class="hint">${t(s, "scenarios.exit_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.siren_duration_override")}</span>
              <input
                type="number"
                min="1"
                max=${meta?.bounds.siren_duration?.[1] ?? 900}
                placeholder=${t(s, "scenarios.global_seconds", {
                  n: ctx.config?.settings.siren_duration ?? 180,
                })}
                .value=${draft.siren_duration_override == null
                  ? ""
                  : String(draft.siren_duration_override)}
                @input=${(e: Event) =>
                  this._set(
                    "siren_duration_override",
                    optionalNumber((e.target as HTMLInputElement).value),
                  )}
              />
              <span class="hint">${t(s, "scenarios.siren_hint")}</span>
            </label>
            ${profileField(this.ctx!, draft.response_profile_id, (value) =>
              this._set("response_profile_id", value),
            )}
            ${codeFields(
              s,
              draft,
              (key, value) => this._set(key, value),
              ctx.status.security.enforced,
            )}
          </div>
          <fieldset>
            <legend>${t(s, "field.areas")}</legend>
            ${(ctx.config?.areas ?? []).map(
              (area) => html`<label class="check">
                <input
                  type="checkbox"
                  .checked=${live(draft.areas.includes(area.id ?? ""))}
                  @change=${(e: Event) =>
                    toggleArea(area.id ?? "", (e.target as HTMLInputElement).checked)}
                />
                <span>${area.name}</span>
              </label>`,
            )}
            <p class="hint">${t(s, "scenarios.areas_hint")}</p>
          </fieldset>
          ${this._renderAllowedUsers(s, draft)}
          ${this._problems.length
            ? html`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
                </ul>
              </div>`
            : nothing}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${t(s, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => (this._draft = undefined)}>
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
          </div>
        </div>
      </div>
    `;
  }

  /** Who may use the scenario (SPEC §4.6). The model has carried the list
   * since Phase 1 and no page could set it (UX review). Changing it needs
   * manage_users as well as edit_config (decision 112): the backend
   * refuses, and the hint says so beforehand, so the refusal is not a
   * surprise. Switching from "everyone" to a list starts from every person
   * rather than from nobody — an empty list saved by accident would lock
   * the whole household out of the scenario. */
  private _renderAllowedUsers(s: Strings, draft: ScenarioConfig) {
    const users = this.ctx?.config?.users ?? [];
    const chosen = draft.allowed_user_ids;
    const toggle = (id: string, on: boolean) => {
      const next = new Set(chosen ?? []);
      if (on) next.add(id);
      else next.delete(id);
      this._set("allowed_user_ids", [...next]);
    };
    return html`
      <fieldset>
        <legend>${t(s, "field.allowed_user_ids")}</legend>
        <label class="check">
          <input
            type="checkbox"
            .checked=${live(chosen === null)}
            @change=${(e: Event) =>
              this._set(
                "allowed_user_ids",
                (e.target as HTMLInputElement).checked
                  ? null
                  : users.map((u) => u.id ?? "").filter(Boolean),
              )}
          />
          <span>${t(s, "scenarios.everyone")}</span>
        </label>
        ${chosen === null
          ? nothing
          : users.map(
              (user) => html`<label class="check">
                <input
                  type="checkbox"
                  .checked=${live(chosen.includes(user.id ?? ""))}
                  ?disabled=${chosen.length === 1 && chosen.includes(user.id ?? "")}
                  title=${chosen.length === 1 ? t(s, "scenarios.last_user") : ""}
                  @change=${(e: Event) =>
                    toggle(user.id ?? "", (e.target as HTMLInputElement).checked)}
                />
                <span>${user.name}</span>
              </label>`,
            )}
        <p class="hint">${t(s, "scenarios.allowed_users_hint")}</p>
      </fieldset>
    `;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      td .state {
        margin-left: 8px;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-scenarios")) {
  customElements.define("foyer-page-scenarios", FoyerPageScenarios);
}
