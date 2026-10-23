"""First actual original8B inference with fixed accepted native visibility."""
from pathlib import Path
import time

import numpy as np
import torch

from frozen_branch46 import RUN
from localized_visual121 import localized_kernel, native_visibility
from native_prepared103 import transfer
from parallel_train108 import cases
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime
from visual_query_prefix119 import values
from visual_query_runtime119 import choose, prefix

OUT = ROOT / 'localized_query122'
TEMP = Path('/dev/shm/aic_T_localized_query122')


def visibility_for(case, proof, gpu, accepted):
    item = accepted['masks'][case.name]
    if item['original_input'] != proof:
        raise ValueError('Frozen121 mask belongs to another actual prefix')
    with np.load(check(item['mask']), allow_pickle=False) as data:
        mask = torch.from_numpy(data['visibility'].copy()).to(gpu['input_ids'].device)
    token = read(check(proof))['video_token_id']
    expected = native_visibility(gpu['input_ids'] == token)
    if not torch.equal(mask, expected):
        raise ValueError('Actual attention mask differs from accepted native group visibility')
    return mask, item['mask']


def main():
    torch.set_num_threads(2); rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    inputs = read(check(lock['actual_inputs']))
    accepted = read(check(lock['accepted_masks']))
    original = read(ROOT / 'parallel_inputs106/completion.json')
    source = cases(read(check(original['loss_bindings'])))[inputs['source']]
    prior = read(ROOT / 'visual_query_fit120/GPU_completion.json')
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if any(loaded[key] != prior['actual_loaded'][key] for key in ['base', 'adapter']):
        raise ValueError('Original BASE/TIME checkpoint differs')
    model.set_adapter('default'); model.eval(); model.gradient_checkpointing_disable()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Original loaded model parameter denominator differs')
    core = model.get_base_model(); TEMP.mkdir(); (OUT / 'outputs').mkdir()
    outputs = {}
    for case in source.cases:
        proof = inputs['inputs'][case.name]; started = time.monotonic()
        actual = values(case, proof, processor.tokenizer, rt)
        gpu, signature, _ = transfer(actual, proof, rt)
        visibility, mask_ref = visibility_for(case, proof, gpu, accepted)
        folder = OUT / 'outputs' / case.name
        with torch.inference_mode():
            packet = prefix(model, core, gpu, proof)
            with localized_kernel(visibility):
                result = choose(model, core, packet, gpu, proof, inputs['actual_query_code'],
                                source, case, signature, folder, TEMP)
        sidecar = folder / 'actual_operator.json'
        save(sidecar, dict(actual_output=result['output'], actual_input=proof,
            visibility=mask_ref, accepted121_masks=lock['accepted_masks'],
            operator=identity(Path(__file__).parent / 'localized_visual121.py'),
            actual_mask_equals_exact_native_group=True, physical_prefix_forwards=1,
            physical_private32_branch_forwards=1, weights_prompt_pool_and_positions_unchanged=True))
        result.update(operator=identity(sidecar), complete_view_seconds=time.monotonic() - started)
        outputs[case.name] = result
        print('FIRST_MASKED8B122', case.name, result['complete_view_seconds'], flush=True)
        del actual, gpu, packet, visibility
    if len(outputs) != 25:
        raise ValueError('Entire fixed25-window source not complete')
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Protected original BASE/TIME changed')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_REAL_LOCAL_VISIBILITY25_COMPLETE_NEEDS_CPU',
        outputs=outputs, actual_new_logical_windows=25, actual_new_multimodal_prefills=25,
        actual_new_private32_branch_decoder_batches=25, actual_new_native_decisions=800,
        actual_complete_parameters=8853994586, actual_training_updates=0,
        actual_loaded=loaded, original_BASE_TIME_unchanged=True,
        peak_torch_bytes=torch.cuda.max_memory_allocated(), no_quality_or_production_admission=True))


if __name__ == '__main__':
    main()
