"""Pure fixed temporal proxy; actual export/transfer admission belongs to its caller."""
from bisect import bisect_left
from fractions import Fraction as F
import random

from lead_guard_v2 import window_spans
from native_profile_04 import native64_windows, validate_original_origin, validate_reference_endpoints
from reference_intervals import paired_duration_metrics


def membership(points, spans):
    result=set()
    for first,last in spans:
        result.update(range(bisect_left(points,first),bisect_left(points,last)))
    return result


def source_comparison(prediction, reference):
    clock=prediction['native_clock']
    validate_original_origin(clock)
    human=reference['annotator_intervals_exact_seconds']
    validate_reference_endpoints(clock,human)
    plan=native64_windows(clock)
    windows=prediction['windows']
    if len(plan)!=len(windows) or any(F(a['start_exact'])!=F(b['start_exact']) or F(a['end_exact'])!=F(b['end_exact'])
                                   for a,b in zip(plan,windows)):
        raise ValueError('Prediction windows differ from actual native64 source plan')
    for window in windows:
        if window['original_status']!=('MODEL_OK' if window['segments'] else 'LEGAL_EMPTY'):
            raise ValueError('A failed model window cannot become an empty prediction')
    points=[F(x) for x in clock['original_exact_pts']]
    baseline,candidate=[window_spans(windows,arm) for arm in ('D8_BASELINE','L16')]
    base_frames,new_frames=membership(points,baseline),membership(points,candidate)
    if not base_frames<=new_frames:
        raise ValueError('Original D8 native frame removed')
    base=[paired_duration_metrics(baseline,span) for span in human]
    new=[paired_duration_metrics(candidate,span) for span in human]
    if any(a['recall']>b['recall'] for a,b in zip(base,new)):
        raise ValueError('An original annotator recall decreased')
    base_f1=sum((x['f1'] for x in base),F(0))/10
    new_f1=sum((x['f1'] for x in new),F(0))/10
    return dict(video_id=prediction['video_id'],group=prediction['group'],
        baseline_mean_f1_exact=str(base_f1),candidate_mean_f1_exact=str(new_f1),delta_exact=str(new_f1-base_f1),
        baseline_mean_f1=float(base_f1),candidate_mean_f1=float(new_f1),
        annotator_baseline=[{k:str(v) for k,v in x.items()} for x in base],
        annotator_candidate=[{k:str(v) for k,v in x.items()} for x in new],
        actual_interval_changed=baseline!=candidate,actual_native_frame_changed=base_frames!=new_frames,
        added_native_frames=len(new_frames-base_frames),baseline_frames_preserved=True,
        all_original_annotator_recalls_preserved=True,source_drop_gate=new_f1-base_f1>=-F(1,100))


def evaluate_group(predictions,references,group):
    if group not in ('screen','confirm'):
        raise ValueError('Undeclared external reference group')
    expected=12 if group=='screen' else 8
    rows=[row for row in predictions if row['group']==group]
    if len(rows)!=expected or len({x['video_id'] for x in rows})!=expected:
        raise ValueError('Frozen12/8 source denominator changed')
    results=[source_comparison(row,references[row['video_id']]) for row in rows]
    deltas=[F(row['delta_exact']) for row in results]
    macro=sum(deltas,F(0))/expected
    changed=sum(row['actual_interval_changed'] and row['actual_native_frame_changed'] for row in results)
    pass_gate=macro>=0 and changed>=3 and all(row['source_drop_gate'] for row in results)
    # Uncertainty is reported independently; it does not change the registered risk admission gate.
    rng=random.Random(20261013)
    means=sorted(float(sum((deltas[rng.randrange(expected)] for _ in range(expected)),F(0))/expected)
                 for _ in range(5000))
    return dict(status='PASS_FIXED_L16_TEMPORAL_PROXY_GROUP_NOT_CROP_OR_OFFICIAL_SCORE' if pass_gate else 'REJECT_FIXED_L16_TEMPORAL_PROXY_GROUP',
        group=group,sources=expected,macro_delta_exact=str(macro),macro_delta=float(macro),
        paired_bootstrap95=[means[125],means[4874]],bootstrap_seed=20261013,bootstrap_samples=5000,
        actual_changed_sources=changed,minimum_changed_sources=3,source_drop_limit_exact='1/100',
        original_fixed_gates_pass=pass_gate,rows=results,
        interpretation='Ten unmodified original manual summaries averaged, duration-F1 proxy; no native1fps truth or crop quality claim',
        new_model_calls=0,new_optimizer_updates=0,new_submission_zips=0)


def targeted_checks():
    from check_native_profile_04 import Container
    from types import SimpleNamespace as NS
    from native_profile_04 import measure_original_video
    clock=measure_original_video('synthetic',NS(__version__='synthetic_only',open=lambda p:Container()))
    windows=[dict(start_exact='0',end_exact='30',segments=[[4,20]],original_status='MODEL_OK'),
             dict(start_exact='30',end_exact='60',segments=[],original_status='LEGAL_EMPTY')]
    pred=dict(video_id='synthetic',group='screen',native_clock=clock,windows=windows)
    ref=dict(annotator_intervals_exact_seconds=[[['3','83/4']] for _ in range(10)])
    row=source_comparison(pred,ref)
    assert row['baseline_mean_f1_exact']=='140/141' and row['candidate_mean_f1_exact']=='1'
    assert row['delta_exact']=='1/141' and row['actual_native_frame_changed'] and row['source_drop_gate']
    nolead=[dict(start_exact='0',end_exact='30',segments=[[4,19]],original_status='MODEL_OK'),windows[1]]
    row=source_comparison(dict(pred,windows=nolead),ref)
    assert row['delta_exact']=='0' and not row['actual_interval_changed']
    short_clock=dict(clock)
    short_clock['physical_end_exact']='59'
    try:source_comparison(dict(pred,native_clock=short_clock),ref)
    except ValueError:pass
    else:raise AssertionError('Mismatched actual native source coverage accepted')
    print('PASS synthetic exact all-annotator F1/native preservation/no-change/window rejection checks; real quality comparisons0')


if __name__=='__main__':
    targeted_checks()
