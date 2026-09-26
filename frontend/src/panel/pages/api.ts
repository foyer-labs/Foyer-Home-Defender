// The API page (SPEC §9.2.2, decision 122): the contract of the device
// endpoint, rendered with Swagger UI for whoever is building a display, a
// relay or a module against it.
//
// Home Assistant administrators only, and only inside the panel. The document
// arrives over the admin-only foyer/api/document command, never from a public
// URL: a documentation page anybody could fetch would tell a scanner that an
// alarm lives on this host. Swagger UI itself is imported only when the page
// opens, so it costs nothing to whoever never does.
import { LitElement, css, html, nothing } from "lit";

import { t } from "../../shared/i18n";
import { formStyles } from "../../shared/styles";
import type { PanelContext } from "../context";
import { define } from "../../shared/define";

class FoyerPageApi extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _state: { state: true },
  };

  ctx?: PanelContext;
  private _state: "loading" | "ready" | "failed" = "loading";
  // A reload started while an earlier one is still on its way wins; the
  // earlier answer is dropped rather than rendered twice into the same host.
  private _attempt = 0;

  protected override firstUpdated(): void {
    void this._load();
  }

  private async _load(): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return;
    const attempt = ++this._attempt;
    this._state = "loading";
    try {
      const [answer, swagger] = await Promise.all([
        ctx.apiDocument(),
        import("./api-swagger"),
      ]);
      if (attempt !== this._attempt) return;
      const document = answer?.document;
      if (typeof document !== "string" || !document.trim()) throw new Error("empty");
      const host = this.renderRoot.querySelector<HTMLElement>(".swagger-host");
      if (!host) return;
      // Swagger UI's own nodes live inside a host Lit renders no bindings
      // into, so a re-render of this page never touches them.
      const style = window.document.createElement("style");
      style.textContent = swagger.swaggerCss;
      const mount = window.document.createElement("div");
      host.replaceChildren(style, mount);
      swagger.renderSwagger(mount, document);
      this._state = "ready";
    } catch {
      if (attempt === this._attempt) this._state = "failed";
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx) return nothing;
    const s = ctx.strings;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "api.title")}</h2>
          <span class="pill idle">${t(s, "api.contract", { version: "v1" })}</span>
        </div>
        <div class="card-bd">
          <p class="note">${t(s, "api.intro")}</p>
          <p class="note">${t(s, "api.try_it")}</p>
          <p class="notice">${t(s, "api.real_requests")}</p>
          ${this._state === "loading"
            ? html`<p class="muted">${t(s, "api.loading")}</p>`
            : nothing}
          ${this._state === "failed"
            ? html`<div class="problems" role="alert">
                ${t(s, "api.failed")}
                <div class="actions">
                  <button class="btn" @click=${() => void this._load()}>
                    ${t(s, "api.retry")}
                  </button>
                </div>
              </div>`
            : nothing}
        </div>
        <div class="swagger-host" ?hidden=${this._state !== "ready"}></div>
      </div>
    `;
  }

  static override styles = [
    formStyles,
    css`
      /* Swagger UI draws for a light page and has no dark theme: it keeps
         its own light background rather than half-inheriting a dark one,
         which leaves grey text on grey. */
      .swagger-host {
        background: #fff;
        color: #3b4151;
        border-radius: 0 0 12px 12px;
        padding: 0 8px 16px;
        overflow-x: auto;
      }
      .swagger-host[hidden] {
        display: none;
      }
    `,
  ];
}

define("foyer-page-api", FoyerPageApi);
