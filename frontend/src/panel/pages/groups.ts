// Page 13 — Verification groups (SPEC §4.8, §15.1): N of M zones within a
// window. Cross-zone pairs set on a zone appear here as 2-of-2 groups, marked
// "from zone field" and edited on the zone: one engine, two ways to configure.
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type { GroupConfig, Problem, ZoneConfig } from "../../shared/types";
import { problemText, type PanelContext, whenNumber, activateOnKey } from "../context";
import { profileField } from "../profile-picker";

interface Row {
  group: GroupConfig;
  derived: boolean; // a cross-zone pair, read-only here
}

class FoyerPageGroups extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _problems: { state: true },
    _busy: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: GroupConfig;
  private _problems: Problem[] = [];
  private _busy = false;

  private _edit(group?: GroupConfig): void {
    // Not while a save or a delete is on its way: its answer would land in
    // this editor, closing it or showing the other item's problems here.
    if (this._busy) return;
    const areaId = this.ctx?.config?.areas[0]?.id ?? "";
    this._draft = group
      ? structuredClone(group)
      : {
          name: "",
          area_id: areaId,
          members: [],
          n: 2,
          window_seconds: 60,
          suppress_members: false,
          response_profile_id: null,
        };
    this._problems = [];
  }

  private _set<K extends keyof GroupConfig>(key: K, value: GroupConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("group", this._draft);
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
      const result = await this.ctx.remove("group", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  // The configured groups, then one derived 2-of-2 group per cross-zone pair,
  // counted once whichever end declares it (part 2 decision 4).
  private _rows(zones: ZoneConfig[], groups: GroupConfig[]): Row[] {
    const rows: Row[] = groups.map((group) => ({ group, derived: false }));
    const seen = new Set<string>();
    for (const zone of zones) {
      if (!zone.id || !zone.cross_zone_id) continue;
      const pair = [zone.id, zone.cross_zone_id].sort();
      const key = pair.join("+");
      if (seen.has(key)) continue;
      seen.add(key);
      rows.push({
        derived: true,
        group: {
          id: `cross:${key}`,
          name: zone.name,
          area_id: zone.area_id,
          members: pair,
          n: 2,
          window_seconds: zone.cross_zone_window,
          suppress_members: false,
          response_profile_id: null,
        },
      });
    }
    return rows;
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const areas = new Map(ctx.config.areas.map((a) => [a.id, a.name]));
    const zones = new Map(ctx.config.zones.map((z) => [z.id, z.name]));
    const rows = this._rows(ctx.config.zones, ctx.config.groups ?? []);
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "groups.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${t(s, "groups.add")}</button>
        </div>
        ${rows.length
          ? html`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${t(s, "field.name")}</th>
                    <th>${t(s, "field.area_id")}</th>
                    <th>${t(s, "field.members")}</th>
                    <th>${t(s, "field.n")}</th>
                    <th>${t(s, "field.window_seconds")}</th>
                    <th>${t(s, "groups.members_below")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map(
                    ({ group, derived }) => html`<tr
                      class=${derived ? "" : "clickable"}
 tabindex=${derived ? "-1" : "0"}
 @keydown=${activateOnKey}
                      aria-selected=${this._draft?.id === group.id ? "true" : "false"}
                      @click=${() => (derived ? undefined : this._edit(group))}
                    >
                      <td>
                        <strong>${group.name}</strong>
                        ${derived ? html`<span class="tag">${t(s, "groups.from_zone")}</span>` : nothing}
                      </td>
                      <td>${areas.get(group.area_id) ?? ""}</td>
                      <td>
                        ${group.members.map(
                          (m) => html`<span class="tag">${zones.get(m) ?? m}</span>`,
                        )}
                      </td>
                      <td>${t(s, "groups.threshold", { n: group.n, m: group.members.length })}</td>
                      <td>${t(s, "common.seconds", { n: group.window_seconds })}</td>
                      <td>
                        ${t(s, group.suppress_members ? "groups.suppressed" : "groups.not_suppressed")}
                      </td>
                    </tr>`,
                  )}
                </tbody>
              </table>
            </div>`
          : html`<div class="empty">${t(s, "groups.none")}</div>`}
        <div class="card-bd">
          <p class="hint">${t(s, "groups.from_zone_hint")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
    `;
  }

  private _renderEditor(s: Strings, draft: GroupConfig) {
    const ctx = this.ctx!;
    const [low, high] = ctx.meta?.bounds.window ?? [1, 3600];
    const areas = new Map(ctx.config?.areas.map((a) => [a.id, a.name]));
    // A zone belongs to one group or pair at most (the backend enforces it):
    // offer only intrusion zones that are free, or already in this group.
    const taken = new Set<string>();
    for (const g of ctx.config?.groups ?? []) {
      if (g.id !== draft.id) g.members.forEach((m) => taken.add(m));
    }
    for (const z of ctx.config?.zones ?? []) {
      if (z.cross_zone_id && z.id) {
        taken.add(z.id);
        taken.add(z.cross_zone_id);
      }
    }
    const candidates = (ctx.config?.zones ?? []).filter(
      (z) =>
        z.channel === "intrusion" &&
        z.id &&
        (!taken.has(z.id) || draft.members.includes(z.id)),
    );
    const toggle = (id: string, on: boolean) =>
      this._set(
        "members",
        on ? [...new Set([...draft.members, id])] : draft.members.filter((m) => m !== id),
      );
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "groups.new")}</h2>
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
              <span class="lbl">${t(s, "field.area_id")}</span>
              <select
                @change=${(e: Event) => this._set("area_id", (e.target as HTMLSelectElement).value)}
              >
                ${(ctx.config?.areas ?? []).map(
                  (a) =>
                    html`<option .value=${a.id ?? ""} .selected=${live(a.id === draft.area_id)}>
                      ${a.name}
                    </option>`,
                )}
              </select>
              <span class="hint">${t(s, "groups.area_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.n")}</span>
              <input
                type="number"
                min="2"
                max=${Math.max(2, draft.members.length)}
                .value=${String(draft.n)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._set("n", n))}
              />
              <span class="hint">
                ${t(s, "groups.threshold", { n: draft.n, m: draft.members.length })}
              </span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.window_seconds")}</span>
              <input
                type="number"
                min=${low}
                max=${high}
                .value=${String(draft.window_seconds)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._set("window_seconds", n))}
              />
              <span class="hint">${t(s, "groups.window_hint")}</span>
            </label>
            ${profileField(
              this.ctx!,
              draft.response_profile_id,
              (value) => this._set("response_profile_id", value),
              t(s, "profiles.group_hint"),
            )}
          </div>
          <fieldset>
            <legend>${t(s, "field.members")}</legend>
            ${candidates.length
              ? candidates.map(
                  (zone) => html`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${live(draft.members.includes(zone.id ?? ""))}
                      @change=${(e: Event) =>
                        toggle(zone.id ?? "", (e.target as HTMLInputElement).checked)}
                    />
                    <span>
                      ${t(s, "zones.entity", {
                        name: zone.name,
                        entity: areas.get(zone.area_id) ?? zone.area_id,
                      })}
                    </span>
                  </label>`,
                )
              : html`<p class="hint">${t(s, "groups.no_zones")}</p>`}
            <p class="hint">${t(s, "groups.members_hint")}</p>
          </fieldset>
          <label class="check suppress">
            <input
              type="checkbox"
              .checked=${live(draft.suppress_members)}
              @change=${(e: Event) =>
                this._set("suppress_members", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "field.suppress_members")}
              <span class="hint">${t(s, "groups.suppress_hint")}</span>
            </span>
          </label>
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
              ? html`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${t(s, "common.delete")}
                </button>`
              : nothing}
          </div>
        </div>
      </div>
    `;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      .suppress {
        margin-top: 12px;
      }
      td .tag {
        margin-left: 6px;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-groups")) {
  customElements.define("foyer-page-groups", FoyerPageGroups);
}
