"""Gradient sufficient-statistic intervals and predeclared content diagnostic."""
import math
import numpy as np


def bounded_dot(a, b):
    assert set(a) == set(b)
    count = sum(np.asarray(v).size for v in a.values())
    values = []
    absolute = []
    for key in a:
        x = np.asarray(a[key], dtype=np.float64)
        y = np.asarray(b[key], dtype=np.float64)
        assert x.shape == y.shape and np.isfinite(x).all() and np.isfinite(y).all()
        product = x * y
        assert np.isfinite(product).all()
        values.append(float(np.sum(product, dtype=np.float64)))
        absolute.append(float(np.sum(np.abs(product), dtype=np.float64)))
    estimate = math.fsum(values)
    u = np.finfo(np.float64).eps / 2
    gamma = (2 * count + 4 * len(a)) * u / (1 - (2 * count + 4 * len(a)) * u)
    radius = gamma * math.fsum(absolute) / (1 - gamma) + 2 * math.ulp(estimate)
    assert math.isfinite(estimate) and math.isfinite(radius)
    return dict(value=estimate, radius=radius, lower=estimate-radius, upper=estimate+radius, elements=count)


def ratio(n, d):
    assert d[0] > 0
    values = [x/y for x in n for y in d]
    padding = 16*np.finfo(float).eps*max(1., *map(abs, values))
    return (min(values)-padding, max(values)+padding)


def product(a, b):
    vv = [x*y for x in a for y in b]
    padding = 16*np.finfo(float).eps*max(1., *map(abs, vv))
    return (min(vv)-padding, max(vv)+padding)


def content_metrics(stats):
    def interval(name):
        s=stats[name]
        return (s['lower'],s['upper'])
    r2,s2,d2 = (interval(k) for k in ['real_norm2','shifted_norm2','direction_norm2'])
    assert min(r2[0],s2[0],d2[0]) > 0, 'Zero or numerically ambiguous gradient norm'
    rd,sd,rs = (interval(k) for k in ['real_dot','shifted_dot','real_shifted_dot'])
    rn=(math.sqrt(r2[0]*d2[0]),math.sqrt(r2[1]*d2[1]))
    sn=(math.sqrt(s2[0]*d2[0]),math.sqrt(s2[1]*d2[1]))
    real_cos=ratio(rd,rn);shift_cos=ratio(sd,sn)
    scale=ratio(rs,s2)
    removed=product(scale,sd)
    residual_dot=(rd[0]-removed[1],rd[1]-removed[0])
    residual_normalized=ratio(residual_dot,rn)
    return dict(real_cosine=real_cos,shifted_cosine=shift_cos,
        cosine_difference=(real_cos[0]-shift_cos[1],real_cos[1]-shift_cos[0]),
        real_minus_shifted_dot=(rd[0]-sd[1],rd[1]-sd[0]),
        residual_dot=residual_dot,residual_projection_over_real_norm=residual_normalized,
        interpretation='Residual removes the component of real gradient along shifted gradient. Numeric intervals do not prove event semantics or generalization.')


def decide(rows, minimum_residual=0.01):
    assert len(rows)==3
    if any(r['stats'][k]['lower']<=0 for r in rows for k in ['real_norm2','shifted_norm2','direction_norm2']):
        return dict(status='STOP_ZERO_OR_NUMERICALLY_AMBIGUOUS_GRADIENT_NORM',
                    process_denominator=4,supported_process_sources=3,
                    automatic_update=False,production_admitted=False)
    metrics=[content_metrics(r['stats']) for r in rows]
    # Fourth pre-registered process source is forced B with zero derivative.
    real_lower=math.fsum(r['stats']['real_dot']['lower'] for r in rows)/4
    advantage_lower=math.fsum(m['real_minus_shifted_dot'][0] for m in metrics)/4
    residual_lower=math.fsum(m['residual_projection_over_real_norm'][0] for m in metrics)/4
    counts=dict(real_positive=sum(r['stats']['real_dot']['lower']>0 for r in rows),
        real_exceeds_shifted=sum(m['real_minus_shifted_dot'][0]>0 for m in metrics),
        scale_removed_projection_over_minimum=sum(m['residual_projection_over_real_norm'][0]>minimum_residual for m in metrics))
    conditions=dict(real_mean_positive=real_lower>0,at_least2_real_positive=counts['real_positive']>=2,
        real_mean_exceeds_shifted=advantage_lower>0,at_least2_real_exceed_shifted=counts['real_exceeds_shifted']>=2,
        scale_removed_mean_over_minimum=residual_lower>minimum_residual,
        at_least2_scale_removed_over_minimum=counts['scale_removed_projection_over_minimum']>=2)
    return dict(status='ELIGIBLE_FOR_SEPARATE_ONE_STEP_REVIEW_ONLY' if all(conditions.values()) else 'STOP_COUPLED_GRADIENT_TRANSFER_OR_SCALE_CONTROL',
        conditions=conditions,counts=counts,real_dot_macro_lower=real_lower,
        real_minus_shifted_macro_lower=advantage_lower,scale_removed_normalized_macro_lower=residual_lower,
        minimum_predeclared_residual=minimum_residual,process_denominator=4,supported_process_sources=3,
        metrics=metrics,automatic_update=False,production_admitted=False)
