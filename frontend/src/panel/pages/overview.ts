// Page 1 — Overview (SPEC §15.1): every area's state, the scenarios, the zones
// that would stop arming, and quick arm/disarm. The page decides nothing: every
// button sends a command and renders the engine's answer (INV-2).
import { LitElement, css, html, nothing, type PropertyValues } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type { CommandResult, LogRow, StatusArea, StatusZone } from "../../shared/types";
import { reasonText, remaining, type PanelContext } from "../context";

/** The name of an event, the same way the log page finds it: the log's own
 * word for it, else the moment's. */
function eventLabel(s: Strings, eventType: string): string {
  const own = t(s, `event_type.${eventType}`);
  if (!own.startsWith("event_type.")) return own;
  const moment = t(s, `moment.${eventType}`);
  return moment.startsWith("moment.") ? eventType : moment;
}

// A refusal that a forced arm could override (§5.4): open or faulted zones.
const FORCEABLE = new Set(["zone_open", "zone_fault"]);

interface Feedback {
  ok: boolean;
  text: string;
  retry?: Record<string, unknown>; // the command to repeat with force
  /** Zones this arming put under guard on a battery that is running out
   * (§4.2). Not a failure and never presented as one — but the warning has
   * to arrive on every arming, and it has to be actionable, so the zones it
   * names can be excluded from this arming in one press. */
  lowBattery?: { id: string; name: string }[];
}

