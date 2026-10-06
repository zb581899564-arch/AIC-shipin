"""Instance-local MPS backward workaround; no parameter or installed-library edits."""
import types
def deepstack_fp32(self,hidden_states,visual_pos_masks,visual_embeds):
    mask=visual_pos_masks.to(hidden_states.device)
    visual=visual_embeds.to(hidden_states.device,hidden_states.dtype).float()
    work=hidden_states.float()
    local=work[mask,:].clone()+visual
    work[mask,:]=local
    return work.to(hidden_states.dtype)

def install(model,torch):
    target=model.model.language_model
    assert target.__class__.__name__=='Qwen3VLTextModel'
    target._deepstack_process=types.MethodType(deepstack_fp32,target)
    model.model.get_placeholder_mask=types.MethodType(placeholder_mask,model.model)
    return dict(method='INSTANCE_LOCAL_FP32_INDEX_ADD_CAST_BACK',model_dtype=str(next(model.parameters()).dtype),
        reason='torch2.5.1 MPS IndexBackward index_put accumulate supports Float/Int/Bool only',parameters_added=0)

def placeholder_mask(self,input_ids,inputs_embeds,image_features=None,video_features=None):
    if input_ids is None:raise ValueError('registered training requires explicit input_ids')
    masks=[input_ids==self.config.image_token_id,input_ids==self.config.video_token_id]
    for kind,mask,features in zip(('image','video'),masks,(image_features,video_features)):
        if features is not None:
            count=int(mask.sum().item())
            if features.ndim!=2 or features.shape[0]!=count or features.shape[1]!=inputs_embeds.shape[-1]:
                raise ValueError(f'{kind} token/feature shape mismatch: tokens={count}, feature_shape={tuple(features.shape)}')
    # Equivalent count*hidden check avoids giant noncontiguous boolean index just for numel.
    # Materialize expanded masks for MPS masked_scatter and downstream positional masks.
    return tuple(mask.unsqueeze(-1).expand_as(inputs_embeds).contiguous() for mask in masks)
