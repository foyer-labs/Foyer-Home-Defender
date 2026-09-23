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
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: ee, getOwnPropertySymbols: te, getPrototypeOf: ne } = Object, f = globalThis, p = f.trustedTypes, re = p ? p.emptyScript : "", ie = f.reactiveElementPolyfillSupport, m = (e, t) => e, h = {
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
}, g = (e, t) => !l(e, t), _ = {
	attribute: !0,
	type: String,
	converter: h,
	reflect: !1,
	useDefault: !1,
	hasChanged: g
};
Symbol.metadata ??= Symbol("metadata"), f.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var v = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = _) {
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
		return this.elementProperties.get(e) ?? _;
	}
	static _$Ei() {
		if (this.hasOwnProperty(m("elementProperties"))) return;
		let e = ne(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(m("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(m("properties"))) {
			let e = this.properties, t = [...ee(e), ...te(e)];
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
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? g)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
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
v.elementStyles = [], v.shadowRootOptions = { mode: "open" }, v[m("elementProperties")] = /* @__PURE__ */ new Map(), v[m("finalized")] = /* @__PURE__ */ new Map(), ie?.({ ReactiveElement: v }), (f.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
var y = globalThis, ae = (e) => e, b = y.trustedTypes, oe = b ? b.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, x = "$lit$", S = `lit$${Math.random().toFixed(9).slice(2)}$`, C = "?" + S, se = `<${C}>`, w = document, T = () => w.createComment(""), E = (e) => e === null || typeof e != "object" && typeof e != "function", D = Array.isArray, ce = (e) => D(e) || typeof e?.[Symbol.iterator] == "function", O = "[ 	\n\f\r]", k = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, le = /-->/g, A = />/g, j = RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), M = /'/g, N = /"/g, P = /^(?:script|style|textarea|title)$/i, F = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), I = Symbol.for("lit-noChange"), L = Symbol.for("lit-nothing"), R = /* @__PURE__ */ new WeakMap(), z = w.createTreeWalker(w, 129);
function B(e, t) {
	if (!D(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return oe === void 0 ? t : oe.createHTML(t);
}
var V = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = k;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === k ? c[1] === "!--" ? o = le : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = j) : (P.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = j) : o = A : o === j ? c[0] === ">" ? (o = i ?? k, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? j : c[3] === "\"" ? N : M) : o === N || o === M ? o = j : o === le || o === A ? o = k : (o = j, i = void 0);
		let d = o === j && e[t + 1].startsWith("/>") ? " " : "";
		a += o === k ? n + se : l >= 0 ? (r.push(s), n.slice(0, l) + x + n.slice(l) + S + d) : n + S + (l === -2 ? t : d);
	}
	return [B(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, H = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = V(t, n);
		if (this.el = e.createElement(l, r), z.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = z.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(x)) {
					let t = u[o++], n = i.getAttribute(e).split(S), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? de : r[1] === "?" ? fe : r[1] === "@" ? pe : G
					}), i.removeAttribute(e);
				} else e.startsWith(S) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (P.test(i.tagName)) {
					let e = i.textContent.split(S), t = e.length - 1;
					if (t > 0) {
						i.textContent = b ? b.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], T()), z.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], T());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === C) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(S, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += S.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = w.createElement("template");
		return n.innerHTML = e, n;
	}
};
function U(e, t, n = e, r) {
	if (t === I) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = E(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = U(e, i._$AS(e, t.values), i, r)), t;
}
var ue = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? w).importNode(t, !0);
		z.currentNode = r;
		let i = z.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new W(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new me(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = z.nextNode(), a++);
		}
		return z.currentNode = w, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, W = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = L, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = U(this, e, t), E(e) ? e === L || e == null || e === "" ? (this._$AH !== L && this._$AR(), this._$AH = L) : e !== this._$AH && e !== I && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? ce(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== L && E(this._$AH) ? this._$AA.nextSibling.data = e : this.T(w.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = H.createElement(B(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new ue(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = R.get(e.strings);
		return t === void 0 && R.set(e.strings, t = new H(e)), t;
	}
	k(t) {
		D(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(T()), this.O(T()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = ae(e).nextSibling;
			ae(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, G = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = L, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = L;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = U(this, e, t, 0), a = !E(e) || e !== this._$AH && e !== I, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = U(this, r[n + o], t, o), s === I && (s = this._$AH[o]), a ||= !E(s) || s !== this._$AH[o], s === L ? e = L : e !== L && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === L ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, de = class extends G {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === L ? void 0 : e;
	}
}, fe = class extends G {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== L);
	}
}, pe = class extends G {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = U(this, e, t, 0) ?? L) === I) return;
		let n = this._$AH, r = e === L && n !== L || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== L && (n === L || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, me = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		U(this, e);
	}
}, he = {
	M: x,
	P: S,
	A: C,
	C: 1,
	L: V,
	R: ue,
	D: ce,
	V: U,
	I: W,
	H: G,
	N: fe,
	U: pe,
	B: de,
	F: me
}, ge = y.litHtmlPolyfillSupport;
ge?.(H, W), (y.litHtmlVersions ??= []).push("3.3.3");
var _e = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new W(t.insertBefore(T(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, K = globalThis, q = class extends v {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = _e(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return I;
	}
};
q._$litElement$ = !0, q.finalized = !0, K.litElementHydrateSupport?.({ LitElement: q });
var ve = K.litElementPolyfillSupport;
ve?.({ LitElement: q }), (K.litElementVersions ??= []).push("4.2.2");
//#endregion
//#region node_modules/lit-html/directive.js
var J = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, ye = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), be = class {
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
}, { I: xe } = he, Se = (e) => e.strings === void 0, Ce = {}, we = (e, t = Ce) => e._$AH = t, Y = ye(class extends be {
	constructor(e) {
		if (super(e), e.type !== J.PROPERTY && e.type !== J.ATTRIBUTE && e.type !== J.BOOLEAN_ATTRIBUTE) throw Error("The `live` directive is not allowed on child or event bindings");
		if (!Se(e)) throw Error("`live` bindings can only contain a single expression");
	}
	render(e) {
		return e;
	}
	update(e, [t]) {
		if (t === I || t === L) return t;
		let n = e.element, r = e.name;
		if (e.type === J.PROPERTY) {
			if (t === n[r]) return I;
		} else if (e.type === J.BOOLEAN_ATTRIBUTE) {
			if (!!t === n.hasAttribute(r)) return I;
		} else if (e.type === J.ATTRIBUTE && n.getAttribute(r) === t + "") return I;
		return we(e), t;
	}
}), X = /* @__PURE__ */ new Map();
function Te(e) {
	let t = e.language, n = X.get(t);
	return n || (n = e.callWS({
		type: "foyer/translations",
		language: t
	}).then((e) => e.strings), n.catch(() => X.delete(t)), X.set(t, n)), n;
}
function Z(e, t, n = {}) {
	let r = e;
	for (let e of t.split(".")) if (r && typeof r == "object" && e in r) r = r[e];
	else return t;
	return typeof r == "string" ? r.replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e) : t;
}
//#endregion
//#region src/shared/styles.ts
var Ee = o`
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
`;
o`
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
  /* Classes the pages have been using without a rule behind them (found in
     review). Each one rendered as nothing at all: a "small" button at full
     size, an editor footer flush against the card edge, a separator that
     separated nothing. They live here rather than in one page because
     several pages use each of them. */
  .btn.sm,
  .btn.small {
    padding: 4px 10px;
    font-size: 13px;
  }
  .card-ft {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    padding: 12px 16px;
    border-top: 1px solid var(--divider-color);
  }
  .hr {
    height: 1px;
    background: var(--divider-color);
    border: 0;
    margin: 16px 0;
  }
  .note {
    color: var(--secondary-text-color);
    font-size: 13px;
    margin: 6px 0 0;
  }
  .sub {
    color: var(--secondary-text-color);
    font-size: 12.5px;
  }
  .num {
    font-variant-numeric: tabular-nums;
  }
  .wide,
  .span {
    grid-column: 1 / -1;
  }
  /* The singular spelling of the problems bar, used by the contact editor. */
  .problem {
    padding: 10px 14px;
    border-left: 3px solid var(--error-color, #d32f2f);
    background: var(--secondary-background-color);
    border-radius: 6px;
    font-size: 13.5px;
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
function De(e) {
	let t = Math.max(0, Math.round(e));
	return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function Q(e, t = 0) {
	return Math.max(0, Math.round((Date.parse(e) - (Date.now() + t)) / 1e3));
}
//#endregion
//#region src/card/foyer-card.ts
var Oe = "alarm_control_panel.foyer_", $ = "alarm_control_panel.foyer_master", ke = /* @__PURE__ */ new Set(["zone_open", "zone_fault"]), Ae = /* @__PURE__ */ new Set(["code_required", "bad_code"]), je = class extends q {
	constructor(...e) {
		super(...e), this._busy = !1, this._code = "", this._padOpen = !1, this._tick = 0, this._offset = 0;
	}
	static {
		this.properties = {
			hass: { attribute: !1 },
			_config: { state: !0 },
			_strings: { state: !0 },
			_status: { state: !0 },
			_busy: { state: !0 },
			_feedback: { state: !0 },
			_code: { state: !0 },
			_padOpen: { state: !0 },
			_pending: { state: !0 },
			_tick: { state: !0 }
		};
	}
	static getStubConfig(e) {
		let t = Object.keys(e.states).filter((e) => e.startsWith(Oe));
		return {
			type: "custom:foyer-card",
			entity: t.includes($) ? $ : t[0],
			layout: "full"
		};
	}
	static getConfigElement() {
		return document.createElement("foyer-card-editor");
	}
	setConfig(e) {
		this._config = e;
	}
	getCardSize() {
		return this._layout === "compact" || this._layout === "badge" ? 1 : 3;
	}
	get _layout() {
		let e = this._config?.layout;
		return e === "compact" || e === "keypad" || e === "badge" ? e : "full";
	}
	get _codeLength() {
		return this._status?.security.code_length ?? 6;
	}
	get _codeUsed() {
		return !!this._status?.security.enforced;
	}
	_press(e) {
		this._code.length >= this._codeLength || (this._code += e, this._feedback = void 0);
	}
	connectedCallback() {
		super.connectedCallback(), this._timer = window.setInterval(() => {
			(this._area?.timer || this._status?.areas.some((e) => e.timer) || this._status?.walk_test || this._pendingAuto) && (this._tick += 1);
		}, 1e3);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._unsubscribe?.then((e) => e()).catch(() => void 0), this._unsubscribe = void 0, window.clearInterval(this._timer);
	}
	willUpdate(e) {
		e.has("hass") && this.hass && (this.hass.language !== this._language && (this._language = this.hass.language, Te(this.hass).then((e) => this._strings = e).catch(() => {
			this._language = void 0;
		})), !this._unsubscribe && this.isConnected && (this._unsubscribe = this.hass.connection.subscribeMessage((e) => {
			this._offset = Date.parse(e.now) - Date.now(), this._status = e;
		}, { type: "foyer/subscribe" }), this._unsubscribe.catch(() => this._unsubscribe = void 0)));
	}
	get _isMaster() {
		return this._config?.entity === $;
	}
	get _area() {
		return this._status?.areas.find((e) => e.entity_id === this._config?.entity);
	}
	async _run(e) {
		if (!this.hass) return;
		this._busy = !0, this._feedback = void 0;
		let t = this._code;
		this._code = "";
		try {
			let n = await this.hass.callWS({
				...e,
				...t ? { code: t } : {}
			});
			if (this._pending = void 0, n.success && n.low_battery_zones.length && (this._feedback = {
				text: Z(this._strings, "card.low_battery", { zones: n.low_battery_zones.map((e) => e.name).join(", ") }),
				warning: !0
			}), !n.success && n.reason === "nothing_to_cancel" && e.type === "foyer/auto/cancel") return;
			n.success || (Ae.has(n.reason ?? "") && (this._padOpen = !0, this._pending = e), this._feedback = {
				text: Z(this._strings, `reason.${n.reason ?? "unknown"}`, { zones: n.blocking_zones.map((e) => e.name).join(", ") }),
				retry: e.type === "foyer/arm" && !e.force && ke.has(n.reason ?? "") ? {
					...e,
					force: !0
				} : void 0
			});
		} catch (e) {
			this._feedback = { text: String(e?.message ?? e) };
		} finally {
			this._busy = !1;
		}
	}
	render() {
		let e = this._strings;
		if (!e || !this.hass) return L;
		this._tick;
		let t = this._config?.entity;
		return t ? this.hass.states[t] ? this._layout === "badge" ? this._renderBadge(e) : this._layout === "compact" ? this._renderCompact(e) : this._layout === "keypad" ? this._renderKeypadLayout(e) : this._isMaster ? this._renderMaster(e) : this._renderArea(e) : this._message(Z(e, "card.entity_missing", { entity: t })) : this._message(Z(e, "card.no_entity"));
	}
	_renderBadge(e) {
		let t = this._status;
		if (!t) return this._message(Z(e, "common.loading"));
		let n = this._area, r = this._isMaster || !n, i = r ? t.master.state : n.state, a = r ? t.areas.some((e) => e.memory) : n.memory, o = t.scenarios.find((e) => e.id === t.active_scenario_id), s = r ? o?.name ?? Z(e, "overview.master") : n.name, c = r ? t.areas.find((e) => e.timer && e.timer.kind !== "siren") : n, l = this._pendingAuto, u = c?.timer, d = u && u.kind !== "siren" ? Z(e, `timer.${u.kind}`, { seconds: Math.max(0, Math.round((Date.parse(u.due) - (Date.now() + this._offset)) / 1e3)) }) : Z(e, `state.${i}`);
		return F`
      <div
        class="badge"
        role="button"
        tabindex="0"
        title=${`${s} — ${Z(e, `state.${i}`)}`}
        @click=${this._openMore}
        @keydown=${(e) => {
			(e.key === "Enter" || e.key === " ") && this._openMore();
		}}
      >
        <span class="badge-name">${s}</span>
        <span class="state ${i}">${d}</span>
        ${a ? F`<span class="state memory">${Z(e, "overview.memory")}</span>` : L}
        ${t.walk_test ? F`<span class="state walk-chip" title=${Z(e, "walk.badge_title")}
              >${Z(e, "walk.badge")}</span
            >` : L}
        ${l ? F`<span
              class="state auto-chip"
              title=${Z(e, `rules.counting_${l.action}`, {
			rule: l.rule_name,
			scenario: t.scenarios.find((e) => e.id === l.scenario_id)?.name ?? "",
			seconds: Q(l.due, this._offset)
		})}
              >${Z(e, "card.auto_badge", { seconds: Q(l.due, this._offset) })}</span
            >` : L}
      </div>
    `;
	}
	_openMore() {
		let e = this._config?.entity;
		e && this.dispatchEvent(new CustomEvent("hass-more-info", {
			detail: { entityId: e },
			bubbles: !0,
			composed: !0
		}));
	}
	_renderCompact(e) {
		let t = this._status;
		if (!t) return this._message(Z(e, "common.loading"));
		let n = this._area, r = this._isMaster || !n, i = r ? t.master.state : n.state, a = r ? t.areas.some((e) => e.memory) : n.memory, o = t.scenarios.find((e) => e.id === t.active_scenario_id), s = r ? o?.name ?? Z(e, "overview.master") : n.name, c = r ? t.areas.some((e) => e.state !== "disarmed" || e.memory) : n.state !== "disarmed" || n.memory, l = r ? t.areas.find((e) => e.timer && e.timer.kind !== "siren") : n;
		return F`
      <ha-card>
        <div class="content compact">
          ${this._walkBanner(e)} ${this._autoBanner(e)}
          <div class="head">
            <div class="name">${s}</div>
            <span class="state ${i}">${Z(e, `state.${i}`)}</span>
            ${a ? F`<span class="state memory">${Z(e, "overview.memory")}</span>` : L}
          </div>
          ${l ? this._countdown(e, l) : L}
          ${this._renderInlinePad(e)}
          <div class="buttons">
            ${r ? F`<select
                  ?disabled=${this._busy}
                  aria-label=${Z(e, "card.scenario")}
                  @change=${(e) => {
			let t = e.target.value;
			t && this._run({
				type: "foyer/arm",
				scenario_id: t
			});
		}}
                >
                  <option value="" .selected=${Y(!o)}>${Z(e, "card.pick_scenario")}</option>
                  ${t.scenarios.map((e) => F`<option .value=${e.id} .selected=${Y(e.id === o?.id)}>
                      ${e.name}
                    </option>`)}
                </select>` : n.state === "disarmed" ? F`<button
                    class="primary"
                    ?disabled=${this._busy}
                    @click=${() => this._run({
			type: "foyer/arm",
			area_id: n.id
		})}
                  >
                    ${Z(e, "card.arm")}
                  </button>` : L}
            ${c ? F`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run(r ? { type: "foyer/disarm" } : {
			type: "foyer/disarm",
			area_ids: [n.id]
		})}
                >
                  ${Z(e, "card.disarm")}
                </button>` : L}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
	}
	_renderArea(e) {
		let t = this._area;
		if (!t) return this._message(Z(e, "common.loading"));
		let n = t.state !== "disarmed" || t.memory;
		return F`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(e)} ${this._head(t.name, t.state, t.memory)}
          ${this._countdown(e, t)} ${this._renderBlocking(e, t)}
          ${this._renderInlinePad(e)}
          <div class="buttons">
            ${t.state === "disarmed" ? F`<button
                  class="primary"
                  ?disabled=${this._busy}
                  @click=${() => this._run({
			type: "foyer/arm",
			area_id: t.id
		})}
                >
                  ${Z(e, "card.arm")}
                </button>` : L}
            ${n ? F`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({
			type: "foyer/disarm",
			area_ids: [t.id]
		})}
                >
                  ${Z(e, "card.disarm")}
                </button>` : L}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
	}
	_renderBlocking(e, t) {
		if (t.state !== "disarmed" || t.ready) return L;
		let n = this._status?.zones ?? [], r = [...t.blocking.fault, ...t.blocking.open].map((e) => n.find((t) => t.id === e)).filter((e) => !!e);
		return r.length ? F`
      <div class="blocking">
        ${r.map((t) => F`<div class="row">
            <span>${t.name}</span>
            ${t.bypassable ? F`<button
                  class="link"
                  ?disabled=${this._busy}
                  @click=${() => this._run({
			type: "foyer/bypass",
			zone_id: t.id,
			bypass: !0
		})}
                >
                  ${Z(e, "zones.bypass")}
                </button>` : L}
          </div>`)}
      </div>
    ` : L;
	}
	_renderMaster(e) {
		let t = this._status;
		if (!t) return this._message(Z(e, "common.loading"));
		let n = t.areas.some((e) => e.memory), r = t.scenarios.find((e) => e.id === t.active_scenario_id), i = t.areas.some((e) => e.state !== "disarmed" || e.memory);
		return F`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(e)}
          ${this._head(r?.name ?? Z(e, "overview.master"), t.master.state, n)}
          <div class="areas">
            ${t.areas.map((t) => F`<div class="row">
                <span class="area-name">${t.name}</span>
                <span class="state ${t.state}">${Z(e, `state.${t.state}`)}</span>
                ${t.memory ? F`<span class="state memory">${Z(e, "overview.memory")}</span>` : L}
                ${this._countdown(e, t)}
              </div>`)}
          </div>
          ${this._renderNotReady(e)} ${this._renderInlinePad(e)}
          <div class="buttons">
            ${t.scenarios.map((e) => F`<button
                class=${e.id === t.active_scenario_id ? "primary" : ""}
                ?disabled=${this._busy}
                @click=${() => this._run({
			type: "foyer/arm",
			scenario_id: e.id
		})}
              >
                ${e.name}
              </button>`)}
            ${i ? F`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({ type: "foyer/disarm" })}
                >
                  ${Z(e, "card.disarm")}
                </button>` : L}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
	}
	_renderNotReady(e) {
		let t = this._status;
		if (!t) return L;
		let n = /* @__PURE__ */ new Map();
		for (let e of t.areas) if (!(e.state !== "disarmed" || e.ready)) for (let t of [...e.blocking.fault, ...e.blocking.open]) n.set(t, [...n.get(t) ?? [], e.name]);
		return n.size ? F`
      <div class="blocking">
        <div class="blocking-hd">${Z(e, "card.not_ready")}</div>
        ${[...n.entries()].map(([n, r]) => {
			let i = t.zones.find((e) => e.id === n);
			return i ? F`<div class="row">
            <span>${Z(e, "card.zone_in", {
				zone: i.name,
				areas: r.join(", ")
			})}</span>
            ${i.bypassable && !i.bypassed ? F`<button
                  class="link"
                  ?disabled=${this._busy}
                  @click=${() => this._run({
				type: "foyer/bypass",
				zone_id: i.id,
				bypass: !0
			})}
                >
                  ${Z(e, "zones.bypass")}
                </button>` : L}
          </div>` : L;
		})}
      </div>
    ` : L;
	}
	_walkBanner(e) {
		let t = this._status?.walk_test;
		if (!t) return L;
		let n = Q(t.deadline, this._offset);
		return F`
      <div class="alert walk" role="alert">
        <span>
          <strong>${Z(e, "walk.banner_title")}</strong>
          ${Z(e, "walk.card_banner", { time: De(n) })}
        </span>
        <button
          ?disabled=${this._busy}
          @click=${() => this._run({
			type: "foyer/walk_test",
			enable: !1
		})}
        >
          ${Z(e, "walk.end")}
        </button>
      </div>
    `;
	}
	get _pendingAuto() {
		return [...this._status?.auto?.pending ?? []].sort((e, t) => e.due.localeCompare(t.due))[0];
	}
	_autoBanner(e) {
		let t = this._pendingAuto;
		if (!t) return L;
		let n = this._status?.scenarios.find((e) => e.id === t.scenario_id), r = Q(t.due, this._offset);
		return F`
      <div class="alert auto" role="alert">
        <span>
          ${Z(e, `rules.counting_${t.action}`, {
			rule: t.rule_name,
			scenario: n?.name ?? "",
			seconds: r
		})}
          ${t.suspension_name ? F`<em>${Z(e, "rules.because", { name: t.suspension_name })}</em>` : L}
        </span>
        <button
          ?disabled=${this._busy}
          @click=${() => this._run({
			type: "foyer/auto/cancel",
			pending_id: t.id
		})}
        >
          ${Z(e, "rules.cancel_now")}
        </button>
      </div>
    `;
	}
	_renderAlerts(e) {
		let t = this._status;
		if (!t) return L;
		let n = new Map(t.zones.map((e) => [e.id, e.name])), r = t.technical ?? [], i = t.incident;
		return F`
      ${this._walkBanner(e)} ${this._autoBanner(e)}
      ${r.length ? F`<div class="alert technical" role="alert">
            <span>${Z(e, "card.technical", { zones: r.map((e) => e.name).join(", ") })}</span>
            ${r.some((e) => !e.acknowledged) ? F`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({
			type: "foyer/acknowledge",
			target: "technical"
		})}
                >
                  ${Z(e, "common.acknowledge")}
                </button>` : L}
          </div>` : L}
      ${i ? F`<div class="alert incident" role="alert">
            <span>
              ${Z(e, "card.incident", { zones: i.zone_ids.map((e) => n.get(e) ?? e).join(", ") })}
            </span>
            ${i.acknowledged ? L : F`<button
                  ?disabled=${this._busy}
                  @click=${() => this._run({
			type: "foyer/acknowledge",
			target: "incident"
		})}
                >
                  ${Z(e, "common.acknowledge")}
                </button>`}
          </div>` : L}
    `;
	}
	_head(e, t, n) {
		let r = this._strings;
		return F`
      <div class="head">
        <div class="name">${e}</div>
        <span class="state ${t}">${Z(r, `state.${t}`)}</span>
        ${n ? F`<span class="state memory">${Z(r, "overview.memory")}</span>` : L}
      </div>
    `;
	}
	_countdown(e, t, n = !1) {
		if (!t.timer || t.timer.kind === "siren") return L;
		let r = Math.max(0, Math.round((Date.parse(t.timer.due) - (Date.now() + this._offset)) / 1e3)), i = Z(e, `timer.${t.timer.kind}`, { seconds: r });
		return F`<div class="countdown">
      ${n ? Z(e, "card.area_countdown", {
			area: t.name,
			countdown: i
		}) : i}
    </div>`;
	}
	_pendingLabel(e) {
		let t = this._pending;
		return t ? t.type === "foyer/disarm" ? Z(e, "card.disarm") : t.type === "foyer/bypass" ? Z(e, "zones.bypass") : t.type === "foyer/arm" ? t.force ? Z(e, "overview.force_arm") : Z(e, "card.arm") : Z(e, "card.code_confirm") : Z(e, "card.code_confirm");
	}
	_renderPad(e) {
		return F`
      <div class="pad">
        <div class="display" aria-live="polite" aria-label=${Z(e, "card.code_entered")}>
          ${this._code ? "•".repeat(this._code.length) : F`<span class="placeholder"
                >${Z(e, "card.code_hint", { n: this._codeLength })}</span
              >`}
        </div>
        <div class="keys">
          ${[
			"1",
			"2",
			"3",
			"4",
			"5",
			"6",
			"7",
			"8",
			"9"
		].map((e) => F`<button
              class="key"
              ?disabled=${this._busy}
              @click=${() => this._press(e)}
            >
              ${e}
            </button>`)}
          <button
            class="key word"
            ?disabled=${this._busy || !this._code}
            @click=${() => this._code = ""}
          >
            ${Z(e, "card.code_clear")}
          </button>
          <button class="key" ?disabled=${this._busy} @click=${() => this._press("0")}>
            0
          </button>
          ${this._pending ? F`<button
                class="key word confirm"
                ?disabled=${this._busy || !this._code}
                @click=${() => this._run(this._pending)}
              >
                ${this._pendingLabel(e)}
              </button>` : L}
        </div>
      </div>
    `;
	}
	_renderKeypadLayout(e) {
		let t = this._status;
		if (!t) return this._message(Z(e, "common.loading"));
		let n = this._area, r = this._isMaster ? t.master.state : n?.state ?? "disarmed", i = this._isMaster ? t.areas.some((e) => e.memory) : !!n?.memory, a = r !== "disarmed" || i, o = this._isMaster ? t.scenarios : [], s = t.scenarios.find((e) => e.id === t.active_scenario_id);
		return F`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(e)}
          ${this._head(this._isMaster ? s?.name ?? Z(e, "overview.master") : n?.name ?? "", r, i)}
          ${n ? this._countdown(e, n) : L}
          ${this._renderPad(e)}
          <div class="buttons">
            ${a ? L : o.length ? o.map((e) => F`<button
                      ?disabled=${this._busy}
                      @click=${() => this._run({
			type: "foyer/arm",
			scenario_id: e.id
		})}
                    >
                      ${e.name}
                    </button>`) : F`<button
                    ?disabled=${this._busy}
                    @click=${() => this._run({
			type: "foyer/arm",
			area_id: n?.id
		})}
                  >
                    ${Z(e, "card.arm")}
                  </button>`}
            ${a ? F`<button
                  class="primary"
                  ?disabled=${this._busy}
                  @click=${() => this._run({
			type: "foyer/disarm",
			...this._isMaster || !n ? {} : { area_ids: [n.id] }
		})}
                >
                  ${Z(e, "card.disarm")}
                </button>` : L}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
	}
	_renderInlinePad(e) {
		return this._codeUsed ? this._padOpen ? F`${this._renderPad(e)}
      <button
        class="link pad-toggle"
        @click=${() => {
			this._padOpen = !1, this._code = "", this._pending = void 0;
		}}
      >
        ${Z(e, "card.code_hide")}
      </button>` : F`<button class="link pad-toggle" @click=${() => this._padOpen = !0}>
        ${Z(e, "card.code_show")}
      </button>` : L;
	}
	_renderFeedback() {
		let e = this._feedback;
		if (!e) return L;
		let t = this._strings;
		return F`<div class="feedback ${e.warning ? "warning" : ""}" role="alert">
      <div>${e.text}</div>
      ${e.retry ? F`<button
              class="force"
              ?disabled=${this._busy}
              @click=${() => this._run(e.retry)}
            >
              ${Z(t, "overview.force_arm")}
            </button>
            <span class="force-hint">${Z(t, "overview.force_arm_hint")}</span>` : L}
    </div>`;
	}
	_message(e) {
		return F`<ha-card><div class="content">${e}</div></ha-card>`;
	}
	static {
		this.styles = [Ee, o`
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
      .keys {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
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
      /* A word instead of a digit — "Clear", "Disarm" — so it is set
         smaller to fit the same square. It does not span two columns, and
         has never been asked to: the pad is three columns, and with a
         pending command the last row fills exactly. */
      .key.word {
        font-size: 14px;
      }
      .key.confirm {
        border-color: var(--primary-color);
        color: var(--primary-color);
        font-weight: 500;
      }
      .pad-toggle {
        align-self: flex-start;
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
      .blocking .link {
        background: none;
        border: 0;
        padding: 0;
        color: var(--primary-color);
        font: inherit;
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
        flex: 1;
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
      .state.auto-chip {
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
        font-weight: 600;
      }
      .state.walk-chip {
        background: var(--warning-color, #c77700);
        color: var(--text-primary-color, #fff);
        font-weight: 600;
      }
    `];
	}
};
customElements.get("foyer-card") || customElements.define("foyer-card", je);
var Me = class extends q {
	constructor(...e) {
		super(...e), this._config = { type: "custom:foyer-card" };
	}
	static {
		this.properties = {
			hass: { attribute: !1 },
			_config: { state: !0 },
			_strings: { state: !0 }
		};
	}
	setConfig(e) {
		this._config = e;
	}
	willUpdate(e) {
		e.has("hass") && this.hass && this.hass.language !== this._language && (this._language = this.hass.language, Te(this.hass).then((e) => this._strings = e));
	}
	_emit(e) {
		this._config = {
			...this._config,
			...e
		}, this.dispatchEvent(new CustomEvent("config-changed", {
			detail: { config: this._config },
			bubbles: !0,
			composed: !0
		}));
	}
	render() {
		let e = this._strings;
		if (!e || !this.hass) return L;
		let t = Object.keys(this.hass.states).filter((e) => e.startsWith(Oe)).sort();
		return F`
      <div class="editor">
        <label>
          <span>${Z(e, "card.editor_entity")}</span>
          <select
            @change=${(e) => this._emit({ entity: e.target.value })}
          >
            ${t.map((t) => F`<option .value=${t} .selected=${Y(t === this._config.entity)}>
                ${t === $ ? Z(e, "card.editor_master") : String(this.hass.states[t]?.attributes.friendly_name ?? t)}
              </option>`)}
          </select>
        </label>
        <label>
          <span>${Z(e, "card.editor_layout")}</span>
          <select
            @change=${(e) => this._emit({ layout: e.target.value })}
          >
            ${[
			"full",
			"compact",
			"badge",
			"keypad"
		].map((t) => F`<option
                .value=${t}
                .selected=${Y(t === (this._config.layout ?? "full"))}
              >
                ${Z(e, `card.layout_${t}`)}
              </option>`)}
          </select>
        </label>
        <p class="hint">${Z(e, "card.editor_hint")}</p>
      </div>
    `;
	}
	static {
		this.styles = o`
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
};
customElements.get("foyer-card-editor") || customElements.define("foyer-card-editor", Me), window.customCards = window.customCards ?? [], window.customCards.some((e) => e.type === "foyer-card") || window.customCards.push({
	type: "foyer-card",
	name: "Foyer Home Defender",
	preview: !0
});
//#endregion
