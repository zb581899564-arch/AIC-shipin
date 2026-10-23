"""Frozen original TIME; first speech-condition greedy or only missing VERIFY."""
import sys

import torch

from frozen_branch46 import RUN, verify_modules
from development_call46 import generate
from development_data46 import development_sources
from speech_task60 import OUT, values
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime


def coarse(model, processor, rt):
    sources = development_sources(rt, processor.tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'))
    inputs = read(ROOT / 'speech_inputs59/completion.json')['accepted']
    old = read(ROOT / 'development51/coarse_GPU_completion.json')['outputs']
    folder = OUT / 'coarse'; folder.mkdir()
    outputs = {}
    for sid, source in sources.items():
        outputs[sid] = dict(original_correct=old[sid]['original_correct'])
        for arm in ('speech_correct', 'speech_shift'):
            outputs[sid][arm] = {}
            for case in source.cases:
                proof = inputs[sid][arm][case.name]
                actual = values(case, proof, rt)
                _, ref = generate(model, processor, rt, actual, folder / (arm + '_' + case.name), 'default', proof)
                outputs[sid][arm][case.name] = ref
                print('SPEECH60_GREEDY', arm, case.name, flush=True)
    return dict(outputs=outputs, actual_new_generations=100, successful_original_controls_adopted=50,
        semantic=read(ROOT / 'development51/coarse_and_BASE_GPU_completion.json')['semantic'],
        successful_BASE_batches_adopted=365, new_BASE_calls=0)


def verify(model, processor, rt):
    from reference_gpu19 import infer_case
    contract, grammar, _ = verify_modules()
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    candidates = grammar.candidate_tokens(processor.tokenizer, contract.responses())
    cpu = read(OUT / 'verify_CPU_completion.json')
    folder = OUT / 'verify_outputs'; folder.mkdir()
    outputs = dict(cpu['adopted_VERIFY_outputs'])
    for key, case in cpu['tasks'].items():
        if key not in outputs:
            outputs[key] = infer_case(model, processor, rt, case, grammar, contract, eos, candidates, folder)
    return dict(outputs=outputs, actual_calls=len(outputs) - len(cpu['adopted_VERIFY_outputs']),
        adopted_calls=len(cpu['adopted_VERIFY_outputs']))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('coarse', 'verify'):
        raise ValueError('One explicit model phase required')
    phase = sys.argv[1]; rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    count = sum(parameter.numel() for parameter in model.parameters()) + 98329 + 37184640
    if count != 8819742089 or count > 9000000000:
        raise ValueError('Actual complete primary/LoRA/head/ASR parameter count differs')
    result = coarse(model, processor, rt) if phase == 'coarse' else verify(model, processor, rt)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Protected original BASE/TIME changed')
    save(OUT / (phase + '_GPU_completion.json'), dict(state='PASS_FIRST_SPEECH_' + phase.upper(),
        **result, actual_complete_parameters=count, original_BASE_TIME_unchanged=True,
        torch_peak_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
