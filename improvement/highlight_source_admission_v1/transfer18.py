"""Frozen matched-HL model transfer to all eight already-cached VideoXum sources."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PILOT=Path('/home/inspur/aic_video_work/highlight_source_admission_20261021_v1/matched_hl_pilot16')
sys.path.insert(0,str(PILOT/'code'))
from pilot15_common import WORK,ENGINEERING,read,checked,ref,save

ROOT=PILOT/'transfer18'
OLD=ENGINEERING/'crossdata12'
RUN=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
PY=WORK/'env/qwen3vl_isolated_20260910/bin/python'
JOB='upm_matched_HL_frozen_videoxum8_transfer_20261021_v18'


def preflight():
    ROOT.mkdir()
    sources=[row for row in read(OLD/'registration.json')['sources'] if row['role']=='held_dataset']
    if len(sources)!=8:raise ValueError('Original full eight-source dataset changed')
    rows=[]
    for source in sources:
        feature=read(OLD/'features'/source['sid']/'acceptance.json')['features'];checked(feature)
        rows.append(dict(source=source,feature=feature,groups=ref(OLD/'inputs'/source['sid']/'groups.npy')))
    checkpoint=read(PILOT/'frozen_final.json')['checkpoint'];checked(checkpoint)
    checked(read(PILOT/'registration.json')['protected_baseline'])
    save(ROOT/'registration.json',dict(sources=rows,checkpoint=checkpoint,
        original_8_source_registration=ref(OLD/'registration.json'),
        original_summary_review=ref(OLD/'review.json'),new_pilot_review=ref(PILOT/'review.json'),
        code=ref(Path(__file__)),runtime=ref(ENGINEERING/'runtime.py'),wrapper=ref(WRAPPER),
        mechanism='One frozen checkpoint; apply to complete old8 raw-I3D feature timelines',
        new_I3D_or8B_calls=0,new_training=0,new_UMT_outputs=16,GPU_budget_seconds=300,
        old_sources_historically_exposed=True,not_blind_test=True,not_exact40_47=True,
        evaluator='All original summary reviewers and native frames; unselected is not explicitNHL',
        coverage='Adopt each original external TIME-control count; no threshold fitting',
        decision='Negative macro transfer or no correct-over-shift benefit stops full replacement; positive signal still requires production review',
        no_automatic426_or_ZIP=True,no_new_direction_or_parameter_scan=True))


def gpu():
    import numpy as np
    import torch
    import torch.nn.functional as F
    from runtime import make_models,score_features
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    registration=read(ROOT/'registration.json');checked(registration['code']);checked(registration['runtime'])
    unused,model,_=make_models(ENGINEERING);del unused
    model.load_state_dict(torch.load(checked(registration['checkpoint']),map_location='cpu',weights_only=True)['model'],strict=True)
    model.cuda().eval().requires_grad_(False);torch.set_num_threads(2)
    (ROOT/'outputs').mkdir()
    for row in registration['sources']:
        source=row['source']['sid'];values=np.load(checked(row['feature']),allow_pickle=False)
        x=F.normalize(torch.from_numpy(values).cuda(),dim=-1)[None]
        valid=torch.ones(x.shape[:2],dtype=torch.bool,device='cuda')
        for condition,data in [('correct',x),('shifted',torch.roll(x,x.shape[1]//2,dims=1))]:
            with torch.inference_mode():scores=score_features(model,data,valid).numpy()[0]
            with (ROOT/'outputs'/(source+'_'+condition+'.npy')).open('xb') as output:np.save(output,scores,allow_pickle=False)
            if len(scores)!=len(values) or not np.isfinite(scores).all():raise ValueError('New first temporal output invalid')
        print('ACCEPTED',source,flush=True)
    save(ROOT/'gpu_completion.json',dict(new_UMT_calls=16,new_I3D_or8B_calls=0,new_updates=0,
        checkpoint=registration['checkpoint'],parameters_UMT=sum(p.numel() for p in model.parameters()),
        complete_parameters=read(PILOT/'gpu_completion.json')['parameters']['complete_with_protected_base']))


def valid_binary(array):
    import numpy as np
    a=np.asarray(array)
    if not np.isfinite(a).all() or not np.isin(a,[0,1]).all():raise ValueError('Nonbinary/unknown reference before bool conversion')
    return a.astype(bool)


def paired_f1(selected,labels):
    import numpy as np
    tp=labels[selected].sum(axis=0);denom=int(selected.sum())+labels.sum(axis=0)
    value=float(np.divide(2*tp,denom,out=np.zeros(len(denom),dtype=float),where=denom>0).mean())
    chosen=set(np.flatnonzero(selected).tolist());independent=[]
    for column in range(labels.shape[1]):
        human=set(np.flatnonzero(labels[:,column]).tolist());d=len(chosen)+len(human)
        independent.append(2*len(chosen&human)/d if d else 0.)
    if abs(value-sum(independent)/len(independent))>1e-12:raise ValueError('Independent paired F1 differs')
    return value


def review():
    import numpy as np
    registration=read(ROOT/'registration.json')
    old_result={row['sid']:row for row in read(OLD/'review.json')['results']}
    rows=[]
    for row in registration['sources']:
        source=row['source'];sid=source['sid']
        with np.load(checked(source['comparison_ref']),allow_pickle=False) as data:
            baseline=valid_binary(data['baseline']);labels=valid_binary(data['labels'])
        groups=np.load(checked(row['groups']),allow_pickle=False)
        if baseline.ndim!=1 or labels.ndim!=2 or len(labels)!=len(baseline) or not np.array_equal(groups,np.arange(len(baseline))//64):
            raise ValueError('Native frame/group/reference dimensions differ')
        native=read(checked(source['clock_ref']));comparison=read(checked(source['comparison_clock_ref']))
        if native['original_exact_pts']!=comparison['original_exact_pts'] or native['source_sha256']!=source['media']['sha256']:
            raise ValueError('Original source presentation mapping differs')
        metrics=dict(external_TIME=paired_f1(baseline,labels),old_summary_UMT=old_result[sid]['metrics']['umt'])
        if abs(metrics['external_TIME']-old_result[sid]['metrics']['inherited_external_control'])>1e-12:
            raise ValueError('Adopted original control F1 differs')
        for condition in ['correct','shifted']:
            scores=np.load(ROOT/'outputs'/(sid+'_'+condition+'.npy'),allow_pickle=False)
            if not np.isfinite(scores).all() or groups.max()>=len(scores):raise ValueError('Actual score/native group mapping failed')
            selected=np.zeros(len(baseline),dtype=bool)
            selected[np.argsort(-scores[groups],kind='stable')[:int(baseline.sum())]]=True
            metrics[condition]=paired_f1(selected,labels)
        rows.append(dict(source=sid,metrics=metrics,selected=int(baseline.sum()),native_frames=len(baseline),reviewers=labels.shape[1]))
    macro={key:float(np.mean([row['metrics'][key] for row in rows])) for key in rows[0]['metrics']}
    passed=macro['correct']>macro['external_TIME'] and macro['correct']>macro['shifted']
    result=dict(state='CROSS_DATASET_SIGNAL_REQUIRES_PRODUCTION_REVIEW' if passed else 'STOP_FIXED_UPM_TO_GENERAL_SUMMARY_TRANSFER',
        results=rows,macro_all_reviewer_paired_F1=macro,all_native_frames_and_reviewers=True,
        independent_set_arithmetic_pass=True,new_training=0,new_features=0,
        checkpoint=registration['checkpoint'],historical_exposure_not_blind=True,
        summary_unselected_not_explicit_ordinary=True,exact40_47_control=False,
        no_automatic_production=True,baseline40_47_changed=False)
    save(ROOT/'review.json',result);print(json.dumps(result),flush=True)


def controller():
    preflight()
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
    if apps.strip():raise RuntimeError('External GPU compute active; no competing launch')
    command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','300','--planned-output-bytes','1000000',
        '--capacity-reason','Frozen UMT6.2M only on8 accepted cached timelines; noI3D/8B/no fitting; actual compute apps absent',
        '--queue-seconds','0','--',str(PY),'-B','-u',str(Path(__file__)),'gpu']
    with (ROOT/'gpu.log').open('x') as log:
        process=subprocess.Popen(command,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2'),stdout=log,stderr=subprocess.STDOUT)
        save(ROOT/'gpu_launch.json',dict(pid=process.pid,command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/'gpu_terminal.json',dict(exit_code=code))
    if code:raise RuntimeError('First frozen bridge inference failed')
    record=read(RUN/'controller'/(JOB+'.resource.json'))
    ledger=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status']!='completed' or record['exit_code']!=0 or [row for row in ledger if row.get('name')==JOB]!=[record]:
        raise ValueError('Unique GPU terminal/ledger differs')
    review()
    checked(read(PILOT/'registration.json')['protected_baseline'])
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],GPU_seconds=record['charged_seconds'],new_ZIP=0,baseline_unchanged=True))


if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'controller'
    try:gpu() if mode=='gpu' else controller()
    except BaseException as error:
        if ROOT.exists():save(ROOT/(mode+'_failure.json'),dict(error=repr(error),time=time.time()))
        raise
