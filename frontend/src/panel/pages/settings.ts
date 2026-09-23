// Page 11 — Settings (SPEC §15.1): the global defaults, the response block,
// the chime (§6.6), what the event log records and keeps (§10.2, §10.3), the
// configuration backup, and the language of the messages Foyer sends out.
import { LitElement, css, html, nothing } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../../shared/i18n";
import { formStyles } from "../../shared/styles";
import type {
  AlarmoLabels,
  AlarmoLine,
  AlarmoPreview,
  ChimeConfig,
  ChimeTarget,
  LogSettingsConfig,
  Problem,
  SettingsConfig,
} from "../../shared/types";
import { download, optionalNumber, problemText, type PanelContext, whenNumber } from "../context";
import { chimeTargets, entityTargets } from "../ha-targets";

// What the switch starts at when somebody turns it on. Thirty days is the
// retention every category has by default, so names age out with the rows
// rather than before them.
const DEFAULT_PSEUDONYMISE_DAYS = 30;

const NO_CHIME: ChimeConfig = {
  targets: [],
  mode: "sound",
  sound: null,
  tts_entity: null,
  volume: null,
  quiet_start: null,
  quiet_end: null,
  during_exit: false,
};

class FoyerPageSettings extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _settings: { state: true },
    _problems: { state: true },
    _busy: { state: true },
    _saved: { state: true },
    _restored: { state: true },
    _confirmPseudonymise: { state: true },
    _languages: { state: true },
    _alarmo: { state: true },
    _alarmoDone: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: ChimeConfig;
  private _settings?: SettingsConfig;
  private _problems: Problem[] = [];
  private _busy = false;
  private _saved = false;
  private _restored = false;
  // Switching timed pseudonymisation on is destructive from the first sweep,
  // which runs at the next start — and a configuration save is a restart.
  // So it is confirmed, like erasing somebody, rather than acted on from a
  // tick nobody meant (found in review).
  private _confirmPseudonymise = false;
  // Read from the files on disk, each named in itself, so that a language is
  // added by copying two files and never by editing a list here (§20.3).
  private _languages: { code: string; name: string }[] = [];
  // The Alarmo importer's preview, until it is applied or read again.
  private _alarmo?: AlarmoPreview;
  private _alarmoDone = false;

  override connectedCallback(): void {
    super.connectedCallback();
    void this.ctx?.hass
      .callWS<{ languages: { code: string; name: string }[] }>({
        type: "foyer/languages",
      })
      .then((result) => (this._languages = result.languages))
      .catch(() => (this._languages = []));
  }

  private get _chime(): ChimeConfig {
    return this._draft ?? structuredClone(this.ctx?.config?.chime ?? NO_CHIME);
  }

  private _set<K extends keyof ChimeConfig>(key: K, value: ChimeConfig[K]): void {
    this._draft = { ...this._chime, [key]: value };
    this._saved = false;
  }

  private _target(entityId: string): ChimeTarget | undefined {
    return this._chime.targets.find((target) => target.entity_id === entityId);
  }

  private _setTarget(entityId: string, changes: Partial<ChimeTarget>): void {
    this._set(
      "targets",
      this._chime.targets.map((target) =>
        target.entity_id === entityId ? { ...target, ...changes } : target,
      ),
    );
  }

  private _toggleTarget(entityId: string, on: boolean): void {
    const targets = this._chime.targets.filter((t2) => t2.entity_id !== entityId);
    if (on) targets.push({ entity_id: entityId, quiet_start: null, quiet_end: null });
    this._set("targets", targets);
  }

  private async _save(): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    try {
      const result = await this.ctx.saveChime(this._chime);
      this._problems = result.problems;
      if (result.success) {
        this._draft = undefined;
        this._saved = true;
      }
    } finally {
      this._busy = false;
    }
  }

  private async _saveSettings(changes: Partial<SettingsConfig>): Promise<void> {
    if (!this.ctx?.config) return;
    this._settings = {
      ...(this._settings ?? this.ctx.config.settings),
      ...changes,
    };
    this._busy = true;
    try {
      const result = await this.ctx.saveSettings(this._settings);
      this._problems = result.problems;
      if (result.success) this._settings = undefined;
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    return html`${this._renderDefaults(ctx.strings)} ${this._renderResponse(ctx.strings)}
    ${this._renderChime(ctx.strings, this._chime)} ${this._renderLog(ctx.strings)}
    ${this._renderPrivacy(ctx.strings)} ${this._renderBackup(ctx.strings)}
    ${this._renderAlarmo(ctx.strings)} ${this._renderLanguage(ctx.strings)}`;
  }

  private _entities(domains: string[]): { id: string; name: string }[] {
    return entityTargets(this.ctx!.hass, domains);
  }


  // --- global defaults (§15.1) -----------------------------------------------------

  private _renderDefaults(s: Strings) {
    const ctx = this.ctx!;
    const settings = this._settings ?? ctx.config!.settings;
    const bounds = ctx.meta?.bounds ?? {};
    const number = (
      key:
        | "siren_duration"
        | "arm_hold_timeout"
        | "default_entry_delay"
        | "default_exit_delay"
        | "low_battery_threshold"
        | "walk_test_timeout",
      range: [number, number] | undefined,
      hint?: string,
    ) => html`<label class="field">
      <span class="lbl">${t(s, `field.${key}`)}</span>
      <input
        type="number"
        min=${range ? range[0] : 0}
        max=${range ? range[1] : 3600}
        .value=${live(String(settings[key]))}
        @change=${(e: Event) =>
          // Emptied is "not changed": Number("") is 0, which saved a delay of
          // no seconds at all (second review).
          whenNumber(e, (n) => void this._saveSettings({ [key]: n }))}
      />
      <span class="hint">${hint ?? t(s, "common.seconds_unit")}</span>
    </label>`;
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "settings.defaults_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${t(s, "settings.defaults_intro")}</p>
          <div class="grid-form">
            ${number("siren_duration", bounds.siren_duration, t(s, "settings.siren_duration_hint"))}
            ${number("arm_hold_timeout", bounds.arm_hold_timeout, t(s, "settings.arm_hold_hint"))}
            ${number("default_entry_delay", bounds.entry_delay, t(s, "settings.area_defaults_hint"))}
            ${number("default_exit_delay", bounds.exit_delay, t(s, "settings.area_defaults_hint"))}
            ${number(
              "low_battery_threshold",
              bounds.low_battery_threshold,
              t(s, "settings.low_battery_hint"),
            )}
            ${number(
              "walk_test_timeout",
              bounds.walk_test_timeout,
              t(s, "settings.walk_test_hint"),
            )}
          </div>
        </div>
      </div>
    `;
  }

  // --- the event log (§10.2, §10.3) ------------------------------------------------

  private _renderLog(s: Strings) {
    const ctx = this.ctx!;
    const settings = this._settings ?? ctx.config!.settings;
    const log = settings.log;
    const categories = ctx.meta?.log_categories ?? [];
    const [min, max] = ctx.meta?.retention_bounds ?? [1, 3650];
    const change = (changes: Partial<LogSettingsConfig>) => {
      const next: LogSettingsConfig = {
        ...log,
        ...changes,
        enabled: { ...log.enabled, ...(changes.enabled ?? {}) },
        retention_days: { ...log.retention_days, ...(changes.retention_days ?? {}) },
      };
      void this._saveSettings({ log: next });
    };
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "settings.log_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${t(s, "settings.log_intro")}</p>
          <div class="rows">
            ${categories.map((category) => {
              const on = log.enabled[category] !== false;
              return html`<div class="row">
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${live(on)}
                    @change=${(e: Event) =>
                      change({
                        enabled: { [category]: (e.target as HTMLInputElement).checked },
                      })}
                  />
                  <span>${t(s, `category.${category}`)}</span>
                </label>
                <span class="spacer"></span>
                ${on
                  ? html`<label class="field inline">
                      <input
                        type="number"
                        min=${min}
                        max=${max}
                        .value=${live(String(log.retention_days[category] ?? 30))}
                        @change=${(e: Event) =>
                          whenNumber(e, (days) =>
                            change({ retention_days: { [category]: days } }),
                          )}
                      />
                      <span class="hint">${t(s, "settings.log_days")}</span>
                    </label>`
                  : html`<span class="hint">${t(s, "settings.log_off")}</span>`}
              </div>`;
            })}
          </div>
          <p class="hint">${t(s, "settings.log_rows_hint")}</p>
          <div class="actions">
            <button
              class="btn"
              ?disabled=${this._busy}
              @click=${() =>
                change({
                  retention_days: Object.fromEntries(
                    (ctx.meta?.named_categories ?? []).map((category) => [
                      category,
                      ctx.meta?.short_retention ?? 7,
                    ]),
                  ),
                })}
            >
              ${t(s, "settings.short_preset", { days: ctx.meta?.short_retention ?? 7 })}
            </button>
          </div>
          <p class="hint">
            ${t(s, "settings.short_preset_hint", {
              days: ctx.meta?.short_retention ?? 7,
              categories: (ctx.meta?.named_categories ?? [])
                .map((category) => t(s, `category.${category}`))
                .join(", "),
            })}
          </p>
        </div>
      </div>
    `;
  }

  // --- personal data in the log (§10.4) ---------------------------------------------

  /** Timed pseudonymisation, and the question §16 says to ask rather than
   * guess. Both are here rather than on page 10 because both are settings of
   * the installation: what page 10 does is act on one person, once. */
  private _renderPrivacy(s: Strings) {
    const ctx = this.ctx!;
    const settings = this._settings ?? ctx.config!.settings;
    const log = settings.log;
    const [min, max] = ctx.meta?.pseudonymise_bounds ?? [1, 365];
    const on = log.pseudonymise_after !== null;
    const change = (changes: Partial<LogSettingsConfig>) =>
      void this._saveSettings({ log: { ...log, ...changes } });
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "settings.privacy_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${t(s, "settings.privacy_intro")}</p>
          <div class="row">
            <label class="check">
              <input
                type="checkbox"
                .checked=${live(on || this._confirmPseudonymise)}
                @change=${(e: Event) => {
                  if ((e.target as HTMLInputElement).checked) {
                    this._confirmPseudonymise = true;
                  } else {
                    this._confirmPseudonymise = false;
                    change({ pseudonymise_after: null });
                  }
                }}
              />
              <span>${t(s, "settings.pseudonymise")}</span>
            </label>
            <span class="spacer"></span>
            ${on
              ? html`<label class="field inline">
                  <input
                    type="number"
                    min=${min}
                    max=${max}
                    .value=${String(log.pseudonymise_after ?? 30)}
                    @change=${(e: Event) => {
                      const days = Number((e.target as HTMLInputElement).value);
                      if (Number.isFinite(days)) change({ pseudonymise_after: days });
                    }}
                  />
                  <span class="hint">${t(s, "settings.log_days")}</span>
                </label>`
              : nothing}
          </div>
          <div class="notice">${t(s, "settings.pseudonymise_warning")}</div>
          ${this._confirmPseudonymise
            ? html`<div class="problems" role="alert">
                <p>${t(s, "settings.pseudonymise_confirm", { days: 30 })}</p>
                <div class="actions">
                  <button
                    class="btn danger"
                    @click=${() => {
                      this._confirmPseudonymise = false;
                      change({ pseudonymise_after: DEFAULT_PSEUDONYMISE_DAYS });
                    }}
                  >
                    ${t(s, "settings.pseudonymise_yes")}
                  </button>
                  <button
                    class="btn"
                    @click=${() => (this._confirmPseudonymise = false)}
                  >
                    ${t(s, "common.cancel")}
                  </button>
                </div>
              </div>`
            : nothing}
          <p class="hint">${t(s, "settings.pseudonymise_hint")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(log.delete_on_uninstall)}
              @change=${(e: Event) =>
                change({ delete_on_uninstall: (e.target as HTMLInputElement).checked })}
            />
            <span>${t(s, "settings.delete_on_uninstall")}</span>
          </label>
          <p class="hint">${t(s, "settings.delete_on_uninstall_hint")}</p>
          <p class="hint">${t(s, "settings.uninstall_snapshots_hint")}</p>
        </div>
      </div>
    `;
  }

  // --- backup and restore (§15.1) --------------------------------------------------

  private _renderBackup(s: Strings) {
    const ctx = this.ctx!;
    const version = (ctx.meta?.schema_version ?? []).join(".");
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "settings.backup_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${t(s, "settings.backup_intro")}</p>
          <div class="actions">
            <button class="btn" ?disabled=${this._busy} @click=${this._exportConfig}>
              ${t(s, "settings.backup_export")}
            </button>
            <label class="btn file">
              ${t(s, "settings.backup_import")}
              <input type="file" accept="application/json,.json" @change=${this._importConfig} />
            </label>
          </div>
          <p class="hint">${t(s, "settings.backup_hint")}</p>
          <p class="hint">${t(s, "settings.backup_version", { version })}</p>
          ${this._restored
            ? html`<div class="notice">${t(s, "settings.backup_restored")}</div>`
            : nothing}
        </div>
      </div>
    `;
  }

  private async _exportConfig(): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    try {
      const result = await this.ctx.exportConfig();
      download(
        result.filename,
        JSON.stringify(result.document, null, 2),
        "application/json",
      );
    } catch (err) {
      // Refused or dropped: said, rather than a button that did nothing.
      this._problems = [
        {
          code: "request_failed",
          kind: "config",
          ref: null,
          field: null,
          detail: String((err as { message?: string })?.message ?? err),
        },
      ];
    } finally {
      this._busy = false;
    }
  }

  private async _importConfig(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = "";
    if (!file || !this.ctx) return;
    this._busy = true;
    this._restored = false;
    try {
      const text = await file.text();
      const result = await this.ctx.importConfig(JSON.parse(text));
      this._problems = result.problems;
      this._restored = result.success;
    } catch {
      // A file that is not JSON at all never reaches the backend, and gets
      // the same answer the backend would give it.
      this._problems = [
        { code: "not_a_foyer_backup", kind: "config", ref: null, field: null },
      ];
    } finally {
      this._busy = false;
    }
  }

  // --- importing from Alarmo (§20.2) -----------------------------------------------

  /** The words new areas, scenarios and profiles are named with, in the
   * language of whoever pressed the button. */
  private _alarmoLabels(s: Strings): AlarmoLabels {
    const modes = [
      "armed_away",
      "armed_home",
      "armed_night",
      "armed_vacation",
      "armed_custom_bypass",
    ];
    return {
      modes: Object.fromEntries(modes.map((m) => [m, t(s, `alarmo.mode.${m}`)])),
      split: t(s, "alarmo.split_name"),
      profile: t(s, "alarmo.profile_name"),
    };
  }

  /** A report line in words. Values that are identifiers — a mode, a
   * setting, a kind — are translated too; names are shown as they are. */
  private _alarmoText(s: Strings, group: "line" | "refused", line: AlarmoLine): string {
    const words: Record<string, string> = {
      mode: "alarmo.mode",
      setting: "alarmo.setting",
      kind: "alarmo.kind",
      type: "alarmo.sensor_type",
    };
    const params = Object.fromEntries(
      Object.entries(line.params).map(([key, value]) => [
        key,
        key in words ? t(s, `${words[key]}.${value}`) : value,
      ]),
    );
    return t(s, `alarmo.${group}.${line.code}`, params);
  }

  private async _alarmoRead(): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    this._alarmoDone = false;
    try {
      this._alarmo = await this.ctx.alarmoPreview(this._alarmoLabels(this.ctx.strings));
    } catch (err) {
      // Refused (a permission, a reload) or failed outright: said as what it
      // is, never as a file that could not be read.
      const detail = String((err as { message?: string })?.message ?? err);
      this._alarmo = {
        success: false,
        problems: [{ code: "request_failed", kind: "config", ref: null, field: null, detail }],
      };
    } finally {
      this._busy = false;
    }
  }

  private async _alarmoApply(): Promise<void> {
    const fingerprint = this._alarmo?.fingerprint;
    if (!this.ctx || !fingerprint) return;
    this._busy = true;
    try {
      const result = await this.ctx.alarmoApply(
        fingerprint,
        this._alarmoLabels(this.ctx.strings),
      );
      if (result.success) {
        this._alarmo = undefined;
        this._alarmoDone = true;
      } else {
        // The report stays on screen; what refused the apply is added to it.
        this._alarmo = {
          ...this._alarmo!,
          success: false,
          refused: result.refused,
          problems: result.problems ?? [],
        };
      }
    } finally {
      this._busy = false;
    }
  }

  private _renderAlarmo(s: Strings) {
    const preview = this._alarmo;
    const created = preview?.created;
    const list = (key: keyof NonNullable<AlarmoPreview["created"]>) =>
      created && created[key].length
        ? html`<li>${t(s, `alarmo.created.${key}`, { names: created[key].join(", ") })}</li>`
        : nothing;
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "alarmo.title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${t(s, "alarmo.intro")}</p>
          <div class="actions">
            <button class="btn" ?disabled=${this._busy} @click=${this._alarmoRead}>
              ${t(s, "alarmo.read")}
            </button>
            ${preview?.fingerprint
              ? html`<button
                  class="btn primary"
                  ?disabled=${this._busy || !preview.success}
                  @click=${this._alarmoApply}
                >
                  ${t(s, "alarmo.apply")}
                </button>`
              : nothing}
          </div>
          ${this._alarmoDone
            ? html`<div class="notice" role="status">${t(s, "alarmo.applied")}</div>`
            : nothing}
          ${preview?.refused
            ? html`<div class="problems" role="alert">
                ${this._alarmoText(s, "refused", preview.refused)}
              </div>`
            : nothing}
          ${preview?.problems?.length
            ? html`<div class="problems" role="alert">
                <ul>
                  ${preview.problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
                </ul>
              </div>`
            : nothing}
          ${created
            ? html`<h3>${t(s, "alarmo.summary_title")}</h3>
                <ul class="alarmo-list">
                  ${list("areas")}
                  <li>
                    ${t(s, "alarmo.created.zones", { count: preview?.counts?.zones ?? 0 })}
                  </li>
                  ${list("scenarios")} ${list("extended")} ${list("people")}
                  ${list("profiles")}
                </ul>`
            : nothing}
          ${preview?.lines?.length
            ? html`<h3>${t(s, "alarmo.report_title")}</h3>
                <ul class="alarmo-list">
                  ${preview.lines.map(
                    (line) => html`<li>${this._alarmoText(s, "line", line)}</li>`,
                  )}
                </ul>`
            : nothing}
          <p class="hint">${t(s, "alarmo.hint")}</p>
        </div>
      </div>
    `;
  }

  // --- language of the messages Foyer sends out ------------------------------------

  private _renderLanguage(s: Strings) {
    const ctx = this.ctx!;
    const settings = this._settings ?? ctx.config!.settings;
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "settings.language_title")}</h2></div>
        <div class="card-bd">
          <label class="field">
            <span class="lbl">${t(s, "field.language")}</span>
            <select
              @change=${(e: Event) =>
                this._saveSettings({
                  language: (e.target as HTMLSelectElement).value || null,
                })}
            >
              <option value="" .selected=${live(!settings.language)}>
                ${t(s, "settings.language_system")}
              </option>
              ${settings.language &&
              !this._languages.some((language) => language.code === settings.language)
                ? html`<option .value=${settings.language} selected>
                    ${settings.language}
                  </option>`
                : nothing}
              ${this._languages.map(
                (language) =>
                  html`<option
                    .value=${language.code}
                    .selected=${live(language.code === settings.language)}
                  >
                    ${language.name}
                  </option>`,
              )}
            </select>
            <span class="hint">${t(s, "settings.language_hint")}</span>
          </label>
          ${this._problems.length
            ? html`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
                </ul>
              </div>`
            : nothing}
        </div>
      </div>
    `;
  }

  // --- response defaults (SPEC §6, part 3 decisions 2, 6 and 7) -------------------

  private _renderResponse(s: Strings) {
    const ctx = this.ctx!;
    const settings = this._settings ?? ctx.config!.settings;
    const profiles = ctx.config!.profiles ?? [];
    const silenceable = ctx.meta?.silenceable ?? [];
    const pick = (key: "default_profile_id" | "technical_profile_id", hint: string) =>
      html`<label class="field">
        <span class="lbl">${t(s, `field.${key}`)}</span>
        <select
          @change=${(e: Event) =>
            this._saveSettings({
              [key]: (e.target as HTMLSelectElement).value || null,
            })}
        >
          <option value="" .selected=${live(!settings[key])}>${t(s, "settings.none")}</option>
          ${profiles.map(
            (profile) =>
              html`<option .value=${profile.id ?? ""} .selected=${live(profile.id === settings[key])}>
                ${profile.name}
              </option>`,
          )}
        </select>
        <span class="hint">${hint}</span>
      </label>`;
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "settings.response_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${t(s, "settings.response_intro")}</p>
          <div class="grid-form">
            ${pick("default_profile_id", t(s, "settings.default_profile_hint"))}
            ${pick("technical_profile_id", t(s, "settings.technical_profile_hint"))}
            <label class="field">
              <span class="lbl">${t(s, "field.camera_dir")}</span>
              <input
                .value=${settings.camera_dir}
                @change=${(e: Event) =>
                  this._saveSettings({
                    camera_dir: (e.target as HTMLInputElement).value.trim(),
                  })}
              />
              <span class="hint">${t(s, "settings.camera_dir_hint")}</span>
            </label>
          </div>
          <fieldset>
            <legend>${t(s, "field.silent_suppresses")}</legend>
            ${silenceable.map(
              (kind) =>
                html`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${live(settings.silent_suppresses.includes(kind))}
                    @change=${(e: Event) => {
                      const on = (e.target as HTMLInputElement).checked;
                      const next = on
                        ? [...settings.silent_suppresses, kind]
                        : settings.silent_suppresses.filter((k) => k !== kind);
                      this._saveSettings({ silent_suppresses: next });
                    }}
                  />
                  <span
                    >${kind === "chime" ? t(s, "settings.chime_title") : t(s, `action_kind.${kind}`)}</span
                  >
                </label>`,
            )}
            <p class="hint">${t(s, "settings.silent_hint")}</p>
          </fieldset>
        </div>
      </div>
    `;
  }

  // --- chime (§6.6) ----------------------------------------------------------------

  private _renderChime(s: Strings, chime: ChimeConfig) {
    const ctx = this.ctx!;
    // A notify target is usually a service, not an entity: read both, or the
    // chime on the phone (decision 60) could never be configured here.
    const targets = chimeTargets(
      ctx.hass,
      ctx.meta?.chime_domains ?? ["media_player", "siren", "notify"],
    );
    // Targets configured earlier stay listed even if the entity has gone.
    for (const target of chime.targets) {
      if (!targets.some((e) => e.id === target.entity_id)) {
        targets.push({ id: target.entity_id, name: target.entity_id });
      }
    }
    const tts = this._entities(["tts"]);
    const time = (key: "quiet_start" | "quiet_end") => (e: Event) =>
      this._set(key, (e.target as HTMLInputElement).value || null);
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "settings.chime_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${t(s, "settings.chime_intro")}</p>
          <fieldset>
            <legend>${t(s, "field.targets")}</legend>
            ${
              targets.length
                ? targets.map((e) => this._renderTarget(s, e))
                : html`<p class="hint">${t(s, "settings.no_targets")}</p>`
            }
            <p class="hint">${t(s, "settings.targets_hint")}</p>
          </fieldset>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.mode")}</span>
              <select
                @change=${(e: Event) =>
                  this._set("mode", (e.target as HTMLSelectElement).value as ChimeConfig["mode"])}
              >
                ${(["sound", "speech"] as const).map(
                  (mode) =>
                    html`<option .value=${mode} .selected=${live(mode === chime.mode)}>
                      ${t(s, `chime_mode.${mode}`)}
                    </option>`,
                )}
              </select>
            </label>
            ${
              chime.mode === "speech"
                ? html`<label class="field">
                    <span class="lbl">${t(s, "field.tts_entity")}</span>
                    <select
                      @change=${(e: Event) =>
                        this._set("tts_entity", (e.target as HTMLSelectElement).value || null)}
                    >
                      <option value="" .selected=${live(!chime.tts_entity)}>
                        ${t(s, "settings.pick_tts")}
                      </option>
                      ${tts.map(
                        (e) =>
                          html`<option .value=${e.id} .selected=${live(e.id === chime.tts_entity)}>
                            ${e.name}
                          </option>`,
                      )}
                    </select>
                    <span class="hint">${t(s, "settings.tts_hint")}</span>
                  </label>`
                : html`<label class="field">
                    <span class="lbl">${t(s, "field.sound")}</span>
                    <input
                      .value=${chime.sound ?? ""}
                      @input=${(e: Event) =>
                        this._set("sound", (e.target as HTMLInputElement).value.trim() || null)}
                    />
                    <span class="hint">${t(s, "settings.sound_hint")}</span>
                  </label>`
            }
            <label class="field">
              <span class="lbl">${t(s, "field.volume")}</span>
              <input
                type="number"
                min="0"
                max="100"
                .value=${chime.volume == null ? "" : String(chime.volume)}
                @input=${(e: Event) =>
                  this._set("volume", optionalNumber((e.target as HTMLInputElement).value))}
              />
              <span class="hint">${t(s, "settings.volume_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.quiet_start")}</span>
              <input type="time" .value=${chime.quiet_start ?? ""} @input=${time("quiet_start")} />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.quiet_end")}</span>
              <input type="time" .value=${chime.quiet_end ?? ""} @input=${time("quiet_end")} />
              <span class="hint">${t(s, "settings.quiet_hint")}</span>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${live(chime.during_exit)}
              @change=${(e: Event) =>
                this._set("during_exit", (e.target as HTMLInputElement).checked)}
            />
            <span>
              ${t(s, "field.during_exit")}
              <span class="hint">${t(s, "settings.during_exit_hint")}</span>
            </span>
          </label>
          <p class="hint">${t(s, "settings.switch_hint")}</p>
          ${
            this._problems.length
              ? html`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((p) => html`<li>${problemText(s, p)}</li>`)}
                  </ul>
                </div>`
              : nothing
          }
          ${this._saved ? html`<div class="notice">${t(s, "settings.saved")}</div>` : nothing}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${t(s, "common.save")}
            </button>
            <button
              class="btn"
              ?disabled=${this._busy || !this._draft}
              @click=${() => {
                this._draft = undefined;
                this._problems = [];
              }}
            >
              ${t(s, "common.cancel")}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  /** One target, with quiet hours of its own: speakers all day, the phone
   * only between nine and ten (part 3 decision 8). */
  private _renderTarget(s: Strings, entity: { id: string; name: string }) {
    const target = this._target(entity.id);
    const time = (key: "quiet_start" | "quiet_end") => (e: Event) =>
      this._setTarget(entity.id, {
        [key]: (e.target as HTMLInputElement).value || null,
      });
    return html`<div class="target">
      <label class="check">
        <input
          type="checkbox"
          .checked=${live(Boolean(target))}
          @change=${(ev: Event) =>
            this._toggleTarget(entity.id, (ev.target as HTMLInputElement).checked)}
        />
        <span>
          ${entity.name === entity.id
            ? entity.id
            : t(s, "zones.entity", { name: entity.name, entity: entity.id })}
        </span>
      </label>
      ${
        target
          ? html`<label class="field inline">
                <span class="lbl">${t(s, "field.quiet_start")}</span>
                <input
                  type="time"
                  .value=${target.quiet_start ?? ""}
                  @input=${time("quiet_start")}
                />
              </label>
              <label class="field inline">
                <span class="lbl">${t(s, "field.quiet_end")}</span>
                <input type="time" .value=${target.quiet_end ?? ""} @input=${time("quiet_end")} />
              </label>`
          : nothing
      }
    </div>`;
  }

  static override styles = [
    formStyles,
    css`
      .alarmo-list {
        margin: 4px 0 12px;
        padding-left: 20px;
        max-width: 80ch;
        font-size: 13.5px;
        line-height: 1.5;
      }
      .alarmo-list li + li {
        margin-top: 6px;
      }
      .card-bd h3 {
        margin: 16px 0 4px;
        font-size: 14px;
        font-weight: 600;
      }
      .intro {
        margin: 0 0 8px;
        color: var(--secondary-text-color);
        font-size: 13.5px;
        max-width: 72ch;
      }
      .grid-form {
        margin-top: 16px;
      }
      .later {
        margin: 4px 4px 0;
      }
      .target {
        display: flex;
        align-items: flex-end;
        gap: 12px;
        flex-wrap: wrap;
      }
      .field.inline {
        max-width: 140px;
      }
      .rows {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .row {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }
      .spacer {
        flex: 1;
      }
      .btn.file {
        position: relative;
        overflow: hidden;
        display: inline-flex;
        align-items: center;
      }
      .btn.file input {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
      }
    `,
  ];
}

if (!customElements.get("foyer-page-settings")) {
  customElements.define("foyer-page-settings", FoyerPageSettings);
}
