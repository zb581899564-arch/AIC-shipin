"""Only first missing original-TIME candidate VERIFY; all old successes adopted."""
import torch

from frozen_branch46 import RUN, verify_modules
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'event_full78'
CPU = ROOT / 'event_verify_inputs76'


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from reference_gpu19 import infer_case
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    cpu = read(check(lock['actual_verify_CPU']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Actual complete original BASE/TIME parameter count differs')
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    contract, grammar, _ = verify_modules()
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    candidates = grammar.candidate_tokens(processor.tokenizer, contract.responses())
    folder = OUT / 'new_VERIFY'; folder.mkdir()
    outputs = dict(cpu['adopted_successful_outputs']); first = []
    for key, task in cpu['tasks'].items():
        if key not in outputs:
            outputs[key] = infer_case(model, processor, rt, task, grammar, contract, eos, candidates, folder)
            first.append(key)
    if len(first) != cpu['maximum_first_new_VERIFY_calls']:
        raise ValueError('First missing VERIFY denominator differs')
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original downstream weights or inference mode changed')
    save(OUT / 'GPU_completion.json', dict(state='ALL_FIRST_MISSING_EVENT_VERIFY_COMPLETE',
        outputs=outputs, first_new_keys=first, first_new_calls=len(first),
        successful_old_calls_adopted=len(cpu['adopted_successful_outputs']),
        all_original_weights_unchanged=True, new_BASE_or_caption_calls=0,
        actual_full40_48_with_ASR_parameters=8853994586,
        peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
