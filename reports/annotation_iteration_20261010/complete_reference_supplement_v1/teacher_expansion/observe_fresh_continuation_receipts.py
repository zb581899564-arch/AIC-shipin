"""Read-only stream observation plus one-time independent CPU receipts.

Does not launch teachers or change any frozen scheduler, request, or input.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'capacity_v4_tool_batches'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(event, **values):
    print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), event=event, **values), ensure_ascii=False), flush=True)


def run(script, *args):
    result = subprocess.run([sys.executable, '-B', str(script), *map(str, args)], cwd=BASE, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        emit('CPU_RECEIPT_FAILURE_NO_MODEL_RETRY', script=str(script), exit_code=result.returncode, stderr=result.stderr[-2000:], stdout=result.stdout[-2000:])
        raise SystemExit(result.returncode)


last_progress = 0.0
while True:
    active = None
    for number in range(3, 11):
        call = ROOT / f'call{number:02d}'
        if not (call / 'request.json').exists():
            continue
        index = read(call / 'index.json')
        first = index['windows'][0]
        prefix_audit = call / f"w{first['job_index']:02d}_completed_scope_audit.json"
        proposal_done = False
        done_tools = 0
        for line in (call / 'stream.jsonl').read_text(encoding='utf-8-sig').splitlines():
            try:
                step = json.loads(line).get('step_update', {})
            except json.JSONDecodeError:
                break
            if step.get('step_type') == 'tool' and step.get('state') == 'DONE':
                done_tools += 1
                if step.get('tool_name') == 'write_to_file' and step.get('tool_info', {}).get('parameters', {}).get('TargetFile') == first['proposal_path']:
                    proposal_done = True
        if proposal_done and not prefix_audit.exists():
            run(ROOT / 'audit_completed_window.py', number, first['job_index'])
            evidence = read(prefix_audit)
            emit('FIRST_SCOPE_CPU_AUDIT_SAVED', call=number, job_index=first['job_index'], status=evidence['status'], audit_path=str(prefix_audit), audit_sha256=sha(prefix_audit), proposal_sha256=sha(Path(first['proposal_path'])))
        terminal = call / 'terminal.json'
        audit = call / 'audit.json'
        receipt = call / 'actual_partial_terminal_receipt.json'
        if terminal.exists() and audit.exists() and not receipt.exists():
            run(BASE / 'audit_actual_tool_batches.py', call)
            run(BASE / 'summarize_actual_partial_terminal.py', call)
            final = read(audit)
            emit('TERMINAL_CPU_RECEIPTS_SAVED', call=number, CLI_after=read(terminal)['CLI_after'], exit_code=read(terminal)['exit_code'], result=final.get('actual_result_status'), windows=[dict(job_index=w['job_index'], status=w['status'], bound_rows=w['bound_rows'], proposal_sha256=w['proposal_sha256']) for w in final['windows']], errors=final.get('error_message_steps'), tool_issues=final['tool_issues'], terminal_sha256=sha(terminal), raw_sha256=sha(call / 'stream.jsonl'), audit_sha256=sha(audit), actual_receipt_sha256=sha(receipt), batch_receipt_sha256=sha(call / 'actual_tool_batch_audit.json'), cash_cost='UNKNOWN_NOT_ZERO')
        if not terminal.exists():
            active = dict(call=number, CLI_after=read(call / 'freeze.json')['CLI_after'], DONE_tools=done_tools)
    stop = next((ROOT / name for name in ('fresh_continue_after_CLI28_completion.json', 'fresh_continue_after_CLI28_stopped.json', 'fresh_continue_after_CLI28_awaiting_root.json') if (ROOT / name).exists()), None)
    if stop:
        emit('FROZEN_RUNNER_TERMINAL_OBSERVED', path=str(stop), sha256=sha(stop))
        break
    if time.monotonic() - last_progress >= 300:
        emit('ACTUAL_ACTIVE_PROGRESS', active=active)
        last_progress = time.monotonic()
    time.sleep(10)
