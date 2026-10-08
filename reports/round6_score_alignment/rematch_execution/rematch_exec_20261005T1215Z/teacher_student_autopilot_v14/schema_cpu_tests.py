"""Reproduce the ignored-schema failure in the pinned runtime, then reject it."""
import copy
import itertools
import json
from pathlib import Path
import subprocess

import autopilot_common as c
import teacher_label as t


def check(schema, examples):
    result = subprocess.run([str(c.HERE / 'runtime_schema_check')],
        input=json.dumps({'schema': schema, 'examples': examples}, ensure_ascii=False),
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr + str(json.loads(result.stdout).get('checks'))
    return json.loads(result.stdout)


obs = {'window_id': 'schema_regression', 'window_pts_start_sec': 90.0,
       'window_pts_end_exclusive_sec': 120.0, 'window_duration_sec': 30.0,
       'actual_pts_sec': [90.125, 105.5, 119.75]}
original = c.read(c.RUN / 'next_round_v1/supervision/teacher_response.schema.json')
saved = copy.deepcopy(original)
schema = t.request_schema(original, obs)
assert original == saved
formatted = t.response_format(schema)
assert formatted['json_schema']['schema'] == schema and 'schema' not in formatted
assert len(schema['anyOf']) == 3

scope = {'window_pts_start_sec': 90.0, 'window_pts_end_exclusive_sec': 120.0,
         'sampled_pts_sec': obs['actual_pts_sec'], 'all_provided_frames_reviewed': True}
base = {'window_id': obs['window_id'], 'observation_scope': scope,
        'retained_segments': [{'start_sec': 0.125, 'end_sec': 15.5, 'reason': 'event'}],
        'explicit_no_highlight': False, 'uncertain': False, 'uncertainty_reasons': [],
        'decision_reason': 'Observed event', 'boundary_notes': []}
examples = []
def annotation_text(value):
    order = ('window_id','decision_reason','uncertain','explicit_no_highlight','uncertainty_reasons',
             'observation_scope','retained_segments','boundary_notes')
    # Test the registered grammar's presentation order without altering values.
    arranged = {key:value[key] for key in order if key in value}
    arranged.update({key:item for key,item in value.items() if key not in order})
    return json.dumps(arranged,separators=(',',':'))

for uncertain, empty, segments, reasons in itertools.product(
        [False, True], [False, True], [[], base['retained_segments']], [[], ['unclear']]):
    value = copy.deepcopy(base)
    value.update(uncertain=uncertain, explicit_no_highlight=empty,
                 retained_segments=segments, uncertainty_reasons=reasons)
    expected = ((uncertain and not empty and bool(reasons)) or
                (not uncertain and not reasons and empty and not segments) or
                (not uncertain and not reasons and not empty and bool(segments)))
    examples.append({'text': annotation_text(value), 'expected': expected})
for key in base:
    missing = dict(base); missing.pop(key)
    examples.append({'text': annotation_text(missing), 'expected': False})
for modify in ('string_segment', 'source_clock', 'missing_reason', 'extra_key', 'wrong_scope'):
    bad = copy.deepcopy(base)
    if modify == 'string_segment': bad['retained_segments'].append('wrong type')
    elif modify == 'source_clock': bad['retained_segments'][0]['start_sec'] = 90.125
    elif modify == 'missing_reason': bad['retained_segments'][0].pop('reason')
    elif modify == 'extra_key': bad['extra'] = True
    else: bad['observation_scope']['window_pts_start_sec'] = 0
    examples.append({'text': annotation_text(bad), 'expected': False})
checked = check(schema, examples)
assert 'window_id' in checked['grammar'] and 'explicit_no_highlight' in checked['grammar']

# Replay the real failed v3 response locally on Linux; never modify or salvage it.
manifest = c.read(c.HERE / 'accepted_resume_manifest.json')
for entry in manifest['failed']:
    raw = Path(entry['directory']) / 'raw_answer.txt'
    assert c.sha(raw) == entry['raw_answer_sha256']
    observation = c.read(Path(entry['directory']) / 'decode_receipt.json')
    assert check(t.request_schema(original, observation),
                 [{'text': raw.read_text(), 'expected': False}])['all_examples_match_expectations']

review_schema = t.request_schema(t.REVIEW_SCHEMA, obs)
review = {'window_id': obs['window_id'], 'observation_scope': scope,
          'semantics_consistent': False, 'uncertain': True,
          'reason': 'Cannot support the annotation', 'issues': ['unclear event']}
assert check(review_schema, [{'text': json.dumps(review, separators=(',', ':')), 'expected': True},
                            {'text': '{}', 'expected': False}])['all_examples_match_expectations']
for row in manifest['accepted'].values():
    path = Path(row['directory'])
    assert c.sha(path / 'done.json') == row['done_sha256']
    done = c.read(path / 'done.json')
    assert all(c.sha(path / name) == digest for name, digest in done['files'].items())
report = {'status': 'PASS_PINNED_RUNTIME_TEACHER_SCHEMA_REGRESSION',
          'grammar_examples': len(examples) + len(manifest['failed']) + 2,
          'semantic_states_preserved': 3, 'accepted_v3_receipts': len(manifest['accepted']),
          'rejected_old_failure_not_rewritten': True, 'GPU_used': False,
          'helper_sha256': c.sha(c.HERE / 'runtime_schema_check')}
c.write(c.HERE / 'schema_cpu_acceptance.json', report, fresh=True)
print(json.dumps(report))
