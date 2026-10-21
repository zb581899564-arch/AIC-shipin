"""Exact finite program scan for a witness-threshold latent margin, CPU only."""
from fractions import Fraction
import math
import time
import numpy as np


def exact_utility(p, tp, gt):
    assert p >= 0 and all(0 <= int(t) <= min(p, int(g)) for t, g in zip(tp, gt))
    return sum((Fraction(2 * int(t), p + int(g)) if p + int(g) else Fraction(1)
                for t, g in zip(tp, gt)), Fraction()) / len(gt)


def scan(lengths, tps, gt, scores, witness, baseline, overlaps,
         chunk=32768, maximum_programs=20000000, maximum_exact_keys=50000,
         deadline=math.inf):
    """Enumerate all native programs; max-gold is not the fixed witness score.

    All input scores are stored finite dyadics. Their common integer scale must
    fit an exact float64 sum; otherwise this implementation reports failure.
    Near-threshold utility and near-max augmented scores use exact fractions.
    """
    gt = np.asarray(gt, dtype=np.int64)
    lengths = [np.asarray(a, dtype=np.int64) for a in lengths]
    tps = [np.asarray(a, dtype=np.int64) for a in tps]
    overlaps = [np.asarray(a, dtype=np.int64) for a in overlaps]
    radices = [len(a) for a in lengths]
    total = math.prod(radices)
    assert 0 < total <= maximum_programs and len(gt) > 0
    assert len(lengths) == len(scores) == len(witness) == len(baseline) == len(overlaps)
    assert all(a.shape == (len(b), len(gt)) for a, b in zip(tps, lengths))
    assert all((a >= 0).all() for a in lengths) and (gt >= 0).all()
    ratios = [[float(v).as_integer_ratio() for v in a] for a in scores]
    denominator = max(d for a in ratios for _, d in a)
    score_units = [np.asarray([n * (denominator // d) for n, d in a], dtype=np.int64) for a in ratios]
    assert all(denominator % d == 0 for a in ratios for _, d in a)
    assert sum(max(abs(int(v)) for v in a) for a in score_units) < 2**52, 'Exact dyadic sum scope exceeded'
    assert all(len(a) == len(b) for a, b in zip(score_units, lengths))
    wp = sum(int(a[j]) for a, j in zip(lengths, witness))
    wtp = sum((a[j] for a, j in zip(tps, witness)), start=np.zeros(len(gt), dtype=np.int64))
    threshold = exact_utility(wp, wtp, gt)
    base_p = sum(int(a[j]) for a, j in zip(lengths, baseline))
    u_radius = 8 * np.finfo(float).eps * (len(gt) + 5)
    aug_radius = u_radius * (1 + sum(max(abs(float(v)) for v in a) for a in scores))
    utility_cache = {}
    best_map = best_gold = best_aug = None
    gold_count = 0

    def decode(index):
        choices = [0] * len(radices)
        for j in range(len(radices) - 1, -1, -1):
            choices[j] = index % radices[j]
            index //= radices[j]
        assert index == 0
        return choices

    def exact(p, tp):
        key = (int(p), tuple(map(int, tp)))
        if key not in utility_cache:
            assert len(utility_cache) < maximum_exact_keys, 'Exact comparison budget exceeded; no guessed gold'
            utility_cache[key] = exact_utility(key[0], key[1], gt)
        return utility_cache[key]

    for begin in range(0, total, chunk):
        assert time.monotonic() < deadline, 'CPU budget exceeded; no approximate fallback'
        ids = np.arange(begin, min(total, begin + chunk), dtype=np.int64)
        remainder = ids.copy()
        choices = [None] * len(radices)
        for j in range(len(radices) - 1, -1, -1):
            choices[j] = remainder % radices[j]
            remainder //= radices[j]
        p = np.zeros(len(ids), dtype=np.int64)
        tp = np.zeros((len(ids), len(gt)), dtype=np.int64)
        score = np.zeros(len(ids), dtype=np.int64)
        keep = np.zeros(len(ids), dtype=np.int64)
        for j, cc in enumerate(choices):
            p += lengths[j][cc]
            tp += tps[j][cc]
            score += score_units[j][cc]
            keep += overlaps[j][cc]
        assert (tp >= 0).all() and (tp <= gt).all() and (tp <= p[:, None]).all()
        den = p[:, None] + gt
        u = np.divide(2. * tp, den, out=np.ones_like(tp, dtype=float), where=den != 0).mean(axis=1)
        gold = u > float(threshold) + u_radius
        for i in np.flatnonzero(np.abs(u - float(threshold)) <= u_radius):
            gold[i] = exact(p[i], tp[i]) >= threshold
        gold_count += int(gold.sum())

        def tie(i):
            return (-int(p[i] + base_p - 2 * keep[i]), int(keep[i]), -int(ids[i]))

        def pick(mask, current):
            if not np.any(mask):
                return current
            value = score[mask].max()
            ii = np.flatnonzero(mask & (score == value))
            i = max(map(int, ii), key=tie)
            record = (int(value), *tie(i), int(ids[i]))
            return record if current is None or record[:4] > current[:4] else current

        best_map = pick(np.ones(len(ids), bool), best_map)
        best_gold = pick(gold, best_gold)
        approximate_aug = score / denominator + np.maximum(0., float(threshold) - u)
        local_max = float(approximate_aug.max())
        if best_aug is not None and local_max + 2 * aug_radius < float(best_aug[0]):
            continue
        for i in np.flatnonzero(approximate_aug >= local_max - 2 * aug_radius):
            value = Fraction(int(score[i]), denominator) + max(Fraction(), threshold - exact(p[i], tp[i]))
            record = (value, *tie(int(i)), int(ids[i]))
            if best_aug is None or record[:4] > best_aug[:4]:
                best_aug = record
    assert best_map is not None and best_gold is not None and best_aug is not None
    loss = best_aug[0] - Fraction(best_gold[0], denominator)
    assert loss >= 0

    def describe(record):
        cc = decode(record[-1])
        p = sum(int(a[j]) for a, j in zip(lengths, cc))
        tp = sum((a[j] for a, j in zip(tps, cc)), start=np.zeros(len(gt), dtype=np.int64))
        s = sum(int(a[j]) for a, j in zip(score_units, cc))
        return dict(choices=cc, P=p, TP=tp.tolist(), utility=float(exact_utility(p, tp, gt)),
                    utility_fraction=str(exact_utility(p, tp, gt)), score=float(Fraction(s, denominator)),
                    score_units=s, score_denominator=denominator, program_index=int(record[-1]))

    result = dict(programs=total, acceptable_programs=gold_count, threshold=float(threshold), threshold_fraction=str(threshold),
                  MAP=describe(best_map), highest_score_acceptable=describe(best_gold),
                  loss_augmented=describe(best_aug), loss=float(loss), loss_fraction=str(loss),
                  exact_utility_keys=len(utility_cache), comparison_radius_is_algorithmic_roundoff_guard=True,
                  near_utility_radius=u_radius, near_augmented_radius=aug_radius)
    regret = max(Fraction(), threshold - Fraction(result['MAP']['utility_fraction']))
    assert loss >= regret
    result['positive_MAP_regret'] = float(regret)
    return result
