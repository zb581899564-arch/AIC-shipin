"""CPU input admission / independent exact processor replay, no model weights."""
import json
import sys
from fractions import Fraction
from pathlib import Path
from runtime import HERE, RUN, sha, save, EMPTY_PROMPT, baseline_frames, encode


def main(mode):
    import torch
    import numpy as np
    from transformers import AutoProcessor
    if torch.cuda.is_initialized():
        raise ValueError('CPU replay must not initialize CUDA')
    cfg = json.loads((RUN/'b_score_aligned_package_v4/config.json').read_text())
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    entries = json.loads((HERE/'inputs.json').read_text())
    proofs = []
    for entry in entries:
        if sha(entry['input_path']) != entry['input_sha256']:
            raise ValueError('input metadata changed')
        meta = json.loads(Path(entry['input_path']).read_text())
        folder = HERE/meta['case_id']
        if mode == 'prepare':
            enc, detail = encode(processor, meta, baseline_frames(meta), Fraction(meta['window_start']), EMPTY_PROMPT)
            proofs.append(dict(case_id=meta['case_id'], input_evidence=detail))
            del enc
        elif mode == 'replay':
            from contracts import parse_segments
            from constrained_json import make_prefix_constraint
            for stage in ['baseline', 'refinement']:
                request_path = folder/(stage+'_request.json')
                if not request_path.exists():
                    if stage == 'baseline':
                        raise ValueError('missing original baseline request')
                    continue
                q = json.loads(request_path.read_text())
                raw_path = folder/(stage+'_raw.json')
                raw = json.loads(raw_path.read_text())
                if 'array_sha256' in q and sha(q['cached_array']) != q['array_sha256']:
                    raise ValueError('context frame cache changed')
                with np.load(q['cached_array'], allow_pickle=False) as archive:
                    arr = archive['rgb']
                enc, detail = encode(processor, meta, (arr, q['ordinals'], q['exact_pts']), Fraction(q['source_start']), q['text'])
                if detail != raw['input_evidence']:
                    raise ValueError('independent CPU native processor replay differs')
                duration = Fraction(q['source_end'])-Fraction(q['source_start'])
                segments, errors, warnings = parse_segments(raw['raw_output'], duration, allow_empty=True)
                if segments is None or errors:
                    raise ValueError('strict original parser replay failed')
                decoded = processor.tokenizer.decode(raw['output_token_ids'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
                if decoded != raw['raw_output']:
                    raise ValueError('actual generated token IDs/raw differ')
                grammar = make_prefix_constraint(processor.tokenizer, raw['input_tokens'], duration, allow_empty=True)
                grammar.assert_complete(raw['output_token_ids'])
                proofs.append(dict(case_id=meta['case_id'], stage=stage, input_tensors_exact=True,
                    raw_sha256=sha(raw_path), parsed_segments=segments, original_parser_tokenizer_and_grammar_pass=True))
                del enc
        else:
            raise ValueError('unsupported CPU mode')
    if torch.cuda.is_initialized():
        raise ValueError('CPU unexpectedly initialized CUDA')
    output = 'baseline_cpu_acceptance.json' if mode == 'prepare' else 'independent_cpu_replay.json'
    save(HERE/output, dict(status='PASS_CPU_NATIVE_PROCESSOR_'+mode.upper(), proofs=proofs,
        CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0))
    print(json.dumps(dict(status='PASS', proofs=len(proofs), mode=mode)), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
