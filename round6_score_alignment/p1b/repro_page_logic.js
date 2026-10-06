#!/usr/bin/env node
/**
 * P1b-fix: drive the REAL page JavaScript of annotate.html in a Node VM.
 *
 * This is not a Python mirror: the script text is taken from the delivered HTML and
 * executed with a minimal DOM stub, so the results come from the same code the
 * browser runs.  It records behaviour (no assertions of its own) so the same harness
 * can be run before and after the fix and the two outputs compared.
 *
 * Usage: node p1b/repro_page_logic.js <annotate.html> <out.json>
 */
const fs = require('fs');
const vm = require('vm');

const htmlPath = process.argv[2];
const outPath = process.argv[3];
const html = fs.readFileSync(htmlPath, 'utf8');

const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (scripts.length === 0) { console.error('no inline script found'); process.exit(2); }
const source = scripts[scripts.length - 1];

// ---- minimal DOM stub -------------------------------------------------------
const listeners = [];
const elements = {};
function makeEl(id) {
  const el = {
    id, style: {}, dataset: {}, children: [], innerHTML: '', textContent: '', title: '',
    value: '', checked: false, max: 0, src: '', className: '', disabled: false,
    classList: { add() {}, remove() {}, contains() { return false; } },
    appendChild(child) { this.children.push(child); return child; },
    removeChild() {}, remove() {}, click() { el._clicked = (el._clicked || 0) + 1; },
    load() {}, play() { return Promise.resolve(); }, pause() {},
    addEventListener(type, fn) { listeners.push({ id, type }); },
    removeEventListener() {},
    setAttribute() {}, getAttribute() { return null; },
    querySelector() { return makeEl(id + '>child'); },
    querySelectorAll() { return []; },
    getBoundingClientRect() { return { left: 0, top: 0, width: 534, height: 300 }; },
    currentTime: 0, duration: 150, videoWidth: 534, videoHeight: 300, readyState: 1,
  };
  elements[id] = el;
  return el;
}
const selectorCache = {};
const documentStub = {
  getElementById(id) { return elements[id] || makeEl(id); },
  querySelector(sel) { return selectorCache[sel] || (selectorCache[sel] = makeEl('sel:' + sel)); },
  querySelectorAll() { return []; },
  createElement(tag) { return makeEl('created:' + tag); },
  addEventListener(type, fn) { listeners.push({ id: 'document', type }); },
  body: makeEl('body'),
  title: 'stub',
};
const context = {
  document: documentStub,
  window: { addEventListener(t, f) { listeners.push({ id: 'window', type: t }); },
            location: { reload() {} }, localStorage: (() => {
              const store = {};
              return { getItem: k => (k in store ? store[k] : null),
                       setItem: (k, v) => { store[k] = String(v); },
                       removeItem: k => { delete store[k]; } };
            })() },
  navigator: { clipboard: { writeText() {} }, sendBeacon: undefined },
  console, setTimeout, clearTimeout, JSON, Math, Date, URL: { createObjectURL() { return 'blob:x'; },
    revokeObjectURL() {} }, Blob: function () {}, alert: () => {}, confirm: () => true,
  fetch: undefined, XMLHttpRequest: undefined, WebSocket: undefined,
};
context.globalThis = context;

const result = { source_file: htmlPath, checks: {}, notes: [] };

function setElementsFromHtml() {
  // create stubs for every id="..." present in the HTML
  for (const m of html.matchAll(/id="([A-Za-z0-9_\-]+)"/g)) { makeEl(m[1]); }
}

try {
  setElementsFromHtml();
  vm.createContext(context);
  vm.runInContext(source, context, { filename: 'annotate.html:inline-script' });
  result.notes.push('page script executed in the VM');
} catch (err) {
  result.notes.push('page script threw: ' + err.message);
}

