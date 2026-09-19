// Page 6 — Contacts (SPEC §7, §15.1). Escalation targets people, not
// services: Home Assistant already provides the transports, so what is
// configured here is who, in what order, and what counts as somebody having
// taken notice.
//
// Three things this page has to say out loud.
//
// A contact with no channel is refused, because a person in the book nobody
// can reach is a step in an escalation that silently reaches nobody — which
// is the failure the whole of §7 exists to prevent.
//
// The test button beside every channel really sends (§11.4). Phase 3 built
// the one beside an action and left this one to arrive here; it is the same
// call the real notification makes, so what is proved is the channel.
//
// And the DTMF webhook is a URL that stops an alarm. Home Assistant webhooks
// are not authenticated, so it does not exist until somebody switches it on,
// and the sentence saying why is next to the switch rather than in a document
// nobody opens (INV-6).
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type {
  ActionConfig,
  ContactChannelConfig,
  ContactConfig,
  ContactChannelKind,
  ProfileConfig,
  Problem,
} from "../../shared/types";
import { notifyTargets } from "../ha-targets";
import { testReason } from "./test";
import { problemText, type PanelContext } from "../context";

const EMPTY: ContactConfig = {
  name: "",
  channels: [],
  quiet_start: null,
  quiet_end: null,
  quiet_min_severity: "alarm",
  linked_user_id: null,
  enabled: true,
};

const NEW_CHANNEL: ContactChannelConfig = {
  kind: "push",
  service: "",
  target: "",
  data: {},
  actionable: false,
  enabled: true,
};

/** The four ways an acknowledgement arrives (§7.2), for the card that says so. */
const ACK_PATHS = ["push", "disarm", "dtmf", "service"] as const;

interface Step {
  profile: ProfileConfig;
  action: ActionConfig;
  index: number;
}

/** Every escalation step in the configuration, earliest first per profile.
 * A step lives on the profile that answers the alarm (§5.6), so this page
 * shows the policies rather than owning them: they are edited on page 5. */
function steps(profiles: ProfileConfig[]): Map<string, Step[]> {
  const out = new Map<string, Step[]>();
  for (const profile of profiles) {
    const found = profile.actions
      .filter((action) => action.enabled && action.escalation_offset !== null)
      .sort((a, b) => (a.escalation_offset ?? 0) - (b.escalation_offset ?? 0))
      .map((action, index) => ({ profile, action, index }));
    if (found.length) out.set(profile.id ?? profile.name, found);
  }
  return out;
}

function contactsOf(action: ActionConfig): { contact_id: string; channel_id: string | null }[] {
  const raw = (action.params as { contacts?: unknown }).contacts;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((entry) =>
      typeof entry === "string"
        ? { contact_id: entry, channel_id: null }
        : (entry as { contact_id: string; channel_id: string | null }),
    )
    .filter((entry) => entry && entry.contact_id);
}

