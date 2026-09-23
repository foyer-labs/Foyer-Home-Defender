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
  /** The house's own time zone. The backend reads a date the panel sends
   * without one in this zone, so the panel shows times in it too. */
  config?: { time_zone?: string };
  user?: { id: string; name: string; is_admin: boolean };
  /** The entity registry as the frontend carries it: which integration an
   * entity belongs to, whatever it has been renamed to. */
  entities?: Record<
    string,
    { entity_id: string; platform?: string; translation_key?: string }
  >;
  connection: HassConnection;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: Record<string, unknown>,
  ): Promise<unknown>;
  localize(key: string, values?: Record<string, unknown>): string;
  /** A state in the Home Assistant user's own words ("Open" for a door's
   * `on`). Present since Home Assistant 2023.9; optional so an older one, or
   * a harness, falls back to the raw state. */
  formatEntityState?(stateObj: HassEntity, state?: string): string;
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
  /** `entity_id` is whatever the household renamed the master to: the card
   * recognises it by this, never by the id it was created with. */
  master: { state: AreaState; mode: string | null; entity_id: string | null };
  areas: StatusArea[];
  scenarios: StatusScenario[];
  zones: StatusZone[];
  technical: StatusTechnical[];
  incident: StatusIncident | null;
  chime_enabled: boolean;
  /** Endpoint keypads whose last request arrived unencrypted (§9.2.1). */
  devices_in_clear?: string[];
  security: StatusSecurity;
  /** A walk test in progress (§11.3), or null. The panel and every card
   * layout read the banner from here: one payload, so the two can never
   * disagree about whether the house is answering. */
  walk_test: WalkTestStatus | null;
  /** Automatic arming (§9.4). On the live status, not only on page 12: two
   * minutes is not long enough to go and find the right page. */
  auto: AutoStatus;
}

/** What a walk test looks like from outside (SPEC §11.3). */
export interface WalkTestStatus {
  started_at: string;
  /** When it ends if nothing else happens: the nearer of the two below. */
  deadline: string;
  /** Pushed back by every detection. */
  until: string;
  /** Never moves, whatever detects (part 2 decision 4). */
  hard_until: string;
  window: number;
  armed_areas: string[];
  user_id: string | null;
  user_name: string | null;
  channel: string | null;
  /** Every zone the walk should have reached, so that a zone with no
   * detection reads as a finding rather than as an empty row. */
  expected_zones: string[];
  detections: Record<string, { first: string; last: string; count: number }>;
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
  /** On a `code_required` refusal: the explicit setting that asked for the
   * code, so the prompt can name it (SPEC §8.2, "the UI names the area that
   * is asking"). Absent from an older backend, and absent on every other
   * refusal. */
  code_required_by?: CodeRequiredBy | null;
}

export interface CodeRequiredBy {
  kind: "area" | "scenario" | "policy";
  id: string | null;
  name: string | null;
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
  /** The outer defence ring (§4.5). An automatic rule never disarms it,
   * whatever the rule says: enforced in the engine, not here (§9.4). */
  is_perimeter: boolean;
}

// --- automatic arming rules (SPEC §9.4) -------------------------------------------

export type RuleTriggerKind = "absence" | "presence" | "time" | "entity";
export type RuleActionKind = "arm" | "disarm" | "switch";
export type SuspensionKind = "until" | "next" | "visitor";

export interface RuleTriggerConfig {
  kind: RuleTriggerKind;
  /** The people an absence or presence rule watches, or the one entity an
   * entity rule does. */
  entity_ids: string[];
  state: string | null;
  minutes: number;
  /** "HH:MM" for a time rule. */
  at: string | null;
  /** 0 = Monday. Empty means every day. */
  weekdays: number[];
}

export interface RuleGuardsConfig {
  only_when_disarmed: boolean;
  only_when_ready: boolean;
  /** No interior zone has moved for this many minutes. null is off. */
  quiet_minutes: number | null;
}

export interface RuleWindowConfig {
  weekdays: number[];
  after: string | null;
  before: string | null;
}

export interface RuleConfig {
  id?: string;
  name: string;
  trigger: RuleTriggerConfig;
  action: RuleActionKind;
  scenario_id: string | null;
  area_ids: string[];
  window: RuleWindowConfig;
  guards: RuleGuardsConfig;
  /** The cancellable countdown before it acts. 0 means at once. */
  grace_seconds: number;
  notify_contact_ids: string[];
  enabled: boolean;
  /** Arm anyway, excluding open zones that are bypassable (decision 126). */
  exclude_open_zones: boolean;
}

