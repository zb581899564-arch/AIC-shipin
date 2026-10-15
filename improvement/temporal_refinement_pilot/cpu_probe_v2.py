"""CPU input admission / independent exact processor replay, no model weights."""
import json
import math
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
            actual_segments = {}
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
                transfer=json.loads(Path(str(raw_path)+'.gpu_input.json').read_text())
                if transfer['status'] != 'PASS_ACTUAL_CPU_GPU_TENSOR_EQUALITY' or transfer['tensor_signature'] != detail['tensor_signature']:
                    raise ValueError('actual GPU input acceptance differs from independent CPU tensors')
                scores=raw['selected_token_scores']
                if len(scores) != len(raw['output_token_ids']) or not all(type(x) in (float,int) and math.isfinite(x) for x in scores):
                    raise ValueError('actual selected token-score denominator or finite check failed')
                duration = Fraction(q['source_end'])-Fraction(q['source_start'])
                segments, errors, warnings = parse_segments(raw['raw_output'], duration, allow_empty=True)
                if segments is None or errors:
                    raise ValueError('strict original parser replay failed')
                actual_segments[stage] = segments
                from contract_v2 import native_ranges
                native_ranges(segments,meta['all_source_exact_pts'],Fraction(q['source_start']))
                decoded = processor.tokenizer.decode(raw['output_token_ids'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
                if decoded != raw['raw_output']:
                    raise ValueError('actual generated token IDs/raw differ')
                grammar = make_prefix_constraint(processor.tokenizer, raw['input_tokens'], duration, allow_empty=True)
                grammar.assert_complete(raw['output_token_ids'])
                proofs.append(dict(case_id=meta['case_id'], stage=stage, input_tensors_exact=True,
                    raw_sha256=sha(raw_path), parsed_segments=segments, original_parser_tokenizer_and_grammar_pass=True))
                del enc
            prediction = json.loads((folder/'prediction.json').read_text())
            if prediction['baseline_segments'] != actual_segments['baseline']:
                raise ValueError('baseline prediction differs from original raw parser')
            if 'refinement' in actual_segments:
                from contract_v2 import project_context
                q = json.loads((folder/'refinement_request.json').read_text())
                lo = Fraction(meta['window_start'])
                origin = Fraction(q['source_start'])
                if native_ranges(q['candidate_context_local'],meta['all_source_exact_pts'],origin) != native_ranges(actual_segments['baseline'],meta['all_source_exact_pts'],lo):
                    raise ValueError('independent candidate-hint native membership differs')
                projected, detail = project_context(actual_segments['refinement'], actual_segments['baseline'],
                    origin-lo, Fraction(meta['window_end'])-lo, meta['all_source_exact_pts'],lo)
                if projected != prediction['refined_segments'] or detail != prediction['exact_projection']:
                    raise ValueError('independent final candidate intersection / native membership differs')
            elif prediction['baseline_segments'] or prediction['refined_segments']:
                raise ValueError('missing verifier must be an original legal empty candidate')
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
