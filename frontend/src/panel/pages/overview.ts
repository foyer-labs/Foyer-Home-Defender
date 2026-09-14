// Page 1 — Overview (SPEC §15.1): every area's state, the scenarios, the zones
// that would stop arming, and quick arm/disarm. The page decides nothing: every
// button sends a command and renders the engine's answer (INV-2).
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type { CommandResult, StatusArea, StatusZone } from "../../shared/types";
import { reasonText, remaining, type PanelContext } from "../context";

// A refusal that a forced arm could override (§5.4): open or faulted zones.
const FORCEABLE = new Set(["zone_open", "zone_fault"]);

interface Feedback {
  ok: boolean;
  text: string;
  retry?: Record<string, unknown>; // the command to repeat with force
}

class FoyerPageOverview extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _busy: { state: true },
    _feedback: { state: true },
  };

  ctx?: PanelContext;
  private _busy = false;
  private _feedback?: Feedback;

  private async _run(
    command: () => Promise<CommandResult>,
    retry?: Record<string, unknown>,
  ): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return;
    this._busy = true;
    this._feedback = undefined;
    try {
      const result = await command();
      if (result.success) {
        const bypassed = result.bypassed_zones.map((z) => z.name).join(", ");
        this._feedback = bypassed
          ? { ok: true, text: t(ctx.strings, "overview.bypassed", { zones: bypassed }) }
          : undefined;
      } else {
        this._feedback = {
          ok: false,
          text: reasonText(ctx.strings, result),
          retry: retry && FORCEABLE.has(result.reason ?? "") ? retry : undefined,
        };
      }
    } catch (err) {
      this._feedback = { ok: false, text: String((err as Error)?.message ?? err) };
    } finally {
      this._busy = false;
    }
  }

  private _arm(target: Record<string, unknown>): void {
    const ctx = this.ctx;
    if (ctx) this._run(() => ctx.arm(target), target);
  }

  private _force(target: Record<string, unknown>): void {
    const ctx = this.ctx;
    if (ctx) this._run(() => ctx.arm({ ...target, force: true }));
  }

  private _disarm(areaIds?: string[]): void {
    const ctx = this.ctx;
    if (ctx) this._run(() => ctx.disarm(areaIds));
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx) return nothing;
    const s = ctx.strings;
    const status = ctx.status;
    const memory = status.areas.filter((a) => a.memory);
    return html`
      <div class="notice" role="note">${t(s, "overview.no_codes_warning")}</div>
      ${memory.map(
        (area) => html`<div class="alarm-memory" role="alert">
          ${t(s, "overview.memory_banner", {
            area: area.name,
            zones: this._zoneNames(area.causes),
          })}
        </div>`,
      )}
      ${this._renderMaster(s)} ${this._renderFeedback(s)}
      <div class="tiles">${status.areas.map((area) => this._renderArea(s, area))}</div>
      ${this._renderNotReady(s)}
    `;
  }

  private _zoneNames(ids: string[]): string {
    const names = new Map(this.ctx!.status.zones.map((z) => [z.id, z.name]));
    return ids.map((id) => names.get(id) ?? id).join(", ");
  }

  private _renderMaster(s: Strings) {
    const status = this.ctx!.status;
    const master = status.master;
    const anyArmed = status.areas.some((a) => a.state !== "disarmed" || a.memory);
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "overview.master")}</h2>
          <span class="state ${master.state}">${t(s, `state.${master.state}`)}</span>
          ${master.mode ? html`<span class="mono">${master.mode}</span>` : nothing}
        </div>
        <div class="card-bd">
          <div class="label">${t(s, "overview.scenario")}</div>
          <div class="chips">
            ${status.scenarios.length
              ? status.scenarios.map(
                  (scenario) => html`
                    <button
                      class="chip"
                      aria-pressed=${scenario.id === status.active_scenario_id
                        ? "true"
                        : "false"}
                      ?disabled=${this._busy}
                      @click=${() => this._arm({ scenario_id: scenario.id })}
                    >
                      ${scenario.name}
                    </button>
                  `,
                )
              : html`<span class="muted">${t(s, "overview.no_scenarios")}</span>`}
          </div>
          <div class="hint">${t(s, "overview.scenario_hint")}</div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !anyArmed}
              @click=${() => this._disarm()}
            >
              ${t(s, "overview.disarm_all")}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  private _renderFeedback(s: Strings) {
    const feedback = this._feedback;
    if (!feedback) return nothing;
    return html`
      <div class=${feedback.ok ? "notice" : "problems"} role="alert">
        ${feedback.text}
        ${feedback.retry
          ? html`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._force(feedback.retry!)}
              >
                ${t(s, "overview.force_arm")}
              </button>
              <span class="hint">${t(s, "overview.force_arm_hint")}</span>
            </div>`
          : nothing}
      </div>
    `;
  }

  private _renderArea(s: Strings, area: StatusArea) {
    const ctx = this.ctx!;
    const scenario = ctx.status.scenarios.find((sc) => sc.id === area.scenario_id);
    return html`
      <div class="card tile">
        <div class="card-bd">
          <div class="label">${t(s, "overview.area")}</div>
          <div class="name">${area.name}</div>
          <div class="row">
            <span class="state ${area.state}">${t(s, `state.${area.state}`)}</span>
            ${area.memory
              ? html`<span class="state memory">${t(s, "overview.memory")}</span>`
              : nothing}
          </div>
          ${area.timer && area.timer.kind !== "siren"
            ? html`<div class="countdown">
                ${t(s, `timer.${area.timer.kind}`, {
                  seconds: remaining(ctx, area.timer.due),
                })}
              </div>`
            : nothing}
          <div class="hint">
            ${area.state === "disarmed"
              ? nothing
              : scenario
                ? t(s, "overview.by_scenario", { scenario: scenario.name })
                : t(s, "overview.on_its_own")}
          </div>
          <div class="actions">
            ${area.state === "disarmed"
              ? html`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._arm({ area_id: area.id })}
                >
                  ${t(s, "overview.arm_area")}
                </button>`
              : nothing}
            ${area.state !== "disarmed" || area.memory
              ? html`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._disarm([area.id])}
                >
                  ${t(s, "overview.disarm_area")}
                </button>`
              : nothing}
          </div>
        </div>
      </div>
    `;
  }

  private _renderNotReady(s: Strings) {
    const ctx = this.ctx!;
    const areas = new Map(ctx.status.areas.map((a) => [a.id, a.name]));
    const rows = ctx.status.zones.filter((z) => z.enabled && (z.fault || z.open || z.bypassed));
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "overview.not_ready")}</h2></div>
        ${rows.length
          ? html`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${t(s, "overview.zone")}</th>
                    <th>${t(s, "overview.area")}</th>
                    <th>${t(s, "overview.status")}</th>
                    <th>${t(s, "overview.entity_state")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map(
                    (zone) => html`<tr>
                      <td>${zone.name}</td>
                      <td>${areas.get(zone.area_id) ?? ""}</td>
                      <td>${this._zoneStatus(s, zone)}</td>
                      <td class="mono">${zone.state ?? "—"}</td>
                    </tr>`,
                  )}
                </tbody>
              </table>
            </div>`
          : html`<div class="empty">${t(s, "overview.all_ready")}</div>`}
      </div>
    `;
  }

  private _zoneStatus(s: Strings, zone: StatusZone) {
    if (zone.fault) {
      return html`<span class="state fault">${t(s, `fault.${zone.fault}`)}</span>`;
    }
    if (zone.bypassed) {
      return html`<span class="state bypassed">${t(s, `bypass.${zone.bypassed}`)}</span>`;
    }
    return html`<span class="state open">${t(s, "zone_status.open")}</span>`;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
      }
      .tile {
        margin: 0;
      }
      .label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--secondary-text-color);
        margin-bottom: 6px;
      }
      .name {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 8px;
      }
      .row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .countdown {
        margin-top: 10px;
        font-size: 15px;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
      }
      .hint {
        margin-top: 6px;
      }
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
      }
      .chip {
        font: inherit;
        font-size: 14px;
        padding: 6px 14px;
        border-radius: 999px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        cursor: pointer;
      }
      .chip[aria-pressed="true"] {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      .alarm-memory {
        margin: 12px 0;
        padding: 10px 14px;
        border-left: 3px solid var(--error-color, #d32f2f);
        background: var(--card-background-color);
        border-radius: 6px;
        font-weight: 500;
      }
      .notice {
        margin: 0 0 16px;
      }
      .problems {
        margin: 0 0 16px;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-overview")) {
  customElements.define("foyer-page-overview", FoyerPageOverview);
}
