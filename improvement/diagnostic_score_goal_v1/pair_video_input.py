"""Pure two-video inputs from accepted image patches, with CPU-only QA hooks.

No model, media decoder, real image/video processor or artifact writer. The
caller must bind and verify the old accepted inputs and synthetic pairing
proof before admission; returning an input does not grant that admission.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
from numbers import Integral
from types import SimpleNamespace
from unittest.mock import patch

import torch

QUESTION = ('Which clip would be more likely included in a concise summary of this video? '
            'Judge visible content only; equal preference and insufficient distinction should not force a winner. '
            'Reply with exactly one digit: 0 for Clip A, 1 for Clip B, 2 for equal preference.\n')
CLIP_OBSERVATIONS = 8
CLIP_GROUPS = 4
SEQUENCE_BUDGET = 4096
DIGITS = ('0', '1', '2')


def require(value, message):
    if not value:
        raise ValueError(message)


def _integer(value):
    require(isinstance(value, Integral) and not isinstance(value, bool), 'Native indices/grid dimensions must be integers')
    return int(value)


def _exact(value):
    require(isinstance(value, (Integral, str, Fraction)) and not isinstance(value, bool), 'Exact PTS required; no float/bool time')
    return Fraction(int(value)) if isinstance(value, Integral) else Fraction(value)


def _bit_equal(first, second):
    return (first.shape == second.shape and first.dtype == second.dtype
            and torch.equal(first.contiguous().view(torch.uint8), second.contiguous().view(torch.uint8)))


def _plan(frames, grid_hw, clip_ranges, sample_ordinals, exact_pts):
    require(len(grid_hw) == 2 and len(clip_ranges) == 2, 'Exactly one h/w grid and two A/B ranges required')
    height, width = map(_integer, grid_hw)
    require(height > 0 and width > 0 and height % 2 == width % 2 == 0, 'Positive merge2-compatible spatial grid required')
    ordinals = list(map(_integer, sample_ordinals))
    points = list(map(_exact, exact_pts))
    require(points and points[0] == 0 and all(a < b for a, b in zip(points, points[1:])), 'Complete increasing zero-origin source PTS required')
    require(len(frames) == len(ordinals) and ordinals and all(a < b for a, b in zip(ordinals, ordinals[1:]))
            and 0 <= ordinals[0] <= ordinals[-1] < len(points), 'Accepted source observations must match unique ordered native ordinals')
    clips = []
    for role, bounds in zip(('A', 'B'), clip_ranges):
        require(len(bounds) == 2, 'Each clip requires a half-open cell range')
        start, end = map(_integer, bounds)
        require(0 <= start < end <= len(frames) and end-start == CLIP_OBSERVATIONS and start % 2 == 0,
                'Each clip requires8 actual observations aligned to4 original groups; no padding')
        ids = ordinals[start:end]; times = [points[i] for i in ids]; origin = times[0]
        centers = [(times[j]+times[j+1])/2 for j in range(0, CLIP_OBSERVATIONS, 2)]
        clips.append(dict(role=role, cell_range_half_open=[start, end], global_group_ids=list(range(start//2, end//2)),
            sample_ordinals=ids, sample_exact_pts=list(map(str, times)), origin_exact=str(origin),
            absolute_group_centers_exact=list(map(str, centers)),
            relative_group_centers_exact=[str(t-origin) for t in centers], padded_observations=0))
    selected = sorted({j for clip in clips for j in range(*clip['cell_range_half_open'])})
    for index in selected:
        frame = frames[index]
        require(isinstance(frame, torch.Tensor) and frame.device.type == 'cpu' and frame.dtype == torch.float32
                and frame.layout == torch.strided and not frame.requires_grad
                and frame.shape == (height*width, 1536) and bool(torch.isfinite(frame).all()),
                'Detached finite accepted CPU float32[h*w,1536] image pixels required')
        value = frame.reshape(height*width, 3, 2, 16, 16)
        require(_bit_equal(value[:, :, 0], value[:, :, 1]), 'Accepted image temporal slices must be bit-identical')
    return height, width, clips


def _proof(reference):
    if reference is None:
        return None
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}
            and isinstance(reference['path'], str) and bool(reference['path'])
            and isinstance(reference['sha256'], str) and len(reference['sha256']) == 64
            and all(c in '0123456789abcdef' for c in reference['sha256']), 'Explicit old synthetic pairing proof reference required')
    return dict(reference)


def pair_video_pixels(frames, grid_hw, clip_ranges, sample_ordinals, exact_pts, *, pairing_proof_ref=None):
    """Return two separate4-group videos, exact local times and sample bindings.

    Ranges index the old occupied image-cell list and start at even indices.
    Clip overlap is recorded, not silently called independent observations.
    Proof references are carried without reading/repeating their old checks.
    """
    height, width, clips = _plan(frames, grid_hw, clip_ranges, sample_ordinals, exact_pts)
    blocks, bindings = [], []
    for clip in clips:
        start, end = clip['cell_range_half_open']
        for group, index in enumerate(range(start, end, 2)):
            left = frames[index].reshape(height*width, 3, 2, 16, 16)[:, :, 0]
            right = frames[index+1].reshape(height*width, 3, 2, 16, 16)[:, :, 0]
            blocks.append(torch.stack((left, right), dim=2).reshape(height*width, 1536))
            for temporal in (0, 1):
                local = 2*group+temporal
                bindings.append(dict(clip=clip['role'], clip_group=group, temporal_slice=temporal,
                    source_cell=index+temporal, native_ordinal=clip['sample_ordinals'][local],
                    exact_pts=clip['sample_exact_pts'][local]))
    return dict(pixel_values_videos=torch.cat(blocks, dim=0).contiguous(),
        video_grid_thw=torch.tensor([[CLIP_GROUPS, height, width]]*2, dtype=torch.int64),
        clip_metadata=clips, sample_bindings=bindings,
        shared_native_ordinals=sorted(set(clips[0]['sample_ordinals']) & set(clips[1]['sample_ordinals'])),
        observation_appearances=16, distinct_native_observations=len({r['native_ordinal'] for r in bindings}),
        old_synthetic_pairing_proof=_proof(pairing_proof_ref),
        old_pairing_proof_verified_here=False, real_processor_calls=0, input_admitted=False)


def independent_pixel_check(frames, grid_hw, clip_ranges, sample_ordinals, exact_pts, pair):
    """Independent flat channel/slice copies, without the builder's stack path."""
    height, width, clips = _plan(frames, grid_hw, clip_ranges, sample_ordinals, exact_pts)
    expected = torch.empty((2*CLIP_GROUPS*height*width, 1536), dtype=torch.float32)
    row = 0
    for clip in clips:
        start, end = clip['cell_range_half_open']
        for index in range(start, end, 2):
            target = expected[row:row+height*width]
            for channel in range(3):
                column = channel*512
                target[:, column:column+256] = frames[index][:, column:column+256]
                target[:, column+256:column+512] = frames[index+1][:, column:column+256]
            row += height*width
    require(_bit_equal(expected, pair['pixel_values_videos']), 'Independent two-video pixel/index mapping mismatch')
    require(torch.equal(pair['video_grid_thw'], torch.tensor([[4, height, width]]*2, dtype=torch.int64))
            and pair['video_grid_thw'].dtype == torch.int64 and pair['video_grid_thw'].device.type == 'cpu'
            and pair['clip_metadata'] == clips and len(pair['sample_bindings']) == 16,
            'Independent two-video grid/time/source binding mismatch')
    expected_bindings = []
    for clip in clips:
        start, _ = clip['cell_range_half_open']
        for local, (ordinal, pts) in enumerate(zip(clip['sample_ordinals'], clip['sample_exact_pts'])):
            expected_bindings.append(dict(clip=clip['role'], clip_group=local//2, temporal_slice=local%2,
                source_cell=start+local, native_ordinal=ordinal, exact_pts=pts))
    require(pair['sample_bindings'] == expected_bindings, 'Independent sample binding mismatch')
    return dict(status='PASS_PURE_TWO_VIDEO_PIXEL_AND_NATIVE_INDEX_CHECK', real_processor_calls=0,
                input_admitted=False, old_synthetic_pairing_proof=pair['old_synthetic_pairing_proof'])


