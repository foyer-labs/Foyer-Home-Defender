// The two code settings an area and a scenario each carry (SPEC §4.5, §4.6,
// §8.2). Three answers, not two: "inherit" is not "no", and collapsing them
// would silently pin a setting that should follow the global policy.
//
// Where an area and a scenario disagree the strictest explicit setting wins
// (decision 80), which is why the hint says so here rather than in the docs:
// somebody setting "no code" on a scenario needs to know an area can still
// ask for one.
import { html, nothing, type TemplateResult } from "lit";

import { t, type Strings } from "../shared/i18n";

type Answer = boolean | null;

function field(
  s: Strings,
  label: string,
  value: Answer,
  onChange: (value: Answer) => void,
): TemplateResult {
  return html`<label class="field">
    <span class="lbl">${t(s, label)}</span>
    <select
      @change=${(e: Event) => {
        const chosen = (e.target as HTMLSelectElement).value;
        onChange(chosen === "" ? null : chosen === "yes");
      }}
    >
      <option value="" ?selected=${value === null}>${t(s, "code_policy.inherit")}</option>
      <option value="yes" ?selected=${value === true}>${t(s, "code_policy.required")}</option>
      <option value="no" ?selected=${value === false}>${t(s, "code_policy.not_required")}</option>
    </select>
  </label>`;
}

/** The pair of selectors, plus the one line that explains how they combine. */
export function codeFields(
  s: Strings,
  draft: { require_code_to_arm: Answer; require_code_to_disarm: Answer },
  set: (key: "require_code_to_arm" | "require_code_to_disarm", value: Answer) => void,
  enforced: boolean,
): TemplateResult {
  return html`
    ${field(s, "field.require_code_to_arm", draft.require_code_to_arm, (v) =>
      set("require_code_to_arm", v),
    )}
    ${field(s, "field.require_code_to_disarm", draft.require_code_to_disarm, (v) =>
      set("require_code_to_disarm", v),
    )}
    <p class="hint span">
      ${t(s, "code_policy.strictest")}
      ${enforced ? nothing : html` ${t(s, "code_policy.inert")}`}
    </p>
  `;
}
