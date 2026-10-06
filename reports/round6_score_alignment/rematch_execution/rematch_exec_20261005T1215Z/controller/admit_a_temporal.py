"""Supervisor's frozen all-426 identity predicate; only A temporal/scheduling."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL=RUN/'controller'
PTS=RUN/'baseline_pts_v3/scan_01'
REGISTERED_M0_SHA='57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32'
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    return json.loads(Path(path).read_text())
if __name__=='__main__':
    authorization=read(CTRL/'authorization.json')
    if authorization['competition_upload_authorized'] is not False or 'complete rematch baseline generation after input contract and regression' not in authorization['scope']:
        raise RuntimeError('registered user authorization missing generation scope')
    receipt=read(PTS/'pts_origin_receipt.json')
    manifest=PTS/'clean_manifest_426_pts_origin_v3.json'
    if (receipt['status']!='PASS_CFR_WITH_LEGACY_ONE_FRAME_TOLERANCE'
        or receipt['registered_sources']!=426 or receipt['audited_sources']!=426 or receipt['passed_sources']!=426
        or receipt['failed_video_ids'] or receipt['input_manifest_sha256']!=REGISTERED_M0_SHA
        or receipt['one_frame_cfr_tolerance_changed'] is not False or receipt['source_bytes_modified'] is not False
        or receipt['labels_read'] is not False or receipt['models_run'] is not False or receipt['GPU_used'] is not False):
        raise RuntimeError('all-426 frozen source identity gate not accepted; no inference admission')
    original=RUN/'baseline_a/m0_finalize_01/clean_manifest_426.json'
    if sha(original)!=REGISTERED_M0_SHA:
        raise RuntimeError('original complete M0 identity changed')
    old=read(original)
    fresh=read(manifest)
    if old['records']!=fresh['records'] or old['allowed_source_roots']!=fresh['allowed_source_roots']:
        raise RuntimeError('source set, IDs, metadata, ratio, scope or paths changed')
    registry=PTS/'origin_registry.json'
    if sha(registry)!=receipt['origin_registry_sha256'] or sha(registry)!=fresh['input_contract']['source_origin_registry_sha256']:
        raise RuntimeError('PTS origin registry binding changed')
    expected={r['video_id']:r['source_sha256'] for r in old['records']}
    audited={r['video_id']:r for r in receipt['records']}
    if len(audited)!=426 or set(audited)!=set(expected):
        raise RuntimeError('426 source audit denominator changed')
    for vid,digest in expected.items():
        result=audited[vid]
        if result['pass'] is not True or result['failures'] or result['source_sha256']!=digest or result['decord_all_frame_binding_checked'] is not True:
            raise RuntimeError('source not accepted: '+vid)
        if sha(result['numeric_evidence_path'])!=result['numeric_evidence_sha256']:
            raise RuntimeError('native numeric evidence changed: '+vid)
    a=RUN/'baseline_a/nontest_e2e_04'
    regression=read(a/'independent_validation.json')
    package=read(a/'package.stage.json')
    if regression['status']!='PASS_INDEPENDENT_STRICT_VALIDATION' or not all(regression['checks'].values()) or package['video_records']!=8 or package['prediction_frames']!=396:
        raise RuntimeError('frozen A non-test regression not passed')
    if sha(a/'candidate_A.zip')!=package['zip_sha256']:
        raise RuntimeError('non-test A package identity changed')
    synthetic=RUN/'baseline_pts_v3/synthetic_decoder_01/synthetic_decoder_receipt.json'
    if read(synthetic)['status']!='PASS_REAL_DECODER_SYNTHETIC_ONLY':
        raise RuntimeError('nonzero-origin real synthetic decoder regression failed')
    hashes=read(CTRL/'a_production_v1_source_hashes.json')
    code=RUN/'baseline_production_v1'
    for name,digest in hashes.items():
        if sha(code/name)!=digest:
            raise RuntimeError('frozen A production source hash changed: '+name)
    policy=read(ROOT/'resource_policy.json')
    planned=536870912
    work=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    free=shutil.disk_usage(ROOT).free
    compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip()
    if compute or (ROOT/'improvement_round1/active_gpu_job.json').exists():
        raise RuntimeError('defer admission until live shared GPU is available')
    if work+planned>policy['added_disk_budget_gib']*2**30 or free<planned:
        raise RuntimeError('real capacity insufficient for measured A scheduling outputs')
    output=RUN/'baseline_a/rematch_temporal_01'
    admission={'schema':'aic_a_rematch_stage_admission_v1','stage':'A_REMATCH426_INFERENCE','authorized':True,
        'admitted_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'A_TEMPORAL_SELECT_SHOTS_ANCHORS_ONLY',
        'manifest_path':str(manifest),'manifest_sha256':sha(manifest),'run_dir':str(output),
        'resource_preflight_pass':True,'shared_gpu_queue_approved':True,'disk_peak_within_80gib':True,
        'budget_runner_required':True,'source_hashes':hashes,'PTS_receipt_sha256':sha(PTS/'pts_origin_receipt.json'),
        'PTS_numeric_sources_checked':426,'non_test_A_receipt_sha256':sha(a/'independent_validation.json'),
        'synthetic_decoder_receipt_sha256':sha(synthetic),'algorithm_config_sha256':sha(code/'config_a.json'),
        'planned_output_bytes':planned,'live_resources':{'work_bytes':work,'free_bytes':free,'compute':compute},
        'single_job_max_seconds':7200,'capacity_reason':'521 frozen 30s windows and CPU frame/anchor scheduling; no model or media copies',
        'space_inference_admitted':False,'formal_C_training_admitted':False,'competition_upload_authorized':False,
        'reason':'all-426 input identity plus unchanged A non-test regression accepted; actual anchor count required before space'}
    with (CTRL/'a_rematch_temporal_01.admission.json').open('x') as handle:
        json.dump(admission,handle,indent=2)
        handle.write('\n')
    print(json.dumps({k:admission[k] for k in ['stage','scope','manifest_sha256','PTS_numeric_sources_checked',
        'space_inference_admitted','competition_upload_authorized']}),flush=True)
