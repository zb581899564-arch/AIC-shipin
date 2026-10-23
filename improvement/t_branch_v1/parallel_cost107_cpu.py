"""First full50 control QA, saved first gradient and complete-scope cost projection."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math

import torch

from development_data46 import development_sources
from frozen_branch46 import RUN
from joint_data44 import Case, Source
from native_next_two104_cpu import gradient_check
from native_sets import NativeTimeline
from parallel_audit107 import audit
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'parallel_cost107'
JOB = 'T_parallel_queries_original50_first_gradient_20261023_v107'


def projection(control, micro, charged):
    # Measured one-worker producer and GPU consumer overlap; no assumed infinite prefetch.
    train_rate = max(micro['CPU_load_seconds'], micro['GPU_consumer_seconds_excluding_first_CPU'])
    dev_rate = max(max(row['CPU_load_seconds'], row['actual_consumer_seconds'])
                   for row in control['timings'])
    overhead = max(60., charged - control['actual_pipeline_seconds'] - micro['CPU_load_seconds']
        - micro['GPU_consumer_seconds_excluding_first_CPU'] - micro['one_off_CPU_seconds'])
    result = 216 * train_rate + 150 * dev_rate + overhead + 5 * (
        micro['actual_gradient_persistence_seconds'] + 2)
    return dict(complete_remaining_training_windows=216, complete_remaining_dev_calls=150,
        measured_train_producer_consumer_rate_seconds=train_rate,
        measured_dev_producer_consumer_rate_seconds=dev_rate, measured_fixed_overhead_seconds=overhead,
        projected_complete_remaining_seconds=result, one_off_first_full_vocab_CPU_not_repeated=True,
        observed_throughput_estimate_not_time_or_quality_guarantee=True)


def main():
    torch.set_num_threads(2)
    raw = read(OUT / 'GPU_completion.json')
    actual = read(ROOT / 'parallel_inputs106/completion.json')
    protocol = read(ROOT / 'code/parallel_protocol105.json')
    controls = read(check(raw['initial_controls']))
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    folder = OUT / 'first_control_CPU'
    folder.mkdir()
    proofs = {}
    for sid, source in sources.items():
        if set(controls['outputs'][sid]) != {case.name for case in source.cases}:
            raise ValueError('First complete originalTIME query control source domain differs')
        for case in source.cases:
            _, proof = audit(controls['outputs'][sid][case.name], source, case,
                actual['development'][sid][protocol['input_arm_keys'][0]][case.name],
                actual['actual_query_code'], folder)
            proofs[case.name] = proof
    micro = raw['first_micro']
    data = read(check(actual['loss_bindings']))
    item = data['sources'][micro['cursor']['source']]
    target = item['cases'][0]
    if target != micro['target_binding'] or micro['cursor']['completed_micro'] != 1:
        raise ValueError('First fixed query training case does not match source loss registration')
    source = Source(micro['cursor']['source'], [],
        NativeTimeline.from_clock(read(check(item['source']['clock']))), [], {})
    meta = read(check(read(check(target['original_CPU']))['input']))
    case = Case(target['case'], target['original_CPU'], meta, {}, {})
    first_folder = OUT / 'first_training_output_CPU'
    first_folder.mkdir()
    _, first = audit(micro['actual_selection'], source, case, target['actual_input_CPU'],
                     actual['actual_query_code'], first_folder)
    norm = gradient_check(micro['exact_successful_gradient'], micro['cursor'])
    packet = torch.load(check(micro['exact_successful_gradient']['file']), map_location='cpu', weights_only=True)
    checkpoint = torch.load(check(micro['initial_actor_optimizer']), map_location='cpu', weights_only=True)
    if packet['publisher_checkpoint'] != micro['initial_actor_optimizer'] or checkpoint['completed_episode'] != 0:
        raise ValueError('First parallel gradient/actor/Adam exact recovery binding differs')
    if len(proofs) != 50 or raw['actual_optimizer_updates'] != 0 or torch.cuda.is_initialized():
        raise ValueError('Full50 controls/first gradient CPU denominator or execution role differs')
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    cost = projection(controls, micro, resource['charged_seconds'])
    remaining = protocol['training_and_development_GPU_seconds_max'] - resource['charged_seconds']
    fits = cost['projected_complete_remaining_seconds'] <= remaining
    save(OUT / 'CPU_completion.json', dict(state='FIRST_PARALLEL50_CONTROL_GRADIENT_CPU_PASS_COST_' + (
        'PASS' if fits else 'STOP'), original50_control_first_CPU=proofs, first_training_output_CPU=first,
        first_full_vocabulary_TF_CPU=micro['actual_first_CPU'], gradient_norm_FP64=norm,
        new_native_optimizer_updates=0, first_complete_parameters=8869330010,
        projection=cost, remaining_native3600_seconds=remaining,
        remaining216_and150dev_cost_admitted=fits, no_quality_confirm_or_production_admission=True,
        no_old_successful_calls_or_QA_repeated=True))


if __name__ == '__main__':
    main()
