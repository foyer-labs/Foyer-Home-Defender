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
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: f, getOwnPropertySymbols: ee, getPrototypeOf: te } = Object, p = globalThis, m = p.trustedTypes, ne = m ? m.emptyScript : "", re = p.reactiveElementPolyfillSupport, h = (e, t) => e, g = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? ne : null;
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
}, ie = (e, t) => !l(e, t), ae = {
	attribute: !0,
	type: String,
	converter: g,
	reflect: !1,
	useDefault: !1,
	hasChanged: ie
};
Symbol.metadata ??= Symbol("metadata"), p.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var _ = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = ae) {
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
		return this.elementProperties.get(e) ?? ae;
	}
	static _$Ei() {
		if (this.hasOwnProperty(h("elementProperties"))) return;
		let e = te(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(h("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(h("properties"))) {
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
			let i = (n.converter?.toAttribute === void 0 ? g : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? g : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? ie)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
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
_.elementStyles = [], _.shadowRootOptions = { mode: "open" }, _[h("elementProperties")] = /* @__PURE__ */ new Map(), _[h("finalized")] = /* @__PURE__ */ new Map(), re?.({ ReactiveElement: _ }), (p.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
var v = globalThis, y = (e) => e, b = v.trustedTypes, x = b ? b.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, S = "$lit$", C = `lit$${Math.random().toFixed(9).slice(2)}$`, w = "?" + C, oe = `<${w}>`, T = document, E = () => T.createComment(""), D = (e) => e === null || typeof e != "object" && typeof e != "function", O = Array.isArray, k = (e) => O(e) || typeof e?.[Symbol.iterator] == "function", A = "[ 	\n\f\r]", j = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, se = /-->/g, M = />/g, N = RegExp(`>|${A}(?:([^\\s"'>=/]+)(${A}*=${A}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), P = /'/g, ce = /"/g, le = /^(?:script|style|textarea|title)$/i, F = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), I = Symbol.for("lit-noChange"), L = Symbol.for("lit-nothing"), ue = /* @__PURE__ */ new WeakMap(), R = T.createTreeWalker(T, 129);
function de(e, t) {
	if (!O(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return x === void 0 ? t : x.createHTML(t);
}
var z = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = j;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === j ? c[1] === "!--" ? o = se : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = N) : (le.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = N) : o = M : o === N ? c[0] === ">" ? (o = i ?? j, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? N : c[3] === "\"" ? ce : P) : o === ce || o === P ? o = N : o === se || o === M ? o = j : (o = N, i = void 0);
		let d = o === N && e[t + 1].startsWith("/>") ? " " : "";
		a += o === j ? n + oe : l >= 0 ? (r.push(s), n.slice(0, l) + S + n.slice(l) + C + d) : n + C + (l === -2 ? t : d);
	}
	return [de(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, B = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = z(t, n);
		if (this.el = e.createElement(l, r), R.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = R.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(S)) {
					let t = u[o++], n = i.getAttribute(e).split(C), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? G : r[1] === "?" ? fe : r[1] === "@" ? pe : W
					}), i.removeAttribute(e);
				} else e.startsWith(C) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (le.test(i.tagName)) {
					let e = i.textContent.split(C), t = e.length - 1;
					if (t > 0) {
						i.textContent = b ? b.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], E()), R.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], E());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === w) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(C, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += C.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = T.createElement("template");
		return n.innerHTML = e, n;
	}
};
function V(e, t, n = e, r) {
	if (t === I) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = D(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = V(e, i._$AS(e, t.values), i, r)), t;
}
var H = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? T).importNode(t, !0);
		R.currentNode = r;
		let i = R.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new U(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new me(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = R.nextNode(), a++);
		}
		return R.currentNode = T, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, U = class e {
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
		e = V(this, e, t), D(e) ? e === L || e == null || e === "" ? (this._$AH !== L && this._$AR(), this._$AH = L) : e !== this._$AH && e !== I && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? k(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== L && D(this._$AH) ? this._$AA.nextSibling.data = e : this.T(T.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = B.createElement(de(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new H(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = ue.get(e.strings);
		return t === void 0 && ue.set(e.strings, t = new B(e)), t;
	}
	k(t) {
		O(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(E()), this.O(E()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = y(e).nextSibling;
			y(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, W = class {
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
		if (i === void 0) e = V(this, e, t, 0), a = !D(e) || e !== this._$AH && e !== I, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = V(this, r[n + o], t, o), s === I && (s = this._$AH[o]), a ||= !D(s) || s !== this._$AH[o], s === L ? e = L : e !== L && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === L ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, G = class extends W {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === L ? void 0 : e;
	}
}, fe = class extends W {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== L);
	}
}, pe = class extends W {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = V(this, e, t, 0) ?? L) === I) return;
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
		V(this, e);
	}
}, he = {
	M: S,
	P: C,
	A: w,
	C: 1,
	L: z,
	R: H,
	D: k,
	V,
	I: U,
	H: W,
	N: fe,
	U: pe,
	B: G,
	F: me
}, ge = v.litHtmlPolyfillSupport;
ge?.(B, U), (v.litHtmlVersions ??= []).push("3.3.3");
var _e = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new U(t.insertBefore(E(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, K = globalThis, q = class extends _ {
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
function De(e, t = {}) {
	let n = e?.config?.time_zone;
	return n ? {
		...t,
		timeZone: n
	} : t;
}
function Oe(e) {
	let t = Math.max(0, Math.round(e));
	return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function Q(e, t = 0) {
	return Math.max(0, Math.round((Date.parse(e) - (Date.now() + t)) / 1e3));
}
//#endregion
//#region src/card/foyer-card.ts
var ke = "alarm_control_panel.foyer_", $ = "alarm_control_panel.foyer_master";
function Ae(e) {
	let t = e.entities;
	return Object.keys(e.states).filter((e) => e.startsWith("alarm_control_panel.")).filter((e) => t?.[e] ? t[e].platform === "foyer" : e.startsWith(ke)).sort();
}
function je(e) {
	let t = e.entities;
	return t ? Object.values(t).find((e) => e.platform === "foyer" && e.translation_key === "master")?.entity_id ?? (e.states[$] ? $ : void 0) : e.states[$] ? $ : void 0;
}
var Me = /* @__PURE__ */ new Set(["zone_open", "zone_fault"]), Ne = /* @__PURE__ */ new Set(["code_required", "bad_code"]), Pe = 3e4, Fe = /* @__PURE__ */ new Set([
	"foyer/auto/cancel",
	"foyer/acknowledge",
	"foyer/walk_test"
]), Ie = class extends q {
	constructor(...e) {
		super(...e), this._busy = !1, this._code = "", this._padOpen = !1, this._retype = !1, this._tick = 0, this._offset = 0;
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
			_retype: { state: !0 },
			_tick: { state: !0 }
		};
	}
	static getStubConfig(e) {
		let t = Ae(e), n = je(e);
		return {
			type: "custom:foyer-card",
			entity: n && t.includes(n) ? n : t[0],
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
		this._code.length >= this._codeLength || (this._code += e, this._feedback = void 0, this._retype = !1, this._touch());
	}
	_touch() {
		window.clearTimeout(this._idle), this._idle = window.setTimeout(() => this._expire(), Pe);
	}
	_forget() {
		window.clearTimeout(this._idle), this._idle = void 0, this._code = "", this._pending = void 0, this._retype = !1;
	}
	_expire() {
		this._forget(), this._feedback = void 0, this._entryOpened || (this._padOpen = !1);
	}
	_padKey(e) {
		if (!(this._busy || e.ctrlKey || e.metaKey || e.altKey)) {
			if (/^[0-9]$/.test(e.key)) this._press(e.key);
			else if (e.key === "Backspace") this._code = this._code.slice(0, -1), this._touch();
			else if (e.key === "Enter" && this._pending && this._code) this._run(this._pending);
			else return;
			e.preventDefault();
		}
	}
	connectedCallback() {
		super.connectedCallback(), this._timer = window.setInterval(() => {
			(this._area?.timer || this._status?.areas.some((e) => e.timer) || this._status?.walk_test || this._pendingAuto || this._status?.security.locked_until) && (this._tick += 1);
		}, 1e3);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._unsubscribe?.then((e) => e()).catch(() => void 0), this._unsubscribe = void 0, window.clearInterval(this._timer), this._forget(), this._padOpen = !1, this._feedback = void 0;
	}
	willUpdate(e) {
		e.has("hass") && this.hass && (this.hass.language !== this._language && (this._language = this.hass.language, Te(this.hass).then((e) => this._strings = e).catch(() => {
			this._language = void 0;
		})), !this._unsubscribe && this.isConnected && (this._unsubscribe = this.hass.connection.subscribeMessage((e) => {
			this._offset = Date.parse(e.now) - Date.now(), this._status = e;
			let t = this._entryWantsCode();
			t && t !== this._entryOpened && (this._padOpen = !0), this._entryOpened = t;
		}, { type: "foyer/subscribe" }), this._unsubscribe.catch(() => this._unsubscribe = void 0)));
	}
	get _isMaster() {
		let e = this._config?.entity, t = this._status?.master.entity_id;
		return t ? e === t : e === $;
	}
	get _area() {
		return this._status?.areas.find((e) => e.entity_id === this._config?.entity);
	}
	_entryWantsCode() {
		let e = this._status;
		if (!e || !this._codeUsed) return;
		let t = this._area;
		return (this._isMaster || !t ? e.areas : [t]).find((t) => t.timer?.kind === "entry" && (t.require_code?.disarm ?? e.security.require_code?.disarm))?.timer?.due;
	}
	_isPending(e) {
		let t = this._pending;
		if (!t || t.type !== e.type) return !1;
		let n = (e) => JSON.stringify({
			...e,
			force: void 0
		});
		return n(t) === n(e);
	}
	_primary(e) {
		return e && !this._pending ? "primary" : "";
	}
	_targetOf(e) {
		let t = this._status, n = this._strings;
		return e.scenario_id ? t?.scenarios.find((t) => t.id === e.scenario_id)?.name ?? "" : e.area_id ? t?.areas.find((t) => t.id === e.area_id)?.name ?? "" : Array.isArray(e.area_ids) ? e.area_ids.map((e) => t?.areas.find((t) => t.id === e)?.name ?? "").join(", ") : e.zone_id ? t?.zones.find((t) => t.id === e.zone_id)?.name ?? "" : e.pending_id ? t?.auto?.pending.find((t) => t.id === e.pending_id)?.rule_name ?? "" : Z(n, "overview.master");
	}
	_disarmLabel(e, t) {
		let n = this._strings;
		return e === "disarmed" && t ? Z(n, "card.clear_memory") : Z(n, "card.disarm");
	}
	async _run(e) {
		if (!this.hass) return;
		this._busy = !0, this._feedback = void 0;
		let t = this._pending, n = t !== void 0 && JSON.stringify(t) === JSON.stringify(e), r = t ? !n : Fe.has(String(e.type)), i = r ? "" : this._code;
		r || this._forget();
		try {
			let t = await this.hass.callWS({
				...e,
				...i ? { code: i } : {}
			});
			if (!this.isConnected || (r || (this._pending = void 0), t.success && !this._pending && (this._padOpen = !1), t.success && t.low_battery_zones.length && (this._feedback = {
				text: Z(this._strings, "card.low_battery", { zones: t.low_battery_zones.map((e) => e.name).join(", ") }),
				warning: !0
			}), !t.success && t.reason === "nothing_to_cancel" && e.type === "foyer/auto/cancel")) return;
			if (!t.success) {
				if (Ne.has(t.reason ?? "")) {
					if (r && (this._retype = !!this._code, this._code = ""), this._padOpen = !0, this._pending = e, this._touch(), t.reason === "code_required") return;
					this._feedback = {
						text: Z(this._strings, `reason.${t.reason}`),
						pad: !0,
						reason: t.reason ?? void 0
					};
					return;
				}
				if (t.reason === "locked_out") {
					this._code = "", this._padOpen = !0, this._feedback = {
						text: Z(this._strings, "reason.locked_out"),
						pad: !0,
						reason: "locked_out"
					};
					return;
				}
				this._feedback = {
					text: Z(this._strings, `reason.${t.reason ?? "unknown"}`, { zones: t.blocking_zones.map((e) => e.name).join(", ") }),
					retry: e.type === "foyer/arm" && !e.force && Me.has(t.reason ?? "") ? {
						...e,
						force: !0
					} : void 0
				};
			}
		} catch {
			this._feedback = { text: Z(this._strings, "card.not_sent") };
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
			(e.key === "Enter" || e.key === " ") && (e.preventDefault(), this._openMore());
		}}
      >
        <span class="badge-name">${s}</span>
        <span class="state ${i}">${d}</span>
        ${a ? F`<span class="state memory">${Z(e, "overview.memory")}</span>` : L}
        ${t.technical?.length ? F`<span class="state triggered">${Z(e, "card.technical_badge")}</span>` : L}
        ${t.incident && !t.incident.acknowledged ? F`<span class="state triggered">${Z(e, "card.incident_badge")}</span>` : L}
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
              >${Z(e, `card.auto_badge_${l.action}`, { seconds: Q(l.due, this._offset) })}</span
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
		let n = this._area, r = this._isMaster || !n, i = r ? t.master.state : n.state, a = r ? t.areas.some((e) => e.memory) : n.memory, o = t.scenarios.find((e) => e.id === t.active_scenario_id), s = r ? o?.name ?? Z(e, "overview.master") : n.name, c = r ? t.areas.some((e) => e.state !== "disarmed" || e.memory) : n.state !== "disarmed" || n.memory, l = r ? t.areas.find((e) => e.timer && e.timer.kind !== "siren") : n, u = {
			type: "foyer/arm",
			area_id: n?.id
		}, d = r ? { type: "foyer/disarm" } : {
			type: "foyer/disarm",
			area_ids: [n.id]
		}, f = (this._pending?.type === "foyer/arm" ? String(this._pending.scenario_id ?? "") : "") || o?.id;
		return F`
      <ha-card>
        <div class="content compact">
          ${this._renderAlerts(e)} ${this._head(s, i, a)}
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
                  <option value="" .selected=${Y(!f)}>
                    ${Z(e, "card.pick_scenario")}
                  </option>
                  ${t.scenarios.map((e) => F`<option .value=${e.id} .selected=${Y(e.id === f)}>
                      ${e.name}
                    </option>`)}
                </select>` : n.state === "disarmed" && !this._isPending(u) ? F`<button
                    class=${this._primary(!0)}
                    ?disabled=${this._busy}
                    @click=${() => this._run(u)}
                  >
                    ${Z(e, "card.arm")}
                  </button>` : L}
            ${c && !this._isPending(d) ? F`<button
                  class=${this._primary(i === "entry" || i === "triggered")}
                  ?disabled=${this._busy}
                  @click=${() => this._run(d)}
                >
                  ${this._disarmLabel(i, a)}
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
		let n = t.state !== "disarmed" || t.memory, r = {
			type: "foyer/arm",
			area_id: t.id
		}, i = {
			type: "foyer/disarm",
			area_ids: [t.id]
		};
		return F`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(e)} ${this._head(t.name, t.state, t.memory)}
          ${this._countdown(e, t)} ${this._renderBlocking(e, t)}
          ${this._renderInlinePad(e)}
          <div class="buttons">
            ${t.state === "disarmed" && !this._isPending(r) ? F`<button
                  class=${this._primary(!0)}
                  ?disabled=${this._busy}
                  @click=${() => this._run(r)}
                >
                  ${Z(e, "card.arm")}
                </button>` : L}
            ${n && !this._isPending(i) ? F`<button
                  class=${this._primary(t.state === "entry" || t.state === "triggered")}
                  ?disabled=${this._busy}
                  @click=${() => this._run(i)}
                >
                  ${this._disarmLabel(t.state, t.memory)}
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
        <div class="blocking-hd">${Z(e, "card.not_ready")}</div>
        ${r.map((t) => F`<div class="row">
            <span>${t.name}</span>
            ${t.bypassable && !t.bypassed ? F`<button
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
		let n = t.areas.some((e) => e.memory), r = t.scenarios.find((e) => e.id === t.active_scenario_id), i = t.areas.some((e) => e.state !== "disarmed" || e.memory), a = this._alarmRunning, o = { type: "foyer/disarm" };
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
            ${a ? L : this._scenarioButtons(e, t.active_scenario_id)}
            ${i && !this._isPending(o) ? F`<button
                  class=${this._primary(a)}
                  ?disabled=${this._busy}
                  @click=${() => this._run(o)}
                >
                  ${this._disarmLabel(t.master.state, n)}
                </button>` : L}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
	}
	get _alarmRunning() {
		let e = (e) => e.state === "entry" || e.state === "triggered", t = this._area;
		return t && !this._isMaster ? e(t) : !!this._status?.areas.some(e);
	}
	_scenarioButtons(e, t) {
		return (this._status?.scenarios ?? []).map((n) => {
			let r = {
				type: "foyer/arm",
				scenario_id: n.id
			};
			return this._isPending(r) ? L : F`<button
        class=${this._primary(n.id === t)}
        ?disabled=${this._busy}
        @click=${() => this._run(r)}
      >
        ${Z(e, "card.arm_scenario", { scenario: n.name })}
      </button>`;
		});
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
          ${Z(e, "walk.card_banner", { time: Oe(n) })}
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
        ${this._status?.walk_test ? F`<span class="state walk-chip" title=${Z(r, "walk.badge_title")}
              >${Z(r, "walk.badge")}</span
            >` : L}
      </div>
    `;
	}
	_countdown(e, t, n = !1) {
		if (!t.timer || t.timer.kind === "siren") return L;
		let r = Math.max(0, Math.round((Date.parse(t.timer.due) - (Date.now() + this._offset)) / 1e3)), i = Z(e, `timer.${t.timer.kind}`, { seconds: r });
		return F`<div class="countdown ${t.timer.kind}">
      ${n ? Z(e, "card.area_countdown", {
			area: t.name,
			countdown: i
		}) : i}
    </div>`;
	}
	_pendingLabel(e) {
		let t = this._pending;
		if (!t) return Z(e, "card.code_confirm");
		let n = this._targetOf(t);
		switch (t.type) {
			case "foyer/disarm": return Z(e, "card.confirm_disarm", { target: n });
			case "foyer/bypass": return Z(e, "card.confirm_bypass", { target: n });
			case "foyer/arm": return Z(e, t.force ? "card.confirm_force" : "card.confirm_arm", { target: n });
			case "foyer/walk_test": return Z(e, "walk.end");
			case "foyer/auto/cancel": return Z(e, "rules.cancel_now");
			case "foyer/acknowledge": return Z(e, "common.acknowledge");
			default: return Z(e, "card.code_confirm");
		}
	}
	_pendingCaption(e) {
		let t = this._pending;
		if (!t) return;
		let n = this._targetOf(t);
		switch (t.type) {
			case "foyer/disarm": return Z(e, "card.code_for_disarm", { target: n });
			case "foyer/bypass": return Z(e, "card.code_for_bypass", { target: n });
			case "foyer/arm": return Z(e, t.force ? "card.code_for_force" : "card.code_for_arm", { target: n });
			case "foyer/walk_test": return Z(e, "card.code_for_walk");
			case "foyer/auto/cancel": return Z(e, "card.code_for_cancel", { target: n });
			case "foyer/acknowledge": return Z(e, t.target === "technical" ? "card.code_for_ack_technical" : "card.code_for_ack_incident");
			default: return;
		}
	}
	_renderPad(e) {
		let t = [
			"1",
			"2",
			"3",
			"4",
			"5",
			"6",
			"7",
			"8",
			"9"
		], n = this._lockedUntil, r = this._pendingCaption(e), i = this._feedback?.pad && !(n && this._feedback.reason === "locked_out") ? this._feedback : void 0;
		return F`
      <div class="pad" tabindex="0" @keydown=${(e) => this._padKey(e)}>
        ${r ? F`<div class="pad-for">${r}</div>` : L}
        ${this._retype ? F`<div class="pad-note" role="status">${Z(e, "card.code_retype")}</div>` : L}
        ${n ? F`<div class="locked" role="status">
              ${Z(e, "card.locked_until", { time: n.toLocaleTimeString(this.hass?.language, De(this.hass, {
			hour: "2-digit",
			minute: "2-digit"
		})) })}
            </div>` : L}
        <div class="display" aria-live="polite" aria-label=${Z(e, "card.code_entered")}>
          ${this._code ? "•".repeat(this._code.length) : F`<span class="placeholder"
                >${Z(e, "card.code_hint", { n: this._codeLength })}</span
              >`}
        </div>
        ${i ? F`<div class="pad-error" role="alert">${i.text}</div>` : L}
        <div class="keys">
          ${t.map((e) => F`<button
              class="key"
              ?disabled=${this._busy}
              @click=${() => this._press(e)}
            >
              ${e}
            </button>`)}
          <button
            class="key word"
            ?disabled=${this._busy || !this._code}
            @click=${() => {
			this._code = "", this._touch();
		}}
          >
            ${Z(e, "card.code_clear")}
          </button>
          <button class="key" ?disabled=${this._busy} @click=${() => this._press("0")}>
            0
          </button>
        </div>
        ${this._pending ? F`<button
              class="key word confirm"
              ?disabled=${this._busy || !this._code}
              @click=${() => this._run(this._pending)}
            >
              ${this._pendingLabel(e)}
            </button>` : L}
      </div>
    `;
	}
	get _lockedUntil() {
		let e = this._status?.security.locked_until;
		if (!e) return;
		let t = new Date(e);
		return t.getTime() > Date.now() + this._offset ? t : void 0;
	}
	_renderKeypadLayout(e) {
		let t = this._status;
		if (!t) return this._message(Z(e, "common.loading"));
		let n = this._area, r = this._isMaster ? t.master.state : n?.state ?? "disarmed", i = this._isMaster ? t.areas.some((e) => e.memory) : !!n?.memory, a = r !== "disarmed" || i, o = {
			type: "foyer/arm",
			area_id: n?.id
		}, s = {
			type: "foyer/disarm",
			...this._isMaster || !n ? {} : { area_ids: [n.id] }
		}, c = t.scenarios.find((e) => e.id === t.active_scenario_id);
		return F`
      <ha-card>
        <div class="content">
          ${this._renderAlerts(e)}
          ${this._head(this._isMaster ? c?.name ?? Z(e, "overview.master") : n?.name ?? "", r, i)}
          ${this._isMaster ? t.areas.filter((e) => e.timer && e.timer.kind !== "siren").map((t) => this._countdown(e, t, !0)) : n ? this._countdown(e, n) : L}
          ${this._renderPad(e)}
          <div class="buttons">
            ${a || this._alarmRunning ? L : this._isMaster && t.scenarios.length ? this._scenarioButtons(e) : this._isPending(o) ? L : F`<button ?disabled=${this._busy} @click=${() => this._run(o)}>
                      ${Z(e, "card.arm")}
                    </button>`}
            ${a && !this._isPending(s) ? F`<button
                  class=${this._primary(!0)}
                  ?disabled=${this._busy}
                  @click=${() => this._run(s)}
                >
                  ${this._disarmLabel(r, i)}
                </button>` : L}
          </div>
          ${this._renderFeedback()}
        </div>
      </ha-card>
    `;
	}
	_renderInlinePad(e) {
		return !this._codeUsed && !this._pending ? L : !this._padOpen && !this._pending ? F`<button class="link pad-toggle" @click=${() => this._padOpen = !0}>
        ${Z(e, "card.code_show")}
      </button>` : F`${this._renderPad(e)}
      <button
        class="link pad-toggle"
        @click=${() => {
			this._padOpen = !1, this._forget(), this._feedback?.pad && (this._feedback = void 0);
		}}
      >
        ${Z(e, "card.code_hide")}
      </button>`;
	}
	get _padShown() {
		return this._layout === "keypad" || this._layout !== "badge" && (this._codeUsed || !!this._pending) && (this._padOpen || !!this._pending);
	}
	_renderFeedback() {
		let e = this._feedback;
		if (!e || e.pad && this._padShown) return L;
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
    `];
	}
};
customElements.get("foyer-card") || customElements.define("foyer-card", Ie);
var Le = class extends q {
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
		e.has("hass") && this.hass && this.hass.language !== this._language && (this._language = this.hass.language, Te(this.hass).then((e) => this._strings = e).catch(() => this._language = void 0));
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
		let t = je(this.hass), n = Ae(this.hass).sort((e, n) => Number(n === t || n === $) - Number(e === t || e === $)), r = this._config.layout ?? "full";
		return !this._config.entity && n.length && queueMicrotask(() => this._emit({ entity: n[0] })), F`
      <div class="editor">
        <label>
          <span>${Z(e, "card.editor_entity")}</span>
          <select
            @change=${(e) => this._emit({ entity: e.target.value })}
          >
            ${n.map((n) => F`<option .value=${n} .selected=${Y(n === this._config.entity)}>
                ${n === $ || n === t ? Z(e, "card.editor_master") : String(this.hass.states[n]?.attributes.friendly_name ?? n)}
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
		].map((t) => F`<option .value=${t} .selected=${Y(t === r)}>
                ${Z(e, `card.layout_${t}`)}
              </option>`)}
          </select>
          <span class="hint">${Z(e, `card.layout_hint_${r}`)}</span>
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
customElements.get("foyer-card-editor") || customElements.define("foyer-card-editor", Le), window.customCards = window.customCards ?? [], window.customCards.some((e) => e.type === "foyer-card") || window.customCards.push({
	type: "foyer-card",
	name: "Foyer Home Defender",
	preview: !0
});
//#endregion
