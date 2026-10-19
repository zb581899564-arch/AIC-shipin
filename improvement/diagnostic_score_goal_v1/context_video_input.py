"""Pure Overview/A/B inputs from accepted image patches; no file or model IO.

Each video owns its actual source identity and clock. An explicitly foreign
Overview is a control, never described in evidence as native to the local source.
Old two-video QA is not reused as acceptance for these new three-video inputs.
"""
from __future__ import annotations

import hashlib
from types import SimpleNamespace
from unittest.mock import patch

import torch

import pair_video_input as pair17


QUESTION = pair17.QUESTION
OVERVIEW_NOTE = ('The Overview is context only. Compare Clip A and Clip B; '
                 'do not select or score the Overview itself.\n')
ROLES = ('Overview', 'A', 'B')


def _owner(value):
    pair17.require(isinstance(value, dict) and set(value) == {'source_id', 'source_sha256'}
        and isinstance(value['source_id'], str) and bool(value['source_id'])
        and isinstance(value['source_sha256'], str) and len(value['source_sha256']) == 64
        and all(c in '0123456789abcdef' for c in value['source_sha256']),
        'Explicit original source_id/source_sha256 owner required')
    return dict(value)


def _plan(local_frames, local_grid, clip_ranges, local_ordinals, local_pts,
          overview_frames, overview_grid, overview_ordinals, overview_pts, *,
          local_owner, overview_owner, overview_is_foreign=False,
          local_ref=None, overview_ref=None, pairing_proof_ref=None):
    h, w, local_clips = pair17._plan(local_frames, local_grid, clip_ranges, local_ordinals, local_pts)
    local_owner, overview_owner = _owner(local_owner), _owner(overview_owner)
    pair17.require(type(overview_is_foreign) is bool, 'Foreign-source control must be explicit')
    pair17.require(list(map(pair17._integer, overview_grid)) == [h, w],
                   'Overview control must have the same accepted spatial grid as local clips')
    ordinals = list(map(pair17._integer, overview_ordinals))
    points = list(map(pair17._exact, overview_pts))
    pair17.require(len(overview_frames) == len(ordinals) and ordinals
        and all(a < b for a, b in zip(ordinals, ordinals[1:]))
        and points and points[0] == 0 and all(a < b for a, b in zip(points, points[1:]))
        and 0 <= ordinals[0] <= ordinals[-1] < len(points),
        'Complete original Overview observations and own normalized exact native PTS required')
    count = min(64, len(ordinals)-len(ordinals) % 2)
    pair17.require(count >= 2, 'Overview needs at least two real observations; no padding')
    indices = [i*(len(ordinals)-1)//(count-1) for i in range(count)]
    pair17.require(len(set(indices)) == count and indices[0] == 0 and indices[-1] == len(ordinals)-1,
                   'Overview integer-equidistant even selection must retain both actual endpoints')
    if overview_is_foreign:
        pair17.require(local_owner['source_id'] != overview_owner['source_id']
            and local_owner['source_sha256'] != overview_owner['source_sha256'] and count == 64,
            'Foreign Overview control requires64 actual same-grid observations from a different owner')
    else:
        pair17.require(local_owner == overview_owner
            and ordinals == list(map(pair17._integer, local_ordinals))
            and points == list(map(pair17._exact, local_pts)),
            'True Overview must use the exact full local-source observation list and clock')
    for index in indices:
        frame = overview_frames[index]
        pair17.require(isinstance(frame, torch.Tensor) and frame.device.type == 'cpu'
            and frame.dtype == torch.float32 and frame.layout == torch.strided and not frame.requires_grad
            and frame.shape == (h*w, 1536) and bool(torch.isfinite(frame).all()),
            'Finite detached accepted CPU Overview image patches required')
        view = frame.reshape(h*w, 3, 2, 16, 16)
        pair17.require(pair17._bit_equal(view[:, :, 0], view[:, :, 1]),
                       'Accepted Overview image temporal slices must be bit-identical')
        if not overview_is_foreign:
            pair17.require(pair17._bit_equal(frame, local_frames[index]),
                           'True Overview accepted image patches differ from the actual local source')
    source_refs = dict(local=pair17._proof(local_ref), overview=pair17._proof(overview_ref))
    ids = [ordinals[i] for i in indices]
    times = [points[i] for i in ids]
    centers = [(a+b)/2 for a, b in zip(times[::2], times[1::2])]
    videos = [dict(video_role='Overview', owner=overview_owner, source_ref=source_refs['overview'],
        source_cell_indices=indices, sample_ordinals=ids, sample_exact_pts=list(map(str, times)),
        timestamps_exact=list(map(str, centers)), timestamp_scope='OWN_SOURCE_GLOBAL_NORMALIZED_PTS',
        origin_exact='0', groups=count//2, observations=count, padded_observations=0)]
    for clip in local_clips:
        videos.append(dict(video_role=clip['role'], owner=local_owner, source_ref=source_refs['local'],
            source_cell_indices=list(range(*clip['cell_range_half_open'])), sample_ordinals=clip['sample_ordinals'],
            sample_exact_pts=clip['sample_exact_pts'], timestamps_exact=clip['relative_group_centers_exact'],
            timestamp_scope='OWN_CLIP_LOCAL_NORMALIZED_PTS', origin_exact=clip['origin_exact'],
            absolute_group_centers_exact=clip['absolute_group_centers_exact'],
            global_group_ids=clip['global_group_ids'], groups=4, observations=8, padded_observations=0))
    bindings = []
    for video in videos:
        for index, (cell, ordinal, pts) in enumerate(zip(video['source_cell_indices'], video['sample_ordinals'], video['sample_exact_pts'])):
            bindings.append(dict(video_role=video['video_role'], owner=dict(video['owner']),
                video_group=index//2, temporal_slice=index % 2, source_cell=cell,
                native_ordinal=ordinal, exact_pts=pts))
    return dict(h=h, w=w, videos=videos, bindings=bindings, source_refs=source_refs,
        local_owner=local_owner, overview_owner=overview_owner, overview_is_foreign=overview_is_foreign,
        pairing_proof_ref=pair17._proof(pairing_proof_ref), local_clips=local_clips)


def build_context_pixels(local_frames, local_grid, clip_ranges, local_ordinals, local_pts,
                         overview_frames, overview_grid, overview_ordinals, overview_pts, *,
                         local_owner, overview_owner, overview_is_foreign=False,
                         local_ref=None, overview_ref=None, pairing_proof_ref=None):
    """Return exactly three separate grids: even Overview, local A8, local B8."""
    plan = _plan(local_frames, local_grid, clip_ranges, local_ordinals, local_pts,
        overview_frames, overview_grid, overview_ordinals, overview_pts,
        local_owner=local_owner, overview_owner=overview_owner, overview_is_foreign=overview_is_foreign,
        local_ref=local_ref, overview_ref=overview_ref, pairing_proof_ref=pairing_proof_ref)
    blocks = []; h, w = plan['h'], plan['w']
    for video in plan['videos']:
        frames = overview_frames if video['video_role'] == 'Overview' else local_frames
        cells = video['source_cell_indices']
        for first, second in zip(cells[::2], cells[1::2]):
            a = frames[first].reshape(h*w, 3, 2, 16, 16)[:, :, 0]
            b = frames[second].reshape(h*w, 3, 2, 16, 16)[:, :, 0]
            blocks.append(torch.stack((a, b), dim=2).reshape(h*w, 1536))
    return dict(pixel_values_videos=torch.cat(blocks).contiguous(),
        video_grid_thw=torch.tensor([[v['groups'], h, w] for v in plan['videos']], dtype=torch.int64),
        video_metadata=plan['videos'], sample_bindings=plan['bindings'], source_refs=plan['source_refs'],
        local_owner=plan['local_owner'], overview_owner=plan['overview_owner'],
        overview_is_foreign=overview_is_foreign, local_clip_metadata=plan['local_clips'],
        observation_appearances=len(plan['bindings']),
        distinct_owner_native_observations=len({(b['owner']['source_sha256'], b['native_ordinal']) for b in plan['bindings']}),
        old_synthetic_pairing_proof=plan['pairing_proof_ref'], old_two_video_QA_adopted=False,
        real_processor_calls=0, new_three_video_QA_required=True, input_admitted=False)


def independent_context_pixel_check(local_frames, local_grid, clip_ranges, local_ordinals, local_pts,
                                    overview_frames, overview_grid, overview_ordinals, overview_pts, *, context,
                                    local_owner, overview_owner, overview_is_foreign=False,
                                    local_ref=None, overview_ref=None, pairing_proof_ref=None):
    """Independent flat channel/slice assignment and complete owner/index QA."""
    plan = _plan(local_frames, local_grid, clip_ranges, local_ordinals, local_pts,
        overview_frames, overview_grid, overview_ordinals, overview_pts,
        local_owner=local_owner, overview_owner=overview_owner, overview_is_foreign=overview_is_foreign,
        local_ref=local_ref, overview_ref=overview_ref, pairing_proof_ref=pairing_proof_ref)
    h, w = plan['h'], plan['w']; groups = sum(v['groups'] for v in plan['videos'])
    expected = torch.empty((groups*h*w, 1536), dtype=torch.float32); offset = 0
    for video in plan['videos']:
        frames = overview_frames if video['video_role'] == 'Overview' else local_frames
        cells = video['source_cell_indices']
        for a, b in zip(cells[::2], cells[1::2]):
            target = expected[offset:offset+h*w]
            for channel in range(3):
                column = channel*512
                target[:, column:column+256] = frames[a][:, column:column+256]
                target[:, column+256:column+512] = frames[b][:, column:column+256]
            offset += h*w
    grid = torch.tensor([[v['groups'], h, w] for v in plan['videos']], dtype=torch.int64)
    pair17.require(pair17._bit_equal(expected, context['pixel_values_videos'])
        and context['video_grid_thw'].dtype == torch.int64 and context['video_grid_thw'].device.type == 'cpu'
        and torch.equal(grid, context['video_grid_thw']), 'Independent three-video flat pixels/grid mismatch')
    pair17.require(context['video_metadata'] == plan['videos'] and context['sample_bindings'] == plan['bindings']
        and context['local_owner'] == plan['local_owner'] and context['overview_owner'] == plan['overview_owner']
        and context['overview_is_foreign'] is overview_is_foreign and context['source_refs'] == plan['source_refs'],
        'Independent actual Overview/local owners, native PTS or sample mappings differ')
    return dict(status='PASS_FIRST_THREE_VIDEO_FLAT_PIXEL_SOURCE_INDEX_QA',
                real_processor_calls=0, old_two_video_QA_adopted=False, input_admitted=False)


def _text_plan(processor, context):
    grid = context['video_grid_thw']; videos = context['video_metadata']
    pair17.require(grid.dtype == torch.int64 and grid.device.type == 'cpu' and grid.shape == (3, 3)
        and [v['video_role'] for v in videos] == list(ROLES)
        and 1 <= int(grid[0, 0]) <= 32 and grid[1:, 0].tolist() == [4, 4]
        and processor.video_processor.merge_size == 2, 'Overview/A/B three separate actual video grids required')
    timestamps = []; counts = []
    for video, (t, h, w) in zip(videos, grid.tolist()):
        times = list(map(pair17._exact, video['timestamps_exact']))
        pair17.require(t == video['groups'] == len(times) and h > 0 and w > 0 and h % 2 == w % 2 == 0
            and all(v >= 0 for v in times) and all(a < b for a, b in zip(times, times[1:])),
            'Each video needs its own ordered exact timestamps and merge2 spatial grid')
        timestamps.append(times); counts.append(h*w//4)
    return grid, videos, timestamps, counts


def _classes(tokenizer, text, encoded):
    result = []
    for digit in pair17.DIGITS:
        ids = tokenizer.encode(digit, add_special_tokens=False)
        pair17.require(len(ids) == 1 and type(ids[0]) is int and ids[0] >= 0, 'Actual0/1/2 digits must be one token each')
        full = pair17._tokens(tokenizer, text+digit)['input_ids']
        pair17.require(full.shape[1] == encoded['input_ids'].shape[1]+1
            and torch.equal(full[:, :-1], encoded['input_ids']) and int(full[0, -1]) == ids[0],
            'Each class must be one actual next token after the exact assistant prefix')
        result.append(ids[0])
    pair17.require(len(set(result)) == 3, 'Three distinct actual digit classes required')
    return result


def build_context_text(processor, context):
    """Fixed original question, context-only note, three expansions, final prefix."""
    grid, videos, timestamps, counts = _text_plan(processor, context)
    content = [dict(type='text', text=QUESTION+OVERVIEW_NOTE+'Overview:\n'), dict(type='video'),
               dict(type='text', text='\nA:\n'), dict(type='video'), dict(type='text', text='\nB:\n'), dict(type='video')]
    messages = [dict(role='user', content=content)]; options = dict(tokenize=False, enable_thinking=False)
    raw = processor.apply_chat_template(messages, add_generation_prompt=True, **options)
    plain = processor.apply_chat_template(messages, add_generation_prompt=False, **options)
    pair17.require(isinstance(raw, str) and raw.startswith(plain) and len(raw) > len(plain), 'Final assistant generation prefix required')
    prefix = raw[len(plain):]
    marker = processor.vision_start_token+processor.video_token+processor.vision_end_token
    parts = raw.split(marker)
    pair17.require(len(parts) == 4, 'Exactly three original video markers required')
    text = parts[0]
    for index, (times, count) in enumerate(zip(timestamps, counts)):
        text += ''.join('<%.1f seconds>' % float(t)+processor.vision_start_token+processor.video_token*count+
                        processor.vision_end_token for t in times)+parts[index+1]
    pair17.require(text.endswith(prefix), 'Assistant prefix must be final; no answer prefill')
    encoded = pair17._tokens(processor.tokenizer, text); classes = _classes(processor.tokenizer, text, encoded)
    video_id = processor.tokenizer.convert_tokens_to_ids(processor.video_token)
    pair17.require(type(video_id) is int and video_id >= 0 and video_id not in classes, 'Actual video token identity required')
    positions = (encoded['input_ids'][0] == video_id).nonzero().flatten().tolist()
    pair17.require(len(positions) == sum(v['groups']*count for v, count in zip(videos, counts)),
                   'All three actual video-token counts must match their grids')
    per_video = []; offset = 0
    for video, count in zip(videos, counts):
        groups = [positions[offset+j*count:offset+(j+1)*count] for j in range(video['groups'])]
        pair17.require(all(len(g) == count and g == list(range(g[0], g[0]+count)) for g in groups),
                       'Each actual timegroup must have contiguous video tokens')
        per_video.append(dict(video_role=video['video_role'], group_token_positions=groups)); offset += video['groups']*count
    return encoded, dict(raw_template=raw, expanded_text=text, question=QUESTION, overview_note=OVERVIEW_NOTE,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(), assistant_generation_prefix=prefix,
        next_token_prediction_position=int(encoded['input_ids'].shape[1])-1,
        class_token_ids=classes, class_tokens_by_digit=dict(zip(pair17.DIGITS, classes)), class_digit_order=list(pair17.DIGITS),
        token_evidence=pair17._token_evidence(encoded), video_token_id=video_id, video_token_count=len(positions),
        video_grids=grid.tolist(), video_positions=per_video, sequence_tokens=int(encoded['input_ids'].shape[1]),
        maximum_input_plus_digit_tokens=4096, old_two_video_QA_adopted=False, input_admitted=False)


def independent_context_text_check(processor, context, encoded, metadata):
    """Pinned processor expands three videos; all video pixels are adopted stubs."""
    grid, videos, timestamps, _ = _text_plan(processor, context)
    original = processor.video_processor
    class AdoptedVideos:
        merge_size = original.merge_size
        model_input_names = original.model_input_names

        def __call__(self, *args, **kwargs):
            return dict(pixel_values_videos=context['pixel_values_videos'], video_grid_thw=grid.clone(),
                video_metadata=[SimpleNamespace(fps=2, frames_indices=list(range(v['observations']))) for v in videos])

    with patch.object(processor, 'video_processor', AdoptedVideos()), \
            patch.object(processor, '_calculate_timestamps', side_effect=[[float(t) for t in times] for times in timestamps]) as calculate:
        actual = processor(text=[metadata['raw_template']], videos=[object(), object(), object()], return_tensors='pt',
                           padding=False, add_special_tokens=False, truncation=False)
        pair17.require(calculate.call_count == 3, 'Overview/A/B must each consume its own timestamp sequence exactly once')
    pair17.require(all(torch.equal(actual[k], encoded[k]) for k in ('input_ids', 'attention_mask'))
        and torch.equal(actual['video_grid_thw'], grid)
        and pair17._bit_equal(actual['pixel_values_videos'], context['pixel_values_videos']),
        'Independent first three-video processor-stub text/grid/pixel mismatch')
    classes = _classes(processor.tokenizer, metadata['expanded_text'], encoded)
    pair17.require(metadata['question'] == QUESTION and metadata['overview_note'] == OVERVIEW_NOTE
        and metadata['raw_template'].count(QUESTION) == metadata['raw_template'].count(OVERVIEW_NOTE) == 1
        and metadata['next_token_prediction_position'] == encoded['input_ids'].shape[1]-1
        and metadata['class_token_ids'] == classes == [metadata['class_tokens_by_digit'][d] for d in pair17.DIGITS]
        and metadata['class_digit_order'] == list(pair17.DIGITS)
        and metadata['token_evidence'] == pair17._token_evidence(encoded)
        and metadata['video_grids'] == grid.tolist()
        and metadata['text_sha256'] == hashlib.sha256(metadata['expanded_text'].encode()).hexdigest()
        and metadata['expanded_text'].endswith(metadata['assistant_generation_prefix']),
        'Fixed question, actual class mapping, final prefix or token/grid evidence changed')
    return dict(status='PASS_FIRST_THREE_VIDEO_STUB_PROCESSOR_TEXT_QA', timestamp_sequences=3,
        real_video_processor_calls=0, original_image_processor_calls=0,
        old_two_video_QA_adopted=False, input_admitted=False)
