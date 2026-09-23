// Swagger UI, for the API page alone (SPEC §9.2.2, decision 122). This module
// is reached only through a dynamic import, so it is built as a chunk of its
// own beside the panel bundle: a household that never opens the page never
// downloads a megabyte and a half of it, and nothing is fetched from a CDN.
import SwaggerUI from "swagger-ui-dist/swagger-ui-es-bundle.js";
import css from "swagger-ui-dist/swagger-ui.css?inline";

/** Swagger UI's stylesheet, for the page's shadow root: a stylesheet in the
 * document would not reach inside it, and would restyle Home Assistant. */
export const swaggerCss: string = css;

/** Render the contract, as YAML text, into `domNode`. */
export function renderSwagger(domNode: HTMLElement, document: string): void {
  const ui = SwaggerUI({
    domNode,
    // The panel owns the address bar, and a `?url=` there must never make
    // this page render somebody else's document.
    deepLinking: false,
    queryConfigEnabled: false,
    // The validator badge is fetched from swagger.io: nothing leaves the house.
    validatorUrl: null,
    // A device token pasted into Authorize stays in this page's memory and
    // goes with it; it is never written to the browser's storage.
    persistAuthorization: false,
    tryItOutEnabled: false,
    displayRequestDuration: true,
    defaultModelsExpandDepth: 0,
  });
  // Given as text, parsed by Swagger UI itself: YAML or JSON alike, with no
  // parser of our own bundled next to its.
  ui.specActions.updateSpec(document);
}
