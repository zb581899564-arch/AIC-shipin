"""Fresh 426/521 final-adapter temporal calls, conditional on independent quality."""
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from fractions import Fraction as F

from common import bound, read, require, save, sha, verify_lock
import candidate_support as cs


def estimate_output_bytes(contract):
    """CPU/static estimate from actual fixed input files; no decoder/model imports.

    Includes full field interpolation intermediates, uncompressed predictions,
    ZIP upper bound, 521 raw/input/done and independent replay receipts. The
    result estimates output bytes; it is never a capacity admission threshold.
    """
    spec = read(cs.locked_ref(contract, contract['config']['candidate_contract']))
    plan = read(cs.locked_ref(contract, spec['plan']))
    require(plan['records'] == 426 and plan['windows'] == 521, 'estimate denominator differs')
    counts = [len(p['window']['planned_source_frame_ordinals']) for j in plan['jobs'] for p in j['windows']]
    require(len(counts) == 521 and all(1 <= n <= 64 for n in counts), 'estimate native input budget differs')
    sizes = {k: cs.locked_ref(contract, spec['space'][k]).stat().st_size
             for k in ('field_frames', 'field_shots', 'anchor_requests', 'anchor_output')}
    evidence = cs.locked_ref(contract, spec['changed_cpu_acceptance']).stat().st_size
    eval_dir = Path(contract['config']['evaluate_output_dir'])
    raw_done = [p.stat().st_size for arm in ('original_B', 'new_final')
                for kind in ('raw', 'done') for p in (eval_dir/arm).glob('*.'+kind+'.json')]
    require(len(raw_done) == 48, 'actual 24 evaluation raw/done sizes required')
    # Per-frame evidence retains hashes/PTS; output tokens are bounded at256.
    window_sizes = [len(__import__('json').dumps(p['window'], ensure_ascii=False, allow_nan=False).encode('utf-8'))
                    for j in plan['jobs'] for p in j['windows']]
    attempt_budget = max(raw_done)+max(raw_done)+max(1, evidence//116)+3*max(window_sizes)
    attempt_budget += max(counts)*256 + 256*128
    # A selected frame can retain an interpolated provenance line and an
    # official box line. Full-field source paths dominate the actual source
    # line sizes; two such measured copies cover both JSON projections.
    field_projection = 2*sum(sizes.values())
    zip_and_predictions = 2*sizes['field_frames']
    estimate = 521*4*attempt_budget + field_projection + zip_and_predictions
    require(type(estimate) is int and estimate > 0, 'invalid actual output estimate')
    return estimate


def attempt(model, processor, encoded, input_receipt, a, raw_path, candidates, binding, balanced_native):
    import torch
    from constrained_json import make_prefix_constraint
    prefix = int(encoded['input_ids'].shape[1])
    constraint = make_prefix_constraint(processor.tokenizer, prefix, cs.duration(a),
        candidate_token_ids=candidates, eos_token_ids=model.generation_config.eos_token_id, allow_empty=True)
    started = time.monotonic()
    with torch.inference_mode():
        generated = model.generate(**encoded.to('cuda:0'), do_sample=False, max_new_tokens=256,
            prefix_allowed_tokens_fn=constraint, return_dict_in_generate=True, output_scores=True)
    torch.cuda.synchronize()
    ids = generated.sequences[0, prefix:]
    raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
    # Exclusive raw bytes precede every validation. A bad answer is retained.
    save(raw_path, dict(binding=binding, raw_output=raw, output_token_ids=ids.tolist(),
        selected_token_scores=[x if math.isfinite(x) else str(x) for x in scores], input_tokens=prefix,
        actual_model_call=True, final_adapter_enabled=True, overview_adapter_disabled=True,
        window=a['window'], video_identity=input_receipt['video_identity'], input_receipt=cs.ref(input_receipt['path']),
        generation_seconds=time.monotonic()-started, grammar_stats=constraint.stats,
        eos_token_ids=model.generation_config.eos_token_id))
    require(1 <= len(ids) == len(scores) <= 256 and all(map(math.isfinite, scores)), 'actual tokens/scores invalid')
    constraint.assert_complete(ids)
    return cs.result(raw, a, input_receipt['video_identity'], balanced_native)


def validate_loaded_final(model, prepared):
    """Actual288 loaded LoRA bytes equal current final safetensors, before use."""
    import torch
    from safetensors.torch import load_file
    weights = prepared['final']/'adapter_model.safetensors'
    require(sha(weights) == prepared['training']['final_adapter_sha256'], 'current final weights changed before tensor binding')
    payload = load_file(str(weights), device='cpu')
    actual = {name.replace('.default.', '.'): p.detach().cpu()
              for name, p in model.named_parameters() if 'lora_' in name}
    require(set(payload) == set(actual) and len(actual) == 288 and
        all(payload[name].dtype == actual[name].dtype and torch.equal(payload[name], actual[name]) and
            bool(torch.isfinite(actual[name]).all()) for name in payload), 'loaded actual final288 tensor identity differs')
    require(set(model.peft_config) == {'default'} and model.active_adapters == ['default'],
            'fresh final default adapter must be the sole active adapter')
    return 288


def execute(prepared, args):
    from model_binding import load_model
    import torch
    from constrained_json import ascii_token_candidates
    c = prepared['contract']['config']; out = Path(c['candidate_output_dir'])
    out.mkdir(parents=True, exist_ok=False); (out/'attempts').mkdir()
    save(out/'candidate_start.json', dict(binding=prepared['binding'], utc=cs.utc(), records=426,
        planned_fresh_temporal_model_calls=521, old_temporal_outputs_reused=0, new_spatial_model_calls=0))
    try:
        m = prepared['modules']
        model, processor, unused, frozen = load_model(prepared['contract'], m['sft'], m['smoke'], prepared['final'], False)
        loaded_equal = validate_loaded_final(model, prepared)
        candidates = ascii_token_candidates(processor.tokenizer); records = []
        for a in prepared['attempts']:
            ip, rp, dp = cs.attempt_paths(out, a['ordinal'])
            encoded, evidence = cs.encode(prepared, a, processor)
            save(ip, dict(binding=prepared['binding'], actual_native_processor_input=True, **evidence))
            value = attempt(model, processor, encoded, dict(**evidence, path=str(ip)), a, rp, candidates,
                            prepared['binding'], m['native'])
            save(dp, dict(binding=prepared['binding'], video_id=a['video_id'], index=a['index'], ordinal=a['ordinal'],
                final_adapter_sha256=prepared['training']['final_adapter_sha256'], input=cs.ref(ip), raw=cs.ref(rp), **value))
            records.append(dict(ordinal=a['ordinal'], input=cs.ref(ip), raw=cs.ref(rp), done=cs.ref(dp)))
            del encoded
            if a['ordinal'] == 0:
                # A separate process reconstructs actual native pixels,
                # processor tensors, generated tokens and original parser.
                first = out/'first_real_cpu_replay.json'
                env = dict(os.environ, CUDA_VISIBLE_DEVICES='')
                command = [sys.executable, '-B', str(Path(__file__).with_name('candidate_replay.py'))]
                command += cs.cli_args(args)+['--output', str(first), '--first-only']
                with (out/'first_real_cpu_replay.log').open('x', encoding='utf-8') as stream:
                    subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
                receipt = read(first); cs.same_binding(receipt, prepared)
                require(receipt['status'] == 'PASS_FIRST_REAL_FINAL_TEMPORAL_INDEPENDENT_CPU_REPLAY' and
                    receipt['attempts_reconstructed'] == 1 and receipt['CUDA_initialized'] is False,
                    'first real independent CPU replay absent')
            print(__import__('json').dumps(dict(stage='CANDIDATE_FRESH_TEMPORAL', completed=len(records), total=521)), flush=True)
        require(m['smoke'].canonical_frozen_hash(model, torch) == frozen, 'candidate modified frozen base')
        require(validate_loaded_final(model, prepared) == loaded_equal, 'inference changed loaded final288 bytes')
        require(sha(prepared['final']/'adapter_model.safetensors') == prepared['training']['final_adapter_sha256'],
                'candidate modified final adapter')
        verify_lock(prepared['contract']['lock_path'], prepared['contract']['lock_sha'])
        report = dict(status='PASS_ALL_521_FRESH_FINAL_TEMPORAL_MODEL_CALLS', utc=cs.utc(), binding=prepared['binding'],
            records=426, fresh_temporal_model_calls=len(records), changed_window_calls=116, unchanged_window_calls=405,
            final_adapter_sha256=prepared['training']['final_adapter_sha256'], saved_tensor_identity_count=288,
            actual_loaded_final_tensor_equality_count=loaded_equal,
            old_temporal_outputs_reused=0, new_spatial_model_calls=0, new_optimizer_updates=0,
            first_real_cpu_replay=cs.ref(out/'first_real_cpu_replay.json'), attempts=records)
        save(out/'engine_receipt.json', report)
        return report
    except BaseException as exc:
        cs.failure(out/'engine_failure.json', exc)
        raise


def main():
    args = cs.parser().parse_args(); prepared = cs.entry(args, 'candidate')
    report = execute(prepared, args)
    print(__import__('json').dumps({k: report[k] for k in ('status', 'records', 'fresh_temporal_model_calls')}))


if __name__ == '__main__':
    main()
