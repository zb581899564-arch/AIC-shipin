"""Small synthetic contract/grammar/baseline/quality checks; no torch or real stages."""
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys
import types

import positive_contract as c
import positive_grammar as g
import positive_metrics as m
from positive_evaluate import assess, validate_export_binding


def rejects(call):
    try:
        call()
    except (ValueError, RuntimeError):
        return
    raise AssertionError('Expected rejection')


def main():
    meta = dict(case_id='view1', source_name='source1', source_sha256='1'*64,
        window_start='0', window_end='15', window_role='overlap', view_roles=['overlap'],
        source_frame_ordinals=list(range(0, 128, 2)), sample_exact_pts=[str(F(i, 5)) for i in range(64)],
        all_source_exact_pts=[str(F(i, 10)) for i in range(151)], physical_end_exact='151/10',
        audio_observed=False, reference_available_to_inference=False)
    event = dict(event_id='dev.B0.example.seg0', original_segment_index=0,
                 original_interval_exact=['1', '10'])
    req = c.request(event, meta, [10, 11, 12, 50, 51])
    assert req['novel_native_ranges'] == [[10, 13], [50, 52]]
    assert req['novel_interval_exact'] == [['1', '13/10'], ['5', '26/5']]
    assert req['novel_visible_sample_counts'] == [2, 1]
    assert req['original_interval_exact'] == ['1', '10']
    assert req['novel_visible_native_samples'][0][0]['ordinal'] == 10
    assert 'EACH listed new part' in c.prompt(req) and 'baseline' in c.prompt(req)
    for decision in c.DECISIONS:
        result = c.resolve('{"decision":"'+decision+'"}', req, execution_status='MODEL_OK')
        assert result['eligible_for_new_addition'] == (decision == 'KEEP')
        assert result['original_interval_exact'] == ['1', '10']
        assert result['baseline_deletion_authorized'] is False
    rejects(lambda: c.resolve('{"decision": "KEEP"}', req, execution_status='MODEL_OK'))
    rejects(lambda: c.resolve('{"decision":"UNKNOWN"}', req, execution_status='FAILED'))
    rejects(lambda: c.request(event, meta, []))
    rejects(lambda: c.request(event, {**meta, 'audio_observed': True}, [10]))
    assert c.native_range(req, meta) == [10, 100]
    # A new run with zero shown samples forbids KEEP in actual finite grammar;
    # this input-evidence uncertainty is not an engineering failure fallback.
    zero = c.request(event, meta, [13])
    assert zero['novel_visible_sample_counts'] == [0] and len(c.responses(zero)) == 2
    rejects(lambda: c.resolve('{"decision":"KEEP"}', zero, execution_status='MODEL_OK'))
    class Tokenizer:
        def get_vocab(self):
            return {chr(i): i for i in range(32, 127)}
        def decode(self, ids, **kwargs):
            return ''.join(chr(i) for i in ids)
    tokenizer = Tokenizer(); eos = [0]
    grammar = g.PositiveConstraint(tokenizer, 2, req, eos)
    for response in c.responses(req):
        prefix = [1000, 1001]
        for token in map(ord, response):
            assert token in grammar(0, prefix)
            prefix.append(token)
        assert grammar(0, prefix) == eos
        assert grammar.assert_complete(prefix[2:]+eos) == {'decision': __import__('json').loads(response)['decision']}
    rejects(lambda: grammar.assert_complete(list(map(ord, '{"decision":"KEEP"'))+eos))
    no_keep = g.PositiveConstraint(tokenizer, 2, zero, eos)
    rejects(lambda: no_keep.assert_complete(list(map(ord, '{"decision":"KEEP"}'))+eos))
    # A forged export cannot change an actual new DROP to KEEP or use a
    # different raw/proof binding while retaining well-formed JSON.
    req.update(group='dev', input_evidence={'signature': 'synthetic'})
    result = c.resolve('{"decision":"DROP"}', req, execution_status='MODEL_OK')
    receipt = dict(case_id=req['request_id'], done_ref={'path': 'done', 'sha256': 'a'*64})
    done = dict(status='PASS_POSITIVE_DECISION_NOT_QUALITY', case_id=req['request_id'], group='dev',
        raw_ref={'path': 'raw', 'sha256': 'b'*64}, decision_result=result, input_evidence=req['input_evidence'])
    firstqa = {'path': 'qa', 'sha256': 'c'*64}
    proof = dict(status='PASS_INDEPENDENT_POSITIVE_OUTPUT_TOKEN_GRAMMAR_PARSER_NATIVE_QA',
        case_id=req['request_id'], group='dev', done_ref=receipt['done_ref'], raw_ref=done['raw_ref'],
        first_input_QA_completion_ref=firstqa, decision_result=result, original_native_range=[10, 100])
    event_output = {key: req[key] for key in ('source_name', 'source_sha256', 'event_id', 'old_event_id',
                                            'original_case_id', 'original_segment_index')}
    event_output.update(decision_result=result, original_native_range=[10, 100])
    validate_export_binding(req, event_output, receipt, done, proof, firstqa)
    forged = {**event_output, 'decision_result': c.resolve('{"decision":"KEEP"}', req, execution_status='MODEL_OK')}
    rejects(lambda: validate_export_binding(req, forged, receipt, done, proof, firstqa))
    rejects(lambda: validate_export_binding(req, event_output, receipt, done,
        {**proof, 'raw_ref': {'path': 'different', 'sha256': 'b'*64}}, firstqa))
    # Check the protected arm against the original pure implementation without
    # importing any real runtime, model, processor or remote data.
    old_stage = sys.modules.get('stage_io')
    dummy = types.ModuleType('stage_io')
    for name in ('read', 'require', 'save', 'sha', 'utc'):
        setattr(dummy, name, lambda *args, **kwargs: None)
    sys.modules['stage_io'] = dummy
    try:
        path = Path(__file__).resolve().parents[1]/'recall_expansion_verify40_46_v1/evaluate_pilot.py'
        spec = importlib.util.spec_from_file_location('_pure_old_metric_check', path)
        original = importlib.util.module_from_spec(spec); spec.loader.exec_module(original)
    finally:
        if old_stage is None:
            del sys.modules['stage_io']
        else:
            sys.modules['stage_io'] = old_stage
    inputs = {'base': dict(window_role='baseline', window_start='0', window_end='30')}
    for decisions in (['KEEP', 'UNKNOWN', 'DROP'], ['DROP']):
        old_events = [dict(event_id='e'+str(i), original_case_id='base', decision_result=dict(
            decision=d, successful_model_call_required=True, original_interval_exact=[str(2+i*5), str(4+i*5)]))
            for i, d in enumerate(decisions)]
        assert m.baseline_prediction(old_events, inputs) == original.source_prediction(old_events, inputs)[0]
    gates = dict(macro_paired_all_rater_duration_F1_delta_min='0', macro_all_rater_recall_delta_min='1/100',
        per_source_F1_delta_min='-1/100', macro_all_rater_precision_delta_min='0', minimum_sources_with_real_new_native_frames=2)
    cases = [dict(baseline=dict(f1=F(1, 2), recall=F(1, 2), precision=F(1, 2)),
        augmented=dict(f1=F(3, 5), recall=F(3, 5), precision=F(1, 2)),
        all_rater_recall_preserved=True, baseline_native_frames_preserved=True, added_native_frames=1) for _ in range(4)]
    conditions, _ = assess(cases, gates)
    assert len(conditions) == 8 and all(conditions.values())
    cases[0]['augmented']['precision'] = F(0)
    conditions, _ = assess(cases, gates)
    assert conditions['macro_precision_not_lower'] is False
    print('PASS: finite positive contract, exact novel native runs, zero-shown KEEP veto, raw grammar, export/GPU/QA tamper veto, protected baseline parity, eight quality gates')


if __name__ == '__main__':
    main()
