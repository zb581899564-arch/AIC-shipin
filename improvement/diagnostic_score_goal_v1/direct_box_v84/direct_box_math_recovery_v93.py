"""Explicit numerical recovery; frozen84 native geometry/loss stay unchanged."""
from __future__ import annotations
import copy
import direct_box_math_v84 as frozen84
from direct_box_math_v84 import (HEAD_PARAMETERS,BASE,LORA,PHYSICAL,PIPELINE,DECODER,
    dimensions,target_xywh,decode_numpy,decode_torch,decode_native,blend_native,
    legal_native,crop_iou,nearest_half_down,loss)

RECIPE=copy.deepcopy(frozen84.RECIPE)
RECIPE.update(updates=798,source_draws=3192,new_training_forwards=3192,initial_step=0,final_step=798,
    pilot_updates=4,remaining_updates=794,source_weight='3192/(602*REMAINING_SOURCE_DRAW_COUNT)',
    head_init='EXACT_ADOPTED84_SUCCESSFUL_STEP1_NONZERO_WEIGHT_AND_BIAS',
    hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',optimizer_initialization='RESET_BOTH_ADAM_GROUPS_EMPTY',
    trainables_initialization='EXACT84_STEP1_ALL288_ADAPTER_AND_HEAD2',
    rng_initialization='EXACT84_STEP1_TORCH_CUDA_NUMPY_PYTHON',
    original_schedule_slice=[8,3200],skipped_successful_original_micro=list(range(8)),
    inherited_successful_updates=1,total_adopted_plus_new_updates=799,
    inherited_failed84_kept=True,decoder_and_loss='EXACT_FROZEN84_UNCHANGED')


def normalize_hidden(hidden):
    """F32 original hidden -> F32 L2 unit vector, preserving autograd."""
    import torch
    frozen84.require(isinstance(hidden,torch.Tensor) and tuple(hidden.shape)==(4096,)
        and bool(torch.isfinite(hidden).all()),'Finite actual source-only hidden4096')
    value=hidden.float();norm=torch.linalg.vector_norm(value,ord=2)
    frozen84.require(bool(torch.isfinite(norm)) and bool(norm>0),'Positive finite F32 hidden L2 norm; no epsilon repair')
    result=value/norm
    frozen84.require(result.dtype==torch.float32 and bool(torch.isfinite(result).all()),'Finite F32 normalized source hidden')
    return result
