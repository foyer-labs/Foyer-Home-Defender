// Page 10 — Log (SPEC §15.1, §10). Filters by date, area, zone, category,
// severity and outcome; export of exactly the rows the filters show.
//
// The rows are data: every event type, category and outcome is translated
// here, never written by the backend, so the log reads in the language of
// whoever is looking at it.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type { LogQuery, LogRow } from "../../shared/types";
import { download, type PanelContext } from "../context";

const PAGE_SIZE = 50;

class FoyerPageLog extends LitElement {
  static override properties = {
    ctx: { attribute: false },
    _rows: { state: true },
    _total: { state: true },
    _offset: { state: true },
    _filters: { state: true },
    _busy: { state: true },
    _error: { state: true },
    _open: { state: true },
    _confirmClear: { state: true },
  };

  ctx?: PanelContext;
  private _rows: LogRow[] = [];
  private _total = 0;
  private _offset = 0;
  private _filters: LogQuery = {};
  private _busy = false;
  private _error?: string;
  private _open?: number;
  private _confirmClear = false;
  private _loaded = false;

  override updated(): void {
    // The first load waits for the context, which arrives with the status.
    if (!this._loaded && this.ctx) {
      this._loaded = true;
      void this._load();
    }
  }

  private async _load(): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    this._error = undefined;
    try {
      const page = await this.ctx.queryLog({
        ...this._filters,
        limit: PAGE_SIZE,
        offset: this._offset,
      });
      this._rows = page.rows;
      this._total = page.total;
    } catch (err) {
      this._rows = [];
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  private _filter(changes: Partial<LogQuery>): void {
    this._filters = { ...this._filters, ...changes };
    this._offset = 0;
    void this._load();
  }

  private async _export(format: "csv" | "json"): Promise<void> {
    if (!this.ctx) return;
    this._busy = true;
    try {
      const result = await this.ctx.exportLog(this._filters, format);
      download(
        result.filename,
        result.content,
        format === "csv" ? "text/csv" : "application/json",
      );
      if (result.truncated) {
        this._error = t(this.ctx.strings, "log.truncated", {
          rows: result.rows,
          total: result.total,
        });
      }
    } catch (err) {
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  private async _clear(): Promise<void> {
    if (!this.ctx) return;
    this._confirmClear = false;
    this._busy = true;
    try {
      await this.ctx.clearLog();
      this._offset = 0;
      await this._load();
    } catch (err) {
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx) return nothing;
    const s = ctx.strings;
    return html`${this._renderFilters(s)} ${this._renderRows(s)}`;
  }

  // --- filters ---------------------------------------------------------------------

  /** The vocabulary of the log. It comes from the backend for an
   * administrator, who has read the configuration; everyone else sees this
   * page too, and for them it is taken from the translations, which carry the
   * same words and the same order. A filter list is not a secret. */
  private _vocabulary(s: Strings, key: string, fromMeta?: string[]): string[] {
    if (fromMeta?.length) return fromMeta;
    const block = (s as Record<string, unknown>)[key];
    return block && typeof block === "object" ? Object.keys(block) : [];
  }

  private _renderFilters(s: Strings) {
    const ctx = this.ctx!;
    const categories = this._vocabulary(s, "category", ctx.meta?.log_categories);
    const severities = this._vocabulary(s, "severity", ctx.meta?.log_severities);
    const outcomes = this._vocabulary(s, "outcome", ctx.meta?.outcomes);
    const selected = this._filters.categories ?? [];
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "log.filters")}</h2></div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "log.from")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.start ?? ""}
                @change=${(e: Event) =>
                  this._filter({ start: (e.target as HTMLInputElement).value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "log.to")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.end ?? ""}
                @change=${(e: Event) =>
                  this._filter({ end: (e.target as HTMLInputElement).value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${t(s, "log.area")}</span>
              <select
                @change=${(e: Event) =>
                  this._filter({ area_id: (e.target as HTMLSelectElement).value || null })}
              >
                <option value="">${t(s, "log.all")}</option>
                ${ctx.status.areas.map(
                  (area) =>
                    html`<option .value=${area.id} ?selected=${area.id === this._filters.area_id}>
                      ${area.name}
                    </option>`,
                )}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "log.zone")}</span>
              <select
                @change=${(e: Event) =>
                  this._filter({ zone_id: (e.target as HTMLSelectElement).value || null })}
              >
                <option value="">${t(s, "log.all")}</option>
                ${ctx.status.zones.map(
                  (zone) =>
                    html`<option .value=${zone.id} ?selected=${zone.id === this._filters.zone_id}>
                      ${zone.name}
                    </option>`,
                )}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "log.severity")}</span>
              <select
                @change=${(e: Event) =>
                  this._filter({ severity: (e.target as HTMLSelectElement).value || null })}
              >
                <option value="">${t(s, "log.all")}</option>
                ${severities.map(
                  (level) =>
                    html`<option .value=${level} ?selected=${level === this._filters.severity}>
                      ${t(s, `severity.${level}`)}
                    </option>`,
                )}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${t(s, "log.outcome")}</span>
              <select
                @change=${(e: Event) =>
                  this._filter({ outcome: (e.target as HTMLSelectElement).value || null })}
              >
                <option value="">${t(s, "log.all")}</option>
                ${outcomes.map(
                  (outcome) =>
                    html`<option .value=${outcome} ?selected=${outcome === this._filters.outcome}>
                      ${t(s, `outcome.${outcome}`)}
                    </option>`,
                )}
              </select>
            </label>
          </div>
          <fieldset>
            <legend>${t(s, "log.categories")}</legend>
            <div class="chips">
              ${categories.map(
                (category) => html`
                  <button
                    class="chip"
                    aria-pressed=${selected.includes(category) ? "true" : "false"}
                    @click=${() =>
                      this._filter({
                        categories: selected.includes(category)
                          ? selected.filter((c) => c !== category)
                          : [...selected, category],
                      })}
                  >
                    ${t(s, `category.${category}`)}
                  </button>
                `,
              )}
            </div>
            <p class="hint">${t(s, "log.categories_hint")}</p>
          </fieldset>
          ${this._filters.incident_id
            ? html`<p class="hint">
                ${t(s, "log.incident_filter", { id: this._filters.incident_id })}
                <button class="btn small" @click=${() => this._filter({ incident_id: null })}>
                  ${t(s, "log.clear_filter")}
                </button>
              </p>`
            : nothing}
        </div>
      </div>
    `;
  }

  // --- rows ------------------------------------------------------------------------

  private _renderRows(s: Strings) {
    const ctx = this.ctx!;
    const shown = this._rows.length;
    return html`
      <div class="card">
        <div class="card-hd">
          <h2>${t(s, "log.events")}</h2>
          <span class="hint"
            >${t(s, "log.count", {
              shown: shown ? `${this._offset + 1}–${this._offset + shown}` : "0",
              total: this._total,
            })}</span
          >
          <button class="btn" ?disabled=${this._busy} @click=${() => void this._load()}>
            ${t(s, "log.refresh")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("csv")}>
            ${t(s, "log.export_csv")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("json")}>
            ${t(s, "log.export_json")}
          </button>
          ${ctx.isAdmin
            ? html`<button class="btn danger" ?disabled=${this._busy} @click=${() =>
                (this._confirmClear = true)}>
                ${t(s, "log.clear")}
              </button>`
            : nothing}
        </div>
        <div class="card-bd">
          ${this._error ? html`<div class="problems" role="alert">${this._error}</div>` : nothing}
          ${this._confirmClear
            ? html`<div class="problems" role="alert">
                <p>${t(s, "log.clear_confirm")}</p>
                <div class="actions">
                  <button class="btn danger" @click=${this._clear}>
                    ${t(s, "log.clear_yes")}
                  </button>
                  <button class="btn" @click=${() => (this._confirmClear = false)}>
                    ${t(s, "common.cancel")}
                  </button>
                </div>
              </div>`
            : nothing}
          ${shown === 0
            ? html`<p class="hint">${t(s, this._busy ? "common.loading" : "log.empty")}</p>`
            : html`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${t(s, "log.time")}</th>
                      <th>${t(s, "log.event")}</th>
                      <th>${t(s, "log.category")}</th>
                      <th>${t(s, "log.where")}</th>
                      <th>${t(s, "log.who")}</th>
                      <th>${t(s, "log.detail")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this._rows.map((row) => this._renderRow(s, row))}
                  </tbody>
                </table>
              </div>`}
          ${this._total > PAGE_SIZE
            ? html`<div class="actions">
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset === 0}
                  @click=${() => {
                    this._offset = Math.max(0, this._offset - PAGE_SIZE);
                    void this._load();
                  }}
                >
                  ${t(s, "log.newer")}
                </button>
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset + PAGE_SIZE >= this._total}
                  @click=${() => {
                    this._offset += PAGE_SIZE;
                    void this._load();
                  }}
                >
                  ${t(s, "log.older")}
                </button>
              </div>`
            : nothing}
        </div>
      </div>
    `;
  }

  private _renderRow(s: Strings, row: LogRow) {
    const ctx = this.ctx!;
    const area = ctx.status.areas.find((a) => a.id === row.area_id);
    const zone = ctx.status.zones.find((z) => z.id === row.zone_id);
    const open = this._open === row.id;
    const where = [area?.name, zone?.name].filter(Boolean).join(" · ");
    return html`
      <tr class="clickable" aria-selected=${open ? "true" : "false"} @click=${() =>
        (this._open = open ? undefined : row.id)}>
        <td class="mono">${new Date(row.ts).toLocaleString(ctx.hass.language)}</td>
        <td>
          <span class="state ${severityClass(row.severity)}">
            ${eventLabel(s, row.event_type)}
          </span>
        </td>
        <td><span class="tag">${t(s, `category.${row.category}`)}</span></td>
        <td>${where}</td>
        <td>
          ${row.user_name ?? (row.channel ? channelLabel(s, row.channel) : "")}
        </td>
        <td class="detail">${this._summary(s, row)}</td>
      </tr>
      ${open
        ? html`<tr class="expanded">
            <td colspan="6">
              <dl class="kv">
                ${row.incident_id
                  ? html`<dt>${t(s, "log.incident")}</dt>
                      <dd>
                        <button
                          class="btn small"
                          @click=${(e: Event) => {
                            e.stopPropagation();
                            this._filter({ incident_id: row.incident_id });
                          }}
                        >
                          ${t(s, "log.show_incident")}
                        </button>
                      </dd>`
                  : nothing}
                ${row.outcome
                  ? html`<dt>${t(s, "log.outcome")}</dt>
                      <dd>${t(s, `outcome.${row.outcome}`)}</dd>`
                  : nothing}
                ${row.channel
                  ? html`<dt>${t(s, "log.channel")}</dt>
                      <dd>${channelLabel(s, row.channel)}</dd>`
                  : nothing}
                <dt>${t(s, "log.detail")}</dt>
                <dd class="mono">${JSON.stringify(row.detail)}</dd>
              </dl>
            </td>
          </tr>`
        : nothing}
    `;
  }

  /** The one line that says what a row was about, without opening it. */
  private _summary(s: Strings, row: LogRow): string {
    const ctx = this.ctx!;
    const detail = row.detail ?? {};
    if (typeof detail.reason === "string") {
      const zones = Array.isArray(detail.blocking_zones)
        ? detail.blocking_zones
            .map((id) => ctx.status.zones.find((z) => z.id === id)?.name ?? String(id))
            .join(", ")
        : "";
      return t(s, `reason.${detail.reason}`, { zones });
    }
    if (typeof detail.error === "string") return detail.error;
    if (row.event_type === "zone_state") {
      return `${detail.from ?? "?"} → ${detail.to ?? "?"}`;
    }
    if (row.event_type === "system_unavailable" && typeof detail.down_since === "string") {
      return t(s, "log.gap", {
        from: new Date(detail.down_since).toLocaleString(ctx.hass.language),
        to: new Date(String(detail.up_at)).toLocaleString(ctx.hass.language),
      });
    }
    if (typeof detail.kind === "string" && row.category === "action") {
      return t(s, `action_kind.${detail.kind}`);
    }
    return "";
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .chip {
        border: 1px solid var(--divider-color);
        background: transparent;
        color: inherit;
        border-radius: 999px;
        padding: 4px 12px;
        font-size: 13px;
        cursor: pointer;
      }
      .chip[aria-pressed="true"] {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }
      .btn.small {
        padding: 4px 10px;
        font-size: 13px;
      }
      .card-hd .hint {
        flex: 1;
      }
      td.detail {
        color: var(--secondary-text-color);
        font-size: 13px;
        max-width: 40ch;
        overflow-wrap: anywhere;
      }
      tr.expanded td {
        background: var(--secondary-background-color);
      }
      dl.kv {
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 4px 16px;
        margin: 0;
        font-size: 13px;
      }
      dl.kv dt {
        color: var(--secondary-text-color);
      }
      dl.kv dd {
        margin: 0;
      }
    `,
  ];
}

/** The name of an event. Most are moments, which page 5 already translates;
 * the rest — a refusal, a config edit, the restart gap — are the log's own.
 * One lookup, two places to find it, no string written twice. */
function eventLabel(s: Strings, eventType: string): string {
  const own = t(s, `event_type.${eventType}`);
  if (!own.startsWith("event_type.")) return own;
  const moment = t(s, `moment.${eventType}`);
  return moment.startsWith("moment.") ? eventType : moment;
}

/** Through what the request came. Not the zone's channel, which is a
 * different thing with the same word (§4.2 versus §9.1). */
function channelLabel(s: Strings, channel: string): string {
  const label = t(s, `log_channel.${channel}`);
  return label.startsWith("log_channel.") ? channel : label;
}

function severityClass(severity: string): string {
  if (severity === "alarm") return "triggered";
  if (severity === "warning") return "arming";
  return "disarmed";
}

if (!customElements.get("foyer-page-log")) {
  customElements.define("foyer-page-log", FoyerPageLog);
}
