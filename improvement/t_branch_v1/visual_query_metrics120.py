"""First whole fitting-source native action/ranking metrics, never production gates."""
import numpy as np

from event_full79 import independent_set_metrics
from parallel_discrimination116 import describe
from preference_reward import SummaryReview, summary_agreement
from t_io import ROOT, check, identity, read, save


def frozen_masks(source, outputs, inputs, folder):
    masks = {key: np.zeros(len(source.timeline.points), dtype=bool) for key in ['correct', 'local_shift16_alias']}
    margins = []; before = np.zeros(len(source.timeline.points), dtype=bool)
    old = read(ROOT / 'parallel_fit115/source_input_lock.json')['initial_outputs']
    for case in source.cases:
        row = read(check(outputs[case.name]['output'])); raw = read(check(row['raw']))
        binary = np.array(raw['binary_logits'], dtype=np.float64)
        margins.append(binary[:, 0] - binary[:, 1])
        selected = np.array(row['selected_cells'], dtype=bool)
        cells = read(check(inputs['inputs'][case.name]))['source_native_cells']
        for key, choices in [('correct', selected), ('local_shift16_alias', np.roll(selected, -16))]:
            for chosen, (first, last) in zip(choices, cells):
                if chosen:
                    masks[key][first:last] = True
        before |= source.selection(case, read(check(old[case.name])))
    path = folder / 'frozen_fit_masks_before_labels.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, **masks)
    return masks, np.stack(margins), before, identity(path)


def label_reference(source):
    inventory = read(ROOT / 'native_action_feasibility97/completion.json')
    row = next(item for item in inventory['sources'] if item['source']['sid'] == source.sid)
    reference = read(check(row['original_reference']))
    with np.load(check(reference['tensor']), allow_pickle=False) as data:
        selected, domain = data['summary_selected'].copy(), data['summary_task_domain'].copy()
    source.reviews = [SummaryReview(name, mask, domain) for name, mask in
                      zip(reference['all_original_reviewers'], selected)]
    with np.load(check(row['native_cells']), allow_pickle=False) as data:
        positive = data['summary_action_positive_coefficient'].copy()
        negative = data['summary_action_negative_coefficient'].copy()
    return positive, negative


def evaluate(source, outputs, inputs, folder):
    masks, margins, initial, binding = frozen_masks(source, outputs, inputs, folder)
    positive, negative = label_reference(source)
    original = read(ROOT / 'parallel_fit115/CPU_completion.json')['metrics']['initial']
    metrics = {}; known = {initial.tobytes(): original['mean_summary_F1']}
    first_metric, first_independent = [], []
    for name, mask in masks.items():
        key = mask.tobytes()
        if key not in known:
            known[key] = summary_agreement(mask, source.reviews, len(source.reviews))['mean_f1']
            first_metric.append(name)
            other = independent_set_metrics(mask, source.reviews, len(source.reviews))
            if abs(other - known[key]) > 1e-12:
                raise ValueError('First complete fit-source/all-original-reviewer F1 differs')
            first_independent.append(name)
        metrics[name] = dict(mean_summary_F1=known[key], selected_native_frames=int(mask.sum()),
                             selected_fraction=float(mask.mean()))
    ranking = dict(correct=describe(margins, positive, negative),
                   local_shift16_alias=describe(np.roll(margins, -16, axis=1), positive, negative))
    correct = ranking['correct']['source_summary_task_weighted_AUC']
    wrong = ranking['local_shift16_alias']['source_summary_task_weighted_AUC']
    return dict(metrics=metrics, ranking=ranking, initial_parallel_codec_control_metric_adopted=original,
        frozen_before_labels=binding, first_native_metrics=first_metric,
        first_independent_set_metrics=first_independent, all_original_reviewers=len(source.reviews),
        prospective_training_information_signal=bool(correct > .5 and correct > wrong),
        source_not_allNo_for_untrained_candidate=bool(masks['correct'].any()),
        counterfactual_is_deterministic_alias_not_extra_model=True, fitting_only_not_quality=True,
        no_complete40_48_or_confirmation_or_official_score_claim=True)