/** A suspension, or an expected-visitor window (§9.4). Runtime state, not
 * configuration: it expires, and setting one is three clicks rather than a
 * configuration edit (part 2 decision 7). */
export interface SuspensionConfig {
  id: string;
  kind: SuspensionKind;
  rule_ids: string[];
  name: string | null;
  start: string | null;
  until: string | null;
  reduced_scenario_id: string | null;
  created_at: string | null;
  user_id: string | null;
  user_name: string | null;
}

export interface PendingRuleAction {
  id: string;
  rule_id: string;
  rule_name: string;
  action: RuleActionKind;
  due: string;
  started_at: string;
  seconds: number;
  scenario_id: string | null;
  area_ids: string[];
  suspension_name: string | null;
}

export interface NextAutoAction {
  rule_id: string;
  rule_name: string;
  action: RuleActionKind;
  at: string | null;
  scenario_id: string | null;
  area_ids: string[];
  /** Set while it is already counting down, which is the one state in which
   * somebody can still stop it. */
  pending_id: string | null;
  suspension: SuspensionConfig | null;
}

export interface AutoStatus {
  /** switch.foyer_auto_arming (§9.4, §13). */
  enabled: boolean;
  /** Whether a rule may leave the house less protected at all (§9.4). */
  allow_auto_disarm: boolean;
  next: NextAutoAction | null;
  pending: PendingRuleAction[];
  suspensions: SuspensionConfig[];
  /** Which guard is currently holding each rule back, by rule id. */
  blocked: Record<string, string>;
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
  /** Seconds from the start of the escalation, or null for an ordinary
   * action (§7.2). An escalation step is a notification at an offset: the
   * offset is the only thing that makes it one. */
  escalation_offset: number | null;
}

/** Who a notify action reaches: a contact, and which of their channels.
 * A null channel means the contact's own order of priority decides. */
export interface NotifyContact {
  contact_id: string;
  channel_id: string | null;
}

export type ContactChannelKind = "push" | "sms" | "voice" | "chat" | "other";

export interface ContactChannelConfig {
  id?: string;
  kind: ContactChannelKind;
  /** Any `notify.*` service, or a notify entity. Foyer orchestrates
   * transports; it does not implement them (§1.2). */
  service: string;
  target: string;
  data: Record<string, unknown>;
  /** Whether this transport can carry the button that acknowledges an
   * alarm. Declared rather than guessed: a transport discards a key it does
   * not know without a word. */
  actionable: boolean;
  enabled: boolean;
}

export interface ContactConfig {
  id?: string;
  name: string;
  /** Ordered, highest priority first (§7.1). */
  channels: ContactChannelConfig[];
  quiet_start: string | null;
  quiet_end: string | null;
  /** What counts as high severity inside the quiet window: the log's own
   * scale of info / warning / alarm (§10.1). */
  quiet_min_severity: "info" | "warning" | "alarm";
  linked_user_id: string | null;
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
  /** False only for a zone an importer brought across with a proposed
   * trigger (INV-5): it stays off until somebody confirms it. Set by the
   * backend, never by the page. */
  trigger_confirmed?: boolean;
  /** The cameras that show this zone, in order (§6.2.1). A notification set
   * to show the zone's cameras attaches these. */
  camera_entity_ids: string[];
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
  /** After how many days a row keeps a stable identifier instead of a name
   * (§10.4). null is off, and off is the default: it trades away the ability
   * to answer "who disarmed that night" for rows older than this. */
  pseudonymise_after: number | null;
  /** Whether removing the integration takes the log database with it (§16).
   * Off, so an installation that never answered keeps its history. */
  delete_on_uninstall: boolean;
}

/** How many rows an erasure would touch, and which key found them (§10.4).
 * `by_name` counts the rows a rename or a row written before this person was
 * a Foyer user leaves behind; `wide` is what an export would carry. */
