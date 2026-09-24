// foyer-card: an area's (or the master's) state, its countdown, and arm/disarm
// (SPEC §15.3). The card decides nothing (INV-2): it sends a command, the
// engine accepts or refuses, and the card renders the answer.
//
// Three layouts. `full` is the alarm dashboard: every area with its state and
// countdown, the scenario selector, the zones that would stop it arming, and —
// when a code may be needed — the keypad. `compact` is one row for the top of
// an existing dashboard. `keypad` is the wall tablet: the state, a PIN pad and
// the actions, nothing else.
//
// The keypad collects digits and transmits them. It never checks one, never
// knows how many are right, and never decides what a code allows (INV-2): a
// check here would be decoration, since anyone with Home Assistant access can
// call the service directly. What it does know is how many digits to collect,
// which the backend tells it, because a keypad has to know when to stop.
import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { live } from "lit/directives/live.js";

import { loadStrings, t, type Strings } from "../shared/i18n";
import { stateStyles } from "../shared/styles";
import { inHouseZone, mmss, secondsUntil } from "../shared/time";
import type {
  AreaState,
  CommandResult,
  FoyerStatus,
  HomeAssistant,
  PendingRuleAction,
  StatusArea,
} from "../shared/types";

type Layout = "full" | "compact" | "badge" | "keypad";

interface FoyerCardConfig {
  type: string;
  entity?: string;
  layout?: Layout;
}

const ENTITY_PREFIX = "alarm_control_panel.foyer_";
const MASTER = "alarm_control_panel.foyer_master";

/** Foyer's panels, renamed ones included: the entity registry says which
 * integration an entity belongs to, and the prefix is only the fallback for
 * a frontend that does not carry it. */
function foyerPanels(hass: HomeAssistant): string[] {
  const registry = hass.entities;
  return Object.keys(hass.states)
    .filter((id) => id.startsWith("alarm_control_panel."))
    .filter((id) =>
      registry?.[id] ? registry[id].platform === "foyer" : id.startsWith(ENTITY_PREFIX),
    )
    .sort();
}

/** The master's entity id as it is now, by the unique id it was created with. */
function masterOf(hass: HomeAssistant): string | undefined {
  const registry = hass.entities;
  if (!registry) return hass.states[MASTER] ? MASTER : undefined;
  return (
    Object.values(registry).find(
      (e) => e.platform === "foyer" && e.translation_key === "master",
    )?.entity_id ?? (hass.states[MASTER] ? MASTER : undefined)
  );
}

// A refusal a forced arm could override (§5.4): zones open, or in fault. The
// card offers it for the same reason the panel does — the alternative is
// excluding the zones one by one, from the thing on the wall, while leaving.
const FORCEABLE = new Set(["zone_open", "zone_fault"]);

// Refusals the keypad answers: the first asks for a code, the second says the
// one typed was wrong. Both clear the pad and leave it open.
const WANTS_CODE = new Set(["code_required", "bad_code"]);

// How long typed digits wait for the key that sends them. A code typed on a
// wall tablet and walked away from must not go out with whatever the next
// person presses — refused as a wrong code, counted towards the lockout, or,
// when it was right, acting in its owner's name (card review).
const CODE_IDLE_MS = 30_000;

// The commands of the banners — cancel a countdown, acknowledge, end the walk
// test. They are pressed without the pad in mind, so the digits on it are not
// theirs to take: sent without a code, and if the engine wants one, the pad
// opens on that command as it does for any other.
const BANNER_COMMANDS = new Set([
  "foyer/auto/cancel",
  "foyer/acknowledge",
  "foyer/walk_test",
]);

interface Feedback {
  text: string;
  /** The command to repeat with force, when forcing could get past it. */
  retry?: Record<string, unknown>;
  /** Something worth knowing rather than something that went wrong: a low
   * battery warns and never blocks. Excluding the zone is done from the
   * panel, where the list of zones is. */
  warning?: boolean;
  /** An answer about the code itself — wrong, or locked out — shown inside
   * the pad, next to the digits it is about, rather than under the buttons
   * where a wall tablet at 220 px puts it below the fold. */
  pad?: boolean;
  /** The refusal it renders, when it renders one. */
  reason?: string;
}

