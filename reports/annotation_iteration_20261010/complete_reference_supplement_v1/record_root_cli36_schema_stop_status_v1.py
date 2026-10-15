"""Record a new status receipt; preserve all historical teacher outputs."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
VERSION = ROOT / 'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5'
CALL = VERSION / 'call36'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def binding(path):
    payload = path.read_bytes()
    return {'path': str(path), 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}

registry = read(ROOT / 'denominator24_v17.json')
stop = read(VERSION / 'stopped.json')
assert stop['status'] == 'REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST'
assert not (VERSION / 'call37/request.json').exists()
assert registry['qualified_references'] == 16 and registry['accepted_train_windows'] == 8
assert registry['new_optimizer_updates'] == 0
groups = []
for number in range(4, 16):
    path = CALL / f'w20_group{number:02d}.json'
    document = read(path)
    assert isinstance(document, list) and len(document) == 4
    assert [item['slot'] for item in document] == [0, 1, 2, 3]
    groups.append(binding(path))
proposal_path = CALL / 'w20_proposal.json'
proposal = read(proposal_path)
assert set(proposal) == {'job_index', 'window_id', 'segments', 'events', 'student_visibility', 'limitations'}
assert all('decision' not in segment and 'fact_support' not in segment for segment in proposal['segments'])
assert '学生' in proposal['student_visibility']['description']
output = {
    'status': 'TEACHER_SCHEMA_DRIFT_STOP_NOT_TRAINING_OR_NEW_SUBMISSION',
    'utc': datetime.now(timezone.utc).isoformat(),
    'registry': binding(ROOT / 'denominator24_v17.json'),
    'counts': {key: registry[key] for key in ('fixed_denominator', 'qualified_references', 'rejected_references', 'pending_references', 'accepted_train_windows', 'new_optimizer_updates')},
    'stopped': binding(VERSION / 'stopped.json'),
    'terminal': binding(CALL / 'terminal.json'),
    'actual_cost_receipt': binding(CALL / 'actual_terminal_cost.json'),
    'rejected_scope': binding(CALL / 'w20_completed_scope_audit.json'),
    'raw_group_arrays': groups,
    'proposal': binding(proposal_path),
    'diagnosis': {
        'fact_group_04_through_15': 'Raw arrays violate closed group/items schema. Wrapping alone cannot repair proposal semantics.',
        'proposal': 'Descriptive segmentation lacks KEEP/NO/UNKNOWN, fact_support and boundary uncertainty. Those fields require new grounded semantic work, not invented CPU conversion.',
        'student_visibility': 'Actual description interprets student as classroom identity, instead of the small model processor previews.',
        'original_whole_rejection_preserved': True,
        'cli37_request_exists': False,
        'source_transfer_permission': 'STILL_PENDING_NO_UPLOAD',
        'source_transfer_bytes': 196570456,
        'new_trained_submission_zip': None,
        'historical_best_score': 37.66,
        'historical_score_origin': 'USER_FEEDBACK_NOT_INDEPENDENT_PORTAL_VERIFICATION',
    },
    'actions_this_receipt': 'Read actual schema/terminal/registry and write this separate status only. No model, decoder, optimizer, source upload or old-output mutation.',
}
destination = ROOT / 'root_cli36_schema_stop_status_v1.json'
serialized = json.dumps(output, ensure_ascii=False, indent=2) + '\n'
with destination.open('x', encoding='utf-8', newline='\n') as handle:
    handle.write(serialized)
print(json.dumps(binding(destination), ensure_ascii=False))
