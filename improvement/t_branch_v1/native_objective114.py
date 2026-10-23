"""Fit-only objective audit: analytic reference policies are never model results."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
import traceback

import numpy as np
import torch

from native_units97 import reviewer_counts
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'native_objective114'


def agreement(chosen, positives, observed):
    true_positive = positives[:, chosen].sum(axis=1)
    denominator = observed[chosen].sum() + positives.sum(axis=1)
    if np.any(denominator <= 0):
        raise ValueError('Original reviewer has no observed selected task support')
    return float(np.mean(2. * true_positive / denominator))


def gradient_contract(positives, observed):
    """Two-pass chain rule checked against the full source graph; no model call."""
    target = torch.tensor(positives, dtype=torch.float64)
    domain = torch.tensor(observed, dtype=torch.float64)
    probability = torch.full_like(domain, .5, requires_grad=True)
    overlap = target @ probability
    denominator = (domain @ probability) + target.sum(dim=1)
    full_loss = -(2 * overlap / denominator).mean()
    full_gradient = torch.autograd.grad(full_loss, probability)[0]
    coefficient = -(2 * (target * denominator[:, None] - overlap[:, None] * domain)
                    / denominator[:, None].square()).mean(dim=0).detach()
    error = float((full_gradient - coefficient).abs().max())
    if error > 1e-12 or bool(coefficient[domain == 0].any()):
        raise ValueError('Source-global chain rule or unobserved-task gradient differs')
    return dict(maximum_absolute_error=error, all_cells=int(len(domain)),
                source_global_derivative_not_a_local_window_loss=True,
                no_actual8B_gradient_or_new_training=True)


def audit(row):
    reference = read(check(row['original_reference']))
    with np.load(check(reference['tensor']), allow_pickle=False) as data:
        selected = data['summary_selected'].copy()
        domain = data['summary_task_domain'].copy()
    with np.load(check(row['native_cells']), allow_pickle=False) as data:
        spans = list(zip(data['native_start'].tolist(), data['native_stop'].tolist()))
        a = data['summary_action_positive_coefficient'].copy()
        b = data['summary_action_negative_coefficient'].copy()
    counts = [reviewer_counts(spans, mask, domain) for mask in selected]
    positives = np.stack([pair[0] for pair in counts])
    observed = counts[0][1]
    if (any(not np.array_equal(pair[1], observed) for pair in counts)
            or len(selected) != row['reviewers'] or len(spans) != row['cells']):
        raise ValueError('All-original-reviewer/domain/native-cell denominator changed')
    balanced = a > b
    posterior_positive = positives.mean(axis=0)
    unbalanced = posterior_positive > observed - posterior_positive
    policies = dict(balanced_CE_reference_minimizer=balanced,
                    unbalanced_CE_reference_minimizer=unbalanced,
                    all_observed_task_units=observed > 0)
    return dict(source=row['source']['sid'], original_reviewers=len(selected),
        native_cells=len(spans), original_reference=row['original_reference'],
        policies={name: dict(mean_summary_F1=agreement(mask, positives, observed),
            selected_native_frames=int(observed[mask].sum()),
            selected_task_fraction=float(observed[mask].sum() / observed.sum()))
            for name, mask in policies.items()},
        source_global_soft_F1_derivative=gradient_contract(positives, observed),
        label_values_only_for_diagnosis_never_inference=True)


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    terminal = read(ROOT / 'parallel_diagnosis113/completion.json')
    if terminal['state'] != 'FIRST_STOP105_STAGEWISE_CPU_DIAGNOSIS_COMPLETE':
        raise ValueError('Complete rejected-profile diagnosis required before this fit-only audit')
    inventory = read(ROOT / 'native_action_feasibility97/completion.json')
    if len(inventory['sources']) != 9 or any(r['source']['role'] != 'fit' for r in inventory['sources']):
        raise ValueError('Only original nine fitting sources admitted, never development/confirmation')
    save(OUT / 'registration.json', dict(completed_diagnosis=identity(ROOT / 'parallel_diagnosis113/completion.json'),
        original_reference_inventory=identity(ROOT / 'native_action_feasibility97/completion.json'),
        scope='Reference-defined loss minimizers, task sparsity and exact source-gradient feasibility only',
        not_a_new_soft_F1_algorithm='Earlier small-head softF1 failures stay rejected; this audit is no model test',
        no_threshold_search_or_new_profile_or_quality_admission=True,
        code=identity(ROOT / 'code/native_objective114.py')))
    rows = [audit(row) for row in inventory['sources']]
    if sum(row['original_reviewers'] for row in rows) != 86 or torch.cuda.is_initialized():
        raise ValueError('Original86-reviewer CPU-only audit domain differs')
    names = list(rows[0]['policies'])
    save(OUT / 'completion.json', dict(state='FIRST_FIT_ONLY_NATIVE_OBJECTIVE_AND_CHAIN_RULE_CPU_AUDIT_COMPLETE',
        sources=rows, mean_reference_defined_F1={name: math.fsum(
            row['policies'][name]['mean_summary_F1'] for row in rows) / len(rows) for name in names},
        no_reference_policy_as_model_or_official_score=True, summary_omissions_semantic_UNKNOWN=True,
        no_new_model_calls_training_or_package_admission=True,
        development_or_confirmation_labels_read=False, old105_STOP_unchanged=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_successes=True))
        raise
