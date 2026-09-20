// Page 10 — Log (SPEC §15.1, §10). Filters by date, area, zone, category,
// severity and outcome; export of exactly the rows the filters show.
//
// The rows are data: every event type, category and outcome is translated
// here, never written by the backend, so the log reads in the language of
// whoever is looking at it.
import { LitElement, css, html, nothing } from "lit";

import { t, type Strings } from "../../shared/i18n";
import { formStyles, stateStyles } from "../../shared/styles";
import type { LogQuery, LogRow, PersonCounts } from "../../shared/types";
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
    _person: { state: true },
    _counts: { state: true },
    _keepPseudonym: { state: true },
    _confirmErase: { state: true },
    _erased: { state: true },
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
  // Personal data (§10.4). The person chosen, what an erasure would touch,
  // and whether this run keeps a stable identifier instead of forgetting.
  private _person = "";
  private _counts?: PersonCounts;
  private _keepPseudonym = false;
  private _confirmErase = false;
  private _erased?: number;

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

  // --- personal data (§10.4) -------------------------------------------------------

  private async _pick(userId: string): Promise<void> {
    this._person = userId;
    this._counts = undefined;
    this._confirmErase = false;
    this._erased = undefined;
    if (!userId || !this.ctx) return;
    try {
      this._counts = await this.ctx.previewPerson(userId);
    } catch (err) {
      this._error = String((err as { message?: string })?.message ?? err);
    }
  }

  private async _exportPerson(format: "csv" | "json"): Promise<void> {
    if (!this.ctx || !this._person) return;
    this._busy = true;
    this._error = undefined;
    try {
      const result = await this.ctx.exportPerson(this._person, format);
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

  private async _erasePerson(): Promise<void> {
    if (!this.ctx || !this._person) return;
    this._confirmErase = false;
    this._busy = true;
    this._error = undefined;
    try {
      const result = await this.ctx.erasePerson(this._person, this._keepPseudonym);
      if (result.success) {
        this._erased = result.removed ?? 0;
        this._counts = await this.ctx.previewPerson(this._person);
        await this._load();
      } else if (result.reason) {
        this._error = t(this.ctx.strings, `reason.${result.reason}`);
      }
    } catch (err) {
      this._error = String((err as { message?: string })?.message ?? err);
    } finally {
      this._busy = false;
    }
  }

  private _renderPeople(s: Strings) {
    const ctx = this.ctx!;
    // The list of people comes from the configuration, which only somebody
    // who may read it has. Export and erasure are theirs anyway (part 2
    // decision 3): a subject access request in a household is made to
    // whoever set the system up, and docs/privacy.md says so plainly.
    const users = ctx.config?.users;
    if (!users?.length) return nothing;
    const counts = this._counts;
    return html`
      <div class="card">
        <div class="card-hd"><h2>${t(s, "log.person_title")}</h2></div>
        <div class="card-bd">
          <p class="hint">${t(s, "log.person_intro")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${t(s, "log.person")}</span>
              <select
                .value=${this._person}
                @change=${(e: Event) =>
                  void this._pick((e.target as HTMLSelectElement).value)}
              >
                <option value="">${t(s, "log.person_none")}</option>
                ${users.map(
                  (user) =>
                    html`<option .value=${user.id!} ?selected=${user.id === this._person}>
                      ${user.name}
                    </option>`,
                )}
              </select>
            </label>
          </div>
          ${counts
            ? html`
                <p class="hint">
                  ${t(s, "log.person_found", {
                    total: counts.total,
                    by_id: counts.by_id,
                    by_name: counts.by_name,
                    about: counts.about,
                  })}
                </p>
                <p class="hint">${t(s, "log.person_export_rows", { rows: counts.wide })}</p>
                <div class="actions">
                  <button
                    class="btn"
                    ?disabled=${this._busy}
                    @click=${() => void this._exportPerson("csv")}
                  >
                    ${t(s, "log.person_export_csv")}
                  </button>
                  <button
                    class="btn"
                    ?disabled=${this._busy}
                    @click=${() => void this._exportPerson("json")}
                  >
                    ${t(s, "log.person_export_json")}
                  </button>
                  <button
                    class="btn danger"
                    ?disabled=${this._busy || counts.total === 0}
                    @click=${() => (this._confirmErase = true)}
                  >
                    ${t(s, "log.person_erase")}
                  </button>
                </div>
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${this._keepPseudonym}
                    @change=${(e: Event) =>
                      (this._keepPseudonym = (e.target as HTMLInputElement).checked)}
                  />
                  <span>${t(s, "log.person_keep_pseudonym")}</span>
                </label>
                <p class="hint">${t(s, "log.person_keep_pseudonym_hint")}</p>
              `
            : nothing}
          ${this._erased !== undefined
            ? html`<p class="hint">${t(s, "log.person_erased", { rows: this._erased })}</p>`
            : nothing}
          ${this._confirmErase
            ? html`<div class="problems" role="alert">
                <p>
                  ${t(
                    s,
                    this._keepPseudonym
                      ? "log.person_erase_confirm_pseudonym"
                      : "log.person_erase_confirm",
                    { rows: counts?.total ?? 0 },
                  )}
                </p>
                <div class="actions">
                  <button class="btn danger" @click=${() => void this._erasePerson()}>
                    ${t(s, "log.person_erase_yes")}
                  </button>
                  <button class="btn" @click=${() => (this._confirmErase = false)}>
                    ${t(s, "common.cancel")}
                  </button>
                </div>
              </div>`
            : nothing}
        </div>
      </div>
    `;
  }

  override render() {
    const ctx = this.ctx;
    if (!ctx) return nothing;
    const s = ctx.strings;
    return html`${this._renderFilters(s)} ${this._renderRows(s)} ${this._renderPeople(s)}`;
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
          ${row.detail?.attributed === "claimed"
            ? // The name was asserted by the request, not established by a
              // code or a token (§9.1). The row keeps it and stops short of
              // claiming it knows (decision 88).
              html`<span class="claimed">${t(s, "log.claimed")}</span>`
            : nothing}
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
                ${this._changeLines(s, row).map(
                  (line, index) => html`<dt>${index ? "" : t(s, "log.changes")}</dt>
                    <dd>${line}</dd>`,
                )}
                ${this._plainDetail(row).map(
                  ([key, value]) => html`<dt>${t(s, `detail.${key}`)}</dt>
                    <dd class="mono">${value}</dd>`,
                )}
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
    if (row.event_type === "reloaded") {
      return t(s, "log.gap_short", { seconds: String(detail.gap_seconds ?? "") });
    }
    // An empty `down_since` is a first start with nothing saved before it, and
    // "from Invalid Date to …" is what a truthy check on an empty string
    // renders. There is no honest range to show, so the row says only what it
    // already says: Foyer was not running.
    if (
      row.event_type === "system_unavailable" &&
      typeof detail.down_since === "string" &&
      detail.down_since !== ""
    ) {
      return t(s, "log.gap", {
        from: new Date(detail.down_since).toLocaleString(ctx.hass.language),
        to: new Date(String(detail.up_at)).toLocaleString(ctx.hass.language),
      });
    }
    if (typeof detail.kind === "string" && row.category === "action") {
      return t(s, `action_kind.${detail.kind}`);
    }
    const lines = this._changeLines(s, row);
    if (lines.length) {
      return lines.length > 2
        ? `${lines.slice(0, 2).join(" · ")} ${t(s, "log.and_more", {
            count: lines.length - 2,
          })}`
        : lines.join(" · ");
    }
    return "";
  }

  /** What a configuration change actually changed, in words.
   *
   * "Who changed what" is what this category is for, and a field name on its
   * own does not answer it: the row carries the value before and the value
   * after, and this turns them into a line a person can read six months later.
   */
  private _changeLines(s: Strings, row: LogRow): string[] {
    const changes = row.detail?.changes;
    if (!changes || typeof changes !== "object" || Array.isArray(changes)) return [];
    const lines: string[] = [];
    for (const [kind, entry] of Object.entries(changes as Record<string, unknown>)) {
      const label = t(s, `config_kind.${kind}`);
      if (typeof entry !== "object" || entry === null) {
        lines.push(`${label}: ${this._value(s, entry)}`);
        continue;
      }
      const group = entry as Record<string, unknown>;
      const grouped = "added" in group || "removed" in group || "changed" in group;
      if (!grouped) {
        // A settings block: the fields are the entry itself.
        lines.push(...this._fieldLines(s, label, group));
        continue;
      }
      for (const name of (group.added as string[]) ?? []) {
        lines.push(`${label} · ${t(s, "log.added")}: ${name}`);
      }
      for (const name of (group.removed as string[]) ?? []) {
        lines.push(`${label} · ${t(s, "log.removed")}: ${name}`);
      }
      const changed = (group.changed as Record<string, unknown>) ?? {};
      for (const [name, fields] of Object.entries(changed)) {
        lines.push(
          ...this._fieldLines(
            s,
            `${label} «${name}»`,
            fields as Record<string, unknown>,
          ),
        );
      }
    }
    return lines;
  }

  private _fieldLines(
    s: Strings,
    prefix: string,
    fields: Record<string, unknown> | string[],
  ): string[] {
    // Rows written before values were recorded carry a list of field names.
    if (Array.isArray(fields)) {
      return fields.map((field) => `${prefix} · ${t(s, `field.${field}`)}`);
    }
    return Object.entries(fields).map(([field, pair]) => {
      const name = t(s, `field.${field}`);
      const label = name.startsWith("field.") ? field : name;
      if (Array.isArray(pair) && pair.length === 2) {
        return `${prefix} · ${label}: ${this._value(s, pair[0])} → ${this._value(
          s,
          pair[1],
        )}`;
      }
      return `${prefix} · ${label}: ${t(s, "log.changed")}`;
    });
  }

  private _value(s: Strings, value: unknown): string {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return t(s, value ? "common.yes" : "common.no");
    if (Array.isArray(value)) {
      return value.length ? value.map((v) => this._value(s, v)).join(", ") : "—";
    }
    return String(value);
  }

  /** Everything else in the detail, as it is: one line per key, so a row is
   * readable without a JSON parser in the reader's head. */
  private _plainDetail(row: LogRow): [string, string][] {
    const skip = new Set(["changes", "zone_ids", "blocking_zones"]);
    return Object.entries(row.detail ?? {})
      .filter(([key, value]) => !skip.has(key) && value !== null && value !== "")
      .map(([key, value]) => [
        key,
        typeof value === "object" ? JSON.stringify(value) : String(value),
      ]);
  }

  static override styles = [
    stateStyles,
    formStyles,
    css`
      .claimed {
        margin-left: 6px;
        font-size: 12px;
        color: var(--warning-color, #c77700);
        white-space: nowrap;
      }
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
