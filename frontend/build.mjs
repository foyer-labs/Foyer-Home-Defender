// Builds each entry as its own self-contained ES module into the integration's
// frontend/ directory, where Home Assistant serves it. The output is committed:
// HACS installs custom_components/foyer as is, with no build step.
//
// One exception to "self-contained": Swagger UI, for the administrators' API
// page (decision 122), is a dynamic import and so a chunk of its own beside
// the panel, named by its content hash. The directory is served whole, with
// cache headers, so the hash is what keeps a new release from being masked
// by a cached chunk; the panel bundle itself does not grow by it.
import { build } from "vite";
import { fileURLToPath } from "node:url";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const here = fileURLToPath(new URL(".", import.meta.url));
const outDir = resolve(here, "../custom_components/foyer/frontend");

// name -> [entry, bundles Lit]
const entries = {
  "foyer-panel": ["src/panel/foyer-panel.ts", true],
  "foyer-card": ["src/card/foyer-card.ts", true],
  "foyer-icons": ["src/icons/foyer-icons.ts", false],
};

// Minification drops the licence comments of bundled dependencies, so the
// notices their licences require are restated at the top of every bundle.
const LIT_NOTICE =
  "\n * Bundles Lit (https://lit.dev): Copyright 2017 Google LLC, BSD-3-Clause.";
const banner = (lit) =>
  `/*! Foyer Home Defender — Apache-2.0. See LICENSE and NOTICE.${lit ? LIT_NOTICE : ""} */`;
// Swagger UI bundles React and some forty other packages; their notices are
// too long for a banner and are written, as its authors ship them, to a file
// beside the chunk.
const SWAGGER_NOTICES = "swagger-ui.LICENSE.txt";
const SWAGGER_BANNER =
  "/*! Swagger UI (https://github.com/swagger-api/swagger-ui): Copyright SmartBear Software Inc.," +
  ` Apache-2.0. Notices of the packages it bundles: ${SWAGGER_NOTICES} */`;
const chunkBanner = (lit) => (chunk) =>
  chunk.name === "api-swagger" ? SWAGGER_BANNER : banner(lit);

let first = true;
for (const [name, [entry, lit]] of Object.entries(entries)) {
  await build({
    configFile: false,
    root: here,
    logLevel: "warn",
    build: {
      outDir,
      emptyOutDir: first,
      minify: true,
      sourcemap: false,
      lib: {
        entry: resolve(here, entry),
        formats: ["es"],
        fileName: () => `${name}.js`,
      },
      rolldownOptions: {
        output: { banner: chunkBanner(lit), chunkFileNames: "[name]-[hash].js" },
      },
    },
  });
  first = false;
  console.log(`built ${name}.js`);
}

const swagger = resolve(here, "node_modules/swagger-ui-dist");
writeFileSync(
  resolve(outDir, SWAGGER_NOTICES),
  [
    readFileSync(resolve(swagger, "NOTICE"), "utf8").trim(),
    "Licensed under the Apache License, Version 2.0: see LICENSE at the root of this repository.",
    readFileSync(resolve(swagger, "swagger-ui-es-bundle.js.LICENSE.txt"), "utf8"),
  ].join("\n\n"),
);
console.log(`wrote ${SWAGGER_NOTICES}`);
