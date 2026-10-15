"""Tiny exact raw-bit dictionary/fallback cases; no fixture/cache/model IO."""
import hashlib
import json
from pathlib import Path

from codec import exact_equal
from pixel_dictionary import validate_roundtrip, FORMAT


def main():
    import torch
    channels = [torch.arange(256,dtype=torch.float32)*0.00390625+offset for offset in (0., 0.125, -0.25)]
    pixel = torch.cat([x[:,None].repeat(1,2) for x in channels],dim=1)
    common = dict(input_ids=torch.tensor([[1,2,3]]),attention_mask=torch.tensor([[True,True,True]]))
    _, good = validate_roundtrip(dict(common,pixel_values_videos=pixel))
    assert good['pixel_values_videos']['storage']==FORMAT
    overflow = torch.arange(257,dtype=torch.float32)[:,None].repeat(1,6)
    _, bad = validate_roundtrip(dict(common,pixel_values_videos=overflow))
    assert bad['pixel_values_videos']['reason']=='BLOCK_UINT32_PATTERN_COUNT_EXCEEDS_256'
    stride = pixel.transpose(0,1)
    _, fallback = validate_roundtrip(dict(common,pixel_values_videos=stride))
    assert fallback['pixel_values_videos']['reason']=='UNSUPPORTED_SHAPE_ORIGINAL' or fallback['pixel_values_videos']['reason']=='UNSUPPORTED_LAYOUT_ORIGINAL'
    # Literal NaN payload bits and signed zeros, with no float arithmetic.
    import numpy as np
    raw=np.array([[0x00000000,0x80000000,0x7fc00001,0x7fc00002,0x3f800000,0xbf800000]],dtype=np.uint32)
    unusual=torch.from_numpy(raw.view(np.float32))
    payload, special=validate_roundtrip(dict(common,pixel_values_videos=unusual))
    assert special['pixel_values_videos']['storage']==FORMAT
    from pixel_dictionary import unpack
    assert exact_equal(dict(common,pixel_values_videos=unusual),unpack(payload))
    result=dict(status='PASS_TINY_EXACT_UINT32_LUT_OVERFLOW_LAYOUT_TOKENMASK_SYNTHETIC',
        checks=['three_blocks_256_bit_values_exact','257_value_original_gzip_fallback',
                'unsupported_stride_original_fallback','NaN_payload_and_signed_zero_bits_exact','tokenmask_original_retained'],
        real_media_processor_model_production_calls=0,original_input_precision_changed=False,
        code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')})
    report=Path(__file__).resolve().parents[2]/'reports/twenty_hour_five_20261014_v1/critic/cache_codec_06'
    with (report/'dictionary_synthetic_result_04.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))


if __name__=='__main__':main()
