"""Fixed salience-weighted source-internal representative coverage; no fitting."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import sys
import json
from pathlib import Path
from fractions import Fraction as F
from bisect import bisect_left
import numpy as np

W = Path('/home/inspur/aic_video_work')
ROOT = W/'coverage_event_20261018_v1'
CAL = W/'calibrated_event_20261018_v1'
EVENT = W/'meaningful_residual_20261018_v1'
sys.path.insert(0, str(CAL/'code_v1'))
from calibrate import read, save, ref, bound, require, utc, deadline
from event_features import projected, proposals, metric
sys.path.insert(0, str(CAL/'source_normalized_code_v2'))
from multiple_choice import multiple_choice_knapsack


def sigmoid(score):
    return 1/(1+np.exp(-np.clip(np.asarray(score, float), -30, 30)))


def coverage_from_kernel(kernel, groups, baseline, candidates, salience):
    m = len(salience)
    require(kernel.shape == (m, m) and np.isfinite(kernel).all() and
            np.all((kernel >= 0) & (kernel <= 1)), 'Finite nonnegative cosine kernel')
    require(baseline.dtype == np.bool_ and len(groups) == len(baseline) and
            groups.min() == 0 and groups.max()+1 == m, 'Actual occupied native time groups')
    count = np.bincount(groups, minlength=m)
    require((count > 0).all() and np.isfinite(salience).all() and
            (salience > 0).all(), 'Positive native-frame and importance weights')
    weights = count*salience
    denominator = weights.sum()
    base_ids = np.unique(groups[baseline])
    base_max = kernel[:, base_ids].max(1) if len(base_ids) else np.zeros(m)
    gains, fractions = [], []
    for candidate in candidates:
        left, right = candidate['left'], candidate['right']
        added = ~baseline[left:right]
        require(int(added.sum()) == candidate['added_frames'] and added.any(),
                'Real unique native cost and nonempty action')
        ids, added_count = np.unique(groups[left:right][added], return_counts=True)
        event_max = kernel[:, ids].max(1)
        # Positive residual sum avoids subtracting two nearly equal coverages.
        gains.append(float(weights@np.maximum(0, event_max-base_max)/denominator))
        fractions.append(float(np.mean(added_count/count[ids])))
    full = kernel.max(1)
    return np.asarray(gains), dict(baseline_coverage=float(weights@base_max/denominator),
        residual_upper_bound=float(weights@np.maximum(0, full-base_max)/denominator),
        groups=m, selected_groups=len(base_ids), positive_candidates=int(np.sum(np.asarray(gains)>0)),
        zero_candidates=int(np.sum(np.asarray(gains)==0)), touched_group_added_fraction=fractions,
        importance_is_uncalibrated_rank_weight=True, null_is_not_harmful_event_detection=True)


def infer(language, score, groups, baseline, candidates, pca):
    require(language.shape == (len(score), 4096) and np.isfinite(language).all() and
            np.isfinite(score).all(), 'Complete accepted BASE language and semantic rows')
    p = projected(language, pca)
    norm = np.linalg.norm(p, axis=1)
    unit = np.divide(p, norm[:, None], out=np.zeros_like(p), where=norm[:, None]>1e-12)
    kernel = np.clip(unit@unit.T, 0, 1)
    gains, stats = coverage_from_kernel(kernel, groups, baseline, candidates, sigmoid(score))
    # New-purpose independent native expansion on first/middle/last actions.
    base_ids = np.unique(groups[baseline])
    base_max = kernel[:, base_ids].max(1) if len(base_ids) else np.zeros(len(score))
    for index in sorted({0, len(candidates)//2, len(candidates)-1}) if candidates else []:
        c = candidates[index]
        ids = np.unique(groups[c['left']:c['right']][~baseline[c['left']:c['right']]])
        residual = np.maximum(0, kernel[:, ids].max(1)-base_max)
        native_importance = sigmoid(score)[groups]
        direct = float(np.sum(native_importance*residual[groups])/native_importance.sum())
        require(abs(direct-gains[index]) < 2e-12, 'First independent expanded-native coverage output')
    stats['zero_norm_groups'] = int(np.sum(norm<=1e-12))
    stats['independent_native_expansion'] = True
    return gains, stats


def checks():
    g = np.array([0, 0, 1, 1], np.int64)
    b = np.array([1, 0, 0, 0], bool)
    c = [dict(left=1, right=2, added_frames=1), dict(left=2, right=3, added_frames=1),
         dict(left=2, right=4, added_frames=2)]
    gain, stats = coverage_from_kernel(np.eye(2), g, b, c, np.ones(2))
    require(np.array_equal(gain, [0, .5, .5]), 'Duplicate group no gain; same new group ignores cost by explicit abstraction')
    result = multiple_choice_knapsack({'synthetic': [dict(candidate_index=i, added_frames=v['added_frames'], predicted_gain=float(gain[i])) for i, v in enumerate(c) if gain[i]>0]}, 2)
    require(result['chosen'] == {'synthetic': 1} and result['total_cost'] == 1,
            'Coverage integration picks cheaper equal-utility alias, not two actions per source')
    zero, _ = coverage_from_kernel(np.zeros((2, 2)), g, b, c, np.ones(2))
    require(not zero.any(), 'Zero-vector kernel saturates at zero, no invented signal')
    full, _ = coverage_from_kernel(np.eye(2), g, np.ones(4, bool), [], np.ones(2))
    require(len(full) == 0, 'Fully selected source has no added actions')
    empty, _ = coverage_from_kernel(np.eye(2), g, np.zeros(4, bool), [dict(left=0, right=4, added_frames=4)], np.array([1., 3.]))
    require(np.array_equal(empty, [1.]), 'Empty selected set uses zero coverage and full event reaches one')
    require(np.all(gain >= 0) and np.all(gain <= stats['residual_upper_bound']+1e-12),
            'Facility gains bounded by actual residual, not expected F1')
    save(ROOT/'targeted_checks.json', dict(status='PASS6_NEW_COVERAGE_AND_SOLVER_INTEGRATION_CHECKS', old_solver_tests_repeated=False, utc=utc()))


def catalogue():
    old = read(EVENT/'registration.json')
    controls = {x['sid']:x for x in read(EVENT/'semantic_event_01/adopted_evaluation.json')['sources']}
    result = []
    for source in old['sources']:
        if source['group'] == 'check':
            result.append(dict(**source, cohort='exposed8', baseline_metric=controls[source['sid']]['baseline'],
                old_semantic_metric=controls[source['sid']]['candidate'], references_ref=None))
    for cohort, pipeline, reference_path, comparison_path in (
        ('exposed4', CAL/'confirm4_02', CAL/'confirm4_reference_01/references.json', CAL/'new4_comparison_01/result.json'),
        ('exposed4b', CAL/'confirm4b_01', CAL/'confirm4b_01/references/references.json', CAL/'new4b_comparison_01/result.json')):
        done = read(pipeline/'stages/finalize/completion.json')
        require(done['status']=='PASS' and done['labels_read'] is False, 'Adopt successful real model/outputQA, no reruns')
        old_rows = {x['sid']:x for x in read(comparison_path)['sources']}
        for source in done['sources']:
            result.append(dict(**source, cohort=cohort, baseline_metric=old_rows[source['sid']]['baseline'],
                old_semantic_metric=old_rows[source['sid']]['results']['semantic'], references_ref=ref(reference_path)))
    require(len(result)==16 and len({x['sid'] for x in result})==16, 'Explicit all16 already exposed diagnostic sources')
    return result


def labels_for(source, clock, native):
    if source['references_ref'] is None:
        return native['labels']
    values = {x['name']:x for x in read(bound(source['references_ref']))}[source['name']]
    points = list(map(F, clock['normalized_exact_pts']))
    labels = np.zeros((len(points), 10), bool)
    require(len(values['annotator_intervals_exact_seconds'])==10, 'All original10 reviewers')
    for reviewer, spans in enumerate(values['annotator_intervals_exact_seconds']):
        for start, stop in spans:
            require(F(0)<=F(start)<F(stop)<=F(clock['physical_end_exact']), 'Original untouched native reference bounds')
            labels[bisect_left(points, F(start)):bisect_left(points, F(stop)), reviewer] = True
    return labels


def evaluate():
    deadline()
    registration = read(ROOT/'registration.json')
    for dependency in registration['method_refs']:
        bound(dependency)
    checks()
    pca = dict(np.load(bound(registration['pca_ref'])))
    require(set(pca)=={'pca_mean','pca_components'}, 'Only adopted frozen PCA, no ridge/calibration/memory state')
    items, catalogue_rows = [], catalogue()
    for source in catalogue_rows:
        native = np.load(bound(source['data_ref']))
        clock = read(bound(source['clock_ref']))
        baseline, groups, score = native['baseline'], native['groups'], native['semantic_score']
        require(len(clock['normalized_exact_pts'])==len(groups)==len(baseline), 'Native source and group mapping')
        language = np.load(bound(source['language_ref']))
        candidates = proposals(clock, baseline)
        gain, stats = infer(language, score, groups, baseline, candidates, pca)
        # Match original D: sigmoid of native mean, not mean of sigmoid.
        control = np.asarray([float(sigmoid(np.mean(score[groups[c['left']:c['right']]][~baseline[c['left']:c['right']]]))) for c in candidates])
        output = ROOT/'diagnostic_inputs'/(source['sid']+'.npz')
        output.parent.mkdir(exist_ok=True)
        with output.open('xb') as f:
            np.savez(f, coverage_gain=gain, semantic_control_value=control)
        items.append(dict(source=source, native=native, clock=clock, baseline=baseline, groups=groups,
                          candidates=candidates, gain=gain, control=control, stats=stats, inference_ref=ref(output)))
    selections = {}
    for cohort in ('exposed8', 'exposed4', 'exposed4b'):
        group = [x for x in items if x['source']['cohort']==cohort]
        budget = sum(int(x['baseline'].sum()) for x in group)//10
        selections[cohort] = {}
        for name, key in (('coverage', 'gain'), ('semantic_exact', 'control')):
            options = {x['source']['sid']:[dict(candidate_index=i, added_frames=c['added_frames'], predicted_gain=float(x[key][i])) for i, c in enumerate(x['candidates']) if x[key][i]>0] for x in group}
            selections[cohort][name] = multiple_choice_knapsack(options, budget)
    frozen_rows = []
    for x in items:
        source, masks, choices = x['source'], {}, {}
        for name in ('coverage', 'semantic_exact'):
            index = selections[source['cohort']][name]['chosen'].get(source['sid'])
            mask = x['baseline'].copy()
            choices[name] = None if index is None else x['candidates'][index]
            if index is not None:
                c = x['candidates'][index]
                mask[c['left']:c['right']] = True
            require(np.all(x['baseline']<=mask), 'Every original native baseline frame protected')
            masks[name] = mask
        out = ROOT/'diagnostic_inputs'/(source['sid']+'_masks.npz')
        with out.open('xb') as f:
            np.savez(f, **masks)
        frozen_rows.append(dict(sid=source['sid'], cohort=source['cohort'], choices=choices, output_ref=ref(out), inference_ref=x['inference_ref'], stats=x['stats']))
    save(ROOT/'outputs_frozen_before_metrics.json', dict(status='PASS16_FIXED_COVERAGE_OUTPUTS_BEFORE_CURRENT_METRICS', sources=frozen_rows, selections=selections, label_values_read_for_new_inference=False, prior_metric_exposure=True, utc=utc()))
    rows = []
    for x, frozen in zip(items, frozen_rows):
        source = x['source']
        labels = labels_for(source, x['clock'], x['native'])
        require(labels.dtype==np.bool_ and len(labels)==len(x['baseline']), 'Original full-source known-rater domain')
        masks = np.load(bound(frozen['output_ref']))
        results = {name:metric(masks[name], labels) for name in ('coverage', 'semantic_exact')}
        added = masks['coverage'] & ~x['baseline']
        rows.append(dict(sid=source['sid'], cohort=source['cohort'], baseline=source['baseline_metric'], results=results,
            delta=results['coverage']['f1']-source['baseline_metric']['f1'],
            minus_semantic_exact=results['coverage']['f1']-results['semantic_exact']['f1'],
            minus_old_semantic=results['coverage']['f1']-source['old_semantic_metric']['f1'],
            added_frames=int(added.sum()), newframe_reviewer_precision=None if not added.any() else float(labels[added].mean()),
            stats=x['stats'], choices=frozen['choices']))
    def summary(group):
        return dict(sources=len(group), macro_delta=float(np.mean([x['delta'] for x in group])),
                    improved=sum(x['delta']>0 for x in group), decreased=sum(x['delta']<0 for x in group),
                    changed=sum(x['added_frames']>0 for x in group), added_frames=sum(x['added_frames'] for x in group),
                    worst_delta=min(x['delta'] for x in group), macro_minus_semantic_exact=float(np.mean([x['minus_semantic_exact'] for x in group])),
                    macro_minus_old_semantic=float(np.mean([x['minus_old_semantic'] for x in group])))
    summaries = {name:summary([x for x in rows if x['cohort']==name]) for name in selections}
    summaries['all16'] = summary(rows)
    save(ROOT/'result.json', dict(status='ONE_FIXED_SALIENCE_WEIGHTED_COVERAGE_EXPOSED_DEVELOPMENT_REVIEW_REQUIRED', summary=summaries, sources=rows,
        new_fit=0, new_8B_calls=0, baseline_metrics_adopted_not_repeated=True, original_three_risk_packages_unchanged=True,
        official_joint_score_estimate=None, blind_confirmation=False, no_post_metric_variants=True,
        limitations=registration['limitations'], utc=utc()))
    save(ROOT/'completion.json', dict(status='COMPLETED_SINGLE_COVERAGE_DEVELOPMENT_NO_AUTO_PRODUCTION', result_ref=ref(ROOT/'result.json'), utc=utc()))
    print(json.dumps(summaries), flush=True)


if __name__ == '__main__':
    try:
        evaluate()
    except BaseException as error:
        import traceback
        save(ROOT/('failure_'+str(os.getpid())+'.json'), dict(error=repr(error), traceback=traceback.format_exc(), successes_preserved=True, utc=utc()))
        raise
