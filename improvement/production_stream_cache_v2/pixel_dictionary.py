"""Optional exact storage coding, never model-input quantization.

Only standard contiguous CPU float32 2D pixel_values_videos with three equal
last-dimension blocks are eligible. Each block needs <=256 actual uint32 bit
patterns. Unsupported/overflow tensors retain original torch serialization.
"""
import sys

if __package__:
    from .codec import exact_equal, require, signature
else:
    from codec import exact_equal, require, signature

FORMAT = 'PIXEL_UINT8_BIT_LUT_V1'


def pack(encoded):
    import numpy as np
    import torch
    full_signature = signature(encoded)
    aliases = {name for group in full_signature['alias_groups'] for name in group}
    records, reports = {}, {}
    for name, tensor in encoded.items():
        reason = None
        if name != 'pixel_values_videos':reason = 'NONPIXEL_TENSOR_ORIGINAL'
        elif tensor.dtype != torch.float32:reason = 'UNSUPPORTED_DTYPE_ORIGINAL'
        elif tensor.ndim != 2 or not all(tensor.shape) or tensor.shape[-1] % 3:
            reason = 'UNSUPPORTED_SHAPE_ORIGINAL'
        elif tensor.stride() != (tensor.shape[-1], 1) or tensor.storage_offset() != 0 or tensor.requires_grad:
            reason = 'UNSUPPORTED_LAYOUT_ORIGINAL'
        elif name in aliases:reason = 'SHARED_STORAGE_ALIAS_ORIGINAL'
        if reason is not None:
            records[name] = dict(kind='ORIGINAL_TORCH_TENSOR', tensor=tensor)
            reports[name] = dict(storage='ORIGINAL_TORCH_GZIP', reason=reason)
            continue
        bits = tensor.detach().numpy().view(np.uint32)
        width = tensor.shape[-1]//3
        counts, LUTs = [], []
        for block in range(3):
            unique = np.unique(bits[:, block*width:(block+1)*width])
            counts.append(len(unique))
            if len(unique) > 256:
                reason = 'BLOCK_UINT32_PATTERN_COUNT_EXCEEDS_256'
                break
            LUTs.append(unique)
        if reason is not None:
            records[name] = dict(kind='ORIGINAL_TORCH_TENSOR', tensor=tensor)
            reports[name] = dict(storage='ORIGINAL_TORCH_GZIP', reason=reason,
                                 inspected_block_unique_counts=counts)
            continue
        blocks = []
        for block, LUT in enumerate(LUTs):
            values = bits[:, block*width:(block+1)*width]
            indices = np.searchsorted(LUT, values).astype(np.uint8)
            require(np.array_equal(LUT[indices], values), 'Raw bit dictionary index mismatch')
            blocks.append(dict(indices=torch.from_numpy(indices),
                LUT_int32_bits=torch.from_numpy(LUT.view(np.int32).copy())))
        records[name] = dict(kind=FORMAT, shape=list(tensor.shape), blocks=blocks,
                             byteorder=sys.byteorder)
        reports[name] = dict(storage=FORMAT, block_unique_counts=counts,
            original_numeric_dtype='torch.float32', model_precision_changed=False,
            original_payload_bytes=tensor.numel()*tensor.element_size(),
            indexed_payload_bytes=sum(x['indices'].numel()+4*x['LUT_int32_bits'].numel() for x in blocks))
    return dict(schema=FORMAT, records=records, full_signature=full_signature), reports


def unpack(payload):
    import numpy as np
    import torch
    require(payload['schema'] == FORMAT, 'Exact dictionary storage schema differs')
    encoded = {}
    for name, record in payload['records'].items():
        if record['kind'] == 'ORIGINAL_TORCH_TENSOR':
            encoded[name] = record['tensor']
            continue
        require(record['kind'] == FORMAT and name == 'pixel_values_videos' and
                record['byteorder'] == sys.byteorder and len(record['blocks']) == 3,
                'Unsupported dictionary encoding or byte order')
        shape = record['shape'];require(len(shape)==2 and shape[1]%3==0, 'Dictionary shape differs')
        width = shape[1]//3
        bits = np.empty(shape, dtype=np.uint32)
        for i, block in enumerate(record['blocks']):
            index, table = block['indices'], block['LUT_int32_bits']
            require(index.dtype == torch.uint8 and table.dtype == torch.int32 and
                    index.device.type == table.device.type == 'cpu' and
                    list(index.shape) == [shape[0], width] and 0 < table.numel() <= 256,
                    'Exact index/LUT shape or dtype differs')
            indices = index.numpy();LUT = table.numpy().view(np.uint32)
            require(int(indices.max()) < len(LUT), 'Dictionary index escaped exact LUT')
            bits[:, i*width:(i+1)*width] = LUT[indices]
        encoded[name] = torch.from_numpy(bits.view(np.float32))
    require(signature(encoded) == payload['full_signature'], 'Dictionary lost original dtype/shape/stride/bit bytes')
    return encoded


def validate_roundtrip(encoded):
    payload, report = pack(encoded)
    restored = unpack(payload)
    require(exact_equal(encoded, restored), 'Full actual dictionary roundtrip is not byte-exact')
    return payload, report
