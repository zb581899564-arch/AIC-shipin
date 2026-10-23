"""One explicitly registered two-arm pilot, after all actual native CPU inputs pass."""
import os
from pathlib import Path
import subprocess
import traceback
import json

from qv_common47 import ROOT,ADMISSION,WORK,ENGINEERING,RUN,PY,WRAPPER,JOB,read,ref,save,checked
from qv_targets47 import source_queries,contracts

CODE=Path(__file__).parent


def register():
    ROOT.mkdir()
    admitted=read(ADMISSION/'qv_native46/completion.json')
    sources=[read(checked(record)) for record in admitted['accepted']]
    for source in sources:
        source['queries']=source_queries(source)
        for name in ['media','annotations','clock','rgb','groups']:checked(source[name])
    if len(sources)<16 or sum(s['role']=='held_recording' for s in sources)<3:
        raise ValueError('Insufficient fixed independent native-compatible sources')
    train=[s for s in sources if s['role']=='development' and any(q['pairs'] for q in s['queries'])]
    if len(train)<12:raise ValueError('Insufficient actual within-query preference supervision')
    bridge=[]
    for source in read(ENGINEERING/'crossdata12/registration.json')['sources']:
        if source['role']!='held_dataset':continue
        input_record=read(ENGINEERING/'crossdata12/inputs'/source['sid']/'acceptance.json')
        for name in ['rgb','groups']:checked(input_record[name])
        feature=read(ENGINEERING/'crossdata12/features'/source['sid']/'acceptance.json')['features']
        checked(feature);checked(source['comparison_ref'])
        bridge.append(dict(source=source,input=input_record,feature=feature,groups=input_record['groups']))
    if len(bridge)!=8:raise ValueError('Original eight-source bridge incomplete')
    baseline=read(ADMISSION/'media24/registration.json')['protected_baseline'];checked(baseline)
    control=read(ENGINEERING/'crossdata12/frozen_final.json')['checkpoint'];checked(control)
    save(ROOT/'protocol.json',dict(
        mechanism='Human within-query saliency teaches actual last I3D residual stage; frozen early visual/8B/TIME/space unchanged',
        arms=['frozen_visual','late_visual'],seed=7347,updates_per_arm=128,temporal_lr=1e-4,visual_lr=1e-5,
        same_supervision_and_update_count_not_claimed_equal_FLOPs=True,
        actual_trainable_visual_stage='I3D blocks[5], 17061888 parameters; eval-mode BN stats frozen',
        paired_gradient_context='Full-source original context; only paired last-stage cells carry gradients; other cells detached original features',
        pair_selection='Within same author query, original mean gap>=1 and2/3 agree; hash first32 pairs per query; each source equally cycled',
        all3_reviewers='BCE logits difference vs each original (rating difference+4)/8; average all3',
        unknown='Outside originally annotated query clips never negative/ordinary',
        final_checkpoint_only=True,no_threshold_prompt_or_checkpoint_scan=True,
        held_signal='All-rater query-macro NDCG and confident pair accuracy strictly above initial and own halfshift; at least2 held sources improve NDCG, no held source NDCG loss>0.10',
        new_mechanism_evidence='Late visual must exceed same-supervision frozen-visual control to attribute gain to visual adaptation',
        transfer='Full historical eight-source same original TIME coverage, all reviewers. Evidence diagnostic; no automatic production; exact40.47 bridge still required',
        no_proxy_metric_claims_as_official_joint_score=True,GPU_limit_seconds=1200,
        data_scope='Author train/val noncommercial student research; no test GT or raw redistribution',
        no_automatic426_or_package=True))
    save(ROOT/'registration.json',dict(sources=sources,external_bridge=bridge,
        protected_baseline=baseline,control_checkpoint=control,actual_training_sources=len(train),
        parent_youtube_ID_disjoint=len({s['youtube_id'] for s in sources})==len(sources),
        roles_frozen_before_model=True,original_source=ref(ADMISSION/'author_qv45/completion.json'),
        native_input=ref(ADMISSION/'qv_native46/completion.json'),
        exact40_47_external_reproduction=False,global_pretraining_or_repost_overlap='UNKNOWN'))
    save(ROOT/'CPU_contracts.json',contracts())
    names=['common.py','qv_common47.py','qv_targets47.py','qv_model47.py','qv_gpu47.py','qv_pilot47.py','qv_review47.py']
    dependencies=dict(runtime=ref(ENGINEERING/'runtime.py'),loader=ref(ENGINEERING/'profile_gpu.py'),
        original_training_helpers=ref(WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16/code/pilot15_gpu.py'),
        wrapper=ref(WRAPPER))
    if dependencies['wrapper']['sha256']!='9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec':
        raise ValueError('Shared wrapper changed')
    save(ROOT/'source_input_lock.json',dict(protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),
        code={name:ref(CODE/name) for name in names},dependencies=dependencies,CPU_contracts=ref(ROOT/'CPU_contracts.json')))


def run_stage(name,gpu=False):
    command=[str(PY),'-B','-u',str(CODE/name)]
    if gpu:
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('External GPU workload active; no competing launch')
        save(ROOT/'resource_admission.json',dict(actual_compute_apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'],text=True),RAM=subprocess.check_output(['free','-b'],text=True),
            disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
            reason='Accepted source inputs already on disk; pooled features and two final checkpoints under250MB; frozen-prefix CPU cache about6GB against current free RAM; only I3D/UMT resident, Java CPU protected'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','1200','--planned-output-bytes','250000000',
            '--capacity-reason','New author24 query preferences; true last-visual intervention and same-supervision frozen control, bounded two final arms; original8B not loaded',
            '--queue-seconds','0','--']+command
    stage='gpu' if gpu else 'review'
    with (ROOT/(stage+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
        save(ROOT/(stage+'_launch.json'),dict(pid=process.pid,command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(stage+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual stage failed: '+stage)
    if gpu:
        record=read(RUN/'controller'/(JOB+'.resource.json'))
        rows=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
        if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
            raise ValueError('Natural GPU terminal / unique ledger differs')
        return record


def main():
    register();record=run_stage('qv_gpu47.py',True);run_stage('qv_review47.py')
    checked(read(ROOT/'registration.json')['protected_baseline'])
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],GPU_seconds=record['charged_seconds'],
        review=ref(ROOT/'review.json'),independent_audit=ref(ROOT/'independent_CPU_audit.json'),
        baseline40_47_unchanged=True,new_ZIP=0,no_automatic_production=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_repeat_success=True))
        raise
