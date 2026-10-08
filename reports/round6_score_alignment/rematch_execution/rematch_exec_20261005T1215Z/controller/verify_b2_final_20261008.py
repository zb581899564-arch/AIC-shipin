"""Independently verify the completed Linux B2 artifacts; transfer metadata only."""
from pathlib import Path
import hashlib
import json

from register_b2_package_v1 import remote


RUN = Path(__file__).resolve().parent.parent
RECEIPT = 'B2_v4_final_acceptance_20261008.json'
SCRIPT = r'''
from pathlib import Path
from datetime import datetime, timezone
from itertools import zip_longest
import hashlib, json, socket, subprocess, zipfile

assert socket.gethostname() == 'inspur-NP5570M5'
run = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
entry = run / 'b_score_aligned_package_v4'
lock_sha = '52363b5a6f452ac01a55474eacf6529b80e7c4e4ec3e99868f7d91162fae27db'
adapter_sha = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def rows(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)

completion = read(entry / 'completion.json')
assert completion['stage'] == 'PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX'
assert sha(entry / 'source_lock.json') == completion['source_lock_sha256'] == lock_sha
lock = read(entry / 'source_lock.json')
assert len(lock['files']) == 571
assert sha(entry / 'config.json') == lock['files'][str(entry / 'config.json')]
config = read(entry / 'config.json')
assert completion['new_optimizer_updates'] == config['new_optimizer_updates'] == 0
assert completion['new_T_training_started'] is config['new_T_training_started'] is False
assert completion['temporal_adapter_sha256'] == config['b_adapter_sha256'] == adapter_sha
assert completion['teacher_quality_stop_preserved'] is True
assert completion['automatic_return'] is completion['uploaded'] is False
assert completion['official_score'] is None

scopes = {}
for scope, count, frames in [('nontest', 8, 444), ('rematch', 426, 105075)]:
    out = entry / (scope + '_01')
    inputs = config['inputs'][scope]
    assert sha(inputs['manifest']) == inputs['manifest_sha256']
    assert sha(inputs['registry']) == inputs['registry_sha256']
    manifest = read(inputs['manifest'])
    expected = {row['video_id'] for row in manifest['records']}
    assert len(manifest['records']) == len(expected) == count
    package = read(out / 'package.stage.json')
    strict = read(out / 'independent_validation.json')
    assert package['status'] == 'PASS_COMPLETE_B2_8B_PACKAGE_ON_LINUX'
    assert package['video_records'] == count and package['issues'] == []
    assert package['weak_roi_inputs_used'] == package['old_test_boxes_used'] == package['silent_fallbacks'] == 0
    assert package['complete_pipeline_parameters'] == 8782459120
    assert strict['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION'
    assert len(strict['checks']) == 11 and all(value is True for value in strict['checks'].values())
    assert strict['missing'] == strict['extra'] == strict['duplicate_frames'] == 0
    assert strict['video_records'] == count
    assert strict['expected_frames'] == strict['prediction_frames'] == package['prediction_frames'] == frames
    candidate = out / 'candidate_B2_8B.zip'
    assert str(candidate) == package['candidate']
    assert candidate.stat().st_size == package['zip_bytes']
    assert sha(candidate) == package['zip_sha256'] == strict['zip_sha256']
    with zipfile.ZipFile(candidate) as archive:
        assert archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
        member = archive.read('predictions.jsonl')
    assert member == (out / 'predictions.jsonl').read_bytes()
    assert hashlib.sha256(member).hexdigest() == package['predictions_sha256'] == strict['predictions_sha256']
    assert sha(out / 'provenance.jsonl') == strict['provenance_sha256']
    ids = [row['video_id'] for row in rows(out / 'predictions.jsonl')]
    assert len(ids) == len(set(ids)) == count and set(ids) == expected
    assert sum(1 for _ in rows(out / 'selected.jsonl')) == frames
    scopes[scope] = dict(videos=count, prediction_frames=frames, strict_checks=strict['checks'],
        independent_report_sha256=sha(out / 'independent_validation.json'),
        manifest_sha256=inputs['manifest_sha256'], registry_sha256=inputs['registry_sha256'],
        candidate=str(candidate), zip_bytes=candidate.stat().st_size, zip_sha256=sha(candidate),
        predictions_sha256=hashlib.sha256(member).hexdigest(), provenance_sha256=strict['provenance_sha256'],
        crc_pass=True, archive_names=['predictions.jsonl'], archive_roundtrip_exact=True,
        source_ids_exact=True, duplicate_source_ids=0)

out = entry / 'rematch_01'
assert scopes['rematch']['zip_bytes'] == completion['zip_bytes'] == 317401
assert scopes['rematch']['zip_sha256'] == completion['zip_sha256'] == '0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3'
assert completion['candidate'] == scopes['rematch']['candidate']
assert completion['predictions_sha256'] == scopes['rematch']['predictions_sha256']
assert completion['independent_validation_sha256'] == scopes['rematch']['independent_report_sha256']
assert completion['nontest_package_receipt_sha256'] == sha(entry / 'nontest_01/package.stage.json')
time = read(out / 'temporal.stage.json')
assert time['status'] == 'PASS_TEMPORAL_EXECUTION' and (time['videos'], time['windows'], time['invalid_windows']) == (426, 521, 0)
assert sha(out / 'temporal.jsonl') == time['output_sha256'] == '9437a04e53c1c3f6aa623a8cbc8ec4f29051a396e1b2af5baf438ef70ef4971f'
assert (time['original_successful_windows_reused'], time['original_record_raw_lines_exact'], time['new_generation_calls'], time['failures_to_empty_conversions']) == (520, 425, 1, 0)
schedule = read(out / 'schedule.stage.json')
assert (schedule['selected_frames'], schedule['field_frames'], schedule['anchors']) == (105075, 234158, 31295)
assert schedule['temporal_selection_used_for_boundaries'] is False
for name, field in [('field_frames.jsonl', 'field_frames_sha256'), ('field_shots.jsonl', 'shots_sha256'), ('anchor_requests.jsonl', 'requests_sha256')]:
    assert sha(out / name) == schedule[field]
anchors = 0
for request, result in zip_longest(rows(out / 'anchor_requests.jsonl'), rows(out / 'anchor_output.jsonl')):
    assert request is not None and result is not None
    assert result['status'] == 'MODEL_OK' and result['used_fallback'] is False
    assert all(result[key] == request[key] for key in ('video_id', 'source_frame', 'anchor_request_sha256'))
    assert result['decoded_pixel_sha256'] == request['expected_pixel_sha256']
    anchors += 1
space = read(out / 'spatial.stage.json')
assert space['status'] == 'PASS_STRICT_SOURCE_FIELD_SPATIAL'
assert anchors == space['rows'] == space['model_calls'] == 31295 and space['invalid'] == 0
assert space['failure_to_empty_conversions'] == 0 and space['time_adapter_enabled'] is False
assert space['base_hash']['sha256'] == '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'

ledger = list(rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl'))
resources = {}
for name in ('rematch_B2_v4_rematch_recover_01', 'rematch_B2_v4_rematch_spatial_01'):
    path = run / 'controller' / (name + '.resource.json')
    receipt = read(path)
    matching = [row for row in ledger if row.get('name') == name]
    assert len(matching) == 1 and matching[0] == receipt
    assert receipt['status'] == 'completed' and receipt['exit_code'] == 0 and receipt['stop_reason'] is None
    resources[name] = dict(receipt_sha256=sha(path), charged_seconds=receipt['charged_seconds'],
        sampled_peak_memory_mib=receipt['sampled_peak_memory_mib'], ledger_exact=True)
provider = run / 'b_score_aligned_package_v1'
assert read(provider / 'completion.json')['stage'] == 'STOP_B2_PACKAGE_V1'
assert sha(provider / 'rematch_01/temporal.stage.json') == 'd077ca5d3017ad25f387b6a4479fe0300620104c79d11b88b4002a3695e21ffb'
assert sha(out / 'recovered_raw/97_0.json') == 'df9ff18d3f2ce92b3ffd082f73fdee52c622aa0ede85778be814f977a584b636'
ps = subprocess.check_output(['ps', '-eo', 'args'], text=True)
owned = [line for line in ps.splitlines() if str(entry) + '/' in line or 'gpu_run.py --name rematch_B2_v4' in line]
assert owned == []

receipt = dict(status='PASS_INDEPENDENT_B2_FINAL_ZIP_ACCEPTANCE', utc=datetime.now(timezone.utc).isoformat(),
    host=socket.gethostname(), entry=entry.name, source_lock_sha256=lock_sha, frozen_files=571,
    verifier_source_sha256='__VERIFIER_SHA__', completion_sha256=sha(entry / 'completion.json'),
    completion_stage=completion['stage'], scopes=scopes, anchors_verified=anchors,
    temporal_videos=426, temporal_windows=521, invalid_temporal_windows=0,
    original_successful_windows_unchanged=520, original_successful_record_lines_unchanged=425,
    actual_recovered_windows=1, failures_to_empty_conversions=0, original_provider_stop_preserved=True,
    whole_source_field_frames=234158, source_field_precedes_temporal_filter=True,
    resources=resources, owned_processes=[], actual_training=completion['actual_training'],
    temporal_adapter_sha256=adapter_sha, complete_pipeline_parameters=8782459120,
    new_T_training_started=False, new_optimizer_updates=0, official_score=None,
    teacher_quality_stop_preserved=True, per_frame_data_exported=False, raw_answers_exported=False,
    automatic_return=False, uploaded=False, large_file_transfers=0)
body = (json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
path = run / 'controller/B2_v4_final_acceptance_20261008.json'
with path.open('xb') as stream:
    stream.write(body)
print(body.decode('utf-8'), end='')
'''


def main():
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    body = remote(SCRIPT.replace('__VERIFIER_SHA__', source_sha), echo=False)
    receipt = json.loads(body)
    assert receipt['status'] == 'PASS_INDEPENDENT_B2_FINAL_ZIP_ACCEPTANCE'
    assert receipt['verifier_source_sha256'] == source_sha
    with (RUN / 'controller' / RECEIPT).open('xb') as stream:
        stream.write(body)
    print(json.dumps(dict(status=receipt['status'], receipt=RECEIPT, bytes=len(body),
        sha256=hashlib.sha256(body).hexdigest(), zip=receipt['scopes']['rematch']), ensure_ascii=False))


if __name__ == '__main__':
    main()
