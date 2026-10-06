#!/usr/bin/env node
/**
 * P1b-fix: run the SHARED boundary cases through the real page core
 * (annotation_core.js — the same file annotate.html loads).
 *
 * Usage: node p1b/run_boundary_cases.js <manifest.json> <boundary_cases.json> <out.json>
 *
 * Expected values come from boundary_cases.json (hand-written), never from the
 * implementation under test.
 */
const fs = require('fs');
const Core = require('./annotation_core.js');

const manifest = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const casesDoc = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const outPath = process.argv[4];

const sample = manifest.samples.find(s => s.sample_id === casesDoc.sample_id);

/** Decode the sentinel strings used by boundary_cases.json into real JS values. */
function decodeBox(v) {
  if (Array.isArray(v)) return v;
  if (typeof v !== 'string') return v;
  return v.split(',').map(tok => {
    const t = tok.trim();
    if (t === 'NaN') return NaN;
    if (t === 'Infinity') return Infinity;
    if (t === '-Infinity') return -Infinity;
    if (t === 'true') return true;
    if (t === 'false') return false;
    return Number(t);
  });
}

function normalise(ann) {
  const out = Object.assign({}, ann);
  out.intervals = ann.intervals ? ann.intervals.map(iv => Object.assign({}, iv)) : null;
  out.keyframes = ann.keyframes ? ann.keyframes.map(kf => Object.assign({}, kf, { box_xyw: decodeBox(kf.box_xyw) })) : null;
  return out;
}

const results = [];
for (const c of casesDoc.cases) {
  const ann = normalise(c.annotation);
  let payload = null, error = null;
  try {
    payload = Core.buildExport(sample, ann, { run_id: 'boundary' });
  } catch (err) {
    error = err.message;
  }
  const got = payload ? {
    valid: payload.validation.valid,
    mode: payload.reference_derivation.mode,
    reference: payload.exportable_as_reference === true,
    problems: payload.validation.problems,
  } : { valid: null, mode: null, reference: null, problems: [error] };
  const pass = got.valid === c.expect.valid && got.mode === c.expect.mode &&
               got.reference === c.expect.reference;
  results.push({ id: c.id, why: c.why, expect: c.expect, got, pass });
}

const summary = { schema: 'p1b_boundary_results_js_v1', core_version: Core.CORE_VERSION,
                  source: 'annotation_core.js (loaded by annotate.html and by this harness)',
                  cases: results.length, passed: results.filter(r => r.pass).length,
                  failed: results.filter(r => !r.pass).map(r => ({ id: r.id, expect: r.expect, got: r.got })),
                  results };
fs.writeFileSync(outPath, JSON.stringify(summary, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ cases: summary.cases, passed: summary.passed,
                             failed: summary.failed.map(f => f.id) }, null, 1));
process.exit(summary.failed.length === 0 ? 0 : 1);
