"""Single new data intervention; protected baseline, source/input locks and unique GPU ledger."""
import os
from pathlib import Path
import subprocess
import time
import traceback

from pilot_common28 import ROOT,ADMISSION,WORK,ENGINEERING,RUN,WRAPPER,PY,JOB,read,ref,save,checked,contracts

CODE=Path(__file__).parent


def register():
    ROOT.mkdir()
    save(ROOT/'protocol.json',dict(mechanism='Only new independent noncompetitive human-summary supervision; same original UMT architecture and final200 updates',
        seed=7328,updates=200,learning_rate=1e-4,coverage=.15,
        targets='All original reviewer selections averaged; native duration-weighted cells and equal sources',
        old_summary_control='Frozen original SumMe20 UMT400 final',
        sport_control='Frozen previous SportCLIP3 UMT200 final, no new fit',
        held_gate='New held macro strictly exceeds original/sport/halfshift; each held source no worse than original',
        general_gate='Full previously exposed external8: strictly above adopted TIME, old UMT and own halfshift at identical original TIME coverage',
        historical_sources_not_new_blind_test=True,not_exact40_47=True,
        GPU_limit_seconds=900,no_automatic_production=True,no_threshold_or_checkpoint_scan=True))
    started=time.monotonic()
    while not (ADMISSION/'native25/completion.json').exists():
        if (ADMISSION/'native26_failure.json').exists():raise ValueError('Actual native preparation failed')
        if time.monotonic()-started>1800:raise TimeoutError('Bounded first CPU inputs wait elapsed')
        time.sleep(2)
    accepted=read(ADMISSION/'native25/completion.json')
    sources=[read(checked(record)) for record in accepted['accepted']]
    dev=sum(s['role']=='development' for s in sources);held=sum(s['role']=='held_recording' for s in sources)
    if dev<3 or held<2:raise ValueError('Insufficient fixed native-compatible training/held recordings')
    bridge=[]
    for source in read(ENGINEERING/'crossdata12/registration.json')['sources']:
        if source['role']!='held_dataset':continue
        feature=read(ENGINEERING/'crossdata12/features'/source['sid']/'acceptance.json')['features'];checked(feature)
        bridge.append(dict(source=source,feature=feature,groups=ref(ENGINEERING/'crossdata12/inputs'/source['sid']/'groups.npy')))
    if len(bridge)!=8:raise ValueError('Original full dataset bridge incomplete')
    media=read(ADMISSION/'media24/registration.json')
    checked(media['protected_baseline'])
    control=read(ENGINEERING/'crossdata12/frozen_final.json')['checkpoint'];checked(control)
    sport=read(WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16/frozen_final.json')['checkpoint'];checked(sport)
    save(ROOT/'registration.json',dict(sources=sources,external_bridge=bridge,
        protected_baseline=media['protected_baseline'],control_checkpoint=control,sport_checkpoint=sport,
        train_sources=dev,held_sources=held,independent_recordings=len(sources),
        distinct_publishers=len({s['publisher'] for s in sources}),
        source_roles_original=ref(ADMISSION/'media24/registration.json'),
        native_admission=ref(ADMISSION/'native25/completion.json'),
        all_media_and_evidence_stay_Linux=True,not_broad80_source_T_main=True))
    contracts()
    dependencies={name:ref(path) for name,path in {
        'runtime':ENGINEERING/'runtime.py','I3D_loader':ENGINEERING/'profile_gpu.py',
        'pure_training_helpers':WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16/code/pilot15_gpu.py',
        'helper_paths':WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16/code/pilot15_common.py',
        'wrapper':WRAPPER}.items()}
    if dependencies['wrapper']['sha256']!='9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec':
        raise ValueError('Unique shared GPU wrapper changed')
    save(ROOT/'source_input_lock.json',dict(protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),
        code={name:ref(CODE/name) for name in ['common.py','pilot_common28.py','pilot_gpu28.py','pilot_review28.py','pilot28.py']},
        dependencies=dependencies,CPU_contracts=ref(ROOT/'CPU_contracts.json')))


def execute(name,gpu=False):
    command=[str(PY),'-B','-u',str(CODE/name)]
    if gpu:
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('External GPU compute active; protect it without competing launch')
        save(ROOT/'resource_admission.json',dict(actual_compute_apps=apps,
            GPU_snapshot=subprocess.check_output(['nvidia-smi'],text=True),
            RAM=subprocess.check_output(['free','-b'],text=True),
            disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
            reason='Prior I3D/UMT actual peak885MB, new7 source clips fit accepted storage; Java CPU workload protected, no Qwen loaded'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','900','--planned-output-bytes','100000000',
            '--capacity-reason','Accepted new noncompetitive native inputs; original I3D28M and UMT6.2M only; prior peak885MB, external compute absent; fixed200 updates',
            '--queue-seconds','0','--']+command
    stage='gpu' if gpu else 'review'
    with (ROOT/(stage+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT)
        save(ROOT/(stage+'_launch.json'),dict(pid=process.pid,command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(stage+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual new first stage failed: '+stage)
    if gpu:
        record=read(RUN/'controller'/(JOB+'.resource.json'))
        rows=[__import__('json').loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
        if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
            raise ValueError('Natural GPU terminal and unique ledger differ')
        return record


def main():
    register();record=execute('pilot_gpu28.py',True);execute('pilot_review28.py')
    checked(read(ROOT/'registration.json')['protected_baseline'])
    result=read(ROOT/'review.json')
    receipt=dict(state=result['state'],held_F1=result['held_all_reviewer_frame_F1'],
        general_F1=result['external8_historical_macro_F1'],
        independent_recordings=len(result['results']),full_parameters=read(ROOT/'gpu_completion.json')['full_parameters'],
        actual_GPU_seconds=record['charged_seconds'],GPU_status=record['status'],GPU_exit=record['exit_code'],
        baseline_unchanged=True,new_ZIP=0,no_automatic_production=True,
        review=ref(ROOT/'review.json'),CPU_audit=ref(ROOT/'independent_CPU_audit.json'))
    save(ROOT/'completion.json',receipt);save(ADMISSION/'short_terminal28.json',receipt)


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_silent_retry=True))
        raise
