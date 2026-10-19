"""Fixed low-capacity, source-balanced RELATIVE-IoU research alternative.

The supervised coefficients number40, versus393537 in the stopped MLP.
PCA is train-only and unsupervised; it is never fit to screen or confirm.
This does not retune the stopped MLP's confidence rule or checkpoint.
"""
from __future__ import annotations
import numpy as np
import torch
from crop_geometry import require
from roi_pool import FEATURE_DIM,VISUAL_DIM

PCA_DIM=32
RIDGE_LAMBDA=.01
SEED=20261018
ARMS=('RELATIVE_ROI','RELATIVE_GEOMETRY_CONTROL')


def checked(row):
    x=row['features'];y=np.asarray(row['targets'],np.float64)
    require(isinstance(x,np.ndarray) and x.dtype==np.float32 and x.ndim==2
            and x.shape[1]==FEATURE_DIM and x.shape[0]>0 and y.shape==(len(x),)
            and np.isfinite(x).all() and np.isfinite(y).all() and ((y>=0)&(y<=1)).all(),
            'Finite aligned original candidate features/true-IoUs required')
    return x,y


def fit_projection(sources,train_ids,normalization,synthetic=False):
    ids=list(train_ids)
    require(len(ids)==len(set(ids)) and (synthetic or len(ids)==482),'Registered unique482 training sources')
    require(set(normalization)=={'mean','std'},'Adopt train-only normalization, no refit to eval')
    mean,std=normalization['mean'],normalization['std']
    require(mean.shape==std.shape==(FEATURE_DIM,) and np.isfinite(mean).all()
            and np.isfinite(std).all() and (std>=np.float32(1e-4)).all(),'Valid frozen train normalization')
    arrays=[];weights=[];loss_weights=[];rows=[];offset=0
    for sid in ids:
        x,_=checked(sources[sid]);z=((x-mean)/std).astype(np.float32)
        require(len(x)>1,'A baseline plus actual alternative candidates required')
        arrays.append(z);weights.extend([1/(len(ids)*len(x))]*len(x));rows.append((sid,offset,offset+len(x)));offset+=len(x)
        loss_weights.extend([0.]+[1/(len(ids)*(len(x)-1))]*(len(x)-1))
    x=np.concatenate(arrays);w=np.asarray(weights,np.float64)
    require(abs(float(w.sum())-1)<1e-12 and min(x.shape[0],VISUAL_DIM)>PCA_DIM,'Complete source weights/PCA denominator')
    # Retain within-source candidate variation, not primarily source identity.
    centered=x[:,:VISUAL_DIM].copy()
    for _,start,end in rows:
        centered[start:end]-=centered[start:end].mean(axis=0,dtype=np.float64).astype(np.float32)
    weighted=centered*np.sqrt(w).astype(np.float32)[:,None]
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(SEED)
        _,singular,components=torch.pca_lowrank(torch.from_numpy(weighted),q=PCA_DIM,center=False,niter=2)
    projection=components.numpy().astype(np.float32)
    require(projection.shape==(VISUAL_DIM,PCA_DIM) and np.isfinite(projection).all()
            and np.allclose(projection.T@projection,np.eye(PCA_DIM),atol=2e-5),'Actual orthonormal train-only PCA')
    # Match query-time per-source GEMM shape instead of switching between one
    # giant batched product and per-image products after the checkpoint.
    raw=np.concatenate([np.concatenate((x[start:end,:VISUAL_DIM]@projection,x[start:end,VISUAL_DIM:]),axis=1)
                        for _,start,end in rows],axis=0).astype(np.float64)
    delta=raw.copy();target=[]
    for sid,start,end in rows:
        delta[start:end]-=raw[start]
        _,y=checked(sources[sid]);target.extend((y-y[0]).tolist())
    wloss=np.asarray(loss_weights,np.float64)
    require(abs(float(wloss.sum())-1)<1e-12,'Source-equal nonbaseline loss weights')
    scale=np.maximum(np.sqrt(np.sum(wloss[:,None]*delta**2,axis=0)),1e-4)
    normalized=delta/scale
    require(np.isfinite(normalized).all() and normalized.shape==(len(x),40),'Finite40 relative input dimensions')
    state=dict(mean=mean.copy(),std=std.copy(),PCA=projection,relative_scale=scale,
               PCA_singular_values=singular.numpy().astype(np.float32),train_ids=ids)
    return state,normalized,np.asarray(target,np.float64),wloss,rows


def fit_coefficients(relative_features,target,weights,arm):
    require(arm in ARMS and relative_features.ndim==2 and relative_features.shape[1]==40
            and target.shape==weights.shape==(len(relative_features),)
            and all(np.isfinite(a).all() for a in (relative_features,target,weights))
            and (weights>=0).all() and abs(float(weights.sum())-1)<1e-10,'Source-balanced complete ridge inputs')
    x=np.array(relative_features,dtype=np.float64,copy=True)
    if arm=='RELATIVE_GEOMETRY_CONTROL':x[:,:PCA_DIM]=0
    gram=x.T@(weights[:,None]*x)+RIDGE_LAMBDA*np.eye(40)
    beta=np.linalg.solve(gram,x.T@(weights*target))
    require(beta.shape==(40,) and np.isfinite(beta).all(),'Finite fixed40 supervised coefficients')
    prediction=x@beta
    return beta,dict(arm=arm,lambda_value=RIDGE_LAMBDA,supervised_coefficients=40,intercept=False,
         source_equal_relative_IoU_MSE=float(np.sum(weights*(prediction-target)**2)),
         penalized_objective=float(np.sum(weights*(prediction-target)**2)+RIDGE_LAMBDA*np.sum(beta**2)),
         optimizer_updates=0,closed_form_solves=1,PCA_dimensions=PCA_DIM,PCA_seed=SEED,PCA_power_iterations=2,
         geometry_control_visual_zero_after_projection=True)


def predict(state,beta,features,arm):
    require(arm in ARMS and features.dtype==np.float32 and features.ndim==2 and features.shape[1]==FEATURE_DIM
            and np.isfinite(features).all() and beta.shape==(40,),'Complete frozen candidate query')
    x=((features-state['mean'])/state['std']).astype(np.float32)
    raw=np.concatenate((x[:,:VISUAL_DIM]@state['PCA'],x[:,VISUAL_DIM:]),axis=1).astype(np.float64)
    value=(raw-raw[0])/state['relative_scale']
    if arm=='RELATIVE_GEOMETRY_CONTROL':value[:,:PCA_DIM]=0
    result=value@beta
    require(result.shape==(len(features),) and np.isfinite(result).all() and result[0]==0.,'Baseline-anchored finite relative scores')
    return result


def choose(scores):
    require(scores.ndim==1 and len(scores)>0 and np.isfinite(scores).all() and scores[0]==0.,'Explicit exactzero original baseline')
    best=int(np.argmax(scores))
    return best if scores[best]>0. else 0
