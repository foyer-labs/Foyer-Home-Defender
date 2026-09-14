// Page 3 — Zones (SPEC §4.2–4.4, §15.1), including the zone wizard.
//
// INV-5: the trigger is proposed from the entity's device_class and current
// state, and must be confirmed against the real sensor before it can be
// saved. The backend enforces the confirmation too; this page only asks.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  KeyConfig,
  Problem,
  StatusZone,
  Trigger,
  ZoneConfig,
  ZoneProposal,
} from "../../shared/types";
import { optionalNumber, problemText, type PanelContext } from "../context";

const EVENT_DOMAINS = new Set(["event", "tag"]);
const FAULT_STATES = new Set(["unavailable", "unknown"]);

function blankZone(areaId: string): ZoneConfig {
  return {
    name: "",
    entity_id: "",
    area_id: areaId,
    trigger: { kind: "state", states: [] },
    type: "instant",
    channel: "intrusion",
    entry_mode: "instant",
    alarm_kind: "intrusion",
    always_on: false,
    entry_delay: null,
    arm_policy: "block",
    arm_hold_timeout: null,
    allow_arm_when_faulted: false,
    bypassable: true,
    supervision_timeout: null,
    enabled: true,
    key: null,
  };
}

const sameTrigger = (a?: Trigger, b?: Trigger) => JSON.stringify(a) === JSON.stringify(b);

