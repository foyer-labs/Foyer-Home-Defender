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
}, h = (e, t) => !l(e, t), g = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	useDefault: !1,
	hasChanged: h
};
Symbol.metadata ??= Symbol("metadata"), f.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var _ = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = g) {
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
		return this.elementProperties.get(e) ?? g;
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
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? h)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
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
_.elementStyles = [], _.shadowRootOptions = { mode: "open" }, _[p("elementProperties")] = /* @__PURE__ */ new Map(), _[p("finalized")] = /* @__PURE__ */ new Map(), ae?.({ ReactiveElement: _ }), (f.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
var v = globalThis, oe = (e) => e, y = v.trustedTypes, se = y ? y.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, ce = "$lit$", b = `lit$${Math.random().toFixed(9).slice(2)}$`, le = "?" + b, ue = `<${le}>`, x = document, S = () => x.createComment(""), C = (e) => e === null || typeof e != "object" && typeof e != "function", w = Array.isArray, de = (e) => w(e) || typeof e?.[Symbol.iterator] == "function", T = "[ 	\n\f\r]", E = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, D = /-->/g, O = />/g, k = RegExp(`>|${T}(?:([^\\s"'>=/]+)(${T}*=${T}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), A = /'/g, j = /"/g, M = /^(?:script|style|textarea|title)$/i, N = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), P = Symbol.for("lit-noChange"), F = Symbol.for("lit-nothing"), I = /* @__PURE__ */ new WeakMap(), L = x.createTreeWalker(x, 129);
function R(e, t) {
	if (!w(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return se === void 0 ? t : se.createHTML(t);
}
var fe = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = E;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === E ? c[1] === "!--" ? o = D : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = k) : (M.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = k) : o = O : o === k ? c[0] === ">" ? (o = i ?? E, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? k : c[3] === "\"" ? j : A) : o === j || o === A ? o = k : o === D || o === O ? o = E : (o = k, i = void 0);
		let d = o === k && e[t + 1].startsWith("/>") ? " " : "";
		a += o === E ? n + ue : l >= 0 ? (r.push(s), n.slice(0, l) + ce + n.slice(l) + b + d) : n + b + (l === -2 ? t : d);
	}
	return [R(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, z = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = fe(t, n);
		if (this.el = e.createElement(l, r), L.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = L.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(ce)) {
					let t = u[o++], n = i.getAttribute(e).split(b), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? me : r[1] === "?" ? he : r[1] === "@" ? ge : H
					}), i.removeAttribute(e);
				} else e.startsWith(b) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (M.test(i.tagName)) {
					let e = i.textContent.split(b), t = e.length - 1;
					if (t > 0) {
						i.textContent = y ? y.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], S()), L.nextNode(), c.push({
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
function B(e, t, n = e, r) {
	if (t === P) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = C(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = B(e, i._$AS(e, t.values), i, r)), t;
}
var pe = class {
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
		L.currentNode = r;
		let i = L.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new V(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new _e(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = L.nextNode(), a++);
		}
		return L.currentNode = x, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, V = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = F, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = B(this, e, t), C(e) ? e === F || e == null || e === "" ? (this._$AH !== F && this._$AR(), this._$AH = F) : e !== this._$AH && e !== P && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? de(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== F && C(this._$AH) ? this._$AA.nextSibling.data = e : this.T(x.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = z.createElement(R(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new pe(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = I.get(e.strings);
		return t === void 0 && I.set(e.strings, t = new z(e)), t;
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
}, H = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = F, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = F;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = B(this, e, t, 0), a = !C(e) || e !== this._$AH && e !== P, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = B(this, r[n + o], t, o), s === P && (s = this._$AH[o]), a ||= !C(s) || s !== this._$AH[o], s === F ? e = F : e !== F && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === F ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, me = class extends H {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === F ? void 0 : e;
	}
}, he = class extends H {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== F);
	}
}, ge = class extends H {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = B(this, e, t, 0) ?? F) === P) return;
		let n = this._$AH, r = e === F && n !== F || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== F && (n === F || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, _e = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		B(this, e);
	}
}, ve = v.litHtmlPolyfillSupport;
ve?.(z, V), (v.litHtmlVersions ??= []).push("3.3.3");
var ye = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new V(t.insertBefore(S(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, U = globalThis, W = class extends _ {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = ye(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return P;
	}
};
W._$litElement$ = !0, W.finalized = !0, U.litElementHydrateSupport?.({ LitElement: W });
var be = U.litElementPolyfillSupport;
be?.({ LitElement: W }), (U.litElementVersions ??= []).push("4.2.2");
//#endregion
//#region node_modules/lit-html/directive.js
var xe = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, Se = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), Ce = class {
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
}, G = class extends Ce {
	constructor(e) {
		if (super(e), this.it = F, e.type !== xe.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
	}
	render(e) {
		if (e === F || e == null) return this._t = void 0, this.it = e;
		if (e === P) return e;
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
G.directiveName = "unsafeHTML", G.resultType = 1;
//#endregion
//#region node_modules/lit-html/directives/unsafe-svg.js
var K = class extends G {};
K.directiveName = "unsafeSVG", K.resultType = 2;
var we = Se(K), Te = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n", Ee = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n";
//#endregion
//#region src/shared/brand.ts
function De(e) {
	return e ? Te : Ee;
}
//#endregion
//#region src/shared/i18n.ts
var q = /* @__PURE__ */ new Map();
function Oe(e) {
	let t = e.language, n = q.get(t);
	return n || (n = e.callWS({
		type: "foyer/translations",
		language: t
	}).then((e) => e.strings), n.catch(() => q.delete(t)), q.set(t, n)), n;
}
function J(e, t, n = {}) {
	let r = e;
	for (let e of t.split(".")) if (r && typeof r == "object" && e in r) r = r[e];
	else return t;
	return typeof r == "string" ? r.replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e) : t;
}
//#endregion
//#region src/shared/styles.ts
var Y = o`
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
`, X = o`
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
function ke(e, t) {
	return Math.max(0, Math.round((Date.parse(t) - e.now()) / 1e3));
}
function Ae(e, t) {
	let n = t.blocking_zones.map((e) => e.name).join(", ");
	return J(e, `reason.${t.reason ?? "unknown"}`, { zones: n });
}
function Z(e, t) {
	let n = t.field ? J(e, `field.${t.field}`) : "";
	return J(e, `problem.${t.code}`, { field: n });
}
function Q(e) {
	let t = e.trim();
	if (t === "") return null;
	let n = Number(t);
	return Number.isFinite(n) ? n : null;
}
//#endregion
//#region src/panel/pages/overview.ts
var je = /* @__PURE__ */ new Set(["zone_open", "zone_fault"]), Me = class extends W {
	constructor(...e) {
		super(...e), this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_busy: { state: !0 },
			_feedback: { state: !0 }
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
						text: J(n.strings, "overview.bypassed", { zones: e })
					} : void 0;
				} else this._feedback = {
					ok: !1,
					text: Ae(n.strings, r),
					retry: t && je.has(r.reason ?? "") ? t : void 0
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
	render() {
		let e = this.ctx;
		if (!e) return F;
		let t = e.strings, n = e.status, r = n.areas.filter((e) => e.memory);
		return N`
      <div class="notice" role="note">${J(t, "overview.no_codes_warning")}</div>
      ${r.map((e) => N`<div class="alarm-memory" role="alert">
          ${J(t, "overview.memory_banner", {
			area: e.name,
			zones: this._zoneNames(e.causes)
		})}
        </div>`)}
      ${this._renderMaster(t)} ${this._renderFeedback(t)}
      <div class="tiles">${n.areas.map((e) => this._renderArea(t, e))}</div>
      ${this._renderNotReady(t)}
    `;
	}
	_zoneNames(e) {
		let t = new Map(this.ctx.status.zones.map((e) => [e.id, e.name]));
		return e.map((e) => t.get(e) ?? e).join(", ");
	}
	_renderMaster(e) {
		let t = this.ctx.status, n = t.master, r = t.areas.some((e) => e.state !== "disarmed" || e.memory);
		return N`
      <div class="card">
        <div class="card-hd">
          <h2>${J(e, "overview.master")}</h2>
          <span class="state ${n.state}">${J(e, `state.${n.state}`)}</span>
          ${n.mode ? N`<span class="mono">${n.mode}</span>` : F}
        </div>
        <div class="card-bd">
          <div class="label">${J(e, "overview.scenario")}</div>
          <div class="chips">
            ${t.scenarios.length ? t.scenarios.map((e) => N`
                    <button
                      class="chip"
                      aria-pressed=${e.id === t.active_scenario_id ? "true" : "false"}
                      ?disabled=${this._busy}
                      @click=${() => this._arm({ scenario_id: e.id })}
                    >
                      ${e.name}
                    </button>
                  `) : N`<span class="muted">${J(e, "overview.no_scenarios")}</span>`}
          </div>
          <div class="hint">${J(e, "overview.scenario_hint")}</div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !r}
              @click=${() => this._disarm()}
            >
              ${J(e, "overview.disarm_all")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderFeedback(e) {
		let t = this._feedback;
		return t ? N`
      <div class=${t.ok ? "notice" : "problems"} role="alert">
        ${t.text}
        ${t.retry ? N`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._force(t.retry)}
              >
                ${J(e, "overview.force_arm")}
              </button>
              <span class="hint">${J(e, "overview.force_arm_hint")}</span>
            </div>` : F}
      </div>
    ` : F;
	}
	_renderArea(e, t) {
		let n = this.ctx, r = n.status.scenarios.find((e) => e.id === t.scenario_id);
		return N`
      <div class="card tile">
        <div class="card-bd">
          <div class="label">${J(e, "overview.area")}</div>
          <div class="name">${t.name}</div>
          <div class="row">
            <span class="state ${t.state}">${J(e, `state.${t.state}`)}</span>
            ${t.memory ? N`<span class="state memory">${J(e, "overview.memory")}</span>` : F}
          </div>
          ${t.timer && t.timer.kind !== "siren" ? N`<div class="countdown">
                ${J(e, `timer.${t.timer.kind}`, { seconds: ke(n, t.timer.due) })}
              </div>` : F}
          <div class="hint">
            ${t.state === "disarmed" ? F : r ? J(e, "overview.by_scenario", { scenario: r.name }) : J(e, "overview.on_its_own")}
          </div>
          <div class="actions">
            ${t.state === "disarmed" ? N`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._arm({ area_id: t.id })}
                >
                  ${J(e, "overview.arm_area")}
                </button>` : F}
            ${t.state !== "disarmed" || t.memory ? N`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._disarm([t.id])}
                >
                  ${J(e, "overview.disarm_area")}
                </button>` : F}
          </div>
        </div>
      </div>
    `;
	}
	_renderNotReady(e) {
		let t = this.ctx, n = new Map(t.status.areas.map((e) => [e.id, e.name])), r = t.status.zones.filter((e) => e.enabled && (e.fault || e.open || e.bypassed));
		return N`
      <div class="card">
        <div class="card-hd"><h2>${J(e, "overview.not_ready")}</h2></div>
        ${r.length ? N`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${J(e, "overview.zone")}</th>
                    <th>${J(e, "overview.area")}</th>
                    <th>${J(e, "overview.status")}</th>
                    <th>${J(e, "overview.entity_state")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${r.map((t) => N`<tr>
                      <td>${t.name}</td>
                      <td>${n.get(t.area_id) ?? ""}</td>
                      <td>${this._zoneStatus(e, t)}</td>
                      <td class="mono">${t.state ?? "—"}</td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : N`<div class="empty">${J(e, "overview.all_ready")}</div>`}
      </div>
    `;
	}
	_zoneStatus(e, t) {
		return t.fault ? N`<span class="state fault">${J(e, `fault.${t.fault}`)}</span>` : t.bypassed ? N`<span class="state bypassed">${J(e, `bypass.${t.bypassed}`)}</span>` : N`<span class="state open">${J(e, "zone_status.open")}</span>`;
	}
	static {
		this.styles = [
			Y,
			X,
			o`
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
    `
		];
	}
};
customElements.get("foyer-page-overview") || customElements.define("foyer-page-overview", Me);
//#endregion
//#region src/panel/pages/areas.ts
var Ne = {
	name: "",
	ha_state_when_armed: "armed_away",
	default_entry_delay: 30,
	default_exit_delay: 30
}, Pe = class extends W {
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
		this._draft = e ? { ...e } : { ...Ne }, this._problems = [];
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
		if (!e?.config) return F;
		let t = e.strings, n = new Map(e.status.areas.map((e) => [e.id, e.state])), r = (t) => e.config.zones.filter((e) => e.area_id === t).length;
		return N`
      <div class="card">
        <div class="card-hd">
          <h2>${J(t, "areas.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${J(t, "areas.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${J(t, "field.name")}</th>
                <th>${J(t, "overview.status")}</th>
                <th>${J(t, "areas.zones")}</th>
                <th>${J(t, "field.default_entry_delay")}</th>
                <th>${J(t, "field.default_exit_delay")}</th>
                <th>${J(t, "field.ha_state_when_armed")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.areas.map((e) => {
			let i = n.get(e.id ?? "") ?? "disarmed";
			return N`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td><span class="state ${i}">${J(t, `state.${i}`)}</span></td>
                  <td>${r(e.id)}</td>
                  <td>${J(t, "common.seconds", { n: e.default_entry_delay })}</td>
                  <td>${J(t, "common.seconds", { n: e.default_exit_delay })}</td>
                  <td class="mono">${e.ha_state_when_armed}</td>
                </tr>`;
		})}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : F}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx.meta, [r, i] = n?.bounds.exit_delay ?? [0, 300], a = n?.bounds.entry_delay?.[1] ?? 300;
		return N`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : J(e, "areas.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${J(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${J(e, "field.ha_state_when_armed")}</span>
              <select
                @change=${(e) => this._set("ha_state_when_armed", e.target.value)}
              >
                ${(n?.ha_states ?? []).map((n) => N`<option .value=${n} ?selected=${n === t.ha_state_when_armed}>
                      ${J(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${J(e, "areas.reports_as_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${J(e, "field.default_entry_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${a}
                .value=${String(t.default_entry_delay)}
                @input=${(e) => this._set("default_entry_delay", Number(e.target.value))}
              />
              <span class="hint">${J(e, "areas.entry_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${J(e, "field.default_exit_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.default_exit_delay)}
                @input=${(e) => this._set("default_exit_delay", Number(e.target.value))}
              />
              <span class="hint">${J(e, "areas.exit_hint")}</span>
            </label>
          </div>
          ${this._problems.length ? N`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => N`<li>${Z(e, t)}</li>`)}
                </ul>
              </div>` : F}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${J(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${J(e, "common.cancel")}
            </button>
            ${t.id ? N`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${J(e, "common.delete")}
                </button>` : F}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [Y, X];
	}
};
customElements.get("foyer-page-areas") || customElements.define("foyer-page-areas", Pe);
//#endregion
//#region src/panel/pages/zones.ts
var Fe = /* @__PURE__ */ new Set(["event", "tag"]), Ie = /* @__PURE__ */ new Set(["unavailable", "unknown"]);
function Le(e) {
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
		key: null
	};
}
var Re = (e, t) => JSON.stringify(e) === JSON.stringify(t), ze = class extends W {
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
		this._draft = e ? structuredClone(e) : Le(t), this._saved = e, this._proposal = void 0, this._confirmed = !1, this._problems = [], e && this._propose(e.entity_id, !1);
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
		}), n.channel !== "key" && (n.key = null), n.arm_policy !== "arm_after_closing" && (n.arm_hold_timeout = null), n.entry_mode !== "follower" && (n.follows = []), this._draft = n;
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
		return !this._saved || !Re(this._saved.trigger, this._draft?.trigger);
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
		if (!e?.config) return F;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.status.zones.map((e) => [e.id, e]));
		return e.config.areas.length ? N`
      <div class="card">
        <div class="card-hd">
          <h2>${J(t, "zones.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${J(t, "zones.add")}</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${J(t, "field.name")}</th>
                <th>${J(t, "field.entity_id")}</th>
                <th>${J(t, "field.area_id")}</th>
                <th>${J(t, "field.type")}</th>
                <th>${J(t, "field.arm_policy")}</th>
                <th>${J(t, "overview.status")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.zones.map((e) => N`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td class="mono">${e.entity_id}</td>
                  <td>${n.get(e.area_id) ?? ""}</td>
                  <td><span class="tag">${J(t, `zone_type.${e.type}`)}</span></td>
                  <td>${J(t, `arm_policy.${e.arm_policy}`)}</td>
                  <td>${this._health(t, r.get(e.id ?? ""))}</td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : F}
    ` : N`<div class="card"><div class="empty">${J(t, "zones.no_areas")}</div></div>`;
	}
	_health(e, t) {
		if (!t) return F;
		if (!t.enabled) return N`<span class="state disabled">${J(e, "zone_status.disabled")}</span>`;
		if (t.fault) return N`<span class="state fault">${J(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) return N`<span class="state bypassed">${J(e, `bypass.${t.bypassed}`)}</span>`;
		let n = t.open ? "open" : "closed";
		return N`<span class="state ${n}">${J(e, `zone_status.${n}`)}</span>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx;
		return N`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : J(e, "zones.new")}</h2>
        </div>
        <div class="card-bd">
          ${t.id ? F : this._renderEntityPicker(e, t)}
          ${t.entity_id ? N`
                ${this._renderTrigger(e, t)} ${this._renderProperties(e, t)}
                ${t.channel === "intrusion" && t.entry_mode === "follower" ? this._renderFollows(e, t) : F}
                ${t.channel === "key" ? this._renderKey(e, t) : F}
              ` : F}
          ${this._problems.length ? N`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => N`<li>${Z(e, t)}</li>`)}
                </ul>
              </div>` : F}
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !t.entity_id || this._triggerChanged() && !this._confirmed}
              @click=${this._save}
            >
              ${J(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${J(e, "common.cancel")}
            </button>
            ${t.id ? N`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${J(e, "common.delete")}
                </button>` : F}
          </div>
          ${this._triggerChanged() && !this._confirmed && t.entity_id ? N`<div class="hint">${J(e, "zones.confirm_first")}</div>` : F}
          ${n.status.areas.some((e) => e.id === t.area_id && e.state !== "disarmed") ? N`<div class="notice">${J(e, "zones.area_armed")}</div>` : F}
        </div>
      </div>
    `;
	}
	_renderEntityPicker(e, t) {
		let n = this.ctx, r = new Set(n.meta?.zone_domains ?? []), i = new Set(n.config?.zones.map((e) => e.entity_id)), a = this._filter.toLowerCase(), o = Object.values(n.hass.states).filter((e) => r.has(e.entity_id.split(".")[0])).filter((e) => {
			let t = String(e.attributes.friendly_name ?? "");
			return !a || e.entity_id.toLowerCase().includes(a) || t.toLowerCase().includes(a);
		}).sort((e, t) => e.entity_id.localeCompare(t.entity_id)).slice(0, 200);
		return N`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${J(e, "zones.search")}</span>
          <input
            .value=${this._filter}
            @input=${(e) => this._filter = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${J(e, "field.entity_id")}</span>
          <select
            @change=${(e) => this._propose(e.target.value, !0)}
          >
            <option value="" ?selected=${!t.entity_id}>${J(e, "zones.pick_entity")}</option>
            ${o.map((n) => N`<option
                .value=${n.entity_id}
                ?selected=${n.entity_id === t.entity_id}
              >
                ${J(e, i.has(n.entity_id) ? "zones.entity_used" : "zones.entity", {
			name: String(n.attributes.friendly_name ?? n.entity_id),
			entity: n.entity_id
		})}
              </option>`)}
          </select>
          <span class="hint">${J(e, "zones.entity_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderTrigger(e, t) {
		let n = this.ctx.hass.states[t.entity_id], r = n?.state ?? "unavailable", i = t.entity_id.split(".")[0], a = t.trigger;
		return N`
      <fieldset>
        <legend>${J(e, "zones.trigger_title")}</legend>
        <p class="hint">
          ${J(e, "zones.trigger_intro", {
			entity: String(n?.attributes.friendly_name ?? t.entity_id),
			state: r
		})}
          ${this._proposal?.device_class ? J(e, "zones.device_class", { device_class: this._proposal.device_class }) : F}
        </p>
        ${Fe.has(i) ? this._renderEventTrigger(e, i, a) : N`
              <label class="field">
                <span class="lbl">${J(e, "zones.trigger_kind")}</span>
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
                    ${J(e, "zones.kind_state")}
                  </option>
                  <option value="numeric" ?selected=${a.kind === "numeric"}>
                    ${J(e, "zones.kind_numeric")}
                  </option>
                </select>
              </label>
              ${a.kind === "numeric" ? this._renderNumericTrigger(e, a) : a.kind === "state" ? this._renderStateTrigger(e, a.states, r) : F}
            `}
        <label class="check confirm">
          <input
            type="checkbox"
            .checked=${this._confirmed || !this._triggerChanged()}
            ?disabled=${!this._triggerChanged()}
            @change=${(e) => this._confirmed = e.target.checked}
          />
          <span>
            ${J(e, "zones.confirm")}
            <span class="hint">${J(e, "zones.confirm_hint")}</span>
          </span>
        </label>
      </fieldset>
    `;
	}
	_renderStateTrigger(e, t, n) {
		let r = /* @__PURE__ */ new Set([...this._proposal?.options ?? [], ...t]);
		Ie.has(n) || r.add(n);
		let i = (e, n) => {
			let r = n ? [...t, e] : t.filter((t) => t !== e);
			this._set("trigger", {
				kind: "state",
				states: [...new Set(r)].sort()
			});
		};
		return N`
      <div class="states">
        ${[...r].map((r) => N`<label class="check">
            <input
              type="checkbox"
              .checked=${t.includes(r)}
              @change=${(e) => i(r, e.target.checked)}
            />
            <span class="mono">${r}</span>
            ${r === n ? N`<span class="tag">${J(e, "zones.now")}</span>` : F}
          </label>`)}
      </div>
      <div class="row">
        <label class="field">
          <span class="lbl">${J(e, "zones.other_state")}</span>
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
          ${J(e, "zones.add_state")}
        </button>
      </div>
      <div class="hint">${J(e, "zones.state_hint")}</div>
    `;
	}
	_renderNumericTrigger(e, t) {
		let n = (e) => this._set("trigger", {
			...t,
			...e
		});
		return N`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${J(e, "zones.operator")}</span>
          <select
            @change=${(e) => n({ operator: e.target.value })}
          >
            ${[
			"gt",
			"lt",
			"eq"
		].map((n) => N`<option .value=${n} ?selected=${n === t.operator}>
                  ${J(e, `operator.${n}`)}
                </option>`)}
          </select>
        </label>
        <label class="field">
          <span class="lbl">${J(e, "zones.threshold")}</span>
          <input
            type="number"
            step="any"
            .value=${String(t.value)}
            @input=${(e) => n({ value: Number(e.target.value) })}
          />
        </label>
        <label class="field">
          <span class="lbl">${J(e, "zones.hysteresis")}</span>
          <input
            type="number"
            step="any"
            min="0"
            ?disabled=${t.operator === "eq"}
            .value=${String(t.hysteresis)}
            @input=${(e) => n({ hysteresis: Number(e.target.value) })}
          />
          <span class="hint">${J(e, "zones.hysteresis_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${J(e, "zones.attribute")}</span>
          <input
            .value=${t.attribute ?? ""}
            @input=${(e) => n({ attribute: e.target.value.trim() || null })}
          />
          <span class="hint">${J(e, "zones.attribute_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderEventTrigger(e, t, n) {
		if (t === "tag") return N`<p class="hint">${J(e, "zones.tag_hint")}</p>`;
		let r = n.kind === "event" ? n.event_type : null;
		return N`
      <label class="field">
        <span class="lbl">${J(e, "zones.event_type")}</span>
        <select
          @change=${(e) => this._set("trigger", {
			kind: "event",
			event_type: e.target.value || null
		})}
        >
          <option value="" ?selected=${!r}>${J(e, "zones.pick_event")}</option>
          ${(this._proposal?.options ?? []).map((e) => N`<option .value=${e} ?selected=${e === r}>${e}</option>`)}
        </select>
        <span class="hint">${J(e, "zones.event_hint")}</span>
      </label>
    `;
	}
	_renderProperties(e, t) {
		let n = this.ctx, r = n.meta, i = n.config?.areas.find((e) => e.id === t.area_id), a = t.channel === "intrusion", o = (n, r) => N`
      <label class="check">
        <input
          type="checkbox"
          .checked=${!!t[n]}
          @change=${(e) => this._set(n, e.target.checked)}
        />
        <span>
          ${J(e, `field.${n}`)}
          ${r ? N`<span class="hint">${J(e, r)}</span>` : F}
        </span>
      </label>
    `;
		return N`
      <fieldset>
        <legend>${J(e, "zones.properties_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${J(e, "field.name")}</span>
            <input
              .value=${t.name}
              @input=${(e) => this._set("name", e.target.value)}
            />
          </label>
          <label class="field">
            <span class="lbl">${J(e, "field.type")}</span>
            <select @change=${(e) => this._applyType(e.target.value)}>
              ${(r?.zone_types ?? []).map((n) => N`<option
                  .value=${n.type}
                  ?selected=${n.type === t.type}
                  ?disabled=${!n.available}
                >
                  ${J(e, n.available ? `zone_type.${n.type}` : "zones.type_unavailable", { type: J(e, `zone_type.${n.type}`) })}
                </option>`)}
            </select>
            <span class="hint">${J(e, "zones.type_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${J(e, "field.area_id")}</span>
            <select
              @change=${(e) => this._set("area_id", e.target.value)}
            >
              ${(n.config?.areas ?? []).map((e) => N`<option .value=${e.id ?? ""} ?selected=${e.id === t.area_id}>
                    ${e.name}
                  </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${J(e, "field.channel")}</span>
            <select
              @change=${(e) => {
			let n = e.target.value;
			this._set("channel", n), this._set("key", n === "key" ? t.key ?? {
				on_activate: "toggle",
				scenario_id: null,
				on_deactivate: "none"
			} : null);
		}}
            >
              ${[
			"intrusion",
			"key",
			"technical"
		].map((n) => N`<option
                    .value=${n}
                    ?selected=${n === t.channel}
                    ?disabled=${n === "technical"}
                  >
                    ${J(e, `channel.${n}`)}
                  </option>`)}
            </select>
          </label>
          ${a ? N`
                <label class="field">
                  <span class="lbl">${J(e, "field.entry_mode")}</span>
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
		].map((n) => N`<option .value=${n} ?selected=${n === t.entry_mode}>
                          ${J(e, `entry_mode.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${J(e, `entry_mode_hint.${t.entry_mode}`)}</span>
                </label>
                <label class="field">
                  <span class="lbl">${J(e, "field.entry_delay")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${r?.bounds.entry_delay?.[1] ?? 300}
                    placeholder=${J(e, "zones.inherit_seconds", { n: i?.default_entry_delay ?? 30 })}
                    .value=${t.entry_delay == null ? "" : String(t.entry_delay)}
                    @input=${(e) => this._set("entry_delay", Q(e.target.value))}
                  />
                  <span class="hint">${J(e, "zones.entry_delay_hint")}</span>
                </label>
                <label class="field">
                  <span class="lbl">${J(e, "field.alarm_kind")}</span>
                  <select
                    @change=${(e) => this._set("alarm_kind", e.target.value)}
                  >
                    ${[
			"intrusion",
			"tamper",
			"panic"
		].map((n) => N`<option .value=${n} ?selected=${n === t.alarm_kind}>
                          ${J(e, `alarm_kind.${n}`)}
                        </option>`)}
                  </select>
                </label>
                <label class="field">
                  <span class="lbl">${J(e, "field.arm_policy")}</span>
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
		].map((n) => N`<option .value=${n} ?selected=${n === t.arm_policy}>
                          ${J(e, `arm_policy.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${J(e, `arm_policy_hint.${t.arm_policy}`)}</span>
                </label>
                ${t.arm_policy === "arm_after_closing" ? N`<label class="field">
                      <span class="lbl">${J(e, "field.arm_hold_timeout")}</span>
                      <input
                        type="number"
                        min=${r?.bounds.arm_hold_timeout?.[0] ?? 60}
                        max=${r?.bounds.arm_hold_timeout?.[1] ?? 1800}
                        placeholder=${J(e, "zones.inherit_seconds", { n: n.config?.settings.arm_hold_timeout ?? 300 })}
                        .value=${t.arm_hold_timeout == null ? "" : String(t.arm_hold_timeout)}
                        @input=${(e) => this._set("arm_hold_timeout", Q(e.target.value))}
                      />
                      <span class="hint">${J(e, "zones.hold_hint")}</span>
                    </label>` : F}
              ` : F}
          <label class="field">
            <span class="lbl">${J(e, "field.supervision_timeout")}</span>
            <input
              type="number"
              min=${r?.bounds.supervision_timeout?.[0] ?? 60}
              placeholder=${J(e, "zones.off")}
              .value=${t.supervision_timeout == null ? "" : String(t.supervision_timeout)}
              @input=${(e) => this._set("supervision_timeout", Q(e.target.value))}
            />
            <span class="hint">${J(e, "zones.supervision_hint")}</span>
          </label>
        </div>
        <div class="checks">
          ${a ? o("always_on", "zones.always_on_hint") : F}
          ${a ? o("bypassable", "zones.bypassable_hint") : F}
          ${o("allow_arm_when_faulted", "zones.allow_faulted_hint")}
          ${o("enabled", "zones.enabled_hint")}
        </div>
      </fieldset>
    `;
	}
	_renderFollows(e, t) {
		let n = new Map(this.ctx?.config?.areas.map((e) => [e.id, e.name])), r = (this.ctx?.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && e.entry_mode === "delayed"), i = (e, n) => this._set("follows", n ? [.../* @__PURE__ */ new Set([...t.follows, e])] : t.follows.filter((t) => t !== e));
		return N`
      <fieldset>
        <legend>${J(e, "field.follows")}</legend>
        ${r.length ? r.map((r) => N`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.follows.includes(r.id ?? "")}
                  @change=${(e) => i(r.id ?? "", e.target.checked)}
                />
                <span>
                  ${J(e, "zones.entity", {
			name: r.name,
			entity: n.get(r.area_id) ?? r.area_id
		})}
                </span>
              </label>`) : N`<p class="hint">${J(e, "zones.no_delayed_zones")}</p>`}
        <p class="hint">${J(e, "zones.follows_hint")}</p>
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
		return N`
      <fieldset>
        <legend>${J(e, "zones.key_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${J(e, "field.on_activate")}</span>
            <select
              @change=${(e) => r({ on_activate: e.target.value })}
            >
              ${[
			"arm",
			"disarm",
			"toggle"
		].map((t) => N`<option .value=${t} ?selected=${t === n.on_activate}>
                    ${J(e, `key_command.${t}`)}
                  </option>`)}
            </select>
          </label>
          ${n.on_activate === "disarm" ? F : N`<label class="field">
                <span class="lbl">${J(e, "field.scenario_id")}</span>
                <select
                  @change=${(e) => r({ scenario_id: e.target.value || null })}
                >
                  <option value="" ?selected=${!n.scenario_id}>
                    ${J(e, "zones.pick_scenario")}
                  </option>
                  ${i.map((e) => N`<option .value=${e.id ?? ""} ?selected=${e.id === n.scenario_id}>
                        ${e.name}
                      </option>`)}
                </select>
              </label>`}
          <label class="field">
            <span class="lbl">${J(e, "field.on_deactivate")}</span>
            <select
              @change=${(e) => r({ on_deactivate: e.target.value })}
            >
              ${["none", "disarm"].map((t) => N`<option .value=${t} ?selected=${t === n.on_deactivate}>
                    ${J(e, `key_release.${t}`)}
                  </option>`)}
            </select>
          </label>
        </div>
        <p class="hint">${J(e, "zones.key_hint")}</p>
      </fieldset>
    `;
	}
	static {
		this.styles = [
			Y,
			X,
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
customElements.get("foyer-page-zones") || customElements.define("foyer-page-zones", ze);
//#endregion
//#region src/panel/pages/scenarios.ts
var Be = {
	name: "",
	areas: [],
	ha_master_state: "armed_away",
	icon: null,
	exit_delay_override: null,
	siren_duration_override: null
}, Ve = class extends W {
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
			...Be,
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
		if (!e?.config) return F;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = e.config.scenarios.map((e) => e.ha_master_state);
		return N`
      <div class="card">
        <div class="card-hd">
          <h2>${J(t, "scenarios.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${J(t, "scenarios.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${J(t, "field.name")}</th>
                <th>${J(t, "field.areas")}</th>
                <th>${J(t, "field.ha_master_state")}</th>
                <th>${J(t, "field.exit_delay_override")}</th>
                <th>${J(t, "field.siren_duration_override")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.scenarios.map((i) => N`<tr
                  class="clickable"
                  aria-selected=${this._draft?.id === i.id ? "true" : "false"}
                  @click=${() => this._edit(i)}
                >
                  <td>
                    <strong>${i.name}</strong>
                    ${i.id === e.status.active_scenario_id ? N`<span class="state armed">${J(t, "scenarios.active")}</span>` : F}
                  </td>
                  <td>
                    ${i.areas.map((e) => N`<span class="tag">${n.get(e) ?? e}</span>`)}
                  </td>
                  <td>
                    <span class="mono">${i.ha_master_state}</span>
                    ${r.filter((e) => e === i.ha_master_state).length > 1 ? N`<div class="hint">${J(t, "scenarios.shared_mode")}</div>` : F}
                  </td>
                  <td>
                    ${i.exit_delay_override == null ? J(t, "scenarios.area_default") : J(t, "common.seconds", { n: i.exit_delay_override })}
                  </td>
                  <td>
                    ${i.siren_duration_override == null ? J(t, "scenarios.global_default") : J(t, "common.seconds", { n: i.siren_duration_override })}
                  </td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : F}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.meta, i = (e, n) => this._set("areas", n ? [...t.areas, e] : t.areas.filter((t) => t !== e));
		return N`
      <div class="card">
        <div class="card-hd">
          <h2>${t.id ? t.name : J(e, "scenarios.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${J(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${J(e, "field.ha_master_state")}</span>
              <select
                @change=${(e) => this._set("ha_master_state", e.target.value)}
              >
                ${(r?.ha_states ?? []).map((n) => N`<option .value=${n} ?selected=${n === t.ha_master_state}>
                      ${J(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${J(e, "scenarios.mode_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${J(e, "field.exit_delay_override")}</span>
              <input
                type="number"
                min="0"
                max=${r?.bounds.exit_delay?.[1] ?? 300}
                placeholder=${J(e, "scenarios.area_default")}
                .value=${t.exit_delay_override == null ? "" : String(t.exit_delay_override)}
                @input=${(e) => this._set("exit_delay_override", Q(e.target.value))}
              />
              <span class="hint">${J(e, "scenarios.exit_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${J(e, "field.siren_duration_override")}</span>
              <input
                type="number"
                min="1"
                max=${r?.bounds.siren_duration?.[1] ?? 900}
                placeholder=${J(e, "scenarios.global_seconds", { n: n.config?.settings.siren_duration ?? 180 })}
                .value=${t.siren_duration_override == null ? "" : String(t.siren_duration_override)}
                @input=${(e) => this._set("siren_duration_override", Q(e.target.value))}
              />
              <span class="hint">${J(e, "scenarios.siren_hint")}</span>
            </label>
          </div>
          <fieldset>
            <legend>${J(e, "field.areas")}</legend>
            ${(n.config?.areas ?? []).map((e) => N`<label class="check">
                <input
                  type="checkbox"
                  .checked=${t.areas.includes(e.id ?? "")}
                  @change=${(t) => i(e.id ?? "", t.target.checked)}
                />
                <span>${e.name}</span>
              </label>`)}
            <p class="hint">${J(e, "scenarios.areas_hint")}</p>
          </fieldset>
          ${this._problems.length ? N`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => N`<li>${Z(e, t)}</li>`)}
                </ul>
              </div>` : F}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${J(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${J(e, "common.cancel")}
            </button>
            ${t.id ? N`<button class="btn danger" ?disabled=${this._busy} @click=${this._delete}>
                  ${J(e, "common.delete")}
                </button>` : F}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			Y,
			X,
			o`
      td .state {
        margin-left: 8px;
      }
    `
		];
	}
};
customElements.get("foyer-page-scenarios") || customElements.define("foyer-page-scenarios", Ve);
//#endregion
//#region src/panel/foyer-panel.ts
var $ = [
	"overview",
	"areas",
	"zones",
	"scenarios"
], He = [
	"areas",
	"zones",
	"scenarios"
], Ue = {
	overview: [
		"area",
		"master",
		"scenario",
		"not_ready",
		"memory"
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
		"supervision"
	],
	scenarios: [
		"areas",
		"reports_master",
		"switching",
		"exit_override",
		"siren"
	]
}, We = class extends W {
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
		e.has("hass") && this.hass && (this.hass.language !== this._language && (this._language = this.hass.language, Oe(this.hass).then((e) => this._strings = e).catch((e) => this._error = String(e?.message ?? e))), !this._unsubscribe && this.isConnected && this._start());
	}
	get _isAdmin() {
		return !!this.hass?.user?.is_admin;
	}
	_start() {
		this.hass && !this._unsubscribe && (this._unsubscribe = this.hass.connection.subscribeMessage((e) => {
			this._offset = Date.parse(e.now) - Date.now(), this._status = e, this._error = void 0;
		}, { type: "foyer/subscribe" }), this._unsubscribe.catch((e) => {
			this._unsubscribe = void 0, this._error = e?.code === "not_loaded" ? J(this._strings, "common.not_loaded") : J(this._strings, "common.connection_error", { error: String(e?.message ?? e) });
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
			save: async (t, n, r = !1) => {
				let i = await e.callWS({
					type: "foyer/config/save",
					kind: t,
					item: n,
					trigger_confirmed: r
				});
				return i.success && await this._reloadConfigSoon(), i;
			},
			remove: async (t, n) => {
				let r = await e.callWS({
					type: "foyer/config/delete",
					kind: t,
					id: n
				});
				return r.success && await this._reloadConfigSoon(), r;
			}
		};
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
		return N`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="symbol" aria-hidden="true"
          >${we(De(!!this.hass?.themes?.darkMode))}</span
        >
        <div class="title">${J(e, "common.brand")}</div>
        ${this._status ? N`<span class="live">${J(e, "common.live")}</span>` : F}
        <button
          class="help-toggle"
          aria-pressed=${t ? "false" : "true"}
          title=${J(e, "help.global_toggle")}
          aria-label=${J(e, "help.global_toggle")}
          @click=${() => this._savePrefs({ help_hidden: !t })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
        </button>
      </div>
      ${e ? this._renderTabs(e) : F}
      <main>${e ? this._renderBody(e) : F}</main>
    `;
	}
	_renderTabs(e) {
		let t = this._isAdmin ? $ : $.filter((e) => !He.includes(e));
		return t.length < 2 ? F : N`
      <nav class="tabs" role="tablist">
        ${t.map((t) => N`
            <button
              role="tab"
              aria-selected=${t === this._page ? "true" : "false"}
              @click=${() => this._page = t}
            >
              ${J(e, `nav.${t}`)}
            </button>
          `)}
      </nav>
    `;
	}
	_renderBody(e) {
		if (this._error) return N`<p class="error">${this._error}</p>`;
		let t = this._context();
		if (!t) return N`<p class="muted">${J(e, "common.loading")}</p>`;
		let n = this._page;
		return N`
      ${this._prefs.help_hidden ? F : this._renderHelp(e, n)}
      ${this._renderPage(n, t)}
    `;
	}
	_renderPage(e, t) {
		switch (this._tick, e) {
			case "areas": return N`<foyer-page-areas .ctx=${t}></foyer-page-areas>`;
			case "zones": return N`<foyer-page-zones .ctx=${t}></foyer-page-zones>`;
			case "scenarios": return N`<foyer-page-scenarios .ctx=${t}></foyer-page-scenarios>`;
			default: return N`<foyer-page-overview .ctx=${t}></foyer-page-overview>`;
		}
	}
	_renderHelp(e, t) {
		let n = `help.${t}`, r = this._helpOpen(t);
		return N`
      <section class="help" ?data-open=${r}>
        <button
          class="help-hd"
          aria-expanded=${r ? "true" : "false"}
          @click=${() => this._savePrefs({ help: { [t]: !r } })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
          <span>${J(e, `${n}.title`)}</span>
          <span class="sr-only">${J(e, "help.toggle")}</span>
          <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon>
        </button>
        ${r ? N`<div class="help-body">
              <p>${J(e, `${n}.intro`)}</p>
              <dl>
                ${Ue[t].map((t) => N`
                    <dt>${J(e, `${n}.items.${t}.term`)}</dt>
                    <dd>${J(e, `${n}.items.${t}.text`)}</dd>
                  `)}
              </dl>
            </div>` : F}
      </section>
    `;
	}
	static {
		this.styles = [
			Y,
			X,
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
customElements.get("foyer-panel") || customElements.define("foyer-panel", We);
//#endregion
