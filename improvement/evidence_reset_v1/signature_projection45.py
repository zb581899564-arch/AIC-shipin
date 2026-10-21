"""Explicit bridge from lossless codec metadata to runtime tensor identities."""
def runtime_projection(codec_signature):
    assert set(codec_signature)=={'tensors','alias_groups'}
    assert codec_signature['alias_groups']==[]
    tensors=codec_signature['tensors']
    assert set(tensors)=={'pixel_values','image_grid_thw','input_ids','attention_mask'}
    projected={}
    for name,row in tensors.items():
        assert row['layout']=='torch.strided'and row['requires_grad']is False
        assert row['storage_offset']==0 and row['bytes']>0
        projected[name]={key:row[key]for key in ['shape','dtype','sha256']}
    return projected
