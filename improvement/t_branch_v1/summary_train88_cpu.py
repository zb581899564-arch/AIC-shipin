"""First exact-recovery/weighting review and independent first AdamW update check."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
import math

import numpy as np
import torch

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_train88'


def first_AdamW(ref):
    raw = torch.load(check(ref), map_location='cpu', weights_only=True)
    if (raw['step'] != 1 or raw['learning_rate'] != 5e-5 or raw['epsilon'] != 1e-8
            or raw['betas'] != [.9, .999] or raw['weight_decay'] != 0.):
        raise ValueError('First actual AdamW witness does not match registered optimizer')
    names = set(raw['before'])
    if names != set(raw['after']) or names != set(raw['clipped_gradient']) or len(names) != 288:
        raise ValueError('First actual complete optimizer witness tensor denominator differs')
    clipped = torch.load(check(raw['actual_clipped_gradient']['file']), map_location='cpu', weights_only=True)['gradients']
    if set(clipped) != names or any(not torch.equal(clipped[k], raw['clipped_gradient'][k]) for k in names):
        raise ValueError('First optimizer witness does not bind its saved actual clipped gradient')
    largest = 0.; changed = 0
    for name in names:
        before = raw['before'][name].numpy().astype(np.float64)
        gradient = raw['clipped_gradient'][name].numpy().astype(np.float64)
        after = raw['after'][name].numpy().astype(np.float64)
        expected = before - 5e-5 * gradient / (np.abs(gradient) + 1e-8)
        if not np.isfinite(expected).all() or not np.allclose(after, expected, atol=1e-8, rtol=3e-6):
            raise ValueError('Independent NumPyFP64 first AdamW update differs')
        largest = max(largest, float(np.max(np.abs(after - expected))))
        changed += int(np.count_nonzero(before != after))
    if not changed:
        raise ValueError('First physical optimizer witness changed no actual value')
    return dict(complete_tensors=288, maximum_FP64_vs_actual_absolute_error=largest,
                actual_changed_elements=changed, raw=ref)


def gradient_checkpoint(ref, cursor):
    payload = torch.load(check(ref), map_location='cpu', weights_only=True)
    if payload['cursor'] != cursor or not payload['exact_accumulated_gradient']:
        raise ValueError('Exact micro-recovery cursor differs from the actual successful forward')
    values = payload['gradients']; size = sum(v.numel() for v in values.values())
    if len(values) != 288 or size != 15335424:
        raise ValueError('Recovery gradient tensor/parameter denominator differs')
    if any(('.lora_A.summary.' not in name and '.lora_B.summary.' not in name)
           or '.visual.' in name or not torch.isfinite(v).all() for name, v in values.items()):
        raise ValueError('A saved gradient is nonfinite or targets a protected parameter')
    return math.sqrt(math.fsum(float(v.double().square().sum()) for v in values.values()))


def main():
    torch.set_num_threads(2)
    result = read(OUT / 'GPU_completion.json')
    data = read(ROOT / 'summary_text_inputs87/completion.json')
    rows = [read(check(ref)) for ref in result['publisher_updates']]
    if len(rows) != 10 or result['actual_target_forwards'] != 172 or result['actual_optimizer_updates'] != 10:
        raise ValueError('Fixed actual10 update/172 review scope incomplete')
    observed, first, micro = {}, None, 0
    for update in rows:
        if update['optimizer_updates'] != 1 or update['before'] == update['after']:
            raise ValueError('A publisher update was fictitious or repeated')
        group_weight = Fraction(0)
        for ref in update['all_original_reviews']:
            row = read(check(ref)); cursor = row['cursor']; micro += 1
            if cursor['micro'] != micro or cursor['episode'] != update['episode']:
                raise ValueError('Successful micro-batch sequence is discontinuous')
            target = row['actual_target']; weight = Fraction(row['publisher_update_weight'])
            if weight != 5 * Fraction(target['global_publisher_source_reviewer_weight']):
                raise ValueError('Actual publisher/source/reviewer loss weighting differs')
            if row['causal_signature'] != target['actual_causal_signature']:
                raise ValueError('Actual teacher-forced data differs from accepted original complete target')
            mean = -math.fsum(row['selected_target_logp']) / len(target['target_ids'])
            if len(row['selected_target_logp']) != len(target['target_ids']) or not math.isclose(mean, row['mean_NLL'], abs_tol=3e-5, rel_tol=3e-5):
                raise ValueError('Independent all-target projection/mean loss arithmetic differs')
            if not math.isclose(mean * float(weight), row['weighted_NLL'], abs_tol=3e-5, rel_tol=3e-5):
                raise ValueError('Actual per-review weighted loss differs from its registered denominator')
            norm = gradient_checkpoint(row['exact_recovery_gradient']['file'], cursor)
            if not math.isclose(norm, row['exact_recovery_gradient']['norm_float64'], rel_tol=1e-7, abs_tol=1e-7):
                raise ValueError('First independent saved cumulative gradient norm differs')
            key = (cursor['source'], cursor['original_review_row'])
            observed[key] = observed.get(key, 0) + 1; group_weight += weight
        if group_weight != 1:
            raise ValueError('Actual complete publisher loss mass differs')
        checkpoint = torch.load(check(update['recovery_checkpoint']), map_location='cpu', weights_only=True)
        if checkpoint['completed_optimizer_updates'] != update['episode']:
            raise ValueError('Exact publisher recovery checkpoint update identity differs')
        if update['episode'] == 1:
            first = first_AdamW(update['first_optimizer_witness'])
    expected = {(sid, row['original_row']): 2 for sid, targets in data['source_targets'].items() for row in targets}
    if observed != expected or micro != 172 or torch.cuda.is_initialized():
        raise ValueError('Not all86 original reviews were used exactly once per epoch')
    save(OUT / 'independent_CPU_completion.json', dict(state='PASS_FIRST_CONTENT_TRAINING_REVIEW_AND_EXACT_RECOVERY_CPU',
        actual_optimizer_updates=10, actual_whole_target_forwards=172, original_review_rows=86,
        all_172_causal_inputs_and_loss_weights_checked=True, all_172_gradient_recovery_files_checked=True,
        first_real_AdamW_update=first, first_full_vocab_TF_proof=identity(OUT / 'first_TF_independent_CPU.json'),
        actor_final=result['actor_final'], actual_complete_parameters=result['actual_complete_pipeline_parameters'],
        final_actual_FP32_save_reload=result['final_adapter'], no_free_generation_or_time_quality_claim=True,
        new8B_calls=0, no_successful_training_or_input_replayed=True))


if __name__ == '__main__':
    main()
