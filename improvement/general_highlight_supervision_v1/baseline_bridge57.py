"""Complete frozen40.47 external branch before routing-production decision."""
import os
from pathlib import Path
import subprocess
import json
import traceback
from baseline_bridge57_common import ROOT,ADMISSION,DATA,SEM,WORK,RUN,PY,WRAPPER,JOB,read,ref,save,checked

CODE=Path(__file__).parent


def stage(name,gpu=False):
    command=[str(PY),'-B','-u',str(CODE/name)]
    if gpu:
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('Protect external GPU compute; accepted CPU inputs retained')
        save(ROOT/'resource_admission.json',dict(compute_apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'],text=True),RAM=subprocess.check_output(['free','-b'],text=True),
            disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
            basis='Previous actual native64 original8B peak22.1GB; no external compute; at most8 context targets per batch, no backward or other GPU model; CPU inputs already materialized, Java protected'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','1200','--planned-output-bytes','32000000',
            '--capacity-reason','Only new external VERIFY and exact frozen context-semantic forwards; original B0 adopted, no test data, no training; actual CPU inputs accepted',
            '--queue-seconds','0','--']+command
    label=Path(name).stem
    with (ROOT/(label+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
        save(ROOT/(label+'_launch.json'),dict(command=command,pid=process.pid,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(label+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual external branch stage failed: '+label)


def main():
    ROOT.mkdir();strong=read(ADMISSION/'time_control54/completion.json')
    if not strong['state'].startswith('STRONG_TIME_ROUTING_SIGNAL'):raise ValueError('No actual strong originalTIME routing signal')
    source=read(DATA/'registration.json')['source'];protected=read(DATA/'registration.json')['protected_baseline'];checked(protected)
    sem=read(SEM/'production_registration.json');checked(sem['selected_head'])
    save(ROOT/'protocol.json',dict(purpose='Complete unchanged VERIFY+frozen semantic40.47 algorithm on the held external recording before production',
        original_B0_answers_adopted=True,external_native64_windows='Same previously registered <=30s originalTIME profile; no claim to reproduce official-source output',
        VERIFY='Exact cv_contract/tp_contract.verify_prompt and TIME role, native original64 pixels, new native eligible window timestamps',
        D8='Clip each original interval padding to original window; same .75/.5(+.25 for original length>=8)',
        empty_source_guard='Preserve original D8 if VERIFY removes whole source',
        semantic='Exact occupied half-second native midpoint images/chunks8/BASE target-specific text/LM transform/frozen98329-head; only residual>1 adds',
        no_endpoint_refinement='Protected40.47 depends on VERIFY arm, not VERIFY_BOTH',
        no_new_training=True,no_threshold_or_prompt_search=True,GPU_max_seconds=1200,
        candidate_policies=['source_rerank','source_remove'],supplement_fixed_failure_preserved=True,
        labels_only_after_all_predictions=True,no_automatic426_or_package=True))
    save(ROOT/'registration.json',dict(source=source,protected_baseline=protected,
        adopted_B0_terminal=ref(ADMISSION/'time_control54/completion.json'),
        semantic_registration=ref(SEM/'production_registration.json'),selected_head=sem['selected_head'],
        old_declarations=[ref(ADMISSION/'semantic_route48/protocol.json'),ref(ADMISSION/'route_remove52/protocol.json')],
        current_external_scope='Only one historically exposed held sport; not new blind or official joint truth'))
    stage('baseline_verify57_prepare.py');stage('baseline_semantic57_prepare.py')
    verify=read(ROOT/'verify_CPU_completion.json');semantic=read(ROOT/'semantic_CPU_completion.json')
    if len(verify['cases'])>50 or semantic['cells']<=0:raise ValueError('Actual fixed external denominator differs')
    names=['common.py','time_control50_common.py','time_entry53.py','time_control50_prepare.py',
        'baseline_bridge57_common.py','baseline_verify57_prepare.py','baseline_semantic57_prepare.py',
        'baseline_bridge57_gpu.py','baseline_bridge57_review.py','baseline_bridge57.py']
    dependencies=[SEM/'code'/n for n in ['production_semantic10.py','semantic09.py','semantic_oof09.py','monotone_head06.py']]
    dependencies += [WORK/'twenty_hour_five_20261014_v1/candidate_verify_v2/code'/n for n in ['cv_contract.py','cv_grammar.py']]
    dependencies += [WORK/'twenty_hour_five_20261014_v1/temporal_production_inputs_v4/code/tp_contract.py',
                     RUN/'b_score_aligned_package_v4/source_color.py',WRAPPER]
    save(ROOT/'source_input_lock.json',dict(code={n:ref(CODE/n) for n in names},
        dependencies={str(p):ref(p) for p in dependencies},protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),
        VERIFY_CPU=ref(ROOT/'verify_CPU_completion.json'),semantic_CPU=ref(ROOT/'semantic_CPU_completion.json'),
        expected_VERIFY_calls=len(verify['cases']),expected_semantic_batches=len(semantic['chunks']),expected_semantic_queries=semantic['cells']))
    stage('baseline_bridge57_gpu.py',True)
    record=read(RUN/'controller'/(JOB+'.resource.json'))
    rows=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
        raise ValueError('Actual unique GPU natural terminal differs')
    stage('baseline_bridge57_review.py');checked(protected)
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],review=ref(ROOT/'review.json'),
        independent_CPU=ref(ROOT/'independent_CPU_audit.json'),GPU_seconds=record['charged_seconds'],new_ZIP=0,baseline_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),keep_every_success=True))
        raise