// ---- checks that only need static inspection of the delivered HTML ----------
const hasShowBoxHandler = /getElementById\(\s*["']showBox["']\s*\)/.test(html) ||
  /showBox["']\s*\)\s*\.onclick/.test(html);
const dragListeners = listeners.filter(l => l.type === 'mousedown' || l.type === 'mousemove' ||
  l.type === 'mouseup' || l.type === 'pointerdown');
const hasDraftApi = /saveDraft|exportDraft|importDraft|loadDraft|restoreDraft/i.test(source);
const hasLocalStorageDraft = /localStorage/.test(source);
const globalFrameSource = (source.match(/frame_source/g) || []).length;
const hasPerRecordProvenance = /frame_source/.test(source) &&
  /intervals\s*\.map/.test(source) && /keyframes\s*\.map/.test(source);
const mentionsEndExclusive = /end_frame_exclusive|half_open|end_exclusive/i.test(source);
const hasValidationCall = /validateExport|validate_export|problems/.test(source);
const currentTimeErrorZero = /estimated_error_frames\s*:\s*0/.test(source);

// ---- drive the real logic if the VM loaded --------------------------------
function tryCall(name, args) {
  try {
    if (typeof context[name] !== 'function') return { called: false, reason: 'not a function' };
    return { called: true, value: context[name](...args) };
  } catch (err) {
    return { called: false, reason: err.message };
  }
}

// `const` bindings are lexical in a vm script, so read them by evaluation
function evalInPage(expr) {
  try { return { ok: true, value: vm.runInContext(expr, context) }; }
  catch (err) { return { ok: false, error: err.message }; }
}
const manifestEval = evalInPage('MANIFEST');
const manifest = manifestEval.ok ? manifestEval.value : null;
result.checks.manifest_present = !!manifest;
result.checks.sample_count = manifest ? manifest.samples.length : null;

if (manifest) {
  const s = manifest.samples[0];
  const fps = s.fps, n = s.n_frames;
  const mk = (over) => Object.assign({
    status: 'HAS_HIGHLIGHT', confirm_no_highlight: false,
    intervals: [{ start_frame: 10, end_frame: 20 }],
    keyframes: [{ frame: 12, box: [0, 0, 320] }],
    annotator: 'NODE_PROBE', reviewer: null, notes: '', frame_source: 'browser_estimate',
    estimated_error_frames: 0,
  }, over || {});
  const build = (ann) => {
    try { return context.buildExport(s, ann); } catch (err) { return { error: err.message }; }
  };
  result.checks.negative_width_box = build(mk({ keyframes: [{ frame: 12, box: [0, 0, -10] }] }));
  result.checks.nan_box = build(mk({ keyframes: [{ frame: 12, box: [NaN, 0, 100] }] }));
  result.checks.out_of_bounds_box = build(mk({ keyframes: [{ frame: 12, box: [400, 0, 320] }] }));
  result.checks.no_highlight_with_leftovers = build(mk({
    status: 'NO_HIGHLIGHT', confirm_no_highlight: true,
    intervals: [{ start_frame: 1, end_frame: 2 }], keyframes: [{ frame: 1, box: [0, 0, 100] }] }));
  result.checks.unannotated_with_leftovers = build(mk({ status: 'UNANNOTATED',
    intervals: [{ start_frame: 1, end_frame: 2 }], keyframes: [] }));
  result.checks.normal_sparse = build(mk({}));
  result.checks.export_has_validation_field = Object.prototype.hasOwnProperty.call(
    result.checks.normal_sparse || {}, 'validation');
  result.checks.export_interval_keys = Object.keys(
    (result.checks.normal_sparse.intervals || [{}])[0] || {});
  result.checks.export_frame_provenance_keys = Object.keys(
    (result.checks.normal_sparse || {}).frame_provenance || {});
}

result.static = {
  has_showBox_handler: hasShowBoxHandler,
  drag_listener_count: dragListeners.length,
  has_draft_api: hasDraftApi,
  has_localstorage_draft: hasLocalStorageDraft,
  frame_source_mentions: globalFrameSource,
  has_per_record_provenance: hasPerRecordProvenance,
  mentions_end_exclusive: mentionsEndExclusive,
  has_export_validation_call: hasValidationCall,
  hardcodes_error_zero: currentTimeErrorZero,
  listener_summary: listeners,
};

// keyframe rows must land in the keyframe table, not the interval table
try {
  const s = manifest.samples[0];
  const a = context.ann(s);
  a.keyframes = [{ frame: 5, box: [0, 0, 100] }];
  a.intervals = [{ start_frame: 1, end_frame: 2 }];
  const itBody = documentStub.querySelector('#intervalTable tbody');
  const ktBody = documentStub.querySelector('#kfTable tbody');
  itBody.children.length = 0; ktBody.children.length = 0;
  context.renderTables();
  result.static.keyframe_rows_in_interval_table = itBody.children.length;
  result.static.keyframe_rows_in_keyframe_table = ktBody.children.length;
} catch (err) {
  result.static.keyframe_row_check_error = err.message;
}

fs.writeFileSync(outPath, JSON.stringify(result, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ out: outPath, static: result.static,
  checks: Object.fromEntries(Object.entries(result.checks).map(([k, v]) => [k,
    v && typeof v === 'object' ? { mode: v.reference_derivation && v.reference_derivation.mode,
      exportable: v.exportable_as_reference } : v])) }, null, 2));
