"""Only first distinct downstream original-TIME VERIFY tasks, after full CPU QA."""
import torch

from frozen_branch46 import RUN, verify_modules
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'development48'


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from reference_gpu19 import infer_case
    for ref in read(OUT / 'verify_source_input_lock.json')['code'].values():
        check(ref)
    cpu = read(OUT / 'verify_CPU_completion.json')
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    contract, grammar, _ = verify_modules()
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    candidates = grammar.candidate_tokens(processor.tokenizer, contract.responses())
    folder = OUT / 'verify_outputs'; folder.mkdir()
    outputs = {}
    for key, case in cpu['tasks'].items():
        outputs[key] = infer_case(model, processor, rt, case, grammar, contract, eos, candidates, folder)
    for p in model.parameters():
        p.requires_grad_(False)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Frozen downstream model changed')
    save(OUT / 'verify_GPU_completion.json', dict(state='PASS_FIRST_ALL_UNIQUE_DEV_VERIFY',
        outputs=outputs, actual_calls=len(outputs), duplicate_successful_tasks_not_repeated=True,
        torch_peak_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
