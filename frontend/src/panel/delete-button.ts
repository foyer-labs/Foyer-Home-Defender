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

  override willUpdate(changed: Map<string, unknown>): void {
    // Another item opened in the same editor reuses this element: a question
    // asked about the first must never become one about the second, deleted
    // with the click that was meant for the first (review).
    if (changed.has("name") && changed.get("name") !== undefined) this._asking = false;
  }

  override updated(changed: Map<string, unknown>): void {
    if (!changed.has("_asking")) return;
    // Straight onto the question's own Cancel, so a stray Enter or a second
    // tap in the same place does not delete — and back onto Delete once it
    // is answered, so the keyboard is not left on the page's body.
    const target = this._asking ? ".ask .btn:not(.danger)" : ".btn.danger";
    this.renderRoot.querySelector<HTMLButtonElement>(target)?.focus();
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
