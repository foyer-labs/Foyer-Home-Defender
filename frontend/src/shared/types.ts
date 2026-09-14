// The subset of Home Assistant's frontend objects that Foyer uses.

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

// foyer/status and foyer/subscribe payload (runtime/system.py: status()).
export type AreaState = "disarmed" | "armed" | "triggered";

export interface FoyerStatus {
  active_scenario_id: string | null;
  areas: { id: string; name: string; state: AreaState; entity_id: string | null }[];
  scenarios: { id: string; name: string; areas: string[]; ha_master_state: string }[];
  zones: {
    id: string;
    name: string;
    area_id: string;
    entity_id: string;
    state: string | null;
    fault: boolean;
    open: boolean;
  }[];
}
