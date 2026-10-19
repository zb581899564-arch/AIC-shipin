"""Global/local automatic exploration contracts; importing this module runs nothing."""
import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
import traceback

SCHEMA = 'GLOBAL_LOCAL_BINARY_CONTEXT_EXPLORATION_V1'
ADOPTED = '/home/inspur/aic_video_work/semantic_context_production_20261016_v1'
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
BASELINE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
IDS = [str(i) for i in range(426)]
QUESTION = (
    'Inspect only visible evidence in this silent video. The global reference images cover the whole source; '
    'the local targets are the only frames you must judge. A neighboring or global-reference highlight cannot '
    'supply evidence missing in a target itself. Do not infer sound, unseen actions, intentions or outcomes.\n'
    'For each target, answer global_highlight: does the target itself show distinctive, meaningful visual '
    'highlight evidence when considered in the whole-video context? Exclude ordinary transitions, idle '
    'repetition and repeated background.\n'
    'For each target, also answer event_payoff: does the target itself visibly show a clear action completion, '
    'key reaction or informative reveal? Ordinary movement or setup alone is insufficient; an adjacent '
    'highlight cannot justify this target.\n'
)
REQUIRED_CONTROLS = dict(source_ids=IDS, global_anchor_count=8, local_target_count=8,
    max_input_tokens=8192, gpu_resident_parameters=8782459120,
    complete_reproduction_parameters=8782557449, adapter_role='BASE_DISABLE_TIME144',
    new_image_processors=0, new_decoders=0)


def require(ok, reason):
    if not ok: raise ValueError(reason)


def utc(): return datetime.now(timezone.utc).isoformat()


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''): h.update(block)
    return h.hexdigest()


def binding(path): return dict(path=str(Path(path).resolve()), sha256=sha(path))


def bound(ref):
    require(set(ref) == {'path', 'sha256'} and sha(ref['path']) == ref['sha256'], 'Changed bound file: '+str(ref))
    return Path(ref['path'])


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def save_tensor(path, value):
    import torch
    with Path(path).open('xb') as stream:
        torch.save(value, stream); stream.flush(); os.fsync(stream.fileno())


