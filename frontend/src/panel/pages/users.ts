// Page 7 — Users and codes (SPEC §8, §15.1). Everyone has their own code,
// because a shared one makes "who disarmed at 03:14?" unanswerable and turns
// the log into decoration.
//
// No hash ever arrives here: the backend says whether a person holds a code,
// and this page sends a new one. A code typed here is transmitted and checked
// in the backend, which is the whole of INV-2 — a check in this file would be
// decoration, since anyone with Home Assistant access can call the service.
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  CodePolicyConfig,
  Problem,
  SecurityConfig,
  UserConfig,
} from "../../shared/types";
import {
  problemText,
  type PanelContext,
  whenNumber,
  activateOnKey,
  revealEditor,
  revealProblems,
} from "../context";
import "../delete-button";

interface Draft extends UserConfig {
  /** Typed here, sent once, never read back. */
  new_code?: string | null;
  new_duress_code?: string | null;
  /** The new code typed a second time. Compared with the first here and
   * never sent: whether the code itself is acceptable is the backend's to
   * say (INV-2); whether the two fields agree is only about the typing. */
  repeat_code?: string;
}

const EMPTY: Draft = {
  name: "",
  has_code: false,
  has_duress_code: false,
  ha_user_id: null,
  permissions: ["arm", "disarm", "bypass_zone", "change_scenario", "view_log"],
  allowed_area_ids: null,
  allowed_scenario_ids: null,
  valid_from: null,
  valid_until: null,
  code_exempt_when_identified: false,
  enabled: true,
};

