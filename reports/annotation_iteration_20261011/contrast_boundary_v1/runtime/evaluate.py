"""One final-only B-versus-new comparison on pre-registered non-test windows."""
import argparse
from fractions import Fraction as F
from pathlib import Path
import traceback
from common import admit, bound, helpers, read, require, save, sha, INITIAL_SHA, verify_lock
from native_runtime import encode, native_ranges
from model_binding import load_model
from objective import classify
from scientific_gate import summarize, gate


def validate_final(contract, receipt_path, expected_sha):
    require(sha(receipt_path) == expected_sha, 'final training receipt SHA differs')
    r = read(receipt_path)
    require(r['status'] == 'PASS_FIXED_NATIVE64_SILVER_SFT_ENGINEERING_ONLY' and r['training_complete'] is True and
        r['lock_sha256'] == contract['lock_sha'] and r['config_sha256'] == contract['config_sha'] and
        r['optimizer_steps'] == contract['schedule']['updates'] and r['saved_tensor_identity_count'] == 288 and
        r['initial_loaded_tensor_equality_count']==288 and
        r['changed_final_lora_tensors'] > 0 and r['finite_losses'] is True and r['first_step_nonzero_gradients'] is True,
        'complete fixed final training evidence absent')
    final = Path(r['final_adapter_dir']).resolve(strict=True)
    require(final == (Path(contract['config']['train_output_dir'])/'final_adapter').resolve(strict=True), 'foreign/early checkpoint')
    require(sha(final/'adapter_model.safetensors') == r['final_adapter_sha256'] and
            sha(final/'adapter_config.json') == r['final_adapter_config_sha256'] and
            r['final_adapter_sha256'] != INITIAL_SHA, 'final adapter binding differs')
    return final, r


def attempt(model, processor, encoded, evidence, window, raw_path, candidates):
    import torch
    from constrained_json import make_prefix_constraint
    from contracts import parse_segments
    prefix = int(encoded['input_ids'].shape[1]); duration = F(window['domain_end_exact'])-F(window['domain_start_exact'])
    constraint = make_prefix_constraint(processor.tokenizer, prefix, duration, candidate_token_ids=candidates,
        eos_token_ids=model.generation_config.eos_token_id, allow_empty=True)
    try:
        with torch.inference_mode():
            generated = model.generate(**encoded.to('cuda:0'), do_sample=False, max_new_tokens=256,
                prefix_allowed_tokens_fn=constraint, return_dict_in_generate=True, output_scores=True)
        ids = generated.sequences[0, prefix:]
        raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        selected = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
        import math
        save(raw_path, dict(raw_output=raw, output_token_ids=ids.tolist(),
            selected_token_scores=[x if math.isfinite(x) else str(x) for x in selected],
            input_tokens=prefix, actual_model_call=True, video_identity=evidence, window=window,
            grammar_stats=constraint.stats))
        require(selected and all(map(math.isfinite, selected)), 'nonfinite generation scores')
        constraint.assert_complete(ids)
        parsed, errors, warnings = parse_segments(raw, duration, allow_empty=True)
        require(parsed is not None and not errors, 'original parser rejected: '+repr(errors))
        result = classify(raw, duration)
        require(result['status'] in ('MODEL_OK', 'LEGAL_EMPTY') and
                result['parsed_segments'] == [[F(str(a)), F(str(b))] for a, b in parsed], 'exact/original parser mismatch')
        result.update(raw_receipt=str(raw_path), raw_sha256=sha(raw_path), parse_warnings=warnings,
                      native_frame_ranges=native_ranges(result['parsed_segments'], window))
        return result
    except BaseException as exc:
        save(str(raw_path)+'.failure.json', dict(status='STOP_ACTUAL_GENERATION_OR_VALIDATION_FAILURE',
            failure_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc(),
            raw_receipt_exists=Path(raw_path).exists(), failure_converted_to_empty=False))
        raise


