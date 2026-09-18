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
}, g = (e, t) => !l(e, t), ae = {
	attribute: !0,
	type: String,
	converter: h,
	reflect: !1,
	useDefault: !1,
	hasChanged: g
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
_.elementStyles = [], _.shadowRootOptions = { mode: "open" }, _[m("elementProperties")] = /* @__PURE__ */ new Map(), _[m("finalized")] = /* @__PURE__ */ new Map(), ie?.({ ReactiveElement: _ }), (p.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
var v = globalThis, oe = (e) => e, y = v.trustedTypes, se = y ? y.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, ce = "$lit$", b = `lit$${Math.random().toFixed(9).slice(2)}$`, le = "?" + b, ue = `<${le}>`, x = document, S = () => x.createComment(""), C = (e) => e === null || typeof e != "object" && typeof e != "function", w = Array.isArray, de = (e) => w(e) || typeof e?.[Symbol.iterator] == "function", T = "[ 	\n\f\r]", E = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, fe = /-->/g, D = />/g, O = RegExp(`>|${T}(?:([^\\s"'>=/]+)(${T}*=${T}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), pe = /'/g, me = /"/g, he = /^(?:script|style|textarea|title)$/i, k = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), A = Symbol.for("lit-noChange"), j = Symbol.for("lit-nothing"), ge = /* @__PURE__ */ new WeakMap(), M = x.createTreeWalker(x, 129);
function _e(e, t) {
	if (!w(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return se === void 0 ? t : se.createHTML(t);
}
var ve = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = E;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === E ? c[1] === "!--" ? o = fe : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = O) : (he.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = O) : o = D : o === O ? c[0] === ">" ? (o = i ?? E, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? O : c[3] === "\"" ? me : pe) : o === me || o === pe ? o = O : o === fe || o === D ? o = E : (o = O, i = void 0);
		let d = o === O && e[t + 1].startsWith("/>") ? " " : "";
		a += o === E ? n + ue : l >= 0 ? (r.push(s), n.slice(0, l) + ce + n.slice(l) + b + d) : n + b + (l === -2 ? t : d);
	}
	return [_e(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, N = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = ve(t, n);
		if (this.el = e.createElement(l, r), M.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = M.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(ce)) {
					let t = u[o++], n = i.getAttribute(e).split(b), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? be : r[1] === "?" ? xe : r[1] === "@" ? Se : I
					}), i.removeAttribute(e);
				} else e.startsWith(b) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (he.test(i.tagName)) {
					let e = i.textContent.split(b), t = e.length - 1;
					if (t > 0) {
						i.textContent = y ? y.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], S()), M.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], S());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === le) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(b, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += b.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = x.createElement("template");
		return n.innerHTML = e, n;
	}
};
function P(e, t, n = e, r) {
	if (t === A) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = C(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = P(e, i._$AS(e, t.values), i, r)), t;
}
var ye = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? x).importNode(t, !0);
		M.currentNode = r;
		let i = M.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new F(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Ce(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = M.nextNode(), a++);
		}
		return M.currentNode = x, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, F = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = j, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = P(this, e, t), C(e) ? e === j || e == null || e === "" ? (this._$AH !== j && this._$AR(), this._$AH = j) : e !== this._$AH && e !== A && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? de(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== j && C(this._$AH) ? this._$AA.nextSibling.data = e : this.T(x.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = N.createElement(_e(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new ye(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = ge.get(e.strings);
		return t === void 0 && ge.set(e.strings, t = new N(e)), t;
	}
	k(t) {
		w(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(S()), this.O(S()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = oe(e).nextSibling;
			oe(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, I = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = j, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = j;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = P(this, e, t, 0), a = !C(e) || e !== this._$AH && e !== A, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = P(this, r[n + o], t, o), s === A && (s = this._$AH[o]), a ||= !C(s) || s !== this._$AH[o], s === j ? e = j : e !== j && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === j ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, be = class extends I {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === j ? void 0 : e;
	}
}, xe = class extends I {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== j);
	}
}, Se = class extends I {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = P(this, e, t, 0) ?? j) === A) return;
		let n = this._$AH, r = e === j && n !== j || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== j && (n === j || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Ce = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		P(this, e);
	}
}, we = v.litHtmlPolyfillSupport;
we?.(N, F), (v.litHtmlVersions ??= []).push("3.3.3");
var Te = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new F(t.insertBefore(S(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, L = globalThis, R = class extends _ {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Te(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return A;
	}
};
R._$litElement$ = !0, R.finalized = !0, L.litElementHydrateSupport?.({ LitElement: R });
var Ee = L.litElementPolyfillSupport;
Ee?.({ LitElement: R }), (L.litElementVersions ??= []).push("4.2.2");
//#endregion
//#region node_modules/lit-html/directive.js
var De = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, Oe = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), ke = class {
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
}, z = class extends ke {
	constructor(e) {
		if (super(e), this.it = j, e.type !== De.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
	}
	render(e) {
		if (e === j || e == null) return this._t = void 0, this.it = e;
		if (e === A) return e;
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
z.directiveName = "unsafeHTML", z.resultType = 1;
//#endregion
//#region node_modules/lit-html/directives/unsafe-svg.js
var B = class extends z {};
B.directiveName = "unsafeSVG", B.resultType = 2;
var Ae = Oe(B), je = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n", Me = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n";
//#endregion
//#region src/shared/brand.ts
function Ne(e) {
	return e ? je : Me;
}
//#endregion
//#region src/shared/i18n.ts
var V = /* @__PURE__ */ new Map();
function Pe(e) {
	let t = e.language, n = V.get(t);
	return n || (n = e.callWS({
		type: "foyer/translations",
		language: t
	}).then((e) => e.strings), n.catch(() => V.delete(t)), V.set(t, n)), n;
}
function H(e, t, n = {}) {
	let r = e;
	for (let e of t.split(".")) if (r && typeof r == "object" && e in r) r = r[e];
	else return t;
	return typeof r == "string" ? r.replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e) : t;
}
//#endregion
//#region src/shared/styles.ts
var U = o`
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
`, W = o`
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
//#region src/panel/context.ts
function Fe(e, t, n) {
	let r = URL.createObjectURL(new Blob([t], { type: n })), i = document.createElement("a");
	i.href = r, i.download = e, i.click(), setTimeout(() => URL.revokeObjectURL(r), 1e3);
}
function Ie(e, t) {
	return Math.max(0, Math.round((Date.parse(t) - e.now()) / 1e3));
}
function Le(e, t) {
	let n = t.blocking_zones.map((e) => e.name).join(", ");
	return H(e, `reason.${t.reason ?? "unknown"}`, { zones: n });
}
function G(e, t) {
	let n = t.field ? H(e, `field.${t.field}`) : "";
	return H(e, `problem.${t.code}`, {
		field: n,
		detail: t.detail ?? ""
	});
}
function K(e) {
	let t = e.trim();
	if (t === "") return null;
	let n = Number(t);
	return Number.isFinite(n) ? n : null;
}
//#endregion
//#region src/panel/pages/overview.ts
function Re(e, t) {
	let n = H(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = H(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
var ze = /* @__PURE__ */ new Set(["zone_open", "zone_fault"]), Be = class extends R {
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
					let e = r.bypassed_zones.map((e) => e.name).join(", ");
					this._feedback = e ? {
						ok: !0,
						text: H(n.strings, "overview.bypassed", { zones: e })
					} : void 0;
				} else this._feedback = {
					ok: !1,
					text: Le(n.strings, r),
					retry: t && ze.has(r.reason ?? "") ? t : void 0
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
		if (!e) return j;
		let t = e.strings, n = e.status, r = n.areas.filter((e) => e.memory);
		return k`
      ${this._renderTechnical(t)} ${this._renderIncident(t)}
      ${n.security.enforced ? j : k`<div class="notice" role="note">
            ${H(t, "overview.no_codes_warning")}
          </div>`}
      ${r.map((e) => k`<div class="alarm-memory" role="alert">
          ${e.causes.length ? H(t, "overview.memory_banner", {
			area: e.name,
			zones: this._zoneNames(e.causes)
		}) : H(t, "overview.memory_banner_plain", { area: e.name })}
        </div>`)}
      ${this._renderMaster(t)} ${this._renderFeedback(t)}
      <div class="tiles">${n.areas.map((e) => this._renderArea(t, e))}</div>
      ${this._renderNotReady(t)} ${this._renderRecent(t)}
    `;
	}
	_renderRecent(e) {
		let t = this.ctx, n = this._recent;
		if (!n.length) return j;
		let r = new Map(t.status.areas.map((e) => [e.id, e.name])), i = new Map(t.status.zones.map((e) => [e.id, e.name]));
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(e, "overview.recent")}</h2>
          <span class="spacer"></span>
          <button class="btn sm" @click=${() => t.navigate("log")}>
            ${H(e, "overview.full_log")}
          </button>
        </div>
        <div class="card-bd">
          <div class="recent">
            ${n.map((n) => k`<div class="row">
                <span class="when mono"
                  >${new Date(n.ts).toLocaleTimeString(t.hass.language, {
			hour: "2-digit",
			minute: "2-digit"
		})}</span
                >
                <span class="state ${n.severity === "alarm" ? "triggered" : n.severity === "warning" ? "arming" : "disarmed"}"
                  >${Re(e, n.event_type)}</span
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
		if (!t.length) return j;
		let n = t.some((e) => !e.acknowledged);
		return k`
      <div class="banner technical" role="alert">
        <div class="banner-hd">${H(e, "overview.technical_title")}</div>
        <div>
          ${H(e, "overview.technical_banner", { zones: t.map((e) => e.name).join(", ") })}
        </div>
        <ul class="plain">
          ${t.map((t) => k`<li>
              <strong>${t.name}</strong> —
              ${H(e, t.acknowledged ? "technical_state.acknowledged" : t.active ? "technical_state.active" : "technical_state.memory")}
            </li>`)}
        </ul>
        ${n ? k`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("technical")}
              >
                ${H(e, "common.acknowledge")}
              </button>
            </div>` : j}
      </div>
    `;
	}
	_renderIncident(e) {
		let t = this.ctx.status.incident;
		return t ? k`
      <div class="banner incident" role="alert">
        <div class="banner-hd">
          ${H(e, "overview.incident_title", { id: t.id })}
          <span class="state ${t.acknowledged ? "memory" : "triggered"}">
            ${H(e, t.acknowledged ? "overview.incident_acknowledged" : "overview.incident_open")}
          </span>
        </div>
        <div>${H(e, "overview.incident_zones", { zones: this._zoneNames(t.zone_ids) })}</div>
        <div class="hint">${H(e, "overview.incident_hint")}</div>
        ${t.acknowledged ? j : k`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("incident")}
              >
                ${H(e, "common.acknowledge")}
              </button>
            </div>`}
      </div>
    ` : j;
	}
	_renderMaster(e) {
		let t = this.ctx.status, n = t.master, r = t.areas.some((e) => e.state !== "disarmed" || e.memory);
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(e, "overview.master")}</h2>
          <span class="state ${n.state}">${H(e, `state.${n.state}`)}</span>
          ${n.mode ? k`<span class="mono">${n.mode}</span>` : j}
        </div>
        <div class="card-bd">
          <div class="label">${H(e, "overview.scenario")}</div>
          <div class="chips">
            ${t.scenarios.length ? t.scenarios.map((e) => k`
                    <button
                      class="chip"
                      aria-pressed=${e.id === t.active_scenario_id ? "true" : "false"}
                      ?disabled=${this._busy}
                      @click=${() => this._arm({ scenario_id: e.id })}
                    >
                      ${e.name}
                    </button>
                  `) : k`<span class="muted">${H(e, "overview.no_scenarios")}</span>`}
          </div>
          <div class="hint">${H(e, "overview.scenario_hint")}</div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !r}
              @click=${() => this._disarm()}
            >
              ${H(e, "overview.disarm_all")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderFeedback(e) {
		let t = this._feedback;
		return t ? k`
      <div class=${t.ok ? "notice" : "problems"} role="alert">
        ${t.text}
        ${t.retry ? k`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._force(t.retry)}
              >
                ${H(e, "overview.force_arm")}
              </button>
              <span class="hint">${H(e, "overview.force_arm_hint")}</span>
            </div>` : j}
      </div>
    ` : j;
	}
	_renderArea(e, t) {
		let n = this.ctx, r = n.status.scenarios.find((e) => e.id === t.scenario_id);
		return k`
      <div class="card tile">
        <div class="card-bd">
          <div class="label">${H(e, "overview.area")}</div>
          <div class="name">${t.name}</div>
          <div class="row">
            <span class="state ${t.state}">${H(e, `state.${t.state}`)}</span>
            ${t.memory ? k`<span class="state memory">${H(e, "overview.memory")}</span>` : j}
          </div>
          ${t.timer && t.timer.kind !== "siren" ? k`<div class="countdown">
                ${H(e, `timer.${t.timer.kind}`, { seconds: Ie(n, t.timer.due) })}
              </div>` : j}
          <div class="hint">
            ${t.state === "disarmed" ? j : r ? H(e, "overview.by_scenario", { scenario: r.name }) : H(e, "overview.on_its_own")}
          </div>
          <div class="actions">
            ${t.state === "disarmed" ? k`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._arm({ area_id: t.id })}
                >
                  ${H(e, "overview.arm_area")}
                </button>` : j}
            ${t.state !== "disarmed" || t.memory ? k`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._disarm([t.id])}
                >
                  ${H(e, "overview.disarm_area")}
                </button>` : j}
          </div>
        </div>
      </div>
    `;
	}
	_renderNotReady(e) {
		let t = this.ctx, n = new Map(t.status.areas.map((e) => [e.id, e.name])), r = t.status.zones.filter((e) => e.enabled && (e.fault || e.open && e.channel === "intrusion" || e.bypassed));
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "overview.not_ready")}</h2></div>
        ${r.length ? k`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${H(e, "overview.zone")}</th>
                    <th>${H(e, "overview.area")}</th>
                    <th>${H(e, "overview.status")}</th>
                    <th>${H(e, "overview.entity_state")}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${r.map((t) => k`<tr>
                      <td>${t.name}</td>
                      <td>${n.get(t.area_id) ?? ""}</td>
                      <td>${this._zoneStatus(e, t)}</td>
                      <td class="mono">${t.state ?? "—"}</td>
                      <td>${this._renderBypass(e, t)}</td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : k`<div class="empty">${H(e, "overview.all_ready")}</div>`}
      </div>
    `;
	}
	_renderBypass(e, t) {
		let n = this.ctx;
		return t.bypassed ? k`<button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !1))}
      >
        ${H(e, "zones.unbypass")}
      </button>` : t.bypassable ? k`<div class="bypass">
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !0))}
      >
        ${H(e, "zones.bypass")}
      </button>
      ${[1, 8].map((r) => k`<button
          class="btn sm ghost"
          ?disabled=${this._busy}
          @click=${() => this._run(() => n.bypass(t.id, !0, r * 3600))}
        >
          ${H(e, "zones.bypass_hours", { hours: r })}
        </button>`)}
      <label class="minutes">
        <input
          type="number"
          min="1"
          max="10080"
          placeholder=${H(e, "zones.bypass_minutes_placeholder")}
          aria-label=${H(e, "zones.bypass_minutes")}
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
          ${H(e, "zones.bypass_minutes")}
        </button>
      </label>
    </div>` : j;
	}
	_bypassMinutes(e, t) {
		let n = this.ctx, r = Number(t.value);
		!Number.isFinite(r) || r < 1 || (t.value = "", this._run(() => n.bypass(e, !0, Math.round(r) * 60)));
	}
	_zoneStatus(e, t) {
		let n = this.ctx;
		if (t.fault) return k`<span class="state fault">${H(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) {
			let r = t.bypass_until ? H(e, "zones.bypass_until", { time: new Date(t.bypass_until).toLocaleTimeString(n.hass.language, {
				hour: "2-digit",
				minute: "2-digit"
			}) }) : H(e, "zones.bypass_indefinite");
			return k`<span class="state bypassed">${H(e, `bypass.${t.bypassed}`)}</span>
        <span class="hint">${t.bypassed === "manual" ? r : ""}</span>`;
		}
		return k`<span class="state open">${H(e, "zone_status.open")}</span>`;
	}
	static {
		this.styles = [
			U,
			W,
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
customElements.get("foyer-page-overview") || customElements.define("foyer-page-overview", Be);
//#endregion
//#region src/panel/code-fields.ts
function Ve(e, t, n, r) {
	return k`<label class="field">
    <span class="lbl">${H(e, t)}</span>
    <select
      @change=${(e) => {
		let t = e.target.value;
		r(t === "" ? null : t === "yes");
	}}
    >
      <option value="" ?selected=${n === null}>${H(e, "code_policy.inherit")}</option>
      <option value="yes" ?selected=${n === !0}>${H(e, "code_policy.required")}</option>
      <option value="no" ?selected=${n === !1}>${H(e, "code_policy.not_required")}</option>
    </select>
  </label>`;
}
function He(e, t, n, r) {
	return k`
    ${Ve(e, "field.require_code_to_arm", t.require_code_to_arm, (e) => n("require_code_to_arm", e))}
    ${Ve(e, "field.require_code_to_disarm", t.require_code_to_disarm, (e) => n("require_code_to_disarm", e))}
    <p class="hint span">
      ${H(e, "code_policy.strictest")}
      ${r ? j : k` ${H(e, "code_policy.inert")}`}
    </p>
  `;
}
//#endregion
//#region src/panel/profile-picker.ts
function Ue(e, t) {
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
function q(e, t, n, r) {
	let i = e.strings, a = e.config?.profiles ?? [];
	return k`<label class="field">
    <span class="lbl">${H(i, "field.response_profile_id")}</span>
    <select @change=${(e) => n(e.target.value || null)}>
      <option value="" ?selected=${!t}>${H(i, "profiles.inherit")}</option>
      ${a.map((e) => k`<option .value=${e.id ?? ""} ?selected=${e.id === t}>
          ${e.name}
        </option>`)}
    </select>
    ${r ? k`<span class="hint">${r}</span>` : j}
  </label>`;
}
function We(e, t) {
	if (!e.config) return j;
	let { name: n, source: r } = Ue(e.config, t), i = e.strings;
	return r === "none" ? k`<p class="hint">${H(i, "profiles.inherited_none")}</p>` : k`<p class="hint">
    ${H(i, "profiles.effective", { profile: n })} —
    ${H(i, `profiles.inherited_from_${r}`)}
  </p>`;
}
//#endregion
//#region src/panel/pages/areas.ts
var Ge = {
	name: "",
	ha_state_when_armed: "armed_away",
	default_entry_delay: 30,
	default_exit_delay: 30,
	response_profile_id: null,
	require_code_to_arm: null,
	require_code_to_disarm: null
}, Ke = class extends R {
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
		this._draft = e ? { ...e } : { ...Ge }, this._problems = [];
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
		if (!e?.config) return j;
		let t = e.strings, n = new Map(e.status.areas.map((e) => [e.id, e.state])), r = (t) => e.config.zones.filter((e) => e.area_id === t).length;
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(t, "areas.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${H(t, "areas.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${H(t, "field.name")}</th>
                <th>${H(t, "overview.status")}</th>
                <th>${H(t, "areas.zones")}</th>
                <th>${H(t, "field.default_entry_delay")}</th>
                <th>${H(t, "field.default_exit_delay")}</th>
                <th>${H(t, "field.ha_state_when_armed")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.areas.map((e) => {
			let i = n.get(e.id ?? "") ?? "disarmed";
			return k`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td><span class="state ${i}">${H(t, `state.${i}`)}</span></td>
                  <td>${r(e.id)}</td>
                  <td>${H(t, "common.seconds", { n: e.default_entry_delay })}</td>
                  <td>${H(t, "common.seconds", { n: e.default_exit_delay })}</td>
                  <td class="mono">${e.ha_state_when_armed}</td>
                </tr>`;
		})}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : j}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx.meta, [r, i] = n?.bounds.exit_delay ?? [0, 300], a = n?.bounds.entry_delay?.[1] ?? 300;
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : H(e, "areas.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${H(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.ha_state_when_armed")}</span>
              <select
                @change=${(e) => this._set("ha_state_when_armed", e.target.value)}
              >
                ${(n?.ha_states ?? []).map((n) => k`<option .value=${n} ?selected=${n === t.ha_state_when_armed}>
                      ${H(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${H(e, "areas.reports_as_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.default_entry_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${a}
                .value=${String(t.default_entry_delay)}
                @input=${(e) => this._set("default_entry_delay", Number(e.target.value))}
              />
              <span class="hint">${H(e, "areas.entry_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.default_exit_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.default_exit_delay)}
                @input=${(e) => this._set("default_exit_delay", Number(e.target.value))}
              />
              <span class="hint">${H(e, "areas.exit_hint")}</span>
            </label>
            ${q(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
            ${He(e, t, (e, t) => this._set(e, t), this.ctx.status.security.enforced)}
          </div>
          ${We(this.ctx, t.id ?? null)}
          ${this._problems.length ? k`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
                </ul>
              </div>` : j}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${H(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${H(e, "common.cancel")}
            </button>
            ${t.id ? k`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${H(e, "common.delete")}
                </button>` : j}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [U, W];
	}
};
customElements.get("foyer-page-areas") || customElements.define("foyer-page-areas", Ke);
//#endregion
//#region src/panel/pages/zones.ts
var qe = /* @__PURE__ */ new Set(["event", "tag"]), Je = /* @__PURE__ */ new Set(["unavailable", "unknown"]);
function Ye(e) {
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
function Xe(e) {
	return e.channel === "intrusion" ? e : {
		...e,
		chime: !1,
		cross_zone_id: null,
		trigger_count: 1,
		silent: !1
	};
}
var Ze = (e, t) => JSON.stringify(e) === JSON.stringify(t), Qe = class extends R {
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
		this._draft = e ? structuredClone(e) : Ye(t), this._saved = e, this._proposal = void 0, this._confirmed = !1, this._problems = [], e && this._propose(e.entity_id, !1);
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
		}), n.channel !== "key" && (n.key = null), n.arm_policy !== "arm_after_closing" && (n.arm_hold_timeout = null), n.entry_mode !== "follower" && (n.follows = []), n.always_on && (n.chime = !1), this._draft = Xe(n);
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
		return !this._saved || !Ze(this._saved.trigger, this._draft?.trigger);
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
		if (!e?.config) return j;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.status.zones.map((e) => [e.id, e]));
		return e.config.areas.length ? k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(t, "zones.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${H(t, "zones.add")}</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${H(t, "field.name")}</th>
                <th>${H(t, "field.entity_id")}</th>
                <th>${H(t, "field.area_id")}</th>
                <th>${H(t, "field.type")}</th>
                <th>${H(t, "field.arm_policy")}</th>
                <th>${H(t, "overview.status")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.zones.map((e) => k`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td class="mono">${e.entity_id}</td>
                  <td>${n.get(e.area_id) ?? ""}</td>
                  <td><span class="tag">${H(t, `zone_type.${e.type}`)}</span></td>
                  <td>${H(t, `arm_policy.${e.arm_policy}`)}</td>
                  <td>${this._health(t, r.get(e.id ?? ""))}</td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : j}
    ` : k`<div class="card"><div class="empty">${H(t, "zones.no_areas")}</div></div>`;
	}
	_health(e, t) {
		if (!t) return j;
		if (!t.enabled) return k`<span class="state disabled">${H(e, "zone_status.disabled")}</span>`;
		if (t.fault) return k`<span class="state fault">${H(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) return k`<span class="state bypassed">${H(e, `bypass.${t.bypassed}`)}</span>`;
		let n = t.open ? "open" : "closed";
		return k`<span class="state ${n}">${H(e, `zone_status.${n}`)}</span>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx;
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : H(e, "zones.new")}</h2>
        </div>
        <div class="card-bd">
          ${t.id ? j : this._renderEntityPicker(e, t)}
          ${t.entity_id ? k`
                ${this._renderTrigger(e, t)} ${this._renderProperties(e, t)}
                ${t.channel === "intrusion" && t.entry_mode === "follower" ? this._renderFollows(e, t) : j}
                ${t.channel === "intrusion" ? this._renderVerification(e, t) : j}
                ${t.channel === "key" ? this._renderKey(e, t) : j}
              ` : j}
          ${this._problems.length ? k`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
                </ul>
              </div>` : j}
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !t.entity_id || this._triggerChanged() && !this._confirmed}
              @click=${this._save}
            >
              ${H(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${H(e, "common.cancel")}
            </button>
            ${t.id ? k`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${H(e, "common.delete")}
                </button>` : j}
          </div>
          ${this._triggerChanged() && !this._confirmed && t.entity_id ? k`<div class="hint">${H(e, "zones.confirm_first")}</div>` : j}
          ${n.status.areas.some((e) => e.id === t.area_id && e.state !== "disarmed") ? k`<div class="notice">${H(e, "zones.area_armed")}</div>` : j}
        </div>
      </div>
    `;
	}
	_renderEntityPicker(e, t) {
		let n = this.ctx, r = new Set(n.meta?.zone_domains ?? []), i = new Set(n.config?.zones.map((e) => e.entity_id)), a = this._filter.toLowerCase(), o = Object.values(n.hass.states).filter((e) => r.has(e.entity_id.split(".")[0])).filter((e) => {
			let t = String(e.attributes.friendly_name ?? "");
			return !a || e.entity_id.toLowerCase().includes(a) || t.toLowerCase().includes(a);
		}).sort((e, t) => e.entity_id.localeCompare(t.entity_id)).slice(0, 200);
		return k`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${H(e, "zones.search")}</span>
          <input
            .value=${this._filter}
            @input=${(e) => this._filter = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${H(e, "field.entity_id")}</span>
          <select
            @change=${(e) => this._propose(e.target.value, !0)}
          >
            <option value="" ?selected=${!t.entity_id}>${H(e, "zones.pick_entity")}</option>
            ${o.map((n) => k`<option
                .value=${n.entity_id}
                ?selected=${n.entity_id === t.entity_id}
              >
                ${H(e, i.has(n.entity_id) ? "zones.entity_used" : "zones.entity", {
			name: String(n.attributes.friendly_name ?? n.entity_id),
			entity: n.entity_id
		})}
              </option>`)}
          </select>
          <span class="hint">${H(e, "zones.entity_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderTrigger(e, t) {
		let n = this.ctx.hass.states[t.entity_id], r = n?.state ?? "unavailable", i = t.entity_id.split(".")[0], a = t.trigger;
		return k`
      <fieldset>
        <legend>${H(e, "zones.trigger_title")}</legend>
        <p class="hint">
          ${H(e, "zones.trigger_intro", {
			entity: String(n?.attributes.friendly_name ?? t.entity_id),
			state: r
		})}
          ${this._proposal?.device_class ? H(e, "zones.device_class", { device_class: this._proposal.device_class }) : j}
        </p>
        ${qe.has(i) ? this._renderEventTrigger(e, i, a) : k`
              <label class="field">
                <span class="lbl">${H(e, "zones.trigger_kind")}</span>
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
                    ${H(e, "zones.kind_state")}
                  </option>
                  <option value="numeric" ?selected=${a.kind === "numeric"}>
                    ${H(e, "zones.kind_numeric")}
                  </option>
                </select>
              </label>
              ${a.kind === "numeric" ? this._renderNumericTrigger(e, a) : a.kind === "state" ? this._renderStateTrigger(e, a.states, r) : j}
            `}
        <label class="check confirm">
          <input
            type="checkbox"
            .checked=${this._confirmed || !this._triggerChanged()}
            ?disabled=${!this._triggerChanged()}
            @change=${(e) => this._confirmed = e.target.checked}
          />
          <span>
            ${H(e, "zones.confirm")}
            <span class="hint">${H(e, "zones.confirm_hint")}</span>
          </span>
        </label>
      </fieldset>
    `;
	}
	_renderStateTrigger(e, t, n) {
		let r = /* @__PURE__ */ new Set([...this._proposal?.options ?? [], ...t]);
		Je.has(n) || r.add(n);
		let i = (e, n) => {
			let r = n ? [...t, e] : t.filter((t) => t !== e);
			this._set("trigger", {
				kind: "state",
				states: [...new Set(r)].sort()
			});
		};
		return k`
      <div class="states">
        ${[...r].map((r) => k`<label class="check">
            <input
              type="checkbox"
              .checked=${t.includes(r)}
              @change=${(e) => i(r, e.target.checked)}
            />
            <span class="mono">${r}</span>
            ${r === n ? k`<span class="tag">${H(e, "zones.now")}</span>` : j}
          </label>`)}
      </div>
      <div class="row">
        <label class="field">
          <span class="lbl">${H(e, "zones.other_state")}</span>
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
          ${H(e, "zones.add_state")}
        </button>
      </div>
      <div class="hint">${H(e, "zones.state_hint")}</div>
    `;
	}
	_renderNumericTrigger(e, t) {
		let n = (e) => this._set("trigger", {
			...t,
			...e
		});
		return k`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${H(e, "zones.operator")}</span>
          <select
            @change=${(e) => n({ operator: e.target.value })}
          >
            ${[
			"gt",
			"lt",
			"eq"
		].map((n) => k`<option .value=${n} ?selected=${n === t.operator}>
                  ${H(e, `operator.${n}`)}
                </option>`)}
          </select>
        </label>
        <label class="field">
          <span class="lbl">${H(e, "zones.threshold")}</span>
          <input
            type="number"
            step="any"
            .value=${String(t.value)}
            @input=${(e) => n({ value: Number(e.target.value) })}
          />
        </label>
        <label class="field">
          <span class="lbl">${H(e, "zones.hysteresis")}</span>
          <input
            type="number"
            step="any"
            min="0"
            ?disabled=${t.operator === "eq"}
            .value=${String(t.hysteresis)}
            @input=${(e) => n({ hysteresis: Number(e.target.value) })}
          />
          <span class="hint">${H(e, "zones.hysteresis_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${H(e, "zones.attribute")}</span>
          <input
            .value=${t.attribute ?? ""}
            @input=${(e) => n({ attribute: e.target.value.trim() || null })}
          />
          <span class="hint">${H(e, "zones.attribute_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderEventTrigger(e, t, n) {
		if (t === "tag") return k`<p class="hint">${H(e, "zones.tag_hint")}</p>`;
		let r = n.kind === "event" ? n.event_type : null;
		return k`
      <label class="field">
        <span class="lbl">${H(e, "zones.event_type")}</span>
        <select
          @change=${(e) => this._set("trigger", {
			kind: "event",
			event_type: e.target.value || null
		})}
        >
          <option value="" ?selected=${!r}>${H(e, "zones.pick_event")}</option>
          ${(this._proposal?.options ?? []).map((e) => k`<option .value=${e} ?selected=${e === r}>${e}</option>`)}
        </select>
        <span class="hint">${H(e, "zones.event_hint")}</span>
      </label>
    `;
	}
	_renderProperties(e, t) {
		let n = this.ctx, r = n.meta, i = n.config?.areas.find((e) => e.id === t.area_id), a = t.channel === "intrusion", o = (n, r) => k`
      <label class="check">
        <input
          type="checkbox"
          .checked=${!!t[n]}
          @change=${(e) => this._set(n, e.target.checked)}
        />
        <span>
          ${H(e, `field.${n}`)}
          ${r ? k`<span class="hint">${H(e, r)}</span>` : j}
        </span>
      </label>
    `;
		return k`
      <fieldset>
        <legend>${H(e, "zones.properties_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${H(e, "field.name")}</span>
            <input
              .value=${t.name}
              @input=${(e) => this._set("name", e.target.value)}
            />
          </label>
          <label class="field">
            <span class="lbl">${H(e, "field.type")}</span>
            <select @change=${(e) => this._applyType(e.target.value)}>
              ${(r?.zone_types ?? []).map((n) => k`<option
                  .value=${n.type}
                  ?selected=${n.type === t.type}
                  ?disabled=${!n.available}
                >
                  ${H(e, n.available ? `zone_type.${n.type}` : "zones.type_unavailable", { type: H(e, `zone_type.${n.type}`) })}
                </option>`)}
            </select>
            <span class="hint">${H(e, "zones.type_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${H(e, "field.area_id")}</span>
            <select
              @change=${(e) => this._set("area_id", e.target.value)}
            >
              ${(n.config?.areas ?? []).map((e) => k`<option .value=${e.id ?? ""} ?selected=${e.id === t.area_id}>
                    ${e.name}
                  </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${H(e, "field.channel")}</span>
            <select
              @change=${(e) => {
			let n = e.target.value;
			this._draft = Xe({
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
		].map((n) => k`<option .value=${n} ?selected=${n === t.channel}>
                    ${H(e, `channel.${n}`)}
                  </option>`)}
            </select>
          </label>
          ${a ? k`
                <label class="field">
                  <span class="lbl">${H(e, "field.entry_mode")}</span>
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
		].map((n) => k`<option .value=${n} ?selected=${n === t.entry_mode}>
                          ${H(e, `entry_mode.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${H(e, `entry_mode_hint.${t.entry_mode}`)}</span>
                </label>
                <label class="field">
                  <span class="lbl">${H(e, "field.entry_delay")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${r?.bounds.entry_delay?.[1] ?? 300}
                    placeholder=${H(e, "zones.inherit_seconds", { n: i?.default_entry_delay ?? 30 })}
                    .value=${t.entry_delay == null ? "" : String(t.entry_delay)}
                    @input=${(e) => this._set("entry_delay", K(e.target.value))}
                  />
                  <span class="hint">${H(e, "zones.entry_delay_hint")}</span>
                </label>
                <label class="field">
                  <span class="lbl">${H(e, "field.alarm_kind")}</span>
                  <select
                    @change=${(e) => this._set("alarm_kind", e.target.value)}
                  >
                    ${[
			"intrusion",
			"tamper",
			"panic"
		].map((n) => k`<option .value=${n} ?selected=${n === t.alarm_kind}>
                          ${H(e, `alarm_kind.${n}`)}
                        </option>`)}
                  </select>
                </label>
                <label class="field">
                  <span class="lbl">${H(e, "field.arm_policy")}</span>
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
		].map((n) => k`<option .value=${n} ?selected=${n === t.arm_policy}>
                          ${H(e, `arm_policy.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${H(e, `arm_policy_hint.${t.arm_policy}`)}</span>
                </label>
                ${t.arm_policy === "arm_after_closing" ? k`<label class="field">
                      <span class="lbl">${H(e, "field.arm_hold_timeout")}</span>
                      <input
                        type="number"
                        min=${r?.bounds.arm_hold_timeout?.[0] ?? 60}
                        max=${r?.bounds.arm_hold_timeout?.[1] ?? 1800}
                        placeholder=${H(e, "zones.inherit_seconds", { n: n.config?.settings.arm_hold_timeout ?? 300 })}
                        .value=${t.arm_hold_timeout == null ? "" : String(t.arm_hold_timeout)}
                        @input=${(e) => this._set("arm_hold_timeout", K(e.target.value))}
                      />
                      <span class="hint">${H(e, "zones.hold_hint")}</span>
                    </label>` : j}
              ` : j}
          <label class="field">
            <span class="lbl">${H(e, "field.supervision_timeout")}</span>
            <input
              type="number"
              min=${r?.bounds.supervision_timeout?.[0] ?? 60}
              placeholder=${H(e, "zones.off")}
              .value=${t.supervision_timeout == null ? "" : String(t.supervision_timeout)}
              @input=${(e) => this._set("supervision_timeout", K(e.target.value))}
            />
            <span class="hint">${H(e, "zones.supervision_hint")}</span>
          </label>
        </div>
        <div class="checks">
          ${a ? o("always_on", "zones.always_on_hint") : j}
          ${a ? o("bypassable", "zones.bypassable_hint") : j}
          ${a && !t.always_on ? o("chime", "zones.chime_hint") : j}
          ${a ? o("silent", "zones.silent_hint") : j}
          ${o("allow_arm_when_faulted", "zones.allow_faulted_hint")}
          ${o("enabled", "zones.enabled_hint")}
        </div>
        ${q(n, t.response_profile_id, (e) => this._set("response_profile_id", e), H(e, "profiles.zone_hint"))}
        ${t.channel === "technical" ? k`<p class="hint">${H(e, "zones.technical_hint")}</p>
              <div class="notice fire" role="note">${H(e, "zones.fire_statement")}</div>` : j}
      </fieldset>
    `;
	}
	_renderVerification(e, t) {
		let n = this.ctx, r = n.meta, [i, a] = r?.bounds.window ?? [1, 3600], o = n.config?.groups.find((e) => e.members.includes(t.id ?? "")), s = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.members.forEach((e) => s.add(e));
		for (let e of n.config?.zones ?? []) e.id && e.cross_zone_id && e.id !== t.id && e.cross_zone_id !== t.id && (s.add(e.id), s.add(e.cross_zone_id));
		let c = (n.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && (!s.has(e.id ?? "") || e.id === t.cross_zone_id)), l = new Map(n.config?.areas.map((e) => [e.id, e.name])), u = (e) => (t) => {
			let n = K(t.target.value);
			this._set(e, n ?? (e === "trigger_count" ? 1 : 60));
		};
		return k`
      <fieldset>
        <legend>${H(e, "zones.verification_title")}</legend>
        ${o ? k`<p class="notice">${H(e, "zones.in_group", { group: o.name })}</p>` : k`<div class="grid-form">
              <label class="field">
                <span class="lbl">${H(e, "field.cross_zone_id")}</span>
                <select
                  @change=${(e) => this._set("cross_zone_id", e.target.value || null)}
                >
                  <option value="" ?selected=${!t.cross_zone_id}>
                    ${H(e, "zones.no_cross_zone")}
                  </option>
                  ${c.map((n) => k`<option .value=${n.id ?? ""} ?selected=${n.id === t.cross_zone_id}>
                      ${H(e, "zones.entity", {
			name: n.name,
			entity: l.get(n.area_id) ?? n.area_id
		})}
                    </option>`)}
                </select>
                <span class="hint">${H(e, "zones.cross_zone_hint")}</span>
              </label>
              ${t.cross_zone_id ? k`<label class="field">
                    <span class="lbl">${H(e, "field.cross_zone_window")}</span>
                    <input
                      type="number"
                      min=${i}
                      max=${a}
                      .value=${String(t.cross_zone_window)}
                      @input=${u("cross_zone_window")}
                    />
                    <span class="hint">${H(e, "groups.window_hint")}</span>
                  </label>` : j}
            </div>`}
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${H(e, "field.trigger_count")}</span>
            <input
              type="number"
              min="1"
              max=${r?.bounds.trigger_count?.[1] ?? 10}
              .value=${String(t.trigger_count)}
              @input=${u("trigger_count")}
            />
            <span class="hint">${H(e, "zones.trigger_count_hint")}</span>
          </label>
          ${t.trigger_count > 1 ? k`<label class="field">
                <span class="lbl">${H(e, "field.trigger_window")}</span>
                <input
                  type="number"
                  min=${i}
                  max=${a}
                  .value=${String(t.trigger_window)}
                  @input=${u("trigger_window")}
                />
                <span class="hint">${H(e, "groups.window_hint")}</span>
              </label>` : j}
        </div>
      </fieldset>
    `;
	}
	_renderFollows(e, t) {
		let n = new Map(this.ctx?.config?.areas.map((e) => [e.id, e.name])), r = (this.ctx?.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && e.entry_mode === "delayed"), i = (e, n) => this._set("follows", n ? [.../* @__PURE__ */ new Set([...t.follows, e])] : t.follows.filter((t) => t !== e));
		return k`
      <fieldset>
        <legend>${H(e, "field.follows")}</legend>
        ${r.length ? r.map((r) => k`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.follows.includes(r.id ?? "")}
                  @change=${(e) => i(r.id ?? "", e.target.checked)}
                />
                <span>
                  ${H(e, "zones.entity", {
			name: r.name,
			entity: n.get(r.area_id) ?? r.area_id
		})}
                </span>
              </label>`) : k`<p class="hint">${H(e, "zones.no_delayed_zones")}</p>`}
        <p class="hint">${H(e, "zones.follows_hint")}</p>
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
		return k`
      <fieldset>
        <legend>${H(e, "zones.key_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${H(e, "field.on_activate")}</span>
            <select
              @change=${(e) => r({ on_activate: e.target.value })}
            >
              ${[
			"arm",
			"disarm",
			"toggle"
		].map((t) => k`<option .value=${t} ?selected=${t === n.on_activate}>
                    ${H(e, `key_command.${t}`)}
                  </option>`)}
            </select>
          </label>
          ${n.on_activate === "disarm" ? j : k`<label class="field">
                <span class="lbl">${H(e, "field.scenario_id")}</span>
                <select
                  @change=${(e) => r({ scenario_id: e.target.value || null })}
                >
                  <option value="" ?selected=${!n.scenario_id}>
                    ${H(e, "zones.pick_scenario")}
                  </option>
                  ${i.map((e) => k`<option .value=${e.id ?? ""} ?selected=${e.id === n.scenario_id}>
                        ${e.name}
                      </option>`)}
                </select>
              </label>`}
          <label class="field">
            <span class="lbl">${H(e, "field.on_deactivate")}</span>
            <select
              @change=${(e) => r({ on_deactivate: e.target.value })}
            >
              ${["none", "disarm"].map((t) => k`<option .value=${t} ?selected=${t === n.on_deactivate}>
                    ${H(e, `key_release.${t}`)}
                  </option>`)}
            </select>
          </label>
        </div>
        <p class="hint">${H(e, "zones.key_hint")}</p>
      </fieldset>
    `;
	}
	static {
		this.styles = [
			U,
			W,
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
customElements.get("foyer-page-zones") || customElements.define("foyer-page-zones", Qe);
//#endregion
//#region src/panel/pages/scenarios.ts
var $e = {
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
}, et = class extends R {
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
			...$e,
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
		if (!e?.config) return j;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = e.config.scenarios.map((e) => e.ha_master_state);
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(t, "scenarios.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${H(t, "scenarios.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${H(t, "field.name")}</th>
                <th>${H(t, "field.areas")}</th>
                <th>${H(t, "field.ha_master_state")}</th>
                <th>${H(t, "field.exit_delay_override")}</th>
                <th>${H(t, "field.siren_duration_override")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.scenarios.map((i) => k`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === i.id ? "true" : "false"}
                  @click=${() => this._edit(i)}
                >
                  <td>
                    <strong>${i.name}</strong>
                    ${i.id === e.status.active_scenario_id ? k`<span class="state armed">${H(t, "scenarios.active")}</span>` : j}
                  </td>
                  <td>
                    ${i.areas.map((e) => k`<span class="tag">${n.get(e) ?? e}</span>`)}
                  </td>
                  <td>
                    <span class="mono">${i.ha_master_state}</span>
                    ${r.filter((e) => e === i.ha_master_state).length > 1 ? k`<div class="hint">${H(t, "scenarios.shared_mode")}</div>` : j}
                  </td>
                  <td>
                    ${i.exit_delay_override == null ? H(t, "scenarios.area_default") : H(t, "common.seconds", { n: i.exit_delay_override })}
                  </td>
                  <td>
                    ${i.siren_duration_override == null ? H(t, "scenarios.global_default") : H(t, "common.seconds", { n: i.siren_duration_override })}
                  </td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : j}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.meta, i = (e, n) => this._set("areas", n ? [...t.areas, e] : t.areas.filter((t) => t !== e));
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : H(e, "scenarios.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${H(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.ha_master_state")}</span>
              <select
                @change=${(e) => this._set("ha_master_state", e.target.value)}
              >
                ${(r?.ha_states ?? []).map((n) => k`<option .value=${n} ?selected=${n === t.ha_master_state}>
                      ${H(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${H(e, "scenarios.mode_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.exit_delay_override")}</span>
              <input
                type="number"
                min="0"
                max=${r?.bounds.exit_delay?.[1] ?? 300}
                placeholder=${H(e, "scenarios.area_default")}
                .value=${t.exit_delay_override == null ? "" : String(t.exit_delay_override)}
                @input=${(e) => this._set("exit_delay_override", K(e.target.value))}
              />
              <span class="hint">${H(e, "scenarios.exit_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.siren_duration_override")}</span>
              <input
                type="number"
                min="1"
                max=${r?.bounds.siren_duration?.[1] ?? 900}
                placeholder=${H(e, "scenarios.global_seconds", { n: n.config?.settings.siren_duration ?? 180 })}
                .value=${t.siren_duration_override == null ? "" : String(t.siren_duration_override)}
                @input=${(e) => this._set("siren_duration_override", K(e.target.value))}
              />
              <span class="hint">${H(e, "scenarios.siren_hint")}</span>
            </label>
            ${q(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
          </div>
          <fieldset>
            <legend>${H(e, "field.areas")}</legend>
            ${(n.config?.areas ?? []).map((e) => k`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.areas.includes(e.id ?? "")}
                  @change=${(t) => i(e.id ?? "", t.target.checked)}
                />
                <span>${e.name}</span>
              </label>`)}
            <p class="hint">${H(e, "scenarios.areas_hint")}</p>
          </fieldset>
          ${this._problems.length ? k`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
                </ul>
              </div>` : j}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${H(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${H(e, "common.cancel")}
            </button>
            ${t.id ? k`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${H(e, "common.delete")}
                </button>` : j}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			U,
			W,
			o`
      td .state {
        margin-left: 8px;
      }
    `
		];
	}
};
customElements.get("foyer-page-scenarios") || customElements.define("foyer-page-scenarios", et);
//#endregion
//#region src/panel/ha-targets.ts
function tt(e, t) {
	let n = e.states[t];
	return String(n?.attributes?.friendly_name ?? t);
}
function J(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) t.has(n.id) || t.set(n.id, n);
	return [...t.values()].sort((e, t) => e.id.localeCompare(t.id));
}
function Y(e, t) {
	return J(Object.values(e.states).filter((e) => t.includes(e.entity_id.split(".")[0])).map((t) => ({
		id: t.entity_id,
		name: tt(e, t.entity_id)
	})));
}
function X(e) {
	let t = Object.keys(e.services?.notify ?? {}).filter((e) => e !== "send_message").map((e) => ({
		id: `notify.${e}`,
		name: `notify.${e}`
	}));
	return J([...Y(e, ["notify"]), ...t]);
}
function nt(e, t) {
	return J([...Y(e, t.filter((e) => e !== "notify")), ...t.includes("notify") ? X(e) : []]);
}
function rt(e) {
	return Object.keys(e.services ?? {}).sort();
}
function it(e, t) {
	return Object.keys(e.services?.[t] ?? {}).sort();
}
//#endregion
//#region src/panel/pages/profiles.ts
var at = {
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
}, ot = [
	"siren",
	"light",
	"switch"
], st = [
	"camera",
	"scene",
	"tts"
];
function ct(e) {
	let t = {};
	return e === "switch" && (t.state = "on"), e === "camera" && (t.mode = "snapshot"), e === "delay" && (t.seconds = 30), (e === "notify" || e === "tts") && (t.message = "{{ zone }}"), {
		kind: e,
		moments: [],
		name: "",
		params: t,
		conditions: [],
		condition_mode: "all",
		enabled: !0
	};
}
var lt = class extends R {
	constructor(...e) {
		super(...e), this._open = -1, this._filters = {}, this._problems = [], this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_open: { state: !0 },
			_filters: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 }
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
			actions: [...this._draft.actions, ct(e)]
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
		if (!e?.config) return j;
		let t = e.strings, n = e.config.profiles ?? [];
		return k`
      <p class="page-intro">${H(t, "profiles.intro")}</p>
      <div class="card">
        <div class="card-hd">
          <h2>${H(t, "profiles.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${H(t, "profiles.add")}</button>
        </div>
        ${n.length ? k`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${H(t, "field.name")}</th>
                      <th>${H(t, "field.actions")}</th>
                      <th>${H(t, "field.severity")}</th>
                      <th>${H(t, "profiles.used_by")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${n.map((e) => k`<tr
                          class="clickable"
                          aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                          @click=${() => this._edit(e)}
                        >
                          <td><strong>${e.name}</strong></td>
                          <td>
                            ${e.actions.length ? e.actions.map((e) => k`<span class="tag"
                                        >${H(t, `action_kind.${e.kind}`)}</span
                                      > `) : k`<span class="muted">${H(t, "profiles.no_actions")}</span>`}
                          </td>
                          <td>${e.severity}</td>
                          <td class="muted">${this._usedBy(t, e)}</td>
                        </tr>`)}
                  </tbody>
                </table>
              </div>` : k`<div class="empty">${H(t, "profiles.none")}</div>`}
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : j}
    `;
	}
	_usedBy(e, t) {
		let n = this.ctx.config, r = [];
		n.settings.default_profile_id === t.id && r.push(H(e, "profiles.used_default")), n.settings.technical_profile_id === t.id && r.push(H(e, "profiles.used_technical"));
		for (let e of [
			n.areas,
			n.zones,
			n.scenarios,
			n.groups
		]) for (let n of e) n.response_profile_id === t.id && r.push(n.name);
		return r.length ? r.join(", ") : H(e, "profiles.unused");
	}
	_renderEditor(e, t) {
		let n = this.ctx?.meta?.bounds.severity ?? [1, 10];
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : H(e, "profiles.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${H(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.severity")}</span>
              <input
                type="number"
                min=${n[0]}
                max=${n[1]}
                .value=${String(t.severity)}
                @input=${(e) => this._set("severity", K(e.target.value) ?? 1)}
              />
              <span class="hint">${H(e, "profiles.severity_hint")}</span>
            </label>
          </div>

          <div class="actions-list">
            ${t.actions.map((t, n) => this._renderAction(e, t, n))}
          </div>
          ${t.actions.length ? j : k`<p class="hint">${H(e, "profiles.no_actions")}</p>`}

          <div class="add-action">
            <label class="field">
              <span class="lbl">${H(e, "profiles.add_action")}</span>
              <select
                .value=${""}
                @change=${(e) => {
			let t = e.target;
			t.value && this._addAction(t.value), t.value = "";
		}}
              >
                <option value=""></option>
                ${(this.ctx?.meta?.action_kinds ?? []).map((t) => k`<option .value=${t}>${H(e, `action_kind.${t}`)}</option>`)}
              </select>
            </label>
          </div>
          <p class="hint">${H(e, "profiles.escalation_later")}</p>

          ${this._problems.length ? k`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
                  </ul>
                </div>` : j}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${H(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${H(e, "common.cancel")}
            </button>
            ${t.id ? k`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                    ${H(e, "common.delete")}
                  </button>` : j}
          </div>
        </div>
      </div>
    `;
	}
	_renderAction(e, t, n) {
		let r = this._open === n;
		return k`
      <div class="action" ?data-open=${r}>
        <button class="action-hd" @click=${() => this._open = r ? -1 : n}>
          <span class="tag">${H(e, `action_kind.${t.kind}`)}</span>
          <span class="summary">${this._summary(e, t)}</span>
          <span class="moments">${this._momentSummary(e, t)}</span>
          ${t.conditions.length ? k`<span class="cond">${t.conditions.length}</span>` : j}
        </button>
        ${r ? k`<div class="action-bd">
                ${this._renderParams(e, t, n)} ${this._renderMoments(e, t, n)}
                ${this._renderConditions(e, t, n)}
                <div class="actions">
                  <button class="btn" @click=${() => this._moveAction(n, -1)}>&uarr;</button>
                  <button class="btn" @click=${() => this._moveAction(n, 1)}>&darr;</button>
                  <button class="btn danger" @click=${() => this._removeAction(n)}>
                    ${H(e, "profiles.delete_action")}
                  </button>
                </div>
              </div>` : j}
      </div>
    `;
	}
	_momentSummary(e, t) {
		let n = t.moments.map((t) => H(e, `moment.${t}`));
		return n.length ? n.length <= 3 ? n.join(", ") : H(e, "profiles.moments_more", {
			moments: n.slice(0, 2).join(", "),
			count: n.length - 2
		}) : H(e, "profiles.no_moments");
	}
	_summary(e, t) {
		let n = t.params;
		if (t.kind === "delay") return `${n.seconds ?? 0} s`;
		if (t.kind === "call_service") return `${n.domain ?? ""}.${n.service ?? ""}`;
		if (t.kind === "notify") return String(n.service ?? "");
		if (t.kind === "persistent_notification") return String(n.message ?? H(e, "profiles.inherit"));
		let r = n.entity_ids ?? n.entity_id ?? "";
		return Array.isArray(r) ? r.join(", ") : String(r);
	}
	_entities(e) {
		return Y(this.ctx.hass, e);
	}
	_suggested(e, t, n, r, i, a) {
		let o = `foyer-${r}-${n}`;
		return k`<label class="field">
      <span class="lbl">${H(e, `field.${r}`)}</span>
      <input
        list=${o}
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      <datalist id=${o}>
        ${i.map((e) => k`<option .value=${e.id}>
            ${e.name === e.id ? e.id : `${e.name} · ${e.id}`}
          </option>`)}
      </datalist>
      <span class="hint">${a ?? H(e, "profiles.pick_or_type")}</span>
    </label>`;
	}
	_text(e, t, n, r, i) {
		return k`<label class="field">
      <span class="lbl">${H(e, `field.${r}`)}</span>
      <input
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      ${i ? k`<span class="hint">${i}</span>` : j}
    </label>`;
	}
	_number(e, t, n, r, i) {
		return k`<label class="field">
      <span class="lbl">${H(e, `field.${r}`)}</span>
      <input
        type="number"
        .value=${t.params[r] == null ? "" : String(t.params[r])}
        @input=${(e) => this._setParam(n, r, K(e.target.value))}
      />
      ${i ? k`<span class="hint">${i}</span>` : j}
    </label>`;
	}
	_picker(e, t, n, r, i, a) {
		let o = this._entities(i), s = t.params[r], c = new Set(Array.isArray(s) ? s : s ? [String(s)] : []);
		for (let e of c) o.some((t) => t.id === e) || o.push({
			id: e,
			name: e
		});
		if (!a) return k`<label class="field">
        <span class="lbl">${H(e, `field.${r}`)}</span>
        <select
          @change=${(e) => this._setParam(n, r, e.target.value || null)}
        >
          <option value=""></option>
          ${o.map((e) => k`<option .value=${e.id} ?selected=${c.has(e.id)}>${e.name}</option>`)}
        </select>
      </label>`;
		let l = `${n}:${r}`, u = (this._filters[l] ?? "").toLowerCase().split(/\s+/).filter(Boolean), d = o.filter((e) => {
			if (c.has(e.id)) return !0;
			let t = `${e.name} ${e.id}`.toLowerCase();
			return u.every((e) => t.includes(e));
		});
		return k`<fieldset class="entities wide">
      <legend>${H(e, `field.${r}`)}</legend>
      ${o.length > 8 ? k`<input
            class="filter"
            type="search"
            .value=${this._filters[l] ?? ""}
            placeholder=${H(e, "profiles.filter")}
            @input=${(e) => {
			this._filters = {
				...this._filters,
				[l]: e.target.value
			};
		}}
          />` : j}
      <div class="entity-list">
        ${d.map((t) => k`<label class="check">
            <input
              type="checkbox"
              .checked=${c.has(t.id)}
              @change=${(e) => {
			let i = e.target.checked, a = new Set(c);
			i ? a.add(t.id) : a.delete(t.id), this._setParam(n, r, [...a]);
		}}
            />
            <span>${H(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}</span>
          </label>`)}
        ${d.length ? j : k`<p class="hint">${H(e, "profiles.no_match")}</p>`}
      </div>
    </fieldset>`;
	}
	_renderParams(e, t, n) {
		let r = this.ctx?.meta?.action_domains[t.kind] ?? [], i = H(e, "profiles.message_hint", { variables: (this.ctx?.meta?.template_variables ?? []).map((e) => `{{ ${e} }}`).join(" ") }), a = [];
		switch (ot.includes(t.kind) && a.push(this._picker(e, t, n, "entity_ids", r, !0)), st.includes(t.kind) && a.push(this._picker(e, t, n, "entity_id", r, !1)), t.kind) {
			case "notify":
				a.push(this._suggested(e, t, n, "service", X(this.ctx.hass), H(e, "profiles.notify_hint"))), a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i)), a.push(this._picker(e, t, n, "camera_entity_id", ["camera"], !1)), a.push(k`<span class="hint">${H(e, "profiles.attach_hint")}</span>`);
				break;
			case "persistent_notification":
				a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i));
				break;
			case "siren":
				a.push(this._number(e, t, n, "duration", H(e, "profiles.siren_duration_hint"))), a.push(this._renderTone(e, t, n));
				break;
			case "light":
				a.push(this._number(e, t, n, "brightness")), a.push(this._select(e, t, n, "flash", [
					"",
					"short",
					"long"
				], (e) => e || "—"));
				break;
			case "camera":
				a.push(this._select(e, t, n, "mode", ["snapshot", "record"], (t) => H(e, `camera_mode.${t}`))), a.push(this._number(e, t, n, "duration", H(e, "profiles.camera_hint")));
				break;
			case "switch":
				a.push(this._select(e, t, n, "state", ["on", "off"], (t) => H(e, `on_off.${t}`))), a.push(this._number(e, t, n, "revert_after", H(e, "profiles.revert_hint")));
				break;
			case "tts":
				a.push(this._picker(e, t, n, "media_player_entity_ids", ["media_player"], !0)), a.push(this._text(e, t, n, "message", i));
				break;
			case "call_service": {
				let r = String(t.params.domain ?? "");
				a.push(this._suggested(e, t, n, "domain", rt(this.ctx.hass).map((e) => ({
					id: e,
					name: e
				})))), a.push(this._suggested(e, t, n, "service", it(this.ctx.hass, r).map((e) => ({
					id: e,
					name: e
				})))), a.push(this._json(e, t, n));
				break;
			}
			case "delay": a.push(this._number(e, t, n, "seconds", H(e, "profiles.delay_hint")));
		}
		return k`<div class="grid-form">${a}</div>`;
	}
	_renderTone(e, t, n) {
		let r = t.params.entity_ids, i = Array.isArray(r) ? r : [], a = /* @__PURE__ */ new Set();
		for (let e of i) {
			let t = this.ctx.hass.states[e]?.attributes?.available_tones;
			Array.isArray(t) ? t.forEach((e) => a.add(String(e))) : t && typeof t == "object" && Object.keys(t).forEach((e) => a.add(e));
		}
		return a.size ? this._select(e, t, n, "tone", ["", ...[...a].sort()], (t) => t || H(e, "profiles.default_tone")) : i.length ? k`<label class="field">
            <span class="lbl">${H(e, "field.tone")}</span>
            <input disabled placeholder=${H(e, "profiles.no_tones")} />
            <span class="hint">${H(e, "profiles.no_tones")}</span>
          </label>` : j;
	}
	_select(e, t, n, r, i, a) {
		return k`<label class="field">
      <span class="lbl">${H(e, `field.${r}`)}</span>
      <select
        @change=${(e) => this._setParam(n, r, e.target.value || null)}
      >
        ${i.map((e) => k`<option .value=${e} ?selected=${t.params[r] === e}>
              ${a(e)}
            </option>`)}
      </select>
    </label>`;
	}
	_json(e, t, n) {
		return k`<label class="field wide">
      <span class="lbl">${H(e, "field.data")}</span>
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
      <span class="hint">${H(e, "profiles.call_service_hint")}</span>
    </label>`;
	}
	_renderMoments(e, t, n) {
		let r = new Set(this.ctx?.meta?.future_moments ?? []), i = new Set(this.ctx?.meta?.moments ?? []);
		return k`<div class="moments-grid">
      ${Object.entries(at).map(([a, o]) => k`<fieldset>
            <legend>${H(e, `moment_group.${a}`)}</legend>
            ${o.filter((e) => i.has(e)).map((i) => k`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${t.moments.includes(i)}
                      @change=${(e) => {
			let r = e.target.checked ? [...t.moments, i] : t.moments.filter((e) => e !== i);
			this._setAction(n, { moments: r });
		}}
                    />
                    <span>
                      ${H(e, `moment.${i}`)}
                      ${r.has(i) ? k`<span class="later">${H(e, "profiles.future_moment")}</span>` : j}
                    </span>
                  </label>`)}
          </fieldset>`)}
    </div>`;
	}
	_renderConditions(e, t, n) {
		let r = this.ctx?.meta?.max_conditions ?? 2, i = (e) => this._setAction(n, { conditions: e });
		return k`<fieldset class="conditions">
      <legend>${H(e, "field.conditions")}</legend>
      ${t.conditions.length ? t.conditions.map((r, i) => this._renderCondition(e, t, n, r, i)) : k`<p class="hint">${H(e, "condition.none")}</p>`}
      ${t.conditions.length < r ? k`<div class="actions">
              <button
                class="btn sm"
                @click=${() => i([...t.conditions, {
			kind: "time",
			after: "22:00",
			before: "07:00"
		}])}
              >
                ${H(e, "condition.time")}
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
                ${H(e, "condition.state")}
              </button>
            </div>` : j}
      ${t.conditions.length === 2 ? k`<label class="field">
              <span class="lbl">${H(e, "field.condition_mode")}</span>
              <select
                @change=${(e) => this._setAction(n, { condition_mode: e.target.value })}
              >
                ${["all", "any"].map((n) => k`<option .value=${n} ?selected=${t.condition_mode === n}>
                      ${H(e, `condition.${n}`)}
                    </option>`)}
              </select>
            </label>` : j}
      <p class="hint">${H(e, "condition.max")}</p>
    </fieldset>`;
	}
	_renderCondition(e, t, n, r, i) {
		let a = (e) => this._setAction(n, { conditions: t.conditions.map((t, n) => n === i ? {
			...t,
			...e
		} : t) });
		return k`<div class="condition">
      ${r.kind === "time" ? k`<label class="field">
                <span class="lbl">${H(e, "condition.after")}</span>
                <input
                  type="time"
                  .value=${r.after}
                  @input=${(e) => a({ after: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${H(e, "condition.before")}</span>
                <input
                  type="time"
                  .value=${r.before}
                  @input=${(e) => a({ before: e.target.value })}
                />
                <span class="hint">${H(e, "condition.midnight_hint")}</span>
              </label>` : k`<label class="field">
                <span class="lbl">${H(e, "field.entity_id")}</span>
                <input
                  .value=${r.entity_id}
                  @input=${(e) => a({ entity_id: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${H(e, "field.state")}</span>
                <select
                  @change=${(e) => a({ operator: e.target.value })}
                >
                  ${["is", "is_not"].map((t) => k`<option .value=${t} ?selected=${r.operator === t}>
                        ${H(e, `condition.${t}`)}
                      </option>`)}
                </select>
              </label>
              <label class="field">
                <span class="lbl">${H(e, "condition.state")}</span>
                <input
                  .value=${r.state}
                  @input=${(e) => a({ state: e.target.value })}
                />
              </label>`}
      <button class="btn sm danger" @click=${() => this._setAction(n, { conditions: t.conditions.filter((e, t) => t !== i) })}>${H(e, "common.delete")}</button>
    </div>`;
	}
	static {
		this.styles = [
			W,
			U,
			o`
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
customElements.get("foyer-page-profiles") || customElements.define("foyer-page-profiles", lt);
//#endregion
//#region src/panel/pages/groups.ts
var ut = class extends R {
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
		if (!e?.config) return j;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.config.zones.map((e) => [e.id, e.name])), i = this._rows(e.config.zones, e.config.groups ?? []);
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(t, "groups.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${H(t, "groups.add")}</button>
        </div>
        ${i.length ? k`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${H(t, "field.name")}</th>
                    <th>${H(t, "field.area_id")}</th>
                    <th>${H(t, "field.members")}</th>
                    <th>${H(t, "field.n")}</th>
                    <th>${H(t, "field.window_seconds")}</th>
                    <th>${H(t, "groups.members_below")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${i.map(({ group: e, derived: i }) => k`<tr
                      class=${i ? "" : "clickable"}
                      aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                      @click=${() => i ? void 0 : this._edit(e)}
                    >
                      <td>
                        <strong>${e.name}</strong>
                        ${i ? k`<span class="tag">${H(t, "groups.from_zone")}</span>` : j}
                      </td>
                      <td>${n.get(e.area_id) ?? ""}</td>
                      <td>
                        ${e.members.map((e) => k`<span class="tag">${r.get(e) ?? e}</span>`)}
                      </td>
                      <td>${H(t, "groups.threshold", {
			n: e.n,
			m: e.members.length
		})}</td>
                      <td>${H(t, "common.seconds", { n: e.window_seconds })}</td>
                      <td>
                        ${H(t, e.suppress_members ? "groups.suppressed" : "groups.not_suppressed")}
                      </td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : k`<div class="empty">${H(t, "groups.none")}</div>`}
        <div class="card-bd">
          <p class="hint">${H(t, "groups.from_zone_hint")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : j}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, [r, i] = n.meta?.bounds.window ?? [1, 3600], a = new Map(n.config?.areas.map((e) => [e.id, e.name])), o = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.id !== t.id && e.members.forEach((e) => o.add(e));
		for (let e of n.config?.zones ?? []) e.cross_zone_id && e.id && (o.add(e.id), o.add(e.cross_zone_id));
		let s = (n.config?.zones ?? []).filter((e) => e.channel === "intrusion" && e.id && (!o.has(e.id) || t.members.includes(e.id))), c = (e, n) => this._set("members", n ? [.../* @__PURE__ */ new Set([...t.members, e])] : t.members.filter((t) => t !== e));
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : H(e, "groups.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${H(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.area_id")}</span>
              <select
                @change=${(e) => this._set("area_id", e.target.value)}
              >
                ${(n.config?.areas ?? []).map((e) => k`<option .value=${e.id ?? ""} ?selected=${e.id === t.area_id}>
                      ${e.name}
                    </option>`)}
              </select>
              <span class="hint">${H(e, "groups.area_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.n")}</span>
              <input
                type="number"
                min="2"
                max=${Math.max(2, t.members.length)}
                .value=${String(t.n)}
                @input=${(e) => this._set("n", K(e.target.value) ?? 2)}
              />
              <span class="hint">
                ${H(e, "groups.threshold", {
			n: t.n,
			m: t.members.length
		})}
              </span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.window_seconds")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.window_seconds)}
                @input=${(e) => this._set("window_seconds", K(e.target.value) ?? 60)}
              />
              <span class="hint">${H(e, "groups.window_hint")}</span>
            </label>
            ${q(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e), H(e, "profiles.group_hint"))}
          </div>
          <fieldset>
            <legend>${H(e, "field.members")}</legend>
            ${s.length ? s.map((n) => k`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${t.members.includes(n.id ?? "")}
                      @change=${(e) => c(n.id ?? "", e.target.checked)}
                    />
                    <span>
                      ${H(e, "zones.entity", {
			name: n.name,
			entity: a.get(n.area_id) ?? n.area_id
		})}
                    </span>
                  </label>`) : k`<p class="hint">${H(e, "groups.no_zones")}</p>`}
            <p class="hint">${H(e, "groups.members_hint")}</p>
          </fieldset>
          <label class="check suppress">
            <input
              type="checkbox"
              .checked=${t.suppress_members}
              @change=${(e) => this._set("suppress_members", e.target.checked)}
            />
            <span>
              ${H(e, "field.suppress_members")}
              <span class="hint">${H(e, "groups.suppress_hint")}</span>
            </span>
          </label>
          ${this._problems.length ? k`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
                </ul>
              </div>` : j}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${H(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${H(e, "common.cancel")}
            </button>
            ${t.id ? k`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${H(e, "common.delete")}
                </button>` : j}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			U,
			W,
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
customElements.get("foyer-page-groups") || customElements.define("foyer-page-groups", ut);
//#endregion
//#region src/panel/pages/users.ts
var dt = {
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
function ft(e) {
	if (!e) return "";
	let t = new Date(e), n = (e) => String(e).padStart(2, "0");
	return `${t.getFullYear()}-${n(t.getMonth() + 1)}-${n(t.getDate())}T${n(t.getHours())}:${n(t.getMinutes())}`;
}
function pt(e) {
	if (!e) return null;
	let t = new Date(e);
	return Number.isNaN(t.getTime()) ? null : t.toISOString();
}
var mt = class extends R {
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
		this._draft = e ? { ...structuredClone(e) } : structuredClone(dt), this._problems = [];
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
		if (!e?.config) return j;
		let t = e.strings, n = e.config.users ?? [];
		return k`
      ${e.status.security.enforced ? j : k`<div class="banner warn">
            <strong>${H(t, "users.not_enforced")}</strong>
            <span>${H(t, "users.not_enforced_hint")}</span>
          </div>`}
      <div class="card">
        <div class="card-hd">
          <h2>${H(t, "users.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${H(t, "users.add")}
          </button>
        </div>
        ${n.length ? k`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${H(t, "field.name")}</th>
                    <th>${H(t, "users.code")}</th>
                    <th>${H(t, "field.permissions")}</th>
                    <th>${H(t, "users.scope")}</th>
                    <th>${H(t, "field.valid_until")}</th>
                    <th>${H(t, "users.duress")}</th>
                    <th>${H(t, "field.ha_user_id")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${n.map((e) => this._row(t, e))}
                </tbody>
              </table>
            </div>` : k`<div class="empty">${H(t, "users.none")}</div>`}
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : j}
      ${this._renderPolicy(t)}
    `;
	}
	_row(e, t) {
		let n = this.ctx, r = new Map((n.config?.areas ?? []).map((e) => [e.id, e.name])), i = t.allowed_area_ids === null ? H(e, "users.every_area") : t.allowed_area_ids.map((e) => r.get(e) ?? e).join(", ");
		return k`<tr
      class="clickable"
      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
      @click=${() => this._edit(t)}
    >
      <td>
        <strong>${t.name}</strong>
        ${t.enabled ? j : k`<span class="tag">${H(e, "users.disabled")}</span>`}
      </td>
      <td>
        ${t.has_code ? k`<span class="pill ok">${H(e, "users.code_set")}</span>` : k`<span class="pill warn">${H(e, "users.code_missing")}</span>`}
      </td>
      <td>${t.permissions.map((t) => k`<span class="tag">${H(e, `permission.${t}`)}</span>`)}</td>
      <td>${i}</td>
      <td>${t.valid_until ? new Date(t.valid_until).toLocaleString(n.hass.language) : "—"}</td>
      <td>${H(e, t.has_duress_code ? "common.yes" : "common.no")}</td>
      <td>${t.ha_user_id ? H(e, "users.linked") : "—"}</td>
    </tr>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.status.security.code_length, i = n.meta?.permissions ?? [], a = n.hass.user?.is_admin ? n.haUsers ?? [] : [];
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : H(e, "users.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${H(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "users.code")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${r}
                placeholder=${t.has_code ? H(e, "users.code_unchanged") : H(e, "users.code_digits", { n: r })}
                @input=${(e) => this._set("new_code", e.target.value)}
              />
              <span class="hint">${H(e, "users.code_hint", { n: r })}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "users.duress")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${r}
                placeholder=${t.has_duress_code ? H(e, "users.code_unchanged") : H(e, "users.code_optional")}
                @input=${(e) => this._set("new_duress_code", e.target.value)}
              />
              <span class="hint">${H(e, "users.duress_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.ha_user_id")}</span>
              <select
                @change=${(e) => this._set("ha_user_id", e.target.value || null)}
              >
                <option value="" ?selected=${!t.ha_user_id}>${H(e, "users.not_linked")}</option>
                ${a.map((e) => k`<option .value=${e.id} ?selected=${e.id === t.ha_user_id}>
                    ${e.name}
                  </option>`)}
              </select>
              <span class="hint">${H(e, "users.linked_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.valid_from")}</span>
              <input
                type="datetime-local"
                .value=${ft(t.valid_from)}
                @input=${(e) => this._set("valid_from", pt(e.target.value))}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.valid_until")}</span>
              <input
                type="datetime-local"
                .value=${ft(t.valid_until)}
                @input=${(e) => this._set("valid_until", pt(e.target.value))}
              />
              <span class="hint">${H(e, "users.validity_hint")}</span>
            </label>
          </div>

          <div class="hr"></div>
          <div class="lbl">${H(e, "field.permissions")}</div>
          <div class="chips">
            ${i.map((n) => k`<label class="chip">
                <input
                  type="checkbox"
                  .checked=${t.permissions.includes(n)}
                  @change=${(e) => this._togglePermission(n, e.target.checked)}
                />
                <span>${H(e, `permission.${n}`)}</span>
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
              ${H(e, "users.exempt")}
              <span class="hint">${H(e, "users.exempt_hint")}</span>
            </span>
          </label>
          <p class="note">${H(e, "users.exempt_note")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.enabled}
              @change=${(e) => this._set("enabled", e.target.checked)}
            />
            <span>
              ${H(e, "users.enabled")}
              <span class="hint">${H(e, "users.enabled_hint")}</span>
            </span>
          </label>

          ${this._problems.length ? k`<ul class="problems">
                ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
              </ul>` : j}
        </div>
        <div class="card-ft">
          <button class="btn" @click=${() => this._draft = void 0}>
            ${H(e, "common.cancel")}
          </button>
          ${t.id ? k`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                ${H(e, "common.delete")}
              </button>` : j}
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${H(e, "common.save")}
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
		return k`<div class="scope">
      <span class="lbl">${H(e, `field.${t}`)}</span>
      <label class="chip">
        <input
          type="checkbox"
          .checked=${i === null}
          @change=${(e) => this._set(t, e.target.checked ? null : [])}
        />
        <span>${H(e, "users.everything")}</span>
      </label>
      ${i === null ? j : k`<div class="chips">
            ${n.map((e) => k`<label class="chip">
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
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(e, "users.policy")}</h2>
        </div>
        <div class="card-bd">
          <p class="hint">${H(e, "users.policy_hint")}</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${H(e, "users.operation")}</th>
                  <th>${H(e, "users.needs_code")}</th>
                </tr>
              </thead>
              <tbody>
                ${r.map((t) => k`<tr>
                    <td>
                      ${H(e, `operation.${t}`)}
                      ${i.has(t) ? k`<span class="tag">${H(e, "users.later_phase")}</span>` : j}
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
              <span class="lbl">${H(e, "users.code_length")}</span>
              <input
                type="number"
                min=${l}
                max=${u}
                .value=${String(n.security.code_length)}
                @input=${(e) => f("code_length", K(e.target.value) ?? 6)}
              />
              <span class="hint">${H(e, "users.code_length_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "users.lockout_failures")}</span>
              <input
                type="number"
                min=${a}
                max=${o}
                .value=${String(n.security.lockout_failures)}
                @input=${(e) => f("lockout_failures", K(e.target.value) ?? 5)}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "users.lockout_window")}</span>
              <input
                type="number"
                min=${s}
                max=${c}
                .value=${String(n.security.lockout_window)}
                @input=${(e) => f("lockout_window", K(e.target.value) ?? 300)}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "users.lockout_duration")}</span>
              <input
                type="number"
                min=${s}
                max=${c}
                .value=${String(n.security.lockout_duration)}
                @input=${(e) => f("lockout_duration", K(e.target.value) ?? 300)}
              />
              <span class="hint">${H(e, "users.lockout_hint")}</span>
            </label>
          </div>
        </div>
        <div class="card-ft">
          <button
            class="btn primary"
            ?disabled=${this._busy || !this._policy}
            @click=${this._savePolicy}
          >
            ${H(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			W,
			U,
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
customElements.define("foyer-page-users", mt);
//#endregion
//#region src/panel/pages/log.ts
var Z = 50, ht = class extends R {
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
					limit: Z,
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
				Fe(t.filename, t.content, e === "csv" ? "text/csv" : "application/json"), t.truncated && (this._error = H(this.ctx.strings, "log.truncated", {
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
		if (!e) return j;
		let t = e.strings;
		return k`${this._renderFilters(t)} ${this._renderRows(t)}`;
	}
	_vocabulary(e, t, n) {
		if (n?.length) return n;
		let r = e[t];
		return r && typeof r == "object" ? Object.keys(r) : [];
	}
	_renderFilters(e) {
		let t = this.ctx, n = this._vocabulary(e, "category", t.meta?.log_categories), r = this._vocabulary(e, "severity", t.meta?.log_severities), i = this._vocabulary(e, "outcome", t.meta?.outcomes), a = this._filters.categories ?? [];
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "log.filters")}</h2></div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${H(e, "log.from")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.start ?? ""}
                @change=${(e) => this._filter({ start: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "log.to")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.end ?? ""}
                @change=${(e) => this._filter({ end: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "log.area")}</span>
              <select
                @change=${(e) => this._filter({ area_id: e.target.value || null })}
              >
                <option value="">${H(e, "log.all")}</option>
                ${t.status.areas.map((e) => k`<option .value=${e.id} ?selected=${e.id === this._filters.area_id}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "log.zone")}</span>
              <select
                @change=${(e) => this._filter({ zone_id: e.target.value || null })}
              >
                <option value="">${H(e, "log.all")}</option>
                ${t.status.zones.map((e) => k`<option .value=${e.id} ?selected=${e.id === this._filters.zone_id}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "log.severity")}</span>
              <select
                @change=${(e) => this._filter({ severity: e.target.value || null })}
              >
                <option value="">${H(e, "log.all")}</option>
                ${r.map((t) => k`<option .value=${t} ?selected=${t === this._filters.severity}>
                      ${H(e, `severity.${t}`)}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "log.outcome")}</span>
              <select
                @change=${(e) => this._filter({ outcome: e.target.value || null })}
              >
                <option value="">${H(e, "log.all")}</option>
                ${i.map((t) => k`<option .value=${t} ?selected=${t === this._filters.outcome}>
                      ${H(e, `outcome.${t}`)}
                    </option>`)}
              </select>
            </label>
          </div>
          <fieldset>
            <legend>${H(e, "log.categories")}</legend>
            <div class="chips">
              ${n.map((t) => k`
                  <button
                    class="chip"
                    aria-pressed=${a.includes(t) ? "true" : "false"}
                    @click=${() => this._filter({ categories: a.includes(t) ? a.filter((e) => e !== t) : [...a, t] })}
                  >
                    ${H(e, `category.${t}`)}
                  </button>
                `)}
            </div>
            <p class="hint">${H(e, "log.categories_hint")}</p>
          </fieldset>
          ${this._filters.incident_id ? k`<p class="hint">
                ${H(e, "log.incident_filter", { id: this._filters.incident_id })}
                <button class="btn small" @click=${() => this._filter({ incident_id: null })}>
                  ${H(e, "log.clear_filter")}
                </button>
              </p>` : j}
        </div>
      </div>
    `;
	}
	_renderRows(e) {
		let t = this.ctx, n = this._rows.length;
		return k`
      <div class="card">
        <div class="card-hd">
          <h2>${H(e, "log.events")}</h2>
          <span class="hint"
            >${H(e, "log.count", {
			shown: n ? `${this._offset + 1}–${this._offset + n}` : "0",
			total: this._total
		})}</span
          >
          <button class="btn" ?disabled=${this._busy} @click=${() => void this._load()}>
            ${H(e, "log.refresh")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("csv")}>
            ${H(e, "log.export_csv")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("json")}>
            ${H(e, "log.export_json")}
          </button>
          ${t.isAdmin ? k`<button class="btn danger" ?disabled=${this._busy} @click=${() => this._confirmClear = !0}>
                ${H(e, "log.clear")}
              </button>` : j}
        </div>
        <div class="card-bd">
          ${this._error ? k`<div class="problems" role="alert">${this._error}</div>` : j}
          ${this._confirmClear ? k`<div class="problems" role="alert">
                <p>${H(e, "log.clear_confirm")}</p>
                <div class="actions">
                  <button class="btn danger" @click=${this._clear}>
                    ${H(e, "log.clear_yes")}
                  </button>
                  <button class="btn" @click=${() => this._confirmClear = !1}>
                    ${H(e, "common.cancel")}
                  </button>
                </div>
              </div>` : j}
          ${n === 0 ? k`<p class="hint">${H(e, this._busy ? "common.loading" : "log.empty")}</p>` : k`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${H(e, "log.time")}</th>
                      <th>${H(e, "log.event")}</th>
                      <th>${H(e, "log.category")}</th>
                      <th>${H(e, "log.where")}</th>
                      <th>${H(e, "log.who")}</th>
                      <th>${H(e, "log.detail")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this._rows.map((t) => this._renderRow(e, t))}
                  </tbody>
                </table>
              </div>`}
          ${this._total > Z ? k`<div class="actions">
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset === 0}
                  @click=${() => {
			this._offset = Math.max(0, this._offset - Z), this._load();
		}}
                >
                  ${H(e, "log.newer")}
                </button>
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset + Z >= this._total}
                  @click=${() => {
			this._offset += Z, this._load();
		}}
                >
                  ${H(e, "log.older")}
                </button>
              </div>` : j}
        </div>
      </div>
    `;
	}
	_renderRow(e, t) {
		let n = this.ctx, r = n.status.areas.find((e) => e.id === t.area_id), i = n.status.zones.find((e) => e.id === t.zone_id), a = this._open === t.id, o = [r?.name, i?.name].filter(Boolean).join(" · ");
		return k`
      <tr class="clickable" aria-selected=${a ? "true" : "false"} @click=${() => this._open = a ? void 0 : t.id}>
        <td class="mono">${new Date(t.ts).toLocaleString(n.hass.language)}</td>
        <td>
          <span class="state ${vt(t.severity)}">
            ${gt(e, t.event_type)}
          </span>
        </td>
        <td><span class="tag">${H(e, `category.${t.category}`)}</span></td>
        <td>${o}</td>
        <td>
          ${t.user_name ?? (t.channel ? _t(e, t.channel) : "")}
        </td>
        <td class="detail">${this._summary(e, t)}</td>
      </tr>
      ${a ? k`<tr class="expanded">
            <td colspan="6">
              <dl class="kv">
                ${t.incident_id ? k`<dt>${H(e, "log.incident")}</dt>
                      <dd>
                        <button
                          class="btn small"
                          @click=${(e) => {
			e.stopPropagation(), this._filter({ incident_id: t.incident_id });
		}}
                        >
                          ${H(e, "log.show_incident")}
                        </button>
                      </dd>` : j}
                ${t.outcome ? k`<dt>${H(e, "log.outcome")}</dt>
                      <dd>${H(e, `outcome.${t.outcome}`)}</dd>` : j}
                ${t.channel ? k`<dt>${H(e, "log.channel")}</dt>
                      <dd>${_t(e, t.channel)}</dd>` : j}
                ${this._changeLines(e, t).map((t, n) => k`<dt>${n ? "" : H(e, "log.changes")}</dt>
                    <dd>${t}</dd>`)}
                ${this._plainDetail(t).map(([t, n]) => k`<dt>${H(e, `detail.${t}`)}</dt>
                    <dd class="mono">${n}</dd>`)}
              </dl>
            </td>
          </tr>` : j}
    `;
	}
	_summary(e, t) {
		let n = this.ctx, r = t.detail ?? {};
		if (typeof r.reason == "string") {
			let t = Array.isArray(r.blocking_zones) ? r.blocking_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? String(e)).join(", ") : "";
			return H(e, `reason.${r.reason}`, { zones: t });
		}
		if (typeof r.error == "string") return r.error;
		if (t.event_type === "zone_state") return `${r.from ?? "?"} → ${r.to ?? "?"}`;
		if (t.event_type === "reloaded") return H(e, "log.gap_short", { seconds: String(r.gap_seconds ?? "") });
		if (t.event_type === "system_unavailable" && typeof r.down_since == "string") return H(e, "log.gap", {
			from: new Date(r.down_since).toLocaleString(n.hass.language),
			to: new Date(String(r.up_at)).toLocaleString(n.hass.language)
		});
		if (typeof r.kind == "string" && t.category === "action") return H(e, `action_kind.${r.kind}`);
		let i = this._changeLines(e, t);
		return i.length ? i.length > 2 ? `${i.slice(0, 2).join(" · ")} ${H(e, "log.and_more", { count: i.length - 2 })}` : i.join(" · ") : "";
	}
	_changeLines(e, t) {
		let n = t.detail?.changes;
		if (!n || typeof n != "object" || Array.isArray(n)) return [];
		let r = [];
		for (let [t, i] of Object.entries(n)) {
			let n = H(e, `config_kind.${t}`);
			if (typeof i != "object" || !i) {
				r.push(`${n}: ${this._value(e, i)}`);
				continue;
			}
			let a = i;
			if (!("added" in a || "removed" in a || "changed" in a)) {
				r.push(...this._fieldLines(e, n, a));
				continue;
			}
			for (let t of a.added ?? []) r.push(`${n} · ${H(e, "log.added")}: ${t}`);
			for (let t of a.removed ?? []) r.push(`${n} · ${H(e, "log.removed")}: ${t}`);
			let o = a.changed ?? {};
			for (let [t, i] of Object.entries(o)) r.push(...this._fieldLines(e, `${n} «${t}»`, i));
		}
		return r;
	}
	_fieldLines(e, t, n) {
		return Array.isArray(n) ? n.map((n) => `${t} · ${H(e, `field.${n}`)}`) : Object.entries(n).map(([n, r]) => {
			let i = H(e, `field.${n}`), a = i.startsWith("field.") ? n : i;
			return Array.isArray(r) && r.length === 2 ? `${t} · ${a}: ${this._value(e, r[0])} → ${this._value(e, r[1])}` : `${t} · ${a}: ${H(e, "log.changed")}`;
		});
	}
	_value(e, t) {
		return t == null || t === "" ? "—" : typeof t == "boolean" ? H(e, t ? "common.yes" : "common.no") : Array.isArray(t) ? t.length ? t.map((t) => this._value(e, t)).join(", ") : "—" : String(t);
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
			U,
			W,
			o`
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
function gt(e, t) {
	let n = H(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = H(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
function _t(e, t) {
	let n = H(e, `log_channel.${t}`);
	return n.startsWith("log_channel.") ? t : n;
}
function vt(e) {
	return e === "alarm" ? "triggered" : e === "warning" ? "arming" : "disarmed";
}
customElements.get("foyer-page-log") || customElements.define("foyer-page-log", ht);
//#endregion
//#region src/panel/pages/settings.ts
var yt = ["en", "it"], bt = {
	targets: [],
	mode: "sound",
	sound: null,
	tts_entity: null,
	volume: null,
	quiet_start: null,
	quiet_end: null,
	during_exit: !1
}, xt = class extends R {
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
		return this._draft ?? structuredClone(this.ctx?.config?.chime ?? bt);
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
		return e?.config ? k`${this._renderDefaults(e.strings)} ${this._renderResponse(e.strings)}
    ${this._renderChime(e.strings, this._chime)} ${this._renderLog(e.strings)}
    ${this._renderBackup(e.strings)} ${this._renderLanguage(e.strings)}` : j;
	}
	_entities(e) {
		return Y(this.ctx.hass, e);
	}
	_renderDefaults(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.meta?.bounds ?? {}, i = (t, r, i) => k`<label class="field">
      <span class="lbl">${H(e, `field.${t}`)}</span>
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
      <span class="hint">${i ?? H(e, "common.seconds_unit")}</span>
    </label>`;
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "settings.defaults_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${H(e, "settings.defaults_intro")}</p>
          <div class="grid-form">
            ${i("siren_duration", r.siren_duration, H(e, "settings.siren_duration_hint"))}
            ${i("arm_hold_timeout", r.arm_hold_timeout, H(e, "settings.arm_hold_hint"))}
            ${i("default_entry_delay", r.entry_delay, H(e, "settings.area_defaults_hint"))}
            ${i("default_exit_delay", r.exit_delay, H(e, "settings.area_defaults_hint"))}
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
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "settings.log_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${H(e, "settings.log_intro")}</p>
          <div class="rows">
            ${r.map((t) => {
			let r = n.enabled[t] !== !1;
			return k`<div class="row">
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${r}
                    @change=${(e) => o({ enabled: { [t]: e.target.checked } })}
                  />
                  <span>${H(e, `category.${t}`)}</span>
                </label>
                <span class="spacer"></span>
                ${r ? k`<label class="field inline">
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
                      <span class="hint">${H(e, "settings.log_days")}</span>
                    </label>` : k`<span class="hint">${H(e, "settings.log_off")}</span>`}
              </div>`;
		})}
          </div>
          <p class="hint">${H(e, "settings.log_rows_hint")}</p>
        </div>
      </div>
    `;
	}
	_renderBackup(e) {
		let t = (this.ctx.meta?.schema_version ?? []).join(".");
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "settings.backup_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${H(e, "settings.backup_intro")}</p>
          <div class="actions">
            <button class="btn" ?disabled=${this._busy} @click=${this._exportConfig}>
              ${H(e, "settings.backup_export")}
            </button>
            <label class="btn file">
              ${H(e, "settings.backup_import")}
              <input type="file" accept="application/json,.json" @change=${this._importConfig} />
            </label>
          </div>
          <p class="hint">${H(e, "settings.backup_hint")}</p>
          <p class="hint">${H(e, "settings.backup_version", { version: t })}</p>
          ${this._restored ? k`<div class="notice">${H(e, "settings.backup_restored")}</div>` : j}
        </div>
      </div>
    `;
	}
	async _exportConfig() {
		if (this.ctx) {
			this._busy = !0;
			try {
				let e = await this.ctx.exportConfig();
				Fe(e.filename, JSON.stringify(e.document, null, 2), "application/json");
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
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "settings.language_title")}</h2></div>
        <div class="card-bd">
          <label class="field">
            <span class="lbl">${H(e, "field.language")}</span>
            <select
              @change=${(e) => this._saveSettings({ language: e.target.value || null })}
            >
              <option value="" ?selected=${!n.language}>
                ${H(e, "settings.language_system")}
              </option>
              ${yt.map((t) => k`<option .value=${t} ?selected=${t === n.language}>
                    ${H(e, `language.${t}`)}
                  </option>`)}
            </select>
            <span class="hint">${H(e, "settings.language_hint")}</span>
          </label>
          ${this._problems.length ? k`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
                </ul>
              </div>` : j}
        </div>
      </div>
    `;
	}
	_renderResponse(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.config.profiles ?? [], i = t.meta?.silenceable ?? [], a = (t, i) => k`<label class="field">
        <span class="lbl">${H(e, `field.${t}`)}</span>
        <select
          @change=${(e) => this._saveSettings({ [t]: e.target.value || null })}
        >
          <option value="" ?selected=${!n[t]}>${H(e, "settings.none")}</option>
          ${r.map((e) => k`<option .value=${e.id ?? ""} ?selected=${e.id === n[t]}>
                ${e.name}
              </option>`)}
        </select>
        <span class="hint">${i}</span>
      </label>`;
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "settings.response_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${H(e, "settings.response_intro")}</p>
          <div class="grid-form">
            ${a("default_profile_id", H(e, "settings.default_profile_hint"))}
            ${a("technical_profile_id", H(e, "settings.technical_profile_hint"))}
            <label class="field">
              <span class="lbl">${H(e, "field.camera_dir")}</span>
              <input
                .value=${n.camera_dir}
                @change=${(e) => this._saveSettings({ camera_dir: e.target.value.trim() })}
              />
              <span class="hint">${H(e, "settings.camera_dir_hint")}</span>
            </label>
          </div>
          <fieldset>
            <legend>${H(e, "field.silent_suppresses")}</legend>
            ${i.map((t) => k`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${n.silent_suppresses.includes(t)}
                    @change=${(e) => {
			let r = e.target.checked ? [...n.silent_suppresses, t] : n.silent_suppresses.filter((e) => e !== t);
			this._saveSettings({ silent_suppresses: r });
		}}
                  />
                  <span
                    >${t === "chime" ? H(e, "settings.chime_title") : H(e, `action_kind.${t}`)}</span
                  >
                </label>`)}
            <p class="hint">${H(e, "settings.silent_hint")}</p>
          </fieldset>
        </div>
      </div>
    `;
	}
	_renderChime(e, t) {
		let n = this.ctx, r = nt(n.hass, n.meta?.chime_domains ?? [
			"media_player",
			"siren",
			"notify"
		]);
		for (let e of t.targets) r.some((t) => t.id === e.entity_id) || r.push({
			id: e.entity_id,
			name: e.entity_id
		});
		let i = this._entities(["tts"]), a = (e) => (t) => this._set(e, t.target.value || null);
		return k`
      <div class="card">
        <div class="card-hd"><h2>${H(e, "settings.chime_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${H(e, "settings.chime_intro")}</p>
          <fieldset>
            <legend>${H(e, "field.targets")}</legend>
            ${r.length ? r.map((t) => this._renderTarget(e, t)) : k`<p class="hint">${H(e, "settings.no_targets")}</p>`}
            <p class="hint">${H(e, "settings.targets_hint")}</p>
          </fieldset>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${H(e, "field.mode")}</span>
              <select
                @change=${(e) => this._set("mode", e.target.value)}
              >
                ${["sound", "speech"].map((n) => k`<option .value=${n} ?selected=${n === t.mode}>
                      ${H(e, `chime_mode.${n}`)}
                    </option>`)}
              </select>
            </label>
            ${t.mode === "speech" ? k`<label class="field">
                    <span class="lbl">${H(e, "field.tts_entity")}</span>
                    <select
                      @change=${(e) => this._set("tts_entity", e.target.value || null)}
                    >
                      <option value="" ?selected=${!t.tts_entity}>
                        ${H(e, "settings.pick_tts")}
                      </option>
                      ${i.map((e) => k`<option .value=${e.id} ?selected=${e.id === t.tts_entity}>
                            ${e.name}
                          </option>`)}
                    </select>
                    <span class="hint">${H(e, "settings.tts_hint")}</span>
                  </label>` : k`<label class="field">
                    <span class="lbl">${H(e, "field.sound")}</span>
                    <input
                      .value=${t.sound ?? ""}
                      @input=${(e) => this._set("sound", e.target.value.trim() || null)}
                    />
                    <span class="hint">${H(e, "settings.sound_hint")}</span>
                  </label>`}
            <label class="field">
              <span class="lbl">${H(e, "field.volume")}</span>
              <input
                type="number"
                min="0"
                max="100"
                .value=${t.volume == null ? "" : String(t.volume)}
                @input=${(e) => this._set("volume", K(e.target.value))}
              />
              <span class="hint">${H(e, "settings.volume_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.quiet_start")}</span>
              <input type="time" .value=${t.quiet_start ?? ""} @input=${a("quiet_start")} />
            </label>
            <label class="field">
              <span class="lbl">${H(e, "field.quiet_end")}</span>
              <input type="time" .value=${t.quiet_end ?? ""} @input=${a("quiet_end")} />
              <span class="hint">${H(e, "settings.quiet_hint")}</span>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.during_exit}
              @change=${(e) => this._set("during_exit", e.target.checked)}
            />
            <span>
              ${H(e, "field.during_exit")}
              <span class="hint">${H(e, "settings.during_exit_hint")}</span>
            </span>
          </label>
          <p class="hint">${H(e, "settings.switch_hint")}</p>
          ${this._problems.length ? k`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
                  </ul>
                </div>` : j}
          ${this._saved ? k`<div class="notice">${H(e, "settings.saved")}</div>` : j}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${H(e, "common.save")}
            </button>
            <button
              class="btn"
              ?disabled=${this._busy || !this._draft}
              @click=${() => {
			this._draft = void 0, this._problems = [];
		}}
            >
              ${H(e, "common.cancel")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderTarget(e, t) {
		let n = this._target(t.id), r = (e) => (n) => this._setTarget(t.id, { [e]: n.target.value || null });
		return k`<div class="target">
      <label class="check">
        <input
          type="checkbox"
          .checked=${!!n}
          @change=${(e) => this._toggleTarget(t.id, e.target.checked)}
        />
        <span>
          ${t.name === t.id ? t.id : H(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}
        </span>
      </label>
      ${n ? k`<label class="field inline">
                <span class="lbl">${H(e, "field.quiet_start")}</span>
                <input
                  type="time"
                  .value=${n.quiet_start ?? ""}
                  @input=${r("quiet_start")}
                />
              </label>
              <label class="field inline">
                <span class="lbl">${H(e, "field.quiet_end")}</span>
                <input type="time" .value=${n.quiet_end ?? ""} @input=${r("quiet_end")} />
              </label>` : j}
    </div>`;
	}
	static {
		this.styles = [W, o`
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
customElements.get("foyer-page-settings") || customElements.define("foyer-page-settings", xt);
//#endregion
//#region src/panel/wizard.ts
var Q = [
	"area",
	"zones",
	"scenario",
	"user",
	"test"
], St = 3, Ct = class extends R {
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
		let e = Q.indexOf(this._step);
		this._problems = [], e < Q.length - 1 && (this._step = Q[e + 1]);
	}
	_back() {
		let e = Q.indexOf(this._step);
		this._problems = [], e > 0 && (this._step = Q[e - 1]);
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
		if (!e?.config) return j;
		let t = e.strings;
		return k`
      <section class="wizard">
        <header>
          <h2>${H(t, "wizard.title")}</h2>
          <button class="btn" ?disabled=${this._busy} @click=${this._finish}>
            ${H(t, "wizard.dismiss")}
          </button>
        </header>
        <p class="intro">${H(t, "wizard.intro")}</p>
        <ol class="steps">
          ${Q.map((e, n) => {
			let r = Q.indexOf(this._step);
			return k`<li class=${n < r ? "done" : n === r ? "active" : ""}>
              <span class="n">${n + 1}</span>${H(t, `wizard.step.${e}`)}
            </li>`;
		})}
        </ol>
        <div class="body">${this._renderStep(t)}</div>
        ${this._problems.length ? k`<div class="problems" role="alert">
              <ul>
                ${this._problems.map((e) => k`<li>${G(t, e)}</li>`)}
              </ul>
            </div>` : j}
        <div class="actions">
          <button
            class="btn"
            ?disabled=${this._busy || this._step === Q[0]}
            @click=${this._back}
          >
            ${H(t, "wizard.back")}
          </button>
          <span class="spacer"></span>
          ${this._step === "test" ? k`<button class="btn primary" ?disabled=${this._busy} @click=${this._finish}>
                ${H(t, "wizard.done")}
              </button>` : k`<button class="btn primary" ?disabled=${this._busy} @click=${this._next}>
                ${H(t, "wizard.next")}
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
		if (!t) return k`<p class="hint">${H(e, "wizard.no_area")}</p>`;
		let n = (e) => this._saveArea({
			...t,
			...e
		});
		return k`
      <p>${H(e, "wizard.area_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${H(e, "field.name")}</span>
          <input
            .value=${t.name}
            @change=${(e) => n({ name: e.target.value.trim() })}
          />
        </label>
        <label class="field">
          <span class="lbl">${H(e, "field.default_exit_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_exit_delay)}
            @change=${(e) => n({ default_exit_delay: Number(e.target.value) })}
          />
          <span class="hint">${H(e, "wizard.exit_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${H(e, "field.default_entry_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_entry_delay)}
            @change=${(e) => n({ default_entry_delay: Number(e.target.value) })}
          />
          <span class="hint">${H(e, "wizard.entry_hint")}</span>
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
		return k`
      <p>${H(e, "wizard.zones_text", {
			have: n.length,
			want: St
		})}</p>
      <ul class="zones">
        ${n.map((t) => k`<li>
            <strong>${t.name}</strong>
            <span class="mono">${t.entity_id}</span>
            <span class="tag">${H(e, `zone_type.${t.type}`)}</span>
          </li>`)}
      </ul>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${H(e, "wizard.add_zone")}</span>
          <select
            @change=${(e) => this._pick(e.target.value)}
          >
            <option value="" ?selected=${!this._pickedEntity}>${H(e, "wizard.pick_entity")}</option>
            ${a.map((e) => k`<option .value=${e.id} ?selected=${e.id === this._pickedEntity}>
                  ${e.name}
                </option>`)}
          </select>
        </label>
      </div>
      ${r ? k`
            <div class="proposal">
              <p>
                ${H(e, "wizard.proposed", {
			entity: r.entity_id,
			state: r.state ?? "",
			type: H(e, `zone_type.${r.zone_type ?? "instant"}`),
			states: r.proposed.join(", ")
		})}
              </p>
              <label class="check">
                <input
                  type="checkbox"
                  .checked=${this._confirmed}
                  @change=${(e) => this._confirmed = e.target.checked}
                />
                <span>${H(e, "wizard.confirm_trigger")}</span>
              </label>
              <p class="hint">${H(e, "wizard.confirm_hint")}</p>
              <button
                class="btn"
                ?disabled=${this._busy || !this._confirmed}
                @click=${this._addZone}
              >
                ${H(e, "wizard.add")}
              </button>
            </div>
          ` : j}
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
		if (!n) return k`<p class="hint">${H(e, "wizard.no_scenario")}</p>`;
		let r = t.config.areas;
		return k`
      <p>${H(e, "wizard.scenario_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${H(e, "field.name")}</span>
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
        ${H(e, "wizard.scenario_areas", { areas: r.filter((e) => n.areas.includes(e.id)).map((e) => e.name).join(", ") })}
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
		if (t.length) return k`
        <p>${H(e, "wizard.user_text")}</p>
        <div class="notice">
          ${H(e, "wizard.user_done", { name: t[0].name })}
        </div>
      `;
		let r = this._userName.trim().length > 0 && this._userCode.length === n;
		return k`
      <p>${H(e, "wizard.user_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${H(e, "field.name")}</span>
          <input
            .value=${this._userName}
            @input=${(e) => this._userName = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${H(e, "users.code")}</span>
          <input
            type="password"
            inputmode="numeric"
            autocomplete="off"
            maxlength=${n}
            .value=${this._userCode}
            @input=${(e) => this._userCode = e.target.value}
          />
          <span class="hint">${H(e, "users.code_hint", { n })}</span>
        </label>
      </div>
      <p class="hint">${H(e, "wizard.user_hint")}</p>
      <button class="btn primary" ?disabled=${this._busy || !r} @click=${this._createUser}>
        ${H(e, "wizard.user_create")}
      </button>
      ${this._problems.length ? k`<ul class="problems">
            ${this._problems.map((t) => k`<li>${G(e, t)}</li>`)}
          </ul>` : j}
    `;
	}
	_renderTest(e) {
		let t = this.ctx, n = X(t.hass);
		return k`
      <p>${H(e, "wizard.test_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${H(e, "wizard.test_target")}</span>
          <select
            @change=${(e) => {
			this._notifyTarget = e.target.value, this._sent = !1;
		}}
          >
            <option value="" ?selected=${!this._notifyTarget}>${H(e, "wizard.pick_target")}</option>
            ${n.map((e) => k`<option .value=${e.id} ?selected=${e.id === this._notifyTarget}>
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
        ${H(e, "wizard.send_test")}
      </button>
      ${this._sent ? k`<div class="notice">${H(e, "wizard.test_sent")}</div>` : j}
      <p class="hint">${H(e, "wizard.test_hint")}</p>
    `;
	}
	async _sendTest() {
		let e = this.ctx;
		if (e && this._notifyTarget) {
			this._busy = !0, this._sent = !1;
			try {
				let t = H(e.strings, "wizard.test_message"), n = this._notifyTarget;
				if (n.startsWith("notify.") && e.hass.states[n]) await e.hass.callService("notify", "send_message", {
					entity_id: n,
					message: t
				});
				else {
					let [r, i] = n.split(".");
					await e.hass.callService(r, i, { message: t });
				}
				this._sent = !0;
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
		this.styles = [W, o`
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
customElements.get("foyer-wizard") || customElements.define("foyer-wizard", Ct);
//#endregion
//#region src/panel/foyer-panel.ts
var wt = [
	"overview",
	"areas",
	"zones",
	"scenarios",
	"profiles",
	"groups",
	"users",
	"log",
	"settings"
], Tt = [
	"areas",
	"zones",
	"scenarios",
	"profiles",
	"groups",
	"users",
	"settings"
], Et = {
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
function $(e) {
	return e === void 0 || e === "" ? {} : { code: e };
}
function Dt(e) {
	return Object.fromEntries(Object.entries(e).filter(([, e]) => e != null && e !== "" && !(Array.isArray(e) && e.length === 0)));
}
var Ot = class extends R {
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
			this._status?.areas.some((e) => e.timer) && (this._tick += 1);
		}, 1e3);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._unsubscribe?.then((e) => e()).catch(() => void 0), this._unsubscribe = void 0, window.clearInterval(this._timer);
	}
	willUpdate(e) {
		e.has("hass") && this.hass && (this.hass.language !== this._language && (this._language = this.hass.language, Pe(this.hass).then((e) => this._strings = e).catch((e) => this._error = String(e?.message ?? e))), !this._unsubscribe && this.isConnected && this._start());
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
			this._unsubscribe = void 0, this._error = e?.code === "not_loaded" ? H(this._strings, "common.not_loaded") : H(this._strings, "common.connection_error", { error: String(e?.message ?? e) });
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
				...$(n)
			})),
			disarm: (t) => this._coded((n) => e.callWS({
				type: "foyer/disarm",
				...t ? { area_ids: t } : {},
				...$(n)
			})),
			acknowledge: (t) => this._coded((n) => e.callWS({
				type: "foyer/acknowledge",
				target: t,
				...$(n)
			})),
			saveChime: (e) => this._edit("chime", {
				type: "foyer/config/chime",
				chime: e
			}),
			saveSettings: (e) => this._edit("settings", {
				type: "foyer/config/settings",
				settings: {
					...this._config?.settings,
					...e
				}
			}),
			queryLog: (t) => e.callWS({
				type: "foyer/log/query",
				...Dt(t)
			}),
			exportLog: (t, n) => e.callWS({
				type: "foyer/log/export",
				format: n,
				...Dt(t)
			}),
			clearLog: async () => await e.callWS({ type: "foyer/log/clear" }),
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
				...$(i)
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
				...$(e)
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
		return k`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="symbol" aria-hidden="true"
          >${Ae(Ne(!!this.hass?.themes?.darkMode))}</span
        >
        <div class="title">${H(e, "common.brand")}</div>
        ${this._status ? k`<span class="live">${H(e, "common.live")}</span>` : j}
        <button
          class="help-toggle"
          aria-pressed=${t ? "false" : "true"}
          title=${H(e, "help.global_toggle")}
          aria-label=${H(e, "help.global_toggle")}
          @click=${() => this._savePrefs({ help_hidden: !t })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
        </button>
      </div>
      ${e ? this._renderTabs(e) : j}
      <main>${e ? this._renderBody(e) : j}</main>
      ${this._asking && e ? this._renderCodeDialog(e) : j}
    `;
	}
	_renderCodeDialog(e) {
		let t = this._status?.security.code_length ?? 6;
		return k`
      <div class="scrim" @click=${() => this._answerCode(void 0)}></div>
      <form class="code-dialog" @submit=${(e) => {
			e.preventDefault();
			let t = e.target.elements.namedItem("code");
			this._answerCode(t.value);
		}} @click=${(e) => e.stopPropagation()}>
        <h2>${H(e, "code.title")}</h2>
        <p>${this._asking?.retry ? H(e, "code.wrong") : H(e, "code.prompt", { n: t })}</p>
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
            ${H(e, "common.cancel")}
          </button>
          <button type="submit" class="btn primary">${H(e, "common.ok")}</button>
        </div>
      </form>
    `;
	}
	_renderTabs(e) {
		let t = this._canConfigure ? wt : wt.filter((e) => !Tt.includes(e));
		return t.length < 2 ? j : k`
      <nav class="tabs" role="tablist">
        ${t.map((t) => k`
            <button
              role="tab"
              aria-selected=${t === this._page ? "true" : "false"}
              @click=${() => this._page = t}
            >
              ${H(e, `nav.${t}`)}
            </button>
          `)}
      </nav>
    `;
	}
	_renderBody(e) {
		if (this._error) return k`<p class="error">${this._error}</p>`;
		let t = this._context();
		if (!t) return k`<p class="muted">${H(e, "common.loading")}</p>`;
		let n = this._page;
		return k`
      ${this._canConfigure && this._config && !this._config.settings.wizard_done ? k`<foyer-wizard
            .ctx=${t}
            @wizard-done=${() => void this._loadConfig()}
          ></foyer-wizard>` : j} ${this._prefs.help_hidden ? j : this._renderHelp(e, n)}
      ${this._renderPage(n, t)}
    `;
	}
	_renderPage(e, t) {
		switch (this._tick, e) {
			case "areas": return k`<foyer-page-areas .ctx=${t}></foyer-page-areas>`;
			case "zones": return k`<foyer-page-zones .ctx=${t}></foyer-page-zones>`;
			case "scenarios": return k`<foyer-page-scenarios .ctx=${t}></foyer-page-scenarios>`;
			case "profiles": return k`<foyer-page-profiles .ctx=${t}></foyer-page-profiles>`;
			case "groups": return k`<foyer-page-groups .ctx=${t}></foyer-page-groups>`;
			case "users": return k`<foyer-page-users .ctx=${t}></foyer-page-users>`;
			case "log": return k`<foyer-page-log .ctx=${t}></foyer-page-log>`;
			case "settings": return k`<foyer-page-settings .ctx=${t}></foyer-page-settings>`;
			default: return k`<foyer-page-overview .ctx=${t}></foyer-page-overview>`;
		}
	}
	_renderHelp(e, t) {
		let n = `help.${t}`, r = this._helpOpen(t);
		return k`
      <section class="help" ?data-open=${r}>
        <button
          class="help-hd"
          aria-expanded=${r ? "true" : "false"}
          @click=${() => this._savePrefs({ help: { [t]: !r } })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
          <span>${H(e, `${n}.title`)}</span>
          <span class="sr-only">${H(e, "help.toggle")}</span>
          <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon>
        </button>
        ${r ? k`<div class="help-body">
              <p>${H(e, `${n}.intro`)}</p>
              <dl>
                ${Et[t].map((t) => k`
                    <dt>${H(e, `${n}.items.${t}.term`)}</dt>
                    <dd>${H(e, `${n}.items.${t}.text`)}</dd>
                  `)}
              </dl>
            </div>` : j}
      </section>
    `;
	}
	static {
		this.styles = [
			U,
			W,
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
customElements.get("foyer-panel") || customElements.define("foyer-panel", Ot);
//#endregion
