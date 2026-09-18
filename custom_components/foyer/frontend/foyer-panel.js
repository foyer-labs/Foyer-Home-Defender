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
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: ee, getOwnPropertySymbols: te, getPrototypeOf: ne } = Object, f = globalThis, re = f.trustedTypes, ie = re ? re.emptyScript : "", ae = f.reactiveElementPolyfillSupport, p = (e, t) => e, m = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? ie : null;
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
}, oe = (e, t) => !l(e, t), se = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	useDefault: !1,
	hasChanged: oe
};
Symbol.metadata ??= Symbol("metadata"), f.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var h = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = se) {
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
		return this.elementProperties.get(e) ?? se;
	}
	static _$Ei() {
		if (this.hasOwnProperty(p("elementProperties"))) return;
		let e = ne(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(p("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(p("properties"))) {
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
			let i = (n.converter?.toAttribute === void 0 ? m : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? m : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? oe)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
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
h.elementStyles = [], h.shadowRootOptions = { mode: "open" }, h[p("elementProperties")] = /* @__PURE__ */ new Map(), h[p("finalized")] = /* @__PURE__ */ new Map(), ae?.({ ReactiveElement: h }), (f.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
var g = globalThis, _ = (e) => e, v = g.trustedTypes, ce = v ? v.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, le = "$lit$", y = `lit$${Math.random().toFixed(9).slice(2)}$`, b = "?" + y, ue = `<${b}>`, x = document, S = () => x.createComment(""), C = (e) => e === null || typeof e != "object" && typeof e != "function", w = Array.isArray, de = (e) => w(e) || typeof e?.[Symbol.iterator] == "function", T = "[ 	\n\f\r]", E = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, fe = /-->/g, pe = />/g, D = RegExp(`>|${T}(?:([^\\s"'>=/]+)(${T}*=${T}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), me = /'/g, O = /"/g, k = /^(?:script|style|textarea|title)$/i, A = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), j = Symbol.for("lit-noChange"), M = Symbol.for("lit-nothing"), he = /* @__PURE__ */ new WeakMap(), N = x.createTreeWalker(x, 129);
function ge(e, t) {
	if (!w(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return ce === void 0 ? t : ce.createHTML(t);
}
var _e = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = E;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === E ? c[1] === "!--" ? o = fe : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = D) : (k.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = D) : o = pe : o === D ? c[0] === ">" ? (o = i ?? E, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? D : c[3] === "\"" ? O : me) : o === O || o === me ? o = D : o === fe || o === pe ? o = E : (o = D, i = void 0);
		let d = o === D && e[t + 1].startsWith("/>") ? " " : "";
		a += o === E ? n + ue : l >= 0 ? (r.push(s), n.slice(0, l) + le + n.slice(l) + y + d) : n + y + (l === -2 ? t : d);
	}
	return [ge(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, P = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = _e(t, n);
		if (this.el = e.createElement(l, r), N.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = N.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(le)) {
					let t = u[o++], n = i.getAttribute(e).split(y), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? ye : r[1] === "?" ? be : r[1] === "@" ? xe : L
					}), i.removeAttribute(e);
				} else e.startsWith(y) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (k.test(i.tagName)) {
					let e = i.textContent.split(y), t = e.length - 1;
					if (t > 0) {
						i.textContent = v ? v.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], S()), N.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], S());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === b) c.push({
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
		let n = x.createElement("template");
		return n.innerHTML = e, n;
	}
};
function F(e, t, n = e, r) {
	if (t === j) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = C(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = F(e, i._$AS(e, t.values), i, r)), t;
}
var ve = class {
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
		N.currentNode = r;
		let i = N.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new I(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Se(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = N.nextNode(), a++);
		}
		return N.currentNode = x, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, I = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = M, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = F(this, e, t), C(e) ? e === M || e == null || e === "" ? (this._$AH !== M && this._$AR(), this._$AH = M) : e !== this._$AH && e !== j && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? de(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== M && C(this._$AH) ? this._$AA.nextSibling.data = e : this.T(x.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = P.createElement(ge(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new ve(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = he.get(e.strings);
		return t === void 0 && he.set(e.strings, t = new P(e)), t;
	}
	k(t) {
		w(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(S()), this.O(S()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = _(e).nextSibling;
			_(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, L = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = M, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = M;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = F(this, e, t, 0), a = !C(e) || e !== this._$AH && e !== j, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = F(this, r[n + o], t, o), s === j && (s = this._$AH[o]), a ||= !C(s) || s !== this._$AH[o], s === M ? e = M : e !== M && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === M ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, ye = class extends L {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === M ? void 0 : e;
	}
}, be = class extends L {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== M);
	}
}, xe = class extends L {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = F(this, e, t, 0) ?? M) === j) return;
		let n = this._$AH, r = e === M && n !== M || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== M && (n === M || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Se = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		F(this, e);
	}
}, Ce = g.litHtmlPolyfillSupport;
Ce?.(P, I), (g.litHtmlVersions ??= []).push("3.3.3");
var we = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new I(t.insertBefore(S(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, R = globalThis, z = class extends h {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = we(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return j;
	}
};
z._$litElement$ = !0, z.finalized = !0, R.litElementHydrateSupport?.({ LitElement: z });
var Te = R.litElementPolyfillSupport;
Te?.({ LitElement: z }), (R.litElementVersions ??= []).push("4.2.2");
//#endregion
//#region node_modules/lit-html/directive.js
var Ee = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, De = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), Oe = class {
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
}, B = class extends Oe {
	constructor(e) {
		if (super(e), this.it = M, e.type !== Ee.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
	}
	render(e) {
		if (e === M || e == null) return this._t = void 0, this.it = e;
		if (e === j) return e;
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
B.directiveName = "unsafeHTML", B.resultType = 1;
//#endregion
//#region node_modules/lit-html/directives/unsafe-svg.js
var V = class extends B {};
V.directiveName = "unsafeSVG", V.resultType = 2;
var ke = De(V), Ae = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n", je = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n";
//#endregion
//#region src/shared/brand.ts
function Me(e) {
	return e ? Ae : je;
}
//#endregion
//#region src/shared/i18n.ts
var H = /* @__PURE__ */ new Map();
function Ne(e) {
	let t = e.language, n = H.get(t);
	return n || (n = e.callWS({
		type: "foyer/translations",
		language: t
	}).then((e) => e.strings), n.catch(() => H.delete(t)), H.set(t, n)), n;
}
function U(e, t, n = {}) {
	let r = e;
	for (let e of t.split(".")) if (r && typeof r == "object" && e in r) r = r[e];
	else return t;
	return typeof r == "string" ? r.replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e) : t;
}
//#endregion
//#region src/shared/styles.ts
var W = o`
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
`, G = o`
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
function Pe(e, t, n) {
	let r = URL.createObjectURL(new Blob([t], { type: n })), i = document.createElement("a");
	i.href = r, i.download = e, i.click(), setTimeout(() => URL.revokeObjectURL(r), 1e3);
}
function Fe(e, t) {
	return Math.max(0, Math.round((Date.parse(t) - e.now()) / 1e3));
}
function Ie(e, t) {
	let n = t.blocking_zones.map((e) => e.name).join(", ");
	return U(e, `reason.${t.reason ?? "unknown"}`, { zones: n });
}
function K(e, t) {
	let n = t.field ? U(e, `field.${t.field}`) : "";
	return U(e, `problem.${t.code}`, {
		field: n,
		detail: t.detail ?? ""
	});
}
function q(e) {
	let t = e.trim();
	if (t === "") return null;
	let n = Number(t);
	return Number.isFinite(n) ? n : null;
}
//#endregion
//#region src/panel/pages/overview.ts
function Le(e, t) {
	let n = U(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = U(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
var Re = /* @__PURE__ */ new Set(["zone_open", "zone_fault"]), ze = class extends z {
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
						text: U(n.strings, "overview.bypassed", { zones: e })
					} : void 0;
				} else this._feedback = {
					ok: !1,
					text: Ie(n.strings, r),
					retry: t && Re.has(r.reason ?? "") ? t : void 0
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
		e.has("ctx") && this.ctx && this._loadRecent();
	}
	render() {
		let e = this.ctx;
		if (!e) return M;
		let t = e.strings, n = e.status, r = n.areas.filter((e) => e.memory);
		return A`
      ${this._renderTechnical(t)} ${this._renderIncident(t)}
      <div class="notice" role="note">${U(t, "overview.no_codes_warning")}</div>
      ${r.map((e) => A`<div class="alarm-memory" role="alert">
          ${e.causes.length ? U(t, "overview.memory_banner", {
			area: e.name,
			zones: this._zoneNames(e.causes)
		}) : U(t, "overview.memory_banner_plain", { area: e.name })}
        </div>`)}
      ${this._renderMaster(t)} ${this._renderFeedback(t)}
      <div class="tiles">${n.areas.map((e) => this._renderArea(t, e))}</div>
      ${this._renderNotReady(t)} ${this._renderRecent(t)}
    `;
	}
	_renderRecent(e) {
		let t = this.ctx, n = this._recent;
		if (!n.length) return M;
		let r = new Map(t.status.areas.map((e) => [e.id, e.name])), i = new Map(t.status.zones.map((e) => [e.id, e.name]));
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${U(e, "overview.recent")}</h2>
          <span class="spacer"></span>
          <button class="btn sm" @click=${() => t.navigate("log")}>
            ${U(e, "overview.full_log")}
          </button>
        </div>
        <div class="card-bd">
          <div class="recent">
            ${n.map((n) => A`<div class="row">
                <span class="when mono"
                  >${new Date(n.ts).toLocaleTimeString(t.hass.language, {
			hour: "2-digit",
			minute: "2-digit"
		})}</span
                >
                <span class="state ${n.severity === "alarm" ? "triggered" : n.severity === "warning" ? "arming" : "disarmed"}"
                  >${Le(e, n.event_type)}</span
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
		if (!t.length) return M;
		let n = t.some((e) => !e.acknowledged);
		return A`
      <div class="banner technical" role="alert">
        <div class="banner-hd">${U(e, "overview.technical_title")}</div>
        <div>
          ${U(e, "overview.technical_banner", { zones: t.map((e) => e.name).join(", ") })}
        </div>
        <ul class="plain">
          ${t.map((t) => A`<li>
              <strong>${t.name}</strong> —
              ${U(e, t.acknowledged ? "technical_state.acknowledged" : t.active ? "technical_state.active" : "technical_state.memory")}
            </li>`)}
        </ul>
        ${n ? A`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("technical")}
              >
                ${U(e, "common.acknowledge")}
              </button>
            </div>` : M}
      </div>
    `;
	}
	_renderIncident(e) {
		let t = this.ctx.status.incident;
		return t ? A`
      <div class="banner incident" role="alert">
        <div class="banner-hd">
          ${U(e, "overview.incident_title", { id: t.id })}
          <span class="state ${t.acknowledged ? "memory" : "triggered"}">
            ${U(e, t.acknowledged ? "overview.incident_acknowledged" : "overview.incident_open")}
          </span>
        </div>
        <div>${U(e, "overview.incident_zones", { zones: this._zoneNames(t.zone_ids) })}</div>
        <div class="hint">${U(e, "overview.incident_hint")}</div>
        ${t.acknowledged ? M : A`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("incident")}
              >
                ${U(e, "common.acknowledge")}
              </button>
            </div>`}
      </div>
    ` : M;
	}
	_renderMaster(e) {
		let t = this.ctx.status, n = t.master, r = t.areas.some((e) => e.state !== "disarmed" || e.memory);
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${U(e, "overview.master")}</h2>
          <span class="state ${n.state}">${U(e, `state.${n.state}`)}</span>
          ${n.mode ? A`<span class="mono">${n.mode}</span>` : M}
        </div>
        <div class="card-bd">
          <div class="label">${U(e, "overview.scenario")}</div>
          <div class="chips">
            ${t.scenarios.length ? t.scenarios.map((e) => A`
                    <button
                      class="chip"
                      aria-pressed=${e.id === t.active_scenario_id ? "true" : "false"}
                      ?disabled=${this._busy}
                      @click=${() => this._arm({ scenario_id: e.id })}
                    >
                      ${e.name}
                    </button>
                  `) : A`<span class="muted">${U(e, "overview.no_scenarios")}</span>`}
          </div>
          <div class="hint">${U(e, "overview.scenario_hint")}</div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !r}
              @click=${() => this._disarm()}
            >
              ${U(e, "overview.disarm_all")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderFeedback(e) {
		let t = this._feedback;
		return t ? A`
      <div class=${t.ok ? "notice" : "problems"} role="alert">
        ${t.text}
        ${t.retry ? A`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._force(t.retry)}
              >
                ${U(e, "overview.force_arm")}
              </button>
              <span class="hint">${U(e, "overview.force_arm_hint")}</span>
            </div>` : M}
      </div>
    ` : M;
	}
	_renderArea(e, t) {
		let n = this.ctx, r = n.status.scenarios.find((e) => e.id === t.scenario_id);
		return A`
      <div class="card tile">
        <div class="card-bd">
          <div class="label">${U(e, "overview.area")}</div>
          <div class="name">${t.name}</div>
          <div class="row">
            <span class="state ${t.state}">${U(e, `state.${t.state}`)}</span>
            ${t.memory ? A`<span class="state memory">${U(e, "overview.memory")}</span>` : M}
          </div>
          ${t.timer && t.timer.kind !== "siren" ? A`<div class="countdown">
                ${U(e, `timer.${t.timer.kind}`, { seconds: Fe(n, t.timer.due) })}
              </div>` : M}
          <div class="hint">
            ${t.state === "disarmed" ? M : r ? U(e, "overview.by_scenario", { scenario: r.name }) : U(e, "overview.on_its_own")}
          </div>
          <div class="actions">
            ${t.state === "disarmed" ? A`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._arm({ area_id: t.id })}
                >
                  ${U(e, "overview.arm_area")}
                </button>` : M}
            ${t.state !== "disarmed" || t.memory ? A`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._disarm([t.id])}
                >
                  ${U(e, "overview.disarm_area")}
                </button>` : M}
          </div>
        </div>
      </div>
    `;
	}
	_renderNotReady(e) {
		let t = this.ctx, n = new Map(t.status.areas.map((e) => [e.id, e.name])), r = t.status.zones.filter((e) => e.enabled && (e.fault || e.open && e.channel === "intrusion" || e.bypassed));
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "overview.not_ready")}</h2></div>
        ${r.length ? A`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${U(e, "overview.zone")}</th>
                    <th>${U(e, "overview.area")}</th>
                    <th>${U(e, "overview.status")}</th>
                    <th>${U(e, "overview.entity_state")}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${r.map((t) => A`<tr>
                      <td>${t.name}</td>
                      <td>${n.get(t.area_id) ?? ""}</td>
                      <td>${this._zoneStatus(e, t)}</td>
                      <td class="mono">${t.state ?? "—"}</td>
                      <td>${this._renderBypass(e, t)}</td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : A`<div class="empty">${U(e, "overview.all_ready")}</div>`}
      </div>
    `;
	}
	_renderBypass(e, t) {
		let n = this.ctx;
		return t.bypassed ? A`<button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !1))}
      >
        ${U(e, "zones.unbypass")}
      </button>` : t.bypassable ? A`<div class="bypass">
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !0))}
      >
        ${U(e, "zones.bypass")}
      </button>
      ${[1, 8].map((r) => A`<button
          class="btn sm ghost"
          ?disabled=${this._busy}
          @click=${() => this._run(() => n.bypass(t.id, !0, r * 3600))}
        >
          ${U(e, "zones.bypass_hours", { hours: r })}
        </button>`)}
      <label class="minutes">
        <input
          type="number"
          min="1"
          max="10080"
          placeholder=${U(e, "zones.bypass_minutes_placeholder")}
          aria-label=${U(e, "zones.bypass_minutes")}
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
          ${U(e, "zones.bypass_minutes")}
        </button>
      </label>
    </div>` : M;
	}
	_bypassMinutes(e, t) {
		let n = this.ctx, r = Number(t.value);
		!Number.isFinite(r) || r < 1 || (t.value = "", this._run(() => n.bypass(e, !0, Math.round(r) * 60)));
	}
	_zoneStatus(e, t) {
		if (t.fault) return A`<span class="state fault">${U(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) {
			let n = t.bypass_until ? U(e, "zones.bypass_until", { time: new Date(t.bypass_until).toLocaleTimeString(void 0, {
				hour: "2-digit",
				minute: "2-digit"
			}) }) : U(e, "zones.bypass_indefinite");
			return A`<span class="state bypassed">${U(e, `bypass.${t.bypassed}`)}</span>
        <span class="hint">${t.bypassed === "manual" ? n : ""}</span>`;
		}
		return A`<span class="state open">${U(e, "zone_status.open")}</span>`;
	}
	static {
		this.styles = [
			W,
			G,
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
customElements.get("foyer-page-overview") || customElements.define("foyer-page-overview", ze);
//#endregion
//#region src/panel/profile-picker.ts
function Be(e, t) {
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
function J(e, t, n, r) {
	let i = e.strings, a = e.config?.profiles ?? [];
	return A`<label class="field">
    <span class="lbl">${U(i, "field.response_profile_id")}</span>
    <select @change=${(e) => n(e.target.value || null)}>
      <option value="" ?selected=${!t}>${U(i, "profiles.inherit")}</option>
      ${a.map((e) => A`<option .value=${e.id ?? ""} ?selected=${e.id === t}>
          ${e.name}
        </option>`)}
    </select>
    ${r ? A`<span class="hint">${r}</span>` : M}
  </label>`;
}
function Ve(e, t) {
	if (!e.config) return M;
	let { name: n, source: r } = Be(e.config, t), i = e.strings;
	return r === "none" ? A`<p class="hint">${U(i, "profiles.inherited_none")}</p>` : A`<p class="hint">
    ${U(i, "profiles.effective", { profile: n })} —
    ${U(i, `profiles.inherited_from_${r}`)}
  </p>`;
}
//#endregion
//#region src/panel/pages/areas.ts
var He = {
	name: "",
	ha_state_when_armed: "armed_away",
	default_entry_delay: 30,
	default_exit_delay: 30,
	response_profile_id: null
}, Ue = class extends z {
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
		this._draft = e ? { ...e } : { ...He }, this._problems = [];
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
		if (!e?.config) return M;
		let t = e.strings, n = new Map(e.status.areas.map((e) => [e.id, e.state])), r = (t) => e.config.zones.filter((e) => e.area_id === t).length;
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${U(t, "areas.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${U(t, "areas.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${U(t, "field.name")}</th>
                <th>${U(t, "overview.status")}</th>
                <th>${U(t, "areas.zones")}</th>
                <th>${U(t, "field.default_entry_delay")}</th>
                <th>${U(t, "field.default_exit_delay")}</th>
                <th>${U(t, "field.ha_state_when_armed")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.areas.map((e) => {
			let i = n.get(e.id ?? "") ?? "disarmed";
			return A`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td><span class="state ${i}">${U(t, `state.${i}`)}</span></td>
                  <td>${r(e.id)}</td>
                  <td>${U(t, "common.seconds", { n: e.default_entry_delay })}</td>
                  <td>${U(t, "common.seconds", { n: e.default_exit_delay })}</td>
                  <td class="mono">${e.ha_state_when_armed}</td>
                </tr>`;
		})}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : M}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx.meta, [r, i] = n?.bounds.exit_delay ?? [0, 300], a = n?.bounds.entry_delay?.[1] ?? 300;
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : U(e, "areas.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${U(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.ha_state_when_armed")}</span>
              <select
                @change=${(e) => this._set("ha_state_when_armed", e.target.value)}
              >
                ${(n?.ha_states ?? []).map((n) => A`<option .value=${n} ?selected=${n === t.ha_state_when_armed}>
                      ${U(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${U(e, "areas.reports_as_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.default_entry_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${a}
                .value=${String(t.default_entry_delay)}
                @input=${(e) => this._set("default_entry_delay", Number(e.target.value))}
              />
              <span class="hint">${U(e, "areas.entry_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.default_exit_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.default_exit_delay)}
                @input=${(e) => this._set("default_exit_delay", Number(e.target.value))}
              />
              <span class="hint">${U(e, "areas.exit_hint")}</span>
            </label>
            ${J(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
          </div>
          ${Ve(this.ctx, t.id ?? null)}
          ${this._problems.length ? A`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => A`<li>${K(e, t)}</li>`)}
                </ul>
              </div>` : M}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${U(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${U(e, "common.cancel")}
            </button>
            ${t.id ? A`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${U(e, "common.delete")}
                </button>` : M}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [W, G];
	}
};
customElements.get("foyer-page-areas") || customElements.define("foyer-page-areas", Ue);
//#endregion
//#region src/panel/pages/zones.ts
var We = /* @__PURE__ */ new Set(["event", "tag"]), Ge = /* @__PURE__ */ new Set(["unavailable", "unknown"]);
function Ke(e) {
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
function qe(e) {
	return e.channel === "intrusion" ? e : {
		...e,
		chime: !1,
		cross_zone_id: null,
		trigger_count: 1,
		silent: !1
	};
}
var Je = (e, t) => JSON.stringify(e) === JSON.stringify(t), Ye = class extends z {
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
		this._draft = e ? structuredClone(e) : Ke(t), this._saved = e, this._proposal = void 0, this._confirmed = !1, this._problems = [], e && this._propose(e.entity_id, !1);
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
		}), n.channel !== "key" && (n.key = null), n.arm_policy !== "arm_after_closing" && (n.arm_hold_timeout = null), n.entry_mode !== "follower" && (n.follows = []), n.always_on && (n.chime = !1), this._draft = qe(n);
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
		return !this._saved || !Je(this._saved.trigger, this._draft?.trigger);
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
		if (!e?.config) return M;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.status.zones.map((e) => [e.id, e]));
		return e.config.areas.length ? A`
      <div class="card">
        <div class="card-hd">
          <h2>${U(t, "zones.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${U(t, "zones.add")}</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${U(t, "field.name")}</th>
                <th>${U(t, "field.entity_id")}</th>
                <th>${U(t, "field.area_id")}</th>
                <th>${U(t, "field.type")}</th>
                <th>${U(t, "field.arm_policy")}</th>
                <th>${U(t, "overview.status")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.zones.map((e) => A`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td class="mono">${e.entity_id}</td>
                  <td>${n.get(e.area_id) ?? ""}</td>
                  <td><span class="tag">${U(t, `zone_type.${e.type}`)}</span></td>
                  <td>${U(t, `arm_policy.${e.arm_policy}`)}</td>
                  <td>${this._health(t, r.get(e.id ?? ""))}</td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : M}
    ` : A`<div class="card"><div class="empty">${U(t, "zones.no_areas")}</div></div>`;
	}
	_health(e, t) {
		if (!t) return M;
		if (!t.enabled) return A`<span class="state disabled">${U(e, "zone_status.disabled")}</span>`;
		if (t.fault) return A`<span class="state fault">${U(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) return A`<span class="state bypassed">${U(e, `bypass.${t.bypassed}`)}</span>`;
		let n = t.open ? "open" : "closed";
		return A`<span class="state ${n}">${U(e, `zone_status.${n}`)}</span>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx;
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : U(e, "zones.new")}</h2>
        </div>
        <div class="card-bd">
          ${t.id ? M : this._renderEntityPicker(e, t)}
          ${t.entity_id ? A`
                ${this._renderTrigger(e, t)} ${this._renderProperties(e, t)}
                ${t.channel === "intrusion" && t.entry_mode === "follower" ? this._renderFollows(e, t) : M}
                ${t.channel === "intrusion" ? this._renderVerification(e, t) : M}
                ${t.channel === "key" ? this._renderKey(e, t) : M}
              ` : M}
          ${this._problems.length ? A`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => A`<li>${K(e, t)}</li>`)}
                </ul>
              </div>` : M}
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !t.entity_id || this._triggerChanged() && !this._confirmed}
              @click=${this._save}
            >
              ${U(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${U(e, "common.cancel")}
            </button>
            ${t.id ? A`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${U(e, "common.delete")}
                </button>` : M}
          </div>
          ${this._triggerChanged() && !this._confirmed && t.entity_id ? A`<div class="hint">${U(e, "zones.confirm_first")}</div>` : M}
          ${n.status.areas.some((e) => e.id === t.area_id && e.state !== "disarmed") ? A`<div class="notice">${U(e, "zones.area_armed")}</div>` : M}
        </div>
      </div>
    `;
	}
	_renderEntityPicker(e, t) {
		let n = this.ctx, r = new Set(n.meta?.zone_domains ?? []), i = new Set(n.config?.zones.map((e) => e.entity_id)), a = this._filter.toLowerCase(), o = Object.values(n.hass.states).filter((e) => r.has(e.entity_id.split(".")[0])).filter((e) => {
			let t = String(e.attributes.friendly_name ?? "");
			return !a || e.entity_id.toLowerCase().includes(a) || t.toLowerCase().includes(a);
		}).sort((e, t) => e.entity_id.localeCompare(t.entity_id)).slice(0, 200);
		return A`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${U(e, "zones.search")}</span>
          <input
            .value=${this._filter}
            @input=${(e) => this._filter = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${U(e, "field.entity_id")}</span>
          <select
            @change=${(e) => this._propose(e.target.value, !0)}
          >
            <option value="" ?selected=${!t.entity_id}>${U(e, "zones.pick_entity")}</option>
            ${o.map((n) => A`<option
                .value=${n.entity_id}
                ?selected=${n.entity_id === t.entity_id}
              >
                ${U(e, i.has(n.entity_id) ? "zones.entity_used" : "zones.entity", {
			name: String(n.attributes.friendly_name ?? n.entity_id),
			entity: n.entity_id
		})}
              </option>`)}
          </select>
          <span class="hint">${U(e, "zones.entity_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderTrigger(e, t) {
		let n = this.ctx.hass.states[t.entity_id], r = n?.state ?? "unavailable", i = t.entity_id.split(".")[0], a = t.trigger;
		return A`
      <fieldset>
        <legend>${U(e, "zones.trigger_title")}</legend>
        <p class="hint">
          ${U(e, "zones.trigger_intro", {
			entity: String(n?.attributes.friendly_name ?? t.entity_id),
			state: r
		})}
          ${this._proposal?.device_class ? U(e, "zones.device_class", { device_class: this._proposal.device_class }) : M}
        </p>
        ${We.has(i) ? this._renderEventTrigger(e, i, a) : A`
              <label class="field">
                <span class="lbl">${U(e, "zones.trigger_kind")}</span>
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
                    ${U(e, "zones.kind_state")}
                  </option>
                  <option value="numeric" ?selected=${a.kind === "numeric"}>
                    ${U(e, "zones.kind_numeric")}
                  </option>
                </select>
              </label>
              ${a.kind === "numeric" ? this._renderNumericTrigger(e, a) : a.kind === "state" ? this._renderStateTrigger(e, a.states, r) : M}
            `}
        <label class="check confirm">
          <input
            type="checkbox"
            .checked=${this._confirmed || !this._triggerChanged()}
            ?disabled=${!this._triggerChanged()}
            @change=${(e) => this._confirmed = e.target.checked}
          />
          <span>
            ${U(e, "zones.confirm")}
            <span class="hint">${U(e, "zones.confirm_hint")}</span>
          </span>
        </label>
      </fieldset>
    `;
	}
	_renderStateTrigger(e, t, n) {
		let r = /* @__PURE__ */ new Set([...this._proposal?.options ?? [], ...t]);
		Ge.has(n) || r.add(n);
		let i = (e, n) => {
			let r = n ? [...t, e] : t.filter((t) => t !== e);
			this._set("trigger", {
				kind: "state",
				states: [...new Set(r)].sort()
			});
		};
		return A`
      <div class="states">
        ${[...r].map((r) => A`<label class="check">
            <input
              type="checkbox"
              .checked=${t.includes(r)}
              @change=${(e) => i(r, e.target.checked)}
            />
            <span class="mono">${r}</span>
            ${r === n ? A`<span class="tag">${U(e, "zones.now")}</span>` : M}
          </label>`)}
      </div>
      <div class="row">
        <label class="field">
          <span class="lbl">${U(e, "zones.other_state")}</span>
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
          ${U(e, "zones.add_state")}
        </button>
      </div>
      <div class="hint">${U(e, "zones.state_hint")}</div>
    `;
	}
	_renderNumericTrigger(e, t) {
		let n = (e) => this._set("trigger", {
			...t,
			...e
		});
		return A`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${U(e, "zones.operator")}</span>
          <select
            @change=${(e) => n({ operator: e.target.value })}
          >
            ${[
			"gt",
			"lt",
			"eq"
		].map((n) => A`<option .value=${n} ?selected=${n === t.operator}>
                  ${U(e, `operator.${n}`)}
                </option>`)}
          </select>
        </label>
        <label class="field">
          <span class="lbl">${U(e, "zones.threshold")}</span>
          <input
            type="number"
            step="any"
            .value=${String(t.value)}
            @input=${(e) => n({ value: Number(e.target.value) })}
          />
        </label>
        <label class="field">
          <span class="lbl">${U(e, "zones.hysteresis")}</span>
          <input
            type="number"
            step="any"
            min="0"
            ?disabled=${t.operator === "eq"}
            .value=${String(t.hysteresis)}
            @input=${(e) => n({ hysteresis: Number(e.target.value) })}
          />
          <span class="hint">${U(e, "zones.hysteresis_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${U(e, "zones.attribute")}</span>
          <input
            .value=${t.attribute ?? ""}
            @input=${(e) => n({ attribute: e.target.value.trim() || null })}
          />
          <span class="hint">${U(e, "zones.attribute_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderEventTrigger(e, t, n) {
		if (t === "tag") return A`<p class="hint">${U(e, "zones.tag_hint")}</p>`;
		let r = n.kind === "event" ? n.event_type : null;
		return A`
      <label class="field">
        <span class="lbl">${U(e, "zones.event_type")}</span>
        <select
          @change=${(e) => this._set("trigger", {
			kind: "event",
			event_type: e.target.value || null
		})}
        >
          <option value="" ?selected=${!r}>${U(e, "zones.pick_event")}</option>
          ${(this._proposal?.options ?? []).map((e) => A`<option .value=${e} ?selected=${e === r}>${e}</option>`)}
        </select>
        <span class="hint">${U(e, "zones.event_hint")}</span>
      </label>
    `;
	}
	_renderProperties(e, t) {
		let n = this.ctx, r = n.meta, i = n.config?.areas.find((e) => e.id === t.area_id), a = t.channel === "intrusion", o = (n, r) => A`
      <label class="check">
        <input
          type="checkbox"
          .checked=${!!t[n]}
          @change=${(e) => this._set(n, e.target.checked)}
        />
        <span>
          ${U(e, `field.${n}`)}
          ${r ? A`<span class="hint">${U(e, r)}</span>` : M}
        </span>
      </label>
    `;
		return A`
      <fieldset>
        <legend>${U(e, "zones.properties_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${U(e, "field.name")}</span>
            <input
              .value=${t.name}
              @input=${(e) => this._set("name", e.target.value)}
            />
          </label>
          <label class="field">
            <span class="lbl">${U(e, "field.type")}</span>
            <select @change=${(e) => this._applyType(e.target.value)}>
              ${(r?.zone_types ?? []).map((n) => A`<option
                  .value=${n.type}
                  ?selected=${n.type === t.type}
                  ?disabled=${!n.available}
                >
                  ${U(e, n.available ? `zone_type.${n.type}` : "zones.type_unavailable", { type: U(e, `zone_type.${n.type}`) })}
                </option>`)}
            </select>
            <span class="hint">${U(e, "zones.type_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${U(e, "field.area_id")}</span>
            <select
              @change=${(e) => this._set("area_id", e.target.value)}
            >
              ${(n.config?.areas ?? []).map((e) => A`<option .value=${e.id ?? ""} ?selected=${e.id === t.area_id}>
                    ${e.name}
                  </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${U(e, "field.channel")}</span>
            <select
              @change=${(e) => {
			let n = e.target.value;
			this._draft = qe({
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
		].map((n) => A`<option .value=${n} ?selected=${n === t.channel}>
                    ${U(e, `channel.${n}`)}
                  </option>`)}
            </select>
          </label>
          ${a ? A`
                <label class="field">
                  <span class="lbl">${U(e, "field.entry_mode")}</span>
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
		].map((n) => A`<option .value=${n} ?selected=${n === t.entry_mode}>
                          ${U(e, `entry_mode.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${U(e, `entry_mode_hint.${t.entry_mode}`)}</span>
                </label>
                <label class="field">
                  <span class="lbl">${U(e, "field.entry_delay")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${r?.bounds.entry_delay?.[1] ?? 300}
                    placeholder=${U(e, "zones.inherit_seconds", { n: i?.default_entry_delay ?? 30 })}
                    .value=${t.entry_delay == null ? "" : String(t.entry_delay)}
                    @input=${(e) => this._set("entry_delay", q(e.target.value))}
                  />
                  <span class="hint">${U(e, "zones.entry_delay_hint")}</span>
                </label>
                <label class="field">
                  <span class="lbl">${U(e, "field.alarm_kind")}</span>
                  <select
                    @change=${(e) => this._set("alarm_kind", e.target.value)}
                  >
                    ${[
			"intrusion",
			"tamper",
			"panic"
		].map((n) => A`<option .value=${n} ?selected=${n === t.alarm_kind}>
                          ${U(e, `alarm_kind.${n}`)}
                        </option>`)}
                  </select>
                </label>
                <label class="field">
                  <span class="lbl">${U(e, "field.arm_policy")}</span>
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
		].map((n) => A`<option .value=${n} ?selected=${n === t.arm_policy}>
                          ${U(e, `arm_policy.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${U(e, `arm_policy_hint.${t.arm_policy}`)}</span>
                </label>
                ${t.arm_policy === "arm_after_closing" ? A`<label class="field">
                      <span class="lbl">${U(e, "field.arm_hold_timeout")}</span>
                      <input
                        type="number"
                        min=${r?.bounds.arm_hold_timeout?.[0] ?? 60}
                        max=${r?.bounds.arm_hold_timeout?.[1] ?? 1800}
                        placeholder=${U(e, "zones.inherit_seconds", { n: n.config?.settings.arm_hold_timeout ?? 300 })}
                        .value=${t.arm_hold_timeout == null ? "" : String(t.arm_hold_timeout)}
                        @input=${(e) => this._set("arm_hold_timeout", q(e.target.value))}
                      />
                      <span class="hint">${U(e, "zones.hold_hint")}</span>
                    </label>` : M}
              ` : M}
          <label class="field">
            <span class="lbl">${U(e, "field.supervision_timeout")}</span>
            <input
              type="number"
              min=${r?.bounds.supervision_timeout?.[0] ?? 60}
              placeholder=${U(e, "zones.off")}
              .value=${t.supervision_timeout == null ? "" : String(t.supervision_timeout)}
              @input=${(e) => this._set("supervision_timeout", q(e.target.value))}
            />
            <span class="hint">${U(e, "zones.supervision_hint")}</span>
          </label>
        </div>
        <div class="checks">
          ${a ? o("always_on", "zones.always_on_hint") : M}
          ${a ? o("bypassable", "zones.bypassable_hint") : M}
          ${a && !t.always_on ? o("chime", "zones.chime_hint") : M}
          ${a ? o("silent", "zones.silent_hint") : M}
          ${o("allow_arm_when_faulted", "zones.allow_faulted_hint")}
          ${o("enabled", "zones.enabled_hint")}
        </div>
        ${J(n, t.response_profile_id, (e) => this._set("response_profile_id", e), U(e, "profiles.zone_hint"))}
        ${t.channel === "technical" ? A`<p class="hint">${U(e, "zones.technical_hint")}</p>
              <div class="notice fire" role="note">${U(e, "zones.fire_statement")}</div>` : M}
      </fieldset>
    `;
	}
	_renderVerification(e, t) {
		let n = this.ctx, r = n.meta, [i, a] = r?.bounds.window ?? [1, 3600], o = n.config?.groups.find((e) => e.members.includes(t.id ?? "")), s = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.members.forEach((e) => s.add(e));
		for (let e of n.config?.zones ?? []) e.id && e.cross_zone_id && e.id !== t.id && e.cross_zone_id !== t.id && (s.add(e.id), s.add(e.cross_zone_id));
		let c = (n.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && (!s.has(e.id ?? "") || e.id === t.cross_zone_id)), l = new Map(n.config?.areas.map((e) => [e.id, e.name])), u = (e) => (t) => {
			let n = q(t.target.value);
			this._set(e, n ?? (e === "trigger_count" ? 1 : 60));
		};
		return A`
      <fieldset>
        <legend>${U(e, "zones.verification_title")}</legend>
        ${o ? A`<p class="notice">${U(e, "zones.in_group", { group: o.name })}</p>` : A`<div class="grid-form">
              <label class="field">
                <span class="lbl">${U(e, "field.cross_zone_id")}</span>
                <select
                  @change=${(e) => this._set("cross_zone_id", e.target.value || null)}
                >
                  <option value="" ?selected=${!t.cross_zone_id}>
                    ${U(e, "zones.no_cross_zone")}
                  </option>
                  ${c.map((n) => A`<option .value=${n.id ?? ""} ?selected=${n.id === t.cross_zone_id}>
                      ${U(e, "zones.entity", {
			name: n.name,
			entity: l.get(n.area_id) ?? n.area_id
		})}
                    </option>`)}
                </select>
                <span class="hint">${U(e, "zones.cross_zone_hint")}</span>
              </label>
              ${t.cross_zone_id ? A`<label class="field">
                    <span class="lbl">${U(e, "field.cross_zone_window")}</span>
                    <input
                      type="number"
                      min=${i}
                      max=${a}
                      .value=${String(t.cross_zone_window)}
                      @input=${u("cross_zone_window")}
                    />
                    <span class="hint">${U(e, "groups.window_hint")}</span>
                  </label>` : M}
            </div>`}
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${U(e, "field.trigger_count")}</span>
            <input
              type="number"
              min="1"
              max=${r?.bounds.trigger_count?.[1] ?? 10}
              .value=${String(t.trigger_count)}
              @input=${u("trigger_count")}
            />
            <span class="hint">${U(e, "zones.trigger_count_hint")}</span>
          </label>
          ${t.trigger_count > 1 ? A`<label class="field">
                <span class="lbl">${U(e, "field.trigger_window")}</span>
                <input
                  type="number"
                  min=${i}
                  max=${a}
                  .value=${String(t.trigger_window)}
                  @input=${u("trigger_window")}
                />
                <span class="hint">${U(e, "groups.window_hint")}</span>
              </label>` : M}
        </div>
      </fieldset>
    `;
	}
	_renderFollows(e, t) {
		let n = new Map(this.ctx?.config?.areas.map((e) => [e.id, e.name])), r = (this.ctx?.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && e.entry_mode === "delayed"), i = (e, n) => this._set("follows", n ? [.../* @__PURE__ */ new Set([...t.follows, e])] : t.follows.filter((t) => t !== e));
		return A`
      <fieldset>
        <legend>${U(e, "field.follows")}</legend>
        ${r.length ? r.map((r) => A`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.follows.includes(r.id ?? "")}
                  @change=${(e) => i(r.id ?? "", e.target.checked)}
                />
                <span>
                  ${U(e, "zones.entity", {
			name: r.name,
			entity: n.get(r.area_id) ?? r.area_id
		})}
                </span>
              </label>`) : A`<p class="hint">${U(e, "zones.no_delayed_zones")}</p>`}
        <p class="hint">${U(e, "zones.follows_hint")}</p>
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
		return A`
      <fieldset>
        <legend>${U(e, "zones.key_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${U(e, "field.on_activate")}</span>
            <select
              @change=${(e) => r({ on_activate: e.target.value })}
            >
              ${[
			"arm",
			"disarm",
			"toggle"
		].map((t) => A`<option .value=${t} ?selected=${t === n.on_activate}>
                    ${U(e, `key_command.${t}`)}
                  </option>`)}
            </select>
          </label>
          ${n.on_activate === "disarm" ? M : A`<label class="field">
                <span class="lbl">${U(e, "field.scenario_id")}</span>
                <select
                  @change=${(e) => r({ scenario_id: e.target.value || null })}
                >
                  <option value="" ?selected=${!n.scenario_id}>
                    ${U(e, "zones.pick_scenario")}
                  </option>
                  ${i.map((e) => A`<option .value=${e.id ?? ""} ?selected=${e.id === n.scenario_id}>
                        ${e.name}
                      </option>`)}
                </select>
              </label>`}
          <label class="field">
            <span class="lbl">${U(e, "field.on_deactivate")}</span>
            <select
              @change=${(e) => r({ on_deactivate: e.target.value })}
            >
              ${["none", "disarm"].map((t) => A`<option .value=${t} ?selected=${t === n.on_deactivate}>
                    ${U(e, `key_release.${t}`)}
                  </option>`)}
            </select>
          </label>
        </div>
        <p class="hint">${U(e, "zones.key_hint")}</p>
      </fieldset>
    `;
	}
	static {
		this.styles = [
			W,
			G,
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
customElements.get("foyer-page-zones") || customElements.define("foyer-page-zones", Ye);
//#endregion
//#region src/panel/pages/scenarios.ts
var Xe = {
	name: "",
	areas: [],
	ha_master_state: "armed_away",
	icon: null,
	exit_delay_override: null,
	siren_duration_override: null,
	response_profile_id: null
}, Ze = class extends z {
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
			...Xe,
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
		if (!e?.config) return M;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = e.config.scenarios.map((e) => e.ha_master_state);
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${U(t, "scenarios.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${U(t, "scenarios.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${U(t, "field.name")}</th>
                <th>${U(t, "field.areas")}</th>
                <th>${U(t, "field.ha_master_state")}</th>
                <th>${U(t, "field.exit_delay_override")}</th>
                <th>${U(t, "field.siren_duration_override")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.scenarios.map((i) => A`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === i.id ? "true" : "false"}
                  @click=${() => this._edit(i)}
                >
                  <td>
                    <strong>${i.name}</strong>
                    ${i.id === e.status.active_scenario_id ? A`<span class="state armed">${U(t, "scenarios.active")}</span>` : M}
                  </td>
                  <td>
                    ${i.areas.map((e) => A`<span class="tag">${n.get(e) ?? e}</span>`)}
                  </td>
                  <td>
                    <span class="mono">${i.ha_master_state}</span>
                    ${r.filter((e) => e === i.ha_master_state).length > 1 ? A`<div class="hint">${U(t, "scenarios.shared_mode")}</div>` : M}
                  </td>
                  <td>
                    ${i.exit_delay_override == null ? U(t, "scenarios.area_default") : U(t, "common.seconds", { n: i.exit_delay_override })}
                  </td>
                  <td>
                    ${i.siren_duration_override == null ? U(t, "scenarios.global_default") : U(t, "common.seconds", { n: i.siren_duration_override })}
                  </td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : M}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.meta, i = (e, n) => this._set("areas", n ? [...t.areas, e] : t.areas.filter((t) => t !== e));
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : U(e, "scenarios.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${U(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.ha_master_state")}</span>
              <select
                @change=${(e) => this._set("ha_master_state", e.target.value)}
              >
                ${(r?.ha_states ?? []).map((n) => A`<option .value=${n} ?selected=${n === t.ha_master_state}>
                      ${U(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${U(e, "scenarios.mode_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.exit_delay_override")}</span>
              <input
                type="number"
                min="0"
                max=${r?.bounds.exit_delay?.[1] ?? 300}
                placeholder=${U(e, "scenarios.area_default")}
                .value=${t.exit_delay_override == null ? "" : String(t.exit_delay_override)}
                @input=${(e) => this._set("exit_delay_override", q(e.target.value))}
              />
              <span class="hint">${U(e, "scenarios.exit_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.siren_duration_override")}</span>
              <input
                type="number"
                min="1"
                max=${r?.bounds.siren_duration?.[1] ?? 900}
                placeholder=${U(e, "scenarios.global_seconds", { n: n.config?.settings.siren_duration ?? 180 })}
                .value=${t.siren_duration_override == null ? "" : String(t.siren_duration_override)}
                @input=${(e) => this._set("siren_duration_override", q(e.target.value))}
              />
              <span class="hint">${U(e, "scenarios.siren_hint")}</span>
            </label>
            ${J(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
          </div>
          <fieldset>
            <legend>${U(e, "field.areas")}</legend>
            ${(n.config?.areas ?? []).map((e) => A`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.areas.includes(e.id ?? "")}
                  @change=${(t) => i(e.id ?? "", t.target.checked)}
                />
                <span>${e.name}</span>
              </label>`)}
            <p class="hint">${U(e, "scenarios.areas_hint")}</p>
          </fieldset>
          ${this._problems.length ? A`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => A`<li>${K(e, t)}</li>`)}
                </ul>
              </div>` : M}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${U(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${U(e, "common.cancel")}
            </button>
            ${t.id ? A`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${U(e, "common.delete")}
                </button>` : M}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			W,
			G,
			o`
      td .state {
        margin-left: 8px;
      }
    `
		];
	}
};
customElements.get("foyer-page-scenarios") || customElements.define("foyer-page-scenarios", Ze);
//#endregion
//#region src/panel/ha-targets.ts
function Qe(e, t) {
	let n = e.states[t];
	return String(n?.attributes?.friendly_name ?? t);
}
function Y(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) t.has(n.id) || t.set(n.id, n);
	return [...t.values()].sort((e, t) => e.id.localeCompare(t.id));
}
function X(e, t) {
	return Y(Object.values(e.states).filter((e) => t.includes(e.entity_id.split(".")[0])).map((t) => ({
		id: t.entity_id,
		name: Qe(e, t.entity_id)
	})));
}
function Z(e) {
	let t = Object.keys(e.services?.notify ?? {}).filter((e) => e !== "send_message").map((e) => ({
		id: `notify.${e}`,
		name: `notify.${e}`
	}));
	return Y([...X(e, ["notify"]), ...t]);
}
function $e(e, t) {
	return Y([...X(e, t.filter((e) => e !== "notify")), ...t.includes("notify") ? Z(e) : []]);
}
function et(e) {
	return Object.keys(e.services ?? {}).sort();
}
function tt(e, t) {
	return Object.keys(e.services?.[t] ?? {}).sort();
}
//#endregion
//#region src/panel/pages/profiles.ts
var nt = {
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
}, rt = [
	"siren",
	"light",
	"switch"
], it = [
	"camera",
	"scene",
	"tts"
];
function at(e) {
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
var ot = class extends z {
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
			actions: [...this._draft.actions, at(e)]
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
		if (!e?.config) return M;
		let t = e.strings, n = e.config.profiles ?? [];
		return A`
      <p class="page-intro">${U(t, "profiles.intro")}</p>
      <div class="card">
        <div class="card-hd">
          <h2>${U(t, "profiles.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${U(t, "profiles.add")}</button>
        </div>
        ${n.length ? A`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${U(t, "field.name")}</th>
                      <th>${U(t, "field.actions")}</th>
                      <th>${U(t, "field.severity")}</th>
                      <th>${U(t, "profiles.used_by")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${n.map((e) => A`<tr
                          class="clickable"
                          aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                          @click=${() => this._edit(e)}
                        >
                          <td><strong>${e.name}</strong></td>
                          <td>
                            ${e.actions.length ? e.actions.map((e) => A`<span class="tag"
                                        >${U(t, `action_kind.${e.kind}`)}</span
                                      > `) : A`<span class="muted">${U(t, "profiles.no_actions")}</span>`}
                          </td>
                          <td>${e.severity}</td>
                          <td class="muted">${this._usedBy(t, e)}</td>
                        </tr>`)}
                  </tbody>
                </table>
              </div>` : A`<div class="empty">${U(t, "profiles.none")}</div>`}
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : M}
    `;
	}
	_usedBy(e, t) {
		let n = this.ctx.config, r = [];
		n.settings.default_profile_id === t.id && r.push(U(e, "profiles.used_default")), n.settings.technical_profile_id === t.id && r.push(U(e, "profiles.used_technical"));
		for (let e of [
			n.areas,
			n.zones,
			n.scenarios,
			n.groups
		]) for (let n of e) n.response_profile_id === t.id && r.push(n.name);
		return r.length ? r.join(", ") : U(e, "profiles.unused");
	}
	_renderEditor(e, t) {
		let n = this.ctx?.meta?.bounds.severity ?? [1, 10];
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : U(e, "profiles.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${U(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.severity")}</span>
              <input
                type="number"
                min=${n[0]}
                max=${n[1]}
                .value=${String(t.severity)}
                @input=${(e) => this._set("severity", q(e.target.value) ?? 1)}
              />
              <span class="hint">${U(e, "profiles.severity_hint")}</span>
            </label>
          </div>

          <div class="actions-list">
            ${t.actions.map((t, n) => this._renderAction(e, t, n))}
          </div>
          ${t.actions.length ? M : A`<p class="hint">${U(e, "profiles.no_actions")}</p>`}

          <div class="add-action">
            <label class="field">
              <span class="lbl">${U(e, "profiles.add_action")}</span>
              <select
                .value=${""}
                @change=${(e) => {
			let t = e.target;
			t.value && this._addAction(t.value), t.value = "";
		}}
              >
                <option value=""></option>
                ${(this.ctx?.meta?.action_kinds ?? []).map((t) => A`<option .value=${t}>${U(e, `action_kind.${t}`)}</option>`)}
              </select>
            </label>
          </div>
          <p class="hint">${U(e, "profiles.escalation_later")}</p>

          ${this._problems.length ? A`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((t) => A`<li>${K(e, t)}</li>`)}
                  </ul>
                </div>` : M}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${U(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${U(e, "common.cancel")}
            </button>
            ${t.id ? A`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                    ${U(e, "common.delete")}
                  </button>` : M}
          </div>
        </div>
      </div>
    `;
	}
	_renderAction(e, t, n) {
		let r = this._open === n;
		return A`
      <div class="action" ?data-open=${r}>
        <button class="action-hd" @click=${() => this._open = r ? -1 : n}>
          <span class="tag">${U(e, `action_kind.${t.kind}`)}</span>
          <span class="summary">${this._summary(e, t)}</span>
          <span class="moments">${this._momentSummary(e, t)}</span>
          ${t.conditions.length ? A`<span class="cond">${t.conditions.length}</span>` : M}
        </button>
        ${r ? A`<div class="action-bd">
                ${this._renderParams(e, t, n)} ${this._renderMoments(e, t, n)}
                ${this._renderConditions(e, t, n)}
                <div class="actions">
                  <button class="btn" @click=${() => this._moveAction(n, -1)}>&uarr;</button>
                  <button class="btn" @click=${() => this._moveAction(n, 1)}>&darr;</button>
                  <button class="btn danger" @click=${() => this._removeAction(n)}>
                    ${U(e, "profiles.delete_action")}
                  </button>
                </div>
              </div>` : M}
      </div>
    `;
	}
	_momentSummary(e, t) {
		let n = t.moments.map((t) => U(e, `moment.${t}`));
		return n.length ? n.length <= 3 ? n.join(", ") : U(e, "profiles.moments_more", {
			moments: n.slice(0, 2).join(", "),
			count: n.length - 2
		}) : U(e, "profiles.no_moments");
	}
	_summary(e, t) {
		let n = t.params;
		if (t.kind === "delay") return `${n.seconds ?? 0} s`;
		if (t.kind === "call_service") return `${n.domain ?? ""}.${n.service ?? ""}`;
		if (t.kind === "notify") return String(n.service ?? "");
		if (t.kind === "persistent_notification") return String(n.message ?? U(e, "profiles.inherit"));
		let r = n.entity_ids ?? n.entity_id ?? "";
		return Array.isArray(r) ? r.join(", ") : String(r);
	}
	_entities(e) {
		return X(this.ctx.hass, e);
	}
	_suggested(e, t, n, r, i, a) {
		let o = `foyer-${r}-${n}`;
		return A`<label class="field">
      <span class="lbl">${U(e, `field.${r}`)}</span>
      <input
        list=${o}
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      <datalist id=${o}>
        ${i.map((e) => A`<option .value=${e.id}>
            ${e.name === e.id ? e.id : `${e.name} · ${e.id}`}
          </option>`)}
      </datalist>
      <span class="hint">${a ?? U(e, "profiles.pick_or_type")}</span>
    </label>`;
	}
	_text(e, t, n, r, i) {
		return A`<label class="field">
      <span class="lbl">${U(e, `field.${r}`)}</span>
      <input
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      ${i ? A`<span class="hint">${i}</span>` : M}
    </label>`;
	}
	_number(e, t, n, r, i) {
		return A`<label class="field">
      <span class="lbl">${U(e, `field.${r}`)}</span>
      <input
        type="number"
        .value=${t.params[r] == null ? "" : String(t.params[r])}
        @input=${(e) => this._setParam(n, r, q(e.target.value))}
      />
      ${i ? A`<span class="hint">${i}</span>` : M}
    </label>`;
	}
	_picker(e, t, n, r, i, a) {
		let o = this._entities(i), s = t.params[r], c = new Set(Array.isArray(s) ? s : s ? [String(s)] : []);
		for (let e of c) o.some((t) => t.id === e) || o.push({
			id: e,
			name: e
		});
		if (!a) return A`<label class="field">
        <span class="lbl">${U(e, `field.${r}`)}</span>
        <select
          @change=${(e) => this._setParam(n, r, e.target.value || null)}
        >
          <option value=""></option>
          ${o.map((e) => A`<option .value=${e.id} ?selected=${c.has(e.id)}>${e.name}</option>`)}
        </select>
      </label>`;
		let l = `${n}:${r}`, u = (this._filters[l] ?? "").toLowerCase().split(/\s+/).filter(Boolean), d = o.filter((e) => {
			if (c.has(e.id)) return !0;
			let t = `${e.name} ${e.id}`.toLowerCase();
			return u.every((e) => t.includes(e));
		});
		return A`<fieldset class="entities wide">
      <legend>${U(e, `field.${r}`)}</legend>
      ${o.length > 8 ? A`<input
            class="filter"
            type="search"
            .value=${this._filters[l] ?? ""}
            placeholder=${U(e, "profiles.filter")}
            @input=${(e) => {
			this._filters = {
				...this._filters,
				[l]: e.target.value
			};
		}}
          />` : M}
      <div class="entity-list">
        ${d.map((t) => A`<label class="check">
            <input
              type="checkbox"
              .checked=${c.has(t.id)}
              @change=${(e) => {
			let i = e.target.checked, a = new Set(c);
			i ? a.add(t.id) : a.delete(t.id), this._setParam(n, r, [...a]);
		}}
            />
            <span>${U(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}</span>
          </label>`)}
        ${d.length ? M : A`<p class="hint">${U(e, "profiles.no_match")}</p>`}
      </div>
    </fieldset>`;
	}
	_renderParams(e, t, n) {
		let r = this.ctx?.meta?.action_domains[t.kind] ?? [], i = U(e, "profiles.message_hint", { variables: (this.ctx?.meta?.template_variables ?? []).map((e) => `{{ ${e} }}`).join(" ") }), a = [];
		switch (rt.includes(t.kind) && a.push(this._picker(e, t, n, "entity_ids", r, !0)), it.includes(t.kind) && a.push(this._picker(e, t, n, "entity_id", r, !1)), t.kind) {
			case "notify":
				a.push(this._suggested(e, t, n, "service", Z(this.ctx.hass), U(e, "profiles.notify_hint"))), a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i)), a.push(this._picker(e, t, n, "camera_entity_id", ["camera"], !1)), a.push(A`<span class="hint">${U(e, "profiles.attach_hint")}</span>`);
				break;
			case "persistent_notification":
				a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i));
				break;
			case "siren":
				a.push(this._number(e, t, n, "duration", U(e, "profiles.siren_duration_hint"))), a.push(this._renderTone(e, t, n));
				break;
			case "light":
				a.push(this._number(e, t, n, "brightness")), a.push(this._select(e, t, n, "flash", [
					"",
					"short",
					"long"
				], (e) => e || "—"));
				break;
			case "camera":
				a.push(this._select(e, t, n, "mode", ["snapshot", "record"], (t) => U(e, `camera_mode.${t}`))), a.push(this._number(e, t, n, "duration", U(e, "profiles.camera_hint")));
				break;
			case "switch":
				a.push(this._select(e, t, n, "state", ["on", "off"], (t) => U(e, `on_off.${t}`))), a.push(this._number(e, t, n, "revert_after", U(e, "profiles.revert_hint")));
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
			case "delay": a.push(this._number(e, t, n, "seconds", U(e, "profiles.delay_hint")));
		}
		return A`<div class="grid-form">${a}</div>`;
	}
	_renderTone(e, t, n) {
		let r = t.params.entity_ids, i = Array.isArray(r) ? r : [], a = /* @__PURE__ */ new Set();
		for (let e of i) {
			let t = this.ctx.hass.states[e]?.attributes?.available_tones;
			Array.isArray(t) ? t.forEach((e) => a.add(String(e))) : t && typeof t == "object" && Object.keys(t).forEach((e) => a.add(e));
		}
		return a.size ? this._select(e, t, n, "tone", ["", ...[...a].sort()], (t) => t || U(e, "profiles.default_tone")) : i.length ? A`<label class="field">
            <span class="lbl">${U(e, "field.tone")}</span>
            <input disabled placeholder=${U(e, "profiles.no_tones")} />
            <span class="hint">${U(e, "profiles.no_tones")}</span>
          </label>` : M;
	}
	_select(e, t, n, r, i, a) {
		return A`<label class="field">
      <span class="lbl">${U(e, `field.${r}`)}</span>
      <select
        @change=${(e) => this._setParam(n, r, e.target.value || null)}
      >
        ${i.map((e) => A`<option .value=${e} ?selected=${t.params[r] === e}>
              ${a(e)}
            </option>`)}
      </select>
    </label>`;
	}
	_json(e, t, n) {
		return A`<label class="field wide">
      <span class="lbl">${U(e, "field.data")}</span>
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
      <span class="hint">${U(e, "profiles.call_service_hint")}</span>
    </label>`;
	}
	_renderMoments(e, t, n) {
		let r = new Set(this.ctx?.meta?.future_moments ?? []), i = new Set(this.ctx?.meta?.moments ?? []);
		return A`<div class="moments-grid">
      ${Object.entries(nt).map(([a, o]) => A`<fieldset>
            <legend>${U(e, `moment_group.${a}`)}</legend>
            ${o.filter((e) => i.has(e)).map((i) => A`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${t.moments.includes(i)}
                      @change=${(e) => {
			let r = e.target.checked ? [...t.moments, i] : t.moments.filter((e) => e !== i);
			this._setAction(n, { moments: r });
		}}
                    />
                    <span>
                      ${U(e, `moment.${i}`)}
                      ${r.has(i) ? A`<span class="later">${U(e, "profiles.future_moment")}</span>` : M}
                    </span>
                  </label>`)}
          </fieldset>`)}
    </div>`;
	}
	_renderConditions(e, t, n) {
		let r = this.ctx?.meta?.max_conditions ?? 2, i = (e) => this._setAction(n, { conditions: e });
		return A`<fieldset class="conditions">
      <legend>${U(e, "field.conditions")}</legend>
      ${t.conditions.length ? t.conditions.map((r, i) => this._renderCondition(e, t, n, r, i)) : A`<p class="hint">${U(e, "condition.none")}</p>`}
      ${t.conditions.length < r ? A`<div class="actions">
              <button
                class="btn sm"
                @click=${() => i([...t.conditions, {
			kind: "time",
			after: "22:00",
			before: "07:00"
		}])}
              >
                ${U(e, "condition.time")}
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
                ${U(e, "condition.state")}
              </button>
            </div>` : M}
      ${t.conditions.length === 2 ? A`<label class="field">
              <span class="lbl">${U(e, "field.condition_mode")}</span>
              <select
                @change=${(e) => this._setAction(n, { condition_mode: e.target.value })}
              >
                ${["all", "any"].map((n) => A`<option .value=${n} ?selected=${t.condition_mode === n}>
                      ${U(e, `condition.${n}`)}
                    </option>`)}
              </select>
            </label>` : M}
      <p class="hint">${U(e, "condition.max")}</p>
    </fieldset>`;
	}
	_renderCondition(e, t, n, r, i) {
		let a = (e) => this._setAction(n, { conditions: t.conditions.map((t, n) => n === i ? {
			...t,
			...e
		} : t) });
		return A`<div class="condition">
      ${r.kind === "time" ? A`<label class="field">
                <span class="lbl">${U(e, "condition.after")}</span>
                <input
                  type="time"
                  .value=${r.after}
                  @input=${(e) => a({ after: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${U(e, "condition.before")}</span>
                <input
                  type="time"
                  .value=${r.before}
                  @input=${(e) => a({ before: e.target.value })}
                />
                <span class="hint">${U(e, "condition.midnight_hint")}</span>
              </label>` : A`<label class="field">
                <span class="lbl">${U(e, "field.entity_id")}</span>
                <input
                  .value=${r.entity_id}
                  @input=${(e) => a({ entity_id: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${U(e, "field.state")}</span>
                <select
                  @change=${(e) => a({ operator: e.target.value })}
                >
                  ${["is", "is_not"].map((t) => A`<option .value=${t} ?selected=${r.operator === t}>
                        ${U(e, `condition.${t}`)}
                      </option>`)}
                </select>
              </label>
              <label class="field">
                <span class="lbl">${U(e, "condition.state")}</span>
                <input
                  .value=${r.state}
                  @input=${(e) => a({ state: e.target.value })}
                />
              </label>`}
      <button class="btn sm danger" @click=${() => this._setAction(n, { conditions: t.conditions.filter((e, t) => t !== i) })}>${U(e, "common.delete")}</button>
    </div>`;
	}
	static {
		this.styles = [
			G,
			W,
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
customElements.get("foyer-page-profiles") || customElements.define("foyer-page-profiles", ot);
//#endregion
//#region src/panel/pages/groups.ts
var st = class extends z {
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
		if (!e?.config) return M;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.config.zones.map((e) => [e.id, e.name])), i = this._rows(e.config.zones, e.config.groups ?? []);
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${U(t, "groups.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${U(t, "groups.add")}</button>
        </div>
        ${i.length ? A`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${U(t, "field.name")}</th>
                    <th>${U(t, "field.area_id")}</th>
                    <th>${U(t, "field.members")}</th>
                    <th>${U(t, "field.n")}</th>
                    <th>${U(t, "field.window_seconds")}</th>
                    <th>${U(t, "groups.members_below")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${i.map(({ group: e, derived: i }) => A`<tr
                      class=${i ? "" : "clickable"}
                      aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                      @click=${() => i ? void 0 : this._edit(e)}
                    >
                      <td>
                        <strong>${e.name}</strong>
                        ${i ? A`<span class="tag">${U(t, "groups.from_zone")}</span>` : M}
                      </td>
                      <td>${n.get(e.area_id) ?? ""}</td>
                      <td>
                        ${e.members.map((e) => A`<span class="tag">${r.get(e) ?? e}</span>`)}
                      </td>
                      <td>${U(t, "groups.threshold", {
			n: e.n,
			m: e.members.length
		})}</td>
                      <td>${U(t, "common.seconds", { n: e.window_seconds })}</td>
                      <td>
                        ${U(t, e.suppress_members ? "groups.suppressed" : "groups.not_suppressed")}
                      </td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : A`<div class="empty">${U(t, "groups.none")}</div>`}
        <div class="card-bd">
          <p class="hint">${U(t, "groups.from_zone_hint")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : M}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, [r, i] = n.meta?.bounds.window ?? [1, 3600], a = new Map(n.config?.areas.map((e) => [e.id, e.name])), o = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.id !== t.id && e.members.forEach((e) => o.add(e));
		for (let e of n.config?.zones ?? []) e.cross_zone_id && e.id && (o.add(e.id), o.add(e.cross_zone_id));
		let s = (n.config?.zones ?? []).filter((e) => e.channel === "intrusion" && e.id && (!o.has(e.id) || t.members.includes(e.id))), c = (e, n) => this._set("members", n ? [.../* @__PURE__ */ new Set([...t.members, e])] : t.members.filter((t) => t !== e));
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : U(e, "groups.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${U(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.area_id")}</span>
              <select
                @change=${(e) => this._set("area_id", e.target.value)}
              >
                ${(n.config?.areas ?? []).map((e) => A`<option .value=${e.id ?? ""} ?selected=${e.id === t.area_id}>
                      ${e.name}
                    </option>`)}
              </select>
              <span class="hint">${U(e, "groups.area_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.n")}</span>
              <input
                type="number"
                min="2"
                max=${Math.max(2, t.members.length)}
                .value=${String(t.n)}
                @input=${(e) => this._set("n", q(e.target.value) ?? 2)}
              />
              <span class="hint">
                ${U(e, "groups.threshold", {
			n: t.n,
			m: t.members.length
		})}
              </span>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.window_seconds")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.window_seconds)}
                @input=${(e) => this._set("window_seconds", q(e.target.value) ?? 60)}
              />
              <span class="hint">${U(e, "groups.window_hint")}</span>
            </label>
            ${J(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e), U(e, "profiles.group_hint"))}
          </div>
          <fieldset>
            <legend>${U(e, "field.members")}</legend>
            ${s.length ? s.map((n) => A`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${t.members.includes(n.id ?? "")}
                      @change=${(e) => c(n.id ?? "", e.target.checked)}
                    />
                    <span>
                      ${U(e, "zones.entity", {
			name: n.name,
			entity: a.get(n.area_id) ?? n.area_id
		})}
                    </span>
                  </label>`) : A`<p class="hint">${U(e, "groups.no_zones")}</p>`}
            <p class="hint">${U(e, "groups.members_hint")}</p>
          </fieldset>
          <label class="check suppress">
            <input
              type="checkbox"
              .checked=${t.suppress_members}
              @change=${(e) => this._set("suppress_members", e.target.checked)}
            />
            <span>
              ${U(e, "field.suppress_members")}
              <span class="hint">${U(e, "groups.suppress_hint")}</span>
            </span>
          </label>
          ${this._problems.length ? A`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => A`<li>${K(e, t)}</li>`)}
                </ul>
              </div>` : M}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${U(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${U(e, "common.cancel")}
            </button>
            ${t.id ? A`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${U(e, "common.delete")}
                </button>` : M}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			W,
			G,
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
customElements.get("foyer-page-groups") || customElements.define("foyer-page-groups", st);
//#endregion
//#region src/panel/pages/log.ts
var Q = 50, ct = class extends z {
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
					limit: Q,
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
				Pe(t.filename, t.content, e === "csv" ? "text/csv" : "application/json"), t.truncated && (this._error = U(this.ctx.strings, "log.truncated", {
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
		if (!e) return M;
		let t = e.strings;
		return A`${this._renderFilters(t)} ${this._renderRows(t)}`;
	}
	_renderFilters(e) {
		let t = this.ctx, n = t.meta?.log_categories ?? [], r = t.meta?.log_severities ?? [], i = t.meta?.outcomes ?? [], a = this._filters.categories ?? [];
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "log.filters")}</h2></div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${U(e, "log.from")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.start ?? ""}
                @change=${(e) => this._filter({ start: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${U(e, "log.to")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.end ?? ""}
                @change=${(e) => this._filter({ end: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${U(e, "log.area")}</span>
              <select
                @change=${(e) => this._filter({ area_id: e.target.value || null })}
              >
                <option value="">${U(e, "log.all")}</option>
                ${t.status.areas.map((e) => A`<option .value=${e.id} ?selected=${e.id === this._filters.area_id}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "log.zone")}</span>
              <select
                @change=${(e) => this._filter({ zone_id: e.target.value || null })}
              >
                <option value="">${U(e, "log.all")}</option>
                ${t.status.zones.map((e) => A`<option .value=${e.id} ?selected=${e.id === this._filters.zone_id}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "log.severity")}</span>
              <select
                @change=${(e) => this._filter({ severity: e.target.value || null })}
              >
                <option value="">${U(e, "log.all")}</option>
                ${r.map((t) => A`<option .value=${t} ?selected=${t === this._filters.severity}>
                      ${U(e, `severity.${t}`)}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "log.outcome")}</span>
              <select
                @change=${(e) => this._filter({ outcome: e.target.value || null })}
              >
                <option value="">${U(e, "log.all")}</option>
                ${i.map((t) => A`<option .value=${t} ?selected=${t === this._filters.outcome}>
                      ${U(e, `outcome.${t}`)}
                    </option>`)}
              </select>
            </label>
          </div>
          <fieldset>
            <legend>${U(e, "log.categories")}</legend>
            <div class="chips">
              ${n.map((t) => A`
                  <button
                    class="chip"
                    aria-pressed=${a.includes(t) ? "true" : "false"}
                    @click=${() => this._filter({ categories: a.includes(t) ? a.filter((e) => e !== t) : [...a, t] })}
                  >
                    ${U(e, `category.${t}`)}
                  </button>
                `)}
            </div>
            <p class="hint">${U(e, "log.categories_hint")}</p>
          </fieldset>
          ${this._filters.incident_id ? A`<p class="hint">
                ${U(e, "log.incident_filter", { id: this._filters.incident_id })}
                <button class="btn small" @click=${() => this._filter({ incident_id: null })}>
                  ${U(e, "log.clear_filter")}
                </button>
              </p>` : M}
        </div>
      </div>
    `;
	}
	_renderRows(e) {
		let t = this.ctx, n = this._rows.length;
		return A`
      <div class="card">
        <div class="card-hd">
          <h2>${U(e, "log.events")}</h2>
          <span class="hint"
            >${U(e, "log.count", {
			shown: n ? `${this._offset + 1}–${this._offset + n}` : "0",
			total: this._total
		})}</span
          >
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("csv")}>
            ${U(e, "log.export_csv")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("json")}>
            ${U(e, "log.export_json")}
          </button>
          ${t.isAdmin ? A`<button class="btn danger" ?disabled=${this._busy} @click=${() => this._confirmClear = !0}>
                ${U(e, "log.clear")}
              </button>` : M}
        </div>
        <div class="card-bd">
          ${this._error ? A`<div class="problems" role="alert">${this._error}</div>` : M}
          ${this._confirmClear ? A`<div class="problems" role="alert">
                <p>${U(e, "log.clear_confirm")}</p>
                <div class="actions">
                  <button class="btn danger" @click=${this._clear}>
                    ${U(e, "log.clear_yes")}
                  </button>
                  <button class="btn" @click=${() => this._confirmClear = !1}>
                    ${U(e, "common.cancel")}
                  </button>
                </div>
              </div>` : M}
          ${n === 0 ? A`<p class="hint">${U(e, this._busy ? "common.loading" : "log.empty")}</p>` : A`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${U(e, "log.time")}</th>
                      <th>${U(e, "log.event")}</th>
                      <th>${U(e, "log.category")}</th>
                      <th>${U(e, "log.where")}</th>
                      <th>${U(e, "log.who")}</th>
                      <th>${U(e, "log.detail")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this._rows.map((t) => this._renderRow(e, t))}
                  </tbody>
                </table>
              </div>`}
          ${this._total > Q ? A`<div class="actions">
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset === 0}
                  @click=${() => {
			this._offset = Math.max(0, this._offset - Q), this._load();
		}}
                >
                  ${U(e, "log.newer")}
                </button>
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset + Q >= this._total}
                  @click=${() => {
			this._offset += Q, this._load();
		}}
                >
                  ${U(e, "log.older")}
                </button>
              </div>` : M}
        </div>
      </div>
    `;
	}
	_renderRow(e, t) {
		let n = this.ctx, r = n.status.areas.find((e) => e.id === t.area_id), i = n.status.zones.find((e) => e.id === t.zone_id), a = this._open === t.id, o = [r?.name, i?.name].filter(Boolean).join(" · ");
		return A`
      <tr class="clickable" aria-selected=${a ? "true" : "false"} @click=${() => this._open = a ? void 0 : t.id}>
        <td class="mono">${new Date(t.ts).toLocaleString(n.hass.language)}</td>
        <td>
          <span class="state ${dt(t.severity)}">
            ${lt(e, t.event_type)}
          </span>
        </td>
        <td><span class="tag">${U(e, `category.${t.category}`)}</span></td>
        <td>${o}</td>
        <td>
          ${t.user_name ?? (t.channel ? ut(e, t.channel) : "")}
        </td>
        <td class="detail">${this._summary(e, t)}</td>
      </tr>
      ${a ? A`<tr class="expanded">
            <td colspan="6">
              <dl class="kv">
                ${t.incident_id ? A`<dt>${U(e, "log.incident")}</dt>
                      <dd>
                        <button
                          class="btn small"
                          @click=${(e) => {
			e.stopPropagation(), this._filter({ incident_id: t.incident_id });
		}}
                        >
                          ${U(e, "log.show_incident")}
                        </button>
                      </dd>` : M}
                ${t.outcome ? A`<dt>${U(e, "log.outcome")}</dt>
                      <dd>${U(e, `outcome.${t.outcome}`)}</dd>` : M}
                ${t.channel ? A`<dt>${U(e, "log.channel")}</dt>
                      <dd>${ut(e, t.channel)}</dd>` : M}
                <dt>${U(e, "log.detail")}</dt>
                <dd class="mono">${JSON.stringify(t.detail)}</dd>
              </dl>
            </td>
          </tr>` : M}
    `;
	}
	_summary(e, t) {
		let n = this.ctx, r = t.detail ?? {};
		if (typeof r.reason == "string") {
			let t = Array.isArray(r.blocking_zones) ? r.blocking_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? String(e)).join(", ") : "";
			return U(e, `reason.${r.reason}`, { zones: t });
		}
		return typeof r.error == "string" ? r.error : t.event_type === "zone_state" ? `${r.from ?? "?"} → ${r.to ?? "?"}` : t.event_type === "system_unavailable" && typeof r.down_since == "string" ? U(e, "log.gap", {
			from: new Date(r.down_since).toLocaleString(n.hass.language),
			to: new Date(String(r.up_at)).toLocaleString(n.hass.language)
		}) : typeof r.kind == "string" && t.category === "action" ? U(e, `action_kind.${r.kind}`) : "";
	}
	static {
		this.styles = [
			W,
			G,
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
function lt(e, t) {
	let n = U(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = U(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
function ut(e, t) {
	let n = U(e, `log_channel.${t}`);
	return n.startsWith("log_channel.") ? t : n;
}
function dt(e) {
	return e === "alarm" ? "triggered" : e === "warning" ? "arming" : "disarmed";
}
customElements.get("foyer-page-log") || customElements.define("foyer-page-log", ct);
//#endregion
//#region src/panel/pages/settings.ts
var ft = ["en", "it"], pt = {
	targets: [],
	mode: "sound",
	sound: null,
	tts_entity: null,
	volume: null,
	quiet_start: null,
	quiet_end: null,
	during_exit: !1
}, mt = class extends z {
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
		return this._draft ?? structuredClone(this.ctx?.config?.chime ?? pt);
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
		return e?.config ? A`${this._renderDefaults(e.strings)} ${this._renderResponse(e.strings)}
    ${this._renderChime(e.strings, this._chime)} ${this._renderLog(e.strings)}
    ${this._renderBackup(e.strings)} ${this._renderLanguage(e.strings)}` : M;
	}
	_entities(e) {
		return X(this.ctx.hass, e);
	}
	_renderDefaults(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.meta?.bounds ?? {}, i = (t, r, i) => A`<label class="field">
      <span class="lbl">${U(e, `field.${t}`)}</span>
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
      <span class="hint">${i ?? U(e, "common.seconds")}</span>
    </label>`;
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "settings.defaults_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${U(e, "settings.defaults_intro")}</p>
          <div class="grid-form">
            ${i("siren_duration", r.siren_duration, U(e, "settings.siren_duration_hint"))}
            ${i("arm_hold_timeout", r.arm_hold_timeout, U(e, "settings.arm_hold_hint"))}
            ${i("default_entry_delay", r.entry_delay, U(e, "settings.area_defaults_hint"))}
            ${i("default_exit_delay", r.exit_delay, U(e, "settings.area_defaults_hint"))}
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
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "settings.log_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${U(e, "settings.log_intro")}</p>
          <div class="rows">
            ${r.map((t) => {
			let r = n.enabled[t] !== !1;
			return A`<div class="row">
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${r}
                    @change=${(e) => o({ enabled: { [t]: e.target.checked } })}
                  />
                  <span>${U(e, `category.${t}`)}</span>
                </label>
                <span class="spacer"></span>
                ${r ? A`<label class="field inline">
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
                      <span class="hint">${U(e, "settings.log_days")}</span>
                    </label>` : A`<span class="hint">${U(e, "settings.log_off")}</span>`}
              </div>`;
		})}
          </div>
          <p class="hint">${U(e, "settings.log_rows_hint")}</p>
        </div>
      </div>
    `;
	}
	_renderBackup(e) {
		let t = (this.ctx.meta?.schema_version ?? []).join(".");
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "settings.backup_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${U(e, "settings.backup_intro")}</p>
          <div class="actions">
            <button class="btn" ?disabled=${this._busy} @click=${this._exportConfig}>
              ${U(e, "settings.backup_export")}
            </button>
            <label class="btn file">
              ${U(e, "settings.backup_import")}
              <input type="file" accept="application/json,.json" @change=${this._importConfig} />
            </label>
          </div>
          <p class="hint">${U(e, "settings.backup_hint")}</p>
          <p class="hint">${U(e, "settings.backup_version", { version: t })}</p>
          ${this._restored ? A`<div class="notice">${U(e, "settings.backup_restored")}</div>` : M}
        </div>
      </div>
    `;
	}
	async _exportConfig() {
		if (this.ctx) {
			this._busy = !0;
			try {
				let e = await this.ctx.exportConfig();
				Pe(e.filename, JSON.stringify(e.document, null, 2), "application/json");
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
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "settings.language_title")}</h2></div>
        <div class="card-bd">
          <label class="field">
            <span class="lbl">${U(e, "field.language")}</span>
            <select
              @change=${(e) => this._saveSettings({ language: e.target.value || null })}
            >
              <option value="" ?selected=${!n.language}>
                ${U(e, "settings.language_system")}
              </option>
              ${ft.map((t) => A`<option .value=${t} ?selected=${t === n.language}>
                    ${U(e, `language.${t}`)}
                  </option>`)}
            </select>
            <span class="hint">${U(e, "settings.language_hint")}</span>
          </label>
          ${this._problems.length ? A`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => A`<li>${K(e, t)}</li>`)}
                </ul>
              </div>` : M}
        </div>
      </div>
    `;
	}
	_renderResponse(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.config.profiles ?? [], i = t.meta?.silenceable ?? [], a = (t, i) => A`<label class="field">
        <span class="lbl">${U(e, `field.${t}`)}</span>
        <select
          @change=${(e) => this._saveSettings({ [t]: e.target.value || null })}
        >
          <option value="" ?selected=${!n[t]}>${U(e, "settings.none")}</option>
          ${r.map((e) => A`<option .value=${e.id ?? ""} ?selected=${e.id === n[t]}>
                ${e.name}
              </option>`)}
        </select>
        <span class="hint">${i}</span>
      </label>`;
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "settings.response_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${U(e, "settings.response_intro")}</p>
          <div class="grid-form">
            ${a("default_profile_id", U(e, "settings.default_profile_hint"))}
            ${a("technical_profile_id", U(e, "settings.technical_profile_hint"))}
            <label class="field">
              <span class="lbl">${U(e, "field.camera_dir")}</span>
              <input
                .value=${n.camera_dir}
                @change=${(e) => this._saveSettings({ camera_dir: e.target.value.trim() })}
              />
              <span class="hint">${U(e, "settings.camera_dir_hint")}</span>
            </label>
          </div>
          <fieldset>
            <legend>${U(e, "field.silent_suppresses")}</legend>
            ${i.map((t) => A`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${n.silent_suppresses.includes(t)}
                    @change=${(e) => {
			let r = e.target.checked ? [...n.silent_suppresses, t] : n.silent_suppresses.filter((e) => e !== t);
			this._saveSettings({ silent_suppresses: r });
		}}
                  />
                  <span
                    >${t === "chime" ? U(e, "settings.chime_title") : U(e, `action_kind.${t}`)}</span
                  >
                </label>`)}
            <p class="hint">${U(e, "settings.silent_hint")}</p>
          </fieldset>
        </div>
      </div>
    `;
	}
	_renderChime(e, t) {
		let n = this.ctx, r = $e(n.hass, n.meta?.chime_domains ?? [
			"media_player",
			"siren",
			"notify"
		]);
		for (let e of t.targets) r.some((t) => t.id === e.entity_id) || r.push({
			id: e.entity_id,
			name: e.entity_id
		});
		let i = this._entities(["tts"]), a = (e) => (t) => this._set(e, t.target.value || null);
		return A`
      <div class="card">
        <div class="card-hd"><h2>${U(e, "settings.chime_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${U(e, "settings.chime_intro")}</p>
          <fieldset>
            <legend>${U(e, "field.targets")}</legend>
            ${r.length ? r.map((t) => this._renderTarget(e, t)) : A`<p class="hint">${U(e, "settings.no_targets")}</p>`}
            <p class="hint">${U(e, "settings.targets_hint")}</p>
          </fieldset>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${U(e, "field.mode")}</span>
              <select
                @change=${(e) => this._set("mode", e.target.value)}
              >
                ${["sound", "speech"].map((n) => A`<option .value=${n} ?selected=${n === t.mode}>
                      ${U(e, `chime_mode.${n}`)}
                    </option>`)}
              </select>
            </label>
            ${t.mode === "speech" ? A`<label class="field">
                    <span class="lbl">${U(e, "field.tts_entity")}</span>
                    <select
                      @change=${(e) => this._set("tts_entity", e.target.value || null)}
                    >
                      <option value="" ?selected=${!t.tts_entity}>
                        ${U(e, "settings.pick_tts")}
                      </option>
                      ${i.map((e) => A`<option .value=${e.id} ?selected=${e.id === t.tts_entity}>
                            ${e.name}
                          </option>`)}
                    </select>
                    <span class="hint">${U(e, "settings.tts_hint")}</span>
                  </label>` : A`<label class="field">
                    <span class="lbl">${U(e, "field.sound")}</span>
                    <input
                      .value=${t.sound ?? ""}
                      @input=${(e) => this._set("sound", e.target.value.trim() || null)}
                    />
                    <span class="hint">${U(e, "settings.sound_hint")}</span>
                  </label>`}
            <label class="field">
              <span class="lbl">${U(e, "field.volume")}</span>
              <input
                type="number"
                min="0"
                max="100"
                .value=${t.volume == null ? "" : String(t.volume)}
                @input=${(e) => this._set("volume", q(e.target.value))}
              />
              <span class="hint">${U(e, "settings.volume_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.quiet_start")}</span>
              <input type="time" .value=${t.quiet_start ?? ""} @input=${a("quiet_start")} />
            </label>
            <label class="field">
              <span class="lbl">${U(e, "field.quiet_end")}</span>
              <input type="time" .value=${t.quiet_end ?? ""} @input=${a("quiet_end")} />
              <span class="hint">${U(e, "settings.quiet_hint")}</span>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${t.during_exit}
              @change=${(e) => this._set("during_exit", e.target.checked)}
            />
            <span>
              ${U(e, "field.during_exit")}
              <span class="hint">${U(e, "settings.during_exit_hint")}</span>
            </span>
          </label>
          <p class="hint">${U(e, "settings.switch_hint")}</p>
          ${this._problems.length ? A`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((t) => A`<li>${K(e, t)}</li>`)}
                  </ul>
                </div>` : M}
          ${this._saved ? A`<div class="notice">${U(e, "settings.saved")}</div>` : M}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${U(e, "common.save")}
            </button>
            <button
              class="btn"
              ?disabled=${this._busy || !this._draft}
              @click=${() => {
			this._draft = void 0, this._problems = [];
		}}
            >
              ${U(e, "common.cancel")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderTarget(e, t) {
		let n = this._target(t.id), r = (e) => (n) => this._setTarget(t.id, { [e]: n.target.value || null });
		return A`<div class="target">
      <label class="check">
        <input
          type="checkbox"
          .checked=${!!n}
          @change=${(e) => this._toggleTarget(t.id, e.target.checked)}
        />
        <span>
          ${t.name === t.id ? t.id : U(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}
        </span>
      </label>
      ${n ? A`<label class="field inline">
                <span class="lbl">${U(e, "field.quiet_start")}</span>
                <input
                  type="time"
                  .value=${n.quiet_start ?? ""}
                  @input=${r("quiet_start")}
                />
              </label>
              <label class="field inline">
                <span class="lbl">${U(e, "field.quiet_end")}</span>
                <input type="time" .value=${n.quiet_end ?? ""} @input=${r("quiet_end")} />
              </label>` : M}
    </div>`;
	}
	static {
		this.styles = [G, o`
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
customElements.get("foyer-page-settings") || customElements.define("foyer-page-settings", mt);
//#endregion
//#region src/panel/wizard.ts
var $ = [
	"area",
	"zones",
	"scenario",
	"user",
	"test"
], ht = 3, gt = class extends z {
	constructor(...e) {
		super(...e), this._step = "area", this._busy = !1, this._problems = [], this._confirmed = !1, this._pickedEntity = "", this._notifyTarget = "", this._sent = !1;
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
			_sent: { state: !0 }
		};
	}
	get _area() {
		return this.ctx?.config?.areas[0];
	}
	_next() {
		let e = $.indexOf(this._step);
		this._problems = [], e < $.length - 1 && (this._step = $[e + 1]);
	}
	_back() {
		let e = $.indexOf(this._step);
		this._problems = [], e > 0 && (this._step = $[e - 1]);
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
		if (!e?.config) return M;
		let t = e.strings;
		return A`
      <section class="wizard">
        <header>
          <h2>${U(t, "wizard.title")}</h2>
          <button class="btn" ?disabled=${this._busy} @click=${this._finish}>
            ${U(t, "wizard.dismiss")}
          </button>
        </header>
        <p class="intro">${U(t, "wizard.intro")}</p>
        <ol class="steps">
          ${$.map((e, n) => {
			let r = $.indexOf(this._step);
			return A`<li class=${n < r ? "done" : n === r ? "active" : ""}>
              <span class="n">${n + 1}</span>${U(t, `wizard.step.${e}`)}
            </li>`;
		})}
        </ol>
        <div class="body">${this._renderStep(t)}</div>
        ${this._problems.length ? A`<div class="problems" role="alert">
              <ul>
                ${this._problems.map((e) => A`<li>${K(t, e)}</li>`)}
              </ul>
            </div>` : M}
        <div class="actions">
          <button
            class="btn"
            ?disabled=${this._busy || this._step === $[0]}
            @click=${this._back}
          >
            ${U(t, "wizard.back")}
          </button>
          <span class="spacer"></span>
          ${this._step === "test" ? A`<button class="btn primary" ?disabled=${this._busy} @click=${this._finish}>
                ${U(t, "wizard.done")}
              </button>` : A`<button class="btn primary" ?disabled=${this._busy} @click=${this._next}>
                ${U(t, "wizard.next")}
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
		if (!t) return A`<p class="hint">${U(e, "wizard.no_area")}</p>`;
		let n = (e) => this._saveArea({
			...t,
			...e
		});
		return A`
      <p>${U(e, "wizard.area_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${U(e, "field.name")}</span>
          <input
            .value=${t.name}
            @change=${(e) => n({ name: e.target.value.trim() })}
          />
        </label>
        <label class="field">
          <span class="lbl">${U(e, "field.default_exit_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_exit_delay)}
            @change=${(e) => n({ default_exit_delay: Number(e.target.value) })}
          />
          <span class="hint">${U(e, "wizard.exit_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${U(e, "field.default_entry_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_entry_delay)}
            @change=${(e) => n({ default_entry_delay: Number(e.target.value) })}
          />
          <span class="hint">${U(e, "wizard.entry_hint")}</span>
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
		})).sort((e, t) => e.name.localeCompare(t.name)).slice(0, 200);
		return A`
      <p>${U(e, "wizard.zones_text", {
			have: n.length,
			want: ht
		})}</p>
      <ul class="zones">
        ${n.map((t) => A`<li>
            <strong>${t.name}</strong>
            <span class="mono">${t.entity_id}</span>
            <span class="tag">${U(e, `zone_type.${t.type}`)}</span>
          </li>`)}
      </ul>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${U(e, "wizard.add_zone")}</span>
          <select
            @change=${(e) => this._pick(e.target.value)}
          >
            <option value="" ?selected=${!this._pickedEntity}>${U(e, "wizard.pick_entity")}</option>
            ${a.map((e) => A`<option .value=${e.id} ?selected=${e.id === this._pickedEntity}>
                  ${e.name}
                </option>`)}
          </select>
        </label>
      </div>
      ${r ? A`
            <div class="proposal">
              <p>
                ${U(e, "wizard.proposed", {
			entity: r.entity_id,
			state: r.state ?? "",
			type: U(e, `zone_type.${r.zone_type ?? "instant"}`),
			states: r.proposed.join(", ")
		})}
              </p>
              <label class="check">
                <input
                  type="checkbox"
                  .checked=${this._confirmed}
                  @change=${(e) => this._confirmed = e.target.checked}
                />
                <span>${U(e, "wizard.confirm_trigger")}</span>
              </label>
              <p class="hint">${U(e, "wizard.confirm_hint")}</p>
              <button
                class="btn"
                ?disabled=${this._busy || !this._confirmed}
                @click=${this._addZone}
              >
                ${U(e, "wizard.add")}
              </button>
            </div>
          ` : M}
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
		if (!n) return A`<p class="hint">${U(e, "wizard.no_scenario")}</p>`;
		let r = t.config.areas;
		return A`
      <p>${U(e, "wizard.scenario_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${U(e, "field.name")}</span>
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
        ${U(e, "wizard.scenario_areas", { areas: r.filter((e) => n.areas.includes(e.id)).map((e) => e.name).join(", ") })}
      </p>
    `;
	}
	_renderUser(e) {
		return A`
      <p>${U(e, "wizard.user_text")}</p>
      <div class="notice">${U(e, "wizard.user_skipped")}</div>
    `;
	}
	_renderTest(e) {
		let t = this.ctx, n = Z(t.hass);
		return A`
      <p>${U(e, "wizard.test_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${U(e, "wizard.test_target")}</span>
          <select
            @change=${(e) => {
			this._notifyTarget = e.target.value, this._sent = !1;
		}}
          >
            <option value="" ?selected=${!this._notifyTarget}>${U(e, "wizard.pick_target")}</option>
            ${n.map((e) => A`<option .value=${e.id} ?selected=${e.id === this._notifyTarget}>
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
        ${U(e, "wizard.send_test")}
      </button>
      ${this._sent ? A`<div class="notice">${U(e, "wizard.test_sent")}</div>` : M}
      <p class="hint">${U(e, "wizard.test_hint")}</p>
    `;
	}
	async _sendTest() {
		let e = this.ctx;
		if (e && this._notifyTarget) {
			this._busy = !0, this._sent = !1;
			try {
				let t = U(e.strings, "wizard.test_message"), n = this._notifyTarget;
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
		this.styles = [G, o`
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
customElements.get("foyer-wizard") || customElements.define("foyer-wizard", gt);
//#endregion
//#region src/panel/foyer-panel.ts
var _t = [
	"overview",
	"areas",
	"zones",
	"scenarios",
	"profiles",
	"groups",
	"log",
	"settings"
], vt = [
	"areas",
	"zones",
	"scenarios",
	"profiles",
	"groups",
	"settings"
], yt = {
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
function bt(e) {
	return Object.fromEntries(Object.entries(e).filter(([, e]) => e != null && e !== "" && !(Array.isArray(e) && e.length === 0)));
}
var xt = class extends z {
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
		e.has("hass") && this.hass && (this.hass.language !== this._language && (this._language = this.hass.language, Ne(this.hass).then((e) => this._strings = e).catch((e) => this._error = String(e?.message ?? e))), !this._unsubscribe && this.isConnected && this._start());
	}
	get _isAdmin() {
		return !!this.hass?.user?.is_admin;
	}
	_start() {
		this.hass && !this._unsubscribe && (this._unsubscribe = this.hass.connection.subscribeMessage((e) => {
			this._offset = Date.parse(e.now) - Date.now(), this._status = e, this._error = void 0;
		}, { type: "foyer/subscribe" }), this._unsubscribe.catch((e) => {
			this._unsubscribe = void 0, this._error = e?.code === "not_loaded" ? U(this._strings, "common.not_loaded") : U(this._strings, "common.connection_error", { error: String(e?.message ?? e) });
		}), this.hass.callWS({ type: "foyer/prefs" }).then((e) => this._prefs = e).catch(() => void 0), this._isAdmin && this._loadConfig());
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
			now: () => Date.now() + this._offset,
			navigate: (e) => this._page = e,
			arm: (t) => e.callWS({
				type: "foyer/arm",
				...t
			}),
			disarm: (t) => e.callWS({
				type: "foyer/disarm",
				...t ? { area_ids: t } : {}
			}),
			acknowledge: (t) => e.callWS({
				type: "foyer/acknowledge",
				target: t
			}),
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
				...bt(t)
			}),
			exportLog: (t, n) => e.callWS({
				type: "foyer/log/export",
				format: n,
				...bt(t)
			}),
			clearLog: async () => await e.callWS({ type: "foyer/log/clear" }),
			exportConfig: () => e.callWS({ type: "foyer/config/export" }),
			importConfig: (e) => this._edit("config", {
				type: "foyer/config/import",
				document: e
			}),
			bypass: (t, n, r) => e.callWS({
				type: "foyer/bypass",
				zone_id: t,
				bypass: n,
				...r ? { seconds: r } : {}
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
			n = await this.hass.callWS(t);
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
		return A`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="symbol" aria-hidden="true"
          >${ke(Me(!!this.hass?.themes?.darkMode))}</span
        >
        <div class="title">${U(e, "common.brand")}</div>
        ${this._status ? A`<span class="live">${U(e, "common.live")}</span>` : M}
        <button
          class="help-toggle"
          aria-pressed=${t ? "false" : "true"}
          title=${U(e, "help.global_toggle")}
          aria-label=${U(e, "help.global_toggle")}
          @click=${() => this._savePrefs({ help_hidden: !t })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
        </button>
      </div>
      ${e ? this._renderTabs(e) : M}
      <main>${e ? this._renderBody(e) : M}</main>
    `;
	}
	_renderTabs(e) {
		let t = this._isAdmin ? _t : _t.filter((e) => !vt.includes(e));
		return t.length < 2 ? M : A`
      <nav class="tabs" role="tablist">
        ${t.map((t) => A`
            <button
              role="tab"
              aria-selected=${t === this._page ? "true" : "false"}
              @click=${() => this._page = t}
            >
              ${U(e, `nav.${t}`)}
            </button>
          `)}
      </nav>
    `;
	}
	_renderBody(e) {
		if (this._error) return A`<p class="error">${this._error}</p>`;
		let t = this._context();
		if (!t) return A`<p class="muted">${U(e, "common.loading")}</p>`;
		let n = this._page;
		return A`
      ${this._isAdmin && this._config && !this._config.settings.wizard_done ? A`<foyer-wizard
            .ctx=${t}
            @wizard-done=${() => void this._loadConfig()}
          ></foyer-wizard>` : M} ${this._prefs.help_hidden ? M : this._renderHelp(e, n)}
      ${this._renderPage(n, t)}
    `;
	}
	_renderPage(e, t) {
		switch (this._tick, e) {
			case "areas": return A`<foyer-page-areas .ctx=${t}></foyer-page-areas>`;
			case "zones": return A`<foyer-page-zones .ctx=${t}></foyer-page-zones>`;
			case "scenarios": return A`<foyer-page-scenarios .ctx=${t}></foyer-page-scenarios>`;
			case "profiles": return A`<foyer-page-profiles .ctx=${t}></foyer-page-profiles>`;
			case "groups": return A`<foyer-page-groups .ctx=${t}></foyer-page-groups>`;
			case "log": return A`<foyer-page-log .ctx=${t}></foyer-page-log>`;
			case "settings": return A`<foyer-page-settings .ctx=${t}></foyer-page-settings>`;
			default: return A`<foyer-page-overview .ctx=${t}></foyer-page-overview>`;
		}
	}
	_renderHelp(e, t) {
		let n = `help.${t}`, r = this._helpOpen(t);
		return A`
      <section class="help" ?data-open=${r}>
        <button
          class="help-hd"
          aria-expanded=${r ? "true" : "false"}
          @click=${() => this._savePrefs({ help: { [t]: !r } })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
          <span>${U(e, `${n}.title`)}</span>
          <span class="sr-only">${U(e, "help.toggle")}</span>
          <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon>
        </button>
        ${r ? A`<div class="help-body">
              <p>${U(e, `${n}.intro`)}</p>
              <dl>
                ${yt[t].map((t) => A`
                    <dt>${U(e, `${n}.items.${t}.term`)}</dt>
                    <dd>${U(e, `${n}.items.${t}.text`)}</dd>
                  `)}
              </dl>
            </div>` : M}
      </section>
    `;
	}
	static {
		this.styles = [
			W,
			G,
			o`
      :host {
        display: block;
        min-height: 100vh;
        background: var(--primary-background-color);
        color: var(--primary-text-color);
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
customElements.get("foyer-panel") || customElements.define("foyer-panel", xt);
//#endregion
