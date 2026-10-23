"""Narrow-evidence explicit production admission, allCPU -> one GPU -> independent CPU."""
import json
import os
from pathlib import Path
import socket
import subprocess
import traceback
from routing_production60_common import ROOT,ADMISSION,WORK,RUN,PY,WRAPPER,JOB,SPORT,ENGINEERING,FULL_PARAMETERS,CLASSES,read,ref,save,checked

CODE=Path(__file__).parent


def register():
    ROOT.mkdir()
    if socket.gethostname()!='inspur-NP5570M5' or not os.environ.get('CUDA_VISIBLE_DEVICES'):
        raise ValueError('Correct live host/nonempty GPU parent visibility required')
    adopted=read(ADMISSION/'baseline_bridge59/completion.json')
    actual=read(checked(adopted['review']))
    gains=actual['F1_delta_vs_complete_frozen_branch']
    if not all(gains[k]>0 for k in ['source_rerank','source_remove']):
        raise ValueError('Both fixed policy external gains required, not package quota')
    assets=ref(ADMISSION/'production_assets58/completion.json');data=read(checked(assets))
    if data['records']!=426:raise ValueError('Complete formal assets unavailable')
    protected=data['protected_baseline'];checked(protected)
    expert=read(SPORT/'frozen_final.json')['checkpoint'];checked(expert)
    names=ref(ADMISSION/'semantic_route48/kinetics_classnames.json')
    save(ROOT/'protocol.json',dict(policies=['source_rerank','source_remove'],
        fixed_route='Mean original K400 cell posteriors, global argmax in fixed four-event set; no test-content-dependent class additions',
        event_classes=CLASSES,native_profile='Exactly original SportCLIP I3D8 samples at min(start+8*k,stop-1),64-native-frame cells, short256/center224/.45/.225',
        source_rerank='Preserve exact baseline selected count within each routed source; stable native-order top scores in pre-existing valid spatial field domain',
        source_remove='On routed sources only, retain original40.47 frame iff frozen binary-HL sigmoid>=0.5; no added frames, legal empty allowed',
        no_route='Exact original40.47 predictions retained; semantic default is not an execution-error fallback',
        spatial='Existing continuous full-source field; old retained boxes identical; no new spatial model',
        quality_scope='One historically exposed held sport, strong originalTIME and full frozen external branch gains;32 nonrouted external sources unchanged. Not independent blind or official joint proof',
        quality_evidence=gains,original_failed_post_flag_GPU_ledger_preserved=True,
        all426_new_actual_RGB_CPU_inputs_before_first_GPU=True,
        cache='Existing private Linux tmpfs; actual uncompressed byte and RAM checks; source RGB lifecycle retires only after all outputs and CPU QA; durable refs/model raw remain',
        GPU_limit_seconds=900,all_models_parameters=FULL_PARAMETERS,
        no_new8B_calls=True,no_training=True,no_test_GT_or_manual_labeling=True,
        no_parameter_or_threshold_search_after_formal_outputs=True,
        no_automatic_website_submission=True,packaging_separate_after_actual_models_and_QA=True))
    save(ROOT/'registration.json',dict(assets=assets,protected_baseline=protected,expert_checkpoint=expert,class_names=names,
        reference_adoption=ref(ADMISSION/'baseline_bridge59/completion.json'),reference_review=adopted['review'],
        old_all_source_expert_transfer_STOP_unchanged=True,no_old_failed_recipe_relabelled_as_pass=True,
        physical_base_and_TIME_semantic_parameters=8782557449,actual_aux_expected_parameters=34252497))
    save(ROOT/'initial_resource_snapshot.json',dict(host=socket.gethostname(),
        tasks=subprocess.check_output(['ps','-eo','pid,ppid,stat,pcpu,pmem,args','--sort=-pcpu'],text=True),
        RAM=subprocess.check_output(['free','-b'],text=True),disk=subprocess.check_output(['df','-B1',str(ROOT),'/dev/shm'],text=True),
        GPU=subprocess.check_output(['nvidia-smi'],text=True),parent_CUDA=os.environ.get('CUDA_VISIBLE_DEVICES')))