class FoyerCard extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
    _strings: { state: true },
    _status: { state: true },
    _busy: { state: true },
    _feedback: { state: true },
    _code: { state: true },
    _padOpen: { state: true },
    _pending: { state: true },
    _retype: { state: true },
    _tick: { state: true },
  };

  hass?: HomeAssistant;
  private _config?: FoyerCardConfig;
  private _strings?: Strings;
  private _status?: FoyerStatus;
  private _busy = false;
  private _feedback?: Feedback;
  // What has been typed on the pad. Held for as long as it takes to send it,
  // never stored anywhere, and cleared the moment the backend answers.
  private _code = "";
  private _padOpen = false;
  // The command the backend refused for want of a code. The pad's confirm key
  // repeats exactly this one, so typing a code has something to act on: a pad
  // that only collects digits is a pad that does nothing.
  private _pending?: Record<string, unknown>;
  // Digits were on the pad when a banner's command asked for a code, and
  // were cleared because they were not typed for it: the pad says so, or
  // the person who typed them waits for a command that will never go out.
  private _retype = false;
  // The entry countdown the pad last opened itself for, so that somebody
  // who folds it away again is not overruled on the next status push.
  private _entryOpened?: string;
  private _tick = 0;
  private _offset = 0;
  private _language?: string;
  private _unsubscribe?: Promise<() => Promise<void>>;
  private _timer?: number;
  private _idle?: number;

  static getStubConfig(hass: HomeAssistant): FoyerCardConfig {
    // The master if it exists: a card that shows the whole house is the one
    // most people want first.
    const entities = foyerPanels(hass);
    const master = masterOf(hass);
    return {
      type: "custom:foyer-card",
      entity: master && entities.includes(master) ? master : entities[0],
      layout: "full",
    };
  }

  static getConfigElement(): HTMLElement {
    return document.createElement("foyer-card-editor");
  }

  setConfig(config: FoyerCardConfig): void {
    this._config = config;
  }

  getCardSize(): number {
    return this._layout === "compact" || this._layout === "badge" ? 1 : 3;
  }

  private get _layout(): Layout {
    const layout = this._config?.layout;
    return layout === "compact" || layout === "keypad" || layout === "badge"
      ? layout
      : "full";
  }

  private get _codeLength(): number {
    return this._status?.security.code_length ?? 6;
  }

  /** Is the keypad worth showing at all? While nobody holds a code, nothing
   * will ever ask for one, and a pad that can only be ignored is furniture. */
  private get _codeUsed(): boolean {
    return Boolean(this._status?.security.enforced);
  }

  private _press(digit: string): void {
    if (this._code.length >= this._codeLength) return;
    this._code += digit;
    this._feedback = undefined;
    this._retype = false;
    this._touch();
  }

  /** Forget the typed digits after a while without a key, and with them the
   * command they were waiting to confirm. */
  private _touch(): void {
    window.clearTimeout(this._idle);
    this._idle = window.setTimeout(() => this._expire(), CODE_IDLE_MS);
  }

  private _forget(): void {
    window.clearTimeout(this._idle);
    this._idle = undefined;
    this._code = "";
    this._pending = undefined;
    this._retype = false;
  }

  /** The idle timeout: the digits go, and so does everything that was said
   * about them — a "wrong code" still showing to the next person reads as
   * an answer to them. The pad folds away too, unless an entry countdown is
   * what opened it. */
  private _expire(): void {
    this._forget();
    this._feedback = undefined;
    if (!this._entryOpened) this._padOpen = false;
  }

  /** The pad from a physical keyboard: digits, Backspace, and Enter for the
   * key that sends. */
  private _padKey(e: KeyboardEvent): void {
    if (this._busy || e.ctrlKey || e.metaKey || e.altKey) return;
    if (/^[0-9]$/.test(e.key)) {
      this._press(e.key);
    } else if (e.key === "Backspace") {
      this._code = this._code.slice(0, -1);
      this._touch();
    } else if (e.key === "Enter" && this._pending && this._code) {
      void this._run(this._pending);
    } else {
      return;
    }
    e.preventDefault();
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => {
      // Only while something is actually counting: a master card that ticked
      // all day would redraw a wall tablet 86 400 times for nothing.
      if (
        this._area?.timer ||
        this._status?.areas.some((a) => a.timer) ||
        this._status?.walk_test ||
        this._pendingAuto ||
        this._status?.security.locked_until
      ) {
        this._tick += 1;
      }
    }, 1000);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsub) => unsub()).catch(() => undefined);
    this._unsubscribe = undefined;
    window.clearInterval(this._timer);
    // A card taken off the screen keeps no code: coming back to the view
    // hours later must not find the digits, or the command, still there.
    this._forget();
    this._padOpen = false;
    this._feedback = undefined;
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (!changed.has("hass") || !this.hass) return;
    if (this.hass.language !== this._language) {
      this._language = this.hass.language;
      loadStrings(this.hass)
        .then((strings) => (this._strings = strings))
        .catch(() => {
          // A wall tablet reconnecting can lose this one call. Forget the
          // language so the next update asks again: without it the card
          // renders nothing at all until somebody reloads the page, which
          // is the worst failure an alarm card has.
          this._language = undefined;
        });
    }
    if (!this._unsubscribe && this.isConnected) {
      this._unsubscribe = this.hass.connection.subscribeMessage<FoyerStatus>(
        (status) => {
          this._offset = Date.parse(status.now) - Date.now();
          this._status = status;
          // An entry countdown that will want a code to stop opens the pad
          // by itself: the seconds spent unfolding it are the ones the
          // person at the door does not have. Read from what the backend
          // publishes; whether the code is right is still its call (INV-2).
          const entry = this._entryWantsCode();
          if (entry && entry !== this._entryOpened) this._padOpen = true;
          this._entryOpened = entry;
        },
        { type: "foyer/subscribe" },
      );
      this._unsubscribe.catch(() => (this._unsubscribe = undefined));
    }
  }

  /** The master, by the id it has now: a household may rename it. */
  private get _isMaster(): boolean {
    const entity = this._config?.entity;
    const current = this._status?.master.entity_id;
    return current ? entity === current : entity === MASTER;
  }

  private get _area(): StatusArea | undefined {
    return this._status?.areas.find((a) => a.entity_id === this._config?.entity);
  }

  /** The due time of an entry countdown this card shows that will ask for a
   * code to disarm, or undefined. What the backend publishes about the code
   * policy, read and nothing more: it opens the pad, it never skips a send. */
  private _entryWantsCode(): string | undefined {
    const status = this._status;
    if (!status || !this._codeUsed) return undefined;
    const area = this._area;
    const areas = this._isMaster || !area ? status.areas : [area];
    return areas.find(
      (a) =>
        a.timer?.kind === "entry" &&
        (a.require_code?.disarm ?? status.security.require_code?.disarm),
    )?.timer?.due;
  }

  /** Is this the command the pad is waiting to send? Its button steps aside
   * while it waits: pressing it would send the same command again without
   * the code — refused again — and take the digits with it. A forced arm
   * hides the plain one it came from as well. */
  private _isPending(command: Record<string, unknown>): boolean {
    const pending = this._pending;
    if (!pending || pending.type !== command.type) return false;
    const plain = (c: Record<string, unknown>) => JSON.stringify({ ...c, force: undefined });
    return plain(pending) === plain(command);
  }

  /** A layout button's class. While the pad waits for a code, its confirm key
   * is the one primary action on the card, so nothing else is drawn as one. */
  private _primary(wanted: boolean): string {
    return wanted && !this._pending ? "primary" : "";
  }

  /** An area, a scenario, a zone or the whole house, as the card names it. */
  private _targetOf(command: Record<string, unknown>): string {
    const status = this._status;
    const s = this._strings;
    if (command.scenario_id) {
      return status?.scenarios.find((sc) => sc.id === command.scenario_id)?.name ?? "";
    }
    if (command.area_id) {
      return status?.areas.find((a) => a.id === command.area_id)?.name ?? "";
    }
    if (Array.isArray(command.area_ids)) {
      return command.area_ids
        .map((id) => status?.areas.find((a) => a.id === id)?.name ?? "")
        .join(", ");
    }
    if (command.zone_id) {
      return status?.zones.find((z) => z.id === command.zone_id)?.name ?? "";
    }
    if (command.pending_id) {
      return (
        status?.auto?.pending.find((p) => p.id === command.pending_id)?.rule_name ?? ""
      );
    }
    return t(s, "overview.master");
  }

  /** "Disarm", or — when the area is already disarmed and only its alarm
   * memory is left — what pressing it actually does. */
  private _disarmLabel(state: AreaState, memory: boolean): string {
    const s = this._strings;
    return state === "disarmed" && memory ? t(s, "card.clear_memory") : t(s, "card.disarm");
  }

  private async _run(command: Record<string, unknown>): Promise<void> {
    if (!this.hass) return;
    this._busy = true;
    this._feedback = undefined;
    // Whose digits these are. While the pad waits for a command they are
    // that command's, and any other button sends without them; with nothing
    // waiting, a banner's button never takes them (decision 114). The same
    // command pressed again from its own button is still the same command.
    const waiting = this._pending;
    const same = waiting !== undefined && JSON.stringify(waiting) === JSON.stringify(command);
    const banner = waiting
      ? !same
      : BANNER_COMMANDS.has(String(command.type));
    const typed = banner ? "" : this._code;
    if (!banner) this._forget();
    try {
      const result = await this.hass.callWS<CommandResult>({
        ...command,
        ...(typed ? { code: typed } : {}),
      });
      // Taken off the screen while the answer travelled: nothing to show,
      // and no pad to reopen on a view somebody has left.
      if (!this.isConnected) return;
      // A banner press leaves the pad's own command alone: the digits on it
      // were typed for that one, not for this.
      if (!banner) this._pending = undefined;
      // Done: the pad folds away, unless it still waits for another command.
      if (result.success && !this._pending) this._padOpen = false;
      if (result.success && result.low_battery_zones.length) {
        // Not a failure, and never shown as one — but the warning belongs on
        // every arming, on every channel, so it reaches whoever arms from
        // the wall tablet as well as the panel (§4.2, part 1 decision 2).
        this._feedback = {
          text: t(this._strings, "card.low_battery", {
            zones: result.low_battery_zones.map((z) => z.name).join(", "),
          }),
          warning: true,
        };
      }
      if (
        !result.success &&
        result.reason === "nothing_to_cancel" &&
        command.type === "foyer/auto/cancel"
      ) {
        // Somebody else stopped it, or it has already run. The banner is
        // gone, which is the answer; a red line under it would only ask the
        // reader to work out which of the two they are looking at.
        return;
      }
      if (!result.success) {
        // A code was wanted, or the one typed was wrong: open the pad, leave
        // it open, and keep the command so the pad's confirm key can repeat
        // it. The card never decides that a code is needed — the backend did.
        if (WANTS_CODE.has(result.reason ?? "")) {
          // The pad now waits for this command, so digits typed for another
          // one must not confirm it: they are cleared first, and the pad
          // says they were.
          if (banner) {
            this._retype = Boolean(this._code);
            this._code = "";
          }
          this._padOpen = true;
          this._pending = command;
          this._touch();
          // "A code is required" is what the pad now says, naming the
          // action and its target; a red line under the buttons would only
          // repeat it less precisely. A wrong code is said inside the pad.
          if (result.reason === "code_required") return;
          this._feedback = {
            text: t(this._strings, `reason.${result.reason}`),
            pad: true,
            reason: result.reason ?? undefined,
          };
          return;
        }
        if (result.reason === "locked_out") {
          // Whatever was said before belongs to a code that no longer
          // matters. The pad opens on the lockout and says until when.
          this._code = "";
          this._padOpen = true;
          this._feedback = {
            text: t(this._strings, "reason.locked_out"),
            pad: true,
            reason: "locked_out",
          };
          return;
        }
        this._feedback = {
          text: t(this._strings, `reason.${result.reason ?? "unknown"}`, {
            zones: result.blocking_zones.map((z) => z.name).join(", "),
          }),
          // Never for a command that is already forced, and never for one
          // forcing cannot help: forced arming is explicit, twice over.
          retry:
            command.type === "foyer/arm" &&
            !command.force &&
            FORCEABLE.has(result.reason ?? "")
              ? { ...command, force: true }
              : undefined,
        };
      }
    } catch {
      // What Home Assistant says when a command does not arrive — a
      // connection dropped, Foyer reloading — is English and technical; the
      // card says, in the reader's language, that nothing happened.
      this._feedback = { text: t(this._strings, "card.not_sent") };
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const s = this._strings;
    if (!s || !this.hass) return nothing;
    void this._tick;
    const entityId = this._config?.entity;
    if (!entityId) return this._message(t(s, "card.no_entity"));
    if (!this.hass.states[entityId]) {
      return this._message(t(s, "card.entity_missing", { entity: entityId }));
    }
    if (this._layout === "badge") return this._renderBadge(s);
    if (this._layout === "compact") return this._renderCompact(s);
    if (this._layout === "keypad") return this._renderKeypadLayout(s);
    return this._isMaster ? this._renderMaster(s) : this._renderArea(s);
  }

  // --- badge: the state, and nothing that can be pressed (§15.3) -------------------

  /** Colour-coded state only, for embedding in an existing dashboard.
   *
   * It has nothing to press and still shows the walk test (§11.3), because
   * the banner is required on *every* layout: a badge reading "armed" while
   * every response was inhibited would be the most misleading thing on the
   * dashboard.
   *
   * It decides nothing and offers nothing to press, which is the point: a
   * badge sits among the lights and the thermostat, where a stray tap must
   * never disarm a house. Tapping it opens the entity's own dialog, as every
   * other badge on that dashboard does.
   *
   * What it does still show is the two things that are dangerous to miss at a
   * glance: a countdown that is running, and an alarm in memory. A badge
   * reading "disarmed" while the siren had sounded an hour ago would be worse
   * than no badge at all — and, for the same reason, a technical alarm or an
   * alarm nobody has acknowledged yet, each as a chip of its own.
   */
  private _renderBadge(s: Strings) {
    const status = this._status;
    if (!status) return this._message(t(s, "common.loading"));
    const area = this._area;
    const master = this._isMaster || !area;
    const state = master ? status.master.state : area!.state;
    const memory = master ? status.areas.some((a) => a.memory) : area!.memory;
    const active = status.scenarios.find((sc) => sc.id === status.active_scenario_id);
    const name = master ? (active?.name ?? t(s, "overview.master")) : area!.name;
    const counting = master
      ? status.areas.find((a) => a.timer && a.timer.kind !== "siren")
      : area;
    const auto = this._pendingAuto;
    const timer = counting?.timer;
    const label =
      timer && timer.kind !== "siren"
        ? t(s, `timer.${timer.kind}`, {
            seconds: Math.max(
              0,
              Math.round((Date.parse(timer.due) - (Date.now() + this._offset)) / 1000),
            ),
          })
        : t(s, `state.${state}`);
    return html`
      <div
        class="badge"
        role="button"
        tabindex="0"
        title=${`${name} — ${t(s, `state.${state}`)}`}
        @click=${this._openMore}
        @keydown=${(e: KeyboardEvent) => {
          if (e.key !== "Enter" && e.key !== " ") return;
          // Space would scroll the page as well as open the dialog.
          e.preventDefault();
          this._openMore();
        }}
      >
        <span class="badge-name">${name}</span>
        <span class="state ${state}">${label}</span>
        ${memory
          ? html`<span class="state memory">${t(s, "overview.memory")}</span>`
          : nothing}
        ${status.technical?.length
          ? html`<span class="state triggered">${t(s, "card.technical_badge")}</span>`
          : nothing}
        ${status.incident && !status.incident.acknowledged
          ? html`<span class="state triggered">${t(s, "card.incident_badge")}</span>`
          : nothing}
        ${status.walk_test
          ? html`<span class="state walk-chip" title=${t(s, "walk.badge_title")}
              >${t(s, "walk.badge")}</span
            >`
          : nothing}
        ${auto
          ? html`<span
              class="state auto-chip"
              title=${t(s, `rules.counting_${auto.action}`, {
                rule: auto.rule_name,
                scenario:
                  status.scenarios.find((sc) => sc.id === auto.scenario_id)?.name ?? "",
                seconds: secondsUntil(auto.due, this._offset),
              })}
              >${t(s, `card.auto_badge_${auto.action}`, {
                seconds: secondsUntil(auto.due, this._offset),
              })}</span
            >`
          : nothing}
      </div>
    `;
  }

  /** The entity's own dialog, the way every badge on a dashboard behaves. */
  private _openMore(): void {
    const entityId = this._config?.entity;
    if (!entityId) return;
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        detail: { entityId },
        bubbles: true,
        composed: true,
      }),
    );
  }

  // --- compact: state, one action, and the scenario (§15.3) ------------------------

  private _renderCompact(s: Strings) {
    const status = this._status;
    if (!status) return this._message(t(s, "common.loading"));
    const area = this._area;
    const master = this._isMaster || !area;
    const state = master ? status.master.state : area!.state;
    const memory = master ? status.areas.some((a) => a.memory) : area!.memory;
    const active = status.scenarios.find((sc) => sc.id === status.active_scenario_id);
    const name = master ? (active?.name ?? t(s, "overview.master")) : area!.name;
    const armed = master
      ? status.areas.some((a) => a.state !== "disarmed" || a.memory)
      : area!.state !== "disarmed" || area!.memory;
    const countdown = master
      ? status.areas.find((a) => a.timer && a.timer.kind !== "siren")
      : area;
    const arm = { type: "foyer/arm", area_id: area?.id };
    const disarm = master
      ? { type: "foyer/disarm" }
      : { type: "foyer/disarm", area_ids: [area!.id] };
    // The select keeps showing the scenario the pad is waiting to arm: were
    // it to snap back to the active one, the person typing the code would
    // be left wondering what the code is for.
    const pending =
      this._pending?.type === "foyer/arm" ? String(this._pending.scenario_id ?? "") : "";
    const selected = pending || active?.id;
    return html`
      <ha-card>
        <div class="content compact">
          ${this._renderAlerts(s)} ${this._head(name, state, memory)}
          ${countdown ? this._countdown(s, countdown) : nothing}
          ${this._renderInlinePad(s)}
          <div class="buttons">
            ${master && this._alarmRunning
              ? nothing
              : master
              ? html`<select
                  ?disabled=${this._busy}
                  aria-label=${t(s, "card.scenario")}
                  @change=${(e: Event) => {
                    const id = (e.target as HTMLSelectElement).value;
                    if (id) void this._run({ type: "foyer/arm", scenario_id: id });
                  }}
                >
                  <option value="" .selected=${live(!selected)}>
                    ${t(s, "card.pick_scenario")}
                  </option>
                  ${status.scenarios.map(
                    (sc) => html`<option .value=${sc.id} .selected=${live(sc.id === selected)}>
                      ${sc.name}
                    </option>`,
                  )}
                </select>`
              : area!.state === "disarmed" && !this._isPending(arm)
                ? html`<button
                    class=${this._primary(true)}
                    ?disabled=${this._busy}
                    @click=${() => this._run(arm)}
                  >
                    ${t(s, "card.arm")}
                  </button>`
                : nothing}
            ${armed && !this._isPending(disarm)
              ? html`<button
                  class=${this._primary(state === "entry" || state === "triggered")}
                  ?disabled=${this._busy}
                  @click=${() => this._run(disarm)}
                >
                  ${this._disarmLabel(state, memory)}
                </button>`
              : nothing}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
  }

  private _renderArea(s: Strings) {
    const area = this._area;
    if (!area) return this._message(t(s, "common.loading"));
    const canDisarm = area.state !== "disarmed" || area.memory;
    const arm = { type: "foyer/arm", area_id: area.id };
    const disarm = { type: "foyer/disarm", area_ids: [area.id] };
    return html`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(s)} ${this._head(area.name, area.state, area.memory)}
          ${this._countdown(s, area)} ${this._renderBlocking(s, area)}
          ${this._renderInlinePad(s)}
          <div class="buttons">
            ${area.state === "disarmed" && !this._isPending(arm)
              ? html`<button
                  class=${this._primary(true)}
                  ?disabled=${this._busy}
                  @click=${() => this._run(arm)}
                >
                  ${t(s, "card.arm")}
                </button>`
              : nothing}
            ${canDisarm && !this._isPending(disarm)
              ? html`<button
                  class=${this._primary(area.state === "entry" || area.state === "triggered")}
                  ?disabled=${this._busy}
                  @click=${() => this._run(disarm)}
                >
                  ${this._disarmLabel(area.state, area.memory)}
                </button>`
              : nothing}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
  }

  /** The zones that stop this area arming, each with a way out (§5.4, §16).
   *
   * Excluding a zone from the card is the same command the panel sends; the
   * engine decides whether it may be excluded at all (INV-2).
   */
  private _renderBlocking(s: Strings, area: StatusArea) {
    if (area.state !== "disarmed" || area.ready) return nothing;
    const zones = this._status?.zones ?? [];
    const blocking = [...area.blocking.fault, ...area.blocking.open]
      .map((id) => zones.find((z) => z.id === id))
      .filter((zone): zone is NonNullable<typeof zone> => Boolean(zone));
    if (!blocking.length) return nothing;
    return html`
      <div class="blocking">
        <div class="blocking-hd">${t(s, "card.not_ready")}</div>
        ${blocking.map(
          (zone) => html`<div class="row">
            <span>${zone.name}</span>
            ${zone.bypassable && !zone.bypassed
              ? html`<button
                  class="link"
                  ?disabled=${this._busy}
                  @click=${() =>
                    this._run({ type: "foyer/bypass", zone_id: zone.id, bypass: true })}
                >
                  ${t(s, "zones.bypass")}
                </button>`
              : nothing}
          </div>`,
        )}
      </div>
    `;
  }

  private _renderMaster(s: Strings) {
    const status = this._status;
    if (!status) return this._message(t(s, "common.loading"));
    const memory = status.areas.some((a) => a.memory);
    const active = status.scenarios.find((sc) => sc.id === status.active_scenario_id);
    const anyArmed = status.areas.some((a) => a.state !== "disarmed" || a.memory);
    const alarm = this._alarmRunning;
    const disarm = { type: "foyer/disarm" };
    return html`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(s)}
          ${this._head(active?.name ?? t(s, "overview.master"), status.master.state, memory)}
          <div class="areas">
            ${status.areas.map(
              (area) => html`<div class="row">
                <span class="area-name">${area.name}</span>
                <span class="state ${area.state}">${t(s, `state.${area.state}`)}</span>
                ${area.memory
                  ? html`<span class="state memory">${t(s, "overview.memory")}</span>`
                  : nothing}
                ${this._countdown(s, area)}
              </div>`,
            )}
          </div>
          ${this._renderNotReady(s)} ${this._renderInlinePad(s)}
          <div class="buttons">
            ${alarm ? nothing : this._scenarioButtons(s, status.active_scenario_id)}
            ${anyArmed && !this._isPending(disarm)
              ? html`<button
                  class=${this._primary(alarm)}
                  ?disabled=${this._busy}
                  @click=${() => this._run(disarm)}
                >
                  ${this._disarmLabel(status.master.state, memory)}
                </button>`
              : nothing}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
  }

  /** An entry countdown or an alarm, anywhere in the house. The scenario
   * buttons step aside for it: the one thing to do then is disarm, and a row
   * of "Arm …" buttons beside it is a row of wrong answers. */
  /** An entry delay or an alarm running where this card looks: the whole
   * house for the master, its own area otherwise — an alarm in the garage
   * must not take the hall keypad's buttons away. */
  private get _alarmRunning(): boolean {
    const running = (a: StatusArea) => a.state === "entry" || a.state === "triggered";
    const area = this._area;
    if (area && !this._isMaster) return running(area);
    return Boolean(this._status?.areas.some(running));
  }

  /** One button per scenario, each saying that it arms — a bare "Away"
   * reads as a status, not an action. The one the pad waits for steps
   * aside, as every pending command's button does. */
  private _scenarioButtons(s: Strings, activeId?: string | null) {
    return (this._status?.scenarios ?? []).map((sc) => {
      const arm = { type: "foyer/arm", scenario_id: sc.id };
      if (this._isPending(arm)) return nothing;
      return html`<button
        class=${this._primary(sc.id === activeId)}
        ?disabled=${this._busy}
        @click=${() => this._run(arm)}
      >
        ${t(s, "card.arm_scenario", { scenario: sc.name })}
      </button>`;
    });
  }

  /** Every zone that would stop some area arming, with a way out (§15.3).
   *
   * On the master's card, because that is the card somebody looks at before
   * leaving the house — and "it would not arm and did not say why" is the
   * complaint this list exists to prevent.
   */
  private _renderNotReady(s: Strings) {
    const status = this._status;
    if (!status) return nothing;
    const blocking = new Map<string, string[]>();
    for (const area of status.areas) {
      if (area.state !== "disarmed" || area.ready) continue;
      for (const id of [...area.blocking.fault, ...area.blocking.open]) {
        blocking.set(id, [...(blocking.get(id) ?? []), area.name]);
      }
    }
    if (!blocking.size) return nothing;
    return html`
      <div class="blocking">
        <div class="blocking-hd">${t(s, "card.not_ready")}</div>
        ${[...blocking.entries()].map(([id, areas]) => {
          const zone = status.zones.find((z) => z.id === id);
          if (!zone) return nothing;
          return html`<div class="row">
            <span>${t(s, "card.zone_in", { zone: zone.name, areas: areas.join(", ") })}</span>
            ${zone.bypassable && !zone.bypassed
              ? html`<button
                  class="link"
                  ?disabled=${this._busy}
                  @click=${() =>
                    this._run({ type: "foyer/bypass", zone_id: zone.id, bypass: true })}
                >
                  ${t(s, "zones.bypass")}
                </button>`
              : nothing}
          </div>`;
        })}
      </div>
    `;
  }

  // The technical alarm and the open incident show on every card, whatever
  // area it shows (§5.5): each with its own acknowledgement, never merged.
  /** The walk-test banner of §11.3, on every layout that has room for one.
   *
   * "A permanent, unmissable banner in the panel and on every card while
   * active" is not a nicety: a real intrusion during a walk test produces
   * nothing at all, by construction, and this is one of the three things
   * standing between that fact and a household that has forgotten. So it is
   * rendered before anything else on the card, it says when the test ends,
   * and it says what is still live — because "have I just switched the
   * smoke detector off?" is the first question, and the answer is no.
   */
  private _walkBanner(s: Strings) {
    const walk = this._status?.walk_test;
    if (!walk) return nothing;
    const left = secondsUntil(walk.deadline, this._offset);
    return html`
      <div class="alert walk" role="alert">
        <span>
          <strong>${t(s, "walk.banner_title")}</strong>
          ${t(s, "walk.card_banner", { time: mmss(left) })}
        </span>
        <button
          ?disabled=${this._busy}
          @click=${() => this._run({ type: "foyer/walk_test", enable: false })}
        >
          ${t(s, "walk.end")}
        </button>
      </div>
    `;
  }

  /** The automatic rule that is counting down, or undefined (§9.4).
   *
   * The earliest of them: two rules can be counting at once and the card has
   * room for one line, so it shows the one that is about to happen. The
   * button cancels **that** countdown by id, never "whatever is running",
   * because the next one is a different decision.
   *
   * It is not filtered by the entity this card is bound to. A rule arms a
   * scenario, which is several areas, and a card on the hall panel that
   * stayed silent while the house was about to arm itself would be the most
   * misleading thing on the wall — the same reasoning that puts the walk
   * test banner on every layout.
   */
  private get _pendingAuto(): PendingRuleAction | undefined {
    const pending = this._status?.auto?.pending ?? [];
    return [...pending].sort((a, b) => a.due.localeCompare(b.due))[0];
  }

  /** "The house will arm in two minutes", with the Cancel button (§9.4).
   *
   * The card transmits and never decides: cancelling is a command the engine
   * resolves against the code policy like any other, so an installation that
   * asks for a code here gets the pad, exactly as it does for a disarm
   * (INV-2).
   */
  private _autoBanner(s: Strings) {
    const pending = this._pendingAuto;
    if (!pending) return nothing;
    const scenario = this._status?.scenarios.find((sc) => sc.id === pending.scenario_id);
    const left = secondsUntil(pending.due, this._offset);
    return html`
      <div class="alert auto" role="alert">
        <span>
          ${t(s, `rules.counting_${pending.action}`, {
            rule: pending.rule_name,
            scenario: scenario?.name ?? "",
            seconds: left,
          })}
          ${pending.suspension_name
            ? html`<em>${t(s, "rules.because", { name: pending.suspension_name })}</em>`
            : nothing}
        </span>
        <button
          ?disabled=${this._busy}
          @click=${() =>
            this._run({ type: "foyer/auto/cancel", pending_id: pending.id })}
        >
          ${t(s, "rules.cancel_now")}
        </button>
      </div>
    `;
  }

  private _renderAlerts(s: Strings) {
    const status = this._status;
    if (!status) return nothing;
    const names = new Map(status.zones.map((z) => [z.id, z.name]));
    const technical = status.technical ?? [];
    const incident = status.incident;
    return html`
      ${this._walkBanner(s)} ${this._autoBanner(s)}
      ${technical.length
        ? html`<div class="alert technical" role="alert">
            <span>${t(s, "card.technical", { zones: technical.map((a) => a.name).join(", ") })}</span>
            ${technical.some((a) => !a.acknowledged)
              ? html`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/acknowledge", target: "technical" })}
                >
                  ${t(s, "common.acknowledge")}
                </button>`
              : nothing}
          </div>`
        : nothing}
      ${incident
        ? html`<div class="alert incident" role="alert">
            <span>
              ${t(s, "card.incident", {
                zones: incident.zone_ids.map((z) => names.get(z) ?? z).join(", "),
              })}
            </span>
            ${incident.acknowledged
              ? nothing
              : html`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/acknowledge", target: "incident" })}
                >
                  ${t(s, "common.acknowledge")}
                </button>`}
          </div>`
        : nothing}
      ${status.security && !status.security.enforced
        ? html`<div class="alert inert" role="note">
            ${t(s, "overview.no_codes_warning")}
          </div>`
        : nothing}
    `;
  }

  /** The name and the state — and, beside "Armed", the walk-test chip: the
   * banner above can scroll away, and "Armed" alone next to a house that
   * answers nothing is the reading §11.3 exists to prevent. */
  private _head(name: string, state: AreaState, memory: boolean) {
    const s = this._strings;
    return html`
      <div class="head">
        <div class="name">${name}</div>
        <span class="state ${state}">${t(s, `state.${state}`)}</span>
        ${memory ? html`<span class="state memory">${t(s, "overview.memory")}</span>` : nothing}
        ${this._status?.walk_test
          ? html`<span class="state walk-chip" title=${t(s, "walk.badge_title")}
              >${t(s, "walk.badge")}</span
            >`
          : nothing}
      </div>
    `;
  }

  private _countdown(s: Strings, area: StatusArea, named = false) {
    if (!area.timer || area.timer.kind === "siren") return nothing;
    const seconds = Math.max(
      0,
      Math.round((Date.parse(area.timer.due) - (Date.now() + this._offset)) / 1000),
    );
    const text = t(s, `timer.${area.timer.kind}`, { seconds });
    // The entry countdown is set large and in the alarm's colour: it is the
    // time left before the siren, and the one line on the card that says so.
    return html`<div class="countdown ${area.timer.kind}">
      ${named ? t(s, "card.area_countdown", { area: area.name, countdown: text }) : text}
    </div>`;
  }

  // --- the keypad (§15.3) ---------------------------------------------------------

  /** What the pad's confirm key will do, in the words the card already uses
   * for that action. A key labelled "OK" leaves the one question a keypad
   * must answer — what am I about to do — to the user's memory. */
  private _pendingLabel(s: Strings): string {
    const pending = this._pending;
    if (!pending) return t(s, "card.code_confirm");
    const target = this._targetOf(pending);
    switch (pending.type) {
      case "foyer/disarm":
        return t(s, "card.confirm_disarm", { target });
      case "foyer/bypass":
        return t(s, "card.confirm_bypass", { target });
      case "foyer/arm":
        return t(s, pending.force ? "card.confirm_force" : "card.confirm_arm", { target });
      // The banners' commands, in the words of the banner button pressed.
      case "foyer/walk_test":
        return t(s, "walk.end");
      case "foyer/auto/cancel":
        return t(s, "rules.cancel_now");
      case "foyer/acknowledge":
        return t(s, "common.acknowledge");
      default:
        return t(s, "card.code_confirm");
    }
  }

  /** What the code being typed is for, above the digits: "Code to arm
   * Away". The refusal that opened the pad said only that a code is needed,
   * and on a wall tablet it landed below the fold. */
  private _pendingCaption(s: Strings): string | undefined {
    const pending = this._pending;
    if (!pending) return undefined;
    const target = this._targetOf(pending);
    switch (pending.type) {
      case "foyer/disarm":
        return t(s, "card.code_for_disarm", { target });
      case "foyer/bypass":
        return t(s, "card.code_for_bypass", { target });
      case "foyer/arm":
        return t(s, pending.force ? "card.code_for_force" : "card.code_for_arm", { target });
      case "foyer/walk_test":
        return t(s, "card.code_for_walk");
      case "foyer/auto/cancel":
        return t(s, "card.code_for_cancel", { target });
      case "foyer/acknowledge":
        return t(
          s,
          pending.target === "technical" ? "card.code_for_ack_technical" : "card.code_for_ack_incident",
        );
      default:
        return undefined;
    }
  }

  /** The pad: a display, ten digits, clear, and — once something is waiting
   * for a code — the key that sends it. The action buttons stay with the
   * layout around it, because what is armable differs per card. */
  private _renderPad(s: Strings) {
    const digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];
    const locked = this._lockedUntil;
    const caption = this._pendingCaption(s);
    // A refusal about the code, said here. A lockout already running is
    // said by the line with its end time instead, which is the useful half.
    const feedback =
      this._feedback?.pad && !(locked && this._feedback.reason === "locked_out")
        ? this._feedback
        : undefined;
    return html`
      <div class="pad" tabindex="0" @keydown=${(e: KeyboardEvent) => this._padKey(e)}>
        ${caption ? html`<div class="pad-for">${caption}</div>` : nothing}
        ${this._retype
          ? html`<div class="pad-note" role="status">${t(s, "card.code_retype")}</div>`
          : nothing}
        ${locked
          ? html`<div class="locked" role="status">
              ${t(s, "card.locked_until", {
                time: locked.toLocaleTimeString(
                  this.hass?.language,
                  inHouseZone(this.hass, { hour: "2-digit", minute: "2-digit" }),
                ),
              })}
            </div>`
          : nothing}
        <div class="display" aria-live="polite" aria-label=${t(s, "card.code_entered")}>
          ${this._code
            ? "•".repeat(this._code.length)
            : html`<span class="placeholder"
                >${t(s, "card.code_hint", { n: this._codeLength })}</span
              >`}
        </div>
        ${feedback ? html`<div class="pad-error" role="alert">${feedback.text}</div>` : nothing}
        <div class="keys">
          ${digits.map(
            (digit) => html`<button
              class="key"
              ?disabled=${this._busy}
              @click=${() => this._press(digit)}
            >
              ${digit}
            </button>`,
          )}
          <button
            class="key word"
            ?disabled=${this._busy || !this._code}
            @click=${() => {
              // The digits only: what they are for stays, so correcting a
              // mistyped one does not drop the command waiting for them.
              this._code = "";
              this._touch();
            }}
          >
            ${t(s, "card.code_clear")}
          </button>
          <button class="key" ?disabled=${this._busy} @click=${() => this._press("0")}>
            0
          </button>
        </div>
        ${this._pending
          ? html`<button
              class="key word confirm"
              ?disabled=${this._busy || !this._code}
              @click=${() => this._run(this._pending!)}
            >
              ${this._pendingLabel(s)}
            </button>`
          : nothing}
      </div>
    `;
  }

  /** When this account may try a code again, while a lockout runs (§8.4).
   * The pad still takes digits — the lockout is the backend's to enforce,
   * and it ends by itself — but it says until when, rather than letting
   * somebody type into a refusal. */
  private get _lockedUntil(): Date | undefined {
    const until = this._status?.security.locked_until;
    if (!until) return undefined;
    const at = new Date(until);
    return at.getTime() > Date.now() + this._offset ? at : undefined;
  }

  /** Layout `keypad`: the wall tablet. State, pad, and what can be done. */
  private _renderKeypadLayout(s: Strings) {
    const status = this._status;
    if (!status) return this._message(t(s, "common.loading"));
    const area = this._area;
    const state = this._isMaster ? status.master.state : (area?.state ?? "disarmed");
    const memory = this._isMaster
      ? status.areas.some((a) => a.memory)
      : Boolean(area?.memory);
    const armed = state !== "disarmed" || memory;
    // Arm is offered over alarm memory, as every other layout offers it: an
    // accepted arming clears the memory without acknowledging anything
    // (§5.2), where "Clear alarm memory" is a disarm, and a disarm of an area
    // the incident touched is its acknowledgement (§5.6).
    const canArm = state === "disarmed";
    const arm = { type: "foyer/arm", area_id: area?.id };
    const disarm = {
      type: "foyer/disarm",
      ...(this._isMaster || !area ? {} : { area_ids: [area.id] }),
    };
    // The scenario that is running, named — as the `full` layout names it.
    // A wall tablet is the one surface where somebody stands and asks "what
    // is the house doing?", and "Whole house, armed" does not answer it when
    // the difference between two scenarios is whether the upstairs is armed.
    const active = status.scenarios.find((sc) => sc.id === status.active_scenario_id);
    return html`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(s)}
          ${this._head(
            this._isMaster
              ? (active?.name ?? t(s, "overview.master"))
              : (area?.name ?? ""),
            state,
            memory,
          )}
          ${this._isMaster
            ? status.areas
                .filter((a) => a.timer && a.timer.kind !== "siren")
                .map((a) => this._countdown(s, a, true))
            : area
              ? this._countdown(s, area)
              : nothing}
          ${this._renderPad(s)}
          <div class="buttons">
            ${!canArm || this._alarmRunning
              ? nothing
              : this._isMaster
                ? // The master arms a scenario, and with none configured
                  // there is nothing it could send (third review).
                  status.scenarios.length
                  ? this._scenarioButtons(s)
                  : nothing
                : this._isPending(arm)
                  ? nothing
                  : html`<button ?disabled=${this._busy} @click=${() => this._run(arm)}>
                      ${t(s, "card.arm")}
                    </button>`}
            ${armed && !this._isPending(disarm)
              ? html`<button
                  class=${this._primary(true)}
                  ?disabled=${this._busy}
                  @click=${() => this._run(disarm)}
                >
                  ${this._disarmLabel(state, memory)}
                </button>`
              : nothing}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
  }

  /** The pad inside layout `full`, folded away until it is worth opening. */
  private _renderInlinePad(s: Strings) {
    // A command waiting for a code shows the pad whatever the card thought
    // of codes a moment ago: the backend has just asked for one.
    if (!this._codeUsed && !this._pending) return nothing;
    if (!this._padOpen && !this._pending) {
      return html`<button class="link pad-toggle" @click=${() => (this._padOpen = true)}>
        ${t(s, "card.code_show")}
      </button>`;
    }
    return html`${this._renderPad(s)}
      <button
        class="link pad-toggle"
        @click=${() => {
          this._padOpen = false;
          this._forget();
          if (this._feedback?.pad) this._feedback = undefined;
        }}
      >
        ${t(s, "card.code_hide")}
      </button>`;
  }

  /** Is the pad on screen, to say a refusal about the code inside it? */
  private get _padShown(): boolean {
    if (this._layout === "keypad") return true;
    if (this._layout === "badge") return false;
    return (this._codeUsed || Boolean(this._pending)) && (this._padOpen || Boolean(this._pending));
  }

  private _renderFeedback() {
    const feedback = this._feedback;
    if (!feedback || (feedback.pad && this._padShown)) return nothing;
    const s = this._strings;
    return html`<div class="feedback ${feedback.warning ? "warning" : ""}" role="alert">
      <div>${feedback.text}</div>
      ${feedback.retry
        ? html`<button
              class="force"
              ?disabled=${this._busy}
              @click=${() => this._run(feedback.retry!)}
            >
              ${t(s, "overview.force_arm")}
            </button>
            <span class="force-hint">${t(s, "overview.force_arm_hint")}</span>`
        : nothing}
    </div>`;
  }

  private _message(text: string) {
    return html`<ha-card><div class="content">${text}</div></ha-card>`;
  }

  static override styles = [
    stateStyles,
    css`
      .pad {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin: 4px 0;
      }
      .display {
        min-height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        letter-spacing: 8px;
        font-size: 22px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 4px 8px;
      }
      .display .placeholder {
        letter-spacing: normal;
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      /* minmax(0, 1fr), not 1fr: a column may never grow to fit a word, or
         "Cancella" at 220 px leaves 2, 5, 8 and 0 narrower than the rest. */
      .keys {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
      }
      .pad-for {
        font-size: 14px;
        font-weight: 500;
      }
      .pad-note {
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      .pad-error {
        color: var(--error-color);
        font-size: 14px;
      }
      .key {
        padding: 14px 0;
        font-size: 20px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        cursor: pointer;
      }
      .key:disabled {
        opacity: 0.5;
        cursor: default;
      }
      /* A word instead of a digit — "Clear" — so it is set smaller to fit
         the same square, and may break rather than widen its column. */
      .key.word {
        font-size: 13px;
        padding: 14px 2px;
        overflow-wrap: anywhere;
      }
      /* The confirm key names an action and a target — "Inserisci Fuori
         casa" — so it has a row of its own under the digits, and while it
         is there it is the one primary action on the card. */
      .key.confirm {
        width: 100%;
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
        font-size: 16px;
        font-weight: 500;
      }
      .pad-toggle {
        align-self: flex-start;
      }
      .pad:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: 4px;
        border-radius: 8px;
      }
      .locked {
        color: var(--error-color);
        font-size: 14px;
        font-weight: 500;
      }
      .content {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .head {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
      }
      .name {
        font-size: 18px;
        font-weight: 500;
        flex: 1;
      }
      .countdown {
        font-size: 15px;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
      }
      .countdown.entry {
        font-size: 21px;
        color: var(--error-color);
      }
      .blocking {
        margin: 8px 0 0;
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      .blocking .row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 2px 0;
      }
      .areas {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .areas .row {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }
      .area-name {
        /* Keep the name on one line: the state chip and the countdown wrap
           below it rather than squeezing it to two words a line. */
        flex: 1 0 auto;
        min-width: 40%;
        font-size: 14px;
      }
      .blocking-hd {
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 4px;
      }
      .content.compact {
        padding: 12px 16px;
        gap: 8px;
      }
      /* The badge draws no ha-card of its own: it is meant to sit inside a row
         of other badges, and a card around it would be a box in a row of
         chips. */
      .badge {
        display: inline-flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        max-width: 100%;
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid var(--divider-color);
        background: var(--ha-card-background, var(--card-background-color));
        cursor: pointer;
        box-sizing: border-box;
      }
      .badge:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
      }
      .badge-name {
        /* Never squeezed to nothing by the chips beside it: a badge that
           does not say which area it is says nothing. */
        flex: 1 0 auto;
        min-width: 4em;
        font-size: 13px;
        color: var(--secondary-text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .badge .state {
        background: none;
        padding: 0;
      }
      /* At 220 px the chips wrap onto a second line rather than being cut
         off at the badge's edge. */
      .badge .state.auto-chip,
      .badge .state.walk-chip {
        padding: 2px 8px;
        white-space: normal;
      }
      .content.compact .head .name {
        font-size: 16px;
      }
      select {
        font: inherit;
        font-size: 14px;
        padding: 9px 10px;
        border-radius: 8px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
      }
      /* A link, not a button: "Exclude" beside a zone, and the toggle that
         unfolds the pad — which, drawn as a full button, read as one more
         action. Tall enough to hit with a finger all the same. */
      .link {
        background: none;
        border: 0;
        padding: 0 4px;
        min-height: 36px;
        color: var(--primary-color);
        font: inherit;
        font-weight: 500;
        cursor: pointer;
      }
      .buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      button {
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 10px 16px;
        font: inherit;
        font-weight: 500;
        cursor: pointer;
        background: var(--card-background-color);
        color: var(--primary-text-color);
      }
      button.primary {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      button[disabled] {
        opacity: 0.5;
        cursor: default;
      }
      .feedback {
        color: var(--error-color);
        font-size: 14px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }
      .feedback.warning {
        color: var(--warning-color, #c77700);
      }
      .feedback .force {
        color: var(--error-color);
      }
      .force-hint {
        color: var(--secondary-text-color);
        font-size: 12.5px;
      }
      .alert.inert {
        border-left-color: var(--warning-color, #f57c00);
      }
      .alert {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 12px;
        padding: 8px 12px;
        border-radius: 8px;
        border-left: 4px solid var(--error-color, #d32f2f);
        background: var(--secondary-background-color);
        font-weight: 500;
      }
      .alert.incident {
        border-left-color: var(--warning-color, #c77700);
      }
      .alert span {
        flex: 1 1 12em;
      }
      .alert button {
        padding: 6px 12px;
      }
      /* The walk test is the loudest thing the card can say, because for as
         long as it runs the house answers nothing (§11.3). */
      .alert.walk {
        border-left-color: var(--warning-color, #c77700);
        background: color-mix(in srgb, var(--warning-color, #c77700) 14%, transparent);
      }
      /* A house about to arm itself is not an alarm and not a warning
         either: it is the two minutes in which somebody can still say no. */
      .alert.auto {
        border-left-color: var(--primary-color);
        background: color-mix(in srgb, var(--primary-color) 12%, transparent);
      }
      /* Tinted, with the theme's text colour on top: white on a light-blue
         or amber fill is too faint to read at a glance. */
      .state.auto-chip {
        background: color-mix(in srgb, var(--primary-color) 20%, transparent);
        color: var(--primary-text-color);
        font-weight: 600;
      }
      .state.walk-chip {
        background: color-mix(in srgb, var(--warning-color, #c77700) 28%, transparent);
        color: var(--primary-text-color);
        font-weight: 600;
      }
      .state.auto-chip::before {
        background: var(--primary-color);
      }
      .state.walk-chip::before {
        background: var(--warning-color, #c77700);
      }
    `,
  ];
}

