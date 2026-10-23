"""First fitting-source ranking/position diagnosis; no cutoffs or candidate scan."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import traceback

import numpy as np

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'parallel_discrimination116'


def concordance(margin, positive, negative):
    """Weighted probability a summary-task positive outranks a task omission."""
    order = np.argsort(margin, kind='stable')
    mass = float(positive.sum() * negative.sum())
    if mass <= 0:
        return None
    below = value = 0.; index = 0
    while index < len(order):
        stop = index + 1
        while stop < len(order) and margin[order[stop]] == margin[order[index]]:
            stop += 1
        group = order[index:stop]
        pos, neg = float(positive[group].sum()), float(negative[group].sum())
        value += pos * (below + .5 * neg)
        below += neg; index = stop
    return value / mass


def describe(margins, positive, negative):
    flat = margins.ravel()
    fast = concordance(flat, positive, negative)
    difference = flat[:, None] - flat[None, :]
    brute = float((positive[:, None] * negative[None, :] *
        ((difference > 0) + .5 * (difference == 0))).sum() / (positive.sum() * negative.sum()))
    if fast is None or abs(fast - brute) > 1e-12:
        raise ValueError('Independent pairwise weighted concordance disagrees')
    variance = float(np.var(margins))
    anchor_fraction = float(np.var(margins.mean(axis=0)) / variance) if variance else 0.
    window_fraction = float(np.var(margins.mean(axis=1)) / variance) if variance else 0.
    numerator = mass = 0.
    for index, row in enumerate(margins):
        a, b = positive[index*32:(index+1)*32], negative[index*32:(index+1)*32]
        local = concordance(row, a, b); weight = float(a.sum() * b.sum())
        if local is not None:
            numerator += weight * local; mass += weight
    return dict(source_summary_task_weighted_AUC=fast,
        independently_exhaustive_pairwise_AUC=brute,
        within_window_summary_task_weighted_AUC=numerator / mass if mass else None,
        summary_positive_weighted_margin=float(positive @ flat / positive.sum()),
        summary_omission_weighted_margin=float(negative @ flat / negative.sum()),
        fixed_anchor_column_fraction_of_unweighted_margin_variance=anchor_fraction,
        whole_window_row_fraction_of_unweighted_margin_variance=window_fraction,
        fixed_anchor_effect_is_diagnostic_not_proof_of_causal_token_bias=True)


def main():
    OUT.mkdir()
    terminal = read(ROOT / 'parallel_fit115/completion.json')
    if terminal['state'] != 'FIRST_FINAL_FIT25_ALL_NATIVE_CPU_AND_METRICS_PASS':
        raise ValueError('Complete first final-fit/model/CPU/ledger evidence required')
    lock = read(ROOT / 'parallel_fit115/source_input_lock.json')
    inputs = read(check(lock['actual_inputs'])); data = read(check(inputs['loss_bindings']))
    sid = lock['source']; cases = data['sources'][sid]['cases']
    selected = next(row for row in read(ROOT / 'native_action_feasibility97/completion.json')['sources']
                    if row['source']['sid'] == sid)
    with np.load(check(selected['native_cells']), allow_pickle=False) as native:
        a = native['summary_action_positive_coefficient'].copy()
        b = native['summary_action_negative_coefficient'].copy()
    final = read(ROOT / 'parallel_fit115/GPU_completion.json')['outputs']
    if len(cases) != 25 or a.shape != (800,) or b.shape != (800,):
        raise ValueError('Entire old first publisher/native-cell domain differs')
    save(OUT / 'registration.json', dict(actual_complete_fit=identity(ROOT / 'parallel_fit115/completion.json'),
        first_fit_CPU_adopted=identity(ROOT / 'parallel_fit115/CPU_completion.json'),
        task='First source/within-window weighted ranking and fixed-query-position variance; no threshold selection',
        no_model_training_or_confirmation_or_production=True, code=identity(ROOT / 'code/parallel_discrimination116.py')))
    statistics = {}
    for name, outputs in [('initial', lock['initial_outputs']), ('final', final)]:
        margins = []
        for case in cases:
            raw = read(check(read(check(outputs[case['case']]))['raw']))
            logits = np.array(raw['binary_logits'], dtype=np.float64)
            if logits.shape != (32, 2) or not np.isfinite(logits).all():
                raise ValueError('Accepted complete original binary logits missing')
            margins.append(logits[:, 0] - logits[:, 1])
        statistics[name] = describe(np.stack(margins), a, b)
    save(OUT / 'completion.json', dict(state='FIRST_FIXED_FIT_NATIVE_DISCRIMINATION_DIAGNOSIS_COMPLETE',
        source=sid, statistics=statistics, actual_native_F1_and_loss_adopted=identity(ROOT / 'parallel_fit115/CPU_completion.json'),
        no_old_QA_or_F1_repeated=True, no_reference_defined_cutoff_or_checkpoint_choice=True,
        summary_omissions_semantically_UNKNOWN=True, no_new_model_calls_or_training=True,
        old105_STOP_unchanged=True, confirmation_sources_read=0, no_quality_or_production_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_successes=True))
        raise
