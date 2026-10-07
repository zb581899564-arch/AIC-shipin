"""CPU checks for the new diagnostic, including its actual pinned grammar."""
import copy
import json
import itertools
from pathlib import Path
import subprocess
import sys

import diagnostic as d

record = {'window_id': 'context_cpu', 'split': 'train',
          'window': {'window_id': 'context_cpu', 'window_pts_start_sec': 90.0,
                     'window_duration_sec': 30.0},
          'actual_observation': {'window_pts_start_sec': 90.0, 'window_duration_sec': 30.0,
                                 'actual_pts_sec': [90.125, 105.5, 119.75],
                                 'source_frame_ordinals': [10, 20, 30]}}
base = {'window_id': record['window_id'], 'global_visible_summary': 'Source main visible content, CPU fixture',
        'comparison_to_rest': 'Target brings visible main information, CPU fixture',
        'decision_reason': 'Actual visible event has independent value',
        'state': 'POSITIVE', 'evidence': [{'frame_ordinal': 20, 'window_local_sec': '15.5',
                                         'description': 'Visible result'}],
        'retained_segments': [{'start_sec': '0.125', 'end_sec': '15.5', 'reason': 'Visible result'}]}
checks = 0


def expect(value, valid):
    global checks
    try:
        d.validate_result(json.dumps(value, ensure_ascii=False), record)
    except (ValueError, RuntimeError, KeyError, TypeError):
        assert not valid, value
    else:
        assert valid, value
    checks += 1


for count in (1, 2, 63, 64, 65, 719, 720, 10302):
    selected = d.ordinal_sample(count)
    assert selected[0] == 0 and len(selected) == min(count, 64) and len(set(selected)) == len(selected)
    assert selected[-1] == count - 1 and selected == sorted(selected)
    checks += 1
for count, limit in ((0, 64), (-1, 64), (True, 64), (4, 0), (4, True)):
    try: d.ordinal_sample(count, limit)
    except ValueError: pass
    else: raise AssertionError('Invalid source/limit accepted')
    checks += 1

values = []
for state in ('POSITIVE', 'NO_HIGHLIGHT', 'UNCERTAIN'):
    value = copy.deepcopy(base)
    value['state'] = state
    if state != 'POSITIVE': value['retained_segments'] = []
    expect(value, True)
    values.append({'text': json.dumps(value, separators=(',', ':')), 'expected': True})

for wrong in ('source_time', 'mismatched_ordinal', 'bool_ordinal', 'missing_description', 'empty_evidence',
              'positive_without_segments', 'negative_with_segments', 'uncertain_with_segments',
              'out_of_window', 'unprovided_endpoint', 'reverse', 'overlap', 'six_segments',
              'empty_reason', 'wrong_window', 'missing_decision', 'extra_key'):
    value = copy.deepcopy(base)
    if wrong == 'source_time': value['evidence'][0]['window_local_sec'] = '105.5'
    elif wrong == 'mismatched_ordinal': value['evidence'][0]['frame_ordinal'] = 10
    elif wrong == 'bool_ordinal': value['evidence'][0]['frame_ordinal'] = True
    elif wrong == 'missing_description': value['evidence'][0].pop('description')
    elif wrong == 'empty_evidence': value['evidence'] = []
    elif wrong == 'positive_without_segments': value['retained_segments'] = []
    elif wrong == 'negative_with_segments': value['state'] = 'NO_HIGHLIGHT'
    elif wrong == 'uncertain_with_segments': value['state'] = 'UNCERTAIN'
    elif wrong == 'out_of_window': value['retained_segments'][0]['end_sec'] = '30.1'
    elif wrong == 'unprovided_endpoint': value['retained_segments'][0]['start_sec'] = '1.111'
    elif wrong == 'reverse': value['retained_segments'][0].update(start_sec='15.5', end_sec='0.125')
    elif wrong == 'overlap': value['retained_segments'].append(copy.deepcopy(value['retained_segments'][0]))
    elif wrong == 'six_segments': value['retained_segments'] *= 6
    elif wrong == 'empty_reason': value['retained_segments'][0]['reason'] = ''
    elif wrong == 'wrong_window': value['window_id'] = 'other'
    elif wrong == 'missing_decision': value.pop('decision_reason')
    else: value['extra'] = 1
    expect(value, False)

# Grammar enforces paired frame/time identity; it does not prove semantic truth.
for wrong in ('missing_keys', 'bad_state', 'missing_description', 'no_evidence', 'negative_segment', 'extra_key', 'source_endpoint'):
    value = copy.deepcopy(base)
    if wrong == 'missing_keys': value.pop('decision_reason')
    elif wrong == 'bad_state': value['state'] = 'EMPTY_FALLBACK'
    elif wrong == 'missing_description': value['evidence'][0].pop('description')
    elif wrong == 'no_evidence': value['evidence'] = []
    elif wrong == 'negative_segment': value['state'] = 'NO_HIGHLIGHT'
    elif wrong == 'extra_key': value['extra'] = 1
    else: value['retained_segments'][0]['end_sec'] = '105.5'
    values.append({'text': json.dumps(value, separators=(',', ':')), 'expected': False})
