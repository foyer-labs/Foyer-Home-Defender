// Page 2 — Areas (SPEC §4.5, §15.1). The backend validates every save; this
// page only collects the fields and shows what the backend said.
import { LitElement, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type { AreaConfig, Problem } from "../../shared/types";
import { codeFields } from "../code-fields";
import {
  problemText,
  type PanelContext,
  whenNumber,
  activateOnKey,
  revealEditor,
  revealProblems,
} from "../context";
import "../delete-button";
import { effectiveHint, profileField } from "../profile-picker";
import { define } from "../../shared/define";

const NEW_AREA: AreaConfig = {
  name: "",
  ha_state_when_armed: "armed_away",
  default_entry_delay: 30,
  default_exit_delay: 30,
  response_profile_id: null,
  require_code_to_arm: null,
  require_code_to_disarm: null,
  is_perimeter: false,
};

class FoyerPageAreas extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _problems: { state: true },
    _busy: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: AreaConfig;
  private _problems: Problem[] = [];
  private _busy = false;

  private _edit(area?: AreaConfig): void {
    // Not while a save or a delete is on its way: its answer would land in
    // this editor, closing it or showing the other item's problems here.
    if (this._busy) return;
    // A new area starts from the defaults on Settings, which say they are
    // what new areas start with; the constants are only the fallback.
    const settings = this.ctx?.config?.settings;
    this._draft = area
      ? { ...area }
      : {
          ...NEW_AREA,
          default_entry_delay: settings?.default_entry_delay ?? NEW_AREA.default_entry_delay,
          default_exit_delay: settings?.default_exit_delay ?? NEW_AREA.default_exit_delay,
        };
    this._problems = [];
    void revealEditor(this);
  }

  private _set<K extends keyof AreaConfig>(key: K, value: AreaConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("area", this._draft);
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
      const result = await this.ctx.remove("area", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const live = new Map(ctx.status.areas.map((a) => [a.id, a.state]));
    const zoneCount = (id?: string) => ctx.config!.zones.filter((z) => z.area_id === id).length;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "areas.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${t(s, "areas.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${t(s, "field.name")}</th>
                <th>${t(s, "overview.status")}</th>
                <th>${t(s, "areas.zones")}</th>
                <th>${t(s, "field.default_entry_delay")}</th>
                <th>${t(s, "field.default_exit_delay")}</th>
                <th>${t(s, "field.ha_state_when_armed")}</th>
              </tr>
            </thead>
            <tbody>
              ${ctx.config.areas.map((area) => {
                const state = live.get(area.id ?? "") ?? "disarmed";
                return html`<tr
                  class="clickable"
 tabindex="0"
 @keydown=${activateOnKey}
                  aria-selected=${this._draft?.id === area.id ? "true" : "false"}
                  @click=${() => this._edit(area)}
                >
                  <td><strong>${area.name}</strong></td>
                  <td><span class="state ${state}">${t(s, `state.${state}`)}</span></td>
                  <td>${zoneCount(area.id)}</td>
                  <td>${t(s, "common.seconds", { n: area.default_entry_delay })}</td>
                  <td>${t(s, "common.seconds", { n: area.default_exit_delay })}</td>
                  <td>${t(s, `ha_state.${area.ha_state_when_armed}`)}</td>
                </tr>`;
              })}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
    `;
  }

  private _renderEditor(s: Strings, draft: AreaConfig) {
    const meta = this.ctx!.meta;
    const [minDelay, maxExit] = meta?.bounds.exit_delay ?? [0, 300];
    const maxEntry = meta?.bounds.entry_delay?.[1] ?? 300;
    return html`
      <div class="card editor">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "areas.new")}</h2>
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
              <span class="lbl">${t(s, "field.ha_state_when_armed")}</span>
              <select
                @change=${(e: Event) =>
                  this._set("ha_state_when_armed", (e.target as HTMLSelectElement).value)}
              >
                ${(meta?.ha_states ?? []).map(
                  (mode) =>
                    html`<option .value=${mode} .selected=${live(mode === draft.ha_state_when_armed)}>
                      ${t(s, `ha_state.${mode}`)}
                    </option>`,
                )}
              </select>
              <span class="hint">${t(s, "areas.reports_as_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.default_entry_delay")}</span>
              <input
                type="number"
                min=${minDelay}
                max=${maxEntry}
                .value=${String(draft.default_entry_delay)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._set("default_entry_delay", n))}
              />
              <span class="hint">${t(s, "areas.entry_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.default_exit_delay")}</span>
              <input
                type="number"
                min=${minDelay}
                max=${maxExit}
                .value=${String(draft.default_exit_delay)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._set("default_exit_delay", n))}
              />
              <span class="hint">${t(s, "areas.exit_hint")}</span>
            </label>
            ${profileField(this.ctx!, draft.response_profile_id, (value) =>
              this._set("response_profile_id", value),
            )}
            ${codeFields(
              s,
              draft,
              (key, value) => this._set(key, value),
              this.ctx!.status.security.enforced,
            )}
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(draft.is_perimeter)}
              @change=${(e: Event) =>
                this._set("is_perimeter", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "field.is_perimeter")}
              <span class="hint">${t(s, "areas.perimeter_hint")}</span>
            </span>
          </label>
          ${effectiveHint(this.ctx!, draft.id ?? null)}
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

  static override styles = [stateStyles, formStyles];
}

define("foyer-page-areas", FoyerPageAreas);
