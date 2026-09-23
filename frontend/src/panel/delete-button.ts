// A Delete button that asks first. Every editor deleted on one click, and a
// delete here is not a draft thrown away: it is a zone that stops watching a
// door, or a person whose code stops opening the house (UX review). The
// question is asked in place, next to the button, rather than in a browser
// dialog that a wall tablet may not show at all.
import { LitElement, css, html } from "lit";

import { t, type Strings } from "../shared/i18n";
import { formStyles } from "../shared/styles";

class FoyerDeleteButton extends LitElement {
  static override properties = {
    strings: { attribute: false },
    name: { attribute: false },
    /** The question, as a translation key taking {name}. */
    message: { attribute: false },
    disabled: { type: Boolean },
    _asking: { state: true },
  };

  strings?: Strings;
  name = "";
  message = "common.confirm_delete";
  disabled = false;
  private _asking = false;

  private _confirm(): void {
    this._asking = false;
    this.dispatchEvent(new CustomEvent("confirm", { bubbles: true, composed: true }));
  }

  override render() {
    const s = this.strings;
    if (!this._asking) {
      return html`<button
        class="btn danger"
        ?disabled=${this.disabled}
        @click=${() => (this._asking = true)}
      >
        ${t(s, "common.delete")}
      </button>`;
    }
    return html`<div class="ask" role="alertdialog" aria-labelledby="q">
      <span id="q">${t(s, this.message, { name: this.name })}</span>
      <span class="buttons">
        <button class="btn danger" ?disabled=${this.disabled} @click=${this._confirm}>
          ${t(s, "common.delete")}
        </button>
        <button class="btn" @click=${() => (this._asking = false)}>
          ${t(s, "common.cancel")}
        </button>
      </span>
    </div>`;
  }

  override updated(changed: Map<string, unknown>): void {
    // Straight onto the question's own Cancel, so a stray Enter or a second
    // tap in the same place does not delete.
    if (changed.has("_asking") && this._asking) {
      this.renderRoot.querySelector<HTMLButtonElement>(".ask .btn:not(.danger)")?.focus();
    }
  }

  static override styles = [
    formStyles,
    css`
      :host {
        display: contents;
      }
      .ask {
        flex-basis: 100%;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 12px;
        padding: 10px 14px;
        border-left: 3px solid var(--error-color, #d32f2f);
        background: var(--secondary-background-color);
        border-radius: 6px;
        font-size: 14px;
      }
      .ask > span:first-child {
        flex: 1 1 240px;
      }
      .buttons {
        display: flex;
        gap: 8px;
      }
    `,
  ];
}

if (!customElements.get("foyer-delete-button")) {
  customElements.define("foyer-delete-button", FoyerDeleteButton);
}
