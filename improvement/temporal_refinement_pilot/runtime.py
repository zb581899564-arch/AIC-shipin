"""Reuse the exact B model, original empty-capable prompt and native processor."""
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN/'b_score_aligned_package_v4'))
import engine as b_engine
from contracts import EMPTY_PROMPT, parse_segments
sys.path.insert(0, str(RUN/'balanced_two_window_risk_v3'))
from bw_video import encode as video_encode, identity as video_identity
from exact_pts import exact_native_pts, verify_native_encoding
from native_frames import prepare_native_processor_input


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def text_prompt(processor, text):
    prompt = processor.apply_chat_template([dict(role='user', content=[dict(type='text', text=text)])],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    if prompt.count('<|im_start|>user\n') != 1:
        raise ValueError('unexpected fixed chat template')
    return prompt.replace('<|im_start|>user\n', '<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>', 1)


def tensor_signature(encoded):
    import torch
    return {k: dict(shape=list(v.shape), dtype=str(v.dtype),
        sha256=hashlib.sha256(v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
        for k, v in encoded.items() if hasattr(v, 'shape')}


def baseline_frames(meta):
    import numpy as np
    if sha(meta['frame_array_path']) != meta['frame_array_sha256']:
        raise ValueError('accepted cached native frames changed')
    with np.load(meta['frame_array_path'], allow_pickle=False) as archive:
        arr = archive['rgb']
    if len(arr) != 64 or [hashlib.sha256(a.tobytes()).hexdigest() for a in arr] != meta['pixel_sha256']:
        raise ValueError('native64 RGB differs from accepted preparation')
    return arr, meta['source_frame_ordinals'], meta['sample_exact_pts']


def context_frames(meta, ordinals):
    import av
    import numpy as np
    wanted = set(ordinals)
    arr = []
    with av.open(meta['source_path']) as container:
        if len(container.streams.video) != 1:
            raise ValueError('ambiguous source stream')
        st = container.streams.video[0]
        if (st.average_rate.numerator, st.average_rate.denominator) != (meta['fps_num'], meta['fps_den']):
            raise ValueError('context rate changed')
        for ordinal, frame in enumerate(container.decode(st)):
            if ordinal in wanted:
                if frame.pts is None or frame.time_base is None or str(Fraction(frame.pts)*frame.time_base) != meta['all_source_exact_pts'][ordinal]:
                    raise ValueError('context native PTS changed')
                image = frame.to_ndarray(format='rgb24')
                if image.shape != (meta['height'], meta['width'], 3):
                    raise ValueError('context RGB geometry changed')
                arr.append(image)
            if ordinal >= ordinals[-1]:
                break
    if len(arr) != len(ordinals):
        raise ValueError('context frame missing')
    return np.stack(arr), ordinals, [meta['all_source_exact_pts'][i] for i in ordinals]


def encode(processor, meta, frames, source_start, text):
    import torch
    arr, ordinals, exact = frames
    plan = dict(source_frame_ids=ordinals, source_relative_pts=[float(Fraction(x)) for x in exact], window_start=float(source_start))
    metadata = dict(fps=meta['fps_num']/meta['fps_den'], frames_indices=ordinals,
        total_num_frames=meta['source_total_frames'], video_backend='pyav')
    physical_count = len(arr)
    pixels = [hashlib.sha256(a.tobytes()).hexdigest() for a in arr]
    arr, metadata = prepare_native_processor_input(arr, metadata, plan)
    with exact_native_pts(processor, plan, metadata['fps']) as native:
        encoded = video_encode(processor, text=[text_prompt(processor, text)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata], max_input=16384)
        verify_native_encoding(processor, encoded, native)
    evidence = dict(case_id=meta['case_id'], source_sha256=meta['source_sha256'], source_start=str(source_start),
        source_frame_ordinals=ordinals, sample_exact_pts=exact, pixel_sha256=pixels,
        native_processor_identity=native, **video_identity(processor, encoded, len(arr)),
        physical_frames=physical_count, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        tensor_signature=tensor_signature(encoded))
    return encoded, evidence


REFINEMENT_PROMPT = '''You are reviewing a proposed highlight from a silent short video. Candidate intervals (in seconds from this CONTEXT clip's start) are {candidates}.
Use the visible action sequence to keep its distinctive core action and meaningful visible result; remove redundant waiting, repetitive preparation, uneventful transitions or duplicated material only when the visual evidence is clear. A person speaking without audio is not evidence of an unimportant moment. Do not invent actions, results or object identities. If the evidence is insufficient to justify removing a candidate, retain that candidate. Refine boundaries around the visible core action and result, rather than keeping the whole context. Only return portions of the supplied candidate intervals; never add a new event outside them.
Return ONLY {{"segments":[[start_sec,end_sec],...]}} using context-local seconds; zero to five sorted, nonoverlapping positive intervals, each within 0..{duration}. An empty list is allowed only if every supplied candidate is clearly visually uneventful. No explanation.'''
