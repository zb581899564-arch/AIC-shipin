/* Offline VM regression of the actual delivered annotate.html script. This is
 * deliberately not described as browser E2E or visual/download verification. */
const fs = require('fs');
const vm = require('vm');
const crypto = require('crypto');
const path = require('path');
const core = require('./annotation_core.js');
const root = path.resolve(__dirname, '../..');
const page = fs.readFileSync(path.join(__dirname, 'annotate.html'), 'utf8');
const script = page.match(/<script>\s*(const CORE = window.AnnotationCore;[\s\S]*?)<\/script>/)[1];
const manifest = JSON.parse(page.match(/const MANIFEST = (.*);/)[1]);
const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    const e = { id, style: {}, dataset: {}, value: '', textContent: '', innerHTML: '',
      checked: false, clientWidth: 320, currentTime: 0, complete: true, naturalWidth: 320,
      children: [], listeners: {}, appendChild(child) { this.children.push(child); },
      addEventListener(name, fn) { this.listeners[name] = fn; },
      dispatchEvent(ev) { if (this.listeners[ev.type]) this.listeners[ev.type](ev);
                          if (this['on' + ev.type]) this['on' + ev.type](ev); },
      click() { if (this.onclick) this.onclick(); },
      load() {}, removeAttribute(name) { if (name === 'src') this._src = ''; },
      replaceWith(newElement) { elements.set(this.id, newElement); },
      getBoundingClientRect() { return { width: 320, left: 0, top: 0 }; } };
    Object.defineProperty(e, 'src', { get() { return this._src || ''; }, set(value) {
      this._src = value; this.complete = !imageDelay;
      if (imageDelay && this.isImage && value.startsWith('blob:')) { pendingImage = this; return; }
      this.naturalWidth = imageFailure && this.isImage && value.startsWith('blob:') ? 0 : 320;
    } });
    elements.set(id, e);
  }
  return elements.get(id);
}
let imageFailure = false, imageDelay = false, pendingImage = null;
let failInfo = false, mismatch = false, wrongMedia = false, held = null;
const body = Buffer.from('offline-page-frame-bytes');
const digest = crypto.createHash('sha256').update(body).digest('hex');
function fetch(url) {
  if (url.endsWith('/health')) return Promise.resolve({ ok: true, json: async () => ({ ok: true }) });
  const query = new URL(url).searchParams;
  const frame = Number(query.get('frame'));
  const sample = manifest.samples.find(s => s.sample_id === query.get('sample'));
  if (url.includes('/frameinfo?')) {
    if (held && held.frame === frame) return held.promise;
    if (failInfo) return Promise.resolve({ ok: false, status: 503 });
    return Promise.resolve({ ok: true, json: async () => ({ sample_id: sample.sample_id,
      media_sha256: wrongMedia ? 'bad' : sample.sha256_local, index: frame, pts_sec: frame / sample.fps,
      time_base_sec: 0.001, width: sample.source_width, height: sample.source_height,
      sha256: mismatch ? '0'.repeat(64) : digest }) });
  }
  return Promise.resolve({ ok: true, arrayBuffer: async () => body });
}
let blobId = 0;
const urlApi = { createObjectURL: () => `blob:offline-${++blobId}`, revokeObjectURL() {} };
const document = { getElementById: element, createElement: id => element('created-' + id + '-' + Math.random()),
  querySelector: element, querySelectorAll: () => [], addEventListener() {}, title: '' };
const window = { AnnotationCore: core, addEventListener() {}, __E2E_NO_DOWNLOAD: true };
const context = { window, document, fetch, crypto: crypto.webcrypto, URL: urlApi,
  Image: class { constructor() { const image = element('image-' + Math.random()); image.isImage = true; return image; } },
  Blob, localStorage: { setItem() {}, getItem() { return null; } },
  navigator: { clipboard: { writeText() {} } }, confirm: () => true,
  Event: class { constructor(type) { this.type = type; } }, MouseEvent: class {},
  console, setTimeout };
