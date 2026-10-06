"""CPU preparation and seal for the explicitly authorized Mac final-model route."""
from runtime import *
import datetime as dt
import subprocess

def audit_old_failure():
    old=ASSETS/'dev'; counts={}
    for arm in ('BASE8B','SFT8B'):
        output=rows(old/(arm+'.jsonl'));windows=[w for r in output for w in r['windows']]
        require(len(output)==104 and len(windows)==112,'old failed dev denominator changed')
        require(all(w['status']=='INFERENCE_FAILURE' and w.get('error')=='RuntimeError: dev source outside Linux workspace'
            and 'raw_output' not in w and 'video_identity' not in w and w['parsed_segments'] is None for w in windows),
            'only pre-decode/pre-generate engineering failures may be recovered')
        counts[arm]=dict(windows=112,pre_decode_failures=112,model_generation_calls=0,output_sha256=sha(old/(arm+'.jsonl')))
    require(read(old/'decision.json')['status']=='STOP_B_PACKAGE_DEV_GATE' and read(ASSETS/'completion.json')['stage']=='STOP_MAC8B_DELIVERY','original STOP evidence changed')
    write(HERE/'pre_generation_failure_audit.json',dict(status='PASS_EXACT_PRE_GENERATION_FAILURE_RECOVERY',
        counts=counts,old_input_contract_sha256=sha(old/'input_contract.json'),old_source_sha256=sha(ASSETS/'lowres.py'),
        failure_location='decode_dev_av Linux-root assertion before av.open, encoding, and model.generate',
        original_failure_preserved=True,quality_evaluation_calls_completed=0,scientific_recipe_changed=False))

def main():
    report=read(ASSETS/'training_evidence/train_report.json')
    completed=read(ASSETS/'training_evidence/pipeline_completion.json')
    require(completed['status']=='PASS_MAC_SECOND_8B_FULL_TRAINING_ENGINEERING' and completed['full_training_completed'], 'Mac full completion missing')
    require(sha(ASSETS/'training_evidence/train_report.json')==completed['full_report_sha256'], 'Mac report transfer hash changed')
    require(sha(ASSETS/'adapter/adapter_model.safetensors')==completed['adapter_sha256']==report['adapter_model_sha256'], 'Mac adapter transfer hash changed')
    require(sha(ASSETS/'training_evidence/source_lock.json')==completed['source_lock_sha256'], 'Mac training source lock changed')
    require(report['parameter_inventory']['total']==8782459120 and report['optimizer_steps']==227 and report['effective_batches']==3620, 'Mac training inventory incomplete')
    frozen=report['freeze_evidence'];require(len({v['sha256'] for v in frozen.values()})==1, 'Mac frozen base evidence mismatch')
    audit_old_failure()
    subprocess.run([sys.executable,'-B',str(HERE/'dev/evaluate.py'),'prepare'],check=True,cwd=RUN)
    require(sha(HERE/'dev/input_contract.json')==sha(ASSETS/'dev/input_contract.json'),'recovery changed the fixed dev bytes or geometry')
    dev=read(HERE/'dev/admission.json')
    for p in (HERE/'lowres.py',HERE/'DEV_PROTOCOL.md',*sorted((ASSETS/'training_evidence').glob('*'))):
        dev['files'][str(p)]=sha(p)
    # Not launched or sealed yet: extend the new CPU admission with relocation identities.
    (HERE/'dev/admission.json').write_text(json.dumps(dev,indent=2))
    write(HERE/'admission.json',dict(dev,scope='MAC_FINAL_LOWRES_8B_COMPLETE_DELIVERY'))
    config={}
    for scope,name in [('nontest','nontest_registry_01'),('rematch','scan_01')]:
        parent=RUN/'baseline_pts_v4'/name
        manifest=parent/'clean_manifest_v2.json';registry=parent/'clock_registry.json'
        config[scope]=dict(manifest=str(manifest),manifest_sha256=sha(manifest),registry=str(registry),registry_sha256=sha(registry))
    require(config['nontest']['manifest_sha256']=='ba34a284183e8a079054ffe811d7ec096e6b47c94e6edf812a37fd11b92d8dd7' and config['rematch']['manifest_sha256']=='ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8','clean manifest drift')
    write(HERE/'inputs.json',config)
    for scope in config: inputs(scope)
    subprocess.run([sys.executable,'-B',str(HERE/'processor_cpu.py')],check=True,cwd=RUN)
    subprocess.run([sys.executable,'-B',str(HERE/'test_cpu.py')],check=True,cwd=RUN)
    subprocess.run([sys.executable,'-B',str(HERE/'test_dev_input.py')],check=True,cwd=RUN)
    files={str(p):sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.log','.tmp')}
    files.update(dev['files'])
    for p in (ASSETS/'dev/BASE8B.jsonl',ASSETS/'dev/SFT8B.jsonl',ASSETS/'dev/decision.json',ASSETS/'source_lock.json',ASSETS/'completion.json',ASSETS/'lowres.py'):
        files[str(p)]=sha(p)
    from run_pts import verify_vendor
    verify_vendor()
    for name in ('vendor_lock.json','snapshot_lock.json','additional_frozen_dependencies.json','source_lock.json'):
        files[str(CODE/name)]=sha(CODE/name)
        for item in read(CODE/name)['files']: files[str(CODE/item['path'])]=item['sha256']
    for p in (RUN/'baseline_a_format_recovery_v1/constrained_json.py',ROOT/'inference/baseline_qwen3vl.py',
        RUN/'temporal_sft8b_v1/verify_saved_smoke.py',RUN/'controller/gpu_run.py'):
        files[str(p)]=sha(p)
    for scope in config:
        for name in ('manifest','registry'): files[config[scope][name]]=config[scope][name+'_sha256']
    write(HERE/'source_lock.json',dict(frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(),variant='MAC_FINAL_LOWRES_CUDA_PATH_RECOVERY_V2',files=files,authorized_by='mac的开发测评和提交包尽早完成',uploaded=False))
    print(json.dumps(dict(status='PASS_MAC_DELIVERY_CPU_SEAL',bound_files=len(files),source_lock_sha256=sha(HERE/'source_lock.json'))))

if __name__=='__main__': main()
