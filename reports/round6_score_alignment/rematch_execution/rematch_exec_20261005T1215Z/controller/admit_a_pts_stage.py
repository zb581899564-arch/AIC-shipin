"""Main supervisor evidence gates for the repaired A-PTS snapshot.

No framework import, model inference or media decoding. Admissions are
exclusive and bind receipts, inputs, source snapshot and the measured resource
estimate. Competition upload and formal C training remain disabled.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL, CODE = RUN/'controller', RUN/'baseline_a_pts_v1'
M0_SHA = '57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32'
N8_SHA = '7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a'
OLD_PRED_SHA = '607392e7b2f60743ef841661cf84a3d560c8e570ca93bc674f2c6450c89fbb43'
OLD_PROV_SHA = '1ea2d03078c517ed9c61d8172e5d1f3433191d8d72b7ea6f70b90b4f111b547e'

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def evidence(processor_name, decoder_name, lock):
    processor_path = CODE/processor_name/'processor_receipt.json'
    processor = read(processor_path)
    require(processor['status'] == 'PASS_ACTUAL_PROCESSOR_SYNTHETIC_ONLY'
        and processor['source_lock_sha256'] == lock and len(processor['records']) == 4
        and all(r['pass'] and r['processor_instance_restored'] for r in processor['records']),
        'all-four installed processor cases not accepted on this snapshot')
    decoder_path = CODE/decoder_name/'decoder_test_receipt.json'
    decoder = read(decoder_path)
    require(decoder['status'] == 'PASS_REAL_CPU_SYNTHETIC_NATIVE_DECODER_IDENTITY'
        and decoder['runtime_identity']['source_lock_sha256'] == lock
        and decoder['runtime_identity']['test_sha256'] == sha(CODE/'test_decoder_synthetic.py')
        and len(decoder['cases']) == 2
        and {c['case'] for c in decoder['cases']} == {'cfr_zero_origin','vfr_gap_nonzero_origin'}
        and all(c['source_frames_checked'] == 80 and c['temporal_sampled_frames_checked'] == 64
            and c['shot_descriptor_matches_frozen'] and c['independent_spatial_reopen_pixel_sha_matches']
            and c['single_last_physical_frame_padding_checked'] and c['expected_stop_cases'] >= 8
            for c in decoder['cases']), 'independent actual marker decoder identity not accepted')
    for result in (processor, decoder):
        require(result['GPU_used'] is False and result['models_run'] is False
            and result['contest_media_read'] is False and result['labels_read'] is False,
            'synthetic identity test scope changed')
    return {'synthetic_processor_pass': True, 'synthetic_decoder_pass': True,
        'synthetic_processor_evidence_path': str(processor_path),
        'synthetic_processor_evidence_sha256': sha(processor_path),
        'synthetic_decoder_evidence_path': str(decoder_path),
        'synthetic_decoder_evidence_sha256': sha(decoder_path)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['nontest','temporal','space'])
    parser.add_argument('--expected-source-lock', required=True)
    parser.add_argument('--processor-name', required=True)
    parser.add_argument('--decoder-name', required=True)
    parser.add_argument('--nontest-name', default='nontest_e2e_02')
    parser.add_argument('--rematch-name', default='rematch_e2e_01')
    args = parser.parse_args()
    require(re.fullmatch('[0-9a-f]{64}', args.expected_source_lock), 'invalid source digest')
    for value in (args.processor_name,args.decoder_name,args.nontest_name,args.rematch_name):
        require(re.fullmatch('[a-z][a-z0-9_]+', value), 'output/evidence names must stay in CODE')
    sys.path.insert(0, str(CODE))
    from pts_contract import load_clocks, legacy_manifest, window_schedule
    from run_pts import verify_vendor
    require(sha(CODE/'source_lock.json') == args.expected_source_lock, 'admitted source snapshot changed')
    verify_vendor()
    authorization = read(CTRL/'authorization.json')
    require(authorization['competition_upload_authorized'] is False
        and 'complete rematch baseline generation after input contract and regression' in authorization['scope'],
        'generation authorization absent')
    identity = evidence(args.processor_name,args.decoder_name,args.expected_source_lock)
    pts_dir = RUN/'baseline_pts_v4'/('nontest_registry_01' if args.mode == 'nontest' else 'scan_01')
    receipt = read(pts_dir/'reaudit_receipt.json')
    count = 8 if args.mode == 'nontest' else 426
    require(receipt['status'] == 'PASS_ALL_SOURCE_CLOCK_BRANCHES_METADATA_ONLY'
        and receipt['expected_count'] == count and not receipt['failed_video_ids'],
        'all-source clock metadata gate absent')
    manifest_path, registry_path = Path(receipt['clean_manifest']['path']), Path(receipt['clock_registry']['path'])
    require(sha(manifest_path) == receipt['clean_manifest']['sha256']
        and sha(registry_path) == receipt['clock_registry']['sha256'], 'clock input changed')
    manifest = read(manifest_path)
    clocks = load_clocks(manifest,registry_path,sha(registry_path))
    original = RUN/('baseline_a/inputs/non_test_frozen8.json' if count == 8
        else 'baseline_a/m0_finalize_01/clean_manifest_426.json')
    require(sha(original) == (N8_SHA if count == 8 else M0_SHA), 'original input identity changed')
    old_rows = {r['video_id']:r for r in read(original)['records']}
    projected = legacy_manifest(manifest)['records']
    for row in projected:
        old = old_rows[row['video_id']]
        expected = dict(old)
        if clocks[row['video_id']]['branch'] == 'NATIVE_PTS':
            # The old manifest computed n / float(fps); the legacy spatial
            # projection computes n*den/num. These two binary64 expressions
            # differ for two native sources. Bind both exact expressions,
            # while the real native window endpoint stays packet-PTS based.
            rational_legacy_end = old['n_frames']*old['fps_den']/old['fps_num']
            require(old['scope_start_sec'] == 0 and old['scope_end_sec'] in
                (rational_legacy_end,old['n_frames']/(old['fps_num']/old['fps_den'])),
                'original native source was not registered for its complete historical scope')
            expected['scope_end_sec'] = rational_legacy_end
        require(row == expected, 'source metadata changed beyond the registered native scope projection')
    if count == 8:
        require(receipt['cfr_eligible_sources'] == 8 and receipt['native_non_cfr_usable_sources'] == 0,
            'non-test denominator must remain the original eight CFR sources')
    else:
        require(receipt['cfr_eligible_sources'] == 416 and receipt['native_non_cfr_usable_sources'] == 10,
            'complete rematch clock branch denominator changed')
    nontest = CODE/args.nontest_name
    if args.mode != 'nontest':
        regression = read(nontest/'independent_validation.json')
        package = read(nontest/'package.stage.json')
        require(regression['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION'
            and all(regression['checks'].values()) and package['source_lock_sha256'] == args.expected_source_lock
            and package['video_records'] == 8 and package['prediction_frames'] == 396
            and sha(nontest/'predictions.jsonl') == OLD_PRED_SHA
            and sha(nontest/'provenance.jsonl') == OLD_PROV_SHA
            and sha(nontest/'candidate_A_PTS.zip') == package['zip_sha256'] == regression['zip_sha256'],
            'new snapshot full NONTEST8 must independently pass and exactly reproduce old A')
        # ZIP member timestamps differ between separate runs. The scientific
        # regression requires identical prediction/provenance bytes; each new
        # archive keeps its own independently validated whole-file identity.
        with zipfile.ZipFile(nontest/'candidate_A_PTS.zip') as archive:
            require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
                and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == OLD_PRED_SHA,
                'new ZIP content differs from the exact original non-test predictions')
        identity.update(non_test_e2e_pass=True, non_test_evidence_path=str(nontest/'independent_validation.json'),
            non_test_evidence_sha256=sha(nontest/'independent_validation.json'))
    name = {'nontest':'a_pts_nontest_02','temporal':'a_pts_temporal_01','space':'a_pts_space_01'}[args.mode]
    stages = {'nontest':['preflight','temporal','select','shots','anchors','spatial','compose','package'],
        'temporal':['preflight','temporal','select','shots','anchors'],
        'space':['spatial','compose','package']}[args.mode]
    run_dir = nontest if args.mode == 'nontest' else CODE/args.rematch_name
    planned = 268435456 if args.mode == 'nontest' else 536870912
    max_seconds = 1800 if args.mode == 'nontest' else 7200
    capacity_reason = 'fixed NONTEST8, previous actual 396 selected frames and 68 anchors; receipts and small ZIP only'
    scheduling = None
    if args.mode == 'temporal':
        windows = sum(len(window_schedule(row,manifest['kind'],clocks[row['video_id']])) for row in manifest['records'])
        require(windows == 521, 'registered temporal window count changed')
        capacity_reason = '521 frozen temporal windows on all426, then CPU source-frame and anchor scheduling; no space yet'
    if args.mode == 'space':
        temporal_resource_path = CTRL/'rematch_a_pts_temporal_01.resource.json'
        temporal_resource = read(temporal_resource_path)
        require(temporal_resource['status'] == 'completed' and temporal_resource['exit_code'] == 0
            and temporal_resource['stop_reason'] is None, 'temporal shared-runner completion not accepted')
        selection, shots, anchors = [read(run_dir/(s+'.stage.json')) for s in ('select','shots','anchors')]
        requests = rows(run_dir/'anchor_requests.jsonl')
        selected = rows(run_dir/'selected.jsonl')
        require(selection['selected_frames'] == shots['frames'] == anchors['selected_frames'] == len(selected)
            and anchors['anchor_calls'] == len(requests) and len(requests) > 0
            and all(read(run_dir/(s+'.stage.json'))['source_lock_sha256'] == args.expected_source_lock
                for s in ('preflight','temporal','select','shots','anchors')),
            'complete admitted scheduling outputs missing or changed')
        require(sha(run_dir/'selected.jsonl') == shots['selected_sha256']
            and sha(run_dir/'anchor_requests.jsonl') == anchors['output_sha256'], 'scheduled outputs changed')
        per_anchor = read(nontest/'spatial.stage.json')['wall_seconds']/68
        max_seconds = math.ceil(per_anchor*len(requests)*1.8+1200)
        inputs_size = sum((run_dir/f).stat().st_size for f in ('selected.jsonl','shots.jsonl','anchor_requests.jsonl'))
        planned = inputs_size*3 + len(selected)*1536 + len(requests)*4096 + 33554432
        capacity_reason = f'actual {len(selected)} selected frames and {len(requests)} anchors; measured NONTEST8 space cost {per_anchor:.6f}s/anchor with explicit teardown/decode margin'
        scheduling = {'selected_frames':len(selected),'anchor_requests':len(requests),
            'measured_non_test_seconds_per_anchor':per_anchor,
            'estimated_space_seconds_without_margin':per_anchor*len(requests),
            'selected_sha256':sha(run_dir/'selected.jsonl'), 'requests_sha256':sha(run_dir/'anchor_requests.jsonl'),
            'completed_temporal_resource_sha256':sha(temporal_resource_path)}
    policy = read(ROOT/'resource_policy.json')
    work = int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    free = shutil.disk_usage(ROOT).free
    compute = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip()
    require(not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists(),
        'defer until the live shared GPU has no conflicting task')
    require(work+planned <= policy['added_disk_budget_gib']*2**30 and free >= planned,
        'current capacity cannot cover this registered job output estimate')
    admission = dict(variant='A_NATIVE_PTS_COMPAT_V1', authorized=True,
        stage='A_PTS_NONTEST_E2E' if count == 8 else 'A_PTS_REMATCH426_INFERENCE',
        admitted_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        scope={'nontest':'NONTEST_ALL_STAGES','temporal':'REMATCH_TEMPORAL_SCHEDULING','space':'REMATCH_SPACE_AND_PACKAGE'}[args.mode],
        allowed_stages=stages, space_inference_admitted=args.mode != 'temporal',
        manifest_path=str(manifest_path), manifest_sha256=sha(manifest_path),
        clock_registry_path=str(registry_path), clock_registry_sha256=sha(registry_path),
        source_lock_sha256=args.expected_source_lock, clock_evidence_sha256=sha(pts_dir/'reaudit_receipt.json'),
        run_dir=str(run_dir), resource_preflight_pass=True, shared_gpu_queue_approved=True,
        disk_peak_within_80gib=True, budget_runner_required=True,
        planned_output_bytes=planned, single_job_max_seconds=max_seconds, capacity_reason=capacity_reason,
        live_resources=dict(work_bytes=work,free_bytes=free,compute=compute), scheduling=scheduling,
        native_branch_model_inference_admitted=count == 426, formal_C_training_admitted=False,
        competition_upload_authorized=False,
        data_use_basis='authorized current rematch inference; frozen NONTEST8 engineering retains prior provenance/use uncertainty',
        **identity)
    with (CTRL/(name+'.admission.json')).open('x') as stream:
        json.dump(admission,stream,indent=2)
        stream.write('\n')
    print(json.dumps({'name':name,'scope':admission['scope'],'sources':count,'planned_output_bytes':planned,
        'single_job_max_seconds':max_seconds,'scheduling':scheduling,'upload_authorized':False}),flush=True)
