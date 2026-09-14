// Builds each entry as its own self-contained ES module into the integration's
// frontend/ directory, where Home Assistant serves it. The output is committed:
// HACS installs custom_components/foyer as is, with no build step.
import { build } from "vite";
import { fileURLToPath } from "node:url";
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
      rolldownOptions: { output: { banner: banner(lit) } },
    },
  });
  first = false;
  console.log(`built ${name}.js`);
}
