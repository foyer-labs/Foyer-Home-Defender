// Page 9 — Test & diagnostics (SPEC §15.1, §11). Four tabs, and the division
// that matters is not what they show but what they do.
//
// The first two only read: the live zone table (§11.1) and the simulator
// (§11.2). Neither can change a thing in the house, and the simulator cannot
// even by accident — the backend calls the same decide() the runtime calls and
// never hands the Decision to the executor (INV-1). The banner on that tab
// says so, because a page that looks like it might fire the siren is a page
// nobody presses the button on.
//
// The last two are writes, and their banners say the opposite. The walk test
// (§11.3) really arms the house and really holds the response back; the action
// test (§11.4) really sounds the siren. Both are gated accordingly —
// `walk_test` and `test_actions`, each with a code — and both say plainly what
// they are about to do.
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { inHouseZone } from "../../shared/time";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  Diagnostics,
  DiagnosticsDevice,
  DiagnosticsZone,
  ActionConfig,
  ProfileConfig,
  Simulation,
  SimulationQuery,
  WalkTestStatus,
  TraceAction,
  TraceBatch,
  TraceStep,
} from "../../shared/types";
import { reasonText, type PanelContext } from "../context";

type Tab = "diagnostics" | "simulator" | "walktest" | "actiontest";

const TABS: Tab[] = ["diagnostics", "simulator", "walktest", "actiontest"];

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

/** Every entity the configuration reads and the simulator can therefore be
 * asked about: an action's conditions (§6.3) and the people an automatic
 * rule watches (§9.4). The list is exactly the configuration's — offering
 * every entity in Home Assistant would bury the three that matter — and
 * without the rules in it, "would it arm tomorrow with everybody out?" is a
 * question the page cannot ask. */
function conditionEntities(ctx: PanelContext): string[] {
  const seen = new Set<string>();
  for (const profile of ctx.config?.profiles ?? []) {
    for (const action of profile.actions) {
      for (const condition of action.conditions) {
        if (condition.kind === "state") seen.add(condition.entity_id);
      }
    }
  }
  for (const rule of ctx.config?.rules ?? []) {
    if (!rule.enabled) continue;
    for (const entityId of rule.trigger.entity_ids) seen.add(entityId);
  }
  return [...seen].sort();
}

/** The language is the Home Assistant user's, not the browser's (found in
 * review): every other page on this panel follows the first. */
