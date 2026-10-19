"""New external-only CPU readout; not a selector, calibration or production job."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np

WORK = Path('/home/inspur/aic_video_work')
OLD = WORK/'temporal_selector_20261018_v1'
SUMMARY = WORK/'score_residual_execution_20261016_v2'
SEMANTIC = WORK/'semantic_context_residual_20261016_v1'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def bound(ref):
    p = Path(ref['path']).resolve()
    require(p.is_relative_to(WORK) and p.is_file(), 'Reference outside Linux project')
    require(sha(p) == ref['sha256'], 'Historical reference bytes changed: '+str(p))
    return p


def save(path, data):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def weighted_auc(scores, positive, total):
    """Tie-correct expected native-frame AUROC for soft multi-rater counts.

    A score belongs to one observed time group. Positive/negative weights count
    native frames averaged over ALL human summaries, not ordinary-event labels.
    """
    s, p, n = map(lambda x: np.asarray(x, dtype=np.float64), (scores, positive, total))
    require(s.ndim == p.ndim == n.ndim == 1 and s.shape == p.shape == n.shape,
            'Equal one-dimensional grouped counts required')
    require(np.isfinite(s).all() and np.isfinite(p).all() and np.isfinite(n).all()
            and (n > 0).all() and (p >= 0).all() and (p <= n).all(), 'Invalid score/count')
    negative = n-p
    if p.sum() == 0 or negative.sum() == 0:
        return None
    order = np.argsort(s, kind='stable')
    ordered = s[order]
    start = np.r_[0, np.flatnonzero(ordered[1:] != ordered[:-1])+1]
    pos = np.add.reduceat(p[order], start)
    neg = np.add.reduceat(negative[order], start)
    less_negative = np.cumsum(neg)-neg
    return float(np.sum(pos*(less_negative+0.5*neg))/(p.sum()*negative.sum()))


def matched_budget(scores, counts, target):
    """One diagnostic per-source budget copied from oldB0, never label chosen.

    Whole actual time groups; equal scores resolved by earlier native group.
    This is not a production rule or a tuned operating-point search.
    """
    s, n = np.asarray(scores), np.asarray(counts, dtype=np.int64)
    require(len(s) == len(n) and (n > 0).all() and 0 <= target <= n.sum(), 'Invalid budget')
    order = np.argsort(-s, kind='stable')
    amounts = np.r_[0, np.cumsum(n[order])]
    k = int(np.argmin(np.abs(amounts-int(target))))
    selected = np.zeros(len(s), dtype=bool)
    selected[order[:k]] = True
    return selected


def paired_f1(selected, labels):
    m = np.asarray(selected, dtype=bool)
    y = np.asarray(labels, dtype=bool)
    require(y.ndim == 2 and len(y) == len(m), 'Exact original native annotation length')
    truth = y.sum(0)
    den = int(m.sum())+truth
    result = np.divide(2*(m[:, None]&y).sum(0), den,
                       out=np.ones(len(truth), dtype=float), where=den != 0)
    return float(result.mean())


def score_diagnostics(scores, native_groups, labels, baseline):
    groups = np.asarray(native_groups, dtype=np.int64)
    n = np.bincount(groups, minlength=len(scores))
    require(len(n) == len(scores) and (n > 0).all(), 'No empty/unmapped time group')
    mean_reference = labels.mean(axis=1, dtype=np.float64)
    positive = np.bincount(groups, weights=mean_reference, minlength=len(scores))
    values = np.asarray(scores, dtype=np.float64)
    center = float(np.average(values, weights=n))
    mask = matched_budget(values, n, int(baseline.sum()))[groups]
    return dict(native_summary_selection_AUC=weighted_auc(values, positive, n),
                within_source_std=float(np.sqrt(np.average((values-center)**2, weights=n))),
                mean=center, minimum=float(values.min()), maximum=float(values.max()),
                baseline_budget_selected_native=int(mask.sum()),
                baseline_budget_paired_f1=paired_f1(mask, labels),
                is_new_candidate=False, uses_labels_for_selection=False,
                references_are_historical_summary_proxy=True)


def main(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU child must mask only itself')
    import torch
    torch.set_num_threads(2)
    sys.path.insert(0, str(OLD/'code'))
    from head import TemporalHead, predict
    require(not torch.cuda.is_initialized(), 'No GPU in external diagnostic')
    dst = root/'ranking_01'
    dst.mkdir(exist_ok=False)
    catalog = read(OLD/'assembled_external.json')
    train_reports = {arm: read(OLD/'training'/(arm+'_completion.json')) for arm in ['BCE', 'SET']}
    models = {}
    for arm, report in train_reports.items():
        m = TemporalHead(report['feature_dim'], report['hidden'])
        m.load_state_dict(torch.load(bound(report['weights']), map_location='cpu', weights_only=True))
        m.eval()
        models[arm] = m
    norm_ref = train_reports['BCE']['normalization']
    require(norm_ref == train_reports['SET']['normalization'], 'Shared original training normalization')
    norm = np.load(bound(norm_ref))
    rows = []
    for source in catalog['sources']:
        sid = source['id']
        data = np.load(bound(source['features']))
        native = np.load(bound(source['native']))
        label_file = SUMMARY/'label_arrays'/(source['name']+'.npy')
        require(sha(SUMMARY/'GT'/(source['name']+'.mat')) == source['annotation_sha256'], 'Original MAT identity')
        proofs = [json.loads(line) for line in (SUMMARY/'journal.jsonl').read_text().splitlines() if line.strip()]
        proof = [r for r in proofs if r.get('stage') == 'FIRST_NATIVE_HUMAN_MAT_READ' and r.get('path') == str(label_file)]
        require(len(proof) == 1 and sha(label_file) == proof[0]['sha256'], 'Adopt original annotation read')
        labels = np.load(label_file)>0
        baseline = native['baseline'].astype(bool)
        groups = data['native_group']
        require(labels.shape[0] == len(baseline) == len(groups) == source['native_frames'], 'No label padding/resampling')
        x = torch.from_numpy(((data['features']-norm['mean'])/norm['std']).astype(np.float32))
        probabilities = {arm: predict(model, x).numpy() for arm, model in models.items()}
        result = dict(id=sid, name=source['name'], role=source['role'],
                      source_sha256=source['source_sha256'],
                      old_B0_paired_f1=paired_f1(baseline, labels),
                      old_B0_coverage=float(baseline.mean()),
                      complete40_47_available=False, complete40_46_available=False,
                      new_8B_forwards=0, new_head_CPU_readouts=2,
                      head_readout={arm: score_diagnostics(p, groups, labels, baseline)
                                    for arm, p in probabilities.items()})
        semantic_path = SEMANTIC/'features'/sid/'yes_no.npy'
        semantic = np.load(semantic_path)
        original = native['groups']
        require(semantic.shape == (int(original.max())+1, 2) and np.isfinite(semantic).all(), 'Actual old yes/no dimensions')
        difference = semantic[:, 0]-semantic[:, 1]
        result['untrained_yes_minus_no'] = score_diagnostics(difference, original, labels, baseline)
        result['untrained_yes_minus_no']['meaning'] = 'Uncalibrated existing semantic-prompt logit difference, not P(highlight)'
        result['bindings'] = dict(source_features=source['features'], native=source['native'],
                                 original_annotation_array=dict(path=str(label_file), sha256=proof[0]['sha256']),
                                 yes_no=dict(path=str(semantic_path), sha256=sha(semantic_path)))
        np.savez(dst/(sid+'_readout.npz'), **probabilities, original_yes_minus_no=difference)
        rows.append(result)
        print(json.dumps(dict(stage='NEW_CPU_EXTERNAL_RANKING_DIAGNOSTIC',id=sid,role=source['role'])), flush=True)
    summary = {}
    for role in ['train', 'dev']:
        part = [r for r in rows if r['role'] == role]
        views = {}
        for name in ['BCE', 'SET', 'untrained_yes_minus_no']:
            values = [r['untrained_yes_minus_no'] if name == 'untrained_yes_minus_no' else r['head_readout'][name] for r in part]
            auc = [v['native_summary_selection_AUC'] for v in values if v['native_summary_selection_AUC'] is not None]
            views[name] = dict(macro_source_AUC=float(np.mean(auc)) if auc else None,
                               macro_matched_B0_budget_f1=float(np.mean([v['baseline_budget_paired_f1'] for v in values])),
                               within_source_variance=float(np.mean([v['within_source_std']**2 for v in values])),
                               between_source_variance=float(np.var([v['mean'] for v in values])),
                               sources_below_chance=sum(v['native_summary_selection_AUC'] is not None and v['native_summary_selection_AUC'] < .5 for v in values))
        summary[role] = dict(sources=[r['id'] for r in part],
                             old_B0_macro_f1=float(np.mean([r['old_B0_paired_f1'] for r in part])), views=views,
                             historical_labels_exposed=True, new_independent_confirmation=False)
    report = dict(status='COMPLETE_NEW_EXTERNAL_RANKING_DIAGNOSTIC_NOT_A_CANDIDATE',
                  utc=dt.datetime.now(dt.timezone.utc).isoformat(), runtime_sha256=sha(__file__),
                  summary=summary, sources=rows, new_8B_forwards=0, new_training_updates=0,
                  new_CPU_head_readouts=2*len(rows), parameters_or_thresholds_changed=False,
                  official_data_used=False, candidate_created=False,
                  purpose='Separate within-source ordering from source-level offsets without a new threshold search',
                  label_scope='Original all-rater public summary selection; unselected is not ordinary',
                  baseline_scope='Old external B0, not complete40.47; no spatial IoU or official joint metric')
    save(dst/'completion.json', report)
    print(json.dumps(dict(status=report['status'], summary=summary)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
