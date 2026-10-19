"""Pre-projection regression recovery, preserving legal frozen84 geometry."""
from __future__ import annotations
import copy
import direct_box_math_recovery_v93 as frozen93
from direct_box_math_v84 import (HEAD_PARAMETERS,BASE,LORA,PHYSICAL,PIPELINE,DECODER,
    dimensions,target_xywh,decode_numpy,decode_torch,decode_native,blend_native,
    legal_native,crop_iou,nearest_half_down)
from direct_box_math_recovery_v93 import normalize_hidden

RECIPE=copy.deepcopy(frozen93.RECIPE)
RECIPE.update(updates=778,source_draws=3112,new_training_forwards=3112,initial_step=0,final_step=778,
    pilot_updates=4,remaining_updates=774,source_weight='3112/(602*REMAINING_SOURCE_DRAW_COUNT)',
    head_init='EXACT_ADOPTED93_SUCCESSFUL_STEP19_NONZERO_WEIGHT_AND_BIAS',
    trainables_initialization='EXACT93_STEP19_ALL288_ADAPTER_AND_HEAD2',
    rng_initialization='EXACT93_STEP19_TORCH_CUDA_NUMPY_PYTHON',
    original_schedule_slice=[88,3200],skipped_successful_original_micro=list(range(88)),
    inherited_successful_updates=20,total_adopted_plus_new_updates=798,
    inherited_failed93_kept=True,decoder_and_loss='FROZEN84_LEGAL_DECODER_GIOU_PLUS_PRECLAMP_SMOOTH_L1',
    loss='SOURCE_EQUAL_DRAW_WEIGHT_TIMES_SMOOTH_L1_PRECLAMP_NORMALIZED_XYW_BETA_POINT1_PLUS_LEGAL_ONE_MINUS_GIOU',
    regression_coordinates='AFFINE_PRECLAMP_XYW_WITH_RAW_WIDTH',remaining_zero_finite_gradient='RECORD_NOT_FAILURE')


def preclamp_xyw(raw_z,width,height):
    import torch
    W,H=dimensions(width,height)
    frozen93.frozen84.require(isinstance(raw_z,torch.Tensor) and raw_z.ndim>=1 and raw_z.shape[-1]==3
        and raw_z.dtype in (torch.float32,torch.float64) and bool(torch.isfinite(raw_z).all()),'Finite differentiable F32/F64 raw head3')
    width_raw=min(float(W),16.*H/9.)+raw_z[...,2]*W
    x=(W-width_raw)/2.+raw_z[...,0]*W
    y=(H-9.*width_raw/16.)/2.+raw_z[...,1]*H
    return torch.stack((x,y,width_raw),dim=-1)


def loss(raw_z,reference_xywh,width,height):
    """Original GT is unchanged; draw/source weight remains caller-owned."""
    import torch
    import torch.nn.functional as F
    W,H=dimensions(width,height);reference=target_xywh(reference_xywh,W,H)
    pre=preclamp_xyw(raw_z,W,H)
    target=torch.as_tensor(reference[:3],dtype=raw_z.dtype,device=raw_z.device)
    normalizer=torch.tensor([W,H,W],dtype=raw_z.dtype,device=raw_z.device)
    regression=F.smooth_l1_loss(pre/normalizer,target.expand_as(pre)/normalizer,beta=.1,reduction='mean')
    _,legal_parts=frozen93.frozen84.loss(raw_z,reference_xywh,W,H)
    geometric=legal_parts['giou_loss'];total=regression+geometric
    frozen93.frozen84.require(bool(torch.isfinite(total)),'Finite preclamp regression plus legal GIoU')
    return total,dict(smooth_l1=regression,giou_loss=geometric,giou=legal_parts['giou'],total=total)
