"""Check only the revision02 short-action eligibility correction on Linux."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import sys
import types

payload = json.loads(base64.b64decode(sys.stdin.buffer.readline()))
code = payload['code']
ast.parse(code)
common = types.ModuleType('charades_v2_common')
for name in ('ROOT', 'V1ROOT', 'RUN', 'LEGACY'):
    setattr(common, name, Path('/unused_pure_synthetic'))
common.read = common.save = common.sha = common.utc = common.resource_snapshot = lambda *args: None
common.check_deadline = lambda: None
def require(ok, why):
    if not ok:
        raise ValueError(why)
common.require = require
sys.modules['charades_v2_common'] = common
module = types.ModuleType('pure_short_action')
exec(compile(code, '<revision02_pure_short_action>', 'exec'), module.__dict__)
points = [str(module.F(i, 25)) for i in range(80)]
clock = dict(normalized_exact_pts=points, original_exact_pts=points, first_original_pts_exact='0',
    n_frames=80, native_frames=80, last_frame_duration_exact='1/25', physical_end_exact='16/5',
    positive_last_frame_duration_verified=True, original_zero_origin_verified=True)
actions = [dict(class_id='PURE_SHORT', start_exact='0.0100', end_exact='0.0200'),
           dict(class_id='PURE_LAST_DURATION', start_exact='3.1700', end_exact='3.1900')]
result = module._validate_reference(clock, dict(actions=actions, author_length_raw='3.2'))
require(result['eligible_action_count'] == 2 and result['censored_action_count'] == 0 and
        result['fully_in_domain_without_native_frame_count'] == 2, 'Short fully-domain author action lost eligibility')
require(all(row['eligibility'] == 'FULLY_IN_DOMAIN' and row['scored'] is True and
            row['contains_native_frame'] is False and row['native_range'][0] == row['native_range'][1]
            for row in result['actions']), 'Empty native membership incorrectly changed seconds-proxy scope')
require([row['original_action'] for row in result['actions']] == actions and
        result['whole_source_GT_complete'] is False and
        result['no_native_frame_action_is_visible_highlight_core'] is False,
        'Raw endpoint text or partial proxy semantics changed')
print(json.dumps(dict(status='PASS_REVISION02_NEW_SHORT_ACTION_CASES_ONLY', syntax_files=1,
    short_cases=2, strict_physical_domain_actions_eligible=True, contains_native_frame=False,
    original_text_preserved=True, empty_native_ranges=[row['native_range'] for row in result['actions']],
    no_visible_core_or_complete_GT_claim=True, old_successful_pure01_not_repeated=True,
    real_media_reads=0, real_cache_reads=0, actual_processor_encodes=0, model_calls=0,
    code_bytes=len(code.encode()), code_sha256=hashlib.sha256(code.encode()).hexdigest())))
