"""At most six original-B calls plus six candidate verifier calls; training=0."""
import json
import math
import time
import traceback
from fractions import Fraction
from pathlib import Path
from runtime import (HERE, RUN, sha, save, b_engine, EMPTY_PROMPT, parse_segments,
                     baseline_frames, context_frames, encode, REFINEMENT_PROMPT)
from contract import context_domain, sample_domain, intersection


def generate(model, processor, encoded, evidence, duration, output, candidates):
    import torch
    from constrained_json import make_prefix_constraint
    prefix = int(encoded['input_ids'].shape[1])
    grammar = make_prefix_constraint(processor.tokenizer, prefix, duration,
        candidate_token_ids=candidates, eos_token_ids=model.generation_config.eos_token_id, allow_empty=True)
    start = time.monotonic()
    with torch.inference_mode():
        result = model.generate(**encoded.to('cuda'), do_sample=False, max_new_tokens=256,
            prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
    torch.cuda.synchronize()
    ids = result.sequences[0, prefix:]
    raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    scores = [float(score[0, int(token)]) for score, token in zip(result.scores, ids)]
    receipt = dict(raw_output=raw, output_token_ids=ids.tolist(),
        selected_token_scores=[x if math.isfinite(x) else str(x) for x in scores],
        input_tokens=prefix, output_tokens=len(ids), generation_seconds=time.monotonic()-start,
        input_evidence=evidence, constraint_stats=grammar.stats, actual_model_call=True)
    save(output, receipt)  # Raw precedes grammar/parser/finite-score acceptance.
    if not scores or not all(math.isfinite(x) for x in scores):
        raise ValueError('invalid actual selected-token scores')
    grammar.assert_complete(ids)
    segments, errors, warnings = parse_segments(raw, duration, allow_empty=True)
    if segments is None or errors:
        raise ValueError('original strict parser rejected '+repr(errors))
    return segments, dict(raw_path=str(output), raw_sha256=sha(output), parse_warnings=warnings)


def main():
    import torch
    import numpy as np
    from constrained_json import ascii_token_candidates
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = json.loads((HERE/'source_lock.json').read_text())
    for path, digest in lock['files'].items():
        if sha(path) != digest:
            raise ValueError('frozen experiment input changed: '+path)
    admission = json.loads((HERE/'mechanism_scope.json').read_text())
    if (admission['scope'] != 'LIMITED_VISUAL_FACT_MECHANISM_DIAGNOSTIC_ONLY'
            or not admission['limited_mechanism_admitted'] or admission['max_model_calls'] != 12
            or admission['quality_pass_allowed'] or admission['training_admitted'] or admission['rematch_admitted']):
        raise ValueError('bounded non-quality diagnostic scope is not admitted')
    entries = json.loads((HERE/'inputs.json').read_text())
    if len(entries) != 6 or len({e['case_id'] for e in entries}) != 6:
        raise ValueError('six source denominator changed')
    proofs = {p['case_id']: p for p in json.loads((HERE/'baseline_cpu_acceptance.json').read_text())['proofs']}
    meta = [json.loads(Path(e['input_path']).read_text()) for e in entries]
    for r in meta:
        if sha(r['source_path']) != r['source_sha256']:
            raise ValueError('source file SHA changed')
    config = json.loads((RUN/'b_score_aligned_package_v4/config.json').read_text())
    model, processor, identity = b_engine.load_model(config)
    save(HERE/'model_identity.json', dict(identity=identity, selected_time_adapter_enabled=True,
        new_optimizer_updates=0, same_model_for_both_arms=True))
    candidates = ascii_token_candidates(processor.tokenizer)
    rows = []
    for r in meta:
        case = r['case_id']
        folder = HERE/case
        baseline = baseline_frames(r)
        lo, hi = Fraction(r['window_start']), Fraction(r['window_end'])
        enc, evidence = encode(processor, r, baseline, lo, EMPTY_PROMPT)
        if evidence != proofs[case]['input_evidence']:
            raise ValueError('actual baseline processor differs from CPU acceptance')
        save(folder/'baseline_request.json', dict(text=EMPTY_PROMPT, source_start=str(lo), source_end=str(hi),
            ordinals=baseline[1], exact_pts=baseline[2], cached_array=r['frame_array_path']))
        segments, call = generate(model, processor, enc, evidence, hi-lo, folder/'baseline_raw.json', candidates)
        del enc
        refined = segments
        row = dict(case_id=case, source_sha256=r['source_sha256'], baseline_segments=segments,
            baseline_call=call, refinement_call=None, candidate_only=True)
        domain = context_domain(segments, lo, hi)
        if domain is not None:
            a, b = domain
            ids = sample_domain(r['all_source_exact_pts'], a, b)
            reused = ids == baseline[1]
            frames = baseline if reused else context_frames(r, ids)
            if reused:
                cache = r['frame_array_path']
            else:
                cache = str(folder/'context_frames.npz')
                np.savez_compressed(cache, rgb=frames[0])
            offset = float(a-lo)
            proposed = [[s-offset, e-offset] for s, e in segments]
            prompt = REFINEMENT_PROMPT.format(candidates=json.dumps(proposed, separators=(',', ':')), duration=float(b-a))
            save(folder/'refinement_request.json', dict(text=prompt, source_start=str(a), source_end=str(b),
                ordinals=ids, exact_pts=frames[2], cached_array=cache, candidate_context_local=proposed,
                array_sha256=sha(cache), new_sampling_not_repeated_original_decode=not reused))
            enc, detail = encode(processor, r, frames, a, prompt)
            values, verify_call = generate(model, processor, enc, detail, b-a, folder/'refinement_raw.json', candidates)
            del enc
            # This explicit registered candidate intersection is the algorithm,
            # not output repair. Both untouched outputs remain in raw receipts.
            shifted = [[s+offset, e+offset] for s, e in values]
            refined = intersection(shifted, segments)
            row.update(refinement_call=verify_call, context_source_start=str(a), context_source_end=str(b),
                context_frames=len(ids), baseline_frames=64, original_frames_reused=reused,
                proposed_before_candidate_intersection=shifted)
        row['refined_segments'] = refined
        save(folder/'prediction.json', row)
        rows.append(row)
        print(json.dumps(dict(case_id=case, baseline=segments, refined=refined)), flush=True)
    save(HERE/'inference_completion.json', dict(status='PASS_BOUNDED_INFERENCE_NOT_QUALITY', rows=rows,
        actual_model_calls=sum(1+(r['refinement_call'] is not None) for r in rows), new_optimizer_updates=0,
        new_426_inference=0, official_score=None, source_lock_sha256=sha(HERE/'source_lock.json'),
        reference_labels_read=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        save(HERE/'failure.json', dict(status='STOP_NO_RETRY_NO_EMPTY_FALLBACK',
            error=type(exc).__name__+': '+str(exc), traceback=traceback.format_exc()))
        raise
