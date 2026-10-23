"""First complete source fitting metrics; no final checkpoint or rule selection."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math

import numpy as np
import torch

from event_full79 import independent_set_metrics
from native_training_data99 import coefficients
from parallel_audit107 import audit
from parallel_train108 import cases
from preference_reward import SummaryReview, summary_agreement
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'parallel_fit115'


def reviews(source):
    inventory = read(ROOT / 'native_action_feasibility97/completion.json')
    ref = next(row['original_reference'] for row in inventory['sources'] if row['source']['sid'] == source.sid)
    original = read(check(ref))
    with np.load(check(original['tensor']), allow_pickle=False) as data:
        target = data['summary_selected'].copy(); domain = data['summary_task_domain'].copy()
    return [SummaryReview(name, mask, domain) for name, mask in zip(original['all_original_reviewers'], target)]


def final_loss(output, target):
    raw = read(check(read(check(output))['raw']))
    logits = np.array(raw['binary_logits'], dtype=np.float64)
    logp = logits - logits.max(axis=1, keepdims=True)
    logp -= np.log(np.exp(logp).sum(axis=1, keepdims=True))
    a, b, _ = coefficients(target, '1')
    return -float((a * logp[:, 0] + b * logp[:, 1]).sum())


def main():
    torch.set_num_threads(2)
    lock = read(OUT / 'source_input_lock.json')
    inputs = read(check(lock['actual_inputs'])); data = read(check(inputs['loss_bindings']))
    source = cases(data)[lock['source']]; source.reviews = reviews(source)
    result = read(OUT / 'GPU_completion.json'); initial = lock['initial_outputs']
    if set(initial) != set(result['outputs']) or len(initial) != 25:
        raise ValueError('Complete initial/final fitting domain differs')
    masks = {name: np.zeros(len(source.timeline.points), dtype=bool) for name in ['initial', 'final']}
    folder = OUT / 'first_final_CPU'; folder.mkdir(); proofs = []
    loss = 0.
    for case, target in zip(source.cases, data['sources'][source.sid]['cases']):
        old = read(check(initial[case.name]))
        if old['actual_model_state'] != lock['initial_model_state']:
            raise ValueError('Adopted pre-update fitting control had later model weights')
        masks['initial'] |= source.selection(case, old)
        ref = result['outputs'][case.name]
        mask, proof = audit(ref, source, case, inputs['fit'][source.sid][case.name],
                            inputs['actual_query_code'], folder)
        if read(check(ref))['actual_model_state'] != result['actual_model_state']:
            raise ValueError('Final fitting outputs use mixed model states')
        masks['final'] |= mask; proofs.append(proof); loss += final_loss(ref, target)
    metrics = {}
    for name, mask in masks.items():
        score = summary_agreement(mask, source.reviews, len(source.reviews))
        other = independent_set_metrics(mask, source.reviews, len(source.reviews))
        if abs(other - score['mean_f1']) > 1e-12:
            raise ValueError('First fitting source/all-reviewer F1 arithmetic differs')
        metrics[name] = dict(mean_summary_F1=other, selected_native_frames=int(mask.sum()),
                             selected_fraction=float(mask.mean()))
    if torch.cuda.is_initialized() or not math.isfinite(loss):
        raise ValueError('Fitting diagnostic CPU role or complete source loss differs')
    save(OUT / 'CPU_completion.json', dict(state='FIRST_FINAL_FIT25_ALL_NATIVE_CPU_AND_METRICS_PASS',
        first_new_output_proofs=proofs, initial_training_QA_adopted=lock['initial_first_CPU'],
        source=source.sid, all_original_reviewers=len(source.reviews), metrics=metrics,
        initial_source_training_loss=lock['initial_source_training_loss'], final_source_training_loss=loss,
        no_initial_model_or_QA_repeated=True, coarse_fitting_diagnostic_only=True,
        old105_full_development_STOP_unchanged=True, no_confirmation_or_production_admission=True))


if __name__ == '__main__':
    main()
