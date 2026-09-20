/*! Foyer Home Defender — Apache-2.0. See LICENSE and NOTICE.
* Bundles Lit (https://lit.dev): Copyright 2017 Google LLC, BSD-3-Clause. */
//#region node_modules/@lit/reactive-element/css-tag.js
var e = globalThis, t = e.ShadowRoot && (e.ShadyCSS === void 0 || e.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, n = Symbol(), r = /* @__PURE__ */ new WeakMap(), i = class {
	constructor(e, t, r) {
		if (this._$cssResult$ = !0, r !== n) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
		this.cssText = e, this.t = t;
	}
	get styleSheet() {
		let e = this.o, n = this.t;
		if (t && e === void 0) {
			let t = n !== void 0 && n.length === 1;
			t && (e = r.get(n)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), t && r.set(n, e));
		}
		return e;
	}
	toString() {
		return this.cssText;
	}
}, a = (e) => new i(typeof e == "string" ? e : e + "", void 0, n), o = (e, ...t) => new i(e.length === 1 ? e[0] : t.reduce((t, n, r) => t + ((e) => {
	if (!0 === e._$cssResult$) return e.cssText;
	if (typeof e == "number") return e;
	throw Error("Value passed to 'css' function must be a 'css' function result: " + e + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
})(n) + e[r + 1], e[0]), e, n), s = (n, r) => {
	if (t) n.adoptedStyleSheets = r.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
	else for (let t of r) {
		let r = document.createElement("style"), i = e.litNonce;
		i !== void 0 && r.setAttribute("nonce", i), r.textContent = t.cssText, n.appendChild(r);
	}
}, c = t ? (e) => e : (e) => e instanceof CSSStyleSheet ? ((e) => {
	let t = "";
	for (let n of e.cssRules) t += n.cssText;
	return a(t);
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: f, getOwnPropertySymbols: ee, getPrototypeOf: te } = Object, p = globalThis, ne = p.trustedTypes, re = ne ? ne.emptyScript : "", ie = p.reactiveElementPolyfillSupport, m = (e, t) => e, h = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? re : null;
				break;
			case Object:
			case Array: e = e == null ? e : JSON.stringify(e);
		}
		return e;
	},
	fromAttribute(e, t) {
		let n = e;
		switch (t) {
			case Boolean:
				n = e !== null;
				break;
			case Number:
				n = e === null ? null : Number(e);
				break;
			case Object:
			case Array: try {
				n = JSON.parse(e);
			} catch {
				n = null;
			}
		}
		return n;
	}
}, ae = (e, t) => !l(e, t), oe = {
	attribute: !0,
	type: String,
	converter: h,
	reflect: !1,
	useDefault: !1,
	hasChanged: ae
};
Symbol.metadata ??= Symbol("metadata"), p.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var g = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = oe) {
		if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
			let n = Symbol(), r = this.getPropertyDescriptor(e, n, t);
			r !== void 0 && u(this.prototype, e, r);
		}
	}
	static getPropertyDescriptor(e, t, n) {
		let { get: r, set: i } = d(this.prototype, e) ?? {
			get() {
				return this[t];
			},
			set(e) {
				this[t] = e;
			}
		};
		return {
			get: r,
			set(t) {
				let a = r?.call(this);
				i?.call(this, t), this.requestUpdate(e, a, n);
			},
			configurable: !0,
			enumerable: !0
		};
	}
	static getPropertyOptions(e) {
		return this.elementProperties.get(e) ?? oe;
	}
	static _$Ei() {
		if (this.hasOwnProperty(m("elementProperties"))) return;
		let e = te(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(m("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(m("properties"))) {
			let e = this.properties, t = [...f(e), ...ee(e)];
			for (let n of t) this.createProperty(n, e[n]);
		}
		let e = this[Symbol.metadata];
		if (e !== null) {
			let t = litPropertyMetadata.get(e);
			if (t !== void 0) for (let [e, n] of t) this.elementProperties.set(e, n);
		}
		this._$Eh = /* @__PURE__ */ new Map();
		for (let [e, t] of this.elementProperties) {
			let n = this._$Eu(e, t);
			n !== void 0 && this._$Eh.set(n, e);
		}
		this.elementStyles = this.finalizeStyles(this.styles);
	}
	static finalizeStyles(e) {
		let t = [];
		if (Array.isArray(e)) {
			let n = new Set(e.flat(1 / 0).reverse());
			for (let e of n) t.unshift(c(e));
		} else e !== void 0 && t.push(c(e));
		return t;
	}
	static _$Eu(e, t) {
		let n = t.attribute;
		return !1 === n ? void 0 : typeof n == "string" ? n : typeof e == "string" ? e.toLowerCase() : void 0;
	}
	constructor() {
		super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
	}
	_$Ev() {
		this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
	}
	addController(e) {
		(this._$EO ??= /* @__PURE__ */ new Set()).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
	}
	removeController(e) {
		this._$EO?.delete(e);
	}
	_$E_() {
		let e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
		for (let n of t.keys()) this.hasOwnProperty(n) && (e.set(n, this[n]), delete this[n]);
		e.size > 0 && (this._$Ep = e);
	}
	createRenderRoot() {
		let e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
		return s(e, this.constructor.elementStyles), e;
	}
	connectedCallback() {
		this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
	}
	enableUpdating(e) {}
	disconnectedCallback() {
		this._$EO?.forEach((e) => e.hostDisconnected?.());
	}
	attributeChangedCallback(e, t, n) {
		this._$AK(e, n);
	}
	_$ET(e, t) {
		let n = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, n);
		if (r !== void 0 && !0 === n.reflect) {
			let i = (n.converter?.toAttribute === void 0 ? h : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? h : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? ae)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
			this.C(e, t, n);
		}
		!1 === this.isUpdatePending && (this._$ES = this._$EP());
	}
	C(e, t, { useDefault: n, reflect: r, wrapped: i }, a) {
		n && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, a ?? t ?? this[e]), !0 !== i || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || n || (t = void 0), this._$AL.set(e, t)), !0 === r && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
	}
	async _$EP() {
		this.isUpdatePending = !0;
		try {
			await this._$ES;
		} catch (e) {
			Promise.reject(e);
		}
		let e = this.scheduleUpdate();
		return e != null && await e, !this.isUpdatePending;
	}
	scheduleUpdate() {
		return this.performUpdate();
	}
	performUpdate() {
		if (!this.isUpdatePending) return;
		if (!this.hasUpdated) {
			if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
				for (let [e, t] of this._$Ep) this[e] = t;
				this._$Ep = void 0;
			}
			let e = this.constructor.elementProperties;
			if (e.size > 0) for (let [t, n] of e) {
				let { wrapped: e } = n, r = this[t];
				!0 !== e || this._$AL.has(t) || r === void 0 || this.C(t, void 0, n, r);
			}
		}
		let e = !1, t = this._$AL;
		try {
			e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((e) => e.hostUpdate?.()), this.update(t)) : this._$EM();
		} catch (t) {
			throw e = !1, this._$EM(), t;
		}
		e && this._$AE(t);
	}
	willUpdate(e) {}
	_$AE(e) {
		this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
	}
	_$EM() {
		this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
	}
	get updateComplete() {
		return this.getUpdateComplete();
	}
	getUpdateComplete() {
		return this._$ES;
	}
	shouldUpdate(e) {
		return !0;
	}
	update(e) {
		this._$Eq &&= this._$Eq.forEach((e) => this._$ET(e, this[e])), this._$EM();
	}
	updated(e) {}
	firstUpdated(e) {}
};
g.elementStyles = [], g.shadowRootOptions = { mode: "open" }, g[m("elementProperties")] = /* @__PURE__ */ new Map(), g[m("finalized")] = /* @__PURE__ */ new Map(), ie?.({ ReactiveElement: g }), (p.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
var _ = globalThis, se = (e) => e, v = _.trustedTypes, ce = v ? v.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, le = "$lit$", y = `lit$${Math.random().toFixed(9).slice(2)}$`, ue = "?" + y, de = `<${ue}>`, b = document, x = () => b.createComment(""), S = (e) => e === null || typeof e != "object" && typeof e != "function", C = Array.isArray, fe = (e) => C(e) || typeof e?.[Symbol.iterator] == "function", w = "[ 	\n\f\r]", T = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, pe = /-->/g, me = />/g, E = RegExp(`>|${w}(?:([^\\s"'>=/]+)(${w}*=${w}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), he = /'/g, ge = /"/g, _e = /^(?:script|style|textarea|title)$/i, D = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), O = Symbol.for("lit-noChange"), k = Symbol.for("lit-nothing"), ve = /* @__PURE__ */ new WeakMap(), A = b.createTreeWalker(b, 129);
function ye(e, t) {
	if (!C(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return ce === void 0 ? t : ce.createHTML(t);
}
var be = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = T;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === T ? c[1] === "!--" ? o = pe : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = E) : (_e.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = E) : o = me : o === E ? c[0] === ">" ? (o = i ?? T, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? E : c[3] === "\"" ? ge : he) : o === ge || o === he ? o = E : o === pe || o === me ? o = T : (o = E, i = void 0);
		let d = o === E && e[t + 1].startsWith("/>") ? " " : "";
		a += o === T ? n + de : l >= 0 ? (r.push(s), n.slice(0, l) + le + n.slice(l) + y + d) : n + y + (l === -2 ? t : d);
	}
	return [ye(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, j = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = be(t, n);
		if (this.el = e.createElement(l, r), A.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = A.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(le)) {
					let t = u[o++], n = i.getAttribute(e).split(y), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? Se : r[1] === "?" ? Ce : r[1] === "@" ? we : P
					}), i.removeAttribute(e);
				} else e.startsWith(y) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (_e.test(i.tagName)) {
					let e = i.textContent.split(y), t = e.length - 1;
					if (t > 0) {
						i.textContent = v ? v.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], x()), A.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], x());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === ue) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(y, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += y.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = b.createElement("template");
		return n.innerHTML = e, n;
	}
};
function M(e, t, n = e, r) {
	if (t === O) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = S(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = M(e, i._$AS(e, t.values), i, r)), t;
}
var xe = class {
	constructor(e, t) {
		this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
	}
	get parentNode() {
		return this._$AM.parentNode;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	u(e) {
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? b).importNode(t, !0);
		A.currentNode = r;
		let i = A.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new N(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Te(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = A.nextNode(), a++);
		}
		return A.currentNode = b, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, N = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = k, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
	}
	get parentNode() {
		let e = this._$AA.parentNode, t = this._$AM;
		return t !== void 0 && e?.nodeType === 11 && (e = t.parentNode), e;
	}
	get startNode() {
		return this._$AA;
	}
	get endNode() {
		return this._$AB;
	}
	_$AI(e, t = this) {
		e = M(this, e, t), S(e) ? e === k || e == null || e === "" ? (this._$AH !== k && this._$AR(), this._$AH = k) : e !== this._$AH && e !== O && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? fe(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== k && S(this._$AH) ? this._$AA.nextSibling.data = e : this.T(b.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = j.createElement(ye(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new xe(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = ve.get(e.strings);
		return t === void 0 && ve.set(e.strings, t = new j(e)), t;
	}
	k(t) {
		C(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(x()), this.O(x()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = se(e).nextSibling;
			se(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, P = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = k, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = k;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = M(this, e, t, 0), a = !S(e) || e !== this._$AH && e !== O, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = M(this, r[n + o], t, o), s === O && (s = this._$AH[o]), a ||= !S(s) || s !== this._$AH[o], s === k ? e = k : e !== k && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === k ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, Se = class extends P {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === k ? void 0 : e;
	}
}, Ce = class extends P {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== k);
	}
}, we = class extends P {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = M(this, e, t, 0) ?? k) === O) return;
		let n = this._$AH, r = e === k && n !== k || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== k && (n === k || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Te = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		M(this, e);
	}
}, Ee = _.litHtmlPolyfillSupport;
Ee?.(j, N), (_.litHtmlVersions ??= []).push("3.3.3");
var De = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new N(t.insertBefore(x(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, F = globalThis, I = class extends g {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = De(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return O;
	}
};
I._$litElement$ = !0, I.finalized = !0, F.litElementHydrateSupport?.({ LitElement: I });
var Oe = F.litElementPolyfillSupport;
Oe?.({ LitElement: I }), (F.litElementVersions ??= []).push("4.2.2");
//#endregion
//#region node_modules/lit-html/directive.js
var ke = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, Ae = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), je = class {
	constructor(e) {}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AT(e, t, n) {
		this._$Ct = e, this._$AM = t, this._$Ci = n;
	}
	_$AS(e, t) {
		return this.update(e, t);
	}
	update(e, t) {
		return this.render(...t);
	}
}, L = class extends je {
	constructor(e) {
		if (super(e), this.it = k, e.type !== ke.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
	}
	render(e) {
		if (e === k || e == null) return this._t = void 0, this.it = e;
		if (e === O) return e;
		if (typeof e != "string") throw Error(this.constructor.directiveName + "() called with a non-string value");
		if (e === this.it) return this._t;
		this.it = e;
		let t = [e];
		return t.raw = t, this._t = {
			_$litType$: this.constructor.resultType,
			strings: t,
			values: []
		};
	}
};
L.directiveName = "unsafeHTML", L.resultType = 1;
//#endregion
//#region node_modules/lit-html/directives/unsafe-svg.js
var R = class extends L {};
R.directiveName = "unsafeSVG", R.resultType = 2;
var Me = Ae(R), Ne = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n", Pe = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n";
//#endregion
//#region src/shared/brand.ts
function Fe(e) {
	return e ? Ne : Pe;
}
//#endregion
//#region src/shared/i18n.ts
var z = /* @__PURE__ */ new Map();
function Ie(e) {
	let t = e.language, n = z.get(t);
	return n || (n = e.callWS({
		type: "foyer/translations",
		language: t
	}).then((e) => e.strings), n.catch(() => z.delete(t)), z.set(t, n)), n;
}
function B(e, t, n = {}) {
	let r = e;
	for (let e of t.split(".")) if (r && typeof r == "object" && e in r) r = r[e];
	else return t;
	return typeof r == "string" ? r.replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e) : t;
}
//#endregion
//#region src/shared/styles.ts
var V = o`
  .state {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 500;
    background: var(--secondary-background-color);
    color: var(--primary-text-color);
    white-space: nowrap;
  }
  .state::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
  }
  .state.disarmed,
  .state.closed {
    color: var(--success-color, #2e9e4f);
  }
  .state.armed {
    color: var(--info-color, #0277bd);
  }
  .state.arming,
  .state.entry,
  .state.open,
  .state.bypassed,
  .state.memory {
    color: var(--warning-color, #c77700);
  }
  .state.triggered,
  .state.fault {
    color: var(--error-color, #d32f2f);
  }
  .state.disabled {
    color: var(--disabled-text-color, #9e9e9e);
  }
`, H = o`
  .card {
    background: var(--card-background-color);
    border: 1px solid var(--divider-color);
    border-radius: var(--ha-card-border-radius, 12px);
    margin-bottom: 16px;
    overflow: hidden;
  }
  .card-hd {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--divider-color);
  }
  .card-hd h2 {
    font-size: 16px;
    font-weight: 500;
    margin: 0;
    flex: 1;
  }
  .card-bd {
    padding: 16px;
  }
  .table-wrap {
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th,
  td {
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid var(--divider-color);
    vertical-align: middle;
  }
  th {
    font-size: 12px;
    font-weight: 500;
    color: var(--secondary-text-color);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  tr.clickable {
    cursor: pointer;
  }
  tr.clickable:hover,
  tr[aria-selected="true"] {
    background: var(--secondary-background-color);
  }
  .mono {
    font-family: var(--code-font-family, monospace);
    font-size: 12.5px;
    overflow-wrap: anywhere;
  }
  .grid-form {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 14px 16px;
  }
  label.field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
  }
  label.field > span.lbl {
    font-weight: 500;
  }
  .hint {
    font-size: 12px;
    color: var(--secondary-text-color);
  }
  input,
  select {
    font: inherit;
    font-size: 14px;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid var(--divider-color);
    background: var(--primary-background-color);
    color: var(--primary-text-color);
    min-width: 0;
  }
  input[type="checkbox"] {
    width: 18px;
    height: 18px;
    padding: 0;
  }
  label.check {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 14px;
    padding: 6px 0;
  }
  label.check .hint {
    display: block;
  }
  fieldset {
    border: 1px solid var(--divider-color);
    border-radius: 10px;
    padding: 10px 14px 14px;
    margin: 16px 0 0;
  }
  legend {
    font-weight: 500;
    font-size: 14px;
    padding: 0 6px;
  }
  .btn {
    font: inherit;
    font-size: 14px;
    font-weight: 500;
    border-radius: 8px;
    padding: 8px 14px;
    border: 1px solid var(--divider-color);
    background: var(--card-background-color);
    color: var(--primary-text-color);
    cursor: pointer;
  }
  .btn.primary {
    background: var(--primary-color);
    border-color: var(--primary-color);
    color: var(--text-primary-color, #fff);
  }
  .btn.danger {
    color: var(--error-color, #d32f2f);
  }
  .btn[disabled] {
    opacity: 0.5;
    cursor: default;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
  }
  .problems {
    margin: 12px 0 0;
    padding: 10px 14px;
    border-left: 3px solid var(--error-color, #d32f2f);
    background: var(--secondary-background-color);
    border-radius: 6px;
    font-size: 13.5px;
  }
  .problems ul {
    margin: 0;
    padding-left: 18px;
  }
  .notice {
    padding: 10px 14px;
    border-left: 3px solid var(--warning-color, #c77700);
    background: var(--secondary-background-color);
    border-radius: 6px;
    font-size: 13.5px;
    margin: 12px 0 0;
  }
  .tag {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 6px;
    background: var(--secondary-background-color);
    font-size: 12.5px;
    margin: 1px 2px;
  }
  /* A chip that carries a verdict: a code set or missing, who a tag belongs
     to. Pages 7 and 8 have asked for one since Phase 2 and there was no rule
     behind the class, so it rendered as plain text — the same defect the
     walk test banner had. The colour is on the text: a filled chip in
     warning amber next to a name reads as an alarm. */
  .pill {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 999px;
    background: var(--secondary-background-color);
    font-size: 12.5px;
    font-weight: 500;
    white-space: nowrap;
  }
  .pill.ok {
    color: var(--success-color, #2e9e4f);
  }
  .pill.warn {
    color: var(--warning-color, #c77700);
  }
  .pill.bad {
    color: var(--error-color, #d32f2f);
  }
  .pill.idle {
    color: var(--secondary-text-color);
  }
  .muted {
    color: var(--secondary-text-color);
  }
  .empty {
    padding: 24px 16px;
    color: var(--secondary-text-color);
    text-align: center;
  }
`;
//#endregion
//#region src/shared/time.ts
function Le(e) {
	let t = Math.max(0, Math.round(e));
	return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function Re(e, t = 0) {
	return Math.max(0, Math.round((Date.parse(e) - (Date.now() + t)) / 1e3));
}
//#endregion
//#region src/panel/context.ts
function ze(e, t, n) {
	let r = URL.createObjectURL(new Blob([t], { type: n })), i = document.createElement("a");
	i.href = r, i.download = e, i.click(), setTimeout(() => URL.revokeObjectURL(r), 1e3);
}
function Be(e, t) {
	return Math.max(0, Math.round((Date.parse(t) - e.now()) / 1e3));
}
function Ve(e, t) {
	let n = t.blocking_zones.map((e) => e.name).join(", ");
	return B(e, `reason.${t.reason ?? "unknown"}`, { zones: n });
}
function U(e, t) {
	let n = t.field ? B(e, `field.${t.field}`) : "";
	return B(e, `problem.${t.code}`, {
		field: n,
		detail: t.detail ?? ""
	});
}
function W(e) {
	let t = e.trim();
	if (t === "") return null;
	let n = Number(t);
	return Number.isFinite(n) ? n : null;
}
//#endregion
//#region src/panel/pages/overview.ts
function He(e, t) {
	let n = B(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = B(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
var Ue = /* @__PURE__ */ new Set(["zone_open", "zone_fault"]), We = class extends I {
	constructor(...e) {
		super(...e), this._busy = !1, this._recent = [];
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_busy: { state: !0 },
			_feedback: { state: !0 },
			_recent: { state: !0 }
		};
	}
	async _run(e, t) {
		let n = this.ctx;
		if (n) {
			this._busy = !0, this._feedback = void 0;
			try {
				let r = await e();
				if (r.success) {
					let e = r.bypassed_zones.map((e) => e.name).join(", "), t = r.low_battery_zones;
					this._feedback = t.length ? {
						ok: !0,
						text: B(n.strings, "overview.low_battery", { zones: t.map((e) => e.name).join(", ") }),
						lowBattery: t
					} : e ? {
						ok: !0,
						text: B(n.strings, "overview.bypassed", { zones: e })
					} : void 0;
				} else this._feedback = {
					ok: !1,
					text: Ve(n.strings, r),
					retry: t && Ue.has(r.reason ?? "") ? t : void 0
				};
			} catch (e) {
				this._feedback = {
					ok: !1,
					text: String(e?.message ?? e)
				};
			} finally {
				this._busy = !1;
			}
		}
	}
	_arm(e) {
		let t = this.ctx;
		t && this._run(() => t.arm(e), e);
	}
	_force(e) {
		let t = this.ctx;
		t && this._run(() => t.arm({
			...e,
			force: !0
		}));
	}
	async _excludeLowBattery(e) {
		let t = this.ctx;
		if (t) {
			this._busy = !0;
			try {
				for (let n of e) await t.bypass(n.id, !0);
				this._feedback = void 0;
			} catch (e) {
				this._feedback = {
					ok: !1,
					text: String(e?.message ?? e)
				};
			} finally {
				this._busy = !1;
			}
		}
	}
	_disarm(e) {
		let t = this.ctx;
		t && this._run(() => t.disarm(e));
	}
	_acknowledge(e) {
		let t = this.ctx;
		t && this._run(() => t.acknowledge(e));
	}
	updated(e) {
		if (!e.has("ctx") || !this.ctx) return;
		let t = this._signature();
		t !== this._signature_ && (this._signature_ = t, this._loadRecent());
	}
	_signature() {
		let e = this.ctx.status;
		return JSON.stringify([
			e.active_scenario_id,
			e.areas.map((e) => [
				e.id,
				e.state,
				e.memory,
				e.ready
			]),
			e.incident?.id,
			e.incident?.acknowledged,
			e.technical.map((e) => [e.zone_id, e.acknowledged]),
			e.zones.map((e) => [
				e.id,
				e.state,
				e.bypassed,
				e.fault
			]),
			e.chime_enabled
		]);
	}
	render() {
		let e = this.ctx;
		if (!e) return k;
		let t = e.strings, n = e.status, r = n.areas.filter((e) => e.memory);
		return D`
      ${this._renderTechnical(t)} ${this._renderIncident(t)}
      ${n.security.enforced ? k : D`<div class="notice" role="note">
            ${B(t, "overview.no_codes_warning")}
          </div>`}
      ${r.map((e) => D`<div class="alarm-memory" role="alert">
          ${e.causes.length ? B(t, "overview.memory_banner", {
			area: e.name,
			zones: this._zoneNames(e.causes)
		}) : B(t, "overview.memory_banner_plain", { area: e.name })}
        </div>`)}
      ${this._renderMaster(t)} ${this._renderFeedback(t)}
      <div class="tiles">${n.areas.map((e) => this._renderArea(t, e))}</div>
      ${this._renderNotReady(t)} ${this._renderRecent(t)}
    `;
	}
	_renderRecent(e) {
		let t = this.ctx, n = this._recent;
		if (!n.length) return k;
		let r = new Map(t.status.areas.map((e) => [e.id, e.name])), i = new Map(t.status.zones.map((e) => [e.id, e.name]));
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "overview.recent")}</h2>
          <span class="spacer"></span>
          <button class="btn sm" @click=${() => t.navigate("log")}>
            ${B(e, "overview.full_log")}
          </button>
        </div>
        <div class="card-bd">
          <div class="recent">
            ${n.map((n) => D`<div class="row">
                <span class="when mono"
                  >${new Date(n.ts).toLocaleTimeString(t.hass.language, {
			hour: "2-digit",
			minute: "2-digit"
		})}</span
                >
                <span class="state ${n.severity === "alarm" ? "triggered" : n.severity === "warning" ? "arming" : "disarmed"}"
                  >${He(e, n.event_type)}</span
                >
                <span class="where">
                  ${[r.get(n.area_id ?? ""), i.get(n.zone_id ?? "")].filter(Boolean).join(" · ")}
                </span>
              </div>`)}
          </div>
        </div>
      </div>
    `;
	}
	async _loadRecent() {
		let e = this.ctx;
		if (e) try {
			let t = await e.queryLog({
				limit: 6,
				categories: [
					"arming",
					"alarm",
					"security",
					"system"
				]
			});
			this._recent = t.rows;
		} catch {
			this._recent = [];
		}
	}
	_zoneNames(e) {
		let t = new Map(this.ctx.status.zones.map((e) => [e.id, e.name]));
		return e.map((e) => t.get(e) ?? e).join(", ");
	}
	_renderTechnical(e) {
		let t = this.ctx.status.technical;
		if (!t.length) return k;
		let n = t.some((e) => !e.acknowledged);
		return D`
      <div class="banner technical" role="alert">
        <div class="banner-hd">${B(e, "overview.technical_title")}</div>
        <div>
          ${B(e, "overview.technical_banner", { zones: t.map((e) => e.name).join(", ") })}
        </div>
        <ul class="plain">
          ${t.map((t) => D`<li>
              <strong>${t.name}</strong> —
              ${B(e, t.acknowledged ? "technical_state.acknowledged" : t.active ? "technical_state.active" : "technical_state.memory")}
            </li>`)}
        </ul>
        ${n ? D`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("technical")}
              >
                ${B(e, "common.acknowledge")}
              </button>
            </div>` : k}
      </div>
    `;
	}
	_renderIncident(e) {
		let t = this.ctx.status.incident;
		return t ? D`
      <div class="banner incident" role="alert">
        <div class="banner-hd">
          ${B(e, "overview.incident_title", { id: t.id })}
          <span class="state ${t.acknowledged ? "memory" : "triggered"}">
            ${B(e, t.acknowledged ? "overview.incident_acknowledged" : "overview.incident_open")}
          </span>
        </div>
        <div>${B(e, "overview.incident_zones", { zones: this._zoneNames(t.zone_ids) })}</div>
        <div class="hint">${B(e, "overview.incident_hint")}</div>
        ${t.acknowledged ? k : D`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("incident")}
              >
                ${B(e, "common.acknowledge")}
              </button>
            </div>`}
      </div>
    ` : k;
	}
	_renderMaster(e) {
		let t = this.ctx.status, n = t.master, r = t.areas.some((e) => e.state !== "disarmed" || e.memory);
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "overview.master")}</h2>
          <span class="state ${n.state}">${B(e, `state.${n.state}`)}</span>
          ${n.mode ? D`<span class="mono">${n.mode}</span>` : k}
        </div>
        <div class="card-bd">
          <div class="label">${B(e, "overview.scenario")}</div>
          <div class="chips">
            ${t.scenarios.length ? t.scenarios.map((e) => D`
                    <button
                      class="chip"
                      aria-pressed=${e.id === t.active_scenario_id ? "true" : "false"}
                      ?disabled=${this._busy}
                      @click=${() => this._arm({ scenario_id: e.id })}
                    >
                      ${e.name}
                    </button>
                  `) : D`<span class="muted">${B(e, "overview.no_scenarios")}</span>`}
          </div>
          <div class="hint">${B(e, "overview.scenario_hint")}</div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !r}
              @click=${() => this._disarm()}
            >
              ${B(e, "overview.disarm_all")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderFeedback(e) {
		let t = this._feedback;
		return t ? D`
      <div class=${t.ok ? "notice" : "problems"} role="alert">
        ${t.text}
        ${t.lowBattery?.length ? D`<div class="actions">
              <button
                class="btn"
                ?disabled=${this._busy}
                @click=${() => void this._excludeLowBattery(t.lowBattery)}
              >
                ${B(e, "overview.exclude_low_battery")}
              </button>
            </div>` : k}
        ${t.retry ? D`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._force(t.retry)}
              >
                ${B(e, "overview.force_arm")}
              </button>
              <span class="hint">${B(e, "overview.force_arm_hint")}</span>
            </div>` : k}
      </div>
    ` : k;
	}
	_renderArea(e, t) {
		let n = this.ctx, r = n.status.scenarios.find((e) => e.id === t.scenario_id);
		return D`
      <div class="card tile">
        <div class="card-bd">
          <div class="label">${B(e, "overview.area")}</div>
          <div class="name">${t.name}</div>
          <div class="row">
            <span class="state ${t.state}">${B(e, `state.${t.state}`)}</span>
            ${t.memory ? D`<span class="state memory">${B(e, "overview.memory")}</span>` : k}
          </div>
          ${t.timer && t.timer.kind !== "siren" ? D`<div class="countdown">
                ${B(e, `timer.${t.timer.kind}`, { seconds: Be(n, t.timer.due) })}
              </div>` : k}
          <div class="hint">
            ${t.state === "disarmed" ? k : r ? B(e, "overview.by_scenario", { scenario: r.name }) : B(e, "overview.on_its_own")}
          </div>
          <div class="actions">
            ${t.state === "disarmed" ? D`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._arm({ area_id: t.id })}
                >
                  ${B(e, "overview.arm_area")}
                </button>` : k}
            ${t.state !== "disarmed" || t.memory ? D`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._disarm([t.id])}
                >
                  ${B(e, "overview.disarm_area")}
                </button>` : k}
          </div>
        </div>
      </div>
    `;
	}
	_renderNotReady(e) {
		let t = this.ctx, n = new Map(t.status.areas.map((e) => [e.id, e.name])), r = t.status.zones.filter((e) => e.enabled && (e.fault || e.open && e.channel === "intrusion" || e.bypassed));
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "overview.not_ready")}</h2></div>
        ${r.length ? D`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${B(e, "overview.zone")}</th>
                    <th>${B(e, "overview.area")}</th>
                    <th>${B(e, "overview.status")}</th>
                    <th>${B(e, "overview.entity_state")}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${r.map((t) => D`<tr>
                      <td>${t.name}</td>
                      <td>${n.get(t.area_id) ?? ""}</td>
                      <td>${this._zoneStatus(e, t)}</td>
                      <td class="mono">${t.state ?? "—"}</td>
                      <td>${this._renderBypass(e, t)}</td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : D`<div class="empty">${B(e, "overview.all_ready")}</div>`}
      </div>
    `;
	}
	_renderBypass(e, t) {
		let n = this.ctx;
		return t.bypassed ? D`<button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !1))}
      >
        ${B(e, "zones.unbypass")}
      </button>` : t.bypassable ? D`<div class="bypass">
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !0))}
      >
        ${B(e, "zones.bypass")}
      </button>
      ${[1, 8].map((r) => D`<button
          class="btn sm ghost"
          ?disabled=${this._busy}
          @click=${() => this._run(() => n.bypass(t.id, !0, r * 3600))}
        >
          ${B(e, "zones.bypass_hours", { hours: r })}
        </button>`)}
      <label class="minutes">
        <input
          type="number"
          min="1"
          max="10080"
          placeholder=${B(e, "zones.bypass_minutes_placeholder")}
          aria-label=${B(e, "zones.bypass_minutes")}
          @keydown=${(e) => {
			e.key === "Enter" && this._bypassMinutes(t.id, e.target);
		}}
        />
        <button
          class="btn sm ghost"
          ?disabled=${this._busy}
          @click=${(e) => {
			let n = e.target.closest("label").querySelector("input");
			this._bypassMinutes(t.id, n);
		}}
        >
          ${B(e, "zones.bypass_minutes")}
        </button>
      </label>
    </div>` : k;
	}
	_bypassMinutes(e, t) {
		let n = this.ctx, r = Number(t.value);
		!Number.isFinite(r) || r < 1 || (t.value = "", this._run(() => n.bypass(e, !0, Math.round(r) * 60)));
	}
	_zoneStatus(e, t) {
		let n = this.ctx;
		if (t.fault) return D`<span class="state fault">${B(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) {
			let r = t.bypass_until ? B(e, "zones.bypass_until", { time: new Date(t.bypass_until).toLocaleTimeString(n.hass.language, {
				hour: "2-digit",
				minute: "2-digit"
			}) }) : B(e, "zones.bypass_indefinite");
			return D`<span class="state bypassed">${B(e, `bypass.${t.bypassed}`)}</span>
        <span class="hint">${t.bypassed === "manual" ? r : ""}</span>`;
		}
		return D`<span class="state open">${B(e, "zone_status.open")}</span>`;
	}
	static {
		this.styles = [
			V,
			H,
			o`
      .recent {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 13.5px;
      }
      .recent .row {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }
      .recent .when {
        color: var(--secondary-text-color);
      }
      .recent .where {
        color: var(--secondary-text-color);
      }
      .spacer {
        flex: 1;
      }
      .minutes {
        display: inline-flex;
        align-items: center;
        gap: 4px;
      }
      .minutes input {
        width: 5.5em;
        font: inherit;
        font-size: 13px;
        padding: 4px 6px;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
      }
      .bypass {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
      }
      .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
      }
      .tile {
        margin: 0;
      }
      .label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--secondary-text-color);
        margin-bottom: 6px;
      }
      .name {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 8px;
      }
      .row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .countdown {
        margin-top: 10px;
        font-size: 15px;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
      }
      .hint {
        margin-top: 6px;
      }
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
      }
      .chip {
        font: inherit;
        font-size: 14px;
        padding: 6px 14px;
        border-radius: 999px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        cursor: pointer;
      }
      .chip[aria-pressed="true"] {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      .alarm-memory {
        margin: 12px 0;
        padding: 10px 14px;
        border-left: 3px solid var(--error-color, #d32f2f);
        background: var(--card-background-color);
        border-radius: 6px;
        font-weight: 500;
      }
      .notice {
        margin: 0 0 16px;
      }
      .problems {
        margin: 0 0 16px;
      }
      .banner {
        margin: 0 0 16px;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid var(--divider-color);
        border-left: 4px solid var(--error-color, #d32f2f);
        background: var(--card-background-color);
        font-size: 14px;
      }
      .banner.incident {
        border-left-color: var(--warning-color, #c77700);
      }
      .banner-hd {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 6px;
      }
      .banner .actions {
        margin-top: 10px;
      }
      ul.plain {
        margin: 8px 0 0;
        padding-left: 18px;
      }
    `
		];
	}
};
customElements.get("foyer-page-overview") || customElements.define("foyer-page-overview", We);
//#endregion
//#region src/panel/code-fields.ts
function Ge(e, t, n, r) {
	return D`<label class="field">
    <span class="lbl">${B(e, t)}</span>
    <select
      @change=${(e) => {
		let t = e.target.value;
		r(t === "" ? null : t === "yes");
	}}
    >
      <option value="" ?selected=${n === null}>${B(e, "code_policy.inherit")}</option>
      <option value="yes" ?selected=${n === !0}>${B(e, "code_policy.required")}</option>
      <option value="no" ?selected=${n === !1}>${B(e, "code_policy.not_required")}</option>
    </select>
  </label>`;
}
function Ke(e, t, n, r) {
	return D`
    ${Ge(e, "field.require_code_to_arm", t.require_code_to_arm, (e) => n("require_code_to_arm", e))}
    ${Ge(e, "field.require_code_to_disarm", t.require_code_to_disarm, (e) => n("require_code_to_disarm", e))}
    <p class="hint span">
      ${B(e, "code_policy.strictest")}
      ${r ? k : D` ${B(e, "code_policy.inert")}`}
    </p>
  `;
}
//#endregion
//#region src/panel/profile-picker.ts
function qe(e, t) {
	let n = e.areas.find((e) => e.id === t), r = e.scenarios.find((e) => n?.id && e.areas.includes(n.id) && e.response_profile_id), i = (t) => e.profiles?.find((e) => e.id === t), a = i(n?.response_profile_id);
	if (a) return {
		name: a.name,
		source: "area"
	};
	let o = i(r?.response_profile_id);
	if (o) return {
		name: o.name,
		source: "scenario"
	};
	let s = i(e.settings?.default_profile_id);
	return s ? {
		name: s.name,
		source: "default"
	} : {
		name: "",
		source: "none"
	};
}
function G(e, t, n, r) {
	let i = e.strings, a = e.config?.profiles ?? [];
	return D`<label class="field">
    <span class="lbl">${B(i, "field.response_profile_id")}</span>
    <select @change=${(e) => n(e.target.value || null)}>
      <option value="" ?selected=${!t}>${B(i, "profiles.inherit")}</option>
      ${a.map((e) => D`<option .value=${e.id ?? ""} ?selected=${e.id === t}>
          ${e.name}
        </option>`)}
    </select>
    ${r ? D`<span class="hint">${r}</span>` : k}
  </label>`;
}
function Je(e, t) {
	if (!e.config) return k;
	let { name: n, source: r } = qe(e.config, t), i = e.strings;
	return r === "none" ? D`<p class="hint">${B(i, "profiles.inherited_none")}</p>` : D`<p class="hint">
    ${B(i, "profiles.effective", { profile: n })} —
    ${B(i, `profiles.inherited_from_${r}`)}
  </p>`;
}
//#endregion
//#region src/panel/pages/areas.ts
var Ye = {
	name: "",
	ha_state_when_armed: "armed_away",
	default_entry_delay: 30,
	default_exit_delay: 30,
	response_profile_id: null,
	require_code_to_arm: null,
	require_code_to_disarm: null,
	is_perimeter: !1
}, Xe = class extends I {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 }
		};
	}
	_edit(e) {
		this._draft = e ? { ...e } : { ...Ye }, this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("area", this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("area", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = new Map(e.status.areas.map((e) => [e.id, e.state])), r = (t) => e.config.zones.filter((e) => e.area_id === t).length;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "areas.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${B(t, "areas.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${B(t, "field.name")}</th>
                <th>${B(t, "overview.status")}</th>
                <th>${B(t, "areas.zones")}</th>
                <th>${B(t, "field.default_entry_delay")}</th>
                <th>${B(t, "field.default_exit_delay")}</th>
                <th>${B(t, "field.ha_state_when_armed")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.areas.map((e) => {
			let i = n.get(e.id ?? "") ?? "disarmed";
			return D`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td><span class="state ${i}">${B(t, `state.${i}`)}</span></td>
                  <td>${r(e.id)}</td>
                  <td>${B(t, "common.seconds", { n: e.default_entry_delay })}</td>
                  <td>${B(t, "common.seconds", { n: e.default_exit_delay })}</td>
                  <td class="mono">${e.ha_state_when_armed}</td>
                </tr>`;
		})}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx.meta, [r, i] = n?.bounds.exit_delay ?? [0, 300], a = n?.bounds.entry_delay?.[1] ?? 300;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "areas.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.ha_state_when_armed")}</span>
              <select
                @change=${(e) => this._set("ha_state_when_armed", e.target.value)}
              >
                ${(n?.ha_states ?? []).map((n) => D`<option .value=${n} ?selected=${n === t.ha_state_when_armed}>
                      ${B(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${B(e, "areas.reports_as_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.default_entry_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${a}
                .value=${String(t.default_entry_delay)}
                @input=${(e) => this._set("default_entry_delay", Number(e.target.value))}
              />
              <span class="hint">${B(e, "areas.entry_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.default_exit_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.default_exit_delay)}
                @input=${(e) => this._set("default_exit_delay", Number(e.target.value))}
              />
              <span class="hint">${B(e, "areas.exit_hint")}</span>
            </label>
            ${G(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
            ${Ke(e, t, (e, t) => this._set(e, t), this.ctx.status.security.enforced)}
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.is_perimeter}
              @change=${(e) => this._set("is_perimeter", e.target.checked)}
            />
            <span>
              ${B(e, "field.is_perimeter")}
              <span class="hint">${B(e, "areas.perimeter_hint")}</span>
            </span>
          </label>
          ${Je(this.ctx, t.id ?? null)}
          ${this._problems.length ? D`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                </ul>
              </div>` : k}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${B(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${B(e, "common.cancel")}
            </button>
            ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${B(e, "common.delete")}
                </button>` : k}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [V, H];
	}
};
customElements.get("foyer-page-areas") || customElements.define("foyer-page-areas", Xe);
//#endregion
//#region src/panel/ha-targets.ts
function Ze(e, t) {
	let n = e.states[t];
	return String(n?.attributes?.friendly_name ?? t);
}
function K(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) t.has(n.id) || t.set(n.id, n);
	return [...t.values()].sort((e, t) => e.id.localeCompare(t.id));
}
function q(e, t) {
	return K(Object.values(e.states).filter((e) => t.includes(e.entity_id.split(".")[0])).map((t) => ({
		id: t.entity_id,
		name: Ze(e, t.entity_id)
	})));
}
function J(e) {
	let t = Object.keys(e.services?.notify ?? {}).filter((e) => e !== "send_message").map((e) => ({
		id: `notify.${e}`,
		name: `notify.${e}`
	}));
	return K([...q(e, ["notify"]), ...t]);
}
function Qe(e, t) {
	return K([...q(e, t.filter((e) => e !== "notify")), ...t.includes("notify") ? J(e) : []]);
}
function $e(e) {
	let t = q(e, ["sensor", "binary_sensor"]), n = (t) => e.states[t.id]?.attributes.device_class === "battery";
	return [...t.filter(n), ...t.filter((e) => !n(e))];
}
function et(e) {
	return Object.keys(e.services ?? {}).sort();
}
function tt(e, t) {
	return Object.keys(e.services?.[t] ?? {}).sort();
}
//#endregion
//#region src/panel/pages/zones.ts
var nt = /* @__PURE__ */ new Set(["event", "tag"]), rt = /* @__PURE__ */ new Set(["unavailable", "unknown"]);
function it(e) {
	return {
		name: "",
		entity_id: "",
		area_id: e,
		trigger: {
			kind: "state",
			states: []
		},
		type: "instant",
		channel: "intrusion",
		entry_mode: "instant",
		alarm_kind: "intrusion",
		always_on: !1,
		entry_delay: null,
		follows: [],
		arm_policy: "block",
		arm_hold_timeout: null,
		allow_arm_when_faulted: !1,
		bypassable: !0,
		supervision_timeout: null,
		battery_entity_id: null,
		enabled: !0,
		key: null,
		chime: !1,
		silent: !1,
		response_profile_id: null,
		cross_zone_id: null,
		cross_zone_window: 60,
		trigger_count: 1,
		trigger_window: 60
	};
}
function at(e) {
	return e.channel === "intrusion" ? e : {
		...e,
		chime: !1,
		cross_zone_id: null,
		trigger_count: 1,
		silent: !1
	};
}
var ot = (e, t) => JSON.stringify(e) === JSON.stringify(t), st = class extends I {
	constructor(...e) {
		super(...e), this._confirmed = !1, this._problems = [], this._busy = !1, this._filter = "", this._customState = "";
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_saved: { state: !0 },
			_proposal: { state: !0 },
			_confirmed: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_filter: { state: !0 },
			_customState: { state: !0 }
		};
	}
	_edit(e) {
		let t = this.ctx?.config?.areas[0]?.id ?? "";
		this._draft = e ? structuredClone(e) : it(t), this._saved = e, this._proposal = void 0, this._confirmed = !1, this._problems = [], e && this._propose(e.entity_id, !1);
	}
	_set(e, t) {
		this._draft && (this._draft = {
			...this._draft,
			[e]: t
		}, e === "trigger" && (this._confirmed = !1));
	}
	_applyType(e) {
		let t = this.ctx?.meta?.zone_types.find((t) => t.type === e)?.preset ?? {};
		if (!this._draft) return;
		let n = {
			...this._draft,
			...t,
			type: e
		};
		n.channel === "key" && !n.key && (n.key = {
			on_activate: "toggle",
			scenario_id: null,
			on_deactivate: "none"
		}), n.channel !== "key" && (n.key = null), n.arm_policy !== "arm_after_closing" && (n.arm_hold_timeout = null), n.entry_mode !== "follower" && (n.follows = []), n.always_on && (n.chime = !1), this._draft = at(n);
	}
	async _propose(e, t) {
		let n = this.ctx;
		if (!n || !e) return;
		let r = await n.hass.callWS({
			type: "foyer/zone/propose",
			entity_id: e
		});
		if (this._proposal = r, !t || !this._draft) return;
		let i = r.trigger_kind === "event" ? {
			kind: "event",
			event_type: e.startsWith("event.") ? r.proposed[0] ?? null : null
		} : r.trigger_kind === "numeric" ? {
			kind: "numeric",
			operator: "gt",
			value: 0,
			hysteresis: 0,
			attribute: null
		} : {
			kind: "state",
			states: [...r.proposed]
		};
		this._draft = {
			...this._draft,
			entity_id: e,
			name: this._draft.name || r.name
		}, this._set("trigger", i), r.zone_type && this._typeAvailable(r.zone_type) && this._applyType(r.zone_type);
	}
	_typeAvailable(e) {
		return this.ctx?.meta?.zone_types.find((t) => t.type === e)?.available ?? !1;
	}
	_triggerChanged() {
		return !this._saved || !ot(this._saved.trigger, this._draft?.trigger);
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("zone", this._draft, this._confirmed);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("zone", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.status.zones.map((e) => [e.id, e]));
		return e.config.areas.length ? D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "zones.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${B(t, "zones.add")}</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${B(t, "field.name")}</th>
                <th>${B(t, "field.entity_id")}</th>
                <th>${B(t, "field.area_id")}</th>
                <th>${B(t, "field.type")}</th>
                <th>${B(t, "field.arm_policy")}</th>
                <th>${B(t, "overview.status")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.zones.map((e) => D`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td class="mono">${e.entity_id}</td>
                  <td>${n.get(e.area_id) ?? ""}</td>
                  <td><span class="tag">${B(t, `zone_type.${e.type}`)}</span></td>
                  <td>${B(t, `arm_policy.${e.arm_policy}`)}</td>
                  <td>${this._health(t, r.get(e.id ?? ""))}</td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
    ` : D`<div class="card"><div class="empty">${B(t, "zones.no_areas")}</div></div>`;
	}
	_health(e, t) {
		if (!t) return k;
		if (!t.enabled) return D`<span class="state disabled">${B(e, "zone_status.disabled")}</span>`;
		if (t.fault) return D`<span class="state fault">${B(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) return D`<span class="state bypassed">${B(e, `bypass.${t.bypassed}`)}</span>`;
		let n = t.open ? "open" : "closed";
		return D`<span class="state ${n}">${B(e, `zone_status.${n}`)}</span>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "zones.new")}</h2>
        </div>
        <div class="card-bd">
          ${t.id ? k : this._renderEntityPicker(e, t)}
          ${t.entity_id ? D`
                ${this._renderTrigger(e, t)} ${this._renderProperties(e, t)}
                ${t.channel === "intrusion" && t.entry_mode === "follower" ? this._renderFollows(e, t) : k}
                ${t.channel === "intrusion" ? this._renderVerification(e, t) : k}
                ${t.channel === "key" ? this._renderKey(e, t) : k}
              ` : k}
          ${this._problems.length ? D`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                </ul>
              </div>` : k}
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !t.entity_id || this._triggerChanged() && !this._confirmed}
              @click=${this._save}
            >
              ${B(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${B(e, "common.cancel")}
            </button>
            ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${B(e, "common.delete")}
                </button>` : k}
          </div>
          ${this._triggerChanged() && !this._confirmed && t.entity_id ? D`<div class="hint">${B(e, "zones.confirm_first")}</div>` : k}
          ${n.status.areas.some((e) => e.id === t.area_id && e.state !== "disarmed") ? D`<div class="notice">${B(e, "zones.area_armed")}</div>` : k}
        </div>
      </div>
    `;
	}
	_renderEntityPicker(e, t) {
		let n = this.ctx, r = new Set(n.meta?.zone_domains ?? []), i = new Set(n.config?.zones.map((e) => e.entity_id)), a = this._filter.toLowerCase(), o = Object.values(n.hass.states).filter((e) => r.has(e.entity_id.split(".")[0])).filter((e) => {
			let t = String(e.attributes.friendly_name ?? "");
			return !a || e.entity_id.toLowerCase().includes(a) || t.toLowerCase().includes(a);
		}).sort((e, t) => e.entity_id.localeCompare(t.entity_id)).slice(0, 200);
		return D`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${B(e, "zones.search")}</span>
          <input
            .value=${this._filter}
            @input=${(e) => this._filter = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${B(e, "field.entity_id")}</span>
          <select
            @change=${(e) => this._propose(e.target.value, !0)}
          >
            <option value="" ?selected=${!t.entity_id}>${B(e, "zones.pick_entity")}</option>
            ${o.map((n) => D`<option
                .value=${n.entity_id}
                ?selected=${n.entity_id === t.entity_id}
              >
                ${B(e, i.has(n.entity_id) ? "zones.entity_used" : "zones.entity", {
			name: String(n.attributes.friendly_name ?? n.entity_id),
			entity: n.entity_id
		})}
              </option>`)}
          </select>
          <span class="hint">${B(e, "zones.entity_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderTrigger(e, t) {
		let n = this.ctx.hass.states[t.entity_id], r = n?.state ?? "unavailable", i = t.entity_id.split(".")[0], a = t.trigger;
		return D`
      <fieldset>
        <legend>${B(e, "zones.trigger_title")}</legend>
        <p class="hint">
          ${B(e, "zones.trigger_intro", {
			entity: String(n?.attributes.friendly_name ?? t.entity_id),
			state: r
		})}
          ${this._proposal?.device_class ? B(e, "zones.device_class", { device_class: this._proposal.device_class }) : k}
        </p>
        ${nt.has(i) ? this._renderEventTrigger(e, i, a) : D`
              <label class="field">
                <span class="lbl">${B(e, "zones.trigger_kind")}</span>
                <select
                  @change=${(e) => {
			let t = e.target.value;
			this._set("trigger", t === "numeric" ? {
				kind: "numeric",
				operator: "gt",
				value: 0,
				hysteresis: 0,
				attribute: null
			} : {
				kind: "state",
				states: []
			});
		}}
                >
                  <option value="state" ?selected=${a.kind === "state"}>
                    ${B(e, "zones.kind_state")}
                  </option>
                  <option value="numeric" ?selected=${a.kind === "numeric"}>
                    ${B(e, "zones.kind_numeric")}
                  </option>
                </select>
              </label>
              ${a.kind === "numeric" ? this._renderNumericTrigger(e, a) : a.kind === "state" ? this._renderStateTrigger(e, a.states, r) : k}
            `}
        <label class="check confirm">
          <input
            type="checkbox"
            .checked=${this._confirmed || !this._triggerChanged()}
            ?disabled=${!this._triggerChanged()}
            @change=${(e) => this._confirmed = e.target.checked}
          />
          <span>
            ${B(e, "zones.confirm")}
            <span class="hint">${B(e, "zones.confirm_hint")}</span>
          </span>
        </label>
      </fieldset>
    `;
	}
	_renderStateTrigger(e, t, n) {
		let r = /* @__PURE__ */ new Set([...this._proposal?.options ?? [], ...t]);
		rt.has(n) || r.add(n);
		let i = (e, n) => {
			let r = n ? [...t, e] : t.filter((t) => t !== e);
			this._set("trigger", {
				kind: "state",
				states: [...new Set(r)].sort()
			});
		};
		return D`
      <div class="states">
        ${[...r].map((r) => D`<label class="check">
            <input
              type="checkbox"
              .checked=${t.includes(r)}
              @change=${(e) => i(r, e.target.checked)}
            />
            <span class="mono">${r}</span>
            ${r === n ? D`<span class="tag">${B(e, "zones.now")}</span>` : k}
          </label>`)}
      </div>
      <div class="row">
        <label class="field">
          <span class="lbl">${B(e, "zones.other_state")}</span>
          <input
            .value=${this._customState}
            @input=${(e) => this._customState = e.target.value}
          />
        </label>
        <button
          class="btn"
          ?disabled=${!this._customState.trim()}
          @click=${() => {
			i(this._customState.trim(), !0), this._customState = "";
		}}
        >
          ${B(e, "zones.add_state")}
        </button>
      </div>
      <div class="hint">${B(e, "zones.state_hint")}</div>
    `;
	}
	_renderNumericTrigger(e, t) {
		let n = (e) => this._set("trigger", {
			...t,
			...e
		});
		return D`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${B(e, "zones.operator")}</span>
          <select
            @change=${(e) => n({ operator: e.target.value })}
          >
            ${[
			"gt",
			"lt",
			"eq"
		].map((n) => D`<option .value=${n} ?selected=${n === t.operator}>
                  ${B(e, `operator.${n}`)}
                </option>`)}
          </select>
        </label>
        <label class="field">
          <span class="lbl">${B(e, "zones.threshold")}</span>
          <input
            type="number"
            step="any"
            .value=${String(t.value)}
            @input=${(e) => n({ value: Number(e.target.value) })}
          />
        </label>
        <label class="field">
          <span class="lbl">${B(e, "zones.hysteresis")}</span>
          <input
            type="number"
            step="any"
            min="0"
            ?disabled=${t.operator === "eq"}
            .value=${String(t.hysteresis)}
            @input=${(e) => n({ hysteresis: Number(e.target.value) })}
          />
          <span class="hint">${B(e, "zones.hysteresis_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${B(e, "zones.attribute")}</span>
          <input
            .value=${t.attribute ?? ""}
            @input=${(e) => n({ attribute: e.target.value.trim() || null })}
          />
          <span class="hint">${B(e, "zones.attribute_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderEventTrigger(e, t, n) {
		if (t === "tag") return D`<p class="hint">${B(e, "zones.tag_hint")}</p>`;
		let r = n.kind === "event" ? n.event_type : null;
		return D`
      <label class="field">
        <span class="lbl">${B(e, "zones.event_type")}</span>
        <select
          @change=${(e) => this._set("trigger", {
			kind: "event",
			event_type: e.target.value || null
		})}
        >
          <option value="" ?selected=${!r}>${B(e, "zones.pick_event")}</option>
          ${(this._proposal?.options ?? []).map((e) => D`<option .value=${e} ?selected=${e === r}>${e}</option>`)}
        </select>
        <span class="hint">${B(e, "zones.event_hint")}</span>
      </label>
    `;
	}
	_renderProperties(e, t) {
		let n = this.ctx, r = n.meta, i = n.config?.areas.find((e) => e.id === t.area_id), a = t.channel === "intrusion", o = (n, r) => D`
      <label class="check">
        <input
          type="checkbox"
          .checked=${!!t[n]}
          @change=${(e) => this._set(n, e.target.checked)}
        />
        <span>
          ${B(e, `field.${n}`)}
          ${r ? D`<span class="hint">${B(e, r)}</span>` : k}
        </span>
      </label>
    `;
		return D`
      <fieldset>
        <legend>${B(e, "zones.properties_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${B(e, "field.name")}</span>
            <input
              .value=${t.name}
              @input=${(e) => this._set("name", e.target.value)}
            />
          </label>
          <label class="field">
            <span class="lbl">${B(e, "field.type")}</span>
            <select @change=${(e) => this._applyType(e.target.value)}>
              ${(r?.zone_types ?? []).map((n) => D`<option
                  .value=${n.type}
                  ?selected=${n.type === t.type}
                  ?disabled=${!n.available}
                >
                  ${B(e, n.available ? `zone_type.${n.type}` : "zones.type_unavailable", { type: B(e, `zone_type.${n.type}`) })}
                </option>`)}
            </select>
            <span class="hint">${B(e, "zones.type_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${B(e, "field.area_id")}</span>
            <select
              @change=${(e) => this._set("area_id", e.target.value)}
            >
              ${(n.config?.areas ?? []).map((e) => D`<option .value=${e.id ?? ""} ?selected=${e.id === t.area_id}>
                    ${e.name}
                  </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${B(e, "field.channel")}</span>
            <select
              @change=${(e) => {
			let n = e.target.value;
			this._draft = at({
				...t,
				channel: n,
				key: n === "key" ? t.key ?? {
					on_activate: "toggle",
					scenario_id: null,
					on_deactivate: "none"
				} : null,
				...n === "technical" ? {
					always_on: !0,
					entry_mode: "instant"
				} : {}
			});
		}}
            >
              ${[
			"intrusion",
			"key",
			"technical"
		].map((n) => D`<option .value=${n} ?selected=${n === t.channel}>
                    ${B(e, `channel.${n}`)}
                  </option>`)}
            </select>
          </label>
          ${a ? D`
                <label class="field">
                  <span class="lbl">${B(e, "field.entry_mode")}</span>
                  <select
                    ?disabled=${t.always_on}
                    @change=${(e) => {
			let t = e.target.value;
			this._set("entry_mode", t), t !== "follower" && this._set("follows", []);
		}}
                  >
                    ${[
			"instant",
			"delayed",
			"follower"
		].map((n) => D`<option .value=${n} ?selected=${n === t.entry_mode}>
                          ${B(e, `entry_mode.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${B(e, `entry_mode_hint.${t.entry_mode}`)}</span>
                </label>
                <label class="field">
                  <span class="lbl">${B(e, "field.entry_delay")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${r?.bounds.entry_delay?.[1] ?? 300}
                    placeholder=${B(e, "zones.inherit_seconds", { n: i?.default_entry_delay ?? 30 })}
                    .value=${t.entry_delay == null ? "" : String(t.entry_delay)}
                    @input=${(e) => this._set("entry_delay", W(e.target.value))}
                  />
                  <span class="hint">${B(e, "zones.entry_delay_hint")}</span>
                </label>
                <label class="field">
                  <span class="lbl">${B(e, "field.alarm_kind")}</span>
                  <select
                    @change=${(e) => this._set("alarm_kind", e.target.value)}
                  >
                    ${[
			"intrusion",
			"tamper",
			"panic"
		].map((n) => D`<option .value=${n} ?selected=${n === t.alarm_kind}>
                          ${B(e, `alarm_kind.${n}`)}
                        </option>`)}
                  </select>
                </label>
                <label class="field">
                  <span class="lbl">${B(e, "field.arm_policy")}</span>
                  <select
                    @change=${(e) => {
			let t = e.target.value;
			this._set("arm_policy", t), t !== "arm_after_closing" && this._set("arm_hold_timeout", null);
		}}
                  >
                    ${[
			"block",
			"auto_bypass",
			"arm_after_closing",
			"ignore"
		].map((n) => D`<option .value=${n} ?selected=${n === t.arm_policy}>
                          ${B(e, `arm_policy.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${B(e, `arm_policy_hint.${t.arm_policy}`)}</span>
                </label>
                ${t.arm_policy === "arm_after_closing" ? D`<label class="field">
                      <span class="lbl">${B(e, "field.arm_hold_timeout")}</span>
                      <input
                        type="number"
                        min=${r?.bounds.arm_hold_timeout?.[0] ?? 60}
                        max=${r?.bounds.arm_hold_timeout?.[1] ?? 1800}
                        placeholder=${B(e, "zones.inherit_seconds", { n: n.config?.settings.arm_hold_timeout ?? 300 })}
                        .value=${t.arm_hold_timeout == null ? "" : String(t.arm_hold_timeout)}
                        @input=${(e) => this._set("arm_hold_timeout", W(e.target.value))}
                      />
                      <span class="hint">${B(e, "zones.hold_hint")}</span>
                    </label>` : k}
              ` : k}
          <label class="field">
            <span class="lbl">${B(e, "field.supervision_timeout")}</span>
            <input
              type="number"
              min=${r?.bounds.supervision_timeout?.[0] ?? 60}
              placeholder=${B(e, "zones.off")}
              .value=${t.supervision_timeout == null ? "" : String(t.supervision_timeout)}
              @input=${(e) => this._set("supervision_timeout", W(e.target.value))}
            />
            <span class="hint">${B(e, "zones.supervision_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${B(e, "field.battery_entity_id")}</span>
            <select
              @change=${(e) => this._set("battery_entity_id", e.target.value || null)}
            >
              <option value="" ?selected=${!t.battery_entity_id}>
                ${B(e, "zones.no_battery")}
              </option>
              ${$e(n.hass).map((e) => D`<option
                  .value=${e.id}
                  ?selected=${e.id === t.battery_entity_id}
                >
                  ${e.name}
                </option>`)}
            </select>
            <span class="hint">${B(e, "zones.battery_hint")}</span>
          </label>
        </div>
        <div class="checks">
          ${a ? o("always_on", "zones.always_on_hint") : k}
          ${a ? o("bypassable", "zones.bypassable_hint") : k}
          ${a && !t.always_on ? o("chime", "zones.chime_hint") : k}
          ${a ? o("silent", "zones.silent_hint") : k}
          ${o("allow_arm_when_faulted", "zones.allow_faulted_hint")}
          ${o("enabled", "zones.enabled_hint")}
        </div>
        ${G(n, t.response_profile_id, (e) => this._set("response_profile_id", e), B(e, "profiles.zone_hint"))}
        ${t.channel === "technical" ? D`<p class="hint">${B(e, "zones.technical_hint")}</p>
              <div class="notice fire" role="note">${B(e, "zones.fire_statement")}</div>` : k}
      </fieldset>
    `;
	}
	_renderVerification(e, t) {
		let n = this.ctx, r = n.meta, [i, a] = r?.bounds.window ?? [1, 3600], o = n.config?.groups.find((e) => e.members.includes(t.id ?? "")), s = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.members.forEach((e) => s.add(e));
		for (let e of n.config?.zones ?? []) e.id && e.cross_zone_id && e.id !== t.id && e.cross_zone_id !== t.id && (s.add(e.id), s.add(e.cross_zone_id));
		let c = (n.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && (!s.has(e.id ?? "") || e.id === t.cross_zone_id)), l = new Map(n.config?.areas.map((e) => [e.id, e.name])), u = (e) => (t) => {
			let n = W(t.target.value);
			this._set(e, n ?? (e === "trigger_count" ? 1 : 60));
		};
		return D`
      <fieldset>
        <legend>${B(e, "zones.verification_title")}</legend>
        ${o ? D`<p class="notice">${B(e, "zones.in_group", { group: o.name })}</p>` : D`<div class="grid-form">
              <label class="field">
                <span class="lbl">${B(e, "field.cross_zone_id")}</span>
                <select
                  @change=${(e) => this._set("cross_zone_id", e.target.value || null)}
                >
                  <option value="" ?selected=${!t.cross_zone_id}>
                    ${B(e, "zones.no_cross_zone")}
                  </option>
                  ${c.map((n) => D`<option .value=${n.id ?? ""} ?selected=${n.id === t.cross_zone_id}>
                      ${B(e, "zones.entity", {
			name: n.name,
			entity: l.get(n.area_id) ?? n.area_id
		})}
                    </option>`)}
                </select>
                <span class="hint">${B(e, "zones.cross_zone_hint")}</span>
              </label>
              ${t.cross_zone_id ? D`<label class="field">
                    <span class="lbl">${B(e, "field.cross_zone_window")}</span>
                    <input
                      type="number"
                      min=${i}
                      max=${a}
                      .value=${String(t.cross_zone_window)}
                      @input=${u("cross_zone_window")}
                    />
                    <span class="hint">${B(e, "groups.window_hint")}</span>
                  </label>` : k}
            </div>`}
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${B(e, "field.trigger_count")}</span>
            <input
              type="number"
              min="1"
              max=${r?.bounds.trigger_count?.[1] ?? 10}
              .value=${String(t.trigger_count)}
              @input=${u("trigger_count")}
            />
            <span class="hint">${B(e, "zones.trigger_count_hint")}</span>
          </label>
          ${t.trigger_count > 1 ? D`<label class="field">
                <span class="lbl">${B(e, "field.trigger_window")}</span>
                <input
                  type="number"
                  min=${i}
                  max=${a}
                  .value=${String(t.trigger_window)}
                  @input=${u("trigger_window")}
                />
                <span class="hint">${B(e, "groups.window_hint")}</span>
              </label>` : k}
        </div>
      </fieldset>
    `;
	}
	_renderFollows(e, t) {
		let n = new Map(this.ctx?.config?.areas.map((e) => [e.id, e.name])), r = (this.ctx?.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && e.entry_mode === "delayed"), i = (e, n) => this._set("follows", n ? [.../* @__PURE__ */ new Set([...t.follows, e])] : t.follows.filter((t) => t !== e));
		return D`
      <fieldset>
        <legend>${B(e, "field.follows")}</legend>
        ${r.length ? r.map((r) => D`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.follows.includes(r.id ?? "")}
                  @change=${(e) => i(r.id ?? "", e.target.checked)}
                />
                <span>
                  ${B(e, "zones.entity", {
			name: r.name,
			entity: n.get(r.area_id) ?? r.area_id
		})}
                </span>
              </label>`) : D`<p class="hint">${B(e, "zones.no_delayed_zones")}</p>`}
        <p class="hint">${B(e, "zones.follows_hint")}</p>
      </fieldset>
    `;
	}
	_renderKey(e, t) {
		let n = t.key ?? {
			on_activate: "toggle",
			scenario_id: null,
			on_deactivate: "none"
		}, r = (e) => this._set("key", {
			...n,
			...e
		}), i = this.ctx?.config?.scenarios ?? [];
		return D`
      <fieldset>
        <legend>${B(e, "zones.key_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${B(e, "field.on_activate")}</span>
            <select
              @change=${(e) => r({ on_activate: e.target.value })}
            >
              ${[
			"arm",
			"disarm",
			"toggle"
		].map((t) => D`<option .value=${t} ?selected=${t === n.on_activate}>
                    ${B(e, `key_command.${t}`)}
                  </option>`)}
            </select>
          </label>
          ${n.on_activate === "disarm" ? k : D`<label class="field">
                <span class="lbl">${B(e, "field.scenario_id")}</span>
                <select
                  @change=${(e) => r({ scenario_id: e.target.value || null })}
                >
                  <option value="" ?selected=${!n.scenario_id}>
                    ${B(e, "zones.pick_scenario")}
                  </option>
                  ${i.map((e) => D`<option .value=${e.id ?? ""} ?selected=${e.id === n.scenario_id}>
                        ${e.name}
                      </option>`)}
                </select>
              </label>`}
          <label class="field">
            <span class="lbl">${B(e, "field.on_deactivate")}</span>
            <select
              @change=${(e) => r({ on_deactivate: e.target.value })}
            >
              ${["none", "disarm"].map((t) => D`<option .value=${t} ?selected=${t === n.on_deactivate}>
                    ${B(e, `key_release.${t}`)}
                  </option>`)}
            </select>
          </label>
        </div>
        <p class="hint">${B(e, "zones.key_hint")}</p>
      </fieldset>
    `;
	}
	static {
		this.styles = [
			V,
			H,
			o`
      .states {
        display: flex;
        flex-wrap: wrap;
        gap: 4px 18px;
        margin: 10px 0;
      }
      .row {
        display: flex;
        align-items: flex-end;
        gap: 8px;
        flex-wrap: wrap;
      }
      .checks {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 0 16px;
        margin-top: 12px;
      }
      .notice.fire {
        border-left-color: var(--error-color, #d32f2f);
        font-weight: 500;
      }
      .confirm {
        margin-top: 12px;
        padding: 10px 12px;
        border-radius: 8px;
        background: var(--secondary-background-color);
        font-weight: 500;
      }
    `
		];
	}
};
customElements.get("foyer-page-zones") || customElements.define("foyer-page-zones", st);
//#endregion
//#region src/panel/pages/scenarios.ts
var ct = {
	name: "",
	areas: [],
	ha_master_state: "armed_away",
	icon: null,
	exit_delay_override: null,
	siren_duration_override: null,
	response_profile_id: null,
	require_code_to_arm: null,
	require_code_to_disarm: null,
	allowed_user_ids: null
}, lt = class extends I {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 }
		};
	}
	_edit(e) {
		this._draft = e ? structuredClone(e) : {
			...ct,
			areas: []
		}, this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("scenario", this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("scenario", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = e.config.scenarios.map((e) => e.ha_master_state);
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "scenarios.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${B(t, "scenarios.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${B(t, "field.name")}</th>
                <th>${B(t, "field.areas")}</th>
                <th>${B(t, "field.ha_master_state")}</th>
                <th>${B(t, "field.exit_delay_override")}</th>
                <th>${B(t, "field.siren_duration_override")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.scenarios.map((i) => D`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === i.id ? "true" : "false"}
                  @click=${() => this._edit(i)}
                >
                  <td>
                    <strong>${i.name}</strong>
                    ${i.id === e.status.active_scenario_id ? D`<span class="state armed">${B(t, "scenarios.active")}</span>` : k}
                  </td>
                  <td>
                    ${i.areas.map((e) => D`<span class="tag">${n.get(e) ?? e}</span>`)}
                  </td>
                  <td>
                    <span class="mono">${i.ha_master_state}</span>
                    ${r.filter((e) => e === i.ha_master_state).length > 1 ? D`<div class="hint">${B(t, "scenarios.shared_mode")}</div>` : k}
                  </td>
                  <td>
                    ${i.exit_delay_override == null ? B(t, "scenarios.area_default") : B(t, "common.seconds", { n: i.exit_delay_override })}
                  </td>
                  <td>
                    ${i.siren_duration_override == null ? B(t, "scenarios.global_default") : B(t, "common.seconds", { n: i.siren_duration_override })}
                  </td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.meta, i = (e, n) => this._set("areas", n ? [...t.areas, e] : t.areas.filter((t) => t !== e));
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "scenarios.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.ha_master_state")}</span>
              <select
                @change=${(e) => this._set("ha_master_state", e.target.value)}
              >
                ${(r?.ha_states ?? []).map((n) => D`<option .value=${n} ?selected=${n === t.ha_master_state}>
                      ${B(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${B(e, "scenarios.mode_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.exit_delay_override")}</span>
              <input
                type="number"
                min="0"
                max=${r?.bounds.exit_delay?.[1] ?? 300}
                placeholder=${B(e, "scenarios.area_default")}
                .value=${t.exit_delay_override == null ? "" : String(t.exit_delay_override)}
                @input=${(e) => this._set("exit_delay_override", W(e.target.value))}
              />
              <span class="hint">${B(e, "scenarios.exit_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.siren_duration_override")}</span>
              <input
                type="number"
                min="1"
                max=${r?.bounds.siren_duration?.[1] ?? 900}
                placeholder=${B(e, "scenarios.global_seconds", { n: n.config?.settings.siren_duration ?? 180 })}
                .value=${t.siren_duration_override == null ? "" : String(t.siren_duration_override)}
                @input=${(e) => this._set("siren_duration_override", W(e.target.value))}
              />
              <span class="hint">${B(e, "scenarios.siren_hint")}</span>
            </label>
            ${G(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
          </div>
          <fieldset>
            <legend>${B(e, "field.areas")}</legend>
            ${(n.config?.areas ?? []).map((e) => D`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.areas.includes(e.id ?? "")}
                  @change=${(t) => i(e.id ?? "", t.target.checked)}
                />
                <span>${e.name}</span>
              </label>`)}
            <p class="hint">${B(e, "scenarios.areas_hint")}</p>
          </fieldset>
          ${this._problems.length ? D`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                </ul>
              </div>` : k}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${B(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${B(e, "common.cancel")}
            </button>
            ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${B(e, "common.delete")}
                </button>` : k}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			V,
			H,
			o`
      td .state {
        margin-left: 8px;
      }
    `
		];
	}
};
customElements.get("foyer-page-scenarios") || customElements.define("foyer-page-scenarios", lt);
//#endregion
//#region src/panel/pages/profiles.ts
var ut = {
	alarm: [
		"entry_started",
		"triggered",
		"siren_cutoff",
		"incident_opened",
		"incident_joined",
		"incident_acknowledged",
		"incident_closed",
		"verification_pending",
		"verification_satisfied",
		"verification_expired",
		"technical_raised",
		"technical_acknowledged",
		"technical_cleared"
	],
	state: [
		"armed",
		"disarmed",
		"arm_failed",
		"forced_arm",
		"zone_bypassed",
		"zone_rejoined",
		"code_rejected",
		"lockout",
		"chime_switched"
	],
	system: [
		"zone_fault",
		"low_battery",
		"ha_restarted",
		"walk_test_started",
		"walk_test_ended",
		"escalation_exhausted",
		"chime"
	]
}, dt = ["companion", "telegram"], ft = ["notify", "persistent_notification"], pt = [
	"siren",
	"light",
	"switch"
], mt = [
	"camera",
	"scene",
	"tts"
];
function ht(e) {
	let t = {};
	return e === "switch" && (t.state = "on"), e === "camera" && (t.mode = "snapshot"), e === "delay" && (t.seconds = 30), (e === "notify" || e === "tts") && (t.message = "{{ zone }}"), e === "notify" && (t.attachment = "companion"), {
		kind: e,
		moments: [],
		name: "",
		params: t,
		conditions: [],
		condition_mode: "all",
		enabled: !0,
		escalation_offset: null
	};
}
function gt(e) {
	let t = e.params.contacts;
	return Array.isArray(t) ? t.map((e) => typeof e == "string" ? {
		contact_id: e,
		channel_id: null
	} : e) : [];
}
var _t = class extends I {
	constructor(...e) {
		super(...e), this._open = -1, this._filters = {}, this._problems = [], this._busy = !1, this._tested = {};
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_open: { state: !0 },
			_filters: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_tested: { state: !0 },
			_confirming: { state: !0 }
		};
	}
	_edit(e) {
		this._draft = e ? structuredClone(e) : {
			name: "",
			severity: 1,
			actions: []
		}, this._open = -1, this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	_setAction(e, t) {
		if (!this._draft) return;
		let n = this._draft.actions.map((n, r) => r === e ? {
			...n,
			...t
		} : n);
		this._draft = {
			...this._draft,
			actions: n
		};
	}
	_setParam(e, t, n) {
		let r = this._draft?.actions[e];
		if (!r) return;
		let i = { ...r.params };
		n === null || n === "" ? delete i[t] : i[t] = n, this._setAction(e, { params: i });
	}
	_addAction(e) {
		this._draft && (this._draft = {
			...this._draft,
			actions: [...this._draft.actions, ht(e)]
		}, this._open = this._draft.actions.length - 1);
	}
	_removeAction(e) {
		if (!this._draft) return;
		let t = this._draft.actions.filter((t, n) => n !== e);
		this._draft = {
			...this._draft,
			actions: t
		}, this._open = -1;
	}
	_moveAction(e, t) {
		if (!this._draft) return;
		let n = [...this._draft.actions], r = e + t;
		r < 0 || r >= n.length || ([n[e], n[r]] = [n[r], n[e]], this._draft = {
			...this._draft,
			actions: n
		}, this._open = r);
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("profile", this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("profile", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = e.config.profiles ?? [];
		return D`
      <p class="page-intro">${B(t, "profiles.intro")}</p>
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "profiles.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${B(t, "profiles.add")}</button>
        </div>
        ${n.length ? D`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${B(t, "field.name")}</th>
                      <th>${B(t, "field.actions")}</th>
                      <th>${B(t, "field.severity")}</th>
                      <th>${B(t, "profiles.used_by")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${n.map((e) => D`<tr
                          class="clickable"
                          aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                          @click=${() => this._edit(e)}
                        >
                          <td><strong>${e.name}</strong></td>
                          <td>
                            ${e.actions.length ? e.actions.map((e) => D`<span class="tag"
                                        >${B(t, `action_kind.${e.kind}`)}</span
                                      > `) : D`<span class="muted">${B(t, "profiles.no_actions")}</span>`}
                          </td>
                          <td>${e.severity}</td>
                          <td class="muted">${this._usedBy(t, e)}</td>
                        </tr>`)}
                  </tbody>
                </table>
              </div>` : D`<div class="empty">${B(t, "profiles.none")}</div>`}
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
    `;
	}
	_usedBy(e, t) {
		let n = this.ctx.config, r = [];
		n.settings.default_profile_id === t.id && r.push(B(e, "profiles.used_default")), n.settings.technical_profile_id === t.id && r.push(B(e, "profiles.used_technical"));
		for (let e of [
			n.areas,
			n.zones,
			n.scenarios,
			n.groups
		]) for (let n of e) n.response_profile_id === t.id && r.push(n.name);
		return r.length ? r.join(", ") : B(e, "profiles.unused");
	}
	_renderEditor(e, t) {
		let n = this.ctx?.meta?.bounds.severity ?? [1, 10];
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "profiles.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.severity")}</span>
              <input
                type="number"
                min=${n[0]}
                max=${n[1]}
                .value=${String(t.severity)}
                @input=${(e) => this._set("severity", W(e.target.value) ?? 1)}
              />
              <span class="hint">${B(e, "profiles.severity_hint")}</span>
            </label>
          </div>

          <div class="actions-list">
            ${t.actions.map((t, n) => this._renderAction(e, t, n))}
          </div>
          ${t.actions.length ? k : D`<p class="hint">${B(e, "profiles.no_actions")}</p>`}

          <div class="add-action">
            <label class="field">
              <span class="lbl">${B(e, "profiles.add_action")}</span>
              <select
                .value=${""}
                @change=${(e) => {
			let t = e.target;
			t.value && this._addAction(t.value), t.value = "";
		}}
              >
                <option value=""></option>
                ${(this.ctx?.meta?.action_kinds ?? []).map((t) => D`<option .value=${t}>${B(e, `action_kind.${t}`)}</option>`)}
              </select>
            </label>
          </div>
          <p class="hint">${B(e, "profiles.escalation_later")}</p>

          ${this._problems.length ? D`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                  </ul>
                </div>` : k}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${B(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${B(e, "common.cancel")}
            </button>
            ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                    ${B(e, "common.delete")}
                  </button>` : k}
          </div>
        </div>
      </div>
    `;
	}
	_renderContacts(e, t, n) {
		let r = this.ctx?.config?.contacts ?? [], i = gt(t);
		if (!r.length) return D`<span class="hint">${B(e, "profiles.no_contacts")}</span>`;
		let a = (e) => {
			this._setParam(n, "contacts", e.length ? e : null), e.length && this._setParam(n, "service", null);
		};
		return D`<div class="field">
      <span class="lbl">${B(e, "field.contacts")}</span>
      ${r.map((t) => {
			let n = i.find((e) => e.contact_id === t.id);
			return D`<div class="contact-row">
          <label class="check">
            <input
              type="checkbox"
              .checked=${n !== void 0}
              @change=${(e) => a(e.target.checked ? [...i, {
				contact_id: t.id,
				channel_id: null
			}] : i.filter((e) => e.contact_id !== t.id))}
            />
            <span>${t.name}</span>
          </label>
          ${n ? D`<select
                @change=${(e) => a(i.map((n) => n.contact_id === t.id ? {
				...n,
				channel_id: e.target.value || null
			} : n))}
              >
                <option value="" ?selected=${!n.channel_id}>
                  ${B(e, "profiles.highest_channel")}
                </option>
                ${t.channels.map((t) => D`<option
                    .value=${t.id ?? ""}
                    ?selected=${t.id === n.channel_id}
                  >
                    ${B(e, `channel_kind.${t.kind}`)} · ${t.service}
                  </option>`)}
              </select>` : k}
        </div>`;
		})}
      <span class="hint">${B(e, "profiles.contacts_hint")}</span>
    </div>`;
	}
	_renderEscalation(e, t, n) {
		let r = this.ctx?.meta?.escalation_moments ?? [];
		if (!ft.includes(t.kind)) return k;
		if (!t.moments.length || !t.moments.every((e) => r.includes(e))) return t.escalation_offset === null ? k : D`<span class="hint">${B(e, "profiles.escalation_moment_hint")}</span>`;
		let i = this.ctx?.meta?.bounds.escalation_offset ?? [0, 3600];
		return D`<label class="field">
      <span class="lbl">${B(e, "field.escalation_offset")}</span>
      <input
        type="number"
        min=${i[0]}
        max=${i[1]}
        .value=${t.escalation_offset === null ? "" : String(t.escalation_offset)}
        @input=${(e) => {
			let t = e.target.value;
			this._setAction(n, { escalation_offset: t === "" ? null : Number(t) });
		}}
      />
      <span class="hint">${B(e, "profiles.escalation_hint")}</span>
    </label>`;
	}
	_renderAction(e, t, n) {
		let r = this._open === n;
		return D`
      <div class="action" ?data-open=${r}>
        <button class="action-hd" @click=${() => this._open = r ? -1 : n}>
          <span class="tag">${B(e, `action_kind.${t.kind}`)}</span>
          <span class="summary">${this._summary(e, t)}</span>
          <span class="moments">${this._momentSummary(e, t)}</span>
          ${t.conditions.length ? D`<span class="cond">${t.conditions.length}</span>` : k}
        </button>
        ${r ? D`<div class="action-bd">
                ${this._renderParams(e, t, n)} ${this._renderMoments(e, t, n)}
                ${this._renderEscalation(e, t, n)}
                ${this._renderConditions(e, t, n)}
                <div class="actions">
                  <button class="btn" @click=${() => this._moveAction(n, -1)}>&uarr;</button>
                  <button class="btn" @click=${() => this._moveAction(n, 1)}>&darr;</button>
                  ${this._renderTestButton(e, t)}
                  <button class="btn danger" @click=${() => this._removeAction(n)}>
                    ${B(e, "profiles.delete_action")}
                  </button>
                </div>
              </div>` : k}
      </div>
    `;
	}
	_renderTestButton(e, t) {
		if (t.kind === "delay" || !t.id || !this._draft?.id) return k;
		let n = t.id, r = this._tested[n];
		return this._confirming === n ? D`
        <button
          class="btn primary"
          ?disabled=${this._busy}
          @click=${() => void this._testAction(t)}
        >
          ${B(e, "action_test.confirm_short")}
        </button>
        <button class="btn" @click=${() => this._confirming = void 0}>
          ${B(e, "common.cancel")}
        </button>
      ` : D`
      <button class="btn" ?disabled=${this._busy} @click=${() => this._confirming = n}>
        ${B(e, "action_test.test")}
      </button>
      ${r ? D`<span class="state ${r.ok ? "closed" : "fault"}" title=${r.error ?? ""}>
            ${B(e, r.ok ? "action_test.ok" : "action_test.failed")}
          </span>` : k}
    `;
	}
	async _testAction(e) {
		let t = this.ctx;
		if (t && e.id && this._draft?.id) {
			this._busy = !0, this._confirming = void 0;
			try {
				let n = await t.testAction({
					profile_id: this._draft.id,
					action_id: e.id
				});
				this._tested = {
					...this._tested,
					[e.id]: {
						ok: n.success,
						error: n.error ?? n.reason ?? void 0
					}
				};
			} finally {
				this._busy = !1;
			}
		}
	}
	_momentSummary(e, t) {
		let n = t.moments.map((t) => B(e, `moment.${t}`));
		return n.length ? n.length <= 3 ? n.join(", ") : B(e, "profiles.moments_more", {
			moments: n.slice(0, 2).join(", "),
			count: n.length - 2
		}) : B(e, "profiles.no_moments");
	}
	_summary(e, t) {
		let n = t.params;
		if (t.kind === "delay") return `${n.seconds ?? 0} s`;
		if (t.kind === "call_service") return `${n.domain ?? ""}.${n.service ?? ""}`;
		if (t.kind === "notify") return String(n.service ?? "");
		if (t.kind === "persistent_notification") return String(n.message ?? B(e, "profiles.inherit"));
		let r = n.entity_ids ?? n.entity_id ?? "";
		return Array.isArray(r) ? r.join(", ") : String(r);
	}
	_entities(e) {
		return q(this.ctx.hass, e);
	}
	_suggested(e, t, n, r, i, a) {
		let o = `foyer-${r}-${n}`;
		return D`<label class="field">
      <span class="lbl">${B(e, `field.${r}`)}</span>
      <input
        list=${o}
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      <datalist id=${o}>
        ${i.map((e) => D`<option .value=${e.id}>
            ${e.name === e.id ? e.id : `${e.name} · ${e.id}`}
          </option>`)}
      </datalist>
      <span class="hint">${a ?? B(e, "profiles.pick_or_type")}</span>
    </label>`;
	}
	_text(e, t, n, r, i) {
		return D`<label class="field">
      <span class="lbl">${B(e, `field.${r}`)}</span>
      <input
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      ${i ? D`<span class="hint">${i}</span>` : k}
    </label>`;
	}
	_number(e, t, n, r, i) {
		return D`<label class="field">
      <span class="lbl">${B(e, `field.${r}`)}</span>
      <input
        type="number"
        .value=${t.params[r] == null ? "" : String(t.params[r])}
        @input=${(e) => this._setParam(n, r, W(e.target.value))}
      />
      ${i ? D`<span class="hint">${i}</span>` : k}
    </label>`;
	}
	_picker(e, t, n, r, i, a) {
		let o = this._entities(i), s = t.params[r], c = new Set(Array.isArray(s) ? s : s ? [String(s)] : []);
		for (let e of c) o.some((t) => t.id === e) || o.push({
			id: e,
			name: e
		});
		if (!a) return D`<label class="field">
        <span class="lbl">${B(e, `field.${r}`)}</span>
        <select
          @change=${(e) => this._setParam(n, r, e.target.value || null)}
        >
          <option value=""></option>
          ${o.map((e) => D`<option .value=${e.id} ?selected=${c.has(e.id)}>${e.name}</option>`)}
        </select>
      </label>`;
		let l = `${n}:${r}`, u = (this._filters[l] ?? "").toLowerCase().split(/\s+/).filter(Boolean), d = o.filter((e) => {
			if (c.has(e.id)) return !0;
			let t = `${e.name} ${e.id}`.toLowerCase();
			return u.every((e) => t.includes(e));
		});
		return D`<fieldset class="entities wide">
      <legend>${B(e, `field.${r}`)}</legend>
      ${o.length > 8 ? D`<input
            class="filter"
            type="search"
            .value=${this._filters[l] ?? ""}
            placeholder=${B(e, "profiles.filter")}
            @input=${(e) => {
			this._filters = {
				...this._filters,
				[l]: e.target.value
			};
		}}
          />` : k}
      <div class="entity-list">
        ${d.map((t) => D`<label class="check">
            <input
              type="checkbox"
              .checked=${c.has(t.id)}
              @change=${(e) => {
			let i = e.target.checked, a = new Set(c);
			i ? a.add(t.id) : a.delete(t.id), this._setParam(n, r, [...a]);
		}}
            />
            <span>${B(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}</span>
          </label>`)}
        ${d.length ? k : D`<p class="hint">${B(e, "profiles.no_match")}</p>`}
      </div>
    </fieldset>`;
	}
	_renderParams(e, t, n) {
		let r = this.ctx?.meta?.action_domains[t.kind] ?? [], i = B(e, "profiles.message_hint", { variables: (this.ctx?.meta?.template_variables ?? []).map((e) => `{{ ${e} }}`).join(" ") }), a = [];
		switch (pt.includes(t.kind) && a.push(this._picker(e, t, n, "entity_ids", r, !0)), mt.includes(t.kind) && a.push(this._picker(e, t, n, "entity_id", r, !1)), t.kind) {
			case "notify":
				a.push(this._renderContacts(e, t, n)), gt(t).length || a.push(this._suggested(e, t, n, "service", J(this.ctx.hass), B(e, "profiles.notify_hint"))), a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i)), a.push(this._picker(e, t, n, "camera_entity_id", ["camera"], !1)), t.params.camera_entity_id && (a.push(this._select(e, t, n, "attachment", dt, (t) => B(e, `attachment.${t}`))), a.push(D`<span class="hint"
              >${B(e, t.params.attachment === "telegram" ? "profiles.attach_hint_telegram" : "profiles.attach_hint")}</span
            >`));
				break;
			case "persistent_notification":
				a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i));
				break;
			case "siren":
				a.push(this._number(e, t, n, "duration", B(e, "profiles.siren_duration_hint"))), a.push(this._renderTone(e, t, n));
				break;
			case "light":
				a.push(this._number(e, t, n, "brightness")), a.push(this._select(e, t, n, "flash", [
					"",
					"short",
					"long"
				], (e) => e || "—"));
				break;
			case "camera":
				a.push(this._select(e, t, n, "mode", ["snapshot", "record"], (t) => B(e, `camera_mode.${t}`))), a.push(this._number(e, t, n, "duration", B(e, "profiles.camera_hint")));
				break;
			case "switch":
				a.push(this._select(e, t, n, "state", ["on", "off"], (t) => B(e, `on_off.${t}`))), a.push(this._number(e, t, n, "revert_after", B(e, "profiles.revert_hint")));
				break;
			case "tts":
				a.push(this._picker(e, t, n, "media_player_entity_ids", ["media_player"], !0)), a.push(this._text(e, t, n, "message", i));
				break;
			case "call_service": {
				let r = String(t.params.domain ?? "");
				a.push(this._suggested(e, t, n, "domain", et(this.ctx.hass).map((e) => ({
					id: e,
					name: e
				})))), a.push(this._suggested(e, t, n, "service", tt(this.ctx.hass, r).map((e) => ({
					id: e,
					name: e
				})))), a.push(this._json(e, t, n));
				break;
			}
			case "delay": a.push(this._number(e, t, n, "seconds", B(e, "profiles.delay_hint")));
		}
		return D`<div class="grid-form">${a}</div>`;
	}
	_renderTone(e, t, n) {
		let r = t.params.entity_ids, i = Array.isArray(r) ? r : [], a = /* @__PURE__ */ new Set();
		for (let e of i) {
			let t = this.ctx.hass.states[e]?.attributes?.available_tones;
			Array.isArray(t) ? t.forEach((e) => a.add(String(e))) : t && typeof t == "object" && Object.keys(t).forEach((e) => a.add(e));
		}
		return a.size ? this._select(e, t, n, "tone", ["", ...[...a].sort()], (t) => t || B(e, "profiles.default_tone")) : i.length ? D`<label class="field">
            <span class="lbl">${B(e, "field.tone")}</span>
            <input disabled placeholder=${B(e, "profiles.no_tones")} />
            <span class="hint">${B(e, "profiles.no_tones")}</span>
          </label>` : k;
	}
	_select(e, t, n, r, i, a) {
		return D`<label class="field">
      <span class="lbl">${B(e, `field.${r}`)}</span>
      <select
        @change=${(e) => this._setParam(n, r, e.target.value || null)}
      >
        ${i.map((e) => D`<option .value=${e} ?selected=${t.params[r] === e}>
              ${a(e)}
            </option>`)}
      </select>
    </label>`;
	}
	_json(e, t, n) {
		return D`<label class="field wide">
      <span class="lbl">${B(e, "field.data")}</span>
      <textarea
        rows="4"
        .value=${JSON.stringify(t.params.data ?? {}, null, 2)}
        @change=${(e) => {
			let t = e.target.value.trim();
			try {
				this._setParam(n, "data", t ? JSON.parse(t) : null);
			} catch {
				this._setParam(n, "data", t);
			}
		}}
      ></textarea>
      <span class="hint">${B(e, "profiles.call_service_hint")}</span>
    </label>`;
	}
	_renderMoments(e, t, n) {
		let r = new Set(this.ctx?.meta?.future_moments ?? []), i = new Set(this.ctx?.meta?.moments ?? []);
		return D`<div class="moments-grid">
      ${Object.entries(ut).map(([a, o]) => D`<fieldset>
            <legend>${B(e, `moment_group.${a}`)}</legend>
            ${o.filter((e) => i.has(e)).map((i) => D`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${t.moments.includes(i)}
                      @change=${(e) => {
			let r = e.target.checked ? [...t.moments, i] : t.moments.filter((e) => e !== i);
			this._setAction(n, { moments: r });
		}}
                    />
                    <span>
                      ${B(e, `moment.${i}`)}
                      ${r.has(i) ? D`<span class="later">${B(e, "profiles.future_moment")}</span>` : k}
                    </span>
                  </label>`)}
          </fieldset>`)}
    </div>`;
	}
	_renderConditions(e, t, n) {
		let r = this.ctx?.meta?.max_conditions ?? 2, i = (e) => this._setAction(n, { conditions: e });
		return D`<fieldset class="conditions">
      <legend>${B(e, "field.conditions")}</legend>
      ${t.conditions.length ? t.conditions.map((r, i) => this._renderCondition(e, t, n, r, i)) : D`<p class="hint">${B(e, "condition.none")}</p>`}
      ${t.conditions.length < r ? D`<div class="actions">
              <button
                class="btn sm"
                @click=${() => i([...t.conditions, {
			kind: "time",
			after: "22:00",
			before: "07:00"
		}])}
              >
                ${B(e, "condition.time")}
              </button>
              <button
                class="btn sm"
                @click=${() => i([...t.conditions, {
			kind: "state",
			entity_id: "",
			operator: "is",
			state: "on"
		}])}
              >
                ${B(e, "condition.state")}
              </button>
            </div>` : k}
      ${t.conditions.length === 2 ? D`<label class="field">
              <span class="lbl">${B(e, "field.condition_mode")}</span>
              <select
                @change=${(e) => this._setAction(n, { condition_mode: e.target.value })}
              >
                ${["all", "any"].map((n) => D`<option .value=${n} ?selected=${t.condition_mode === n}>
                      ${B(e, `condition.${n}`)}
                    </option>`)}
              </select>
            </label>` : k}
      <p class="hint">${B(e, "condition.max")}</p>
    </fieldset>`;
	}
	_renderCondition(e, t, n, r, i) {
		let a = (e) => this._setAction(n, { conditions: t.conditions.map((t, n) => n === i ? {
			...t,
			...e
		} : t) });
		return D`<div class="condition">
      ${r.kind === "time" ? D`<label class="field">
                <span class="lbl">${B(e, "condition.after")}</span>
                <input
                  type="time"
                  .value=${r.after}
                  @input=${(e) => a({ after: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${B(e, "condition.before")}</span>
                <input
                  type="time"
                  .value=${r.before}
                  @input=${(e) => a({ before: e.target.value })}
                />
                <span class="hint">${B(e, "condition.midnight_hint")}</span>
              </label>` : D`<label class="field">
                <span class="lbl">${B(e, "field.entity_id")}</span>
                <input
                  .value=${r.entity_id}
                  @input=${(e) => a({ entity_id: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${B(e, "field.state")}</span>
                <select
                  @change=${(e) => a({ operator: e.target.value })}
                >
                  ${["is", "is_not"].map((t) => D`<option .value=${t} ?selected=${r.operator === t}>
                        ${B(e, `condition.${t}`)}
                      </option>`)}
                </select>
              </label>
              <label class="field">
                <span class="lbl">${B(e, "condition.state")}</span>
                <input
                  .value=${r.state}
                  @input=${(e) => a({ state: e.target.value })}
                />
              </label>`}
      <button class="btn sm danger" @click=${() => this._setAction(n, { conditions: t.conditions.filter((e, t) => t !== i) })}>${B(e, "common.delete")}</button>
    </div>`;
	}
	static {
		this.styles = [
			H,
			V,
			o`
      .contact-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0;
      }
      .contact-row select {
        flex: 1;
      }
      .page-intro {
        margin: 0 4px 12px;
        color: var(--secondary-text-color);
        font-size: 13.5px;
        max-width: 78ch;
      }
      .actions-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 16px;
      }
      .action {
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        overflow: hidden;
      }
      .action-hd {
        width: 100%;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: none;
        border: 0;
        color: inherit;
        font: inherit;
        text-align: left;
        cursor: pointer;
        flex-wrap: wrap;
      }
      .action[data-open] .action-hd {
        border-bottom: 1px solid var(--divider-color);
      }
      .summary {
        font-family: var(--code-font-family, monospace);
        font-size: 12.5px;
        color: var(--secondary-text-color);
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .moments {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .cond {
        font-size: 12px;
        border-radius: 999px;
        padding: 1px 7px;
        background: var(--warning-color, #f0a835);
        color: #0d1014;
      }
      .action-bd {
        padding: 12px;
      }
      .moments-grid {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        margin-top: 12px;
      }
      .entities.wide {
        grid-column: 1 / -1;
      }
      .entity-list {
        max-height: 200px;
        overflow: auto;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 2px 16px;
        margin-top: 6px;
      }
      .filter {
        width: min(100%, 320px);
      }
      .condition {
        display: flex;
        gap: 12px;
        align-items: flex-end;
        flex-wrap: wrap;
        padding: 8px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      .later {
        font-size: 11px;
        color: var(--secondary-text-color);
        display: block;
      }
      .add-action {
        margin-top: 12px;
        max-width: 320px;
      }
      textarea {
        font-family: var(--code-font-family, monospace);
        font-size: 12.5px;
      }
      .wide {
        grid-column: 1 / -1;
      }
    `
		];
	}
};
customElements.get("foyer-page-profiles") || customElements.define("foyer-page-profiles", _t);
//#endregion
//#region src/panel/pages/groups.ts
var vt = class extends I {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 }
		};
	}
	_edit(e) {
		let t = this.ctx?.config?.areas[0]?.id ?? "";
		this._draft = e ? structuredClone(e) : {
			name: "",
			area_id: t,
			members: [],
			n: 2,
			window_seconds: 60,
			suppress_members: !1,
			response_profile_id: null
		}, this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("group", this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("group", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	_rows(e, t) {
		let n = t.map((e) => ({
			group: e,
			derived: !1
		})), r = /* @__PURE__ */ new Set();
		for (let t of e) {
			if (!t.id || !t.cross_zone_id) continue;
			let e = [t.id, t.cross_zone_id].sort(), i = e.join("+");
			r.has(i) || (r.add(i), n.push({
				derived: !0,
				group: {
					id: `cross:${i}`,
					name: t.name,
					area_id: t.area_id,
					members: e,
					n: 2,
					window_seconds: t.cross_zone_window,
					suppress_members: !1,
					response_profile_id: null
				}
			}));
		}
		return n;
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.config.zones.map((e) => [e.id, e.name])), i = this._rows(e.config.zones, e.config.groups ?? []);
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "groups.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${B(t, "groups.add")}</button>
        </div>
        ${i.length ? D`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${B(t, "field.name")}</th>
                    <th>${B(t, "field.area_id")}</th>
                    <th>${B(t, "field.members")}</th>
                    <th>${B(t, "field.n")}</th>
                    <th>${B(t, "field.window_seconds")}</th>
                    <th>${B(t, "groups.members_below")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${i.map(({ group: e, derived: i }) => D`<tr
                      class=${i ? "" : "clickable"}
                      aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                      @click=${() => i ? void 0 : this._edit(e)}
                    >
                      <td>
                        <strong>${e.name}</strong>
                        ${i ? D`<span class="tag">${B(t, "groups.from_zone")}</span>` : k}
                      </td>
                      <td>${n.get(e.area_id) ?? ""}</td>
                      <td>
                        ${e.members.map((e) => D`<span class="tag">${r.get(e) ?? e}</span>`)}
                      </td>
                      <td>${B(t, "groups.threshold", {
			n: e.n,
			m: e.members.length
		})}</td>
                      <td>${B(t, "common.seconds", { n: e.window_seconds })}</td>
                      <td>
                        ${B(t, e.suppress_members ? "groups.suppressed" : "groups.not_suppressed")}
                      </td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : D`<div class="empty">${B(t, "groups.none")}</div>`}
        <div class="card-bd">
          <p class="hint">${B(t, "groups.from_zone_hint")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, [r, i] = n.meta?.bounds.window ?? [1, 3600], a = new Map(n.config?.areas.map((e) => [e.id, e.name])), o = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.id !== t.id && e.members.forEach((e) => o.add(e));
		for (let e of n.config?.zones ?? []) e.cross_zone_id && e.id && (o.add(e.id), o.add(e.cross_zone_id));
		let s = (n.config?.zones ?? []).filter((e) => e.channel === "intrusion" && e.id && (!o.has(e.id) || t.members.includes(e.id))), c = (e, n) => this._set("members", n ? [.../* @__PURE__ */ new Set([...t.members, e])] : t.members.filter((t) => t !== e));
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "groups.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.area_id")}</span>
              <select
                @change=${(e) => this._set("area_id", e.target.value)}
              >
                ${(n.config?.areas ?? []).map((e) => D`<option .value=${e.id ?? ""} ?selected=${e.id === t.area_id}>
                      ${e.name}
                    </option>`)}
              </select>
              <span class="hint">${B(e, "groups.area_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.n")}</span>
              <input
                type="number"
                min="2"
                max=${Math.max(2, t.members.length)}
                .value=${String(t.n)}
                @input=${(e) => this._set("n", W(e.target.value) ?? 2)}
              />
              <span class="hint">
                ${B(e, "groups.threshold", {
			n: t.n,
			m: t.members.length
		})}
              </span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.window_seconds")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.window_seconds)}
                @input=${(e) => this._set("window_seconds", W(e.target.value) ?? 60)}
              />
              <span class="hint">${B(e, "groups.window_hint")}</span>
            </label>
            ${G(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e), B(e, "profiles.group_hint"))}
          </div>
          <fieldset>
            <legend>${B(e, "field.members")}</legend>
            ${s.length ? s.map((n) => D`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${t.members.includes(n.id ?? "")}
                      @change=${(e) => c(n.id ?? "", e.target.checked)}
                    />
                    <span>
                      ${B(e, "zones.entity", {
			name: n.name,
			entity: a.get(n.area_id) ?? n.area_id
		})}
                    </span>
                  </label>`) : D`<p class="hint">${B(e, "groups.no_zones")}</p>`}
            <p class="hint">${B(e, "groups.members_hint")}</p>
          </fieldset>
          <label class="check suppress">
            <input
              type="checkbox"
              .checked=${t.suppress_members}
              @change=${(e) => this._set("suppress_members", e.target.checked)}
            />
            <span>
              ${B(e, "field.suppress_members")}
              <span class="hint">${B(e, "groups.suppress_hint")}</span>
            </span>
          </label>
          ${this._problems.length ? D`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                </ul>
              </div>` : k}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${B(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${B(e, "common.cancel")}
            </button>
            ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${B(e, "common.delete")}
                </button>` : k}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			V,
			H,
			o`
      .suppress {
        margin-top: 12px;
      }
      td .tag {
        margin-left: 6px;
      }
    `
		];
	}
};
customElements.get("foyer-page-groups") || customElements.define("foyer-page-groups", vt);
//#endregion
//#region src/panel/pages/users.ts
var yt = {
	name: "",
	has_code: !1,
	has_duress_code: !1,
	ha_user_id: null,
	permissions: [
		"arm",
		"disarm",
		"bypass_zone",
		"change_scenario",
		"view_log"
	],
	allowed_area_ids: null,
	allowed_scenario_ids: null,
	valid_from: null,
	valid_until: null,
	code_exempt_when_identified: !1,
	enabled: !0
};
function bt(e) {
	if (!e) return "";
	let t = new Date(e), n = (e) => String(e).padStart(2, "0");
	return `${t.getFullYear()}-${n(t.getMonth() + 1)}-${n(t.getDate())}T${n(t.getHours())}:${n(t.getMinutes())}`;
}
function xt(e) {
	if (!e) return null;
	let t = new Date(e);
	return Number.isNaN(t.getTime()) ? null : t.toISOString();
}
var St = class extends I {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_policy: { state: !0 }
		};
	}
	_edit(e) {
		this._draft = e ? { ...structuredClone(e) } : structuredClone(yt), this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	_togglePermission(e, t) {
		let n = new Set(this._draft?.permissions ?? []);
		t ? n.add(e) : n.delete(e), this._set("permissions", [...n].sort());
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let { new_code: e, new_duress_code: t, ...n } = this._draft, r = await this.ctx.saveUser(n, {
					...e === void 0 ? {} : { new_code: e },
					...t === void 0 ? {} : { new_duress_code: t }
				});
				this._problems = r.problems, r.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("user", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	_policyDraft() {
		let e = this.ctx.config;
		return this._policy ?? {
			code_policy: { ...e.code_policy },
			security: { ...e.settings.security }
		};
	}
	async _savePolicy() {
		if (this.ctx && this._policy) {
			this._busy = !0;
			try {
				let e = await this.ctx.saveSecurity(this._policy.code_policy, this._policy.security);
				this._problems = e.problems, e.success && (this._policy = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = e.config.users ?? [];
		return D`
      ${e.status.security.enforced ? k : D`<div class="banner warn">
            <strong>${B(t, "users.not_enforced")}</strong>
            <span>${B(t, "users.not_enforced_hint")}</span>
          </div>`}
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "users.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${B(t, "users.add")}
          </button>
        </div>
        ${n.length ? D`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${B(t, "field.name")}</th>
                    <th>${B(t, "users.code")}</th>
                    <th>${B(t, "field.permissions")}</th>
                    <th>${B(t, "users.scope")}</th>
                    <th>${B(t, "field.valid_until")}</th>
                    <th>${B(t, "users.duress")}</th>
                    <th>${B(t, "field.ha_user_id")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${n.map((e) => this._row(t, e))}
                </tbody>
              </table>
            </div>` : D`<div class="empty">${B(t, "users.none")}</div>`}
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
      ${this._renderPolicy(t)}
    `;
	}
	_row(e, t) {
		let n = this.ctx, r = new Map((n.config?.areas ?? []).map((e) => [e.id, e.name])), i = t.allowed_area_ids === null ? B(e, "users.every_area") : t.allowed_area_ids.map((e) => r.get(e) ?? e).join(", ");
		return D`<tr
      class="clickable"
      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
      @click=${() => this._edit(t)}
    >
      <td>
        <strong>${t.name}</strong>
        ${t.enabled ? k : D`<span class="tag">${B(e, "users.disabled")}</span>`}
      </td>
      <td>
        ${t.has_code ? D`<span class="pill ok">${B(e, "users.code_set")}</span>` : D`<span class="pill warn">${B(e, "users.code_missing")}</span>`}
      </td>
      <td>${t.permissions.map((t) => D`<span class="tag">${B(e, `permission.${t}`)}</span>`)}</td>
      <td>${i}</td>
      <td>${t.valid_until ? new Date(t.valid_until).toLocaleString(n.hass.language) : "—"}</td>
      <td>${B(e, t.has_duress_code ? "common.yes" : "common.no")}</td>
      <td>${t.ha_user_id ? B(e, "users.linked") : "—"}</td>
    </tr>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.status.security.code_length, i = n.meta?.permissions ?? [], a = n.hass.user?.is_admin ? n.haUsers ?? [] : [];
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "users.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "users.code")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${r}
                placeholder=${t.has_code ? B(e, "users.code_unchanged") : B(e, "users.code_digits", { n: r })}
                @input=${(e) => this._set("new_code", e.target.value)}
              />
              <span class="hint">${B(e, "users.code_hint", { n: r })}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "users.duress")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${r}
                placeholder=${t.has_duress_code ? B(e, "users.code_unchanged") : B(e, "users.code_optional")}
                @input=${(e) => this._set("new_duress_code", e.target.value)}
              />
              <span class="hint">${B(e, "users.duress_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.ha_user_id")}</span>
              <select
                @change=${(e) => this._set("ha_user_id", e.target.value || null)}
              >
                <option value="" ?selected=${!t.ha_user_id}>${B(e, "users.not_linked")}</option>
                ${a.map((e) => D`<option .value=${e.id} ?selected=${e.id === t.ha_user_id}>
                    ${e.name}
                  </option>`)}
              </select>
              <span class="hint">${B(e, "users.linked_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.valid_from")}</span>
              <input
                type="datetime-local"
                .value=${bt(t.valid_from)}
                @input=${(e) => this._set("valid_from", xt(e.target.value))}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.valid_until")}</span>
              <input
                type="datetime-local"
                .value=${bt(t.valid_until)}
                @input=${(e) => this._set("valid_until", xt(e.target.value))}
              />
              <span class="hint">${B(e, "users.validity_hint")}</span>
            </label>
          </div>

          <div class="hr"></div>
          <div class="lbl">${B(e, "field.permissions")}</div>
          <div class="chips">
            ${i.map((n) => D`<label class="chip">
                <input
                  type="checkbox"
                  .checked=${t.permissions.includes(n)}
                  @change=${(e) => this._togglePermission(n, e.target.checked)}
                />
                <span>${B(e, `permission.${n}`)}</span>
              </label>`)}
          </div>

          <div class="hr"></div>
          <div class="scopes">
            ${this._scope(e, "allowed_area_ids", (n.config?.areas ?? []).map((e) => ({
			id: e.id ?? "",
			name: e.name
		})), t)}
            ${this._scope(e, "allowed_scenario_ids", (n.config?.scenarios ?? []).map((e) => ({
			id: e.id ?? "",
			name: e.name
		})), t)}
          </div>

          <div class="hr"></div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.code_exempt_when_identified}
              @change=${(e) => this._set("code_exempt_when_identified", e.target.checked)}
            />
            <span>
              ${B(e, "users.exempt")}
              <span class="hint">${B(e, "users.exempt_hint")}</span>
            </span>
          </label>
          <p class="note">${B(e, "users.exempt_note")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.enabled}
              @change=${(e) => this._set("enabled", e.target.checked)}
            />
            <span>
              ${B(e, "users.enabled")}
              <span class="hint">${B(e, "users.enabled_hint")}</span>
            </span>
          </label>

          ${this._problems.length ? D`<ul class="problems">
                ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
              </ul>` : k}
        </div>
        <div class="card-ft">
          <button class="btn" @click=${() => this._draft = void 0}>
            ${B(e, "common.cancel")}
          </button>
          ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                ${B(e, "common.delete")}
              </button>` : k}
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${B(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	_scope(e, t, n, r) {
		let i = r[t], a = (e, r) => {
			let a = new Set(i ?? n.map((e) => e.id));
			r ? a.add(e) : a.delete(e), this._set(t, [...a]);
		};
		return D`<div class="scope">
      <span class="lbl">${B(e, `field.${t}`)}</span>
      <label class="chip">
        <input
          type="checkbox"
          .checked=${i === null}
          @change=${(e) => this._set(t, e.target.checked ? null : [])}
        />
        <span>${B(e, "users.everything")}</span>
      </label>
      ${i === null ? k : D`<div class="chips">
            ${n.map((e) => D`<label class="chip">
                <input
                  type="checkbox"
                  .checked=${i.includes(e.id)}
                  @change=${(t) => a(e.id, t.target.checked)}
                />
                <span>${e.name}</span>
              </label>`)}
          </div>`}
    </div>`;
	}
	_renderPolicy(e) {
		let t = this.ctx, n = this._policyDraft(), r = t.meta?.operations ?? [], i = new Set(t.meta?.future_operations ?? []), [a, o] = t.meta?.bounds.lockout_failures ?? [2, 20], [s, c] = t.meta?.bounds.lockout_seconds ?? [10, 86400], [l, u] = t.meta?.bounds.code_length ?? [4, 12], d = (e, t) => this._policy = {
			...n,
			code_policy: {
				...n.code_policy,
				[e]: t
			}
		}, f = (e, t) => this._policy = {
			...n,
			security: {
				...n.security,
				[e]: t
			}
		};
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "users.policy")}</h2>
        </div>
        <div class="card-bd">
          <p class="hint">${B(e, "users.policy_hint")}</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${B(e, "users.operation")}</th>
                  <th>${B(e, "users.needs_code")}</th>
                </tr>
              </thead>
              <tbody>
                ${r.map((t) => D`<tr>
                    <td>
                      ${B(e, `operation.${t}`)}
                      ${i.has(t) ? D`<span class="tag">${B(e, "users.later_phase")}</span>` : k}
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        .checked=${!!n.code_policy[t]}
                        @change=${(e) => d(t, e.target.checked)}
                      />
                    </td>
                  </tr>`)}
              </tbody>
            </table>
          </div>

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "users.code_length")}</span>
              <input
                type="number"
                min=${l}
                max=${u}
                .value=${String(n.security.code_length)}
                @input=${(e) => f("code_length", W(e.target.value) ?? 6)}
              />
              <span class="hint">${B(e, "users.code_length_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "users.lockout_failures")}</span>
              <input
                type="number"
                min=${a}
                max=${o}
                .value=${String(n.security.lockout_failures)}
                @input=${(e) => f("lockout_failures", W(e.target.value) ?? 5)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "users.lockout_window")}</span>
              <input
                type="number"
                min=${s}
                max=${c}
                .value=${String(n.security.lockout_window)}
                @input=${(e) => f("lockout_window", W(e.target.value) ?? 300)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "users.lockout_duration")}</span>
              <input
                type="number"
                min=${s}
                max=${c}
                .value=${String(n.security.lockout_duration)}
                @input=${(e) => f("lockout_duration", W(e.target.value) ?? 300)}
              />
              <span class="hint">${B(e, "users.lockout_hint")}</span>
            </label>
          </div>
        </div>
        <div class="card-ft">
          <button
            class="btn primary"
            ?disabled=${this._busy || !this._policy}
            @click=${this._savePolicy}
          >
            ${B(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			H,
			V,
			o`
      .scopes {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
      }
      .scope {
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: flex-start;
      }
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
      }
      .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border: 1px solid var(--divider-color);
        border-radius: 999px;
        font-size: 13px;
      }
      .banner {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px 16px;
        margin-bottom: 16px;
        border-radius: 8px;
        background: var(--warning-color, #f0a835);
        color: #0d1014;
      }
      .note {
        margin-top: 12px;
        color: var(--secondary-text-color);
        font-size: 13px;
      }
    `
		];
	}
};
customElements.define("foyer-page-users", St);
//#endregion
//#region src/panel/pages/devices.ts
var Ct = {
	name: "",
	kind: "keypad",
	ref: "",
	entity_id: null,
	event_type: null,
	user_id: null,
	command: "toggle",
	scenario_id: null,
	enabled: !0
}, wt = ["tag.", "event."], Tt = class extends I {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1, this._mqttProblems = [];
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_mqtt: { state: !0 },
			_mqttProblems: { state: !0 }
		};
	}
	_edit(e) {
		this._draft = e ? structuredClone(e) : structuredClone(Ct), this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	_setKind(e) {
		this._draft = e === "keypad" ? {
			...this._draft,
			kind: e,
			entity_id: null,
			event_type: null,
			user_id: null,
			ref: this._draft?.ref || ""
		} : {
			...this._draft,
			kind: e,
			ref: null
		};
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("device", this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("device", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	_mqttDraft() {
		return this._mqtt ?? { ...this.ctx.config.settings.mqtt };
	}
	async _saveMqtt() {
		if (this.ctx && this._mqtt) {
			this._busy = !0;
			try {
				let e = {
					...this.ctx.config.settings,
					mqtt: this._mqtt
				}, t = await this.ctx.saveSettings(e);
				this._mqttProblems = t.problems, t.success && (this._mqtt = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = e.config.devices ?? [];
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "devices.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${B(t, "devices.add")}
          </button>
        </div>
        ${n.length ? D`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${B(t, "field.name")}</th>
                    <th>${B(t, "field.kind")}</th>
                    <th>${B(t, "devices.reaches")}</th>
                    <th>${B(t, "devices.identifies")}</th>
                    <th>${B(t, "field.enabled")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${n.map((e) => this._row(t, e))}
                </tbody>
              </table>
            </div>` : D`<div class="empty">${B(t, "devices.none")}</div>`}
        <div class="card-bd">
          <p class="note">${B(t, "devices.white_list")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
      ${this._renderMqtt(t)}
    `;
	}
	_row(e, t) {
		let n = (this.ctx.config?.users ?? []).find((e) => e.id === t.user_id);
		return D`<tr
      class="clickable"
      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
      @click=${() => this._edit(t)}
    >
      <td><strong>${t.name}</strong></td>
      <td>${B(e, `device_kind.${t.kind}`)}</td>
      <td class="mono">${t.kind === "keypad" ? t.ref : t.entity_id}</td>
      <td>
        ${t.kind === "tag" ? D`<span class="pill ok">${n?.name ?? "—"}</span>` : D`<span class="pill idle">${B(e, "devices.code_is_identity")}</span>`}
      </td>
      <td>${B(e, t.enabled ? "common.yes" : "common.no")}</td>
    </tr>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.config?.users ?? [], i = n.config?.scenarios ?? [], a = Object.keys(n.hass.states).filter((e) => wt.some((t) => e.startsWith(t))).sort();
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "devices.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.kind")}</span>
              <select
                @change=${(e) => this._setKind(e.target.value)}
              >
                ${["keypad", "tag"].map((n) => D`<option .value=${n} ?selected=${n === t.kind}>
                    ${B(e, `device_kind.${n}`)}
                  </option>`)}
              </select>
              <span class="hint">${B(e, `devices.kind_hint_${t.kind}`)}</span>
            </label>
          </div>

          ${t.kind === "keypad" ? D`<div class="grid-form">
                <label class="field">
                  <span class="lbl">${B(e, "field.ref")}</span>
                  <input
                    .value=${t.ref ?? ""}
                    placeholder="keypad_hall"
                    @input=${(e) => this._set("ref", e.target.value)}
                  />
                  <span class="hint">${B(e, "devices.ref_hint")}</span>
                </label>
              </div>` : D`
                <div class="banner warn">
                  <strong>${B(e, "devices.stolen_tag")}</strong>
                  <span>${B(e, "devices.stolen_tag_hint")}</span>
                </div>
                <div class="grid-form">
                  <label class="field">
                    <span class="lbl">${B(e, "field.entity_id")}</span>
                    <select
                      @change=${(e) => this._set("entity_id", e.target.value || null)}
                    >
                      <option value="" ?selected=${!t.entity_id}>—</option>
                      ${a.map((e) => D`<option .value=${e} ?selected=${e === t.entity_id}>
                          ${e}
                        </option>`)}
                    </select>
                    <span class="hint">${B(e, "devices.entity_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${B(e, "field.event_type")}</span>
                    <input
                      .value=${t.event_type ?? ""}
                      @input=${(e) => this._set("event_type", e.target.value || null)}
                    />
                    <span class="hint">${B(e, "devices.event_type_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${B(e, "field.user_id")}</span>
                    <select
                      @change=${(e) => this._set("user_id", e.target.value || null)}
                    >
                      <option value="" ?selected=${!t.user_id}>—</option>
                      ${r.map((e) => D`<option .value=${e.id ?? ""} ?selected=${e.id === t.user_id}>
                          ${e.name}
                        </option>`)}
                    </select>
                    <span class="hint">${B(e, "devices.owner_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${B(e, "field.command")}</span>
                    <select
                      @change=${(e) => this._set("command", e.target.value)}
                    >
                      ${[
			"toggle",
			"arm",
			"disarm"
		].map((n) => D`<option
                          .value=${n}
                          ?selected=${n === t.command}
                        >
                          ${B(e, `key_command.${n}`)}
                        </option>`)}
                    </select>
                  </label>
                  ${t.command === "disarm" ? k : D`<label class="field">
                        <span class="lbl">${B(e, "field.scenario_id")}</span>
                        <select
                          @change=${(e) => this._set("scenario_id", e.target.value || null)}
                        >
                          <option value="" ?selected=${!t.scenario_id}>—</option>
                          ${i.map((e) => D`<option
                              .value=${e.id ?? ""}
                              ?selected=${e.id === t.scenario_id}
                            >
                              ${e.name}
                            </option>`)}
                        </select>
                      </label>`}
                </div>
              `}

          <div class="hr"></div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.enabled}
              @change=${(e) => this._set("enabled", e.target.checked)}
            />
            <span>
              ${B(e, "field.enabled")}
              <span class="hint">${B(e, "devices.enabled_hint")}</span>
            </span>
          </label>

          ${this._problems.length ? D`<ul class="problems">
                ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
              </ul>` : k}
        </div>
        <div class="card-ft">
          <button class="btn" @click=${() => this._draft = void 0}>
            ${B(e, "common.cancel")}
          </button>
          ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                ${B(e, "common.delete")}
              </button>` : k}
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${B(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	_renderMqtt(e) {
		let t = this._mqttDraft(), n = (e, n) => {
			this._mqtt = {
				...t,
				[e]: n
			};
		};
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "devices.mqtt")}</h2>
        </div>
        <div class="card-bd">
          <p class="note">${B(e, "devices.mqtt_note")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.enabled}
              @change=${(e) => n("enabled", e.target.checked)}
            />
            <span>
              ${B(e, "devices.mqtt_enabled")}
              <span class="hint">${B(e, "devices.mqtt_enabled_hint")}</span>
            </span>
          </label>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.command_topic")}</span>
              <input
                .value=${t.command_topic}
                placeholder=${B(e, "devices.topic_command_example")}
                @input=${(e) => n("command_topic", e.target.value)}
              />
              <span class="hint">${B(e, "devices.topic_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.state_topic")}</span>
              <input
                .value=${t.state_topic}
                placeholder=${B(e, "devices.topic_state_example")}
                @input=${(e) => n("state_topic", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.detail")}</span>
              <select
                @change=${(e) => n("detail", e.target.value)}
              >
                ${[
			"minimal",
			"standard",
			"full"
		].map((n) => D`<option .value=${n} ?selected=${n === t.detail}>
                    ${B(e, `mqtt_detail.${n}`)}
                  </option>`)}
              </select>
              <span class="hint">${B(e, `devices.detail_hint_${t.detail}`)}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.qos")}</span>
              <select
                @change=${(e) => n("qos", Number(e.target.value))}
              >
                ${[
			0,
			1,
			2
		].map((e) => D`<option .value=${String(e)} ?selected=${e === t.qos}>
                    ${e}
                  </option>`)}
              </select>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.retain}
              @change=${(e) => n("retain", e.target.checked)}
            />
            <span>
              ${B(e, "field.retain")}
              <span class="hint">${B(e, "devices.retain_hint")}</span>
            </span>
          </label>
          <div class="hr"></div>
          <div class="grid-form">
            <div class="field">
              <span class="lbl">${B(e, "devices.inbound")}</span>
              <pre class="sample">${Et}</pre>
            </div>
            <div class="field">
              <span class="lbl">${B(e, "devices.outbound")}</span>
              <pre class="sample">${Dt[t.detail]}</pre>
              <span class="hint">${B(e, "devices.last_result_hint")}</span>
            </div>
          </div>
          ${this._mqttProblems.length ? D`<ul class="problems">
                ${this._mqttProblems.map((t) => D`<li>${U(e, t)}</li>`)}
              </ul>` : k}
        </div>
        <div class="card-ft">
          <button
            class="btn primary"
            ?disabled=${this._busy || !this._mqtt}
            @click=${this._saveMqtt}
          >
            ${B(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			H,
			V,
			o`
      .sample {
        margin: 0;
        padding: 10px 12px;
        border-radius: 8px;
        background: var(--secondary-background-color);
        font-family: var(--code-font-family, monospace);
        font-size: 12px;
        line-height: 1.5;
        overflow-x: auto;
        white-space: pre;
      }
      .mono {
        font-family: var(--code-font-family, monospace);
        font-size: 12px;
      }
      /* The one sentence on this page that has to stop somebody: §9.3 says a
         stolen tag arms and disarms without knowing any code, and it is read
         while deciding whether to carry one. Plain text would not stop
         anybody. */
      .banner {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 8px;
        background: var(--warning-color, #f0a835);
        color: #0d1014;
      }
    `
		];
	}
}, Et = "{\n  \"action\": \"arm\",\n  \"scenario\": \"Night\",\n  \"code\": \"123456\",\n  \"device_id\": \"keypad_hall\"\n}", Dt = {
	minimal: "{\n  \"master\": \"armed_night\",\n  \"countdown\": { \"kind\": \"exit\", \"remaining\": 22 },\n  \"ready_to_arm\": false,\n  \"blocking_zones\": 1,\n  \"fault\": false,\n  \"last_result\": \"ok\"\n}",
	standard: "{\n  \"master\": \"armed_night\",\n  \"countdown\": null,\n  \"ready_to_arm\": true,\n  \"blocking_zones\": 0,\n  \"fault\": false,\n  \"last_result\": \"ok\",\n  \"scenario\": \"Night\",\n  \"areas\": { \"Ground floor\": \"armed\" }\n}",
	full: "{\n  \"master\": \"armed_night\",\n  \"countdown\": null,\n  \"ready_to_arm\": false,\n  \"blocking_zones\": 1,\n  \"fault\": false,\n  \"last_result\": \"blocked\",\n  \"scenario\": \"Night\",\n  \"areas\": { \"Ground floor\": \"armed\" },\n  \"open_zones\": [\"Bathroom window\"]\n}"
};
customElements.define("foyer-page-devices", Tt);
//#endregion
//#region src/panel/pages/test.ts
var Ot = [
	"diagnostics",
	"simulator",
	"walktest",
	"actiontest"
], kt = /* @__PURE__ */ new Set([
	"triggered",
	"entry_started",
	"verification_satisfied",
	"technical_raised"
]);
function At(e, t) {
	let n = e.config?.zones.find((e) => e.id === t);
	return n && n.trigger.kind === "state" ? n.trigger.states : [];
}
function jt(e) {
	let t = /* @__PURE__ */ new Set();
	for (let n of e.config?.profiles ?? []) for (let e of n.actions) for (let n of e.conditions) n.kind === "state" && t.add(n.entity_id);
	return [...t].sort();
}
function Y(e) {
	return new Date(e).toLocaleTimeString(void 0, {
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit"
	});
}
var Mt = class extends I {
	constructor(...e) {
		super(...e), this._tab = "diagnostics", this._busy = !1, this._scenario = "", this._start = "", this._overrides = [], this._entities = {}, this._code = "", this._codeWanted = !1, this._loaded = !1, this._mentioned = /* @__PURE__ */ new Set(), this._walkDuration = "", this._tested = {};
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_tab: { state: !0 },
			_diagnostics: { state: !0 },
			_simulation: { state: !0 },
			_busy: { state: !0 },
			_error: { state: !0 },
			_scenario: { state: !0 },
			_start: { state: !0 },
			_overrides: { state: !0 },
			_entities: { state: !0 },
			_code: { state: !0 },
			_codeWanted: { state: !0 },
			_walkDuration: { state: !0 },
			_tested: { state: !0 },
			_confirming: { state: !0 }
		};
	}
	updated() {
		!this._loaded && this.ctx && (this._loaded = !0, this._refresh());
	}
	async _refresh() {
		if (this.ctx) {
			this._busy = !0, this._error = void 0;
			try {
				this._diagnostics = await this.ctx.diagnostics();
			} catch (e) {
				this._diagnostics = void 0, this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _run() {
		if (!this.ctx) return;
		this._busy = !0, this._error = void 0, this._codeWanted = !1;
		let e = {
			scenario_id: this._scenario || null,
			start: this._start ? new Date(this._start).toISOString() : null,
			zones: this._overrides.filter((e) => e.zone_id && e.state),
			entities: this._entities,
			code: this._code || void 0
		};
		try {
			this._simulation = await this.ctx.simulate(e);
		} catch (e) {
			let t = e?.code;
			this._codeWanted = t === "bad_code" || t === "code_required", this._simulation = void 0, this._error = this._codeWanted ? void 0 : String(e?.message ?? e);
		} finally {
			this._busy = !1;
		}
	}
	render() {
		let e = this.ctx;
		if (!e) return k;
		let t = e.strings;
		return D`
      <nav class="subtabs" role="tablist">
        ${Ot.map((e) => D`
            <button
              role="tab"
              aria-selected=${e === this._tab ? "true" : "false"}
              @click=${() => this._tab = e}
            >
              ${B(t, `test.tab.${e}`)}
            </button>
          `)}
      </nav>
      ${this._error ? D`<div class="problems" role="alert">${this._error}</div>` : k}
      ${this._tab === "diagnostics" ? this._renderDiagnostics(t) : this._tab === "simulator" ? this._renderSimulator(t) : this._tab === "walktest" ? this._renderWalkTest(t) : this._renderActionTest(t)}
    `;
	}
	_renderDiagnostics(e) {
		let t = this._diagnostics;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "test.diagnostics.title")}</h2>
          <span class="hint">${B(e, "test.diagnostics.subtitle")}</span>
          <button class="btn" ?disabled=${this._busy} @click=${() => void this._refresh()}>
            ${B(e, "test.refresh")}
          </button>
        </div>
        <div class="card-bd">
          ${t?.missing_entities.length ? D`<div class="problems" role="alert">
                <p>${B(e, "test.diagnostics.missing")}</p>
                <ul>
                  ${t.missing_entities.map((e) => D`<li class="mono">${e}</li>`)}
                </ul>
              </div>` : k}
          ${t ? t.zones.length === 0 ? D`<p class="empty">${B(e, "test.diagnostics.empty")}</p>` : D`<div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>${B(e, "test.col.zone")}</th>
                        <th>${B(e, "test.col.entity")}</th>
                        <th>${B(e, "test.col.state")}</th>
                        <th>${B(e, "test.col.evaluation")}</th>
                        <th>${B(e, "test.col.last_change")}</th>
                        <th>${B(e, "test.col.health")}</th>
                        <th>${B(e, "test.col.battery")}</th>
                        <th>${B(e, "test.col.signal")}</th>
                        <th>${B(e, "test.col.supervision")}</th>
                        <th>${B(e, "test.col.arming")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${t.zones.map((t) => this._renderZoneRow(e, t))}
                    </tbody>
                  </table>
                </div>` : D`<p class="hint">${B(e, "common.loading")}</p>`}
        </div>
      </div>
      ${t && t.devices.length ? this._renderDevices(e, t.devices) : k}
    `;
	}
	_renderZoneRow(e, t) {
		let n = this.ctx?.status.areas.find((e) => e.id === t.area_id)?.name ?? "";
		return D`
      <tr>
        <td>
          <strong>${t.name}</strong>
          ${n ? D`<div class="hint">${n}</div>` : k}
        </td>
        <td class="mono">${t.entity_id}</td>
        <td>
          ${t.state === null ? D`<span class="state fault">${B(e, "test.no_entity")}</span>` : D`<span class="mono">${t.state}</span>`}
        </td>
        <td>
          ${t.momentary ? D`<span class="muted">${B(e, "test.momentary")}</span>` : D`<span class="state ${t.triggered ? "open" : "closed"}">
                ${B(e, t.triggered ? "test.would_trigger" : "test.would_not")}
              </span>`}
        </td>
        <td class="mono">
          ${t.last_changed ? Y(t.last_changed) : "—"}
        </td>
        <td>
          ${t.enabled ? t.fault ? D`<span class="state fault">${B(e, `fault.${t.fault}`)}</span>` : D`<span class="state closed">${B(e, "test.ok")}</span>` : D`<span class="state disabled">${B(e, "test.disabled")}</span>`}
        </td>
        <td>${this._renderBattery(e, t)}</td>
        <td class="mono">
          ${t.signal ? `${t.signal.value} ${B(e, `test.unit.${t.signal.unit}`)}` : "—"}
        </td>
        <td class="hint">
          ${t.supervision_timeout === null ? B(e, "test.supervision_off") : B(e, "test.supervision_on", { n: t.supervision_timeout })}
        </td>
        <td>
          ${t.bypassed ? D`<span class="state bypassed">${B(e, `bypass.${t.bypassed}`)}</span>` : t.blocks_arming ? D`<span class="state fault"
                  >${B(e, `test.blocks.${t.blocks_because}`)}</span
                >` : D`<span class="muted">—</span>`}
        </td>
      </tr>
    `;
	}
	_renderBattery(e, t) {
		if (!t.battery_entity_id) return D`<span class="muted">—</span>`;
		let n = t.battery_level === null ? "" : `${Math.round(t.battery_level)} %`;
		return D`
      <span class="state ${t.battery_low ? "open" : "closed"}">
        ${n || B(e, t.battery_low ? "test.battery_low" : "test.battery_ok")}
      </span>
    `;
	}
	_renderDevices(e, t) {
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "test.devices.title")}</h2>
          <span class="hint">${B(e, "test.devices.subtitle")}</span>
        </div>
        <div class="card-bd">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${B(e, "test.col.device")}</th>
                  <th>${B(e, "test.col.kind")}</th>
                  <th>${B(e, "test.col.entity")}</th>
                  <th>${B(e, "test.col.state")}</th>
                  <th>${B(e, "test.col.last_change")}</th>
                  <th>${B(e, "test.col.health")}</th>
                </tr>
              </thead>
              <tbody>
                ${t.map((t) => D`
                    <tr>
                      <td><strong>${t.name}</strong></td>
                      <td>${B(e, `device_kind.${t.kind}`)}</td>
                      <td class="mono">${t.entity_id ?? "—"}</td>
                      <td class="mono">${t.state ?? "—"}</td>
                      <td class="mono">
                        ${t.last_changed ? Y(t.last_changed) : "—"}
                      </td>
                      <td>
                        ${t.enabled ? t.watchable ? t.available ? D`<span class="state closed">${B(e, "test.ok")}</span>` : D`<span class="state fault"
                                  >${B(e, "fault.unavailable")}</span
                                >` : D`<span class="muted">${B(e, "test.no_entity_kind")}</span>` : D`<span class="state disabled"
                              >${B(e, "test.disabled")}</span
                            >`}
                      </td>
                    </tr>
                  `)}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
	}
	_renderSimulator(e) {
		let t = this.ctx;
		return D`
      <div class="notice info">
        <strong>${B(e, "test.simulator.safe_title")}</strong>
        ${B(e, "test.simulator.safe")}
      </div>
      <div class="split">
        <div class="card">
          <div class="card-hd">
            <h2>${B(e, "test.simulator.conditions")}</h2>
          </div>
          <div class="card-bd">
            <div class="grid-form">
              <label class="field">
                <span class="lbl">${B(e, "test.simulator.scenario")}</span>
                <select
                  .value=${this._scenario}
                  @change=${(e) => this._scenario = e.target.value}
                >
                  <option value="">${B(e, "test.simulator.disarmed")}</option>
                  ${t.status.scenarios.map((e) => D`<option
                      .value=${e.id}
                      ?selected=${e.id === this._scenario}
                    >
                      ${e.name}
                    </option>`)}
                </select>
                <span class="hint">${B(e, "test.simulator.scenario_hint")}</span>
              </label>
              <label class="field">
                <span class="lbl">${B(e, "test.simulator.clock")}</span>
                <input
                  type="datetime-local"
                  .value=${this._start}
                  @change=${(e) => this._start = e.target.value}
                />
                <span class="hint">${B(e, "test.simulator.clock_hint")}</span>
              </label>
            </div>
            ${this._renderOverrides(e)} ${this._renderEntityOverrides(e)}
            <div class="actions">
              <button
                class="btn primary"
                ?disabled=${this._busy}
                @click=${() => void this._run()}
              >
                ${B(e, "test.simulator.run")}
              </button>
              <button
                class="btn"
                @click=${() => {
			this._overrides = [], this._entities = {}, this._simulation = void 0, this._start = "";
		}}
              >
                ${B(e, "test.simulator.reset")}
              </button>
            </div>
          </div>
        </div>
        ${this._renderTrace(e)}
      </div>
    `;
	}
	_renderOverrides(e) {
		let t = this.ctx;
		return D`
      <fieldset>
        <legend>${B(e, "test.simulator.zones")}</legend>
        <p class="hint">${B(e, "test.simulator.zones_hint")}</p>
        ${this._overrides.map((n, r) => D`
            <div class="override">
              <select
                @change=${(e) => this._setOverride(r, {
			zone_id: e.target.value,
			state: At(t, e.target.value)[0] ?? n.state
		})}
              >
                <option value="">${B(e, "test.simulator.pick_zone")}</option>
                ${t.status.zones.map((e) => D`<option
                    .value=${e.id}
                    ?selected=${e.id === n.zone_id}
                  >
                    ${e.name}
                  </option>`)}
              </select>
              <input
                class="state-input"
                .value=${n.state}
                list="foyer-sim-states-${r}"
                placeholder=${B(e, "test.simulator.state")}
                @change=${(e) => this._setOverride(r, { state: e.target.value })}
              />
              <datalist id="foyer-sim-states-${r}">
                ${At(t, n.zone_id).map((e) => D`<option .value=${e}></option>`)}
              </datalist>
              <input
                class="at-input"
                type="number"
                min="0"
                .value=${String(n.at)}
                title=${B(e, "test.simulator.at")}
                @change=${(e) => this._setOverride(r, { at: Number(e.target.value) || 0 })}
              />
              <span class="hint">${B(e, "test.simulator.seconds")}</span>
              <button
                class="btn small"
                @click=${() => this._overrides = this._overrides.filter((e, t) => t !== r)}
              >
                ${B(e, "common.delete")}
              </button>
            </div>
          `)}
        <button
          class="btn small"
          @click=${() => this._overrides = [...this._overrides, {
			zone_id: "",
			state: "on",
			at: 0
		}]}
        >
          ${B(e, "test.simulator.add_zone")}
        </button>
      </fieldset>
    `;
	}
	_renderEntityOverrides(e) {
		let t = jt(this.ctx);
		return t.length ? D`
      <fieldset>
        <legend>${B(e, "test.simulator.entities")}</legend>
        <p class="hint">${B(e, "test.simulator.entities_hint")}</p>
        <div class="grid-form">
          ${t.map((t) => D`
              <label class="field">
                <span class="lbl mono">${t}</span>
                <input
                  .value=${this._entities[t] ?? ""}
                  placeholder=${B(e, "test.simulator.as_now")}
                  @change=${(e) => {
			let n = e.target.value, r = { ...this._entities };
			n ? r[t] = n : delete r[t], this._entities = r;
		}}
                />
              </label>
            `)}
        </div>
      </fieldset>
    ` : k;
	}
	_setOverride(e, t) {
		this._overrides = this._overrides.map((n, r) => r === e ? {
			...n,
			...t
		} : n);
	}
	_renderTrace(e) {
		let t = this._simulation;
		return this._mentioned = /* @__PURE__ */ new Set(), D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "test.trace.title")}</h2>
          <span class="hint">${B(e, "test.trace.subtitle")}</span>
        </div>
        <div class="card-bd">
          ${this._premiseNeedsCode(t) ? this._renderCodePrompt(e) : k}
          ${t ? D`
                <ol class="trace">
                  ${t.steps.filter((e) => this._worthShowing(e)).map((t) => this._renderStep(e, t))}
                </ol>
                ${t.truncated ? D`<p class="notice">${B(e, "test.trace.truncated")}</p>` : k}
              ` : D`<p class="empty">
                ${B(e, this._busy ? "common.loading" : "test.trace.empty")}
              </p>`}
        </div>
      </div>
    `;
	}
	_premiseNeedsCode(e) {
		if (this._codeWanted) return !0;
		let t = e?.steps.find((e) => e.kind === "request");
		return !!t && !t.accepted && (t.reason === "code_required" || t.reason === "bad_code");
	}
	_worthShowing(e) {
		return e.kind === "setup" ? !1 : e.kind === "zone" || !e.accepted || e.occurrences.length > 0 || e.areas.length > 0 || e.loose_actions.length > 0;
	}
	_renderCodePrompt(e) {
		return D`
      <div class="notice">
        <p>${B(e, "test.simulator.premise_code")}</p>
        <input
          type="password"
          inputmode="numeric"
          autocomplete="off"
          .value=${this._code}
          @change=${(e) => this._code = e.target.value}
        />
        <div class="actions">
          <button
            class="btn primary"
            ?disabled=${this._busy}
            @click=${() => void this._run()}
          >
            ${B(e, "test.simulator.run")}
          </button>
        </div>
      </div>
    `;
	}
	_renderStep(e, t) {
		let n = this.ctx, r = t.zone_id ? n.status.zones.find((e) => e.id === t.zone_id)?.name ?? t.zone_id : "";
		return D`
      <li class="step">
        <div class="when mono">${Y(t.at)}</div>
        <div class="what">
          ${t.kind === "zone" ? D`<div>
                ${B(e, "test.trace.zone", { zone: r })}
                <span class="mono">${t.zone_state}</span>
              </div>` : k}
          ${t.accepted ? k : D`<div class="no">
                ${B(e, `reason.${t.reason ?? "unknown"}`, { zones: t.blocking_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? e).join(", ") })}
              </div>`}
          ${t.low_battery_zones.length ? D`<div class="warn">
                ${B(e, "test.trace.low_battery", { zones: t.low_battery_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? e).join(", ") })}
              </div>` : k}
          ${t.areas.map((t) => D`
              <div class="key">
                ${B(e, "test.trace.area", {
			area: n.status.areas.find((e) => e.id === t.area_id)?.name ?? t.area_id,
			was: B(e, `state.${t.was}`),
			now: B(e, `state.${t.now}`)
		})}
                ${t.timer_due ? D`<span class="muted">
                      ${B(e, "test.trace.timer", {
			kind: B(e, `test.timer.${t.timer_kind}`),
			at: Y(t.timer_due)
		})}
                    </span>` : k}
              </div>
            `)}
          ${t.occurrences.map((t) => this._renderOccurrence(e, t))}
          ${this._renderBatches(e, t)}
          ${t.loose_actions.map((t) => t.escalation ? D`<div class="yes">
                  ${B(e, "test.trace.escalation_sent", {
			step: String(t.escalation_step ?? 0),
			who: this._whoFor(t.recipients)
		})}
                </div>` : D`<div class="yes">
                  ${B(e, "test.trace.ran", { action: B(e, `action_kind.${t.kind}`) })}
                </div>`)}
          ${t.scheduled.filter((e) => e.kind === "delay" || e.kind === "siren").filter((e) => this._firstMention(e)).map((t) => D`<div class="wait">
                ${B(e, `test.trace.later.${t.kind}`, { at: Y(t.at) })}
              </div>`)}
          ${t.scheduled.filter((e) => e.kind === "escalation_step").map((t) => D`<div class="wait">
                ${B(e, "test.trace.later.escalation_step", {
			step: String(t.step ?? 0),
			offset: String(t.offset ?? 0),
			who: this._whoAhead(t.contact_ids, t.channel_ids)
		})}
              </div>`)}
        </div>
      </li>
    `;
	}
	_whoFor(e) {
		let t = this.ctx?.config?.contacts ?? [];
		return e.map((e) => {
			let n = t.find((t) => t.id === e.contact_id), r = B(this.ctx.strings, `channel_kind.${e.kind}`);
			return `${n?.name ?? e.contact_id} (${r})`;
		}).join(", ");
	}
	_whoAhead(e, t) {
		let n = this.ctx?.config?.contacts ?? [];
		return e.map((e, r) => {
			let i = n.find((t) => t.id === e), a = i?.channels.find((e) => e.id === t[r]), o = a ? ` (${B(this.ctx.strings, `channel_kind.${a.kind}`)})` : "";
			return `${i?.name ?? e}${o}`;
		}).join(", ");
	}
	_firstMention(e) {
		let t = `${e.kind}|${e.at}|${e.area_id ?? ""}`;
		return !this._mentioned.has(t) && (this._mentioned.add(t), !0);
	}
	_renderOccurrence(e, t) {
		let n = this.ctx;
		if (t.detail.verification) {
			let r = t.group_id?.startsWith("cross:") ?? !0, i = n.config?.groups.find((e) => e.id === t.group_id);
			return D`<div class="key">
        ${B(e, t.moment === "verification_satisfied" ? "test.trace.group_satisfied" : "test.trace.group", {
				group: i?.name ?? (r ? B(e, "test.trace.cross_zone") : B(e, "test.trace.a_group")),
				count: t.detail.count,
				n: t.detail.n,
				window: t.detail.window
			})}
      </div>`;
		}
		return t.moment.startsWith("incident_") ? D`<div class="key">
        ${B(e, `moment.${t.moment}`)}
        <span class="mono">${t.incident_id ?? ""}</span>
      </div>` : D`<div class="key">${B(e, `moment.${t.moment}`)}</div>`;
	}
	_renderBatches(e, t) {
		return D`${t.batches.filter((e) => e.actions.length > 0 || kt.has(e.moment)).map((t) => this._renderBatch(e, t))}`;
	}
	_renderBatch(e, t) {
		return t.profile_id ? D`
      <div class="batch">
        <div class="key">
          ${B(e, "test.trace.profile", {
			profile: t.profile_name,
			source: B(e, `test.source.${t.source}`)
		})}
        </div>
        ${t.actions.length ? t.actions.map((t) => this._renderAction(e, t)) : D`<div class="no">${B(e, "test.trace.nothing_configured")}</div>`}
      </div>
    ` : D`<div class="no">${B(e, "test.trace.no_profile")}</div>`;
	}
	_renderAction(e, t) {
		let n = t.name || B(e, `action_kind.${t.kind}`);
		if (t.ran) return D`<div class="yes">
        ${B(e, "test.trace.ran", { action: n })}
        ${t.recipients.length ? D`<span class="muted">
              ${B(e, "test.trace.reached", { who: this._whoFor(t.recipients) })}
            </span>` : k}
        ${t.quiet.length ? D`<span class="muted">
              ${B(e, "test.trace.quiet", { who: t.quiet.map((e) => (this.ctx?.config?.contacts ?? []).find((t) => t.id === e)?.name ?? e).join(", ") })}
            </span>` : k}
      </div>`;
		let r = t.skipped === "condition" ? B(e, "test.skip.condition", { conditions: t.conditions.map((t) => t.kind === "time" ? B(e, "test.condition.time", t) : B(e, "test.condition.state", {
			entity_id: t.entity_id,
			operator: B(e, `condition.${t.operator}`),
			state: t.state
		})).join(", ") }) : B(e, `test.skip.${t.skipped}`);
		return D`<div class=${t.skipped === "held_by_delay" ? "wait" : "no"}>
      ${B(e, "test.trace.skipped", {
			action: n,
			why: r
		})}
    </div>`;
	}
	_renderWalkTest(e) {
		let t = this.ctx.status.walk_test;
		return D`
      <div class="notice ${t ? "danger" : "warn"}">
        ${t ? B(e, "walk.active") : D`<strong>${B(e, "walk.idle_title")}</strong>
              ${B(e, "walk.idle")}
              <div class="hint">${B(e, "walk.always_on_live")}</div>`}
      </div>
      ${t ? this._renderWalkRunning(e, t) : this._renderWalkStart(e)}
    `;
	}
	_renderWalkStart(e) {
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "walk.start_title")}</h2>
          <span class="hint">${B(e, "walk.start_sub")}</span>
        </div>
        <div class="card-bd">
          <p>${B(e, "walk.explainer")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "walk.duration")}</span>
              <input
                type="number"
                min="1"
                .value=${this._walkDuration}
                placeholder=${B(e, "walk.duration_default")}
                @change=${(e) => this._walkDuration = e.target.value}
              />
              <span class="hint">${B(e, "walk.duration_hint")}</span>
            </label>
          </div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy}
              @click=${() => void this._startWalkTest()}
            >
              ${B(e, "walk.start")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderWalkRunning(e, t) {
		let n = this.ctx, r = new Map(n.status.zones.map((e) => [e.id, e])), i = new Map(n.status.areas.map((e) => [e.id, e.name])), a = t.expected_zones.filter((e) => !t.detections[e]), o = t.expected_zones.filter((e) => t.detections[e]), s = (n) => {
			let a = r.get(n), o = t.detections[n];
			return D`
        <tr>
          <td><strong>${a?.name ?? n}</strong></td>
          <td>${i.get(a?.area_id ?? "") ?? ""}</td>
          <td>
            <span class="state ${o ? "closed" : "fault"}">
              ${B(e, o ? "walk.detected" : "walk.never")}
            </span>
          </td>
          <td class="mono">${o ? Y(o.first) : "—"}</td>
          <td class="mono">${o ? o.count : 0}</td>
          <td>
            ${a?.fault ? D`<span class="state fault">${B(e, `fault.${a.fault}`)}</span>` : k}
          </td>
        </tr>
      `;
		};
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "walk.table_title")}</h2>
          <span class="hint">
            ${B(e, "walk.started_by", {
			who: t.user_name ?? B(e, "walk.somebody"),
			at: Y(t.started_at)
		})}
          </span>
        </div>
        <div class="card-bd">
          ${a.length ? D`<div class="problems" role="alert">
                ${B(e, a.length === 1 ? "walk.never_reacted_one" : "walk.never_reacted", { n: a.length })}
              </div>` : D`<div class="notice">${B(e, "walk.all_reacted")}</div>`}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${B(e, "test.col.zone")}</th>
                  <th>${B(e, "walk.col.area")}</th>
                  <th>${B(e, "walk.col.result")}</th>
                  <th>${B(e, "walk.col.first")}</th>
                  <th>${B(e, "walk.col.count")}</th>
                  <th>${B(e, "test.col.health")}</th>
                </tr>
              </thead>
              <tbody>
                ${a.map(s)}${o.map(s)}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
	}
	async _startWalkTest() {
		let e = this.ctx;
		if (e) {
			this._busy = !0, this._error = void 0;
			try {
				let t = Number(this._walkDuration) || 0, n = await e.walkTest(!0, { duration: t > 0 ? t * 60 : void 0 });
				n.success ? n.blocking_zones.length && (this._error = B(e.strings, "walk.partly_armed", { zones: n.blocking_zones.map((e) => e.name).join(", ") })) : this._error = Ve(e.strings, n);
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderActionTest(e) {
		let t = this.ctx.config?.profiles ?? [];
		return D`
      <div class="notice danger">
        <strong>${B(e, "action_test.warn_title")}</strong>
        ${B(e, "action_test.warn")}
      </div>
      ${this._confirming ? this._renderConfirm(e) : k}
      ${t.length === 0 ? D`<p class="empty">${B(e, "action_test.no_profiles")}</p>` : t.map((t) => this._renderProfileTests(e, t))}
    `;
	}
	_renderProfileTests(e, t) {
		let n = t.actions.filter((e) => e.kind !== "delay");
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.name}</h2>
          <span class="hint">${B(e, "action_test.subtitle")}</span>
        </div>
        <div class="card-bd">
          ${n.length === 0 ? D`<p class="empty">${B(e, "action_test.no_actions")}</p>` : D`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${B(e, "action_test.col.action")}</th>
                      <th>${B(e, "action_test.col.what")}</th>
                      <th>${B(e, "action_test.col.last")}</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    ${n.map((n) => this._renderActionRow(e, t, n))}
                  </tbody>
                </table>
              </div>`}
        </div>
      </div>
    `;
	}
	_renderActionRow(e, t, n) {
		let r = `${t.id}:${n.id}`, i = this._tested[r], a = n.name || B(e, `action_kind.${n.kind}`);
		return D`
      <tr>
        <td><strong>${a}</strong></td>
        <td class="hint">${B(e, `action_test.what.${n.kind}`)}</td>
        <td>
          ${i ? i.ok ? D`<span class="state closed">${B(e, "action_test.ok")}</span>` : D`<span class="state fault" title=${i.error ?? ""}
                  >${B(e, "action_test.failed")}</span
                >` : D`<span class="muted">${B(e, "action_test.never")}</span>`}
        </td>
        <td>
          <button
            class="btn small"
            ?disabled=${this._busy}
            @click=${() => this._confirming = {
			profile_id: t.id ?? "",
			action_id: n.id ?? "",
			name: a
		}}
          >
            ${B(e, "action_test.test")}
          </button>
        </td>
      </tr>
    `;
	}
	_renderConfirm(e) {
		let t = this._confirming;
		return D`
      <div class="problems" role="alertdialog">
        <p>${B(e, "action_test.confirm", { action: t.name })}</p>
        <div class="actions">
          <button
            class="btn primary"
            ?disabled=${this._busy}
            @click=${() => void this._runTest(t)}
          >
            ${B(e, "action_test.confirm_yes")}
          </button>
          <button class="btn" @click=${() => this._confirming = void 0}>
            ${B(e, "common.cancel")}
          </button>
        </div>
      </div>
    `;
	}
	async _runTest(e) {
		let t = this.ctx;
		if (t) {
			this._busy = !0, this._confirming = void 0, this._error = void 0;
			try {
				let n = await t.testAction({
					profile_id: e.profile_id,
					action_id: e.action_id
				}), r = n.error ?? Nt(t.strings, n.reason);
				this._tested = {
					...this._tested,
					[`${e.profile_id}:${e.action_id}`]: {
						ok: n.success,
						at: Date.now(),
						error: r || void 0
					}
				}, n.success || (this._error = B(t.strings, "action_test.failed_detail", {
					action: e.name,
					detail: r
				}));
			} finally {
				this._busy = !1;
			}
		}
	}
	static {
		this.styles = [
			V,
			H,
			o`
      :host {
        display: block;
      }
      .subtabs {
        display: flex;
        gap: 4px;
        margin-bottom: 16px;
        border-bottom: 1px solid var(--divider-color);
        overflow-x: auto;
      }
      .subtabs button {
        font: inherit;
        font-size: 14px;
        background: none;
        border: none;
        border-bottom: 2px solid transparent;
        color: var(--secondary-text-color);
        padding: 8px 14px;
        cursor: pointer;
        white-space: nowrap;
      }
      .subtabs button[aria-selected="true"] {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color);
      }
      .notice.info {
        border-left-color: var(--info-color, #0277bd);
        margin: 0 0 16px;
      }
      /* The two tabs that write say so in the colour of what they do: the
         walk test holds the whole response back, the action test really
         sounds the siren. */
      .notice.danger {
        border-left-color: var(--error-color, #d32f2f);
        margin: 0 0 16px;
      }
      .notice.warn {
        margin: 0 0 16px;
      }
      .card-hd .btn.danger {
        margin-left: auto;
      }
      .split {
        display: grid;
        gap: 16px;
        grid-template-columns: minmax(280px, 380px) 1fr;
        align-items: start;
      }
      @media (max-width: 900px) {
        .split {
          grid-template-columns: 1fr;
        }
      }
      .override {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .override select {
        flex: 1 1 140px;
      }
      .state-input {
        flex: 0 1 90px;
      }
      .at-input {
        flex: 0 0 76px;
      }
      ol.trace {
        list-style: none;
        margin: 0;
        padding: 0;
        font-size: 13.5px;
      }
      li.step {
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      li.step:last-child {
        border-bottom: none;
      }
      .when {
        color: var(--secondary-text-color);
        padding-top: 1px;
      }
      .what > div {
        margin-bottom: 2px;
      }
      .batch {
        margin: 6px 0 6px 0;
        padding-left: 10px;
        border-left: 2px solid var(--divider-color);
      }
      .key {
        color: var(--secondary-text-color);
      }
      .yes {
        color: var(--success-color, #2e9e4f);
      }
      .no {
        color: var(--error-color, #d32f2f);
      }
      .wait,
      .warn {
        color: var(--warning-color, #c77700);
      }
      td .hint {
        font-weight: 400;
      }
    `
		];
	}
};
function Nt(e, t) {
	if (!t) return "";
	let n = B(e, `action_test.reason.${t}`);
	return n.startsWith("action_test.reason.") ? t : n;
}
customElements.get("foyer-page-test") || customElements.define("foyer-page-test", Mt);
//#endregion
//#region src/panel/pages/contacts.ts
var Pt = {
	name: "",
	channels: [],
	quiet_start: null,
	quiet_end: null,
	quiet_min_severity: "alarm",
	linked_user_id: null,
	enabled: !0
}, Ft = {
	kind: "push",
	service: "",
	target: "",
	data: {},
	actionable: !1,
	enabled: !0
}, It = [
	"push",
	"disarm",
	"dtmf",
	"service"
];
function Lt(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) {
		let e = n.actions.filter((e) => e.enabled && e.escalation_offset !== null).sort((e, t) => (e.escalation_offset ?? 0) - (t.escalation_offset ?? 0)).map((e, t) => ({
			profile: n,
			action: e,
			index: t
		}));
		e.length && t.set(n.id ?? n.name, e);
	}
	return t;
}
function Rt(e) {
	let t = e.params.contacts;
	return Array.isArray(t) ? t.map((e) => typeof e == "string" ? {
		contact_id: e,
		channel_id: null
	} : e).filter((e) => e && e.contact_id) : [];
}
var zt = class extends I {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1, this._tested = {};
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_tested: { state: !0 }
		};
	}
	_edit(e) {
		this._draft = e ? structuredClone(e) : {
			...structuredClone(Pt),
			channels: [structuredClone(Ft)]
		}, this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	_setChannel(e, t) {
		if (!this._draft) return;
		let n = this._draft.channels.map((n, r) => r === e ? {
			...n,
			...t
		} : n);
		this._draft = {
			...this._draft,
			channels: n
		};
	}
	_move(e, t) {
		if (!this._draft) return;
		let n = [...this._draft.channels], r = e + t;
		r < 0 || r >= n.length || ([n[e], n[r]] = [n[r], n[e]], this._draft = {
			...this._draft,
			channels: n
		});
	}
	_addChannel() {
		this._draft &&= {
			...this._draft,
			channels: [...this._draft.channels, structuredClone(Ft)]
		};
	}
	_removeChannel(e) {
		this._draft &&= {
			...this._draft,
			channels: this._draft.channels.filter((t, n) => n !== e)
		};
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("contact", this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("contact", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _test(e, t) {
		if (this.ctx && e.id && t.id) {
			this._busy = !0;
			try {
				let n = await this.ctx.testAction({
					contact_id: e.id,
					channel_id: t.id
				});
				this._tested = {
					...this._tested,
					[t.id]: {
						ok: n.success,
						error: n.error ?? Nt(this.ctx.strings, n.reason ?? null)
					}
				};
			} finally {
				this._busy = !1;
			}
		}
	}
	_isEntity(e) {
		return !!(e && this.ctx?.hass.states[e]);
	}
	async _toggleWebhook(e) {
		if (this.ctx) {
			this._busy = !0;
			try {
				await this.ctx.setAckWebhook(e);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = e.config.contacts ?? [];
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(t, "contacts.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${B(t, "contacts.add")}
          </button>
        </div>
        ${n.length ? D`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${B(t, "field.name")}</th>
                    <th>${B(t, "contacts.channels_order")}</th>
                    <th>${B(t, "contacts.quiet_hours")}</th>
                    <th>${B(t, "field.linked_user_id")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${n.map((e) => this._row(t, e))}
                </tbody>
              </table>
            </div>` : D`<div class="empty">${B(t, "contacts.none")}</div>`}
        <div class="card-bd">
          <p class="note">${B(t, "contacts.orchestration")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : k}
      ${this._renderPolicies(t)} ${this._renderAcknowledgement(t)}
    `;
	}
	_row(e, t) {
		let n = (this.ctx?.config?.users ?? []).find((e) => e.id === t.linked_user_id);
		return D`<tr
      class="clickable"
      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
      @click=${() => this._edit(t)}
    >
      <td><strong>${t.name}</strong></td>
      <td>
        <div class="channels">
          ${t.channels.map((t, n) => D`<span class="tag"
                >${n + 1}. ${B(e, `channel_kind.${t.kind}`)} ·
                ${t.service}</span
              >`)}
        </div>
      </td>
      <td class="mono">
        ${t.quiet_start ? `${t.quiet_start}–${t.quiet_end}` : B(e, "contacts.no_quiet_hours")}
      </td>
      <td>${n?.name ?? "—"}</td>
    </tr>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.config?.users ?? [], i = J(n.hass), a = n.meta?.contact_channel_kinds ?? [
			"push",
			"sms",
			"voice",
			"chat",
			"other"
		];
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "contacts.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.linked_user_id")}</span>
              <select
                @change=${(e) => this._set("linked_user_id", e.target.value || null)}
              >
                <option value="" ?selected=${!t.linked_user_id}>—</option>
                ${r.map((e) => D`<option
                    .value=${e.id ?? ""}
                    ?selected=${e.id === t.linked_user_id}
                  >
                    ${e.name}
                  </option>`)}
              </select>
              <span class="hint">${B(e, "contacts.linked_hint")}</span>
            </label>
          </div>

          <h3>${B(e, "contacts.channels")}</h3>
          <p class="note">${B(e, "contacts.channels_hint")}</p>
          ${t.channels.map((n, r) => this._renderChannel(e, t, n, r, i, a))}
          <button class="btn" @click=${() => this._addChannel()}>
            ${B(e, "contacts.add_channel")}
          </button>

          <h3>${B(e, "contacts.quiet_hours")}</h3>
          <p class="note">${B(e, "contacts.quiet_hint")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.quiet_start")}</span>
              <input
                type="time"
                .value=${t.quiet_start ?? ""}
                @change=${(e) => this._set("quiet_start", e.target.value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.quiet_end")}</span>
              <input
                type="time"
                .value=${t.quiet_end ?? ""}
                @change=${(e) => this._set("quiet_end", e.target.value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "contacts.quiet_min_severity")}</span>
              <select
                @change=${(e) => this._set("quiet_min_severity", e.target.value)}
              >
                ${[
			"info",
			"warning",
			"alarm"
		].map((n) => D`<option
                    .value=${n}
                    ?selected=${n === t.quiet_min_severity}
                  >
                    ${B(e, `severity.${n}`)}
                  </option>`)}
              </select>
              <span class="hint">${B(e, "contacts.quiet_severity_hint")}</span>
            </label>
          </div>

          ${this._problems.map((t) => D`<p class="problem">${U(e, t)}</p>`)}
        </div>
        <div class="card-ft">
          ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${() => this._delete()}>
                ${B(e, "common.delete")}
              </button>` : k}
          <button class="btn" @click=${() => this._draft = void 0}>
            ${B(e, "common.cancel")}
          </button>
          <button class="btn primary" ?disabled=${this._busy} @click=${() => this._save()}>
            ${B(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	_renderChannel(e, t, n, r, i, a) {
		let o = n.id ? this._tested[n.id] : void 0, s = i.some((e) => e.id === n.service) ? i : [...i, {
			id: n.service,
			name: n.service
		}].filter((e) => e.id);
		return D`
      <div class="channel">
        <div class="channel-hd">
          <span class="rank">${r + 1}</span>
          <div class="channel-tools">
            <button class="btn sm" @click=${() => this._move(r, -1)}>↑</button>
            <button class="btn sm" @click=${() => this._move(r, 1)}>↓</button>
            <button class="btn sm danger" @click=${() => this._removeChannel(r)}>
              ${B(e, "common.delete")}
            </button>
          </div>
        </div>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${B(e, "field.kind")}</span>
            <select
              @change=${(e) => this._setChannel(r, { kind: e.target.value })}
            >
              ${a.map((t) => D`<option .value=${t} ?selected=${t === n.kind}>
                  ${B(e, `channel_kind.${t}`)}
                </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${B(e, "contacts.service")}</span>
            <select
              @change=${(e) => this._setChannel(r, { service: e.target.value })}
            >
              <option value="" ?selected=${!n.service}>—</option>
              ${s.map((e) => D`<option
                  .value=${e.id}
                  ?selected=${e.id === n.service}
                >
                  ${e.name}
                </option>`)}
            </select>
            <span class="hint">${B(e, "contacts.service_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${B(e, "contacts.target")}</span>
            <input
              .value=${n.target}
              @input=${(e) => this._setChannel(r, { target: e.target.value })}
            />
            <span class="hint">${B(e, "contacts.target_hint")}</span>
          </label>
          <label class="check">
            <input
              type="checkbox"
              .checked=${n.actionable}
              @change=${(e) => this._setChannel(r, { actionable: e.target.checked })}
            />
            <span class="lbl">${B(e, "contacts.actionable")}</span>
            <span class="hint">
              ${B(e, this._isEntity(n.service) ? "contacts.actionable_entity" : "contacts.actionable_hint")}
            </span>
          </label>
        </div>
        <div class="channel-ft">
          <button
            class="btn sm"
            ?disabled=${this._busy || !t.id || !n.id}
            @click=${() => this._test(t, n)}
          >
            ${B(e, "contacts.test")}
          </button>
          ${t.id && n.id ? k : D`<span class="hint">${B(e, "contacts.test_after_save")}</span>`}
          ${o ? D`<span class=${o.ok ? "tag ok" : "tag bad"}>
                ${o.ok ? B(e, "contacts.test_sent") : o.error}
              </span>` : k}
        </div>
      </div>
    `;
	}
	_renderPolicies(e) {
		let t = this.ctx, n = t.config?.contacts ?? [], r = Lt(t.config?.profiles ?? []);
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "contacts.policies")}</h2>
          <button class="btn" @click=${() => t.navigate("profiles")}>
            ${B(e, "contacts.edit_on_profiles")}
          </button>
        </div>
        ${r.size ? D`<div class="card-bd">
              ${[...r.values()].map((t) => D`
                  <h3>${t[0].profile.name}</h3>
                  ${t.map(({ action: t, index: r }) => D`
                      <div class="step">
                        <span class="mono at">+${t.escalation_offset}s</span>
                        <div>
                          <div class="who">
                            ${Rt(t).map((t) => {
			let r = n.find((e) => e.id === t.contact_id), i = r?.channels.find((e) => e.id === t.channel_id);
			return i ? `${r?.name} · ${B(e, `channel_kind.${i.kind}`)}` : r?.name ?? B(e, "problem.unknown_contact");
		}).join(" · ") || String(t.params.service ?? "")}
                          </div>
                          <div class="mono">
                            ${B(e, "contacts.step_number")} ${r} ·
                            ${B(e, `moment.${t.moments[0]}`)}
                          </div>
                        </div>
                      </div>
                    `)}
                `)}
              <p class="note">${B(e, "contacts.exhausted")}</p>
            </div>` : D`<div class="empty">${B(e, "contacts.no_policies")}</div>`}
      </div>
    `;
	}
	_renderAcknowledgement(e) {
		let t = this.ctx.config?.settings.ack_webhook_id ?? null;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "contacts.acknowledgement")}</h2>
        </div>
        <div class="card-bd">
          <p class="note">${B(e, "contacts.ack_stops")}</p>
          ${It.map((t) => D`<div class="path">
              <div class="who">${B(e, `contacts.ack_${t}`)}</div>
              <div class="mono">${B(e, `contacts.ack_${t}_how`)}</div>
            </div>`)}
          <h3>${B(e, "contacts.webhook")}</h3>
          <div class="banner warn">
            <strong>${B(e, "contacts.webhook_warning")}</strong>
            <span>${B(e, "contacts.webhook_warning_hint")}</span>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t !== null}
              ?disabled=${this._busy}
              @change=${(e) => this._toggleWebhook(e.target.checked)}
            />
            <span class="lbl">${B(e, "contacts.webhook_enable")}</span>
          </label>
          ${t ? D`<p class="sample">/api/webhook/${t}</p>
                <p class="note">${B(e, "contacts.webhook_hint")}</p>` : k}
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			H,
			V,
			o`
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
    `
		];
	}
};
customElements.define("foyer-page-contacts", zt);
//#endregion
//#region src/panel/pages/rules.ts
var Bt = [
	0,
	1,
	2,
	3,
	4,
	5,
	6
];
function Vt(e) {
	return e ? new Date(e).toLocaleString(void 0, {
		dateStyle: "short",
		timeStyle: "short"
	}) : "";
}
function Ht() {
	return {
		name: "",
		trigger: {
			kind: "absence",
			entity_ids: [],
			state: null,
			minutes: 30,
			at: null,
			weekdays: []
		},
		action: "arm",
		scenario_id: null,
		area_ids: [],
		window: {
			weekdays: [],
			after: null,
			before: null
		},
		guards: {
			only_when_disarmed: !0,
			only_when_ready: !0,
			quiet_minutes: null
		},
		grace_seconds: 120,
		notify_contact_ids: [],
		enabled: !0
	};
}
var Ut = class extends I {
	constructor(...e) {
		super(...e), this._visitor = {
			name: "",
			start: "",
			until: "",
			reduced_scenario_id: null
		}, this._problems = [], this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_visitor: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_error: { state: !0 }
		};
	}
	get _auto() {
		return this.ctx?.status?.auto;
	}
	_edit(e) {
		this._draft = e ? structuredClone(e) : Ht(), this._problems = [];
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	_setTrigger(e, t) {
		this._draft && this._set("trigger", {
			...this._draft.trigger,
			[e]: t
		});
	}
	_setGuard(e, t) {
		this._draft && this._set("guards", {
			...this._draft.guards,
			[e]: t
		});
	}
	_setWindow(e, t) {
		this._draft && this._set("window", {
			...this._draft.window,
			[e]: t
		});
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("rule", this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _delete() {
		if (this.ctx && this._draft?.id) {
			this._busy = !0;
			try {
				let e = await this.ctx.remove("rule", this._draft.id);
				this._problems = e.problems, e.success && (this._draft = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _run(e) {
		this._busy = !0, this._error = void 0;
		try {
			let t = await e();
			t.success || (this._error = B(this.ctx.strings, `reason.${t.reason ?? "unknown"}`));
		} finally {
			this._busy = !1;
		}
	}
	async _addVisitor() {
		let e = this.ctx, t = this._visitor;
		e && t.name.trim() && t.until && (await this._run(() => e.suspend({
			kind: "visitor",
			name: t.name.trim(),
			start: t.start ? new Date(t.start).toISOString() : null,
			until: new Date(t.until).toISOString(),
			reduced_scenario_id: t.reduced_scenario_id
		})), this._visitor = {
			name: "",
			start: "",
			until: "",
			reduced_scenario_id: null
		});
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings, n = this._auto;
		return D`
      ${this._renderNext(t)}
      ${this._error ? D`<div class="problems" role="alert">${this._error}</div>` : k}
      ${this._renderRules(t)}
      ${this._draft ? this._renderEditor(t, this._draft) : k}
      ${this._renderSuspensions(t, n?.suspensions ?? [])}
      ${this._renderDisarming(t)}
    `;
	}
	_renderNext(e) {
		let t = this.ctx, n = this._auto, r = n?.next, i = n?.pending ?? [];
		return n?.enabled ? i.length ? D`${i.map((n) => D`<div class="banner crit">
          <div>
            ${B(e, `rules.counting_${n.action}`, {
			rule: n.rule_name,
			scenario: this._scenarioName(n.scenario_id),
			seconds: Math.max(0, Math.round((Date.parse(n.due) - t.now()) / 1e3))
		})}
          </div>
          <span class="spacer"></span>
          <button
            class="btn sm primary"
            ?disabled=${this._busy}
            @click=${() => this._run(() => t.cancelAuto(n.id))}
          >
            ${B(e, "rules.cancel_now")}
          </button>
        </div>`)}` : D`<div class="banner info">
      <div>
        ${r ? B(e, `rules.next_${r.action}`, {
			rule: r.rule_name,
			scenario: this._scenarioName(r.scenario_id),
			when: Vt(r.at)
		}) : B(e, "rules.next_none")}
      </div>
      <span class="spacer"></span>
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => t.setAutoArming(!1))}
      >
        ${B(e, "rules.switch_off")}
      </button>
    </div>` : D`<div class="banner warn">
        <div>${B(e, "rules.switched_off")}</div>
        <span class="spacer"></span>
        <button
          class="btn sm"
          ?disabled=${this._busy}
          @click=${() => this._run(() => t.setAutoArming(!0))}
        >
          ${B(e, "rules.switch_on")}
        </button>
      </div>`;
	}
	_scenarioName(e) {
		return e ? this.ctx?.config?.scenarios.find((t) => t.id === e)?.name ?? "" : "";
	}
	_triggerText(e, t) {
		let n = t.trigger, r = n.entity_ids.length;
		switch (n.kind) {
			case "absence": return B(e, "rules.trigger_absence", {
				n: r,
				minutes: n.minutes
			});
			case "presence": return B(e, "rules.trigger_presence", { n: r });
			case "time": return B(e, "rules.trigger_time", {
				at: n.at ?? "",
				days: this._days(e, n.weekdays)
			});
			default: return B(e, "rules.trigger_entity", {
				entity: n.entity_ids[0] ?? "",
				state: n.state ?? "",
				minutes: n.minutes
			});
		}
	}
	_days(e, t) {
		return t.length ? t.map((t) => B(e, `rules.weekday_${t}`)).join(", ") : B(e, "rules.every_day");
	}
	_actionText(e, t) {
		if (t.action === "disarm") {
			let n = this.ctx?.config?.areas ?? [];
			return B(e, "rules.action_disarm", { areas: t.area_ids.map((e) => n.find((t) => t.id === e)).filter((e) => e !== void 0).map((e) => e.name).join(", ") });
		}
		return B(e, `rules.action_${t.action}`, { scenario: this._scenarioName(t.scenario_id) });
	}
	_guardText(e, t) {
		let n = [];
		return t.guards.only_when_disarmed && n.push(B(e, "rules.guard_disarmed")), t.guards.only_when_ready && n.push(B(e, "rules.guard_ready")), t.guards.quiet_minutes !== null && n.push(B(e, "rules.guard_quiet", { minutes: t.guards.quiet_minutes })), n.length ? n.join(" · ") : B(e, "rules.guard_none");
	}
	_renderRules(e) {
		let t = this.ctx.config?.rules ?? [], n = this._auto?.blocked ?? {};
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "rules.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${B(e, "rules.add")}
          </button>
        </div>
        ${t.length ? D`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${B(e, "field.name")}</th>
                    <th>${B(e, "field.trigger")}</th>
                    <th>${B(e, "rules.action")}</th>
                    <th>${B(e, "field.window")}</th>
                    <th>${B(e, "field.guards")}</th>
                    <th>${B(e, "field.grace_seconds")}</th>
                    <th>${B(e, "rules.status")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${t.map((t) => D`<tr
                      class="clickable"
                      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
                      @click=${() => this._edit(t)}
                    >
                      <td><strong>${t.name}</strong></td>
                      <td>${this._triggerText(e, t)}</td>
                      <td>
                        <span class=${t.action === "arm" ? "pill ok" : "pill warn"}>
                          ${this._actionText(e, t)}
                        </span>
                      </td>
                      <td class="muted">
                        ${t.window.after && t.window.before ? `${this._days(e, t.window.weekdays)} ${t.window.after}–${t.window.before}` : this._days(e, t.window.weekdays)}
                      </td>
                      <td class="muted small">${this._guardText(e, t)}</td>
                      <td class="num">
                        ${t.grace_seconds ? B(e, "common.seconds", { n: t.grace_seconds }) : B(e, "rules.at_once")}
                      </td>
                      <td>
                        ${t.enabled ? n[t.id ?? ""] ? D`<span class="pill warn"
                                >${B(e, `rules.block_${n[t.id ?? ""]}`)}</span
                              >` : D`<span class="pill ok">${B(e, "rules.active")}</span>` : D`<span class="pill idle">${B(e, "rules.disabled")}</span>`}
                      </td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : D`<div class="empty">${B(e, "rules.none")}</div>`}
      </div>
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = q(n.hass, n.meta?.presence_domains ?? ["person"]), i = n.meta?.max_grace_seconds ?? 900, a = n.meta?.max_rule_minutes ?? 1440, o = t.trigger;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : B(e, "rules.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.trigger")}</span>
              <select
                @change=${(e) => this._setTrigger("kind", e.target.value)}
              >
                ${(n.meta?.rule_triggers ?? []).map((t) => D`<option .value=${t} ?selected=${t === o.kind}>
                      ${B(e, `rules.trigger_kind_${t}`)}
                    </option>`)}
              </select>
              <span class="hint">${B(e, `rules.trigger_hint_${o.kind}`)}</span>
            </label>
            ${o.kind === "time" ? D`<label class="field">
                  <span class="lbl">${B(e, "rules.at")}</span>
                  <input
                    type="time"
                    .value=${o.at ?? ""}
                    @change=${(e) => this._setTrigger("at", e.target.value || null)}
                  />
                </label>` : D`<label class="field">
                  <span class="lbl">${B(e, "rules.for_minutes")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${a}
                    .value=${String(o.minutes)}
                    ?disabled=${o.kind === "presence"}
                    @input=${(e) => this._setTrigger("minutes", W(e.target.value) ?? 0)}
                  />
                </label>`}
          </div>

          ${o.kind === "absence" || o.kind === "presence" ? D`<div class="block">
                <div class="lbl strong">${B(e, "rules.people")}</div>
                <div class="chips">
                  ${r.length ? r.map((e) => D`<label class="chip">
                          <input
                            type="checkbox"
                            .checked=${o.entity_ids.includes(e.id)}
                            @change=${(t) => this._setTrigger("entity_ids", t.target.checked ? [...o.entity_ids, e.id] : o.entity_ids.filter((t) => t !== e.id))}
                          />
                          <span>${e.name}</span>
                        </label>`) : D`<span class="hint">${B(e, "rules.no_people")}</span>`}
                </div>
                <span class="hint">${B(e, "rules.people_hint")}</span>
              </div>` : k}
          ${o.kind === "entity" ? D`<div class="grid-form">
                <label class="field">
                  <span class="lbl">${B(e, "field.entity_id")}</span>
                  <input
                    .value=${o.entity_ids[0] ?? ""}
                    @change=${(e) => this._setTrigger("entity_ids", [e.target.value].filter(Boolean))}
                  />
                </label>
                <label class="field">
                  <span class="lbl">${B(e, "field.state")}</span>
                  <input
                    .value=${o.state ?? ""}
                    @change=${(e) => this._setTrigger("state", e.target.value || null)}
                  />
                </label>
              </div>` : k}
          ${o.kind === "time" ? this._renderDays(e, o.weekdays, (e) => this._setTrigger("weekdays", e)) : k}

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "rules.action")}</span>
              <select
                @change=${(e) => this._set("action", e.target.value)}
              >
                ${(n.meta?.rule_actions ?? []).map((n) => D`<option .value=${n} ?selected=${n === t.action}>
                      ${B(e, `rules.action_kind_${n}`)}
                    </option>`)}
              </select>
            </label>
            ${t.action === "disarm" ? k : D`<label class="field">
                  <span class="lbl">${B(e, "field.scenario_id")}</span>
                  <select
                    @change=${(e) => this._set("scenario_id", e.target.value || null)}
                  >
                    <option value="" ?selected=${!t.scenario_id}>
                      ${B(e, "rules.choose_scenario")}
                    </option>
                    ${(n.config?.scenarios ?? []).map((e) => D`<option .value=${e.id ?? ""} ?selected=${e.id === t.scenario_id}>
                          ${e.name}
                        </option>`)}
                  </select>
                </label>`}
          </div>
          ${t.action === "disarm" ? this._renderDisarmAreas(e, t) : k}

          <div class="hr"></div>
          <div class="lbl strong">${B(e, "field.window")}</div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.after")}</span>
              <input
                type="time"
                .value=${t.window.after ?? ""}
                @change=${(e) => this._setWindow("after", e.target.value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.before")}</span>
              <input
                type="time"
                .value=${t.window.before ?? ""}
                @change=${(e) => this._setWindow("before", e.target.value || null)}
              />
            </label>
          </div>
          ${this._renderDays(e, t.window.weekdays, (e) => this._setWindow("weekdays", e))}
          <span class="hint">${B(e, "rules.window_hint")}</span>

          <div class="hr"></div>
          <div class="lbl strong">${B(e, "field.guards")}</div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.guards.only_when_disarmed}
              @change=${(e) => this._setGuard("only_when_disarmed", e.target.checked)}
            />
            <span>${B(e, "rules.guard_disarmed")}</span>
          </label>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.guards.only_when_ready}
              @change=${(e) => this._setGuard("only_when_ready", e.target.checked)}
            />
            <span>
              ${B(e, "rules.guard_ready")}
              <span class="hint">${B(e, "rules.guard_ready_hint")}</span>
            </span>
          </label>
          <label class="field">
            <span class="lbl">${B(e, "rules.guard_quiet_label")}</span>
            <input
              type="number"
              min="1"
              max=${a}
              .value=${t.guards.quiet_minutes === null ? "" : String(t.guards.quiet_minutes)}
              @input=${(e) => this._setGuard("quiet_minutes", W(e.target.value))}
            />
            <span class="hint">${B(e, "rules.guard_quiet_hint")}</span>
          </label>

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.grace_seconds")}</span>
              <input
                type="number"
                min="0"
                max=${i}
                .value=${String(t.grace_seconds)}
                @input=${(e) => this._set("grace_seconds", W(e.target.value) ?? 0)}
              />
              <span class="hint">${B(e, "rules.grace_hint")}</span>
            </label>
          </div>
          <div class="block">
            <div class="lbl strong">${B(e, "field.notify_contact_ids")}</div>
            <div class="chips">
              ${(n.config?.contacts ?? []).map((e) => D`<label class="chip">
                  <input
                    type="checkbox"
                    .checked=${t.notify_contact_ids.includes(e.id ?? "")}
                    @change=${(n) => this._set("notify_contact_ids", n.target.checked ? [...t.notify_contact_ids, e.id ?? ""] : t.notify_contact_ids.filter((t) => t !== e.id))}
                  />
                  <span>${e.name}</span>
                </label>`)}
            </div>
            <span class="hint">${B(e, "rules.notify_hint")}</span>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.enabled}
              @change=${(e) => this._set("enabled", e.target.checked)}
            />
            <span>${B(e, "rules.enabled")}</span>
          </label>

          ${this._problems.length ? D`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                </ul>
              </div>` : k}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${B(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${B(e, "common.cancel")}
            </button>
            ${t.id ? D`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${B(e, "common.delete")}
                </button>` : k}
          </div>
        </div>
      </div>
    `;
	}
	_renderDays(e, t, n) {
		return D`<div class="chips days">
      ${Bt.map((r) => D`<label class="chip">
          <input
            type="checkbox"
            .checked=${t.includes(r)}
            @change=${(e) => n(e.target.checked ? [...t, r].sort((e, t) => e - t) : t.filter((e) => e !== r))}
          />
          <span>${B(e, `rules.weekday_${r}`)}</span>
        </label>`)}
    </div>`;
	}
	_renderDisarmAreas(e, t) {
		let n = this.ctx?.config?.areas ?? [];
		return D`<div class="block">
      <div class="lbl strong">${B(e, "field.area_ids")}</div>
      <div class="chips">
        ${n.map((n) => {
			let r = t.area_ids.includes(n.id ?? "");
			return D`<label class=${n.is_perimeter ? "chip never" : "chip"}>
            <input
              type="checkbox"
              .checked=${r}
              ?disabled=${n.is_perimeter}
              @change=${(e) => this._set("area_ids", e.target.checked ? [...t.area_ids, n.id ?? ""] : t.area_ids.filter((e) => e !== n.id))}
            />
            <span>
              ${n.name}
              ${n.is_perimeter ? D`<em>&nbsp;· ${B(e, "rules.never_disarmed")}</em>` : k}
            </span>
          </label>`;
		})}
      </div>
    </div>`;
	}
	_renderSuspensions(e, t) {
		let n = this.ctx, r = n.config?.rules ?? [], i = this._visitor;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "rules.suspensions")}</h2>
        </div>
        <div class="card-bd">
          <p class="hint">${B(e, "rules.visitor_intro")}</p>
          ${t.length ? D`<div class="stack">
                ${t.map((t) => D`<div class="suspension">
                    <div>
                      <div class="lbl strong">
                        ${t.name ?? B(e, `rules.suspension_${t.kind}`)}
                      </div>
                      <div class="hint mono">
                        ${t.kind === "next" ? B(e, "rules.suspension_next_hint") : `${Vt(t.start)} – ${Vt(t.until)}`}
                        ${t.rule_ids.length ? ` · ${t.rule_ids.map((e) => r.find((t) => t.id === e)?.name ?? e).join(", ")}` : ` · ${B(e, "rules.every_rule")}`}
                        ${t.reduced_scenario_id ? ` · ${B(e, "rules.instead", { scenario: this._scenarioName(t.reduced_scenario_id) })}` : ""}
                      </div>
                    </div>
                    <span class="spacer"></span>
                    <button
                      class="btn sm"
                      ?disabled=${this._busy}
                      @click=${() => this._run(() => n.liftSuspension(t.id))}
                    >
                      ${B(e, "rules.lift")}
                    </button>
                  </div>`)}
              </div>` : D`<div class="empty">${B(e, "rules.no_suspensions")}</div>`}

          <div class="hr"></div>
          <div class="lbl strong">${B(e, "rules.visitor")}</div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "rules.reason")}</span>
              <input
                .value=${i.name}
                placeholder=${B(e, "rules.reason_placeholder")}
                @input=${(e) => this._visitor = {
			...i,
			name: e.target.value
		}}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.after")}</span>
              <input
                type="datetime-local"
                .value=${i.start}
                @change=${(e) => this._visitor = {
			...i,
			start: e.target.value
		}}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.before")}</span>
              <input
                type="datetime-local"
                .value=${i.until}
                @change=${(e) => this._visitor = {
			...i,
			until: e.target.value
		}}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "rules.instead_label")}</span>
              <select
                @change=${(e) => this._visitor = {
			...i,
			reduced_scenario_id: e.target.value || null
		}}
              >
                <option value="" ?selected=${!i.reduced_scenario_id}>
                  ${B(e, "rules.instead_nothing")}
                </option>
                ${(n.config?.scenarios ?? []).map((e) => D`<option
                      .value=${e.id ?? ""}
                      ?selected=${e.id === i.reduced_scenario_id}
                    >
                      ${e.name}
                    </option>`)}
              </select>
              <span class="hint">${B(e, "rules.instead_hint")}</span>
            </label>
          </div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !i.name.trim() || !i.until}
              @click=${this._addVisitor}
            >
              ${B(e, "rules.add_visitor")}
            </button>
            ${(n.config?.rules ?? []).length ? D`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._run(() => n.suspend({
			kind: "next",
			rule_ids: []
		}))}
                >
                  ${B(e, "rules.skip_next")}
                </button>` : k}
          </div>
        </div>
      </div>
    `;
	}
	_renderDisarming(e) {
		let t = this.ctx, n = t.config?.settings.allow_auto_disarm ?? !1, r = t.config?.areas ?? [];
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "rules.disarming")}</h2>
        </div>
        <div class="card-bd">
          <div class="notice">${B(e, "rules.disarming_warning")}</div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${n}
              ?disabled=${this._busy || !t.isAdmin}
              @change=${async (e) => {
			let n = e.target.checked;
			this._busy = !0;
			try {
				await t.saveSettings({ allow_auto_disarm: n });
			} finally {
				this._busy = !1;
			}
		}}
            />
            <span>
              ${B(e, "rules.allow_disarm")}
              <span class="hint">${B(e, "rules.allow_disarm_hint")}</span>
            </span>
          </label>
          <div class="hr"></div>
          <div class="lbl strong">${B(e, "rules.areas_a_rule_may_disarm")}</div>
          <div class="chips">
            ${r.map((t) => D`<span class=${t.is_perimeter ? "pill bad" : "pill ok"}>
                  ${t.name}${t.is_perimeter ? ` · ${B(e, "rules.never_disarmed")}` : ""}
                </span>`)}
          </div>
          <p class="hint">${B(e, "rules.perimeter_note")}</p>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			V,
			H,
			o`
      .banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        font-size: 13.5px;
      }
      .banner.warn {
        border-color: var(--warning-color, #c77700);
      }
      .banner.crit {
        border-color: var(--error-color, #d32f2f);
      }
      .spacer {
        flex: 1;
      }
      .block {
        margin-top: 14px;
      }
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 6px 0;
      }
      label.chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 10px;
        border: 1px solid var(--divider-color);
        border-radius: 999px;
        font-size: 13px;
      }
      label.chip.never {
        opacity: 0.7;
        border-style: dashed;
      }
      label.chip em {
        color: var(--secondary-text-color);
        font-style: normal;
      }
      .lbl.strong {
        font-weight: 500;
        display: block;
        margin: 14px 0 6px;
        font-size: 13px;
      }
      .suspension {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
      }
      .stack {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .hr {
        height: 1px;
        background: var(--divider-color);
        margin: 16px 0;
        border: 0;
      }
      td.small {
        font-size: 12.5px;
      }
    `
		];
	}
};
customElements.get("foyer-page-rules") || customElements.define("foyer-page-rules", Ut);
//#endregion
//#region src/panel/pages/log.ts
var X = 50, Wt = class extends I {
	constructor(...e) {
		super(...e), this._rows = [], this._total = 0, this._offset = 0, this._filters = {}, this._busy = !1, this._confirmClear = !1, this._loaded = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_rows: { state: !0 },
			_total: { state: !0 },
			_offset: { state: !0 },
			_filters: { state: !0 },
			_busy: { state: !0 },
			_error: { state: !0 },
			_open: { state: !0 },
			_confirmClear: { state: !0 }
		};
	}
	updated() {
		!this._loaded && this.ctx && (this._loaded = !0, this._load());
	}
	async _load() {
		if (this.ctx) {
			this._busy = !0, this._error = void 0;
			try {
				let e = await this.ctx.queryLog({
					...this._filters,
					limit: X,
					offset: this._offset
				});
				this._rows = e.rows, this._total = e.total;
			} catch (e) {
				this._rows = [], this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	_filter(e) {
		this._filters = {
			...this._filters,
			...e
		}, this._offset = 0, this._load();
	}
	async _export(e) {
		if (this.ctx) {
			this._busy = !0;
			try {
				let t = await this.ctx.exportLog(this._filters, e);
				ze(t.filename, t.content, e === "csv" ? "text/csv" : "application/json"), t.truncated && (this._error = B(this.ctx.strings, "log.truncated", {
					rows: t.rows,
					total: t.total
				}));
			} catch (e) {
				this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _clear() {
		if (this.ctx) {
			this._confirmClear = !1, this._busy = !0;
			try {
				await this.ctx.clearLog(), this._offset = 0, await this._load();
			} catch (e) {
				this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e) return k;
		let t = e.strings;
		return D`${this._renderFilters(t)} ${this._renderRows(t)}`;
	}
	_vocabulary(e, t, n) {
		if (n?.length) return n;
		let r = e[t];
		return r && typeof r == "object" ? Object.keys(r) : [];
	}
	_renderFilters(e) {
		let t = this.ctx, n = this._vocabulary(e, "category", t.meta?.log_categories), r = this._vocabulary(e, "severity", t.meta?.log_severities), i = this._vocabulary(e, "outcome", t.meta?.outcomes), a = this._filters.categories ?? [];
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "log.filters")}</h2></div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "log.from")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.start ?? ""}
                @change=${(e) => this._filter({ start: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "log.to")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.end ?? ""}
                @change=${(e) => this._filter({ end: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "log.area")}</span>
              <select
                @change=${(e) => this._filter({ area_id: e.target.value || null })}
              >
                <option value="">${B(e, "log.all")}</option>
                ${t.status.areas.map((e) => D`<option .value=${e.id} ?selected=${e.id === this._filters.area_id}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "log.zone")}</span>
              <select
                @change=${(e) => this._filter({ zone_id: e.target.value || null })}
              >
                <option value="">${B(e, "log.all")}</option>
                ${t.status.zones.map((e) => D`<option .value=${e.id} ?selected=${e.id === this._filters.zone_id}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "log.severity")}</span>
              <select
                @change=${(e) => this._filter({ severity: e.target.value || null })}
              >
                <option value="">${B(e, "log.all")}</option>
                ${r.map((t) => D`<option .value=${t} ?selected=${t === this._filters.severity}>
                      ${B(e, `severity.${t}`)}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "log.outcome")}</span>
              <select
                @change=${(e) => this._filter({ outcome: e.target.value || null })}
              >
                <option value="">${B(e, "log.all")}</option>
                ${i.map((t) => D`<option .value=${t} ?selected=${t === this._filters.outcome}>
                      ${B(e, `outcome.${t}`)}
                    </option>`)}
              </select>
            </label>
          </div>
          <fieldset>
            <legend>${B(e, "log.categories")}</legend>
            <div class="chips">
              ${n.map((t) => D`
                  <button
                    class="chip"
                    aria-pressed=${a.includes(t) ? "true" : "false"}
                    @click=${() => this._filter({ categories: a.includes(t) ? a.filter((e) => e !== t) : [...a, t] })}
                  >
                    ${B(e, `category.${t}`)}
                  </button>
                `)}
            </div>
            <p class="hint">${B(e, "log.categories_hint")}</p>
          </fieldset>
          ${this._filters.incident_id ? D`<p class="hint">
                ${B(e, "log.incident_filter", { id: this._filters.incident_id })}
                <button class="btn small" @click=${() => this._filter({ incident_id: null })}>
                  ${B(e, "log.clear_filter")}
                </button>
              </p>` : k}
        </div>
      </div>
    `;
	}
	_renderRows(e) {
		let t = this.ctx, n = this._rows.length;
		return D`
      <div class="card">
        <div class="card-hd">
          <h2>${B(e, "log.events")}</h2>
          <span class="hint"
            >${B(e, "log.count", {
			shown: n ? `${this._offset + 1}–${this._offset + n}` : "0",
			total: this._total
		})}</span
          >
          <button class="btn" ?disabled=${this._busy} @click=${() => void this._load()}>
            ${B(e, "log.refresh")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("csv")}>
            ${B(e, "log.export_csv")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("json")}>
            ${B(e, "log.export_json")}
          </button>
          ${t.isAdmin ? D`<button class="btn danger" ?disabled=${this._busy} @click=${() => this._confirmClear = !0}>
                ${B(e, "log.clear")}
              </button>` : k}
        </div>
        <div class="card-bd">
          ${this._error ? D`<div class="problems" role="alert">${this._error}</div>` : k}
          ${this._confirmClear ? D`<div class="problems" role="alert">
                <p>${B(e, "log.clear_confirm")}</p>
                <div class="actions">
                  <button class="btn danger" @click=${this._clear}>
                    ${B(e, "log.clear_yes")}
                  </button>
                  <button class="btn" @click=${() => this._confirmClear = !1}>
                    ${B(e, "common.cancel")}
                  </button>
                </div>
              </div>` : k}
          ${n === 0 ? D`<p class="hint">${B(e, this._busy ? "common.loading" : "log.empty")}</p>` : D`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${B(e, "log.time")}</th>
                      <th>${B(e, "log.event")}</th>
                      <th>${B(e, "log.category")}</th>
                      <th>${B(e, "log.where")}</th>
                      <th>${B(e, "log.who")}</th>
                      <th>${B(e, "log.detail")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this._rows.map((t) => this._renderRow(e, t))}
                  </tbody>
                </table>
              </div>`}
          ${this._total > X ? D`<div class="actions">
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset === 0}
                  @click=${() => {
			this._offset = Math.max(0, this._offset - X), this._load();
		}}
                >
                  ${B(e, "log.newer")}
                </button>
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset + X >= this._total}
                  @click=${() => {
			this._offset += X, this._load();
		}}
                >
                  ${B(e, "log.older")}
                </button>
              </div>` : k}
        </div>
      </div>
    `;
	}
	_renderRow(e, t) {
		let n = this.ctx, r = n.status.areas.find((e) => e.id === t.area_id), i = n.status.zones.find((e) => e.id === t.zone_id), a = this._open === t.id, o = [r?.name, i?.name].filter(Boolean).join(" · ");
		return D`
      <tr class="clickable" aria-selected=${a ? "true" : "false"} @click=${() => this._open = a ? void 0 : t.id}>
        <td class="mono">${new Date(t.ts).toLocaleString(n.hass.language)}</td>
        <td>
          <span class="state ${qt(t.severity)}">
            ${Gt(e, t.event_type)}
          </span>
        </td>
        <td><span class="tag">${B(e, `category.${t.category}`)}</span></td>
        <td>${o}</td>
        <td>
          ${t.user_name ?? (t.channel ? Kt(e, t.channel) : "")}
          ${t.detail?.attributed === "claimed" ? D`<span class="claimed">${B(e, "log.claimed")}</span>` : k}
        </td>
        <td class="detail">${this._summary(e, t)}</td>
      </tr>
      ${a ? D`<tr class="expanded">
            <td colspan="6">
              <dl class="kv">
                ${t.incident_id ? D`<dt>${B(e, "log.incident")}</dt>
                      <dd>
                        <button
                          class="btn small"
                          @click=${(e) => {
			e.stopPropagation(), this._filter({ incident_id: t.incident_id });
		}}
                        >
                          ${B(e, "log.show_incident")}
                        </button>
                      </dd>` : k}
                ${t.outcome ? D`<dt>${B(e, "log.outcome")}</dt>
                      <dd>${B(e, `outcome.${t.outcome}`)}</dd>` : k}
                ${t.channel ? D`<dt>${B(e, "log.channel")}</dt>
                      <dd>${Kt(e, t.channel)}</dd>` : k}
                ${this._changeLines(e, t).map((t, n) => D`<dt>${n ? "" : B(e, "log.changes")}</dt>
                    <dd>${t}</dd>`)}
                ${this._plainDetail(t).map(([t, n]) => D`<dt>${B(e, `detail.${t}`)}</dt>
                    <dd class="mono">${n}</dd>`)}
              </dl>
            </td>
          </tr>` : k}
    `;
	}
	_summary(e, t) {
		let n = this.ctx, r = t.detail ?? {};
		if (typeof r.reason == "string") {
			let t = Array.isArray(r.blocking_zones) ? r.blocking_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? String(e)).join(", ") : "";
			return B(e, `reason.${r.reason}`, { zones: t });
		}
		if (typeof r.error == "string") return r.error;
		if (t.event_type === "zone_state") return `${r.from ?? "?"} → ${r.to ?? "?"}`;
		if (t.event_type === "reloaded") return B(e, "log.gap_short", { seconds: String(r.gap_seconds ?? "") });
		if (t.event_type === "system_unavailable" && typeof r.down_since == "string") return B(e, "log.gap", {
			from: new Date(r.down_since).toLocaleString(n.hass.language),
			to: new Date(String(r.up_at)).toLocaleString(n.hass.language)
		});
		if (typeof r.kind == "string" && t.category === "action") return B(e, `action_kind.${r.kind}`);
		let i = this._changeLines(e, t);
		return i.length ? i.length > 2 ? `${i.slice(0, 2).join(" · ")} ${B(e, "log.and_more", { count: i.length - 2 })}` : i.join(" · ") : "";
	}
	_changeLines(e, t) {
		let n = t.detail?.changes;
		if (!n || typeof n != "object" || Array.isArray(n)) return [];
		let r = [];
		for (let [t, i] of Object.entries(n)) {
			let n = B(e, `config_kind.${t}`);
			if (typeof i != "object" || !i) {
				r.push(`${n}: ${this._value(e, i)}`);
				continue;
			}
			let a = i;
			if (!("added" in a || "removed" in a || "changed" in a)) {
				r.push(...this._fieldLines(e, n, a));
				continue;
			}
			for (let t of a.added ?? []) r.push(`${n} · ${B(e, "log.added")}: ${t}`);
			for (let t of a.removed ?? []) r.push(`${n} · ${B(e, "log.removed")}: ${t}`);
			let o = a.changed ?? {};
			for (let [t, i] of Object.entries(o)) r.push(...this._fieldLines(e, `${n} «${t}»`, i));
		}
		return r;
	}
	_fieldLines(e, t, n) {
		return Array.isArray(n) ? n.map((n) => `${t} · ${B(e, `field.${n}`)}`) : Object.entries(n).map(([n, r]) => {
			let i = B(e, `field.${n}`), a = i.startsWith("field.") ? n : i;
			return Array.isArray(r) && r.length === 2 ? `${t} · ${a}: ${this._value(e, r[0])} → ${this._value(e, r[1])}` : `${t} · ${a}: ${B(e, "log.changed")}`;
		});
	}
	_value(e, t) {
		return t == null || t === "" ? "—" : typeof t == "boolean" ? B(e, t ? "common.yes" : "common.no") : Array.isArray(t) ? t.length ? t.map((t) => this._value(e, t)).join(", ") : "—" : String(t);
	}
	_plainDetail(e) {
		let t = /* @__PURE__ */ new Set([
			"changes",
			"zone_ids",
			"blocking_zones"
		]);
		return Object.entries(e.detail ?? {}).filter(([e, n]) => !t.has(e) && n !== null && n !== "").map(([e, t]) => [e, typeof t == "object" ? JSON.stringify(t) : String(t)]);
	}
	static {
		this.styles = [
			V,
			H,
			o`
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
    `
		];
	}
};
function Gt(e, t) {
	let n = B(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = B(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
function Kt(e, t) {
	let n = B(e, `log_channel.${t}`);
	return n.startsWith("log_channel.") ? t : n;
}
function qt(e) {
	return e === "alarm" ? "triggered" : e === "warning" ? "arming" : "disarmed";
}
customElements.get("foyer-page-log") || customElements.define("foyer-page-log", Wt);
//#endregion
//#region src/panel/pages/settings.ts
var Jt = ["en", "it"], Yt = {
	targets: [],
	mode: "sound",
	sound: null,
	tts_entity: null,
	volume: null,
	quiet_start: null,
	quiet_end: null,
	during_exit: !1
}, Xt = class extends I {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1, this._saved = !1, this._restored = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_settings: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_saved: { state: !0 },
			_restored: { state: !0 }
		};
	}
	get _chime() {
		return this._draft ?? structuredClone(this.ctx?.config?.chime ?? Yt);
	}
	_set(e, t) {
		this._draft = {
			...this._chime,
			[e]: t
		}, this._saved = !1;
	}
	_target(e) {
		return this._chime.targets.find((t) => t.entity_id === e);
	}
	_setTarget(e, t) {
		this._set("targets", this._chime.targets.map((n) => n.entity_id === e ? {
			...n,
			...t
		} : n));
	}
	_toggleTarget(e, t) {
		let n = this._chime.targets.filter((t) => t.entity_id !== e);
		t && n.push({
			entity_id: e,
			quiet_start: null,
			quiet_end: null
		}), this._set("targets", n);
	}
	async _save() {
		if (this.ctx) {
			this._busy = !0;
			try {
				let e = await this.ctx.saveChime(this._chime);
				this._problems = e.problems, e.success && (this._draft = void 0, this._saved = !0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _saveSettings(e) {
		if (this.ctx?.config) {
			this._settings = {
				...this._settings ?? this.ctx.config.settings,
				...e
			}, this._busy = !0;
			try {
				let e = await this.ctx.saveSettings(this._settings);
				this._problems = e.problems, e.success && (this._settings = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		return e?.config ? D`${this._renderDefaults(e.strings)} ${this._renderResponse(e.strings)}
    ${this._renderChime(e.strings, this._chime)} ${this._renderLog(e.strings)}
    ${this._renderBackup(e.strings)} ${this._renderLanguage(e.strings)}` : k;
	}
	_entities(e) {
		return q(this.ctx.hass, e);
	}
	_renderDefaults(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.meta?.bounds ?? {}, i = (t, r, i) => D`<label class="field">
      <span class="lbl">${B(e, `field.${t}`)}</span>
      <input
        type="number"
        min=${r ? r[0] : 0}
        max=${r ? r[1] : 3600}
        .value=${String(n[t])}
        @change=${(e) => {
			let n = Number(e.target.value);
			Number.isFinite(n) && this._saveSettings({ [t]: n });
		}}
      />
      <span class="hint">${i ?? B(e, "common.seconds_unit")}</span>
    </label>`;
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "settings.defaults_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${B(e, "settings.defaults_intro")}</p>
          <div class="grid-form">
            ${i("siren_duration", r.siren_duration, B(e, "settings.siren_duration_hint"))}
            ${i("arm_hold_timeout", r.arm_hold_timeout, B(e, "settings.arm_hold_hint"))}
            ${i("default_entry_delay", r.entry_delay, B(e, "settings.area_defaults_hint"))}
            ${i("default_exit_delay", r.exit_delay, B(e, "settings.area_defaults_hint"))}
            ${i("low_battery_threshold", r.low_battery_threshold, B(e, "settings.low_battery_hint"))}
            ${i("walk_test_timeout", r.walk_test_timeout, B(e, "settings.walk_test_hint"))}
          </div>
        </div>
      </div>
    `;
	}
	_renderLog(e) {
		let t = this.ctx, n = (this._settings ?? t.config.settings).log, r = t.meta?.log_categories ?? [], [i, a] = t.meta?.retention_bounds ?? [1, 3650], o = (e) => {
			let t = {
				enabled: {
					...n.enabled,
					...e.enabled ?? {}
				},
				retention_days: {
					...n.retention_days,
					...e.retention_days ?? {}
				}
			};
			this._saveSettings({ log: t });
		};
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "settings.log_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${B(e, "settings.log_intro")}</p>
          <div class="rows">
            ${r.map((t) => {
			let r = n.enabled[t] !== !1;
			return D`<div class="row">
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${r}
                    @change=${(e) => o({ enabled: { [t]: e.target.checked } })}
                  />
                  <span>${B(e, `category.${t}`)}</span>
                </label>
                <span class="spacer"></span>
                ${r ? D`<label class="field inline">
                      <input
                        type="number"
                        min=${i}
                        max=${a}
                        .value=${String(n.retention_days[t] ?? 30)}
                        @change=${(e) => {
				let n = Number(e.target.value);
				Number.isFinite(n) && o({ retention_days: { [t]: n } });
			}}
                      />
                      <span class="hint">${B(e, "settings.log_days")}</span>
                    </label>` : D`<span class="hint">${B(e, "settings.log_off")}</span>`}
              </div>`;
		})}
          </div>
          <p class="hint">${B(e, "settings.log_rows_hint")}</p>
        </div>
      </div>
    `;
	}
	_renderBackup(e) {
		let t = (this.ctx.meta?.schema_version ?? []).join(".");
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "settings.backup_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${B(e, "settings.backup_intro")}</p>
          <div class="actions">
            <button class="btn" ?disabled=${this._busy} @click=${this._exportConfig}>
              ${B(e, "settings.backup_export")}
            </button>
            <label class="btn file">
              ${B(e, "settings.backup_import")}
              <input type="file" accept="application/json,.json" @change=${this._importConfig} />
            </label>
          </div>
          <p class="hint">${B(e, "settings.backup_hint")}</p>
          <p class="hint">${B(e, "settings.backup_version", { version: t })}</p>
          ${this._restored ? D`<div class="notice">${B(e, "settings.backup_restored")}</div>` : k}
        </div>
      </div>
    `;
	}
	async _exportConfig() {
		if (this.ctx) {
			this._busy = !0;
			try {
				let e = await this.ctx.exportConfig();
				ze(e.filename, JSON.stringify(e.document, null, 2), "application/json");
			} finally {
				this._busy = !1;
			}
		}
	}
	async _importConfig(e) {
		let t = e.target, n = t.files?.[0];
		if (t.value = "", n && this.ctx) {
			this._busy = !0, this._restored = !1;
			try {
				let e = await n.text(), t = await this.ctx.importConfig(JSON.parse(e));
				this._problems = t.problems, this._restored = t.success;
			} catch {
				this._problems = [{
					code: "not_a_foyer_backup",
					kind: "config",
					ref: null,
					field: null
				}];
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderLanguage(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings;
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "settings.language_title")}</h2></div>
        <div class="card-bd">
          <label class="field">
            <span class="lbl">${B(e, "field.language")}</span>
            <select
              @change=${(e) => this._saveSettings({ language: e.target.value || null })}
            >
              <option value="" ?selected=${!n.language}>
                ${B(e, "settings.language_system")}
              </option>
              ${Jt.map((t) => D`<option .value=${t} ?selected=${t === n.language}>
                    ${B(e, `language.${t}`)}
                  </option>`)}
            </select>
            <span class="hint">${B(e, "settings.language_hint")}</span>
          </label>
          ${this._problems.length ? D`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                </ul>
              </div>` : k}
        </div>
      </div>
    `;
	}
	_renderResponse(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.config.profiles ?? [], i = t.meta?.silenceable ?? [], a = (t, i) => D`<label class="field">
        <span class="lbl">${B(e, `field.${t}`)}</span>
        <select
          @change=${(e) => this._saveSettings({ [t]: e.target.value || null })}
        >
          <option value="" ?selected=${!n[t]}>${B(e, "settings.none")}</option>
          ${r.map((e) => D`<option .value=${e.id ?? ""} ?selected=${e.id === n[t]}>
                ${e.name}
              </option>`)}
        </select>
        <span class="hint">${i}</span>
      </label>`;
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "settings.response_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${B(e, "settings.response_intro")}</p>
          <div class="grid-form">
            ${a("default_profile_id", B(e, "settings.default_profile_hint"))}
            ${a("technical_profile_id", B(e, "settings.technical_profile_hint"))}
            <label class="field">
              <span class="lbl">${B(e, "field.camera_dir")}</span>
              <input
                .value=${n.camera_dir}
                @change=${(e) => this._saveSettings({ camera_dir: e.target.value.trim() })}
              />
              <span class="hint">${B(e, "settings.camera_dir_hint")}</span>
            </label>
          </div>
          <fieldset>
            <legend>${B(e, "field.silent_suppresses")}</legend>
            ${i.map((t) => D`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${n.silent_suppresses.includes(t)}
                    @change=${(e) => {
			let r = e.target.checked ? [...n.silent_suppresses, t] : n.silent_suppresses.filter((e) => e !== t);
			this._saveSettings({ silent_suppresses: r });
		}}
                  />
                  <span
                    >${t === "chime" ? B(e, "settings.chime_title") : B(e, `action_kind.${t}`)}</span
                  >
                </label>`)}
            <p class="hint">${B(e, "settings.silent_hint")}</p>
          </fieldset>
        </div>
      </div>
    `;
	}
	_renderChime(e, t) {
		let n = this.ctx, r = Qe(n.hass, n.meta?.chime_domains ?? [
			"media_player",
			"siren",
			"notify"
		]);
		for (let e of t.targets) r.some((t) => t.id === e.entity_id) || r.push({
			id: e.entity_id,
			name: e.entity_id
		});
		let i = this._entities(["tts"]), a = (e) => (t) => this._set(e, t.target.value || null);
		return D`
      <div class="card">
        <div class="card-hd"><h2>${B(e, "settings.chime_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${B(e, "settings.chime_intro")}</p>
          <fieldset>
            <legend>${B(e, "field.targets")}</legend>
            ${r.length ? r.map((t) => this._renderTarget(e, t)) : D`<p class="hint">${B(e, "settings.no_targets")}</p>`}
            <p class="hint">${B(e, "settings.targets_hint")}</p>
          </fieldset>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${B(e, "field.mode")}</span>
              <select
                @change=${(e) => this._set("mode", e.target.value)}
              >
                ${["sound", "speech"].map((n) => D`<option .value=${n} ?selected=${n === t.mode}>
                      ${B(e, `chime_mode.${n}`)}
                    </option>`)}
              </select>
            </label>
            ${t.mode === "speech" ? D`<label class="field">
                    <span class="lbl">${B(e, "field.tts_entity")}</span>
                    <select
                      @change=${(e) => this._set("tts_entity", e.target.value || null)}
                    >
                      <option value="" ?selected=${!t.tts_entity}>
                        ${B(e, "settings.pick_tts")}
                      </option>
                      ${i.map((e) => D`<option .value=${e.id} ?selected=${e.id === t.tts_entity}>
                            ${e.name}
                          </option>`)}
                    </select>
                    <span class="hint">${B(e, "settings.tts_hint")}</span>
                  </label>` : D`<label class="field">
                    <span class="lbl">${B(e, "field.sound")}</span>
                    <input
                      .value=${t.sound ?? ""}
                      @input=${(e) => this._set("sound", e.target.value.trim() || null)}
                    />
                    <span class="hint">${B(e, "settings.sound_hint")}</span>
                  </label>`}
            <label class="field">
              <span class="lbl">${B(e, "field.volume")}</span>
              <input
                type="number"
                min="0"
                max="100"
                .value=${t.volume == null ? "" : String(t.volume)}
                @input=${(e) => this._set("volume", W(e.target.value))}
              />
              <span class="hint">${B(e, "settings.volume_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.quiet_start")}</span>
              <input type="time" .value=${t.quiet_start ?? ""} @input=${a("quiet_start")} />
            </label>
            <label class="field">
              <span class="lbl">${B(e, "field.quiet_end")}</span>
              <input type="time" .value=${t.quiet_end ?? ""} @input=${a("quiet_end")} />
              <span class="hint">${B(e, "settings.quiet_hint")}</span>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.during_exit}
              @change=${(e) => this._set("during_exit", e.target.checked)}
            />
            <span>
              ${B(e, "field.during_exit")}
              <span class="hint">${B(e, "settings.during_exit_hint")}</span>
            </span>
          </label>
          <p class="hint">${B(e, "settings.switch_hint")}</p>
          ${this._problems.length ? D`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
                  </ul>
                </div>` : k}
          ${this._saved ? D`<div class="notice">${B(e, "settings.saved")}</div>` : k}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${B(e, "common.save")}
            </button>
            <button
              class="btn"
              ?disabled=${this._busy || !this._draft}
              @click=${() => {
			this._draft = void 0, this._problems = [];
		}}
            >
              ${B(e, "common.cancel")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderTarget(e, t) {
		let n = this._target(t.id), r = (e) => (n) => this._setTarget(t.id, { [e]: n.target.value || null });
		return D`<div class="target">
      <label class="check">
        <input
          type="checkbox"
          .checked=${!!n}
          @change=${(e) => this._toggleTarget(t.id, e.target.checked)}
        />
        <span>
          ${t.name === t.id ? t.id : B(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}
        </span>
      </label>
      ${n ? D`<label class="field inline">
                <span class="lbl">${B(e, "field.quiet_start")}</span>
                <input
                  type="time"
                  .value=${n.quiet_start ?? ""}
                  @input=${r("quiet_start")}
                />
              </label>
              <label class="field inline">
                <span class="lbl">${B(e, "field.quiet_end")}</span>
                <input type="time" .value=${n.quiet_end ?? ""} @input=${r("quiet_end")} />
              </label>` : k}
    </div>`;
	}
	static {
		this.styles = [H, o`
      .intro {
        margin: 0 0 8px;
        color: var(--secondary-text-color);
        font-size: 13.5px;
        max-width: 72ch;
      }
      .grid-form {
        margin-top: 16px;
      }
      .later {
        margin: 4px 4px 0;
      }
      .target {
        display: flex;
        align-items: flex-end;
        gap: 12px;
        flex-wrap: wrap;
      }
      .field.inline {
        max-width: 140px;
      }
      .rows {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .row {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }
      .spacer {
        flex: 1;
      }
      .btn.file {
        position: relative;
        overflow: hidden;
        display: inline-flex;
        align-items: center;
      }
      .btn.file input {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
      }
    `];
	}
};
customElements.get("foyer-page-settings") || customElements.define("foyer-page-settings", Xt);
//#endregion
//#region src/panel/wizard.ts
var Z = [
	"area",
	"zones",
	"scenario",
	"user",
	"test"
], Zt = 3, Qt = class extends I {
	constructor(...e) {
		super(...e), this._step = "area", this._userName = "", this._userCode = "", this._busy = !1, this._problems = [], this._confirmed = !1, this._pickedEntity = "", this._notifyTarget = "", this._sent = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_step: { state: !0 },
			_busy: { state: !0 },
			_problems: { state: !0 },
			_proposal: { state: !0 },
			_confirmed: { state: !0 },
			_pickedEntity: { state: !0 },
			_notifyTarget: { state: !0 },
			_sent: { state: !0 },
			_userName: { state: !0 },
			_userCode: { state: !0 }
		};
	}
	get _area() {
		return this.ctx?.config?.areas[0];
	}
	_next() {
		let e = Z.indexOf(this._step);
		this._problems = [], e < Z.length - 1 && (this._step = Z[e + 1]);
	}
	_back() {
		let e = Z.indexOf(this._step);
		this._problems = [], e > 0 && (this._step = Z[e - 1]);
	}
	async _finish() {
		if (this.ctx) {
			this._busy = !0;
			try {
				await this.ctx.saveSettings({ wizard_done: !0 }), this.dispatchEvent(new CustomEvent("wizard-done", {
					bubbles: !0,
					composed: !0
				}));
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return k;
		let t = e.strings;
		return D`
      <section class="wizard">
        <header>
          <h2>${B(t, "wizard.title")}</h2>
          <button class="btn" ?disabled=${this._busy} @click=${this._finish}>
            ${B(t, "wizard.dismiss")}
          </button>
        </header>
        <p class="intro">${B(t, "wizard.intro")}</p>
        <ol class="steps">
          ${Z.map((e, n) => {
			let r = Z.indexOf(this._step);
			return D`<li class=${n < r ? "done" : n === r ? "active" : ""}>
              <span class="n">${n + 1}</span>${B(t, `wizard.step.${e}`)}
            </li>`;
		})}
        </ol>
        <div class="body">${this._renderStep(t)}</div>
        ${this._problems.length ? D`<div class="problems" role="alert">
              <ul>
                ${this._problems.map((e) => D`<li>${U(t, e)}</li>`)}
              </ul>
            </div>` : k}
        <div class="actions">
          <button
            class="btn"
            ?disabled=${this._busy || this._step === Z[0]}
            @click=${this._back}
          >
            ${B(t, "wizard.back")}
          </button>
          <span class="spacer"></span>
          ${this._step === "test" ? D`<button class="btn primary" ?disabled=${this._busy} @click=${this._finish}>
                ${B(t, "wizard.done")}
              </button>` : D`<button class="btn primary" ?disabled=${this._busy} @click=${this._next}>
                ${B(t, "wizard.next")}
              </button>`}
        </div>
      </section>
    `;
	}
	_renderStep(e) {
		switch (this._step) {
			case "area": return this._renderArea(e);
			case "zones": return this._renderZones(e);
			case "scenario": return this._renderScenario(e);
			case "user": return this._renderUser(e);
			default: return this._renderTest(e);
		}
	}
	_renderArea(e) {
		let t = this._area;
		if (!t) return D`<p class="hint">${B(e, "wizard.no_area")}</p>`;
		let n = (e) => this._saveArea({
			...t,
			...e
		});
		return D`
      <p>${B(e, "wizard.area_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${B(e, "field.name")}</span>
          <input
            .value=${t.name}
            @change=${(e) => n({ name: e.target.value.trim() })}
          />
        </label>
        <label class="field">
          <span class="lbl">${B(e, "field.default_exit_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_exit_delay)}
            @change=${(e) => n({ default_exit_delay: Number(e.target.value) })}
          />
          <span class="hint">${B(e, "wizard.exit_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${B(e, "field.default_entry_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_entry_delay)}
            @change=${(e) => n({ default_entry_delay: Number(e.target.value) })}
          />
          <span class="hint">${B(e, "wizard.entry_hint")}</span>
        </label>
      </div>
    `;
	}
	async _saveArea(e) {
		if (this.ctx) {
			this._busy = !0;
			try {
				let t = await this.ctx.save("area", e);
				this._problems = t.problems;
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderZones(e) {
		let t = this.ctx, n = t.config.zones, r = this._proposal, i = t.meta?.zone_domains ?? [], a = Object.values(t.hass.states).filter((e) => i.includes(e.entity_id.split(".")[0])).filter((e) => !n.some((t) => t.entity_id === e.entity_id)).map((e) => ({
			id: e.entity_id,
			name: String(e.attributes.friendly_name ?? e.entity_id)
		})).sort((e, t) => e.name.localeCompare(t.name));
		return D`
      <p>${B(e, "wizard.zones_text", {
			have: n.length,
			want: Zt
		})}</p>
      <ul class="zones">
        ${n.map((t) => D`<li>
            <strong>${t.name}</strong>
            <span class="mono">${t.entity_id}</span>
            <span class="tag">${B(e, `zone_type.${t.type}`)}</span>
          </li>`)}
      </ul>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${B(e, "wizard.add_zone")}</span>
          <select
            @change=${(e) => this._pick(e.target.value)}
          >
            <option value="" ?selected=${!this._pickedEntity}>${B(e, "wizard.pick_entity")}</option>
            ${a.map((e) => D`<option .value=${e.id} ?selected=${e.id === this._pickedEntity}>
                  ${e.name}
                </option>`)}
          </select>
        </label>
      </div>
      ${r ? D`
            <div class="proposal">
              <p>
                ${B(e, "wizard.proposed", {
			entity: r.entity_id,
			state: r.state ?? "",
			type: B(e, `zone_type.${r.zone_type ?? "instant"}`),
			states: r.proposed.join(", ")
		})}
              </p>
              <label class="check">
                <input
                  type="checkbox"
                  .checked=${this._confirmed}
                  @change=${(e) => this._confirmed = e.target.checked}
                />
                <span>${B(e, "wizard.confirm_trigger")}</span>
              </label>
              <p class="hint">${B(e, "wizard.confirm_hint")}</p>
              <button
                class="btn"
                ?disabled=${this._busy || !this._confirmed}
                @click=${this._addZone}
              >
                ${B(e, "wizard.add")}
              </button>
            </div>
          ` : k}
    `;
	}
	async _pick(e) {
		this._pickedEntity = e, this._confirmed = !1, this._proposal = void 0, e && this.ctx && (this._proposal = await this.ctx.hass.callWS({
			type: "foyer/zone/propose",
			entity_id: e
		}));
	}
	async _addZone() {
		let e = this.ctx, t = this._proposal, n = this._area;
		if (!e || !t || !n) return;
		let r = t.trigger_kind === "event" ? {
			kind: "event",
			event_type: t.entity_id.startsWith("event.") ? t.proposed[0] ?? null : null
		} : t.trigger_kind === "numeric" ? {
			kind: "numeric",
			operator: "gt",
			value: 0,
			hysteresis: 0,
			attribute: null
		} : {
			kind: "state",
			states: [...t.proposed]
		}, i = {
			name: t.name,
			entity_id: t.entity_id,
			area_id: n.id,
			trigger: r,
			type: t.zone_type ?? "instant"
		};
		this._busy = !0;
		try {
			let t = await e.save("zone", i, !0);
			this._problems = t.problems, t.success && (this._proposal = void 0, this._pickedEntity = "", this._confirmed = !1);
		} finally {
			this._busy = !1;
		}
	}
	_renderScenario(e) {
		let t = this.ctx, n = t.config.scenarios[0];
		if (!n) return D`<p class="hint">${B(e, "wizard.no_scenario")}</p>`;
		let r = t.config.areas;
		return D`
      <p>${B(e, "wizard.scenario_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${B(e, "field.name")}</span>
          <input
            .value=${n.name}
            @change=${async (e) => {
			let r = e.target.value.trim();
			this._busy = !0;
			try {
				let e = await t.save("scenario", {
					...n,
					name: r
				});
				this._problems = e.problems;
			} finally {
				this._busy = !1;
			}
		}}
          />
        </label>
      </div>
      <p class="hint">
        ${B(e, "wizard.scenario_areas", { areas: r.filter((e) => n.areas.includes(e.id)).map((e) => e.name).join(", ") })}
      </p>
    `;
	}
	async _createUser() {
		let e = this.ctx;
		if (e) {
			this._busy = !0;
			try {
				let t = await e.saveUser({
					name: this._userName.trim(),
					has_code: !1,
					has_duress_code: !1,
					ha_user_id: e.hass.user?.id ?? null,
					permissions: e.meta?.permissions ?? [],
					allowed_area_ids: null,
					allowed_scenario_ids: null,
					valid_from: null,
					valid_until: null,
					code_exempt_when_identified: !1,
					enabled: !0
				}, { new_code: this._userCode });
				this._problems = t.problems, t.success && (this._userCode = "", this._next());
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderUser(e) {
		let t = this.ctx?.config?.users ?? [], n = this.ctx?.status.security.code_length ?? 6;
		if (t.length) return D`
        <p>${B(e, "wizard.user_text")}</p>
        <div class="notice">
          ${B(e, "wizard.user_done", { name: t[0].name })}
        </div>
      `;
		let r = this._userName.trim().length > 0 && this._userCode.length === n;
		return D`
      <p>${B(e, "wizard.user_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${B(e, "field.name")}</span>
          <input
            .value=${this._userName}
            @input=${(e) => this._userName = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${B(e, "users.code")}</span>
          <input
            type="password"
            inputmode="numeric"
            autocomplete="off"
            maxlength=${n}
            .value=${this._userCode}
            @input=${(e) => this._userCode = e.target.value}
          />
          <span class="hint">${B(e, "users.code_hint", { n })}</span>
        </label>
      </div>
      <p class="hint">${B(e, "wizard.user_hint")}</p>
      <button class="btn primary" ?disabled=${this._busy || !r} @click=${this._createUser}>
        ${B(e, "wizard.user_create")}
      </button>
      ${this._problems.length ? D`<ul class="problems">
            ${this._problems.map((t) => D`<li>${U(e, t)}</li>`)}
          </ul>` : k}
    `;
	}
	_renderTest(e) {
		let t = this.ctx, n = J(t.hass);
		return D`
      <p>${B(e, "wizard.test_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${B(e, "wizard.test_target")}</span>
          <select
            @change=${(e) => {
			this._notifyTarget = e.target.value, this._sent = !1;
		}}
          >
            <option value="" ?selected=${!this._notifyTarget}>${B(e, "wizard.pick_target")}</option>
            ${n.map((e) => D`<option .value=${e.id} ?selected=${e.id === this._notifyTarget}>
                  ${e.name}
                </option>`)}
          </select>
        </label>
      </div>
      <button
        class="btn"
        ?disabled=${this._busy || !this._notifyTarget}
        @click=${this._sendTest}
      >
        ${B(e, "wizard.send_test")}
      </button>
      ${this._sent ? D`<div class="notice">${B(e, "wizard.test_sent")}</div>` : k}
      <p class="hint">${B(e, "wizard.test_hint")}</p>
    `;
	}
	async _sendTest() {
		let e = this.ctx;
		if (e && this._notifyTarget) {
			this._busy = !0, this._sent = !1;
			try {
				let t = await e.testAction({
					service: this._notifyTarget,
					message: B(e.strings, "wizard.test_message")
				});
				this._sent = t.success, t.success || (this._problems = [{
					code: "request_failed",
					kind: "notify",
					ref: null,
					field: null,
					detail: t.error ?? t.reason ?? ""
				}]);
			} catch (e) {
				this._problems = [{
					code: "request_failed",
					kind: "notify",
					ref: null,
					field: null,
					detail: String(e?.message ?? e)
				}];
			} finally {
				this._busy = !1;
			}
		}
	}
	static {
		this.styles = [H, o`
      .wizard {
        background: var(--card-background-color);
        border: 1px solid var(--primary-color);
        border-radius: var(--ha-card-border-radius, 12px);
        padding: 16px;
        margin-bottom: 16px;
      }
      header {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      h2 {
        margin: 0;
        flex: 1;
        font-size: 17px;
        font-weight: 500;
      }
      .intro {
        color: var(--secondary-text-color);
        font-size: 13.5px;
        max-width: 72ch;
      }
      ol.steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 16px;
        list-style: none;
        margin: 12px 0;
        padding: 0;
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      ol.steps li {
        display: flex;
        align-items: center;
        gap: 6px;
      }
      ol.steps li.active {
        color: var(--primary-text-color);
        font-weight: 500;
      }
      .n {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--secondary-background-color);
        font-size: 12px;
      }
      ol.steps li.active .n {
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      ol.steps li.done .n {
        background: var(--success-color, #2e9e4f);
        color: var(--text-primary-color, #fff);
      }
      .body {
        border-top: 1px solid var(--divider-color);
        padding-top: 12px;
      }
      ul.zones {
        list-style: none;
        margin: 8px 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 13.5px;
      }
      ul.zones li {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
      }
      .proposal {
        margin-top: 12px;
        padding: 12px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
      }
      .spacer {
        flex: 1;
      }
    `];
	}
};
customElements.get("foyer-wizard") || customElements.define("foyer-wizard", Qt);
//#endregion
//#region src/panel/foyer-panel.ts
var $t = [
	"overview",
	"areas",
	"zones",
	"scenarios",
	"profiles",
	"groups",
	"users",
	"devices",
	"contacts",
	"rules",
	"test",
	"log",
	"settings"
], en = [
	"areas",
	"zones",
	"scenarios",
	"profiles",
	"groups",
	"users",
	"devices",
	"contacts",
	"rules",
	"settings"
], tn = {
	overview: [
		"area",
		"master",
		"scenario",
		"not_ready",
		"memory",
		"technical",
		"incident"
	],
	areas: [
		"own_state",
		"entry",
		"exit",
		"reports_as"
	],
	zones: [
		"trigger",
		"type",
		"entry_mode",
		"arm_policy",
		"hold",
		"always_on",
		"supervision",
		"verification"
	],
	scenarios: [
		"areas",
		"reports_master",
		"switching",
		"exit_override",
		"siren"
	],
	profiles: [
		"inheritance",
		"moments",
		"conditions",
		"severity",
		"silent"
	],
	groups: [
		"threshold",
		"members",
		"suppress",
		"derived"
	],
	users: [
		"own_code",
		"policy",
		"identified",
		"duress",
		"lockout",
		"scope"
	],
	devices: [
		"declared",
		"device_id",
		"identifies",
		"topics",
		"detail",
		"last_result"
	],
	contacts: [
		"order",
		"quiet",
		"linked",
		"step",
		"acknowledge",
		"webhook",
		"test"
	],
	rules: [
		"trigger",
		"guards",
		"grace",
		"suspension",
		"visitor",
		"disarming",
		"next"
	],
	test: [
		"trigger_column",
		"blocks",
		"battery",
		"nothing_runs",
		"clock",
		"skipped",
		"inherited"
	],
	log: [
		"category",
		"zone_disarmed",
		"incident",
		"user",
		"export"
	],
	settings: [
		"targets",
		"mode",
		"quiet",
		"during_exit",
		"response",
		"retention",
		"backup",
		"language"
	]
};
function Q(e) {
	return e === void 0 || e === "" ? {} : { code: e };
}
function $(e) {
	return Object.fromEntries(Object.entries(e).filter(([, e]) => e != null && e !== "" && !(Array.isArray(e) && e.length === 0)));
}
var nn = class extends I {
	constructor(...e) {
		super(...e), this.narrow = !1, this._page = "overview", this._prefs = {}, this._tick = 0, this._offset = 0;
	}
	static {
		this.properties = {
			hass: { attribute: !1 },
			narrow: { type: Boolean },
			route: { attribute: !1 },
			_strings: { state: !0 },
			_status: { state: !0 },
			_config: { state: !0 },
			_meta: { state: !0 },
			_error: { state: !0 },
			_page: { state: !0 },
			_prefs: { state: !0 },
			_tick: { state: !0 }
		};
	}
	connectedCallback() {
		super.connectedCallback(), this.hass && this._start(), this._timer = window.setInterval(() => {
			(this._status?.areas.some((e) => e.timer) || this._status?.walk_test) && (this._tick += 1);
		}, 1e3);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._unsubscribe?.then((e) => e()).catch(() => void 0), this._unsubscribe = void 0, window.clearInterval(this._timer);
	}
	willUpdate(e) {
		e.has("hass") && this.hass && (this.hass.language !== this._language && (this._language = this.hass.language, Ie(this.hass).then((e) => this._strings = e).catch((e) => this._error = String(e?.message ?? e))), !this._unsubscribe && this.isConnected && this._start());
	}
	get _isAdmin() {
		return !!this.hass?.user?.is_admin;
	}
	get _canConfigure() {
		let e = this._status?.security.me;
		return this._isAdmin || !!e?.permissions.includes("edit_config");
	}
	_askForCode(e) {
		return new Promise((t) => {
			this._asking = {
				resolve: t,
				retry: e
			}, this.requestUpdate();
		});
	}
	_answerCode(e) {
		let t = this._asking;
		this._asking = void 0, this._code = e, this.requestUpdate(), t?.resolve(e);
	}
	async _coded(e) {
		let t = await e(this._code);
		for (let n = 0; n < 3; n++) {
			if (t.success || t.reason !== "code_required" && t.reason !== "bad_code") return t;
			let n = await this._askForCode(t.reason === "bad_code");
			if (n === void 0) return t;
			t = await e(n);
		}
		return t;
	}
	_start() {
		this.hass && !this._unsubscribe && (this._unsubscribe = this.hass.connection.subscribeMessage((e) => {
			this._offset = Date.parse(e.now) - Date.now(), this._status = e, this._error = void 0, !this._config && this._canConfigure && this._loadConfig().catch(() => void 0);
		}, { type: "foyer/subscribe" }), this._unsubscribe.catch((e) => {
			this._unsubscribe = void 0, this._error = e?.code === "not_loaded" ? B(this._strings, "common.not_loaded") : B(this._strings, "common.connection_error", { error: String(e?.message ?? e) });
		}), this.hass.callWS({ type: "foyer/prefs" }).then((e) => this._prefs = e).catch(() => void 0), this._isAdmin && this.hass.callWS({ type: "config/auth/list" }).then((e) => this._haUsers = e.filter((e) => !e.system_generated)).catch(() => void 0));
	}
	async _loadConfig() {
		if (!this.hass) return;
		let e = await this.hass.callWS({ type: "foyer/config" });
		this._config = e.config, this._meta = e.meta;
	}
	_context() {
		let e = this.hass;
		if (e && this._strings && this._status) return {
			hass: e,
			strings: this._strings,
			status: this._status,
			config: this._config,
			meta: this._meta,
			isAdmin: this._isAdmin,
			haUsers: this._haUsers,
			now: () => Date.now() + this._offset,
			navigate: (e) => this._page = e,
			arm: (t) => this._coded((n) => e.callWS({
				type: "foyer/arm",
				...t,
				...Q(n)
			})),
			disarm: (t) => this._coded((n) => e.callWS({
				type: "foyer/disarm",
				...t ? { area_ids: t } : {},
				...Q(n)
			})),
			acknowledge: (t) => this._coded((n) => e.callWS({
				type: "foyer/acknowledge",
				target: t,
				...Q(n)
			})),
			saveChime: (e) => this._edit("chime", {
				type: "foyer/config/chime",
				chime: e
			}),
			setAckWebhook: (e) => this._edit("settings", {
				type: "foyer/ack_webhook",
				enabled: e
			}),
			cancelAuto: (t) => this._coded((n) => e.callWS({
				type: "foyer/auto/cancel",
				...t ? { pending_id: t } : {},
				...Q(n)
			})),
			setAutoArming: (t) => this._coded((n) => e.callWS({
				type: "foyer/auto/switch",
				enabled: t,
				...Q(n)
			})),
			suspend: (t) => this._coded((n) => e.callWS({
				type: "foyer/auto/suspend",
				...$(t),
				...Q(n)
			})),
			liftSuspension: (t) => this._coded((n) => e.callWS({
				type: "foyer/auto/suspend",
				suspension_id: t,
				...Q(n)
			})),
			saveSettings: (e) => this._edit("settings", {
				type: "foyer/config/settings",
				settings: {
					...this._config?.settings,
					...e
				}
			}),
			queryLog: (t) => e.callWS({
				type: "foyer/log/query",
				...$(t)
			}),
			exportLog: (t, n) => e.callWS({
				type: "foyer/log/export",
				format: n,
				...$(t)
			}),
			clearLog: async () => await e.callWS({ type: "foyer/log/clear" }),
			diagnostics: () => e.callWS({ type: "foyer/diagnostics" }),
			simulate: (t) => e.callWS({
				type: "foyer/simulate",
				...$(t)
			}),
			walkTest: (t, n) => this._coded((r) => e.callWS({
				type: "foyer/walk_test",
				enable: t,
				...n?.duration ? { duration: n.duration } : {},
				...Q(n?.code ?? r)
			})),
			testAction: (t) => this._coded((n) => e.callWS({
				type: "foyer/test_action",
				...$(t),
				...Q(t.code ?? n)
			})),
			exportConfig: () => e.callWS({ type: "foyer/config/export" }),
			importConfig: (e) => this._edit("config", {
				type: "foyer/config/import",
				document: e
			}),
			bypass: (t, n, r) => this._coded((i) => e.callWS({
				type: "foyer/bypass",
				zone_id: t,
				bypass: n,
				...r ? { seconds: r } : {},
				...Q(i)
			})),
			saveUser: (e, t) => this._edit("user", {
				type: "foyer/user/save",
				user: e,
				...t
			}),
			saveSecurity: (e, t) => this._edit("settings", {
				type: "foyer/config/security",
				code_policy: e,
				security: t
			}),
			save: (e, t, n = !1) => this._edit(e, {
				type: "foyer/config/save",
				kind: e,
				item: t,
				trigger_confirmed: n
			}),
			remove: (e, t) => this._edit(e, {
				type: "foyer/config/delete",
				kind: e,
				item_id: t
			})
		};
	}
	async _edit(e, t) {
		let n;
		try {
			n = await this._coded((e) => this.hass.callWS({
				...t,
				...Q(e)
			}));
		} catch (t) {
			return {
				success: !1,
				problems: [{
					code: "request_failed",
					kind: e,
					ref: null,
					field: null,
					detail: String(t?.message ?? t)
				}]
			};
		}
		return n.success && await this._reloadConfigSoon(), n;
	}
	async _reloadConfigSoon() {
		for (let e = 0; e < 10; e++) {
			await new Promise((e) => setTimeout(e, 300));
			try {
				await this._loadConfig();
				return;
			} catch {}
		}
	}
	_helpOpen(e) {
		return this._prefs.help?.[e] ?? !0;
	}
	_savePrefs(e) {
		this._prefs = {
			...this._prefs,
			...e,
			help: {
				...this._prefs.help,
				...e.help
			}
		}, this.hass?.callWS({
			type: "foyer/prefs/set",
			prefs: e
		}).catch(() => void 0);
	}
	render() {
		let e = this._strings, t = !!this._prefs.help_hidden;
		return D`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="symbol" aria-hidden="true"
          >${Me(Fe(!!this.hass?.themes?.darkMode))}</span
        >
        <div class="title">${B(e, "common.brand")}</div>
        ${this._status ? D`<span class="live">${B(e, "common.live")}</span>` : k}
        <button
          class="help-toggle"
          aria-pressed=${t ? "false" : "true"}
          title=${B(e, "help.global_toggle")}
          aria-label=${B(e, "help.global_toggle")}
          @click=${() => this._savePrefs({ help_hidden: !t })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
        </button>
      </div>
      ${e ? this._renderWalkTestBanner(e) : k}
      ${e ? this._renderTabs(e) : k}
      <main>${e ? this._renderBody(e) : k}</main>
      ${this._asking && e ? this._renderCodeDialog(e) : k}
    `;
	}
	_renderWalkTestBanner(e) {
		let t = this._status?.walk_test;
		if (!t) return k;
		this._tick;
		let n = Re(t.deadline, this._offset);
		return D`
      <div class="walk-banner" role="alert">
        <ha-icon icon="mdi:shield-off-outline"></ha-icon>
        <div>
          <strong>${B(e, "walk.banner_title")}</strong>
          ${B(e, "walk.banner", {
			time: Le(n),
			who: t.user_name ?? B(e, "walk.somebody")
		})}
          <div class="live-note">${B(e, "walk.always_on_live")}</div>
        </div>
        <button class="btn danger" @click=${() => void this._endWalkTest()}>
          ${B(e, "walk.end")}
        </button>
      </div>
    `;
	}
	async _endWalkTest() {
		await this._context()?.walkTest(!1);
	}
	_renderCodeDialog(e) {
		let t = this._status?.security.code_length ?? 6;
		return D`
      <div class="scrim" @click=${() => this._answerCode(void 0)}></div>
      <form class="code-dialog" @submit=${(e) => {
			e.preventDefault();
			let t = e.target.elements.namedItem("code");
			this._answerCode(t.value);
		}} @click=${(e) => e.stopPropagation()}>
        <h2>${B(e, "code.title")}</h2>
        <p>${this._asking?.retry ? B(e, "code.wrong") : B(e, "code.prompt", { n: t })}</p>
        <input
          name="code"
          type="password"
          inputmode="numeric"
          autocomplete="off"
          maxlength=${t}
          autofocus
        />
        <div class="row">
          <button type="button" class="btn" @click=${() => this._answerCode(void 0)}>
            ${B(e, "common.cancel")}
          </button>
          <button type="submit" class="btn primary">${B(e, "common.ok")}</button>
        </div>
      </form>
    `;
	}
	_renderTabs(e) {
		let t = this._canConfigure ? $t : $t.filter((e) => !en.includes(e));
		return t.length < 2 ? k : D`
      <nav class="tabs" role="tablist">
        ${t.map((t) => D`
            <button
              role="tab"
              aria-selected=${t === this._page ? "true" : "false"}
              @click=${() => this._page = t}
            >
              ${B(e, `nav.${t}`)}
            </button>
          `)}
      </nav>
    `;
	}
	_renderBody(e) {
		if (this._error) return D`<p class="error">${this._error}</p>`;
		let t = this._context();
		if (!t) return D`<p class="muted">${B(e, "common.loading")}</p>`;
		let n = this._page;
		return D`
      ${this._canConfigure && this._config && !this._config.settings.wizard_done ? D`<foyer-wizard
            .ctx=${t}
            @wizard-done=${() => void this._loadConfig()}
          ></foyer-wizard>` : k} ${this._prefs.help_hidden ? k : this._renderHelp(e, n)}
      ${this._renderPage(n, t)}
    `;
	}
	_renderPage(e, t) {
		switch (this._tick, e) {
			case "areas": return D`<foyer-page-areas .ctx=${t}></foyer-page-areas>`;
			case "zones": return D`<foyer-page-zones .ctx=${t}></foyer-page-zones>`;
			case "scenarios": return D`<foyer-page-scenarios .ctx=${t}></foyer-page-scenarios>`;
			case "profiles": return D`<foyer-page-profiles .ctx=${t}></foyer-page-profiles>`;
			case "groups": return D`<foyer-page-groups .ctx=${t}></foyer-page-groups>`;
			case "users": return D`<foyer-page-users .ctx=${t}></foyer-page-users>`;
			case "devices": return D`<foyer-page-devices .ctx=${t}></foyer-page-devices>`;
			case "contacts": return D`<foyer-page-contacts .ctx=${t}></foyer-page-contacts>`;
			case "rules": return D`<foyer-page-rules .ctx=${t}></foyer-page-rules>`;
			case "test": return D`<foyer-page-test .ctx=${t}></foyer-page-test>`;
			case "log": return D`<foyer-page-log .ctx=${t}></foyer-page-log>`;
			case "settings": return D`<foyer-page-settings .ctx=${t}></foyer-page-settings>`;
			default: return D`<foyer-page-overview .ctx=${t}></foyer-page-overview>`;
		}
	}
	_renderHelp(e, t) {
		let n = `help.${t}`, r = this._helpOpen(t);
		return D`
      <section class="help" ?data-open=${r}>
        <button
          class="help-hd"
          aria-expanded=${r ? "true" : "false"}
          @click=${() => this._savePrefs({ help: { [t]: !r } })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
          <span>${B(e, `${n}.title`)}</span>
          <span class="sr-only">${B(e, "help.toggle")}</span>
          <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon>
        </button>
        ${r ? D`<div class="help-body">
              <p>${B(e, `${n}.intro`)}</p>
              <dl>
                ${tn[t].map((t) => D`
                    <dt>${B(e, `${n}.items.${t}.term`)}</dt>
                    <dd>${B(e, `${n}.items.${t}.text`)}</dd>
                  `)}
              </dl>
            </div>` : k}
      </section>
    `;
	}
	static {
		this.styles = [
			V,
			H,
			o`
      :host {
        display: block;
        min-height: 100vh;
        background: var(--primary-background-color);
        color: var(--primary-text-color);
      }
      /* The code dialog: over everything, because nothing else can happen
         until it is answered — the command that opened it is waiting. */
      .scrim {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.55);
        z-index: 10;
      }
      .code-dialog {
        position: fixed;
        z-index: 11;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: min(320px, calc(100vw - 32px));
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 20px;
        border-radius: 12px;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
      }
      .code-dialog h2 {
        margin: 0;
        font-size: 18px;
      }
      .code-dialog p {
        margin: 0;
        color: var(--secondary-text-color);
        font-size: 14px;
      }
      .code-dialog input {
        font-size: 24px;
        letter-spacing: 8px;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid var(--divider-color);
        background: var(--primary-background-color);
        color: var(--primary-text-color);
      }
      .code-dialog .row {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
      }
      .toolbar {
        display: flex;
        align-items: center;
        gap: 12px;
        height: var(--header-height, 56px);
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color));
        color: var(--app-header-text-color, var(--text-primary-color));
        border-bottom: var(--app-header-border-bottom, none);
        box-sizing: border-box;
      }
      .symbol svg {
        width: 32px;
        height: 32px;
        display: block;
      }
      .title {
        font-size: 20px;
        font-weight: 400;
        flex: 1;
      }
      .live {
        font-size: 12px;
        opacity: 0.85;
      }
      /* The banner §11.3 calls permanent and unmissable. It sits between the
         toolbar and the tabs, on every page, for as long as the walk test
         runs — because for as long as it runs a real intrusion produces
         nothing at all, and that is not something to mention discreetly. */
      .walk-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        background: var(--warning-color, #c77700);
        color: var(--text-primary-color, #fff);
        font-size: 14px;
        line-height: 1.35;
      }
      .walk-banner > div {
        flex: 1;
      }
      .walk-banner strong {
        margin-right: 4px;
      }
      .walk-banner .btn {
        background: rgba(0, 0, 0, 0.18);
        border-color: rgba(255, 255, 255, 0.55);
        color: inherit;
        white-space: nowrap;
      }
      /* What stays live, said in the banner itself: "have I just switched the
         smoke detector off?" is the first question, and it is answered here
         rather than a page away. */
      .live-note {
        font-size: 12.5px;
        opacity: 0.9;
      }
      @media (max-width: 600px) {
        .walk-banner {
          flex-wrap: wrap;
        }
      }
      .help-toggle {
        border: 0;
        background: transparent;
        color: inherit;
        cursor: pointer;
        padding: 6px;
        border-radius: 50%;
        opacity: 0.7;
      }
      .help-toggle[aria-pressed="true"] {
        opacity: 1;
      }
      .tabs {
        display: flex;
        gap: 4px;
        padding: 0 16px;
        overflow-x: auto;
        background: var(--card-background-color);
        border-bottom: 1px solid var(--divider-color);
      }
      .tabs button {
        font: inherit;
        font-size: 14px;
        font-weight: 500;
        padding: 12px 14px;
        border: 0;
        border-bottom: 2px solid transparent;
        background: transparent;
        color: var(--secondary-text-color);
        cursor: pointer;
        white-space: nowrap;
      }
      .tabs button[aria-selected="true"] {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color);
      }
      main {
        max-width: 1100px;
        margin: 0 auto;
        padding: 16px;
      }
      .help {
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-left: 3px solid var(--primary-color);
        border-radius: 8px;
        margin-bottom: 18px;
        overflow: hidden;
      }
      .help-hd {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        padding: 12px 16px;
        border: 0;
        background: transparent;
        color: var(--primary-text-color);
        font: inherit;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        text-align: left;
      }
      .help-hd .chev {
        margin-left: auto;
        color: var(--secondary-text-color);
        transition: transform 0.15s;
      }
      .help:not([data-open]) .chev {
        transform: rotate(-90deg);
      }
      .help-body {
        padding: 0 16px 16px;
        font-size: 13.5px;
      }
      .help-body p {
        margin: 0 0 12px;
        color: var(--secondary-text-color);
        max-width: 72ch;
      }
      dl {
        display: grid;
        grid-template-columns: minmax(120px, 190px) 1fr;
        gap: 6px 16px;
        margin: 0;
      }
      dt {
        font-weight: 500;
      }
      dd {
        margin: 0;
        color: var(--secondary-text-color);
      }
      .error {
        color: var(--error-color);
      }
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
      }
      @media (max-width: 560px) {
        dl {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    `
		];
	}
};
customElements.get("foyer-panel") || customElements.define("foyer-panel", nn);
//#endregion
