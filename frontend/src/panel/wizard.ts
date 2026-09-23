// The first-run wizard (SPEC §15.1). An empty panel on first open is how
// projects lose people in the first five minutes — but Foyer is never empty:
// the config flow has already made one area, one zone and one scenario. So
// this continues from there rather than starting again, and the steps are
// about finishing: name the area, add the zones that matter, look at the
// scenario, prove a notification actually arrives.
//
// The user step creates the first person and their code, which is what turns
// the log from "the panel disarmed at 03:14" into "Luca did"
// about what protects the house.
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../shared/i18n";
import { formStyles } from "../shared/styles";
import type {
  AreaConfig,
  PageId,
  Problem,
  Trigger,
  ZoneConfig,
  ZoneProposal,
} from "../shared/types";
import { problemText, type PanelContext, whenNumber } from "./context";
import { notifyTargets, stateLabel } from "./ha-targets";

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
    _userName: { state: true },
    _userCode: { state: true },
    _userRepeat: { state: true },
    _zoneType: { state: true },
  };

  ctx?: PanelContext;
  private _step: Step = "area";
  private _userName = "";
  private _userCode = "";
  private _userRepeat = "";
  /** Instant or delayed, for a zone the proposal made one of the two. */
  private _zoneType = "";
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
      const result = await this.ctx.saveSettings({ wizard_done: true });
      if (!result.success) {
        // Said, rather than a wizard that stays with no explanation.
        this._problems = result.problems;
        return;
      }
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
            : this._step === "user" && !this.ctx?.config?.users.length
              ? this._renderUserAction(s)
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
              whenNumber(e, (n) => save({ default_exit_delay: n }))}
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
              whenNumber(e, (n) => save({ default_entry_delay: n }))}
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
            <option value="" .selected=${live(!this._pickedEntity)}>${t(s, "wizard.pick_entity")}</option>
            ${candidates.map(
              (entity) =>
                html`<option .value=${entity.id} .selected=${live(entity.id === this._pickedEntity)}>
                  ${entity.name}
                </option>`,
            )}
          </select>
        </label>
      </div>
      ${proposal ? this._renderProposal(s, proposal) : nothing}
    `;
  }

  /** What Foyer proposes for the entity picked, and the confirmation INV-5
   * asks for. Everything is read live: the point of the check is that
   * somebody opens the door and watches the sentence change, so a state
   * read once when the entity was picked proved nothing (UX review). The
   * state is in the Home Assistant user's own words, with the raw value
   * beside it, because the raw value is what the trigger stores.
   *
   * A sensor that reports a number is not added from here: its trigger is
   * a threshold, and the wizard would have saved "above 0" that nobody had
   * seen (INV-5). The Zones page has the fields for it. */
  private _renderProposal(s: Strings, proposal: ZoneProposal) {
    const ctx = this.ctx!;
    const entity = ctx.hass.states[proposal.entity_id];
    const name = String(entity?.attributes.friendly_name ?? proposal.name);
    if (proposal.trigger_kind === "numeric" || !proposal.proposed.length) {
      return html`<div class="proposal">
        <p>${t(s, `wizard.${proposal.trigger_kind === "numeric" ? "numeric_elsewhere" : "no_proposal_elsewhere"}`)}</p>
        <button class="btn" @click=${() => ctx.navigate("zones")}>
          ${t(s, "wizard.go_zones")}
        </button>
      </div>`;
    }
    const now = entity?.state ?? proposal.state ?? "unavailable";
    const label = (state: string) => stateLabel(ctx.hass, proposal.entity_id, state);
    const choosable = !proposal.zone_type || ["instant", "delayed"].includes(proposal.zone_type);
    const type = this._zoneType || proposal.zone_type || "instant";
    return html`
            <div class="proposal">
              <p>
                ${t(s, "wizard.proposed", {
                  name,
                  state: label(now),
                  states: proposal.proposed.map(label).join(", "),
                })}
              </p>
              ${choosable
                ? html`<div class="grid-form">
                    <label class="field">
                      <span class="lbl">${t(s, "field.type")}</span>
                      <select
                        @change=${(e: Event) =>
                          (this._zoneType = (e.target as HTMLSelectElement).value)}
                      >
                        ${["instant", "delayed"].map(
                          (option) => html`<option
                            .value=${option}
                            .selected=${live(option === type)}
                          >
                            ${t(s, `zone_type.${option}`)}
                          </option>`,
                        )}
                      </select>
                      <span class="hint">${t(s, "wizard.type_hint")}</span>
                    </label>
                  </div>`
                : html`<p class="hint">
                    ${t(s, "wizard.type_fixed", { type: t(s, `zone_type.${type}`) })}
                  </p>`}
              <label class="check">
                <input
                  type="checkbox"
                  .checked=${live(this._confirmed)}
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
    `;
  }

  private async _pick(entityId: string): Promise<void> {
    this._pickedEntity = entityId;
    this._confirmed = false;
    this._proposal = undefined;
    this._zoneType = "";
    if (!entityId || !this.ctx) return;
    try {
      const proposal = await this.ctx.hass.callWS<ZoneProposal>({
        type: "foyer/zone/propose",
        entity_id: entityId,
      });
      // Only for the entity still picked: a slow answer for an earlier pick
      // would otherwise add that entity while the menu shows this one.
      if (this._pickedEntity === entityId) this._proposal = proposal;
    } catch {
      if (this._pickedEntity === entityId) {
        this._problems = [
          { code: "propose_failed", kind: "zone", ref: null, field: "entity_id" },
        ];
      }
    }
  }

  private async _addZone(): Promise<void> {
    const ctx = this.ctx;
    const proposal = this._proposal;
    const area = this._area;
    // A number, or a trigger with no state to confirm, is never saved from
    // here: see _renderProposal (INV-5).
    if (
      !ctx ||
      !proposal ||
      !area ||
      proposal.trigger_kind === "numeric" ||
      !proposal.proposed.length
    ) {
      return;
    }
    const trigger: Trigger =
      proposal.trigger_kind === "event"
        ? {
            kind: "event",
            event_type: proposal.entity_id.startsWith("event.")
              ? (proposal.proposed[0] ?? null)
              : null,
          }
        : { kind: "state", states: [...proposal.proposed] };
    const zone: Partial<ZoneConfig> = {
      name: proposal.name,
      entity_id: proposal.entity_id,
      area_id: area.id!,
      trigger,
      type: this._zoneType || proposal.zone_type || "instant",
    };
    this._busy = true;
    try {
      const result = await ctx.save("zone", zone, true);
      this._problems = result.problems;
      if (result.success) {
        this._proposal = undefined;
        this._pickedEntity = "";
        this._confirmed = false;
        this._zoneType = "";
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

  // --- step 4: the first person, and their code (§8.1) ----------------------------

  /** The one button of the user step, and what it says is what it does
   * (UX review): with a name or a code typed, it creates the person and
   * moves on; with both empty, it skips. "Continue" beside a separate
   * "Create user" threw away a name and a code typed into the form. */
  private _renderUserAction(s: Strings) {
    const typed = this._userName.trim() !== "" || this._userCode !== "";
    return typed
      ? html`<button class="btn primary" ?disabled=${this._busy} @click=${this._createUser}>
          ${t(s, "wizard.user_create_next")}
        </button>`
      : html`<button class="btn primary" ?disabled=${this._busy} @click=${this._next}>
          ${t(s, "wizard.skip")}
        </button>`;
  }

  private async _createUser(): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return;
    // Typed once, a code with a slip in it is a code nobody knows. Only the
    // two fields are compared here; whether the code is acceptable is the
    // backend's to say (INV-2).
    if (this._userCode !== this._userRepeat) {
      this._problems = [{ code: "code_mismatch", kind: "user", ref: null, field: null }];
      return;
    }
    this._busy = true;
    try {
      const result = await ctx.saveUser(
        {
          name: this._userName.trim(),
          has_code: false,
          has_duress_code: false,
          // Linked to whoever is doing the setting up: from now on the panel
          // knows who they are without a code being typed (§8.2).
          ha_user_id: ctx.hass.user?.id ?? null,
          permissions: ctx.meta?.permissions ?? [],
          allowed_area_ids: null,
          allowed_scenario_ids: null,
          valid_from: null,
          valid_until: null,
          code_exempt_when_identified: false,
          enabled: true,
        },
        this._userCode ? { new_code: this._userCode } : {},
      );
      this._problems = result.problems;
      if (result.success) {
        this._userCode = "";
        this._userRepeat = "";
        this._next();
      }
    } finally {
      this._busy = false;
    }
  }

  private _renderUser(s: Strings) {
    const users = this.ctx?.config?.users ?? [];
    const length = this.ctx?.status.security.code_length ?? 6;
    if (users.length) {
      return html`
        <p>${t(s, "wizard.user_text")}</p>
        <div class="notice">
          ${t(s, "wizard.user_done", { name: users[0].name })}
        </div>
      `;
    }
    return html`
      <p>${t(s, "wizard.user_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${t(s, "field.name")}</span>
          <input
            .value=${this._userName}
            @input=${(e: Event) =>
              (this._userName = (e.target as HTMLInputElement).value)}
          />
        </label>
        <label class="field">
          <span class="lbl">${t(s, "users.code")}</span>
          <input
            type="password"
            inputmode="numeric"
            autocomplete="off"
            maxlength=${length}
            .value=${this._userCode}
            @input=${(e: Event) =>
              (this._userCode = (e.target as HTMLInputElement).value)}
          />
          <span class="hint">${t(s, "users.code_hint_new", { n: length })}</span>
        </label>
        <label class="field">
          <span class="lbl">${t(s, "users.code_repeat")}</span>
          <input
            type="password"
            inputmode="numeric"
            autocomplete="off"
            maxlength=${length}
            .value=${this._userRepeat}
            @input=${(e: Event) =>
              (this._userRepeat = (e.target as HTMLInputElement).value)}
          />
        </label>
      </div>
      <p class="hint">${t(s, "wizard.user_hint")}</p>
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
            <option value="" .selected=${live(!this._notifyTarget)}>${t(s, "wizard.pick_target")}</option>
            ${targets.map(
              (target) =>
                html`<option .value=${target.id} .selected=${live(target.id === this._notifyTarget)}>
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
      <div class="actions">
        <button class="btn" @click=${() => ctx.navigate("contacts")}>
          ${t(s, "wizard.go_contacts")}
        </button>
      </div>
      ${this._renderLeft(s)}
    `;
  }

  /** Before "Finish": what the five steps did not cover, each with the page
   * that covers it. Finishing the wizard is not finishing the setup, and a
   * wizard that ends on "done" with two zones and no contact says the
   * opposite (UX review). */
  private _renderLeft(s: Strings) {
    const ctx = this.ctx!;
    const config = ctx.config!;
    const left: { key: string; page: PageId; params?: Record<string, number> }[] = [];
    if (config.zones.length < WANTED_ZONES) {
      left.push({
        key: "wizard.left.zones",
        page: "zones",
        params: { have: config.zones.length, want: WANTED_ZONES },
      });
    }
    if (!config.users.some((u) => u.has_code)) left.push({ key: "wizard.left.users", page: "users" });
    if (!(config.contacts ?? []).length) left.push({ key: "wizard.left.contacts", page: "contacts" });
    return html`<div class="left">
      <h3>${t(s, "wizard.left.title")}</h3>
      ${left.length
        ? html`<ul>
            ${left.map(
              (item) => html`<li>
                <span>${t(s, item.key, item.params)}</span>
                <button class="btn sm" @click=${() => ctx.navigate(item.page)}>
                  ${t(s, `nav.${item.page}`)}
                </button>
              </li>`,
            )}
          </ul>`
        : html`<p class="hint">${t(s, "wizard.left.none")}</p>`}
    </div>`;
  }

  /** Prove a notification arrives — through the real action test (§11.4).
   *
   * It used to call the notify service straight from the browser, which
   * worked and proved almost nothing: it tested the browser's session
   * rather than Foyer's path, and it left no trace. Now it goes where every
   * other test goes, so it is verified server-side, gated by the
   * `test_actions` permission and recorded in the log as a test.
   */
  private async _sendTest(): Promise<void> {
    const ctx = this.ctx;
    if (!ctx || !this._notifyTarget) return;
    this._busy = true;
    this._sent = false;
    try {
      const result = await ctx.testAction({
        service: this._notifyTarget,
        message: t(ctx.strings, "wizard.test_message"),
      });
      this._sent = result.success;
      if (!result.success) {
        this._problems = [
          {
            code: "request_failed",
            kind: "notify",
            ref: null,
            field: null,
            detail: result.error ?? result.reason ?? "",
          },
        ];
      }
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
      .left {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid var(--divider-color);
      }
      .left h3 {
        margin: 0 0 8px;
        font-size: 14px;
        font-weight: 500;
      }
      .left ul {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
        font-size: 13.5px;
      }
      .left li {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }
    `,
  ];
}

if (!customElements.get("foyer-wizard")) {
  customElements.define("foyer-wizard", FoyerWizard);
}