export interface PersonCounts {
  by_id: number;
  by_name: number;
  /** Configuration rows about their account, written by whoever edited it. */
  about: number;
  total: number;
  wide: number;
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
  /** A keypad only: the one path it may speak on (§9.2.1, decision 98). */
  transport: "mqtt" | "http";
  /** Whether a token exists. The token itself is shown once, on generation,
   * and never again; its hash never reaches the panel. */
  has_token?: boolean;
  /** An API device on the endpoint only (§9.2.2): what it may read and do,
   * every scope off until switched on (decision 115). */
  scopes: DeviceScope[];
  /** The read scopes it reads with its token alone (decision 117). */
  free_scopes: DeviceScope[];
  /** Where its arm and disarm reach; null is everywhere its code's owner
   * may go. */
  arm_scenario_ids: string[] | null;
  arm_area_ids: string[] | null;
  disarm_area_ids: string[] | null;
  /** How long a code unlocks the after-a-code scopes, 30–600 s (decision 118). */
  unlock_seconds: number;
  /** Scopes beyond status may cross the network in the clear (decision 119). */
  clear_text_confirmed: boolean;
}

export type DeviceScope =
  | "status"
  | "zones"
  | "batteries"
  | "health"
  | "log"
  | "arm"
  | "disarm"
  | "exclude"
  | "acknowledge";

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
  /** How long a walk test runs without a detection before it ends itself
   * (§5.3, §11.3). Bounded in code: the auto-exit cannot be switched off. */
  walk_test_timeout: number;
  /** The DTMF acknowledgement webhook's id, or null when it is off (§7.2).
   * A Home Assistant webhook is not authenticated, so this URL is a way of
   * stopping an alarm: it exists only while somebody wants it to. */
  ack_webhook_id: string | null;
  /** Whether an automatic rule may disarm anything at all (§9.4 point 2).
   * Off until somebody turns it on, having read what it costs. */
  allow_auto_disarm: boolean;
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
  contacts: ContactConfig[];
  rules: RuleConfig[];
  code_policy: CodePolicyConfig;
  health: HealthConfig;
}

// --- system health (SPEC §12) -----------------------------------------------------

/** One radio integration whose zones are counted together (§12.5).
 *
 * `entry_id` is the Home Assistant config entry the radio *is*: Home
 * Assistant has no general notion of a radio, and the config entry is the one
 * thing every entity of a ZHA, Z-Wave JS or Zigbee2MQTT installation shares.
 * `coordinator_entity_id` is named by hand and is the whole feature — zones
 * going quiet while the coordinator answers is interference, zones going
 * quiet with the coordinator gone is a dead switch. */
export interface RadioConfig {
  id?: string;
  name: string;
  entry_id: string;
  coordinator_entity_id: string | null;
  n_zones: number | null;
  window: number | null;
  enabled: boolean;
}

export interface WatchdogConfig {
  enabled: boolean;
  url: string;
  interval: number;
  timeout: number;
  failures: number;
  /** Off by default and behind an explicit warning (P-1): a ping saying
   * "armed, Night, nobody home" tells a third party when to come. */
  payload: boolean;
}

export interface HealthConfig {
  mains_entity_id: string | null;
  /** Which states of that entity mean the mains has failed. Explicit for the
   * same reason INV-5 exists: a UPS says `on` and a power sensor says `off`. */
  mains_lost_states: string[];
  watchdog: WatchdogConfig;
  radios: RadioConfig[];
  rf_zones: number;
  rf_window: number;
  rf_confirm: number;
  channel_sweep: number;
  channel_failures: number;
  repair_after: number;
}

/** What page 14 reads. Everything here is computed by the backend from the
 * state the engine produced: the panel never works out for itself whether a
 * radio is being jammed. */
export interface HealthStatus {
  now: string;
  causes: string[];
  unreachable_zones: { id: string; name: string; since: string; days: number }[];
  mains: {
    entity_id: string | null;
    lost_states: string[];
    state: string | null;
    lost: boolean | null;
    since: string | null;
  };
  watchdog: {
    enabled: boolean;
    /** Whether a URL is configured — never the URL itself. A healthchecks.io
     * ping URL is the credential, and this payload is open to anyone holding
     * view_log; the editor reads the real value through foyer/config, which
     * is edit_config. */
    url_set: boolean;
    interval: number;
    timeout: number;
    failures_allowed: number;
    payload: boolean;
    failures: number;
    down_since: string | null;
    last_ok: string | null;
    last_attempt: string | null;
    last_error: string;
    ever_ok: boolean;
  };
  channels: {
    key: string;
    contact_id: string;
    contact_name: string;
    channel_id: string;
    kind: string;
    service: string;
    fault: string | null;
    since: string | null;
    failures: number;
    last_ok: string | null;
    checked: boolean;
  }[];
  radios: {
    id: string;
    name: string;
    entry_id: string;
    coordinator_entity_id: string | null;
    coordinator_state: string | null;
    enabled: boolean;
    zones: number;
    quiet: number;
    threshold: number;
    window: number;
    suspected_since: string | null;
    confirmed: boolean;
    coordinator_down_since: string | null;
  }[];
  rf: { zones: number; window: number; confirm: number };
  faults: string[];
  repair_after: number;
}

