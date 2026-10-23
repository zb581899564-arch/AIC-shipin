"""First independent new2 output/gradient audit and unchanged complete-scope cost gate."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math

import numpy as np
import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from joint_data44 import Case, Source
from native_audit100 import audit
from native_sets import NativeTimeline
from native_training_data99 import coefficients
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_next_two104'
JOB = 'T_native_action_exact_remaining_input_reuse_two_20261023_v104'


def teacher_check(raw, rt, code):
    task = raw['target_binding']
    generated = read(check(read(check(raw['actual_greedy']))['raw']))
    proof = read(check(task['actual_input_CPU']))
    with np.load(check(proof['text']), allow_pickle=False) as archive:
        prefix = archive['input_ids'].copy()
    ids = np.concatenate([prefix, np.array([generated['tokens'][:-1]], dtype=np.int64)], axis=1)
    expected = dict(input_ids=torch.from_numpy(ids), attention_mask=torch.ones_like(torch.from_numpy(ids)))
    if (rt.tensor_signature(expected) != raw['actual_causal_text_signature']
            or raw['choice_logit_positions'] != list(range(prefix.shape[1], prefix.shape[1] + 64, 2))
            or generated['actual_model_state'] != raw['actual_model_state']):
        raise ValueError('Prepared teacher differs from actual greedy history or original prefix')
    binary = np.asarray(raw['binary_logits'], dtype=np.float64)
    logp = binary - binary.max(axis=1, keepdims=True)
    logp -= np.log(np.exp(logp).sum(axis=1, keepdims=True))
    a, b, weight = coefficients(task, raw['publisher_source_weight'])
    loss = -float(np.sum(a * logp[:, 0] + b * logp[:, 1])) * weight
    if (binary.shape != (32, 2) or not np.isfinite(binary).all()
            or not np.allclose(logp, raw['binary_logp'], atol=2e-5, rtol=2e-5)
            or not math.isclose(loss, raw['weighted_preference_loss'], abs_tol=2e-6, rel_tol=3e-5)):
        raise ValueError('Independent prepared teacher native preference loss differs')
    return loss


def gradient_check(ref, cursor):
    packet = torch.load(check(ref['file']), map_location='cpu', weights_only=True)
    gradients = packet['gradients']
    if packet['cursor'] != cursor or len(gradients) != 288:
        raise ValueError('Prepared cumulative gradient recovery cursor/inventory differs')
    if sum(v.numel() for v in gradients.values()) != 15335424 or any(
            ('.lora_A.actor.' not in name and '.lora_B.actor.' not in name)
            or value.dtype != torch.float32 or not torch.isfinite(value).all()
            for name, value in gradients.items()):
        raise ValueError('Prepared exact gradient affects protected parameters or is invalid')
    norm = math.sqrt(math.fsum(float(v.double().square().sum()) for v in gradients.values()))
    if not math.isclose(norm, ref['norm_float64'], abs_tol=1e-7, rel_tol=1e-7):
        raise ValueError('Independent prepared accumulated gradient norm differs')
    return norm


def projection(rows, charged):
    control = read(ROOT / 'native_action_control100/completion.json')
    output = read(check(control['actual_outputs']))
    baseline_max = max(read(check(ref))['seconds'] for ref in output['physical_raw'].values())
    micro = max(row['actual_shared_GPU_micro_seconds'] for row in rows)
    inference = max(baseline_max, *(row['actual_greedy_seconds'] for row in rows))
    transfer = max(row['actual_transfer_seconds'] for row in rows)
    overhead = max(60., charged - math.fsum(row['actual_shared_GPU_micro_seconds'] for row in rows))
    if max(row['bounded_CPU_load_seconds'] for row in rows) >= min(
            row['actual_shared_GPU_micro_seconds'] for row in rows):
        raise ValueError('Measured bounded CPU producer cannot keep up with GPU consumer')
    return dict(remaining_training_micros=214, remaining_final_dev_calls=150,
        actual_max_shared_GPU_micro_seconds=micro, actual_max_transfer_seconds=transfer,
        actual_max_inference_model_seconds=inference, actual_fixed_job_overhead_seconds=overhead,
        projected_remaining_seconds=214 * micro + 150 * (inference + transfer)
            + overhead + 5 * (max(row['actual_gradient_persistence_seconds'] for row in rows) + 2),
        bounded_producer_observed_faster_than_consumer=True, no_throughput_or_quality_guarantee=True)


def main():
    torch.set_num_threads(2)
    rt = runtime()
    result = read(OUT / 'GPU_completion.json')
    data = read(ROOT / 'native_action_loss99/completion.json')
    first = read(check(result['adopted_first_micro']))
    code = read(ROOT / 'native_action_contract98/completion.json')['actual_token_codec']
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    folder = OUT / 'first_CPU'
    folder.mkdir()
    rows, proofs = [], []
    for index, ref in enumerate(result['micro'], 2):
        row = read(check(ref))
        cursor = row['cursor']
        if cursor['completed_micro'] != index or cursor['optimizer_updates'] != 0:
            raise ValueError('Next fixed micro cursor is discontinuous')
        item = data['sources'][cursor['source']]
        target = item['cases'][index - 1]
        if target != row['actual_teacher']['target_binding']:
            raise ValueError('Prepared cost probe changed fixed original source order')
        source = Source(cursor['source'], [], NativeTimeline.from_clock(read(check(item['source']['clock']))), [], {})
        original = read(check(read(check(target['original_CPU']))['input']))
        case = Case(target['case'], target['original_CPU'], original, {}, {})
        _, proof = audit(row['actual_greedy'], source, case, target['actual_input_CPU'],
                         code, tokenizer, folder, {})
        loss = teacher_check(row['actual_teacher'], rt, code)
        norm = gradient_check(row['exact_recovery_gradient'], cursor)
        proofs.append(dict(cursor=cursor, greedy_CPU=proof, source_global_preference_loss_FP64=loss,
                           exact_accumulated_gradient_norm_FP64=norm))
        rows.append(row)
    if len(rows) != 2 or result['actual_optimizer_updates'] != 0 or torch.cuda.is_initialized():
        raise ValueError('Fixed remaining-two engineering denominator differs')
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    costs = projection(rows, resource['charged_seconds'])
    prior = read(ROOT / 'native_first_micro101/completion.json')
    remaining = prior['native_combined_remaining_seconds'] - resource['charged_seconds']
    save(OUT / 'CPU_completion.json', dict(state='FIRST_REMAINING_TWO_CPU_PASS_COST_' + (
        'PASS' if costs['projected_remaining_seconds'] <= remaining else 'STOP'),
        first_output_and_teacher_and_gradient_CPU=proofs, first101_proof_adopted=True,
        old_sequential_cost_STOP_preserved=True, new_actual_greedy_calls=2, new_actual_teacher_backwards=2,
        actual_optimizer_updates=0, total_prescribed_micros_complete=3,
        projection=costs, original5600_remaining_seconds=remaining,
        remaining214_and150dev_cost_admitted=costs['projected_remaining_seconds'] <= remaining,
        actual_parameters=8869330010, no_quality_or_confirmation_or_production_admission=True))


if __name__ == '__main__':
    main()
