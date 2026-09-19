// Page 9 — Test & diagnostics (SPEC §15.1, §11). Two tabs in part 1: the live
// zone table (§11.1) and the simulator (§11.2). The walk test and the real
// action test are part 2's, and their tabs arrive with them rather than
// sitting here doing nothing.
//
// Both tabs only read. Neither can change a thing in the house, and the
// simulator cannot even by accident: the backend calls the same decide() the
// runtime calls and never hands the Decision to the executor (INV-1). The
// banner on the tab says so, because a page that looks like it might fire the
// siren is a page nobody presses the button on.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  Diagnostics,
  DiagnosticsDevice,
  DiagnosticsZone,
  Simulation,
  SimulationQuery,
  TraceAction,
  TraceBatch,
  TraceStep,
} from "../../shared/types";
import type { PanelContext } from "../context";

type Tab = "diagnostics" | "simulator";

const TABS: Tab[] = ["diagnostics", "simulator"];

// Moments where a profile running nothing is itself the answer: the alarm of
// a zone, the entry it opens, a satisfied group, a technical alarm. Anywhere
// else, silence is simply how the configuration is and needs no line.
const ANSWERABLE = new Set([
  "triggered",
  "entry_started",
  "verification_satisfied",
  "technical_raised",
]);

/** A forced zone, as the operator is building it up. */
interface Override {
  zone_id: string;
  state: string;
  at: number;
}

/** What a zone's entity has to be in for Foyer to count it as triggered.
 * Offered as the obvious choice rather than imposed: the field stays free
 * text, because a zone may declare any state at all (INV-5). */
function triggerStates(ctx: PanelContext, zoneId: string): string[] {
  const zone = ctx.config?.zones.find((z) => z.id === zoneId);
  if (!zone) return [];
  return zone.trigger.kind === "state" ? zone.trigger.states : [];
}

/** Every entity an action's condition reads (§6.3). These are what the
 * simulator lets you override, and the list is exactly the configuration's:
 * offering every entity in Home Assistant would bury the three that matter. */
function conditionEntities(ctx: PanelContext): string[] {
  const seen = new Set<string>();
  for (const profile of ctx.config?.profiles ?? []) {
    for (const action of profile.actions) {
      for (const condition of action.conditions) {
        if (condition.kind === "state") seen.add(condition.entity_id);
      }
    }
  }
  return [...seen].sort();
}

