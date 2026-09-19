// Page 5 — Response profiles (SPEC §6, §15.1). A profile is a named list of
// actions: what happens, when, and under which conditions. The area is the
// unit of response; a zone's own profile is read only for its own alarm,
// which is what makes a verification group's graduated response work (§4.8).
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  ActionConfig,
  ActionKind,
  Condition,
  ProfileConfig,
  Problem,
} from "../../shared/types";
import { optionalNumber, problemText, type PanelContext } from "../context";
import {
  domainServices,
  entityTargets,
  notifyTargets,
  serviceDomains,
  type Target,
} from "../ha-targets";

// The three groups of SPEC §6.1, plus the moments this phase added for the
// log and the simulator's trace.
const MOMENT_GROUPS: Record<string, string[]> = {
  alarm: [
    "entry_started",
    "triggered",
    "siren_cutoff",
    "incident_opened",
    "incident_joined",
    "incident_acknowledged",
    "incident_closed",
    "verification_pending",
    "verification_satisfied",
    "verification_expired",
    "technical_raised",
    "technical_acknowledged",
    "technical_cleared",
  ],
  state: [
    "armed",
    "disarmed",
    "arm_failed",
    "forced_arm",
    "zone_bypassed",
    "zone_rejoined",
    "code_rejected",
    "lockout",
    "chime_switched",
  ],
  system: [
    "zone_fault",
    "low_battery",
    "ha_restarted",
    "walk_test_started",
    "walk_test_ended",
    "escalation_exhausted",
    "chime",
  ],
};

// How a notification carries the camera picture. The transport is named
// because there is no shared key: the Companion app reads `image`, Telegram
// reads `photo`, and neither complains about the other's.
const ATTACHMENTS = ["companion", "telegram"];

const MULTI_ENTITY: ActionKind[] = ["siren", "light", "switch"];
const SINGLE_ENTITY: ActionKind[] = ["camera", "scene", "tts"];

function blankAction(kind: ActionKind): ActionConfig {
  const params: Record<string, unknown> = {};
  if (kind === "switch") params.state = "on";
  if (kind === "camera") params.mode = "snapshot";
  if (kind === "delay") params.seconds = 30;
  if (kind === "notify" || kind === "tts") params.message = "{{ zone }}";
  // Stated, not assumed: each transport reads its own key for an attached
  // picture and ignores the others in silence.
  if (kind === "notify") params.attachment = "companion";
  return {
    kind,
    moments: [],
    name: "",
    params,
    conditions: [],
    condition_mode: "all",
    enabled: true,
  };
}

