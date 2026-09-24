// The response-profile field, shared by pages 2, 3, 4 and 13 (SPEC §6).
//
// The UI must always show the *effective* profile and where it was inherited
// from, otherwise the behaviour looks arbitrary. The chain is the engine's
// (core/response.py): area → scenario → global default, with a zone's own
// profile read only for its own alarm.
import { html, nothing, type TemplateResult } from "lit";
import { live } from "lit/directives/live.js";

import { t, type Strings } from "../shared/i18n";
import type { FoyerConfig } from "../shared/types";
import type { PanelContext } from "./context";

export interface Inherited {
  name: string;
  source: "area" | "scenario" | "default" | "none";
}

/** What an area would actually respond with, and where that comes from. */
export function effectiveProfile(
  config: FoyerConfig,
  areaId: string | null,
  armedBy: string | null = null,
): Inherited {
  const area = config.areas.find((a) => a.id === areaId);
  // The engine reads the scenario the area was armed with. Armed, that is
  // the one to show; disarmed, the first scenario that would arm it with a
  // profile of its own is the best guess there is (fix phase).
  const scenario = armedBy
    ? config.scenarios.find((s) => s.id === armedBy)
    : config.scenarios.find(
        (s) => area?.id && s.areas.includes(area.id) && s.response_profile_id,
      );
  const byId = (id: string | null | undefined) => config.profiles?.find((p) => p.id === id);
  const ofArea = byId(area?.response_profile_id);
  if (ofArea) return { name: ofArea.name, source: "area" };
  const ofScenario = byId(scenario?.response_profile_id);
  if (ofScenario) return { name: ofScenario.name, source: "scenario" };
  const fallback = byId(config.settings?.default_profile_id);
  if (fallback) return { name: fallback.name, source: "default" };
  return { name: "", source: "none" };
}

/** A select listing every profile, plus "inherit". */
export function profileField(
  ctx: PanelContext,
  value: string | null,
  onChange: (value: string | null) => void,
  hint?: string,
): TemplateResult {
  const s: Strings = ctx.strings;
  const profiles = ctx.config?.profiles ?? [];
  return html`<label class="field">
    <span class="lbl">${t(s, "field.response_profile_id")}</span>
    <select @change=${(e: Event) => onChange((e.target as HTMLSelectElement).value || null)}>
      <option value="" .selected=${live(!value)}>${t(s, "profiles.inherit")}</option>
      ${profiles.map(
        (profile) => html`<option .value=${profile.id ?? ""} .selected=${live(profile.id === value)}>
          ${profile.name}
        </option>`,
      )}
    </select>
    ${hint ? html`<span class="hint">${hint}</span>` : nothing}
  </label>`;
}

/** "Effective profile: Full — inherited from the area". */
export function effectiveHint(
  ctx: PanelContext,
  areaId: string | null,
): TemplateResult | typeof nothing {
  if (!ctx.config) return nothing;
  const armedBy = ctx.status?.areas.find((a) => a.id === areaId)?.scenario_id ?? null;
  const { name, source } = effectiveProfile(ctx.config, areaId, armedBy);
  const s = ctx.strings;
  if (source === "none") {
    return html`<p class="hint">${t(s, "profiles.inherited_none")}</p>`;
  }
  return html`<p class="hint">
    ${t(s, "profiles.effective_from", {
      profile: name,
      from: t(s, `profiles.inherited_from_${source}`),
    })}
  </p>`;
}