def execute(contract, final, final_receipt_sha):
    import gc
    import torch
    c = contract['config']; out = Path(c['evaluate_output_dir']); out.mkdir(parents=True, exist_ok=False)
    report = dict(reference_kind='CONTRAST_BOUNDARY_NATIVE_SILVER_V1',status='RUNNING_FINAL_ONLY_NONTEST_EVALUATION', new_optimizer_updates=0,
        final_training_receipt_sha256=final_receipt_sha, lock_sha256=contract['lock_sha'],
        config_sha256=contract['config_sha'], predictions={}, quality_claim=False,
        final_only=True, official_submission_authorized=False)
    try:
        student, video, sft, smoke = helpers(c)
        from constrained_json import ascii_token_candidates
        for arm, adapter in (('original_B', c['initial_adapter_dir']), ('new_final', final)):
            model, processor, unused, frozen = load_model(contract, sft, smoke, adapter, False)
            candidates = ascii_token_candidates(processor.tokenizer); rows = {}
            folder = out/arm; folder.mkdir(exist_ok=False)
            for ix, key in enumerate(c['final_only_evaluation_window_ids']):
                encoded, evidence = encode(contract, key, processor, video)
                result = attempt(model, processor, encoded, evidence, contract['jobs'][key]['window'],
                                 folder/('%02d.raw.json'%ix), candidates)
                save(folder/('%02d.done.json'%ix), dict(window_id=key, arm=arm, adapter_sha256=sha(Path(adapter)/'adapter_model.safetensors'),
                    reference_sha256=contract['reference_sha'][key], **result))
                rows[key] = result; del encoded
            report['predictions'][arm] = rows
            require(smoke.canonical_frozen_hash(model, torch) == frozen, 'evaluation changed frozen base bytes')
            del model, processor, unused; gc.collect(); torch.cuda.empty_cache()
        summaries = {}
        for arm, predictions in report['predictions'].items():
            summaries[arm] = {}
            for role in ('process_dev', 'locked_evaluation'):
                rows = {k: p for k, p in predictions.items() if contract['jobs'][k]['role'] == role}
                summaries[arm][role] = summarize(contract['jobs'], contract['refs'], rows, contract['quality'], contract['events'], role)
        b, n = summaries['original_B'], summaries['new_final']
        scientific = gate(b['process_dev'], n['process_dev'], b['locked_evaluation'],
                          n['locked_evaluation'], contract['quality'],contract['protocol'])
        save(out/'scientific_gate.json', scientific)
        verify_lock(contract['lock_path'], contract['lock_sha'])
        report.update(status='PASS_FINAL_ONLY_EVALUATION_ENGINEERING', scientific_status=scientific['status'],
            scientific_gate_sha256=sha(out/'scientific_gate.json'), summaries=summaries,
            model_calls=contract['protocol']['counts']['evaluation_model_calls'], quality_gate_passed=scientific['status'] == 'PASS_FIXED_SILVER_QUALITY_GATE')
    except BaseException as exc:
        report.update(status='STOP_FINAL_ONLY_EVALUATION_ENGINEERING', failure_type=type(exc).__name__, failure=str(exc),
            traceback=traceback.format_exc(), failure_converted_to_empty=False, quality_gate_passed=False)
        save(out/'evaluation_receipt.json', report)
        raise
    save(out/'evaluation_receipt.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True); p.add_argument('--lock', required=True)
    p.add_argument('--expected-lock', required=True); p.add_argument('--final-receipt', required=True)
    p.add_argument('--expected-final-receipt', required=True); p.add_argument('--check-only', action='store_true')
    args = p.parse_args(); contract = admit(args.config, args.lock, args.expected_lock, 'evaluate')
    final, receipt = validate_final(contract, args.final_receipt, args.expected_final_receipt)
    if args.check_only:
        print(__import__('json').dumps(dict(status='PASS_STATIC_FINAL_ONLY_ADMISSION',
            windows=len(contract['config']['final_only_evaluation_window_ids']), arms=2, model_started=False, decoder_started=False, processor_started=False)))
        return 0
    result = execute(contract, final, args.expected_final_receipt)
    return 0 if result['quality_gate_passed'] else 5


if __name__ == '__main__':
    raise SystemExit(main())
