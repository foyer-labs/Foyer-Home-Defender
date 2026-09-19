// The subset of Home Assistant's frontend objects that Foyer uses, and the
// shapes of Foyer's own WebSocket payloads (api/websocket.py).

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

export interface HassConnection {
  subscribeMessage<T>(
    callback: (message: T) => void,
    message: Record<string, unknown>,
  ): Promise<() => Promise<void>>;
}

/** One service as Home Assistant's registry describes it. */
export interface HassService {
  name?: string;
  description?: string;
}

export interface HomeAssistant {
  language: string;
  states: Record<string, HassEntity>;
  /** The service registry, by domain then service name. Home Assistant keeps
   * it on the hass object; a notify target is usually a service and not an
   * entity, so a picker that reads only `states` would never find it. */
  services?: Record<string, Record<string, HassService>>;
  themes?: { darkMode?: boolean };
  user?: { id: string; name: string; is_admin: boolean };
  connection: HassConnection;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: Record<string, unknown>,
  ): Promise<unknown>;
  localize(key: string, values?: Record<string, unknown>): string;
  loadBackendTranslation(category: string, integration?: string): Promise<unknown>;
}

// Error shape of a rejected service call.
export interface HassServiceError {
  message?: string;
  translation_domain?: string;
  translation_key?: string;
  translation_placeholders?: Record<string, string>;
}

// --- live status: foyer/status and foyer/subscribe (runtime/system.py) ----------

export type AreaState = "disarmed" | "arming" | "armed" | "entry" | "triggered";
export type TimerKind = "exit" | "hold" | "entry" | "siren";

export interface StatusArea {
  id: string;
  name: string;
  state: AreaState;
  entity_id: string | null;
  scenario_id: string | null;
  memory: boolean;
  causes: string[];
  timer: { kind: TimerKind; due: string } | null;
  ready: boolean;
  blocking: { fault: string[]; open: string[] };
  /** Whether arming or disarming this area would ask the connected user for
   * a code right now (SPEC §8.2). A courtesy: the backend decides (INV-2). */
  require_code: { arm: boolean; disarm: boolean };
}

export interface StatusZone {
  id: string;
  name: string;
  area_id: string;
  entity_id: string;
  type: string;
  channel: "intrusion" | "technical" | "key";
  enabled: boolean;
  state: string | null;
  fault: string | null;
  open: boolean;
  bypassed: string | null;
  bypassable: boolean;
  /** When a timed manual bypass ends (SPEC §16), ISO, or null. */
  bypass_until: string | null;
  /** The percentage the zone's battery entity reports, when it reports one.
   * A battery binary_sensor has no level to show, only the flag beside it. */
  battery: number | null;
  low_battery: boolean;
}

export interface StatusScenario {
  id: string;
  name: string;
  icon: string | null;
  areas: string[];
  ha_master_state: string;
  require_code: { arm: boolean; disarm: boolean };
}

/** What the connected user needs to know about codes (SPEC §8.2, §8.4). */
export interface StatusSecurity {
  /** False while nobody holds a code: nothing asks for one, and the panel
   * says so plainly rather than looking secured when it is not. */
  enforced: boolean;
  code_length: number;
  has_users: boolean;
  me: {
    user_id: string;
    name: string;
    permissions: string[];
    code_exempt: boolean;
  } | null;
  require_code: Record<string, boolean>;
  /** When this channel stops being locked out, ISO, or null. */
  locked_until: string | null;
}

// The technical channel (§5.5): one entry per zone in alarm or in memory.
export interface StatusTechnical {
  zone_id: string;
  name: string;
  area_id: string | null;
  since: string;
  active: boolean;
  acknowledged: boolean;
}

// The open intrusion incident (§5.6).
export interface StatusIncident {
  id: string;
  opened_at: string;
  zone_ids: string[];
  area_ids: string[];
  acknowledged: boolean;
}

export interface FoyerStatus {
  now: string;
  active_scenario_id: string | null;
  master: { state: AreaState; mode: string | null };
  areas: StatusArea[];
  scenarios: StatusScenario[];
  zones: StatusZone[];
  technical: StatusTechnical[];
  incident: StatusIncident | null;
  chime_enabled: boolean;
  security: StatusSecurity;
}

// Result of foyer/arm and foyer/disarm (SPEC §9.1).
export interface CommandResult {
  success: boolean;
  reason: string | null;
  blocking_zones: { id: string; name: string }[];
  bypassed_zones: { id: string; name: string }[];
  /** Zones this arming would put under guard on a battery that is running
   * out (§4.2). They never block — a contact at 15 % still sees — but every
   * attempt carries them, so the warning arrives each time rather than once
   * (Phase 3 part 1 decision 2). Excluding one is an ordinary bypass. */
  low_battery_zones: { id: string; name: string }[];
  state: FoyerStatus;
}