export interface RadioCandidate {
  entry_id: string;
  title: string;
  domain: string;
  zones: number;
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
  /** The bounds of the pseudonymisation delay, and the short retention preset
   * §10.4 offers to installations with domestic staff, with the categories it
   * touches — the ones that name people. */
  pseudonymise_bounds: [number, number];
  short_retention: number;
  named_categories: string[];
  /** What page 12 needs to build a rule without knowing §9.4 by heart. */
  rule_triggers: RuleTriggerKind[];
  rule_actions: RuleActionKind[];
  suspension_kinds: SuspensionKind[];
  presence_domains: string[];
  max_grace_seconds: number;
  max_rule_minutes: number;
  /** §8.3, and the operations of the §8.2 table, for page 7. */
  permissions: string[];
  operations: string[];
  /** Operations no phase raises yet: the policy is complete, the features
   * are not, and the page says which is which. */
  future_operations: string[];
  /** The channels on which the per-user exemption of §8.2 can apply. */
  identifying_channels: string[];
  /** Which moments an escalation step may answer, and the two things that
   * escalate at all (§5.5, §5.6, §7.2). */
  escalation_moments: string[];
  escalation_kinds: string[];
  contact_channel_kinds: ContactChannelKind[];
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
  reason?: string | null;
  code_required_by?: CodeRequiredBy | null;
}

/** One sentence of the Alarmo importer's report (§20.2): a stable code the
 * panel turns into words, and the values that fill it. */
export interface AlarmoLine {
  code: string;
  params: Record<string, string | number>;
}

/** The words the importer names new things with, from this panel's own
 * translations: the backend writes no word a person reads. */
export interface AlarmoLabels {
  modes: Record<string, string>;
  split: string;
  profile: string;
}

/** What an import would do, before anything is written. `refused` when the
 * file is not one it will read; otherwise the report, what would be created,
 * and the fingerprint the apply must carry back. */
export interface AlarmoPreview {
  success: boolean;
  refused?: AlarmoLine;
  lines?: AlarmoLine[];
  counts?: Record<string, number>;
  created?: Record<"areas" | "scenarios" | "extended" | "people" | "profiles", string[]>;
  problems?: Problem[];
  fingerprint?: string;
  reason?: string;
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
  /** For "condition": which ones failed, as fields rather than a sentence.
   * The backend writes no words a person reads (§15.2); the panel builds the
   * phrase from `kind` plus the rest. */
  conditions: (
    | { kind: "time"; after: string; before: string }
    | { kind: "state"; entity_id: string; operator: string; state: string }
  )[];
  /** Who a notification reached, and who its quiet hours held back (§7.1),
   * and which escalation step it was (§7.2). */
  recipients: { contact_id: string; channel_id: string; kind: string }[];
  quiet: string[];
  /** The cameras this notification would have carried, one picture each,
   * and how many did not fit (§6.2.1). Entity ids; nothing was fetched. */
  cameras: string[];
  cameras_omitted: number;
  escalation: string | null;
  escalation_step: number | null;
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
    /** An escalation step still to come: "escalation step 1 at +60s ->
     * Luca (SMS)" (§11.2). Read off the Decision, never predicted.
     * `escalation` is which of the two escalations it belongs to. */
    escalation: string | null;
    step: number | null;
    offset: number | null;
    contact_ids: string[];
    channel_ids: string[];
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
  /** Not for the command, which only reads: for the arming the run uses as
   * its premise, which goes through §8.2 like any other arming. */
  code?: string;
}

/** What a real action test did (§11.4). It really executed. */
export interface TestActionResult {
  success: boolean;
  reason: string | null;
  kind?: string;
  error?: string | null;
}

export interface TestActionQuery {
  /** One configured action of one profile (page 5)… */
  profile_id?: string;
  action_id?: string;
  /** …or one channel of one contact (page 6), which is §11.4's "a test
   * button next to every action and every contact channel"… */
  contact_id?: string;
  channel_id?: string;
  /** …or a notification service on its own, which is what the wizard tests. */
  service?: string;
  message?: string;
  code?: string;
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
  | "contacts"
  | "log"
  | "settings"
  | "rules"
  | "test"
  | "health"
  | "api";
