"""First150 originalTIME calls with the frozen source-summary/local-card interface."""
import torch

from development_data46 import development_sources
from event_native71 import bindings
from event_select72_gpu import generate
from frozen_branch46 import RUN
from summary_context90 import ARMS
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_selection91'


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    cpu = read(check(lock['complete_actual_native_context_CPU']))
    for ref in cpu['old_native_grammar_CPU_adopted']['code'].values():
        check(ref)
    if cpu['unique_first_model_calls'] != 150:
        raise ValueError('This frozen actual150-unique cohort differs; never repeat logical duplicates')
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Actual original frozenTIME parameters differ')
    model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    _, grammar = bindings(); candidates = grammar.ascii_token_candidates(processor.tokenizer)
    folder = OUT / 'outputs'; folder.mkdir(); outputs = {}; count = 0
    with (OUT / 'accepted.jsonl').open('x') as journal:
        for sid in sorted(sources):
            source = sources[sid]; outputs[sid] = {arm: {} for arm in ARMS}
            for case in source.cases:
                for arm in ARMS:
                    owner = cpu['provenance'][sid][arm][case.name]['owner']
                    if owner['arm'] != arm or owner['case'] != case.name or owner['source'] != sid:
                        raise ValueError('Actual immutable owner differs; do not re-execute another owner')
                    task = cpu['inputs'][sid][arm][case.name]
                    ref = generate(model, processor.tokenizer, rt, source, case, arm, task, candidates,
                                   folder / (arm + '_' + case.name))
                    outputs[sid][arm][case.name] = ref; count += 1
                    journal.write(__import__('json').dumps(dict(source=sid, case=case.name, arm=arm, result=ref)) + '\n')
                    journal.flush()
    if count != 150:
        raise ValueError('Actual complete first150 native outputs not reached')
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Protected originalBASE/TIME bytes changed during real native selection')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_ALL150_CONTENT_GOAL_NATIVE_GREEDY_COMPLETE_NEEDS_CPU',
        outputs=outputs, actual_first_TIME_calls=150, original_BASE_TIME_unchanged=True,
        actual_resident_original_TIME_parameters=8782459120,
        full_method_parameters_including_previous_trained_summary_and_auxiliaries=8869330010,
        actual_original_goal_predictions=lock['trained_goals'], actual_new_training=0,
        peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
