"""First inverse-query/output audit and label-free equivariance/null comparison."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import numpy as np
import torch

from parallel_audit107 import audit
from parallel_train108 import cases
from query_binding117_common import layout
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'query_binding117'


def margins(ref):
    raw = read(check(read(check(ref))['raw']))
    values = np.array(raw['binary_logits'], dtype=np.float64)
    if values.shape != (32, 2) or not np.isfinite(values).all():
        raise ValueError('Accepted query logits incomplete/nonfinite')
    return values[:, 0] - values[:, 1], values


def error(transformed, expected):
    centered = transformed - transformed.mean(axis=1, keepdims=True)
    baseline = expected - expected.mean(axis=1, keepdims=True)
    flat, other = centered.ravel(), baseline.ravel()
    scale = float(np.linalg.norm(flat) * np.linalg.norm(other))
    return dict(raw_mean_squared_error=float(np.mean((transformed - expected) ** 2)),
        within_window_centered_MSE=float(np.mean((centered - baseline) ** 2)),
        centered_correlation=float(flat @ other / scale) if scale else None,
        source_mean_margin_shift=float((transformed - expected).mean()))


def validate_mapping(mapping_ref, output_ref, proof, expected_state):
    raw = read(check(mapping_ref)); row = read(check(proof))
    if (raw['actual_input'] != proof or raw['actual_output'] != output_ref
            or raw['actual_model_state'] != expected_state or raw['actual_forward_calls'] != 1
            or raw['query_to_native'] != row['query_to_native']
            or raw['actual_query_anchor_indices'] != row['actual_query_anchor_indices']
            or raw['actual_query_positions'] != row['query_positions']):
        raise ValueError('Actual inverse-query raw belongs to a different input/model/output')
    query = np.array(raw['query_order_binary_logits'], dtype=np.float64)
    if query.shape != (32, 2) or not np.isfinite(query).all():
        raise ValueError('Actual transformed query output is incomplete/nonfinite')
    expected = np.stack([query[row['query_to_native'].index(j)] for j in range(32)])
    _, native = margins(output_ref)
    if not np.array_equal(expected, native):
        raise ValueError('Independent native-order logits do not match actual inverse mapping')


def main():
    torch.set_num_threads(2)
    inputs = read(ROOT / 'query_binding_inputs117/completion.json')
    result = read(OUT / 'GPU_completion.json')
    old = read(ROOT / 'parallel_inputs106/completion.json'); data = read(check(old['loss_bindings']))
    source = cases(data)[inputs['source']]
    original = read(ROOT / 'parallel_fit115/GPU_completion.json')
    if result['actual_model_state'] != original['actual_model_state']:
        raise ValueError('Causal diagnosis changed the frozen final actor')
    analyses, proofs = {}, []
    code = inputs['actual_query_code']
    def choice(margin):
        return (margin > 0) | ((margin == 0) & (code['Yes'] < code['No']))
    for arm, outputs in result['outputs'].items():
        folder = OUT / ('first_CPU_' + arm); folder.mkdir()
        before, after, null = [], [], []
        cells, labels = layout(arm); inverse = np.argsort(cells)
        null_indices = inverse if arm == 'reverse_query_order' else np.array(labels)[inverse]
        for case in source.cases:
            ref = outputs[case.name]; proof = inputs['inputs'][arm][case.name]
            validate_mapping(result['query_mapping_raw'][arm][case.name], ref, proof, result['actual_model_state'])
            _, accepted = audit(ref, source, case, proof, inputs['actual_query_code'], folder)
            proofs.append(accepted)
            old_margin, _ = margins(original['outputs'][case.name]); new_margin, _ = margins(ref)
            before.append(old_margin); after.append(new_margin); null.append(old_margin[null_indices])
        native, changed, prior = np.stack(before), np.stack(after), np.stack(null)
        equivariant, fixed_prior = error(changed, native), error(changed, prior)
        analyses[arm] = dict(native_cell_equivariance=equivariant, fixed_interface_prior=fixed_prior,
            interface_null='query_absolute_position' if arm == 'reverse_query_order' else 'anchor_token_identity',
            interface_prior_has_lower_centered_error=(fixed_prior['within_window_centered_MSE']
                                                       < equivariant['within_window_centered_MSE']),
            native_action_agreement=float(np.mean(choice(changed) == choice(native))),
            interface_prior_action_agreement=float(np.mean(choice(changed) == choice(prior))),
            complete_windows=len(before), native_cells=int(native.size), not_quality_or_official_score=True)
    if len(proofs) != 50 or torch.cuda.is_initialized():
        raise ValueError('Complete50 first native/permutation QA domain or CPU-only role differs')
    save(OUT / 'CPU_completion.json', dict(state='FIRST_ALL50_QUERY_BINDING_CPU_AND_CAUSAL_DIAGNOSIS_COMPLETE',
        first_new_output_proofs=proofs, analyses=analyses,
        original25_first_CPU_adopted=identity(ROOT / 'parallel_fit115/CPU_completion.json'),
        no_labels_or_new_F1_scoring_or_candidate_selection=True, no_original_model_or_QA_repeated=True,
        old105_STOP_unchanged=True, no_confirmation_training_or_production_admission=True))


if __name__ == '__main__':
    main()
