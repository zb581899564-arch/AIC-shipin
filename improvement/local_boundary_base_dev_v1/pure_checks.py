"""Pure fake-PEFT, grammar and exact-clock oracles; no source execution."""
import argparse
import ast
import contextlib
from fractions import Fraction as F
import importlib
import json
from pathlib import Path
import sys
import types

import bd_contract as c
from driver import generation_arguments, output_denominator


class Parameter:
    def __init__(self, count):
        self.count, self.requires_grad = count, False
    def numel(self):
        return self.count


class FakePEFT:
    """Simulates the actual known PEFT exit grad re-enable fault, no torch."""
    active_adapter = 'default'
    def __init__(self):
        self.layers = [(str(i), types.SimpleNamespace(disable_adapters=False, lora_A={})) for i in range(144)]
        self.parameters = [('base', Parameter(c.BASE_PARAMETERS))]+[
            ('lora_'+str(i), Parameter(c.ADAPTER_PARAMETERS//288)) for i in range(288)]
    def named_modules(self):
        return iter(self.layers)
    def named_parameters(self):
        return iter(self.parameters)
    def requires_grad_(self, value):
        for _, parameter in self.parameters:
            parameter.requires_grad = value
        return self
    @contextlib.contextmanager
    def disable_adapter(self):
        for _, layer in self.layers:
            layer.disable_adapters = True
        try:
            yield
        finally:
            for _, layer in self.layers:
                layer.disable_adapters = False
            for name, parameter in self.parameters:
                if name.startswith('lora_'):
                    parameter.requires_grad = True


class ASCII:
    def get_vocab(self):
        return {chr(i): i for i in range(32, 127)}
    def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        del clean_up_tokenization_spaces
        return ''.join(chr(i) if i != 999 else ('' if skip_special_tokens else '<eos>') for i in ids)


def rejected(callback):
    try:
        callback()
    except (ValueError, RuntimeError):
        return
    raise AssertionError('Malformed case unexpectedly accepted')


def main(code_dir, v4_code, code_sources=None):
    sources = code_sources if code_sources is not None else {
        path.name: path.read_text(encoding='utf-8') for path in Path(code_dir).glob('*.py')}
    for name, source in sources.items():
        ast.parse(source, filename=str(Path(code_dir)/name))
    sys.path.insert(0, str(v4_code))
    contract = importlib.import_module('lb_contract')
    grammar = importlib.import_module('lb_grammar')
    independent = importlib.import_module('replay_local_boundaries')
    structural = importlib.import_module('lb_structural')
    model = FakePEFT()
    initial_inventory = c.inventory(model)
    names = c.layer_state(model, False)['layer_names']
    for _ in range(2):
        before = dict(layer_state=c.layer_state(model, False, names), gradients=c.frozen_gradients(model))
        with model.disable_adapter():
            inside = dict(layer_state=c.layer_state(model, True, names), gradients=c.frozen_gradients(model))
        assert c.gradients(model)['trainable_tensor_count'] == 288
        rejected(lambda: c.frozen_gradients(model))
        restored = c.restore_frozen_gradients(model)
        after = dict(layer_state=c.layer_state(model, False, names), gradients=c.frozen_gradients(model))
        c.validate_restoration(before, inside, after, restored, names)
        assert c.inventory(model) == initial_inventory and restored['before_restore']['trainable_parameters'] == c.ADAPTER_PARAMETERS
    model.layers[0][1].disable_adapters = True
    rejected(lambda: c.layer_state(model, False, names))
    model.layers[0][1].disable_adapters = False
    tampered = dict(after, gradients=dict(trainable_tensor_count=1, trainable_parameters=3, trainable_tensor_names=['bad']))
    rejected(lambda: c.validate_restoration(before, inside, tampered, restored, names))
    # Full original clock, 60fps, every native adjacency1/60, no video/read.
    n = 1800
    pts = [F(i, 60) for i in range(n)]
    clock = dict(original_exact_pts=list(map(str, pts)), normalized_exact_pts=list(map(str, pts)), first_original_pts_exact='0',
        n_frames=n, physical_end_exact='30', last_frame_duration_exact='1/60', source_id='SYN01', source_sha256='a'*64,
        source_bytes=100, physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
                                                        last_normalized_pts_exact=str(pts[-1]), last_frame_duration_exact='1/60'))
    event = dict(event_id='SYN01.E', original_case_id='CH_SYN01_W000', original_segment_index=0,
        original_interval_exact=['5', '11'], source_id='SYN01', source_sha256='a'*64, source_bytes=100,
        source_total_frames=n, all_source_exact_pts=list(map(str, pts)), original_clock_origin_exact='0',
        original_evidence={'clock': {'path': 'synthetic-only', 'sha256': 'b'*64}})
    meta = {**event, **contract.plan_endpoint(event, 'start', clock)}
    meta.update(native_duration_by_ordinal={str(i): '1/60' for i in range(n)},
                continuity_by_sample={str(i): True for i in range(64)}, original_endpoint_continuity_verified=True)
    for decision in ({'decision': 'KEEP'}, {'decision': 'UNKNOWN'},
                     {'decision': 'REFINE', 'sample_index': meta['allowed_sample_indices'][1]}):
        assert contract.resolve_endpoint(decision, meta) == independent.independent_endpoint(decision, meta, clock)
    tokenizer = ASCII()
    text = '{"decision":"UNKNOWN"}'
    ids = list(map(ord, text))+[999]
    constraint = grammar.BoundaryConstraint(tokenizer, 100, meta, [999])
    assert constraint.assert_complete(ids) == {'decision': 'UNKNOWN'}
    rejected(lambda: constraint.assert_complete(list(map(ord, '{"decision":"OTHER"}'))+[999]))
    args = generation_arguments(contract, constraint)
    assert args == dict(do_sample=False, max_new_tokens=contract.MAX_OUTPUT_TOKENS,
                        prefix_allowed_tokens_fn=constraint, return_dict_in_generate=True, output_scores=True)
    assert not ({'past_key_values', 'encoder_outputs', 'inputs_embeds'} & set(args))
    raw = dict(output_token_ids=ids, selected_token_scores=[0.0]*len(ids), generated_score_count=len(ids),
               output_tokens=len(ids), input_tokens=100, eos_token_ids=[999], actual_model_call=True,
               actual_physical_parameters=c.PHYSICAL_PARAMETERS, activated_base_parameters=c.BASE_PARAMETERS)
    assert output_denominator(raw, {'input_tokens': 100}, [999], contract.MAX_OUTPUT_TOKENS) == ids
    rejected(lambda: output_denominator(dict(raw, selected_token_scores=[float('nan')]*len(ids)), {'input_tokens': 100}, [999], contract.MAX_OUTPUT_TOKENS))
    rejected(lambda: output_denominator(dict(raw, input_tokens=99), {'input_tokens': 100}, [999], contract.MAX_OUTPUT_TOKENS))
    # The current predeclared20/40, 37call+3skip partition, never event filtering.
    events = [dict(event_id='E'+str(i), original_case_id='C'+str(i), original_segment_index=0,
                   original_interval_exact=['0', '11']) for i in range(20)]
    skip_ids = {'E0.start', 'E1.start', 'E2.start'}
    requests, skips, endpoints = [], [], {}
    for event in events:
        for side, exact in (('start', '0'), ('end', '11')):
            rid = event['event_id']+'.'+side
            endpoint = dict(request_id=rid, event_id=event['event_id'], side=side, original_endpoint_exact=exact,
                            endpoint_exact=exact, changed=False, displacement_exact='0')
            if rid in skip_ids:
                endpoint.update(applied_decision='UNKNOWN_SHORT_NATIVE_CONTEXT_UNAVAILABLE', actual_model_call=False, predeclared_skip=True)
                skips.append(dict(request_id=rid, structural_status='SHORT_NATIVE_CONTEXT_UNAVAILABLE', actionable=False,
                                  structural_skip=True, actual_context_native_frames=46, endpoint_result=endpoint))
            else:
                endpoint.update(applied_decision='UNKNOWN', actual_model_call=True, predeclared_skip=False)
                requests.append(dict(request_id=rid, actionable=True, structural_skip=False, actual_context_native_frames=360))
            endpoints[rid] = endpoint
    denominators = c.counts(events, requests, skips)
    assert denominators == dict(nominal_endpoints=40, actionable_requests=37, structural_skips=3)
    exported = [independent.independent_event(event, endpoints) for event in events]
    assert len(exported) == 20 and sum(len(e['endpoint_results']) for e in exported) == 40 and all(not e['changed'] for e in exported)
    rejected(lambda: c.counts(events, requests[:-1], skips))
    rejected(lambda: c.counts(events, requests+[requests[0]], skips))
    entries = [dict(request_id=r['request_id'], done_path=r['request_id']+'/done.json', done_sha256='d'*64) for r in requests]
    journal = []
    for i, entry in enumerate(entries, 1):
        journal.extend([dict(event='BEGIN_MODEL_CALL', call_id=i, request_id=entry['request_id']),
                        dict(event='ACCEPTED_MODEL_CALL', call_id=i, **entry)])
    c.validate_journal(journal, [r['request_id'] for r in requests], entries)
    rejected(lambda: c.validate_journal(journal[:-1], [r['request_id'] for r in requests], entries))
    protocol = dict(schema=c.SCHEMA, role='dev', source_root='/S/dev', hypothesis='SAME_INPUT_LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION',
        actual_model_call_budget=37, **denominators, actual_physical_parameters=c.PHYSICAL_PARAMETERS,
        activated_base_parameters=c.BASE_PARAMETERS, disable_time_adapter_layers=144, optimizer_updates=0,
        new_input_processor_encodes=0, new_media_decodes=0, prior_TIME_completed_and_first_input_replay_required=True,
        same_prompt_grammar_native_conversion=True, weight_check_strategy=c.WEIGHT_CHECK_STRATEGY,
        independent_prefill_per_call=True, quality_claim_or_selection_by_this_driver=False, gpu_job_name='new_BASE37')
    c.protocol(protocol, 'dev', Path('/S/dev'), denominators)
    rejected(lambda: c.protocol(dict(protocol, actual_model_call_budget=40), 'dev', Path('/S/dev'), denominators))
    # Static execution surfaces: output replay cannot call any input decoder,
    # encoder, cache loader, AutoProcessor or GPU generation.
    tree = ast.parse(sources['driver.py'])
    replay_node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'replay')
    calls = [x.func.attr if isinstance(x.func, ast.Attribute) else x.func.id if isinstance(x.func, ast.Name) else ''
             for x in ast.walk(replay_node) if isinstance(x, ast.Call)]
    assert not set(calls) & {'encode', 'baseline_frames', 'load_tensor_cache', 'generate', 'AutoProcessor'}
    loop = next(x for x in ast.walk(next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'infer'))
                if isinstance(x, ast.For) and isinstance(x.target, ast.Tuple))
    loop_calls = [x.func.attr if isinstance(x.func, ast.Attribute) else x.func.id if isinstance(x.func, ast.Name) else ''
                  for x in ast.walk(loop) if isinstance(x, ast.Call)]
    assert not set(loop_calls) & {'frozen_identity', 'adapter_identity', 'final_weights'}
    print(json.dumps(dict(status='PASS_BASE_PAIRED_PURE_GRADIENT_PARTITION_TOKEN_NATIVE_CHECKS',
        repeated_contexts=2, observed_PEFT_exit_trainable_tensors=288, explicit_restore_zero=True, all_144_false_true_false=True,
        job_inventory=[c.PHYSICAL_PARAMETERS, c.BASE_PARAMETERS, c.ADAPTER_PARAMETERS],
        unchanged_v4_KEEP_UNKNOWN_REFINE_native_math=True, grammar_valid_unknown=True, bad_output_or_gradients_fail=True,
        nominal_actionable_structural=[40, 37, 3], full_event_export=20, full_endpoint_export=40,
        complete_BEGIN_ACCEPTED=[37, 37], no_prior_KV=True, output_replay_no_input_encoder_or_cache=True,
        no_full_weight_hash_inside_call_loop=True, actual_source_gate_executions=0, actual_plan_runs=0,
        media_reads=0, RGB_decodes=0, processor_encodes=0, model_calls=0, actual_replays=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--code-dir', required=True)
    parser.add_argument('--v4-code', required=True)
    a = parser.parse_args()
    main(a.code_dir, Path(a.v4_code))
