"""SOURCE_ONLY_DIRECT_BOX_GRADIENT: pure fixed decoder/loss, no artifact IO.

Predictions always have implicit 16:9 height. Original human native XYWH is
never projected, stretched, clipped, or required to have an exact aspect ratio.
"""
from fractions import Fraction
import math
from numbers import Integral
import numpy as np

HEAD_PARAMETERS=3*4096+3
BASE=8767123696
LORA=7667712
PHYSICAL=8774803699
PIPELINE=8790237452
RECIPE=dict(updates=800,grad_accum=4,source_draws=3200,train_sources=602,rank=8,alpha=16,dropout=0.,
    lora_lr=5e-5,head_lr=.001,weight_decay=0.,adam_eps=1e-8,adam_betas=[.9,.999],grad_clip=1.,seed=20261018,
    head_bias=True,head_init='ALL_ZERO_WEIGHT_AND_BIAS',final_only=True,initial_step=0,final_step=800,
    pilot_updates=4,remaining_updates=796,source_weight='3200/(602*SOURCE_DRAW_COUNT)',
    loss='SOURCE_EQUAL_DRAW_WEIGHT_TIMES_SMOOTH_L1_NORMALIZED_XYW_BETA_POINT1_PLUS_ONE_MINUS_GIOU',
    smooth_l1_beta=.1,smooth_l1_weight=1.,giou_weight=1.,new_training_forwards=3200,
    adapter_name='direct_box',original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,
    output_arms=['DIRECT','ANCHORED_HALF'],anchored_direct_weight=.5)
DECODER=dict(raw_order=['dx/W','dy/H','dw/W'],continuous_width_cap='min(W,16*H/9)',
    native_width_cap='min(W,floor(16*H/9))',rounding='NEAREST_HALF_DOWN_THEN_LEGAL_CLAMP',
    zero_head='GEOMETRIC_MAX_CENTER_NOT_OBSERVED_B0',prediction_ratio=[16,9],GT_modified=False)


def require(value,message):
    if not value:raise ValueError(message)


def dimensions(width,height):
    require(isinstance(width,Integral) and not isinstance(width,bool) and isinstance(height,Integral)
        and not isinstance(height,bool) and width>0 and height>0,'Positive original integer source dimensions')
    return int(width),int(height)


def target_xywh(reference,width,height):
    W,H=dimensions(width,height);a=np.asarray(reference,dtype=np.float64)
    require(a.shape==(4,) and bool(np.isfinite(a).all()),'Original finite native XYWH4 required')
    x,y,w,h=map(float,a)
    x_ulp=math.ulp(x)+math.ulp(w)+math.ulp(float(W))
    y_ulp=math.ulp(y)+math.ulp(h)+math.ulp(float(H))
    require(x>=0 and y>=0 and w>0 and h>0 and x+w-W<=x_ulp and y+h-H<=y_ulp,
        'Original human target must be legal; never clip/repair/project it')
    return a.copy()


def decode_numpy(raw_z,width,height):
    W,H=dimensions(width,height);z=np.asarray(raw_z,dtype=np.float64)
    require(z.shape==(3,) and bool(np.isfinite(z).all()),'Finite CPU raw head3')
    maximum=min(float(W),16.*H/9.)
    w=min(maximum,max(1.,maximum+float(z[2])*W));h=9.*w/16.
    x=min(float(W)-w,max(0.,(W-w)/2.+float(z[0])*W))
    y=min(float(H)-h,max(0.,(H-h)/2.+float(z[1])*H))
    return np.asarray([x,y,w],dtype=np.float64)


def nearest_half_down(value):
    require(math.isfinite(float(value)),'Finite coordinate to round')
    fraction=Fraction(str(float(value)));floor,remainder=divmod(fraction.numerator,fraction.denominator)
    return floor+int(2*remainder>fraction.denominator)


def legal_native(box,width,height):
    W,H=dimensions(width,height)
    return (isinstance(box,(list,tuple)) and len(box)==3
        and all(isinstance(v,Integral) and not isinstance(v,bool) for v in box)
        and box[0]>=0 and box[1]>=0 and box[2]>0 and box[0]+box[2]<=W and 16*box[1]+9*box[2]<=16*H)


