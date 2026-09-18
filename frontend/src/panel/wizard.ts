// The first-run wizard (SPEC §15.1). An empty panel on first open is how
// projects lose people in the first five minutes — but Foyer is never empty:
// the config flow has already made one area, one zone and one scenario. So
// this continues from there rather than starting again, and the steps are
// about finishing: name the area, add the zones that matter, look at the
// scenario, prove a notification actually arrives.
//
// The user step of §15.1 is shown and skipped, in as many words: codes and
// users are Phase 2, and a wizard that pretends otherwise would be lying
// about what protects the house.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../shared/i18n";
import { formStyles } from "../shared/styles";
import type { AreaConfig, Problem, Trigger, ZoneConfig, ZoneProposal } from "../shared/types";
import { problemText, type PanelContext } from "./context";
import { notifyTargets } from "./ha-targets";

type Step = "area" | "zones" | "scenario" | "user" | "test";

const STEPS: Step[] = ["area", "zones", "scenario", "user", "test"];

// Three zones is what §15.1 asks for, and the config flow has made one.
const WANTED_ZONES = 3;

class FoyerWizard extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _step: { state: true },
    _busy: { state: true },
    _problems: { state: true },
    _proposal: { state: true },
    _confirmed: { state: true },
    _pickedEntity: { state: true },
    _notifyTarget: { state: true },
    _sent: { state: true },
  };

  ctx?: PanelContext;
  private _step: Step = "area";
  private _busy = false;
  private _problems: Problem[] = [];
  private _proposal?: ZoneProposal;
  private _confirmed = false;
  private _pickedEntity = "";
  private _notifyTarget = "";
  private _sent = false;

  private get _area(): AreaConfig | undefined {
    return this.ctx?.config?.areas[0];
  }

  private _next(): void {
    const index = STEPS.indexOf(this._step);
    this._problems = [];
    if (index < STEPS.length - 1) this._step = STEPS[index + 1];
  }

  private _back(): void {
    const index = STEPS.indexOf(this._step);
    this._problems = [];
    if (index > 0) this._step = STEPS[index - 1];
  }

  /** Completed or dismissed: either way the panel stops offering it. The
   * flag lives in the configuration, not in a per-user preference — it is
   * the installation that has been set up, not the person looking at it. */
  private async _finish(): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    try {
      await this.ctx.saveSettings({ wizard_done: true });
      this.dispatchEvent(new CustomEvent("wizard-done", { bubbles: true, composed: true }));
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    return html`
      <section class="wizard">
        <header>
          <h2>${t(s, "wizard.title")}</h2>
          <button class="btn" ?disabled=${this._busy} @click=${this._finish}>
            ${t(s, "wizard.dismiss")}
          </button>
        </header>
        <p class="intro">${t(s, "wizard.intro")}</p>
        <ol class="steps">
          ${STEPS.map((step, index) => {
            const at = STEPS.indexOf(this._step);
            const state = index < at ? "done" : index === at ? "active" : "";
            return html`<li class=${state}>
              <span class="n">${index + 1}</span>${t(s, `wizard.step.${step}`)}
            </li>`;
          })}
        </ol>
        <div class="body">${this._renderStep(s)}</div>
        ${this._problems.length
          ? html`<div class="problems" role="alert">
              <ul>
                ${this._problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
              </ul>
            </div>`
          : nothing}
        <div class="actions">
          <button
            class="btn"
            ?disabled=${this._busy || this._step === STEPS[0]}
            @click=${this._back}
          >
            ${t(s, "wizard.back")}
          </button>
          <span class="spacer"></span>
          ${this._step === "test"
            ? html`<button class="btn primary" ?disabled=${this._busy} @click=${this._finish}>
                ${t(s, "wizard.done")}
              </button>`
            : html`<button class="btn primary" ?disabled=${this._busy} @click=${this._next}>
                ${t(s, "wizard.next")}
              </button>`}
        </div>
      </section>
    `;
  }

  private _renderStep(s: Strings) {
    switch (this._step) {
      case "area":
        return this._renderArea(s);
      case "zones":
        return this._renderZones(s);
      case "scenario":
        return this._renderScenario(s);
      case "user":
        return this._renderUser(s);
      default:
        return this._renderTest(s);
    }
  }

  // --- step 1: the area the config flow already made -------------------------------

  private _renderArea(s: Strings) {
    const area = this._area;
    if (!area) return html`<p class="hint">${t(s, "wizard.no_area")}</p>`;
    const save = (changes: Partial<AreaConfig>) => this._saveArea({ ...area, ...changes });
    return html`
      <p>${t(s, "wizard.area_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "field.name")}</span>
          <input
            .value=${area.name}
            @change=${(e: Event) => save({ name: (e.target as HTMLInputElement).value.trim() })}
          />
        </label>
        <label class="field">
          <span class="lbl">${t(s, "field.default_exit_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(area.default_exit_delay)}
            @change=${(e: Event) =>
              save({ default_exit_delay: Number((e.target as HTMLInputElement).value) })}
          />
          <span class="hint">${t(s, "wizard.exit_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${t(s, "field.default_entry_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(area.default_entry_delay)}
            @change=${(e: Event) =>
              save({ default_entry_delay: Number((e.target as HTMLInputElement).value) })}
          />
          <span class="hint">${t(s, "wizard.entry_hint")}</span>
        </label>
      </div>
    `;
  }

  private async _saveArea(area: AreaConfig): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("area", area);
      this._problems = result.problems;
    } finally {
      this._busy = false;
    }
  }

  // --- step 2: the zones that matter (INV-5 on every one) --------------------------

  private _renderZones(s: Strings) {
    const ctx = this.ctx!;
    const zones = ctx.config!.zones;
    const proposal = this._proposal;
    const domains = ctx.meta?.zone_domains ?? [];
    const candidates = Object.values(ctx.hass.states)
      .filter((e) => domains.includes(e.entity_id.split(".")[0]))
      .filter((e) => !zones.some((z) => z.entity_id === e.entity_id))
      .map((e) => ({
        id: e.entity_id,
        name: String(e.attributes.friendly_name ?? e.entity_id),
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
    return html`
      <p>${t(s, "wizard.zones_text", { have: zones.length, want: WANTED_ZONES })}</p>
      <ul class="zones">
        ${zones.map(
          (zone) => html`<li>
            <strong>${zone.name}</strong>
            <span class="mono">${zone.entity_id}</span>
            <span class="tag">${t(s, `zone_type.${zone.type}`)}</span>
          </li>`,
        )}
      </ul>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "wizard.add_zone")}</span>
          <select
            @change=${(e: Event) => this._pick((e.target as HTMLSelectElement).value)}
          >
            <option value="" ?selected=${!this._pickedEntity}>${t(s, "wizard.pick_entity")}</option>
            ${candidates.map(
              (entity) =>
                html`<option .value=${entity.id} ?selected=${entity.id === this._pickedEntity}>
                  ${entity.name}
                </option>`,
            )}
          </select>
        </label>
      </div>
      ${proposal
        ? html`
            <div class="proposal">
              <p>
                ${t(s, "wizard.proposed", {
                  entity: proposal.entity_id,
                  state: proposal.state ?? "",
                  type: t(s, `zone_type.${proposal.zone_type ?? "instant"}`),
                  states: proposal.proposed.join(", "),
                })}
              </p>
              <label class="check">
                <input
                  type="checkbox"
                  .checked=${this._confirmed}
                  @change=${(e: Event) =>
                    (this._confirmed = (e.target as HTMLInputElement).checked)}
                />
                <span>${t(s, "wizard.confirm_trigger")}</span>
              </label>
              <p class="hint">${t(s, "wizard.confirm_hint")}</p>
              <button
                class="btn"
                ?disabled=${this._busy || !this._confirmed}
                @click=${this._addZone}
              >
                ${t(s, "wizard.add")}
              </button>
            </div>
          `
        : nothing}
    `;
  }

  private async _pick(entityId: string): Promise<void> {
    this._pickedEntity = entityId;
    this._confirmed = false;
    this._proposal = undefined;
    if (!entityId || !this.ctx) return;
    this._proposal = await this.ctx.hass.callWS<ZoneProposal>({
      type: "foyer/zone/propose",
      entity_id: entityId,
    });
  }

  private async _addZone(): Promise<void> {
    const ctx = this.ctx;
    const proposal = this._proposal;
    const area = this._area;
    if (!ctx || !proposal || !area) return;
    const trigger: Trigger =
      proposal.trigger_kind === "event"
        ? {
            kind: "event",
            event_type: proposal.entity_id.startsWith("event.")
              ? (proposal.proposed[0] ?? null)
              : null,
          }
        : proposal.trigger_kind === "numeric"
          ? { kind: "numeric", operator: "gt", value: 0, hysteresis: 0, attribute: null }
          : { kind: "state", states: [...proposal.proposed] };
    const zone: Partial<ZoneConfig> = {
      name: proposal.name,
      entity_id: proposal.entity_id,
      area_id: area.id!,
      trigger,
      type: proposal.zone_type ?? "instant",
    };
    this._busy = true;
    try {
      const result = await ctx.save("zone", zone, true);
      this._problems = result.problems;
      if (result.success) {
        this._proposal = undefined;
        this._pickedEntity = "";
        this._confirmed = false;
      }
    } finally {
      this._busy = false;
    }
  }

  // --- step 3: the scenario --------------------------------------------------------

  private _renderScenario(s: Strings) {
    const ctx = this.ctx!;
    const scenario = ctx.config!.scenarios[0];
    if (!scenario) return html`<p class="hint">${t(s, "wizard.no_scenario")}</p>`;
    const areas = ctx.config!.areas;
    return html`
      <p>${t(s, "wizard.scenario_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "field.name")}</span>
          <input
            .value=${scenario.name}
            @change=${async (e: Event) => {
              const name = (e.target as HTMLInputElement).value.trim();
              this._busy = true;
              try {
                const result = await ctx.save("scenario", { ...scenario, name });
                this._problems = result.problems;
              } finally {
                this._busy = false;
              }
            }}
          />
        </label>
      </div>
      <p class="hint">
        ${t(s, "wizard.scenario_areas", {
          areas: areas
            .filter((a) => scenario.areas.includes(a.id!))
            .map((a) => a.name)
            .join(", "),
        })}
      </p>
    `;
  }

  // --- step 4: users and codes, which are not this phase's ------------------------

  private _renderUser(s: Strings) {
    return html`
      <p>${t(s, "wizard.user_text")}</p>
      <div class="notice">${t(s, "wizard.user_skipped")}</div>
    `;
  }

  // --- step 5: prove a notification actually arrives -------------------------------

  private _renderTest(s: Strings) {
    const ctx = this.ctx!;
    const targets = notifyTargets(ctx.hass);
    return html`
      <p>${t(s, "wizard.test_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "wizard.test_target")}</span>
          <select
            @change=${(e: Event) => {
              this._notifyTarget = (e.target as HTMLSelectElement).value;
              this._sent = false;
            }}
          >
            <option value="" ?selected=${!this._notifyTarget}>${t(s, "wizard.pick_target")}</option>
            ${targets.map(
              (target) =>
                html`<option .value=${target.id} ?selected=${target.id === this._notifyTarget}>
                  ${target.name}
                </option>`,
            )}
          </select>
        </label>
      </div>
      <button
        class="btn"
        ?disabled=${this._busy || !this._notifyTarget}
        @click=${this._sendTest}
      >
        ${t(s, "wizard.send_test")}
      </button>
      ${this._sent ? html`<div class="notice">${t(s, "wizard.test_sent")}</div>` : nothing}
      <p class="hint">${t(s, "wizard.test_hint")}</p>
    `;
  }

  private async _sendTest(): Promise<void> {
    const ctx = this.ctx;
    if (!ctx || !this._notifyTarget) return;
    this._busy = true;
    this._sent = false;
    try {
      const message = t(ctx.strings, "wizard.test_message");
      const target = this._notifyTarget;
      if (target.startsWith("notify.") && ctx.hass.states[target]) {
        // A notify *entity*: one service for all of them.
        await ctx.hass.callService("notify", "send_message", {
          entity_id: target,
          message,
        });
      } else {
        const [domain, service] = target.split(".");
        await ctx.hass.callService(domain, service, { message });
      }
      this._sent = true;
    } catch (err) {
      this._problems = [
        {
          code: "request_failed",
          kind: "notify",
          ref: null,
          field: null,
          detail: String((err as { message?: string })?.message ?? err),
        },
      ];
    } finally {
      this._busy = false;
    }
  }

  static override styles = [
    formStyles,
    css`
      .wizard {
        background: var(--card-background-color);
        border: 1px solid var(--primary-color);
        border-radius: var(--ha-card-border-radius, 12px);
        padding: 16px;
        margin-bottom: 16px;
      }
      header {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      h2 {
        margin: 0;
        flex: 1;
        font-size: 17px;
        font-weight: 500;
      }
      .intro {
        color: var(--secondary-text-color);
        font-size: 13.5px;
        max-width: 72ch;
      }
      ol.steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 16px;
        list-style: none;
        margin: 12px 0;
        padding: 0;
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      ol.steps li {
        display: flex;
        align-items: center;
        gap: 6px;
      }
      ol.steps li.active {
        color: var(--primary-text-color);
        font-weight: 500;
      }
      .n {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--secondary-background-color);
        font-size: 12px;
      }
      ol.steps li.active .n {
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      ol.steps li.done .n {
        background: var(--success-color, #2e9e4f);
        color: var(--text-primary-color, #fff);
      }
      .body {
        border-top: 1px solid var(--divider-color);
        padding-top: 12px;
      }
      ul.zones {
        list-style: none;
        margin: 8px 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 13.5px;
      }
      ul.zones li {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
      }
      .proposal {
        margin-top: 12px;
        padding: 12px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
      }
      .spacer {
        flex: 1;
      }
    `,
  ];
}

if (!customElements.get("foyer-wizard")) {
  customElements.define("foyer-wizard", FoyerWizard);
}
