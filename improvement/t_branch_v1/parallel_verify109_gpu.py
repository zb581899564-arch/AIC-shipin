"""First missing exact originalTIME VERIFY only; successful historical calls adopted."""
import json

import torch

from frozen_branch46 import RUN, verify_modules
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'parallel_full109'


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from reference_gpu19 import infer_case
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    inputs = read(check(lock['actual_verify_CPU']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Original shared BASE/TIME resident parameter budget differs')
    model.set_adapter('default')
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    contract, grammar, _ = verify_modules()
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    candidates = grammar.candidate_tokens(processor.tokenizer, contract.responses())
    folder = OUT / 'new_VERIFY'
    folder.mkdir()
    outputs = dict(inputs['adopted_successful_outputs'])
    first = []
    with (OUT / 'accepted.jsonl').open('x') as journal:
        for key, task in inputs['tasks'].items():
            if key in outputs:
                continue
            outputs[key] = infer_case(model, processor, rt, task, grammar, contract, eos, candidates, folder)
            first.append(key)
            journal.write(json.dumps(dict(key=key, output=outputs[key])) + '\n')
            journal.flush()
    if len(first) != inputs['maximum_first_new_VERIFY_calls']:
        raise ValueError('First exact remaining VERIFY task domain incomplete')
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Original BASE/TIME changed during first missing VERIFY')
    save(OUT / 'GPU_completion.json', dict(state='COMPLETE_FIRST_MISSING_PARALLEL_VERIFY_GPU',
        outputs=outputs, first_new_keys=first, first_new_calls=len(first),
        successful_prior_outputs_adopted=len(inputs['adopted_successful_outputs']),
        actual_resident_BASE_TIME_parameters=8782459120,
        complete_shared_method_parameters=8869330010, peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
