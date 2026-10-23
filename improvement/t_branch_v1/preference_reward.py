"""Human-summary agreement and explicit HL/NHL are different supervision tasks."""
from dataclasses import dataclass
import math

import numpy as np

from native_sets import bool_mask, replace_component, union_components


class Unscorable(ValueError):
    pass


@dataclass(frozen=True)
class SummaryReview:
    reviewer: str
    selected: np.ndarray
    observed_task_domain: np.ndarray


def overlap_metrics(prediction, reference, observed):
    size = len(observed)
    observed = bool_mask(observed, size)
    prediction = bool_mask(prediction, size) & observed
    reference = bool_mask(reference, size) & observed
    if not observed.any():
        raise Unscorable('No observed evaluation domain; not a zero-quality result')
    proposed, positive = int(prediction.sum()), int(reference.sum())
    matched = int(np.count_nonzero(prediction & reference))
    return dict(precision=matched / proposed if proposed else 0.0,
                recall=matched / positive if positive else 0.0,
                f1=2 * matched / (proposed + positive) if proposed + positive else 0.0,
                matched=matched, proposed=proposed, reference=positive,
                observed_frames=int(observed.sum()), zero_division_convention=0)


def summary_agreement(prediction, reviews, expected_reviewers):
    if len(reviews) != expected_reviewers or expected_reviewers <= 0:
        raise ValueError('All original review rows are required')
    if len({row.reviewer for row in reviews}) != len(reviews):
        raise ValueError('Duplicate reviewer is not an independent reference')
    metrics = [overlap_metrics(prediction, row.selected, row.observed_task_domain) for row in reviews]
    return dict(mean_f1=math.fsum(row['f1'] for row in metrics) / expected_reviewers,
                mean_precision=math.fsum(row['precision'] for row in metrics) / expected_reviewers,
                mean_recall=math.fsum(row['recall'] for row in metrics) / expected_reviewers,
                reviewers=expected_reviewers, per_review=metrics,
                task='Human-summary preference agreement, not generic semantic HL/NHL',
                unselected_summary_semantic_label='UNKNOWN')


def source_marginal_gain(components, window, candidate, allowed, reviews, expected_reviewers):
    anchor = union_components(components, len(allowed))
    changed = replace_component(components, window, candidate, allowed)
    before = summary_agreement(anchor, reviews, expected_reviewers)
    after = summary_agreement(changed, reviews, expected_reviewers)
    return dict(delta_f1=after['mean_f1'] - before['mean_f1'], anchor=before, candidate=after,
                changed_native_frames=int(np.count_nonzero(anchor != changed)),
                scope='Complete source after one provenance-preserving window replacement')


def explicit_highlight_metrics(prediction, labels, annotation_task):
    if annotation_task != 'EXPLICIT_HL_NHL_UNKNOWN':
        raise ValueError('Summary/query/replay labels cannot silently become semantic negatives')
    labels = np.asarray(labels)
    if labels.ndim != 1 or labels.dtype.kind not in 'iu' or not np.isin(labels, [-1, 0, 1]).all():
        raise ValueError('Original HL/NHL/UNKNOWN label schema differs')
    observed = labels != -1
    result = overlap_metrics(prediction, labels == 1, observed)
    result.update(task=annotation_task, unknown_frames=int(np.count_nonzero(~observed)),
                  predictions_on_UNKNOWN=int(np.count_nonzero(bool_mask(prediction, len(labels)) & ~observed)))
    return result
