"""User-authorized 8B training, main-registered B smoke after successful A."""
import argparse,datetime as dt,hashlib,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL,HERE=RUN/'controller',RUN/'temporal_sft8b_v1'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def require(ok,message):
    if not ok:raise RuntimeError(message)
def current(stage,**extra):
    row=dict(stage=stage,checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),pid=os.getpid(),
        formal_c_bce_admitted=False,uploaded=False,**extra)
    p=CTRL/'sft8b_queue_latest.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(p)
    print(json.dumps(row),flush=True);return row

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--expected-lock-sha256',required=True);args=ap.parse_args()
    route_path=HERE/'training_authorization_B_SMOKE.json'
    route=read(route_path)
    require(route['authorized'] is True and route['route']=='TEMPORAL_8B_INTERVAL_SFT'
        and route['scope']=='TEMPORAL_8B_SFT_SMOKE_NONTEST'
        and route['authority_kind']=='USER_TRAINING_REQUEST_MAIN_REGISTERED_B_ROUTE'
        and route['user_request_quote']=='然后推理打包开训。' and route['explicit_user_route_choice'] is False,
        'actual user training request and main B registration missing')
    completion=CTRL/'sft8b_queue_completion.json'
    require(not completion.exists(),'queue completion exists; no repeat')
    with (CTRL/'sft8b_queue.registration.json').open('x') as f:json.dump(dict(pid=os.getpid()),f)
    try:
        lock_path=HERE/'smoke_source_lock.json'
        def verify():
            require(sha(lock_path)==args.expected_lock_sha256,'SFT queue source lock changed')
            lock=read(lock_path)
            for name,digest in lock['files'].items():require(sha(HERE/name)==digest,'SFT recipe/input changed: '+name)
            require(sha(__file__)==lock['queue_helper_sha256'],'SFT queue helper changed')
            require(sha(CTRL/'gpu_run.py')=='0cddca5f85a2a885ee2ac50e9193819b58dead39b6b561a30cb1c97f192ca961',
                'shared runner identity changed')
            require(sha(route_path)==lock['training_authorization_evidence_sha256'],'training authorization evidence changed')
        verify()
        config_path=HERE/'smoke_config_PREPARED_NOT_ADMITTED.json';config=read(config_path)
        a_admission=read(CTRL/'format_space_01.admission.json');a_launch=read(CTRL/'format_space_01.launch.json')
        deadline=dt.datetime.fromisoformat(a_launch['started_utc']).timestamp()+a_admission['single_job_max_seconds']+1800+600
        a_complete=CTRL/'format_pipeline_completion.json'
        current('WAITING_A_COMPLETE_CANDIDATE_BEFORE_SFT_SMOKE')
        while not a_complete.exists():
            require(time.time()<deadline,'bounded A completion wait expired; no training started')
            time.sleep(15)
        result=read(a_complete)
        require(result['stage']=='PASS_COMPLETE_426_CANDIDATE_NOT_UPLOADED' and result['videos']==426,
            'A candidate did not pass; SFT queue not started')
        verify()
        current('WAITING_LIVE_SHARED_RESOURCE_FOR_SFT_SMOKE')
        resource_deadline=time.monotonic()+1800
        while True:
            compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip()
            if not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists():break
            require(time.monotonic()<resource_deadline,'external GPU conflict remains; untouched')
            time.sleep(15)
        work=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0]);free=shutil.disk_usage(ROOT).free
        planned=15335424*4*2+config['updates']*config['grad_accum']*config['max_sequence_length']*32+33554432
        require(work+planned<=read(ROOT/'resource_policy.json')['added_disk_budget_gib']*2**30 and free>=planned,
            'capacity cannot cover actual SFT adapter/evidence plan')
        verify()
        admission=dict(schema='aic_temporal_sft8b_admission_v1',scope='TEMPORAL_8B_SFT_SMOKE_NONTEST',authorized=True,
            registered_route='TEMPORAL_8B_INTERVAL_SFT',training_authorized_by_user=True,
            training_authorization_evidence=dict(path=str(route_path),sha256=sha(route_path)),
            config_sha256=sha(config_path),train_manifest_sha256=config['train_manifest']['sha256'],
            r7_train_registry_sha256=config['r7_train_registry']['sha256'],model_receipt_sha256=config['model_receipt']['sha256'],
            source_code_sha256={n:sha(HERE/n) for n in ('train_sft.py','sft_contract.py')},
            resource_preflight_pass=True,shared_gpu_queue_approved=True,disk_peak_within_80gib=True,
            budget_runner_required=True,formal_c_bce_admitted=False,
            A_completed_evidence_sha256=sha(a_complete),planned_output_bytes=planned,
            live_resource=dict(work_bytes=work,free_bytes=free))
        admission_path=CTRL/'sft8b_smoke_01.admission.json'
        with admission_path.open('x') as f:f.write(json.dumps(admission,indent=2)+'\n')
        # Stdlib contract validates all pinned source/model bytes before CUDA.
        subprocess.run([sys.executable,'-B',str(HERE/'train_sft.py'),'--config',str(config_path),
            '--admission',str(admission_path),'--check-only'],check=True,timeout=300)
        verify()
        current('RUNNING_SFT8B_FIVE_UPDATE_SMOKE',planned_output_bytes=planned)
        subprocess.run([sys.executable,'-B','-u',str(CTRL/'gpu_run.py'),'--name','rematch_sft8b_smoke_01',
            '--max-seconds',str(config['max_wall_seconds']),'--planned-output-bytes',str(planned),
            '--capacity-reason','pinned 8B five-update interval SFT on fixed 16 non-test train sources; actual adapter/evidence size',
            '--queue-seconds','1800','--',sys.executable,'-B','-u',str(HERE/'train_sft.py'),
            '--config',str(config_path),'--admission',str(admission_path)],check=True)
        report_path=HERE/'smoke_01/train_report.json';report=read(report_path)
        require(report['status']=='PASS_INTERVAL_SFT_SMOKE_ENGINEERING_ONLY' and report['optimizer_steps']==config['updates']
            and report['effective_batches']==config['updates']*config['grad_accum'] and report['base_frozen']
            and report['vision_frozen'] and report['adapter_reload_succeeded'],'actual SFT smoke did not pass')
        result=current('PASS_8B_INTERVAL_SFT_SMOKE_ONLY',report_sha256=sha(report_path),
            optimizer_steps=report['optimizer_steps'],adapter_sha256=report['adapter_model_sha256'],full_training_completed=False,
            quality_claim=False)
    except Exception as exc:
        result=current('STOP_SFT8B_QUEUE',failure_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
    with completion.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    raise SystemExit(0 if result['stage'].startswith('PASS_') else 1)
