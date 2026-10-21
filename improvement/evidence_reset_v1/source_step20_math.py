"""A single exact source-risk chain-rule step; no model imports at import time."""
import math


def combine_jacobians(np, gradients, coefficients):
    """Float64 sum, without per-window/per-source gradient normalization."""
    if not gradients or len(gradients) != len(coefficients):
        raise ValueError('Complete same-theta branches required')
    keys = set(gradients[0])
    result = {k: np.zeros_like(v, dtype=np.float64) for k, v in gradients[0].items()}
    for row, coefficient in zip(gradients, coefficients):
        if set(row) != keys or not math.isfinite(float(coefficient)):
            raise ValueError('Finite complete Jacobian required')
        for key, value in row.items():
            if value.shape != result[key].shape or not np.isfinite(value).all():
                raise ValueError('Jacobian geometry/nonfinite')
            result[key] += float(coefficient) * value.astype(np.float64)
    return result


def fixed_step(np, initial, gradient, relative_norm=1e-4):
    if relative_norm != 1e-4 or set(initial) != set(gradient):
        raise ValueError('Single preregistered global normalized ascent step only')
    norm = math.sqrt(sum(float(np.sum(v.astype(np.float64) ** 2)) for v in initial.values()))
    gnorm = math.sqrt(sum(float(np.sum(v.astype(np.float64) ** 2)) for v in gradient.values()))
    if not math.isfinite(norm + gnorm) or not norm > 0 or not gnorm > 0:
        raise ValueError('Finite nonzero complete gradient/initial weights')
    rate = relative_norm * norm / gnorm
    final = {k: (initial[k].astype(np.float64) + rate * gradient[k]).astype(np.float32) for k in initial}
    if any(not np.isfinite(v).all() for v in final.values()):
        raise ValueError('Nonfinite updated parameter')
    prediction = sum(float(np.sum(gradient[k] * (final[k].astype(np.float64) - initial[k]))) for k in final)
    if not prediction > 0:
        raise ValueError('Rounded actual update is not an ascent direction')
    return final, dict(initial_norm=norm, gradient_norm=gnorm, effective_learning_rate=rate,
                       relative_step_norm=relative_norm, predicted_first_order_gain=prediction)
