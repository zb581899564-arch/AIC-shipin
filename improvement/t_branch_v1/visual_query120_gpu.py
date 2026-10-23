"""Only first remaining23 original-model contexts; first2 actual results adopted."""
from pathlib import Path
import time

import torch

from frozen_branch46 import RUN
from native_prepared103 import transfer
from parallel_train108 import cases
from t_io import ROOT, check, read, save
from t_runtime39 import runtime
from visual_query_prefix119 import values
from visual_query_runtime119 import choose, prefix

OUT = ROOT / 'visual_query_fit120'
TEMP = Path('/dev/shm/aic_T_visual_query120_remaining')


def main():
    torch.set_num_threads(2); rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    inputs = read(check(lock['actual_inputs']))
    original = read(ROOT / 'parallel_inputs106/completion.json'); data = read(check(original['loss_bindings']))
    source = cases(data)[inputs['source']]
    prior = read(ROOT / 'visual_query_engine119/GPU_completion.json')
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if loaded['base'] != prior['actual_loaded']['base'] or loaded['adapter'] != prior['actual_loaded']['adapter']:
        raise ValueError('Remaining fitting used another original model/checkpoint')
    model.set_adapter('default'); model.eval(); model.gradient_checkpointing_disable()
    for p in model.parameters():
        p.requires_grad_(False)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Original model parameter count changed')
    core = model.get_base_model(); TEMP.mkdir(); (OUT / 'outputs').mkdir()
    outputs = dict(prior['outputs']); fresh = []
    for case in source.cases:
        if case.name in outputs:
            continue
        proof = inputs['inputs'][case.name]; started = time.monotonic()
        actual = values(case, proof, processor.tokenizer, rt)
        gpu, signature, _ = transfer(actual, proof, rt)
        with torch.inference_mode():
            packet = prefix(model, core, gpu, proof)
            outputs[case.name] = choose(model, core, packet, gpu, proof, inputs['actual_query_code'],
                                       source, case, signature, OUT / 'outputs' / case.name, TEMP)
        outputs[case.name]['complete_view_seconds'] = time.monotonic() - started
        fresh.append(case.name); del actual, gpu, packet
        print('FIRST_REMAINING_VISUAL_FIT120', case.name, outputs[case.name]['complete_view_seconds'], flush=True)
    if len(outputs) != 25 or len(fresh) != 23:
        raise ValueError('Complete25 fitting source or only remaining23 denominator differs')
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Original BASE/TIME changed during fitting diagnosis')
    save(OUT / 'GPU_completion.json', dict(state='COMPLETE25_SHARED_VISUAL_FIT_ONLY23NEW_NEEDS_CPU',
        outputs=outputs, first_new_cases=fresh, actual_new_multimodal_prefills=23,
        actual_new32_branch_decoder_batches=23, first2_actual_outputs_adopted=True,
        actual_complete_parameters=8853994586, actual_training_updates=0,
        original_BASE_TIME_unchanged=True, actual_loaded=loaded,
        peak_torch_bytes=torch.cuda.max_memory_allocated(), no_quality_or_production_admission=True))


if __name__ == '__main__':
    main()
