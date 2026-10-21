"""Lossless original+FP32-direction recipe; one fit-only computed correction."""
import hashlib
import json
import math
import numpy as np


def rate(loss, fit_directional_derivative):
    if not math.isfinite(loss+fit_directional_derivative) or loss<=0 or fit_directional_derivative<=0:
        raise ValueError('Positive finite fixed-fit plane and directional derivative required')
    return float(loss/fit_directional_derivative)


def state_digest(state):
    h=hashlib.sha256()
    for key in sorted(state):
        a=np.ascontiguousarray(state[key]);assert a.dtype==np.float32 and np.isfinite(a).all()
        h.update(key.encode());h.update(a.dtype.str.encode());h.update(json.dumps(list(a.shape),separators=(',',':')).encode());h.update(a.tobytes())
    return h.hexdigest()


def materialize(original,direction,alpha_hex):
    alpha=float.fromhex(alpha_hex)
    if not math.isfinite(alpha) or alpha<=0:raise ValueError('One finite positive precommitted scalar')
    canonical={k.replace('.policy.weight','.weight'):v for k,v in direction.items()}
    if len(canonical)!=len(direction) or set(canonical)!=set(original):raise ValueError('Exact PEFT tensor mapping')
    out={};delta2=[];theta2=[];rounding2=[];direction_delta=[]
    for key,old in original.items():
        g=canonical[key]
        if old.dtype!=np.float32 or g.dtype!=np.float32 or old.shape!=g.shape:raise ValueError('Exact FP32 geometry')
        # Separate multiply/add ufuncs explicitly fix the no-FMA CPU recipe.
        step=np.multiply(g.astype(np.float64),alpha,dtype=np.float64)
        candidate=np.add(old.astype(np.float64),step,dtype=np.float64).astype(np.float32)
        if not np.isfinite(candidate).all():raise ValueError('Candidate FP32 overflow; no smaller-dose retry')
        out[key]=candidate
        actual=candidate.astype(np.float64)-old.astype(np.float64)
        delta2.append(float(np.sum(actual*actual,dtype=np.float64)))
        theta2.append(float(np.sum(old.astype(np.float64)**2,dtype=np.float64)))
        rounding2.append(float(np.sum((actual-step)**2,dtype=np.float64)))
        direction_delta.append(float(np.sum(g.astype(np.float64)*actual,dtype=np.float64)))
    step_norm=math.sqrt(math.fsum(delta2));theta_norm=math.sqrt(math.fsum(theta2))
    if not step_norm>0 or not theta_norm>0:raise ValueError('Nonzero materialized update')
    return out,dict(alpha_hex=alpha_hex,alpha=alpha,initial_norm=theta_norm,actual_step_norm=step_norm,
        actual_relative_step_norm=step_norm/theta_norm,FP32_rounding_residual_norm=math.sqrt(math.fsum(rounding2)),
        stored_direction_dot_actual_step=math.fsum(direction_delta),canonical_FP32_state_sha256=state_digest(out))
