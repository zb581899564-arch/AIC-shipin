"""Original SumMe mean pairwise frame F1, without author's length repair."""
import numpy as np


def mean_pairwise(selection, user_score):
    selection = np.asarray(selection, dtype=bool)
    reference = np.asarray(user_score) > 0
    if selection.ndim != 1 or reference.ndim != 2 or len(selection) != reference.shape[0]:
        raise ValueError('Native selection/annotation frame count mismatch; no padding or truncation')
    if not reference.shape[1] or not len(selection):
        raise ValueError('Empty annotation denominator')
    selected = int(selection.sum())
    positives = reference.sum(axis=0)
    if np.any(positives == 0):
        raise ValueError('Empty human summary requires explicit protocol treatment')
    intersections = (reference & selection[:, None]).sum(axis=0)
    recall = intersections / positives
    precision = intersections / selected if selected else np.zeros(reference.shape[1])
    f1 = 2 * intersections / (positives + selected)
    return dict(f1=float(f1.mean()), recall=float(recall.mean()), precision=float(precision.mean()),
                selected_frames=selected, selection_fraction=float(selection.mean()),
                summary_columns=reference.shape[1], user_f1=f1.tolist(),
                user_recall=recall.tolist(), user_precision=precision.tolist())


def paired_summary(baseline, candidate, seed=20261013):
    baseline = np.asarray(baseline, dtype=float)
    candidate = np.asarray(candidate, dtype=float)
    if baseline.shape != candidate.shape or baseline.ndim != 1 or not len(baseline):
        raise ValueError('Missing or unpaired source denominator')
    delta = candidate - baseline
    generator = np.random.default_rng(seed)
    bootstrap = delta[generator.integers(len(delta), size=(5000, len(delta)))].mean(axis=1)
    return dict(sources=len(delta), baseline_macro=float(baseline.mean()), candidate_macro=float(candidate.mean()),
                delta=float(delta.mean()), worst_source_delta=float(delta.min()),
                positive_sources=int((delta > 0).sum()), negative_sources=int((delta < 0).sum()),
                equal_sources=int((delta == 0).sum()),
                paired_bootstrap95=np.quantile(bootstrap, [.025, .975]).tolist(),
                diagnostic_risk_pass=bool(delta.mean() >= 0 and delta.min() >= -.01),
                bootstrap_is_not_official_score_proof=True)
