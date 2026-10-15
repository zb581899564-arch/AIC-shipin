"""Independent fixed fresh calls5..10 scheduler; never resumes failed scopes."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import subprocess
import sys

OWN = Path(__file__).resolve().parent
BASE = OWN.parent
ROOT = OWN


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)


gate=read(ROOT/'root_start_admission.json')
assert gate['status']=='ROOT_APPROVED_START_FIXED_SELF_CHECK_CLI33_36'
assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
assert max(json.loads(line)['global_count'] for line in (BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())==32
for number in range(7,11):
    call=ROOT/f'call{number:02d}';fr=read(call/'freeze.json')
    assert not (call/'request.json').exists() and fr['CLI_after']==26+number and fr['timeout_seconds']==7200
    for path,digest in fr['inputs'].items():assert sha(Path(path))==digest
save(OWN/'registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),runner_pid=os.getpid(),runner_command=sys.orig_argv,runner_source_sha256=sha(Path(__file__)),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),fixed_calls=list(range(7,11)),fixed_jobs=list(range(16,24)),CLI_numbers=list(range(33,37)),global_cap=36,automatic_retry=False,cash_cost='UNKNOWN_NOT_ZERO'))


def snapshot24(cli):
    previous = read(BASE / 'remaining_CLI32_36_literal_paths_v1/full_denominator24_after_CLI32.json')
    records = copy.deepcopy(previous['records'])
    assert len(records) == 24
    for number in range(7, 11):
        call = ROOT / f'call{number:02d}'
        index = read(call / 'index.json')
        audit = read(call / 'audit.json') if (call / 'audit.json').exists() else None
        for window in index['windows']:
            report = next((item for item in audit['windows'] if item['window_id'] == window['window_id']), None) if audit else None
            records[window['window_id']]['teacher_observation'] = dict(job_index=window['job_index'], status=report['status'] if report else 'PENDING_NOT_REGISTERED', bound_rows=report['bound_rows'] if report else 0, audit_path=str(call / 'audit.json') if audit else None, audit_sha256=sha(call / 'audit.json') if audit else None, proposal_sha256=report['proposal_sha256'] if report else None, semantic_correctness='PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW')
    save(OWN / f'full_denominator24_after_CLI{cli:02d}.json', dict(utc=datetime.now(timezone.utc).isoformat(), status='ACTUAL_FIXED24_SNAPSHOT_PRIOR_AUTHORITY_PRESERVED', fixed_denominator=24, previous_snapshot=dict(path=str(BASE / 'remaining_CLI32_36_literal_paths_v1/full_denominator24_after_CLI32.json'), sha256=sha(BASE / 'remaining_CLI32_36_literal_paths_v1/full_denominator24_after_CLI32.json')), root_registry=previous['root_registry'], root_qualified_references_at_frozen_registry=previous['root_qualified_references_at_frozen_registry'], records=records, global_CLI_calls=cli, global_CLI_cap=36, failed_job13_not_retried=True, new_optimizer_updates=0, new_426=0, cash_cost='UNKNOWN_NOT_ZERO'))


for number in range(7, 11):
    call = ROOT / f'call{number:02d}'
    assert not (call / 'request.json').exists()
    subprocess.run([sys.executable, '-B', str(ROOT / 'run_pair.py'), str(number)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-B', str(ROOT / 'audit_pair.py'), str(number)], cwd=ROOT, check=True)
    audit = read(call / 'audit.json')
    terminal = read(call / 'terminal.json')
    snapshot24(terminal['CLI_after'])
    save(OWN / f"status_after_CLI{terminal['CLI_after']:02d}.json", dict(utc=datetime.now(timezone.utc).isoformat(), call=number, CLI_after=terminal['CLI_after'], windows=audit['windows'], audit_path=str(call / 'audit.json'), audit_sha256=sha(call / 'audit.json'), terminal_sha256=sha(call / 'terminal.json'), raw_sha256=sha(call / 'stream.jsonl'), actual_result_status=audit.get('actual_result_status'), error_message_steps=audit.get('error_message_steps'), training_admitted=False, cash_cost='UNKNOWN_NOT_ZERO'))
    print(json.dumps(dict(event='FRESH_AFTER_CLI32_TERMINAL_AUDITED', call=number, CLI_after=terminal['CLI_after'], exit_code=terminal['exit_code'], actual_result_status=audit.get('actual_result_status'), windows=[dict(job_index=w['job_index'], status=w['status']) for w in audit['windows']], terminal_sha256=sha(call / 'terminal.json'), raw_sha256=sha(call / 'stream.jsonl')), ensure_ascii=False), flush=True)
    if terminal['exit_code'] != 0 or audit['tool_issues'] or any(window['schema_issues'] or window['proposal_issues'] for window in audit['windows']):
        save(OWN / 'stopped.json', dict(utc=datetime.now(timezone.utc).isoformat(), after_call=number, CLI_after=terminal['CLI_after'], reason='REAL_AUTH_OR_ENGINEERING_FAILURE_NO_AUTOMATIC_RETRY_OR_ADVANCE', pending_calls=list(range(number + 1, 11))))
        sys.exit(2)
    if audit.get('actual_result_status') != 'SUCCESS' or audit.get('reported_nonmedia_errors') or audit.get('errored_tool_attempts') or audit.get('unfinished_tool_attempts'):
        save(OWN / 'awaiting_root.json', dict(utc=datetime.now(timezone.utc).isoformat(), after_call=number, CLI_after=terminal['CLI_after'], reason='COMPLETE_WORK_WITH_REAL_ERROR_REQUIRES_ROOT_REVIEW', pending_calls=list(range(number + 1, 11))))
        sys.exit(3)
save(OWN / 'completion.json', dict(utc=datetime.now(timezone.utc).isoformat(), status='COMPLETE_FIXED8_FRESH_STRUCTURES_PENDING_ROOT_SEMANTIC', fresh_windows=8, total_teacher_expansion_denominator=21, global_CLI_calls=36, failed_job13_not_retried=True, cash_cost='UNKNOWN_NOT_ZERO', training_admitted=False, new_optimizer_updates=0, new_426=0))
