"""First coarse native/output audit followed by unique exact VERIFY prefix CPU QA."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from development_data46 import ARMS, development_sources
from development_verify46 import candidate_request, prepare
from joint_audit45 import trajectory
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'development48'


def main():
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = development_sources(rt, tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'))
    coarse = read(OUT / 'coarse_GPU_completion.json')['outputs']
    folder = OUT / 'verify_CPU'; folder.mkdir()
    tasks, policies = {}, {}
    for sid, source in sources.items():
        policies[sid] = {}
        for arm in ARMS:
            policies[sid][arm] = []
            if set(coarse[sid][arm]) != {case.name for case in source.cases}:
                raise ValueError('Development source missing an actual window')
            for case in source.cases:
                if arm == 'original_correct':
                    result = read(check(coarse[sid][arm][case.name]))
                    if result['original_control_adopted'] != case.original:
                        raise ValueError('Original successful token/native QA not exactly adopted')
                else:
                    result, _ = trajectory(coarse[sid][arm][case.name], case, source, rt, tokenizer)
                for index, segment in enumerate(result['segments']):
                    event, request = candidate_request(case, source, segment, index)
                    key = request['request_id']
                    if key not in tasks:
                        tasks[key] = prepare(case, event, request, folder / key, tokenizer, rt)
                    elif read(check(tasks[key]['request'])) != request:
                        raise ValueError('Distinct actual VERIFY tasks collide')
                    policies[sid][arm].append(key)
    if torch.cuda.is_initialized():
        raise ValueError('First independent development input/output QA initialized CUDA')
    save(OUT / 'verify_CPU_completion.json', dict(state='PASS_FIRST_ALL_DEV_NATIVE_OUTPUT_AND_VERIFY_PREFIXES',
        tasks=tasks, source_policies=policies, unique_first_VERIFY_calls=len(tasks),
        exact_duplicate_tasks_adopted=True, correct_native_content_for_all_downstream_conditions=True,
        all_first_actual_task_prefixes_verified_before_model=True))


if __name__ == '__main__':
    main()