class FoyerPageContacts extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _draft: { state: true },
    _problems: { state: true },
    _busy: { state: true },
    _tested: { state: true },
  };

  ctx?: PanelContext;
  private _draft?: ContactConfig;
  private _problems: Problem[] = [];
  private _busy = false;
  /** The result of the last channel test, by channel id: what §11.4 is for. */
  private _tested: Record<string, { ok: boolean; error?: string | null }> = {};

  private _edit(contact?: ContactConfig): void {
    this._draft = contact
      ? structuredClone(contact)
      : { ...structuredClone(EMPTY), channels: [structuredClone(NEW_CHANNEL)] };
    this._problems = [];
  }

  private _set<K extends keyof ContactConfig>(key: K, value: ContactConfig[K]): void {
    if (this._draft) this._draft = { ...this._draft, [key]: value };
  }

  private _setChannel(
    index: number,
    changes: Partial<ContactChannelConfig>,
  ): void {
    if (!this._draft) return;
    const channels = this._draft.channels.map((channel, i) =>
      i === index ? { ...channel, ...changes } : channel,
    );
    this._draft = { ...this._draft, channels };
  }

  private _move(index: number, by: number): void {
    if (!this._draft) return;
    const channels = [...this._draft.channels];
    const to = index + by;
    if (to < 0 || to >= channels.length) return;
    [channels[index], channels[to]] = [channels[to], channels[index]];
    this._draft = { ...this._draft, channels };
  }

  private _addChannel(): void {
    if (!this._draft) return;
    this._draft = {
      ...this._draft,
      channels: [...this._draft.channels, structuredClone(NEW_CHANNEL)],
    };
  }

  private _removeChannel(index: number): void {
    if (!this._draft) return;
    this._draft = {
      ...this._draft,
      channels: this._draft.channels.filter((_, i) => i !== index),
    };
  }

  private async _save(): Promise<void> {
    if (!this.ctx || !this._draft) return;
    this._busy = true;
    try {
      const result = await this.ctx.save("contact", this._draft);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  private async _delete(): Promise<void> {
    if (!this.ctx || !this._draft?.id) return;
    this._busy = true;
    try {
      const result = await this.ctx.remove("contact", this._draft.id);
      this._problems = result.problems;
      if (result.success) this._draft = undefined;
    } finally {
      this._busy = false;
    }
  }

  /** Really sends (§11.4): the same call the real notification makes. */
  private async _test(contact: ContactConfig, channel: ContactChannelConfig): Promise<void> {
    if (!this.ctx || !contact.id || !channel.id) return;
    this._busy = true;
    try {
      const result = await this.ctx.testAction({
        contact_id: contact.id,
        channel_id: channel.id,
      });
      this._tested = {
        ...this._tested,
        [channel.id]: {
          ok: result.success,
          error:
            result.error ?? testReason(this.ctx.strings, result.reason ?? null),
        },
      };
    } finally {
      this._busy = false;
    }
  }

  /** A notify *entity* carries a message and a title and nothing else: no
   * target, no transport data, no action button. The difference is not in
   * the name — `notify.mobile_app_luca` is a service and `notify.my_phone`
   * may be an entity — so it is read the way the backend reads it, from
   * whether Home Assistant has a state for it. Said where somebody is
   * ticking the box, rather than discovered when the button never arrives. */
  private _isEntity(service: string): boolean {
    return Boolean(service && this.ctx?.hass.states[service]);
  }

  private async _toggleWebhook(enabled: boolean): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    try {
      await this.ctx.setAckWebhook(enabled);
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx?.config) return nothing;
    const s = ctx.strings;
    const contacts = ctx.config.contacts ?? [];
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "contacts.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${t(s, "contacts.add")}
          </button>
        </div>
        ${contacts.length
          ? html`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${t(s, "field.name")}</th>
                    <th>${t(s, "contacts.channels_order")}</th>
                    <th>${t(s, "contacts.quiet_hours")}</th>
                    <th>${t(s, "field.linked_user_id")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${contacts.map((contact) => this._row(s, contact))}
                </tbody>
              </table>
            </div>`
          : html`<div class="empty">${t(s, "contacts.none")}</div>`}
        <div class="card-bd">
          <p class="note">${t(s, "contacts.orchestration")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(s, this._draft) : nothing}
      ${this._renderPolicies(s)} ${this._renderAcknowledgement(s)}
    `;
  }

  private _row(s: Strings, contact: ContactConfig) {
    const users = this.ctx?.config?.users ?? [];
    const owner = users.find((u) => u.id === contact.linked_user_id);
    return html`<tr
      class="clickable"
      aria-selected=${this._draft?.id === contact.id ? "true" : "false"}
      @click=${() => this._edit(contact)}
    >
      <td><strong>${contact.name}</strong></td>
      <td>
        <div class="channels">
          ${contact.channels.map(
            (channel, index) =>
              html`<span class="tag"
                >${index + 1}. ${t(s, `channel_kind.${channel.kind}`)} ·
                ${channel.service}</span
              >`,
          )}
        </div>
      </td>
      <td class="mono">
        ${contact.quiet_start
          ? `${contact.quiet_start}–${contact.quiet_end}`
          : t(s, "contacts.no_quiet_hours")}
      </td>
      <td>${owner?.name ?? "—"}</td>
    </tr>`;
  }

  private _renderEditor(s: Strings, draft: ContactConfig) {
    const ctx = this.ctx!;
    const users = ctx.config?.users ?? [];
    const services = notifyTargets(ctx.hass);
    const kinds: ContactChannelKind[] = ctx.meta?.contact_channel_kinds ?? [
      "push",
      "sms",
      "voice",
      "chat",
      "other",
    ];
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${draft.id ? draft.name : t(s, "contacts.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.name")}</span>
              <input
                .value=${draft.name}
                @input=${(e: Event) =>
                  this._set("name", (e.target as HTMLInputElement).value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.linked_user_id")}</span>
              <select
                @change=${(e: Event) =>
                  this._set(
                    "linked_user_id",
                    (e.target as HTMLSelectElement).value || null,
                  )}
              >
                <option value="" ?selected=${!draft.linked_user_id}>—</option>
                ${users.map(
                  (u) => html`<option
                    .value=${u.id ?? ""}
                    ?selected=${u.id === draft.linked_user_id}
                  >
                    ${u.name}
                  </option>`,
                )}
              </select>
              <span class="hint">${t(s, "contacts.linked_hint")}</span>
            </label>
          </div>

          <h3>${t(s, "contacts.channels")}</h3>
          <p class="note">${t(s, "contacts.channels_hint")}</p>
          ${draft.channels.map((channel, index) =>
            this._renderChannel(s, draft, channel, index, services, kinds),
          )}
          <button class="btn" @click=${() => this._addChannel()}>
            ${t(s, "contacts.add_channel")}
          </button>

          <h3>${t(s, "contacts.quiet_hours")}</h3>
          <p class="note">${t(s, "contacts.quiet_hint")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "field.quiet_start")}</span>
              <input
                type="time"
                .value=${draft.quiet_start ?? ""}
                @change=${(e: Event) =>
                  this._set("quiet_start", (e.target as HTMLInputElement).value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "field.quiet_end")}</span>
              <input
                type="time"
                .value=${draft.quiet_end ?? ""}
                @change=${(e: Event) =>
                  this._set("quiet_end", (e.target as HTMLInputElement).value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "contacts.quiet_min_severity")}</span>
              <select
                @change=${(e: Event) =>
                  this._set(
                    "quiet_min_severity",
                    (e.target as HTMLSelectElement)
                      .value as ContactConfig["quiet_min_severity"],
                  )}
              >
                ${(["info", "warning", "alarm"] as const).map(
                  (severity) => html`<option
                    .value=${severity}
                    ?selected=${severity === draft.quiet_min_severity}
                  >
                    ${t(s, `severity.${severity}`)}
                  </option>`,
                )}
              </select>
              <span class="hint">${t(s, "contacts.quiet_severity_hint")}</span>
            </label>
          </div>

          ${this._problems.map(
            (problem) =>
              html`<p class="problem">${problemText(s, problem)}</p>`,
          )}
        </div>
        <div class="card-ft">
          ${draft.id
            ? html`<button class="btn danger" ?disabled=${this._busy} @click=${() => this._delete()}>
                ${t(s, "common.delete")}
              </button>`
            : nothing}
          <button class="btn" @click=${() => (this._draft = undefined)}>
            ${t(s, "common.cancel")}
          </button>
          <button class="btn primary" ?disabled=${this._busy} @click=${() => this._save()}>
            ${t(s, "common.save")}
          </button>
        </div>
      </div>
    `;
  }

  private _renderChannel(
    s: Strings,
    draft: ContactConfig,
    channel: ContactChannelConfig,
    index: number,
    services: { id: string; name: string }[],
    kinds: ContactChannelKind[],
  ) {
    const tested = channel.id ? this._tested[channel.id] : undefined;
    // A service this installation cannot see right now — an integration
    // being reloaded, or one that failed to load after an update — is still
    // what this channel is configured to use. Dropping it from the list
    // would show the channel as unset and lose it on the next save, which is
    // a notification channel silently disappearing from an alarm.
    const options = services.some((target) => target.id === channel.service)
      ? services
      : [...services, { id: channel.service, name: channel.service }].filter(
          (target) => target.id,
        );
    return html`
      <div class="channel">
        <div class="channel-hd">
          <span class="rank">${index + 1}</span>
          <div class="channel-tools">
            <button class="btn sm" @click=${() => this._move(index, -1)}>↑</button>
            <button class="btn sm" @click=${() => this._move(index, 1)}>↓</button>
            <button class="btn sm danger" @click=${() => this._removeChannel(index)}>
              ${t(s, "common.delete")}
            </button>
          </div>
        </div>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${t(s, "field.kind")}</span>
            <select
              @change=${(e: Event) =>
                this._setChannel(index, {
                  kind: (e.target as HTMLSelectElement).value as ContactChannelKind,
                })}
            >
              ${kinds.map(
                (kind) => html`<option .value=${kind} ?selected=${kind === channel.kind}>
                  ${t(s, `channel_kind.${kind}`)}
                </option>`,
              )}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${t(s, "contacts.service")}</span>
            <select
              @change=${(e: Event) =>
                this._setChannel(index, {
                  service: (e.target as HTMLSelectElement).value,
                })}
            >
              <option value="" ?selected=${!channel.service}>—</option>
              ${options.map(
                (target) => html`<option
                  .value=${target.id}
                  ?selected=${target.id === channel.service}
                >
                  ${target.name}
                </option>`,
              )}
            </select>
            <span class="hint">${t(s, "contacts.service_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${t(s, "contacts.target")}</span>
            <input
              .value=${channel.target}
              @input=${(e: Event) =>
                this._setChannel(index, {
                  target: (e.target as HTMLInputElement).value,
                })}
            />
            <span class="hint">${t(s, "contacts.target_hint")}</span>
          </label>
          <label class="check">
            <input
              type="checkbox"
              .checked=${channel.actionable}
              @change=${(e: Event) =>
                this._setChannel(index, {
                  actionable: (e.target as HTMLInputElement).checked,
                })}
            />
            <span class="lbl">${t(s, "contacts.actionable")}</span>
            <span class="hint">
              ${t(
                s,
                this._isEntity(channel.service)
                  ? "contacts.actionable_entity"
                  : "contacts.actionable_hint",
              )}
            </span>
          </label>
        </div>
        <div class="channel-ft">
          <button
            class="btn sm"
            ?disabled=${this._busy || !draft.id || !channel.id}
            @click=${() => this._test(draft, channel)}
          >
            ${t(s, "contacts.test")}
          </button>
          ${draft.id && channel.id
            ? nothing
            : html`<span class="hint">${t(s, "contacts.test_after_save")}</span>`}
          ${tested
            ? html`<span class=${tested.ok ? "tag ok" : "tag bad"}>
                ${tested.ok ? t(s, "contacts.test_sent") : tested.error}
              </span>`
            : nothing}
        </div>
      </div>
    `;
  }

  /** The policies as they are: steps belong to the profile that answers the
   * alarm (§5.6), so this reads them and page 5 edits them. */
  private _renderPolicies(s: Strings) {
    const ctx = this.ctx!;
    const contacts = ctx.config?.contacts ?? [];
    const policies = steps(ctx.config?.profiles ?? []);
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "contacts.policies")}</h2>
          <button class="btn" @click=${() => ctx.navigate("profiles")}>
            ${t(s, "contacts.edit_on_profiles")}
          </button>
        </div>
        ${policies.size
          ? html`<div class="card-bd">
              ${[...policies.values()].map(
                (found) => html`
                  <h3>${found[0].profile.name}</h3>
                  ${found.map(
                    ({ action, index }) => html`
                      <div class="step">
                        <span class="mono at">+${action.escalation_offset}s</span>
                        <div>
                          <div class="who">
                            ${contactsOf(action)
                              .map((ref) => {
                                const contact = contacts.find(
                                  (c) => c.id === ref.contact_id,
                                );
                                const channel = contact?.channels.find(
                                  (c) => c.id === ref.channel_id,
                                );
                                return channel
                                  ? `${contact?.name} · ${t(s, `channel_kind.${channel.kind}`)}`
                                  : (contact?.name ??
                                      t(s, "problem.unknown_contact"));
                              })
                              .join(" · ") ||
                            String(
                              (action.params as { service?: string }).service ?? "",
                            )}
                          </div>
                          <div class="mono">
                            ${t(s, "contacts.step_number")} ${index} ·
                            ${t(s, `moment.${action.moments[0]}`)}
                          </div>
                        </div>
                      </div>
                    `,
                  )}
                `,
              )}
              <p class="note">${t(s, "contacts.exhausted")}</p>
            </div>`
          : html`<div class="empty">${t(s, "contacts.no_policies")}</div>`}
      </div>
    `;
  }

  private _renderAcknowledgement(s: Strings) {
    const ctx = this.ctx!;
    const webhookId = ctx.config?.settings.ack_webhook_id ?? null;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "contacts.acknowledgement")}</h2>
        </div>
        <div class="card-bd">
          <p class="note">${t(s, "contacts.ack_stops")}</p>
          ${ACK_PATHS.map(
            (path) => html`<div class="path">
              <div class="who">${t(s, `contacts.ack_${path}`)}</div>
              <div class="mono">${t(s, `contacts.ack_${path}_how`)}</div>
            </div>`,
          )}
          <h3>${t(s, "contacts.webhook")}</h3>
          <div class="banner warn">
            <strong>${t(s, "contacts.webhook_warning")}</strong>
            <span>${t(s, "contacts.webhook_warning_hint")}</span>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${webhookId !== null}
              ?disabled=${this._busy}
              @change=${(e: Event) =>
                this._toggleWebhook((e.target as HTMLInputElement).checked)}
            />
            <span class="lbl">${t(s, "contacts.webhook_enable")}</span>
          </label>
          ${webhookId
            ? html`<p class="sample">/api/webhook/${webhookId}</p>
                <p class="note">${t(s, "contacts.webhook_hint")}</p>`
            : nothing}
        </div>
      </div>
    `;
  }

  static override styles = [
    formStyles,
    stateStyles,
    css`
      /* One chip per channel, in priority order. Without the gap they run
         into each other and "…luca2. SMS" reads as one service. */
      .channels {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .channel {
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
      }
      .channel-hd {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
      }
      .channel-tools {
        display: flex;
        gap: 6px;
      }
      .channel-ft {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
      }
      .tag.ok {
        color: var(--success-color, #2e9e4f);
      }
      .tag.bad {
        color: var(--error-color, #d32f2f);
      }
      .rank {
        font-weight: 600;
        color: var(--secondary-text-color);
      }
      .step,
      .path {
        display: grid;
        grid-template-columns: 72px 1fr;
        gap: 14px;
        padding: 10px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      .path {
        grid-template-columns: 1fr;
        gap: 2px;
      }
      .at {
        color: var(--secondary-text-color);
      }
      .who {
        font-weight: 500;
      }
      .mono {
        font-family: var(--code-font-family, monospace);
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .sample {
        margin: 8px 0 0;
        padding: 10px 12px;
        border-radius: 8px;
        background: var(--secondary-background-color);
        font-family: var(--code-font-family, monospace);
        font-size: 12px;
        overflow-x: auto;
      }
      /* The sentence that has to stop somebody: a Home Assistant webhook is
         not authenticated, and this one stops an alarm (INV-6). */
      .banner {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 8px;
        background: var(--warning-color, #f0a835);
        color: #0d1014;
      }
    `,
  ];
}

customElements.define("foyer-page-contacts", FoyerPageContacts);
