// Page 14 — System health (SPEC §12, §15.1). "An alarm that cannot tell you
// it has stopped working has stopped working."
//
// Two halves, deliberately in this order. The top is the condition: mains,
// watchdog, channels, radios, faults — what is true right now, readable by
// anybody who may read the log. The bottom is the configuration, which is
// edit_config and asks for a code where the policy says so. Nothing on this
// page decides anything: every number comes from the backend, because the
// panel working out for itself whether a radio is being jammed is a panel
// that can disagree with the engine that decides it.
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  HealthConfig,
  HealthStatus,
  Problem,
  RadioCandidate,
  RadioConfig,
} from "../../shared/types";
import { anyArmed, problemText, type PanelContext, whenNumber } from "../context";
import { allEntities, entityListStyles, renderEntityList } from "../entity-list";
import { define } from "../../shared/define";

/** A timestamp as the rest of the panel writes one. An absent one is a dash
 * rather than an empty cell: "nothing has happened yet" is an answer. */
function when(ctx: PanelContext, value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString(ctx.hass.language) : "—";
}

type Tone = "ok" | "warn" | "crit" | "idle";

class FoyerPageHealth extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _status: { state: true },
    _draft: { state: true },
    _candidates: { state: true },
    _problems: { state: true },
    _busy: { state: true },
    _error: { state: true },
  };

  ctx?: PanelContext;
  private _status?: HealthStatus;
  private _draft?: HealthConfig;
  private _candidates: RadioCandidate[] = [];
  private _problems: Problem[] = [];
  private _busy = false;
  private _error = "";
  private _timer?: number;

  override connectedCallback(): void {
    super.connectedCallback();
    void this._load();
    // The page is a live reading, so it refreshes while it is open. A
    // watchdog that pings every quarter of an hour is not worth a second
    // ticker: thirty seconds is fast enough for somebody watching, and the
    // interesting half of this page changes on an entity, not on a clock.
    this._timer = window.setInterval(() => void this._load(), 30000);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this._timer) window.clearInterval(this._timer);
  }

  private async _load(): Promise<void> {
    if (!this.ctx) return;
    try {
      this._status = await this.ctx.health();
      this._error = "";
    } catch (err) {
      this._error = String((err as { message?: string })?.message ?? err);
    }
  }

  private _editConfig(): void {
    const health = this.ctx?.config?.health;
    if (!health) return;
    // The watchdog URL is written and never read back (§12.3, decision 130):
    // the configuration says only whether one is set, so the field starts
    // empty whatever is stored, and what is typed there replaces it. Left
    // empty, the stored one stays.
    this._draft = structuredClone(health);
    this._problems = [];
    void this._loadCandidates();
  }

  private async _loadCandidates(): Promise<void> {
    if (!this.ctx) return;
    try {
      this._candidates = await this.ctx.radioCandidates();
    } catch {
      this._candidates = [];
    }
  }

  private _set<K extends keyof HealthConfig>(key: K, value: HealthConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private _setWatchdog<K extends keyof HealthConfig["watchdog"]>(
    key: K,
    value: HealthConfig["watchdog"][K],
  ): void {
    if (this._draft) {
      this._draft = { ...this._draft, watchdog: { ...this._draft.watchdog, [key]: value } };
    }
  }

  private _setRadio(index: number, patch: Partial<RadioConfig>): void {
    if (!this._draft) return;
    const radios = this._draft.radios.map((r, i) => (i === index ? { ...r, ...patch } : r));
    this._set("radios", radios);
  }

  private _addRadio(): void {
    if (!this._draft) return;
    const used = new Set(this._draft.radios.map((r) => r.entry_id));
    const free = this._candidates.find((c) => !used.has(c.entry_id));
    this._set("radios", [
      ...this._draft.radios,
      {
        name: free?.title ?? "",
        entry_id: free?.entry_id ?? "",
        coordinator_entity_id: null,
        n_zones: null,
        window: null,
        enabled: true,
      },
    ]);
  }

  private _removeRadio(index: number): void {
    if (!this._draft) return;
    this._set(
      "radios",
      this._draft.radios.filter((_, i) => i !== index),
    );
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.saveHealth(this._draft);
      this._problems = result.problems;
      if (result.success) {
        this._draft = undefined;
        await this._load();
      }
    } finally {
      this._busy = false;
    }
  }

  // --- rendering ------------------------------------------------------------------

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    // One failed poll no longer replaces the page — and an open editor with
    // it — with the error: the last answer stays, and the error says it is
    // not fresh (second review).
    const status = this._status;
    if (this._error && !status) {
      return html`<div class="card">
        <div class="card-bd"><div class="empty">${this._error}</div></div>
      </div>`;
    }
    if (!status) {
      return html`<div class="card">
        <div class="card-bd"><div class="empty">${t(s, "common.loading")}</div></div>
      </div>`;
    }
    return html`
      ${this._error ? html`<div class="problems" role="alert">${this._error}</div>` : nothing}
      ${this._renderTiles(s, status)} ${this._renderChannels(s, status)}
      ${this._renderRadios(s, status)} ${this._renderFaults(s, status)}
      ${this._renderDiagnostics(s)}
      ${this._draft
        ? this._renderEditor(s, this._draft)
        : html`<div class="card">
            <div class="card-hd">
              <h2>${t(s, "health.settings")}</h2>
              <button class="btn" @click=${() => this._editConfig()}>
                ${t(s, "common.edit")}
              </button>
            </div>
            <div class="card-bd">
              <p class="hint">${t(s, "health.settings_hint")}</p>
            </div>
          </div>`}
    `;
  }

  private _tile(label: string, state: string, meta: string, tone: Tone) {
    return html`<div class="tile ${tone}">
      <div class="name">${label}</div>
      <div class="state">${state}</div>
      <div class="meta">${meta}</div>
    </div>`;
  }

  private _renderTiles(s: Strings, status: HealthStatus) {
    const mains = status.mains;
    const outside = mains.mode === "outside_ups";
    const mainsSet = outside ? mains.outside.length > 0 : Boolean(mains.entity_id);
    const mainsTone: Tone = !mainsSet
      ? "idle"
      : mains.lost === true
        ? "crit"
        : mains.lost === null
          ? "warn"
          : "ok";
    const watchdog = status.watchdog;
    const watchdogTone: Tone = !watchdog.enabled
      ? "idle"
      : watchdog.down_since
        ? "crit"
        : "ok";
    const broken = status.channels.filter((c) => c.fault).length;
    const unchecked = status.channels.filter((c) => !c.fault && !c.checked).length;
    return html`<div class="tiles">
      ${this._tile(
        t(s, "health.mains"),
        !mainsSet
          ? t(s, "health.not_configured")
          : mains.lost === true
            ? t(s, "health.mains_lost")
            : mains.lost === null
              ? t(s, "health.unreadable")
              : t(s, "health.mains_present"),
        outside && mainsSet
          ? t(s, "health.mains_outside_meta", {
              count: String(mains.outside.length),
              silent: String(mains.outside.filter((o) => o.quiet_since).length),
            })
          : (mains.entity_id ?? t(s, "health.mains_pick")),
        mainsTone,
      )}
      ${this._tile(
        t(s, "health.watchdog"),
        !watchdog.enabled
          ? t(s, "health.off")
          : watchdog.down_since
            ? t(s, "health.unreachable")
            : t(s, "health.reporting"),
        watchdog.enabled
          ? t(s, "health.watchdog_meta", {
              every: String(Math.round(watchdog.interval / 60)),
              payload: t(s, watchdog.payload ? "health.with_payload" : "health.no_payload"),
            })
          : t(s, "health.watchdog_off_hint"),
        watchdogTone,
      )}
      ${this._tile(
        t(s, "health.channels"),
        broken
          ? t(s, "health.channels_broken", { n: String(broken) })
          : t(s, "health.channels_ok", { n: String(status.channels.length) }),
        t(s, "health.channels_meta", { n: String(unchecked) }),
        broken ? "crit" : status.channels.length ? "ok" : "idle",
      )}
    </div>`;
  }

  private _renderChannels(s: Strings, status: HealthStatus) {
    return html`<div class="card">
      <div class="card-hd">
        <h2>${t(s, "health.channels")}</h2>
        <span class="sub">
          ${t(s, "health.sweep_every", {
            minutes: String(Math.round((this.ctx?.config?.health.channel_sweep ?? 900) / 60)),
          })}
        </span>
      </div>
      ${status.channels.length
        ? html`<div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${t(s, "contacts.title")}</th>
                  <th>${t(s, "field.service")}</th>
                  <th>${t(s, "field.state")}</th>
                  <th>${t(s, "health.last_result")}</th>
                </tr>
              </thead>
              <tbody>
                ${status.channels.map(
                  (channel) => html`<tr>
                    <td>
                      <strong>${channel.contact_name}</strong>
                      <span class="tag">${t(s, `channel_kind.${channel.kind}`)}</span>
                    </td>
                    <td class="mono">${channel.service}</td>
                    <td>
                      <span class="pill ${channel.fault ? "bad" : channel.checked ? "ok" : "warn"}">
                        ${channel.fault
                          ? t(s, `health.fault_${channel.fault}`)
                          : channel.checked
                            ? t(s, "health.healthy")
                            : t(s, "health.untested")}
                      </span>
                    </td>
                    <td>${when(this.ctx!, channel.since ?? channel.last_ok)}</td>
                  </tr>`,
                )}
              </tbody>
            </table>
          </div>`
        : html`<div class="empty">${t(s, "health.no_channels")}</div>`}
      <div class="card-bd">
        <p class="hint">${t(s, "health.channels_note")}</p>
      </div>
    </div>`;
  }

  private _renderRadios(s: Strings, status: HealthStatus) {
    return html`<div class="card">
      <div class="card-hd">
        <h2>${t(s, "health.radios")}</h2>
      </div>
      ${status.radios.length
        ? html`<div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${t(s, "field.name")}</th>
                  <th>${t(s, "field.coordinator_entity_id")}</th>
                  <th>${t(s, "health.quiet_zones")}</th>
                  <th>${t(s, "field.state")}</th>
                </tr>
              </thead>
              <tbody>
                ${status.radios.map(
                  (radio) => html`<tr>
                    <td><strong>${radio.name}</strong></td>
                    <td class="mono">
                      ${radio.coordinator_entity_id ?? t(s, "health.no_coordinator")}
                    </td>
                    <td class="mono">
                      ${t(s, "health.quiet_of", {
                        quiet: String(radio.quiet),
                        zones: String(radio.zones),
                        threshold: String(radio.threshold),
                      })}
                    </td>
                    <td>
                      <span
                        class="pill ${radio.confirmed
                          ? "bad"
                          : radio.coordinator_down_since
                            ? "bad"
                            : radio.suspected_since
                              ? "warn"
                              : !radio.coordinator_entity_id || !radio.zones
                                ? "warn"
                                : "ok"}"
                      >
                        ${radio.confirmed
                          ? t(s, "health.interference")
                          : radio.coordinator_down_since
                            ? t(s, "health.coordinator_down")
                            : radio.suspected_since
                              ? t(s, "health.confirming")
                              : !radio.coordinator_entity_id
                                ? t(s, "health.not_gated")
                                : !radio.zones
                                  ? t(s, "health.no_zones")
                                  : t(s, "health.watching")}
                      </span>
                    </td>
                  </tr>`,
                )}
              </tbody>
            </table>
          </div>`
        : html`<div class="empty">${t(s, "health.no_radios")}</div>`}
      <div class="card-bd">
        <p class="hint">${t(s, "health.radios_note")}</p>
      </div>
    </div>`;
  }

  private _renderFaults(s: Strings, status: HealthStatus) {
    const zones = new Map((this.ctx?.config?.zones ?? []).map((z) => [z.id ?? "", z]));
    const unreachable = new Map(status.unreachable_zones.map((z) => [z.id, z]));
    return html`<div class="card">
      <div class="card-hd">
        <h2>${t(s, "health.faults")}</h2>
        <span class="sub">${t(s, "health.faults_sub")}</span>
      </div>
      ${status.faults.length
        ? html`<div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${t(s, "field.name")}</th>
                  <th>${t(s, "field.entity_id")}</th>
                  <th>${t(s, "health.since")}</th>
                </tr>
              </thead>
              <tbody>
                ${status.faults.map((id) => {
                  const zone = zones.get(id);
                  const gone = unreachable.get(id);
                  return html`<tr>
                    <td><strong>${zone?.name ?? id}</strong></td>
                    <td class="mono">${zone?.entity_id ?? ""}</td>
                    <td>
                      ${gone
                        ? t(s, "health.days", { n: String(gone.days) })
                        : t(s, "health.recent")}
                    </td>
                  </tr>`;
                })}
              </tbody>
            </table>
          </div>`
        : html`<div class="empty">${t(s, "health.no_faults")}</div>`}
    </div>`;
  }

  private _renderDiagnostics(s: Strings) {
    return html`<div class="card">
      <div class="card-hd">
        <h2>${t(s, "health.diagnostics")}</h2>
      </div>
      <div class="card-bd">
        <p class="hint">${t(s, "health.diagnostics_hint")}</p>
        <a class="btn" href="/config/integrations/integration/foyer">
          ${t(s, "health.diagnostics_open")}
        </a>
        <p class="hint">${t(s, "health.diagnostics_where")}</p>
      </div>
    </div>`;
  }

  // --- the configuration half -----------------------------------------------------

  private _bounds(key: string, fallback: [number, number]): [number, number] {
    return (this.ctx?.meta?.bounds[key] as [number, number] | undefined) ?? fallback;
  }

  /** Every entity Home Assistant has, for the fields below to suggest
   * from as the household types a name or an id. A suggestion, never a
   * restriction: an entity that is not there yet can still be typed. */
  private _renderEntityList() {
    const states = Object.values(this.ctx?.hass.states ?? {}).sort((a, b) =>
      a.entity_id.localeCompare(b.entity_id),
    );
    return html`<datalist id="foyer-entities">
      ${states.map(
        (e) =>
          html`<option value=${e.entity_id}>
            ${String(e.attributes.friendly_name ?? e.entity_id)}
          </option>`,
      )}
    </datalist>`;
  }

  private _renderSensor(s: Strings, draft: HealthConfig) {
    return html`<div class="grid-form">
      <label class="field">
        <span class="lbl">${t(s, "field.mains_entity_id")}</span>
        <input
          list="foyer-entities"
          .value=${draft.mains_entity_id ?? ""}
          placeholder=${t(s, "health.mains_placeholder")}
          @input=${(e: Event) =>
            this._set("mains_entity_id", (e.target as HTMLInputElement).value.trim() || null)}
        />
        <span class="hint">${t(s, "health.mains_hint")}</span>
      </label>
      <label class="field">
        <span class="lbl">${t(s, "field.mains_lost_states")}</span>
        <input
          .value=${draft.mains_lost_states.join(", ")}
          @input=${(e: Event) =>
            this._set(
              "mains_lost_states",
              (e.target as HTMLInputElement).value
                .split(",")
                .map((v) => v.trim())
                .filter(Boolean),
            )}
        />
        <span class="hint">${t(s, "health.mains_states_hint")}</span>
      </label>
    </div>`;
  }

  /** Devices outside the UPS (decision 162): a list to add to and take
   * from, each with what it reads now, and the delay. */
  private _renderOutside(s: Strings, draft: HealthConfig) {
    const [minDelay, maxDelay] = this._bounds("mains_outside_delay", [30, 3600]);
    return html`<div class="field">
        <span class="lbl">${t(s, "field.mains_outside_entity_ids")}</span>
        ${renderEntityList({
          hass: this.ctx!.hass,
          s,
          chosen: draft.mains_outside_entity_ids,
          candidates: allEntities(this.ctx!.hass),
          listId: "foyer-outside-ups",
          onChange: (next) => this._set("mains_outside_entity_ids", next),
        })}
        <span class="hint">${t(s, "health.mains_outside_hint")}</span>
      </div>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "field.mains_outside_delay")}</span>
          <input
            type="number"
            min=${minDelay}
            max=${maxDelay}
            .value=${String(draft.mains_outside_delay)}
            @input=${(e: Event) => whenNumber(e, (n) => this._set("mains_outside_delay", n))}
          />
          <span class="hint">${t(s, "health.mains_outside_delay_hint")}</span>
        </label>
      </div>`;
  }

  /** Decision 165: how long after a start a zone may take to answer before
   * its fault is news. */
  private _renderStartupGrace(s: Strings, draft: HealthConfig) {
    const [low, high] = this._bounds("startup_grace", [0, 900]);
    return html`<div class="grid-form">
      <label class="field">
        <span class="lbl">${t(s, "field.startup_grace")}</span>
        <input
          type="number"
          min=${low}
          max=${high}
          .value=${String(draft.startup_grace ?? 120)}
          @input=${(e: Event) => whenNumber(e, (n) => this._set("startup_grace", n))}
        />
        <span class="hint">${t(s, "health.startup_grace_hint")}</span>
      </label>
    </div>`;
  }

  private _renderEditor(s: Strings, draft: HealthConfig) {
    const [minInterval, maxInterval] = this._bounds("watchdog_interval", [60, 86400]);
    const [minTimeout, maxTimeout] = this._bounds("watchdog_timeout", [5, 120]);
    const [minFailures, maxFailures] = this._bounds("watchdog_failures", [1, 20]);
    const [minZones, maxZones] = this._bounds("rf_zones", [2, 50]);
    const [minWindow, maxWindow] = this._bounds("rf_window", [5, 3600]);
    const [minConfirm, maxConfirm] = this._bounds("rf_confirm", [0, 3600]);
    return html`<div class="card">
      <div class="card-hd">
        <h2>${t(s, "health.settings")}</h2>
      </div>
      <div class="card-bd">
        ${this._renderEntityList()}
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${t(s, "field.mains_mode")}</span>
            <select
              @change=${(e: Event) =>
                this._set(
                  "mains_mode",
                  (e.target as HTMLSelectElement).value as HealthConfig["mains_mode"],
                )}
            >
              ${(["sensor", "outside_ups"] as const).map(
                (mode) =>
                  html`<option .value=${mode} .selected=${live(draft.mains_mode === mode)}>
                    ${t(s, `health.mains_mode.${mode}`)}
                  </option>`,
              )}
            </select>
            <span class="hint">${t(s, `health.mains_mode_hint.${draft.mains_mode}`)}</span>
          </label>
        </div>
        ${draft.mains_mode === "outside_ups"
          ? this._renderOutside(s, draft)
          : this._renderSensor(s, draft)}
        ${this._renderStartupGrace(s, draft)}

        <fieldset>
          <legend>${t(s, "health.watchdog")}</legend>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(draft.watchdog.enabled)}
              @change=${(e: Event) =>
                this._setWatchdog("enabled", (e.target as HTMLInputElement).checked)}
            />
            <span>${t(s, "health.watchdog_enable")}</span>
          </label>
          <div class="grid-form">
            <label class="field wide">
              <span class="lbl">${t(s, "field.url")}</span>
              <input
                autocomplete="off"
                .value=${live(draft.watchdog.url ?? "")}
                placeholder=${t(
                  s,
                  draft.watchdog.url_set ? "health.url_set_placeholder" : "health.url_placeholder",
                )}
                @input=${(e: Event) =>
                  this._setWatchdog("url", (e.target as HTMLInputElement).value)}
              />
              ${draft.watchdog.url_set
                ? html`<span class="hint">${t(s, "health.url_set_hint")}</span>`
                : nothing}
              <span class="hint">${t(s, "health.url_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.interval")}</span>
              <input
                type="number"
                min=${minInterval}
                max=${maxInterval}
                .value=${String(draft.watchdog.interval)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._setWatchdog("interval", n))}
              />
              <span class="hint">${t(s, "health.interval_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.timeout")}</span>
              <input
                type="number"
                min=${minTimeout}
                max=${maxTimeout}
                .value=${String(draft.watchdog.timeout)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._setWatchdog("timeout", n))}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.failures")}</span>
              <input
                type="number"
                min=${minFailures}
                max=${maxFailures}
                .value=${String(draft.watchdog.failures)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._setWatchdog("failures", n))}
              />
              <span class="hint">${t(s, "health.failures_hint")}</span>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(draft.watchdog.payload)}
              @change=${(e: Event) =>
                this._setWatchdog("payload", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "health.payload")}
              <span class="hint">${t(s, "health.payload_hint")}</span>
            </span>
          </label>
          ${draft.watchdog.payload
            ? html`<div class="warning" role="alert">${t(s, "health.payload_warning")}</div>`
            : nothing}
          <p class="hint">${t(s, "health.watchdog_note")}</p>
        </fieldset>

        <fieldset>
          <legend>${t(s, "health.radios")}</legend>
          <p class="hint">${t(s, "health.radios_hint")}</p>
          ${anyArmed(this.ctx!)
            ? html`<div class="notice" role="note">${t(s, "health.radios_armed")}</div>`
            : nothing}
          ${draft.radios.map((radio, index) => this._renderRadioEditor(s, radio, index))}
          <button class="btn" @click=${() => this._addRadio()}>${t(s, "health.add_radio")}</button>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.rf_zones")}</span>
              <input
                type="number"
                min=${minZones}
                max=${maxZones}
                .value=${String(draft.rf_zones)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._set("rf_zones", n))}
              />
              <span class="hint">${t(s, "health.rf_zones_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.rf_window")}</span>
              <input
                type="number"
                min=${minWindow}
                max=${maxWindow}
                .value=${String(draft.rf_window)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._set("rf_window", n))}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.rf_confirm")}</span>
              <input
                type="number"
                min=${minConfirm}
                max=${maxConfirm}
                .value=${String(draft.rf_confirm)}
                @input=${(e: Event) =>
                  whenNumber(e, (n) => this._set("rf_confirm", n))}
              />
              <span class="hint">${t(s, "health.rf_confirm_hint")}</span>
            </label>
          </div>
        </fieldset>

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
        </div>
      </div>
    </div>`;
  }

  private _renderRadioEditor(s: Strings, radio: RadioConfig, index: number) {
    return html`<div class="radio-row">
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "field.name")}</span>
          <input
            .value=${radio.name}
            @input=${(e: Event) =>
              this._setRadio(index, { name: (e.target as HTMLInputElement).value })}
          />
        </label>
        <label class="field">
          <span class="lbl">${t(s, "field.entry_id")}</span>
          <select
            @change=${(e: Event) => {
              const entry = (e.target as HTMLSelectElement).value;
              const found = this._candidates.find((c) => c.entry_id === entry);
              this._setRadio(index, {
                entry_id: entry,
                name: radio.name || (found?.title ?? ""),
              });
            }}
          >
            <option .value=${""} .selected=${live(!radio.entry_id)}>—</option>
            ${this._candidates.map(
              (candidate) => html`<option
                .value=${candidate.entry_id}
                .selected=${live(candidate.entry_id === radio.entry_id)}
              >
                ${t(s, "health.candidate", {
                  title: candidate.title,
                  zones: String(candidate.zones),
                })}
              </option>`,
            )}
          </select>
          <span class="hint">${t(s, "health.entry_hint")}</span>
        </label>
        <label class="field wide">
          <span class="lbl">${t(s, "field.coordinator_entity_id")}</span>
          <input
            .value=${radio.coordinator_entity_id ?? ""}
            placeholder=${t(s, "health.coordinator_placeholder")}
            @input=${(e: Event) =>
              this._setRadio(index, {
                coordinator_entity_id: (e.target as HTMLInputElement).value || null,
              })}
          />
          <span class="hint">${t(s, "health.coordinator_hint")}</span>
        </label>
      </div>
      <div class="actions">
        <label class="check">
          <input
            type="checkbox"
            .checked=${live(radio.enabled)}
            @change=${(e: Event) =>
              this._setRadio(index, { enabled: (e.target as HTMLInputElement).checked })}
          />
          <span>${t(s, "field.enabled")}</span>
        </label>
        <button class="btn danger" @click=${() => this._removeRadio(index)}>
          ${t(s, "common.delete")}
        </button>
      </div>
    </div>`;
  }

  static override styles = [
    stateStyles,
    formStyles,
    entityListStyles,
    css`
      .tiles {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        margin-bottom: 16px;
      }
      .tile {
        background: var(--card-background-color, #fff);
        border: 1px solid var(--divider-color, #e0e0e0);
        border-left: 4px solid var(--disabled-text-color, #9e9e9e);
        border-radius: 8px;
        padding: 12px 14px;
      }
      .tile.ok {
        border-left-color: var(--success-color, #43a047);
      }
      .tile.warn {
        border-left-color: var(--warning-color, #ffa726);
      }
      .tile.crit {
        border-left-color: var(--error-color, #e53935);
      }
      .tile .name {
        color: var(--secondary-text-color);
        font-size: 12.5px;
      }
      .tile .state {
        font-size: 18px;
        font-weight: 500;
        margin: 2px 0 4px;
      }
      .tile .meta {
        color: var(--secondary-text-color);
        font-size: 12.5px;
        overflow-wrap: anywhere;
      }
      .radio-row {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        margin-bottom: 12px;
        padding: 12px;
      }
      .warning {
        background: color-mix(in srgb, var(--warning-color, #ffa726) 14%, transparent);
        border-left: 3px solid var(--warning-color, #ffa726);
        border-radius: 4px;
        font-size: 13px;
        margin: 8px 0;
        padding: 10px 12px;
      }
      a.btn {
        display: inline-block;
        text-decoration: none;
      }
    `,
  ];
}

define("foyer-page-health", FoyerPageHealth);
