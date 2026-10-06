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
    return dict(method='INSTANCE_LOCAL_FP32_INDEX_ADD_CAST_BACK',model_dtype=str(next(model.parameters()).dtype),
        reason='torch2.5.1 MPS IndexBackward index_put accumulate supports Float/Int/Bool only',parameters_added=0)
