"""First14 correctly prompted frozen TIME VERIFY calls; no old BASE or B0 replay."""
import math
import sys
import time

import torch

from prompt_contract13 import prompt_binding
from reference_data18 import accepted_cases, load_input
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'reference_control19'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime, verify_modules


def infer_case(model, processor, rt, row, grammar, contract, eos, candidates, folder):
    cpu = read(check(row['CPU']))
    request = read(check(row['request']))
    values = load_input(cpu)
    if rt.tensor_signature(values) != cpu['detail']['tensor_signature']:
        raise ValueError('Accepted corrected task input changed before first model call')
    binding = prompt_binding(processor.tokenizer, values['input_ids'], cpu['detail'],
                             request['prompt'], 'VERIFY', rt.EMPTY_PROMPT)
    prefix = int(values['input_ids'].shape[1])
    constraint = grammar.VerifyConstraint(processor.tokenizer, prefix, request, eos, candidates)
    target = folder / request['request_id']
    target.mkdir()
    save(target / 'request.json', dict(request=row['request'], CPU=row['CPU'], binding=binding))
    start = time.monotonic()
    with torch.inference_mode():
        output = model.generate(**{k: v.cuda() if torch.is_tensor(v) else v for k, v in values.items()},
            do_sample=False, max_new_tokens=256, prefix_allowed_tokens_fn=constraint,
            return_dict_in_generate=True, output_scores=True)
    torch.cuda.synchronize()
    tokens = output.sequences[0, prefix:]
    text = processor.tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    scores = [float(score[0, int(token)]) for score, token in zip(output.scores, tokens)]
    save(target / 'raw.json', dict(text=text, tokens=tokens.tolist(), prefix=prefix, eos=eos,
        scores=[value if math.isfinite(value) else str(value) for value in scores],
        seconds=time.monotonic() - start))
    if len(scores) != len(tokens) or not all(math.isfinite(value) for value in scores):
        raise ValueError('First correct task output has invalid selected scores')
    constraint.assert_complete(tokens)
    decision = contract.resolve(text, request, execution_status='MODEL_OK')
    save(target / 'acceptance.json', dict(decision=decision, raw=identity(target / 'raw.json'), input=row))
    print('CORRECT_VERIFY19_ACCEPTED', request['request_id'], decision['decision'], flush=True)
    return identity(target / 'acceptance.json')


def main():
    rt = legacy_runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if loaded['logical_parameters'] != 8782459120:
        raise ValueError('Original actual BASE+TIME parameter identity differs')
    save(OUT / 'model_identity.json', loaded)
    contract, grammar, _ = verify_modules()
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    candidates = grammar.candidate_tokens(processor.tokenizer, contract.responses())
    folder = OUT / 'verify_outputs'
    folder.mkdir()
    outputs = [infer_case(model, processor, rt, row, grammar, contract, eos, candidates, folder)
               for row in accepted_cases(ROOT / 'reference_input18')]
    if (rt.b_engine.frozen_identity(model, config) != loaded['base'] or
            rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Frozen BASE/TIME changed during correct reference inference')
    save(OUT / 'verify_GPU_completion.json', dict(state='ALL14_FIRST_CORRECT_VERIFY_TASKS_COMPLETE', outputs=outputs))
    save(OUT / 'gpu_completion.json', dict(state='PASS', first_correct_VERIFY_calls=len(outputs),
        repeated_old_generic_task_calls=0, repeated_B0_or_BASE_calls=0, updates=0,
        original_BASE_TIME_parameters=loaded['logical_parameters'], protected_baseline_unchanged=True))


if __name__ == '__main__':
    main()
