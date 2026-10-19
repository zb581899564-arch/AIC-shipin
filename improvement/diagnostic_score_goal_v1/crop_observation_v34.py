"""Exact uint8 recovery of a PROCESSOR-RESIZED observation, never native RGB.

Pinned profile: Qwen2VLImageProcessorFast, patch16/temporal2/merge2, static
image temporal copies, fused float32 (u-127.5)/127.5 normalization. Every inverse
must exactly reproduce all original patch bytes; no clipping or fallback exists.
No processor/model/media/file IO or ground-truth argument is used here.
"""
from __future__ import annotations
from fractions import Fraction
import hashlib
from numbers import Integral

import numpy as np
from PIL import Image
import torch

PROFILE = 'RESIZED_OBSERVATION_PLANE'
OUTPUT_SIZE = (320, 180)


def _require(value, message):
    if not value:
        raise ValueError(message)


def _integer(value, name):
    _require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)), name+' must be an integer')
    return int(value)


def _rgb(value):
    _require(isinstance(value, np.ndarray) and value.dtype == np.uint8 and value.ndim == 3
             and value.shape[2] == 3 and min(value.shape[:2]) > 0, 'Actual uint8[H,W,3] observation RGB required')
    return value.shape[1], value.shape[0]


def _grid(value):
    if isinstance(value, torch.Tensor):
        _require(value.device.type == 'cpu' and value.dtype == torch.int64 and tuple(value.shape) in ((3,), (1, 3)),
                 'Exactly one CPU int64 static image grid required')
        row = value.reshape(3).tolist()
    elif isinstance(value, np.ndarray):
        _require(value.dtype == np.int64 and value.shape in ((3,), (1, 3)), 'Exactly one int64 grid required')
        row = value.reshape(3).tolist()
    else:
        _require(isinstance(value, (list, tuple)), 'Explicit one static image grid required')
        row = value[0] if len(value) == 1 and isinstance(value[0], (list, tuple)) else value
        _require(len(row) == 3, 'Exactly one THW grid required')
    t, h, w = [_integer(v, 'Grid dimension') for v in row]
    _require(t == 1 and h > 0 and w > 0 and h % 2 == w % 2 == 0,
             'Only T1 static images with merge2-compatible spatial grids are supported')
    return h, w


def _pixels(pixels, h, w):
    _require(isinstance(pixels, torch.Tensor) and pixels.device.type == 'cpu' and pixels.dtype == torch.float32
             and pixels.layout == torch.strided and not pixels.requires_grad and tuple(pixels.shape) == (h*w, 1536)
             and bool(torch.isfinite(pixels).all()), 'Finite detached CPU float32[h*w,1536] static image patches required')


def _bit_equal(a, b):
    return a.dtype == b.dtype and a.shape == b.shape and torch.equal(
        a.contiguous().view(torch.uint8), b.contiguous().view(torch.uint8))


def _array_sha(value):
    return hashlib.sha256(value.tobytes(order='C')).hexdigest()


