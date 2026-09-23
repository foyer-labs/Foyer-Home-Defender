// What every panel page receives from the shell. Pages never talk to Home
// Assistant except through these functions, so there is one place that knows
// the WebSocket commands.
import { t, type Strings } from "../shared/i18n";
import type {
  ChimeConfig,
  Diagnostics,
  CodePolicyConfig,
  CommandResult,
  ConfigBackup,
  ConfigMeta,
  AlarmoLabels,
  AlarmoPreview,
  EditResult,
  FoyerConfig,
  FoyerStatus,
  HealthConfig,
  HealthStatus,
  HomeAssistant,
  LogExport,
  LogPage,
  LogQuery,
  PageId,
  PersonCounts,
  Problem,
  RadioCandidate,
  SecurityConfig,
  SettingsConfig,
  Simulation,
  SimulationQuery,
  SuspensionKind,
  TestActionQuery,
  TestActionResult,
  UserConfig,
} from "../shared/types";

export interface PanelContext {
  hass: HomeAssistant;
  strings: Strings;
  status: FoyerStatus;
  config?: FoyerConfig;
  meta?: ConfigMeta;
  isAdmin: boolean;
  /** Home Assistant's own accounts, for linking a person to one (§8.2).
   * Admin only, and empty when the list could not be read. */
  haUsers?: { id: string; name: string }[];
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
  saveSettings(settings: Partial<SettingsConfig>): Promise<EditResult>;
  /** Switch the DTMF acknowledgement webhook on or off (§7.2). The id is
   * the backend's to generate and this never sends one. */
  setAckWebhook(enabled: boolean): Promise<EditResult>;
  /** Generate an endpoint keypad's token, or revoke it (§9.2.1). The token is
   * the backend's to generate, and this answer is the only time it is ever
   * shown: it is stored as a hash nothing can read back. */
  deviceToken(deviceId: string, revoke: boolean): Promise<EditResult & { token?: string }>;
  /** Automatic arming (§9.4). Cancelling stops a countdown before it acts;
   * the switch is the global kill switch; a suspension holds rules back
   * until a date, for one occurrence, or for a named visitor window. */
  cancelAuto(pendingId?: string): Promise<CommandResult>;
  setAutoArming(enabled: boolean): Promise<CommandResult>;
  suspend(suspension: {
    kind: SuspensionKind;
    rule_ids?: string[];
    name?: string | null;
    start?: string | null;
    until?: string | null;
    reduced_scenario_id?: string | null;
  }): Promise<CommandResult>;
  liftSuspension(id: string): Promise<CommandResult>;
  /** Create or change a person. The codes travel separately and one way:
   * absent means "leave it", null means "remove it" (SPEC §8.1). */
  saveUser(
    user: UserConfig,
    codes: { new_code?: string | null; new_duress_code?: string | null },
  ): Promise<EditResult>;
  saveSecurity(policy: CodePolicyConfig, security: SecurityConfig): Promise<EditResult>;
  /** Exclude a zone by hand, with an optional duration (SPEC §16). */
  bypass(zoneId: string, bypass: boolean, seconds?: number): Promise<CommandResult>;
  /** The event log (§10): read, export exactly what the filters show, empty. */
  queryLog(query: LogQuery): Promise<LogPage>;
  exportLog(query: LogQuery, format: "csv" | "json"): Promise<LogExport>;
  clearLog(): Promise<{ success: boolean; removed: number; reason?: string | null }>;
  /** Personal data in the log (§10.4). The preview says what an erasure would
   * touch before anybody presses the button; the export is one person's rows
   * for a subject access request; the erasure takes them out of the log and
   * leaves every event where it is. */
  previewPerson(userId: string): Promise<PersonCounts>;
  exportPerson(userId: string, format: "csv" | "json"): Promise<LogExport>;
  erasePerson(
    userId: string,
    pseudonymise: boolean,
  ): Promise<{ success: boolean; removed?: number; reason?: string | null }>;
  /** Page 9 (§11): both only read, and both are gated as reads — view_log,
   * no code. Nothing here executes anything; the simulator calls the same
   * decide() the runtime calls and never hands the result to the executor. */
  diagnostics(): Promise<Diagnostics>;
  simulate(query: SimulationQuery): Promise<Simulation>;
  /** Page 9, tabs 3 and 4 (§11.3, §11.4). Both are writes and both are
   * gated as writes: `walk_test` and `test_actions`, each with a code. The
   * walk test goes through the engine like any other state-changing
   * request; the action test really executes, which is the point. */
  walkTest(enable: boolean, options?: { duration?: number; code?: string }):
    Promise<CommandResult>;
  testAction(query: TestActionQuery): Promise<TestActionResult>;
  /** Page 14 — system health (§12). Reading is gated on view_log, like the
   * log itself; saving the block is edit_config and its code policy. The
   * diagnostics *download* is Home Assistant's own button on the integration
   * page, which is already admin-only (part 1 decision 12). */
  health(): Promise<HealthStatus>;
  saveHealth(health: HealthConfig): Promise<EditResult>;
  radioCandidates(): Promise<RadioCandidate[]>;
  /** Configuration backup and restore (§15.1). */
  exportConfig(): Promise<{ filename: string; document: ConfigBackup }>;
  importConfig(document: unknown): Promise<EditResult>;
  /** The Alarmo importer (§20.2): a preview that reads and writes nothing,
   * then an apply that stores exactly what the preview showed — refused, by
   * the backend, if anything it was computed from has changed since. */
  alarmoPreview(labels: AlarmoLabels): Promise<AlarmoPreview>;
  alarmoApply(fingerprint: string, labels: AlarmoLabels): Promise<AlarmoPreview>;
}

/** Offer a file to the browser. Used by both exports: the content crosses the
 * WebSocket and never becomes a file on the Home Assistant server. */
export function download(filename: string, content: string, type: string): void {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  // Revoked on the next turn: revoking at once can beat the download.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
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
/** Enter or Space on a focused clickable row opens it, as a click does.
 * Every list opened its editor on a mouse click only, so nobody using a
 * keyboard could open an item at all (second review). */
export function activateOnKey(e: KeyboardEvent): void {
  if (e.key !== "Enter" && e.key !== " ") return;
  if (e.target !== e.currentTarget) return;
  e.preventDefault();
  (e.currentTarget as HTMLElement).click();
}

/** Apply a number the field holds, and nothing while it is empty. A field
 * that wrote its default back the moment it was cleared turned "3" cleared
 * and "5" typed into "15" — and a delay cleared into 0 seconds. Empty now
 * means "not changed", and the draft keeps what it had. */
export function whenNumber(e: Event, apply: (n: number) => void): void {
  const n = optionalNumber((e.target as HTMLInputElement).value);
  if (n !== null) apply(n);
}

export function optionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed === "") return null;
  const n = Number(trimmed);
  return Number.isFinite(n) ? n : null;
}
