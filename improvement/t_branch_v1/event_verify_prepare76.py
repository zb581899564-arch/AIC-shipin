"""First remaining VERIFY requests after150 native event outputs; reuse old accepted tasks."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import traceback

import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from development_verify46 import candidate_request, prepare
from event_select72_common import ARMS, OUT as SELECT
from frozen_branch46 import RUN
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'event_verify_inputs76'
OLD = ROOT / 'development_remaining55'


def adopt(key, case, event, request, old_cpu, old_gpu):
    if key not in old_cpu['tasks']:
        return None
    previous = old_cpu['tasks'][key]
    if (previous['event'] != event or read(check(previous['request'])) != request
            or read(check(previous['CPU']))['original_CPU'] != case.CPU):
        raise ValueError('Prior accepted same-name VERIFY task differs')
    row = read(check(old_gpu[key]))
    if row['input'] != previous:
        raise ValueError('Prior accepted model output is bound to a different request')
    return previous, old_gpu[key], row['decision']


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    complete = read(SELECT / 'completion.json')
    if complete['state'] != 'PASS_FIRST_ALL150_NATIVE_MEMORY_OUTPUTS_NOT_FULL40_48_QUALITY':
        raise ValueError('All150 first native output proofs must complete before VERIFY preparation')
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = development_sources(rt, tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'), values=True, labels=False)
    old_cpu = read(OLD / 'verify_CPU_completion.json'); old_gpu = read(OLD / 'verify_GPU_completion.json')['outputs']
    old_first_QA = identity(OLD / 'independent_CPU_audit.json')
    generated = read(SELECT / 'GPU_completion.json')['outputs']
    folder = OUT / 'requests'; folder.mkdir()
    tasks, policies, adopted, decisions = {}, {}, {}, {}
    for sid, source in sources.items():
        baseline = old_cpu['source_policies'][sid]['original_correct']
        policies[sid] = {'original40_47_before_route': baseline}
        for key in baseline:
            tasks[key] = old_cpu['tasks'][key]; adopted[key] = old_gpu[key]
            decisions[key] = read(check(old_gpu[key]))['decision']
        for arm in ARMS:
            policies[sid][arm] = []
            for case in source.cases:
                output = read(check(generated[sid][arm][case.name]))
                # Native/token/greedy first QA already completed in72. Only
                # its identity is adopted here; do not replay it again.
                proof = read(SELECT / 'first_CPU' / (arm + '_' + case.name + '.json'))
                if proof['actual_output'] != generated[sid][arm][case.name]:
                    raise ValueError('Adopted first native output QA has a different actual result')
                for index, segment in enumerate(output['segments']):
                    event, request = candidate_request(case, source, segment, index)
                    key = request['request_id']
                    if key not in tasks:
                        previous = adopt(key, case, event, request, old_cpu, old_gpu)
                        if previous is None:
                            tasks[key] = prepare(case, event, request, folder / key, tokenizer, rt)
                        else:
                            tasks[key], adopted[key], decisions[key] = previous
                    elif tasks[key]['event'] != event or read(check(tasks[key]['request'])) != request:
                        raise ValueError('Distinct exact VERIFY tasks collided')
                    policies[sid][arm].append(key)
    if torch.cuda.is_initialized():
        raise ValueError('First remaining VERIFY input preparation initialized CUDA')
    save(OUT / 'completion.json', dict(state='FIRST_ALL_REQUIRED_EVENT_VERIFY_INPUTS_PASS',
        tasks=tasks, source_policies=policies, adopted_successful_outputs=adopted,
        adopted_independently_accepted_decisions=decisions, original_first_QA=old_first_QA,
        maximum_first_new_VERIFY_calls=len(set(tasks) - set(adopted)),
        old_successful_inference_or_QA_replayed=0, no_new_model_calls=True,
        no_human_labels_or_confirmation_read=True,
        downstream_always_uses_original_correct_video_without_machine_event_memory=True,
        original40_47_before_route_not_mislabeled_as40_48=True,
        next='First missing original-TIME VERIFY only under remaining fixed downstream budget, first new-output CPU QA, adopt original BASE semantic features, then exact fixed40.48 route before complete-source quality.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