/** An ISO instant as the value of a `datetime-local` input, and back. */
function toLocal(iso: string | null): string {
  if (!iso) return "";
  const at = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${at.getFullYear()}-${pad(at.getMonth() + 1)}-${pad(at.getDate())}T${pad(
    at.getHours(),
  )}:${pad(at.getMinutes())}`;
}

function fromLocal(value: string): string | null {
  if (!value) return null;
  const at = new Date(value);
  return Number.isNaN(at.getTime()) ? null : at.toISOString();
}

class FoyerPageUsers extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _problems: { state: true },
    _policyProblems: { state: true },
    _busy: { state: true },
    _policy: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: Draft;
  private _problems: Problem[] = [];
  private _policyProblems: Problem[] = [];
  private _busy = false;
  private _policy?: { code_policy: CodePolicyConfig; security: SecurityConfig };

  private _edit(user?: UserConfig): void {
    // Not while a save or a delete is on its way: its answer would land in
    // this editor, closing it or showing the other item's problems here.
    if (this._busy) return;
    this._draft = user ? { ...structuredClone(user) } : structuredClone(EMPTY);
    this._problems = [];
    void revealEditor(this);
  }

  private _set<K extends keyof Draft>(key: K, value: Draft[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private _togglePermission(permission: string, on: boolean): void {
    const current = new Set(this._draft?.permissions ?? []);
    if (on) current.add(permission);
    else current.delete(permission);
    this._set("permissions", [...current].sort());
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const { new_code, new_duress_code, repeat_code, ...user } = this._draft;
      if (new_code && new_code !== (repeat_code ?? "")) {
        this._problems = [{ code: "code_mismatch", kind: "user", ref: null, field: null }];
        void revealProblems(this);
        return;
      }
      const result = await this.ctx.saveUser(user, {
        ...(new_code !== undefined ? { new_code } : {}),
        ...(new_duress_code !== undefined ? { new_duress_code } : {}),
      });
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
      const result = await this.ctx.remove("user", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  private _policyDraft(): { code_policy: CodePolicyConfig; security: SecurityConfig } {
    const config = this.ctx!.config!;
    return (
      this._policy ?? {
        code_policy: { ...config.code_policy },
        security: { ...config.settings.security },
      }
    );
  }

  private async _savePolicy(): Promise<void> {
    if (!this.ctx || !this._policy) return;
    this._busy = true;
    try {
      const result = await this.ctx.saveSecurity(
        this._policy.code_policy,
        this._policy.security,
      );
      // Shown in the policy card, where the save was made: under a person
      // being edited, or nowhere at all when nobody was, a refused policy
      // looked like a save that did nothing (second review).
      this._policyProblems = result.problems;
      if (result.success) this._policy = undefined;
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const users = ctx.config.users ?? [];
    return html`
      ${ctx.status.security.enforced
        ? nothing
        : html`<div class="banner warn">
            <strong>${t(s, "users.not_enforced")}</strong>
            <span>${t(s, "users.not_enforced_hint")}</span>
          </div>`}
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "users.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${t(s, "users.add")}
          </button>
        </div>
        ${users.length
          ? html`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${t(s, "field.name")}</th>
                    <th>${t(s, "users.code")}</th>
                    <th>${t(s, "field.permissions")}</th>
                    <th>${t(s, "users.scope")}</th>
                    <th>${t(s, "field.valid_until")}</th>
                    <th>${t(s, "users.duress")}</th>
                    <th>${t(s, "field.ha_user_id")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${users.map((user) => this._row(s, user))}
                </tbody>
              </table>
            </div>`
          : html`<div class="empty">${t(s, "users.none")}</div>`}
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
      ${this._renderPolicy(s)}
    `;
  }

  private _row(s: Strings, user: UserConfig) {
    const ctx = this.ctx!;
    const areas = new Map((ctx.config?.areas ?? []).map((a) => [a.id, a.name]));
    const scope =
      user.allowed_area_ids === null
        ? t(s, "users.every_area")
        : user.allowed_area_ids.map((id) => areas.get(id) ?? id).join(", ");
    return html`<tr
      class="clickable"
 tabindex="0"
 @keydown=${activateOnKey}
      aria-selected=${this._draft?.id === user.id ? "true" : "false"}
      @click=${() => this._edit(user)}
    >
      <td>
        <strong>${user.name}</strong>
        ${user.enabled ? nothing : html`<span class="tag">${t(s, "users.disabled")}</span>`}
      </td>
      <td>
        ${user.has_code
          ? html`<span class="pill ok">${t(s, "users.code_set")}</span>`
          : html`<span class="pill warn">${t(s, "users.code_missing")}</span>`}
      </td>
      <td>${user.permissions.map((p) => html`<span class="tag">${t(s, `permission.${p}`)}</span>`)}</td>
      <td>${scope}</td>
      <td>${user.valid_until ? new Date(user.valid_until).toLocaleString(ctx.hass.language) : "—"}</td>
      <td>${t(s, user.has_duress_code ? "common.yes" : "common.no")}</td>
      <td>${user.ha_user_id ? t(s, "users.linked") : "—"}</td>
    </tr>`;
  }

  private _renderEditor(s: Strings, draft: Draft) {
    const ctx = this.ctx!;
    const length = ctx.status.security.code_length;
    const permissions = ctx.meta?.permissions ?? [];
    const haUsers = ctx.hass.user?.is_admin ? (ctx.haUsers ?? []) : [];
    return html`
      <div class="card editor">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "users.new")}</h2>
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
              <span class="lbl">${t(s, "users.code")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${length}
                placeholder=${draft.has_code ? t(s, "users.code_unchanged") : t(s, "users.code_digits", { n: length })}
                .value=${live(draft.new_code ?? "")}
                @input=${(e: Event) =>
                  this._set("new_code", (e.target as HTMLInputElement).value)}
              />
              <span class="hint">
                ${t(s, draft.id ? "users.code_hint" : "users.code_hint_new", { n: length })}
              </span>
            </label>
            ${draft.new_code
              ? html`<label class="field">
                  <span class="lbl">${t(s, "users.code_repeat")}</span>
                  <input
                    type="password"
                    inputmode="numeric"
                    autocomplete="off"
                    maxlength=${length}
                    .value=${live(draft.repeat_code ?? "")}
                    @input=${(e: Event) =>
                      this._set("repeat_code", (e.target as HTMLInputElement).value)}
                  />
                </label>`
              : nothing}
            <label class="field">
              <span class="lbl">${t(s, "users.duress")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${length}
                placeholder=${draft.has_duress_code
                  ? t(s, "users.code_unchanged")
                  : t(s, "users.code_optional")}
                .value=${live(draft.new_duress_code ?? "")}
                @input=${(e: Event) =>
                  this._set("new_duress_code", (e.target as HTMLInputElement).value)}
              />
              <span class="hint">${t(s, "users.duress_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.ha_user_id")}</span>
              <select
                @change=${(e: Event) =>
                  this._set("ha_user_id", (e.target as HTMLSelectElement).value || null)}
              >
                <option value="" .selected=${live(!draft.ha_user_id)}>${t(s, "users.not_linked")}</option>
                ${haUsers.map(
                  (u) => html`<option .value=${u.id} .selected=${live(u.id === draft.ha_user_id)}>
                    ${u.name}
                  </option>`,
                )}
              </select>
              <span class="hint">${t(s, "users.linked_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.valid_from")}</span>
              <input
                type="datetime-local"
                .value=${toLocal(draft.valid_from)}
                @input=${(e: Event) =>
                  this._set("valid_from", fromLocal((e.target as HTMLInputElement).value))}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.valid_until")}</span>
              <input
                type="datetime-local"
                .value=${toLocal(draft.valid_until)}
                @input=${(e: Event) =>
                  this._set("valid_until", fromLocal((e.target as HTMLInputElement).value))}
              />
              <span class="hint">${t(s, "users.validity_hint")}</span>
            </label>
          </div>

          <div class="hr"></div>
          <div class="lbl">${t(s, "field.permissions")}</div>
          <div class="chips">
            ${permissions.map(
              (permission) => html`<label class="chip">
                <input
                  type="checkbox"
                  .checked=${live(draft.permissions.includes(permission))}
                  @change=${(e: Event) =>
                    this._togglePermission(
                      permission,
                      (e.target as HTMLInputElement).checked,
                    )}
                />
                <span>${t(s, `permission.${permission}`)}</span>
              </label>`,
            )}
          </div>

          <div class="hr"></div>
          <div class="scopes">
            ${this._scope(
              s,
              "allowed_area_ids",
              (ctx.config?.areas ?? []).map((a) => ({ id: a.id ?? "", name: a.name })),
              draft,
            )}
            ${this._scope(
              s,
              "allowed_scenario_ids",
              (ctx.config?.scenarios ?? []).map((sc) => ({
                id: sc.id ?? "",
                name: sc.name,
              })),
              draft,
            )}
          </div>

          <div class="hr"></div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(draft.code_exempt_when_identified)}
              @change=${(e: Event) =>
                this._set(
                  "code_exempt_when_identified",
                  (e.target as HTMLInputElement).checked,
                )}
            />
            <span>
              ${t(s, "users.exempt")}
              <span class="hint">${t(s, "users.exempt_hint")}</span>
            </span>
          </label>
          <p class="note">${t(s, "users.exempt_note")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(draft.enabled)}
              @change=${(e: Event) =>
                this._set("enabled", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "users.enabled")}
              <span class="hint">${t(s, "users.enabled_hint")}</span>
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
            ? html`<foyer-delete-button
                .strings=${s}
                .name=${draft.name}
                .message=${"users.confirm_delete"}
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

  private _scope(
    s: Strings,
    key: "allowed_area_ids" | "allowed_scenario_ids",
    options: { id: string; name: string }[],
    draft: Draft,
  ) {
    const current = draft[key];
    const toggle = (id: string, on: boolean) => {
      const chosen = new Set(current ?? options.map((o) => o.id));
      if (on) chosen.add(id);
      else chosen.delete(id);
      this._set(key, [...chosen]);
    };
    return html`<div class="scope">
      <span class="lbl">${t(s, `field.${key}`)}</span>
      <label class="chip">
        <input
          type="checkbox"
          .checked=${live(current === null)}
          @change=${(e: Event) =>
            this._set(key, (e.target as HTMLInputElement).checked ? null : [])}
        />
        <span>${t(s, "users.everything")}</span>
      </label>
      ${current === null
        ? nothing
        : html`<div class="chips">
            ${options.map(
              (option) => html`<label class="chip">
                <input
                  type="checkbox"
                  .checked=${live(current.includes(option.id))}
                  @change=${(e: Event) =>
                    toggle(option.id, (e.target as HTMLInputElement).checked)}
                />
                <span>${option.name}</span>
              </label>`,
            )}
          </div>`}
    </div>`;
  }

  private _renderPolicy(s: Strings) {
    const ctx = this.ctx!;
    const draft = this._policyDraft();
    const operations = ctx.meta?.operations ?? [];
    const future = new Set(ctx.meta?.future_operations ?? []);
    const [lowFailures, highFailures] = ctx.meta?.bounds.lockout_failures ?? [2, 20];
    const [lowSeconds, highSeconds] = ctx.meta?.bounds.lockout_seconds ?? [10, 86400];
    const [lowLength, highLength] = ctx.meta?.bounds.code_length ?? [4, 12];
    const setPolicy = (operation: string, on: boolean) =>
      (this._policy = {
        ...draft,
        code_policy: { ...draft.code_policy, [operation]: on },
      });
    const setSecurity = (key: keyof SecurityConfig, value: number) =>
      (this._policy = { ...draft, security: { ...draft.security, [key]: value } });
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "users.policy")}</h2>
        </div>
        <div class="card-bd">
          <p class="hint">${t(s, "users.policy_hint")}</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${t(s, "users.operation")}</th>
                  <th>${t(s, "users.needs_code")}</th>
                </tr>
              </thead>
              <tbody>
                ${operations.map(
                  (operation) => html`<tr>
                    <td>
                      ${t(s, `operation.${operation}`)}
                      ${future.has(operation)
                        ? html`<span class="tag">${t(s, "users.later_phase")}</span>`
                        : nothing}
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        aria-label=${t(s, `operation.${operation}`)}
                        .checked=${live(Boolean(draft.code_policy[operation]))}
                        @change=${(e: Event) =>
                          setPolicy(operation, (e.target as HTMLInputElement).checked)}
                      />
                    </td>
                  </tr>`,
                )}
              </tbody>
            </table>
          </div>

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "users.code_length")}</span>
              <input
                type="number"
                min=${lowLength}
                max=${highLength}
                .value=${String(draft.security.code_length)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => setSecurity("code_length", n))}
              />
              <span class="hint">${t(s, "users.code_length_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "users.lockout_failures")}</span>
              <input
                type="number"
                min=${lowFailures}
                max=${highFailures}
                .value=${String(draft.security.lockout_failures)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => setSecurity("lockout_failures", n))}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "users.lockout_window")}</span>
              <input
                type="number"
                min=${lowSeconds}
                max=${highSeconds}
                .value=${String(draft.security.lockout_window)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => setSecurity("lockout_window", n))}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "users.lockout_duration")}</span>
              <input
                type="number"
                min=${lowSeconds}
                max=${highSeconds}
                .value=${String(draft.security.lockout_duration)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => setSecurity("lockout_duration", n))}
              />
              <span class="hint">${t(s, "users.lockout_hint")}</span>
            </label>
          </div>
          ${this._policyProblems.length
            ? html`<ul class="problems">
                ${this._policyProblems.map((p) => html`<li>${problemText(s, p)}</li>`)}
              </ul>`
            : nothing}
        </div>
        <div class="card-ft">
          <button
            class="btn primary"
            ?disabled=${this._busy || !this._policy}
            @click=${this._savePolicy}
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
      .scopes {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
      }
      .scope {
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: flex-start;
      }
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
      }
      .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border: 1px solid var(--divider-color);
        border-radius: 999px;
        font-size: 13px;
      }
      .banner {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px 16px;
        margin-bottom: 16px;
        border-radius: 8px;
        background: var(--warning-color, #f0a835);
        color: #0d1014;
      }
      .note {
        margin-top: 12px;
        color: var(--secondary-text-color);
        font-size: 13px;
      }
    `,
  ];
}

customElements.define("foyer-page-users", FoyerPageUsers);
