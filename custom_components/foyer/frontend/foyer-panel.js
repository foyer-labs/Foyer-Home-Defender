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
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: f, getOwnPropertySymbols: ee, getPrototypeOf: te } = Object, p = globalThis, ne = p.trustedTypes, re = ne ? ne.emptyScript : "", ie = p.reactiveElementPolyfillSupport, m = (e, t) => e, ae = {
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
}, oe = (e, t) => !l(e, t), se = {
	attribute: !0,
	type: String,
	converter: ae,
	reflect: !1,
	useDefault: !1,
	hasChanged: oe
};
Symbol.metadata ??= Symbol("metadata"), p.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
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
			let i = (n.converter?.toAttribute === void 0 ? ae : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? ae : e.converter;
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
h.elementStyles = [], h.shadowRootOptions = { mode: "open" }, h[m("elementProperties")] = /* @__PURE__ */ new Map(), h[m("finalized")] = /* @__PURE__ */ new Map(), ie?.({ ReactiveElement: h }), (p.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
var ce = globalThis, le = (e) => e, g = ce.trustedTypes, ue = g ? g.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, de = "$lit$", _ = `lit$${Math.random().toFixed(9).slice(2)}$`, fe = "?" + _, pe = `<${fe}>`, v = document, y = () => v.createComment(""), b = (e) => e === null || typeof e != "object" && typeof e != "function", me = Array.isArray, he = (e) => me(e) || typeof e?.[Symbol.iterator] == "function", ge = "[ 	\n\f\r]", x = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, _e = /-->/g, ve = />/g, S = RegExp(`>|${ge}(?:([^\\s"'>=/]+)(${ge}*=${ge}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), ye = /'/g, be = /"/g, xe = /^(?:script|style|textarea|title)$/i, C = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), w = Symbol.for("lit-noChange"), T = Symbol.for("lit-nothing"), Se = /* @__PURE__ */ new WeakMap(), E = v.createTreeWalker(v, 129);
function Ce(e, t) {
	if (!me(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return ue === void 0 ? t : ue.createHTML(t);
}
var we = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = x;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === x ? c[1] === "!--" ? o = _e : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = S) : (xe.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = S) : o = ve : o === S ? c[0] === ">" ? (o = i ?? x, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? S : c[3] === "\"" ? be : ye) : o === be || o === ye ? o = S : o === _e || o === ve ? o = x : (o = S, i = void 0);
		let d = o === S && e[t + 1].startsWith("/>") ? " " : "";
		a += o === x ? n + pe : l >= 0 ? (r.push(s), n.slice(0, l) + de + n.slice(l) + _ + d) : n + _ + (l === -2 ? t : d);
	}
	return [Ce(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, Te = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = we(t, n);
		if (this.el = e.createElement(l, r), E.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = E.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(de)) {
					let t = u[o++], n = i.getAttribute(e).split(_), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? De : r[1] === "?" ? Oe : r[1] === "@" ? ke : k
					}), i.removeAttribute(e);
				} else e.startsWith(_) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (xe.test(i.tagName)) {
					let e = i.textContent.split(_), t = e.length - 1;
					if (t > 0) {
						i.textContent = g ? g.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], y()), E.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], y());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === fe) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(_, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += _.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = v.createElement("template");
		return n.innerHTML = e, n;
	}
};
function D(e, t, n = e, r) {
	if (t === w) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = b(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = D(e, i._$AS(e, t.values), i, r)), t;
}
var Ee = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? v).importNode(t, !0);
		E.currentNode = r;
		let i = E.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new O(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Ae(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = E.nextNode(), a++);
		}
		return E.currentNode = v, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, O = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = T, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = D(this, e, t), b(e) ? e === T || e == null || e === "" ? (this._$AH !== T && this._$AR(), this._$AH = T) : e !== this._$AH && e !== w && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? he(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== T && b(this._$AH) ? this._$AA.nextSibling.data = e : this.T(v.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = Te.createElement(Ce(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new Ee(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = Se.get(e.strings);
		return t === void 0 && Se.set(e.strings, t = new Te(e)), t;
	}
	k(t) {
		me(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(y()), this.O(y()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = le(e).nextSibling;
			le(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, k = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = T, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = T;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = D(this, e, t, 0), a = !b(e) || e !== this._$AH && e !== w, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = D(this, r[n + o], t, o), s === w && (s = this._$AH[o]), a ||= !b(s) || s !== this._$AH[o], s === T ? e = T : e !== T && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === T ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, De = class extends k {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === T ? void 0 : e;
	}
}, Oe = class extends k {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== T);
	}
}, ke = class extends k {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = D(this, e, t, 0) ?? T) === w) return;
		let n = this._$AH, r = e === T && n !== T || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== T && (n === T || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Ae = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		D(this, e);
	}
}, je = {
	M: de,
	P: _,
	A: fe,
	C: 1,
	L: we,
	R: Ee,
	D: he,
	V: D,
	I: O,
	H: k,
	N: Oe,
	U: ke,
	B: De,
	F: Ae
}, Me = ce.litHtmlPolyfillSupport;
Me?.(Te, O), (ce.litHtmlVersions ??= []).push("3.3.3");
var Ne = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new O(t.insertBefore(y(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, Pe = globalThis, A = class extends h {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ne(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return w;
	}
};
A._$litElement$ = !0, A.finalized = !0, Pe.litElementHydrateSupport?.({ LitElement: A });
var Fe = Pe.litElementPolyfillSupport;
Fe?.({ LitElement: A }), (Pe.litElementVersions ??= []).push("4.2.2");
//#endregion
//#region node_modules/lit-html/directive.js
var j = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, Ie = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), Le = class {
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
}, Re = class extends Le {
	constructor(e) {
		if (super(e), this.it = T, e.type !== j.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
	}
	render(e) {
		if (e === T || e == null) return this._t = void 0, this.it = e;
		if (e === w) return e;
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
Re.directiveName = "unsafeHTML", Re.resultType = 1;
//#endregion
//#region node_modules/lit-html/directives/unsafe-svg.js
var ze = class extends Re {};
ze.directiveName = "unsafeSVG", ze.resultType = 2;
var Be = Ie(ze), Ve = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#E8ECF2\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n", He = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"256\" height=\"256\" role=\"img\" aria-label=\"Foyer Home Defender\">\n  <title>Foyer Home Defender</title>\n  <path d=\"M32 5.5 L55 13.5 V32 C55 44 45 53.5 32 58.5 C19 53.5 9 44 9 32 V13.5 Z\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linejoin=\"round\"/>\n  <polyline points=\"19,32 32,21.5 45,32\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" opacity=\"0.5\"/>\n  <polyline points=\"24,38 32,31.5 40,38\" fill=\"none\" stroke=\"#0D1014\" stroke-width=\"3.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n  <rect x=\"28.5\" y=\"45.5\" width=\"7\" height=\"7\" fill=\"#F0A835\"/>\n  <circle cx=\"32\" cy=\"45.5\" r=\"3.5\" fill=\"#F0A835\"/>\n</svg>\n";
//#endregion
//#region src/shared/brand.ts
function Ue(e) {
	return e ? Ve : He;
}
//#endregion
//#region src/shared/i18n.ts
var We = /* @__PURE__ */ new Map();
function Ge(e) {
	let t = e.language, n = We.get(t);
	return n || (n = e.callWS({
		type: "foyer/translations",
		language: t
	}).then((e) => e.strings), n.catch(() => We.delete(t)), We.set(t, n)), n;
}
function M(e, t, n = {}) {
	let r = e;
	for (let e of t.split(".")) if (r && typeof r == "object" && e in r) r = r[e];
	else return t;
	return typeof r == "string" ? r.replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e) : t;
}
//#endregion
//#region src/shared/styles.ts
var N = o`
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
`, P = o`
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
function F(e, t = {}) {
	let n = e?.config?.time_zone;
	return n ? {
		...t,
		timeZone: n
	} : t;
}
function Ke(e) {
	let t = Math.max(0, Math.round(e));
	return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}
function qe(e, t = 0) {
	return Math.max(0, Math.round((Date.parse(e) - (Date.now() + t)) / 1e3));
}
//#endregion
//#region src/panel/context.ts
function Je(e, t, n) {
	let r = URL.createObjectURL(new Blob([t], { type: n })), i = document.createElement("a");
	i.href = r, i.download = e, i.click(), setTimeout(() => URL.revokeObjectURL(r), 1e3);
}
function I(e) {
	return e.status.areas.some((e) => e.state !== "disarmed");
}
function Ye(e, t) {
	return Math.max(0, Math.round((Date.parse(t) - e.now()) / 1e3));
}
function Xe(e, t, n) {
	let r = t.state?.security?.locked_until;
	if (t.reason === "locked_out" && r) return Ze(e, n, r);
	let i = (t.blocking_zones ?? []).map((e) => e.name).join(", ");
	return M(e, `reason.${t.reason ?? "unknown"}`, { zones: i });
}
function Ze(e, t, n) {
	return M(e, "code.locked_until", { time: new Date(n).toLocaleTimeString(t, {
		hour: "2-digit",
		minute: "2-digit"
	}) });
}
async function L(e) {
	await e.updateComplete;
	let t = e.renderRoot.querySelector(".editor");
	t && (t.scrollIntoView({
		behavior: "smooth",
		block: "start"
	}), t.querySelector("input:not([type=checkbox]):not([disabled]), select, textarea")?.focus({ preventScroll: !0 }));
}
async function R(e) {
	await e.updateComplete, e.renderRoot.querySelector(".editor .problems, .editor .problem")?.scrollIntoView({
		behavior: "smooth",
		block: "nearest"
	});
}
function z(e, t) {
	let n = t.field ? M(e, `field.${t.field}`) : "";
	return M(e, `problem.${t.code}`, {
		field: n,
		detail: t.detail ?? ""
	});
}
function B(e) {
	(e.key === "Enter" || e.key === " ") && e.target === e.currentTarget && (e.preventDefault(), e.currentTarget.click());
}
function V(e, t) {
	let n = H(e.target.value);
	n !== null && t(n);
}
function H(e) {
	let t = e.trim();
	if (t === "") return null;
	let n = Number(t);
	return Number.isFinite(n) ? n : null;
}
//#endregion
//#region src/panel/pages/overview.ts
function Qe(e, t) {
	let n = M(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = M(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
var $e = /* @__PURE__ */ new Set(["zone_open", "zone_fault"]), et = class extends A {
	constructor(...e) {
		super(...e), this._busy = !1, this._perArea = !1, this._recent = [];
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_busy: { state: !0 },
			_feedback: { state: !0 },
			_recent: { state: !0 },
			_perArea: { state: !0 }
		};
	}
	async _run(e, t) {
		let n = this.ctx;
		if (n) {
			this._busy = !0, this._feedback = void 0;
			try {
				let r = await e();
				if (r.reason === "cancelled") this._feedback = {
					ok: !0,
					text: M(n.strings, "reason.cancelled")
				};
				else if (r.success) {
					let e = r.bypassed_zones.map((e) => e.name).join(", "), t = r.low_battery_zones;
					this._feedback = t.length ? {
						ok: !0,
						text: M(n.strings, "overview.low_battery", { zones: t.map((e) => e.name).join(", ") }),
						lowBattery: t
					} : e ? {
						ok: !0,
						text: M(n.strings, "overview.bypassed", { zones: e })
					} : void 0;
				} else this._feedback = {
					ok: !1,
					text: Xe(n.strings, r, n.hass.language),
					retry: t && $e.has(r.reason ?? "") ? t : void 0
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
				for (let n of e) {
					let e = await t.bypass(n.id, !0);
					if (!e.success) {
						this._feedback = {
							ok: e.reason === "cancelled",
							text: Xe(t.strings, e, t.hass.language)
						};
						return;
					}
				}
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
		this._feedback && !this._feedback.ok && this._feedback.retry && this.ctx.status.areas.every((e) => e.ready) && (this._feedback = void 0);
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
		if (!e) return T;
		let t = e.strings, n = e.status, r = n.areas.filter((e) => e.memory);
		return C`
      ${this._renderTechnical(t)} ${this._renderIncident(t)}
      ${n.security.enforced ? T : C`<div class="notice" role="note">
            ${M(t, "overview.no_codes_warning")}
          </div>`}
      ${r.map((e) => {
			let n = this._zoneNames(e.causes), r = e.state !== "disarmed";
			return C`<div class="alarm-memory" role="alert">
          ${e.causes.length ? r ? M(t, "overview.memory_banner_armed", {
				area: e.name,
				zones: n
			}) : M(t, "overview.memory_banner", {
				area: e.name,
				zones: n
			}) : r ? M(t, "overview.memory_banner_armed_plain", { area: e.name }) : M(t, "overview.memory_banner_plain", { area: e.name })}
        </div>`;
		})}
      ${this._renderMaster(t)} ${this._renderFeedback(t)}
      <div class="tiles">${n.areas.map((e) => this._renderArea(t, e))}</div>
      ${this._renderNotReady(t)} ${this._renderRecent(t)}
    `;
	}
	_renderRecent(e) {
		let t = this.ctx, n = this._recent;
		if (!n.length) return T;
		let r = new Map(t.status.areas.map((e) => [e.id, e.name])), i = new Map(t.status.zones.map((e) => [e.id, e.name]));
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "overview.recent")}</h2>
          <span class="spacer"></span>
          <button class="btn sm" @click=${() => t.navigate("log")}>
            ${M(e, "overview.full_log")}
          </button>
        </div>
        <div class="card-bd">
          <div class="recent">
            ${n.map((n) => C`<div class="row">
                <span class="when mono"
                  >${new Date(n.ts).toLocaleTimeString(t.hass.language, {
			hour: "2-digit",
			minute: "2-digit"
		})}</span
                >
                <span class="state ${n.severity === "alarm" ? "triggered" : n.severity === "warning" ? "arming" : "disarmed"}"
                  >${Qe(e, n.event_type)}</span
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
				],
				glance: !0
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
		if (!t.length) return T;
		let n = t.some((e) => !e.acknowledged);
		return C`
      <div class="banner technical" role="alert">
        <div class="banner-hd">${M(e, "overview.technical_title")}</div>
        <div>
          ${M(e, "overview.technical_banner", { zones: t.map((e) => e.name).join(", ") })}
        </div>
        <ul class="plain">
          ${t.map((t) => C`<li>
              <strong>${t.name}</strong> —
              ${M(e, t.acknowledged ? "technical_state.acknowledged" : t.active ? "technical_state.active" : "technical_state.memory")}
            </li>`)}
        </ul>
        ${n ? C`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("technical")}
              >
                ${M(e, "common.acknowledge")}
              </button>
            </div>` : T}
      </div>
    `;
	}
	_renderIncident(e) {
		let t = this.ctx.status.incident;
		return t ? C`
      <div class="banner incident" role="alert">
        <div class="banner-hd">
          ${M(e, "overview.incident_title", { id: t.id })}
          <span class="state ${t.acknowledged ? "memory" : "triggered"}">
            ${M(e, t.acknowledged ? "overview.incident_acknowledged" : "overview.incident_open")}
          </span>
        </div>
        <div>${M(e, "overview.incident_zones", { zones: this._zoneNames(t.zone_ids) })}</div>
        <div class="hint">${M(e, "overview.incident_hint")}</div>
        ${t.acknowledged ? T : C`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._acknowledge("incident")}
              >
                ${M(e, "common.acknowledge")}
              </button>
            </div>`}
      </div>
    ` : T;
	}
	_renderMaster(e) {
		let t = this.ctx.status, n = t.master, r = t.areas.some((e) => e.state !== "disarmed" || e.memory);
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "overview.master")}</h2>
          <span class="state ${n.state}">${M(e, `state.${n.state}`)}</span>
          ${n.mode ? C`<span>${M(e, `ha_state.${n.mode}`)}</span>` : T}
        </div>
        <div class="card-bd">
          <div class="label">${M(e, "overview.scenario")}</div>
          ${t.scenarios.length ? C`<div class="scenarios">
                ${t.scenarios.map((t) => this._renderScenario(e, t))}
              </div>` : C`<div class="muted">${M(e, "overview.no_scenarios")}</div>`}
          <div class="hint">${M(e, "overview.scenario_hint")}</div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !r}
              @click=${() => this._disarm()}
            >
              ${M(e, "overview.disarm_all")}
            </button>
            <button
              class="link"
              aria-expanded=${this._perArea ? "true" : "false"}
              @click=${() => this._perArea = !this._perArea}
            >
              ${M(e, this._perArea ? "overview.one_area_hide" : "overview.one_area")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderScenario(e, t) {
		let n = this.ctx.status, r = t.id === n.active_scenario_id, i = n.areas.filter((e) => t.areas.includes(e.id)), a = i.every((e) => e.ready), o = [...new Set(i.flatMap((e) => [...e.blocking.open, ...e.blocking.fault]))];
		return C`<div class="scenario">
      <button
        class="btn ${r ? "" : "primary"}"
        aria-pressed=${r ? "true" : "false"}
        ?disabled=${this._busy}
        @click=${() => this._arm({ scenario_id: t.id })}
      >
        ${(n.active_scenario_id && !r ? t.require_code.change ?? t.require_code.arm : t.require_code.arm) ? C`<ha-icon
              icon="mdi:lock-outline"
              title=${M(e, "overview.code_needed")}
              aria-label=${M(e, "overview.code_needed")}
            ></ha-icon>` : T}
        ${M(e, "overview.arm_scenario", { name: t.name })}
      </button>
      ${r ? C`<span class="state armed">${M(e, "scenarios.active")}</span>` : a ? C`<span class="ready ok">${M(e, "overview.ready")}</span>` : C`<span class="ready not">
              ${o.length ? M(e, "overview.not_ready_zones", { zones: this._zoneNames(o) }) : M(e, "overview.not_ready_plain")}
            </span>`}
    </div>`;
	}
	_renderFeedback(e) {
		let t = this._feedback;
		return t ? C`
      <div class=${t.ok ? "notice" : "problems"} role="alert">
        ${t.text}
        ${t.lowBattery?.length ? C`<div class="actions">
              <button
                class="btn"
                ?disabled=${this._busy}
                @click=${() => void this._excludeLowBattery(t.lowBattery)}
              >
                ${M(e, "overview.exclude_low_battery")}
              </button>
            </div>` : T}
        ${t.retry ? C`<div class="actions">
              <button
                class="btn danger"
                ?disabled=${this._busy}
                @click=${() => this._force(t.retry)}
              >
                ${M(e, "overview.force_arm")}
              </button>
              <span class="hint">${M(e, "overview.force_arm_hint")}</span>
            </div>` : T}
      </div>
    ` : T;
	}
	_renderArea(e, t) {
		let n = this.ctx, r = n.status.scenarios.find((e) => e.id === t.scenario_id);
		return C`
      <div class="card tile">
        <div class="card-bd">
          <div class="label">${M(e, "overview.area")}</div>
          <div class="name">${t.name}</div>
          <div class="row">
            <span class="state ${t.state}">${M(e, `state.${t.state}`)}</span>
            ${t.memory ? C`<span class="state memory">${M(e, "overview.memory")}</span>` : T}
          </div>
          ${t.timer && t.timer.kind !== "siren" ? C`<div class="countdown">
                ${M(e, `timer.${t.timer.kind}`, { seconds: Ye(n, t.timer.due) })}
              </div>` : T}
          <div class="hint">
            ${t.state === "disarmed" ? T : r ? M(e, "overview.by_scenario", { scenario: r.name }) : M(e, "overview.on_its_own")}
          </div>
          <div class="actions">
            ${t.state === "disarmed" && this._perArea ? C`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._arm({ area_id: t.id })}
                >
                  ${M(e, "overview.arm_area")}
                </button>` : T}
            ${t.state !== "disarmed" || t.memory ? C`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._disarm([t.id])}
                >
                  ${M(e, "overview.disarm_area")}
                </button>` : T}
          </div>
        </div>
      </div>
    `;
	}
	_renderNotReady(e) {
		let t = this.ctx, n = new Map(t.status.areas.map((e) => [e.id, e.name])), r = t.status.zones.filter((e) => e.enabled && (e.fault || e.open && e.channel === "intrusion" || e.bypassed));
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "overview.not_ready")}</h2></div>
        ${r.length ? C`<div class="table-wrap">
              <table class="stack">
                <thead>
                  <tr>
                    <th>${M(e, "overview.zone")}</th>
                    <th>${M(e, "overview.area")}</th>
                    <th>${M(e, "overview.status")}</th>
                    <th>${M(e, "overview.entity_state")}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${r.map((t) => C`<tr>
                      <td class="lead">${t.name}</td>
                      <td data-label=${M(e, "overview.area")}>${n.get(t.area_id) ?? ""}</td>
                      <td data-label=${M(e, "overview.status")}>${this._zoneStatus(e, t)}</td>
                      <td data-label=${M(e, "overview.entity_state")}>
                        <span class="mono">${t.state ?? "—"}</span>
                      </td>
                      <td>${this._renderBypass(e, t)}</td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : C`<div class="empty">${M(e, "overview.all_ready")}</div>`}
      </div>
    `;
	}
	_renderBypass(e, t) {
		let n = this.ctx;
		return t.bypassed ? C`<button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !1))}
      >
        ${M(e, "zones.unbypass")}
      </button>` : t.bypassable ? C`<div class="bypass">
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => n.bypass(t.id, !0))}
      >
        ${M(e, "zones.bypass")}
      </button>
      ${[1, 8].map((r) => C`<button
          class="btn sm ghost"
          ?disabled=${this._busy}
          @click=${() => this._run(() => n.bypass(t.id, !0, r * 3600))}
        >
          ${M(e, "zones.bypass_hours", { hours: r })}
        </button>`)}
      <label class="minutes">
        <input
          type="number"
          min="1"
          max="10080"
          placeholder=${M(e, "zones.bypass_minutes_placeholder")}
          aria-label=${M(e, "zones.bypass_minutes")}
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
          ${M(e, "zones.bypass_minutes")}
        </button>
      </label>
    </div>` : T;
	}
	_bypassMinutes(e, t) {
		let n = this.ctx, r = Number(t.value);
		!Number.isFinite(r) || r < 1 || (t.value = "", this._run(() => n.bypass(e, !0, Math.round(r) * 60)));
	}
	_zoneStatus(e, t) {
		let n = this.ctx;
		if (t.fault) return C`<span class="state fault">${M(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) {
			let r = t.bypass_until ? M(e, "zones.bypass_until", { time: new Date(t.bypass_until).toLocaleTimeString(n.hass.language, {
				hour: "2-digit",
				minute: "2-digit"
			}) }) : M(e, "zones.bypass_indefinite");
			return C`<span class="state bypassed">${M(e, `bypass.${t.bypassed}`)}</span>
        <span class="hint">${t.bypassed === "manual" ? r : ""}</span>`;
		}
		return C`<span class="state open">${M(e, "zone_status.open")}</span>`;
	}
	static {
		this.styles = [
			N,
			P,
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
      .scenarios {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 8px;
      }
      .scenario {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px 12px;
      }
      .scenario .btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .scenario ha-icon {
        --mdc-icon-size: 18px;
      }
      .ready {
        font-size: 13px;
      }
      .ready.ok {
        color: var(--success-color, #2e9e4f);
      }
      .ready.not {
        color: var(--warning-color, #c77700);
      }
      .actions .link {
        font: inherit;
        font-size: 13.5px;
        border: 0;
        background: transparent;
        color: var(--primary-color);
        cursor: pointer;
        padding: 8px 4px;
        text-decoration: underline;
      }
      /* The not-ready table on a phone: one card per zone instead of a table
         that scrolls sideways past the one button that matters (UX review). */
      @media (max-width: 600px) {
        table.stack thead {
          display: none;
        }
        table.stack,
        table.stack tbody,
        table.stack tr,
        table.stack td {
          display: block;
        }
        table.stack tr {
          padding: 10px 16px;
          border-bottom: 1px solid var(--divider-color);
        }
        table.stack td {
          border: 0;
          padding: 3px 0;
        }
        table.stack td.lead {
          font-weight: 500;
          font-size: 15px;
        }
        table.stack td[data-label]::before {
          content: attr(data-label) ": ";
          color: var(--secondary-text-color);
          font-size: 12.5px;
        }
      }
    `
		];
	}
};
customElements.get("foyer-page-overview") || customElements.define("foyer-page-overview", et);
//#endregion
//#region node_modules/lit-html/directive-helpers.js
var { I: tt } = je, nt = (e) => e.strings === void 0, rt = {}, it = (e, t = rt) => e._$AH = t, U = Ie(class extends Le {
	constructor(e) {
		if (super(e), e.type !== j.PROPERTY && e.type !== j.ATTRIBUTE && e.type !== j.BOOLEAN_ATTRIBUTE) throw Error("The `live` directive is not allowed on child or event bindings");
		if (!nt(e)) throw Error("`live` bindings can only contain a single expression");
	}
	render(e) {
		return e;
	}
	update(e, [t]) {
		if (t === w || t === T) return t;
		let n = e.element, r = e.name;
		if (e.type === j.PROPERTY) {
			if (t === n[r]) return w;
		} else if (e.type === j.BOOLEAN_ATTRIBUTE) {
			if (!!t === n.hasAttribute(r)) return w;
		} else if (e.type === j.ATTRIBUTE && n.getAttribute(r) === t + "") return w;
		return it(e), t;
	}
});
//#endregion
//#region src/panel/code-fields.ts
function at(e, t, n, r) {
	return C`<label class="field">
    <span class="lbl">${M(e, t)}</span>
    <select
      @change=${(e) => {
		let t = e.target.value;
		r(t === "" ? null : t === "yes");
	}}
    >
      <option value="" .selected=${U(n === null)}>${M(e, "code_policy.inherit")}</option>
      <option value="yes" .selected=${U(n === !0)}>${M(e, "code_policy.required")}</option>
      <option value="no" .selected=${U(n === !1)}>${M(e, "code_policy.not_required")}</option>
    </select>
  </label>`;
}
function ot(e, t, n, r) {
	return C`
    ${at(e, "field.require_code_to_arm", t.require_code_to_arm, (e) => n("require_code_to_arm", e))}
    ${at(e, "field.require_code_to_disarm", t.require_code_to_disarm, (e) => n("require_code_to_disarm", e))}
    <p class="hint span">
      ${M(e, "code_policy.strictest")}
      ${r ? T : C` ${M(e, "code_policy.inert")}`}
    </p>
  `;
}
//#endregion
//#region src/panel/delete-button.ts
var st = class extends A {
	constructor(...e) {
		super(...e), this.name = "", this.message = "common.confirm_delete", this.disabled = !1, this._asking = !1;
	}
	static {
		this.properties = {
			strings: { attribute: !1 },
			name: { attribute: !1 },
			message: { attribute: !1 },
			disabled: { type: Boolean },
			_asking: { state: !0 }
		};
	}
	_confirm() {
		this._asking = !1, this.dispatchEvent(new CustomEvent("confirm", {
			bubbles: !0,
			composed: !0
		}));
	}
	render() {
		let e = this.strings;
		return this._asking ? C`<div class="ask" role="alertdialog" aria-labelledby="q">
      <span id="q">${M(e, this.message, { name: this.name })}</span>
      <span class="buttons">
        <button class="btn danger" ?disabled=${this.disabled} @click=${this._confirm}>
          ${M(e, "common.delete")}
        </button>
        <button class="btn" @click=${() => this._asking = !1}>
          ${M(e, "common.cancel")}
        </button>
      </span>
    </div>` : C`<button
        class="btn danger"
        ?disabled=${this.disabled}
        @click=${() => this._asking = !0}
      >
        ${M(e, "common.delete")}
      </button>`;
	}
	willUpdate(e) {
		e.has("name") && e.get("name") !== void 0 && (this._asking = !1);
	}
	updated(e) {
		if (!e.has("_asking")) return;
		let t = this._asking ? ".ask .btn:not(.danger)" : ".btn.danger";
		this.renderRoot.querySelector(t)?.focus();
	}
	static {
		this.styles = [P, o`
      :host {
        display: contents;
      }
      .ask {
        flex-basis: 100%;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 12px;
        padding: 10px 14px;
        border-left: 3px solid var(--error-color, #d32f2f);
        background: var(--secondary-background-color);
        border-radius: 6px;
        font-size: 14px;
      }
      .ask > span:first-child {
        flex: 1 1 240px;
      }
      .buttons {
        display: flex;
        gap: 8px;
      }
    `];
	}
};
customElements.get("foyer-delete-button") || customElements.define("foyer-delete-button", st);
//#endregion
//#region src/panel/profile-picker.ts
function ct(e, t, n = null) {
	let r = e.areas.find((e) => e.id === t), i = n ? e.scenarios.find((e) => e.id === n) : e.scenarios.find((e) => r?.id && e.areas.includes(r.id) && e.response_profile_id), a = (t) => e.profiles?.find((e) => e.id === t), o = a(r?.response_profile_id);
	if (o) return {
		name: o.name,
		source: "area"
	};
	let s = a(i?.response_profile_id);
	if (s) return {
		name: s.name,
		source: "scenario"
	};
	let c = a(e.settings?.default_profile_id);
	return c ? {
		name: c.name,
		source: "default"
	} : {
		name: "",
		source: "none"
	};
}
function W(e, t, n, r) {
	let i = e.strings, a = e.config?.profiles ?? [];
	return C`<label class="field">
    <span class="lbl">${M(i, "field.response_profile_id")}</span>
    <select @change=${(e) => n(e.target.value || null)}>
      <option value="" .selected=${U(!t)}>${M(i, "profiles.inherit")}</option>
      ${a.map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === t)}>
          ${e.name}
        </option>`)}
    </select>
    ${r ? C`<span class="hint">${r}</span>` : T}
  </label>`;
}
function lt(e, t) {
	if (!e.config) return T;
	let n = e.status?.areas.find((e) => e.id === t)?.scenario_id ?? null, { name: r, source: i } = ct(e.config, t, n), a = e.strings;
	return i === "none" ? C`<p class="hint">${M(a, "profiles.inherited_none")}</p>` : C`<p class="hint">
    ${M(a, "profiles.effective_from", {
		profile: r,
		from: M(a, `profiles.inherited_from_${i}`)
	})}
  </p>`;
}
//#endregion
//#region src/panel/pages/areas.ts
var G = {
	name: "",
	ha_state_when_armed: "armed_away",
	default_entry_delay: 30,
	default_exit_delay: 30,
	response_profile_id: null,
	require_code_to_arm: null,
	require_code_to_disarm: null,
	is_perimeter: !1
}, ut = class extends A {
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
		if (this._busy) return;
		let t = this.ctx?.config?.settings;
		this._draft = e ? { ...e } : {
			...G,
			default_entry_delay: t?.default_entry_delay ?? G.default_entry_delay,
			default_exit_delay: t?.default_exit_delay ?? G.default_exit_delay
		}, this._problems = [], L(this);
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
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0);
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
		if (!e?.config) return T;
		let t = e.strings, n = new Map(e.status.areas.map((e) => [e.id, e.state])), r = (t) => e.config.zones.filter((e) => e.area_id === t).length;
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "areas.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${M(t, "areas.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${M(t, "field.name")}</th>
                <th>${M(t, "overview.status")}</th>
                <th>${M(t, "areas.zones")}</th>
                <th>${M(t, "field.default_entry_delay")}</th>
                <th>${M(t, "field.default_exit_delay")}</th>
                <th>${M(t, "field.ha_state_when_armed")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.areas.map((e) => {
			let i = n.get(e.id ?? "") ?? "disarmed";
			return C`<tr
                  class="clickable"
 tabindex="0"
 @keydown=${B}
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td><span class="state ${i}">${M(t, `state.${i}`)}</span></td>
                  <td>${r(e.id)}</td>
                  <td>${M(t, "common.seconds", { n: e.default_entry_delay })}</td>
                  <td>${M(t, "common.seconds", { n: e.default_exit_delay })}</td>
                  <td>${M(t, `ha_state.${e.ha_state_when_armed}`)}</td>
                </tr>`;
		})}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : T}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx.meta, [r, i] = n?.bounds.exit_delay ?? [0, 300], a = n?.bounds.entry_delay?.[1] ?? 300;
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "areas.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.ha_state_when_armed")}</span>
              <select
                @change=${(e) => this._set("ha_state_when_armed", e.target.value)}
              >
                ${(n?.ha_states ?? []).map((n) => C`<option .value=${n} .selected=${U(n === t.ha_state_when_armed)}>
                      ${M(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${M(e, "areas.reports_as_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.default_entry_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${a}
                .value=${String(t.default_entry_delay)}
                @input=${(e) => V(e, (e) => this._set("default_entry_delay", e))}
              />
              <span class="hint">${M(e, "areas.entry_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.default_exit_delay")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.default_exit_delay)}
                @input=${(e) => V(e, (e) => this._set("default_exit_delay", e))}
              />
              <span class="hint">${M(e, "areas.exit_hint")}</span>
            </label>
            ${W(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
            ${ot(e, t, (e, t) => this._set(e, t), this.ctx.status.security.enforced)}
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.is_perimeter)}
              @change=${(e) => this._set("is_perimeter", e.target.checked)}
            />
            <span>
              ${M(e, "field.is_perimeter")}
              <span class="hint">${M(e, "areas.perimeter_hint")}</span>
            </span>
          </label>
          ${lt(this.ctx, t.id ?? null)}
          ${this._problems.length ? C`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
                </ul>
              </div>` : T}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${M(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${M(e, "common.cancel")}
            </button>
            ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [N, P];
	}
};
customElements.get("foyer-page-areas") || customElements.define("foyer-page-areas", ut);
//#endregion
//#region src/panel/ha-targets.ts
function dt(e, t) {
	let n = e.states[t];
	return String(n?.attributes?.friendly_name ?? t);
}
function ft(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) t.has(n.id) || t.set(n.id, n);
	return [...t.values()].sort((e, t) => e.id.localeCompare(t.id));
}
var pt = /* @__PURE__ */ new WeakMap();
function K(e, t) {
	let n = pt.get(e.states);
	n || (n = /* @__PURE__ */ new Map(), pt.set(e.states, n));
	let r = t.join(","), i = n.get(r);
	return i || (i = ft(Object.values(e.states).filter((e) => t.includes(e.entity_id.split(".")[0])).map((t) => ({
		id: t.entity_id,
		name: dt(e, t.entity_id)
	}))), n.set(r, i)), i;
}
function q(e) {
	let t = Object.keys(e.services?.notify ?? {}).filter((e) => e !== "send_message").map((e) => ({
		id: `notify.${e}`,
		name: `notify.${e}`
	}));
	return ft([...K(e, ["notify"]), ...t]);
}
function mt(e, t) {
	return ft([...K(e, t.filter((e) => e !== "notify")), ...t.includes("notify") ? q(e) : []]);
}
function ht(e) {
	let t = K(e, ["sensor", "binary_sensor"]), n = (t) => e.states[t.id]?.attributes.device_class === "battery";
	return [...t.filter(n), ...t.filter((e) => !n(e))];
}
function gt(e) {
	return Object.keys(e.services ?? {}).sort();
}
function _t(e, t) {
	return Object.keys(e.services?.[t] ?? {}).sort();
}
function J(e, t, n) {
	let r = e.states[t], i = n;
	if (r && e.formatEntityState) try {
		i = e.formatEntityState(r, n);
	} catch {
		i = n;
	}
	return i && i !== n ? `${i} (${n})` : n;
}
//#endregion
//#region src/panel/pages/zones.ts
var vt = /* @__PURE__ */ new Set(["event", "tag"]), yt = /* @__PURE__ */ new Set(["unavailable", "unknown"]);
function bt(e) {
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
		camera_entity_ids: [],
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
function xt(e) {
	return e.channel === "intrusion" ? e : {
		...e,
		chime: !1,
		cross_zone_id: null,
		trigger_count: 1,
		silent: !1
	};
}
var St = (e, t) => JSON.stringify(e) === JSON.stringify(t), Ct = class extends A {
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
		if (this._busy) return;
		let t = this.ctx?.config?.areas[0]?.id ?? "";
		this._draft = e ? structuredClone(e) : bt(t), this._saved = e, this._proposal = void 0, this._confirmed = !1, this._problems = [], e && this._propose(e.entity_id, !1), L(this);
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
		}), n.channel !== "key" && (n.key = null), n.arm_policy !== "arm_after_closing" && (n.arm_hold_timeout = null), n.entry_mode !== "follower" && (n.follows = []), n.always_on && (n.chime = !1), this._draft = xt(n);
	}
	async _propose(e, t) {
		let n = this.ctx;
		if (!n || !e) return;
		let r = this._draft, i;
		try {
			i = await n.hass.callWS({
				type: "foyer/zone/propose",
				entity_id: e
			});
		} catch {
			if (this._draft !== r) return;
			this._problems = [{
				code: "propose_failed",
				kind: "zone",
				ref: null,
				field: "entity_id"
			}];
			return;
		}
		if (this._draft !== r || (this._proposal = i, !t || !this._draft)) return;
		let a = i.trigger_kind === "event" ? {
			kind: "event",
			event_type: e.startsWith("event.") ? i.proposed[0] ?? null : null
		} : i.trigger_kind === "numeric" ? {
			kind: "numeric",
			operator: "gt",
			value: 0,
			hysteresis: 0,
			attribute: null
		} : {
			kind: "state",
			states: [...i.proposed]
		};
		this._draft = {
			...this._draft,
			entity_id: e,
			name: this._draft.name || i.name
		}, this._set("trigger", a), i.zone_type && this._typeAvailable(i.zone_type) && this._applyType(i.zone_type);
	}
	_typeAvailable(e) {
		return this.ctx?.meta?.zone_types.find((t) => t.type === e)?.available ?? !1;
	}
	_needsConfirmation() {
		return !this._saved || !St(this._saved.trigger, this._draft?.trigger) || this._saved.trigger_confirmed === !1 && !!this._draft?.enabled;
	}
	_confirmable() {
		return this._needsConfirmation() || this._saved?.trigger_confirmed === !1;
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("zone", this._draft, this._confirmed);
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0);
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
		if (!e?.config) return T;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.status.zones.map((e) => [e.id, e]));
		return e.config.areas.length ? C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "zones.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${M(t, "zones.add")}</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${M(t, "field.name")}</th>
                <th>${M(t, "field.entity_id")}</th>
                <th>${M(t, "field.area_id")}</th>
                <th>${M(t, "field.type")}</th>
                <th>${M(t, "field.arm_policy")}</th>
                <th>${M(t, "overview.status")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.zones.map((e) => C`<tr
                  class="clickable"
 tabindex="0"
 @keydown=${B}
                  aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                  @click=${() => this._edit(e)}
                >
                  <td><strong>${e.name}</strong></td>
                  <td class="mono">${e.entity_id}</td>
                  <td>${n.get(e.area_id) ?? ""}</td>
                  <td><span class="tag">${M(t, `zone_type.${e.type}`)}</span></td>
                  <td>${M(t, `arm_policy.${e.arm_policy}`)}</td>
                  <td>
                    ${e.trigger_confirmed === !1 ? C`<span class="state fault">${M(t, "zone_status.unconfirmed")}</span>` : this._health(t, r.get(e.id ?? ""))}
                  </td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : T}
    ` : C`<div class="card"><div class="empty">${M(t, "zones.no_areas")}</div></div>`;
	}
	_health(e, t) {
		if (!t) return T;
		if (!t.enabled) return C`<span class="state disabled">${M(e, "zone_status.disabled")}</span>`;
		if (t.fault) return C`<span class="state fault">${M(e, `fault.${t.fault}`)}</span>`;
		if (t.bypassed) return C`<span class="state bypassed">${M(e, `bypass.${t.bypassed}`)}</span>`;
		let n = t.open ? "open" : "closed";
		return C`<span class="state ${n}">${M(e, `zone_status.${n}`)}</span>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx;
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "zones.new")}</h2>
        </div>
        <div class="card-bd">
          ${this._saved?.trigger_confirmed === !1 ? C`<div class="notice">${M(e, "zones.unconfirmed_notice")}</div>` : T}
          ${t.id ? T : this._renderEntityPicker(e, t)}
          ${t.entity_id ? C`
                ${this._renderTrigger(e, t)} ${this._renderProperties(e, t)}
                ${t.channel === "intrusion" && t.entry_mode === "follower" ? this._renderFollows(e, t) : T}
                ${t.channel === "intrusion" ? this._renderVerification(e, t) : T}
                ${t.channel === "key" ? this._renderKey(e, t) : T}
              ` : T}
          ${this._problems.length ? C`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
                </ul>
              </div>` : T}
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !t.entity_id || this._needsConfirmation() && !this._confirmed}
              @click=${this._save}
            >
              ${M(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${M(e, "common.cancel")}
            </button>
            ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          </div>
          ${this._needsConfirmation() && !this._confirmed && t.entity_id ? C`<div class="hint">${M(e, "zones.confirm_first")}</div>` : T}
          ${n.status.areas.some((e) => e.id === t.area_id && e.state !== "disarmed") ? C`<div class="notice">${M(e, "zones.area_armed")}</div>` : T}
        </div>
      </div>
    `;
	}
	_renderEntityPicker(e, t) {
		let n = this.ctx, r = new Set(n.meta?.zone_domains ?? []), i = new Set(n.config?.zones.map((e) => e.entity_id)), a = this._filter.toLowerCase(), o = Object.values(n.hass.states).filter((e) => r.has(e.entity_id.split(".")[0])).filter((e) => {
			let t = String(e.attributes.friendly_name ?? "");
			return !a || e.entity_id.toLowerCase().includes(a) || t.toLowerCase().includes(a);
		}).sort((e, t) => e.entity_id.localeCompare(t.entity_id)).slice(0, 200);
		return C`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "zones.search")}</span>
          <input
            .value=${this._filter}
            @input=${(e) => this._filter = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${M(e, "field.entity_id")}</span>
          <select
            @change=${(e) => this._propose(e.target.value, !0)}
          >
            <option value="" .selected=${U(!t.entity_id)}>${M(e, "zones.pick_entity")}</option>
            ${o.map((n) => C`<option
                .value=${n.entity_id}
                .selected=${U(n.entity_id === t.entity_id)}
              >
                ${M(e, i.has(n.entity_id) ? "zones.entity_used" : "zones.entity", {
			name: String(n.attributes.friendly_name ?? n.entity_id),
			entity: n.entity_id
		})}
              </option>`)}
          </select>
          <span class="hint">${M(e, "zones.entity_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderTrigger(e, t) {
		let n = this.ctx, r = n.hass.states[t.entity_id], i = r?.state ?? "unavailable", a = t.entity_id.split(".")[0], o = t.trigger;
		return C`
      <fieldset>
        <legend>${M(e, "zones.trigger_title")}</legend>
        <p class="hint">
          ${M(e, "zones.trigger_intro", {
			entity: String(r?.attributes.friendly_name ?? t.entity_id),
			state: J(n.hass, t.entity_id, i)
		})}
          ${this._proposal?.device_class ? M(e, "zones.device_class", { device_class: this._proposal.device_class }) : T}
        </p>
        ${vt.has(a) ? this._renderEventTrigger(e, a, o) : C`
              <label class="field">
                <span class="lbl">${M(e, "zones.trigger_kind")}</span>
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
                  <option value="state" .selected=${U(o.kind === "state")}>
                    ${M(e, "zones.kind_state")}
                  </option>
                  <option value="numeric" .selected=${U(o.kind === "numeric")}>
                    ${M(e, "zones.kind_numeric")}
                  </option>
                </select>
              </label>
              ${o.kind === "numeric" ? this._renderNumericTrigger(e, o) : o.kind === "state" ? this._renderStateTrigger(e, t.entity_id, o.states, i) : T}
            `}
        <label class="check confirm">
          <input
            type="checkbox"
            .checked=${U(this._confirmed || !this._confirmable())}
            ?disabled=${!this._confirmable()}
            @change=${(e) => this._confirmed = e.target.checked}
          />
          <span>
            ${M(e, "zones.confirm")}
            <span class="hint">${M(e, "zones.confirm_hint")}</span>
          </span>
        </label>
      </fieldset>
    `;
	}
	_renderStateTrigger(e, t, n, r) {
		let i = this.ctx.hass, a = /* @__PURE__ */ new Set([...this._proposal?.options ?? [], ...n]);
		yt.has(r) || a.add(r);
		let o = (e, t) => {
			let r = t ? [...n, e] : n.filter((t) => t !== e);
			this._set("trigger", {
				kind: "state",
				states: [...new Set(r)].sort()
			});
		};
		return C`
      <div class="states">
        ${[...a].map((a) => C`<label class="check">
            <input
              type="checkbox"
              .checked=${U(n.includes(a))}
              @change=${(e) => o(a, e.target.checked)}
            />
            <span>${J(i, t, a)}</span>
            ${a === r ? C`<span class="tag">${M(e, "zones.now")}</span>` : T}
          </label>`)}
      </div>
      <div class="row">
        <label class="field">
          <span class="lbl">${M(e, "zones.other_state")}</span>
          <input
            .value=${this._customState}
            @input=${(e) => this._customState = e.target.value}
          />
        </label>
        <button
          class="btn"
          ?disabled=${!this._customState.trim()}
          @click=${() => {
			o(this._customState.trim(), !0), this._customState = "";
		}}
        >
          ${M(e, "zones.add_state")}
        </button>
      </div>
      <div class="hint">${M(e, "zones.state_hint")}</div>
    `;
	}
	_renderNumericTrigger(e, t) {
		let n = (e) => this._set("trigger", {
			...t,
			...e
		});
		return C`
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "zones.operator")}</span>
          <select
            @change=${(e) => n({ operator: e.target.value })}
          >
            ${[
			"gt",
			"lt",
			"eq"
		].map((n) => C`<option .value=${n} .selected=${U(n === t.operator)}>
                  ${M(e, `operator.${n}`)}
                </option>`)}
          </select>
        </label>
        <label class="field">
          <span class="lbl">${M(e, "zones.threshold")}</span>
          <input
            type="number"
            step="any"
            .value=${String(t.value)}
            @input=${(e) => n({ value: Number(e.target.value) })}
          />
        </label>
        <label class="field">
          <span class="lbl">${M(e, "zones.hysteresis")}</span>
          <input
            type="number"
            step="any"
            min="0"
            ?disabled=${t.operator === "eq"}
            .value=${String(t.hysteresis)}
            @input=${(e) => n({ hysteresis: Number(e.target.value) })}
          />
          <span class="hint">${M(e, "zones.hysteresis_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${M(e, "zones.attribute")}</span>
          <input
            .value=${t.attribute ?? ""}
            @input=${(e) => n({ attribute: e.target.value.trim() || null })}
          />
          <span class="hint">${M(e, "zones.attribute_hint")}</span>
        </label>
      </div>
    `;
	}
	_renderEventTrigger(e, t, n) {
		if (t === "tag") return C`<p class="hint">${M(e, "zones.tag_hint")}</p>`;
		let r = n.kind === "event" ? n.event_type : null;
		return C`
      <label class="field">
        <span class="lbl">${M(e, "zones.event_type")}</span>
        <select
          @change=${(e) => this._set("trigger", {
			kind: "event",
			event_type: e.target.value || null
		})}
        >
          <option value="" .selected=${U(!r)}>${M(e, "zones.pick_event")}</option>
          ${(this._proposal?.options ?? []).map((e) => C`<option .value=${e} .selected=${U(e === r)}>${e}</option>`)}
        </select>
        <span class="hint">${M(e, "zones.event_hint")}</span>
      </label>
    `;
	}
	_renderProperties(e, t) {
		let n = this.ctx, r = n.meta, i = n.config?.areas.find((e) => e.id === t.area_id), a = t.channel === "intrusion", o = (n, r) => C`
      <label class="check">
        <input
          type="checkbox"
          .checked=${U(!!t[n])}
          @change=${(e) => {
			let t = e.target.checked;
			this._set(n, t), n === "always_on" && t && this._set("chime", !1);
		}}
        />
        <span>
          ${M(e, `field.${n}`)}
          ${r ? C`<span class="hint">${M(e, r)}</span>` : T}
        </span>
      </label>
    `;
		return C`
      <fieldset>
        <legend>${M(e, "zones.properties_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${M(e, "field.name")}</span>
            <input
              .value=${t.name}
              @input=${(e) => this._set("name", e.target.value)}
            />
          </label>
          <label class="field">
            <span class="lbl">${M(e, "field.type")}</span>
            <select @change=${(e) => this._applyType(e.target.value)}>
              ${(r?.zone_types ?? []).map((n) => C`<option
                  .value=${n.type}
                  .selected=${U(n.type === t.type)}
                  ?disabled=${!n.available}
                >
                  ${M(e, n.available ? `zone_type.${n.type}` : "zones.type_unavailable", { type: M(e, `zone_type.${n.type}`) })}
                </option>`)}
            </select>
            <span class="hint">${M(e, "zones.type_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${M(e, "field.area_id")}</span>
            <select
              @change=${(e) => this._set("area_id", e.target.value)}
            >
              ${(n.config?.areas ?? []).map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === t.area_id)}>
                    ${e.name}
                  </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${M(e, "field.channel")}</span>
            <select
              @change=${(e) => {
			let n = e.target.value;
			this._draft = xt({
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
				} : {},
				...n === "key" ? { always_on: !1 } : {},
				...n === "intrusion" ? {} : { follows: [] }
			});
		}}
            >
              ${[
			"intrusion",
			"key",
			"technical"
		].map((n) => C`<option .value=${n} .selected=${U(n === t.channel)}>
                    ${M(e, `channel.${n}`)}
                  </option>`)}
            </select>
          </label>
          ${a ? C`
                <label class="field">
                  <span class="lbl">${M(e, "field.entry_mode")}</span>
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
		].map((n) => C`<option .value=${n} .selected=${U(n === t.entry_mode)}>
                          ${M(e, `entry_mode.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${M(e, `entry_mode_hint.${t.entry_mode}`)}</span>
                </label>
                <label class="field">
                  <span class="lbl">${M(e, "field.entry_delay")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${r?.bounds.entry_delay?.[1] ?? 300}
                    placeholder=${M(e, "zones.inherit_seconds", { n: i?.default_entry_delay ?? 30 })}
                    .value=${t.entry_delay == null ? "" : String(t.entry_delay)}
                    @input=${(e) => this._set("entry_delay", H(e.target.value))}
                  />
                  <span class="hint">${M(e, "zones.entry_delay_hint")}</span>
                </label>
                <label class="field">
                  <span class="lbl">${M(e, "field.alarm_kind")}</span>
                  <select
                    @change=${(e) => this._set("alarm_kind", e.target.value)}
                  >
                    ${[
			"intrusion",
			"tamper",
			"panic"
		].map((n) => C`<option .value=${n} .selected=${U(n === t.alarm_kind)}>
                          ${M(e, `alarm_kind.${n}`)}
                        </option>`)}
                  </select>
                </label>
                <label class="field">
                  <span class="lbl">${M(e, "field.arm_policy")}</span>
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
		].map((n) => C`<option .value=${n} .selected=${U(n === t.arm_policy)}>
                          ${M(e, `arm_policy.${n}`)}
                        </option>`)}
                  </select>
                  <span class="hint">${M(e, `arm_policy_hint.${t.arm_policy}`)}</span>
                </label>
                ${t.arm_policy === "arm_after_closing" ? C`<label class="field">
                      <span class="lbl">${M(e, "field.arm_hold_timeout")}</span>
                      <input
                        type="number"
                        min=${r?.bounds.arm_hold_timeout?.[0] ?? 60}
                        max=${r?.bounds.arm_hold_timeout?.[1] ?? 1800}
                        placeholder=${M(e, "zones.inherit_seconds", { n: n.config?.settings.arm_hold_timeout ?? 300 })}
                        .value=${t.arm_hold_timeout == null ? "" : String(t.arm_hold_timeout)}
                        @input=${(e) => this._set("arm_hold_timeout", H(e.target.value))}
                      />
                      <span class="hint">${M(e, "zones.hold_hint")}</span>
                    </label>` : T}
              ` : T}
          <label class="field">
            <span class="lbl">${M(e, "field.supervision_timeout")}</span>
            <input
              type="number"
              min=${r?.bounds.supervision_timeout?.[0] ?? 60}
              placeholder=${M(e, "zones.off")}
              .value=${t.supervision_timeout == null ? "" : String(t.supervision_timeout)}
              @input=${(e) => this._set("supervision_timeout", H(e.target.value))}
            />
            <span class="hint">${M(e, "zones.supervision_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${M(e, "field.battery_entity_id")}</span>
            <select
              @change=${(e) => this._set("battery_entity_id", e.target.value || null)}
            >
              <option value="" .selected=${U(!t.battery_entity_id)}>
                ${M(e, "zones.no_battery")}
              </option>
              ${ht(n.hass).map((e) => C`<option
                  .value=${e.id}
                  .selected=${U(e.id === t.battery_entity_id)}
                >
                  ${e.name}
                </option>`)}
            </select>
            <span class="hint">${M(e, "zones.battery_hint")}</span>
          </label>
        </div>
        ${this._renderCameras(e, t)}
        <div class="checks">
          ${a ? o("always_on", "zones.always_on_hint") : T}
          ${a ? o("bypassable", "zones.bypassable_hint") : T}
          ${a && !t.always_on ? o("chime", "zones.chime_hint") : T}
          ${a ? o("silent", "zones.silent_hint") : T}
          ${o("allow_arm_when_faulted", "zones.allow_faulted_hint")}
          ${o("enabled", "zones.enabled_hint")}
        </div>
        ${W(n, t.response_profile_id, (e) => this._set("response_profile_id", e), M(e, "profiles.zone_hint"))}
        ${t.channel === "technical" ? C`<p class="hint">${M(e, "zones.technical_hint")}</p>
              <div class="notice fire" role="note">${M(e, "zones.fire_statement")}</div>` : T}
      </fieldset>
    `;
	}
	_renderCameras(e, t) {
		let n = this.ctx, r = t.camera_entity_ids ?? [], i = K(n.hass, ["camera"]), a = (e) => i.find((t) => t.id === e)?.name ?? e, o = (e, t) => {
			let n = [...r], [i] = n.splice(e, 1);
			n.splice(e + t, 0, i), this._set("camera_entity_ids", n);
		};
		return C`<div class="field cameras">
      <span class="lbl">${M(e, "field.camera_entity_ids")}</span>
      ${r.length ? C`<ol class="camera-list" role="list">
            ${r.map((t, n) => C`<li>
                <span class="camera-rank">${n + 1}</span>
                <span class="camera-name">${a(t)}</span>
                <button
                  class="btn sm"
                  ?disabled=${n === 0}
                  aria-label=${M(e, "zones.camera_up")}
                  title=${M(e, "zones.camera_up")}
                  @click=${() => o(n, -1)}
                >
                  ↑
                </button>
                <button
                  class="btn sm"
                  ?disabled=${n === r.length - 1}
                  aria-label=${M(e, "zones.camera_down")}
                  title=${M(e, "zones.camera_down")}
                  @click=${() => o(n, 1)}
                >
                  ↓
                </button>
                <button
                  class="btn sm"
                  @click=${() => this._set("camera_entity_ids", r.filter((e) => e !== t))}
                >
                  ${M(e, "zones.camera_remove")}
                </button>
              </li>`)}
          </ol>` : T}
      <select
        aria-label=${M(e, "zones.camera_add")}
        @change=${(e) => {
			let t = e.target;
			t.value && this._set("camera_entity_ids", [...r, t.value]), t.value = "";
		}}
      >
        <option value="" selected>${M(e, "zones.camera_add")}</option>
        ${i.filter((e) => !r.includes(e.id)).map((e) => C`<option .value=${e.id}>${e.name}</option>`)}
      </select>
      <span class="hint"
        >${r.length ? M(e, "zones.cameras_hint") : M(e, "zones.cameras_none_hint")}</span
      >
    </div>`;
	}
	_renderVerification(e, t) {
		let n = this.ctx, r = n.meta, [i, a] = r?.bounds.window ?? [1, 3600], o = n.config?.groups.find((e) => e.members.includes(t.id ?? "")), s = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.members.forEach((e) => s.add(e));
		for (let e of n.config?.zones ?? []) e.id && e.cross_zone_id && e.id !== t.id && e.cross_zone_id !== t.id && (s.add(e.id), s.add(e.cross_zone_id));
		let c = (n.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && (!s.has(e.id ?? "") || e.id === t.cross_zone_id)), l = new Map(n.config?.areas.map((e) => [e.id, e.name])), u = (e) => (t) => {
			let n = H(t.target.value);
			this._set(e, n ?? (e === "trigger_count" ? 1 : 60));
		};
		return C`
      <fieldset>
        <legend>${M(e, "zones.verification_title")}</legend>
        ${o ? C`<p class="notice">${M(e, "zones.in_group", { group: o.name })}</p>` : C`<div class="grid-form">
              <label class="field">
                <span class="lbl">${M(e, "field.cross_zone_id")}</span>
                <select
                  @change=${(e) => this._set("cross_zone_id", e.target.value || null)}
                >
                  <option value="" .selected=${U(!t.cross_zone_id)}>
                    ${M(e, "zones.no_cross_zone")}
                  </option>
                  ${c.map((n) => C`<option .value=${n.id ?? ""} .selected=${U(n.id === t.cross_zone_id)}>
                      ${M(e, "zones.entity", {
			name: n.name,
			entity: l.get(n.area_id) ?? n.area_id
		})}
                    </option>`)}
                </select>
                <span class="hint">${M(e, "zones.cross_zone_hint")}</span>
              </label>
              ${t.cross_zone_id ? C`<label class="field">
                    <span class="lbl">${M(e, "field.cross_zone_window")}</span>
                    <input
                      type="number"
                      min=${i}
                      max=${a}
                      .value=${String(t.cross_zone_window)}
                      @input=${u("cross_zone_window")}
                    />
                    <span class="hint">${M(e, "groups.window_hint")}</span>
                  </label>` : T}
            </div>`}
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${M(e, "field.trigger_count")}</span>
            <input
              type="number"
              min="1"
              max=${r?.bounds.trigger_count?.[1] ?? 10}
              .value=${String(t.trigger_count)}
              @input=${u("trigger_count")}
            />
            <span class="hint">${M(e, "zones.trigger_count_hint")}</span>
          </label>
          ${t.trigger_count > 1 ? C`<label class="field">
                <span class="lbl">${M(e, "field.trigger_window")}</span>
                <input
                  type="number"
                  min=${i}
                  max=${a}
                  .value=${String(t.trigger_window)}
                  @input=${u("trigger_window")}
                />
                <span class="hint">${M(e, "groups.window_hint")}</span>
              </label>` : T}
        </div>
      </fieldset>
    `;
	}
	_renderFollows(e, t) {
		let n = new Map(this.ctx?.config?.areas.map((e) => [e.id, e.name])), r = (this.ctx?.config?.zones ?? []).filter((e) => e.id !== t.id && e.channel === "intrusion" && e.entry_mode === "delayed"), i = (e, n) => this._set("follows", n ? [.../* @__PURE__ */ new Set([...t.follows, e])] : t.follows.filter((t) => t !== e));
		return C`
      <fieldset>
        <legend>${M(e, "field.follows")}</legend>
        ${r.length ? r.map((r) => C`<label class="check">
                <input
                  type="checkbox"
                  .checked=${U(t.follows.includes(r.id ?? ""))}
                  @change=${(e) => i(r.id ?? "", e.target.checked)}
                />
                <span>
                  ${M(e, "zones.entity", {
			name: r.name,
			entity: n.get(r.area_id) ?? r.area_id
		})}
                </span>
              </label>`) : C`<p class="hint">${M(e, "zones.no_delayed_zones")}</p>`}
        <p class="hint">${M(e, "zones.follows_hint")}</p>
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
		return C`
      <fieldset>
        <legend>${M(e, "zones.key_title")}</legend>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${M(e, "field.on_activate")}</span>
            <select
              @change=${(e) => r({ on_activate: e.target.value })}
            >
              ${[
			"arm",
			"disarm",
			"toggle"
		].map((t) => C`<option .value=${t} .selected=${U(t === n.on_activate)}>
                    ${M(e, `key_command.${t}`)}
                  </option>`)}
            </select>
          </label>
          ${n.on_activate === "disarm" ? T : C`<label class="field">
                <span class="lbl">${M(e, "field.scenario_id")}</span>
                <select
                  @change=${(e) => r({ scenario_id: e.target.value || null })}
                >
                  <option value="" .selected=${U(!n.scenario_id)}>
                    ${M(e, "zones.pick_scenario")}
                  </option>
                  ${i.map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === n.scenario_id)}>
                        ${e.name}
                      </option>`)}
                </select>
              </label>`}
          <label class="field">
            <span class="lbl">${M(e, "zones.key_person")}</span>
            <select
              @change=${(e) => r({ user_id: e.target.value || null })}
            >
              <option value="" .selected=${U(!n.user_id)}>
                ${M(e, "zones.key_person_none")}
              </option>
              ${(this.ctx?.config?.users ?? []).map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === n.user_id)}>
                    ${e.name}
                  </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${M(e, "field.on_deactivate")}</span>
            <select
              @change=${(e) => r({ on_deactivate: e.target.value })}
            >
              ${["none", "disarm"].map((t) => C`<option .value=${t} .selected=${U(t === n.on_deactivate)}>
                    ${M(e, `key_release.${t}`)}
                  </option>`)}
            </select>
          </label>
        </div>
        <p class="hint">${M(e, "zones.key_hint")}</p>
      </fieldset>
    `;
	}
	static {
		this.styles = [
			N,
			P,
			o`
      .cameras {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        margin-top: 14px;
        max-width: 480px;
      }
      .cameras > .lbl {
        font-weight: 500;
      }
      .camera-list {
        margin: 4px 0 8px;
        padding: 0;
        list-style: none;
      }
      .camera-rank {
        min-width: 1.5em;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .camera-list li {
        display: flex;
        align-items: center;
        gap: 6px;
        margin: 4px 0;
      }
      .camera-name {
        flex: 1;
      }
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
        grid-template-columns: repeat(auto-fill, minmax(min(260px, 100%), 1fr));
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
customElements.get("foyer-page-zones") || customElements.define("foyer-page-zones", Ct);
//#endregion
//#region src/panel/pages/scenarios.ts
var wt = {
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
}, Tt = class extends A {
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
		this._busy || (this._draft = e ? structuredClone(e) : {
			...wt,
			areas: []
		}, this._problems = [], L(this));
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
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0);
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
		if (!e?.config) return T;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = e.config.scenarios.map((e) => e.ha_master_state);
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "scenarios.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${M(t, "scenarios.add")}
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>${M(t, "field.name")}</th>
                <th>${M(t, "field.areas")}</th>
                <th>${M(t, "field.ha_master_state")}</th>
                <th>${M(t, "field.exit_delay_override")}</th>
                <th>${M(t, "field.siren_duration_override")}</th>
              </tr>
            </thead>
            <tbody>
              ${e.config.scenarios.map((i) => C`<tr
                  class="clickable"
 tabindex="0"
 @keydown=${B}
                  aria-selected=${this._draft?.id === i.id ? "true" : "false"}
                  @click=${() => this._edit(i)}
                >
                  <td>
                    <strong>${i.name}</strong>
                    ${i.id === e.status.active_scenario_id ? C`<span class="state armed">${M(t, "scenarios.active")}</span>` : T}
                  </td>
                  <td>
                    ${i.areas.map((e) => C`<span class="tag">${n.get(e) ?? e}</span>`)}
                  </td>
                  <td>
                    <span>${M(t, `ha_state.${i.ha_master_state}`)}</span>
                    ${r.filter((e) => e === i.ha_master_state).length > 1 ? C`<div class="hint">${M(t, "scenarios.shared_mode")}</div>` : T}
                  </td>
                  <td>
                    ${i.exit_delay_override == null ? M(t, "scenarios.area_default") : M(t, "common.seconds", { n: i.exit_delay_override })}
                  </td>
                  <td>
                    ${i.siren_duration_override == null ? M(t, "scenarios.global_default") : M(t, "common.seconds", { n: i.siren_duration_override })}
                  </td>
                </tr>`)}
            </tbody>
          </table>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : T}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.meta, i = (e, n) => this._set("areas", n ? [...t.areas, e] : t.areas.filter((t) => t !== e));
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "scenarios.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.ha_master_state")}</span>
              <select
                @change=${(e) => this._set("ha_master_state", e.target.value)}
              >
                ${(r?.ha_states ?? []).map((n) => C`<option .value=${n} .selected=${U(n === t.ha_master_state)}>
                      ${M(e, `ha_state.${n}`)}
                    </option>`)}
              </select>
              <span class="hint">${M(e, "scenarios.mode_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.exit_delay_override")}</span>
              <input
                type="number"
                min="0"
                max=${r?.bounds.exit_delay?.[1] ?? 300}
                placeholder=${M(e, "scenarios.area_default")}
                .value=${t.exit_delay_override == null ? "" : String(t.exit_delay_override)}
                @input=${(e) => this._set("exit_delay_override", H(e.target.value))}
              />
              <span class="hint">${M(e, "scenarios.exit_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.siren_duration_override")}</span>
              <input
                type="number"
                min="1"
                max=${r?.bounds.siren_duration?.[1] ?? 900}
                placeholder=${M(e, "scenarios.global_seconds", { n: n.config?.settings.siren_duration ?? 180 })}
                .value=${t.siren_duration_override == null ? "" : String(t.siren_duration_override)}
                @input=${(e) => this._set("siren_duration_override", H(e.target.value))}
              />
              <span class="hint">${M(e, "scenarios.siren_hint")}</span>
            </label>
            ${W(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e))}
            ${ot(e, t, (e, t) => this._set(e, t), n.status.security.enforced)}
          </div>
          <fieldset>
            <legend>${M(e, "field.areas")}</legend>
            ${(n.config?.areas ?? []).map((e) => C`<label class="check">
                <input
                  type="checkbox"
                  .checked=${U(t.areas.includes(e.id ?? ""))}
                  @change=${(t) => i(e.id ?? "", t.target.checked)}
                />
                <span>${e.name}</span>
              </label>`)}
            <p class="hint">${M(e, "scenarios.areas_hint")}</p>
          </fieldset>
          ${this._renderAllowedUsers(e, t)}
          ${this._problems.length ? C`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
                </ul>
              </div>` : T}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${M(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${M(e, "common.cancel")}
            </button>
            ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          </div>
        </div>
      </div>
    `;
	}
	_renderAllowedUsers(e, t) {
		let n = this.ctx?.config?.users ?? [], r = t.allowed_user_ids, i = (e, t) => {
			let n = new Set(r ?? []);
			t ? n.add(e) : n.delete(e), this._set("allowed_user_ids", [...n]);
		};
		return C`
      <fieldset>
        <legend>${M(e, "field.allowed_user_ids")}</legend>
        <label class="check">
          <input
            type="checkbox"
            .checked=${U(r === null)}
            @change=${(e) => this._set("allowed_user_ids", e.target.checked ? null : n.map((e) => e.id ?? "").filter(Boolean))}
          />
          <span>${M(e, "scenarios.everyone")}</span>
        </label>
        ${r === null ? T : n.map((t) => C`<label class="check">
                <input
                  type="checkbox"
                  .checked=${U(r.includes(t.id ?? ""))}
                  ?disabled=${r.length === 1 && r.includes(t.id ?? "")}
                  title=${r.length === 1 ? M(e, "scenarios.last_user") : ""}
                  @change=${(e) => i(t.id ?? "", e.target.checked)}
                />
                <span>${t.name}</span>
              </label>`)}
        <p class="hint">${M(e, "scenarios.allowed_users_hint")}</p>
      </fieldset>
    `;
	}
	static {
		this.styles = [
			N,
			P,
			o`
      td .state {
        margin-left: 8px;
      }
    `
		];
	}
};
customElements.get("foyer-page-scenarios") || customElements.define("foyer-page-scenarios", Tt);
//#endregion
//#region src/panel/pages/profiles.ts
var Et = {
	alarm: [
		"entry_started",
		"triggered",
		"siren_cutoff",
		"alarm_ended",
		"alarm_cleared",
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
		"chime_switched",
		"duress"
	],
	system: [
		"zone_fault",
		"low_battery",
		"ha_restarted",
		"walk_test_started",
		"walk_test_ended",
		"escalation_exhausted",
		"chime"
	],
	health: [
		"system_power_lost",
		"system_power_restored",
		"notification_channel_down",
		"notification_channel_restored",
		"watchdog_unreachable",
		"watchdog_recovered",
		"rf_interference_suspected",
		"rf_interference_cleared",
		"radio_coordinator_down",
		"radio_coordinator_up"
	]
}, Dt = ["companion", "telegram"], Ot = [
	"zone",
	"fixed",
	"none"
], kt = [
	"triggered",
	"incident_opened",
	"incident_joined",
	"verification_satisfied",
	"technical_raised"
];
function At(e) {
	let t = e.params.images;
	return typeof t == "string" && Ot.includes(t) ? t : e.params.camera_entity_id ? "fixed" : "none";
}
var jt = ["notify", "persistent_notification"], Mt = [
	"siren",
	"light",
	"switch"
], Nt = [
	"camera",
	"scene",
	"tts"
];
function Pt(e) {
	let t = {};
	return e === "switch" && (t.state = "on"), e === "camera" && (t.mode = "snapshot"), e === "delay" && (t.seconds = 30), (e === "notify" || e === "tts") && (t.message = "{{ zone }}"), e === "notify" && (t.attachment = "companion"), e === "notify" && (t.images = "zone"), {
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
var Ft = [
	{
		key: "alarm",
		moments: ["triggered", "incident_joined"],
		images: "zone"
	},
	{
		key: "technical",
		moments: ["technical_raised"],
		images: "zone"
	},
	{
		key: "armed",
		moments: ["armed"],
		images: "none"
	},
	{
		key: "disarmed",
		moments: ["disarmed"],
		images: "none"
	},
	{
		key: "warning",
		moments: [
			"arm_failed",
			"forced_arm",
			"zone_fault",
			"low_battery"
		],
		images: "none"
	}
];
function It(e) {
	let t = e.params.contacts;
	return Array.isArray(t) ? t.map((e) => typeof e == "string" ? {
		contact_id: e,
		channel_id: null
	} : e) : [];
}
var Lt = class extends A {
	constructor(...e) {
		super(...e), this._open = -1, this._filters = {}, this._jsonErrors = {}, this._problems = [], this._busy = !1, this._tested = {}, this._templating = !1, this._templateContacts = [];
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_open: { state: !0 },
			_filters: { state: !0 },
			_jsonErrors: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_tested: { state: !0 },
			_confirming: { state: !0 },
			_templating: { state: !0 },
			_templateContacts: { state: !0 }
		};
	}
	_fromTemplate(e) {
		let t = this._templateContacts.map((e) => ({
			contact_id: e,
			channel_id: null
		})), n = Ft.map(({ key: n, moments: r, images: i }) => {
			let a = Pt("notify");
			return {
				...a,
				name: M(e, `profiles.template.${n}.name`),
				moments: r,
				params: {
					...a.params,
					title: M(e, `profiles.template.${n}.title`),
					message: M(e, `profiles.template.${n}.message`),
					images: i,
					contacts: t
				}
			};
		});
		this._templating = !1, this._templateContacts = [], this._edit({
			name: M(e, "profiles.template.profile_name"),
			severity: 1,
			actions: n
		});
	}
	_renderTemplate(e) {
		let t = this.ctx?.config?.contacts ?? [], n = this._templateContacts;
		return C`<div class="card editor">
      <div class="card-hd"><h2>${M(e, "profiles.template.title")}</h2></div>
      <div class="card-bd">
        <p class="hint">${M(e, "profiles.template.intro")}</p>
        ${t.length ? C`<div class="field">
                <span class="lbl">${M(e, "profiles.template.contacts")}</span>
                ${t.map((e) => C`<label class="check"
                      ><input
                        type="checkbox"
                        .checked=${U(n.includes(e.id ?? ""))}
                        @change=${(t) => {
			let n = e.id ?? "", r = this._templateContacts.filter((e) => e !== n);
			this._templateContacts = t.target.checked ? [...r, n] : r;
		}}
                      />
                      ${e.name}</label
                    >`)}
              </div>
              <p class="hint">${M(e, "profiles.template.telegram_hint")}</p>` : C`<p class="hint">${M(e, "profiles.template.no_contacts")}</p>`}
        <div class="actions">
          <button
            class="btn primary"
            ?disabled=${!n.length}
            @click=${() => this._fromTemplate(e)}
          >
            ${M(e, "profiles.template.create")}
          </button>
          <button
            class="btn"
            @click=${() => {
			this._templating = !1, this._templateContacts = [];
		}}
          >
            ${M(e, "common.cancel")}
          </button>
        </div>
      </div>
    </div>`;
	}
	_edit(e) {
		this._busy || (this._draft = e ? structuredClone(e) : {
			name: "",
			severity: 1,
			actions: []
		}, this._open = -1, this._problems = [], this._filters = {}, this._confirming = void 0, this._jsonErrors = {}, L(this));
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
			actions: [...this._draft.actions, Pt(e)]
		}, this._open = this._draft.actions.length - 1);
	}
	_removeAction(e) {
		if (!this._draft) return;
		let t = this._draft.actions.filter((t, n) => n !== e);
		this._draft = {
			...this._draft,
			actions: t
		}, this._open = -1, this._filters = {}, this._jsonErrors = {};
	}
	_moveAction(e, t) {
		if (!this._draft) return;
		let n = [...this._draft.actions], r = e + t;
		r < 0 || r >= n.length || ([n[e], n[r]] = [n[r], n[e]], this._draft = {
			...this._draft,
			actions: n
		}, this._open = r, this._filters = {}, this._jsonErrors = {});
	}
	async _save() {
		if (this.ctx && this._draft) {
			if (Object.values(this._jsonErrors).some(Boolean)) {
				this._problems = [{
					code: "data_invalid",
					kind: "profile",
					ref: null,
					field: "data"
				}];
				return;
			}
			this._busy = !0;
			try {
				let e = await this.ctx.save("profile", this._draft);
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0);
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
		if (!e?.config) return T;
		let t = e.strings, n = e.config.profiles ?? [];
		return C`
      <p class="page-intro">${M(t, "profiles.intro")}</p>
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "profiles.title")}</h2>
          <div class="hd-buttons">
            <button class="btn" @click=${() => this._templating = !this._templating}>
              ${M(t, "profiles.template.button")}
            </button>
            <button class="btn primary" @click=${() => this._edit()}>${M(t, "profiles.add")}</button>
          </div>
        </div>
        ${n.length ? C`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${M(t, "field.name")}</th>
                      <th>${M(t, "field.actions")}</th>
                      <th>${M(t, "field.severity")}</th>
                      <th>${M(t, "profiles.used_by")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${n.map((e) => C`<tr
                          class="clickable"
 tabindex="0"
 @keydown=${B}
                          aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                          @click=${() => this._edit(e)}
                        >
                          <td><strong>${e.name}</strong></td>
                          <td>
                            ${e.actions.length ? e.actions.map((e) => C`<span class="tag"
                                        >${M(t, `action_kind.${e.kind}`)}</span
                                      > `) : C`<span class="muted">${M(t, "profiles.no_actions")}</span>`}
                          </td>
                          <td>${e.severity}</td>
                          <td class="muted">${this._usedBy(t, e)}</td>
                        </tr>`)}
                  </tbody>
                </table>
              </div>` : C`<div class="empty">${M(t, "profiles.none")}</div>`}
      </div>
      ${this._templating ? this._renderTemplate(t) : T}
      ${this._draft ? this._renderEditor(t, this._draft) : T}
    `;
	}
	_usedBy(e, t) {
		let n = this.ctx.config, r = [];
		n.settings.default_profile_id === t.id && r.push(M(e, "profiles.used_default")), n.settings.technical_profile_id === t.id && r.push(M(e, "profiles.used_technical"));
		for (let e of [
			n.areas,
			n.zones,
			n.scenarios,
			n.groups
		]) for (let n of e) n.response_profile_id === t.id && r.push(n.name);
		return r.length ? r.join(", ") : M(e, "profiles.unused");
	}
	_renderEditor(e, t) {
		let n = this.ctx?.meta?.bounds.severity ?? [1, 10];
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "profiles.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.severity")}</span>
              <input
                type="number"
                min=${n[0]}
                max=${n[1]}
                .value=${String(t.severity)}
                @input=${(e) => V(e, (e) => this._set("severity", e))}
              />
              <span class="hint">${M(e, "profiles.severity_hint")}</span>
            </label>
          </div>

          <div class="actions-list">
            ${t.actions.map((t, n) => this._renderAction(e, t, n))}
          </div>
          ${t.actions.length ? T : C`<p class="hint">${M(e, "profiles.no_actions")}</p>`}

          <div class="add-action">
            <label class="field">
              <span class="lbl">${M(e, "profiles.add_action")}</span>
              <select
                .value=${""}
                @change=${(e) => {
			let t = e.target;
			t.value && this._addAction(t.value), t.value = "";
		}}
              >
                <option value=""></option>
                ${(this.ctx?.meta?.action_kinds ?? []).map((t) => C`<option .value=${t}>${M(e, `action_kind.${t}`)}</option>`)}
              </select>
            </label>
          </div>
          <p class="hint">${M(e, "profiles.escalation_later")}</p>

          ${this._problems.length ? C`<div class="problems" role="alert">
                  <ul>
                    ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
                  </ul>
                </div>` : T}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${M(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${M(e, "common.cancel")}
            </button>
            ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          </div>
        </div>
      </div>
    `;
	}
	_renderContacts(e, t, n) {
		let r = this.ctx?.config?.contacts ?? [], i = It(t);
		if (!r.length) return C`<span class="hint">${M(e, "profiles.no_contacts")}</span>`;
		let a = (e) => {
			this._setParam(n, "contacts", e.length ? e : null), e.length && this._setParam(n, "service", null);
		};
		return C`<div class="field">
      <span class="lbl">${M(e, "field.contacts")}</span>
      ${r.map((t) => {
			let n = i.find((e) => e.contact_id === t.id);
			return C`<div class="contact-row">
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(n !== void 0)}
              @change=${(e) => a(e.target.checked ? [...i, {
				contact_id: t.id,
				channel_id: null
			}] : i.filter((e) => e.contact_id !== t.id))}
            />
            <span>${t.name}</span>
          </label>
          ${n ? C`<select
                @change=${(e) => a(i.map((n) => n.contact_id === t.id ? {
				...n,
				channel_id: e.target.value || null
			} : n))}
              >
                <option value="" .selected=${U(!n.channel_id)}>
                  ${M(e, "profiles.highest_channel")}
                </option>
                ${t.channels.map((t) => C`<option
                    .value=${t.id ?? ""}
                    .selected=${U(t.id === n.channel_id)}
                  >
                    ${M(e, `channel_kind.${t.kind}`)} · ${t.service}
                  </option>`)}
              </select>` : T}
        </div>`;
		})}
      <span class="hint">${M(e, "profiles.contacts_hint")}</span>
    </div>`;
	}
	_renderEscalation(e, t, n) {
		let r = this.ctx?.meta?.escalation_moments ?? [];
		if (!jt.includes(t.kind)) return T;
		if (!t.moments.length || !t.moments.every((e) => r.includes(e))) return t.escalation_offset === null ? T : C`<span class="hint">${M(e, "profiles.escalation_moment_hint")}</span>`;
		let i = this.ctx?.meta?.bounds.escalation_offset ?? [0, 3600];
		return C`<label class="field">
      <span class="lbl">${M(e, "field.escalation_offset")}</span>
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
      <span class="hint">${M(e, "profiles.escalation_hint")}</span>
    </label>`;
	}
	_renderAction(e, t, n) {
		let r = this._open === n;
		return C`
      <div class="action" ?data-open=${r}>
        <button
          class="action-hd"
          @click=${() => {
			this._open = r ? -1 : n, this._jsonErrors = {};
		}}
        >
          <span class="tag">${M(e, `action_kind.${t.kind}`)}</span>
          <span class="summary">${this._summary(e, t)}</span>
          <span class="moments">${this._momentSummary(e, t)}</span>
          ${t.conditions.length ? C`<span class="cond">${t.conditions.length}</span>` : T}
        </button>
        ${r ? C`<div class="action-bd">
                ${this._renderParams(e, t, n)} ${this._renderMoments(e, t, n)}
                ${this._renderDuress(e, t)} ${this._renderEscalation(e, t, n)}
                ${this._renderConditions(e, t, n)}
                <div class="actions">
                  <button
                    class="btn"
                    aria-label=${M(e, "common.move_up")}
                    title=${M(e, "common.move_up")}
                    @click=${() => this._moveAction(n, -1)}
                  >
                    &uarr;
                  </button>
                  <button
                    class="btn"
                    aria-label=${M(e, "common.move_down")}
                    title=${M(e, "common.move_down")}
                    @click=${() => this._moveAction(n, 1)}
                  >
                    &darr;
                  </button>
                  ${this._renderTestButton(e, t)}
                  <button class="btn danger" @click=${() => this._removeAction(n)}>
                    ${M(e, "profiles.delete_action")}
                  </button>
                </div>
              </div>` : T}
      </div>
    `;
	}
	_renderTestButton(e, t) {
		if (t.kind === "delay" || !t.id || !this._draft?.id) return T;
		let n = this.ctx?.config?.profiles.find((e) => e.id === this._draft?.id)?.actions.find((e) => e.id === t.id);
		if (!n || JSON.stringify(n) !== JSON.stringify(t)) return C`<span class="hint">${M(e, "profiles.test_after_save")}</span>`;
		let r = t.id, i = this._tested[r];
		return this._confirming === r ? C`
        <button
          class="btn primary"
          ?disabled=${this._busy}
          @click=${() => void this._testAction(t)}
        >
          ${M(e, "action_test.confirm_short")}
        </button>
        <button class="btn" @click=${() => this._confirming = void 0}>
          ${M(e, "common.cancel")}
        </button>
      ` : C`
      <button class="btn" ?disabled=${this._busy} @click=${() => this._confirming = r}>
        ${M(e, "action_test.test")}
      </button>
      ${i ? C`<span class="state ${i.ok ? "closed" : "fault"}" title=${i.error ?? ""}>
            ${M(e, i.ok ? "action_test.ok" : "action_test.failed")}
          </span>` : T}
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
			} catch (t) {
				this._tested = {
					...this._tested,
					[e.id]: {
						ok: !1,
						error: String(t?.message ?? t)
					}
				};
			} finally {
				this._busy = !1;
			}
		}
	}
	_momentSummary(e, t) {
		let n = t.moments.map((t) => M(e, `moment.${t}`));
		return n.length ? n.length <= 3 ? n.join(", ") : M(e, "profiles.moments_more", {
			moments: n.slice(0, 2).join(", "),
			count: n.length - 2
		}) : M(e, "profiles.no_moments");
	}
	_summary(e, t) {
		let n = t.params;
		if (t.kind === "delay") return M(this.ctx.strings, "common.seconds", { n: String(n.seconds ?? 0) });
		if (t.kind === "call_service") return `${n.domain ?? ""}.${n.service ?? ""}`;
		if (t.kind === "notify") return String(n.service ?? "");
		if (t.kind === "persistent_notification") return String(n.message ?? M(e, "profiles.inherit"));
		let r = n.entity_ids ?? n.entity_id ?? "";
		return Array.isArray(r) ? r.join(", ") : String(r);
	}
	_entities(e) {
		return K(this.ctx.hass, e);
	}
	_suggested(e, t, n, r, i, a) {
		let o = `foyer-${r}-${n}`;
		return C`<label class="field">
      <span class="lbl">${M(e, `field.${r}`)}</span>
      <input
        list=${o}
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      <datalist id=${o}>
        ${i.map((e) => C`<option .value=${e.id}>
            ${e.name === e.id ? e.id : `${e.name} · ${e.id}`}
          </option>`)}
      </datalist>
      <span class="hint">${a ?? M(e, "profiles.pick_or_type")}</span>
    </label>`;
	}
	_text(e, t, n, r, i) {
		return C`<label class="field">
      <span class="lbl">${M(e, `field.${r}`)}</span>
      <input
        .value=${String(t.params[r] ?? "")}
        @input=${(e) => this._setParam(n, r, e.target.value)}
      />
      ${i ? C`<span class="hint">${i}</span>` : T}
    </label>`;
	}
	_number(e, t, n, r, i) {
		return C`<label class="field">
      <span class="lbl">${M(e, `field.${r}`)}</span>
      <input
        type="number"
        .value=${t.params[r] == null ? "" : String(t.params[r])}
        @input=${(e) => this._setParam(n, r, H(e.target.value))}
      />
      ${i ? C`<span class="hint">${i}</span>` : T}
    </label>`;
	}
	_picker(e, t, n, r, i, a) {
		let o = [...this._entities(i)], s = t.params[r], c = new Set(Array.isArray(s) ? s : s ? [String(s)] : []);
		for (let e of c) o.some((t) => t.id === e) || o.push({
			id: e,
			name: e
		});
		if (!a) return C`<label class="field">
        <span class="lbl">${M(e, `field.${r}`)}</span>
        <select
          @change=${(e) => this._setParam(n, r, e.target.value || null)}
        >
          <option value=""></option>
          ${o.map((e) => C`<option .value=${e.id} .selected=${U(c.has(e.id))}>${e.name}</option>`)}
        </select>
      </label>`;
		let l = `${n}:${r}`, u = (this._filters[l] ?? "").toLowerCase().split(/\s+/).filter(Boolean), d = o.filter((e) => {
			if (c.has(e.id)) return !0;
			let t = `${e.name} ${e.id}`.toLowerCase();
			return u.every((e) => t.includes(e));
		});
		return C`<fieldset class="entities wide">
      <legend>${M(e, `field.${r}`)}</legend>
      ${o.length > 8 ? C`<input
            class="filter"
            type="search"
            .value=${this._filters[l] ?? ""}
            placeholder=${M(e, "profiles.filter")}
            @input=${(e) => {
			this._filters = {
				...this._filters,
				[l]: e.target.value
			};
		}}
          />` : T}
      <div class="entity-list">
        ${d.map((t) => C`<label class="check">
            <input
              type="checkbox"
              .checked=${U(c.has(t.id))}
              @change=${(e) => {
			let i = e.target.checked, a = new Set(c);
			i ? a.add(t.id) : a.delete(t.id), this._setParam(n, r, [...a]);
		}}
            />
            <span>${M(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}</span>
          </label>`)}
        ${d.length ? T : C`<p class="hint">${M(e, "profiles.no_match")}</p>`}
      </div>
    </fieldset>`;
	}
	_renderParams(e, t, n) {
		let r = this.ctx?.meta?.action_domains[t.kind] ?? [], i = M(e, "profiles.message_hint", { variables: (this.ctx?.meta?.template_variables ?? []).map((e) => `{{ ${e} }}`).join(" ") }), a = [];
		switch (Mt.includes(t.kind) && a.push(this._picker(e, t, n, "entity_ids", r, !0)), Nt.includes(t.kind) && a.push(this._picker(e, t, n, "entity_id", r, !1)), t.kind) {
			case "notify":
				a.push(this._renderContacts(e, t, n)), It(t).length || a.push(this._suggested(e, t, n, "service", q(this.ctx.hass), M(e, "profiles.notify_hint"))), a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i)), a.push(this._renderImages(e, t, n)), (At(t) === "zone" || At(t) === "fixed" && t.params.camera_entity_id) && (a.push(this._select(e, t, n, "attachment", Dt, (t) => M(e, `attachment.${t}`))), a.push(C`<span class="hint"
              >${M(e, t.params.attachment === "telegram" ? "profiles.attach_hint_telegram" : "profiles.attach_hint")}</span
            >`));
				break;
			case "persistent_notification":
				a.push(this._text(e, t, n, "title")), a.push(this._text(e, t, n, "message", i));
				break;
			case "siren":
				a.push(this._number(e, t, n, "duration", M(e, "profiles.siren_duration_hint"))), a.push(this._renderTone(e, t, n));
				break;
			case "light":
				a.push(this._number(e, t, n, "brightness")), a.push(this._select(e, t, n, "flash", [
					"",
					"short",
					"long"
				], (t) => M(e, `profiles.flash_${t || "none"}`)));
				break;
			case "camera":
				a.push(this._select(e, t, n, "mode", ["snapshot", "record"], (t) => M(e, `camera_mode.${t}`))), a.push(this._number(e, t, n, "duration", M(e, "profiles.camera_hint")));
				break;
			case "switch":
				a.push(this._select(e, t, n, "state", ["on", "off"], (t) => M(e, `on_off.${t}`))), a.push(this._number(e, t, n, "revert_after", M(e, "profiles.revert_hint")));
				break;
			case "tts":
				a.push(this._picker(e, t, n, "media_player_entity_ids", ["media_player"], !0)), a.push(this._text(e, t, n, "message", i));
				break;
			case "call_service": {
				let r = String(t.params.domain ?? "");
				a.push(this._suggested(e, t, n, "domain", gt(this.ctx.hass).map((e) => ({
					id: e,
					name: e
				})))), a.push(this._suggested(e, t, n, "service", _t(this.ctx.hass, r).map((e) => ({
					id: e,
					name: e
				})))), a.push(this._json(e, t, n));
				break;
			}
			case "delay": a.push(this._number(e, t, n, "seconds", M(e, "profiles.delay_hint")));
		}
		return C`<div class="grid-form">${a}</div>`;
	}
	_renderTone(e, t, n) {
		let r = t.params.entity_ids, i = Array.isArray(r) ? r : [], a = /* @__PURE__ */ new Set();
		for (let e of i) {
			let t = this.ctx.hass.states[e]?.attributes?.available_tones;
			Array.isArray(t) ? t.forEach((e) => a.add(String(e))) : t && typeof t == "object" && Object.keys(t).forEach((e) => a.add(e));
		}
		return a.size ? this._select(e, t, n, "tone", ["", ...[...a].sort()], (t) => t || M(e, "profiles.default_tone")) : i.length ? C`<label class="field">
            <span class="lbl">${M(e, "field.tone")}</span>
            <input disabled placeholder=${M(e, "profiles.no_tones")} />
            <span class="hint">${M(e, "profiles.no_tones")}</span>
          </label>` : T;
	}
	_renderImages(e, t, n) {
		let r = At(t), i = t.moments.filter((e) => !kt.includes(e));
		return C`<label class="field">
        <span class="lbl">${M(e, "field.images")}</span>
        <select
          @change=${(e) => {
			let r = e.target.value, i = {
				...t.params,
				images: r
			};
			r !== "fixed" && delete i.camera_entity_id, this._setAction(n, { params: i });
		}}
        >
          ${Ot.map((t) => C`<option .value=${t} .selected=${U(t === r)}>
                ${M(e, `images.${t}`)}
              </option>`)}
        </select>
        <span class="hint">${M(e, `images.${r}_hint`)}</span>
      </label>
      ${r === "fixed" ? this._picker(e, t, n, "camera_entity_id", ["camera"], !1) : T}
      ${r === "zone" && i.length ? C`<span class="hint wide"
            >${M(e, "profiles.images_text_alone", { moments: i.map((t) => M(e, `moment.${t}`)).join(", ") })}</span
          >` : T}
      ${r === "zone" && It(t).length ? C`<span class="hint wide">${M(e, "profiles.images_channels")}</span>` : T}`;
	}
	_select(e, t, n, r, i, a) {
		return C`<label class="field">
      <span class="lbl">${M(e, `field.${r}`)}</span>
      <select
        @change=${(e) => this._setParam(n, r, e.target.value || null)}
      >
        ${i.map((e) => C`<option .value=${e} .selected=${U(t.params[r] === e)}>
              ${a(e)}
            </option>`)}
      </select>
    </label>`;
	}
	_json(e, t, n) {
		return C`<label class="field wide">
      <span class="lbl">${M(e, "field.data")}</span>
      <textarea
        rows="4"
        .value=${JSON.stringify(t.params.data ?? {}, null, 2)}
        @change=${(e) => {
			let t = e.target.value.trim();
			try {
				this._setParam(n, "data", t ? JSON.parse(t) : null), this._jsonErrors = {
					...this._jsonErrors,
					[n]: !1
				};
			} catch {
				this._jsonErrors = {
					...this._jsonErrors,
					[n]: !0
				};
			}
		}}
      ></textarea>
      ${this._jsonErrors[n] ? C`<span class="hint bad" role="alert">${M(e, "profiles.json_invalid")}</span>` : T}
      <span class="hint">${M(e, "profiles.call_service_hint")}</span>
    </label>`;
	}
	_renderMoments(e, t, n) {
		let r = new Set(this.ctx?.meta?.future_moments ?? []), i = new Set(this.ctx?.meta?.moments ?? []);
		return C`<div class="moments-grid">
      ${Object.entries(Et).map(([a, o]) => C`<fieldset>
            <legend>${M(e, `moment_group.${a}`)}</legend>
            ${o.filter((e) => i.has(e)).map((i) => C`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${U(t.moments.includes(i))}
                      @change=${(e) => {
			let r = e.target.checked ? [...t.moments, i] : t.moments.filter((e) => e !== i);
			this._setAction(n, { moments: r });
		}}
                    />
                    <span>
                      ${M(e, `moment.${i}`)}
                      ${r.has(i) ? C`<span class="later">${M(e, "profiles.future_moment")}</span>` : T}
                    </span>
                  </label>`)}
          </fieldset>`)}
    </div>`;
	}
	_renderDuress(e, t) {
		if (!t.moments.includes("duress")) return T;
		let n = this.ctx?.config?.settings, r = this._draft, i = !!r?.id && n?.default_profile_id === r?.id, a = (n?.silent_suppresses ?? []).includes(t.kind), o = (e) => C`<span class="hint bad wide" role="alert">${e}</span>`;
		return C`<div class="duress">
      <span class="hint wide">${M(e, "profiles.duress_hint")}</span>
      ${i ? T : o(M(e, "profiles.duress_not_default"))}
      ${t.kind === "persistent_notification" ? o(M(e, "profiles.duress_persistent")) : T}
      ${a ? o(M(e, "profiles.duress_silent", { kind: M(e, `action_kind.${t.kind}`) })) : T}
    </div>`;
	}
	_renderConditions(e, t, n) {
		let r = this.ctx?.meta?.max_conditions ?? 2, i = (e) => this._setAction(n, { conditions: e });
		return C`<fieldset class="conditions">
      <legend>${M(e, "field.conditions")}</legend>
      ${t.conditions.length ? t.conditions.map((r, i) => this._renderCondition(e, t, n, r, i)) : C`<p class="hint">${M(e, "condition.none")}</p>`}
      ${t.conditions.length < r ? C`<div class="actions">
              <button
                class="btn sm"
                @click=${() => i([...t.conditions, {
			kind: "time",
			after: "22:00",
			before: "07:00"
		}])}
              >
                ${M(e, "condition.time")}
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
                ${M(e, "condition.state")}
              </button>
            </div>` : T}
      ${t.conditions.length === 2 ? C`<label class="field">
              <span class="lbl">${M(e, "field.condition_mode")}</span>
              <select
                @change=${(e) => this._setAction(n, { condition_mode: e.target.value })}
              >
                ${["all", "any"].map((n) => C`<option .value=${n} .selected=${U(t.condition_mode === n)}>
                      ${M(e, `condition.${n}`)}
                    </option>`)}
              </select>
            </label>` : T}
      <p class="hint">${M(e, "condition.max")}</p>
    </fieldset>`;
	}
	_renderCondition(e, t, n, r, i) {
		let a = (e) => this._setAction(n, { conditions: t.conditions.map((t, n) => n === i ? {
			...t,
			...e
		} : t) });
		return C`<div class="condition">
      ${r.kind === "time" ? C`<label class="field">
                <span class="lbl">${M(e, "condition.after")}</span>
                <input
                  type="time"
                  .value=${r.after}
                  @input=${(e) => a({ after: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${M(e, "condition.before")}</span>
                <input
                  type="time"
                  .value=${r.before}
                  @input=${(e) => a({ before: e.target.value })}
                />
                <span class="hint">${M(e, "condition.midnight_hint")}</span>
              </label>` : C`<label class="field">
                <span class="lbl">${M(e, "field.entity_id")}</span>
                <input
                  .value=${r.entity_id}
                  @input=${(e) => a({ entity_id: e.target.value })}
                />
              </label>
              <label class="field">
                <span class="lbl">${M(e, "field.state")}</span>
                <select
                  @change=${(e) => a({ operator: e.target.value })}
                >
                  ${["is", "is_not"].map((t) => C`<option .value=${t} .selected=${U(r.operator === t)}>
                        ${M(e, `condition.${t}`)}
                      </option>`)}
                </select>
              </label>
              <label class="field">
                <span class="lbl">${M(e, "condition.state")}</span>
                <input
                  .value=${r.state}
                  @input=${(e) => a({ state: e.target.value })}
                />
              </label>`}
      <button class="btn sm danger" @click=${() => this._setAction(n, { conditions: t.conditions.filter((e, t) => t !== i) })}>${M(e, "common.delete")}</button>
    </div>`;
	}
	static {
		this.styles = [
			P,
			N,
			o`
      .hd-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .hint.bad {
        color: var(--error-color, #d32f2f);
      }
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
      .duress {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin-top: 12px;
      }
      .entity-list {
        max-height: 200px;
        overflow: auto;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(260px, 100%), 1fr));
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
customElements.get("foyer-page-profiles") || customElements.define("foyer-page-profiles", Lt);
//#endregion
//#region src/panel/pages/groups.ts
var Rt = class extends A {
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
		if (this._busy) return;
		let t = this.ctx?.config?.areas[0]?.id ?? "";
		this._draft = e ? structuredClone(e) : {
			name: "",
			area_id: t,
			members: [],
			n: 2,
			window_seconds: 60,
			suppress_members: !1,
			response_profile_id: null
		}, this._problems = [], L(this);
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
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0);
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
		if (!e?.config) return T;
		let t = e.strings, n = new Map(e.config.areas.map((e) => [e.id, e.name])), r = new Map(e.config.zones.map((e) => [e.id, e.name])), i = this._rows(e.config.zones, e.config.groups ?? []);
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "groups.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>${M(t, "groups.add")}</button>
        </div>
        ${i.length ? C`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${M(t, "field.name")}</th>
                    <th>${M(t, "field.area_id")}</th>
                    <th>${M(t, "field.members")}</th>
                    <th>${M(t, "field.n")}</th>
                    <th>${M(t, "field.window_seconds")}</th>
                    <th>${M(t, "groups.members_below")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${i.map(({ group: e, derived: i }) => C`<tr
                      class=${i ? "" : "clickable"}
 tabindex=${i ? "-1" : "0"}
 @keydown=${B}
                      aria-selected=${this._draft?.id === e.id ? "true" : "false"}
                      @click=${() => i ? void 0 : this._edit(e)}
                    >
                      <td>
                        <strong>${e.name}</strong>
                        ${i ? C`<span class="tag">${M(t, "groups.from_zone")}</span>` : T}
                      </td>
                      <td>${n.get(e.area_id) ?? ""}</td>
                      <td>
                        ${e.members.map((e) => C`<span class="tag">${r.get(e) ?? e}</span>`)}
                      </td>
                      <td>${M(t, "groups.threshold", {
			n: e.n,
			m: e.members.length
		})}</td>
                      <td>${M(t, "common.seconds", { n: e.window_seconds })}</td>
                      <td>
                        ${M(t, e.suppress_members ? "groups.suppressed" : "groups.not_suppressed")}
                      </td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : C`<div class="empty">${M(t, "groups.none")}</div>`}
        <div class="card-bd">
          <p class="hint">${M(t, "groups.from_zone_hint")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : T}
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, [r, i] = n.meta?.bounds.window ?? [1, 3600], a = new Map(n.config?.areas.map((e) => [e.id, e.name])), o = /* @__PURE__ */ new Set();
		for (let e of n.config?.groups ?? []) e.id !== t.id && e.members.forEach((e) => o.add(e));
		for (let e of n.config?.zones ?? []) e.cross_zone_id && e.id && (o.add(e.id), o.add(e.cross_zone_id));
		let s = (n.config?.zones ?? []).filter((e) => e.channel === "intrusion" && e.id && (!o.has(e.id) || t.members.includes(e.id))), c = (e, n) => this._set("members", n ? [.../* @__PURE__ */ new Set([...t.members, e])] : t.members.filter((t) => t !== e));
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "groups.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.area_id")}</span>
              <select
                @change=${(e) => this._set("area_id", e.target.value)}
              >
                ${(n.config?.areas ?? []).map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === t.area_id)}>
                      ${e.name}
                    </option>`)}
              </select>
              <span class="hint">${M(e, "groups.area_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.n")}</span>
              <input
                type="number"
                min="2"
                max=${Math.max(2, t.members.length)}
                .value=${String(t.n)}
                @input=${(e) => V(e, (e) => this._set("n", e))}
              />
              <span class="hint">
                ${M(e, "groups.threshold", {
			n: t.n,
			m: t.members.length
		})}
              </span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.window_seconds")}</span>
              <input
                type="number"
                min=${r}
                max=${i}
                .value=${String(t.window_seconds)}
                @input=${(e) => V(e, (e) => this._set("window_seconds", e))}
              />
              <span class="hint">${M(e, "groups.window_hint")}</span>
            </label>
            ${W(this.ctx, t.response_profile_id, (e) => this._set("response_profile_id", e), M(e, "profiles.group_hint"))}
          </div>
          <fieldset>
            <legend>${M(e, "field.members")}</legend>
            ${s.length ? s.map((n) => C`<label class="check">
                    <input
                      type="checkbox"
                      .checked=${U(t.members.includes(n.id ?? ""))}
                      @change=${(e) => c(n.id ?? "", e.target.checked)}
                    />
                    <span>
                      ${M(e, "zones.entity", {
			name: n.name,
			entity: a.get(n.area_id) ?? n.area_id
		})}
                    </span>
                  </label>`) : C`<p class="hint">${M(e, "groups.no_zones")}</p>`}
            <p class="hint">${M(e, "groups.members_hint")}</p>
          </fieldset>
          <label class="check suppress">
            <input
              type="checkbox"
              .checked=${U(t.suppress_members)}
              @change=${(e) => this._set("suppress_members", e.target.checked)}
            />
            <span>
              ${M(e, "field.suppress_members")}
              <span class="hint">${M(e, "groups.suppress_hint")}</span>
            </span>
          </label>
          ${this._problems.length ? C`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
                </ul>
              </div>` : T}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${M(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${M(e, "common.cancel")}
            </button>
            ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          </div>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			N,
			P,
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
customElements.get("foyer-page-groups") || customElements.define("foyer-page-groups", Rt);
//#endregion
//#region src/panel/pages/users.ts
var zt = {
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
function Bt(e) {
	if (!e) return "";
	let t = new Date(e), n = (e) => String(e).padStart(2, "0");
	return `${t.getFullYear()}-${n(t.getMonth() + 1)}-${n(t.getDate())}T${n(t.getHours())}:${n(t.getMinutes())}`;
}
function Vt(e) {
	if (!e) return null;
	let t = new Date(e);
	return Number.isNaN(t.getTime()) ? null : t.toISOString();
}
var Ht = class extends A {
	constructor(...e) {
		super(...e), this._problems = [], this._policyProblems = [], this._busy = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_policyProblems: { state: !0 },
			_busy: { state: !0 },
			_policy: { state: !0 }
		};
	}
	_edit(e) {
		this._busy || (this._draft = e ? { ...structuredClone(e) } : structuredClone(zt), this._problems = [], L(this));
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
				let { new_code: e, new_duress_code: t, repeat_code: n, ...r } = this._draft;
				if (e && e !== (n ?? "")) {
					this._problems = [{
						code: "code_mismatch",
						kind: "user",
						ref: null,
						field: null
					}], R(this);
					return;
				}
				let i = await this.ctx.saveUser(r, {
					...e === void 0 ? {} : { new_code: e },
					...t === void 0 ? {} : { new_duress_code: t }
				});
				this._problems = i.problems, i.success || R(this), i.success && (this._draft = void 0);
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
				this._policyProblems = e.problems, e.success && (this._policy = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return T;
		let t = e.strings, n = e.config.users ?? [];
		return C`
      ${e.status.security.enforced ? T : C`<div class="banner warn">
            <strong>${M(t, "users.not_enforced")}</strong>
            <span>${M(t, "users.not_enforced_hint")}</span>
          </div>`}
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "users.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${M(t, "users.add")}
          </button>
        </div>
        ${n.length ? C`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${M(t, "field.name")}</th>
                    <th>${M(t, "users.code")}</th>
                    <th>${M(t, "field.permissions")}</th>
                    <th>${M(t, "users.scope")}</th>
                    <th>${M(t, "field.valid_until")}</th>
                    <th>${M(t, "users.duress")}</th>
                    <th>${M(t, "field.ha_user_id")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${n.map((e) => this._row(t, e))}
                </tbody>
              </table>
            </div>` : C`<div class="empty">${M(t, "users.none")}</div>`}
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : T}
      ${this._renderPolicy(t)}
    `;
	}
	_row(e, t) {
		let n = this.ctx, r = new Map((n.config?.areas ?? []).map((e) => [e.id, e.name])), i = t.allowed_area_ids === null ? M(e, "users.every_area") : t.allowed_area_ids.map((e) => r.get(e) ?? e).join(", ");
		return C`<tr
      class="clickable"
 tabindex="0"
 @keydown=${B}
      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
      @click=${() => this._edit(t)}
    >
      <td>
        <strong>${t.name}</strong>
        ${t.enabled ? T : C`<span class="tag">${M(e, "users.disabled")}</span>`}
      </td>
      <td>
        ${t.has_code ? C`<span class="pill ok">${M(e, "users.code_set")}</span>` : C`<span class="pill warn">${M(e, "users.code_missing")}</span>`}
      </td>
      <td>${t.permissions.map((t) => C`<span class="tag">${M(e, `permission.${t}`)}</span>`)}</td>
      <td>${i}</td>
      <td>${t.valid_until ? new Date(t.valid_until).toLocaleString(n.hass.language) : "—"}</td>
      <td>${M(e, t.has_duress_code ? "common.yes" : "common.no")}</td>
      <td>${t.ha_user_id ? M(e, "users.linked") : "—"}</td>
    </tr>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.status.security.code_length, i = n.meta?.permissions ?? [], a = n.hass.user?.is_admin ? n.haUsers ?? [] : [];
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "users.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "users.code")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${r}
                placeholder=${t.has_code ? M(e, "users.code_unchanged") : M(e, "users.code_digits", { n: r })}
                .value=${U(t.new_code ?? "")}
                @input=${(e) => this._set("new_code", e.target.value)}
              />
              <span class="hint">
                ${M(e, t.id ? "users.code_hint" : "users.code_hint_new", { n: r })}
              </span>
            </label>
            ${t.new_code ? C`<label class="field">
                  <span class="lbl">${M(e, "users.code_repeat")}</span>
                  <input
                    type="password"
                    inputmode="numeric"
                    autocomplete="off"
                    maxlength=${r}
                    .value=${U(t.repeat_code ?? "")}
                    @input=${(e) => this._set("repeat_code", e.target.value)}
                  />
                </label>` : T}
            <label class="field">
              <span class="lbl">${M(e, "users.duress")}</span>
              <input
                type="password"
                inputmode="numeric"
                autocomplete="off"
                maxlength=${r}
                placeholder=${t.has_duress_code ? M(e, "users.code_unchanged") : M(e, "users.code_optional")}
                .value=${U(t.new_duress_code ?? "")}
                @input=${(e) => this._set("new_duress_code", e.target.value)}
              />
              <span class="hint">${M(e, "users.duress_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.ha_user_id")}</span>
              <select
                @change=${(e) => this._set("ha_user_id", e.target.value || null)}
              >
                <option value="" .selected=${U(!t.ha_user_id)}>${M(e, "users.not_linked")}</option>
                ${a.map((e) => C`<option .value=${e.id} .selected=${U(e.id === t.ha_user_id)}>
                    ${e.name}
                  </option>`)}
              </select>
              <span class="hint">${M(e, "users.linked_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.valid_from")}</span>
              <input
                type="datetime-local"
                .value=${Bt(t.valid_from)}
                @input=${(e) => this._set("valid_from", Vt(e.target.value))}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.valid_until")}</span>
              <input
                type="datetime-local"
                .value=${Bt(t.valid_until)}
                @input=${(e) => this._set("valid_until", Vt(e.target.value))}
              />
              <span class="hint">${M(e, "users.validity_hint")}</span>
            </label>
          </div>

          <div class="hr"></div>
          <div class="lbl">${M(e, "field.permissions")}</div>
          <div class="chips">
            ${i.map((n) => C`<label class="chip">
                <input
                  type="checkbox"
                  .checked=${U(t.permissions.includes(n))}
                  @change=${(e) => this._togglePermission(n, e.target.checked)}
                />
                <span>${M(e, `permission.${n}`)}</span>
              </label>`)}
          </div>
          ${t.permissions.includes("walk_test") ? C`<div class="notice" role="alert">${M(e, "users.walk_test_note")}</div>` : T}

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
              .checked=${U(t.code_exempt_when_identified)}
              @change=${(e) => this._set("code_exempt_when_identified", e.target.checked)}
            />
            <span>
              ${M(e, "users.exempt")}
              <span class="hint">${M(e, "users.exempt_hint")}</span>
            </span>
          </label>
          <p class="note">${M(e, "users.exempt_note")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.enabled)}
              @change=${(e) => this._set("enabled", e.target.checked)}
            />
            <span>
              ${M(e, "users.enabled")}
              <span class="hint">${M(e, "users.enabled_hint")}</span>
            </span>
          </label>

          ${this._problems.length ? C`<ul class="problems">
                ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
              </ul>` : T}
        </div>
        <div class="card-ft">
          <button class="btn" @click=${() => this._draft = void 0}>
            ${M(e, "common.cancel")}
          </button>
          ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                .message=${"users.confirm_delete"}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${M(e, "common.save")}
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
		return C`<div class="scope">
      <span class="lbl">${M(e, `field.${t}`)}</span>
      <label class="chip">
        <input
          type="checkbox"
          .checked=${U(i === null)}
          @change=${(e) => this._set(t, e.target.checked ? null : [])}
        />
        <span>${M(e, "users.everything")}</span>
      </label>
      ${i === null ? T : C`<div class="chips">
            ${n.map((e) => C`<label class="chip">
                <input
                  type="checkbox"
                  .checked=${U(i.includes(e.id))}
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
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "users.policy")}</h2>
        </div>
        <div class="card-bd">
          <p class="hint">${M(e, "users.policy_hint")}</p>
          ${I(t) ? C`<div class="notice" role="note">${M(e, "users.policy_armed")}</div>` : T}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${M(e, "users.operation")}</th>
                  <th>${M(e, "users.needs_code")}</th>
                </tr>
              </thead>
              <tbody>
                ${r.map((t) => C`<tr>
                    <td>
                      ${M(e, `operation.${t}`)}
                      ${i.has(t) ? C`<span class="tag">${M(e, "users.later_phase")}</span>` : T}
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        aria-label=${M(e, `operation.${t}`)}
                        .checked=${U(!!n.code_policy[t])}
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
              <span class="lbl">${M(e, "users.code_length")}</span>
              <input
                type="number"
                min=${l}
                max=${u}
                .value=${String(n.security.code_length)}
                @input=${(e) => V(e, (e) => f("code_length", e))}
              />
              <span class="hint">${M(e, "users.code_length_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "users.lockout_failures")}</span>
              <input
                type="number"
                min=${a}
                max=${o}
                .value=${String(n.security.lockout_failures)}
                @input=${(e) => V(e, (e) => f("lockout_failures", e))}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "users.lockout_window")}</span>
              <input
                type="number"
                min=${s}
                max=${c}
                .value=${String(n.security.lockout_window)}
                @input=${(e) => V(e, (e) => f("lockout_window", e))}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "users.lockout_duration")}</span>
              <input
                type="number"
                min=${s}
                max=${c}
                .value=${String(n.security.lockout_duration)}
                @input=${(e) => V(e, (e) => f("lockout_duration", e))}
              />
              <span class="hint">${M(e, "users.lockout_hint")}</span>
            </label>
          </div>
          ${this._policyProblems.length ? C`<ul class="problems">
                ${this._policyProblems.map((t) => C`<li>${z(e, t)}</li>`)}
              </ul>` : T}
        </div>
        <div class="card-ft">
          <button
            class="btn primary"
            ?disabled=${this._busy || !this._policy}
            @click=${this._savePolicy}
          >
            ${M(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			P,
			N,
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
customElements.define("foyer-page-users", Ht);
//#endregion
//#region src/panel/pages/devices.ts
function Ut() {
	return {
		scopes: [],
		free_scopes: ["status"],
		arm_scenario_ids: null,
		arm_area_ids: null,
		disarm_area_ids: null,
		unlock_seconds: 120,
		clear_text_confirmed: !1
	};
}
var Wt = [
	"status",
	"zones",
	"batteries",
	"health",
	"log"
], Gt = [
	"arm",
	"disarm",
	"exclude",
	"acknowledge"
], Kt = 30, qt = 600, Jt = {
	name: "",
	kind: "keypad",
	ref: "",
	entity_id: null,
	event_type: null,
	user_id: null,
	command: "toggle",
	scenario_id: null,
	enabled: !0,
	transport: "mqtt",
	...Ut()
}, Yt = ["tag.", "event."], Xt = class extends A {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1, this._mqttProblems = [], this._tokenProblems = [];
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_mqtt: { state: !0 },
			_mqttProblems: { state: !0 },
			_token: { state: !0 },
			_tokenProblems: { state: !0 },
			_confirmToken: { state: !0 }
		};
	}
	_edit(e) {
		this._busy || (this._draft = e ? {
			...Ut(),
			...structuredClone(e)
		} : structuredClone(Jt), this._problems = [], this._token = void 0, this._tokenProblems = [], this._confirmToken = void 0, L(this));
	}
	async _tokenAction(e) {
		let t = this._draft?.id;
		if (this._confirmToken = void 0, this.ctx && t) {
			this._busy = !0;
			try {
				let n = await this.ctx.deviceToken(t, e);
				if (this._draft?.id !== t) return;
				this._tokenProblems = n.problems, this._token = n.success && n.token ? {
					deviceId: t,
					value: n.token
				} : void 0, n.success && (this._draft = {
					...this._draft,
					has_token: !e
				});
			} finally {
				this._busy = !1;
			}
		}
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
			ref: null,
			transport: "mqtt",
			scopes: []
		};
	}
	_setTransport(e) {
		this._draft = {
			...this._draft,
			transport: e,
			...e === "mqtt" ? {
				scopes: [],
				clear_text_confirmed: !1
			} : {}
		};
	}
	_toggle(e, t, n) {
		let r = this._draft, i = r[e].filter((e) => e !== t);
		n && i.push(t);
		let a = {
			...r,
			[e]: i
		};
		a.scopes.some((e) => e !== "status") || (a.clear_text_confirmed = !1), this._draft = a;
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.save("device", this._draft);
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0, this._token = void 0);
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
				let e = { mqtt: this._mqtt }, t = await this.ctx.saveSettings(e);
				this._mqttProblems = t.problems, t.success && (this._mqtt = void 0);
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return T;
		let t = e.strings, n = e.config.devices ?? [];
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "devices.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${M(t, "devices.add")}
          </button>
        </div>
        ${n.length ? C`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${M(t, "field.name")}</th>
                    <th>${M(t, "field.kind")}</th>
                    <th>${M(t, "devices.reaches")}</th>
                    <th>${M(t, "devices.identifies")}</th>
                    <th>${M(t, "field.enabled")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${n.map((e) => this._row(t, e))}
                </tbody>
              </table>
            </div>` : C`<div class="empty">${M(t, "devices.none")}</div>`}
        <div class="card-bd">
          <p class="note">${M(t, "devices.white_list")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : T}
      ${this._renderMqtt(t)}
    `;
	}
	_row(e, t) {
		let n = (this.ctx.config?.users ?? []).find((e) => e.id === t.user_id);
		return C`<tr
      class="clickable"
 tabindex="0"
 @keydown=${B}
      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
      @click=${() => this._edit(t)}
    >
      <td><strong>${t.name}</strong></td>
      <td>${M(e, `device_kind.${t.kind}`)}</td>
      <td class="mono">
        ${t.kind === "keypad" ? t.ref : t.entity_id}
        ${t.kind === "keypad" ? C`<span class="pill idle">${M(e, `transport.${t.transport}`)}</span>` : T}
        ${this._inClear(t) ? C`<span class="pill warn">${M(e, "devices.in_clear_pill")}</span>` : T}
      </td>
      <td>
        ${t.kind === "tag" ? C`<span class="pill ok">${n?.name ?? "—"}</span>` : C`<span class="pill idle">${M(e, "devices.code_is_identity")}</span>`}
      </td>
      <td>${M(e, t.enabled ? "common.yes" : "common.no")}</td>
    </tr>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.config?.users ?? [], i = n.config?.scenarios ?? [], a = this._tagEntities(n.hass.states);
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "devices.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.kind")}</span>
              <select
                @change=${(e) => this._setKind(e.target.value)}
              >
                ${["keypad", "tag"].map((n) => C`<option .value=${n} .selected=${U(n === t.kind)}>
                    ${M(e, `device_kind.${n}`)}
                  </option>`)}
              </select>
              <span class="hint">${M(e, `devices.kind_hint_${t.kind}`)}</span>
            </label>
          </div>

          ${t.kind === "keypad" ? C`<div class="grid-form">
                  <label class="field">
                    <span class="lbl">${M(e, "field.ref")}</span>
                    <input
                      .value=${t.ref ?? ""}
                      placeholder="keypad_hall"
                      @input=${(e) => this._set("ref", e.target.value)}
                    />
                    <span class="hint"
                      >${M(e, t.transport === "http" ? "devices.ref_hint_http" : "devices.ref_hint")}</span
                    >
                  </label>
                  <label class="field">
                    <span class="lbl">${M(e, "field.transport")}</span>
                    <select
                      @change=${(e) => this._setTransport(e.target.value)}
                    >
                      ${["mqtt", "http"].map((n) => C`<option
                          .value=${n}
                          .selected=${U(n === t.transport)}
                        >
                          ${M(e, `transport.${n}`)}
                        </option>`)}
                    </select>
                    <span class="hint">${M(e, `devices.transport_hint_${t.transport}`)}</span>
                    ${t.transport === "mqtt" && this.ctx?.config?.devices.find((e) => e.id === t.id)?.has_token ? C`<span class="hint warn-text">${M(e, "devices.token_dropped")}</span>` : T}
                  </label>
                </div>
                ${t.transport === "http" ? C`${this._renderToken(e, t)} ${this._renderScopes(e, t)}` : T}` : C`
                ${this.ctx?.config?.devices.find((e) => e.id === t.id)?.has_token ? C`<p class="hint warn-text">${M(e, "devices.token_dropped")}</p>` : T}
                <div class="banner warn">
                  <strong>${M(e, "devices.stolen_tag")}</strong>
                  <span>${M(e, "devices.stolen_tag_hint")}</span>
                </div>
                <div class="grid-form">
                  <label class="field">
                    <span class="lbl">${M(e, "field.entity_id")}</span>
                    <select
                      @change=${(e) => this._set("entity_id", e.target.value || null)}
                    >
                      <option value="" .selected=${U(!t.entity_id)}>—</option>
                      ${a.map((e) => C`<option .value=${e} .selected=${U(e === t.entity_id)}>
                          ${e}
                        </option>`)}
                    </select>
                    <span class="hint">${M(e, "devices.entity_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${M(e, "field.event_type")}</span>
                    <input
                      .value=${t.event_type ?? ""}
                      @input=${(e) => this._set("event_type", e.target.value || null)}
                    />
                    <span class="hint">${M(e, "devices.event_type_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${M(e, "field.user_id")}</span>
                    <select
                      @change=${(e) => this._set("user_id", e.target.value || null)}
                    >
                      <option value="" .selected=${U(!t.user_id)}>—</option>
                      ${r.map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === t.user_id)}>
                          ${e.name}
                        </option>`)}
                    </select>
                    <span class="hint">${M(e, "devices.owner_hint")}</span>
                  </label>
                  <label class="field">
                    <span class="lbl">${M(e, "field.command")}</span>
                    <select
                      @change=${(e) => this._set("command", e.target.value)}
                    >
                      ${[
			"toggle",
			"arm",
			"disarm"
		].map((n) => C`<option
                          .value=${n}
                          .selected=${U(n === t.command)}
                        >
                          ${M(e, `key_command.${n}`)}
                        </option>`)}
                    </select>
                  </label>
                  ${t.command === "disarm" ? T : C`<label class="field">
                        <span class="lbl">${M(e, "field.scenario_id")}</span>
                        <select
                          @change=${(e) => this._set("scenario_id", e.target.value || null)}
                        >
                          <option value="" .selected=${U(!t.scenario_id)}>—</option>
                          ${i.map((e) => C`<option
                              .value=${e.id ?? ""}
                              .selected=${U(e.id === t.scenario_id)}
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
              .checked=${U(t.enabled)}
              @change=${(e) => this._set("enabled", e.target.checked)}
            />
            <span>
              ${M(e, "field.enabled")}
              <span class="hint">${M(e, "devices.enabled_hint")}</span>
            </span>
          </label>

          ${this._problems.length ? C`<ul class="problems">
                ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
              </ul>` : T}
        </div>
        <div class="card-ft">
          <button
            class="btn"
            @click=${() => {
			this._draft = void 0, this._token = void 0;
		}}
          >
            ${M(e, "common.cancel")}
          </button>
          ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${M(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	_tagEntities(e) {
		return this._tagCache?.states !== e && (this._tagCache = {
			states: e,
			ids: Object.keys(e).filter((e) => Yt.some((t) => e.startsWith(t))).sort()
		}), this._tagCache.ids;
	}
	_inClear(e) {
		return e.kind === "keypad" && e.transport === "http" && !!e.id && (this.ctx?.status.devices_in_clear ?? []).includes(e.id);
	}
	_renderToken(e, t) {
		let n = this.ctx?.config?.devices.find((e) => e.id === t.id), r = !!n && n.transport === "http", i = this._token && this._token.deviceId === t.id ? this._token : void 0;
		return C`<div class="token">
      ${this._inClear(t) ? C`<div class="banner warn" role="alert">
            <strong>${M(e, "devices.in_clear")}</strong>
            <span>${M(e, "devices.in_clear_hint")}</span>
          </div>` : T}
      <p class="note">${M(e, "devices.token_note")}</p>
      ${i ? C`<div class="once" role="status">
            <span class="lbl">${M(e, "devices.token_once")}</span>
            <code class="mono secret">${i.value}</code>
            <span class="hint">${M(e, "devices.token_once_hint")}</span>
          </div>` : C`<p class="hint">
            ${r ? t.has_token ? M(e, "devices.token_exists") : M(e, "devices.token_none") : M(e, "devices.token_save_first")}
          </p>`}
      ${r ? C`<div class="actions">
            ${this._confirmToken ? C`<span class="hint">${M(e, "devices.token_confirm")}</span>
                  <button
                    class="btn danger"
                    ?disabled=${this._busy}
                    @click=${() => this._tokenAction(this._confirmToken === "revoke")}
                  >
                    ${M(e, this._confirmToken === "revoke" ? "devices.token_revoke" : "devices.token_replace")}
                  </button>
                  <button class="btn" @click=${() => this._confirmToken = void 0}>
                    ${M(e, "common.cancel")}
                  </button>` : C`<button
                    class="btn"
                    ?disabled=${this._busy}
                    @click=${() => t.has_token ? this._confirmToken = "replace" : this._tokenAction(!1)}
                  >
                    ${M(e, t.has_token ? "devices.token_replace" : "devices.token_generate")}
                  </button>
                  ${t.has_token ? C`<button
                        class="btn danger"
                        ?disabled=${this._busy}
                        @click=${() => this._confirmToken = "revoke"}
                      >
                        ${M(e, "devices.token_revoke")}
                      </button>` : T}`}
          </div>` : T}
      ${this._tokenProblems.length ? C`<ul class="problems">
            ${this._tokenProblems.map((t) => C`<li>${z(e, t)}</li>`)}
          </ul>` : T}
      <div class="endpoint-samples">
        <div class="field">
          <span class="lbl">${M(e, "devices.endpoint_request")}</span>
          <pre class="sample">${Qt}</pre>
        </div>
        <div class="field">
          <span class="lbl">${M(e, "devices.endpoint_stream")}</span>
          <pre class="sample">${$t}</pre>
          <span class="hint">${M(e, "devices.endpoint_stream_hint")}</span>
        </div>
      </div>
    </div>`;
	}
	_renderScopes(e, t) {
		let n = this.ctx?.config, r = (e) => t.scopes.includes(e), i = t.scopes.some((e) => e !== "status"), a = Wt.some((e) => r(e) && !t.free_scopes.includes(e)), o = (n?.areas ?? []).map((e) => ({
			id: e.id ?? "",
			name: e.name
		})), s = (n?.scenarios ?? []).map((e) => ({
			id: e.id ?? "",
			name: e.name
		}));
		return C`<fieldset class="scopes">
      <legend>${M(e, "field.scopes")}</legend>
      <p class="note">${M(e, "devices.scopes_note")}</p>
      ${t.scopes.length ? T : C`<p class="hint warn-text">${M(e, "devices.scopes_none")}</p>`}

      <h3>${M(e, "devices.scopes_read")}</h3>
      <p class="hint">${M(e, "devices.scopes_read_hint")}</p>
      ${Wt.map((n) => C`<div class="scope-row">
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(r(n))}
              @change=${(e) => this._toggle("scopes", n, e.target.checked)}
            />
            <span>
              ${M(e, `devices.scope.${n}`)}
              <span class="hint">${M(e, `devices.scope_hint.${n}`)}</span>
            </span>
          </label>
          <label class="check free">
            <input
              type="checkbox"
              ?disabled=${!r(n)}
              .checked=${U(t.free_scopes.includes(n))}
              @change=${(e) => this._toggle("free_scopes", n, e.target.checked)}
            />
            <span>${M(e, "field.free_scopes")}</span>
          </label>
        </div>`)}
      ${r("log") && t.free_scopes.includes("log") ? C`<p class="hint">${M(e, "devices.free_log_hint")}</p>` : T}
      ${a ? C`<label class="field unlock">
            <span class="lbl">${M(e, "field.unlock_seconds")}</span>
            <input
              type="number"
              min=${Kt}
              max=${qt}
              step="1"
              .value=${String(t.unlock_seconds)}
              @change=${(e) => V(e, (e) => this._set("unlock_seconds", e))}
            />
            <span class="hint">${M(e, "devices.unlock_hint")}</span>
          </label>` : T}

      <h3>${M(e, "devices.scopes_act")}</h3>
      <p class="hint">${M(e, "devices.scopes_act_hint")}</p>
      ${Gt.map((n) => C`<label class="check">
            <input
              type="checkbox"
              .checked=${U(r(n))}
              @change=${(e) => this._toggle("scopes", n, e.target.checked)}
            />
            <span>
              ${M(e, `devices.scope.${n}`)}
              <span class="hint">${M(e, `devices.scope_hint.${n}`)}</span>
            </span>
          </label>
          ${n === "arm" && r("arm") ? C`<div class="reach">
                ${this._reach(e, "arm_scenario_ids", "devices.reach_all_scenarios", s, t)}
                ${this._reach(e, "arm_area_ids", "devices.reach_whole_house", o, t)}
              </div>` : T}
          ${n === "disarm" && r("disarm") ? C`<div class="reach">
                ${this._reach(e, "disarm_area_ids", "devices.reach_whole_house", o, t)}
              </div>` : T}`)}

      ${i ? C`<div class="clear-text">
            <label class="check">
              <input
                type="checkbox"
                .checked=${U(t.clear_text_confirmed)}
                @change=${(e) => this._set("clear_text_confirmed", e.target.checked)}
              />
              <span>
                ${M(e, "field.clear_text_confirmed")}
                ${this._inClear(t) ? C`<span class="pill warn">${M(e, "devices.in_clear_pill")}</span>` : T}
                <span class="hint">${M(e, "devices.clear_text_hint")}</span>
                ${this._inClear(t) ? C`<span class="hint warn-text">${M(e, "devices.clear_text_now")}</span>` : T}
              </span>
            </label>
          </div>` : T}
    </fieldset>`;
	}
	_reach(e, t, n, r, i) {
		let a = i[t], o = [...r, ...(a ?? []).filter((e) => !r.some((t) => t.id === e)).map((e) => ({
			id: e,
			name: e
		}))];
		return C`<div class="field">
      <span class="lbl">${M(e, `field.${t}`)}</span>
      <label class="check">
        <input
          type="radio"
          name=${t}
          .checked=${U(a === null)}
          @change=${() => this._set(t, null)}
        />
        <span>${M(e, n)}</span>
      </label>
      <label class="check">
        <input
          type="radio"
          name=${t}
          .checked=${U(a !== null)}
          @change=${() => this._set(t, a ?? [])}
        />
        <span>${M(e, "devices.reach_only")}</span>
      </label>
      ${a === null ? T : C`<div class="choices">
              ${o.map((e) => C`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${U(a.includes(e.id))}
                    @change=${(n) => this._set(t, n.target.checked ? [...a, e.id] : a.filter((t) => t !== e.id))}
                  />
                  <span>${e.name}</span>
                </label>`)}
            </div>
            ${a.length ? T : C`<span class="hint warn-text">${M(e, "devices.reach_none")}</span>`}`}
    </div>`;
	}
	_renderMqtt(e) {
		let t = this._mqttDraft(), n = (e, n) => {
			this._mqtt = {
				...t,
				[e]: n
			};
		};
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "devices.mqtt")}</h2>
        </div>
        <div class="card-bd">
          <p class="note">${M(e, "devices.mqtt_note")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.enabled)}
              @change=${(e) => n("enabled", e.target.checked)}
            />
            <span>
              ${M(e, "devices.mqtt_enabled")}
              <span class="hint">${M(e, "devices.mqtt_enabled_hint")}</span>
            </span>
          </label>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.command_topic")}</span>
              <input
                .value=${t.command_topic}
                placeholder=${M(e, "devices.topic_command_example")}
                @input=${(e) => n("command_topic", e.target.value)}
              />
              <span class="hint">${M(e, "devices.topic_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.state_topic")}</span>
              <input
                .value=${t.state_topic}
                placeholder=${M(e, "devices.topic_state_example")}
                @input=${(e) => n("state_topic", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.detail")}</span>
              <select
                @change=${(e) => n("detail", e.target.value)}
              >
                ${[
			"minimal",
			"standard",
			"full"
		].map((n) => C`<option .value=${n} .selected=${U(n === t.detail)}>
                    ${M(e, `mqtt_detail.${n}`)}
                  </option>`)}
              </select>
              <span class="hint">${M(e, `devices.detail_hint_${t.detail}`)}</span>
              <span class="hint">${M(e, "devices.detail_shared_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.qos")}</span>
              <select
                @change=${(e) => n("qos", Number(e.target.value))}
              >
                ${[
			0,
			1,
			2
		].map((e) => C`<option .value=${String(e)} .selected=${U(e === t.qos)}>
                    ${e}
                  </option>`)}
              </select>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.retain)}
              @change=${(e) => n("retain", e.target.checked)}
            />
            <span>
              ${M(e, "field.retain")}
              <span class="hint">${M(e, "devices.retain_hint")}</span>
            </span>
          </label>
          <div class="hr"></div>
          <div class="grid-form">
            <div class="field">
              <span class="lbl">${M(e, "devices.inbound")}</span>
              <pre class="sample">${Zt}</pre>
            </div>
            <div class="field">
              <span class="lbl">${M(e, "devices.outbound")}</span>
              <pre class="sample">${en[t.detail]}</pre>
              <span class="hint">${M(e, "devices.last_result_hint")}</span>
            </div>
          </div>
          ${this._mqttProblems.length ? C`<ul class="problems">
                ${this._mqttProblems.map((t) => C`<li>${z(e, t)}</li>`)}
              </ul>` : T}
        </div>
        <div class="card-ft">
          <button
            class="btn primary"
            ?disabled=${this._busy || !this._mqtt}
            @click=${this._saveMqtt}
          >
            ${M(e, "common.save")}
          </button>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			P,
			N,
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
      .token {
        margin-top: 12px;
      }
      .warn-text {
        color: var(--warning-color, #c77700);
      }
      .endpoint-samples {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 16px;
      }
      .endpoint-samples .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
      }
      .endpoint-samples .lbl {
        font-weight: 500;
      }
      .once {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 8px;
        border: 1px solid var(--primary-color);
        background: var(--secondary-background-color);
      }
      .once .lbl {
        font-weight: 500;
      }
      .secret {
        overflow-wrap: anywhere;
        user-select: all;
        font-size: 13px;
      }
      .scopes h3 {
        font-size: 14px;
        font-weight: 500;
        margin: 16px 0 2px;
      }
      /* A read scope and its "without a code" beside it, on one line while
         there is room: the pair is one decision about one piece of the house. */
      .scope-row {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start;
        gap: 0 24px;
      }
      .scope-row > label.check:first-child {
        flex: 1 1 280px;
      }
      .scope-row .free {
        flex: 0 0 auto;
        font-size: 13px;
        color: var(--secondary-text-color);
      }
      .reach {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 8px 16px;
        margin: 0 0 8px 28px;
      }
      .reach .field {
        display: flex;
        flex-direction: column;
        font-size: 13px;
      }
      .reach .lbl {
        font-weight: 500;
      }
      .reach label.check {
        padding: 2px 0;
        font-size: 13px;
      }
      .choices {
        margin-left: 28px;
      }
      input[type="radio"] {
        width: 18px;
        height: 18px;
        padding: 0;
      }
      /* Beside a long hint a box would otherwise shrink to a dot. */
      .scopes input[type="checkbox"],
      .scopes input[type="radio"] {
        flex: none;
      }
      .unlock {
        max-width: 320px;
        margin: 8px 0 0;
      }
      .clear-text {
        margin-top: 16px;
        padding-top: 8px;
        border-top: 1px solid var(--divider-color);
      }
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
}, Zt = "{\n  \"action\": \"arm\",\n  \"scenario\": \"Night\",\n  \"code\": \"123456\",\n  \"device_id\": \"keypad_hall\"\n}", Qt = "POST /api/foyer/device\nAuthorization: Bearer <token>\n\n{ \"action\": \"arm\", \"scenario\": \"Night\", \"code\": \"123456\" }", $t = "GET /api/foyer/device/state\nAuthorization: Bearer <token>\n\ndata: {\"master\": \"arming\", \"countdown\": {\"kind\": \"exit\", \"remaining\": 30}, …}\n\n: keepalive", en = {
	minimal: "{\n  \"master\": \"armed_night\",\n  \"countdown\": { \"kind\": \"exit\", \"remaining\": 22 },\n  \"ready_to_arm\": false,\n  \"blocking_zones\": 1,\n  \"fault\": false,\n  \"last_result\": \"ok\"\n}",
	standard: "{\n  \"master\": \"armed_night\",\n  \"countdown\": null,\n  \"ready_to_arm\": true,\n  \"blocking_zones\": 0,\n  \"fault\": false,\n  \"last_result\": \"ok\",\n  \"scenario\": \"Night\",\n  \"areas\": { \"Ground floor\": \"armed\" }\n}",
	full: "{\n  \"master\": \"armed_night\",\n  \"countdown\": null,\n  \"ready_to_arm\": false,\n  \"blocking_zones\": 1,\n  \"fault\": false,\n  \"last_result\": \"blocked\",\n  \"scenario\": \"Night\",\n  \"areas\": { \"Ground floor\": \"armed\" },\n  \"open_zones\": [\"Bathroom window\"]\n}"
};
customElements.define("foyer-page-devices", Xt);
//#endregion
//#region src/panel/pages/test.ts
var tn = [
	"diagnostics",
	"simulator",
	"walktest",
	"actiontest"
], nn = /* @__PURE__ */ new Set([
	"triggered",
	"entry_started",
	"verification_satisfied",
	"technical_raised"
]);
function rn(e, t) {
	let n = e.config?.zones.find((e) => e.id === t);
	return n && n.trigger.kind === "state" ? n.trigger.states : [];
}
function an(e) {
	let t = /* @__PURE__ */ new Set();
	for (let n of e.config?.profiles ?? []) for (let e of n.actions) for (let n of e.conditions) n.kind === "state" && t.add(n.entity_id);
	for (let n of e.config?.rules ?? []) if (n.enabled) for (let e of n.trigger.entity_ids) t.add(e);
	return [...t].sort();
}
function Y(e, t, n) {
	return new Date(e).toLocaleTimeString(t, F(n, {
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit"
	}));
}
var on = class extends A {
	constructor(...e) {
		super(...e), this._tab = "diagnostics", this._busy = !1, this._walkWasOn = !1, this._scenario = "", this._start = "", this._overrides = [], this._entities = {}, this._code = "", this._codeWanted = !1, this._loaded = !1, this._mentioned = /* @__PURE__ */ new Set(), this._walkDuration = "", this._tested = {};
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_tab: { state: !0 },
			_diagnostics: { state: !0 },
			_simulation: { state: !0 },
			_busy: { state: !0 },
			_error: { state: !0 },
			_notice: { state: !0 },
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
	willUpdate() {
		let e = !!this.ctx?.status.walk_test;
		this._walkWasOn && !e && (this._notice = void 0), this._walkWasOn = e;
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
			start: this._start || null,
			zones: this._overrides.filter((e) => e.zone_id && e.state),
			entities: this._entities,
			code: this._code || void 0
		};
		try {
			this._simulation = await this.ctx.simulate(e), this._code = "";
		} catch (e) {
			let t = e?.code;
			this._codeWanted = t === "bad_code" || t === "code_required", this._simulation = void 0, t === "bad_code" && (this._code = ""), this._error = this._codeWanted ? void 0 : String(e?.message ?? e);
		} finally {
			this._busy = !1;
		}
	}
	render() {
		let e = this.ctx;
		if (!e) return T;
		let t = e.strings;
		return C`
      <nav class="subtabs" role="tablist">
        ${tn.map((e) => C`
            <button
              role="tab"
              aria-selected=${e === this._tab ? "true" : "false"}
              @click=${() => {
			this._tab = e, this._error = void 0, this._notice = void 0;
		}}
            >
              ${M(t, `test.tab.${e}`)}
            </button>
          `)}
      </nav>
      ${this._error ? C`<div class="problems" role="alert">${this._error}</div>` : T}
      ${this._notice && this._tab === "walktest" ? C`<div class="notice" role="status">${this._notice}</div>` : T}
      ${this._tab === "diagnostics" ? this._renderDiagnostics(t) : this._tab === "simulator" ? this._renderSimulator(t) : this._tab === "walktest" ? this._renderWalkTest(t) : this._renderActionTest(t)}
    `;
	}
	_renderDiagnostics(e) {
		let t = this._diagnostics;
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "test.diagnostics.title")}</h2>
          <span class="hint">${M(e, "test.diagnostics.subtitle")}</span>
          <button class="btn" ?disabled=${this._busy} @click=${() => void this._refresh()}>
            ${M(e, "test.refresh")}
          </button>
        </div>
        <div class="card-bd">
          ${t?.missing_entities.length ? C`<div class="problems" role="alert">
                <p>${M(e, "test.diagnostics.missing")}</p>
                <ul>
                  ${t.missing_entities.map((e) => C`<li class="mono">${e}</li>`)}
                </ul>
              </div>` : T}
          ${t ? t.zones.length === 0 ? C`<p class="empty">${M(e, "test.diagnostics.empty")}</p>` : C`<div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>${M(e, "test.col.zone")}</th>
                        <th>${M(e, "test.col.entity")}</th>
                        <th>${M(e, "test.col.state")}</th>
                        <th>${M(e, "test.col.evaluation")}</th>
                        <th>${M(e, "test.col.last_change")}</th>
                        <th>${M(e, "test.col.health")}</th>
                        <th>${M(e, "test.col.battery")}</th>
                        <th>${M(e, "test.col.signal")}</th>
                        <th>${M(e, "test.col.supervision")}</th>
                        <th>${M(e, "test.col.arming")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${t.zones.map((t) => this._renderZoneRow(e, t))}
                    </tbody>
                  </table>
                </div>` : C`<p class="hint">${M(e, "common.loading")}</p>`}
        </div>
      </div>
      ${t && t.devices.length ? this._renderDevices(e, t.devices) : T}
    `;
	}
	_renderZoneRow(e, t) {
		let n = this.ctx?.status.areas.find((e) => e.id === t.area_id)?.name ?? "";
		return C`
      <tr>
        <td>
          <strong>${t.name}</strong>
          ${n ? C`<div class="hint">${n}</div>` : T}
        </td>
        <td class="mono">${t.entity_id}</td>
        <td>
          ${t.state === null ? C`<span class="state fault">${M(e, "test.no_entity")}</span>` : C`<span class="mono">${t.state}</span>`}
        </td>
        <td>
          ${t.momentary ? C`<span class="muted">${M(e, "test.momentary")}</span>` : C`<span class="state ${t.triggered ? "open" : "closed"}">
                ${M(e, t.triggered ? "test.would_trigger" : "test.would_not")}
              </span>`}
        </td>
        <td class="mono">
          ${t.last_changed ? Y(t.last_changed, this.ctx?.hass.language, this.ctx?.hass) : "—"}
        </td>
        <td>
          ${t.enabled ? t.fault ? C`<span class="state fault">${M(e, `fault.${t.fault}`)}</span>` : C`<span class="state closed">${M(e, "test.ok")}</span>` : C`<span class="state disabled">${M(e, "test.disabled")}</span>`}
        </td>
        <td>${this._renderBattery(e, t)}</td>
        <td class="mono">
          ${t.signal ? `${t.signal.value} ${M(e, `test.unit.${t.signal.unit}`)}` : "—"}
        </td>
        <td class="hint">
          ${t.supervision_timeout === null ? M(e, "test.supervision_off") : M(e, "test.supervision_on", { n: t.supervision_timeout })}
        </td>
        <td>
          ${t.bypassed ? C`<span class="state bypassed">${M(e, `bypass.${t.bypassed}`)}</span>` : t.blocks_arming ? C`<span class="state fault"
                  >${M(e, `test.blocks.${t.blocks_because}`)}</span
                >` : C`<span class="muted">—</span>`}
        </td>
      </tr>
    `;
	}
	_renderBattery(e, t) {
		if (!t.battery_entity_id) return C`<span class="muted">—</span>`;
		let n = t.battery_level === null ? "" : `${Math.round(t.battery_level)} %`;
		return C`
      <span class="state ${t.battery_low ? "open" : "closed"}">
        ${n || M(e, t.battery_low ? "test.battery_low" : "test.battery_ok")}
      </span>
    `;
	}
	_renderDevices(e, t) {
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "test.devices.title")}</h2>
          <span class="hint">${M(e, "test.devices.subtitle")}</span>
        </div>
        <div class="card-bd">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${M(e, "test.col.device")}</th>
                  <th>${M(e, "test.col.kind")}</th>
                  <th>${M(e, "test.col.entity")}</th>
                  <th>${M(e, "test.col.state")}</th>
                  <th>${M(e, "test.col.last_change")}</th>
                  <th>${M(e, "test.col.health")}</th>
                </tr>
              </thead>
              <tbody>
                ${t.map((t) => C`
                    <tr>
                      <td><strong>${t.name}</strong></td>
                      <td>${M(e, `device_kind.${t.kind}`)}</td>
                      <td class="mono">${t.entity_id ?? "—"}</td>
                      <td class="mono">${t.state ?? "—"}</td>
                      <td class="mono">
                        ${t.last_changed ? Y(t.last_changed, this.ctx?.hass.language, this.ctx?.hass) : "—"}
                      </td>
                      <td>
                        ${t.enabled ? t.watchable ? t.available ? C`<span class="state closed">${M(e, "test.ok")}</span>` : C`<span class="state fault"
                                  >${M(e, "fault.unavailable")}</span
                                >` : C`<span class="muted">${M(e, "test.no_entity_kind")}</span>` : C`<span class="state disabled"
                              >${M(e, "test.disabled")}</span
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
		return C`
      <div class="notice info">
        <strong>${M(e, "test.simulator.safe_title")}</strong>
        ${M(e, "test.simulator.safe")}
      </div>
      <div class="split">
        <div class="card">
          <div class="card-hd">
            <h2>${M(e, "test.simulator.conditions")}</h2>
          </div>
          <div class="card-bd">
            <div class="grid-form">
              <label class="field">
                <span class="lbl">${M(e, "test.simulator.scenario")}</span>
                <select
                  .value=${this._scenario}
                  @change=${(e) => this._scenario = e.target.value}
                >
                  <option value="">${M(e, "test.simulator.disarmed")}</option>
                  ${t.status.scenarios.map((e) => C`<option
                      .value=${e.id}
                      .selected=${U(e.id === this._scenario)}
                    >
                      ${e.name}
                    </option>`)}
                </select>
                <span class="hint">${M(e, "test.simulator.scenario_hint")}</span>
              </label>
              <label class="field">
                <span class="lbl">${M(e, "test.simulator.clock")}</span>
                <input
                  type="datetime-local"
                  .value=${this._start}
                  @change=${(e) => this._start = e.target.value}
                />
                <span class="hint">${M(e, "test.simulator.clock_hint")}</span>
              </label>
            </div>
            ${this._renderOverrides(e)} ${this._renderEntityOverrides(e)}
            <div class="actions">
              <button
                class="btn primary"
                ?disabled=${this._busy}
                @click=${() => void this._run()}
              >
                ${M(e, "test.simulator.run")}
              </button>
              <button
                class="btn"
                @click=${() => {
			this._overrides = [], this._entities = {}, this._simulation = void 0, this._start = "", this._code = "", this._codeWanted = !1;
		}}
              >
                ${M(e, "test.simulator.reset")}
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
		return C`
      <fieldset>
        <legend>${M(e, "test.simulator.zones")}</legend>
        <p class="hint">${M(e, "test.simulator.zones_hint")}</p>
        ${this._overrides.map((n, r) => C`
            <div class="override">
              <select
                aria-label=${M(e, "test.simulator.pick_zone")}
                @change=${(e) => this._setOverride(r, {
			zone_id: e.target.value,
			state: rn(t, e.target.value)[0] ?? n.state
		})}
              >
                <option value="">${M(e, "test.simulator.pick_zone")}</option>
                ${t.status.zones.map((e) => C`<option
                    .value=${e.id}
                    .selected=${U(e.id === n.zone_id)}
                  >
                    ${e.name}
                  </option>`)}
              </select>
              <input
                class="state-input"
                aria-label=${M(e, "test.simulator.state")}
                .value=${n.state}
                list="foyer-sim-states-${r}"
                placeholder=${M(e, "test.simulator.state")}
                @change=${(e) => this._setOverride(r, { state: e.target.value })}
              />
              <datalist id="foyer-sim-states-${r}">
                ${rn(t, n.zone_id).map((e) => C`<option .value=${e}></option>`)}
              </datalist>
              <input
                class="at-input"
                type="number"
                min="0"
                .value=${String(n.at)}
                title=${M(e, "test.simulator.at")}
                aria-label=${M(e, "test.simulator.at")}
                @change=${(e) => this._setOverride(r, { at: Number(e.target.value) || 0 })}
              />
              <span class="hint">${M(e, "test.simulator.seconds")}</span>
              <button
                class="btn small"
                @click=${() => this._overrides = this._overrides.filter((e, t) => t !== r)}
              >
                ${M(e, "common.delete")}
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
          ${M(e, "test.simulator.add_zone")}
        </button>
      </fieldset>
    `;
	}
	_renderEntityOverrides(e) {
		let t = an(this.ctx);
		return t.length ? C`
      <fieldset>
        <legend>${M(e, "test.simulator.entities")}</legend>
        <p class="hint">${M(e, "test.simulator.entities_hint")}</p>
        <div class="grid-form">
          ${t.map((t) => C`
              <label class="field">
                <span class="lbl mono">${t}</span>
                <input
                  .value=${this._entities[t] ?? ""}
                  placeholder=${M(e, "test.simulator.as_now")}
                  @change=${(e) => {
			let n = e.target.value, r = { ...this._entities };
			n ? r[t] = n : delete r[t], this._entities = r;
		}}
                />
              </label>
            `)}
        </div>
      </fieldset>
    ` : T;
	}
	_setOverride(e, t) {
		this._overrides = this._overrides.map((n, r) => r === e ? {
			...n,
			...t
		} : n);
	}
	_renderTrace(e) {
		let t = this._simulation;
		return this._mentioned = /* @__PURE__ */ new Set(), C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "test.trace.title")}</h2>
          <span class="hint">${M(e, "test.trace.subtitle")}</span>
        </div>
        <div class="card-bd">
          ${this._premiseNeedsCode(t) ? this._renderCodePrompt(e) : T}
          ${t ? C`
                <ol class="trace">
                  ${t.steps.filter((e) => this._worthShowing(e)).map((t) => this._renderStep(e, t))}
                </ol>
                ${t.truncated ? C`<p class="notice">${M(e, "test.trace.truncated")}</p>` : T}
              ` : C`<p class="empty">
                ${M(e, this._busy ? "common.loading" : "test.trace.empty")}
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
		return C`
      <div class="notice">
        <p>${M(e, "test.simulator.premise_code")}</p>
        <input
          type="password"
          inputmode="numeric"
          autocomplete="off"
          aria-label=${M(e, "test.simulator.premise_code")}
          .value=${this._code}
          @change=${(e) => this._code = e.target.value}
        />
        <div class="actions">
          <button
            class="btn primary"
            ?disabled=${this._busy}
            @click=${() => void this._run()}
          >
            ${M(e, "test.simulator.run")}
          </button>
        </div>
      </div>
    `;
	}
	_renderStep(e, t) {
		let n = this.ctx, r = t.zone_id ? n.status.zones.find((e) => e.id === t.zone_id)?.name ?? t.zone_id : "";
		return C`
      <li class="step">
        <div class="when mono">${Y(t.at, this.ctx?.hass.language, this.ctx?.hass)}</div>
        <div class="what">
          ${t.kind === "zone" ? C`<div>
                ${M(e, "test.trace.zone", { zone: r })}
                <span class="mono">${t.zone_state}</span>
              </div>` : T}
          ${t.accepted ? T : C`<div class="no">
                ${M(e, `reason.${t.reason ?? "unknown"}`, { zones: t.blocking_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? e).join(", ") })}
              </div>`}
          ${t.low_battery_zones.length ? C`<div class="warn">
                ${M(e, "test.trace.low_battery", { zones: t.low_battery_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? e).join(", ") })}
              </div>` : T}
          ${t.areas.map((t) => C`
              <div class="key">
                ${M(e, "test.trace.area", {
			area: n.status.areas.find((e) => e.id === t.area_id)?.name ?? t.area_id,
			was: M(e, `state.${t.was}`),
			now: M(e, `state.${t.now}`)
		})}
                ${t.timer_due ? C`<span class="muted">
                      ${M(e, "test.trace.timer", {
			kind: M(e, `test.timer.${t.timer_kind}`),
			at: Y(t.timer_due, this.ctx?.hass.language, this.ctx?.hass)
		})}
                    </span>` : T}
              </div>
            `)}
          ${t.occurrences.map((t) => this._renderOccurrence(e, t))}
          ${this._renderBatches(e, t)}
          ${t.loose_actions.map((t) => t.escalation ? C`<div class="yes">
                  ${M(e, "test.trace.escalation_sent", {
			step: String(t.escalation_step ?? 0),
			who: this._whoFor(t.recipients)
		})}
                  ${this._renderCameras(e, t)}
                </div>` : C`<div class="yes">
                  ${M(e, "test.trace.ran", { action: M(e, `action_kind.${t.kind}`) })}
                </div>`)}
          ${t.scheduled.filter((e) => e.kind === "delay" || e.kind === "siren").filter((e) => this._firstMention(e)).map((t) => C`<div class="wait">
                ${M(e, `test.trace.later.${t.kind}`, { at: Y(t.at, this.ctx?.hass.language, this.ctx?.hass) })}
              </div>`)}
          ${t.scheduled.filter((e) => e.kind === "escalation_step").map((t) => C`<div class="wait">
                ${M(e, "test.trace.later.escalation_step", {
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
			let n = t.find((t) => t.id === e.contact_id), r = M(this.ctx.strings, `channel_kind.${e.kind}`);
			return `${n?.name ?? e.contact_id} (${r})`;
		}).join(", ");
	}
	_whoAhead(e, t) {
		let n = this.ctx?.config?.contacts ?? [];
		return e.map((e, r) => {
			let i = n.find((t) => t.id === e), a = i?.channels.find((e) => e.id === t[r]), o = a ? ` (${M(this.ctx.strings, `channel_kind.${a.kind}`)})` : "";
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
			return C`<div class="key">
        ${M(e, t.moment === "verification_satisfied" ? "test.trace.group_satisfied" : "test.trace.group", {
				group: i?.name ?? (r ? M(e, "test.trace.cross_zone") : M(e, "test.trace.a_group")),
				count: t.detail.count,
				n: t.detail.n,
				window: t.detail.window
			})}
      </div>`;
		}
		return t.moment.startsWith("incident_") ? C`<div class="key">
        ${M(e, `moment.${t.moment}`)}
        <span class="mono">${t.incident_id ?? ""}</span>
      </div>` : C`<div class="key">${M(e, `moment.${t.moment}`)}</div>`;
	}
	_renderBatches(e, t) {
		return C`${t.batches.filter((e) => e.actions.length > 0 || nn.has(e.moment)).map((t) => this._renderBatch(e, t))}`;
	}
	_renderBatch(e, t) {
		return t.profile_id ? C`
      <div class="batch">
        <div class="key">
          ${M(e, "test.trace.profile", {
			profile: t.profile_name,
			source: M(e, `test.source.${t.source}`)
		})}
        </div>
        ${t.actions.length ? t.actions.map((t) => this._renderAction(e, t)) : C`<div class="no">${M(e, "test.trace.nothing_configured")}</div>`}
      </div>
    ` : C`<div class="no">${M(e, "test.trace.no_profile")}</div>`;
	}
	_renderCameras(e, t) {
		let n = t.cameras ?? [];
		return n.length ? C`<span class="muted">
      ${M(e, "test.trace.cameras", { cameras: n.map((e) => this.ctx?.hass.states[e]?.attributes?.friendly_name ?? e).join(", ") })}
      ${t.cameras_omitted ? M(e, "test.trace.cameras_omitted", { count: String(t.cameras_omitted) }) : T}
    </span>` : T;
	}
	_renderAction(e, t) {
		let n = t.name || M(e, `action_kind.${t.kind}`);
		if (t.ran) return C`<div class="yes">
        ${M(e, "test.trace.ran", { action: n })}
        ${this._renderCameras(e, t)}
        ${t.recipients.length ? C`<span class="muted">
              ${M(e, "test.trace.reached", { who: this._whoFor(t.recipients) })}
            </span>` : T}
        ${t.quiet.length ? C`<span class="muted">
              ${M(e, "test.trace.quiet", { who: t.quiet.map((e) => (this.ctx?.config?.contacts ?? []).find((t) => t.id === e)?.name ?? e).join(", ") })}
            </span>` : T}
      </div>`;
		let r = t.skipped === "condition" ? M(e, "test.skip.condition", { conditions: t.conditions.map((t) => t.kind === "time" ? M(e, "test.condition.time", t) : M(e, "test.condition.state", {
			entity_id: t.entity_id,
			operator: M(e, `condition.${t.operator}`),
			state: t.state
		})).join(", ") }) : M(e, `test.skip.${t.skipped}`);
		return C`<div class=${t.skipped === "held_by_delay" ? "wait" : "no"}>
      ${M(e, "test.trace.skipped", {
			action: n,
			why: r
		})}
    </div>`;
	}
	_renderWalkTest(e) {
		let t = this.ctx.status.walk_test;
		return C`
      <div class="notice ${t ? "danger" : "warn"}">
        ${t ? M(e, "walk.active") : C`<strong>${M(e, "walk.idle_title")}</strong>
              ${M(e, "walk.idle")}
              <div class="hint">${M(e, "walk.always_on_live")}</div>`}
      </div>
      ${t ? this._renderWalkRunning(e, t) : this._renderWalkStart(e)}
    `;
	}
	_renderWalkStart(e) {
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "walk.start_title")}</h2>
          <span class="hint">${M(e, "walk.start_sub")}</span>
        </div>
        <div class="card-bd">
          <p>${M(e, "walk.explainer")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "walk.duration")}</span>
              <input
                type="number"
                min="1"
                .value=${this._walkDuration}
                placeholder=${M(e, "walk.duration_default")}
                @change=${(e) => this._walkDuration = e.target.value}
              />
              <span class="hint">${M(e, "walk.duration_hint")}</span>
            </label>
          </div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy}
              @click=${() => void this._startWalkTest()}
            >
              ${M(e, "walk.start")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderWalkRunning(e, t) {
		let n = this.ctx, r = new Map(n.status.zones.map((e) => [e.id, e])), i = new Map(n.status.areas.map((e) => [e.id, e.name])), a = t.expected_zones.filter((e) => !t.detections[e]), o = t.expected_zones.filter((e) => t.detections[e]), s = (n) => {
			let a = r.get(n), o = t.detections[n];
			return C`
        <tr>
          <td><strong>${a?.name ?? n}</strong></td>
          <td>${i.get(a?.area_id ?? "") ?? ""}</td>
          <td>
            <span class="state ${o ? "closed" : "fault"}">
              ${M(e, o ? "walk.detected" : "walk.never")}
            </span>
          </td>
          <td class="mono">${o ? Y(o.first, this.ctx?.hass.language, this.ctx?.hass) : "—"}</td>
          <td class="mono">${o ? o.count : 0}</td>
          <td>
            ${a?.fault ? C`<span class="state fault">${M(e, `fault.${a.fault}`)}</span>` : T}
          </td>
        </tr>
      `;
		};
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "walk.table_title")}</h2>
          <span class="hint">
            ${M(e, "walk.started_by", {
			who: t.user_name ?? M(e, "walk.somebody"),
			at: Y(t.started_at, this.ctx?.hass.language, this.ctx?.hass)
		})}
          </span>
        </div>
        <div class="card-bd">
          ${a.length ? C`<div class="problems" role="alert">
                ${M(e, a.length === 1 ? "walk.never_reacted_one" : "walk.never_reacted", { n: a.length })}
              </div>` : C`<div class="notice">${M(e, "walk.all_reacted")}</div>`}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${M(e, "test.col.zone")}</th>
                  <th>${M(e, "walk.col.area")}</th>
                  <th>${M(e, "walk.col.result")}</th>
                  <th>${M(e, "walk.col.first")}</th>
                  <th>${M(e, "walk.col.count")}</th>
                  <th>${M(e, "test.col.health")}</th>
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
			this._busy = !0, this._error = void 0, this._notice = void 0;
			try {
				let t = Number(this._walkDuration) || 0, n = await e.walkTest(!0, { duration: t > 0 ? t * 60 : void 0 });
				n.success ? n.blocking_zones.length && (this._notice = M(e.strings, "walk.partly_armed", { zones: n.blocking_zones.map((e) => e.name).join(", ") })) : this._error = Xe(e.strings, n, e.hass.language);
			} catch (e) {
				this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderActionTest(e) {
		let t = this.ctx.config?.profiles ?? [];
		return C`
      <div class="notice danger">
        <strong>${M(e, "action_test.warn_title")}</strong>
        ${M(e, "action_test.warn")}
      </div>
      ${this._confirming ? this._renderConfirm(e) : T}
      ${t.length === 0 ? C`<p class="empty">${M(e, "action_test.no_profiles")}</p>` : t.map((t) => this._renderProfileTests(e, t))}
    `;
	}
	_renderProfileTests(e, t) {
		let n = t.actions.filter((e) => e.kind !== "delay");
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${t.name}</h2>
          <span class="hint">${M(e, "action_test.subtitle")}</span>
        </div>
        <div class="card-bd">
          ${n.length === 0 ? C`<p class="empty">${M(e, "action_test.no_actions")}</p>` : C`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${M(e, "action_test.col.action")}</th>
                      <th>${M(e, "action_test.col.what")}</th>
                      <th>${M(e, "action_test.col.last")}</th>
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
		let r = `${t.id}:${n.id}`, i = this._tested[r], a = n.name || M(e, `action_kind.${n.kind}`);
		return C`
      <tr>
        <td><strong>${a}</strong></td>
        <td class="hint">${M(e, `action_test.what.${n.kind}`)}</td>
        <td>
          ${i ? i.ok ? C`<span class="state closed">${M(e, "action_test.ok")}</span>` : C`<span class="state fault" title=${i.error ?? ""}
                  >${M(e, "action_test.failed")}</span
                >` : C`<span class="muted">${M(e, "action_test.never")}</span>`}
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
            ${M(e, "action_test.test")}
          </button>
        </td>
      </tr>
    `;
	}
	_renderConfirm(e) {
		let t = this._confirming;
		return C`
      <div class="problems" role="alertdialog">
        <p>${M(e, "action_test.confirm", { action: t.name })}</p>
        <div class="actions">
          <button
            class="btn primary"
            ?disabled=${this._busy}
            @click=${() => void this._runTest(t)}
          >
            ${M(e, "action_test.confirm_yes")}
          </button>
          <button class="btn" @click=${() => this._confirming = void 0}>
            ${M(e, "common.cancel")}
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
				}), r = n.error ?? sn(t.strings, n.reason);
				this._tested = {
					...this._tested,
					[`${e.profile_id}:${e.action_id}`]: {
						ok: n.success,
						at: Date.now(),
						error: r || void 0
					}
				}, n.success || (this._error = M(t.strings, "action_test.failed_detail", {
					action: e.name,
					detail: r
				}));
			} catch (e) {
				this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	static {
		this.styles = [
			N,
			P,
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
function sn(e, t) {
	if (!t) return "";
	let n = M(e, `action_test.reason.${t}`);
	return n.startsWith("action_test.reason.") ? t : n;
}
customElements.get("foyer-page-test") || customElements.define("foyer-page-test", on);
//#endregion
//#region src/panel/pages/contacts.ts
async function cn(e, t) {
	try {
		if (window.isSecureContext && navigator.clipboard) return await navigator.clipboard.writeText(t), !0;
	} catch {}
	let n = document.createElement("textarea");
	n.value = t, n.setAttribute("readonly", ""), n.style.position = "fixed", n.style.opacity = "0", e.appendChild(n);
	try {
		return n.select(), document.execCommand("copy");
	} catch {
		return !1;
	} finally {
		n.remove();
	}
}
var ln = {
	name: "",
	channels: [],
	quiet_start: null,
	quiet_end: null,
	quiet_min_severity: "alarm",
	linked_user_id: null,
	enabled: !0
}, un = {
	kind: "push",
	service: "",
	target: "",
	data: {},
	actionable: !1,
	enabled: !0
}, dn = [
	"push",
	"disarm",
	"dtmf",
	"service"
];
function fn(e) {
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
function pn(e) {
	let t = e.params.contacts;
	return Array.isArray(t) ? t.map((e) => typeof e == "string" ? {
		contact_id: e,
		channel_id: null
	} : e).filter((e) => e && e.contact_id) : [];
}
var mn = class extends A {
	constructor(...e) {
		super(...e), this._problems = [], this._busy = !1, this._tested = {}, this._webhookProblems = [], this._confirmWebhook = !1, this._health = {};
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_tested: { state: !0 },
			_webhookProblems: { state: !0 },
			_webhookShown: { state: !0 },
			_confirmWebhook: { state: !0 },
			_copied: { state: !0 },
			_health: { state: !0 }
		};
	}
	connectedCallback() {
		super.connectedCallback(), this._loadHealth();
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._forgetWebhook();
	}
	_forgetWebhook() {
		this._webhookShown = void 0, this._confirmWebhook = !1, this._copied = void 0;
	}
	async _loadHealth() {
		if (this.ctx) try {
			let e = await this.ctx.health();
			this._health = Object.fromEntries(e.channels.filter((e) => e.fault).map((e) => [e.key, e.fault]));
		} catch {
			this._health = {};
		}
	}
	_edit(e) {
		this._busy || (this._draft = e ? structuredClone(e) : {
			...structuredClone(ln),
			channels: [structuredClone(un)]
		}, this._problems = [], L(this));
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
		let r = this._draft.channels[e]?.id;
		if (r && r in this._tested) {
			let { [r]: e, ...t } = this._tested;
			this._tested = t;
		}
	}
	_unsaved(e, t) {
		let n = this.ctx?.config?.contacts.find((t) => t.id === e.id)?.channels.find((e) => e.id === t.id);
		return !n || JSON.stringify(n) !== JSON.stringify(t);
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
			channels: [...this._draft.channels, structuredClone(un)]
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
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0);
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
						error: n.error ?? sn(this.ctx.strings, n.reason ?? null)
					}
				};
			} catch (e) {
				this._tested = {
					...this._tested,
					[t.id]: {
						ok: !1,
						error: String(e?.message ?? e)
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
			this._busy = !0, this._webhookProblems = [], this._forgetWebhook();
			try {
				let t = await this.ctx.setAckWebhook(e);
				t.success ? e && t.url ? this._webhookShown = {
					address: t.url,
					path: !1
				} : e && t.path && (this._webhookShown = {
					address: t.path,
					path: !0
				}) : this._webhookProblems = t.problems;
			} finally {
				this._busy = !1, this.requestUpdate();
			}
		}
	}
	async _copyWebhook() {
		let e = this._webhookShown?.address;
		e && (this._copied = await cn(this.renderRoot, e));
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return T;
		let t = e.strings, n = e.config.contacts ?? [];
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "contacts.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${M(t, "contacts.add")}
          </button>
        </div>
        ${n.length ? C`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${M(t, "field.name")}</th>
                    <th>${M(t, "contacts.channels_order")}</th>
                    <th>${M(t, "contacts.quiet_hours")}</th>
                    <th>${M(t, "field.linked_user_id")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${n.map((e) => this._row(t, e))}
                </tbody>
              </table>
            </div>` : C`<div class="empty">${M(t, "contacts.none")}</div>`}
        <div class="card-bd">
          <p class="note">${M(t, "contacts.orchestration")}</p>
        </div>
      </div>
      ${this._draft ? this._renderEditor(t, this._draft) : T}
      ${this._renderPolicies(t)} ${this._renderAcknowledgement(t)}
    `;
	}
	_row(e, t) {
		let n = (this.ctx?.config?.users ?? []).find((e) => e.id === t.linked_user_id);
		return C`<tr
      class="clickable"
 tabindex="0"
 @keydown=${B}
      aria-selected=${this._draft?.id === t.id ? "true" : "false"}
      @click=${() => this._edit(t)}
    >
      <td><strong>${t.name}</strong></td>
      <td>
        <div class="channels">
          ${t.channels.map((n, r) => {
			let i = this._health[`${t.id}:${n.id}`];
			return C`<span class="tag ${i ? "broken" : ""}"
              >${r + 1}. ${M(e, `channel_kind.${n.kind}`)} ·
              ${n.service}${i ? C` · <strong>${M(e, `health.fault_${i}`)}</strong>` : T}</span
            >`;
		})}
        </div>
      </td>
      <td class="mono">
        ${t.quiet_start ? `${t.quiet_start}–${t.quiet_end}` : M(e, "contacts.no_quiet_hours")}
      </td>
      <td>${n?.name ?? "—"}</td>
    </tr>`;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = n.config?.users ?? [], i = q(n.hass), a = n.meta?.contact_channel_kinds ?? [
			"push",
			"sms",
			"voice",
			"chat",
			"other"
		];
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "contacts.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.linked_user_id")}</span>
              <select
                @change=${(e) => this._set("linked_user_id", e.target.value || null)}
              >
                <option value="" .selected=${U(!t.linked_user_id)}>—</option>
                ${r.map((e) => C`<option
                    .value=${e.id ?? ""}
                    .selected=${U(e.id === t.linked_user_id)}
                  >
                    ${e.name}
                  </option>`)}
              </select>
              <span class="hint">${M(e, "contacts.linked_hint")}</span>
            </label>
          </div>

          <h3>${M(e, "contacts.channels")}</h3>
          <p class="note">${M(e, "contacts.channels_hint")}</p>
          ${t.channels.map((n, r) => this._renderChannel(e, t, n, r, i, a))}
          <button class="btn" @click=${() => this._addChannel()}>
            ${M(e, "contacts.add_channel")}
          </button>

          <h3>${M(e, "contacts.quiet_hours")}</h3>
          <p class="note">${M(e, "contacts.quiet_hint")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.quiet_start")}</span>
              <input
                type="time"
                .value=${t.quiet_start ?? ""}
                @change=${(e) => this._set("quiet_start", e.target.value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.quiet_end")}</span>
              <input
                type="time"
                .value=${t.quiet_end ?? ""}
                @change=${(e) => this._set("quiet_end", e.target.value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "contacts.quiet_min_severity")}</span>
              <select
                @change=${(e) => this._set("quiet_min_severity", e.target.value)}
              >
                ${[
			"info",
			"warning",
			"alarm"
		].map((n) => C`<option
                    .value=${n}
                    .selected=${U(n === t.quiet_min_severity)}
                  >
                    ${M(e, `severity.${n}`)}
                  </option>`)}
              </select>
              <span class="hint">${M(e, "contacts.quiet_severity_hint")}</span>
            </label>
          </div>

          ${this._problems.map((t) => C`<p class="problem">${z(e, t)}</p>`)}
        </div>
        <div class="card-ft">
          ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          <button class="btn" @click=${() => this._draft = void 0}>
            ${M(e, "common.cancel")}
          </button>
          <button class="btn primary" ?disabled=${this._busy} @click=${() => this._save()}>
            ${M(e, "common.save")}
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
		return C`
      <div class="channel">
        <div class="channel-hd">
          <span class="rank">${r + 1}</span>
          <div class="channel-tools">
            <button
              class="btn sm"
              aria-label=${M(e, "common.move_up")}
              title=${M(e, "common.move_up")}
              @click=${() => this._move(r, -1)}
            >
              ↑
            </button>
            <button
              class="btn sm"
              aria-label=${M(e, "common.move_down")}
              title=${M(e, "common.move_down")}
              @click=${() => this._move(r, 1)}
            >
              ↓
            </button>
            <button class="btn sm danger" @click=${() => this._removeChannel(r)}>
              ${M(e, "common.delete")}
            </button>
          </div>
        </div>
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${M(e, "field.kind")}</span>
            <select
              @change=${(e) => this._setChannel(r, { kind: e.target.value })}
            >
              ${a.map((t) => C`<option .value=${t} .selected=${U(t === n.kind)}>
                  ${M(e, `channel_kind.${t}`)}
                </option>`)}
            </select>
          </label>
          <label class="field">
            <span class="lbl">${M(e, "contacts.service")}</span>
            <select
              @change=${(e) => this._setChannel(r, { service: e.target.value })}
            >
              <option value="" .selected=${U(!n.service)}>—</option>
              ${s.map((e) => C`<option
                  .value=${e.id}
                  .selected=${U(e.id === n.service)}
                >
                  ${e.name}
                </option>`)}
            </select>
            <span class="hint">${M(e, "contacts.service_hint")}</span>
          </label>
          <label class="field">
            <span class="lbl">${M(e, "contacts.target")}</span>
            <input
              .value=${n.target}
              @input=${(e) => this._setChannel(r, { target: e.target.value })}
            />
            <span class="hint">${M(e, "contacts.target_hint")}</span>
          </label>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(n.actionable)}
              @change=${(e) => this._setChannel(r, { actionable: e.target.checked })}
            />
            <span class="lbl">${M(e, "contacts.actionable")}</span>
            <span class="hint">
              ${M(e, this._isEntity(n.service) ? "contacts.actionable_entity" : "contacts.actionable_hint")}
            </span>
          </label>
        </div>
        <div class="channel-ft">
          <button
            class="btn sm"
            ?disabled=${this._busy || !t.id || !n.id || this._unsaved(t, n)}
            @click=${() => this._test(t, n)}
          >
            ${M(e, "contacts.test")}
          </button>
          ${t.id && n.id && !this._unsaved(t, n) ? T : C`<span class="hint">${M(e, "contacts.test_after_save")}</span>`}
          ${o ? C`<span class=${o.ok ? "tag ok" : "tag bad"}>
                ${o.ok ? M(e, "contacts.test_sent") : o.error}
              </span>` : T}
        </div>
      </div>
    `;
	}
	_renderPolicies(e) {
		let t = this.ctx, n = t.config?.contacts ?? [], r = fn(t.config?.profiles ?? []);
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "contacts.policies")}</h2>
          <button class="btn" @click=${() => t.navigate("profiles")}>
            ${M(e, "contacts.edit_on_profiles")}
          </button>
        </div>
        ${r.size ? C`<div class="card-bd">
              ${[...r.values()].map((t) => C`
                  <h3>${t[0].profile.name}</h3>
                  ${t.map(({ action: t, index: r }) => C`
                      <div class="step">
                        <span class="mono at"
                          >${M(e, "contacts.step_offset", { n: String(t.escalation_offset) })}</span
                        >
                        <div>
                          <div class="who">
                            ${pn(t).map((t) => {
			let r = n.find((e) => e.id === t.contact_id), i = r?.channels.find((e) => e.id === t.channel_id);
			return i ? `${r?.name} · ${M(e, `channel_kind.${i.kind}`)}` : r?.name ?? M(e, "problem.unknown_contact");
		}).join(" · ") || String(t.params.service ?? "")}
                          </div>
                          <div class="mono">
                            ${M(e, "contacts.step_number")} ${r + 1} ·
                            ${M(e, `moment.${t.moments[0]}`)}
                          </div>
                        </div>
                      </div>
                    `)}
                `)}
              <p class="note">${M(e, "contacts.exhausted")}</p>
            </div>` : C`<div class="empty">${M(e, "contacts.no_policies")}</div>`}
      </div>
    `;
	}
	_renderAcknowledgement(e) {
		let t = this.ctx.config?.settings.ack_webhook_enabled ?? !1, n = this._webhookShown;
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "contacts.acknowledgement")}</h2>
        </div>
        <div class="card-bd">
          <p class="note">${M(e, "contacts.ack_stops")}</p>
          ${dn.map((t) => C`<div class="path">
              <div class="who">${M(e, `contacts.ack_${t}`)}</div>
              <div class="mono">${M(e, `contacts.ack_${t}_how`)}</div>
            </div>`)}
          <h3>${M(e, "contacts.webhook")}</h3>
          <div class="banner warn">
            <strong>${M(e, "contacts.webhook_warning")}</strong>
            <span>${M(e, "contacts.webhook_warning_hint")}</span>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t)}
              ?disabled=${this._busy}
              @change=${(e) => this._toggleWebhook(e.target.checked)}
            />
            <span class="lbl">${M(e, "contacts.webhook_enable")}</span>
          </label>
          ${this._webhookProblems.length ? C`<ul class="problems">
                ${this._webhookProblems.map((t) => C`<li>${z(e, t)}</li>`)}
              </ul>` : T}
          ${n ? C`<div class="once" role="status">
                <span class="lbl">${M(e, "contacts.webhook_once")}</span>
                <code class="secret">${n.address}</code>
                <div class="copy">
                  <button class="btn" @click=${() => this._copyWebhook()}>
                    ${M(e, "contacts.webhook_copy")}
                  </button>
                  ${this._copied === void 0 ? T : C`<span class="hint">
                        ${M(e, this._copied ? "contacts.webhook_copied" : "contacts.webhook_copy_failed")}
                      </span>`}
                </div>
                ${n.path ? C`<span class="hint">${M(e, "contacts.webhook_path_hint")}</span>` : T}
                <span class="hint">${M(e, "contacts.webhook_once_hint")}</span>
              </div>` : t ? C`<p class="hint">${M(e, "contacts.webhook_exists")}</p>` : T}
          ${t ? C`<p class="note">${M(e, "contacts.webhook_hint")}</p>
                <div class="actions">
                  ${this._confirmWebhook ? C`<span class="hint">${M(e, "contacts.webhook_confirm")}</span>
                        <button
                          class="btn danger"
                          ?disabled=${this._busy}
                          @click=${() => this._toggleWebhook(!0)}
                        >
                          ${M(e, "contacts.webhook_regenerate")}
                        </button>
                        <button class="btn" @click=${() => this._confirmWebhook = !1}>
                          ${M(e, "common.cancel")}
                        </button>` : C`<button
                        class="btn"
                        ?disabled=${this._busy}
                        @click=${() => this._confirmWebhook = !0}
                      >
                        ${M(e, "contacts.webhook_regenerate")}
                      </button>`}
                </div>` : T}
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			P,
			N,
			o`
      /* A channel Foyer cannot reach (§12.2). Red here as well as on page
         14, because this is the page somebody is on when they decide who
         gets told at four in the morning. */
      .tag.broken {
        border-color: var(--error-color, #e53935);
        color: var(--error-color, #e53935);
      }
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
      /* The address, the one time it is shown: set apart from the page so
         it reads as something to copy now rather than something that stays. */
      .once {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 8px;
        border: 1px solid var(--primary-color);
        background: var(--secondary-background-color);
      }
      .once .lbl {
        font-weight: 500;
      }
      .secret {
        font-family: var(--code-font-family, monospace);
        font-size: 13px;
        overflow-wrap: anywhere;
        user-select: all;
      }
      .copy {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
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
customElements.define("foyer-page-contacts", mn);
//#endregion
//#region src/panel/entity-list.ts
function hn(e) {
	return Object.values(e.states).map((e) => ({
		id: e.entity_id,
		name: String(e.attributes.friendly_name ?? e.entity_id)
	})).sort((e, t) => e.name.localeCompare(t.name));
}
function gn(e) {
	let { hass: t, s: n, chosen: r, candidates: i, listId: a, onChange: o } = e, s = new Map(i.map((e) => [e.id, e.name])), c = (t) => {
		if (!t) return;
		let n = t.value.trim(), a = n.toLowerCase(), c = i.filter((e) => e.name.toLowerCase() === a), l = s.has(n) ? n : c.length === 1 ? c[0].id : void 0;
		l && (t.value = "", !r.includes(l) && o(e.single ? [l] : [...r, l]));
	};
	return C`<div class="entity-list">
    ${r.length ? C`<ul>
          ${r.map((e) => {
		let i = t.states[e];
		return C`<li>
              <span class="who">
                <strong>${s.get(e) ?? String(i?.attributes.friendly_name ?? e)}</strong>
                <span class="muted">${e}</span>
              </span>
              <span class=${i ? "now" : "now missing"}>
                ${i ? J(t, e, i.state) : M(n, "entity_list.missing")}
              </span>
              <button class="btn sm" @click=${() => o(r.filter((t) => t !== e))}>
                ${M(n, "common.remove")}
              </button>
            </li>`;
	})}
        </ul>` : T}
    <div class="add-row">
      <input
        list=${a}
        placeholder=${M(n, "entity_list.placeholder")}
        aria-label=${M(n, "entity_list.placeholder")}
        @change=${(e) => {
		let t = e.target;
		s.has(t.value.trim()) && c(t);
	}}
        @keydown=${(e) => {
		e.key === "Enter" && c(e.target);
	}}
      />
      <button
        class="btn"
        @click=${(e) => c(e.target.previousElementSibling)}
      >
        ${M(n, e.single && r.length ? "entity_list.replace" : "common.add")}
      </button>
    </div>
    <datalist id=${a}>
      ${i.filter((e) => !r.includes(e.id)).map((e) => C`<option value=${e.id}>${e.name}</option>`)}
    </datalist>
  </div>`;
}
var _n = o`
  .entity-list ul {
    list-style: none;
    margin: 4px 0 8px;
    padding: 0;
  }
  .entity-list li {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
    border-bottom: 1px solid var(--divider-color, #e0e0e0);
  }
  .entity-list .who {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .entity-list .now {
    color: var(--secondary-text-color);
    white-space: nowrap;
  }
  .entity-list .now.missing {
    color: var(--error-color, #d32f2f);
  }
  .entity-list .add-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .entity-list .add-row input {
    flex: 1;
    min-width: 0;
  }
`, vn = [
	0,
	1,
	2,
	3,
	4,
	5,
	6
];
function yn(e, t) {
	return e ? new Date(e).toLocaleString(t, {
		dateStyle: "short",
		timeStyle: "short"
	}) : "";
}
function bn() {
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
		enabled: !0,
		exclude_open_zones: !1
	};
}
var xn = class extends A {
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
		this._busy || (this._draft = e ? structuredClone(e) : bn(), this._problems = [], L(this));
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	_setTrigger(e, t) {
		if (!this._draft) return;
		let n = {
			...this._draft.trigger,
			[e]: t
		};
		e === "kind" && t !== this._draft.trigger.kind && (n.entity_ids = []), this._set("trigger", n);
	}
	_setAction(e) {
		let t = this._draft;
		if (!t) return;
		let n = e === "disarm" && t.grace_seconds === 120 ? 0 : e !== "disarm" && t.grace_seconds === 0 ? 120 : t.grace_seconds;
		this._draft = {
			...t,
			action: e,
			grace_seconds: n
		};
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
				this._problems = e.problems, e.success || R(this), e.success && (this._draft = void 0);
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
			t.success || (this._error = M(this.ctx.strings, `reason.${t.reason ?? "unknown"}`));
		} catch (e) {
			this._error = M(this.ctx.strings, "problem.request_failed", { detail: String(e?.message ?? e) });
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
		})), this._error || (this._visitor = {
			name: "",
			start: "",
			until: "",
			reduced_scenario_id: null
		}));
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return T;
		let t = e.strings, n = this._auto;
		return C`
      ${this._renderNext(t)}
      ${this._error ? C`<div class="problems" role="alert">${this._error}</div>` : T}
      ${this._renderRules(t)}
      ${this._draft ? this._renderEditor(t, this._draft) : T}
      ${this._renderSuspensions(t, n?.suspensions ?? [])}
      ${this._renderDisarming(t)}
    `;
	}
	_renderNext(e) {
		let t = this.ctx, n = this._auto, r = n?.next, i = n?.pending ?? [];
		return n?.enabled ? i.length ? C`${i.map((n) => C`<div class="banner crit">
          <div>
            ${M(e, `rules.counting_${n.action}`, {
			rule: n.rule_name,
			scenario: this._scenarioName(n.scenario_id),
			seconds: Math.max(0, Math.round((Date.parse(n.due) - t.now()) / 1e3))
		})}
            ${n.suspension_name ? C`<em>${M(e, "rules.because", { name: n.suspension_name })}</em>` : T}
          </div>
          <span class="spacer"></span>
          <button
            class="btn sm primary"
            ?disabled=${this._busy}
            @click=${() => this._run(() => t.cancelAuto(n.id))}
          >
            ${M(e, "rules.cancel_now")}
          </button>
        </div>`)}` : C`<div class="banner info">
      <div>
        ${r ? M(e, `rules.next_${r.action}`, {
			rule: r.rule_name,
			scenario: this._scenarioName(r.scenario_id),
			when: yn(r.at, t.hass.language)
		}) : M(e, "rules.next_none")}
      </div>
      <span class="spacer"></span>
      <button
        class="btn sm"
        ?disabled=${this._busy}
        @click=${() => this._run(() => t.setAutoArming(!1))}
      >
        ${M(e, "rules.switch_off")}
      </button>
    </div>` : C`<div class="banner warn">
        <div>${M(e, "rules.switched_off")}</div>
        <span class="spacer"></span>
        <button
          class="btn sm"
          ?disabled=${this._busy}
          @click=${() => this._run(() => t.setAutoArming(!0))}
        >
          ${M(e, "rules.switch_on")}
        </button>
      </div>`;
	}
	_scenarioName(e) {
		return e ? this.ctx?.config?.scenarios.find((t) => t.id === e)?.name ?? "" : "";
	}
	_triggerText(e, t) {
		let n = t.trigger, r = n.entity_ids.length;
		switch (n.kind) {
			case "absence": return M(e, "rules.trigger_absence", {
				n: r,
				minutes: n.minutes
			});
			case "presence": return M(e, "rules.trigger_presence", { n: r });
			case "time": return M(e, "rules.trigger_time", {
				at: n.at ?? "",
				days: this._days(e, n.weekdays)
			});
			default: return M(e, "rules.trigger_entity", {
				entity: n.entity_ids[0] ?? "",
				state: n.state ?? "",
				minutes: n.minutes
			});
		}
	}
	_days(e, t) {
		return t.length ? t.map((t) => M(e, `rules.weekday_${t}`)).join(", ") : M(e, "rules.every_day");
	}
	_actionText(e, t) {
		if (t.action === "disarm") {
			let n = this.ctx?.config?.areas ?? [];
			return M(e, "rules.action_disarm", { areas: t.area_ids.map((e) => n.find((t) => t.id === e)).filter((e) => e !== void 0).map((e) => e.name).join(", ") });
		}
		return M(e, `rules.action_${t.action}`, { scenario: this._scenarioName(t.scenario_id) });
	}
	_guardText(e, t) {
		let n = [];
		return t.guards.only_when_disarmed && n.push(M(e, "rules.guard_disarmed")), t.guards.only_when_ready && n.push(M(e, "rules.guard_ready")), t.guards.quiet_minutes !== null && n.push(M(e, "rules.guard_quiet", { minutes: t.guards.quiet_minutes })), n.length ? n.join(" · ") : M(e, "rules.guard_none");
	}
	_renderRules(e) {
		let t = this.ctx.config?.rules ?? [], n = this._auto?.blocked ?? {};
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "rules.title")}</h2>
          <button class="btn primary" @click=${() => this._edit()}>
            ${M(e, "rules.add")}
          </button>
        </div>
        ${t.length ? C`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${M(e, "field.name")}</th>
                    <th>${M(e, "field.trigger")}</th>
                    <th>${M(e, "rules.action")}</th>
                    <th>${M(e, "field.window")}</th>
                    <th>${M(e, "field.guards")}</th>
                    <th>${M(e, "field.grace_seconds")}</th>
                    <th>${M(e, "rules.status")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${t.map((t) => C`<tr
                      class="clickable"
 tabindex="0"
 @keydown=${B}
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
                        ${t.grace_seconds ? M(e, "common.seconds", { n: t.grace_seconds }) : M(e, "rules.at_once")}
                      </td>
                      <td>
                        ${t.enabled ? n[t.id ?? ""] ? C`<span class="pill warn"
                                >${M(e, `rules.block_${n[t.id ?? ""]}`)}</span
                              >` : C`<span class="pill ok">${M(e, "rules.active")}</span>` : C`<span class="pill idle">${M(e, "rules.disabled")}</span>`}
                      </td>
                    </tr>`)}
                </tbody>
              </table>
            </div>` : C`<div class="empty">${M(e, "rules.none")}</div>`}
      </div>
    `;
	}
	_renderEditor(e, t) {
		let n = this.ctx, r = K(n.hass, n.meta?.presence_domains ?? ["person"]), i = n.meta?.max_grace_seconds ?? 900, a = n.meta?.max_rule_minutes ?? 1440, o = t.trigger;
		return C`
      <div class="card editor">
        <div class="card-hd">
          <h2>${t.id ? t.name : M(e, "rules.new")}</h2>
        </div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.name")}</span>
              <input
                .value=${t.name}
                @input=${(e) => this._set("name", e.target.value)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.trigger")}</span>
              <select
                @change=${(e) => this._setTrigger("kind", e.target.value)}
              >
                ${(n.meta?.rule_triggers ?? []).map((t) => C`<option .value=${t} .selected=${U(t === o.kind)}>
                      ${M(e, `rules.trigger_kind_${t}`)}
                    </option>`)}
              </select>
              <span class="hint">${M(e, `rules.trigger_hint_${o.kind}`)}</span>
            </label>
            ${o.kind === "time" ? C`<label class="field">
                  <span class="lbl">${M(e, "rules.at")}</span>
                  <input
                    type="time"
                    .value=${o.at ?? ""}
                    @change=${(e) => this._setTrigger("at", e.target.value || null)}
                  />
                </label>` : C`<label class="field">
                  <span class="lbl">${M(e, "rules.for_minutes")}</span>
                  <input
                    type="number"
                    min="0"
                    max=${a}
                    .value=${String(o.minutes)}
                    ?disabled=${o.kind === "presence"}
                    @input=${(e) => V(e, (e) => this._setTrigger("minutes", e))}
                  />
                </label>`}
          </div>

          ${o.kind === "absence" || o.kind === "presence" ? C`<div class="block">
                <div class="lbl strong">${M(e, "rules.people")}</div>
                ${r.length ? gn({
			hass: n.hass,
			s: e,
			chosen: o.entity_ids,
			candidates: r,
			listId: "foyer-rule-people",
			onChange: (e) => this._setTrigger("entity_ids", e)
		}) : C`<span class="hint">${M(e, "rules.no_people")}</span>`}
                <span class="hint">${M(e, "rules.people_hint")}</span>
              </div>` : T}
          ${o.kind === "entity" ? C`<div class="field">
                  <span class="lbl">${M(e, "field.entity_id")}</span>
                  ${gn({
			hass: n.hass,
			s: e,
			chosen: o.entity_ids,
			candidates: hn(n.hass),
			listId: "foyer-rule-entity",
			single: !0,
			onChange: (e) => this._setTrigger("entity_ids", e)
		})}
                </div>
                <div class="grid-form">
                <label class="field">
                  <span class="lbl">${M(e, "field.state")}</span>
                  <input
                    .value=${o.state ?? ""}
                    @change=${(e) => this._setTrigger("state", e.target.value || null)}
                  />
                </label>
              </div>` : T}
          ${o.kind === "time" ? this._renderDays(e, o.weekdays, (e) => this._setTrigger("weekdays", e)) : T}

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "rules.action")}</span>
              <select
                @change=${(e) => this._setAction(e.target.value)}
              >
                ${(n.meta?.rule_actions ?? []).map((n) => C`<option .value=${n} .selected=${U(n === t.action)}>
                      ${M(e, `rules.action_kind_${n}`)}
                    </option>`)}
              </select>
            </label>
            ${t.action === "disarm" ? T : C`<label class="field">
                  <span class="lbl">${M(e, "field.scenario_id")}</span>
                  <select
                    @change=${(e) => this._set("scenario_id", e.target.value || null)}
                  >
                    <option value="" .selected=${U(!t.scenario_id)}>
                      ${M(e, "rules.choose_scenario")}
                    </option>
                    ${(n.config?.scenarios ?? []).map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === t.scenario_id)}>
                          ${e.name}
                        </option>`)}
                  </select>
                </label>`}
          </div>
          ${t.action === "disarm" ? this._renderDisarmAreas(e, t) : T}

          <div class="hr"></div>
          <div class="lbl strong">${M(e, "field.window")}</div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.after")}</span>
              <input
                type="time"
                .value=${t.window.after ?? ""}
                @change=${(e) => this._setWindow("after", e.target.value || null)}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.before")}</span>
              <input
                type="time"
                .value=${t.window.before ?? ""}
                @change=${(e) => this._setWindow("before", e.target.value || null)}
              />
            </label>
          </div>
          ${this._renderDays(e, t.window.weekdays, (e) => this._setWindow("weekdays", e))}
          <span class="hint">${M(e, "rules.window_hint")}</span>

          <div class="hr"></div>
          <div class="lbl strong">${M(e, "field.guards")}</div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.guards.only_when_disarmed)}
              @change=${(e) => this._setGuard("only_when_disarmed", e.target.checked)}
            />
            <span>${M(e, "rules.guard_disarmed")}</span>
          </label>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.guards.only_when_ready)}
              @change=${(e) => this._setGuard("only_when_ready", e.target.checked)}
            />
            <span>
              ${M(e, "rules.guard_ready")}
              <span class="hint">${M(e, "rules.guard_ready_hint")}</span>
            </span>
          </label>
          ${t.action === "disarm" ? T : C`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${U(!!t.exclude_open_zones)}
                    @change=${(e) => this._set("exclude_open_zones", e.target.checked)}
                  />
                  <span>
                    ${M(e, "field.exclude_open_zones")}
                    <span class="hint">${M(e, "rules.exclude_open_hint")}</span>
                  </span>
                </label>
                ${t.exclude_open_zones ? C`<div class="notice">
                      ${M(e, t.guards.only_when_ready ? "rules.exclude_open_no_effect" : "rules.exclude_open_warning")}
                    </div>` : T}`}
          <label class="field">
            <span class="lbl">${M(e, "rules.guard_quiet_label")}</span>
            <input
              type="number"
              min="1"
              max=${a}
              .value=${t.guards.quiet_minutes === null ? "" : String(t.guards.quiet_minutes)}
              @input=${(e) => this._setGuard("quiet_minutes", H(e.target.value))}
            />
            <span class="hint">${M(e, "rules.guard_quiet_hint")}</span>
          </label>

          <div class="hr"></div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.grace_seconds")}</span>
              <input
                type="number"
                min="0"
                max=${i}
                .value=${String(t.grace_seconds)}
                @input=${(e) => V(e, (e) => this._set("grace_seconds", e))}
              />
              <span class="hint">${M(e, "rules.grace_hint")}</span>
            </label>
          </div>
          <div class="block">
            <div class="lbl strong">${M(e, "field.notify_contact_ids")}</div>
            <p class="hint">${M(e, "rules.notify_outcome_hint")}</p>
            <div class="chips">
              ${(n.config?.contacts ?? []).map((e) => C`<label class="chip">
                  <input
                    type="checkbox"
                    .checked=${U(t.notify_contact_ids.includes(e.id ?? ""))}
                    @change=${(n) => this._set("notify_contact_ids", n.target.checked ? [...t.notify_contact_ids, e.id ?? ""] : t.notify_contact_ids.filter((t) => t !== e.id))}
                  />
                  <span>${e.name}</span>
                </label>`)}
            </div>
            <span class="hint">${M(e, "rules.notify_hint")}</span>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.enabled)}
              @change=${(e) => this._set("enabled", e.target.checked)}
            />
            <span>${M(e, "rules.enabled")}</span>
          </label>

          ${this._problems.length ? C`<div class="problems" role="alert">
                <ul>
                  ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
                </ul>
              </div>` : T}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${M(e, "common.save")}
            </button>
            <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
              ${M(e, "common.cancel")}
            </button>
            ${t.id ? C`<foyer-delete-button
                .strings=${e}
                .name=${t.name}
                ?disabled=${this._busy}
                @confirm=${this._delete}
              ></foyer-delete-button>` : T}
          </div>
        </div>
      </div>
    `;
	}
	_renderDays(e, t, n) {
		return C`<div class="chips days">
      ${vn.map((r) => C`<label class="chip">
          <input
            type="checkbox"
            .checked=${U(t.includes(r))}
            @change=${(e) => n(e.target.checked ? [...t, r].sort((e, t) => e - t) : t.filter((e) => e !== r))}
          />
          <span>${M(e, `rules.weekday_${r}`)}</span>
        </label>`)}
    </div>`;
	}
	_renderDisarmAreas(e, t) {
		let n = this.ctx?.config?.areas ?? [];
		return C`<div class="block">
      <div class="lbl strong">${M(e, "field.area_ids")}</div>
      <div class="chips">
        ${n.map((n) => {
			let r = t.area_ids.includes(n.id ?? "");
			return C`<label class=${n.is_perimeter ? "chip never" : "chip"}>
            <input
              type="checkbox"
              .checked=${U(r)}
              ?disabled=${n.is_perimeter}
              @change=${(e) => this._set("area_ids", e.target.checked ? [...t.area_ids, n.id ?? ""] : t.area_ids.filter((e) => e !== n.id))}
            />
            <span>
              ${n.name}
              ${n.is_perimeter ? C`<em>&nbsp;· ${M(e, "rules.never_disarmed")}</em>` : T}
            </span>
          </label>`;
		})}
      </div>
    </div>`;
	}
	_renderSuspensions(e, t) {
		let n = this.ctx, r = n.config?.rules ?? [], i = this._visitor;
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "rules.suspensions")}</h2>
        </div>
        <div class="card-bd">
          <p class="hint">${M(e, "rules.visitor_intro")}</p>
          ${t.length ? C`<div class="stack">
                ${t.map((t) => C`<div class="suspension">
                    <div>
                      <div class="lbl strong">
                        ${t.name ?? M(e, `rules.suspension_${t.kind}`)}
                      </div>
                      <div class="hint mono">
                        ${t.kind === "next" ? M(e, "rules.suspension_next_hint") : `${yn(t.start, n.hass.language)} – ${yn(t.until, n.hass.language)}`}
                        ${t.rule_ids.length ? ` · ${t.rule_ids.map((e) => r.find((t) => t.id === e)?.name ?? e).join(", ")}` : ` · ${M(e, "rules.every_rule")}`}
                        ${t.reduced_scenario_id ? ` · ${M(e, "rules.instead", { scenario: this._scenarioName(t.reduced_scenario_id) })}` : ""}
                      </div>
                    </div>
                    <span class="spacer"></span>
                    <button
                      class="btn sm"
                      ?disabled=${this._busy}
                      @click=${() => this._run(() => n.liftSuspension(t.id))}
                    >
                      ${M(e, "rules.lift")}
                    </button>
                  </div>`)}
              </div>` : C`<div class="empty">${M(e, "rules.no_suspensions")}</div>`}

          <div class="hr"></div>
          <div class="lbl strong">${M(e, "rules.visitor")}</div>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "rules.reason")}</span>
              <input
                .value=${i.name}
                placeholder=${M(e, "rules.reason_placeholder")}
                @input=${(e) => this._visitor = {
			...i,
			name: e.target.value
		}}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.after")}</span>
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
              <span class="lbl">${M(e, "field.before")}</span>
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
              <span class="lbl">${M(e, "rules.instead_label")}</span>
              <select
                @change=${(e) => this._visitor = {
			...i,
			reduced_scenario_id: e.target.value || null
		}}
              >
                <option value="" .selected=${U(!i.reduced_scenario_id)}>
                  ${M(e, "rules.instead_nothing")}
                </option>
                ${(n.config?.scenarios ?? []).map((e) => C`<option
                      .value=${e.id ?? ""}
                      .selected=${U(e.id === i.reduced_scenario_id)}
                    >
                      ${e.name}
                    </option>`)}
              </select>
              <span class="hint">${M(e, "rules.instead_hint")}</span>
            </label>
          </div>
          <div class="actions">
            <button
              class="btn primary"
              ?disabled=${this._busy || !i.name.trim() || !i.until}
              @click=${this._addVisitor}
            >
              ${M(e, "rules.add_visitor")}
            </button>
            ${(n.config?.rules ?? []).length ? C`<button
                  class="btn"
                  ?disabled=${this._busy}
                  @click=${() => this._run(() => n.suspend({
			kind: "next",
			rule_ids: []
		}))}
                >
                  ${M(e, "rules.skip_next")}
                </button>` : T}
          </div>
        </div>
      </div>
    `;
	}
	_renderDisarming(e) {
		let t = this.ctx, n = t.config?.settings.allow_auto_disarm ?? !1, r = t.config?.areas ?? [];
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "rules.disarming")}</h2>
        </div>
        <div class="card-bd">
          <div class="notice">${M(e, "rules.disarming_warning")}</div>
          ${I(t) ? C`<div class="notice" role="note">${M(e, "rules.allow_disarm_armed")}</div>` : T}
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(n)}
              ?disabled=${this._busy}
              @change=${async (n) => {
			let r = n.target.checked;
			this._busy = !0, this._error = void 0;
			try {
				let n = await t.saveSettings({ allow_auto_disarm: r });
				n.success || (this._error = n.problems.map((t) => z(e, t)).join(" ") || M(e, "reason.code_required"));
			} finally {
				this._busy = !1, this.requestUpdate();
			}
		}}
            />
            <span>
              ${M(e, "rules.allow_disarm")}
              <span class="hint">${M(e, "rules.allow_disarm_hint")}</span>
            </span>
          </label>
          <div class="hr"></div>
          <div class="lbl strong">${M(e, "rules.areas_a_rule_may_disarm")}</div>
          <div class="chips">
            ${r.map((t) => C`<span class=${t.is_perimeter ? "pill bad" : "pill ok"}>
                  ${t.name}${t.is_perimeter ? ` · ${M(e, "rules.never_disarmed")}` : ""}
                </span>`)}
          </div>
          <p class="hint">${M(e, "rules.perimeter_note")}</p>
        </div>
      </div>
    `;
	}
	static {
		this.styles = [
			N,
			P,
			_n,
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
customElements.get("foyer-page-rules") || customElements.define("foyer-page-rules", xn);
//#endregion
//#region src/panel/pages/log.ts
var X = 50, Sn = class extends A {
	constructor(...e) {
		super(...e), this._rows = [], this._total = 0, this._offset = 0, this._filters = {}, this._busy = !1, this._confirmClear = !1, this._loaded = !1, this._person = "", this._keepPseudonym = !1, this._confirmErase = !1;
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
			_confirmClear: { state: !0 },
			_person: { state: !0 },
			_counts: { state: !0 },
			_keepPseudonym: { state: !0 },
			_confirmErase: { state: !0 },
			_erased: { state: !0 }
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
				Je(t.filename, t.content, e === "csv" ? "text/csv" : "application/json"), t.truncated && (this._error = M(this.ctx.strings, "log.truncated", {
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
				let e = await this.ctx.clearLog();
				if (!e.success) {
					this._error = M(this.ctx.strings, `reason.${e.reason ?? "unknown"}`);
					return;
				}
				this._offset = 0, await this._load();
			} catch (e) {
				this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _pick(e) {
		if (this._person = e, this._counts = void 0, this._confirmErase = !1, this._erased = void 0, e && this.ctx) try {
			let t = await this.ctx.previewPerson(e);
			this._person === e && (this._counts = t);
		} catch (e) {
			this._error = String(e?.message ?? e);
		}
	}
	async _exportPerson(e) {
		if (this.ctx && this._person) {
			this._busy = !0, this._error = void 0;
			try {
				let t = await this.ctx.exportPerson(this._person, e);
				Je(t.filename, t.content, e === "csv" ? "text/csv" : "application/json"), t.truncated && (this._error = M(this.ctx.strings, "log.truncated", {
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
	async _erasePerson() {
		if (this.ctx && this._person) {
			this._confirmErase = !1, this._busy = !0, this._error = void 0;
			try {
				let e = await this.ctx.erasePerson(this._person, this._keepPseudonym);
				e.success ? (this._erased = e.removed ?? 0, this._counts = await this.ctx.previewPerson(this._person), await this._load()) : e.reason && (this._error = M(this.ctx.strings, `reason.${e.reason}`));
			} catch (e) {
				this._error = String(e?.message ?? e);
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderPeople(e) {
		let t = this.ctx.config?.users;
		if (!t?.length) return T;
		let n = this._counts;
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "log.person_title")}</h2></div>
        <div class="card-bd">
          <p class="hint">${M(e, "log.person_intro")}</p>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "log.person")}</span>
              <select
                .value=${this._person}
                @change=${(e) => void this._pick(e.target.value)}
              >
                <option value="">${M(e, "log.person_none")}</option>
                ${t.map((e) => C`<option .value=${e.id} .selected=${U(e.id === this._person)}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
          </div>
          ${n ? C`
                <p class="hint">
                  ${M(e, "log.person_found", {
			total: n.total,
			by_id: n.by_id,
			by_name: n.by_name,
			about: n.about
		})}
                </p>
                <p class="hint">${M(e, "log.person_export_rows", { rows: n.wide })}</p>
                <div class="actions">
                  <button
                    class="btn"
                    ?disabled=${this._busy}
                    @click=${() => void this._exportPerson("csv")}
                  >
                    ${M(e, "log.person_export_csv")}
                  </button>
                  <button
                    class="btn"
                    ?disabled=${this._busy}
                    @click=${() => void this._exportPerson("json")}
                  >
                    ${M(e, "log.person_export_json")}
                  </button>
                  <button
                    class="btn danger"
                    ?disabled=${this._busy || n.total === 0}
                    @click=${() => this._confirmErase = !0}
                  >
                    ${M(e, "log.person_erase")}
                  </button>
                </div>
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${U(this._keepPseudonym)}
                    @change=${(e) => this._keepPseudonym = e.target.checked}
                  />
                  <span>${M(e, "log.person_keep_pseudonym")}</span>
                </label>
                <p class="hint">${M(e, "log.person_keep_pseudonym_hint")}</p>
              ` : T}
          ${this._erased === void 0 ? T : C`<p class="hint">${M(e, "log.person_erased", { rows: this._erased })}</p>`}
          ${this._confirmErase ? C`<div class="problems" role="alert">
                <p>
                  ${M(e, this._keepPseudonym ? "log.person_erase_confirm_pseudonym" : "log.person_erase_confirm", { rows: n?.total ?? 0 })}
                </p>
                <div class="actions">
                  <button class="btn danger" @click=${() => void this._erasePerson()}>
                    ${M(e, "log.person_erase_yes")}
                  </button>
                  <button class="btn" @click=${() => this._confirmErase = !1}>
                    ${M(e, "common.cancel")}
                  </button>
                </div>
              </div>` : T}
        </div>
      </div>
    `;
	}
	render() {
		let e = this.ctx;
		if (!e) return T;
		let t = e.strings;
		return C`${this._renderFilters(t)} ${this._renderRows(t)} ${this._renderPeople(t)}`;
	}
	_vocabulary(e, t, n) {
		if (n?.length) return n;
		let r = e[t];
		return r && typeof r == "object" ? Object.keys(r) : [];
	}
	_renderFilters(e) {
		let t = this.ctx, n = this._vocabulary(e, "category", t.meta?.log_categories), r = this._vocabulary(e, "severity", t.meta?.log_severities), i = this._vocabulary(e, "outcome", t.meta?.outcomes), a = this._filters.categories ?? [];
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "log.filters")}</h2></div>
        <div class="card-bd">
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "log.from")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.start ?? ""}
                @change=${(e) => this._filter({ start: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "log.to")}</span>
              <input
                type="datetime-local"
                .value=${this._filters.end ?? ""}
                @change=${(e) => this._filter({ end: e.target.value || null })}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "log.area")}</span>
              <select
                @change=${(e) => this._filter({ area_id: e.target.value || null })}
              >
                <option value="">${M(e, "log.all")}</option>
                ${t.status.areas.map((e) => C`<option .value=${e.id} .selected=${U(e.id === this._filters.area_id)}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "log.zone")}</span>
              <select
                @change=${(e) => this._filter({ zone_id: e.target.value || null })}
              >
                <option value="">${M(e, "log.all")}</option>
                ${t.status.zones.map((e) => C`<option .value=${e.id} .selected=${U(e.id === this._filters.zone_id)}>
                      ${e.name}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "log.severity")}</span>
              <select
                @change=${(e) => this._filter({ severity: e.target.value || null })}
              >
                <option value="">${M(e, "log.all")}</option>
                ${r.map((t) => C`<option .value=${t} .selected=${U(t === this._filters.severity)}>
                      ${M(e, `severity.${t}`)}
                    </option>`)}
              </select>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "log.outcome")}</span>
              <select
                @change=${(e) => this._filter({ outcome: e.target.value || null })}
              >
                <option value="">${M(e, "log.all")}</option>
                ${i.map((t) => C`<option .value=${t} .selected=${U(t === this._filters.outcome)}>
                      ${M(e, `outcome.${t}`)}
                    </option>`)}
              </select>
            </label>
          </div>
          <fieldset>
            <legend>${M(e, "log.categories")}</legend>
            <div class="chips">
              ${n.map((t) => C`
                  <button
                    class="chip"
                    aria-pressed=${a.includes(t) ? "true" : "false"}
                    @click=${() => this._filter({ categories: a.includes(t) ? a.filter((e) => e !== t) : [...a, t] })}
                  >
                    ${M(e, `category.${t}`)}
                  </button>
                `)}
            </div>
            <p class="hint">${M(e, "log.categories_hint")}</p>
          </fieldset>
          ${this._filters.incident_id ? C`<p class="hint">
                ${M(e, "log.incident_filter", { id: this._filters.incident_id })}
                <button class="btn small" @click=${() => this._filter({ incident_id: null })}>
                  ${M(e, "log.clear_filter")}
                </button>
              </p>` : T}
        </div>
      </div>
    `;
	}
	_renderRows(e) {
		let t = this.ctx, n = this._rows.length;
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(e, "log.events")}</h2>
          <span class="hint"
            >${M(e, "log.count", {
			shown: n ? `${this._offset + 1}–${this._offset + n}` : "0",
			total: this._total
		})}</span
          >
          <button class="btn" ?disabled=${this._busy} @click=${() => void this._load()}>
            ${M(e, "log.refresh")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("csv")}>
            ${M(e, "log.export_csv")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._export("json")}>
            ${M(e, "log.export_json")}
          </button>
          ${t.isAdmin ? C`<button class="btn danger" ?disabled=${this._busy} @click=${() => this._confirmClear = !0}>
                ${M(e, "log.clear")}
              </button>` : T}
        </div>
        <div class="card-bd">
          ${this._error ? C`<div class="problems" role="alert">${this._error}</div>` : T}
          ${this._confirmClear ? C`<div class="problems" role="alert">
                <p>${M(e, "log.clear_confirm")}</p>
                <div class="actions">
                  <button class="btn danger" @click=${this._clear}>
                    ${M(e, "log.clear_yes")}
                  </button>
                  <button class="btn" @click=${() => this._confirmClear = !1}>
                    ${M(e, "common.cancel")}
                  </button>
                </div>
              </div>` : T}
          ${n === 0 ? C`<p class="hint">${M(e, this._busy ? "common.loading" : "log.empty")}</p>` : C`<div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>${M(e, "log.time")}</th>
                      <th>${M(e, "log.event")}</th>
                      <th>${M(e, "log.category")}</th>
                      <th>${M(e, "log.where")}</th>
                      <th>${M(e, "log.who")}</th>
                      <th>${M(e, "log.detail")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this._rows.map((t) => this._renderRow(e, t))}
                  </tbody>
                </table>
              </div>`}
          ${this._total > X ? C`<div class="actions">
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset === 0}
                  @click=${() => {
			this._offset = Math.max(0, this._offset - X), this._load();
		}}
                >
                  ${M(e, "log.newer")}
                </button>
                <button
                  class="btn"
                  ?disabled=${this._busy || this._offset + X >= this._total}
                  @click=${() => {
			this._offset += X, this._load();
		}}
                >
                  ${M(e, "log.older")}
                </button>
              </div>` : T}
        </div>
      </div>
    `;
	}
	_renderRow(e, t) {
		let n = this.ctx, r = n.status.areas.find((e) => e.id === t.area_id), i = n.status.zones.find((e) => e.id === t.zone_id), a = this._open === t.id, o = [r?.name, i?.name].filter(Boolean).join(" · ");
		return C`
      <tr class="clickable"
 tabindex="0"
 @keydown=${B} aria-selected=${a ? "true" : "false"} @click=${() => this._open = a ? void 0 : t.id}>
        <td class="mono">${new Date(t.ts).toLocaleString(n.hass.language, F(n.hass))}</td>
        <td>
          <span class="state ${Tn(t.severity)}">
            ${Cn(e, t.event_type)}
          </span>
        </td>
        <td><span class="tag">${M(e, `category.${t.category}`)}</span></td>
        <td>${o}</td>
        <td>
          ${t.user_name ?? (t.channel ? wn(e, t.channel) : "")}
          ${t.detail?.attributed === "claimed" ? C`<span class="claimed">${M(e, "log.claimed")}</span>` : T}
        </td>
        <td class="detail">${this._summary(e, t)}</td>
      </tr>
      ${a ? C`<tr class="expanded">
            <td colspan="6">
              <dl class="kv">
                ${t.incident_id ? C`<dt>${M(e, "log.incident")}</dt>
                      <dd>
                        <button
                          class="btn small"
                          @click=${(e) => {
			e.stopPropagation(), this._filter({ incident_id: t.incident_id });
		}}
                        >
                          ${M(e, "log.show_incident")}
                        </button>
                      </dd>` : T}
                ${t.outcome ? C`<dt>${M(e, "log.outcome")}</dt>
                      <dd>${M(e, `outcome.${t.outcome}`)}</dd>` : T}
                ${t.channel ? C`<dt>${M(e, "log.channel")}</dt>
                      <dd>${wn(e, t.channel)}</dd>` : T}
                ${this._changeLines(e, t).map((t, n) => C`<dt>${n ? "" : M(e, "log.changes")}</dt>
                    <dd>${t}</dd>`)}
                ${this._plainDetail(e, t).map(([t, n]) => C`<dt>${this._detailLabel(e, t)}</dt>
                    <dd class="mono">${n}</dd>`)}
              </dl>
            </td>
          </tr>` : T}
    `;
	}
	_summary(e, t) {
		let n = this.ctx, r = t.detail ?? {};
		if (t.event_type === "duress") return this._duressSummary(e, t);
		if (typeof r.reason == "string" && r.reason) {
			let t = Array.isArray(r.blocking_zones) ? r.blocking_zones.map((e) => n.status.zones.find((t) => t.id === e)?.name ?? String(e)).join(", ") : "", i = `reason.${r.reason}`, a = M(e, i, { zones: t });
			return a === i ? M(e, `rules.block_${r.reason}`) : a;
		}
		if (typeof r.error == "string") return r.error;
		if (t.event_type === "zone_state") return `${r.from ?? "?"} → ${r.to ?? "?"}`;
		if (t.event_type === "tokens_rejected") return M(e, "log.tokens_rejected", {
			count: String(r.count ?? "?"),
			addresses: String(r.addresses ?? "?")
		});
		if (t.event_type === "reloaded") return M(e, "log.gap_short", { seconds: String(r.gap_seconds ?? "") });
		if (t.event_type === "system_unavailable" && typeof r.down_since == "string" && r.down_since !== "") return M(e, "log.gap", {
			from: new Date(r.down_since).toLocaleString(n.hass.language, F(n.hass)),
			to: new Date(String(r.up_at)).toLocaleString(n.hass.language, F(n.hass))
		});
		if (typeof r.kind == "string" && t.category === "action") return M(e, `action_kind.${r.kind}`);
		let i = this._changeLines(e, t);
		return i.length ? i.length > 2 ? `${i.slice(0, 2).join(" · ")} ${M(e, "log.and_more", { count: i.length - 2 })}` : i.join(" · ") : "";
	}
	_duressSummary(e, t) {
		let n = this.ctx.status, r = t.detail ?? {}, i = (e) => {
			let t = r[e];
			return typeof t == "string" ? t : "";
		}, a = i("operation"), o = `operation.${a}`, s = a ? M(e, o) : "", c = [
			...[...i("areas").split(","), i("area")].filter(Boolean).map((e) => n.areas.find((t) => t.id === e)?.name ?? e),
			...[i("scenario")].filter(Boolean).map((e) => n.scenarios.find((t) => t.id === e)?.name ?? e),
			...[i("zone")].filter(Boolean).map((e) => n.zones.find((t) => t.id === e)?.name ?? e)
		];
		return [s === o ? a : s, c.join(", ")].filter(Boolean).join(" · ");
	}
	_changeLines(e, t) {
		let n = t.detail?.changes;
		if (!n || typeof n != "object" || Array.isArray(n)) return [];
		let r = [];
		for (let [t, i] of Object.entries(n)) {
			let n = M(e, `config_kind.${t}`);
			if (t === "reason" && typeof i == "string") {
				r.push(`${n}: ${M(e, `reason.${i}`)}`);
				continue;
			}
			if (typeof i != "object" || !i) {
				r.push(`${n}: ${this._value(e, i)}`);
				continue;
			}
			let a = i;
			if (!("added" in a || "removed" in a || "changed" in a)) {
				r.push(...this._fieldLines(e, n, a));
				continue;
			}
			for (let t of a.added ?? []) r.push(`${n} · ${M(e, "log.added")}: ${t}`);
			for (let t of a.removed ?? []) r.push(`${n} · ${M(e, "log.removed")}: ${t}`);
			let o = a.changed ?? {};
			for (let [t, i] of Object.entries(o)) r.push(...this._fieldLines(e, `${n} «${t}»`, i));
		}
		return r;
	}
	_fieldLines(e, t, n) {
		return Array.isArray(n) ? n.map((n) => `${t} · ${this._fieldLabel(e, n)}`) : Object.entries(n).map(([n, r]) => {
			let i = this._fieldLabel(e, n);
			return Array.isArray(r) && r.length === 2 ? `${t} · ${i}: ${this._value(e, r[0])} → ${this._value(e, r[1])}` : `${t} · ${i}: ${M(e, "log.changed")}`;
		});
	}
	_fieldLabel(e, t) {
		let n = M(e, `field.${t.replace(/\./g, "_")}`);
		return n.startsWith("field.") ? t : n;
	}
	_value(e, t) {
		return t == null || t === "" ? "—" : typeof t == "boolean" ? M(e, t ? "common.yes" : "common.no") : Array.isArray(t) ? t.length ? t.map((t) => this._value(e, t)).join(", ") : "—" : String(t);
	}
	_detailLabel(e, t) {
		let n = M(e, `detail.${t}`);
		return n === `detail.${t}` ? t : n;
	}
	_plainDetail(e, t) {
		let n = /* @__PURE__ */ new Set([
			"changes",
			"zone_ids",
			"blocking_zones"
		]), r = (n, r) => {
			if (t.event_type !== "duress" || typeof r != "string") return null;
			let i = n === "operation" ? `operation.${r}` : n === "target" ? `log.duress_target.${r}` : "";
			if (!i) return null;
			let a = M(e, i);
			return a === i ? null : a;
		};
		return Object.entries(t.detail ?? {}).filter(([e, t]) => !n.has(e) && t !== null && t !== "").map(([t, n]) => [t, r(t, n) ?? (n === "true" || n === "false" ? this._value(e, n === "true") : typeof n == "object" ? JSON.stringify(n) : this._value(e, n))]);
	}
	static {
		this.styles = [
			N,
			P,
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
function Cn(e, t) {
	let n = M(e, `event_type.${t}`);
	if (!n.startsWith("event_type.")) return n;
	let r = M(e, `moment.${t}`);
	return r.startsWith("moment.") ? t : r;
}
function wn(e, t) {
	let n = M(e, `log_channel.${t}`);
	return n.startsWith("log_channel.") ? t : n;
}
function Tn(e) {
	return e === "alarm" ? "triggered" : e === "warning" ? "arming" : "disarmed";
}
customElements.get("foyer-page-log") || customElements.define("foyer-page-log", Sn);
//#endregion
//#region src/panel/pages/settings.ts
var En = 30, Dn = {
	targets: [],
	mode: "sound",
	sound: null,
	tts_entity: null,
	volume: null,
	quiet_start: null,
	quiet_end: null,
	during_exit: !1
}, On = class extends A {
	constructor(...e) {
		super(...e), this._problems = [], this._backupProblems = [], this._busy = !1, this._saved = !1, this._restored = !1, this._confirmPseudonymise = !1, this._languages = [], this._alarmoDone = !1;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_draft: { state: !0 },
			_settings: { state: !0 },
			_problems: { state: !0 },
			_backupProblems: { state: !0 },
			_busy: { state: !0 },
			_saved: { state: !0 },
			_restored: { state: !0 },
			_confirmPseudonymise: { state: !0 },
			_languages: { state: !0 },
			_alarmo: { state: !0 },
			_alarmoDone: { state: !0 }
		};
	}
	connectedCallback() {
		super.connectedCallback(), this.ctx?.hass.callWS({ type: "foyer/languages" }).then((e) => this._languages = e.languages ?? []).catch(() => this._languages = []);
	}
	get _chime() {
		return this._draft ?? structuredClone(this.ctx?.config?.chime ?? Dn);
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
				this._problems = e.problems, this._problemsIn = "chime", e.success && (this._draft = void 0, this._saved = !0);
			} finally {
				this._busy = !1;
			}
		}
	}
	async _saveSettings(e, t) {
		if (this.ctx?.config) {
			this._settings = {
				...this._settings ?? this.ctx.config.settings,
				...e
			}, this._busy = !0;
			try {
				let n = await this.ctx.saveSettings(e);
				this._problems = n.problems, this._problemsIn = t, this._settings = void 0;
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderProblems(e, t) {
		return this._problemsIn !== t || !this._problems.length ? T : C`<div class="problems" role="alert">
      <ul>
        ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
      </ul>
    </div>`;
	}
	render() {
		let e = this.ctx;
		return e?.config ? C`${this._renderDefaults(e.strings)} ${this._renderResponse(e.strings)}
    ${this._renderChime(e.strings, this._chime)} ${this._renderLog(e.strings)}
    ${this._renderPrivacy(e.strings)} ${this._renderBackup(e.strings)}
    ${this._renderAlarmo(e.strings)} ${this._renderLanguage(e.strings)}` : T;
	}
	_entities(e) {
		return K(this.ctx.hass, e);
	}
	_renderDefaults(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.meta?.bounds ?? {}, i = (t, r, i) => C`<label class="field">
      <span class="lbl">${M(e, `field.${t}`)}</span>
      <input
        type="number"
        min=${r ? r[0] : 0}
        max=${r ? r[1] : 3600}
        .value=${String(n[t])}
        @change=${(e) => V(e, (e) => void this._saveSettings({ [t]: e }, "defaults"))}
      />
      <span class="hint">${i ?? M(e, "common.seconds_unit")}</span>
    </label>`;
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "settings.defaults_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${M(e, "settings.defaults_intro")}</p>
          ${I(t) ? C`<div class="notice" role="note">${M(e, "settings.defaults_armed")}</div>` : T}
          <div class="grid-form">
            ${i("siren_duration", r.siren_duration, M(e, "settings.siren_duration_hint"))}
            ${i("arm_hold_timeout", r.arm_hold_timeout, M(e, "settings.arm_hold_hint"))}
            ${i("default_entry_delay", r.entry_delay, M(e, "settings.area_defaults_hint"))}
            ${i("default_exit_delay", r.exit_delay, M(e, "settings.area_defaults_hint"))}
            ${i("low_battery_threshold", r.low_battery_threshold, M(e, "settings.low_battery_hint"))}
            ${i("walk_test_timeout", r.walk_test_timeout, M(e, "settings.walk_test_hint"))}
          </div>
          ${this._renderProblems(e, "defaults")}
        </div>
      </div>
    `;
	}
	_renderLog(e) {
		let t = this.ctx, n = (this._settings ?? t.config.settings).log, r = t.meta?.log_categories ?? [], [i, a] = t.meta?.retention_bounds ?? [1, 3650], o = (e) => {
			let t = {
				...n,
				...e,
				enabled: {
					...n.enabled,
					...e.enabled ?? {}
				},
				retention_days: {
					...n.retention_days,
					...e.retention_days ?? {}
				}
			};
			this._saveSettings({ log: t }, "log");
		};
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "settings.log_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${M(e, "settings.log_intro")}</p>
          <div class="rows">
            ${r.map((t) => {
			let r = n.enabled[t] !== !1;
			return C`<div class="row">
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${U(r)}
                    @change=${(e) => o({ enabled: { [t]: e.target.checked } })}
                  />
                  <span>${M(e, `category.${t}`)}</span>
                </label>
                <span class="spacer"></span>
                ${r ? C`<label class="field inline">
                      <input
                        type="number"
                        min=${i}
                        max=${a}
                        .value=${String(n.retention_days[t] ?? 30)}
                        @change=${(e) => V(e, (e) => o({ retention_days: { [t]: e } }))}
                      />
                      <span class="hint">${M(e, "settings.log_days")}</span>
                    </label>` : C`<span class="hint">${M(e, "settings.log_off")}</span>`}
              </div>
              ${!r && t === "security" ? C`<p class="hint">${M(e, "settings.log_security_off")}</p>` : T}`;
		})}
          </div>
          <p class="hint">${M(e, "settings.log_rows_hint")}</p>
          <div class="actions">
            <button
              class="btn"
              ?disabled=${this._busy}
              @click=${() => o({ retention_days: Object.fromEntries((t.meta?.named_categories ?? []).map((e) => [e, t.meta?.short_retention ?? 7])) })}
            >
              ${M(e, "settings.short_preset", { days: t.meta?.short_retention ?? 7 })}
            </button>
          </div>
          <p class="hint">
            ${M(e, "settings.short_preset_hint", {
			days: t.meta?.short_retention ?? 7,
			categories: (t.meta?.named_categories ?? []).map((t) => M(e, `category.${t}`)).join(", ")
		})}
          </p>
          ${this._renderProblems(e, "log")}
        </div>
      </div>
    `;
	}
	_renderPrivacy(e) {
		let t = this.ctx, n = (this._settings ?? t.config.settings).log, [r, i] = t.meta?.pseudonymise_bounds ?? [1, 365], a = n.pseudonymise_after !== null, o = (e) => void this._saveSettings({ log: {
			...n,
			...e
		} }, "privacy");
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "settings.privacy_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${M(e, "settings.privacy_intro")}</p>
          <div class="row">
            <label class="check">
              <input
                type="checkbox"
                .checked=${U(a || this._confirmPseudonymise)}
                @change=${(e) => {
			e.target.checked ? this._confirmPseudonymise = !0 : (this._confirmPseudonymise = !1, o({ pseudonymise_after: null }));
		}}
              />
              <span>${M(e, "settings.pseudonymise")}</span>
            </label>
            <span class="spacer"></span>
            ${a ? C`<label class="field inline">
                  <input
                    type="number"
                    min=${r}
                    max=${i}
                    .value=${String(n.pseudonymise_after ?? 30)}
                    @change=${(e) => V(e, (e) => o({ pseudonymise_after: e }))}
                  />
                  <span class="hint">${M(e, "settings.log_days")}</span>
                </label>` : T}
          </div>
          <div class="notice">${M(e, "settings.pseudonymise_warning")}</div>
          ${this._confirmPseudonymise ? C`<div class="problems" role="alert">
                <p>${M(e, "settings.pseudonymise_confirm", { days: 30 })}</p>
                <div class="actions">
                  <button
                    class="btn danger"
                    @click=${() => {
			this._confirmPseudonymise = !1, o({ pseudonymise_after: En });
		}}
                  >
                    ${M(e, "settings.pseudonymise_yes")}
                  </button>
                  <button
                    class="btn"
                    @click=${() => this._confirmPseudonymise = !1}
                  >
                    ${M(e, "common.cancel")}
                  </button>
                </div>
              </div>` : T}
          <p class="hint">${M(e, "settings.pseudonymise_hint")}</p>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(n.delete_on_uninstall)}
              @change=${(e) => o({ delete_on_uninstall: e.target.checked })}
            />
            <span>${M(e, "settings.delete_on_uninstall")}</span>
          </label>
          <p class="hint">${M(e, "settings.delete_on_uninstall_hint")}</p>
          <p class="hint">${M(e, "settings.uninstall_snapshots_hint")}</p>
          ${this._renderProblems(e, "privacy")}
        </div>
      </div>
    `;
	}
	_renderBackup(e) {
		let t = (this.ctx.meta?.schema_version ?? []).join(".");
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "settings.backup_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${M(e, "settings.backup_intro")}</p>
          <div class="actions">
            <button class="btn" ?disabled=${this._busy} @click=${this._exportConfig}>
              ${M(e, "settings.backup_export")}
            </button>
            <label class="btn file">
              ${M(e, "settings.backup_import")}
              <input type="file" accept="application/json,.json" @change=${this._importConfig} />
            </label>
          </div>
          <p class="hint">${M(e, "settings.backup_hint")}</p>
          <p class="hint">${M(e, "settings.backup_version", { version: t })}</p>
          ${this._backupProblems.length ? C`<div class="problems" role="alert">
                <ul>
                  ${this._backupProblems.map((t) => C`<li>${z(e, t)}</li>`)}
                </ul>
              </div>` : T}
          ${this._restored ? C`<div class="notice">${M(e, "settings.backup_restored")}</div>` : T}
        </div>
      </div>
    `;
	}
	async _exportConfig() {
		if (this.ctx) {
			this._busy = !0, this._backupProblems = [];
			try {
				let e = await this.ctx.exportConfig();
				if (!e.success || !e.filename || !e.document) {
					this._backupProblems = e.problems?.length ? e.problems : [{
						code: e.reason ?? "request_failed",
						kind: "code",
						ref: null,
						field: null
					}];
					return;
				}
				Je(e.filename, JSON.stringify(e.document, null, 2), "application/json");
			} catch (e) {
				this._backupProblems = [{
					code: "request_failed",
					kind: "config",
					ref: null,
					field: null,
					detail: String(e?.message ?? e)
				}];
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
				this._backupProblems = t.problems, this._restored = t.success;
			} catch {
				this._backupProblems = [{
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
	_alarmoLabels(e) {
		return {
			modes: Object.fromEntries([
				"armed_away",
				"armed_home",
				"armed_night",
				"armed_vacation",
				"armed_custom_bypass"
			].map((t) => [t, M(e, `alarmo.mode.${t}`)])),
			split: M(e, "alarmo.split_name"),
			profile: M(e, "alarmo.profile_name")
		};
	}
	_alarmoText(e, t, n) {
		let r = {
			mode: "alarmo.mode",
			setting: "alarmo.setting",
			kind: "alarmo.kind",
			type: "alarmo.sensor_type"
		}, i = Object.fromEntries(Object.entries(n.params).map(([t, n]) => [t, t in r ? M(e, `${r[t]}.${n}`) : n]));
		return M(e, `alarmo.${t}.${n.code}`, i);
	}
	async _alarmoRead() {
		if (this.ctx) {
			this._busy = !0, this._alarmoDone = !1;
			try {
				this._alarmo = await this.ctx.alarmoPreview(this._alarmoLabels(this.ctx.strings));
			} catch (e) {
				let t = String(e?.message ?? e);
				this._alarmo = {
					success: !1,
					problems: [{
						code: "request_failed",
						kind: "config",
						ref: null,
						field: null,
						detail: t
					}]
				};
			} finally {
				this._busy = !1;
			}
		}
	}
	async _alarmoApply() {
		let e = this._alarmo?.fingerprint;
		if (this.ctx && e) {
			this._busy = !0;
			try {
				let t = await this.ctx.alarmoApply(e, this._alarmoLabels(this.ctx.strings));
				t.success ? (this._alarmo = void 0, this._alarmoDone = !0) : this._alarmo = {
					...this._alarmo,
					success: !1,
					refused: t.refused,
					problems: t.problems ?? []
				};
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderAlarmo(e) {
		let t = this._alarmo, n = t?.created, r = (t) => n && n[t].length ? C`<li>${M(e, `alarmo.created.${t}`, { names: n[t].join(", ") })}</li>` : T;
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "alarmo.title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${M(e, "alarmo.intro")}</p>
          <div class="actions">
            <button class="btn" ?disabled=${this._busy} @click=${this._alarmoRead}>
              ${M(e, "alarmo.read")}
            </button>
            ${t?.fingerprint ? C`<button
                  class="btn primary"
                  ?disabled=${this._busy || !t.success}
                  @click=${this._alarmoApply}
                >
                  ${M(e, "alarmo.apply")}
                </button>` : T}
          </div>
          ${this._alarmoDone ? C`<div class="notice" role="status">${M(e, "alarmo.applied")}</div>` : T}
          ${t?.refused ? C`<div class="problems" role="alert">
                ${this._alarmoText(e, "refused", t.refused)}
              </div>` : T}
          ${t?.problems?.length ? C`<div class="problems" role="alert">
                <ul>
                  ${t.problems.map((t) => C`<li>${z(e, t)}</li>`)}
                </ul>
              </div>` : T}
          ${n ? C`<h3>${M(e, "alarmo.summary_title")}</h3>
                <ul class="alarmo-list">
                  ${r("areas")}
                  <li>
                    ${M(e, "alarmo.created.zones", { count: t?.counts?.zones ?? 0 })}
                  </li>
                  ${r("scenarios")} ${r("extended")} ${r("people")}
                  ${r("profiles")}
                </ul>` : T}
          ${t?.lines?.length ? C`<h3>${M(e, "alarmo.report_title")}</h3>
                <ul class="alarmo-list">
                  ${t.lines.map((t) => C`<li>${this._alarmoText(e, "line", t)}</li>`)}
                </ul>` : T}
          <p class="hint">${M(e, "alarmo.hint")}</p>
        </div>
      </div>
    `;
	}
	_renderLanguage(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings;
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "settings.language_title")}</h2></div>
        <div class="card-bd">
          <label class="field">
            <span class="lbl">${M(e, "field.language")}</span>
            <select
              @change=${(e) => this._saveSettings({ language: e.target.value || null }, "language")}
            >
              <option value="" .selected=${U(!n.language)}>
                ${M(e, "settings.language_system")}
              </option>
              ${n.language && !this._languages.some((e) => e.code === n.language) ? C`<option .value=${n.language} selected>
                    ${n.language}
                  </option>` : T}
              ${this._languages.map((e) => C`<option
                    .value=${e.code}
                    .selected=${U(e.code === n.language)}
                  >
                    ${e.name}
                  </option>`)}
            </select>
            <span class="hint">${M(e, "settings.language_hint")}</span>
          </label>
          ${this._renderProblems(e, "language")}
        </div>
      </div>
    `;
	}
	_renderResponse(e) {
		let t = this.ctx, n = this._settings ?? t.config.settings, r = t.config.profiles ?? [], i = t.meta?.silenceable ?? [], a = (t, i) => C`<label class="field">
        <span class="lbl">${M(e, `field.${t}`)}</span>
        <select
          @change=${(e) => this._saveSettings({ [t]: e.target.value || null }, "response")}
        >
          <option value="" .selected=${U(!n[t])}>${M(e, "settings.none")}</option>
          ${r.map((e) => C`<option .value=${e.id ?? ""} .selected=${U(e.id === n[t])}>
                ${e.name}
              </option>`)}
        </select>
        <span class="hint">${i}</span>
      </label>`;
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "settings.response_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${M(e, "settings.response_intro")}</p>
          ${I(t) ? C`<div class="notice" role="note">${M(e, "settings.response_armed")}</div>` : T}
          <div class="grid-form">
            ${a("default_profile_id", M(e, "settings.default_profile_hint"))}
            ${a("technical_profile_id", M(e, "settings.technical_profile_hint"))}
            <label class="field">
              <span class="lbl">${M(e, "field.camera_dir")}</span>
              <input
                .value=${n.camera_dir}
                @change=${(e) => this._saveSettings({ camera_dir: e.target.value.trim() }, "response")}
              />
              <span class="hint">${M(e, "settings.camera_dir_hint")}</span>
            </label>
          </div>
          <fieldset>
            <legend>${M(e, "field.silent_suppresses")}</legend>
            ${i.map((t) => C`<label class="check">
                  <input
                    type="checkbox"
                    .checked=${U(n.silent_suppresses.includes(t))}
                    @change=${(e) => {
			let r = e.target.checked ? [...n.silent_suppresses, t] : n.silent_suppresses.filter((e) => e !== t);
			this._saveSettings({ silent_suppresses: r }, "response");
		}}
                  />
                  <span
                    >${t === "chime" ? M(e, "settings.chime_title") : M(e, `action_kind.${t}`)}</span
                  >
                </label>`)}
            <p class="hint">${M(e, "settings.silent_hint")}</p>
          </fieldset>
          ${this._renderProblems(e, "response")}
        </div>
      </div>
    `;
	}
	_renderChime(e, t) {
		let n = this.ctx, r = mt(n.hass, n.meta?.chime_domains ?? [
			"media_player",
			"siren",
			"notify"
		]);
		for (let e of t.targets) r.some((t) => t.id === e.entity_id) || r.push({
			id: e.entity_id,
			name: e.entity_id
		});
		let i = this._entities(["tts"]), a = (e) => (t) => this._set(e, t.target.value || null);
		return C`
      <div class="card">
        <div class="card-hd"><h2>${M(e, "settings.chime_title")}</h2></div>
        <div class="card-bd">
          <p class="intro">${M(e, "settings.chime_intro")}</p>
          <fieldset>
            <legend>${M(e, "field.targets")}</legend>
            ${r.length ? r.map((t) => this._renderTarget(e, t)) : C`<p class="hint">${M(e, "settings.no_targets")}</p>`}
            <p class="hint">${M(e, "settings.targets_hint")}</p>
          </fieldset>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.mode")}</span>
              <select
                @change=${(e) => this._set("mode", e.target.value)}
              >
                ${["sound", "speech"].map((n) => C`<option .value=${n} .selected=${U(n === t.mode)}>
                      ${M(e, `chime_mode.${n}`)}
                    </option>`)}
              </select>
            </label>
            ${t.mode === "speech" ? C`<label class="field">
                    <span class="lbl">${M(e, "field.tts_entity")}</span>
                    <select
                      @change=${(e) => this._set("tts_entity", e.target.value || null)}
                    >
                      <option value="" .selected=${U(!t.tts_entity)}>
                        ${M(e, "settings.pick_tts")}
                      </option>
                      ${i.map((e) => C`<option .value=${e.id} .selected=${U(e.id === t.tts_entity)}>
                            ${e.name}
                          </option>`)}
                    </select>
                    <span class="hint">${M(e, "settings.tts_hint")}</span>
                  </label>` : C`<label class="field">
                    <span class="lbl">${M(e, "field.sound")}</span>
                    <input
                      .value=${t.sound ?? ""}
                      @input=${(e) => this._set("sound", e.target.value.trim() || null)}
                    />
                    <span class="hint">${M(e, "settings.sound_hint")}</span>
                  </label>`}
            <label class="field">
              <span class="lbl">${M(e, "field.volume")}</span>
              <input
                type="number"
                min="0"
                max="100"
                .value=${t.volume == null ? "" : String(t.volume)}
                @input=${(e) => this._set("volume", H(e.target.value))}
              />
              <span class="hint">${M(e, "settings.volume_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.quiet_start")}</span>
              <input type="time" .value=${t.quiet_start ?? ""} @input=${a("quiet_start")} />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.quiet_end")}</span>
              <input type="time" .value=${t.quiet_end ?? ""} @input=${a("quiet_end")} />
              <span class="hint">${M(e, "settings.quiet_hint")}</span>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.during_exit)}
              @change=${(e) => this._set("during_exit", e.target.checked)}
            />
            <span>
              ${M(e, "field.during_exit")}
              <span class="hint">${M(e, "settings.during_exit_hint")}</span>
            </span>
          </label>
          <p class="hint">${M(e, "settings.switch_hint")}</p>
          ${this._renderProblems(e, "chime")}
          ${this._saved ? C`<div class="notice">${M(e, "settings.saved")}</div>` : T}
          <div class="actions">
            <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
              ${M(e, "common.save")}
            </button>
            <button
              class="btn"
              ?disabled=${this._busy || !this._draft}
              @click=${() => {
			this._draft = void 0, this._problems = [];
		}}
            >
              ${M(e, "common.cancel")}
            </button>
          </div>
        </div>
      </div>
    `;
	}
	_renderTarget(e, t) {
		let n = this._target(t.id), r = (e) => (n) => this._setTarget(t.id, { [e]: n.target.value || null });
		return C`<div class="target">
      <label class="check">
        <input
          type="checkbox"
          .checked=${U(!!n)}
          @change=${(e) => this._toggleTarget(t.id, e.target.checked)}
        />
        <span>
          ${t.name === t.id ? t.id : M(e, "zones.entity", {
			name: t.name,
			entity: t.id
		})}
        </span>
      </label>
      ${n ? C`<label class="field inline">
                <span class="lbl">${M(e, "field.quiet_start")}</span>
                <input
                  type="time"
                  .value=${n.quiet_start ?? ""}
                  @input=${r("quiet_start")}
                />
              </label>
              <label class="field inline">
                <span class="lbl">${M(e, "field.quiet_end")}</span>
                <input type="time" .value=${n.quiet_end ?? ""} @input=${r("quiet_end")} />
              </label>` : T}
    </div>`;
	}
	static {
		this.styles = [P, o`
      .alarmo-list {
        margin: 4px 0 12px;
        padding-left: 20px;
        max-width: 80ch;
        font-size: 13.5px;
        line-height: 1.5;
      }
      .alarmo-list li + li {
        margin-top: 6px;
      }
      .card-bd h3 {
        margin: 16px 0 4px;
        font-size: 14px;
        font-weight: 600;
      }
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
customElements.get("foyer-page-settings") || customElements.define("foyer-page-settings", On);
//#endregion
//#region src/panel/pages/health.ts
function kn(e, t) {
	return t ? new Date(t).toLocaleString(e.hass.language) : "—";
}
var An = class extends A {
	constructor(...e) {
		super(...e), this._candidates = [], this._problems = [], this._busy = !1, this._error = "";
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_status: { state: !0 },
			_draft: { state: !0 },
			_candidates: { state: !0 },
			_problems: { state: !0 },
			_busy: { state: !0 },
			_error: { state: !0 }
		};
	}
	connectedCallback() {
		super.connectedCallback(), this._load(), this._timer = window.setInterval(() => void this._load(), 3e4);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._timer && window.clearInterval(this._timer);
	}
	async _load() {
		if (this.ctx) try {
			this._status = await this.ctx.health(), this._error = "";
		} catch (e) {
			this._error = String(e?.message ?? e);
		}
	}
	_editConfig() {
		let e = this.ctx?.config?.health;
		e && (this._draft = structuredClone(e), this._problems = [], this._loadCandidates());
	}
	async _loadCandidates() {
		if (this.ctx) try {
			this._candidates = await this.ctx.radioCandidates();
		} catch {
			this._candidates = [];
		}
	}
	_set(e, t) {
		this._draft &&= {
			...this._draft,
			[e]: t
		};
	}
	_setWatchdog(e, t) {
		this._draft &&= {
			...this._draft,
			watchdog: {
				...this._draft.watchdog,
				[e]: t
			}
		};
	}
	_setRadio(e, t) {
		if (!this._draft) return;
		let n = this._draft.radios.map((n, r) => r === e ? {
			...n,
			...t
		} : n);
		this._set("radios", n);
	}
	_addRadio() {
		if (!this._draft) return;
		let e = new Set(this._draft.radios.map((e) => e.entry_id)), t = this._candidates.find((t) => !e.has(t.entry_id));
		this._set("radios", [...this._draft.radios, {
			name: t?.title ?? "",
			entry_id: t?.entry_id ?? "",
			coordinator_entity_id: null,
			n_zones: null,
			window: null,
			enabled: !0
		}]);
	}
	_removeRadio(e) {
		this._draft && this._set("radios", this._draft.radios.filter((t, n) => n !== e));
	}
	async _save() {
		if (this.ctx && this._draft) {
			this._busy = !0;
			try {
				let e = await this.ctx.saveHealth(this._draft);
				this._problems = e.problems, e.success && (this._draft = void 0, await this._load());
			} finally {
				this._busy = !1;
			}
		}
	}
	render() {
		let e = this.ctx;
		if (!e?.config) return T;
		let t = e.strings, n = this._status;
		return this._error && !n ? C`<div class="card">
        <div class="card-bd"><div class="empty">${this._error}</div></div>
      </div>` : n ? C`
      ${this._error ? C`<div class="problems" role="alert">${this._error}</div>` : T}
      ${this._renderTiles(t, n)} ${this._renderChannels(t, n)}
      ${this._renderRadios(t, n)} ${this._renderFaults(t, n)}
      ${this._renderDiagnostics(t)}
      ${this._draft ? this._renderEditor(t, this._draft) : C`<div class="card">
            <div class="card-hd">
              <h2>${M(t, "health.settings")}</h2>
              <button class="btn" @click=${() => this._editConfig()}>
                ${M(t, "common.edit")}
              </button>
            </div>
            <div class="card-bd">
              <p class="hint">${M(t, "health.settings_hint")}</p>
            </div>
          </div>`}
    ` : C`<div class="card">
        <div class="card-bd"><div class="empty">${M(t, "common.loading")}</div></div>
      </div>`;
	}
	_tile(e, t, n, r) {
		return C`<div class="tile ${r}">
      <div class="name">${e}</div>
      <div class="state">${t}</div>
      <div class="meta">${n}</div>
    </div>`;
	}
	_renderTiles(e, t) {
		let n = t.mains, r = n.mode === "outside_ups", i = r ? n.outside.length > 0 : !!n.entity_id, a = i ? n.lost === !0 ? "crit" : n.lost === null ? "warn" : "ok" : "idle", o = t.watchdog, s = o.enabled ? o.down_since ? "crit" : "ok" : "idle", c = t.channels.filter((e) => e.fault).length, l = t.channels.filter((e) => !e.fault && !e.checked).length;
		return C`<div class="tiles">
      ${this._tile(M(e, "health.mains"), i ? n.lost === !0 ? M(e, "health.mains_lost") : n.lost === null ? M(e, "health.unreadable") : M(e, "health.mains_present") : M(e, "health.not_configured"), r && i ? M(e, "health.mains_outside_meta", {
			count: String(n.outside.length),
			silent: String(n.outside.filter((e) => e.quiet_since).length)
		}) : n.entity_id ?? M(e, "health.mains_pick"), a)}
      ${this._tile(M(e, "health.watchdog"), o.enabled ? o.down_since ? M(e, "health.unreachable") : M(e, "health.reporting") : M(e, "health.off"), o.enabled ? M(e, "health.watchdog_meta", {
			every: String(Math.round(o.interval / 60)),
			payload: M(e, o.payload ? "health.with_payload" : "health.no_payload")
		}) : M(e, "health.watchdog_off_hint"), s)}
      ${this._tile(M(e, "health.channels"), c ? M(e, "health.channels_broken", { n: String(c) }) : M(e, "health.channels_ok", { n: String(t.channels.length) }), M(e, "health.channels_meta", { n: String(l) }), c ? "crit" : t.channels.length ? "ok" : "idle")}
    </div>`;
	}
	_renderChannels(e, t) {
		return C`<div class="card">
      <div class="card-hd">
        <h2>${M(e, "health.channels")}</h2>
        <span class="sub">
          ${M(e, "health.sweep_every", { minutes: String(Math.round((this.ctx?.config?.health.channel_sweep ?? 900) / 60)) })}
        </span>
      </div>
      ${t.channels.length ? C`<div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${M(e, "contacts.title")}</th>
                  <th>${M(e, "field.service")}</th>
                  <th>${M(e, "field.state")}</th>
                  <th>${M(e, "health.last_result")}</th>
                </tr>
              </thead>
              <tbody>
                ${t.channels.map((t) => C`<tr>
                    <td>
                      <strong>${t.contact_name}</strong>
                      <span class="tag">${M(e, `channel_kind.${t.kind}`)}</span>
                    </td>
                    <td class="mono">${t.service}</td>
                    <td>
                      <span class="pill ${t.fault ? "bad" : t.checked ? "ok" : "warn"}">
                        ${t.fault ? M(e, `health.fault_${t.fault}`) : t.checked ? M(e, "health.healthy") : M(e, "health.untested")}
                      </span>
                    </td>
                    <td>${kn(this.ctx, t.since ?? t.last_ok)}</td>
                  </tr>`)}
              </tbody>
            </table>
          </div>` : C`<div class="empty">${M(e, "health.no_channels")}</div>`}
      <div class="card-bd">
        <p class="hint">${M(e, "health.channels_note")}</p>
      </div>
    </div>`;
	}
	_renderRadios(e, t) {
		return C`<div class="card">
      <div class="card-hd">
        <h2>${M(e, "health.radios")}</h2>
      </div>
      ${t.radios.length ? C`<div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${M(e, "field.name")}</th>
                  <th>${M(e, "field.coordinator_entity_id")}</th>
                  <th>${M(e, "health.quiet_zones")}</th>
                  <th>${M(e, "field.state")}</th>
                </tr>
              </thead>
              <tbody>
                ${t.radios.map((t) => C`<tr>
                    <td><strong>${t.name}</strong></td>
                    <td class="mono">
                      ${t.coordinator_entity_id ?? M(e, "health.no_coordinator")}
                    </td>
                    <td class="mono">
                      ${M(e, "health.quiet_of", {
			quiet: String(t.quiet),
			zones: String(t.zones),
			threshold: String(t.threshold)
		})}
                    </td>
                    <td>
                      <span
                        class="pill ${t.confirmed || t.coordinator_down_since ? "bad" : t.suspected_since || !t.coordinator_entity_id || !t.zones ? "warn" : "ok"}"
                      >
                        ${t.confirmed ? M(e, "health.interference") : t.coordinator_down_since ? M(e, "health.coordinator_down") : t.suspected_since ? M(e, "health.confirming") : t.coordinator_entity_id ? t.zones ? M(e, "health.watching") : M(e, "health.no_zones") : M(e, "health.not_gated")}
                      </span>
                    </td>
                  </tr>`)}
              </tbody>
            </table>
          </div>` : C`<div class="empty">${M(e, "health.no_radios")}</div>`}
      <div class="card-bd">
        <p class="hint">${M(e, "health.radios_note")}</p>
      </div>
    </div>`;
	}
	_renderFaults(e, t) {
		let n = new Map((this.ctx?.config?.zones ?? []).map((e) => [e.id ?? "", e])), r = new Map(t.unreachable_zones.map((e) => [e.id, e]));
		return C`<div class="card">
      <div class="card-hd">
        <h2>${M(e, "health.faults")}</h2>
        <span class="sub">${M(e, "health.faults_sub")}</span>
      </div>
      ${t.faults.length ? C`<div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>${M(e, "field.name")}</th>
                  <th>${M(e, "field.entity_id")}</th>
                  <th>${M(e, "health.since")}</th>
                </tr>
              </thead>
              <tbody>
                ${t.faults.map((t) => {
			let i = n.get(t), a = r.get(t);
			return C`<tr>
                    <td><strong>${i?.name ?? t}</strong></td>
                    <td class="mono">${i?.entity_id ?? ""}</td>
                    <td>
                      ${a ? M(e, "health.days", { n: String(a.days) }) : M(e, "health.recent")}
                    </td>
                  </tr>`;
		})}
              </tbody>
            </table>
          </div>` : C`<div class="empty">${M(e, "health.no_faults")}</div>`}
    </div>`;
	}
	_renderDiagnostics(e) {
		return C`<div class="card">
      <div class="card-hd">
        <h2>${M(e, "health.diagnostics")}</h2>
      </div>
      <div class="card-bd">
        <p class="hint">${M(e, "health.diagnostics_hint")}</p>
        <a class="btn" href="/config/integrations/integration/foyer">
          ${M(e, "health.diagnostics_open")}
        </a>
        <p class="hint">${M(e, "health.diagnostics_where")}</p>
      </div>
    </div>`;
	}
	_bounds(e, t) {
		return this.ctx?.meta?.bounds[e] ?? t;
	}
	_renderEntityList() {
		return C`<datalist id="foyer-entities">
      ${Object.values(this.ctx?.hass.states ?? {}).sort((e, t) => e.entity_id.localeCompare(t.entity_id)).map((e) => C`<option value=${e.entity_id}>
            ${String(e.attributes.friendly_name ?? e.entity_id)}
          </option>`)}
    </datalist>`;
	}
	_renderSensor(e, t) {
		return C`<div class="grid-form">
      <label class="field">
        <span class="lbl">${M(e, "field.mains_entity_id")}</span>
        <input
          list="foyer-entities"
          .value=${t.mains_entity_id ?? ""}
          placeholder=${M(e, "health.mains_placeholder")}
          @input=${(e) => this._set("mains_entity_id", e.target.value.trim() || null)}
        />
        <span class="hint">${M(e, "health.mains_hint")}</span>
      </label>
      <label class="field">
        <span class="lbl">${M(e, "field.mains_lost_states")}</span>
        <input
          .value=${t.mains_lost_states.join(", ")}
          @input=${(e) => this._set("mains_lost_states", e.target.value.split(",").map((e) => e.trim()).filter(Boolean))}
        />
        <span class="hint">${M(e, "health.mains_states_hint")}</span>
      </label>
    </div>`;
	}
	_renderOutside(e, t) {
		let [n, r] = this._bounds("mains_outside_delay", [30, 3600]);
		return C`<div class="field">
        <span class="lbl">${M(e, "field.mains_outside_entity_ids")}</span>
        ${gn({
			hass: this.ctx.hass,
			s: e,
			chosen: t.mains_outside_entity_ids,
			candidates: hn(this.ctx.hass),
			listId: "foyer-outside-ups",
			onChange: (e) => this._set("mains_outside_entity_ids", e)
		})}
        <span class="hint">${M(e, "health.mains_outside_hint")}</span>
      </div>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "field.mains_outside_delay")}</span>
          <input
            type="number"
            min=${n}
            max=${r}
            .value=${String(t.mains_outside_delay)}
            @input=${(e) => V(e, (e) => this._set("mains_outside_delay", e))}
          />
          <span class="hint">${M(e, "health.mains_outside_delay_hint")}</span>
        </label>
      </div>`;
	}
	_renderEditor(e, t) {
		let [n, r] = this._bounds("watchdog_interval", [60, 86400]), [i, a] = this._bounds("watchdog_timeout", [5, 120]), [o, s] = this._bounds("watchdog_failures", [1, 20]), [c, l] = this._bounds("rf_zones", [2, 50]), [u, d] = this._bounds("rf_window", [5, 3600]), [f, ee] = this._bounds("rf_confirm", [0, 3600]);
		return C`<div class="card">
      <div class="card-hd">
        <h2>${M(e, "health.settings")}</h2>
      </div>
      <div class="card-bd">
        ${this._renderEntityList()}
        <div class="grid-form">
          <label class="field">
            <span class="lbl">${M(e, "field.mains_mode")}</span>
            <select
              @change=${(e) => this._set("mains_mode", e.target.value)}
            >
              ${["sensor", "outside_ups"].map((n) => C`<option .value=${n} .selected=${U(t.mains_mode === n)}>
                    ${M(e, `health.mains_mode.${n}`)}
                  </option>`)}
            </select>
            <span class="hint">${M(e, `health.mains_mode_hint.${t.mains_mode}`)}</span>
          </label>
        </div>
        ${t.mains_mode === "outside_ups" ? this._renderOutside(e, t) : this._renderSensor(e, t)}

        <fieldset>
          <legend>${M(e, "health.watchdog")}</legend>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.watchdog.enabled)}
              @change=${(e) => this._setWatchdog("enabled", e.target.checked)}
            />
            <span>${M(e, "health.watchdog_enable")}</span>
          </label>
          <div class="grid-form">
            <label class="field wide">
              <span class="lbl">${M(e, "field.url")}</span>
              <input
                autocomplete="off"
                .value=${U(t.watchdog.url ?? "")}
                placeholder=${M(e, t.watchdog.url_set ? "health.url_set_placeholder" : "health.url_placeholder")}
                @input=${(e) => this._setWatchdog("url", e.target.value)}
              />
              ${t.watchdog.url_set ? C`<span class="hint">${M(e, "health.url_set_hint")}</span>` : T}
              <span class="hint">${M(e, "health.url_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.interval")}</span>
              <input
                type="number"
                min=${n}
                max=${r}
                .value=${String(t.watchdog.interval)}
                @input=${(e) => V(e, (e) => this._setWatchdog("interval", e))}
              />
              <span class="hint">${M(e, "health.interval_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.timeout")}</span>
              <input
                type="number"
                min=${i}
                max=${a}
                .value=${String(t.watchdog.timeout)}
                @input=${(e) => V(e, (e) => this._setWatchdog("timeout", e))}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.failures")}</span>
              <input
                type="number"
                min=${o}
                max=${s}
                .value=${String(t.watchdog.failures)}
                @input=${(e) => V(e, (e) => this._setWatchdog("failures", e))}
              />
              <span class="hint">${M(e, "health.failures_hint")}</span>
            </label>
          </div>
          <label class="check">
            <input
              type="checkbox"
              .checked=${U(t.watchdog.payload)}
              @change=${(e) => this._setWatchdog("payload", e.target.checked)}
            />
            <span>
              ${M(e, "health.payload")}
              <span class="hint">${M(e, "health.payload_hint")}</span>
            </span>
          </label>
          ${t.watchdog.payload ? C`<div class="warning" role="alert">${M(e, "health.payload_warning")}</div>` : T}
          <p class="hint">${M(e, "health.watchdog_note")}</p>
        </fieldset>

        <fieldset>
          <legend>${M(e, "health.radios")}</legend>
          <p class="hint">${M(e, "health.radios_hint")}</p>
          ${I(this.ctx) ? C`<div class="notice" role="note">${M(e, "health.radios_armed")}</div>` : T}
          ${t.radios.map((t, n) => this._renderRadioEditor(e, t, n))}
          <button class="btn" @click=${() => this._addRadio()}>${M(e, "health.add_radio")}</button>
          <div class="grid-form">
            <label class="field">
              <span class="lbl">${M(e, "field.rf_zones")}</span>
              <input
                type="number"
                min=${c}
                max=${l}
                .value=${String(t.rf_zones)}
                @input=${(e) => V(e, (e) => this._set("rf_zones", e))}
              />
              <span class="hint">${M(e, "health.rf_zones_hint")}</span>
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.rf_window")}</span>
              <input
                type="number"
                min=${u}
                max=${d}
                .value=${String(t.rf_window)}
                @input=${(e) => V(e, (e) => this._set("rf_window", e))}
              />
            </label>
            <label class="field">
              <span class="lbl">${M(e, "field.rf_confirm")}</span>
              <input
                type="number"
                min=${f}
                max=${ee}
                .value=${String(t.rf_confirm)}
                @input=${(e) => V(e, (e) => this._set("rf_confirm", e))}
              />
              <span class="hint">${M(e, "health.rf_confirm_hint")}</span>
            </label>
          </div>
        </fieldset>

        ${this._problems.length ? C`<div class="problems" role="alert">
              <ul>
                ${this._problems.map((t) => C`<li>${z(e, t)}</li>`)}
              </ul>
            </div>` : T}
        <div class="actions">
          <button class="btn primary" ?disabled=${this._busy} @click=${this._save}>
            ${M(e, "common.save")}
          </button>
          <button class="btn" ?disabled=${this._busy} @click=${() => this._draft = void 0}>
            ${M(e, "common.cancel")}
          </button>
        </div>
      </div>
    </div>`;
	}
	_renderRadioEditor(e, t, n) {
		return C`<div class="radio-row">
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "field.name")}</span>
          <input
            .value=${t.name}
            @input=${(e) => this._setRadio(n, { name: e.target.value })}
          />
        </label>
        <label class="field">
          <span class="lbl">${M(e, "field.entry_id")}</span>
          <select
            @change=${(e) => {
			let r = e.target.value, i = this._candidates.find((e) => e.entry_id === r);
			this._setRadio(n, {
				entry_id: r,
				name: t.name || (i?.title ?? "")
			});
		}}
          >
            <option .value=${""} .selected=${U(!t.entry_id)}>—</option>
            ${this._candidates.map((n) => C`<option
                .value=${n.entry_id}
                .selected=${U(n.entry_id === t.entry_id)}
              >
                ${M(e, "health.candidate", {
			title: n.title,
			zones: String(n.zones)
		})}
              </option>`)}
          </select>
          <span class="hint">${M(e, "health.entry_hint")}</span>
        </label>
        <label class="field wide">
          <span class="lbl">${M(e, "field.coordinator_entity_id")}</span>
          <input
            .value=${t.coordinator_entity_id ?? ""}
            placeholder=${M(e, "health.coordinator_placeholder")}
            @input=${(e) => this._setRadio(n, { coordinator_entity_id: e.target.value || null })}
          />
          <span class="hint">${M(e, "health.coordinator_hint")}</span>
        </label>
      </div>
      <div class="actions">
        <label class="check">
          <input
            type="checkbox"
            .checked=${U(t.enabled)}
            @change=${(e) => this._setRadio(n, { enabled: e.target.checked })}
          />
          <span>${M(e, "field.enabled")}</span>
        </label>
        <button class="btn danger" @click=${() => this._removeRadio(n)}>
          ${M(e, "common.delete")}
        </button>
      </div>
    </div>`;
	}
	static {
		this.styles = [
			N,
			P,
			_n,
			o`
      .tiles {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        margin-bottom: 16px;
      }
      .tile {
        background: var(--card-background-color, #fff);
        border: 1px solid var(--divider-color, #e0e0e0);
        border-left: 4px solid var(--disabled-text-color, #9e9e9e);
        border-radius: 8px;
        padding: 12px 14px;
      }
      .tile.ok {
        border-left-color: var(--success-color, #43a047);
      }
      .tile.warn {
        border-left-color: var(--warning-color, #ffa726);
      }
      .tile.crit {
        border-left-color: var(--error-color, #e53935);
      }
      .tile .name {
        color: var(--secondary-text-color);
        font-size: 12.5px;
      }
      .tile .state {
        font-size: 18px;
        font-weight: 500;
        margin: 2px 0 4px;
      }
      .tile .meta {
        color: var(--secondary-text-color);
        font-size: 12.5px;
        overflow-wrap: anywhere;
      }
      .radio-row {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        margin-bottom: 12px;
        padding: 12px;
      }
      .warning {
        background: color-mix(in srgb, var(--warning-color, #ffa726) 14%, transparent);
        border-left: 3px solid var(--warning-color, #ffa726);
        border-radius: 4px;
        font-size: 13px;
        margin: 8px 0;
        padding: 10px 12px;
      }
      a.btn {
        display: inline-block;
        text-decoration: none;
      }
    `
		];
	}
};
customElements.get("foyer-page-health") || customElements.define("foyer-page-health", An);
//#endregion
//#region src/panel/pages/api.ts
var jn = class extends A {
	constructor(...e) {
		super(...e), this._state = "loading", this._attempt = 0;
	}
	static {
		this.properties = {
			ctx: { attribute: !1 },
			_state: { state: !0 }
		};
	}
	firstUpdated() {
		this._load();
	}
	async _load() {
		let e = this.ctx;
		if (!e) return;
		let t = ++this._attempt;
		this._state = "loading";
		try {
			let [n, r] = await Promise.all([e.apiDocument(), import("./api-swagger-BQGx-a3h.js")]);
			if (t !== this._attempt) return;
			let i = n?.document;
			if (typeof i != "string" || !i.trim()) throw Error("empty");
			let a = this.renderRoot.querySelector(".swagger-host");
			if (!a) return;
			let o = window.document.createElement("style");
			o.textContent = r.swaggerCss;
			let s = window.document.createElement("div");
			a.replaceChildren(o, s), r.renderSwagger(s, i), this._state = "ready";
		} catch {
			t === this._attempt && (this._state = "failed");
		}
	}
	render() {
		let e = this.ctx;
		if (!e) return T;
		let t = e.strings;
		return C`
      <div class="card">
        <div class="card-hd">
          <h2>${M(t, "api.title")}</h2>
          <span class="pill idle">${M(t, "api.contract", { version: "v1" })}</span>
        </div>
        <div class="card-bd">
          <p class="note">${M(t, "api.intro")}</p>
          <p class="note">${M(t, "api.try_it")}</p>
          <p class="notice">${M(t, "api.real_requests")}</p>
          ${this._state === "loading" ? C`<p class="muted">${M(t, "api.loading")}</p>` : T}
          ${this._state === "failed" ? C`<div class="problems" role="alert">
                ${M(t, "api.failed")}
                <div class="actions">
                  <button class="btn" @click=${() => void this._load()}>
                    ${M(t, "api.retry")}
                  </button>
                </div>
              </div>` : T}
        </div>
        <div class="swagger-host" ?hidden=${this._state !== "ready"}></div>
      </div>
    `;
	}
	static {
		this.styles = [P, o`
      /* Swagger UI draws for a light page and has no dark theme: it keeps
         its own light background rather than half-inheriting a dark one,
         which leaves grey text on grey. */
      .swagger-host {
        background: #fff;
        color: #3b4151;
        border-radius: 0 0 12px 12px;
        padding: 0 8px 16px;
        overflow-x: auto;
      }
      .swagger-host[hidden] {
        display: none;
      }
    `];
	}
};
customElements.define("foyer-page-api", jn);
//#endregion
//#region src/panel/wizard.ts
var Z = [
	"area",
	"zones",
	"scenario",
	"user",
	"test"
], Mn = 3, Nn = class extends A {
	constructor(...e) {
		super(...e), this._step = "area", this._userName = "", this._userCode = "", this._userRepeat = "", this._zoneType = "", this._busy = !1, this._problems = [], this._confirmed = !1, this._pickedEntity = "", this._notifyTarget = "", this._sent = !1;
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
			_userCode: { state: !0 },
			_userRepeat: { state: !0 },
			_zoneType: { state: !0 }
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
				let e = await this.ctx.saveSettings({ wizard_done: !0 });
				if (!e.success) {
					this._problems = e.problems;
					return;
				}
				this.dispatchEvent(new CustomEvent("wizard-done", {
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
		if (!e?.config) return T;
		let t = e.strings;
		return C`
      <section class="wizard">
        <header>
          <h2>${M(t, "wizard.title")}</h2>
          <button class="btn" ?disabled=${this._busy} @click=${this._finish}>
            ${M(t, "wizard.dismiss")}
          </button>
        </header>
        <p class="intro">${M(t, "wizard.intro")}</p>
        <ol class="steps">
          ${Z.map((e, n) => {
			let r = Z.indexOf(this._step);
			return C`<li class=${n < r ? "done" : n === r ? "active" : ""}>
              <span class="n">${n + 1}</span>${M(t, `wizard.step.${e}`)}
            </li>`;
		})}
        </ol>
        <div class="body">${this._renderStep(t)}</div>
        ${this._problems.length ? C`<div class="problems" role="alert">
              <ul>
                ${this._problems.map((e) => C`<li>${z(t, e)}</li>`)}
              </ul>
            </div>` : T}
        <div class="actions">
          <button
            class="btn"
            ?disabled=${this._busy || this._step === Z[0]}
            @click=${this._back}
          >
            ${M(t, "wizard.back")}
          </button>
          <span class="spacer"></span>
          ${this._step === "test" ? C`<button class="btn primary" ?disabled=${this._busy} @click=${this._finish}>
                ${M(t, "wizard.done")}
              </button>` : this._step === "user" && !this.ctx?.config?.users.some((e) => e.enabled && e.has_code) ? this._renderUserAction(t) : C`<button class="btn primary" ?disabled=${this._busy} @click=${this._next}>
                  ${M(t, "wizard.next")}
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
		if (!t) return C`<p class="hint">${M(e, "wizard.no_area")}</p>`;
		let n = (e) => this._saveArea({
			...t,
			...e
		});
		return C`
      <p>${M(e, "wizard.area_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "field.name")}</span>
          <input
            .value=${t.name}
            @change=${(e) => n({ name: e.target.value.trim() })}
          />
        </label>
        <label class="field">
          <span class="lbl">${M(e, "field.default_exit_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_exit_delay)}
            @change=${(e) => V(e, (e) => n({ default_exit_delay: e }))}
          />
          <span class="hint">${M(e, "wizard.exit_hint")}</span>
        </label>
        <label class="field">
          <span class="lbl">${M(e, "field.default_entry_delay")}</span>
          <input
            type="number"
            min="0"
            max="300"
            .value=${String(t.default_entry_delay)}
            @change=${(e) => V(e, (e) => n({ default_entry_delay: e }))}
          />
          <span class="hint">${M(e, "wizard.entry_hint")}</span>
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
		return C`
      <p>${M(e, "wizard.zones_text", {
			have: n.length,
			want: Mn
		})}</p>
      <ul class="zones">
        ${n.map((t) => C`<li>
            <strong>${t.name}</strong>
            <span class="mono">${t.entity_id}</span>
            <span class="tag">${M(e, `zone_type.${t.type}`)}</span>
          </li>`)}
      </ul>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "wizard.add_zone")}</span>
          <select
            @change=${(e) => this._pick(e.target.value)}
          >
            <option value="" .selected=${U(!this._pickedEntity)}>${M(e, "wizard.pick_entity")}</option>
            ${a.map((e) => C`<option .value=${e.id} .selected=${U(e.id === this._pickedEntity)}>
                  ${e.name}
                </option>`)}
          </select>
        </label>
      </div>
      ${r ? this._renderProposal(e, r) : T}
    `;
	}
	_renderProposal(e, t) {
		let n = this.ctx, r = n.hass.states[t.entity_id], i = String(r?.attributes.friendly_name ?? t.name);
		if (t.trigger_kind === "numeric" || !t.proposed.length) return C`<div class="proposal">
        <p>${M(e, `wizard.${t.trigger_kind === "numeric" ? "numeric_elsewhere" : "no_proposal_elsewhere"}`)}</p>
        <button class="btn" @click=${() => n.navigate("zones")}>
          ${M(e, "wizard.go_zones")}
        </button>
      </div>`;
		let a = r?.state ?? t.state ?? "unavailable", o = (e) => J(n.hass, t.entity_id, e), s = !t.zone_type || ["instant", "delayed"].includes(t.zone_type), c = this._zoneType || t.zone_type || "instant";
		return C`
            <div class="proposal">
              <p>
                ${M(e, "wizard.proposed", {
			name: i,
			state: o(a),
			states: t.proposed.map(o).join(", ")
		})}
              </p>
              ${s ? C`<div class="grid-form">
                    <label class="field">
                      <span class="lbl">${M(e, "field.type")}</span>
                      <select
                        @change=${(e) => this._zoneType = e.target.value}
                      >
                        ${["instant", "delayed"].map((t) => C`<option
                            .value=${t}
                            .selected=${U(t === c)}
                          >
                            ${M(e, `zone_type.${t}`)}
                          </option>`)}
                      </select>
                      <span class="hint">${M(e, "wizard.type_hint")}</span>
                    </label>
                  </div>` : C`<p class="hint">
                    ${M(e, "wizard.type_fixed", { type: M(e, `zone_type.${c}`) })}
                  </p>`}
              <label class="check">
                <input
                  type="checkbox"
                  .checked=${U(this._confirmed)}
                  @change=${(e) => this._confirmed = e.target.checked}
                />
                <span>${M(e, "wizard.confirm_trigger")}</span>
              </label>
              <p class="hint">${M(e, "wizard.confirm_hint")}</p>
              <button
                class="btn"
                ?disabled=${this._busy || !this._confirmed}
                @click=${this._addZone}
              >
                ${M(e, "wizard.add")}
              </button>
            </div>
    `;
	}
	async _pick(e) {
		if (this._pickedEntity = e, this._confirmed = !1, this._proposal = void 0, this._zoneType = "", e && this.ctx) try {
			let t = await this.ctx.hass.callWS({
				type: "foyer/zone/propose",
				entity_id: e
			});
			this._pickedEntity === e && (this._proposal = t);
		} catch {
			this._pickedEntity === e && (this._problems = [{
				code: "propose_failed",
				kind: "zone",
				ref: null,
				field: "entity_id"
			}]);
		}
	}
	async _addZone() {
		let e = this.ctx, t = this._proposal, n = this._area;
		if (!e || !t || !n || t.trigger_kind === "numeric" || !t.proposed.length) return;
		let r = t.trigger_kind === "event" ? {
			kind: "event",
			event_type: t.entity_id.startsWith("event.") ? t.proposed[0] ?? null : null
		} : {
			kind: "state",
			states: [...t.proposed]
		}, i = {
			name: t.name,
			entity_id: t.entity_id,
			area_id: n.id,
			trigger: r,
			type: this._zoneType || t.zone_type || "instant"
		};
		this._busy = !0;
		try {
			let t = await e.save("zone", i, !0);
			this._problems = t.problems, t.success && (this._proposal = void 0, this._pickedEntity = "", this._confirmed = !1, this._zoneType = "");
		} finally {
			this._busy = !1;
		}
	}
	_renderScenario(e) {
		let t = this.ctx, n = t.config.scenarios[0];
		if (!n) return C`<p class="hint">${M(e, "wizard.no_scenario")}</p>`;
		let r = t.config.areas;
		return C`
      <p>${M(e, "wizard.scenario_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "field.name")}</span>
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
        ${M(e, "wizard.scenario_areas", { areas: r.filter((e) => n.areas.includes(e.id)).map((e) => e.name).join(", ") })}
      </p>
    `;
	}
	_renderUserAction(e) {
		return this._userName.trim() !== "" || this._userCode !== "" ? C`<button class="btn primary" ?disabled=${this._busy} @click=${this._createUser}>
          ${M(e, "wizard.user_create_next")}
        </button>` : C`<button class="btn primary" ?disabled=${this._busy} @click=${this._next}>
          ${M(e, "wizard.skip")}
        </button>`;
	}
	async _createUser() {
		let e = this.ctx;
		if (e) {
			if (this._userCode !== this._userRepeat) {
				this._problems = [{
					code: "code_mismatch",
					kind: "user",
					ref: null,
					field: null
				}];
				return;
			}
			if (!this._userCode) {
				this._problems = [{
					code: "code_required_here",
					kind: "user",
					ref: null,
					field: null
				}];
				return;
			}
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
				}, this._userCode ? { new_code: this._userCode } : {});
				this._problems = t.problems, t.success && (this._userCode = "", this._userRepeat = "", this._next());
			} finally {
				this._busy = !1;
			}
		}
	}
	_renderUser(e) {
		let t = this.ctx?.config?.users ?? [], n = this.ctx?.status.security.code_length ?? 6, r = t.find((e) => e.enabled && e.has_code);
		return r ? C`
        <p>${M(e, "wizard.user_text")}</p>
        <div class="notice">${M(e, "wizard.user_done", { name: r.name })}</div>
      ` : C`
      <p>${M(e, "wizard.user_text")}</p>
      ${t.length ? C`<div class="notice">
            ${M(e, "wizard.user_no_code", { name: t[0].name })}
          </div>` : T}
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "field.name")}</span>
          <input
            .value=${this._userName}
            @input=${(e) => this._userName = e.target.value}
          />
        </label>
        <label class="field">
          <span class="lbl">${M(e, "users.code")}</span>
          <input
            type="password"
            inputmode="numeric"
            autocomplete="off"
            maxlength=${n}
            .value=${this._userCode}
            @input=${(e) => this._userCode = e.target.value}
          />
          <span class="hint">${M(e, "users.code_hint_new", { n })}</span>
        </label>
        <label class="field">
          <span class="lbl">${M(e, "users.code_repeat")}</span>
          <input
            type="password"
            inputmode="numeric"
            autocomplete="off"
            maxlength=${n}
            .value=${this._userRepeat}
            @input=${(e) => this._userRepeat = e.target.value}
          />
        </label>
      </div>
      <p class="hint">${M(e, "wizard.user_hint")}</p>
    `;
	}
	_renderTest(e) {
		let t = this.ctx, n = q(t.hass);
		return C`
      <p>${M(e, "wizard.test_text")}</p>
      <div class="grid-form">
        <label class="field">
          <span class="lbl">${M(e, "wizard.test_target")}</span>
          <select
            @change=${(e) => {
			this._notifyTarget = e.target.value, this._sent = !1;
		}}
          >
            <option value="" .selected=${U(!this._notifyTarget)}>${M(e, "wizard.pick_target")}</option>
            ${n.map((e) => C`<option .value=${e.id} .selected=${U(e.id === this._notifyTarget)}>
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
        ${M(e, "wizard.send_test")}
      </button>
      ${this._sent ? C`<div class="notice">${M(e, "wizard.test_sent")}</div>` : T}
      <p class="hint">${M(e, "wizard.test_hint")}</p>
      <div class="actions">
        <button class="btn" @click=${() => t.navigate("contacts")}>
          ${M(e, "wizard.go_contacts")}
        </button>
      </div>
      ${this._renderLeft(e)}
    `;
	}
	_renderLeft(e) {
		let t = this.ctx, n = t.config, r = [];
		return n.zones.length < Mn && r.push({
			key: "wizard.left.zones",
			page: "zones",
			params: {
				have: n.zones.length,
				want: Mn
			}
		}), n.users.some((e) => e.has_code) || r.push({
			key: "wizard.left.users",
			page: "users"
		}), (n.contacts ?? []).length || r.push({
			key: "wizard.left.contacts",
			page: "contacts"
		}), C`<div class="left">
      <h3>${M(e, "wizard.left.title")}</h3>
      ${r.length ? C`<ul>
            ${r.map((n) => C`<li>
                <span>${M(e, n.key, n.params)}</span>
                <button class="btn sm" @click=${() => t.navigate(n.page)}>
                  ${M(e, `nav.${n.page}`)}
                </button>
              </li>`)}
          </ul>` : C`<p class="hint">${M(e, "wizard.left.none")}</p>`}
    </div>`;
	}
	async _sendTest() {
		let e = this.ctx;
		if (e && this._notifyTarget) {
			this._busy = !0, this._sent = !1;
			try {
				let t = await e.testAction({
					service: this._notifyTarget,
					message: M(e.strings, "wizard.test_message")
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
		this.styles = [P, o`
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
      .left {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid var(--divider-color);
      }
      .left h3 {
        margin: 0 0 8px;
        font-size: 14px;
        font-weight: 500;
      }
      .left ul {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
        font-size: 13.5px;
      }
      .left li {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }
    `];
	}
};
customElements.get("foyer-wizard") || customElements.define("foyer-wizard", Nn);
//#endregion
//#region src/panel/foyer-panel.ts
var Pn = [
	"overview",
	"log",
	"test",
	"health"
], Fn = [
	"areas",
	"zones",
	"scenarios",
	"users",
	"contacts",
	"profiles",
	"groups",
	"devices",
	"rules",
	"settings"
], In = {
	overview: [
		"area",
		"master",
		"scenario",
		"not_ready",
		"memory",
		"technical",
		"incident",
		"disclaimer"
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
		"cameras",
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
		"images",
		"severity",
		"silent",
		"armed"
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
		"endpoint",
		"scopes",
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
		"test",
		"armed"
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
		"export",
		"personal"
	],
	settings: [
		"targets",
		"mode",
		"quiet",
		"during_exit",
		"response",
		"armed",
		"retention",
		"privacy",
		"backup",
		"alarmo",
		"language"
	],
	health: [
		"mains",
		"channels",
		"watchdog",
		"payload",
		"radio",
		"coordinator",
		"diagnostics"
	],
	api: [
		"contract",
		"token",
		"try",
		"internal"
	]
}, Ln = "https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs", Rn = {
	overview: "getting-started.md#the-overview",
	areas: "zones.md#areas",
	zones: "zones.md#zones",
	scenarios: "zones.md#scenarios",
	groups: "zones.md#verification-groups",
	profiles: "response-profiles.md",
	users: "security-model.md",
	devices: "keypads.md",
	contacts: "notification-channels.md",
	rules: "automation-rules.md",
	test: "simulator.md",
	log: "privacy.md",
	settings: "settings.md",
	health: "system-health.md",
	api: "keypads.md#api-devices-displays-relays-and-modules-of-your-own"
}, zn = { it: /* @__PURE__ */ new Set([
	"getting-started.md",
	"zones.md",
	"response-profiles.md",
	"security-model.md",
	"settings.md",
	"keypads.md",
	"notification-channels.md",
	"automation-rules.md",
	"simulator.md",
	"privacy.md",
	"system-health.md"
]) };
function Bn(e, t) {
	let n = Rn[e];
	if (!n) return;
	let [r, i] = n.split("#"), a = (t ?? "en").split("-")[0];
	return `${Ln}/${zn[a]?.has(r) ? r.replace(/\.md$/, `.${a}.md`) : r}${i ? `#${i}` : ""}`;
}
var Vn = 12e4;
function Hn(e) {
	let t = {
		...e,
		reason: "cancelled"
	};
	return Array.isArray(e.problems) && (t.problems = [{
		code: "cancelled",
		kind: "code",
		ref: null,
		field: null
	}]), t;
}
function Q(e) {
	return e === void 0 || e === "" ? {} : { code: e };
}
function $(e) {
	return Object.fromEntries(Object.entries(e).filter(([, e]) => e != null && e !== "" && !(Array.isArray(e) && e.length === 0)));
}
var Un = class extends A {
	constructor(...e) {
		super(...e), this.narrow = !1, this._page = "overview", this._prefs = {}, this._tick = 0, this._focusCode = !1, this._offset = 0, this._retryAt = 0;
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
			(this._status?.areas.some((e) => e.timer) || this._status?.walk_test || this._status?.auto?.pending?.length || this._status?.security?.locked_until) && (this._tick += 1);
		}, 1e3);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._forgetCode(), this._asking?.resolve(void 0), this._asking = void 0, this._unsubscribe?.then((e) => e()).catch(() => void 0), this._unsubscribe = void 0, window.clearInterval(this._timer), window.clearTimeout(this._retryTimer);
	}
	willUpdate(e) {
		e.has("hass") && this.hass && (this.hass.language !== this._language && (this._language = this.hass.language, Ge(this.hass).then((e) => this._strings = e).catch((e) => this._error = String(e?.message ?? e))), !this._unsubscribe && this.isConnected && Date.now() >= this._retryAt && this._start());
	}
	get _isAdmin() {
		return !!this.hass?.user?.is_admin;
	}
	get _canConfigure() {
		let e = this._status?.security.me;
		return this._isAdmin || !!e?.permissions.includes("edit_config");
	}
	_askForCode(e, t, n) {
		return new Promise((r) => {
			this._asking?.resolve(void 0), this._asking = {
				resolve: r,
				retry: e,
				purpose: t,
				requiredBy: n
			}, this._focusCode = !0, this.requestUpdate();
		});
	}
	_answerCode(e) {
		let t = this._asking;
		this._asking = void 0, this.requestUpdate(), t?.resolve(e);
	}
	_rememberCode(e) {
		this._code = e, window.clearTimeout(this._codeTimer), this._codeTimer = window.setTimeout(() => this._forgetCode(), Vn);
	}
	_forgetCode() {
		this._code = void 0, window.clearTimeout(this._codeTimer), this._codeTimer = void 0;
	}
	async _coded(e, t) {
		let n = this._code, r = !1, i = null, a = await e(n);
		for (let o = 0; o < 3 && !(a.success || a.reason !== "code_required" && a.reason !== "bad_code"); o++) {
			a.reason === "bad_code" && this._forgetCode(), i = a.code_required_by ?? i;
			let o = await this._askForCode(r && a.reason === "bad_code", t, i);
			if (o === void 0) return Hn(a);
			n = o, r = !0, a = await e(n);
		}
		return a.success && n && this.isConnected && this._rememberCode(n), (a.reason === "bad_code" || a.reason === "locked_out") && this._forgetCode(), a;
	}
	_armPurpose(e) {
		let t = this._status, n = t?.scenarios.find((t) => t.id === e.scenario_id)?.name ?? t?.areas.find((t) => t.id === e.area_id)?.name;
		return n ? {
			key: "code.purpose.arm",
			params: { target: n }
		} : { key: "code.purpose.arm_plain" };
	}
	_disarmPurpose(e) {
		return e ? {
			key: "code.purpose.disarm",
			params: { target: e.map((e) => this._status?.areas.find((t) => t.id === e)?.name ?? e).join(", ") }
		} : { key: "code.purpose.disarm_all" };
	}
	_zoneName(e) {
		return this._status?.zones.find((t) => t.id === e)?.name ?? e;
	}
	_start() {
		this.hass && !this._unsubscribe && (this._unsubscribe = this.hass.connection.subscribeMessage((e) => {
			this._offset = Date.parse(e.now) - Date.now(), this._status = e, this._error = void 0, !this._config && this._canConfigure && this._loadConfig().catch(() => void 0);
		}, { type: "foyer/subscribe" }), this._unsubscribe.catch((e) => {
			this._unsubscribe = void 0, this._retryAt = Date.now() + 5e3, window.clearTimeout(this._retryTimer), this._retryTimer = window.setTimeout(() => {
				this.isConnected && !this._unsubscribe && this._start();
			}, 5e3), this._error = e?.code === "not_loaded" ? M(this._strings, "common.not_loaded") : M(this._strings, "common.connection_error", { error: String(e?.message ?? e) });
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
			}), this._armPurpose(t)).finally(() => this._forgetCode()),
			disarm: (t) => this._coded((n) => e.callWS({
				type: "foyer/disarm",
				...t ? { area_ids: t } : {},
				...Q(n)
			}), this._disarmPurpose(t)).finally(() => this._forgetCode()),
			acknowledge: (t) => this._coded((n) => e.callWS({
				type: "foyer/acknowledge",
				target: t,
				...Q(n)
			})),
			saveChime: (e) => this._edit("chime", {
				type: "foyer/config/chime",
				chime: e
			}),
			health: () => e.callWS({ type: "foyer/health" }),
			saveHealth: (e) => {
				let t = { ...e.watchdog };
				return delete t.url_set, e.watchdog.url?.trim() || delete t.url, this._edit("health", {
					type: "foyer/config/health",
					health: {
						...e,
						watchdog: t
					}
				});
			},
			radioCandidates: async () => (await e.callWS({ type: "foyer/health/radios" })).radios,
			setAckWebhook: (e) => this._edit("settings", {
				type: "foyer/ack_webhook",
				enabled: e
			}),
			deviceToken: (e, t) => this._edit("device", {
				type: "foyer/device/token",
				device_id: e,
				revoke: t
			}),
			apiDocument: () => e.callWS({ type: "foyer/api/document" }),
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
			saveSettings: async (e) => {
				await this._loadConfig().catch(() => void 0);
				let t = {
					...this._config?.settings,
					...e
				};
				return delete t.ack_webhook_enabled, this._edit("settings", {
					type: "foyer/config/settings",
					settings: t
				});
			},
			queryLog: (t) => e.callWS({
				type: "foyer/log/query",
				...$(t)
			}),
			exportLog: (t, n) => e.callWS({
				type: "foyer/log/export",
				format: n,
				...$(t)
			}),
			clearLog: () => this._coded((t) => e.callWS({
				type: "foyer/log/clear",
				...Q(t)
			})),
			previewPerson: (t) => e.callWS({
				type: "foyer/privacy/preview",
				user_id: t
			}),
			exportPerson: (t, n) => e.callWS({
				type: "foyer/privacy/export",
				user_id: t,
				format: n
			}),
			erasePerson: (t, n) => this._coded((r) => e.callWS({
				type: "foyer/privacy/erase",
				user_id: t,
				pseudonymise: n,
				...Q(r)
			})),
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
			exportConfig: () => this._coded((t) => e.callWS({
				type: "foyer/config/export",
				...Q(t)
			}).then((e) => ({
				...e,
				success: e.success !== !1
			}))),
			importConfig: (e) => this._edit("config", {
				type: "foyer/config/import",
				document: e
			}),
			alarmoPreview: (t) => e.callWS({
				type: "foyer/alarmo/preview",
				labels: t
			}),
			alarmoApply: (e, t) => this._edit("config", {
				type: "foyer/alarmo/apply",
				fingerprint: e,
				labels: t
			}),
			bypass: (t, n, r) => this._coded((i) => e.callWS({
				type: "foyer/bypass",
				zone_id: t,
				bypass: n,
				...r ? { seconds: r } : {},
				...Q(i)
			}), {
				key: n ? "code.purpose.bypass" : "code.purpose.unbypass",
				params: { zone: this._zoneName(t) }
			}),
			saveUser: async (t, n) => {
				let r = await this._edit("user", {
					type: "foyer/user/save",
					user: t,
					...n
				});
				return r.success && n.new_code && t.ha_user_id === e.user?.id && this._forgetCode(), r;
			},
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
			}), { key: "code.purpose.config" });
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
		return this._prefs.help?.[e] ?? e !== "overview";
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
		return C`
      <div class="shell" ?inert=${!!this._asking}>
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="symbol" aria-hidden="true"
          >${Be(Ue(!!this.hass?.themes?.darkMode))}</span
        >
        <div class="title">${M(e, "common.brand")}</div>
        ${this._status ? C`<span class="live">${M(e, "common.live")}</span>` : T}
        <button
          class="help-toggle"
          aria-pressed=${t ? "false" : "true"}
          title=${M(e, "help.global_toggle")}
          aria-label=${M(e, "help.global_toggle")}
          @click=${() => this._savePrefs({ help_hidden: !t })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
        </button>
      </div>
      ${e ? this._renderWalkTestBanner(e) : T}
      ${e ? this._renderTabs(e) : T}
      <main>${e ? this._renderBody(e) : T}</main>
      </div>
      ${this._asking && e ? this._renderCodeDialog(e) : T}
    `;
	}
	_renderWalkTestBanner(e) {
		let t = this._status?.walk_test;
		if (!t) return T;
		this._tick;
		let n = qe(t.deadline, this._offset);
		return C`
      <div class="walk-banner" role="alert">
        <ha-icon icon="mdi:shield-off-outline"></ha-icon>
        <div>
          <strong>${M(e, "walk.banner_title")}</strong>
          ${M(e, "walk.banner", {
			time: Ke(n),
			who: t.user_name ?? M(e, "walk.somebody")
		})}
          <div class="live-note">${M(e, "walk.always_on_live")}</div>
        </div>
        <button class="btn danger" @click=${() => void this._endWalkTest()}>
          ${M(e, "walk.end")}
        </button>
      </div>
    `;
	}
	async _endWalkTest() {
		await this._context()?.walkTest(!1);
	}
	_renderCodeDialog(e) {
		let t = this._asking, n = this._status?.security.code_length ?? 6, r = (e) => {
			e.preventDefault();
			let t = e.target.elements.namedItem("code");
			this._answerCode(t.value);
		}, i = t.requiredBy, a = this._lockoutText(e);
		return C`
      <div class="scrim"></div>
      <form
        class="code-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="code-title"
        aria-describedby="code-prompt"
        @submit=${r}
        @keydown=${(e) => {
			e.key === "Escape" && (e.preventDefault(), this._answerCode(void 0));
		}}
      >
        <h2 id="code-title">
          ${t.purpose ? M(e, t.purpose.key, t.purpose.params) : M(e, "code.title")}
        </h2>
        ${i?.name ? C`<p class="by">${M(e, "code.required_by", { name: i.name })}</p>` : T}
        <p id="code-prompt" class=${t.retry ? "wrong" : ""}>
          ${t.retry ? M(e, "code.wrong", { n }) : M(e, "code.prompt", { n })}
        </p>
        ${a ? C`<p class="wrong">${a}</p>` : T}
        <input
          name="code"
          type="password"
          inputmode="numeric"
          autocomplete="off"
          aria-labelledby="code-title"
          maxlength=${n}
        />
        <div class="row">
          <button type="button" class="btn" @click=${() => this._answerCode(void 0)}>
            ${M(e, "common.cancel")}
          </button>
          <button type="submit" class="btn primary">${M(e, "common.ok")}</button>
        </div>
      </form>
    `;
	}
	updated() {
		this._focusCode && this._asking && (this._focusCode = !1, this.renderRoot.querySelector(".code-dialog input")?.focus());
	}
	_lockoutText(e) {
		let t = this._status?.security.locked_until;
		return !t || Date.parse(t) <= Date.now() + this._offset ? null : Ze(e, this.hass?.language, t);
	}
	_renderTabs(e) {
		let t = (t) => C`
      <button
        role="tab"
        aria-selected=${t === this._page ? "true" : "false"}
        @click=${() => this._page = t}
      >
        ${M(e, `nav.${t}`)}
      </button>
    `;
		return this._canConfigure ? C`
      <nav class="tabs" role="tablist">
        ${Pn.map(t)}
        <span class="tab-group" role="presentation">${M(e, "nav.group_setup")}</span>
        ${Fn.map(t)} ${this._isAdmin ? t("api") : T}
      </nav>
    ` : C`<nav class="tabs" role="tablist">${Pn.map(t)}</nav>`;
	}
	_renderBody(e) {
		if (this._error) return C`<p class="error">${this._error}</p>`;
		let t = this._context();
		if (!t) return C`<p class="muted">${M(e, "common.loading")}</p>`;
		let n = this._page, r = this._canConfigure && this._config && !this._config.settings.wizard_done ? C`<foyer-wizard
            .ctx=${t}
            @wizard-done=${() => void this._loadConfig()}
          ></foyer-wizard>` : T, i = this._lockoutText(e);
		return C`
      ${i ? C`<div class="lockout" role="alert">${i}</div>` : T}
      ${r} ${this._prefs.help_hidden ? T : this._renderHelp(e, n)}
      ${this._renderPage(n, t)}
    `;
	}
	_renderPage(e, t) {
		switch (this._tick, e) {
			case "areas": return C`<foyer-page-areas .ctx=${t}></foyer-page-areas>`;
			case "zones": return C`<foyer-page-zones .ctx=${t}></foyer-page-zones>`;
			case "scenarios": return C`<foyer-page-scenarios .ctx=${t}></foyer-page-scenarios>`;
			case "profiles": return C`<foyer-page-profiles .ctx=${t}></foyer-page-profiles>`;
			case "groups": return C`<foyer-page-groups .ctx=${t}></foyer-page-groups>`;
			case "users": return C`<foyer-page-users .ctx=${t}></foyer-page-users>`;
			case "devices": return C`<foyer-page-devices .ctx=${t}></foyer-page-devices>`;
			case "contacts": return C`<foyer-page-contacts .ctx=${t}></foyer-page-contacts>`;
			case "rules": return C`<foyer-page-rules .ctx=${t}></foyer-page-rules>`;
			case "health": return C`<foyer-page-health .ctx=${t}></foyer-page-health>`;
			case "test": return C`<foyer-page-test .ctx=${t}></foyer-page-test>`;
			case "log": return C`<foyer-page-log .ctx=${t}></foyer-page-log>`;
			case "settings": return C`<foyer-page-settings .ctx=${t}></foyer-page-settings>`;
			case "api": return this._isAdmin ? C`<foyer-page-api .ctx=${t}></foyer-page-api>` : C`<foyer-page-overview .ctx=${t}></foyer-page-overview>`;
			default: return C`<foyer-page-overview .ctx=${t}></foyer-page-overview>`;
		}
	}
	_renderHelp(e, t) {
		let n = `help.${t}`, r = this._helpOpen(t);
		return C`
      <section class="help" ?data-open=${r}>
        <button
          class="help-hd"
          aria-expanded=${r ? "true" : "false"}
          @click=${() => this._savePrefs({ help: { [t]: !r } })}
        >
          <ha-icon icon="mdi:help-circle-outline"></ha-icon>
          <span>${M(e, `${n}.title`)}</span>
          <span class="sr-only">${M(e, "help.toggle")}</span>
          <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon>
        </button>
        ${r ? C`<div class="help-body">
              <p>${M(e, `${n}.intro`)}</p>
              <dl>
                ${In[t].map((t) => C`
                    <dt>${M(e, `${n}.items.${t}.term`)}</dt>
                    <dd>${M(e, `${n}.items.${t}.text`)}</dd>
                  `)}
              </dl>
              ${Rn[t] ? C`<a
                    class="learn-more"
                    href=${Bn(t, this.hass?.language)}
                    target="_blank"
                    rel="noreferrer noopener"
                    >${M(e, "help.learn_more")}</a
                  >` : T}
            </div>` : T}
      </section>
    `;
	}
	static {
		this.styles = [
			N,
			P,
			o`
      :host {
        display: block;
        min-height: 100vh;
        background: var(--primary-background-color);
        color: var(--primary-text-color);
      }
      .learn-more {
        display: inline-block;
        margin-top: 10px;
        color: var(--primary-color);
        font-size: 13px;
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
      .code-dialog p.by {
        color: var(--primary-text-color);
      }
      .code-dialog p.wrong,
      .lockout {
        color: var(--error-color, #d32f2f);
      }
      .lockout {
        margin: 0 0 16px;
        padding: 10px 14px;
        border-left: 3px solid var(--error-color, #d32f2f);
        background: var(--card-background-color);
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
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
      /* Where the setup pages begin: a rule and a small caption, so the row
         reads as two groups instead of fourteen equal tabs. */
      .tab-group {
        display: flex;
        align-items: center;
        margin-left: 10px;
        padding-left: 14px;
        border-left: 1px solid var(--divider-color);
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--secondary-text-color);
        white-space: nowrap;
        align-self: center;
        height: 20px;
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
customElements.get("foyer-panel") || customElements.define("foyer-panel", Un);
//#endregion
