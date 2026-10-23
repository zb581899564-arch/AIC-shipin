"""First missing VERIFY inputs after all150 source-goal native outputs pass."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import traceback

import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from development_verify46 import candidate_request, prepare
from frozen_branch46 import RUN
from summary_context90 import ARMS
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime
from verify_adoption92 import accepted_catalog, adopt

OUT = ROOT / 'summary_verify_inputs92'
SELECT = ROOT / 'summary_selection91'


def main():
    OUT.mkdir(); torch.set_num_threads(2); rt = runtime()
    terminal = read(SELECT / 'completion.json')
    if terminal['state'] != 'PASS_FIRST_ALL150_CONTENT_GOAL_NATIVE_OUTPUTS_NOT_FULL40_48_QUALITY':
        raise ValueError('All150 first independent native output proofs required')
    tokenizer = AutoTokenizer.from_pretrained(
        read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = development_sources(rt, tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=True, labels=False)
    catalog, old_QA = accepted_catalog()
    old = read(ROOT / 'development_remaining55/verify_CPU_completion.json')
    generated = read(SELECT / 'GPU_completion.json')['outputs']
    folder = OUT / 'requests'; folder.mkdir()
    tasks, policies, adopted, decisions = {}, {}, {}, {}
    for sid, source in sources.items():
        original = old['source_policies'][sid]['original_correct']
        policies[sid] = {'original40_47_before_route': original}
        for key in original:
            item = catalog[key]; tasks[key] = item['task']
            adopted[key], decisions[key] = item['output'], item['decision']
        for arm in ARMS:
            policies[sid][arm] = []
            for case in source.cases:
                ref = generated[sid][arm][case.name]; output = read(check(ref))
                proof = read(SELECT / 'first_CPU' / (arm + '_' + case.name + '.json'))
                if proof['actual_output'] != ref:
                    raise ValueError('Adopted first native QA has a different actual output')
                for index, segment in enumerate(output['segments']):
                    event, request = candidate_request(case, source, segment, index)
                    key = request['request_id']
                    if key not in tasks:
                        item = adopt(catalog, key, case, event, request)
                        if item is None:
                            tasks[key] = prepare(case, event, request, folder / key, tokenizer, rt)
                        else:
                            tasks[key] = item['task']
                            adopted[key], decisions[key] = item['output'], item['decision']
                    elif tasks[key]['event'] != event or read(check(tasks[key]['request'])) != request:
                        raise ValueError('Distinct exact candidate VERIFY inputs collided')
                    policies[sid][arm].append(key)
    if torch.cuda.is_initialized():
        raise ValueError('First remaining VERIFY preparation initialized CUDA')
    save(OUT / 'completion.json', dict(state='ALL_CONTENT_GOAL_VERIFY_INPUTS_PASS',
        tasks=tasks, source_policies=policies, adopted_successful_outputs=adopted,
        adopted_independently_accepted_decisions=decisions, old_first_QA=old_QA,
        adopted_first_native_QA=identity(SELECT / 'CPU_completion.json'),
        maximum_first_new_VERIFY_calls=len(set(tasks) - set(adopted)),
        no_old_inference_or_QA_repeated=True, no_human_labels_or_confirmation_read=True,
        downstream_video_original_without_event_or_summary_context=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
