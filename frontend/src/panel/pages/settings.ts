// Page 11 — Settings (SPEC §15.1). Phase 1 part 3 ships the chime block
// (§6.6) and the response defaults: where every inheritance chain ends and
// what a silent zone keeps quiet. Log retention and backup arrive with part 4.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles } from "../../shared/styles";
import type { ChimeConfig, ChimeTarget, Problem, SettingsConfig } from "../../shared/types";
import { optionalNumber, problemText, type PanelContext } from "../context";

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
  };

  ctx?: PanelContext;
  private _draft?: ChimeConfig;
  private _settings?: SettingsConfig;
  private _problems: Problem[] = [];
  private _busy = false;
  private _saved = false;

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
    return html`${this._renderResponse(ctx.strings)} ${this._renderChime(ctx.strings, this._chime)}
      <p class="hint later">${t(ctx.strings, "settings.later")}</p>`;
  }

  private _entities(domains: string[]): { id: string; name: string }[] {
    return Object.values(this.ctx!.hass.states)
      .filter((e) => domains.includes(e.entity_id.split(".")[0]))
      .map((e) => ({
        id: e.entity_id,
        name: String(e.attributes.friendly_name ?? e.entity_id),
      }))
      .sort((a, b) => a.id.localeCompare(b.id));
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
          <option value="" ?selected=${!settings[key]}>${t(s, "settings.none")}</option>
          ${profiles.map(
            (profile) =>
              html`<option .value=${profile.id ?? ""} ?selected=${profile.id === settings[key]}>
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
                    .checked=${settings.silent_suppresses.includes(kind)}
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
    const targets = this._entities(ctx.meta?.chime_domains ?? ["media_player", "siren", "notify"]);
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
                    html`<option .value=${mode} ?selected=${mode === chime.mode}>
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
                      <option value="" ?selected=${!chime.tts_entity}>
                        ${t(s, "settings.pick_tts")}
                      </option>
                      ${tts.map(
                        (e) =>
                          html`<option .value=${e.id} ?selected=${e.id === chime.tts_entity}>
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
              .checked=${chime.during_exit}
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
          .checked=${Boolean(target)}
          @change=${(ev: Event) =>
            this._toggleTarget(entity.id, (ev.target as HTMLInputElement).checked)}
        />
        <span>${t(s, "zones.entity", { name: entity.name, entity: entity.id })}</span>
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
    `,
  ];
}

if (!customElements.get("foyer-page-settings")) {
  customElements.define("foyer-page-settings", FoyerPageSettings);
}
