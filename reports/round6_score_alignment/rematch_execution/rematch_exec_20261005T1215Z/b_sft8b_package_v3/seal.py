"""Bind only declared engineering code, clean manifests and real CPU evidence."""
from runtime import *
import datetime as dt

def main():
    config={}
    for scope,name in [('nontest','nontest_registry_01'),('rematch','scan_01')]:
        parent=RUN/'baseline_pts_v4'/name
        manifest=parent/'clean_manifest_v2.json';registry=parent/'clock_registry.json'
        config[scope]=dict(manifest=str(manifest),manifest_sha256=sha(manifest),registry=str(registry),registry_sha256=sha(registry))
    require(config['nontest']['manifest_sha256']=='ba34a284183e8a079054ffe811d7ec096e6b47c94e6edf812a37fd11b92d8dd7' and
        config['rematch']['manifest_sha256']=='ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8','original clean manifests changed')
    write(HERE/'inputs.json',config)
    for scope in config:inputs(scope)
    require(read(HERE/'processor_cpu_01.json')['status']=='PASS_ACTUAL_8B_NATIVE_PROCESSOR','processor gate failed')
    require(read(HERE/'cpu_contract_01.json')['status']=='PASS_CPU_CONTRACT','CPU contract failed')
    files={}
    for name in ('runtime.py','production.py','controller.py','processor_cpu.py','test_cpu.py','PROTOCOL.md',
                 'inputs.json','processor_cpu_01.json','cpu_contract_01.json','seal.py','launch.py',
                 'bridge_and_deliver.ps1','verify_delivery.py','CPU_PRESEAL_NOTE.md','RECOVERY.md','mac_timestamp_fixture.json',
                 'prepare_recovery.py','partial_recovery_inputs.json'):
        files[str(HERE/name)]=sha(HERE/name)
    from run_pts import verify_vendor
    verify_vendor()
    for p in (HERE/'cpu_reference').glob('*'):
        if p.is_file():files[str(p)]=sha(p)
    for name in ('vendor_lock.json','snapshot_lock.json','additional_frozen_dependencies.json','source_lock.json'):
        files[str(CODE/name)]=sha(CODE/name)
        for item in read(CODE/name)['files']:files[str(CODE/item['path'])]=item['sha256']
    for path in (RUN/'baseline_a_format_recovery_v1/constrained_json.py',ROOT/'inference/baseline_qwen3vl.py',
        RUN/'temporal_sft8b_v1/verify_saved_smoke.py',RUN/'controller/gpu_run.py',
        RUN/'temporal_sft8b_dev_v1/decision.json',RUN/'controller/rematch_sft8b_dev_01.resource.json',
        RUN/'b_sft8b_package_v1/completion.json',RUN/'b_sft8b_package_v1/source_lock.json',
        RUN/'baseline_a_pts_v1/real_decoder_02/decoder_test_receipt.json'):
        files[str(path)]=sha(path)
    for scope in config:
        for name in ('manifest','registry'):files[config[scope][name]]=config[scope][name+'_sha256']
    for path,digest in files.items():require(sha(path)==digest,'declared original source drifted')
    for path in (RUN/'controller/b8b_geometry_cpu_01.json',RUN/'controller/measure8b_processor_geometry_cpu.py',
        RUN/'b_sft8b_package_v2/completion.json',RUN/'b_sft8b_package_v2/source_lock.json',
        RUN/'b_sft8b_package_v2/nontest_01/package.stage.json',RUN/'b_sft8b_package_v2/nontest_01/independent_validation.json',
        RUN/'b_sft8b_package_v2/nontest_01/spatial.stage.json',RUN/'b_sft8b_package_v2/nontest_01/temporal.stage.json',
        Path(read(HERE/'partial_recovery_inputs.json')['partial_path'])):
        files[str(path)]=sha(path)
    write(HERE/'source_lock.json',dict(frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(),variant='B_8B_INFERENCE_CONTEXT_COMPAT_V3',
        files=files,authorized_by='user_generate_package_main_registered_existing_B_route',uploaded=False))
    print(json.dumps(dict(status='PASS_SEALED_CPU_AND_BYTE_CONTRACT',bound_files=len(files),source_lock_sha256=sha(HERE/'source_lock.json'))))

if __name__=='__main__':main()
