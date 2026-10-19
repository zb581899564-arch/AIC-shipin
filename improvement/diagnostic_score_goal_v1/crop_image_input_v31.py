"""Pure source/A/B physical-crop inputs. No filesystem, JPEG decoder or model IO.

Real crop encoding belongs to the caller's first CPU preparation. This module
adopts already encoded image pixels; a stub processor QA never encodes images.
"""
from __future__ import annotations

import hashlib
from numbers import Integral
from unittest.mock import patch

import numpy as np
from PIL import Image
import torch

import crop_geometry_v31 as geometry

QUESTION = ('Which crop is better composed for the source image? Judge visible composition and preserved subjects '
            'in Crop A and Crop B, using Source only as context. Reply with exactly one digit: '
            '0 for Crop A, 1 for Crop B, 2 for equally suitable.\n')
ROLES = ('Source', 'A', 'B')
DIGITS = ('0', '1', '2')
SEQUENCE_BUDGET = 4096
RENDER_SIZE = (320, 180)


def _require(value, message):
    geometry.require(value, message)


def _rgb(value):
    _require(isinstance(value, np.ndarray) and value.dtype == np.uint8 and value.ndim == 3
             and value.shape[2] == 3 and min(value.shape[:2]) > 0, 'Accepted original uint8[H,W,3] RGB required')
    return value.shape[1], value.shape[0]


def _sha_array(value):
    return hashlib.sha256(value.tobytes(order='C')).hexdigest()


def render_crop(rgb, box):
    """Render accepted original RGB at fractional implicit-height EXTENT."""
    width, height = _rgb(rgb)
    _require(geometry.legal(box, width, height), 'Legal original native box required')
    x, y, w = map(int, box)
    extent = [x, y, x+w, y+9*w/16]
    rendered = np.asarray(Image.fromarray(rgb).transform(RENDER_SIZE, Image.Transform.EXTENT,
        tuple(extent), resample=Image.Resampling.BICUBIC)).copy()
    return rendered, dict(source_dimensions=[width, height], source_RGB_pixel_sha256=_sha_array(rgb),
        native_box=[x, y, w], extent_xyxy=extent, implicit_height_exact=f'{9*w}/16',
        output_size=list(RENDER_SIZE), interpolation='PIL_EXTENT_BICUBIC',
        output_RGB_pixel_sha256=_sha_array(rendered), new_JPEG_decode=False, input_admitted=False)


def independent_render_check(rgb, box, rendered, metadata):
    """Independent bounds/extent/direct PIL replay; never decodes the old JPEG."""
    width, height = _rgb(rgb)
    _require(isinstance(box, (list, tuple)) and len(box) == 3
        and all(isinstance(v, Integral) and not isinstance(v, bool) for v in box), 'Integer original box required')
    x, y, w = map(int, box)
    _require(w > 0 and x >= 0 and y >= 0 and x+w <= width and 16*y+9*w <= 16*height,
             'Independent native boundary check failed')
    extent = [x, y, x+w, (16*y+9*w)/16]
    expected = np.array(Image.fromarray(rgb).transform((320, 180), Image.Transform.EXTENT,
        data=tuple(extent), resample=Image.Resampling.BICUBIC), dtype=np.uint8)
    _require(isinstance(rendered, np.ndarray) and rendered.dtype == np.uint8
        and rendered.shape == (180, 320, 3) and np.array_equal(rendered, expected),
        'Independent actual crop pixels differ')
    _require(metadata == dict(source_dimensions=[width, height], source_RGB_pixel_sha256=_sha_array(rgb),
        native_box=[x, y, w], extent_xyxy=extent, implicit_height_exact=f'{9*w}/16',
        output_size=[320, 180], interpolation='PIL_EXTENT_BICUBIC',
        output_RGB_pixel_sha256=_sha_array(expected), new_JPEG_decode=False, input_admitted=False),
        'Independent original RGB/box/render binding differs')
    return dict(status='PASS_NEW_NATIVE_CROP_RGB_GEOMETRY_AND_RENDER_CHECK', new_JPEG_decodes=0,
                processor_calls=0, input_admitted=False)


def _grid(value):
    if isinstance(value, torch.Tensor):
        _require(value.device.type == 'cpu' and value.dtype == torch.int64, 'CPU int64 image grids required')
        rows = value.tolist()
    else:
        rows = value
    _require(isinstance(rows, (list, tuple)) and len(rows) == 3, 'Exactly Source/A/B grid rows required')
    checked = []
    for row in rows:
        _require(len(row) == 3 and all(isinstance(x, Integral) and not isinstance(x, bool) for x in row),
                 'Integer image grid THW required')
        t, h, w = map(int, row)
        _require(t == 1 and h > 0 and w > 0 and h % 2 == w % 2 == 0, 'Three actual static merge2 image grids required')
        checked.append([t, h, w])
    return torch.tensor(checked, dtype=torch.int64)


