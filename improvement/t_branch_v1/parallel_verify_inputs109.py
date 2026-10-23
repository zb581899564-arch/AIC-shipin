"""First missing exact VERIFY texts, existing native video referenced without decoding."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
import shutil
import traceback

import torch
from transformers import AutoTokenizer

from coarse_call25 import load_case
from development_data46 import development_sources
from development_verify46 import prepare
from event_chain78 import measured_cost
from frozen_branch46 import RUN
from parallel_verify_plan109 import plan
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'parallel_verify_inputs109'


def main():
    OUT.mkdir()
    torch.set_num_threads(2)
    native = read(ROOT / 'parallel_remaining108/completion.json')
    if native['state'] != 'COMPLETE217_TRAINING_AND150_DEV_FIRST_CPU_PASS_NOT_QUALITY':
        raise ValueError('Actual complete217 training/final150 outputs/first independent CPU required')
    protocol = read(ROOT / 'code/parallel_protocol105.json')
    rt = runtime()
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    old = read(ROOT / 'parallel_verify_catalog109/completion.json')
    if old['state'] != 'ALL_PRIOR_EXACT_VERIFY_ADOPTION_CATALOG109_BOUND':
        raise ValueError('Prior successful exact VERIFY adoption index not bound')
    previous, proofs = old['catalog'], old['original_first_QA']
    planned = plan(sources, protocol, previous)
    calls = planned['maximum_first_new_VERIFY_calls']
    cost = measured_cost(calls)
    if calls == 0:
        cost['conservative_estimate'] = 0.
        cost['no_new_GPU_load_required'] = True
    remaining = math.floor(protocol['profile_GPU_seconds_max_all_failures'] - native['profile_GPU_seconds'])
    required = calls * (16384 * 16 + 16384 + 131072) + 8388608
    save(OUT / 'first_complete_request_plan.json', dict(**planned, measured_cost=cost,
        remaining_fixed_profile_GPU_seconds=remaining, proposed_specific_bytes=required,
        adopted_old_first_VERIFY_QA=proofs, no_media_processor_ASR_or_old_GPU_calls=True,
        original4_confirmation_unread=True))
    if cost['conservative_estimate'] > remaining or native['all_goal_GPU_seconds'] + remaining > 43200:
        save(OUT / 'cost_STOP.json', dict(state='STOP_COMPLETE_PARALLEL_VERIFY_COST_BEFORE_ANY_NEW_INPUT_OR_GPU',
            actual_first_new_calls=calls, cost=cost, remaining=remaining,
            all_source_outputs_retained=True, no_partial_source_or_cap_change=True))
        return
    if shutil.disk_usage(ROOT).free < required:
        raise RuntimeError('Specific complete new VERIFY text/raw/proof artifacts do not fit current root capacity')
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    requests = OUT / 'requests'
    requests.mkdir()
    tasks = dict(planned['tasks'])
    pending_by_case = {}
    for key, entry in planned['pending'].items():
        pending_by_case.setdefault(entry['case'], []).append((key, entry))
    for source in sources.values():
        for case in source.cases:
            if case.name not in pending_by_case:
                continue
            case.values = load_case(case.CPU, rt, tokenizer)[2]
            for key, entry in pending_by_case[case.name]:
                tasks[key] = prepare(case, entry['event'], entry['request'], requests / key, tokenizer, rt)
                print('PARALLEL109_FIRST_VERIFY_TEXT', key, flush=True)
            case.values = {}
    if len(tasks) != len(planned['tasks']) + calls or torch.cuda.is_initialized():
        raise ValueError('Complete first/adopted VERIFY input denominator or CPU role differs')
    save(OUT / 'completion.json', dict(state='COMPLETE_PARALLEL_VERIFY_INPUTS_CPU_PASS',
        tasks=tasks, source_policies=planned['source_policies'],
        adopted_successful_outputs=planned['adopted_successful_outputs'],
        adopted_independently_accepted_decisions=planned['adopted_independently_accepted_decisions'],
        old_first_QA=proofs, adopted_first_new_policy_CPU=identity(ROOT / 'parallel_remaining108/CPU_completion.json'),
        maximum_first_new_VERIFY_calls=calls, remaining_fixed_profile_GPU_seconds=remaining,
        cost_estimate=cost, proposed_specific_bytes=required,
        no_old_models_inputs_or_QA_repeated=True, downstream_always_original_correct_video=True,
        original4confirmation_unread=True, no_quality_or_production_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successful_requests=True))
        raise
