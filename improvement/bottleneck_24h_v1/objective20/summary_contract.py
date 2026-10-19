"""One new source-summary task; pure cached-patch input and label construction.

No CUDA masking, media decoding, processor image encoding, model or artifact IO.
Overview and Excerpt are two videos with separate, actual native time origins.
"""
from fractions import Fraction as F
from bisect import bisect_left
from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import json
import torch

MAX_SEGMENTS = 6
MAX_ANSWER_TOKENS = 512
MAX_SEQUENCE_TOKENS = 12288


def require(value, message):
    if not value:
        raise ValueError(message)


def signature(values):
    return {k: dict(shape=list(v.shape), dtype=str(v.dtype), sha256=hashlib.sha256(
        v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
        for k, v in values.items()}


def sample_even(indices, maximum=64):
    """Actual observations only, both actual endpoints, no padding or duplicates."""
    count = min(maximum, len(indices) - len(indices) % 2)
    require(count >= 2, 'At least two real observations required')
    selected = [indices[j * (len(indices)-1)//(count-1)] for j in range(count)]
    require(len(set(selected)) == count and selected[0] == indices[0]
            and selected[-1] == indices[-1], 'Even source observation sampling failed')
    return selected


def build_pixels(frames, grid_hw, ordinals, exact_pts, start_exact, end_exact, owner):
    h, w = map(int, grid_hw); points = list(map(F, exact_pts))
    start, end = F(start_exact), F(end_exact)
    require(h > 0 and w > 0 and h % 2 == w % 2 == 0, 'Merge2 spatial grid required')
    require(len(frames) == len(ordinals) and points[0] == 0
            and all(a < b for a, b in zip(points, points[1:]))
            and all(a < b for a, b in zip(ordinals, ordinals[1:])), 'Ordered original source observations/clock')
    local = [i for i, o in enumerate(ordinals) if start <= points[o] < end]
    plans = [('Overview', sample_even(list(range(len(frames)))), F(0)),
             ('Excerpt', sample_even(local), start)]
    blocks, videos = [], []
    for role, indices, origin in plans:
        ids = [ordinals[i] for i in indices]; times = [points[o] for o in ids]
        for a, b in zip(indices[::2], indices[1::2]):
            for i in (a, b):
                require(frames[i].device.type == 'cpu' and frames[i].dtype == torch.float32
                        and frames[i].shape == (h*w, 1536) and bool(torch.isfinite(frames[i]).all()),
                        'Finite original CPU image patches required')
                v = frames[i].reshape(h*w, 3, 2, 16, 16)
                require(torch.equal(v[:, :, 0].contiguous().view(torch.uint8),
                                    v[:, :, 1].contiguous().view(torch.uint8)),
                        'Original image temporal slices must be identical')
            left = frames[a].reshape(h*w, 3, 2, 16, 16)[:, :, 0]
            right = frames[b].reshape(h*w, 3, 2, 16, 16)[:, :, 0]
            blocks.append(torch.stack((left, right), 2).reshape(h*w, 1536))
        videos.append(dict(role=role, owner=owner, cells=indices, native_ordinals=ids,
            exact_pts=list(map(str, times)), origin_exact=str(origin),
            group_timestamps_exact=[str((a+b)/2-origin) for a, b in zip(times[::2], times[1::2])],
            observations=len(indices), groups=len(indices)//2, padding=0))
    values = dict(pixel_values_videos=torch.cat(blocks).contiguous(),
                  video_grid_thw=torch.tensor([[v['groups'], h, w] for v in videos], dtype=torch.int64))
    return values, dict(videos=videos, window_start_exact=str(start), window_end_exact=str(end),
        sparse_visual_observations_not_continuous_motion=True, new_media_decodes=0, new_image_processor_calls=0)


def independent_pixels(frames, grid_hw, values, plan, ordinals, exact_pts):
    h, w = map(int, grid_hw); points = list(map(F, exact_pts)); offset = 0
    expected = torch.empty_like(values['pixel_values_videos'])
    for video in plan['videos']:
        require(video['native_ordinals'] == [ordinals[i] for i in video['cells']]
            and video['exact_pts'] == [str(points[o]) for o in video['native_ordinals']],
            'First independent original source/frame/time order check')
        for a, b in zip(video['cells'][::2], video['cells'][1::2]):
            dst = expected[offset:offset+h*w]
            for c in range(3):
                dst[:, c*512:c*512+256] = frames[a][:, c*512:c*512+256]
                dst[:, c*512+256:(c+1)*512] = frames[b][:, c*512:c*512+256]
            offset += h*w
    require(offset == len(expected) and torch.equal(expected.view(torch.uint8),
            values['pixel_values_videos'].view(torch.uint8)), 'First independent two-role flat pixel check')
    require(values['video_grid_thw'].tolist() == [[v['groups'], h, w] for v in plan['videos']],
            'Actual two separate video grids')


def question(source_end, start, end):
    duration = F(end)-F(start)
    display_duration = float(F((duration*1000000).__floor__(), 1000000))
    return (
        'Create a concise visual summary of the whole source video. You see two silent sparse views '
        'of the SAME source: Overview samples the whole source; Excerpt samples only the current '
        'interval. These sampled views do not show continuous motion. Use the Overview to judge '
        'which Excerpt content belongs in a representative whole-source summary, avoiding redundant '
        'content. Do not infer unobserved audio. Select only intervals from the Excerpt, not Overview. '
        'All, some, or none of the Excerpt can be included. An empty selection means the Excerpt is '
        'not chosen for this source summary; it does NOT assert there are no worthwhile events. '
        'Source duration %.6f seconds; Excerpt source interval [%.6f,%.6f) seconds. '
        'Overview timestamps are source-global; Excerpt timestamps and output coordinates are '
        'Excerpt-local, starting at zero. Reply ONLY with a JSON object '
        '{"segments":[[start,end],...]}, containing 0 to 6 ordered, non-overlapping intervals. '
        'Use seconds, 0 <= start < end <= %.6f. No explanation.\n'
    ) % (float(F(source_end)), float(F(start)), float(F(end)), display_duration)


def build_text(processor, plan, grid, source_end):
    prompt = question(source_end, plan['window_start_exact'], plan['window_end_exact'])
    content = [dict(type='text', text=prompt+'Overview:\n'), dict(type='video'),
               dict(type='text', text='\nExcerpt:\n'), dict(type='video')]
    raw = processor.apply_chat_template([dict(role='user', content=content)], tokenize=False,
                                         add_generation_prompt=True, enable_thinking=False)
    marker = processor.vision_start_token+processor.video_token+processor.vision_end_token
    parts = raw.split(marker); require(len(parts) == 3, 'Exactly two source-owned videos')
    text = parts[0]
    for index, (video, (_, h, w)) in enumerate(zip(plan['videos'], grid.tolist())):
        text += ''.join('<%.1f seconds>' % float(F(t)) + processor.vision_start_token +
                       processor.video_token*(h*w//4) + processor.vision_end_token
                       for t in video['group_timestamps_exact']) + parts[index+1]
    enc = processor.tokenizer(text, return_tensors='pt', add_special_tokens=False, truncation=False)
    encoded = {k: enc[k].contiguous() for k in ('input_ids', 'attention_mask')}
    require(encoded['input_ids'].shape[1]+MAX_ANSWER_TOKENS <= MAX_SEQUENCE_TOKENS,
            'Actual input+answer exceeds budget; no truncation allowed')
    vid = processor.tokenizer.convert_tokens_to_ids(processor.video_token)
    require(int((encoded['input_ids'] == vid).sum()) == sum(t*h*w//4 for t,h,w in grid.tolist()),
            'Actual two-video token count differs from grid')
    return encoded, dict(prompt=prompt, raw_template=raw, expanded_text=text,
        prefix_tokens=int(encoded['input_ids'].shape[1]), video_token_id=vid,
        max_answer_tokens=MAX_ANSWER_TOKENS, max_sequence_tokens=MAX_SEQUENCE_TOKENS)


def independent_text(processor, plan, values, metadata):
    original = processor.video_processor
    class AdoptedVideos:
        merge_size = original.merge_size
        model_input_names = original.model_input_names
        def __call__(self, *args, **kwargs):
            return dict(pixel_values_videos=values['pixel_values_videos'], video_grid_thw=values['video_grid_thw'],
                video_metadata=[SimpleNamespace(fps=2, frames_indices=list(range(v['observations']))) for v in plan['videos']])
    with patch.object(processor, 'video_processor', AdoptedVideos()), patch.object(processor,
            '_calculate_timestamps', side_effect=[[float(F(t)) for t in v['group_timestamps_exact']]
                                                 for v in plan['videos']]) as calculate:
        actual = processor(text=[metadata['raw_template']], videos=[object(), object()],
                           return_tensors='pt', padding=False, add_special_tokens=False, truncation=False)
    require(calculate.call_count == 2 and all(torch.equal(actual[k], values[k])
            for k in ('input_ids','attention_mask','video_grid_thw','pixel_values_videos')),
            'First independent pinned processor-stub expansion differs')


def training_suffix(tokenizer, metadata, prefix_ids, answer):
    # Actual token boundary is checked, not inferred by answer length subtraction.
    text = metadata['expanded_text']; stop = '<|im_end|>'
    full = tokenizer.encode(text+answer+stop, add_special_tokens=False)
    prefix = prefix_ids[0].tolist()
    require(full[:len(prefix)] == prefix and len(full) > len(prefix), 'Actual assistant prefix boundary changed')
    suffix = full[len(prefix):]; eos = tokenizer.convert_tokens_to_ids(stop)
    require(suffix[-1] == eos and len(suffix) <= MAX_ANSWER_TOKENS,
            'Complete answer+EOS exceeds registered output budget')
    require(tokenizer.decode(suffix[:-1], skip_special_tokens=False) == answer,
            'Exact target JSON token roundtrip')
    return suffix


def parse_answer(text, duration):
    """Execution failure/invalid output is never converted to a valid empty answer."""
    value = json.loads(text)
    require(isinstance(value, dict) and set(value) == {'segments'} and isinstance(value['segments'], list)
            and len(value['segments']) <= MAX_SEGMENTS, 'Exact source-summary output schema')
    previous = F(0); result = []
    for pair in value['segments']:
        require(isinstance(pair, list) and len(pair) == 2 and all(type(v) in (int,float) for v in pair),
                'Numeric segment pair required')
        a,b = map(lambda v:F(str(v)), pair)
        require(previous <= a < b <= F(duration), 'Unordered/overlapping/out-of-domain output')
        result.append((a,b)); previous = b
    return result
