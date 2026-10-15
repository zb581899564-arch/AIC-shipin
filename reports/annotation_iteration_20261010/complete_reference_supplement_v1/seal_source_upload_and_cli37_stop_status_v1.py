"""Record completed source transfer and actual blocked teacher terminal."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
T = R / 'teacher_expansion' / 'prospective_CLI37_schema_local_v2'
A = T / 'call37'
def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def bind(path):
    path = Path(path).resolve(strict=True)
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

upload_path = R / 'source_transfer_completed_v1' / 'upload_validation_receipt.json'
upload = read(upload_path)
assert upload['status'] == 'PASS_FIXED12_SOURCE_UPLOAD_EXTRACTION_ALL_SHA_NOT_TRAINING'
assert upload['source_count'] == 12 and upload['zip_bytes'] == 196570456
assert upload['all_CRC_and_source_SHA_pass'] is True and upload['all_extracted_file_SHA_pass'] is True
assert upload['training_started'] is False
terminal = read(A / 'terminal.json')
audit = read(A / 'audit.json')
cost = read(A / 'actual_terminal_cost.json')
assert terminal['exit_code'] == 3 and terminal['child_process_created'] is True
assert audit['status'] == 'REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST'
assert audit['actual_result_status'] == 'ERROR'
assert audit['actual_result_error'] == 'FAILED_PRECONDITION (code 400): User location is not supported for the API use.'
assert audit['actual_result_usage']['total_tokens'] == 0
assert cost['terminal_sha256'] == bind(A / 'terminal.json')['sha256']
assert cost['raw_sha256'] == bind(A / 'stream.jsonl')['sha256'] == terminal['stream_sha256']
ledger_path = R / 'teacher_expansion' / 'global_CLI_ledger.jsonl'
ledger = [json.loads(line) for line in ledger_path.read_text(encoding='utf-8-sig').splitlines()]
actual = [row for row in ledger if row.get('task') == T.name+'/call37']
assert len(actual) == 2 and [row['event'] for row in actual] == ['REGISTERED','TERMINAL']
assert actual[-1]['terminal_sha256'] == bind(A / 'terminal.json')['sha256']
registry_path = R / 'denominator24_v18.json'
registry = read(registry_path)
assert (registry['qualified_references'],registry['rejected_references'],registry['pending_references'],registry['accepted_train_windows']) == (17,4,3,8)
assert all(not Path(group['output_path']).exists() for window in read(A / 'index.json')['windows'] for group in window['groups'])
best = R.parents[2] / 'deliveries' / 'ANNOTATION_ITERATION_20261010' / 'SAFE_37_66' / 'candidate_SAFE_37_66.zip'
# R is PROJECT/reports/annotation_iteration/complete_reference; parents[2] is PROJECT.
assert best.stat().st_size == 306167
assert bind(best)['sha256'] == '07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
status = dict(status='SOURCE_UPLOAD_ACCEPTED_TEACHER37_REGION_ERROR_TRAINING_BLOCKED_BEST_PRESERVED',
    utc=datetime.now(timezone.utc).isoformat(),source_transfer=bind(upload_path),
    reference_registry=bind(registry_path),qualified_references=17,rejected_references=4,pending_references=3,
    accepted_train_windows=8,teacher_request=bind(A / 'request.json'),actual_terminal=bind(A / 'terminal.json'),
    actual_whole_audit=bind(A / 'audit.json'),actual_cost=bind(A / 'actual_terminal_cost.json'),
    actual_global_ledger=bind(ledger_path),unique_registered_and_terminal=True,
    error=audit['actual_result_error'],actual_usage=audit['actual_result_usage'],cash_cost='UNKNOWN_NOT_ZERO',
    no_video_or_image_read_in_CLI37=True,no_new_labels_in_CLI37=True,no_automatic_retry=True,no38=True,
    training_started=False,new_optimizer_updates=0,new_426_generation=False,
    remaining_fixed_jobs=[21,22,23],current_best_zip=bind(best),current_best_bytes=best.stat().st_size,
    current_best_score=37.66,score_source='USER_REPORTED_PREVIOUS_PORTAL_DONE_NOT_NEW_SCORE',
    local_proxy_listener_readonly_check='127.0.0.1:7892 FlClashCore PID8344 LISTENING at 2026-10-11T07:38Z',
    provider_region_error_origin='EXACT_PROVIDER_ERROR; account/location/routing cause not independently resolved',
    old_successful_data_and_references_preserved=True,source=bind(__file__))
output = R / 'source_upload_and_cli37_stop_status_v1.json'
with output.open('x',encoding='utf-8') as stream:
    json.dump(status,stream,ensure_ascii=False,indent=2)
print(json.dumps({'status_receipt':bind(output),'status':status['status'],'upload_complete':True,'training_started':False},ensure_ascii=False))