def _tensor_sha(value):
    return hashlib.sha256(value.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()


def forward_pack_observation_rgb(rgb):
    """Pinned pure forward layout/normalization; returns (patches, grid[1,3])."""
    width, height = _rgb(rgb)
    _require(height % 32 == width % 32 == 0, 'Observation dimensions must be patch16/merge2 compatible')
    h, w = height//16, width//16
    image = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).to(torch.float32)
    normalized = (image-127.5)/127.5
    # [B,gridT,T2,C,h/2,mH2,pH16,w/2,mW2,pW16], then pinned fast-processor permutation.
    copies = normalized.unsqueeze(0).unsqueeze(0).unsqueeze(0).expand(1, 1, 2, 3, height, width)
    patches = copies.reshape(1, 1, 2, 3, h//2, 2, 16, w//2, 2, 16)
    patches = patches.permute(0, 1, 4, 7, 5, 8, 3, 2, 6, 9).reshape(h*w, 1536).contiguous()
    return patches, torch.tensor([[1, h, w]], dtype=torch.int64)


def recover_observation_rgb(pixels, grid):
    """Recover only the resized uint8 observation and prove exact forward bytes.

    Inverse rounding uses nearest integer without clipping. Out-of-range values,
    unequal temporal copies, changed normalization, or even a one-ULP mismatch
    fail. Source-native dimensions and information lost by resize are unknown.
    """
    h, w = _grid(grid); _pixels(pixels, h, w)
    packed = pixels.reshape(h//2, w//2, 2, 2, 3, 2, 16, 16)
    copies = packed.permute(5, 4, 0, 2, 6, 1, 3, 7).reshape(2, 3, h*16, w*16)
    _require(_bit_equal(copies[0], copies[1]), 'Static temporal copies are not bit-identical')
    unscaled = copies[0]*127.5+127.5
    rounded = torch.round(unscaled)
    _require(bool(torch.isfinite(rounded).all()) and bool(((rounded >= 0) & (rounded <= 255)).all()),
             'Inverse observation values lie outside uint8; clipping is prohibited')
    rgb = rounded.to(torch.uint8).permute(1, 2, 0).contiguous().numpy().copy()
    reconstructed, actual_grid = forward_pack_observation_rgb(rgb)
    _require(actual_grid.tolist() == [[1, h, w]] and _bit_equal(pixels, reconstructed),
             'Forward repatch/fused normalization does not reproduce every input bit; no approximate fallback')
    metadata = dict(profile=PROFILE, native_RGB_recovered=False, observation_dimensions=[w*16, h*16],
        image_grid_thw=[1, h, w], patch_size=16, temporal_patch_size=2, spatial_merge_size=2,
        normalization='FLOAT32(u-127.5)/127.5', inverse_rounding='nearest_uint8_without_clipping',
        max_inverse_rounding_error=float((unscaled-rounded).abs().max()), temporal_copies_bitidentical=True,
        forward_roundtrip_bitidentical=True, observation_RGB_pixel_sha256=_array_sha(rgb),
        input_pixel_tensor_sha256=_tensor_sha(pixels), original_decode_calls=0, processor_calls=0,
        production_admitted=False)
    return rgb, metadata


def independent_recovery_check(pixels, grid, recovered_rgb, metadata):
    """Independent row/merge/channel/time/patch traversal, without inverse code."""
    h, w = _grid(grid); _pixels(pixels, h, w)
    width, height = _rgb(recovered_rgb)
    _require((width, height) == (w*16, h*16), 'Observation dimensions do not match the actual patch grid')
    # Direct patches avoid the reshape/permute expression used by the forward packer.
    rows = []
    for by in range(h//2):
        for bx in range(w//2):
            for my in range(2):
                for mx in range(2):
                    y, x = (2*by+my)*16, (2*bx+mx)*16
                    block = torch.from_numpy(recovered_rgb[y:y+16, x:x+16].copy()).permute(2, 0, 1).float()
                    normalized = (block-127.5)/127.5
                    rows.append(normalized[:, None].expand(3, 2, 16, 16).reshape(1536))
    independent = torch.stack(rows)
    _require(_bit_equal(pixels, independent), 'Independent observation colors/spatial/channel/temporal order differs')
    _require(metadata['profile'] == PROFILE and metadata['native_RGB_recovered'] is False
             and metadata['observation_dimensions'] == [width, height] and metadata['image_grid_thw'] == [1, h, w]
             and metadata['observation_RGB_pixel_sha256'] == _array_sha(recovered_rgb)
             and metadata['input_pixel_tensor_sha256'] == _tensor_sha(pixels)
             and metadata['temporal_copies_bitidentical'] is True and metadata['forward_roundtrip_bitidentical'] is True,
             'Declared observation profile/pixel identity differs')
    return dict(status='PASS_EXACT_RESIZED_OBSERVATION_LAYOUT_AND_UINT8', profile=PROFILE,
                native_RGB_recovered=False, all_input_pixel_bits_equal=True, production_admitted=False)


def _extent(rgb, native_box, native_dimensions):
    ow, oh = _rgb(rgb)
    _require(isinstance(native_dimensions, (list, tuple)) and len(native_dimensions) == 2,
             'Original native dimensions [W,H] required')
    W, H = [_integer(v, 'Native dimension') for v in native_dimensions]
    _require(W > 0 and H > 0 and isinstance(native_box, (list, tuple)) and len(native_box) == 3,
             'Positive native dimensions and integer native crop triplet required')
    x, y, width = [_integer(v, 'Native box') for v in native_box]
    _require(x >= 0 and y >= 0 and width > 0 and x+width <= W and 16*y+9*width <= 16*H,
             'Original native box is not a legal implicit16:9 crop; no repair')
    exact = [Fraction(x*ow, W), Fraction(y*oh, H), Fraction((x+width)*ow, W), Fraction((16*y+9*width)*oh, 16*H)]
    return (ow, oh), (W, H), (x, y, width), exact


def render_observation_crop(recovered_rgb, native_box, native_dimensions):
    """Render a legal native-coordinate crop on the resized observation plane."""
    observed, native, box, exact = _extent(recovered_rgb, native_box, native_dimensions)
    rendered = np.asarray(Image.fromarray(recovered_rgb).transform(OUTPUT_SIZE, Image.Transform.EXTENT,
        tuple(map(float, exact)), resample=Image.Resampling.BICUBIC)).copy()
    proof = dict(profile=PROFILE, native_RGB_recovered=False, native_box=list(box), native_dimensions=list(native),
        observation_dimensions=list(observed), native_implicit_height_exact=str(Fraction(9*box[2], 16)),
        native_to_observation_scale_exact=[str(Fraction(observed[0], native[0])), str(Fraction(observed[1], native[1]))],
        extent_observation_xyxy_exact=list(map(str, exact)), extent_observation_xyxy_float=list(map(float, exact)),
        output_size=list(OUTPUT_SIZE), interpolation='PIL_EXTENT_BICUBIC',
        observation_RGB_pixel_sha256=_array_sha(recovered_rgb), output_RGB_pixel_sha256=_array_sha(rendered),
        original_decode_calls=0, processor_calls=0, production_admitted=False)
    return rendered, proof


def independent_observation_crop_check(recovered_rgb, native_box, native_dimensions, rendered, proof):
    """Re-derive exact scaled bounds and directly replay the declared PIL extent."""
    observed, native, box, exact = _extent(recovered_rgb, native_box, native_dimensions)
    ow, oh = observed; W, H = native; x, y, width = box
    independently_scaled = [Fraction(ow, W)*x, Fraction(oh, H)*y,
        Fraction(ow, W)*(x+width), Fraction(oh, H)*(Fraction(y)+Fraction(9*width, 16))]
    _require(exact == independently_scaled and 0 <= exact[0] < exact[2] <= ow and 0 <= exact[1] < exact[3] <= oh,
             'Independent native-to-observation extent/bounds differ')
    expected = np.array(Image.fromarray(recovered_rgb).transform((320, 180), Image.Transform.EXTENT,
        data=tuple(map(float, independently_scaled)), resample=Image.Resampling.BICUBIC), dtype=np.uint8)
    _require(isinstance(rendered, np.ndarray) and rendered.dtype == np.uint8 and rendered.shape == (180, 320, 3)
             and np.array_equal(rendered, expected), 'Independent observation crop pixels differ')
    _, expected_proof = render_observation_crop(recovered_rgb, native_box, native_dimensions)
    _require(proof == expected_proof, 'Declared resized-observation/native-box/source-order proof differs')
    return dict(status='PASS_RESIZED_OBSERVATION_NATIVE_BOX_EXTENT_RENDER', profile=PROFILE,
                native_RGB_recovered=False, production_admitted=False)