if (!customElements.get("foyer-card")) customElements.define("foyer-card", FoyerCard);


// --- the visual editor (§15.3) ------------------------------------------------------
//
// Two things to choose: which panel the card shows, and how much of it. The
// editor writes the same YAML a person would write by hand, so switching
// between the two never loses anything.

class FoyerCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
    _strings: { state: true },
  };

  hass?: HomeAssistant;
  private _config: FoyerCardConfig = { type: "custom:foyer-card" };
  private _strings?: Strings;
  private _language?: string;

  setConfig(config: FoyerCardConfig): void {
    this._config = config;
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (!changed.has("hass") || !this.hass) return;
    if (this.hass.language !== this._language) {
      this._language = this.hass.language;
      loadStrings(this.hass)
        .then((strings) => (this._strings = strings))
        .catch(() => (this._language = undefined));
    }
  }

  private _emit(changes: Partial<FoyerCardConfig>): void {
    this._config = { ...this._config, ...changes };
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      }),
    );
  }

  override render() {
    const s = this._strings;
    if (!s || !this.hass) return nothing;
    // The whole house first: it is the card most people add first.
    const master = masterOf(this.hass);
    const panels = foyerPanels(this.hass).sort(
      (a, b) => Number(b === master || b === MASTER) - Number(a === master || a === MASTER),
    );
    const layout = this._config.layout ?? "full";
    // Nothing chosen yet: the first entry is what the select shows, so it is
    // what the configuration says — otherwise the editor looks set while the
    // card says "set an entity".
    if (!this._config.entity && panels.length) {
      queueMicrotask(() => this._emit({ entity: panels[0] }));
    }
    return html`
      <div class="editor">
        <label>
          <span>${t(s, "card.editor_entity")}</span>
          <select
            @change=${(e: Event) => this._emit({ entity: (e.target as HTMLSelectElement).value })}
          >
            ${panels.map(
              (id) => html`<option .value=${id} .selected=${live(id === this._config.entity)}>
                ${id === MASTER || id === master
                  ? t(s, "card.editor_master")
                  : String(this.hass!.states[id]?.attributes.friendly_name ?? id)}
              </option>`,
            )}
          </select>
        </label>
        <label>
          <span>${t(s, "card.editor_layout")}</span>
          <select
            @change=${(e: Event) =>
              this._emit({ layout: (e.target as HTMLSelectElement).value as Layout })}
          >
            ${(["full", "compact", "badge", "keypad"] as Layout[]).map(
              (option) => html`<option .value=${option} .selected=${live(option === layout)}>
                ${t(s, `card.layout_${option}`)}
              </option>`,
            )}
          </select>
          <span class="hint">${t(s, `card.layout_hint_${layout}`)}</span>
        </label>
        <p class="hint">${t(s, "card.editor_hint")}</p>
      </div>
    `;
  }

  static override styles = css`
    .editor {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 8px 0;
    }
    label {
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 13px;
      font-weight: 500;
    }
    select {
      font: inherit;
      font-size: 14px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color);
      color: var(--primary-text-color);
    }
    .hint {
      margin: 0;
      font-size: 12.5px;
      font-weight: 400;
      color: var(--secondary-text-color);
    }
  `;
}

if (!customElements.get("foyer-card-editor")) {
  customElements.define("foyer-card-editor", FoyerCardEditor);
}


// Listed in the dashboard's "add card" picker.
declare global {
  interface Window {
    customCards?: { type: string; name: string; description?: string; preview?: boolean }[];
  }
}
window.customCards = window.customCards ?? [];
if (!window.customCards.some((c) => c.type === "foyer-card")) {
  window.customCards.push({ type: "foyer-card", name: "Foyer Home Defender", preview: true });
}
