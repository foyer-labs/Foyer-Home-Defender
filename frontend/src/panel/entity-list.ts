// A list of Home Assistant entities to add to and take from: the chosen ones
// with their name, id and what they read right now, and a field that
// suggests the rest as a name or an id is typed. Rows of tick-boxes stop
// working at a few dozen entities, and a house with a hundred device
// trackers has more than that; seeing each entity's state beside it is how
// a wrong pick is caught before the rule relies on it.
import { css, html, nothing } from "lit";

import { t, type Strings } from "../shared/i18n";
import type { HomeAssistant } from "../shared/types";
import { stateLabel, type Target } from "./ha-targets";

export interface EntityListOptions {
  hass: HomeAssistant;
  s: Strings;
  chosen: string[];
  /** What may be added. An id typed that is not among them is refused, so
   * the list can only hold what the backend will accept. */
  candidates: Target[];
  /** Unique within the page: the suggestions are a `<datalist>` by this id. */
  listId: string;
  onChange: (next: string[]) => void;
  /** One entity at most: adding replaces the one there. */
  single?: boolean;
}

/** Every entity Home Assistant has, by name: for a field that may name any. */
export function allEntities(hass: HomeAssistant): Target[] {
  return Object.values(hass.states)
    .map((e) => ({
      id: e.entity_id,
      name: String(e.attributes.friendly_name ?? e.entity_id),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function renderEntityList(o: EntityListOptions) {
  const { hass, s, chosen, candidates, listId, onChange } = o;
  const names = new Map(candidates.map((c) => [c.id, c.name]));
  const add = (input: HTMLInputElement | null): void => {
    if (!input) return;
    const typed = input.value.trim();
    const lower = typed.toLowerCase();
    // An id, or a name that belongs to exactly one entity.
    const byName = candidates.filter((c) => c.name.toLowerCase() === lower);
    const id = names.has(typed) ? typed : byName.length === 1 ? byName[0].id : undefined;
    if (!id) return;
    input.value = "";
    if (chosen.includes(id)) return;
    onChange(o.single ? [id] : [...chosen, id]);
  };
  return html`<div class="entity-list">
    ${chosen.length
      ? html`<ul>
          ${chosen.map((id) => {
            const entity = hass.states[id];
            return html`<li>
              <span class="who">
                <strong>${names.get(id) ?? String(entity?.attributes.friendly_name ?? id)}</strong>
                <span class="muted">${id}</span>
              </span>
              <span class=${entity ? "now" : "now missing"}>
                ${entity
                  ? stateLabel(hass, id, entity.state)
                  : t(s, "entity_list.missing")}
              </span>
              <button class="btn sm" @click=${() => onChange(chosen.filter((c) => c !== id))}>
                ${t(s, "common.remove")}
              </button>
            </li>`;
          })}
        </ul>`
      : nothing}
    <div class="add-row">
      <input
        list=${listId}
        placeholder=${t(s, "entity_list.placeholder")}
        aria-label=${t(s, "entity_list.placeholder")}
        @change=${(e: Event) => {
          // Picking a suggestion adds it at once; a half-typed name waits
          // for Enter or the button.
          const input = e.target as HTMLInputElement;
          if (names.has(input.value.trim())) add(input);
        }}
        @keydown=${(e: KeyboardEvent) => {
          if (e.key === "Enter") add(e.target as HTMLInputElement);
        }}
      />
      <button
        class="btn"
        @click=${(e: Event) =>
          add((e.target as HTMLElement).previousElementSibling as HTMLInputElement | null)}
      >
        ${t(s, o.single && chosen.length ? "entity_list.replace" : "common.add")}
      </button>
    </div>
    <datalist id=${listId}>
      ${candidates
        .filter((c) => !chosen.includes(c.id))
        .map((c) => html`<option value=${c.id}>${c.name}</option>`)}
    </datalist>
  </div>`;
}

export const entityListStyles = css`
  .entity-list ul {
    list-style: none;
    margin: 4px 0 8px;
    padding: 0;
  }
  .entity-list li {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
    border-bottom: 1px solid var(--divider-color, #e0e0e0);
  }
  .entity-list .who {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .entity-list .now {
    color: var(--secondary-text-color);
    white-space: nowrap;
  }
  .entity-list .now.missing {
    color: var(--error-color, #d32f2f);
  }
  .entity-list .add-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .entity-list .add-row input {
    flex: 1;
    min-width: 0;
  }
`;