def stage(name,gpu=False):
    command=[str(PY),'-B','-u',str(CODE/name)]
    if gpu:
        # Admission uses a measured prior driver peak and the actual longest new sequence, not a fixed free-GiB line.
        previous=read(RUN/'controller/author_qv24_late_visual_rank_20261022_v47.resource.json')
        assets=read(checked(read(ROOT/'registration.json')['assets']))
        longest=max(s['RGB_I3D_native64_cells'] for s in assets['sources'])
        expected=previous['sampled_peak_memory_mib']*(1<<20)+longest*longest*8*6*4*2
        query=subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip()
        free=int(query.splitlines()[0])*(1<<20)
        if free<expected:raise RuntimeError('Measured prior peak plus actual new sequence bound does not fit current GPU availability')
        save(ROOT/'resource_admission.json',dict(
            actual_compute_apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True),
            actual_tasks=subprocess.check_output(['ps','-eo','pid,ppid,stat,pcpu,pmem,args','--sort=-pcpu'],text=True),
            observed_prior_peak=previous['sampled_peak_memory_mib'],actual_max_cells=longest,derived_peak_bound_bytes=expected,
            actual_free_GPU_bytes=free,RAM=subprocess.check_output(['free','-b'],text=True),
            disk=subprocess.check_output(['df','-B1',str(ROOT),'/dev/shm'],text=True),
            basis='All actual input RGB already in private RAM files; only34.25M auxiliary weights onGPU, no8B load/backward; source/frame outputs bounded, shared Java CPU protected'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','900','--planned-output-bytes','256000000',
            '--capacity-reason','First3870 native64 auxiliary clips across426; all actual CPU inputs accepted in existing tmpfs, only frozen I3D+UMT; original40.47 answers/space reused',
            '--queue-seconds','0','--']+command
    label=Path(name).stem
    with (ROOT/(label+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
        save(ROOT/(label+'_launch.json'),dict(command=command,pid=process.pid,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(label+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual formal stage failed: '+label)


def retire_ram():
    info=read(ROOT/'RAM_cache_registration.json');cache=Path(info['path']).resolve(strict=True)
    if cache.parent!=Path('/dev/shm') or not cache.name.startswith('aic_routing60_') or cache.stat().st_uid!=os.getuid() or cache.is_symlink():
        raise ValueError('RAM retirement scope/owner differs')
    files=sorted((cache/'inputs').glob('*/*'))
    if any(not p.is_file() or p.is_symlink() or p.name not in {'rgb.npy','groups.npy','acceptance.json'} for p in files):
        raise ValueError('Unexpected private cache member; refuse cleanup')
    save(ROOT/'RAM_retirement_manifest.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size) for p in files],
        reason='Predeclared ephemeral own-input lifecycle after all model outputs and independent CPU QA',
        durable_CPU_acceptance_and_output=ref(ROOT/'selection_acceptance.json'),no_original_media_or_model_deleted=True))
    for path in files:path.unlink()
    for folder in (cache/'inputs').iterdir():folder.rmdir()
    (cache/'inputs').rmdir();cache.rmdir()
    save(ROOT/'RAM_retirement_completion.json',dict(state='OWN_EPHEMERAL_INPUTS_RELEASED_AFTER_QA',
        retired_files=len(files),durable_input_hashes_and_raw_outputs_kept=True))


def main():
    register();stage('routing_production60_prepare.py')
    names=['common.py','routing_production60_common.py','routing_production60_prepare.py',
           'routing_production60_gpu.py','routing_production60_review.py','routing_production60.py']
    dependencies=[ENGINEERING/'runtime.py',ENGINEERING/'profile_gpu.py',SPORT/'code/pilot15_common.py',
        SPORT/'code/pilot15_prepare.py',SPORT/'code/pilot15_gpu.py',ENGINEERING/'crossdata12/code/prepare_raw.py',WRAPPER]
    save(ROOT/'source_input_lock.json',dict(protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),
        CPU=ref(ROOT/'CPU_completion.json'),code={n:ref(CODE/n) for n in names},dependencies={str(p):ref(p) for p in dependencies}))
    stage('routing_production60_gpu.py',True)
    resource=read(RUN/'controller'/(JOB+'.resource.json'))
    rows=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status']!='completed' or resource['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[resource]:
        raise ValueError('Natural full production GPU terminal / unique ledger differs')
    stage('routing_production60_review.py');checked(read(ROOT/'registration.json')['protected_baseline'])
    retire_ram()
    save(ROOT/'model_and_selection_completion.json',dict(state='ALL426_MODEL_AND_FIRST_CPU_QA_COMPLETE_PACKAGE_PENDING',
        selection=ref(ROOT/'selection_acceptance.json'),GPU_seconds=resource['charged_seconds'],
        actual_GPU_status=resource['status'],actual_GPU_exit=resource['exit_code'],actual_parameters=FULL_PARAMETERS,
        new8B_calls=0,new_ZIP=0,baseline40_47_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),keep_all_success_and_RAM_cache=True))
        raise
