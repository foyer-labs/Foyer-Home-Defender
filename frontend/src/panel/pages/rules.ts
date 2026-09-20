// Page 12 — Automation rules (SPEC §9.4, §15.1): the rules that let the house
// arm itself, the guards that stop them, the cancellable countdown, and the
// suspensions — including the named window for the morning the boiler
// engineer is expected.
//
// Two things on this page are not decoration. Automatic disarming is off
// until somebody turns it on, and the warning beside that switch names the
// attack in the words of §9.4 rather than a general caution. And the list of
// areas a rule may disarm shows the perimeter ones as never — the engine is
// what enforces it, and this only says so.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  AutoStatus,
  Problem,
  RuleActionKind,
  RuleConfig,
  RuleTriggerKind,
  SuspensionConfig,
} from "../../shared/types";
import { entityTargets } from "../ha-targets";
import { optionalNumber, problemText, type PanelContext } from "../context";

const WEEKDAYS = [0, 1, 2, 3, 4, 5, 6];

/** A date and time as the reader's own locale writes it, to the minute. The
 * seconds a raw toLocaleString adds are noise on a window that lasts hours. */
function when(value: string | null | undefined): string {
  if (!value) return "";
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function emptyRule(): RuleConfig {
  return {
    name: "",
    trigger: {
      kind: "absence",
      entity_ids: [],
      state: null,
      minutes: 30,
      at: null,
      weekdays: [],
    },
    action: "arm",
    scenario_id: null,
    area_ids: [],
    window: { weekdays: [], after: null, before: null },
    guards: { only_when_disarmed: true, only_when_ready: true, quiet_minutes: null },
    grace_seconds: 120,
    notify_contact_ids: [],
    enabled: true,
  };
}

interface VisitorDraft {
  name: string;
  start: string;
  until: string;
  reduced_scenario_id: string | null;
}

class FoyerPageRules extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _visitor: { state: true },
    _problems: { state: true },
    _busy: { state: true },
    _error: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: RuleConfig;
  private _visitor: VisitorDraft = {
    name: "",
    start: "",
    until: "",
    reduced_scenario_id: null,
  };
  private _problems: Problem[] = [];
  private _busy = false;
  private _error?: string;

  private get _auto(): AutoStatus | undefined {
    return this.ctx?.status?.auto;
  }

  private _edit(rule?: RuleConfig): void {
    this._draft = rule ? structuredClone(rule) : emptyRule();
    this._problems = [];
  }

  private _set<K extends keyof RuleConfig>(key: K, value: RuleConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private _setTrigger<K extends keyof RuleConfig["trigger"]>(
    key: K,
    value: RuleConfig["trigger"][K],
  ): void {
    if (this._draft) {
      this._set("trigger", { ...this._draft.trigger, [key]: value });
    }
  }

  private _setGuard<K extends keyof RuleConfig["guards"]>(
    key: K,
    value: RuleConfig["guards"][K],
  ): void {
    if (this._draft) this._set("guards", { ...this._draft.guards, [key]: value });
  }

  private _setWindow<K extends keyof RuleConfig["window"]>(
    key: K,
    value: RuleConfig["window"][K],
  ): void {
    if (this._draft) this._set("window", { ...this._draft.window, [key]: value });
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("rule", this._draft);
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
      const result = await this.ctx.remove("rule", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  private async _run(action: () => Promise<{ success: boolean; reason: string | null }>) {
    this._busy = true;
    this._error = undefined;
    try {
      const result = await action();
      if (!result.success) {
        this._error = t(this.ctx!.strings, `reason.${result.reason ?? "unknown"}`);
      }
    } finally {
      this._busy = false;
    }
  }

  private async _addVisitor(): Promise<void> {
    const ctx = this.ctx;
    const draft = this._visitor;
    if (!ctx || !draft.name.trim() || !draft.until) return;
    await this._run(() =>
      ctx.suspend({
        kind: "visitor",
        name: draft.name.trim(),
        start: draft.start ? new Date(draft.start).toISOString() : null,
        until: new Date(draft.until).toISOString(),
        reduced_scenario_id: draft.reduced_scenario_id,
      }),
    );
    this._visitor = { name: "", start: "", until: "", reduced_scenario_id: null };
  }

  // --- rendering -----------------------------------------------------------------

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const auto = this._auto;
    return html`
      ${this._renderNext(s)}
      ${this._error ? html`<div class="problems" role="alert">${this._error}</div>` : nothing}
      ${this._renderRules(s)}
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
      ${this._renderSuspensions(s, auto?.suspensions ?? [])}
      ${this._renderDisarming(s)}
    `;
  }

  /** The banner of §9.4: what happens next, and the one place to stop it. */
  private _renderNext(s: Strings) {
    const ctx = this.ctx!;
    const auto = this._auto;
    const next = auto?.next;
    const pending = auto?.pending ?? [];
    if (!auto?.enabled) {
      return html`<div class="banner warn">
        <div>${t(s, "rules.switched_off")}</div>
        <span class="spacer"></span>
        <button
          class="btn sm"
          ?disabled=${this._busy}
          @click=${() => this._run(() => ctx.setAutoArming(true))}
        >
          ${t(s, "rules.switch_on")}
        </button>
      </div>`;
    }
    if (pending.length) {
      return html`${pending.map(
        (item) => html`<div class="banner crit">
          <div>
            ${t(s, `rules.counting_${item.action}`, {
              rule: item.rule_name,
              scenario: this._scenarioName(item.scenario_id),
              seconds: Math.max(
                0,
                Math.round((Date.parse(item.due) - ctx.now()) / 1000),
              ),
            })}
          </div>
          <span class="spacer"></span>
          <button
            class="btn sm primary"
            ?disabled=${this._busy}
            @click=${() => this._run(() => ctx.cancelAuto(item.id))}
          >
            ${t(s, "rules.cancel_now")}
          </button>
        </div>`,
      )}`;
    }
    return html`<div class="banner info">
      <div>
        ${next
          ? t(s, `rules.next_${next.action}`, {
              rule: next.rule_name,
              scenario: this._scenarioName(next.scenario_id),
              when: when(next.at),
            })
          : t(s, "rules.next_none")}
      </div>
      <span class="spacer"></span>
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => ctx.setAutoArming(false))}
      >
        ${t(s, "rules.switch_off")}
      </button>
    </div>`;
  }

  private _scenarioName(id: string | null | undefined): string {
    if (!id) return "";
    return this.ctx?.config?.scenarios.find((sc) => sc.id === id)?.name ?? "";
  }

  private _triggerText(s: Strings, rule: RuleConfig): string {
    const trigger = rule.trigger;
    const people = trigger.entity_ids.length;
    switch (trigger.kind) {
      case "absence":
        return t(s, "rules.trigger_absence", { n: people, minutes: trigger.minutes });
      case "presence":
        return t(s, "rules.trigger_presence", { n: people });
      case "time":
        return t(s, "rules.trigger_time", {
          at: trigger.at ?? "",
          days: this._days(s, trigger.weekdays),
        });
      default:
        return t(s, "rules.trigger_entity", {
          entity: trigger.entity_ids[0] ?? "",
          state: trigger.state ?? "",
          minutes: trigger.minutes,
        });
    }
  }

  private _days(s: Strings, days: number[]): string {
    if (!days.length) return t(s, "rules.every_day");
    return days.map((d) => t(s, `rules.weekday_${d}`)).join(", ");
  }

  private _actionText(s: Strings, rule: RuleConfig): string {
    if (rule.action === "disarm") {
      const areas = this.ctx?.config?.areas ?? [];
      const named = rule.area_ids
        .map((id) => areas.find((a) => a.id === id))
        .filter((a) => a !== undefined);
      return t(s, "rules.action_disarm", {
        areas: named.map((a) => a!.name).join(", "),
      });
    }
    return t(s, `rules.action_${rule.action}`, {
      scenario: this._scenarioName(rule.scenario_id),
    });
  }

  private _guardText(s: Strings, rule: RuleConfig): string {
    const parts: string[] = [];
    if (rule.guards.only_when_disarmed) parts.push(t(s, "rules.guard_disarmed"));
    if (rule.guards.only_when_ready) parts.push(t(s, "rules.guard_ready"));
    if (rule.guards.quiet_minutes !== null) {
      parts.push(t(s, "rules.guard_quiet", { minutes: rule.guards.quiet_minutes }));
    }
    return parts.length ? parts.join(" · ") : t(s, "rules.guard_none");
  }

  private _renderRules(s: Strings) {
    const ctx = this.ctx!;
    const rules = ctx.config?.rules ?? [];
    const blocked = this._auto?.blocked ?? {};
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "rules.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${t(s, "rules.add")}
          </button>
        </div>
        ${rules.length
          ? html`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${t(s, "field.name")}</th>
                    <th>${t(s, "field.trigger")}</th>
                    <th>${t(s, "rules.action")}</th>
                    <th>${t(s, "field.window")}</th>
                    <th>${t(s, "field.guards")}</th>
                    <th>${t(s, "field.grace_seconds")}</th>
                    <th>${t(s, "rules.status")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${rules.map(
                    (rule) => html`<tr
                      class="clickable"
                      aria-selected=${this._draft?.id === rule.id ? "true" : "false"}
                      @click=${() => this._edit(rule)}
                    >
                      <td><strong>${rule.name}</strong></td>
                      <td>${this._triggerText(s, rule)}</td>
                      <td>
                        <span class=${rule.action === "arm" ? "pill ok" : "pill warn"}>
                          ${this._actionText(s, rule)}
                        </span>
                      </td>
                      <td class="muted">
                        ${rule.window.after && rule.window.before
                          ? `${this._days(s, rule.window.weekdays)} ${rule.window.after}–${rule.window.before}`
                          : this._days(s, rule.window.weekdays)}
                      </td>
                      <td class="muted small">${this._guardText(s, rule)}</td>
                      <td class="num">
                        ${rule.grace_seconds
                          ? t(s, "common.seconds", { n: rule.grace_seconds })
                          : t(s, "rules.at_once")}
                      </td>
                      <td>
                        ${!rule.enabled
                          ? html`<span class="pill idle">${t(s, "rules.disabled")}</span>`
                          : blocked[rule.id ?? ""]
                            ? html`<span class="pill warn"
                                >${t(s, `rules.block_${blocked[rule.id ?? ""]}`)}</span
                              >`
                            : html`<span class="pill ok">${t(s, "rules.active")}</span>`}
                      </td>
                    </tr>`,
                  )}
                </tbody>
              </table>
            </div>`
          : html`<div class="empty">${t(s, "rules.none")}</div>`}
      </div>
    `;
  }

  private _renderEditor(s: Strings, draft: RuleConfig) {
    const ctx = this.ctx!;
    const people = entityTargets(ctx.hass, ctx.meta?.presence_domains ?? ["person"]);
    const maxGrace = ctx.meta?.max_grace_seconds ?? 900;
    const maxMinutes = ctx.meta?.max_rule_minutes ?? 1440;
    const trigger = draft.trigger;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "rules.new")}</h2>
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
              <span class="lbl">${t(s, "field.trigger")}</span>
              <select
                @change=${(e: Event) =>
                  this._setTrigger("kind", (e.target as HTMLSelectElement).value as RuleTriggerKind)}
              >
                ${(ctx.meta?.rule_triggers ?? []).map(
                  (kind) =>
                    html`<option .value=${kind} ?selected=${kind === trigger.kind}>
                      ${t(s, `rules.trigger_kind_${kind}`)}
                    </option>`,
                )}
              </select>
              <span class="hint">${t(s, `rules.trigger_hint_${trigger.kind}`)}</span>
            </label>
            ${trigger.kind === "time"
              ? html`<label class="field">
                  <span class="lbl">${t(s, "rules.at")}</span>
                  <input
                    type="time"
                    .value=${trigger.at ?? ""}
                    @change=${(e: Event) =>
                      this._setTrigger("at", (e.target as HTMLInputElement).value || null)}
                  />
                </label>`
              : html`<label class="field">
                  <span class="lbl">${t(s, "rules.for_minutes")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${maxMinutes}
                    .value=${String(trigger.minutes)}
                    ?disabled=${trigger.kind === "presence"}
                    @input=${(e: Event) =>
                      this._setTrigger(
                        "minutes",
                        optionalNumber((e.target as HTMLInputElement).value) ?? 0,
                      )}
                  />
                </label>`}
          </div>

          ${trigger.kind === "absence" || trigger.kind === "presence"
            ? html`<div class="block">
                <div class="lbl strong">${t(s, "rules.people")}</div>
                <div class="chips">
                  ${people.length
                    ? people.map((person) => {
                        const on = trigger.entity_ids.includes(person.id);
                        return html`<label class="chip">
                          <input
                            type="checkbox"
                            .checked=${on}
                            @change=${(e: Event) =>
                              this._setTrigger(
                                "entity_ids",
                                (e.target as HTMLInputElement).checked
                                  ? [...trigger.entity_ids, person.id]
                                  : trigger.entity_ids.filter((id) => id !== person.id),
                              )}
                          />
                          <span>${person.name}</span>
                        </label>`;
                      })
                    : html`<span class="hint">${t(s, "rules.no_people")}</span>`}
                </div>
                <span class="hint">${t(s, "rules.people_hint")}</span>
              </div>`
            : nothing}
          ${trigger.kind === "entity"
            ? html`<div class="grid-form">
                <label class="field">
                  <span class="lbl">${t(s, "field.entity_id")}</span>
                  <input
                    .value=${trigger.entity_ids[0] ?? ""}
                    @change=${(e: Event) =>
                      this._setTrigger(
                        "entity_ids",
                        [(e.target as HTMLInputElement).value].filter(Boolean),
                      )}
                  />
                </label>
                <label class="field">
                  <span class="lbl">${t(s, "field.state")}</span>
                  <input
                    .value=${trigger.state ?? ""}
                    @change=${(e: Event) =>
                      this._setTrigger("state", (e.target as HTMLInputElement).value || null)}
                  />
                </label>
              </div>`
            : nothing}
          ${trigger.kind === "time"
            ? this._renderDays(s, trigger.weekdays, (days) =>
                this._setTrigger("weekdays", days),
              )
            : nothing}

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "rules.action")}</span>
              <select
                @change=${(e: Event) =>
                  this._set("action", (e.target as HTMLSelectElement).value as RuleActionKind)}
              >
                ${(ctx.meta?.rule_actions ?? []).map(
                  (kind) =>
                    html`<option .value=${kind} ?selected=${kind === draft.action}>
                      ${t(s, `rules.action_kind_${kind}`)}
                    </option>`,
                )}
              </select>
            </label>
            ${draft.action === "disarm"
              ? nothing
              : html`<label class="field">
                  <span class="lbl">${t(s, "field.scenario_id")}</span>
                  <select
                    @change=${(e: Event) =>
                      this._set("scenario_id", (e.target as HTMLSelectElement).value || null)}
                  >
                    <option value="" ?selected=${!draft.scenario_id}>
                      ${t(s, "rules.choose_scenario")}
                    </option>
                    ${(ctx.config?.scenarios ?? []).map(
                      (sc) =>
                        html`<option .value=${sc.id ?? ""} ?selected=${sc.id === draft.scenario_id}>
                          ${sc.name}
                        </option>`,
                    )}
                  </select>
                </label>`}
          </div>
          ${draft.action === "disarm" ? this._renderDisarmAreas(s, draft) : nothing}

          <div class="hr"></div>
          <div class="lbl strong">${t(s, "field.window")}</div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.after")}</span>
              <input
                type="time"
                .value=${draft.window.after ?? ""}
                @change=${(e: Event) =>
                  this._setWindow("after", (e.target as HTMLInputElement).value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.before")}</span>
              <input
                type="time"
                .value=${draft.window.before ?? ""}
                @change=${(e: Event) =>
                  this._setWindow("before", (e.target as HTMLInputElement).value || null)}
              />
            </label>
          </div>
          ${this._renderDays(s, draft.window.weekdays, (days) =>
            this._setWindow("weekdays", days),
          )}
          <span class="hint">${t(s, "rules.window_hint")}</span>

          <div class="hr"></div>
          <div class="lbl strong">${t(s, "field.guards")}</div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${draft.guards.only_when_disarmed}
              @change=${(e: Event) =>
                this._setGuard("only_when_disarmed", (e.target as HTMLInputElement).checked)}
            />
            <span>${t(s, "rules.guard_disarmed")}</span>
          </label>
          <label class="check">
            <input
              type="checkbox"
              .checked=${draft.guards.only_when_ready}
              @change=${(e: Event) =>
                this._setGuard("only_when_ready", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "rules.guard_ready")}
              <span class="hint">${t(s, "rules.guard_ready_hint")}</span>
            </span>
          </label>
          <label class="field">
            <span class="lbl">${t(s, "rules.guard_quiet_label")}</span>
            <input
              type="number"
              min="1"
              max=${maxMinutes}
              .value=${draft.guards.quiet_minutes === null
                ? ""
                : String(draft.guards.quiet_minutes)}
              @input=${(e: Event) =>
                this._setGuard(
                  "quiet_minutes",
                  optionalNumber((e.target as HTMLInputElement).value),
                )}
            />
            <span class="hint">${t(s, "rules.guard_quiet_hint")}</span>
          </label>

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.grace_seconds")}</span>
              <input
                type="number"
                min="0"
                max=${maxGrace}
                .value=${String(draft.grace_seconds)}
                @input=${(e: Event) =>
                  this._set(
                    "grace_seconds",
                    optionalNumber((e.target as HTMLInputElement).value) ?? 0,
                  )}
              />
              <span class="hint">${t(s, "rules.grace_hint")}</span>
            </label>
          </div>
          <div class="block">
            <div class="lbl strong">${t(s, "field.notify_contact_ids")}</div>
            <div class="chips">
              ${(ctx.config?.contacts ?? []).map((contact) => {
                const on = draft.notify_contact_ids.includes(contact.id ?? "");
                return html`<label class="chip">
                  <input
                    type="checkbox"
                    .checked=${on}
                    @change=${(e: Event) =>
                      this._set(
                        "notify_contact_ids",
                        (e.target as HTMLInputElement).checked
                          ? [...draft.notify_contact_ids, contact.id ?? ""]
                          : draft.notify_contact_ids.filter((id) => id !== contact.id),
                      )}
                  />
                  <span>${contact.name}</span>
                </label>`;
              })}
            </div>
            <span class="hint">${t(s, "rules.notify_hint")}</span>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${draft.enabled}
              @change=${(e: Event) =>
                this._set("enabled", (e.target as HTMLInputElement).checked)}
            />
            <span>${t(s, "rules.enabled")}</span>
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

  private _renderDays(s: Strings, days: number[], set: (days: number[]) => void) {
    return html`<div class="chips days">
      ${WEEKDAYS.map((day) => {
        const on = days.includes(day);
        return html`<label class="chip">
          <input
            type="checkbox"
            .checked=${on}
            @change=${(e: Event) =>
              set(
                (e.target as HTMLInputElement).checked
                  ? [...days, day].sort((a, b) => a - b)
                  : days.filter((d) => d !== day),
              )}
          />
          <span>${t(s, `rules.weekday_${day}`)}</span>
        </label>`;
      })}
    </div>`;
  }

  /** The areas a disarm rule names. A perimeter area is offered and marked:
   * the engine takes it out whatever this screen shows (§9.4 point 3). */
  private _renderDisarmAreas(s: Strings, draft: RuleConfig) {
    const areas = this.ctx?.config?.areas ?? [];
    return html`<div class="block">
      <div class="lbl strong">${t(s, "field.area_ids")}</div>
      <div class="chips">
        ${areas.map((area) => {
          const on = draft.area_ids.includes(area.id ?? "");
          return html`<label class=${area.is_perimeter ? "chip never" : "chip"}>
            <input
              type="checkbox"
              .checked=${on}
              ?disabled=${area.is_perimeter}
              @change=${(e: Event) =>
                this._set(
                  "area_ids",
                  (e.target as HTMLInputElement).checked
                    ? [...draft.area_ids, area.id ?? ""]
                    : draft.area_ids.filter((id) => id !== area.id),
                )}
            />
            <span>
              ${area.name}
              ${area.is_perimeter
                ? html`<em>&nbsp;· ${t(s, "rules.never_disarmed")}</em>`
                : nothing}
            </span>
          </label>`;
        })}
      </div>
    </div>`;
  }

  private _renderSuspensions(s: Strings, suspensions: SuspensionConfig[]) {
    const ctx = this.ctx!;
    const rules = ctx.config?.rules ?? [];
    const draft = this._visitor;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "rules.suspensions")}</h2>
        </div>
        <div class="card-bd">
          <p class="hint">${t(s, "rules.visitor_intro")}</p>
          ${suspensions.length
            ? html`<div class="stack">
                ${suspensions.map(
                  (item) => html`<div class="suspension">
                    <div>
                      <div class="lbl strong">
                        ${item.name ?? t(s, `rules.suspension_${item.kind}`)}
                      </div>
                      <div class="hint mono">
                        ${item.kind === "next"
                          ? t(s, "rules.suspension_next_hint")
                          : `${when(item.start)} – ${when(item.until)}`}
                        ${item.rule_ids.length
                          ? ` · ${item.rule_ids
                              .map((id) => rules.find((r) => r.id === id)?.name ?? id)
                              .join(", ")}`
                          : ` · ${t(s, "rules.every_rule")}`}
                        ${item.reduced_scenario_id
                          ? ` · ${t(s, "rules.instead", {
                              scenario: this._scenarioName(item.reduced_scenario_id),
                            })}`
                          : ""}
                      </div>
                    </div>
                    <span class="spacer"></span>
                    <button
                      class="btn sm"
                      ?disabled=${this._busy}
                      @click=${() => this._run(() => ctx.liftSuspension(item.id))}
                    >
                      ${t(s, "rules.lift")}
                    </button>
                  </div>`,
                )}
              </div>`
            : html`<div class="empty">${t(s, "rules.no_suspensions")}</div>`}

          <div class="hr"></div>
          <div class="lbl strong">${t(s, "rules.visitor")}</div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "rules.reason")}</span>
              <input
                .value=${draft.name}
                placeholder=${t(s, "rules.reason_placeholder")}
                @input=${(e: Event) =>
                  (this._visitor = {
                    ...draft,
                    name: (e.target as HTMLInputElement).value,
                  })}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.after")}</span>
              <input
                type="datetime-local"
                .value=${draft.start}
                @change=${(e: Event) =>
                  (this._visitor = {
                    ...draft,
                    start: (e.target as HTMLInputElement).value,
                  })}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.before")}</span>
              <input
                type="datetime-local"
                .value=${draft.until}
                @change=${(e: Event) =>
                  (this._visitor = {
                    ...draft,
                    until: (e.target as HTMLInputElement).value,
                  })}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "rules.instead_label")}</span>
              <select
                @change=${(e: Event) =>
                  (this._visitor = {
                    ...draft,
                    reduced_scenario_id: (e.target as HTMLSelectElement).value || null,
                  })}
              >
                <option value="" ?selected=${!draft.reduced_scenario_id}>
                  ${t(s, "rules.instead_nothing")}
                </option>
                ${(ctx.config?.scenarios ?? []).map(
                  (sc) =>
                    html`<option
                      .value=${sc.id ?? ""}
                      ?selected=${sc.id === draft.reduced_scenario_id}
                    >
                      ${sc.name}
                    </option>`,
                )}
              </select>
              <span class="hint">${t(s, "rules.instead_hint")}</span>
            </label>
          </div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !draft.name.trim() || !draft.until}
              @click=${this._addVisitor}
            >
              ${t(s, "rules.add_visitor")}
            </button>
            ${(ctx.config?.rules ?? []).length
              ? html`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() =>
                    this._run(() => ctx.suspend({ kind: "next", rule_ids: [] }))}
                >
                  ${t(s, "rules.skip_next")}
                </button>`
              : nothing}
          </div>
        </div>
      </div>
    `;
  }

  /** §9.4's asymmetry, said where somebody is about to enable it. */
  private _renderDisarming(s: Strings) {
    const ctx = this.ctx!;
    const allowed = ctx.config?.settings.allow_auto_disarm ?? false;
    const areas = ctx.config?.areas ?? [];
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "rules.disarming")}</h2>
        </div>
        <div class="card-bd">
          <div class="notice">${t(s, "rules.disarming_warning")}</div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${allowed}
              ?disabled=${this._busy || !ctx.isAdmin}
              @change=${async (e: Event) => {
                const enabled = (e.target as HTMLInputElement).checked;
                this._busy = true;
                try {
                  await ctx.saveSettings({ allow_auto_disarm: enabled });
                } finally {
                  this._busy = false;
                }
              }}
            />
            <span>
              ${t(s, "rules.allow_disarm")}
              <span class="hint">${t(s, "rules.allow_disarm_hint")}</span>
            </span>
          </label>
          <div class="hr"></div>
          <div class="lbl strong">${t(s, "rules.areas_a_rule_may_disarm")}</div>
          <div class="chips">
            ${areas.map(
              (area) =>
                html`<span class=${area.is_perimeter ? "pill bad" : "pill ok"}>
                  ${area.name}${area.is_perimeter ? ` · ${t(s, "rules.never_disarmed")}` : ""}
                </span>`,
            )}
          </div>
          <p class="hint">${t(s, "rules.perimeter_note")}</p>
        </div>
      </div>
    `;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      .banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        font-size: 13.5px;
      }
      .banner.warn {
        border-color: var(--warning-color, #c77700);
      }
      .banner.crit {
        border-color: var(--error-color, #d32f2f);
      }
      .spacer {
        flex: 1;
      }
      .block {
        margin-top: 14px;
      }
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 6px 0;
      }
      label.chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 10px;
        border: 1px solid var(--divider-color);
        border-radius: 999px;
        font-size: 13px;
      }
      label.chip.never {
        opacity: 0.7;
        border-style: dashed;
      }
      label.chip em {
        color: var(--secondary-text-color);
        font-style: normal;
      }
      .lbl.strong {
        font-weight: 500;
        display: block;
        margin: 14px 0 6px;
        font-size: 13px;
      }
      .suspension {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
      }
      .stack {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .hr {
        height: 1px;
        background: var(--divider-color);
        margin: 16px 0;
        border: 0;
      }
      td.small {
        font-size: 12.5px;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-rules")) {
  customElements.define("foyer-page-rules", FoyerPageRules);
}
