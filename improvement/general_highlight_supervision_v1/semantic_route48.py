"""New mechanism: semantic routing of an existing narrow expert, not global replacement."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import json
import sys
import traceback
import numpy as np
import torch

from common import ROOT as ADMISSION,WORK,read,ref,save,fetch
from qv_common47 import ENGINEERING,checked
from qv_review47 import frame_f1

ROOT=ADMISSION/'semantic_route48'
SPORT=WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16'
EVENT_CLASSES=['long jump','pole vault','gymnastics tumbling','springboard diving']


def inventory():
    rows=[]
    for source in read(SPORT/'registration.json')['sources']:
        stem=source['source'];record=read(SPORT/'features'/stem/'acceptance.json')
        rows.append(dict(sid='S_'+stem,domain='sportclip',feature=record['features'],source=source))
    for row in read(SPORT/'transfer18/registration.json')['sources']:
        rows.append(dict(sid=row['source']['sid'],domain='external8',feature=row['feature'],source=row['source'],groups=row['groups']))
    for source in read(ADMISSION/'qv_pilot47/registration.json')['sources']:
        path=ADMISSION/'qv_pilot47/features'/source['sid']/'initial_all.npy'
        rows.append(dict(sid=source['sid'],domain='new_QV24',feature=ref(path),source=source))
    for row in rows:checked(row['feature'])
    return rows


def class_names():
    path=ROOT/'kinetics_classnames.json'
    fetch('https://dl.fbaipublicfiles.com/pyslowfast/dataset/class_names/kinetics_classnames.json',path,60000)
    mapping=read(path)
    mapping={name.strip('"'):index for name,index in mapping.items()}
    if len(mapping)!=400 or set(mapping.values())!=set(range(400)):
        raise ValueError('Official complete K400 class-to-index map differs')
    if any(name not in mapping for name in EVENT_CLASSES):
        raise ValueError('Predeclared event names absent; no metric-driven replacement classes')
    return mapping


def first_projection(rows, mapping):
    receipt=read(ENGINEERING/'weight_acceptance.json');checked(receipt)
    state=torch.load(receipt['path'],map_location='cpu',weights_only=True)['model_state']
    weight,bias=state['blocks.6.proj.weight'],state['blocks.6.proj.bias']
    if tuple(weight.shape)!=(400,2048) or tuple(bias.shape)!=(400,):raise ValueError('Original classifier head differs')
    inverse={v:k for k,v in mapping.items()};target={mapping[k] for k in EVENT_CLASSES}
    results=[]
    for row in rows:
        values=np.load(checked(row['feature']),allow_pickle=False)
        if values.ndim!=2 or values.shape[1]!=2048:raise ValueError('Original pooled visual feature shape differs')
        with torch.inference_mode():
            logits=torch.nn.functional.linear(torch.from_numpy(values),weight,bias)
            probabilities=logits.softmax(dim=-1).numpy()
        path=ROOT/(row['sid']+'_K400.npy')
        with path.open('xb') as out:np.save(out,probabilities,allow_pickle=False)
        # Independent float64 first-row softmax, not another backbone or model call.
        raw=values[0].astype(np.float64)@weight.numpy().astype(np.float64).T+bias.numpy()
        expected=np.exp(raw-raw.max());expected/=expected.sum()
        if not np.allclose(expected,probabilities[0],atol=2e-6,rtol=2e-5):raise ValueError('Independent classifier arithmetic differs')
        cells=np.isin(probabilities.argmax(axis=1),list(target))
        global_id=int(probabilities.mean(axis=0).argmax())
        result=dict(sid=row['sid'],domain=row['domain'],probabilities=ref(path),
            global_top1=inverse[global_id],source_routed=global_id in target,
            routed_cells=np.flatnonzero(cells).tolist(),total_cells=len(cells))
        results.append(result)
        print('SEMANTIC_ROUTE',row['sid'],result['global_top1'],result['source_routed'],int(cells.sum()),flush=True)
    return results


def sport_metrics(row, routing):
    sys.path.insert(0,str(SPORT/'code'))
    from pilot15_common import original_targets
    source=row['source'];stem=source['source'];labels=original_targets(source);known=labels>=0
    groups=np.load(checked(read(SPORT/'inputs'/stem/'acceptance.json')['groups']),allow_pickle=False)
    old=np.load(SPORT/'outputs'/(stem+'_old_summary.npy'),allow_pickle=False)
    expert=np.load(SPORT/'outputs'/(stem+'_matched_HL.npy'),allow_pickle=False)
    coverage=read(SPORT/'review.json')['training_known_positive_coverage'];count=round(int(known.sum())*coverage)
    baseline=np.zeros(len(labels),dtype=bool)
    native=np.flatnonzero(known);baseline[native[np.argsort(-old[groups[known]],kind='stable')[:count]]]=True
    source_choice=baseline.copy()
    if routing['source_routed']:
        source_choice[:]=False;source_choice[native[np.argsort(-expert[groups[known]],kind='stable')[:count]]]=True
    cell_domain=np.isin(groups,routing['routed_cells'])
    supplemental=baseline | (cell_domain & (expert[groups]>=.5))
    metrics={name:frame_f1(chosen[known],labels[known,None].astype(bool))
        for name,chosen in [('old_summary',baseline),('source_route',source_choice),('cell_supplement',supplemental)]}
    return dict(sid=row['sid'],role=source['role'],metrics=metrics,
        cell_added=int((supplemental & ~baseline & known).sum()),
        explicit_NHL_added=int((supplemental & ~baseline & (labels==0)).sum()),
        uncertainty_excluded=True,not_exact_TIME_or40_47_control=True)


def external_metrics(row,routing):
    source=row['source'];sid=row['sid']
    with np.load(checked(source['comparison_ref']),allow_pickle=False) as data:
        raw=data['labels'];baseline=data['baseline']
        if not np.isin(raw,[0,1]).all() or not np.isin(baseline,[0,1]).all():raise ValueError('Original bridge label values differ')
        labels=raw.astype(bool);baseline=baseline.astype(bool)
    groups=np.load(checked(row['groups']),allow_pickle=False)
    expert=np.load(SPORT/'transfer18/outputs'/(sid+'_correct.npy'),allow_pickle=False)
    source_choice=baseline.copy()
    if routing['source_routed']:
        source_choice[:]=False;source_choice[np.argsort(-expert[groups],kind='stable')[:int(baseline.sum())]]=True
    supplemental=baseline | (np.isin(groups,routing['routed_cells']) & (expert[groups]>=.5))
    metrics={name:frame_f1(chosen,labels) for name,chosen in
             [('original_TIME',baseline),('source_route',source_choice),('cell_supplement',supplemental)]}
    return dict(sid=sid,metrics=metrics,source_change=int(np.logical_xor(source_choice,baseline).sum()),
                cell_added=int((supplemental & ~baseline).sum()),not_blind=True)


def main():
    ROOT.mkdir();torch.set_num_threads(2)
    rows=inventory()
    save(ROOT/'protocol.json',dict(mechanism='Semantically route an existing athlete-phase expert, preserving default TIME elsewhere; no global replacement',
        fixed_event_names=EVENT_CLASSES,source_route='Mean K400 posterior global argmax in fixed event set; same original selected count',
        cell_supplement='Cell K400 argmax in fixed event set AND trained binary-HL sigmoid>=0.5; retain all original baseline frames',
        no_class_threshold_or_test_source_scan=True,no_new_backbone_or_temporal_inference=True,
        first400_class_projection_on_cached_original_features=True,no_training=True,
        actual_full_parameters=8816809946,old_expert_global_transfer_STOP_unchanged=True,
        study_limits='Sports held sport and all historical external metrics already exposed; no claim of new blind test',
        evidence_required='Must retain narrow sport benefit and no macro degradation on complete historical8; then exact40.47 bridge and source isolation before production',
        no_automatic426_or_package=True))
    save(ROOT/'registration.json',dict(sources=rows,code=ref(Path(__file__)),
        protected_baseline=read(ADMISSION/'media24/registration.json')['protected_baseline']))
    mapping=class_names();routed=first_projection(rows,mapping)
    save(ROOT/'routing.json',routed);by_id={row['sid']:row for row in routed}
    sports=[sport_metrics(row,by_id[row['sid']]) for row in rows if row['domain']=='sportclip']
    external=[external_metrics(row,by_id[row['sid']]) for row in rows if row['domain']=='external8']
    macro={name:float(np.mean([r['metrics'][name] for r in external])) for name in external[0]['metrics']}
    held=next(row for row in sports if row['role']=='held_sport')
    candidates={name:dict(narrow_gain=held['metrics'][name]-held['metrics']['old_summary'],
        complete_external8_delta=macro[name]-macro['original_TIME'],
        external_changes=sum(row['source_change'] if name=='source_route' else row['cell_added'] for row in external))
        for name in ['source_route','cell_supplement']}
    signal=any(row['narrow_gain']>0 and row['complete_external8_delta']>=0 for row in candidates.values())
    save(ROOT/'review.json',dict(state='ROUTING_SIGNAL_REQUIRES_EXACT40_47_BRIDGE' if signal else 'STOP_FIXED_SEMANTIC_ROUTE48',
        sports=sports,external_sources=external,external8_macro_F1=macro,candidates=candidates,
        QV_routing_diagnostic=[r for r in routed if r['domain']=='new_QV24'],
        QV_route_activation_not_human_false_positive_ground_truth=True,
        no_new_I3D_UMT_or8B_forward=True,new_classifier_cells=sum(r['total_cells'] for r in routed),
        CPU_projection_only=True,no_official_joint_score=True,no_automatic_production=True))
    checked(read(ROOT/'registration.json')['protected_baseline'])
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],new_GPU=0,new_ZIP=0,
        review=ref(ROOT/'review.json'),baseline_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_silent_fallback=True))
        raise