def decode_native(raw_z,width,height):
    W,H=dimensions(width,height);x,y,w=decode_numpy(raw_z,W,H)
    iw=min(min(W,16*H//9),max(1,nearest_half_down(w)))
    ix=min(W-iw,max(0,nearest_half_down(x)))
    iy=min((16*H-9*iw)//16,max(0,nearest_half_down(y)))
    result=[ix,iy,iw];require(legal_native(result,W,H),'Independent integer decoder legality failed')
    return result


def blend_native(base_xyw,direct_xyw,width,height):
    """Pre-registered 1/2 baseline + 1/2 direct integer-coordinate arm."""
    W,H=dimensions(width,height)
    require(legal_native(base_xyw,W,H) and legal_native(direct_xyw,W,H),'Both original BASE and DIRECT must already be legal')
    x,y,w=[nearest_half_down((int(a)+int(b))/2.) for a,b in zip(base_xyw,direct_xyw)]
    w=min(min(W,16*H//9),max(1,w));x=min(W-w,max(0,x));y=min((16*H-9*w)//16,max(0,y))
    result=[x,y,w];require(legal_native(result,W,H),'Independent anchored-half legality')
    return result


def decode_torch(raw_z,width,height):
    """raw[...,3] -> continuous native xyw[...,3], preserving its gradient."""
    import torch
    W,H=dimensions(width,height)
    require(isinstance(raw_z,torch.Tensor) and raw_z.ndim>=1 and raw_z.shape[-1]==3
        and raw_z.dtype in (torch.float32,torch.float64) and bool(torch.isfinite(raw_z).all()),'Finite differentiable F32/F64 raw head3')
    cap=min(float(W),16.*H/9.);w=torch.clamp(cap+raw_z[...,2]*W,min=1.,max=cap);h=w*(9./16.)
    x=torch.minimum(torch.clamp((W-w)/2.+raw_z[...,0]*W,min=0.),W-w)
    y=torch.minimum(torch.clamp((H-h)/2.+raw_z[...,1]*H,min=0.),H-h)
    return torch.stack((x,y,w),dim=-1)


def loss(raw_z,reference_xywh,width,height):
    """Return (unweighted scalar, differentiable scalar components).

    Draw/source-equal weight is multiplied by GPU caller after this function.
    Reference is the original native XYWH4; never infer it from IoU/candidates.
    """
    import torch
    import torch.nn.functional as F
    W,H=dimensions(width,height)
    reference=target_xywh(reference_xywh,W,H)
    pred=decode_torch(raw_z,W,H)
    target=torch.as_tensor(reference,dtype=raw_z.dtype,device=raw_z.device)
    normalizer=torch.tensor([W,H,W],dtype=raw_z.dtype,device=raw_z.device)
    regression=F.smooth_l1_loss(pred/normalizer,target[:3].expand_as(pred)/normalizer,beta=.1,reduction='mean')
    px,py,pw=pred.unbind(-1);ph=pw*(9./16.);tx,ty,tw,th=target.unbind(-1)
    inter_w=torch.clamp(torch.minimum(px+pw,tx+tw)-torch.maximum(px,tx),min=0.)
    inter_h=torch.clamp(torch.minimum(py+ph,ty+th)-torch.maximum(py,ty),min=0.)
    intersection=inter_w*inter_h;union=pw*ph+tw*th-intersection
    enclosure=(torch.maximum(px+pw,tx+tw)-torch.minimum(px,tx))*(torch.maximum(py+ph,ty+th)-torch.minimum(py,ty))
    giou=intersection/union-(enclosure-union)/enclosure
    giou_mean=giou.mean();geometric=1.-giou_mean;total=regression+geometric
    require(bool(torch.isfinite(total)),'Finite direct-box loss')
    return total,dict(smooth_l1=regression,giou_loss=geometric,giou=giou_mean,total=total)


def crop_iou(box,reference,width,height):
    require(legal_native(box,width,height),'Only independent legal native predictions may be evaluated')
    x,y,w=map(float,box);h=9.*w/16.;u,v,rw,rh=target_xywh(reference,width,height)
    intersection=max(0.,min(x+w,u+rw)-max(x,u))*max(0.,min(y+h,v+rh)-max(y,v))
    return intersection/(w*h+rw*rh-intersection)