def _bit_equal(a, b):
    return a.shape == b.shape and a.dtype == b.dtype and torch.equal(
        a.contiguous().view(torch.uint8), b.contiguous().view(torch.uint8))


def _images(image_pixels, grid):
    _require(len(image_pixels) == 3, 'Exactly Source/A/B encoded images required')
    for value, (t, h, w) in zip(image_pixels, grid.tolist()):
        _require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.dtype == torch.float32
            and value.layout == torch.strided and not value.requires_grad and value.shape == (t*h*w, 1536)
            and bool(torch.isfinite(value).all()), 'Finite detached CPU float32 image patch rows required')
        repeated = value.reshape(t*h*w, 3, 2, 16, 16)
        _require(_bit_equal(repeated[:, :, 0], repeated[:, :, 1]), 'Static image temporal slices must be bit-identical')


def pack_image_pixels(image_pixels, image_grid_thw):
    """Adopt old Source pixels and first-new encoded A/B; no encoding is done."""
    grid = _grid(image_grid_thw)
    _images(image_pixels, grid)
    return dict(pixel_values=torch.cat(list(image_pixels), dim=0).contiguous(), image_grid_thw=grid)


def independent_pixel_check(image_pixels, image_grid_thw, packed):
    grid = _grid(image_grid_thw)
    _images(image_pixels, grid)
    _require(set(packed) == {'pixel_values', 'image_grid_thw'} and _bit_equal(grid, packed['image_grid_thw']),
             'Independent three-image grid/key mismatch')
    offset = 0
    actual = packed['pixel_values']
    _require(actual.device.type == 'cpu' and actual.dtype == torch.float32
        and actual.shape == (sum(int(row.prod()) for row in grid), 1536), 'Independent packed pixel shape mismatch')
    for value in image_pixels:
        end = offset+len(value)
        _require(_bit_equal(value, actual[offset:end]), 'Independent Source/A/B flat pixel boundary/order mismatch')
        offset = end
    return dict(status='PASS_THREE_IMAGE_ADOPTED_PIXEL_ORDER_CHECK', image_roles=list(ROLES),
                processor_calls=0, input_admitted=False)


def _messages():
    return [dict(role='user', content=[dict(type='text', text=QUESTION+'Source:\n'), dict(type='image'),
        dict(type='text', text='\nCrop A:\n'), dict(type='image'),
        dict(type='text', text='\nCrop B:\n'), dict(type='image')])]


def _tokens(tokenizer, text):
    values = tokenizer(text, return_tensors='pt', add_special_tokens=False, truncation=False)
    result = {key: values[key].contiguous() for key in ('input_ids', 'attention_mask')}
    _require(all(v.device.type == 'cpu' and v.dtype == torch.int64 and v.ndim == 2 and v.shape[0] == 1 for v in result.values())
        and result['input_ids'].shape == result['attention_mask'].shape
        and bool((result['attention_mask'] == 1).all()), 'One unpadded complete CPU token sequence required')
    _require(0 < result['input_ids'].shape[1] <= SEQUENCE_BUDGET, 'Input plus digit exceeds4096; never truncate')
    return result