function hhmm(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

class FoyerPageTest extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _tab: { state: true },
    _diagnostics: { state: true },
    _simulation: { state: true },
    _busy: { state: true },
    _error: { state: true },
    _scenario: { state: true },
    _start: { state: true },
    _overrides: { state: true },
    _entities: { state: true },
  };

  ctx?: PanelContext;
  private _tab: Tab = "diagnostics";
  private _diagnostics?: Diagnostics;
  private _simulation?: Simulation;
  private _busy = false;
  private _error?: string;
  private _scenario = "";
  private _start = "";
  private _overrides: Override[] = [];
  private _entities: Record<string, string> = {};
  private _loaded = false;
  private _mentioned = new Set<string>();

  override updated(): void {
    if (!this._loaded && this.ctx) {
      this._loaded = true;
      void this._refresh();
    }
  }

  private async _refresh(): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    this._error = undefined;
    try {
      this._diagnostics = await this.ctx.diagnostics();
    } catch (err) {
      this._diagnostics = undefined;
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  private async _run(): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    this._error = undefined;
    const query: SimulationQuery = {
      scenario_id: this._scenario || null,
      start: this._start ? new Date(this._start).toISOString() : null,
      zones: this._overrides.filter((o) => o.zone_id && o.state),
      entities: this._entities,
    };
    try {
      this._simulation = await this.ctx.simulate(query);
    } catch (err) {
      this._simulation = undefined;
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx) return nothing;
    const s = ctx.strings;
    return html`
      <nav class="subtabs" role="tablist">
        ${TABS.map(
          (tab) => html`
            <button
              role="tab"
              aria-selected=${tab === this._tab ? "true" : "false"}
              @click=${() => (this._tab = tab)}
            >
              ${t(s, `test.tab.${tab}`)}
            </button>
          `,
        )}
      </nav>
      ${this._error
        ? html`<div class="problems" role="alert">${this._error}</div>`
        : nothing}
      ${this._tab === "diagnostics"
        ? this._renderDiagnostics(s)
        : this._renderSimulator(s)}
    `;
  }

  // --- tab 1: live zone diagnostics (§11.1) ----------------------------------------

  private _renderDiagnostics(s: Strings) {
    const data = this._diagnostics;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "test.diagnostics.title")}</h2>
          <span class="hint">${t(s, "test.diagnostics.subtitle")}</span>
          <button class="btn" ?disabled=${this._busy} @click=${() => void this._refresh()}>
            ${t(s, "test.refresh")}
          </button>
        </div>
        <div class="card-bd">
          ${data?.missing_entities.length
            ? html`<div class="problems" role="alert">
                <p>${t(s, "test.diagnostics.missing")}</p>
                <ul>
                  ${data.missing_entities.map(
                    (entity) => html`<li class="mono">${entity}</li>`,
                  )}
                </ul>
              </div>`
            : nothing}
          ${!data
            ? html`<p class="hint">${t(s, "common.loading")}</p>`
            : data.zones.length === 0
              ? html`<p class="empty">${t(s, "test.diagnostics.empty")}</p>`
              : html`<div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>${t(s, "test.col.zone")}</th>
                        <th>${t(s, "test.col.entity")}</th>
                        <th>${t(s, "test.col.state")}</th>
                        <th>${t(s, "test.col.evaluation")}</th>
                        <th>${t(s, "test.col.last_change")}</th>
                        <th>${t(s, "test.col.health")}</th>
                        <th>${t(s, "test.col.battery")}</th>
                        <th>${t(s, "test.col.signal")}</th>
                        <th>${t(s, "test.col.supervision")}</th>
                        <th>${t(s, "test.col.arming")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${data.zones.map((zone) => this._renderZoneRow(s, zone))}
                    </tbody>
                  </table>
                </div>`}
        </div>
      </div>
      ${data && data.devices.length ? this._renderDevices(s, data.devices) : nothing}
    `;
  }

  private _renderZoneRow(s: Strings, zone: DiagnosticsZone) {
    const areaName =
      this.ctx?.status.areas.find((a) => a.id === zone.area_id)?.name ?? "";
    return html`
      <tr>
        <td>
          <strong>${zone.name}</strong>
          ${areaName ? html`<div class="hint">${areaName}</div>` : nothing}
        </td>
        <td class="mono">${zone.entity_id}</td>
        <td>
          ${zone.state === null
            ? html`<span class="state fault">${t(s, "test.no_entity")}</span>`
            : html`<span class="mono">${zone.state}</span>`}
        </td>
        <td>
          ${zone.momentary
            ? html`<span class="muted">${t(s, "test.momentary")}</span>`
            : html`<span class="state ${zone.triggered ? "open" : "closed"}">
                ${t(s, zone.triggered ? "test.would_trigger" : "test.would_not")}
              </span>`}
        </td>
        <td class="mono">
          ${zone.last_changed ? hhmm(zone.last_changed) : "—"}
        </td>
        <td>
          ${!zone.enabled
            ? html`<span class="state disabled">${t(s, "test.disabled")}</span>`
            : zone.fault
              ? html`<span class="state fault">${t(s, `fault.${zone.fault}`)}</span>`
              : html`<span class="state closed">${t(s, "test.ok")}</span>`}
        </td>
        <td>${this._renderBattery(s, zone)}</td>
        <td class="mono">
          ${zone.signal
            ? `${zone.signal.value} ${t(s, `test.unit.${zone.signal.unit}`)}`
            : "—"}
        </td>
        <td class="hint">
          ${zone.supervision_timeout === null
            ? t(s, "test.supervision_off")
            : t(s, "test.supervision_on", { n: zone.supervision_timeout })}
        </td>
        <td>
          ${zone.bypassed
            ? html`<span class="state bypassed">${t(s, `bypass.${zone.bypassed}`)}</span>`
            : zone.blocks_arming
              ? html`<span class="state fault"
                  >${t(s, `test.blocks.${zone.blocks_because}`)}</span
                >`
              : html`<span class="muted">—</span>`}
        </td>
      </tr>
    `;
  }

  private _renderBattery(s: Strings, zone: DiagnosticsZone) {
    if (!zone.battery_entity_id) return html`<span class="muted">—</span>`;
    // A battery binary_sensor has no number to show, only the flag beside it.
    const label =
      zone.battery_level === null ? "" : `${Math.round(zone.battery_level)} %`;
    return html`
      <span class="state ${zone.battery_low ? "open" : "closed"}">
        ${label || t(s, zone.battery_low ? "test.battery_low" : "test.battery_ok")}
      </span>
    `;
  }

  private _renderDevices(s: Strings, devices: DiagnosticsDevice[]) {
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "test.devices.title")}</h2>
          <span class="hint">${t(s, "test.devices.subtitle")}</span>
        </div>
        <div class="card-bd">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${t(s, "test.col.device")}</th>
                  <th>${t(s, "test.col.kind")}</th>
                  <th>${t(s, "test.col.entity")}</th>
                  <th>${t(s, "test.col.state")}</th>
                  <th>${t(s, "test.col.last_change")}</th>
                  <th>${t(s, "test.col.health")}</th>
                </tr>
              </thead>
              <tbody>
                ${devices.map(
                  (device) => html`
                    <tr>
                      <td><strong>${device.name}</strong></td>
                      <td>${t(s, `device_kind.${device.kind}`)}</td>
                      <td class="mono">${device.entity_id ?? "—"}</td>
                      <td class="mono">${device.state ?? "—"}</td>
                      <td class="mono">
                        ${device.last_changed ? hhmm(device.last_changed) : "—"}
                      </td>
                      <td>
                        ${!device.enabled
                          ? html`<span class="state disabled"
                              >${t(s, "test.disabled")}</span
                            >`
                          : !device.watchable
                            ? html`<span class="muted">${t(s, "test.no_entity_kind")}</span>`
                            : device.available
                              ? html`<span class="state closed">${t(s, "test.ok")}</span>`
                              : html`<span class="state fault"
                                  >${t(s, "fault.unavailable")}</span
                                >`}
                      </td>
                    </tr>
                  `,
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  // --- tab 2: the simulator (§11.2) ------------------------------------------------

  private _renderSimulator(s: Strings) {
    const ctx = this.ctx!;
    return html`
      <div class="notice info">
        <strong>${t(s, "test.simulator.safe_title")}</strong>
        ${t(s, "test.simulator.safe")}
      </div>
      <div class="split">
        <div class="card">
          <div class="card-hd">
            <h2>${t(s, "test.simulator.conditions")}</h2>
          </div>
          <div class="card-bd">
            <div class="grid-form">
              <label class="field">
                <span class="lbl">${t(s, "test.simulator.scenario")}</span>
                <select
                  .value=${this._scenario}
                  @change=${(e: Event) =>
                    (this._scenario = (e.target as HTMLSelectElement).value)}
                >
                  <option value="">${t(s, "test.simulator.disarmed")}</option>
                  ${ctx.status.scenarios.map(
                    (scenario) => html`<option
                      .value=${scenario.id}
                      ?selected=${scenario.id === this._scenario}
                    >
                      ${scenario.name}
                    </option>`,
                  )}
                </select>
                <span class="hint">${t(s, "test.simulator.scenario_hint")}</span>
              </label>
              <label class="field">
                <span class="lbl">${t(s, "test.simulator.clock")}</span>
                <input
                  type="datetime-local"
                  .value=${this._start}
                  @change=${(e: Event) =>
                    (this._start = (e.target as HTMLInputElement).value)}
                />
                <span class="hint">${t(s, "test.simulator.clock_hint")}</span>
              </label>
            </div>
            ${this._renderOverrides(s)} ${this._renderEntityOverrides(s)}
            <div class="actions">
              <button
                class="btn primary"
                ?disabled=${this._busy}
                @click=${() => void this._run()}
              >
                ${t(s, "test.simulator.run")}
              </button>
              <button
                class="btn"
                @click=${() => {
                  this._overrides = [];
                  this._entities = {};
                  this._simulation = undefined;
                  this._start = "";
                }}
              >
                ${t(s, "test.simulator.reset")}
              </button>
            </div>
          </div>
        </div>
        ${this._renderTrace(s)}
      </div>
    `;
  }

  private _renderOverrides(s: Strings) {
    const ctx = this.ctx!;
    return html`
      <fieldset>
        <legend>${t(s, "test.simulator.zones")}</legend>
        <p class="hint">${t(s, "test.simulator.zones_hint")}</p>
        ${this._overrides.map(
          (override, index) => html`
            <div class="override">
              <select
                @change=${(e: Event) =>
                  this._setOverride(index, {
                    zone_id: (e.target as HTMLSelectElement).value,
                    state:
                      triggerStates(ctx, (e.target as HTMLSelectElement).value)[0] ??
                      override.state,
                  })}
              >
                <option value="">${t(s, "test.simulator.pick_zone")}</option>
                ${ctx.status.zones.map(
                  (zone) => html`<option
                    .value=${zone.id}
                    ?selected=${zone.id === override.zone_id}
                  >
                    ${zone.name}
                  </option>`,
                )}
              </select>
              <input
                class="state-input"
                .value=${override.state}
                list="foyer-sim-states-${index}"
                placeholder=${t(s, "test.simulator.state")}
                @change=${(e: Event) =>
                  this._setOverride(index, {
                    state: (e.target as HTMLInputElement).value,
                  })}
              />
              <datalist id="foyer-sim-states-${index}">
                ${triggerStates(ctx, override.zone_id).map(
                  (state) => html`<option .value=${state}></option>`,
                )}
              </datalist>
              <input
                class="at-input"
                type="number"
                min="0"
                .value=${String(override.at)}
                title=${t(s, "test.simulator.at")}
                @change=${(e: Event) =>
                  this._setOverride(index, {
                    at: Number((e.target as HTMLInputElement).value) || 0,
                  })}
              />
              <span class="hint">${t(s, "test.simulator.seconds")}</span>
              <button
                class="btn small"
                @click=${() =>
                  (this._overrides = this._overrides.filter((_, i) => i !== index))}
              >
                ${t(s, "common.delete")}
              </button>
            </div>
          `,
        )}
        <button
          class="btn small"
          @click=${() =>
            (this._overrides = [
              ...this._overrides,
              { zone_id: "", state: "on", at: 0 },
            ])}
        >
          ${t(s, "test.simulator.add_zone")}
        </button>
      </fieldset>
    `;
  }

  private _renderEntityOverrides(s: Strings) {
    const entities = conditionEntities(this.ctx!);
    if (!entities.length) return nothing;
    return html`
      <fieldset>
        <legend>${t(s, "test.simulator.entities")}</legend>
        <p class="hint">${t(s, "test.simulator.entities_hint")}</p>
        <div class="grid-form">
          ${entities.map(
            (entity) => html`
              <label class="field">
                <span class="lbl mono">${entity}</span>
                <input
                  .value=${this._entities[entity] ?? ""}
                  placeholder=${t(s, "test.simulator.as_now")}
                  @change=${(e: Event) => {
                    const value = (e.target as HTMLInputElement).value;
                    const next = { ...this._entities };
                    if (value) next[entity] = value;
                    else delete next[entity];
                    this._entities = next;
                  }}
                />
              </label>
            `,
          )}
        </div>
      </fieldset>
    `;
  }

  private _setOverride(index: number, changes: Partial<Override>): void {
    this._overrides = this._overrides.map((o, i) =>
      i === index ? { ...o, ...changes } : o,
    );
  }

  // --- the trace ------------------------------------------------------------------

  private _renderTrace(s: Strings) {
    const simulation = this._simulation;
    this._mentioned = new Set();
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "test.trace.title")}</h2>
          <span class="hint">${t(s, "test.trace.subtitle")}</span>
        </div>
        <div class="card-bd">
          ${!simulation
            ? html`<p class="empty">
                ${t(s, this._busy ? "common.loading" : "test.trace.empty")}
              </p>`
            : html`
                <ol class="trace">
                  ${simulation.steps
                    .filter((step) => this._worthShowing(step))
                    .map((step) => this._renderStep(s, step))}
                </ol>
                ${simulation.truncated
                  ? html`<p class="notice">${t(s, "test.trace.truncated")}</p>`
                  : nothing}
              `}
        </div>
      </div>
    `;
  }

  /** A tick that decided nothing and changed nothing is noise. The setup
   * tick is always one of those by construction: it reads the world once so
   * every zone has a baseline, which is not part of the answer.
   *
   * A zone the operator forced is never noise, even when nothing followed
   * from it: "I opened that window and the house did nothing" is the answer
   * this page exists to give, and a trace that silently dropped the line
   * would look as though the override had not been applied. */
  private _worthShowing(step: TraceStep): boolean {
    if (step.kind === "setup") return false;
    if (step.kind === "zone") return true;
    return (
      !step.accepted ||
      step.occurrences.length > 0 ||
      step.areas.length > 0 ||
      step.loose_actions.length > 0
    );
  }

  private _renderStep(s: Strings, step: TraceStep) {
    const ctx = this.ctx!;
    const zoneName = step.zone_id
      ? (ctx.status.zones.find((z) => z.id === step.zone_id)?.name ?? step.zone_id)
      : "";
    return html`
      <li class="step">
        <div class="when mono">${hhmm(step.at)}</div>
        <div class="what">
          ${step.kind === "zone"
            ? html`<div>
                ${t(s, "test.trace.zone", { zone: zoneName })}
                <span class="mono">${step.zone_state}</span>
              </div>`
            : nothing}
          ${!step.accepted
            ? html`<div class="no">
                ${t(s, `reason.${step.reason ?? "unknown"}`, {
                  zones: step.blocking_zones
                    .map(
                      (id) =>
                        ctx.status.zones.find((z) => z.id === id)?.name ?? id,
                    )
                    .join(", "),
                })}
              </div>`
            : nothing}
          ${step.low_battery_zones.length
            ? html`<div class="warn">
                ${t(s, "test.trace.low_battery", {
                  zones: step.low_battery_zones
                    .map(
                      (id) =>
                        ctx.status.zones.find((z) => z.id === id)?.name ?? id,
                    )
                    .join(", "),
                })}
              </div>`
            : nothing}
          ${step.areas.map(
            (change) => html`
              <div class="key">
                ${t(s, "test.trace.area", {
                  area:
                    ctx.status.areas.find((a) => a.id === change.area_id)?.name ??
                    change.area_id,
                  was: t(s, `state.${change.was}`),
                  now: t(s, `state.${change.now}`),
                })}
                ${change.timer_due
                  ? html`<span class="muted">
                      ${t(s, "test.trace.timer", {
                        kind: t(s, `test.timer.${change.timer_kind}`),
                        at: hhmm(change.timer_due),
                      })}
                    </span>`
                  : nothing}
              </div>
            `,
          )}
          ${step.occurrences.map((occurrence) => this._renderOccurrence(s, occurrence))}
          ${this._renderBatches(s, step)}
          ${step.loose_actions.map(
            (action) => html`<div class="yes">
              ${t(s, "test.trace.ran", { action: t(s, `action_kind.${action.kind}`) })}
            </div>`,
          )}
          ${step.scheduled
            .filter((item) => item.kind === "delay" || item.kind === "siren")
            .filter((item) => this._firstMention(item))
            .map(
              (item) => html`<div class="wait">
                ${t(s, `test.trace.later.${item.kind}`, { at: hhmm(item.at) })}
              </div>`,
            )}
        </div>
      </li>
    `;
  }

  /** A siren cutoff is scheduled once and stays scheduled; saying so again
   * on every later step is how a trace teaches people to skip its own
   * warnings. Reset whenever a new run is rendered. */
  private _firstMention(item: { kind: string; at: string; area_id: string | null }): boolean {
    const key = `${item.kind}|${item.at}|${item.area_id ?? ""}`;
    if (this._mentioned.has(key)) return false;
    this._mentioned.add(key);
    return true;
  }

  private _renderOccurrence(s: Strings, occurrence: TraceStep["occurrences"][0]) {
    const ctx = this.ctx!;
    // A verification window carries its own arithmetic (§4.8): the trace must
    // show group state, not just the zone.
    if (occurrence.detail.verification) {
      const group = ctx.config?.groups.find((g) => g.id === occurrence.group_id);
      return html`<div class="key">
        ${t(
          s,
          occurrence.moment === "verification_satisfied"
            ? "test.trace.group_satisfied"
            : "test.trace.group",
          {
            group: group?.name ?? t(s, "test.trace.cross_zone"),
            count: occurrence.detail.count,
            n: occurrence.detail.n,
            window: occurrence.detail.window,
          },
        )}
      </div>`;
    }
    if (occurrence.moment.startsWith("incident_")) {
      return html`<div class="key">
        ${t(s, `moment.${occurrence.moment}`)}
        <span class="mono">${occurrence.incident_id ?? ""}</span>
      </div>`;
    }
    return html`<div class="key">${t(s, `moment.${occurrence.moment}`)}</div>`;
  }

  /** Which profiles are worth a line. §6 requires the effective profile and
   * where it came from to be shown — but a bookkeeping moment that no
   * profile was ever going to answer would put three empty lines under every
   * trigger, and a trace people skim is a trace people stop reading.
   *
   * So: a profile that runs something is always named, and a profile that
   * runs nothing is named only at the moments where running nothing is a
   * finding. "The group was satisfied and its profile did nothing" is the
   * answer to why the siren stayed quiet. */
  private _renderBatches(s: Strings, step: TraceStep) {
    const worth = step.batches.filter(
      (b) => b.actions.length > 0 || ANSWERABLE.has(b.moment),
    );
    return html`${worth.map((batch) => this._renderBatch(s, batch))}`;
  }

  private _renderBatch(s: Strings, batch: TraceBatch) {
    if (!batch.profile_id) {
      return html`<div class="no">${t(s, "test.trace.no_profile")}</div>`;
    }
    return html`
      <div class="batch">
        <div class="key">
          ${t(s, "test.trace.profile", {
            profile: batch.profile_name,
            source: t(s, `test.source.${batch.source}`),
          })}
        </div>
        ${batch.actions.length
          ? batch.actions.map((action) => this._renderAction(s, action))
          : html`<div class="no">${t(s, "test.trace.nothing_configured")}</div>`}
      </div>
    `;
  }

  private _renderAction(s: Strings, action: TraceAction) {
    const name = action.name || t(s, `action_kind.${action.kind}`);
    if (action.ran) {
      return html`<div class="yes">${t(s, "test.trace.ran", { action: name })}</div>`;
    }
    // "Skipped AND WHY", well enough to act on (§11.2). A condition names
    // itself; everything else has one sentence that says the whole reason.
    const why =
      action.skipped === "condition"
        ? t(s, "test.skip.condition", { conditions: action.conditions.join(", ") })
        : t(s, `test.skip.${action.skipped}`);
    const held = action.skipped === "held_by_delay";
    return html`<div class=${held ? "wait" : "no"}>
      ${t(s, "test.trace.skipped", { action: name, why })}
    </div>`;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      :host {
        display: block;
      }
      .subtabs {
        display: flex;
        gap: 4px;
        margin-bottom: 16px;
        border-bottom: 1px solid var(--divider-color);
        overflow-x: auto;
      }
      .subtabs button {
        font: inherit;
        font-size: 14px;
        background: none;
        border: none;
        border-bottom: 2px solid transparent;
        color: var(--secondary-text-color);
        padding: 8px 14px;
        cursor: pointer;
        white-space: nowrap;
      }
      .subtabs button[aria-selected="true"] {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color);
      }
      .notice.info {
        border-left-color: var(--info-color, #0277bd);
        margin: 0 0 16px;
      }
      .split {
        display: grid;
        gap: 16px;
        grid-template-columns: minmax(280px, 380px) 1fr;
        align-items: start;
      }
      @media (max-width: 900px) {
        .split {
          grid-template-columns: 1fr;
        }
      }
      .override {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .override select {
        flex: 1 1 140px;
      }
      .state-input {
        flex: 0 1 90px;
      }
      .at-input {
        flex: 0 0 76px;
      }
      ol.trace {
        list-style: none;
        margin: 0;
        padding: 0;
        font-size: 13.5px;
      }
      li.step {
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      li.step:last-child {
        border-bottom: none;
      }
      .when {
        color: var(--secondary-text-color);
        padding-top: 1px;
      }
      .what > div {
        margin-bottom: 2px;
      }
      .batch {
        margin: 6px 0 6px 0;
        padding-left: 10px;
        border-left: 2px solid var(--divider-color);
      }
      .key {
        color: var(--secondary-text-color);
      }
      .yes {
        color: var(--success-color, #2e9e4f);
      }
      .no {
        color: var(--error-color, #d32f2f);
      }
      .wait,
      .warn {
        color: var(--warning-color, #c77700);
      }
      td .hint {
        font-weight: 400;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-test")) {
  customElements.define("foyer-page-test", FoyerPageTest);
}