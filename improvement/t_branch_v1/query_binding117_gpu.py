"""First50 fixed-model query transforms, no new training or original25 replay."""
import time

import torch

from frozen_branch46 import RUN
from native_prepared103 import Prefetch, transfer
from native_state100 import fingerprint
from parallel_fit115_gpu import load_final
from parallel_forward107 import accepted, forward
from parallel_train108 import cases
from query_binding117_common import remap, values
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'query_binding117'


def transformed_call(model, source, case, proof, code, state, gpu, signature, folder):
    row = read(check(proof)); folder.mkdir()
    started = time.monotonic()
    with torch.inference_mode():
        full, query_binary = forward(model, gpu, proof, code)
        native_binary = remap(query_binary, row['query_to_native'])
    torch.cuda.synchronize(); elapsed = time.monotonic() - started
    result = accepted(source, case, proof, code, state, 'actor', native_binary,
                      signature, elapsed, folder)
    path = folder / 'query_mapping_raw.json'
    save(path, dict(actual_input=proof, actual_output=result, actual_model_state=state,
        query_order_binary_logits=query_binary.detach().float().cpu().tolist(),
        query_to_native=row['query_to_native'], actual_query_anchor_indices=row['actual_query_anchor_indices'],
        actual_query_positions=row['query_positions'], actual_forward_calls=1,
        canonical_native_order_only_after_actual_forward=True))
    del full, query_binary, native_binary
    return result, identity(path)


def main():
    torch.set_num_threads(2); rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    previous = read(check(lock['adopted_lock115']))
    ancestor = read(check(previous['adopted_source_lock108']))
    for group in [lock['code'], previous['code'], ancestor['code']]:
        for ref in group.values():
            check(ref)
    inputs = read(check(lock['actual_inputs']))
    old = read(ROOT / 'parallel_inputs106/completion.json'); data = read(check(old['loss_bindings']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    final = read(ROOT / 'parallel_remaining108/GPU_completion.json')['final_adapter']
    state = load_final(model, final, loaded['base'])
    actual = sum(p.numel() for p in model.parameters()) + 98329 + 37184640 + 28043472 + 6209025
    if actual != 8869330010 or actual > 9000000000:
        raise ValueError('Actual complete query-binding model parameters differ')
    source = cases(data)[inputs['source']]
    outputs, mappings = {}, {}
    for arm, proofs in inputs['inputs'].items():
        folder = OUT / arm; folder.mkdir(); outputs[arm] = {}; mappings[arm] = {}
        entries = [(case, proofs[case.name]) for case in source.cases]
        def loader(entry):
            return values(entry[0], entry[1], processor.tokenizer, rt)
        with Prefetch(entries, loader) as pending:
            for (case, proof), actual_input in pending:
                gpu, signature, _ = transfer(actual_input, proof, rt)
                outputs[arm][case.name], mappings[arm][case.name] = transformed_call(model,
                    source, case, proof, inputs['actual_query_code'], state, gpu, signature, folder / case.name)
                del actual_input, gpu
                print('FIRST_QUERY_BINDING117', arm, case.name, flush=True)
    if sum(map(len, outputs.values())) != 50 or fingerprint(model, 'actor', loaded['base']) != state:
        raise ValueError('Complete50 transformed queries or fixed model state differs')
    model.set_adapter('default')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Original BASE/TIME changed during causal query diagnosis')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_ALL50_QUERY_BINDING_TRANSFORM_OUTPUTS_COMPLETE',
        outputs=outputs, query_mapping_raw=mappings, actual_new_calls=50, actual_model_state=state,
        actual_complete_parameters=actual, actual_training_updates=0, original_BASE_TIME_unchanged=True,
        original25_outputs_adopted=identity(ROOT / 'parallel_fit115/GPU_completion.json'),
        no_quality_candidate_or_production_admission=True))


if __name__ == '__main__':
    main()