// --- configuration: foyer/config (store/schema.py) --------------------------------

export type Trigger =
  | { kind: "state"; states: string[] }
  | {
      kind: "numeric";
      operator: "gt" | "lt" | "eq";
      value: number;
      hysteresis: number;
      attribute: string | null;
    }
  | { kind: "event"; event_type: string | null };

export interface AreaConfig {
  id?: string;
  name: string;
  ha_state_when_armed: string;
  default_entry_delay: number;
  default_exit_delay: number;
  response_profile_id: string | null;
  /** null inherits the global policy; where an area and a scenario disagree
   * the strictest explicit setting wins (SPEC §8.2, decision 80). */
  require_code_to_arm: boolean | null;
  require_code_to_disarm: boolean | null;
}

// --- response profiles (SPEC §6) --------------------------------------------------

export type ActionKind =
  | "notify"
  | "persistent_notification"
  | "siren"
  | "light"
  | "camera"
  | "scene"
  | "switch"
  | "tts"
  | "call_service"
  | "delay";

export type Condition =
  | { kind: "time"; after: string; before: string }
  | { kind: "state"; entity_id: string; operator: "is" | "is_not"; state: string };

export interface ActionConfig {
  id?: string;
  kind: ActionKind;
  moments: string[];
  name: string;
  params: Record<string, unknown>;
  conditions: Condition[];
  condition_mode: "all" | "any";
  enabled: boolean;
}

export interface ProfileConfig {
  id?: string;
  name: string;
  severity: number;
  actions: ActionConfig[];
}

export interface KeyConfig {
  on_activate: "arm" | "disarm" | "toggle";
  scenario_id: string | null;
  on_deactivate: "none" | "disarm";
}

export interface ZoneConfig {
  id?: string;
  name: string;
  entity_id: string;
  area_id: string;
  trigger: Trigger;
  type: string;
  channel: "intrusion" | "technical" | "key";
  entry_mode: "instant" | "delayed" | "follower";
  alarm_kind: "intrusion" | "tamper" | "panic";
  always_on: boolean;
  entry_delay: number | null;
  follows: string[];
  arm_policy: "block" | "auto_bypass" | "arm_after_closing" | "ignore";
  arm_hold_timeout: number | null;
  allow_arm_when_faulted: boolean;
  bypassable: boolean;
  supervision_timeout: number | null;
  enabled: boolean;
  key: KeyConfig | null;
  chime: boolean;
  cross_zone_id: string | null;
  cross_zone_window: number;
  trigger_count: number;
  trigger_window: number;
  response_profile_id: string | null;
  silent: boolean;
  /** The entity reporting this zone's battery (§4.2), for diagnostics and
   * the low_battery moment. Never the zone's own entity. */
  battery_entity_id: string | null;
}

export interface GroupConfig {
  id?: string;
  name: string;
  area_id: string;
  members: string[];
  n: number;
  window_seconds: number;
  suppress_members: boolean;
  response_profile_id: string | null;
}

export interface ChimeTarget {
  entity_id: string;
  /** Quiet hours of this target alone; null falls back to the global ones. */
  quiet_start: string | null;
  quiet_end: string | null;
}

export interface ChimeConfig {
  targets: ChimeTarget[];
  mode: "sound" | "speech";
  sound: string | null;
  tts_entity: string | null;
  volume: number | null;
  quiet_start: string | null;
  quiet_end: string | null;
  during_exit: boolean;
}

export interface ScenarioConfig {
  id?: string;
  name: string;
  areas: string[];
  ha_master_state: string;
  icon: string | null;
  exit_delay_override: number | null;
  siren_duration_override: number | null;
  response_profile_id: string | null;
  require_code_to_arm: boolean | null;
  require_code_to_disarm: boolean | null;
  /** Who may use this scenario. null = everyone with the permission. */
  allowed_user_ids: string[] | null;
}

/** A person (SPEC §8.1). No hash ever crosses the API: what the panel is told
 * is whether a code exists, and what it sends is a new one. */
export interface UserConfig {
  id?: string;
  name: string;
  has_code: boolean;
  has_duress_code: boolean;
  ha_user_id: string | null;
  permissions: string[];
  allowed_area_ids: string[] | null;
  allowed_scenario_ids: string[] | null;
  valid_from: string | null;
  valid_until: string | null;
  code_exempt_when_identified: boolean;
  enabled: boolean;
}

/** Which operations need a code (SPEC §8.2). */
export type CodePolicyConfig = Record<string, boolean>;

