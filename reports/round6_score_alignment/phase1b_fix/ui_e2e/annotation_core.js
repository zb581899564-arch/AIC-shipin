/**
 * P1b annotation core — pure logic, no DOM, no network.
 *
 * This file is loaded by BOTH the delivered page (annotate.html) and the Node
 * cross-check harness, so the browser and the Python validator cannot drift apart
 * silently.  The Python side mirrors exactly these rules and the two are compared
 * on the same fixed boundary cases (boundary_cases.json).
 *
 * Conventions fixed here (v2):
 *   interval_semantics = "half_open_end_exclusive"
 *       an interval is [start_frame, end_frame_exclusive); legal range is
 *       0 <= start_frame < end_frame_exclusive <= n_frames, so an interval may end
 *       at n_frames to cover the last frame.
 *   keyframes are sparse composition boxes stored under `box_xyw` = [x, y, w] (the same
 *       key the P1a reference schema uses) at one exact frame; the height is derived as
 *       h = w * target_h / target_w and must stay inside the frame.
 *   every interval endpoint and every keyframe carries its own provenance record.
 *   unannotated is not empty: UNANNOTATED/UNCERTAIN keep intervals=null.
 */
(function (root) {
  'use strict';

  const CORE_VERSION = 'p1b_core_v2';
  const EXPORT_SCHEMA = 'p1b_annotation_export_v2';
  const DRAFT_SCHEMA = 'p1b_annotation_draft_v2';
  const INTERVAL_SEMANTICS = 'half_open_end_exclusive';
  const STATES = ['UNANNOTATED', 'HAS_HIGHLIGHT', 'NO_HIGHLIGHT', 'UNCERTAIN'];
  const LOCATOR_METHODS = ['decoded_frame', 'pts_sample', 'manual_frame_input',
                           'browser_seek', 'unknown'];

  function isFiniteNumber(v) {
    return typeof v === 'number' && Number.isFinite(v);
  }

  function isFrame(v) {
    return typeof v === 'number' && Number.isInteger(v) && Number.isFinite(v);
  }

  function timeFromFrame(frame, sample) {
    return frame / sample.fps;
  }

  function boxHeight(w, sample) {
    return w * sample.target_ratio_wh[1] / sample.target_ratio_wh[0];
  }

  /** Clamp a box so it keeps the target ratio and stays inside the source frame. */
  function clampBox(box, sample) {
    const [tw, th] = sample.target_ratio_wh;
    let x = isFiniteNumber(box[0]) ? box[0] : 0;
    let y = isFiniteNumber(box[1]) ? box[1] : 0;
    let w = isFiniteNumber(box[2]) ? box[2] : 0;
    const maxW = Math.min(sample.max_legal_crop.max_width, sample.source_width);
    w = Math.max(1, Math.min(w, maxW));
    const h = w * th / tw;
    x = Math.max(0, Math.min(x, sample.source_width - w));
    y = Math.max(0, Math.min(y, sample.source_height - h));
    return [Math.round(x), Math.round(y), Math.round(w * 100) / 100];
  }

  function boxProblems(box, sample, where) {
    const out = [];
    if (!Array.isArray(box) || box.length !== 3) {
      out.push(where + ': box must be a three-element [x, y, w]');
      return out;
    }
    const [x, y, w] = box;
    for (const [name, v] of [['x', x], ['y', y], ['w', w]]) {
      if (typeof v === 'boolean' || typeof v === 'string' || !isFiniteNumber(v)) {
        out.push(where + ': ' + name + ' must be a finite number (got ' + JSON.stringify(v) + ')');
      }
    }
    if (out.length) return out;
    if (x < 0 || y < 0) out.push(where + ': x and y must be >= 0');
    if (w <= 0) out.push(where + ': w must be > 0');
    const h = boxHeight(w, sample);
    if (w > sample.max_legal_crop.max_width + 1e-6) {
      out.push(where + ': w=' + w + ' exceeds the max legal width ' +
        sample.max_legal_crop.max_width.toFixed(4));
    }
    if (x + w > sample.source_width + 1e-6 || y + h > sample.source_height + 1e-6) {
      out.push(where + ': box [' + [x, y, w] + '] with derived h=' + h.toFixed(2) +
        ' leaves the ' + sample.source_width + 'x' + sample.source_height + ' frame');
    }
    return out;
  }

  //: methods whose frame position is verified against decoded media (exact)
  const EXACT_METHODS = ['decoded_frame', 'pts_sample'];

  /**
   * Provenance rules for one endpoint / keyframe.
   * `allowed_frames` lists the frames this locator is allowed to reference: the
   * annotator always lands on a displayed frame, and an exclusive interval end is
   * derived from the last kept frame (end_frame_exclusive - 1).
   */
  function locatorProblems(loc, where, allowed_frames) {
    const out = [];
    if (!loc || typeof loc !== 'object') { out.push(where + ': missing provenance record'); return out; }
    if (LOCATOR_METHODS.indexOf(loc.method) < 0) {
      out.push(where + ': unknown locator method ' + JSON.stringify(loc.method));
    }
    if (!isFrame(loc.frame)) {
      out.push(where + ': provenance must record the displayed frame it used');
    } else if (allowed_frames && allowed_frames.indexOf(loc.frame) < 0) {
      out.push(where + ': provenance frame ' + loc.frame + ' is not one of ' +
        JSON.stringify(allowed_frames) + ' for this boundary');
    }
    if (loc.method === 'decoded_frame') {
      if (!isFrame(loc.decoded_index)) out.push(where + ': decoded index missing');
      if (!isFiniteNumber(loc.decoded_pts_sec)) out.push(where + ': decoded PTS missing');
      if (!loc.image_sha256) out.push(where + ': decoded frame image hash missing');
      if (loc.decoded_index !== loc.frame) {
        out.push(where + ': decoded index ' + loc.decoded_index + ' != provenanced frame ' + loc.frame);
      }
    }
    if (loc.method === 'pts_sample' && !isFrame(loc.pts_sample_index)) {
      out.push(where + ': pts sample index missing');
    }
    if (loc.method === 'browser_seek' && loc.verified === true) {
      out.push(where + ': a browser seek cannot be marked verified');
    }
    if (!isFiniteNumber(loc.estimated_error_frames) && loc.estimated_error_frames !== null) {
      out.push(where + ': estimated_error_frames must be a number or null');
    }
    if (EXACT_METHODS.indexOf(loc.method) < 0 && loc.estimated_error_frames === 0) {
      out.push(where + ': only a media-verified locator (' + EXACT_METHODS.join('/') +
        ') may claim an exact position (error 0); use null when the error is unknown');
    }
    return out;
  }

  /** Validate one sample's annotation. Returns {valid, problems, warnings, mode, reference}. */
  function validateAnnotation(sample, ann) {
    const problems = [];
    const warnings = [];
    const state = ann && ann.status;
    if (STATES.indexOf(state) < 0) problems.push('unknown annotation_status ' + JSON.stringify(state));
    const intervals = ann && ann.intervals ? ann.intervals : null;
    const keyframes = ann && ann.keyframes ? ann.keyframes : null;
    const n = sample.n_frames;

    if (state === 'UNANNOTATED' || state === 'UNCERTAIN') {
      if (intervals !== null && intervals !== undefined) {
        problems.push(state + ' must not carry intervals (unannotated is not empty)');
      }
      if (keyframes !== null && keyframes !== undefined) {
        problems.push(state + ' must not carry keyframes');
      }
    }

    if (state === 'NO_HIGHLIGHT') {
      if (!ann.confirm_no_highlight) {
        problems.push('NO_HIGHLIGHT requires the explicit confirmation checkbox');
      }
      if ((intervals && intervals.length) || (keyframes && keyframes.length)) {
        problems.push('NO_HIGHLIGHT conflicts with the remaining intervals/keyframes; ' +
                      'clear them explicitly or switch the status back (nothing is discarded silently)');
      }
    }

    if (state === 'HAS_HIGHLIGHT' && (!intervals || intervals.length === 0)) {
      problems.push('HAS_HIGHLIGHT requires at least one interval');
    }

    const seenIntervals = new Set();
    (intervals || []).forEach((iv, i) => {
      const where = 'interval ' + i;
      const s = iv.start_frame, e = iv.end_frame_exclusive;
      if (!isFrame(s)) problems.push(where + ': start_frame must be an integer');
      if (!isFrame(e)) problems.push(where + ': end_frame_exclusive must be an integer');
      if (isFrame(s) && isFrame(e)) {
        if (!(0 <= s && s < e && e <= n)) {
          problems.push(where + ': require 0 <= start_frame < end_frame_exclusive <= ' + n +
            ' (got [' + s + ', ' + e + '))');
        }
        const key = s + ':' + e;
        if (seenIntervals.has(key)) problems.push(where + ': duplicate interval [' + s + ', ' + e + ')');
        seenIntervals.add(key);
      }
      problems.push(...locatorProblems(iv.start_provenance, where + ' start',
                                       isFrame(s) ? [s] : null));
      problems.push(...locatorProblems(iv.end_provenance, where + ' end',
                                       isFrame(e) ? [e - 1] : null));
      if (isFrame(e) && iv.end_provenance && iv.end_provenance.frame === e - 1 &&
          iv.end_provenance.derived !== 'end_frame_exclusive = last_kept_frame + 1') {
        warnings.push(where + ': end provenance should record the derivation ' +
                      'end_frame_exclusive = last_kept_frame + 1');
      }
      if (isFrame(s) && isFiniteNumber(iv.start_sec)) {
        const err = Math.abs(iv.start_sec - timeFromFrame(s, sample)) * sample.fps;
        if (err > 0.5) problems.push(where + ': start_sec deviates ' + err.toFixed(2) +
          ' frames from the frame number');
      }
      if (isFrame(e) && isFiniteNumber(iv.end_sec)) {
        const err = Math.abs(iv.end_sec - timeFromFrame(e, sample)) * sample.fps;
        if (err > 0.5) problems.push(where + ': end_sec deviates ' + err.toFixed(2) +
          ' frames from the frame number');
      }
      if (iv.end_frame_exclusive === n && iv.end_frame !== undefined) {
        warnings.push(where + ': end_frame_exclusive equals n_frames, covering the last frame');
      }
    });

    const seenFrames = new Set();
    (keyframes || []).forEach((kf, i) => {
      const where = 'keyframe ' + i;
      if (!isFrame(kf.frame)) problems.push(where + ': frame must be an integer');
      else {
        if (!(kf.frame >= 0 && kf.frame < n)) {
          problems.push(where + ': frame ' + kf.frame + ' outside 0..' + (n - 1));
        }
        if (seenFrames.has(kf.frame)) problems.push(where + ': duplicate keyframe for frame ' + kf.frame);
        seenFrames.add(kf.frame);
      }
      problems.push(...boxProblems(kf.box_xyw, sample, where));
      problems.push(...locatorProblems(kf.provenance, where,
                                       isFrame(kf.frame) ? [kf.frame] : null));
    });

    const annotator = ann && ann.annotator ? String(ann.annotator).trim() : '';
    if (!annotator) problems.push('annotator must be recorded');

    const mode = deriveMode(state, ann, problems.length === 0);
    return { valid: problems.length === 0, problems: problems, warnings: warnings,
             mode: mode.mode, mode_reason: mode.reason,
             reference: problems.length === 0 ? mode.reference : null };
  }

  function deriveMode(state, ann, valid) {
    if (state === 'UNANNOTATED') {
      return { mode: 'NOT_EXPORTABLE', reason: '尚未标注；未标注不等于空参考', reference: null };
    }
    if (state === 'UNCERTAIN') {
      return { mode: 'NOT_EXPORTABLE', reason: '标注者标记为不确定；不计入参考', reference: null };
    }
    if (state === 'NO_HIGHLIGHT') {
      if (!ann.confirm_no_highlight) {
        return { mode: 'NOT_EXPORTABLE', reason: '无高光需标注者显式确认', reference: null };
      }
      if (!valid) {
        return { mode: 'BLOCKED_BY_VALIDATION',
                 reason: '校验未通过（例如仍残留区间/关键帧），不允许导出空参考', reference: null };
      }
      return { mode: 'NO_HIGHLIGHT_EMPTY_GT',
               reason: '标注者确认整段无高光：空帧集合（coverage=full, frames=[]）',
               reference: { coverage: 'full',
                            videos: [{ video_id: null, coverage: 'full', frames: [] }] } };
    }
    if (state === 'HAS_HIGHLIGHT') {
      if (!valid) {
        return { mode: 'BLOCKED_BY_VALIDATION', reason: '校验未通过，不允许导出参考',
                 reference: null };
      }
      const intervals = ann.intervals || [];
      const keyframes = ann.keyframes || [];
      if (!intervals.length) {
        return { mode: 'NOT_EXPORTABLE', reason: '状态为有高光但没有时间区间', reference: null };
      }
      if (!keyframes.length) {
        return { mode: 'TEMPORAL_ONLY',
                 reason: '只有时间区间、没有构图关键帧：仅可做时间诊断，不构成联合指标参考',
                 reference: null };
      }
      return { mode: 'SPARSE_KEYFRAME_GT',
               reason: '稀疏构图关键帧：coverage=sparse（只有列出的帧被标注）',
               reference: { coverage: 'sparse',
                            videos: [{ video_id: null, coverage: 'sparse',
                                       frames: keyframes.map(kf => ({ frame: kf.frame, box_xyw: kf.box_xyw })) }] } };
    }
    return { mode: 'NOT_EXPORTABLE', reason: 'unknown state', reference: null };
  }

  /** Build the v2 export object (draft or reference payload). */
  function buildExport(sample, ann, opts) {
    opts = opts || {};
    const verdict = validateAnnotation(sample, ann);
    const reference = verdict.reference && verdict.reference.videos
      ? { coverage: verdict.reference.coverage,
          videos: verdict.reference.videos.map(v => Object.assign({}, v, { video_id: sample.sample_id })) }
      : null;
    const payload = {
      schema: EXPORT_SCHEMA,
      core_version: CORE_VERSION,
      run_id: opts.run_id || null,
      sample_id: sample.sample_id,
      source_group: sample.source_group,
      split: sample.split || 'pilot_dev',
      media: { file_name: sample.file_name, sha256: sample.sha256_local, fps: sample.fps,
               n_frames: sample.n_frames, source_width: sample.source_width,
               source_height: sample.source_height, target_ratio_wh: sample.target_ratio_wh },
      annotation_status: ann.status,
      confirm_no_highlight: !!ann.confirm_no_highlight,
      interval_semantics: INTERVAL_SEMANTICS,
      intervals: (ann.intervals || null) && ann.intervals.map(iv => ({
        start_frame: iv.start_frame,
        end_frame_exclusive: iv.end_frame_exclusive,
        start_sec: timeFromFrame(iv.start_frame, sample),
        end_sec: timeFromFrame(iv.end_frame_exclusive, sample),
        start_provenance: iv.start_provenance || null,
        end_provenance: iv.end_provenance || null,
      })),
      keyframes: (ann.keyframes || null) && ann.keyframes.map(kf => ({
        frame: kf.frame,
        box_xyw: kf.box_xyw,
        box_height_derived: boxHeight(kf.box_xyw[2], sample),
        provenance: kf.provenance || null,
      })),
      identity: { annotator: (ann.annotator || '').trim() || null,
                  reviewer: (ann.reviewer || '').trim() || null },
      notes: ann.notes || '',
      validation: { core_version: CORE_VERSION, valid: verdict.valid,
                    problems: verdict.problems, warnings: verdict.warnings },
      exportable_as_reference: reference !== null,
      reference_derivation: { mode: verdict.mode, reason: verdict.mode_reason, reference: reference },
      not_human_reviewed_unless_recorded: true,
      label_status: 'WEAK_HUMAN_SPARSE_PENDING_REVIEW',
    };
    return payload;
  }

  /** Draft document (all samples, no validation requirement). */
  function buildDraft(manifest, annotations, opts) {
    opts = opts || {};
    return {
      schema: DRAFT_SCHEMA,
      core_version: CORE_VERSION,
      run_id: opts.run_id || null,
      created_utc: new Date().toISOString(),
      interval_semantics: INTERVAL_SEMANTICS,
      manifest: {
        schema: manifest.schema,
        run_id: manifest.run_id,
        sample_digest: sampleDigest(manifest),
      },
      annotations: manifest.samples.map(s => ({
        sample_id: s.sample_id,
        media_sha256: s.sha256_local,
        annotation: annotations[s.sample_id] || null,
      })),
    };
  }

  function sampleDigest(manifest) {
    return manifest.samples.map(s => s.sample_id + ':' + s.sha256_local).join('|');
  }

  /** Validate a draft against the current manifest (identity + version). */
  function validateDraft(draft, manifest) {
    const problems = [];
    if (!draft || typeof draft !== 'object') return { valid: false, problems: ['draft is not an object'] };
    if (draft.schema !== DRAFT_SCHEMA) problems.push('unexpected draft schema ' + JSON.stringify(draft.schema));
    if (draft.core_version !== CORE_VERSION) {
      problems.push('draft core_version ' + draft.core_version + ' != ' + CORE_VERSION);
    }
    if (draft.interval_semantics !== INTERVAL_SEMANTICS) {
      problems.push('draft interval semantics ' + JSON.stringify(draft.interval_semantics) +
                    ' cannot be converted automatically; refusing to guess');
    }
    const digest = (draft.manifest && draft.manifest.sample_digest) || '';
    if (digest !== sampleDigest(manifest)) {
      problems.push('draft was written for a different media manifest (identity mismatch)');
    }
    const known = new Set(manifest.samples.map(s => s.sample_id));
    const byId = {};
    manifest.samples.forEach(s => { byId[s.sample_id] = s; });
    (draft.annotations || []).forEach(entry => {
      if (!known.has(entry.sample_id)) { problems.push('draft has unknown sample ' + entry.sample_id); return; }
      const s = byId[entry.sample_id];
      if (entry.media_sha256 !== s.sha256_local) {
        problems.push('draft media hash mismatch for ' + entry.sample_id);
      }
      const ann = entry.annotation;
      if (!ann) return;
      if (ann.intervals) {
        ann.intervals.forEach((iv, i) => {
          if (iv.end_frame !== undefined && iv.end_frame_exclusive === undefined) {
            problems.push(entry.sample_id + ' interval ' + i +
                          ': legacy closed-end field without semantics; refusing to convert');
          }
        });
      }
    });
    return { valid: problems.length === 0, problems: problems };
  }

  const api = { CORE_VERSION, EXPORT_SCHEMA, DRAFT_SCHEMA, INTERVAL_SEMANTICS, STATES, EXACT_METHODS,
                LOCATOR_METHODS, isFiniteNumber, isFrame, timeFromFrame, boxHeight, clampBox,
                boxProblems, locatorProblems, validateAnnotation, deriveMode, buildExport,
                buildDraft, validateDraft, sampleDigest };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.AnnotationCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