def event(root, stage, **values):
    row = dict(utc=utc(), stage=stage, **values)
    with (root/'journal.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())
    print(json.dumps(row, ensure_ascii=False), flush=True)


def checked_protocol(root):
    root = Path(root).resolve(strict=True); protocol = read(root/'protocol.json')
    require(protocol['schema'] == SCHEMA and protocol['adopted_root'] == ADOPTED, 'Registered schema/adopted root')
    for key, value in REQUIRED_CONTROLS.items():
        require(protocol['controls'][key] == value, 'Frozen control differs: '+key)
    require(isinstance(protocol['budget'], dict) and protocol['budget'], 'Explicit controller budget required')
    require(protocol['current_baseline']['sha256'] == BASELINE_SHA, 'Current40.47 baseline identity')
    bound(protocol['current_baseline']); bound(protocol['frozen_model_config'])
    require(Path(protocol['frozen_model_config']['path']) == RUN/'b_score_aligned_package_v4/config.json', 'Original B engine config')
    require(Path(protocol['adopted_cpu_acceptance']['path']) == Path(ADOPTED)/'cpu_acceptance.json', 'CPU acceptance path')
    require(Path(protocol['adopted_metadata']['path']) == Path(ADOPTED)/'metadata.json', 'Adopted metadata path')
    accepted = read(bound(protocol['adopted_cpu_acceptance']))
    metadata = read(bound(protocol['adopted_metadata']))
    require(accepted['status'] == 'PASS_ALL_REGISTERED_NEW_FEATURE_INPUTS', 'Prior successful actual CPU inputs required')
    sources = sorted(accepted['sources'], key=lambda v: int(v['id']))
    require([s['id'] for s in sources] == IDS and len(sources) == 426, 'Exact source IDs0..425')
    require(sorted((m['video_id'] for m in metadata['records']), key=int) == IDS, 'Exact metadata IDs')
    require(sum(s['feature_cells'] for s in sources) == accepted['total_cells'], 'Complete source cells denominator')
    return root, protocol, sources


def anchors(count):
    """Uniform linspace(0,n-1,min(8,n)), exact round-half-to-even, stable dedup."""
    require(type(count) is int and count > 0, 'Positive source cell count')
    size = min(8, count)
    if size == 1: return [0]
    return list(dict.fromkeys(round(F(i*(count-1), size-1)) for i in range(size)))


def tensor_fingerprint(tensor):
    value = tensor.detach().cpu().contiguous()
    raw = value.view(__import__('torch').uint8).numpy().tobytes()
    return dict(dtype=str(value.dtype), shape=list(value.shape), sha256=hashlib.sha256(raw).hexdigest())


def effective_input(tensors):
    require(set(tensors) == {'input_ids','attention_mask','pixel_values','image_grid_thw'}, 'Exact actual input keys')
    proof = {key: tensor_fingerprint(tensors[key]) for key in sorted(tensors)}
    key = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return key, proof  # No source/case identity enters the effective key.


def checked_source(source):
    import numpy as np
    sid = source['id']; directory = Path(ADOPTED)/'inputs'/sid
    require(read(directory/'acceptance.json') == source and source['status'] == 'PASS_FIRST_NEW_IMAGE_CPU_INPUTS', 'Prior source success identity')
    require(sha(directory/'native.npz') == source['native_sha256'] and sha(directory/'clock.json') == source['clock_sha256'], 'Native/clock SHA')
    clock = read(directory/'clock.json'); pts = list(map(F, clock['normalized_exact_pts']))
    native = np.load(directory/'native.npz', allow_pickle=False)
    groups = native['groups']; ordinals = native['sample_ordinals'].tolist()
    require(len(pts) == len(groups) and len(ordinals) == source['feature_cells'] > 0 and
            ordinals == sorted(set(ordinals)) and all(0 <= o < len(pts) for o in ordinals), 'Actual native target identity')
    require(all(y > x for x,y in zip(pts, pts[1:])) and
            groups.dtype.kind in 'iu' and groups.min() == 0 and groups.max() == len(ordinals)-1 and
            np.array_equal(np.unique(groups), np.arange(len(ordinals))) and
            all(int(groups[o]) == i for i,o in enumerate(ordinals)), 'Complete native ordinal-to-cell mapping')
    require([o for c in source['chunks'] for o in c['samples']] == ordinals, 'Accepted chunk sample order')
    refs = []
    for chunk in source['chunks']:
        require(1 <= len(chunk['samples']) <= 8 and len(chunk['grid']) == len(chunk['samples']), 'Old chunk cardinality')
        offset = 0
        for image_index, (ordinal, grid) in enumerate(zip(chunk['samples'], chunk['grid'])):
            require(len(grid) == 3 and grid[0] == 1 and all(type(v) is int and v > 0 for v in grid) and math.prod(grid) % 4 == 0, 'Original image grid/merge')
            end = offset + math.prod(grid)
            refs.append(dict(cell_index=len(refs), ordinal=ordinal, exact_pts=str(pts[ordinal]),
                old_chunk=dict(chunk), image_index=image_index, pixel_slice=[offset,end], grid=grid))
            offset = end
        require(offset == chunk['pixel_shape'][0], 'Old chunk grid/pixel rows')
    return refs, pts, groups


class ChunkCache:
    """Bound CPU payload LRU. Reuses processed images, never calls a processor."""
    def __init__(self, limit=16): self.limit = limit; self.values = OrderedDict()

    def load(self, chunk):
        import torch
        path = Path(chunk['path']); identity = (str(path), chunk['sha256'])
        stat = path.stat(); stamp = (stat.st_size, stat.st_mtime_ns)
        if identity in self.values:
            old_stamp, value = self.values.pop(identity)
            require(old_stamp == stamp, 'Cached original chunk changed during phase')
            self.values[identity] = (stamp, value); return value
        require(sha(path) == chunk['sha256'], 'Original image chunk SHA differs')
        value = torch.load(path, map_location='cpu', weights_only=True)
        pix, grid = value['pixel_values'], value['image_grid_thw']
        require(set(value) == {'pixel_values','image_grid_thw','sample_ordinals'} and
                value['sample_ordinals'] == chunk['samples'] and grid.tolist() == chunk['grid'] and
                list(pix.shape) == chunk['pixel_shape'] and pix.ndim == 2 and grid.dtype == torch.int64 and
                pix.device.type == grid.device.type == 'cpu', 'Actual adopted chunk contents/grid/order')
        require(hashlib.sha256(pix.contiguous().numpy().tobytes()).hexdigest() == chunk['pixel_sha256'], 'Original accepted pixel bytes differ')
        self.values[identity] = (stamp, value)
        if len(self.values) > self.limit: self.values.popitem(last=False)
        return value


def compose(refs, cache):
    import torch
    pixels, grids = [], []
    require(1 <= len(refs) <= 16 and [r['ordinal'] for r in refs] == sorted(set(r['ordinal'] for r in refs)), 'Unique ordinal-ordered physical images')
    for ref in refs:
        original = cache.load(ref['old_chunk']); index = ref['image_index']
        grid = original['image_grid_thw'][index]
        lengths = original['image_grid_thw'].prod(dim=1).tolist()
        start = sum(lengths[:index]); end = start+lengths[index]
        require(ref['pixel_slice'] == [start,end] and grid.tolist() == ref['grid'] and
                original['sample_ordinals'][index] == ref['ordinal'], 'Independent per-image tensor slice/native mapping')
        pixels.append(original['pixel_values'][start:end]); grids.append(grid)
    return dict(pixel_values=torch.cat(pixels, dim=0).contiguous(), image_grid_thw=torch.stack(grids).contiguous())


def case_mapping(refs, local_indices, anchor_indices):
    indices = sorted(set(local_indices) | set(anchor_indices))
    images = [refs[i] for i in indices]; positions = {cell:i+1 for i,cell in enumerate(indices)}
    targets = [dict(target_index=j+1, cell_index=i, ordinal=refs[i]['ordinal'],
                    image_index=positions[i], exact_pts=refs[i]['exact_pts']) for j,i in enumerate(local_indices)]
    return images, targets, [positions[i] for i in anchor_indices]


def prompt_content(images, targets, global_positions):
    content = [dict(type='text', text=QUESTION)]
    for i, ref in enumerate(images, 1):
        tag = 'global reference' if i in global_positions else 'local image'
        content.extend([dict(type='text', text='Image %d, native ordinal %d, exact PTS %ss (%.3fs), %s.\n' %
            (i, ref['ordinal'], ref['exact_pts'], float(F(ref['exact_pts'])), tag)), dict(type='image')])
    lines = ['Target %d -> image %d, native ordinal %d, exact PTS %ss.' %
        (t['target_index'],t['image_index'],t['ordinal'],t['exact_pts']) for t in targets]
    k = len(targets)
    content.append(dict(type='text', text='\n'.join(lines)+'\nJudge only these %d targets in this order. '
        'Output exactly %d binary digits separated by one ASCII space: first the %d global_highlight answers, '
        'then the %d event_payoff answers in the same target order. Use 1 for yes and 0 for no. '
        'No prose, labels, punctuation, newline or extra digits.' % (k, 2*k, k, k)))
    return content


def render_text(processor, images, targets, global_positions):
    text = processor.apply_chat_template([dict(role='user', content=prompt_content(images, targets, global_positions))],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    require(text.count('<|image_pad|>') == len(images), 'One image placeholder per physical image')
    for ref in images:
        text = text.replace('<|image_pad|>', '<|global_local_placeholder|>'*(math.prod(ref['grid'])//4), 1)
    return text.replace('<|global_local_placeholder|>', '<|image_pad|>')


def grammar_spec(tokenizer):
    ids = {}
    for key, word in [('zero','0'),('one','1'),('space',' ')]:
        encoded = tokenizer.encode(word, add_special_tokens=False)
        require(len(encoded) == 1 and tokenizer.decode(encoded, clean_up_tokenization_spaces=False) == word, 'Exact single binary/space token required')
        ids[key] = encoded[0]
    ids['eos'] = tokenizer.eos_token_id
    require(all(type(v) is int and v >= 0 for v in ids.values()) and len(set(ids.values())) == 4, 'Four distinct grammar token IDs')
    for k in range(1,9):
        for bits in ([0]*(2*k), [1]*(2*k), [i%2 for i in range(2*k)]):
            raw = ' '.join(map(str,bits)); expected = []
            for i,bit in enumerate(bits):
                if i: expected.append(ids['space'])
                expected.append(ids['one'] if bit else ids['zero'])
            require(tokenizer.encode(raw, add_special_tokens=False) == expected and
                    tokenizer.decode(expected, clean_up_tokenization_spaces=False) == raw, 'Exact full2K token text identity')
    return ids


def allowed_tokens(position, k, grammar):
    require(type(k) is int and 1 <= k <= 8 and 0 <= position <= 4*k-1, 'Binary grammar generated position')
    if position == 4*k-1: return [grammar['eos']]
    return [grammar['zero'],grammar['one']] if position % 2 == 0 else [grammar['space']]


def parse_output(tokens, k, grammar, raw):
    require(len(tokens) == 4*k and all(v in allowed_tokens(i,k,grammar) for i,v in enumerate(tokens)), 'Exact generated2K grammar/EOS length')
    parts = raw.split(' ')
    require(len(parts) == 2*k and all(v in ('0','1') for v in parts) and ' '.join(parts) == raw, 'Strict2K binary text')
    require([grammar['one'] if p=='1' else grammar['zero'] for p in parts] == tokens[:-1:2], 'Raw/token binary equality')
    return list(map(int,parts[:k])), list(map(int,parts[k:]))


def checked_manifest(root):
    manifest = read(root/'input_manifest.json')
    require(manifest['status'] == 'PASS_ALL426_NEW_GLOBAL_LOCAL_INPUTS' and
            manifest['protocol_sha256'] == sha(root/'protocol.json') and
            [s['id'] for s in manifest['sources']] == IDS, 'Actual full426 query manifest')
    return manifest


def run_phase(functions):
    parser = argparse.ArgumentParser(); parser.add_argument('--root', required=True)
    parser.add_argument('--phase', required=True, choices=functions)
    args = parser.parse_args(); root = Path(args.root).resolve(strict=True)
    try: functions[args.phase](root)
    except BaseException as exc:
        failure = root/('failure_%s_%s_%s.json' % (args.phase, os.getpid(), datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')))
        write(failure, dict(phase=args.phase, utc=utc(), error=repr(exc), traceback=traceback.format_exc(), failure_to_zero=False))
        raise