function hhmm(
  iso: string,
  language?: string,
  hass?: { config?: { time_zone?: string } },
): string {
  const date = new Date(iso);
  return date.toLocaleTimeString(
    language,
    inHouseZone(hass, { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
  );
}

class FoyerPageTest extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _tab: { state: true },
    _diagnostics: { state: true },
    _simulation: { state: true },
    _busy: { state: true },
    _error: { state: true },
    _notice: { state: true },
    _scenario: { state: true },
    _start: { state: true },
    _overrides: { state: true },
    _entities: { state: true },
    _code: { state: true },
    _codeWanted: { state: true },
    _walkDuration: { state: true },
    _tested: { state: true },
    _confirming: { state: true },
  };

  ctx?: PanelContext;
  private _tab: Tab = "diagnostics";
  private _diagnostics?: Diagnostics;
  private _simulation?: Simulation;
  private _busy = false;
  private _error?: string;
  private _notice?: string;
  private _walkWasOn = false;

  override willUpdate(): void {
    // The note about areas left out of a walk test is about that test: once
    // it has ended, by the banner or by its timeout, it is no longer true.
    const on = Boolean(this.ctx?.status.walk_test);
    if (this._walkWasOn && !on) this._notice = undefined;
    this._walkWasOn = on;
  }
  private _scenario = "";
  private _start = "";
  private _overrides: Override[] = [];
  private _entities: Record<string, string> = {};
  private _code = "";
  private _codeWanted = false;
  private _loaded = false;
  private _mentioned = new Set<string>();
  private _walkDuration = "";
  private _tested: Record<string, { ok: boolean; at: number; error?: string }> = {};
  private _confirming?: { profile_id: string; action_id: string; name: string };

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
    this._codeWanted = false;
    const query: SimulationQuery = {
      scenario_id: this._scenario || null,
      // As typed, without a zone: the backend reads it in the house's time
      // zone, which is the one the trace is shown in.
      start: this._start || null,
      zones: this._overrides.filter((o) => o.zone_id && o.state),
      entities: this._entities,
      code: this._code || undefined,
    };
    try {
      this._simulation = await this.ctx.simulate(query);
      // Used, and not kept: a code that proved what it had to stays out of
      // memory for the rest of the visit (second review).
      this._code = "";
    } catch (err) {
      // A wrong code fails the command outright, before the run starts, so
      // it never reaches the trace. It is still the same question the trace
      // would have asked, and it gets the same answer on the page.
      const code = (err as { code?: string })?.code;
      this._codeWanted = code === "bad_code" || code === "code_required";
      this._simulation = undefined;
      // A wrong code is not offered back for another try.
      if (code === "bad_code") this._code = "";
      this._error = this._codeWanted
        ? undefined
        : String((err as { message?: string })?.message ?? err);
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
              @click=${() => {
                this._tab = tab;
                // An answer belongs to the tab that asked for it.
                this._error = undefined;
                this._notice = undefined;
              }}
            >
              ${t(s, `test.tab.${tab}`)}
            </button>
          `,
        )}
      </nav>
      ${this._error
        ? html`<div class="problems" role="alert">${this._error}</div>`
        : nothing}
      ${this._notice && this._tab === "walktest"
        ? html`<div class="notice" role="status">${this._notice}</div>`
        : nothing}
      ${this._tab === "diagnostics"
        ? this._renderDiagnostics(s)
        : this._tab === "simulator"
          ? this._renderSimulator(s)
          : this._tab === "walktest"
            ? this._renderWalkTest(s)
            : this._renderActionTest(s)}
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
          ${zone.last_changed ? hhmm(zone.last_changed, this.ctx?.hass.language, this.ctx?.hass) : "—"}
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
                        ${device.last_changed ? hhmm(device.last_changed, this.ctx?.hass.language, this.ctx?.hass) : "—"}
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
                      .selected=${live(scenario.id === this._scenario)}
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
                  this._code = "";
                  this._codeWanted = false;
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
                aria-label=${t(s, "test.simulator.pick_zone")}
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
                    .selected=${live(zone.id === override.zone_id)}
                  >
                    ${zone.name}
                  </option>`,
                )}
              </select>
              <input
                class="state-input"
                aria-label=${t(s, "test.simulator.state")}
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
                aria-label=${t(s, "test.simulator.at")}
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
          ${this._premiseNeedsCode(simulation) ? this._renderCodePrompt(s) : nothing}
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

  /** Whether the run never got off the ground because the house asks for a
   * code to arm (§8.2). The code policy is not suspended for a rehearsal —
   * inventing an exemption would be a second authorisation path — so the
   * page asks, the way every other page asks. */
  private _premiseNeedsCode(simulation?: Simulation): boolean {
    if (this._codeWanted) return true;
    const first = simulation?.steps.find((step) => step.kind === "request");
    return (
      !!first &&
      !first.accepted &&
      (first.reason === "code_required" || first.reason === "bad_code")
    );
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

  private _renderCodePrompt(s: Strings) {
    return html`
      <div class="notice">
        <p>${t(s, "test.simulator.premise_code")}</p>
        <input
          type="password"
          inputmode="numeric"
          autocomplete="off"
          aria-label=${t(s, "test.simulator.premise_code")}
          .value=${this._code}
          @change=${(e: Event) => (this._code = (e.target as HTMLInputElement).value)}
        />
        <div class="actions">
          <button
            class="btn primary"
            ?disabled=${this._busy}
            @click=${() => void this._run()}
          >
            ${t(s, "test.simulator.run")}
          </button>
        </div>
      </div>
    `;
  }

  private _renderStep(s: Strings, step: TraceStep) {
    const ctx = this.ctx!;
    const zoneName = step.zone_id
      ? (ctx.status.zones.find((z) => z.id === step.zone_id)?.name ?? step.zone_id)
      : "";
    return html`
      <li class="step">
        <div class="when mono">${hhmm(step.at, this.ctx?.hass.language, this.ctx?.hass)}</div>
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
                        at: hhmm(change.timer_due, this.ctx?.hass.language, this.ctx?.hass),
                      })}
                    </span>`
                  : nothing}
              </div>
            `,
          )}
          ${step.occurrences.map((occurrence) => this._renderOccurrence(s, occurrence))}
          ${this._renderBatches(s, step)}
          ${step.loose_actions.map((action) =>
            action.escalation
              ? html`<div class="yes">
                  ${t(s, "test.trace.escalation_sent", {
                    step: String(action.escalation_step ?? 0),
                    who: this._whoFor(action.recipients),
                  })}
                  ${this._renderCameras(s, action)}
                </div>`
              : html`<div class="yes">
                  ${t(s, "test.trace.ran", {
                    action: t(s, `action_kind.${action.kind}`),
                  })}
                </div>`,
          )}
          ${step.scheduled
            .filter((item) => item.kind === "delay" || item.kind === "siren")
            .filter((item) => this._firstMention(item))
            .map(
              (item) => html`<div class="wait">
                ${t(s, `test.trace.later.${item.kind}`, { at: hhmm(item.at, this.ctx?.hass.language, this.ctx?.hass) })}
              </div>`,
            )}
          ${step.scheduled
            .filter((item) => item.kind === "escalation_step")
            .map(
              (item) => html`<div class="wait">
                ${t(s, "test.trace.later.escalation_step", {
                  step: String(item.step ?? 0),
                  offset: String(item.offset ?? 0),
                  who: this._whoAhead(item.contact_ids, item.channel_ids),
                })}
              </div>`,
            )}
        </div>
      </li>
    `;
  }

  /** Who an escalation step reached, or will reach. The backend sends
   * identifiers and this page writes the words (§15.2). */
  private _whoFor(recipients: TraceAction["recipients"]): string {
    const contacts = this.ctx?.config?.contacts ?? [];
    return recipients
      .map((recipient) => {
        const contact = contacts.find((c) => c.id === recipient.contact_id);
        const kind = t(this.ctx!.strings, `channel_kind.${recipient.kind}`);
        return `${contact?.name ?? recipient.contact_id} (${kind})`;
      })
      .join(", ");
  }

  private _whoAhead(contactIds: string[], channelIds: string[]): string {
    const contacts = this.ctx?.config?.contacts ?? [];
    return contactIds
      .map((id, index) => {
        const contact = contacts.find((c) => c.id === id);
        const channel = contact?.channels.find((c) => c.id === channelIds[index]);
        const kind = channel
          ? ` (${t(this.ctx!.strings, `channel_kind.${channel.kind}`)})`
          : "";
        return `${contact?.name ?? id}${kind}`;
      })
      .join(", ");
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
      // A cross-zone pair is a derived 2-of-2 group whose id says so
      // (core/verification.cross_zone_id). Telling the two apart by whether
      // the configuration happens to be loaded would label a real group as a
      // pair for anyone who may not read the configuration.
      const pair = occurrence.group_id?.startsWith("cross:") ?? true;
      const group = ctx.config?.groups.find((g) => g.id === occurrence.group_id);
      return html`<div class="key">
        ${t(
          s,
          occurrence.moment === "verification_satisfied"
            ? "test.trace.group_satisfied"
            : "test.trace.group",
          {
            group:
              group?.name ??
              (pair ? t(s, "test.trace.cross_zone") : t(s, "test.trace.a_group")),
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

  // Which cameras a notification would have carried (§6.2.1): named, and
  // never fetched — the simulator takes a picture of nothing.
  private _renderCameras(s: Strings, action: TraceAction) {
    const cameras = action.cameras ?? [];
    if (!cameras.length) return nothing;
    const name = (id: string) =>
      (this.ctx?.hass.states[id]?.attributes?.friendly_name as string | undefined) ?? id;
    return html`<span class="muted">
      ${t(s, "test.trace.cameras", { cameras: cameras.map(name).join(", ") })}
      ${action.cameras_omitted
        ? t(s, "test.trace.cameras_omitted", { count: String(action.cameras_omitted) })
        : nothing}
    </span>`;
  }

  private _renderAction(s: Strings, action: TraceAction) {
    const name = action.name || t(s, `action_kind.${action.kind}`);
    if (action.ran) {
      return html`<div class="yes">
        ${t(s, "test.trace.ran", { action: name })}
        ${this._renderCameras(s, action)}
        ${action.recipients.length
          ? html`<span class="muted">
              ${t(s, "test.trace.reached", { who: this._whoFor(action.recipients) })}
            </span>`
          : nothing}
        ${action.quiet.length
          ? html`<span class="muted">
              ${t(s, "test.trace.quiet", {
                who: action.quiet
                  .map(
                    (id) =>
                      (this.ctx?.config?.contacts ?? []).find((c) => c.id === id)
                        ?.name ?? id,
                  )
                  .join(", "),
              })}
            </span>`
          : nothing}
      </div>`;
    }
    // "Skipped AND WHY", well enough to act on (§11.2). A condition names
    // itself; everything else has one sentence that says the whole reason.
    const why =
      action.skipped === "condition"
        ? t(s, "test.skip.condition", {
            conditions: action.conditions
              .map((condition) =>
                condition.kind === "time"
                  ? t(s, "test.condition.time", condition)
                  : t(s, "test.condition.state", {
                      entity_id: condition.entity_id,
                      operator: t(s, `condition.${condition.operator}`),
                      state: condition.state,
                    }),
              )
              .join(", "),
          })
        : t(s, `test.skip.${action.skipped}`);
    const held = action.skipped === "held_by_delay";
    return html`<div class=${held ? "wait" : "no"}>
      ${t(s, "test.trace.skipped", { action: name, why })}
    </div>`;
  }

  // --- tab 3: the walk test (§11.3) ------------------------------------------------

  /** Really armed, really reading, nothing answering.
   *
   * The table is the feature. Not the zones that detected you — those are
   * the reassuring half — but the ones that never did, which is where a
   * misaimed PIR and a dead battery are found. So the zones that never
   * reacted are listed first, and the ones that did are below them.
   */
  private _renderWalkTest(s: Strings) {
    const walk = this.ctx!.status.walk_test;

    // While one is running the shell's banner is directly above this, on
    // every page, and it already says what is held back, when it ends and
    // what stays live. Saying it again here would be the page repeating
    // itself inside one screen — so this keeps only what the banner has no
    // room for: what to do now.
    return html`
      <div class="notice ${walk ? "danger" : "warn"}">
        ${walk
          ? t(s, "walk.active")
          : html`<strong>${t(s, "walk.idle_title")}</strong>
              ${t(s, "walk.idle")}
              <div class="hint">${t(s, "walk.always_on_live")}</div>`}
      </div>
      ${walk ? this._renderWalkRunning(s, walk) : this._renderWalkStart(s)}
    `;
  }

  private _renderWalkStart(s: Strings) {
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "walk.start_title")}</h2>
          <span class="hint">${t(s, "walk.start_sub")}</span>
        </div>
        <div class="card-bd">
          <p>${t(s, "walk.explainer")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "walk.duration")}</span>
              <input
                type="number"
                min="1"
                .value=${this._walkDuration}
                placeholder=${t(s, "walk.duration_default")}
                @change=${(e: Event) =>
                  (this._walkDuration = (e.target as HTMLInputElement).value)}
              />
              <span class="hint">${t(s, "walk.duration_hint")}</span>
            </label>
          </div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy}
              @click=${() => void this._startWalkTest()}
            >
              ${t(s, "walk.start")}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  private _renderWalkRunning(s: Strings, walk: WalkTestStatus) {
    const ctx = this.ctx!;
    const zones = new Map(ctx.status.zones.map((z) => [z.id, z]));
    const areas = new Map(ctx.status.areas.map((a) => [a.id, a.name]));
    const missed = walk.expected_zones.filter((id) => !walk.detections[id]);
    const seen = walk.expected_zones.filter((id) => walk.detections[id]);
    const row = (id: string) => {
      const zone = zones.get(id);
      const detection = walk.detections[id];
      return html`
        <tr>
          <td><strong>${zone?.name ?? id}</strong></td>
          <td>${areas.get(zone?.area_id ?? "") ?? ""}</td>
          <td>
            <span class="state ${detection ? "closed" : "fault"}">
              ${t(s, detection ? "walk.detected" : "walk.never")}
            </span>
          </td>
          <td class="mono">${detection ? hhmm(detection.first, this.ctx?.hass.language, this.ctx?.hass) : "—"}</td>
          <td class="mono">${detection ? detection.count : 0}</td>
          <td>
            ${zone?.fault
              ? html`<span class="state fault">${t(s, `fault.${zone.fault}`)}</span>`
              : nothing}
          </td>
        </tr>
      `;
    };
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "walk.table_title")}</h2>
          <span class="hint">
            ${t(s, "walk.started_by", {
              who: walk.user_name ?? t(s, "walk.somebody"),
              at: hhmm(walk.started_at, this.ctx?.hass.language, this.ctx?.hass),
            })}
          </span>
        </div>
        <div class="card-bd">
          ${missed.length
            ? html`<div class="problems" role="alert">
                ${t(
                  s,
                  // One zone is the common case on a second walk, and
                  // "1 zone(s) have not reacted" is the kind of string that
                  // makes a household trust the rest of the page less.
                  missed.length === 1
                    ? "walk.never_reacted_one"
                    : "walk.never_reacted",
                  { n: missed.length },
                )}
              </div>`
            : html`<div class="notice">${t(s, "walk.all_reacted")}</div>`}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${t(s, "test.col.zone")}</th>
                  <th>${t(s, "walk.col.area")}</th>
                  <th>${t(s, "walk.col.result")}</th>
                  <th>${t(s, "walk.col.first")}</th>
                  <th>${t(s, "walk.col.count")}</th>
                  <th>${t(s, "test.col.health")}</th>
                </tr>
              </thead>
              <tbody>
                ${missed.map(row)}${seen.map(row)}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  private async _startWalkTest(): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return;
    this._busy = true;
    this._error = undefined;
    this._notice = undefined;
    try {
      const minutes = Number(this._walkDuration) || 0;
      const result = await ctx.walkTest(true, {
        duration: minutes > 0 ? minutes * 60 : undefined,
      });
      if (!result.success) {
        this._error = reasonText(ctx.strings, result);
      } else if (result.blocking_zones.length) {
        // Not a refusal: the test is running, and those areas are not in it
        // (part 2 decision 7). Said plainly, because a zone that was never
        // armed cannot have detected anything — as a note, not as the red
        // alert a refusal is (second review).
        this._notice = t(ctx.strings, "walk.partly_armed", {
          zones: result.blocking_zones.map((z) => z.name).join(", "),
        });
      }
    } catch (err) {
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  // --- tab 4: the real action test (§11.4) -----------------------------------------

  /** A test button beside every action, and it really executes.
   *
   * That is the whole feature, and the reason it is worth the risk: the
   * failure it prevents is discovering during the emergency that the
   * emergency channel was misconfigured. So it asks first, it says what is
   * about to happen, and every run leaves a row in the log marked as a test.
   *
   * §11.4 also asks for a button beside every *contact channel*. That half
   * lives on page 6, beside the channel it tests, because that is where
   * somebody has just finished configuring it and is wondering whether it
   * arrives.
   */
  private _renderActionTest(s: Strings) {
    const profiles = this.ctx!.config?.profiles ?? [];
    return html`
      <div class="notice danger">
        <strong>${t(s, "action_test.warn_title")}</strong>
        ${t(s, "action_test.warn")}
      </div>
      ${this._confirming ? this._renderConfirm(s) : nothing}
      ${profiles.length === 0
        ? html`<p class="empty">${t(s, "action_test.no_profiles")}</p>`
        : profiles.map((profile) => this._renderProfileTests(s, profile))}
    `;
  }

  private _renderProfileTests(s: Strings, profile: ProfileConfig) {
    const actions = profile.actions.filter((a) => a.kind !== "delay");
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${profile.name}</h2>
          <span class="hint">${t(s, "action_test.subtitle")}</span>
        </div>
        <div class="card-bd">
          ${actions.length === 0
            ? html`<p class="empty">${t(s, "action_test.no_actions")}</p>`
            : html`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${t(s, "action_test.col.action")}</th>
                      <th>${t(s, "action_test.col.what")}</th>
                      <th>${t(s, "action_test.col.last")}</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    ${actions.map((action) =>
                      this._renderActionRow(s, profile, action),
                    )}
                  </tbody>
                </table>
              </div>`}
        </div>
      </div>
    `;
  }

  private _renderActionRow(s: Strings, profile: ProfileConfig, action: ActionConfig) {
    const key = `${profile.id}:${action.id}`;
    const last = this._tested[key];
    const name = action.name || t(s, `action_kind.${action.kind}`);
    return html`
      <tr>
        <td><strong>${name}</strong></td>
        <td class="hint">${t(s, `action_test.what.${action.kind}`)}</td>
        <td>
          ${!last
            ? html`<span class="muted">${t(s, "action_test.never")}</span>`
            : last.ok
              ? html`<span class="state closed">${t(s, "action_test.ok")}</span>`
              : html`<span class="state fault" title=${last.error ?? ""}
                  >${t(s, "action_test.failed")}</span
                >`}
        </td>
        <td>
          <button
            class="btn small"
            ?disabled=${this._busy}
            @click=${() =>
              (this._confirming = {
                profile_id: profile.id ?? "",
                action_id: action.id ?? "",
                name,
              })}
          >
            ${t(s, "action_test.test")}
          </button>
        </td>
      </tr>
    `;
  }

  /** §11.4: "it really executes, so it requires explicit confirmation". */
  private _renderConfirm(s: Strings) {
    const asking = this._confirming!;
    return html`
      <div class="problems" role="alertdialog">
        <p>${t(s, "action_test.confirm", { action: asking.name })}</p>
        <div class="actions">
          <button
            class="btn primary"
            ?disabled=${this._busy}
            @click=${() => void this._runTest(asking)}
          >
            ${t(s, "action_test.confirm_yes")}
          </button>
          <button class="btn" @click=${() => (this._confirming = undefined)}>
            ${t(s, "common.cancel")}
          </button>
        </div>
      </div>
    `;
  }

  private async _runTest(asking: {
    profile_id: string;
    action_id: string;
    name: string;
  }): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return;
    this._busy = true;
    this._confirming = undefined;
    this._error = undefined;
    try {
      const result = await ctx.testAction({
        profile_id: asking.profile_id,
        action_id: asking.action_id,
      });
      const detail = result.error ?? testReason(ctx.strings, result.reason);
      this._tested = {
        ...this._tested,
        [`${asking.profile_id}:${asking.action_id}`]: {
          ok: result.success,
          at: Date.now(),
          error: detail || undefined,
        },
      };
      if (!result.success) {
        this._error = t(ctx.strings, "action_test.failed_detail", {
          action: asking.name,
          detail,
        });
      }
    } catch (err) {
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
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
      /* The two tabs that write say so in the colour of what they do: the
         walk test holds the whole response back, the action test really
         sounds the siren. */
      .notice.danger {
        border-left-color: var(--error-color, #d32f2f);
        margin: 0 0 16px;
      }
      .notice.warn {
        margin: 0 0 16px;
      }
      .card-hd .btn.danger {
        margin-left: auto;
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

/** Why a test did not run at all: a reason rather than a transport error,
 * and the panel writes the sentence, as it does for every other code the
 * backend returns (§15.2). An unknown one is shown as it came, which is
 * better than nothing at all. */
export function testReason(s: Strings, reason: string | null): string {
  if (!reason) return "";
  const text = t(s, `action_test.reason.${reason}`);
  return text.startsWith("action_test.reason.") ? reason : text;
}

if (!customElements.get("foyer-page-test")) {
  customElements.define("foyer-page-test", FoyerPageTest);
}