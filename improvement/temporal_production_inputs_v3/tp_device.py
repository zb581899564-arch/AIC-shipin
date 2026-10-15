"""Complete input transfer/signature; no model, decode, precision conversion or IO."""
import hashlib

from tp_contract import require


def signature_any_device(encoded):
    """Same fields and logical-byte hashes as the frozen CPU codec signature."""
    import torch
    require(isinstance(encoded,dict) and encoded,'Complete nonempty tensor dictionary required')
    tensors,storages={},{}
    for key,value in sorted(encoded.items()):
        require(isinstance(value,torch.Tensor) and value.layout==torch.strided and not value.is_quantized,
                'Dense original dtype tensors required')
        raw=value.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes()
        tensors[key]=dict(dtype=str(value.dtype),shape=list(value.shape),stride=list(value.stride()),
            storage_offset=value.storage_offset(),layout=str(value.layout),requires_grad=value.requires_grad,
            bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        storage=value.untyped_storage()
        storages.setdefault((str(value.device),storage.data_ptr(),storage.nbytes()),[]).append(key)
    return dict(tensors=tensors,alias_groups=sorted(sorted(names) for names in storages.values() if len(names)>1))


def transfer_exact(encoded,device,expected_signature):
    """Copy every unique storage, recreate original views, verify before prefill.

    Ordinary dictionary .to() may lose aliases and noncontiguous storage layout.
    This preserves the complete CPU input ABI including unused storage and offsets.
    Each caller must perform an independent model prefill; there is no KV cache.
    """
    import torch
    require(signature_any_device(encoded)==expected_signature,'CPU canonical signature changed before transfer')
    target=torch.device(device);buffers={};result={}
    for name,value in encoded.items():
        require(value.device.type=='cpu','Only permanent CPU canonical input may be transferred')
        storage=value.untyped_storage();key=(storage.data_ptr(),storage.nbytes())
        if key not in buffers:
            byteview=torch.empty(0,dtype=torch.uint8).set_(storage,0,(storage.nbytes(),),(1,))
            # copy=True also makes the pure CPU check exercise independent storage.
            buffers[key]=byteview.to(device=target,copy=True)
        view=torch.empty(0,dtype=value.dtype,device=target).set_(buffers[key].untyped_storage(),
            value.storage_offset(),tuple(value.shape),tuple(value.stride()))
        view.requires_grad_(value.requires_grad)
        result[name]=view
    actual=signature_any_device(result)
    require(actual==expected_signature,'Actual complete GPU/target input dtype/stride/offset/alias/bytes differs')
    return result,dict(full_input_signature=expected_signature,GPU_input_signature=actual,
        target_device=str(target),actual_GPU_transfer=target.type=='cuda',precision_conversion=False,
        complete_dictionary_transferred=True,cross_role_KV_reuse=False,new_model_calls=0)