class FoyerPageZones extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _saved: { state: true },
    _proposal: { state: true },
    _confirmed: { state: true },
    _problems: { state: true },
    _busy: { state: true },
    _filter: { state: true },
    _customState: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: ZoneConfig;
  private _saved?: ZoneConfig; // as stored, to know whether the trigger changed
  private _proposal?: ZoneProposal;
  private _confirmed = false;
  private _problems: Problem[] = [];
  private _busy = false;
  private _filter = "";
  private _customState = "";

  // --- editing -------------------------------------------------------------------

  private _edit(zone?: ZoneConfig): void {
    const areaId = this.ctx?.config?.areas[0]?.id ?? "";
    this._draft = zone ? structuredClone(zone) : blankZone(areaId);
    this._saved = zone;
    this._proposal = undefined;
    this._confirmed = false;
    this._problems = [];
    if (zone) this._propose(zone.entity_id, false);
  }

  private _set<K extends keyof ZoneConfig>(key: K, value: ZoneConfig[K]): void {
    if (!this._draft) return;
    this._draft = { ...this._draft, [key]: value };
    if (key === "trigger") this._confirmed = false;
  }

  private _applyType(type: string): void {
    const preset = this.ctx?.meta?.zone_types.find((z) => z.type === type)?.preset ?? {};
    if (!this._draft) return;
    const draft: ZoneConfig = { ...this._draft, ...preset, type };
    if (draft.channel === "key" && !draft.key) {
      draft.key = { on_activate: "toggle", scenario_id: null, on_deactivate: "none" };
    }
    if (draft.channel !== "key") draft.key = null;
    if (draft.arm_policy !== "arm_after_closing") draft.arm_hold_timeout = null;
    this._draft = draft;
  }

  private async _propose(entityId: string, apply: boolean): Promise<void> {
    const ctx = this.ctx;
    if (!ctx || !entityId) return;
    const proposal = await ctx.hass.callWS<ZoneProposal>({
      type: "foyer/zone/propose",
      entity_id: entityId,
    });
    this._proposal = proposal;
    if (!apply || !this._draft) return;
    // A proposal is a starting point, never a decision (INV-5).
    const trigger: Trigger =
      proposal.trigger_kind === "event"
        ? {
            kind: "event",
            event_type: entityId.startsWith("event.") ? (proposal.proposed[0] ?? null) : null,
            subtype: null,
          }
        : proposal.trigger_kind === "numeric"
          ? { kind: "numeric", operator: "gt", value: 0, hysteresis: 0, attribute: null }
          : { kind: "state", states: [...proposal.proposed] };
    this._draft = {
      ...this._draft,
      entity_id: entityId,
      name: this._draft.name || proposal.name,
    };
    this._set("trigger", trigger);
    if (proposal.zone_type && this._typeAvailable(proposal.zone_type)) {
      this._applyType(proposal.zone_type);
    }
  }

  private _typeAvailable(type: string): boolean {
    return this.ctx?.meta?.zone_types.find((z) => z.type === type)?.available ?? false;
  }

  private _triggerChanged(): boolean {
    return !this._saved || !sameTrigger(this._saved.trigger, this._draft?.trigger);
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("zone", this._draft, this._confirmed);
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
      const result = await this.ctx.remove("zone", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  // --- list -------------------------------------------------------------------------

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const areas = new Map(ctx.config.areas.map((a) => [a.id, a.name]));
    const live = new Map(ctx.status.zones.map((z) => [z.id, z]));
    if (!ctx.config.areas.length) {
      return html`<div class="card"><div class="empty">${t(s, "zones.no_areas")}</div></div>`;
    }
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "zones.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${t(s, "zones.add")}</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${t(s, "field.name")}</th>
                <th>${t(s, "field.entity_id")}</th>
                <th>${t(s, "field.area_id")}</th>
                <th>${t(s, "field.type")}</th>
                <th>${t(s, "field.arm_policy")}</th>
                <th>${t(s, "overview.status")}</th>
              </tr>
            </thead>
            <tbody>
              ${ctx.config.zones.map(
                (zone) => html`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === zone.id ? "true" : "false"}
                  @click=${() => this._edit(zone)}
                >
                  <td><strong>${zone.name}</strong></td>
                  <td class="mono">${zone.entity_id}</td>
                  <td>${areas.get(zone.area_id) ?? ""}</td>
                  <td><span class="tag">${t(s, `zone_type.${zone.type}`)}</span></td>
                  <td>${t(s, `arm_policy.${zone.arm_policy}`)}</td>
                  <td>${this._health(s, live.get(zone.id ?? ""))}</td>
                </tr>`,
              )}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
    `;
  }

  private _health(s: Strings, zone?: StatusZone) {
    if (!zone) return nothing;
    if (!zone.enabled) {
      return html`<span class="state disabled">${t(s, "zone_status.disabled")}</span>`;
    }
    if (zone.fault) {
      return html`<span class="state fault">${t(s, `fault.${zone.fault}`)}</span>`;
    }
    if (zone.bypassed) {
      return html`<span class="state bypassed">${t(s, `bypass.${zone.bypassed}`)}</span>`;
    }
    const kind = zone.open ? "open" : "closed";
    return html`<span class="state ${kind}">${t(s, `zone_status.${kind}`)}</span>`;
  }

  // --- editor ---------------------------------------------------------------------

  private _renderEditor(s: Strings, draft: ZoneConfig) {
    const ctx = this.ctx!;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "zones.new")}</h2>
        </div>
        <div class="card-bd">
          ${draft.id ? nothing : this._renderEntityPicker(s, draft)}
          ${draft.entity_id
            ? html`
                ${this._renderTrigger(s, draft)} ${this._renderProperties(s, draft)}
                ${draft.channel === "key" ? this._renderKey(s, draft) : nothing}
              `
            : nothing}
          ${this._problems.length
            ? html`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
                </ul>
              </div>`
            : nothing}
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy ||
              !draft.entity_id ||
              (this._triggerChanged() && !this._confirmed)}
              @click=${this._save}
            >
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
          ${this._triggerChanged() && !this._confirmed && draft.entity_id
            ? html`<div class="hint">${t(s, "zones.confirm_first")}</div>`
            : nothing}
          ${ctx.status.areas.some((a) => a.id === draft.area_id && a.state !== "disarmed")
            ? html`<div class="notice">${t(s, "zones.area_armed")}</div>`
            : nothing}
        </div>
      </div>
    `;
  }

  private _renderEntityPicker(s: Strings, draft: ZoneConfig) {
    const ctx = this.ctx!;
    const domains = new Set(ctx.meta?.zone_domains ?? []);
    const used = new Set(ctx.config?.zones.map((z) => z.entity_id));
    const filter = this._filter.toLowerCase();
    const candidates = Object.values(ctx.hass.states)
      .filter((e) => domains.has(e.entity_id.split(".")[0]))
      .filter((e) => {
        const name = String(e.attributes.friendly_name ?? "");
        return (
          !filter ||
          e.entity_id.toLowerCase().includes(filter) ||
          name.toLowerCase().includes(filter)
        );
      })
      .sort((a, b) => a.entity_id.localeCompare(b.entity_id))
      .slice(0, 200);
    return html`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "zones.search")}</span>
          <input
            .value=${this._filter}
            @input=${(e: Event) => (this._filter = (e.target as HTMLInputElement).value)}
          />
        </label>
        <label class="field">
          <span class="lbl">${t(s, "field.entity_id")}</span>
          <select
            @change=${(e: Event) => this._propose((e.target as HTMLSelectElement).value, true)}
          >
            <option value="" ?selected=${!draft.entity_id}>${t(s, "zones.pick_entity")}</option>
            ${candidates.map(
              (e) => html`<option
                .value=${e.entity_id}
                ?selected=${e.entity_id === draft.entity_id}
              >
                ${t(s, used.has(e.entity_id) ? "zones.entity_used" : "zones.entity", {
                  name: String(e.attributes.friendly_name ?? e.entity_id),
                  entity: e.entity_id,
                })}
              </option>`,
            )}
          </select>
          <span class="hint">${t(s, "zones.entity_hint")}</span>
        </label>
      </div>
    `;
  }

  private _renderTrigger(s: Strings, draft: ZoneConfig) {
    const ctx = this.ctx!;
    const entity = ctx.hass.states[draft.entity_id];
    const current = entity?.state ?? "unavailable";
    const domain = draft.entity_id.split(".")[0];
    const trigger = draft.trigger;
    return html`
      <fieldset>
        <legend>${t(s, "zones.trigger_title")}</legend>
        <p class="hint">
          ${t(s, "zones.trigger_intro", {
            entity: String(entity?.attributes.friendly_name ?? draft.entity_id),
            state: current,
          })}
          ${this._proposal?.device_class
            ? t(s, "zones.device_class", { device_class: this._proposal.device_class })
            : nothing}
        </p>
        ${EVENT_DOMAINS.has(domain)
          ? this._renderEventTrigger(s, domain, trigger)
          : html`
              <label class="field">
                <span class="lbl">${t(s, "zones.trigger_kind")}</span>
                <select
                  @change=${(e: Event) => {
                    const kind = (e.target as HTMLSelectElement).value;
                    this._set(
                      "trigger",
                      kind === "numeric"
                        ? { kind: "numeric", operator: "gt", value: 0, hysteresis: 0, attribute: null }
                        : { kind: "state", states: [] },
                    );
                  }}
                >
                  <option value="state" ?selected=${trigger.kind === "state"}>
                    ${t(s, "zones.kind_state")}
                  </option>
                  <option value="numeric" ?selected=${trigger.kind === "numeric"}>
                    ${t(s, "zones.kind_numeric")}
                  </option>
                </select>
              </label>
              ${trigger.kind === "numeric"
                ? this._renderNumericTrigger(s, trigger)
                : trigger.kind === "state"
                  ? this._renderStateTrigger(s, trigger.states, current)
                  : nothing}
            `}
        <label class="check confirm">
          <input
            type="checkbox"
            .checked=${this._confirmed || !this._triggerChanged()}
            ?disabled=${!this._triggerChanged()}
            @change=${(e: Event) => (this._confirmed = (e.target as HTMLInputElement).checked)}
          />
          <span>
            ${t(s, "zones.confirm")}
            <span class="hint">${t(s, "zones.confirm_hint")}</span>
          </span>
        </label>
      </fieldset>
    `;
  }

  private _renderStateTrigger(s: Strings, states: string[], current: string) {
    const options = new Set<string>([...(this._proposal?.options ?? []), ...states]);
    if (!FAULT_STATES.has(current)) options.add(current);
    const toggle = (state: string, on: boolean) => {
      const next = on ? [...states, state] : states.filter((x) => x !== state);
      this._set("trigger", { kind: "state", states: [...new Set(next)].sort() });
    };
    return html`
      <div class="states">
        ${[...options].map(
          (state) => html`<label class="check">
            <input
              type="checkbox"
              .checked=${states.includes(state)}
              @change=${(e: Event) => toggle(state, (e.target as HTMLInputElement).checked)}
            />
            <span class="mono">${state}</span>
            ${state === current ? html`<span class="tag">${t(s, "zones.now")}</span>` : nothing}
          </label>`,
        )}
      </div>
      <div class="row">
        <label class="field">
          <span class="lbl">${t(s, "zones.other_state")}</span>
          <input
            .value=${this._customState}
            @input=${(e: Event) => (this._customState = (e.target as HTMLInputElement).value)}
          />
        </label>
        <button
          class="btn"
          ?disabled=${!this._customState.trim()}
          @click=${() => {
            toggle(this._customState.trim(), true);
            this._customState = "";
          }}
        >
          ${t(s, "zones.add_state")}
        </button>
      </div>
      <div class="hint">${t(s, "zones.state_hint")}</div>
    `;
  }

  private _renderNumericTrigger(s: Strings, trigger: Extract<Trigger, { kind: "numeric" }>) {
    const update = (patch: Partial<typeof trigger>) =>
      this._set("trigger", { ...trigger, ...patch });
    return html`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "zones.operator")}</span>
          <select
            @change=${(e: Event) =>
              update({ operator: (e.target as HTMLSelectElement).value as "gt" | "lt" | "eq" })}
          >
            ${(["gt", "lt", "eq"] as const).map(
              (op) =>
                html`<option .value=${op} ?selected=${op === trigger.operator}>
                  ${t(s, `operator.${op}`)}
                </option>`,
            )}
          </select>
        </label>
        <label class="field">
          <span class="lbl">${t(s, "zones.threshold")}</span>
          <input
            type="number"
            step="any"
            .value=${String(trigger.value)}
            @input=${(e: Event) => update({ value: Number((e.target as HTMLInputElement).value) })}
          />
        </label>
        <label class="field">
          <span class="lbl">${t(s, "zones.hysteresis")}</span>
          <input
            type="number"
            step="any"
            min="0"
            ?disabled=${trigger.operator === "eq"}
            .value=${String(trigger.hysteresis)}
            @input=${(e: Event) =>
              update({ hysteresis: Number((e.target as HTMLInputElement).value) })}
          />
          <span class="hint">${t(s, "zones.hysteresis_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${t(s, "zones.attribute")}</span>
          <input
            .value=${trigger.attribute ?? ""}
            @input=${(e: Event) =>
              update({ attribute: (e.target as HTMLInputElement).value.trim() || null })}
          />
          <span class="hint">${t(s, "zones.attribute_hint")}</span>
        </label>
      </div>
    `;
  }

  private _renderEventTrigger(s: Strings, domain: string, trigger: Trigger) {
    if (domain === "tag") {
      // The proposal already set an event trigger with no type: a tag has one
      // event, the scan.
      return html`<p class="hint">${t(s, "zones.tag_hint")}</p>`;
    }
    const eventType = trigger.kind === "event" ? trigger.event_type : null;
    return html`
      <label class="field">
        <span class="lbl">${t(s, "zones.event_type")}</span>
        <select
          @change=${(e: Event) =>
            this._set("trigger", {
              kind: "event",
              event_type: (e.target as HTMLSelectElement).value || null,
              subtype: null,
            })}
        >
          <option value="" ?selected=${!eventType}>${t(s, "zones.pick_event")}</option>
          ${(this._proposal?.options ?? []).map(
            (type) =>
              html`<option .value=${type} ?selected=${type === eventType}>${type}</option>`,
          )}
        </select>
        <span class="hint">${t(s, "zones.event_hint")}</span>
      </label>
    `;
  }

  private _renderProperties(s: Strings, draft: ZoneConfig) {
    const ctx = this.ctx!;
    const meta = ctx.meta;
    const area = ctx.config?.areas.find((a) => a.id === draft.area_id);
    const intrusion = draft.channel === "intrusion";
    const check = (key: keyof ZoneConfig, hintKey?: string) => html`
      <label class="check">
        <input
          type="checkbox"
          .checked=${Boolean(draft[key])}
          @change=${(e: Event) =>
            this._set(key, (e.target as HTMLInputElement).checked as never)}
        />
        <span>
          ${t(s, `field.${key}`)}
          ${hintKey ? html`<span class="hint">${t(s, hintKey)}</span>` : nothing}
        </span>
      </label>
    `;
    return html`
      <fieldset>
        <legend>${t(s, "zones.properties_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${t(s, "field.name")}</span>
            <input
              .value=${draft.name}
              @input=${(e: Event) => this._set("name", (e.target as HTMLInputElement).value)}
            />
          </label>
          <label class="field">
            <span class="lbl">${t(s, "field.type")}</span>
            <select @change=${(e: Event) => this._applyType((e.target as HTMLSelectElement).value)}>
              ${(meta?.zone_types ?? []).map(
                (zt) => html`<option
                  .value=${zt.type}
                  ?selected=${zt.type === draft.type}
                  ?disabled=${!zt.available}
                >
                  ${t(s, zt.available ? `zone_type.${zt.type}` : "zones.type_unavailable", {
                    type: t(s, `zone_type.${zt.type}`),
                  })}
                </option>`,
              )}
            </select>
            <span class="hint">${t(s, "zones.type_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${t(s, "field.area_id")}</span>
            <select
              @change=${(e: Event) => this._set("area_id", (e.target as HTMLSelectElement).value)}
            >
              ${(ctx.config?.areas ?? []).map(
                (a) =>
                  html`<option .value=${a.id ?? ""} ?selected=${a.id === draft.area_id}>
                    ${a.name}
                  </option>`,
              )}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${t(s, "field.channel")}</span>
            <select
              @change=${(e: Event) => {
                const channel = (e.target as HTMLSelectElement).value as ZoneConfig["channel"];
                this._set("channel", channel);
                this._set(
                  "key",
                  channel === "key"
                    ? (draft.key ?? { on_activate: "toggle", scenario_id: null, on_deactivate: "none" })
                    : null,
                );
              }}
            >
              ${(["intrusion", "key", "technical"] as const).map(
                (channel) =>
                  html`<option
                    .value=${channel}
                    ?selected=${channel === draft.channel}
                    ?disabled=${channel === "technical"}
                  >
                    ${t(s, `channel.${channel}`)}
                  </option>`,
              )}
            </select>
          </label>
          ${intrusion
            ? html`
                <label class="field">
                  <span class="lbl">${t(s, "field.entry_mode")}</span>
                  <select
                    ?disabled=${draft.always_on}
                    @change=${(e: Event) =>
                      this._set(
                        "entry_mode",
                        (e.target as HTMLSelectElement).value as ZoneConfig["entry_mode"],
                      )}
                  >
                    ${(["instant", "delayed", "follower"] as const).map(
                      (mode) =>
                        html`<option .value=${mode} ?selected=${mode === draft.entry_mode}>
                          ${t(s, `entry_mode.${mode}`)}
                        </option>`,
                    )}
                  </select>
                  <span class="hint">${t(s, `entry_mode_hint.${draft.entry_mode}`)}</span>
                </label>
                <label class="field">
                  <span class="lbl">${t(s, "field.entry_delay")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${meta?.bounds.entry_delay?.[1] ?? 300}
                    placeholder=${t(s, "zones.inherit_seconds", {
                      n: area?.default_entry_delay ?? 30,
                    })}
                    .value=${draft.entry_delay == null ? "" : String(draft.entry_delay)}
                    @input=${(e: Event) =>
                      this._set("entry_delay", optionalNumber((e.target as HTMLInputElement).value))}
                  />
                  <span class="hint">${t(s, "zones.entry_delay_hint")}</span>
                </label>
                <label class="field">
                  <span class="lbl">${t(s, "field.alarm_kind")}</span>
                  <select
                    @change=${(e: Event) =>
                      this._set(
                        "alarm_kind",
                        (e.target as HTMLSelectElement).value as ZoneConfig["alarm_kind"],
                      )}
                  >
                    ${(["intrusion", "tamper", "panic"] as const).map(
                      (kind) =>
                        html`<option .value=${kind} ?selected=${kind === draft.alarm_kind}>
                          ${t(s, `alarm_kind.${kind}`)}
                        </option>`,
                    )}
                  </select>
                </label>
                <label class="field">
                  <span class="lbl">${t(s, "field.arm_policy")}</span>
                  <select
                    @change=${(e: Event) => {
                      const policy = (e.target as HTMLSelectElement)
                        .value as ZoneConfig["arm_policy"];
                      this._set("arm_policy", policy);
                      if (policy !== "arm_after_closing") this._set("arm_hold_timeout", null);
                    }}
                  >
                    ${(["block", "auto_bypass", "arm_after_closing", "ignore"] as const).map(
                      (policy) =>
                        html`<option .value=${policy} ?selected=${policy === draft.arm_policy}>
                          ${t(s, `arm_policy.${policy}`)}
                        </option>`,
                    )}
                  </select>
                  <span class="hint">${t(s, `arm_policy_hint.${draft.arm_policy}`)}</span>
                </label>
                ${draft.arm_policy === "arm_after_closing"
                  ? html`<label class="field">
                      <span class="lbl">${t(s, "field.arm_hold_timeout")}</span>
                      <input
                        type="number"
                        min=${meta?.bounds.arm_hold_timeout?.[0] ?? 60}
                        max=${meta?.bounds.arm_hold_timeout?.[1] ?? 1800}
                        placeholder=${t(s, "zones.inherit_seconds", {
                          n: ctx.config?.settings.arm_hold_timeout ?? 300,
                        })}
                        .value=${draft.arm_hold_timeout == null ? "" : String(draft.arm_hold_timeout)}
                        @input=${(e: Event) =>
                          this._set(
                            "arm_hold_timeout",
                            optionalNumber((e.target as HTMLInputElement).value),
                          )}
                      />
                      <span class="hint">${t(s, "zones.hold_hint")}</span>
                    </label>`
                  : nothing}
              `
            : nothing}
          <label class="field">
            <span class="lbl">${t(s, "field.supervision_timeout")}</span>
            <input
              type="number"
              min=${meta?.bounds.supervision_timeout?.[0] ?? 60}
              placeholder=${t(s, "zones.off")}
              .value=${draft.supervision_timeout == null ? "" : String(draft.supervision_timeout)}
              @input=${(e: Event) =>
                this._set(
                  "supervision_timeout",
                  optionalNumber((e.target as HTMLInputElement).value),
                )}
            />
            <span class="hint">${t(s, "zones.supervision_hint")}</span>
          </label>
        </div>
        <div class="checks">
          ${intrusion ? check("always_on", "zones.always_on_hint") : nothing}
          ${intrusion ? check("bypassable", "zones.bypassable_hint") : nothing}
          ${check("allow_arm_when_faulted", "zones.allow_faulted_hint")}
          ${check("enabled", "zones.enabled_hint")}
        </div>
      </fieldset>
    `;
  }

  private _renderKey(s: Strings, draft: ZoneConfig) {
    const key: KeyConfig = draft.key ?? {
      on_activate: "toggle",
      scenario_id: null,
      on_deactivate: "none",
    };
    const update = (patch: Partial<KeyConfig>) => this._set("key", { ...key, ...patch });
    const scenarios = this.ctx?.config?.scenarios ?? [];
    return html`
      <fieldset>
        <legend>${t(s, "zones.key_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${t(s, "field.on_activate")}</span>
            <select
              @change=${(e: Event) =>
                update({
                  on_activate: (e.target as HTMLSelectElement).value as KeyConfig["on_activate"],
                })}
            >
              ${(["arm", "disarm", "toggle"] as const).map(
                (cmd) =>
                  html`<option .value=${cmd} ?selected=${cmd === key.on_activate}>
                    ${t(s, `key_command.${cmd}`)}
                  </option>`,
              )}
            </select>
          </label>
          ${key.on_activate === "disarm"
            ? nothing
            : html`<label class="field">
                <span class="lbl">${t(s, "field.scenario_id")}</span>
                <select
                  @change=${(e: Event) =>
                    update({ scenario_id: (e.target as HTMLSelectElement).value || null })}
                >
                  <option value="" ?selected=${!key.scenario_id}>
                    ${t(s, "zones.pick_scenario")}
                  </option>
                  ${scenarios.map(
                    (sc) =>
                      html`<option .value=${sc.id ?? ""} ?selected=${sc.id === key.scenario_id}>
                        ${sc.name}
                      </option>`,
                  )}
                </select>
              </label>`}
          <label class="field">
            <span class="lbl">${t(s, "field.on_deactivate")}</span>
            <select
              @change=${(e: Event) =>
                update({
                  on_deactivate: (e.target as HTMLSelectElement)
                    .value as KeyConfig["on_deactivate"],
                })}
            >
              ${(["none", "disarm"] as const).map(
                (cmd) =>
                  html`<option .value=${cmd} ?selected=${cmd === key.on_deactivate}>
                    ${t(s, `key_release.${cmd}`)}
                  </option>`,
              )}
            </select>
          </label>
        </div>
        <p class="hint">${t(s, "zones.key_hint")}</p>
      </fieldset>
    `;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      .states {
        display: flex;
        flex-wrap: wrap;
        gap: 4px 18px;
        margin: 10px 0;
      }
      .row {
        display: flex;
        align-items: flex-end;
        gap: 8px;
        flex-wrap: wrap;
      }
      .checks {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 0 16px;
        margin-top: 12px;
      }
      .confirm {
        margin-top: 12px;
        padding: 10px 12px;
        border-radius: 8px;
        background: var(--secondary-background-color);
        font-weight: 500;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-zones")) {
  customElements.define("foyer-page-zones", FoyerPageZones);
}
