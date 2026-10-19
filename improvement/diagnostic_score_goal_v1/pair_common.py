"""Bindings for one explicitly registered two-video preference experiment."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys

WORK = Path('/home/inspur/aic_video_work')
RUN = WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PYTHON = WORK/'env/qwen3vl_isolated_20260910/bin/python'
OLD = WORK/'temporal_selector_20261018_v1'


def require(value, message):
    if not value:
        raise ValueError(message)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def bound(reference):
    path = Path(reference['path']).resolve()
    require(path.is_relative_to(WORK) and path.is_file(), 'Real file outside authorized Linux work root')
    require(sha(path) == reference['sha256'], 'Bound original file bytes changed: '+str(path))
    return path


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def append_event(path, **row):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(utc=utc(), **row), ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())


def signature(values):
    import torch
    return {name: dict(shape=list(t.shape), dtype=str(t.dtype),
            sha256=hashlib.sha256(t.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
            for name, t in values.items()}


def paths():
    sys.path[:0] = [str(RUN/'b_score_aligned_package_v4'), str(RUN/'baseline_a_pts_v1'),
                   str(RUN/'baseline_a_pts_v1/vendor'), str(RUN/'temporal_sft8b_v1')]


def registration(root):
    reg = read(root/'pair_registration_17.json')
    require(reg['schema'] == 'TWO_VIDEO_HUMAN_SUMMARY_PREFERENCE_SFT_SINGLE_VERSION', 'Explicit new pair registration')
    for name, digest in reg['new_code'].items():
        require(sha(root/'pair_code_17'/name) == digest, 'Frozen pair runtime changed: '+name)
    for reference in reg['old_helpers']:
        bound(reference)
    return reg


class PairInputs:
    """Adopt accepted image patches; new paired input integrity, no decoding."""
    def __init__(self, root):
        import torch
        self.root = root
        self.reg = registration(root)
        gate = read(root/'pair_inputs_17/input_acceptance.json')
        require(gate['status'] == 'PASS_ALL_NEW_TWO_VIDEO_PREFERENCE_CPU_INPUTS', 'All first real input QA before GPU')
        self.prepared = read(bound(gate['prepared']))
        catalog = read(bound(self.prepared['source_catalog']))
        self.sources = {s['id']: s for s in catalog['sources']}
        self.cache = {}
        sys.path.insert(0, str(OLD/'code'))
        from data import source_pixels
        self.source_pixels = source_pixels

    def get(self, reference):
        import torch
        from pair_video_input import pair_video_pixels
        request = read(bound(reference)); sid = request['source_id']
        source = self.sources[sid]
        require(request['source_sha256'] == source['source_sha256'], 'New paired input source identity')
        if sid not in self.cache:
            frames, grid, ordinals = self.source_pixels(source)
            clock = read(bound(source['clock']))
            require(clock['source_sha256'] == source['source_sha256'], 'Native clock/source identity')
            self.cache[sid] = frames, grid, ordinals, clock['normalized_exact_pts']
        frames, grid, ordinals, pts = self.cache[sid]
        pair = pair_video_pixels(frames, grid, request['clip_ranges'], ordinals, pts)
        tokens = torch.load(bound(request['tokens']), map_location='cpu', weights_only=True)
        values = dict(**tokens, pixel_values_videos=pair['pixel_values_videos'], video_grid_thw=pair['video_grid_thw'])
        require(signature(values) == request['input_signature'] and
                values['video_grid_thw'].tolist() == request['video_grid_thw'],
                'Actual newly paired CPU values differ from first independent input QA')
        require(values['input_ids'].shape[0] == 1 and values['input_ids'].shape[1] <= 4096 and
                len(request['class_token_ids']) == len(set(request['class_token_ids'])) == 3,
                'Actual two-video token budget and three distinct classes')
        return values, request
