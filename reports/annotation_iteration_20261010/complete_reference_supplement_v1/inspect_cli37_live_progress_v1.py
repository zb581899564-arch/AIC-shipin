"""Bounded read-only progress; incomplete observations are never accepted."""
import json
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent / 'teacher_expansion' / 'prospective_CLI37_schema_local_v2'
A = R / 'call37'
def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

result = {'utc': datetime.now(timezone.utc).isoformat(), 'CLI':37, 'training_started':False}
raw = (A / 'stream.jsonl').read_bytes() if (A / 'stream.jsonl').exists() else b''
rows = []
for line in raw.splitlines():
    try:
        rows.append(json.loads(line))
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
updates = [x['step_update'] for x in rows if x.get('step_update', {}).get('step_type') == 'tool']
done = {x['step_index']:x for x in updates if x.get('state') == 'DONE'}
errors = [x for x in updates if x.get('state') == 'ERROR']
result.update(raw_bytes=len(raw), unique_tool_DONE=len(done), actual_raw_ERROR=len(errors))
if updates:
    update = updates[-1]
    params = update.get('tool_info', {}).get('parameters', {})
    result['last_tool'] = {'step_index':update.get('step_index'), 'state':update.get('state'),
        'name':update.get('tool_name'), 'target_name':Path(params.get('AbsolutePath', params.get('TargetFile', ''))).name}
result['windows'] = []
for window in read(A / 'index.json')['windows']:
    entry = {'job_index':window['job_index'], 'fact_groups_written':sum(Path(g['output_path']).is_file() for g in window['groups']),
        'proposal_written':Path(window['proposal_path']).is_file()}
    audit = A / ('w%02d_completed_scope_audit.json' % window['job_index'])
    entry['scope_status'] = read(audit)['status'] if audit.is_file() else 'PENDING_ACTUAL_SCOPE'
    result['windows'].append(entry)
for name in ('owned_stop_request.json','terminal.json','audit.json','actual_terminal_cost.json'):
    if (A / name).is_file():
        actual = read(A / name)
        result[name] = {key:actual.get(key) for key in ('status','exit_code','stop_reason','wall_seconds','reason') if key in actual}
for name in ('stopped.json','completion.json'):
    if (R / name).is_file():
        result[name] = read(R / name)
result['observer_stderr_bytes'] = (R / 'observer.stderr.txt').stat().st_size
result['controller_stderr_bytes'] = (R / 'controller.stderr.txt').stat().st_size
print(json.dumps(result,ensure_ascii=False))