def _tokens(tokenizer, text):
    value = tokenizer(text, return_tensors='pt', add_special_tokens=False, truncation=False)
    result = {k: value[k].contiguous() for k in ('input_ids', 'attention_mask')}
    require(all(v.device.type == 'cpu' and v.dtype == torch.int64 and v.ndim == 2 and v.shape[0] == 1 for v in result.values())
            and result['input_ids'].shape == result['attention_mask'].shape
            and bool((result['attention_mask'] == 1).all()), 'One complete unpadded CPU tokenizer sequence required')
    require(0 < result['input_ids'].shape[1] <= SEQUENCE_BUDGET, 'New pair exceeds4096 tokens; no truncation')
    return result


def _token_evidence(encoded):
    return {key: dict(shape=list(value.shape), dtype=str(value.dtype),
                     sha256=hashlib.sha256(value.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
            for key, value in encoded.items()}


def build_text_input(processor, pair):
    """Fixed user question and exactly two original video-marker expansions.

    Returns prefix tokens only. Each actual class must also remain a single
    new token after this exact assistant prefix, not only in isolation.
    """
    clips = pair['clip_metadata']; grid = pair['video_grid_thw']
    require(len(clips) == 2 and [c['role'] for c in clips] == ['A', 'B'] and grid.shape == (2, 3)
            and grid.tolist()[0][0] == grid.tolist()[1][0] == CLIP_GROUPS
            and processor.video_processor.merge_size == 2, 'Explicit two4-group video inputs required')
    content = [dict(type='text', text=QUESTION+'A:\n'), dict(type='video'),
               dict(type='text', text='\nB:\n'), dict(type='video')]
    messages = [dict(role='user', content=content)]
    options = dict(tokenize=False, enable_thinking=False)
    raw = processor.apply_chat_template(messages, add_generation_prompt=True, **options)
    plain = processor.apply_chat_template(messages, add_generation_prompt=False, **options)
    require(isinstance(raw, str) and raw.startswith(plain) and len(raw) > len(plain), 'Final assistant generation prefix required')
    assistant_prefix = raw[len(plain):]
    marker = processor.vision_start_token+processor.video_token+processor.vision_end_token
    parts = raw.split(marker)
    require(len(parts) == 3, 'Exactly two original video markers required')
    expansions, per_group = [], []
    for clip, (_, h, w) in zip(clips, grid.tolist()):
        require(h > 0 and w > 0 and h % 2 == w % 2 == 0, 'Merge2 spatial grid required')
        times = list(map(_exact, clip['relative_group_centers_exact']))
        require(len(times) == 4 and all(t >= 0 for t in times) and all(a < b for a, b in zip(times, times[1:])),
                'Four ordered clip-local exact group centers required')
        count = h*w//4; per_group.append(count)
        expansions.append(''.join('<%.1f seconds>' % float(t)+processor.vision_start_token+
                           processor.video_token*count+processor.vision_end_token for t in times))
    # Split originals once: K=1 means an expanded group itself contains marker.
    text = parts[0]+expansions[0]+parts[1]+expansions[1]+parts[2]
    require(text.endswith(assistant_prefix), 'Assistant prefix must be the final input suffix; no answer prefill')
    encoded = _tokens(processor.tokenizer, text)
    class_ids = {}
    for digit in DIGITS:
        ids = processor.tokenizer.encode(digit, add_special_tokens=False)
        require(len(ids) == 1 and type(ids[0]) is int and ids[0] >= 0, 'Each class digit must be exactly one actual token')
        full = _tokens(processor.tokenizer, text+digit)['input_ids']
        require(full.shape[1] == encoded['input_ids'].shape[1]+1
                and torch.equal(full[:, :-1], encoded['input_ids']) and int(full[0, -1]) == ids[0],
                'Class digit merges with the assistant prefix or is not one next token')
        class_ids[digit] = ids[0]
    require(len(set(class_ids.values())) == 3, 'Actual class tokens must be distinct')
    video_id = processor.tokenizer.convert_tokens_to_ids(processor.video_token)
    require(type(video_id) is int and video_id >= 0 and video_id not in class_ids.values(), 'Explicit video token identity required')
    positions = (encoded['input_ids'][0] == video_id).nonzero().flatten().tolist()
    require(len(positions) == sum(4*k for k in per_group), 'All actual video-token positions must match two grids')
    clip_positions = []; offset = 0
    for role, count in zip(('A', 'B'), per_group):
        groups = [positions[offset+j*count:offset+(j+1)*count] for j in range(4)]
        require(all(len(g) == count and g == list(range(g[0], g[0]+count)) for g in groups), 'Each timegroup needs contiguous video tokens')
        clip_positions.append(dict(clip=role, group_token_positions=groups)); offset += 4*count
    return encoded, dict(raw_template=raw, expanded_text=text, question=QUESTION,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(), assistant_generation_prefix=assistant_prefix,
        next_token_prediction_position=int(encoded['input_ids'].shape[1])-1,
        class_token_ids=[class_ids[digit] for digit in DIGITS], class_tokens_by_digit=class_ids,
        class_digit_order=list(DIGITS), token_evidence=_token_evidence(encoded),
        video_token_id=video_id, clip_positions=clip_positions, sequence_tokens=int(encoded['input_ids'].shape[1]),
        maximum_input_plus_digit_tokens=SEQUENCE_BUDGET, real_processor_calls=0, input_admitted=False)


def independent_text_check(processor, pair, encoded, metadata):
    """Pinned processor expands two markers; pixels are adopted, never encoded.

    This is intended for the main agent's FIRST actual CPU QA, after source
    registration. Unit tests use a fake processor/tokenizer only.
    """
    original = processor.video_processor
    grid = pair['video_grid_thw']; clips = pair['clip_metadata']
    times = [[float(_exact(t)) for t in c['relative_group_centers_exact']] for c in clips]
    class AdoptedVideos:
        merge_size = original.merge_size
        model_input_names = original.model_input_names

        def __call__(self, *args, **kwargs):
            return dict(pixel_values_videos=pair['pixel_values_videos'], video_grid_thw=grid.clone(),
                        video_metadata=[SimpleNamespace(fps=2, frames_indices=list(range(8))) for _ in range(2)])

    with patch.object(processor, 'video_processor', AdoptedVideos()), \
            patch.object(processor, '_calculate_timestamps', side_effect=times) as timestamps:
        actual = processor(text=[metadata['raw_template']], videos=[object(), object()], return_tensors='pt',
                           padding=False, add_special_tokens=False, truncation=False)
        require(timestamps.call_count == 2, 'Each video must consume its own timestamp sequence exactly once')
    require(all(torch.equal(actual[k], encoded[k]) for k in ('input_ids', 'attention_mask'))
            and torch.equal(actual['video_grid_thw'], grid)
            and _bit_equal(actual['pixel_values_videos'], pair['pixel_values_videos']),
            'Independent pinned two-video processor text/grid/pixel adoption mismatch')
    require(metadata['question'] == QUESTION and metadata['next_token_prediction_position'] == encoded['input_ids'].shape[1]-1,
            'Fixed question or next-token position changed')
    actual_classes = []
    for digit in DIGITS:
        ids = processor.tokenizer.encode(digit, add_special_tokens=False)
        require(len(ids) == 1 and type(ids[0]) is int and ids[0] >= 0, 'Independent class digit is not one actual token')
        candidate = _tokens(processor.tokenizer, metadata['expanded_text']+digit)['input_ids']
        require(candidate.shape[1] == encoded['input_ids'].shape[1]+1
                and torch.equal(candidate[:, :-1], encoded['input_ids']) and int(candidate[0, -1]) == ids[0],
                'Independent next-digit prefix/identity mismatch')
        actual_classes.append(ids[0])
    require(metadata['class_digit_order'] == list(DIGITS)
            and len(set(actual_classes)) == 3
            and metadata['class_token_ids'] == actual_classes == [metadata['class_tokens_by_digit'][d] for d in DIGITS]
            and metadata['token_evidence'] == _token_evidence(encoded)
            and metadata['text_sha256'] == hashlib.sha256(metadata['expanded_text'].encode()).hexdigest()
            and metadata['expanded_text'].endswith(metadata['assistant_generation_prefix']),
            'Registered digit order, text or token evidence changed')
    return dict(status='PASS_FIRST_TWO_VIDEO_STUB_PROCESSOR_TEXT_CHECK_NOT_GPU_ADMISSION',
                real_video_processor_calls=0, original_image_processor_calls=0, timestamp_sequences=2,
                input_admitted=False, old_synthetic_pairing_proof=pair['old_synthetic_pairing_proof'])
