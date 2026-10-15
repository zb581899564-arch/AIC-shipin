"""Independent CPU native/processor/token/grammar/parser replay; never loads model."""
import math
import os
from pathlib import Path
from fractions import Fraction as F
import sys

from common import read, require, save, sha, verify_lock, bound
import candidate_support as cs


def reconstruct_one(prepared, a, processor, candidates):
    import torch
    from constrained_json import make_prefix_constraint, BoundedSegmentsGrammar
    out = Path(prepared['contract']['config']['candidate_output_dir'])
    ip, rp, dp = cs.attempt_paths(out, a['ordinal'])
    original_input, raw, done = read(ip), read(rp), read(dp)
    for r in (original_input, raw, done):
        cs.same_binding(r, prepared)
    require(done['ordinal'] == a['ordinal'] and done['video_id'] == a['video_id'] and done['index'] == a['index'] and
        done['input'] == cs.ref(ip) and done['raw'] == cs.ref(rp) and
        done['final_adapter_sha256'] == prepared['training']['final_adapter_sha256'] and
        raw['input_receipt'] == cs.ref(ip) and raw['actual_model_call'] is True and
        raw['final_adapter_enabled'] is True and raw['overview_adapter_disabled'] is True and
        raw['window'] == a['window'], 'actual fresh raw/input/done identity differs')
    encoded, observed = cs.encode(prepared, a, processor)
    require(original_input == dict(binding=prepared['binding'], actual_native_processor_input=True, **observed),
        'independent actual native/processor tensor reconstruction differs')
    require(raw['video_identity'] == observed['video_identity'] and raw['input_tokens'] == int(encoded['input_ids'].shape[1])
            and raw['input_tokens'] <= 16384, 'actual raw input identity differs')
    ids, scores = raw['output_token_ids'], raw['selected_token_scores']
    require(1 <= len(ids) == len(scores) <= 256 and all(type(t) is int and t >= 0 for t in ids) and
        all(type(x) in (int, float) and math.isfinite(x) for x in scores), 'actual token/score budget differs')
    require(processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False) == raw['raw_output'],
            'actual tokens do not decode to actual saved raw')
    # Generation EOS identity comes from locked base generation config; a raw
    # receipt is not allowed to invent a different termination alphabet.
    generation = read(Path(prepared['contract']['config']['model_dir'])/'generation_config.json')
    eos = generation['eos_token_id']
    require(raw['eos_token_ids'] == eos, 'actual EOS differs from locked base generation config')
    duration = cs.duration(a)
    grammar = make_prefix_constraint(processor.tokenizer, raw['input_tokens'], duration,
        candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
    prefix = encoded['input_ids'][0].tolist()
    for token in ids:
        require(token in grammar(0, torch.tensor(prefix, dtype=torch.long)), 'actual generated token violates original prefix grammar')
        prefix.append(token)
    grammar.assert_complete(ids)
    require(BoundedSegmentsGrammar(duration, allow_empty=True).complete(raw['raw_output']), 'actual raw grammar incomplete')
    result = cs.result(raw['raw_output'], a, observed['video_identity'], prepared['modules']['native'])
    require(done == dict(binding=prepared['binding'], video_id=a['video_id'], index=a['index'], ordinal=a['ordinal'],
        final_adapter_sha256=prepared['training']['final_adapter_sha256'], input=cs.ref(ip), raw=cs.ref(rp), **result),
        'GPU done differs from independent exact/parser/native reconstruction')
    require(not torch.cuda.is_initialized(), 'independent replay initialized CUDA')
    return dict(ordinal=a['ordinal'], input=cs.ref(ip), raw=cs.ref(rp), done=cs.ref(dp), result=result,
        actual_native_processor_tensors_equal=True, actual_token_grammar_parser_native_equal=True)


def replay(prepared, output, first_only=False):
    import torch
    from transformers import AutoProcessor
    from constrained_json import ascii_token_candidates
    out = Path(prepared['contract']['config']['candidate_output_dir']).resolve()
    output = Path(output).resolve()
    require(output.parent == out and not output.exists(), 'fresh candidate CPU replay output required')
    require(not torch.cuda.is_initialized() and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
        'independent CPU replay requires CUDA_VISIBLE_DEVICES empty before process startup')
    engine = None; reconstructed = []
    if first_only:
        require(output == out/'first_real_cpu_replay.json' and not (out/'engine_receipt.json').exists(),
            'first replay must precede continuation/completion')
        todo = prepared['attempts'][:1]
    else:
        ep, engine = cs.validate_engine(prepared)
        first_ref = engine['first_real_cpu_replay']; first = read(bound(first_ref)); cs.same_binding(first, prepared)
        require(first['status'] == 'PASS_FIRST_REAL_FINAL_TEMPORAL_INDEPENDENT_CPU_REPLAY' and
            first['attempts_reconstructed'] == 1 and first['CUDA_initialized'] is False and len(first['attempts']) == 1,
            'successful first CPU replay absent')
        original = first['attempts'][0]
        require(original['ordinal'] == 0 and all(original[k] == engine['attempts'][0][k] for k in ('input', 'raw', 'done')),
            'completed first CPU replay bytes changed')
        for k in ('input', 'raw', 'done'):
            bound(original[k])
        reconstructed.append(original)
        todo = prepared['attempts'][1:]
    processor = AutoProcessor.from_pretrained(prepared['contract']['config']['processor_dir'], local_files_only=True)
    candidates = ascii_token_candidates(processor.tokenizer)
    folder = out/'cpu_replay'; folder.mkdir(exist_ok=True)
    for a in todo:
        target = folder/('%03d.acceptance.json'%a['ordinal'])
        require(not target.exists(), 'successful independent native CPU replay must not repeat')
        value = reconstruct_one(prepared, a, processor, candidates)
        save(target, dict(binding=prepared['binding'], **value))
        reconstructed.append(value)
        print(__import__('json').dumps(dict(stage='INDEPENDENT_CANDIDATE_CPU', completed=len(reconstructed), total=1 if first_only else 521)), flush=True)
    verify_lock(prepared['contract']['lock_path'], prepared['contract']['lock_sha'])
    require(sha(prepared['final']/'adapter_model.safetensors') == prepared['training']['final_adapter_sha256'] and
            not torch.cuda.is_initialized(), 'CPU final/base identity changed')
    receipt = dict(status='PASS_FIRST_REAL_FINAL_TEMPORAL_INDEPENDENT_CPU_REPLAY' if first_only else
        'PASS_ALL_521_FRESH_FINAL_TEMPORAL_INDEPENDENT_CPU_REPLAY', utc=cs.utc(), binding=prepared['binding'],
        attempts_reconstructed=len(reconstructed), records=1 if first_only else 426, attempts=reconstructed,
        new_model_calls=0, new_optimizer_updates=0, CUDA_initialized=False,
        first_successful_CPU_replay_reused=not first_only,
        engine_receipt=None if first_only else cs.ref(ep))
    require(len(reconstructed) == (1 if first_only else 521), 'CPU replay denominator incomplete')
    save(output, receipt)
    return receipt


def main():
    # Set before torch/transformers import; inherited engine CUDA allocation is
    # never touched by this new CPU process.
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    p = cs.parser(); p.add_argument('--output', required=True); p.add_argument('--first-only', action='store_true')
    args = p.parse_args(); prepared = cs.entry(args, 'candidate_replay')
    try:
        replay(prepared, args.output, args.first_only)
    except BaseException as exc:
        target = Path(args.output).with_suffix('.failure.json')
        if not target.exists():
            cs.failure(target, exc)
        raise


if __name__ == '__main__':
    main()