vm.createContext(context); vm.runInContext(script, context);
const api = window.__annotator;
const cases = [];
function check(name, pass, observed) { cases.push({ name, pass: !!pass, observed }); }
function hold(frame) {
  let release;
  const promise = new Promise(resolve => { release = resolve; });
  held = { frame, promise, release: () => { held = null; resolveStub(release, frame); } };
}
function resolveStub(resolve, frame) {
  const s = api.currentSample();
  resolve({ ok: true, json: async () => ({ sample_id: s.sample_id,
    media_sha256: s.sha256_local, index: frame, pts_sec: frame / s.fps,
    time_base_sec: 0.001, width: s.source_width, height: s.source_height, sha256: digest }) });
}
async function run() {
  await Promise.resolve();
  await api.fetchExactFrame(64);
  const exact64 = api.state().still;
  api.setFrame(65);
  api.addKeyframe();
  const old = api.state().annotations.P01.keyframes[0].provenance;
  check('64_then_65_invalidates_still', !!exact64 && !api.state().still &&
    element('still').style.display === 'none' && old.method !== 'decoded_frame', old);

  await api.fetchExactFrame(64);
  element('setStartHere').click();
  api.setFrame(65);
  await api.fetchExactFrame(65);
  element('setLastHere').click();
  api.addInterval(64, 65);
  const iv = api.state().annotations.P01.intervals[0];
  check('endpoint_clicks_keep_separate_provenance', iv.start_provenance.method === 'decoded_frame' &&
    iv.start_provenance.frame === 64 && iv.end_provenance.method === 'decoded_frame' &&
    iv.end_provenance.frame === 65 && iv.start_provenance.request_version !==
    iv.end_provenance.request_version, iv);

  hold(37); const pending = api.fetchExactFrame(37);
  await Promise.resolve(); api.switchSample(1); held.release(); await pending;
  check('late_response_cannot_cross_sample', api.state().current === 1 && !api.state().still,
    api.state().still);

  hold(38); const older = api.fetchExactFrame(38);
  await Promise.resolve(); const releaseOlder = held.release;
  await api.fetchExactFrame(39); releaseOlder(); await older;
  check('reverse_response_keeps_latest', api.state().still && api.state().still.frame === 39,
    api.state().still);

  imageDelay = true; const loading = api.fetchExactFrame(43);
  for (let i = 0; i < 50 && !pendingImage; i++) await new Promise(setImmediate);
  if (!pendingImage) throw new Error('image load did not enter delayed state');
  api.switchSample(0);
  imageDelay = false;
  pendingImage.complete = true; pendingImage.naturalWidth = 320; pendingImage.onload();
  await loading; pendingImage = null;
  check('image_loading_then_switch_sample', api.state().current === 0 && !api.state().still,
    api.state().still);

  failInfo = true; await api.fetchExactFrame(40); failInfo = false;
  check('service_failure_no_exact', !api.state().still, element('frameInfo').textContent);
  imageFailure = true; await api.fetchExactFrame(41); imageFailure = false;
  check('image_failure_no_exact', !api.state().still, element('frameInfo').textContent);
  mismatch = true; await api.fetchExactFrame(42); mismatch = false;
  check('hash_failure_no_exact', !api.state().still, element('frameInfo').textContent);
  wrongMedia = true; await api.fetchExactFrame(44); wrongMedia = false;
  check('media_identity_failure_no_exact', !api.state().still, element('frameInfo').textContent);

  for (const s of [manifest.samples[0], manifest.samples[4]]) {
    for (const [label, b] of [['left', [-500, 0, s.max_legal_crop.max_width]],
      ['right', [500, 0, s.max_legal_crop.max_width]],
      ['top', [0, -500, s.max_legal_crop.max_width]],
      ['bottom', [0, 500, s.max_legal_crop.max_width]]]) {
      const clamped = core.clampBox(b, s), problems = core.boxProblems(clamped, s, label);
      check('clamp_' + s.sample_id + '_' + label, problems.length === 0,
            { box: clamped, problems });
    }
  }
  const draft = core.buildDraft(manifest, {}, {});
  const changes = [
    ['duplicate', d => d.annotations.push(JSON.parse(JSON.stringify(d.annotations[0])))],
    ['annotations_object', d => { d.annotations = {}; }],
    ['entry_array', d => { d.annotations[0] = []; }],
    ['annotation_array', d => { d.annotations[0].annotation = []; }],
    ['intervals_object', d => { d.annotations[0].annotation = { intervals: {} }; }],
    ['keyframe_entry', d => { d.annotations[0].annotation = { keyframes: [1] }; }],
    ['missing_keyframe_box', d => { d.annotations[0].annotation = { keyframes: [{ frame: 64 }] }; }],
    ['annotator_object', d => { d.annotations[0].annotation = { annotator: {} }; }],
    ['endpoint_provenance_array', d => { d.annotations[0].annotation = {
      intervals: [{ start_frame: 1, end_frame_exclusive: 2, start_provenance: [] }] }; }],
    ['media_hash', d => { d.annotations[0].media_sha256 = 'bad'; }],
    ['manifest_version', d => { d.manifest.run_id = 'bad'; }],
    ['schema_version', d => { d.core_version = 'bad'; }],
  ];
  const draftCases = [];
  for (const [name, mutate] of changes) {
    const d = JSON.parse(JSON.stringify(draft)); mutate(d);
    const before = JSON.stringify(api.state().annotations);
    const verdict = core.validateDraft(d, manifest);
    const applied = api.applyDraft(d);
    const unchanged = JSON.stringify(api.state().annotations) === before;
    check('draft_' + name, !verdict.valid && !applied && unchanged, verdict.problems);
    draftCases.push({ name, draft: d, js_valid: verdict.valid });
  }
  const incomplete = JSON.parse(JSON.stringify(draft));
  incomplete.annotations[0].annotation = { status: 'HAS_HIGHLIGHT', intervals: [], annotator: '' };
  const incompleteVerdict = core.validateDraft(incomplete, manifest);
  check('incomplete_semantic_draft_allowed', incompleteVerdict.valid, incompleteVerdict);
  draftCases.push({ name: 'incomplete_semantic', draft: incomplete, js_valid: incompleteVerdict.valid });
  const out = { run_id: 'round6_p1b_fix2_20260917T0951Z',
    source: 'actual annotate.html script in Node VM, not browser',
    cases, passed: cases.filter(c => c.pass).length, total: cases.length };
  const dir = path.join(root, 'reports/round6_score_alignment/phase1b_fix2');
  fs.writeFileSync(path.join(dir, 'page_vm_tests.json'), JSON.stringify(out, null, 2) + '\n');
  fs.writeFileSync(path.join(dir, 'draft_common_cases.json'), JSON.stringify(draftCases, null, 2) + '\n');
  console.log(JSON.stringify({ passed: out.passed, total: out.total }));
  if (out.passed !== out.total) process.exitCode = 2;
}
run().catch(err => { console.error(err); process.exitCode = 2; });