class FoyerPageOverview extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _busy: { state: true },
    _feedback: { state: true },
    _recent: { state: true },
  };

  ctx?: PanelContext;
  private _busy = false;
  private _feedback?: Feedback;
  private _recent: LogRow[] = [];
  private _signature_?: string;

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
        const low = result.low_battery_zones;
        this._feedback = low.length
          ? {
              ok: true,
              text: t(ctx.strings, "overview.low_battery", {
                zones: low.map((z) => z.name).join(", "),
              }),
              lowBattery: low,
            }
          : bypassed
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

  /** Take the zones a warning named out of this arming (§5.4): an ordinary
   * manual bypass, which ends when the area is disarmed. A zone that may not
   * be excluded is left alone and the backend says so. */
  private async _excludeLowBattery(zones: { id: string }[]): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return;
    this._busy = true;
    try {
      // Every answer read: a zone that may not be excluded, or a code prompt
      // somebody cancelled, left the warning gone as if it had worked while
      // the zones stayed armed (second review).
      for (const zone of zones) {
        const result = await ctx.bypass(zone.id, true);
        if (!result.success) {
          this._feedback = { ok: false, text: reasonText(ctx.strings, result) };
          return;
        }
      }
      this._feedback = undefined;
    } catch (err) {
      this._feedback = { ok: false, text: String((err as Error)?.message ?? err) };
    } finally {
      this._busy = false;
    }
  }

  private _disarm(areaIds?: string[]): void {
    const ctx = this.ctx;
    if (ctx) this._run(() => ctx.disarm(areaIds));
  }

  private _acknowledge(target: "incident" | "technical"): void {
    const ctx = this.ctx;
    if (ctx) this._run(() => ctx.acknowledge(target));
  }

  override updated(changed: PropertyValues): void {
    // The shell hands us a fresh context object on every render, and a running
    // countdown re-renders every second: reloading on "ctx changed" would ask
    // the log a question a second. Ask only when something actually happened.
    if (!changed.has("ctx") || !this.ctx) return;
    if (
      this._feedback &&
      !this._feedback.ok &&
      this._feedback.retry &&
      this.ctx.status.areas.every((a) => a.ready)
    ) {
      // The refusal was about a zone that is closed now: the box offering to
      // force the arming stayed, pointing at a problem that had gone
      // (second review).
      this._feedback = undefined;
    }
    const signature = this._signature();
    if (signature === this._signature_) return;
    this._signature_ = signature;
    void this._loadRecent();
  }

  /** What has to change before the recent-events list is worth reloading. */
  private _signature(): string {
    const status = this.ctx!.status;
    return JSON.stringify([
      status.active_scenario_id,
      status.areas.map((a) => [a.id, a.state, a.memory, a.ready]),
      status.incident?.id,
      status.incident?.acknowledged,
      status.technical.map((t2) => [t2.zone_id, t2.acknowledged]),
      status.zones.map((z) => [z.id, z.state, z.bypassed, z.fault]),
      status.chime_enabled,
    ]);
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx) return nothing;
    const s = ctx.strings;
    const status = ctx.status;
    const memory = status.areas.filter((a) => a.memory);
    return html`
      ${this._renderTechnical(s)} ${this._renderIncident(s)}
      ${status.security.enforced
        ? nothing
        : html`<div class="notice" role="note">
            ${t(s, "overview.no_codes_warning")}
          </div>`}
      ${memory.map(
        (area) => html`<div class="alarm-memory" role="alert">
          ${area.causes.length
            ? t(s, "overview.memory_banner", {
                area: area.name,
                zones: this._zoneNames(area.causes),
              })
            : // A memory whose zones are no longer known — a restart, a zone
              // deleted since — still has to say the alarm went off, without
              // a dangling colon where the names should be.
              t(s, "overview.memory_banner_plain", { area: area.name })}
        </div>`,
      )}
      ${this._renderMaster(s)} ${this._renderFeedback(s)}
      <div class="tiles">${status.areas.map((area) => this._renderArea(s, area))}</div>
      ${this._renderNotReady(s)} ${this._renderRecent(s)}
    `;
  }

  /** The last few things that happened (§15.1, page 1).
   *
   * Only what matters: zone activity is excluded here even when it is being
   * recorded, because six rows of "hall motion" would say nothing about the
   * night. The log page shows everything.
   */
  private _renderRecent(s: Strings) {
    const ctx = this.ctx!;
    const rows = this._recent;
    if (!rows.length) return nothing;
    const areas = new Map(ctx.status.areas.map((a) => [a.id, a.name]));
    const zones = new Map(ctx.status.zones.map((z) => [z.id, z.name]));
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "overview.recent")}</h2>
          <span class="spacer"></span>
          <button class="btn sm" @click=${() => ctx.navigate("log")}>
            ${t(s, "overview.full_log")}
          </button>
        </div>
        <div class="card-bd">
          <div class="recent">
            ${rows.map(
              (row) => html`<div class="row">
                <span class="when mono"
                  >${new Date(row.ts).toLocaleTimeString(ctx.hass.language, {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}</span
                >
                <span class="state ${row.severity === "alarm"
                  ? "triggered"
                  : row.severity === "warning"
                    ? "arming"
                    : "disarmed"}"
                  >${eventLabel(s, row.event_type)}</span
                >
                <span class="where">
                  ${[areas.get(row.area_id ?? ""), zones.get(row.zone_id ?? "")]
                    .filter(Boolean)
                    .join(" \u00b7 ")}
                </span>
              </div>`,
            )}
          </div>
        </div>
      </div>
    `;
  }

  /** Reloaded whenever the live status changes, which is exactly when
   * something worth showing has just been written. */
  private async _loadRecent(): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return;
    try {
      const page = await ctx.queryLog({
        limit: 6,
        categories: ["arming", "alarm", "security", "system"],
      });
      this._recent = page.rows;
    } catch {
      this._recent = [];
    }
  }

  private _zoneNames(ids: string[]): string {
    const names = new Map(this.ctx!.status.zones.map((z) => [z.id, z.name]));
    return ids.map((id) => names.get(id) ?? id).join(", ");
  }

  // The technical channel (§5.5): its own banner and its own acknowledgement,
  // visible whatever the areas are doing. Disarming does not clear it.
  private _renderTechnical(s: Strings) {
    const alarms = this.ctx!.status.technical;
    if (!alarms.length) return nothing;
    const pending = alarms.some((a) => !a.acknowledged);
    return html`
      <div class="banner technical" role="alert">
        <div class="banner-hd">${t(s, "overview.technical_title")}</div>
        <div>
          ${t(s, "overview.technical_banner", { zones: alarms.map((a) => a.name).join(", ") })}
        </div>
        <ul class="plain">
          ${alarms.map(
            (a) => html`<li>
              <strong>${a.name}</strong> —
              ${t(
                s,
                a.acknowledged
                  ? "technical_state.acknowledged"
                  : a.active
                    ? "technical_state.active"
                    : "technical_state.memory",
              )}
            </li>`,
          )}
        </ul>
        ${pending
          ? html`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("technical")}
              >
                ${t(s, "common.acknowledge")}
              </button>
            </div>`
          : nothing}
      </div>
    `;
  }

  // The open intrusion incident (§5.6): every zone of one alarm, acknowledged once.
  private _renderIncident(s: Strings) {
    const incident = this.ctx!.status.incident;
    if (!incident) return nothing;
    return html`
      <div class="banner incident" role="alert">
        <div class="banner-hd">
          ${t(s, "overview.incident_title", { id: incident.id })}
          <span class="state ${incident.acknowledged ? "memory" : "triggered"}">
            ${t(
              s,
              incident.acknowledged ? "overview.incident_acknowledged" : "overview.incident_open",
            )}
          </span>
        </div>
        <div>${t(s, "overview.incident_zones", { zones: this._zoneNames(incident.zone_ids) })}</div>
        <div class="hint">${t(s, "overview.incident_hint")}</div>
        ${incident.acknowledged
          ? nothing
          : html`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("incident")}
              >
                ${t(s, "common.acknowledge")}
              </button>
            </div>`}
      </div>
    `;
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
          ${master.mode ? html`<span>${t(s, `ha_state.${master.mode}`)}</span>` : nothing}
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
        ${feedback.lowBattery?.length
          ? html`<div class="actions">
              <button
                class="btn"
                ?disabled=${this._busy}
                @click=${() => void this._excludeLowBattery(feedback.lowBattery!)}
              >
                ${t(s, "overview.exclude_low_battery")}
              </button>
            </div>`
          : nothing}
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
    // A smoke detector in alarm is not an open zone: it has its own banner.
    const rows = ctx.status.zones.filter(
      (z) => z.enabled && (z.fault || (z.open && z.channel === "intrusion") || z.bypassed),
    );
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
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map(
                    (zone) => html`<tr>
                      <td>${zone.name}</td>
                      <td>${areas.get(zone.area_id) ?? ""}</td>
                      <td>${this._zoneStatus(s, zone)}</td>
                      <td class="mono">${zone.state ?? "—"}</td>
                      <td>${this._renderBypass(s, zone)}</td>
                    </tr>`,
                  )}
                </tbody>
              </table>
            </div>`
          : html`<div class="empty">${t(s, "overview.all_ready")}</div>`}
      </div>
    `;
  }

  /** Excluding a zone by hand, with or without a duration (SPEC §16).

   * Without one it comes back when the area is disarmed; with one it comes
   * back on its own and says so, because a zone excluded and forgotten is
   * exactly the window somebody comes through.
   */
  private _renderBypass(s: Strings, zone: StatusZone) {
    const ctx = this.ctx!;
    if (zone.bypassed) {
      return html`<button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => ctx.bypass(zone.id, false))}
      >
        ${t(s, "zones.unbypass")}
      </button>`;
    }
    if (!zone.bypassable) return nothing;
    return html`<div class="bypass">
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => ctx.bypass(zone.id, true))}
      >
        ${t(s, "zones.bypass")}
      </button>
      ${[1, 8].map(
        (hours) => html`<button
          class="btn sm ghost"
          ?disabled=${this._busy}
          @click=${() => this._run(() => ctx.bypass(zone.id, true, hours * 3600))}
        >
          ${t(s, "zones.bypass_hours", { hours })}
        </button>`,
      )}
      <label class="minutes">
        <input
          type="number"
          min="1"
          max="10080"
          placeholder=${t(s, "zones.bypass_minutes_placeholder")}
          aria-label=${t(s, "zones.bypass_minutes")}
          @keydown=${(e: KeyboardEvent) => {
            if (e.key === "Enter") this._bypassMinutes(zone.id, e.target as HTMLInputElement);
          }}
        />
        <button
          class="btn sm ghost"
          ?disabled=${this._busy}
          @click=${(e: Event) => {
            const input = (e.target as HTMLElement)
              .closest("label")!
              .querySelector("input") as HTMLInputElement;
            this._bypassMinutes(zone.id, input);
          }}
        >
          ${t(s, "zones.bypass_minutes")}
        </button>
      </label>
    </div>`;
  }

  /** Any duration, in minutes: an hour and eight hours cover the common cases
   * but not "twenty minutes while the window airs the room" — and a timed
   * exclusion whose length you cannot choose is one you round up. */
  private _bypassMinutes(zoneId: string, input: HTMLInputElement): void {
    const ctx = this.ctx!;
    const minutes = Number(input.value);
    if (!Number.isFinite(minutes) || minutes < 1) return;
    input.value = "";
    void this._run(() => ctx.bypass(zoneId, true, Math.round(minutes) * 60));
  }

  private _zoneStatus(s: Strings, zone: StatusZone) {
    const ctx = this.ctx!;
    if (zone.fault) {
      return html`<span class="state fault">${t(s, `fault.${zone.fault}`)}</span>`;
    }
    if (zone.bypassed) {
      const until = zone.bypass_until
        ? t(s, "zones.bypass_until", {
            // The Home Assistant user's language, like every other time on
            // this page: the browser's would print 9:30 PM beside 21:30.
            time: new Date(zone.bypass_until).toLocaleTimeString(ctx.hass.language, {
              hour: "2-digit",
              minute: "2-digit",
            }),
          })
        : t(s, "zones.bypass_indefinite");
      return html`<span class="state bypassed">${t(s, `bypass.${zone.bypassed}`)}</span>
        <span class="hint">${zone.bypassed === "manual" ? until : ""}</span>`;
    }
    return html`<span class="state open">${t(s, "zone_status.open")}</span>`;
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      .recent {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 13.5px;
      }
      .recent .row {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }
      .recent .when {
        color: var(--secondary-text-color);
      }
      .recent .where {
        color: var(--secondary-text-color);
      }
      .spacer {
        flex: 1;
      }
      .minutes {
        display: inline-flex;
        align-items: center;
        gap: 4px;
      }
      .minutes input {
        width: 5.5em;
        font: inherit;
        font-size: 13px;
        padding: 4px 6px;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
      }
      .bypass {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
      }
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
      .banner {
        margin: 0 0 16px;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid var(--divider-color);
        border-left: 4px solid var(--error-color, #d32f2f);
        background: var(--card-background-color);
        font-size: 14px;
      }
      .banner.incident {
        border-left-color: var(--warning-color, #c77700);
      }
      .banner-hd {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 6px;
      }
      .banner .actions {
        margin-top: 10px;
      }
      ul.plain {
        margin: 8px 0 0;
        padding-left: 18px;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-overview")) {
  customElements.define("foyer-page-overview", FoyerPageOverview);
}
