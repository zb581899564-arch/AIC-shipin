"""First remaining dev output replay; recover allowed metadata from actual scores."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
import hashlib

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from causal_policy32 import actual_allowed_states
from development_data46 import ARMS, development_sources
from development_verify46 import candidate_request, prepare
from joint_audit45 import trajectory
from t_io import ROOT, check, identity, read, save
from t_runtime39 import grammar, runtime

OUT = ROOT / 'development_remaining55'
OLD = ROOT / 'development51'


def normalized_output(ref, case, rt, tokenizer, candidates, target):
    original = read(check(ref))
    raw = read(check(original['raw']))
    payload = torch.load(check(original['allowed_scores']), map_location='cpu', weights_only=True)
    if 'allowed' in original or set(payload) != {'allowed', 'scores', 'tokens'}:
        raise ValueError('Expected exact missing-redundant-field interface absent')
    if original['tokens'] != raw['tokens'] or original['tokens'] != payload['tokens']:
        raise ValueError('Actual persisted generation token bindings differ')
    rule = grammar().make_prefix_constraint(tokenizer, case.values['input_ids'].shape[1],
        Fraction(case.meta['window_end']) - Fraction(case.meta['window_start']),
        candidate_token_ids=candidates, eos_token_ids=raw['eos'], allow_empty=True)
    actual = actual_allowed_states(case.values['input_ids'], raw['tokens'], rule)
    if payload['allowed'] != actual:
        raise ValueError('Actual saved allowed actions differ from original independent grammar')
    save(target, dict(original, allowed=actual, original_acceptance_adopted=ref,
        actual_saved_allowed_scores=original['allowed_scores'], metadata_interface_normalization_only=True,
        new_model_calls=0))
    return identity(target)


def prior_input(key, case, request):
    folder = OLD / 'verify_CPU' / key
    if not (folder / 'CPU_acceptance.json').exists():
        return None
    cpu = read(folder / 'CPU_acceptance.json')
    if read(folder / 'request.json') != request or cpu['original_CPU'] != case.CPU:
        raise ValueError('Existing successful VERIFY CPU task binding differs')
    if cpu['prompt_binding']['expected_prompt_sha256'] != hashlib.sha256(request['prompt'].encode()).hexdigest():
        raise ValueError('Existing successful VERIFY prefix uses a different prompt')
    check(cpu['encoded_text']); check(cpu['adopted_multimodal'])
    return dict(request=identity(folder / 'request.json'), CPU=identity(folder / 'CPU_acceptance.json'))


def main():
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = development_sources(rt, tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'))
    coarse = read(OLD / 'coarse_GPU_completion.json')['outputs']
    shift = read(OLD / 'coarse_CPU_completion.json')['shifted_inputs']
    candidates = grammar().ascii_token_candidates(tokenizer)
    folder, repaired = OUT / 'verify_CPU', OUT / 'coarse_replay'
    folder.mkdir(); repaired.mkdir()
    tasks, policies, accepted, adopted = {}, {}, [], []
    for sid, source in sources.items():
        policies[sid] = {}
        for arm in ARMS:
            policies[sid][arm] = []
            if set(coarse[sid][arm]) != {case.name for case in source.cases}:
                raise ValueError('Full source is missing an accepted original model task')
            for case in source.cases:
                old_ref = coarse[sid][arm][case.name]
                if arm == 'original_correct':
                    result = read(check(old_ref))
                    if result['original_control_adopted'] != case.original:
                        raise ValueError('Original successful control was not adopted exactly')
                else:
                    row = read(check(old_ref))
                    expected_role = 'default' if arm.startswith('original_') else 'actor'
                    expected_input = shift[case.name] if arm.endswith('_shift') else case.CPU
                    if row['model_role'] != expected_role or row['actual_input_proof'] != expected_input:
                        raise ValueError('Actual counterfactual input or model role differs')
                    ref = normalized_output(old_ref, case, rt, tokenizer, candidates,
                        repaired / (arm + '_' + case.name + '.json'))
                    result, _ = trajectory(ref, case, source, rt, tokenizer)
                    accepted.append(ref)
                for index, segment in enumerate(result['segments']):
                    event, request = candidate_request(case, source, segment, index)
                    key = request['request_id']
                    if key not in tasks:
                        prior = prior_input(key, case, request)
                        if prior is not None:
                            tasks[key] = dict(event=event, **prior); adopted.append(key)
                        else:
                            tasks[key] = prepare(case, event, request, folder / key, tokenizer, rt)
                    elif read(check(tasks[key]['request'])) != request:
                        raise ValueError('Distinct real task collided during cross-arm deduplication')
                    policies[sid][arm].append(key)
    if len(accepted) != 150 or len(adopted) != 31 or torch.cuda.is_initialized():
        raise ValueError('First remaining output/prefix count or CPU-only constraint differs')
    save(OUT / 'verify_CPU_completion.json', dict(state='PASS_FIRST_ALL_DEV_NATIVE_OUTPUT_AND_VERIFY_PREFIXES',
        tasks=tasks, source_policies=policies, unique_first_VERIFY_calls=len(tasks),
        exact_duplicate_tasks_adopted=True, correct_native_content_for_all_downstream_conditions=True,
        all_first_actual_task_prefixes_verified_before_model=True,
        actual_first150_output_QA=accepted, prior_successful31_prefixes_adopted=adopted,
        source_model_calls_repeated=0, old_failure_preserved=True))


if __name__ == '__main__':
    main()
