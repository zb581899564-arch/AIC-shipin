"""One source-relative temporal readout on already accepted external features."""
import argparse
import os
from pathlib import Path
import sys
import time
import traceback
from fractions import Fraction

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
from ranking_diagnostic import read, bound, save, sha, require, paired_f1, weighted_auc, matched_budget
from relative_time_rank import fit, predict, select_window, apply_selection


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only this CPU child masks CUDA')
    import datetime as dt
    import numpy as np
    import torch
    import resource
    torch.set_num_threads(2)
    reg = read(root/'relative_time_registration_15.json')
    require(reg['schema'] == 'SOURCE_CENTERED_TIME_RANK32_SINGLE_VERSION', 'Explicit one-version entry')
    for name, digest in reg['new_code'].items():
        require(sha(Path(__file__).parent/name) == digest, 'Registered relative temporal runtime changed')
    bound(reg['ranking_helper'])
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00')),
            'Within authorized 10h window')
    out = root/'relative_time_15'
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(registration=ref(root/'relative_time_registration_15.json'),
                               pid=os.getpid(), started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                               new_8B_forwards=0, new_optimizer_updates=0))
    started = time.monotonic()
    completed = []
    try:
        catalog = read(bound(reg['assembled_external']))
        prior = read(bound(reg['original_ranking_diagnostic']))
        adoption = {s['id']: s for s in prior['sources']}
        require(catalog['status'] == 'PASS_UNIQUE_NATIVE_GROUPS_OVERLAP_MEAN' and len(catalog['sources']) == 25,
                'Exact accepted historical external25 source catalog')
        for gate in reg['original_feature_output_QA']:
            require(read(bound(gate))['status'] == 'PASS_ALL_FIRST_OUTPUT_QA_WITHOUT_NEW_FORWARD',
                    'Adopt actual once-completed original feature QA, do not replay')
        train_ids = [s['id'] for s in catalog['sources'] if s['role'] == 'train']
        dev_ids = [s['id'] for s in catalog['sources'] if s['role'] == 'dev']
        require(len(train_ids) == 20 and len(dev_ids) == 5 and len(set(train_ids + dev_ids)) == 25,
                'Frozen historical 20/5 roles; not a new blind split')
        require(not ({s['source_sha256'] for s in catalog['sources'] if s['role'] == 'train'} &
                     {s['source_sha256'] for s in catalog['sources'] if s['role'] == 'dev'}),
                'Known source byte identities must be split-disjoint')
        samples = {}
        native = {}
        labels = {}
        clocks = {}
        identities = {}
        applicability = []
        for source in catalog['sources']:
            sid = source['id']; old = adoption[sid]
            require(old['source_sha256'] == source['source_sha256'] and old['role'] == source['role'] and
                    old['bindings']['source_features'] == source['features'] and
                    old['bindings']['native'] == source['native'], 'Adopt exact source feature/native identities')
            feature_path = bound(source['features']); native_path = bound(source['native'])
            label_ref = old['bindings']['original_annotation_array']
            with np.load(feature_path, allow_pickle=False) as f:
                x = f['features'].copy(); groups = f['native_group'].copy()
                counts_windows = f['window_counts'].copy()
            with np.load(native_path, allow_pickle=False) as f:
                old_groups = f['groups'].copy(); baseline = f['baseline'].copy()
            y_raw = np.load(bound(label_ref), allow_pickle=False)
            require(y_raw.ndim == 2 and y_raw.shape[0] == len(groups) == source['native_frames'] and
                    np.isfinite(y_raw).all() and y_raw.shape[1] > 0,
                    'No missing reviewer labels silently treated as unselected; no padding/truncation')
            require(x.dtype == np.float32 and x.shape == (source['groups'], 8192) and
                    np.isfinite(x).all() and np.all(counts_windows > 0) and
                    np.array_equal(groups, old_groups // 2) and baseline.dtype == np.bool_,
                    'Actual accepted overlapping-window temporal features and native ownership')
            y = y_raw > 0
            counts = np.bincount(groups, minlength=len(x))
            require((counts > 0).all() and len(counts) == len(x), 'No unobserved/empty group')
            positive = np.bincount(groups, weights=y.mean(1), minlength=len(x))
            samples[sid] = dict(features=x, native_counts=counts, softvote=positive/counts)
            native[sid] = dict(groups=groups, old_groups=old_groups, baseline=baseline)
            labels[sid] = y
            clock = read(bound(source['clock']))
            require(clock['source_sha256'] == source['source_sha256'] and clock['n_frames'] == len(groups),
                    'Original native clock/source identity')
            clocks[sid] = clock
            identities[sid] = dict(source=source, original_annotation_array=label_ref)
            # Scores equal zero here: applicability only, not a fit or result selection.
            app = select_window(np.zeros(len(x)), groups, old_groups, baseline)
            applicability.append(dict(id=sid, role=source['role'],
                complete_baseline_anchor_windows=len(app['anchors']),
                complete_nonoverlap_candidate_windows=len(app['candidates']),
                comparison_baseline='ORIGINAL_EXTERNAL_B0_NOT_COMPLETE40.47'))
        save(out/'input_adoption.json', dict(status='BOUND_PREVIOUSLY_ACCEPTED_EXTERNAL_FEATURES_ONLY',
             catalog=reg['assembled_external'], sources=identities, original_QA=reg['original_feature_output_QA'],
             new_processor_calls=0, new_decode=0, old_QA_repeated=False, official_data_read=False,
             applicability=applicability))
        state, report = fit(samples, train_ids)
        checkpoint = out/'final_ranker.npz'
        with checkpoint.open('xb') as stream:
            np.savez(stream, **state)
        with np.load(checkpoint, allow_pickle=False) as f:
            restored = {k: f[k] for k in f.files}
        save(out/'fit_report.json', dict(report=report, checkpoint=ref(checkpoint),
             train_ids=train_ids, dev_ids=dev_ids, fit_count=1, closed_form_fits=1,
             actual_stored_numeric_elements=sum(np.asarray(v).size for v in state.values()),
             new_optimizer_updates=0, new_8B_forwards=0,
             target='Source-native-frame-weighted all-rater summary vote; unselected is not ordinary'))
        scores = {}
        for sid, sample in samples.items():
            score = predict(state, sample['features'], sample['native_counts'])
            restored_score = predict(restored, sample['features'], sample['native_counts'])
            require(np.array_equal(score, restored_score) and np.isfinite(score).all(),
                    'Exact actual save/reload prediction, finite new source-relative scores')
            path = out/(sid+'_scores.npy')
            with path.open('xb') as stream:
                np.save(stream, score, allow_pickle=False)
            scores[sid] = score
            completed.append(dict(id=sid, scores=ref(path)))
        save(out/'readout_completion.json', dict(status='ALL25_NEW_SOURCE_RELATIVE_READOUTS_AND_RELOAD_COMPLETE',
             sources=completed, checkpoint=ref(checkpoint), new_model_forward=0))
        rows = []
        for source in catalog['sources']:
            sid = source['id']; sample = samples[sid]; n = native[sid]; y = labels[sid]; score = scores[sid]
            decision = select_window(score, n['groups'], n['old_groups'], n['baseline'])
            mask = apply_selection(n['baseline'], decision)
            require(np.all(mask[n['baseline']]), 'Add-only fixed policy must retain every baseline frame')
            matched = matched_budget(score, sample['native_counts'], int(n['baseline'].sum()))[n['groups']]
            positive = sample['softvote'] * sample['native_counts']
            candidate_span = None
            if decision['selected'] is not None:
                v = decision['selected']; lo, hi = v['native_start'], v['native_end_exclusive']
                clock = clocks[sid]; pts = clock['normalized_exact_pts']
                end = pts[hi] if hi < len(pts) else clock['physical_end_exact']
                candidate_span = dict(native_start=lo, native_end_exclusive=hi, start_exact=pts[lo], end_exact=end,
                                      duration_exact=str(Fraction(end)-Fraction(pts[lo])))
            before = paired_f1(n['baseline'], y); after = paired_f1(mask, y)
            policy_path = out/(sid+'_policy.json')
            save(policy_path, dict(source_sha256=source['source_sha256'], **decision,
                                  selected_native_span=candidate_span))
            rows.append(dict(id=sid, role=source['role'], name=source['name'],
                source_sha256=source['source_sha256'], paired_F1_before=before, paired_F1_after=after,
                paired_F1_delta=after-before, baseline_native_frames=int(n['baseline'].sum()),
                added_native_frames=int(mask.sum()-n['baseline'].sum()), removed_native_frames=0,
                source_AUC=weighted_auc(score, positive, sample['native_counts']),
                matched_originalB0_budget_paired_F1=paired_f1(matched, y), policy=ref(policy_path),
                decision=decision['abstain_reason'] or decision['status'], selected_native_span=candidate_span,
                baseline_scope='Historical external original B0; NOT complete40.47'))
        summary = {}
        for role in ('train', 'dev'):
            part = [r for r in rows if r['role'] == role]
            auc = [r['source_AUC'] for r in part if r['source_AUC'] is not None]
            summary[role] = dict(sources=len(part), source_AUC_mean=float(np.mean(auc)) if auc else None,
                paired_F1_before=float(np.mean([r['paired_F1_before'] for r in part])),
                paired_F1_after=float(np.mean([r['paired_F1_after'] for r in part])),
                paired_F1_delta=float(np.mean([r['paired_F1_delta'] for r in part])),
                matched_originalB0_budget_F1=float(np.mean([r['matched_originalB0_budget_paired_F1'] for r in part])),
                sources_with_addition=sum(r['added_native_frames'] > 0 for r in part),
                added_native_frames=sum(r['added_native_frames'] for r in part),
                worst_source_F1_delta=min(r['paired_F1_delta'] for r in part))
        save(out/'completion.json', dict(status='COMPLETE_ONE_NEW_RELATIVE_TEMPORAL_READOUT_DIAGNOSTIC',
             summary=summary, sources=rows, checkpoint=ref(checkpoint), train_ids=train_ids, dev_ids=dev_ids,
             original_40_47_external_complete=False, historical_exposure=True, new_blind_sources=0,
             fixed_policy_not_confidence_calibrated=True, multiple_max_candidate_count_risk=True,
             new_PCA_fits=1, new_closed_form_fits=1, new_optimizer_updates=0, new_8B_calls=0,
             elapsed_seconds=time.monotonic()-started, max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             official_joint_metric_computed=False, production_admitted=False))
        require(not torch.cuda.is_initialized(), 'CPU readout must never initialize CUDA')
        print(summary, flush=True)
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
             completed_readouts=completed, preserve_all_success=True, no_automatic_retry=True))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    run(p.parse_args().root)
