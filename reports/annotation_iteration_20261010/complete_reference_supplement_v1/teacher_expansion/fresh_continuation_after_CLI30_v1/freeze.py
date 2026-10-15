from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

OWN = Path(__file__).resolve().parent
BASE = OWN.parent
ROOT = BASE / 'capacity_v4_tool_batches'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)


metadata = BASE.parent / 'teacher_readonly_models_after_CLI30.json'
assert sha(metadata) == 'c63c2270b6a869f6608d41cfd054e6f1ba9b6ee77608309a6a6fac179b06a21c'
meta = read(metadata)
assert meta['actual_exit_code'] == 0 and meta['teacher_inference_calls_added'] == 0
assert meta['current_selected_model_listed'] == 'gemini-3.8-flash-high' and meta['auth_generation_recovery_not_verified'] is True
stdout_copy = Path(meta['tool_response_copy']['path'])
assert sha(stdout_copy) == meta['tool_response_copy']['sha256']
authorization = OWN / 'root_authorization_record.json'
save(authorization, dict(utc=datetime.now(timezone.utc).isoformat(), provenance='Direct trusted root agent message in this task', instruction='Create independent continuation after CLI30; freeze old call04 terminal/raw/audit/401 classification and actual readonly model metadata; only fixed call05..10/jobs12..23/global31..36, unchanged7200s/model high/4image sequence/whitelist/SHA; never regenerate jobs10/11; no extra probes/login/account/proxy/service changes; any real auth or engineering failure naturally stops. CLI31 actual result validates generation auth; another401 stops without spending other5 calls.', root_code_review_not_claimed=True, authenticated_generation_recovery_not_claimed=True, automatic_retry=False))
ledger = BASE / 'global_CLI_ledger.jsonl'
lines = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()]
assert max(line['global_count'] for line in lines) == 30
prefix = OWN / 'global_CLI30_ledger_prefix.jsonl'
with prefix.open('xb') as output:
    output.write(ledger.read_bytes())
inputs = {}
for path in [Path(__file__), OWN / 'run.py', OWN / 'PROTOCOL.md', authorization, prefix, metadata, stdout_copy, BASE / 'observe_fresh_after_CLI30_receipts.py', BASE / 'audit_actual_tool_batches.py', BASE / 'summarize_actual_partial_terminal.py', BASE / 'continue_capacity_v4_fresh_after_CLI28.py', ROOT / 'fresh_continue_after_CLI28_stopped.json', ROOT / 'full_denominator24_after_CLI30.json', ROOT / 'call04/terminal.json', ROOT / 'call04/stream.jsonl', ROOT / 'call04/audit.json', ROOT / 'call04/engineering_authentication_failure_CLI30.json', ROOT / 'call04/actual_partial_terminal_receipt.json', ROOT / 'call04/w10_completed_scope_audit.json', ROOT / 'call04/w10_completed_scope_stream_prefix.jsonl', ROOT / 'call04/w10_proposal.json']:
    inputs[str(path)] = sha(path)
for path in [OWN / 'run.py', Path(__file__), BASE / 'observe_fresh_after_CLI30_receipts.py']:
    ast.parse(path.read_text(encoding='utf-8-sig'))
checks = []
for number in range(5, 11):
    call = ROOT / f'call{number:02d}'
    freeze = read(call / 'freeze.json')
    assert not (call / 'request.json').exists()
    assert freeze['CLI_after'] == 26 + number and freeze['timeout_seconds'] == 7200 and freeze['automatic_retry'] is False
    assert freeze['fixed_job_indices'] == [2 * number + 2, 2 * number + 3]
    for path, digest in freeze['inputs'].items():
        assert sha(Path(path)) == digest
        inputs[path] = digest
    for path in [call / 'freeze.json', call / 'index.json']:
        inputs[str(path)] = sha(path)
    checks.append(dict(call=number, jobs=freeze['fixed_job_indices'], CLI_after=freeze['CLI_after'], frozen_inputs=len(freeze['inputs']), actual_all_SHA_PASS=True))
binding = OWN / 'binding.json'
save(binding, dict(utc=datetime.now(timezone.utc).isoformat(), status='FROZEN_ROOT_AUTHORIZED_FIXED_FRESH_AFTER_CLI30', runner_sha256=sha(OWN / 'run.py'), inputs=inputs, calls=list(range(5, 11)), jobs=list(range(12, 24)), CLI_numbers=list(range(31, 37)), global_cap=36, timeout_seconds=7200, model='gemini-3.8-flash-high', failed_job11_not_retried=True, successful_job10_not_regenerated=True, model_metadata_not_authenticated_generation_proof=True, automatic_retry=False, new_model_calls_at_freeze=0, cash_cost='UNKNOWN_NOT_ZERO'))
receipt = OWN / 'AST_binding_acceptance.json'
save(receipt, dict(utc=datetime.now(timezone.utc).isoformat(), status='PASS_AST_ACTUAL_FROZEN_SHA_INHERITANCE_NO_MODEL', runner_sha256=sha(OWN / 'run.py'), binding_sha256=sha(binding), checks=checks, old_sources_and_freezes_unchanged=True, readonly_model_metadata_sha256=sha(metadata), original401_classification_sha256=sha(ROOT / 'call04/engineering_authentication_failure_CLI30.json'), new_model_calls=0, new_optimizer_updates=0, new_426=0))
print(json.dumps(dict(runner_sha256=sha(OWN / 'run.py'), binding_sha256=sha(binding), AST_receipt_sha256=sha(receipt), checks=checks, new_model_calls=0), ensure_ascii=False))
