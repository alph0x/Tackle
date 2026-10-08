// A minimal DOM that runs the shipped plan-view controller against the generated page's own markup.
// It supports the selectors, events and properties the controller uses; it is not a layout engine.
'use strict';
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

function parseSelector(text) {
  return text.split(',').map((part) => part.trim()).filter(Boolean).map((part) => part.split(/\s+/).map((compound) => {
    const attrs = [...compound.matchAll(/\[([\w-]+)(?:(\^?=)"([^"]*)")?\]/g)].map((m) => ({ name: m[1], op: m[2] || null, value: m[3] }));
    const bare = compound.replace(/\[[^\]]*\]/g, '');
    const tag = bare.match(/^[a-zA-Z][\w-]*/);
    return {
      tag: tag ? tag[0].toLowerCase() : null,
      id: (bare.match(/#([\w-]+)/) || [])[1] || null,
      classes: [...bare.matchAll(/\.([\w-]+)/g)].map((m) => m[1]),
      attrs,
    };
  }));
}

class Text {
  constructor(data) { this.nodeType = 3; this.data = data; this.parentNode = null; }
  get textContent() { return this.data; }
  cloneNode() { return new Text(this.data); }
}

class Element {
  constructor(doc, tag, attrs) {
    this.nodeType = 1;
    this.ownerDocument = doc;
    this.tagName = tag.toLowerCase();
    this.attributes = Object.assign({}, attrs || {});
    this.childNodes = [];
    this.parentNode = null;
    this.listeners = {};
    this.style = {};
    this.clientWidth = 0;
    this.clientHeight = 0;
    this.scrollLeft = 0;
    this.scrollTop = 0;
    this.offsetLeft = 0;
    this.offsetWidth = 0;
    this.scrollWidth = 0;
    this.scrolledTo = null;
  }
  get children() { return this.childNodes.filter((n) => n.nodeType === 1); }
  get id() { return this.getAttribute('id') || ''; }
  get className() { return this.getAttribute('class') || ''; }
  set className(value) { this.setAttribute('class', value); }
  get classList() {
    const self = this;
    const read = () => new Set(self.className.split(/\s+/).filter(Boolean));
    const write = (set) => self.setAttribute('class', [...set].join(' '));
    return {
      contains: (name) => read().has(name),
      add: (...names) => { const set = read(); names.forEach((n) => set.add(n)); write(set); },
      remove: (...names) => { const set = read(); names.forEach((n) => set.delete(n)); write(set); },
      toggle: (name, force) => {
        const set = read();
        const on = force === undefined ? !set.has(name) : !!force;
        if (on) { set.add(name); } else { set.delete(name); }
        write(set);
        return on;
      },
    };
  }
  get lang() { return this.getAttribute('lang') || ''; }
  get hidden() { return this.hasAttribute('hidden'); }
  set hidden(value) { if (value) { this.setAttribute('hidden', ''); } else { this.removeAttribute('hidden'); } }
  get tabIndex() { return Number(this.getAttribute('tabindex') || -1); }
  set tabIndex(value) { this.setAttribute('tabindex', String(value)); }
  get value() {
    if (this._value !== undefined) { return this._value; }
    const options = this.querySelectorAll('option');
    const chosen = options.find((o) => o.hasAttribute('selected')) || options[0];
    return chosen ? chosen.getAttribute('value') : '';
  }
  set value(v) { this._value = String(v); }
  get textContent() { return this.childNodes.map((n) => n.textContent).join(''); }
  set textContent(value) { this.childNodes = []; if (value !== '') { this.appendChild(new Text(String(value))); } }
  set innerHTML(value) { assert.strictEqual(value, '', 'the DOM stub only clears innerHTML'); this.childNodes = []; }
  getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null; }
  hasAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attributes, name); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  removeAttribute(name) { delete this.attributes[name]; }
  appendChild(node) {
    if (node.parentNode) { node.parentNode.childNodes.splice(node.parentNode.childNodes.indexOf(node), 1); }
    node.parentNode = this;
    this.childNodes.push(node);
    return node;
  }
  removeChild(node) { const i = this.childNodes.indexOf(node); if (i >= 0) { this.childNodes.splice(i, 1); node.parentNode = null; } return node; }
  contains(node) { for (let n = node; n; n = n.parentNode) { if (n === this) { return true; } } return false; }
  compoundMatches(c) {
    if (c.tag && c.tag !== this.tagName) { return false; }
    if (c.id && this.id !== c.id) { return false; }
    if (!c.classes.every((name) => this.classList.contains(name))) { return false; }
    return c.attrs.every((a) => {
      const value = this.getAttribute(a.name);
      if (value === null) { return false; }
      if (a.op === '=') { return value === a.value; }
      if (a.op === '^=') { return value.startsWith(a.value); }
      return true;
    });
  }
  chainMatches(chain) {
    if (!this.compoundMatches(chain[chain.length - 1])) { return false; }
    let index = chain.length - 2;
    for (let n = this.parentNode; n && index >= 0; n = n.parentNode) {
      if (n.nodeType === 1 && n.compoundMatches(chain[index])) { index -= 1; }
    }
    return index < 0;
  }
  matches(selector) { return parseSelector(selector).some((chain) => this.chainMatches(chain)); }
  closest(selector) {
    const chains = parseSelector(selector);
    for (let n = this; n && n.nodeType === 1; n = n.parentNode) { if (chains.some((chain) => n.chainMatches(chain))) { return n; } }
    return null;
  }
  querySelectorAll(selector) {
    const chains = parseSelector(selector);
    const found = [];
    const walk = (node) => {
      node.children.forEach((child) => {
        if (chains.some((chain) => child.chainMatches(chain))) { found.push(child); }
        walk(child);
      });
    };
    walk(this);
    return found;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  cloneNode(deep) {
    const copy = new Element(this.ownerDocument, this.tagName, this.attributes);
    if (deep) { this.childNodes.forEach((n) => copy.appendChild(n.cloneNode(true))); }
    return copy;
  }
  addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
  removeEventListener(type, fn) { this.listeners[type] = (this.listeners[type] || []).filter((f) => f !== fn); }
  dispatch(type, init) {
    const event = Object.assign({ type, target: this, defaultPrevented: false, button: 0, clientX: 0, clientY: 0, key: null, relatedTarget: null,
      preventDefault() { this.defaultPrevented = true; }, stopPropagation() { this.stopped = true; } }, init || {});
    for (let n = this; n && !event.stopped; n = n.parentNode) {
      event.currentTarget = n;
      (n.listeners[type] || []).slice().forEach((fn) => fn.call(n, event));
    }
    if (!event.stopped) { (this.ownerDocument.listeners[type] || []).slice().forEach((fn) => fn(event)); }
    return event;
  }
  click() { return this.dispatch('click'); }
  key(name) { return this.dispatch('keydown', { key: name }); }
  focus() { this.ownerDocument.activeElement = this; }
  scrollTo(options) { this.scrolledTo = options; }
  getBoundingClientRect() { return { left: 0, top: 0, right: this.clientWidth, bottom: this.clientHeight, width: this.clientWidth, height: this.clientHeight }; }
  scrollIntoView() {}
  getBBox() {
    const box = this.querySelector('rect') || this;
    return { x: Number(box.getAttribute('x') || 0), y: Number(box.getAttribute('y') || 0),
      width: Number(box.getAttribute('width') || 0), height: Number(box.getAttribute('height') || 0) };
  }
}

function buildDocument(tree) {
  const doc = { listeners: {}, activeElement: null };
  doc.createElement = (tag) => new Element(doc, tag, {});
  doc.createTextNode = (data) => new Text(data);
  doc.addEventListener = (type, fn) => { (doc.listeners[type] = doc.listeners[type] || []).push(fn); };
  const build = (node) => {
    if (typeof node === 'string') { return new Text(node); }
    const element = new Element(doc, node[0], node[1]);
    node[2].forEach((child) => element.appendChild(build(child)));
    return element;
  };
  doc.documentElement = build(tree);
  doc.body = doc.documentElement.querySelector('body');
  doc.getElementById = (id) => doc.documentElement.querySelector('#' + id);
  doc.querySelector = (s) => doc.documentElement.querySelector(s);
  doc.querySelectorAll = (s) => doc.documentElement.querySelectorAll(s);
  return doc;
}

function load(options) {
  options = options || {};
  const doc = buildDocument(JSON.parse(fs.readFileSync(process.argv[2], 'utf8')));
  const scripts = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
  const store = {};
  const listeners = {};
  const media = Object.assign({ '(prefers-color-scheme: dark)': false, '(max-width: 760px)': false }, options.media || {});
  const window = {
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    fire(type) { (listeners[type] || []).forEach((fn) => fn({ type })); },
    matchMedia(query) { return { matches: !!media[query], addEventListener() {}, addListener() {} }; },
    setTimeout(fn) { fn(); return 1; },
    setInterval(fn) { (window.intervals = window.intervals || []).push(fn); return 1; },
    localStorage: options.storage === 'throws'
      ? { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); }, removeItem() { throw new Error('blocked'); } }
      : { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } },
  };
  window.window = window;
  const location = { hash: options.hash || '', pathname: '/plan-view.html', search: '', protocol: options.protocol === undefined ? 'file:' : options.protocol, hostname: '', href: 'file:///plan-view.html' + (options.hash || '') };
  window.location = location;
  window.history = { replaceState(state, title, url) { location.hash = String(url).startsWith('#') ? String(url) : ''; } };
  (options.sizes || []).forEach(([selector, width]) => doc.querySelectorAll(selector).forEach((el) => { el.clientWidth = width; }));
  const context = vm.createContext({ window, document: doc, location, console, JSON, Math, Object, Array, String, Number, Date, Error, sessionStorage: window.localStorage });
  ['controller'].concat(options.extra || []).forEach((name) => vm.runInContext(scripts[name], context));
  return { window, document: doc, root: doc.documentElement, store, location, context, scripts,
    all: (s) => doc.querySelectorAll(s), one: (s) => doc.querySelector(s) };
}

global.assert = assert;
global.load = load;
global.vm = vm;
global.settle = () => new Promise((resolve) => setImmediate(resolve));
const scenario = fs.readFileSync(process.argv[4], 'utf8');
vm.runInThisContext('(async () => {\n' + scenario + '\n})()', { filename: 'scenario.js' })
  .then(() => process.stdout.write('OK'), (problem) => { console.error(problem && problem.stack || problem); process.exitCode = 1; });
