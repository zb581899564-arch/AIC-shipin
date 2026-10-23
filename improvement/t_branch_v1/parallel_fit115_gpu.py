"""First25 final-actor fitting observations; original pre-update25 are adopted."""
import time

import torch
from peft import get_peft_model_state_dict, set_peft_model_state_dict
from safetensors.torch import load_file

from frozen_branch46 import RUN
from native_prepared103 import Prefetch, transfer
from native_state100 import fingerprint
from parallel_forward107 import infer
from parallel_input106 import values
from parallel_train108 import cases
from t_io import ROOT, check, read, save
from t_runtime39 import runtime

OUT = ROOT / 'parallel_fit115'


def load_final(model, final, base):
    model.load_adapter(final['adapter_directory'], adapter_name='actor', is_trainable=False)
    saved = load_file(str(check(final['weights'])), device='cpu')
    set_peft_model_state_dict(model, saved, adapter_name='actor')
    actual = get_peft_model_state_dict(model, adapter_name='actor')
    if set(saved) != set(actual) or any(not torch.equal(saved[k], actual[k].detach().cpu()) for k in saved):
        raise ValueError('Actual loaded final actor differs from accepted FP32 checkpoint')
    model.set_adapter('actor'); model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    state = fingerprint(model, 'actor', base)
    expected = read(ROOT / 'parallel_remaining108/training_CPU.json')['actual_final_actor_state']
    if state != expected:
        raise ValueError('Fitting diagnosis used another checkpoint')
    return state


def main():
    torch.set_num_threads(2)
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    for ref in read(check(lock['adopted_source_lock108']))['code'].values():
        check(ref)
    inputs = read(check(lock['actual_inputs']))
    data = read(check(inputs['loss_bindings']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    final = read(ROOT / 'parallel_remaining108/GPU_completion.json')['final_adapter']
    state = load_final(model, final, loaded['base'])
    complete = sum(p.numel() for p in model.parameters()) + 98329 + 37184640 + 28043472 + 6209025
    if complete != 8869330010 or complete > 9000000000:
        raise ValueError('Actual complete fitting method parameter budget differs')
    sid = lock['source']; source = cases(data)[sid]
    entries = [(case, inputs['fit'][sid][case.name]) for case in source.cases]
    def loader(entry):
        started = time.monotonic()
        return values(entry[0], entry[1], processor.tokenizer, rt), time.monotonic() - started
    folder = OUT / 'final_outputs'; folder.mkdir(); outputs = {}
    with Prefetch(entries, loader) as pending:
        for (case, proof), (actual, _) in pending:
            gpu, signature, _ = transfer(actual, proof, rt)
            outputs[case.name], _ = infer(model, source, case, proof, inputs['actual_query_code'],
                                          state, 'actor', gpu, signature, folder / case.name)
            del actual, gpu
            print('FIRST_FINAL_FIT115', case.name, flush=True)
    if len(outputs) != 25 or fingerprint(model, 'actor', loaded['base']) != state:
        raise ValueError('Complete fixed source/final actor identity changed')
    model.set_adapter('default')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Protected original BASE/TIME changed during fitting diagnosis')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_FROZEN_FINAL_FIT25_OUTPUTS_COMPLETE',
        outputs=outputs, actual_new_calls=25, actual_model_state=state,
        actual_complete_parameters=complete, actual_training_updates=0,
        original_BASE_TIME_unchanged=True, no_candidate_quality_admission=True))


if __name__ == '__main__':
    main()
