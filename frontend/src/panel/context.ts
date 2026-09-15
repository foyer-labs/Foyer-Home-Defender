// What every panel page receives from the shell. Pages never talk to Home
// Assistant except through these functions, so there is one place that knows
// the WebSocket commands.
import { t, type Strings } from "../shared/i18n";
import type {
  ChimeConfig,
  CommandResult,
  ConfigMeta,
  EditResult,
  FoyerConfig,
  FoyerStatus,
  HomeAssistant,
  PageId,
  Problem,
} from "../shared/types";

export interface PanelContext {
  hass: HomeAssistant;
  strings: Strings;
  status: FoyerStatus;
  config?: FoyerConfig;
  meta?: ConfigMeta;
  isAdmin: boolean;
  /** Server time now, corrected for the browser clock's offset. */
  now(): number;
  navigate(page: PageId): void;
  arm(target: Record<string, unknown>): Promise<CommandResult>;
  disarm(areaIds?: string[]): Promise<CommandResult>;
  /** The incident and the technical channel have separate acknowledgements. */
  acknowledge(target: "incident" | "technical"): Promise<CommandResult>;
  save(kind: string, item: object, triggerConfirmed?: boolean): Promise<EditResult>;
  remove(kind: string, id: string): Promise<EditResult>;
  saveChime(chime: ChimeConfig): Promise<EditResult>;
}

/** Seconds left on a timer, never negative. */
export function remaining(ctx: PanelContext, due: string): number {
  return Math.max(0, Math.round((Date.parse(due) - ctx.now()) / 1000));
}

/** The translated reason for a refused command, naming the zones (§5.4). */
export function reasonText(s: Strings, result: CommandResult): string {
  const zones = result.blocking_zones.map((z) => z.name).join(", ");
  return t(s, `reason.${result.reason ?? "unknown"}`, { zones });
}

export function problemText(s: Strings, problem: Problem): string {
  const field = problem.field ? t(s, `field.${problem.field}`) : "";
  return t(s, `problem.${problem.code}`, { field, detail: problem.detail ?? "" });
}

/** "" becomes null: an empty number field means "inherit" or "off". */
export function optionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed === "") return null;
  const n = Number(trimmed);
  return Number.isFinite(n) ? n : null;
}
