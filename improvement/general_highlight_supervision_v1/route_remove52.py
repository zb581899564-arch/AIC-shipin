"""Predeclare the third intrinsic binary-expert policy before strong-control quality is read."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import time
import traceback
import numpy as np
from common import ROOT as ADMISSION,read,ref,save

ROOT=ADMISSION/'route_remove52'
SPORT=ADMISSION.parent/'highlight_source_admission_20261021_v1/matched_hl_pilot16'
CONTROL=ADMISSION/'time_control51'


def main():
    ROOT.mkdir()
    save(ROOT/'protocol.json',dict(mechanism='Third predeclared routing policy: source-gated automatic binary-NHL suppression only',
        rule='If original globalK400 argmax is in frozen four-event set, keep baseline native frame iff frozen matched-HL expert sigmoid>=0.5; otherwise retain baseline',
        threshold='Intrinsic binary BCE operating point0.5, no search/calibration from new control or official scores',
        third_policy_registered_before_strong_control_quality_read=True,
        existing_strong_control_completion=(CONTROL/'completion.json').exists(),
        actual_prior_strong_model_answers=len(list((CONTROL/'outputs').glob('*/acceptance.json'))),
        all_previous_STOPs_unchanged=True,no_new_model_inference=True,no_automatic_production=True))
    started=time.monotonic()
    while not (CONTROL/'completion.json').exists():
        if (CONTROL/'failure.json').exists():raise RuntimeError('Actual strong control failed, do not infer empty results')
        if time.monotonic()-started>1200:raise TimeoutError('Bounded control wait elapsed, not classified as model failure')
        time.sleep(5)
    strong=read(CONTROL/'review.json')
    from time_control50_common import checked
    from time_control50_review import metrics
    source=read(CONTROL/'registration.json')['source'];stem=source['source']
    import sys
    sys.path.insert(0,str(SPORT/'code'));from pilot15_common import original_targets
    # Produce all choices using inference outputs only, before opening human labels.
    groups=np.load(checked(read(SPORT/'inputs'/stem/'acceptance.json')['groups']),allow_pickle=False)
    expert=np.load(SPORT/'outputs'/(stem+'_matched_HL.npy'),allow_pickle=False)
    route=next(r for r in read(ADMISSION/'semantic_route48/routing.json') if r['sid']=='S_'+stem)
    choices={}
    with np.load(CONTROL/'selections.npz',allow_pickle=False) as data:
        for control in ['B0','D8']:
            baseline=data[control+'_original_TIME']
            choices[control]=baseline & (expert[groups]>=.5) if route['source_routed'] else baseline.copy()
    with (ROOT/'choices.npz').open('xb') as out:np.savez_compressed(out,**choices)
    labels=original_targets(source);result={}
    for control,chosen in choices.items():
        baseline=strong['metrics'][control]['original_TIME'];value=metrics(chosen,labels)
        result[control]=dict(original_TIME=baseline,source_remove=value,F1_delta=value['F1']-baseline['F1'])
    passed=all(row['F1_delta']>0 for row in result.values())
    save(ROOT/'completion.json',dict(state='STRONG_TIME_REMOVAL_SIGNAL_REQUIRES_PRODUCTION_SCOPE_REVIEW' if passed else 'STOP_FIXED_SOURCE_REMOVE52',
        metrics=result,no_human_labels_in_selector=True,labels_only_in_metric=True,
        baseline40_47_file_unchanged=True,exact40_47_external_control=False,
        actual_new_model_calls=0,new_ZIP=0,
        prior_route_signals=strong['positive_gain_under_both_frozen_controls']))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_silent_fallback=True))
        raise