/** Code length and lockout (SPEC §8.1, §8.4). */
export interface SecurityConfig {
  code_length: number;
  lockout_failures: number;
  lockout_window: number;
  lockout_duration: number;
}

/** Which categories the log writes, and for how long (SPEC §10.2, §10.3). */
export interface LogSettingsConfig {
  enabled: Record<string, boolean>;
  retention_days: Record<string, number>;
}

/** How much the retained MQTT state message says (§9.2, part 2 decision 3). */
export type MqttDetail = "minimal" | "standard" | "full";

export interface MqttConfig {
  enabled: boolean;
  /** Empty means the default, foyer/<install_id>/…, resolved by the backend. */
  command_topic: string;
  state_topic: string;
  detail: MqttDetail;
  retain: boolean;
  qos: number;
}

/** An arming device (SPEC §9.3). A keypad is shared and carries a code; a tag
 * is one person's, carries none, and its identity is the user it names. */
export interface DeviceConfig {
  id?: string;
  name: string;
  kind: "keypad" | "tag";
  /** What a keypad puts in its own messages. A tag never has one. */
  ref: string | null;
  entity_id: string | null;
  event_type: string | null;
  user_id: string | null;
  command: "arm" | "disarm" | "toggle";
  scenario_id: string | null;
  enabled: boolean;
}

export interface SettingsConfig {
  siren_duration: number;
  arm_hold_timeout: number;
  default_profile_id: string | null;
  technical_profile_id: string | null;
  silent_suppresses: string[];
  camera_dir: string;
  log: LogSettingsConfig;
  default_entry_delay: number;
  default_exit_delay: number;
  /** The language of the messages Foyer sends out, not of this panel: the
   * panel follows each Home Assistant user. null means the system language. */
  language: string | null;
  /** Whether the first-run wizard has been completed or dismissed (§15.1). */
  wizard_done: boolean;
  security: SecurityConfig;
  mqtt: MqttConfig;
  /** Below what percentage a numeric battery entity counts as low (§4.2). */
  low_battery_threshold: number;
}

export interface FoyerConfig {
  areas: AreaConfig[];
  zones: ZoneConfig[];
  scenarios: ScenarioConfig[];
  groups: GroupConfig[];
  profiles: ProfileConfig[];
  settings: SettingsConfig;
  chime: ChimeConfig;
  users: UserConfig[];
  devices: DeviceConfig[];
  code_policy: CodePolicyConfig;
}

export interface ConfigMeta {
  zone_types: { type: string; available: boolean; preset: Partial<ZoneConfig> }[];
  zone_domains: string[];
  chime_domains: string[];
  ha_states: string[];
  bounds: Record<string, [number, number]>;
  action_kinds: ActionKind[];
  /** Which entity domains each action kind may point at. */
  action_domains: Record<string, string[]>;
  silenceable: string[];
  moments: string[];
  /** Moments no phase raises yet: selectable, and labelled as such. */
  future_moments: string[];
  template_variables: string[];
  max_conditions: number;
  log_categories: string[];
  log_severities: string[];
  outcomes: string[];
  retention_bounds: [number, number];
  /** §8.3, and the operations of the §8.2 table, for page 7. */
  permissions: string[];
  operations: string[];
  /** Operations no phase raises yet: the policy is complete, the features
   * are not, and the page says which is which. */
  future_operations: string[];
  /** The channels on which the per-user exemption of §8.2 can apply. */
  identifying_channels: string[];
  /** The stored configuration's schema version, shown beside a backup. */
  schema_version: [number, number];
}

// --- the event log: foyer/log/* (store/log_store.py) ------------------------------

export interface LogRow {
  id: number;
  ts: string;
  category: string;
  event_type: string;
  severity: "info" | "warning" | "alarm";
  area_id: string | null;
  zone_id: string | null;
  scenario_id: string | null;
  incident_id: string | null;
  user_id: string | null;
  user_name: string | null;
  channel: string | null;
  device_id: string | null;
  outcome: string | null;
  detail: Record<string, unknown>;
}

export interface LogQuery {
  start?: string | null;
  end?: string | null;
  categories?: string[];
  severity?: string | null;
  area_id?: string | null;
  zone_id?: string | null;
  incident_id?: string | null;
  outcome?: string | null;
  limit?: number;
  offset?: number;
}

export interface LogPage {
  rows: LogRow[];
  total: number;
}

export interface LogExport {
  filename: string;
  content: string;
  rows: number;
  total: number;
  truncated: boolean;
}

/** A configuration backup: the stored document with its schema version. */
export interface ConfigBackup {
  foyer: string;
  version: [number, number];
  created: string;
  config: FoyerConfig;
}

