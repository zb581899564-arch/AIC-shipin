"""Fixed full-fit local-information diagnostic, adopting all old metrics."""
import numpy as np

from event_full79 import independent_set_metrics
from parallel_discrimination116 import describe
from preference_reward import summary_agreement
from t_io import ROOT, check, read
from visual_query_metrics120 import frozen_masks, label_reference


def evaluate(source, outputs, inputs, folder, criteria):
    masks, margins, _, binding = frozen_masks(source, outputs, inputs, folder)
    positive, negative = label_reference(source)
    old = read(ROOT / 'visual_query_fit120/CPU_completion.json')
    old_masks = ROOT / 'visual_query_fit120/frozen_fit_masks_before_labels.npz'
    with np.load(old_masks, allow_pickle=False) as data:
        known = {data[key].tobytes(): row['mean_summary_F1'] for key, row in old['metrics'].items()}
    first = []; metrics = {}
    for name, mask in masks.items():
        key = mask.tobytes()
        if key not in known:
            known[key] = summary_agreement(mask, source.reviews, len(source.reviews))['mean_f1']
            if abs(known[key] - independent_set_metrics(mask, source.reviews, len(source.reviews))) > 1e-12:
                raise ValueError('New masked native/all-reviewer F1 differs from independent set arithmetic')
            first.append(name)
        metrics[name] = dict(mean_summary_F1=known[key], selected_native_frames=int(mask.sum()),
                            selected_fraction=float(mask.mean()))
    ranking = dict(correct=describe(margins, positive, negative),
        local_shift16_alias=describe(np.roll(margins, -16, axis=1), positive, negative))
    within = ranking['correct']['within_window_summary_task_weighted_AUC']
    wrong = ranking['local_shift16_alias']['within_window_summary_task_weighted_AUC']
    gain = metrics['correct']['mean_summary_F1'] - old['metrics']['correct']['mean_summary_F1']
    passed = (within is not None and wrong is not None and within >= criteria['within_window_AUC_at_least']
        and within - wrong >= criteria['within_window_AUC_gain_over_local_shift_at_least'] and gain > 0)
    return dict(metrics=metrics, ranking=ranking, frozen_before_labels=binding,
        first_native_metrics=first, original_unmasked120_metrics_adopted=old['metrics'],
        original_unmasked120_ranking_adopted=old['ranking'], native_F1_gain_over_unmasked120=gain,
        preregistered_local_information_gate=criteria, local_information_gate_pass=bool(passed),
        all_original_reviewers=len(source.reviews), fitting_only_not_quality=True,
        alias_not_additional_model_inference=True, summary_omissions_semantically_UNKNOWN=True,
        no_training_confirmation_or_production_admission=True)
