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

export interface HomeAssistant {
  language: string;
  states: Record<string, HassEntity>;
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
}

export interface StatusScenario {
  id: string;
  name: string;
  icon: string | null;
  areas: string[];
  ha_master_state: string;
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
}

// Result of foyer/arm and foyer/disarm (SPEC §9.1).
export interface CommandResult {
  success: boolean;
  reason: string | null;
  blocking_zones: { id: string; name: string }[];
  bypassed_zones: { id: string; name: string }[];
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
}

export interface SettingsConfig {
  siren_duration: number;
  arm_hold_timeout: number;
  default_profile_id: string | null;
  technical_profile_id: string | null;
  silent_suppresses: string[];
  camera_dir: string;
}

export interface FoyerConfig {
  areas: AreaConfig[];
  zones: ZoneConfig[];
  scenarios: ScenarioConfig[];
  groups: GroupConfig[];
  profiles: ProfileConfig[];
  settings: SettingsConfig;
  chime: ChimeConfig;
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

export type PageId =
  | "overview"
  | "areas"
  | "zones"
  | "scenarios"
  | "profiles"
  | "groups"
  | "settings";