class FoyerPageProfiles extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _open: { state: true },
    _filters: { state: true },
    _problems: { state: true },
    _busy: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: ProfileConfig;
  private _open = -1; // which action is expanded
  // One search box per entity picker, so a house with sixty switches is
  // usable: keyed by "<action index>:<parameter>".
  private _filters: Record<string, string> = {};
  private _problems: Problem[] = [];
  private _busy = false;

  private _edit(profile?: ProfileConfig): void {
    this._draft = profile ? structuredClone(profile) : { name: "", severity: 1, actions: [] };
    this._open = -1;
    this._problems = [];
  }

  private _set<K extends keyof ProfileConfig>(key: K, value: ProfileConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private _setAction(index: number, changes: Partial<ActionConfig>): void {
    if (!this._draft) return;
    const actions = this._draft.actions.map((a, i) => (i === index ? { ...a, ...changes } : a));
    this._draft = { ...this._draft, actions };
  }

  private _setParam(index: number, key: string, value: unknown): void {
    const action = this._draft?.actions[index];
    if (!action) return;
    const params = { ...action.params };
    if (value === null || value === "") delete params[key];
    else params[key] = value;
    this._setAction(index, { params });
  }

  private _addAction(kind: ActionKind): void {
    if (!this._draft) return;
    this._draft = {
      ...this._draft,
      actions: [...this._draft.actions, blankAction(kind)],
    };
    this._open = this._draft.actions.length - 1;
  }

  private _removeAction(index: number): void {
    if (!this._draft) return;
    const actions = this._draft.actions.filter((_, i) => i !== index);
    this._draft = { ...this._draft, actions };
    this._open = -1;
  }

  private _moveAction(index: number, by: number): void {
    if (!this._draft) return;
    const actions = [...this._draft.actions];
    const target = index + by;
    if (target < 0 || target >= actions.length) return;
    [actions[index], actions[target]] = [actions[target], actions[index]];
    this._draft = { ...this._draft, actions };
    this._open = target;
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("profile", this._draft);
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
      const result = await this.ctx.remove("profile", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  // --- rendering ------------------------------------------------------------------

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const profiles = ctx.config.profiles ?? [];
    return html`
      <p class="page-intro">${t(s, "profiles.intro")}</p>
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "profiles.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${t(s, "profiles.add")}</button>
        </div>
        ${
          profiles.length
            ? html`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${t(s, "field.name")}</th>
                      <th>${t(s, "field.actions")}</th>
                      <th>${t(s, "field.severity")}</th>
                      <th>${t(s, "profiles.used_by")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${profiles.map(
                      (profile) =>
                        html`<tr
                          class="clickable"
                          aria-selected=${this._draft?.id === profile.id ? "true" : "false"}
                          @click=${() => this._edit(profile)}
                        >
                          <td><strong>${profile.name}</strong></td>
                          <td>
                            ${
                              profile.actions.length
                                ? profile.actions.map(
                                    (a) =>
                                      html`<span class="tag"
                                        >${t(s, `action_kind.${a.kind}`)}</span
                                      > `,
                                  )
                                : html`<span class="muted">${t(s, "profiles.no_actions")}</span>`
                            }
                          </td>
                          <td>${profile.severity}</td>
                          <td class="muted">${this._usedBy(s, profile)}</td>
                        </tr>`,
                    )}
                  </tbody>
                </table>
              </div>`
            : html`<div class="empty">${t(s, "profiles.none")}</div>`
        }
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
    `;
  }

  /** Where this profile is pointed at, so deleting it is never a surprise. */
  private _usedBy(s: Strings, profile: ProfileConfig): string {
    const config = this.ctx!.config!;
    const used: string[] = [];
    if (config.settings.default_profile_id === profile.id) {
      used.push(t(s, "profiles.used_default"));
    }
    if (config.settings.technical_profile_id === profile.id) {
      used.push(t(s, "profiles.used_technical"));
    }
    for (const list of [config.areas, config.zones, config.scenarios, config.groups]) {
      for (const item of list) {
        if (item.response_profile_id === profile.id) used.push(item.name);
      }
    }
    return used.length ? used.join(", ") : t(s, "profiles.unused");
  }

  private _renderEditor(s: Strings, draft: ProfileConfig) {
    const bounds = this.ctx?.meta?.bounds.severity ?? [1, 10];
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "profiles.new")}</h2>
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
              <span class="lbl">${t(s, "field.severity")}</span>
              <input
                type="number"
                min=${bounds[0]}
                max=${bounds[1]}
                .value=${String(draft.severity)}
                @input=${(e: Event) =>
                  this._set("severity", optionalNumber((e.target as HTMLInputElement).value) ?? 1)}
              />
              <span class="hint">${t(s, "profiles.severity_hint")}</span>
            </label>
          </div>

          <div class="actions-list">
            ${draft.actions.map((action, index) => this._renderAction(s, action, index))}
          </div>
          ${draft.actions.length ? nothing : html`<p class="hint">${t(s, "profiles.no_actions")}</p>`}

          <div class="add-action">
            <label class="field">
              <span class="lbl">${t(s, "profiles.add_action")}</span>
              <select
                .value=${""}
                @change=${(e: Event) => {
                  const select = e.target as HTMLSelectElement;
                  if (select.value) this._addAction(select.value as ActionKind);
                  select.value = "";
                }}
              >
                <option value=""></option>
                ${(this.ctx?.meta?.action_kinds ?? []).map(
                  (kind) => html`<option .value=${kind}>${t(s, `action_kind.${kind}`)}</option>`,
                )}
              </select>
            </label>
          </div>
          <p class="hint">${t(s, "profiles.escalation_later")}</p>

          ${
            this._problems.length
              ? html`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
                  </ul>
                </div>`
              : nothing
          }
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${t(s, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => (this._draft = undefined)}>
              ${t(s, "common.cancel")}
            </button>
            ${
              draft.id
                ? html`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                    ${t(s, "common.delete")}
                  </button>`
                : nothing
            }
          </div>
        </div>
      </div>
    `;
  }

  private _renderAction(s: Strings, action: ActionConfig, index: number) {
    const open = this._open === index;
    return html`
      <div class="action" ?data-open=${open}>
        <button class="action-hd" @click=${() => (this._open = open ? -1 : index)}>
          <span class="tag">${t(s, `action_kind.${action.kind}`)}</span>
          <span class="summary">${this._summary(s, action)}</span>
          <span class="moments">${this._momentSummary(s, action)}</span>
          ${
            action.conditions.length
              ? html`<span class="cond">${action.conditions.length}</span>`
              : nothing
          }
        </button>
        ${
          open
            ? html`<div class="action-bd">
                ${this._renderParams(s, action, index)} ${this._renderMoments(s, action, index)}
                ${this._renderConditions(s, action, index)}
                <div class="actions">
                  <button class="btn" @click=${() => this._moveAction(index, -1)}>&uarr;</button>
                  <button class="btn" @click=${() => this._moveAction(index, 1)}>&darr;</button>
                  <button class="btn danger" @click=${() => this._removeAction(index)}>
                    ${t(s, "profiles.delete_action")}
                  </button>
                </div>
              </div>`
            : nothing
        }
      </div>
    `;
  }

  /** The moments, short enough to read at a glance: a profile action that
   * answers a dozen of them must not push the row to three lines. */
  private _momentSummary(s: Strings, action: ActionConfig): string {
    const names = action.moments.map((m) => t(s, `moment.${m}`));
    if (!names.length) return t(s, "profiles.no_moments");
    if (names.length <= 3) return names.join(", ");
    return t(s, "profiles.moments_more", {
      moments: names.slice(0, 2).join(", "),
      count: names.length - 2,
    });
  }

  /** One line saying what the action actually does, for the collapsed row. */
  private _summary(s: Strings, action: ActionConfig): string {
    const params = action.params as Record<string, string | number | string[]>;
    if (action.kind === "delay") return `${params.seconds ?? 0} s`;
    if (action.kind === "call_service") return `${params.domain ?? ""}.${params.service ?? ""}`;
    if (action.kind === "notify") return String(params.service ?? "");
    if (action.kind === "persistent_notification") {
      return String(params.message ?? t(s, "profiles.inherit"));
    }
    const entities = params.entity_ids ?? params.entity_id ?? "";
    return Array.isArray(entities) ? entities.join(", ") : String(entities);
  }

  // --- parameters, one shape per kind (§6.2) --------------------------------------

  private _entities(domains: string[]): Target[] {
    return entityTargets(this.ctx!.hass, domains);
  }

  /** A text field with suggestions: the list is what Home Assistant has, but
   * a value can still be typed, because an integration that is not loaded
   * right now would otherwise be impossible to configure. */
  private _suggested(
    s: Strings,
    action: ActionConfig,
    index: number,
    key: string,
    options: Target[],
    hint?: string,
  ) {
    const listId = `foyer-${key}-${index}`;
    return html`<label class="field">
      <span class="lbl">${t(s, `field.${key}`)}</span>
      <input
        list=${listId}
        .value=${String(action.params[key] ?? "")}
        @input=${(e: Event) => this._setParam(index, key, (e.target as HTMLInputElement).value)}
      />
      <datalist id=${listId}>
        ${options.map(
          (option) => html`<option .value=${option.id}>
            ${option.name === option.id ? option.id : `${option.name} · ${option.id}`}
          </option>`,
        )}
      </datalist>
      <span class="hint">${hint ?? t(s, "profiles.pick_or_type")}</span>
    </label>`;
  }

  private _text(s: Strings, action: ActionConfig, index: number, key: string, hint?: string) {
    return html`<label class="field">
      <span class="lbl">${t(s, `field.${key}`)}</span>
      <input
        .value=${String(action.params[key] ?? "")}
        @input=${(e: Event) => this._setParam(index, key, (e.target as HTMLInputElement).value)}
      />
      ${hint ? html`<span class="hint">${hint}</span>` : nothing}
    </label>`;
  }

  private _number(s: Strings, action: ActionConfig, index: number, key: string, hint?: string) {
    return html`<label class="field">
      <span class="lbl">${t(s, `field.${key}`)}</span>
      <input
        type="number"
        .value=${action.params[key] == null ? "" : String(action.params[key])}
        @input=${(e: Event) =>
          this._setParam(index, key, optionalNumber((e.target as HTMLInputElement).value))}
      />
      ${hint ? html`<span class="hint">${hint}</span>` : nothing}
    </label>`;
  }

  private _picker(
    s: Strings,
    action: ActionConfig,
    index: number,
    key: string,
    domains: string[],
    multiple: boolean,
  ) {
    const options = this._entities(domains);
    const current = action.params[key];
    const selected = new Set(
      Array.isArray(current) ? (current as string[]) : current ? [String(current)] : [],
    );
    for (const id of selected) {
      if (!options.some((o) => o.id === id)) options.push({ id, name: id });
    }
    if (!multiple) {
      return html`<label class="field">
        <span class="lbl">${t(s, `field.${key}`)}</span>
        <select
          @change=${(e: Event) =>
            this._setParam(index, key, (e.target as HTMLSelectElement).value || null)}
        >
          <option value=""></option>
          ${options.map(
            (o) => html`<option .value=${o.id} ?selected=${selected.has(o.id)}>${o.name}</option>`,
          )}
        </select>
      </label>`;
    }
    const filterKey = `${index}:${key}`;
    // Every word must appear somewhere in the name or the id, in any order:
    // "alexa cucina" finds "Alexa Cucina Ripetere" the way a person expects.
    const words = (this._filters[filterKey] ?? "").toLowerCase().split(/\s+/).filter(Boolean);
    // What is chosen always stays visible, however the list is filtered:
    // otherwise a search hides a target that is still going to sound.
    const shown = options.filter((o) => {
      if (selected.has(o.id)) return true;
      const haystack = `${o.name} ${o.id}`.toLowerCase();
      return words.every((word) => haystack.includes(word));
    });
    return html`<fieldset class="entities wide">
      <legend>${t(s, `field.${key}`)}</legend>
      ${options.length > 8
        ? html`<input
            class="filter"
            type="search"
            .value=${this._filters[filterKey] ?? ""}
            placeholder=${t(s, "profiles.filter")}
            @input=${(e: Event) => {
              this._filters = {
                ...this._filters,
                [filterKey]: (e.target as HTMLInputElement).value,
              };
            }}
          />`
        : nothing}
      <div class="entity-list">
        ${shown.map(
          (o) => html`<label class="check">
            <input
              type="checkbox"
              .checked=${selected.has(o.id)}
              @change=${(e: Event) => {
                const on = (e.target as HTMLInputElement).checked;
                const next = new Set(selected);
                if (on) next.add(o.id);
                else next.delete(o.id);
                this._setParam(index, key, [...next]);
              }}
            />
            <span>${t(s, "zones.entity", { name: o.name, entity: o.id })}</span>
          </label>`,
        )}
        ${shown.length ? nothing : html`<p class="hint">${t(s, "profiles.no_match")}</p>`}
      </div>
    </fieldset>`;
  }

  private _renderParams(s: Strings, action: ActionConfig, index: number) {
    const domains = this.ctx?.meta?.action_domains[action.kind] ?? [];
    const variables = (this.ctx?.meta?.template_variables ?? []).map((v) => `{{ ${v} }}`).join(" ");
    const messageHint = t(s, "profiles.message_hint", { variables });
    const parts = [];
    if (MULTI_ENTITY.includes(action.kind)) {
      parts.push(this._picker(s, action, index, "entity_ids", domains, true));
    }
    if (SINGLE_ENTITY.includes(action.kind)) {
      parts.push(this._picker(s, action, index, "entity_id", domains, false));
    }
    switch (action.kind) {
      case "notify":
        parts.push(
          this._suggested(
            s,
            action,
            index,
            "service",
            notifyTargets(this.ctx!.hass),
            t(s, "profiles.notify_hint"),
          ),
        );
        parts.push(this._text(s, action, index, "title"));
        parts.push(this._text(s, action, index, "message", messageHint));
        parts.push(
          this._picker(s, action, index, "camera_entity_id", ["camera"], false),
        );
        // Only once there is a picture to attach: an empty choice above an
        // empty camera field is two questions where the user asked none.
        if (action.params.camera_entity_id) {
          parts.push(
            this._select(s, action, index, "attachment", ATTACHMENTS, (v) =>
              t(s, `attachment.${v}`),
            ),
          );
          parts.push(
            html`<span class="hint"
              >${t(
                s,
                action.params.attachment === "telegram"
                  ? "profiles.attach_hint_telegram"
                  : "profiles.attach_hint",
              )}</span
            >`,
          );
        }
        break;
      case "persistent_notification":
        parts.push(this._text(s, action, index, "title"));
        parts.push(this._text(s, action, index, "message", messageHint));
        break;
      case "siren":
        parts.push(
          this._number(s, action, index, "duration", t(s, "profiles.siren_duration_hint")),
        );
        parts.push(this._renderTone(s, action, index));
        break;
      case "light":
        parts.push(this._number(s, action, index, "brightness"));
        parts.push(this._select(s, action, index, "flash", ["", "short", "long"], (v) => v || "—"));
        break;
      case "camera":
        parts.push(
          this._select(s, action, index, "mode", ["snapshot", "record"], (v) =>
            t(s, `camera_mode.${v}`),
          ),
        );
        parts.push(this._number(s, action, index, "duration", t(s, "profiles.camera_hint")));
        break;
      case "switch":
        parts.push(
          this._select(s, action, index, "state", ["on", "off"], (v) => t(s, `on_off.${v}`)),
        );
        parts.push(this._number(s, action, index, "revert_after", t(s, "profiles.revert_hint")));
        break;
      case "tts":
        parts.push(
          this._picker(s, action, index, "media_player_entity_ids", ["media_player"], true),
        );
        parts.push(this._text(s, action, index, "message", messageHint));
        break;
      case "call_service": {
        const domain = String(action.params.domain ?? "");
        parts.push(
          this._suggested(
            s,
            action,
            index,
            "domain",
            serviceDomains(this.ctx!.hass).map((d) => ({ id: d, name: d })),
          ),
        );
        parts.push(
          this._suggested(
            s,
            action,
            index,
            "service",
            domainServices(this.ctx!.hass, domain).map((name) => ({
              id: name,
              name,
            })),
          ),
        );
        parts.push(this._json(s, action, index));
        break;
      }
      case "delay":
        parts.push(this._number(s, action, index, "seconds", t(s, "profiles.delay_hint")));
        break;
      default:
        break;
    }
    return html`<div class="grid-form">${parts}</div>`;
  }

  /** The tones the chosen sirens declare, and nothing else.
   *
   * Home Assistant publishes them as `available_tones` on the entity; a siren
   * that has none simply has no tone to pick, so the field disappears instead
   * of inviting a guess that would fail at the one moment it matters.
   */
  private _renderTone(s: Strings, action: ActionConfig, index: number) {
    const chosen = action.params.entity_ids;
    const ids = Array.isArray(chosen) ? (chosen as string[]) : [];
    const tones = new Set<string>();
    for (const id of ids) {
      const available = this.ctx!.hass.states[id]?.attributes?.available_tones;
      if (Array.isArray(available)) available.forEach((tone) => tones.add(String(tone)));
      else if (available && typeof available === "object") {
        Object.keys(available).forEach((tone) => tones.add(tone));
      }
    }
    if (!tones.size) {
      return ids.length
        ? html`<label class="field">
            <span class="lbl">${t(s, "field.tone")}</span>
            <input disabled placeholder=${t(s, "profiles.no_tones")} />
            <span class="hint">${t(s, "profiles.no_tones")}</span>
          </label>`
        : nothing;
    }
    return this._select(
      s,
      action,
      index,
      "tone",
      ["", ...[...tones].sort()],
      (v) => v || t(s, "profiles.default_tone"),
    );
  }

  private _select(
    s: Strings,
    action: ActionConfig,
    index: number,
    key: string,
    options: string[],
    label: (value: string) => string,
  ) {
    return html`<label class="field">
      <span class="lbl">${t(s, `field.${key}`)}</span>
      <select
        @change=${(e: Event) =>
          this._setParam(index, key, (e.target as HTMLSelectElement).value || null)}
      >
        ${options.map(
          (option) =>
            html`<option .value=${option} ?selected=${action.params[key] === option}>
              ${label(option)}
            </option>`,
        )}
      </select>
    </label>`;
  }

  private _json(s: Strings, action: ActionConfig, index: number) {
    return html`<label class="field wide">
      <span class="lbl">${t(s, "field.data")}</span>
      <textarea
        rows="4"
        .value=${JSON.stringify(action.params.data ?? {}, null, 2)}
        @change=${(e: Event) => {
          const text = (e.target as HTMLTextAreaElement).value.trim();
          try {
            this._setParam(index, "data", text ? JSON.parse(text) : null);
          } catch {
            this._setParam(index, "data", text);
          }
        }}
      ></textarea>
      <span class="hint">${t(s, "profiles.call_service_hint")}</span>
    </label>`;
  }

  // --- moments (§6.1) --------------------------------------------------------------

  private _renderMoments(s: Strings, action: ActionConfig, index: number) {
    const future = new Set(this.ctx?.meta?.future_moments ?? []);
    const known = new Set(this.ctx?.meta?.moments ?? []);
    return html`<div class="moments-grid">
      ${Object.entries(MOMENT_GROUPS).map(
        ([group, moments]) =>
          html`<fieldset>
            <legend>${t(s, `moment_group.${group}`)}</legend>
            ${moments
              .filter((moment) => known.has(moment))
              .map(
                (moment) =>
                  html`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${action.moments.includes(moment)}
                      @change=${(e: Event) => {
                        const on = (e.target as HTMLInputElement).checked;
                        const next = on
                          ? [...action.moments, moment]
                          : action.moments.filter((m) => m !== moment);
                        this._setAction(index, { moments: next });
                      }}
                    />
                    <span>
                      ${t(s, `moment.${moment}`)}
                      ${
                        future.has(moment)
                          ? html`<span class="later">${t(s, "profiles.future_moment")}</span>`
                          : nothing
                      }
                    </span>
                  </label>`,
              )}
          </fieldset>`,
      )}
    </div>`;
  }

  // --- conditions (§6.3): at most two, and or or --------------------------------

  private _renderConditions(s: Strings, action: ActionConfig, index: number) {
    const max = this.ctx?.meta?.max_conditions ?? 2;
    const setConditions = (conditions: Condition[]) => this._setAction(index, { conditions });
    return html`<fieldset class="conditions">
      <legend>${t(s, "field.conditions")}</legend>
      ${
        action.conditions.length
          ? action.conditions.map((condition, i) =>
              this._renderCondition(s, action, index, condition, i),
            )
          : html`<p class="hint">${t(s, "condition.none")}</p>`
      }
      ${
        action.conditions.length < max
          ? html`<div class="actions">
              <button
                class="btn sm"
                @click=${() =>
                  setConditions([
                    ...action.conditions,
                    { kind: "time", after: "22:00", before: "07:00" },
                  ])}
              >
                ${t(s, "condition.time")}
              </button>
              <button
                class="btn sm"
                @click=${() =>
                  setConditions([
                    ...action.conditions,
                    {
                      kind: "state",
                      entity_id: "",
                      operator: "is",
                      state: "on",
                    },
                  ])}
              >
                ${t(s, "condition.state")}
              </button>
            </div>`
          : nothing
      }
      ${
        action.conditions.length === 2
          ? html`<label class="field">
              <span class="lbl">${t(s, "field.condition_mode")}</span>
              <select
                @change=${(e: Event) =>
                  this._setAction(index, {
                    condition_mode: (e.target as HTMLSelectElement).value as "all" | "any",
                  })}
              >
                ${(["all", "any"] as const).map(
                  (mode) =>
                    html`<option .value=${mode} ?selected=${action.condition_mode === mode}>
                      ${t(s, `condition.${mode}`)}
                    </option>`,
                )}
              </select>
            </label>`
          : nothing
      }
      <p class="hint">${t(s, "condition.max")}</p>
    </fieldset>`;
  }

  private _renderCondition(
    s: Strings,
    action: ActionConfig,
    index: number,
    condition: Condition,
    at: number,
  ) {
    const update = (changes: Partial<Condition>) =>
      this._setAction(index, {
        conditions: action.conditions.map((c, i) =>
          i === at ? ({ ...c, ...changes } as Condition) : c,
        ),
      });
    const remove = () =>
      this._setAction(index, {
        conditions: action.conditions.filter((_, i) => i !== at),
      });
    return html`<div class="condition">
      ${
        condition.kind === "time"
          ? html`<label class="field">
                <span class="lbl">${t(s, "condition.after")}</span>
                <input
                  type="time"
                  .value=${condition.after}
                  @input=${(e: Event) => update({ after: (e.target as HTMLInputElement).value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${t(s, "condition.before")}</span>
                <input
                  type="time"
                  .value=${condition.before}
                  @input=${(e: Event) => update({ before: (e.target as HTMLInputElement).value })}
                />
                <span class="hint">${t(s, "condition.midnight_hint")}</span>
              </label>`
          : html`<label class="field">
                <span class="lbl">${t(s, "field.entity_id")}</span>
                <input
                  .value=${condition.entity_id}
                  @input=${(e: Event) => update({ entity_id: (e.target as HTMLInputElement).value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${t(s, "field.state")}</span>
                <select
                  @change=${(e: Event) =>
                    update({
                      operator: (e.target as HTMLSelectElement).value as "is" | "is_not",
                    })}
                >
                  ${(["is", "is_not"] as const).map(
                    (op) =>
                      html`<option .value=${op} ?selected=${condition.operator === op}>
                        ${t(s, `condition.${op}`)}
                      </option>`,
                  )}
                </select>
              </label>
              <label class="field">
                <span class="lbl">${t(s, "condition.state")}</span>
                <input
                  .value=${condition.state}
                  @input=${(e: Event) => update({ state: (e.target as HTMLInputElement).value })}
                />
              </label>`
      }
      <button class="btn sm danger" @click=${remove}>${t(s, "common.delete")}</button>
    </div>`;
  }

  static override styles = [
    formStyles,
    stateStyles,
    css`
      .page-intro {
        margin: 0 4px 12px;
        color: var(--secondary-text-color);
        font-size: 13.5px;
        max-width: 78ch;
      }
      .actions-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 16px;
      }
      .action {
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        overflow: hidden;
      }
      .action-hd {
        width: 100%;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: none;
        border: 0;
        color: inherit;
        font: inherit;
        text-align: left;
        cursor: pointer;
        flex-wrap: wrap;
      }
      .action[data-open] .action-hd {
        border-bottom: 1px solid var(--divider-color);
      }
      .summary {
        font-family: var(--code-font-family, monospace);
        font-size: 12.5px;
        color: var(--secondary-text-color);
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .moments {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .cond {
        font-size: 12px;
        border-radius: 999px;
        padding: 1px 7px;
        background: var(--warning-color, #f0a835);
        color: #0d1014;
      }
      .action-bd {
        padding: 12px;
      }
      .moments-grid {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        margin-top: 12px;
      }
      .entities.wide {
        grid-column: 1 / -1;
      }
      .entity-list {
        max-height: 200px;
        overflow: auto;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 2px 16px;
        margin-top: 6px;
      }
      .filter {
        width: min(100%, 320px);
      }
      .condition {
        display: flex;
        gap: 12px;
        align-items: flex-end;
        flex-wrap: wrap;
        padding: 8px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      .later {
        font-size: 11px;
        color: var(--secondary-text-color);
        display: block;
      }
      .add-action {
        margin-top: 12px;
        max-width: 320px;
      }
      textarea {
        font-family: var(--code-font-family, monospace);
        font-size: 12.5px;
      }
      .wide {
        grid-column: 1 / -1;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-profiles")) {
  customElements.define("foyer-page-profiles", FoyerPageProfiles);
}