def _evidence(values):
    return {key: dict(shape=list(v.shape), dtype=str(v.dtype),
        sha256=hashlib.sha256(v.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()) for key, v in values.items()}


def _classes(processor, text, encoded):
    classes = []
    for digit in DIGITS:
        ids = processor.tokenizer.encode(digit, add_special_tokens=False)
        _require(len(ids) == 1 and type(ids[0]) is int and ids[0] >= 0, 'Each class must be one actual next digit token')
        full = _tokens(processor.tokenizer, text+digit)['input_ids']
        _require(full.shape[1] == encoded['input_ids'].shape[1]+1
            and torch.equal(full[:, :-1], encoded['input_ids']) and int(full[0, -1]) == ids[0],
            'Digit merges with assistant prefix or changes existing tokens')
        classes.append(ids[0])
    _require(len(set(classes)) == 3, 'Three class tokens must be distinct')
    return classes


def build_text_input(processor, image_grid_thw):
    """Prefix-only source/A/B text for three actual image grids; no GT argument."""
    grid = _grid(image_grid_thw)
    _require(processor.image_processor.merge_size == 2, 'Actual merge2 processor required')
    options = dict(tokenize=False, enable_thinking=False)
    raw = processor.apply_chat_template(_messages(), add_generation_prompt=True, **options)
    plain = processor.apply_chat_template(_messages(), add_generation_prompt=False, **options)
    _require(isinstance(raw, str) and raw.startswith(plain) and len(raw) > len(plain), 'Final assistant generation prefix required')
    prefix = raw[len(plain):]
    marker = processor.vision_start_token+processor.image_token+processor.vision_end_token
    parts = raw.split(marker)
    _require(len(parts) == 4, 'Exactly three original image markers required')
    counts = [int(row.prod())//4 for row in grid]
    expansions = [processor.vision_start_token+processor.image_token*count+processor.vision_end_token for count in counts]
    text = parts[0]+''.join(expansion+part for expansion, part in zip(expansions, parts[1:]))
    _require(text.endswith(prefix), 'Assistant prefix must be final; no answer prefill')
    encoded = _tokens(processor.tokenizer, text)
    classes = _classes(processor, text, encoded)
    image_id = processor.tokenizer.convert_tokens_to_ids(processor.image_token)
    _require(type(image_id) is int and image_id >= 0 and image_id not in classes, 'Actual image-token identity required')
    positions = (encoded['input_ids'][0] == image_id).nonzero().flatten().tolist()
    _require(len(positions) == sum(counts), 'Actual image-token count differs from three grids')
    bindings, offset = [], 0
    for role, count in zip(ROLES, counts):
        selected = positions[offset:offset+count]
        _require(selected == list(range(selected[0], selected[0]+count)), 'Each image token run must be contiguous')
        bindings.append(dict(role=role, token_positions=selected, image_tokens=count))
        offset += count
    return encoded, dict(question=QUESTION, raw_template=raw, expanded_text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(), assistant_generation_prefix=prefix,
        next_token_prediction_position=int(encoded['input_ids'].shape[1])-1,
        class_token_ids=classes, class_digit_order=list(DIGITS), class_tokens_by_digit=dict(zip(DIGITS, classes)),
        image_grid_thw=grid.tolist(), image_roles=list(ROLES), image_tokens_per_image=counts,
        image_token_id=image_id, image_positions=bindings, total_image_tokens=sum(counts),
        sequence_tokens=int(encoded['input_ids'].shape[1]), maximum_input_plus_digit_tokens=SEQUENCE_BUDGET,
        token_evidence=_evidence(encoded), real_image_processor_calls=0, input_admitted=False)


def independent_text_check(processor, packed, encoded, metadata):
    """Pinned processor expands three markers while a stub adopts actual pixels."""
    grid = _grid(packed['image_grid_thw'])
    original = processor.image_processor

    class AdoptedImages:
        def __getattr__(self, name):
            return getattr(original, name)

        def __call__(self, *args, **kwargs):
            return dict(pixel_values=packed['pixel_values'], image_grid_thw=grid.clone())

    expected_raw = processor.apply_chat_template(_messages(), add_generation_prompt=True,
                                                 tokenize=False, enable_thinking=False)
    _require(metadata['raw_template'] == expected_raw and metadata['question'] == QUESTION,
             'Fixed label-free three-image question/template changed')
    with patch.object(processor, 'image_processor', AdoptedImages()):
        actual = processor(text=[metadata['raw_template']], images=[object(), object(), object()],
            return_tensors='pt', padding=False, add_special_tokens=False, truncation=False)
    _require(all(torch.equal(actual[k], encoded[k]) for k in ('input_ids', 'attention_mask'))
        and _bit_equal(actual['image_grid_thw'], grid) and _bit_equal(actual['pixel_values'], packed['pixel_values']),
        'Independent three-image processor text/grid/adopted pixel mismatch')
    classes = _classes(processor, metadata['expanded_text'], encoded)
    _require(all(torch.equal(_tokens(processor.tokenizer, metadata['expanded_text'])[k], encoded[k])
        for k in ('input_ids', 'attention_mask')), 'Expanded text no longer matches exact prefix tokens')
    _, expected_meta = build_text_input(processor, grid)
    _require(metadata == expected_meta and metadata['class_token_ids'] == classes,
             'Independent text evidence/class/grid/token binding changed')
    return dict(status='PASS_FIRST_THREE_IMAGE_STUB_PROCESSOR_TEXT_CHECK_NOT_GPU_ADMISSION',
        image_roles=list(ROLES), image_tokens_per_image=metadata['image_tokens_per_image'],
        real_image_processor_calls=0, input_admitted=False)
