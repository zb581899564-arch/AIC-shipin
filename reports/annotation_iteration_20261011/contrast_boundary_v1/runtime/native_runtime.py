"""Shared sequential native64 encoder for train and both final evaluation arms."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
from pathlib import Path
import sys
from common import require, sha, load, VIDEO_SIZE
from objective import assistant_mask, target


def validate_plan(w):
    ids = w['planned_source_frame_ordinals']; points = list(map(F, w['eligible_exact_pts']))
    a, b = F(w['domain_start_exact']), F(w['domain_end_exact'])
    require(a < b and b-a <= 30 and points and all(a <= p < b for p in points), 'exact domain differs')
    require(all(x < y for x, y in zip(points, points[1:])), 'native PTS not strictly increasing')
    require(len(points) == w['eligible_source_frame_count'], 'eligible PTS denominator differs')
    first = ids[0]; count = len(points)
    expected = list(range(first, first+count)) if count <= 64 else [first+i*(count-1)//63 for i in range(64)]
    require(ids == expected and len(ids) == 64, 'fixed actual native64 floor selection required')
    require(type(w['source_total_frames']) is int and w['source_total_frames'] > ids[-1], 'full source frame denominator differs')
    require(list(map(F, w['planned_exact_pts'])) == [points[i-first] for i in ids], 'sample exact clock differs')
    require(w['planned_actual_pts_sec'] == [float(p) for p in map(F, w['planned_exact_pts'])], 'registered float metadata differs')
    # Exact domains stay authoritative. JSON float fields are one-way IEEE
    # projections, whose decimal repr need not equal the original rational.
    require(w['window_pts_start_sec'] == float(a) and
            w['window_pts_end_exclusive_sec'] == float(b), 'exact/processor domain projection differs')
    require(w['window_duration_sec'] == float(b-a), 'exact/processor duration projection differs')
    return a, b, points


def decode(contract, key):
    # Imports happen only after complete static admission, in an admitted entry.
    import av
    import numpy as np
    w = contract['jobs'][key]['window']; a, b, points = validate_plan(w)
    path = contract['sources'][key]; require(sha(path) == w['source_sha256'], 'source bytes changed')
    stat = path.stat(); ids = w['planned_source_frame_ordinals']
    run = Path(contract['config']['historical_run_root'])
    color = load(run/'teacher_student_autopilot_v14/source_color.py', 'silver_registered_color')
    frames = []; pixels = []; actual = []; observed_eligible = []
    with av.open(str(path)) as container:
        require(len(container.streams.video) == 1, 'ambiguous video stream')
        stream = container.streams.video[0]; rate = stream.average_rate
        require(rate is not None and rate > 0, 'native rate metadata missing')
        wanted = set(ids)
        for ordinal, frame in enumerate(container.decode(stream)):
            require(frame.pts is not None and frame.time_base is not None, 'decoded native PTS missing')
            p = F(frame.pts)*frame.time_base
            if a <= p < b:
                observed_eligible.append(p)
            if ordinal in wanted:
                require(p == F(w['planned_exact_pts'][len(frames)]), 'actual native sample PTS differs')
                image = color.convert_frame(frame, w['source_sha256'], 'rgb24')
                require(image.shape == (w['height'], w['width'], 3), 'RGB geometry differs')
                frames.append(image); actual.append(p); pixels.append(hashlib.sha256(image.tobytes(order='C')).hexdigest())
            if p >= b:
                break
        require(len(frames) == 64 and observed_eligible == points, 'complete native domain or samples differ')
    require((stat.st_size, stat.st_mtime_ns) == (path.stat().st_size, path.stat().st_mtime_ns), 'source changed while decoding')
    arr = np.stack(frames)
    metadata = dict(fps=float(rate), frames_indices=ids, total_num_frames=w['source_total_frames'], video_backend='pyav')
    plan = dict(source_frame_ids=ids, source_relative_pts=list(map(float, actual)), window_start=float(a))
    from native_frames import prepare_native_processor_input
    arr, metadata = prepare_native_processor_input(arr, metadata, plan)
    return arr, metadata, plan, dict(window_id=key, source_sha256=w['source_sha256'], source_frame_ids=ids,
        actual_pts_exact=list(map(str, actual)), eligible_pts_exact=list(map(str, points)), frame_pixel_sha256=pixels)


def prompt(processor):
    from contracts import EMPTY_PROMPT
    text = processor.apply_chat_template([{'role': 'user', 'content': [{'type': 'text', 'text': EMPTY_PROMPT}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    require(text.count('<|im_start|>user\n') == 1, 'original user template boundary differs')
    return text.replace('<|im_start|>user\n', '<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>', 1)


def encode(contract, key, processor, video, training=False):
    import torch
    from exact_pts import exact_native_pts, verify_native_encoding
    arr, metadata, plan, evidence = decode(contract, key)
    head_text = prompt(processor)
    def apply(text, limit):
        with exact_native_pts(processor, plan, metadata['fps']) as native:
            encoded = video.encode(processor, text=[text], videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)],
                video_metadata=[metadata], video_size=VIDEO_SIZE, max_input=limit)
            verify_native_encoding(processor, encoded, native)
        return encoded, native
    head, native = apply(head_text, 16384)
    evidence.update(native_processor_identity=native, processor_identity=video.identity(processor, head, len(arr)))
    # Bound actual reviewed student view, including normalized tensor bytes.
    from common import bound, read
    ref = contract['refs'][key]
    reviewed = read(bound(ref['evidence']['student_processor']))
    pixel_sha = hashlib.sha256(memoryview(head['pixel_values_videos'].detach().cpu().contiguous().numpy()).cast('B')).hexdigest()
    require(reviewed['normalized_tensor_sha256'] == pixel_sha and reviewed['video_grid_thw'] == head['video_grid_thw'].tolist() and
            reviewed['input_tokens'] == int(head['input_ids'].shape[1]), 'actual reviewed student tensor/input differs')
    require(reviewed['evidence']['frame_pixel_sha256'] == evidence['frame_pixel_sha256'] and
            reviewed['evidence']['source_frame_ids'] == evidence['source_frame_ids'], 'reviewed raw frame identity differs')
    evidence['normalized_tensor_sha256'] = pixel_sha
    if not training:
        return head, evidence
    answer, exact = target(ref, contract['jobs'][key]['window'], contract['sidecars'].get(key), contract['reference_sha'][key])
    suffix = answer+'<|im_end|>\n'
    suffix_ids = processor.tokenizer.encode(suffix, add_special_tokens=False)
    end_id = processor.tokenizer.convert_tokens_to_ids('<|im_end|>')
    require(end_id in suffix_ids and len(suffix_ids) <= 256, 'assistant termination/output length differs')
    full, full_native = apply(head_text+suffix, 16384)
    require(full_native == native, 'native identity changed between head and target')
    for k in ('pixel_values_videos', 'video_grid_thw'):
        require(torch.equal(head[k], full[k]), 'target changed video encoding')
    labels = assistant_mask(full['input_ids'][0].tolist(), full['attention_mask'][0].tolist(),
        head['input_ids'][0].tolist(), head['attention_mask'][0].tolist(), suffix_ids, end_id)
    require(processor.tokenizer.decode(suffix_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) == suffix, 'suffix token decoding differs')
    # Keep one causal predecessor logit plus every assistant target. HF shifts once.
    first = next(i for i, x in enumerate(labels) if x != -100)
    keep = len(labels)-first+1
    full['labels'] = torch.tensor([labels[-keep:]], dtype=torch.long)
    full['logits_to_keep'] = keep
    evidence.update(target_json=answer, exact_target_local=exact, assistant_token_ids=suffix_ids,
                    terminator_token_id=end_id, full_input_tokens=len(labels), logits_to_keep=keep)
    return full, evidence


def native_ranges(segments, window):
    a, b, pts = validate_plan(window)
    out = []
    for start, end in segments:
        lo, hi = a+F(start), a+F(end)
        require(a <= lo < hi <= b, 'prediction exact bounds')
        first, stop = bisect_left(pts, lo), bisect_left(pts, hi)
        require(first < stop, 'positive interval has no native source frame')
        out.append([first, stop])
    return out
