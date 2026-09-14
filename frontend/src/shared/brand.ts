// Full-colour symbol for headers (SPEC §17.1). Two files, never one recoloured.
import symbolDark from "../../../docs/logo/foyer-hd-symbol-dark-bg.svg?raw";
import symbolLight from "../../../docs/logo/foyer-hd-symbol-light-bg.svg?raw";

export function brandSymbol(darkMode: boolean): string {
  return darkMode ? symbolDark : symbolLight;
}