export interface Problem {
  code: string;
  kind: string;
  ref: string | null;
  field: string | null;
  detail?: string; // only for request_failed: what Home Assistant said
}

export interface EditResult {
  success: boolean;
  id?: string;
  problems: Problem[];
}

export interface ZoneProposal {
  entity_id: string;
  name: string;
  state: string | null;
  device_class: string | null;
  trigger_kind: "state" | "numeric" | "event";
  options: string[];
  proposed: string[];
  zone_type: string | null;
}

// --- page 9: diagnostics and the simulator (core/diagnostics.py, core/simulate.py)

export interface DiagnosticsZone {
  zone_id: string;
  name: string;
  area_id: string;
  entity_id: string;
  enabled: boolean;
  /** The entity's raw state. null means the entity does not exist at all,
   * which is not the same as unavailable and is usually a rename. */
  state: string | null;
  /** Would Foyer count this as triggered right now? Resolved through the
   * zone's own trigger, which is why the column exists at all (INV-5). */
  triggered: boolean;
  /** An event or tag zone is never "open": it has scans, not a state. */
  momentary: boolean;
  available: boolean;
  last_changed: string | null;
  last_reported: string | null;
  fault: string | null;
  supervision_timeout: number | null;
  supervision_due: string | null;
  battery_entity_id: string | null;
  battery_level: number | null;
  battery_low: boolean;
  signal: { value: number; unit: string } | null;
  bypassed: string | null;
  blocks_arming: boolean;
  /** "fault" or "open": which of §5.4's two reasons, so the row says what to
   * do about it rather than only that something is wrong. */
  blocks_because: string | null;
}

export interface DiagnosticsDevice {
  device_id: string;
  name: string;
  kind: string;
  enabled: boolean;
  entity_id: string | null;
  state: string | null;
  available: boolean;
  last_changed: string | null;
  /** A keypad speaks over MQTT and has no entity, so there is nothing to be
   * available: the table says so rather than claiming it is healthy. */
  watchable: boolean;
}

export interface Diagnostics {
  at: string;
  zones: DiagnosticsZone[];
  devices: DiagnosticsDevice[];
  missing_entities: string[];
}

export interface TraceAction {
  action_id: string;
  kind: string;
  name: string;
  moment: string;
  profile_id: string | null;
  ran: boolean;
  /** "silent" | "already_running" | "condition" | "held_by_delay", or null
   * when it ran. Translated in the panel, never sent as a sentence. */
  skipped: string | null;
  /** For "condition": which ones failed, well enough to act on (§11.2). */
  conditions: string[];
}

export interface TraceBatch {
  moment: string;
  profile_id: string | null;
  profile_name: string;
  /** Where the profile was inherited from: zone, group, area, scenario,
   * technical, default or none (§6 requires the UI to show this). */
  source: string;
  area_id: string | null;
  zone_id: string | null;
  group_id: string | null;
  actions: TraceAction[];
}

export interface TraceOccurrence {
  moment: string;
  area_id: string | null;
  zone_id: string | null;
  zone_ids: string[];
  group_id: string | null;
  incident_id: string | null;
  scenario_id: string | null;
  detail: Record<string, string>;
}

export interface TraceStep {
  at: string;
  kind: "setup" | "request" | "zone" | "tick";
  zone_id: string | null;
  zone_state: string | null;
  scenario_id: string | null;
  accepted: boolean;
  reason: string | null;
  blocking_zones: string[];
  low_battery_zones: string[];
  areas: {
    area_id: string;
    was: string;
    now: string;
    timer_kind: string | null;
    timer_due: string | null;
  }[];
  occurrences: TraceOccurrence[];
  batches: TraceBatch[];
  loose_actions: TraceAction[];
  scheduled: {
    at: string;
    kind: string;
    profile_id: string | null;
    moment: string | null;
    area_id: string | null;
  }[];
}

export interface Simulation {
  at: string;
  scenario_id: string | null;
  area_ids: string[];
  /** The run stopped because it ran out of room, not because the house went
   * quiet. Said plainly: a trace that simply ends reads as "it was over". */
  truncated: boolean;
  steps: TraceStep[];
}

export interface SimulationQuery {
  scenario_id?: string | null;
  area_ids?: string[];
  start?: string | null;
  zones?: { zone_id: string; state: string; at: number }[];
  entities?: Record<string, string>;
  horizon?: number;
}

export type PageId =
  | "overview"
  | "areas"
  | "zones"
  | "scenarios"
  | "profiles"
  | "groups"
  | "users"
  | "devices"
  | "log"
  | "settings"
  | "test";
