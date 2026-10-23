"""Adopt52's predeclared removal policy after explicit strong-control recoveries."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import sys
import time
import traceback
import numpy as np
from common import ROOT as ADMISSION,read,ref,save

ROOT=ADMISSION/'route_remove55';CONTROL=ADMISSION/'time_control54';DATA=ADMISSION/'time_control53'
SPORT=ADMISSION.parent/'highlight_source_admission_20261021_v1/matched_hl_pilot16'


def main():
    ROOT.mkdir()
    original=ADMISSION/'route_remove52/protocol.json'
    save(ROOT/'registration.json',dict(adopted_predeclared_policy=ref(original),
        original_control_failure=ref(ADMISSION/'route_remove52/failure.json'),
        no_rule_or_threshold_change=True,model_results_not_read_before_declaration=True,
        only_recovery='Wait for explicit remaining54 terminal, adopt its original first model answers',
        new_model_calls=0))
    started=time.monotonic()
    while not (CONTROL/'completion.json').exists():
        if (CONTROL/'failure.json').exists():raise RuntimeError('Authoritative strong control failed')
        if time.monotonic()-started>1200:raise TimeoutError('Bounded terminal wait elapsed; not an empty model result')
        time.sleep(5)
    terminal=read(CONTROL/'completion.json');strong=read(terminal['time_review']['path'])
    from time_control50_common import checked
    from time_control50_review import metrics
    source=read(DATA/'registration.json')['source'];stem=source['source']
    groups=np.load(checked(read(SPORT/'inputs'/stem/'acceptance.json')['groups']),allow_pickle=False)
    expert=np.load(SPORT/'outputs'/(stem+'_matched_HL.npy'),allow_pickle=False)
    route=next(row for row in read(ADMISSION/'semantic_route48/routing.json') if row['sid']=='S_'+stem)
    choices={}
    with np.load(terminal['selections']['path'],allow_pickle=False) as data:
        for control in ['B0','D8']:
            baseline=data[control+'_original_TIME'];choices[control]=(baseline & (expert[groups]>=.5)
                if route['source_routed'] else baseline.copy())
    with (ROOT/'choices.npz').open('xb') as out:np.savez_compressed(out,**choices)
    sys.path.insert(0,str(SPORT/'code'));from pilot15_common import original_targets
    labels=original_targets(source);results={}
    for control,chosen in choices.items():
        baseline=strong['metrics'][control]['original_TIME'];value=metrics(chosen,labels)
        results[control]=dict(original_TIME=baseline,source_remove=value,F1_delta=value['F1']-baseline['F1'])
    passed=all(row['F1_delta']>0 for row in results.values())
    save(ROOT/'completion.json',dict(state='STRONG_TIME_REMOVAL_SIGNAL_REQUIRES_PRODUCTION_SCOPE_REVIEW' if passed else 'STOP_FIXED_SOURCE_REMOVE52',
        adopted_original_policy=ref(original),metrics=results,no_labels_in_selector=True,
        exact40_47_external_control=False,other_routing_signals=strong['positive_gain_under_both_frozen_controls'],
        actual_new_model_calls=0,new_ZIP=0,baseline40_47_file_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_silent_fallback=True))
        raise