for key in ('global_visible_summary','comparison_to_rest'):
    value=copy.deepcopy(base);value.pop(key);expect(value,False)
    values.append({'text':json.dumps(value),'expected':False})

grammar = None
grammar_examples = 0
replay_files = {}
if sys.platform.startswith('linux'):
    def checked(schema, examples):
        global checks, grammar_examples
        result = subprocess.run([str(d.V7 / 'runtime_schema_check')],
                                input=json.dumps({'schema': schema, 'examples': examples}),
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert report['all_examples_match_expectations']
        checks += len(examples); grammar_examples += len(examples)
        return report
    grammar = checked(d.schema(record), values)
    old_root = d.RUN / 'teacher_context_diagnostic_v1/run_01/requests/complete_7757d020fcdef4d4db1f4dbc/WINDOW_ONLY'
    raw_file = old_root / 'raw_answer.txt'
    old_schema_file = old_root / 'generation_schema.json'
    old_raw = raw_file.read_text(encoding='utf-8')
    # The old actual grammar accepted the mismatched pair; no failed text is altered.
    checked(d.c.read(old_schema_file), [{'text': old_raw, 'expected': True}])
    replay_files = {str(p): d.c.sha(p) for p in (raw_file, old_schema_file)}
    selected = d.choose(d.c.rows(d.V7 / 'pilot_01/validated/validated_records.jsonl'))
    for actual in selected:
        observations = actual['actual_observation']
        points = d.t.window_local_points(observations)
        exact = []
        for ordinal, point in zip(observations['source_frame_ordinals'], points):
            value = {'window_id': actual['window_id'], 'global_visible_summary':'Source main visible content, CPU fixture',
                     'comparison_to_rest':'Target brings visible main information, CPU fixture',
                     'decision_reason': 'CPU identity fixture only, no labels',
                     'state': 'POSITIVE',
                     'evidence': [{'frame_ordinal': ordinal, 'window_local_sec': d.clock_text(point), 'description': 'CPU fixture'}],
                     'retained_segments': [{'start_sec': '0.0', 'end_sec': d.clock_text(float(actual['window']['window_duration_sec'])),
                                            'reason': 'CPU fixture'}]}
            assert d.validate_result(json.dumps(value), actual) == value
            exact.append({'text': json.dumps(value), 'expected': True})
        wrong = copy.deepcopy(value)
        wrong['evidence'][0]['window_local_sec'] = d.clock_text(points[0])
        exact.append({'text': json.dumps(wrong), 'expected': False})
        if actual['window_id'] == 'complete_7757d020fcdef4d4db1f4dbc':
            mapping = dict(zip(observations['source_frame_ordinals'], points))
            mismatch = json.loads(old_raw)['evidence'][1]
            assert abs(mapping[mismatch['frame_ordinal']] - mismatch['window_local_sec']) > 0.5
            exact.append({'text': old_raw, 'expected': False})
        checked(d.schema(actual), exact)
    # Reproduce precision loss of numeric constants in this same fixed converter.
    checked({'type': 'object', 'properties': {'time': {'const': 13.782041666666667}}, 'required': ['time']},
            [{'text': '{"time":13.782041666666667}', 'expected': False},
             {'text': '{"time":13.782041666666666}', 'expected': True}])
    review_examples=[]
    for seen,consistent,uncertain in itertools.product((False,True),repeat=3):
        value={'window_id':record['window_id'],'all_provided_frames_reviewed':seen,
               'semantics_consistent':consistent,'uncertain':uncertain,
               'reason':'CPU weak review can refuse or be uncertain','issues':[]}
        review_examples.append({'text':json.dumps(value),'expected':True})
    for key in value:
        missing=dict(value);missing.pop(key)
        review_examples.append({'text':json.dumps(missing),'expected':False})
    checked(d.review_schema(record),review_examples)

report = {'status': 'PASS_CONTEXT_DIAGNOSTIC_CPU' if grammar else 'PASS_LOCAL_SEMANTIC_ONLY_CPU',
          'checks': checks, 'actual_pinned_grammar_examples': grammar_examples,
          'actual_native_endpoints_checked': 256 if grammar else 0,
          'weak_review_can_reject':bool(grammar),
          'failure_replay_files': replay_files,
          'three_decision_states_expressible': bool(grammar), 'GPU_started': False,
          'source_sha256': {name: d.c.sha(d.HERE / name) for name in ('cpu_tests.py', 'diagnostic.py', 'prompt.txt', 'review_prompt.txt', 'PROTOCOL.md')},
          'runtime_helper_sha256': d.c.sha(d.V7 / 'runtime_schema_check') if grammar else None,
          'utc': d.c.utc()}
if grammar: d.c.write(d.HERE / 'cpu_acceptance.json', report, fresh=True)
print(json.dumps(report))
