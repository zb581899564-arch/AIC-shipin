"""Two first actual multimodal prefixes and private visual-query decoder batches."""
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

OUT = ROOT / 'visual_query_engine119'
TEMP = Path('/dev/shm/aic_T_visual_query119_first')


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
    by_name = {case.name: case for case in source.cases}
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    expected = read(ROOT / 'parallel_remaining108/GPU_completion.json')['actual_loaded']
    if loaded['base'] != expected['base'] or loaded['adapter'] != expected['adapter']:
        raise ValueError('Loaded original BASE/TIME is not the accepted protected model identity')
    model.set_adapter('default'); model.eval(); model.gradient_checkpointing_disable()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    count = sum(parameter.numel() for parameter in model.parameters())
    if count != 8782459120 or count + 98329 + 37184640 + 28043472 + 6209025 != 8853994586:
        raise ValueError('Actual original and complete local-visual model parameters differ')
    core = model.get_base_model()
    if int(core.model.visual.spatial_merge_size) != inputs['actual_spatial_merge_size']:
        raise ValueError('Actual vision merger is incompatible with the first CPU/native grouping')
    TEMP.mkdir(); outputs = {}; (OUT / 'outputs').mkdir()
    for name in inputs['first_engineering_cases']:
        case = by_name[name]; proof = inputs['inputs'][name]; started = time.monotonic()
        actual = values(case, proof, processor.tokenizer, rt)
        gpu, signature, _ = transfer(actual, proof, rt)
        with torch.inference_mode():
            packet = prefix(model, core, gpu, proof)
            outputs[name] = choose(model, core, packet, gpu, proof, inputs['actual_query_code'],
                                   source, case, signature, OUT / 'outputs' / name, TEMP)
        outputs[name]['complete_view_seconds'] = time.monotonic() - started
        del actual, gpu, packet
        print('FIRST_REAL_VISUAL_QUERY119', name, outputs[name]['complete_view_seconds'], flush=True)
    if len(outputs) != 2:
        raise ValueError('First two fixed native engineering windows incomplete')
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Protected original BASE/TIME changed during local visual inference')
    save(OUT / 'GPU_completion.json', dict(state='FIRST2_REAL_VISUAL_QUERY_PREFIX_AND_DECODER_COMPLETE_NEEDS_CPU',
        outputs=outputs, actual_new_multimodal_prefills=2, actual_new32_branch_decoder_batches=2,
        actual_native_judgments=64, local_shift_alias_is_not_extra_model_forward=True,
        actual_complete_parameters=8853994586, actual_original_parameters=count,
        actual_loaded=loaded,
        original_BASE_TIME_unchanged=True, actual_training_updates=0,
        peak_torch_bytes=torch.cuda.max_memory_allocated(), no_candidate_quality_admission=True))


if __name__ == '__main__':
    main()
