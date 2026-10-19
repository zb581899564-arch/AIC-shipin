"""Lossless image-patch reuse and explicit new video/text inputs."""
from collections import OrderedDict
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math
import os
import sys
import time

from common import *
from mapping import pair_image_pixels, window_schedule, group_centers, build_native_groups


def source_catalog(prior):
    accepted = read(prior/'cpu_acceptance.json')
    result = []
    for source in accepted['sources']:
        sid = source['id']
        receipt = prior/'inputs'/sid/'acceptance.json'
        clock = prior/'inputs'/sid/'clock.json'
        native = prior/'inputs'/sid/'native.npz'
        require(sha(clock) == source['clock_sha256'] and sha(native) == source['native_sha256'],
                'Inherited native clock/mapping bytes differ')
        c = read(clock)
        result.append(dict(id=sid, name=source['name'], source_sha256=c['source_sha256'],
                           source_path=c['source_path'], clock=reference(clock), native=reference(native),
                           old_acceptance=reference(receipt), chunks=source['chunks'],
                           feature_cells=source['feature_cells'], native_frames=source['native_frames']))
    require(len(result) == len({x['id'] for x in result}), 'Duplicate source id')
    return result


def source_pixels(source, verify=True):
    import torch
    frames, grids, ordinals = [], [], []
    for chunk in source['chunks']:
        path = Path(chunk['path']).resolve()
        require(path.is_relative_to(WORK) and path.is_file(), 'Existing accepted image chunk missing')
        if verify:
            require(sha(path) == chunk['sha256'], 'Adopted image chunk bytes differ')
        payload = torch.load(path, map_location='cpu', weights_only=True)
        pixels = payload['pixel_values']
        grid = payload['image_grid_thw']
        require(list(pixels.shape) == chunk['pixel_shape'] and grid.tolist() == chunk['grid'],
                'Adopted image tensor/grid mismatch')
        require(payload['sample_ordinals'] == chunk['samples'], 'Adopted native image order differs')
        require(pixels.dtype == torch.float32 and torch.isfinite(pixels).all(), 'Finite original float32 pixels')
        if verify:
            require(tensor_sha(pixels) == chunk['pixel_sha256'], 'Actual inherited image tensor SHA differs')
        offset = 0
        for row in grid.tolist():
            require(row[0] == 1, 'Only already accepted image frames are adopted')
            count = row[1]*row[2]
            frames.append(pixels[offset:offset+count])
            grids.append(row[1:])
            offset += count
        require(offset == len(pixels), 'All actual spatial patches accounted for')
        ordinals.extend(chunk['samples'])
    require(len(frames) == source['feature_cells'] == len(ordinals), 'Complete original observations')
    require(all(x == grids[0] for x in grids), 'A source must have one accepted spatial grid')
    return frames, grids[0], ordinals


def text_input(processor, centers, grid_hw):
    import torch
    # Match the pinned HF Qwen3VL processor's video placeholder presentation,
    # while taking timestamps from exact native PTS rather than assumed CFR FPS.
    content = [dict(type='text', text=PROMPT+'\n'), dict(type='video'),
               dict(type='text', text='Give your assessment of the complete visible sequence.')]
    raw = processor.apply_chat_template([dict(role='user', content=content)], tokenize=False,
                                        add_generation_prompt=True, enable_thinking=False)
    per_group = grid_hw[0]*grid_hw[1]//(processor.video_processor.merge_size**2)
    marker = processor.vision_start_token+processor.video_token+processor.vision_end_token
    require(raw.count(marker) == 1, 'One original video placeholder required')
    expanded = ''.join('<%.1f seconds>' % float(center)+processor.vision_start_token+
                       processor.video_token*per_group+processor.vision_end_token for center in centers)
    text = raw.replace(marker, expanded)
    encoded = processor.tokenizer(text, return_tensors='pt', add_special_tokens=False)
    encoded = {key: encoded[key].contiguous() for key in ('input_ids', 'attention_mask')}
    video_id = processor.tokenizer.convert_tokens_to_ids(processor.video_token)
    positions = (encoded['input_ids'][0] == video_id).nonzero().flatten()
    require(len(positions) == len(centers)*per_group and encoded['input_ids'].shape[1] <= 16384,
            'New actual video token/time-group budget')
    return encoded, dict(video_token_id=video_id, group_token_positions=positions.reshape(len(centers), per_group).tolist(),
                         text_sha256=hashlib.sha256(text.encode()).hexdigest(), raw_template=raw)


def independent_text_check(processor, meta, grid_hw, encoded):
    """Use the processor's own expansion, with cached video pixels stubbed out.

    No actual video processor or old successful encoding is repeated.
    """
    import torch
    from types import SimpleNamespace
    from unittest.mock import patch
    centers = [Fraction(x) for x in meta['relative_group_centers_exact']]
    old_video = processor.video_processor
    class AdoptedVideo:
        merge_size = old_video.merge_size
        model_input_names = old_video.model_input_names
        def __call__(self, *args, **kwargs):
            return dict(video_grid_thw=torch.tensor([[len(centers), *grid_hw]]),
                        video_metadata=[SimpleNamespace(fps=2, frames_indices=list(range(2*len(centers))))])
    with patch.object(processor, 'video_processor', AdoptedVideo()), \
            patch.object(processor, '_calculate_timestamps', return_value=[float(x) for x in centers]):
        actual = processor(text=[meta['raw_template']], videos=[object()], return_tensors='pt',
                           padding=False, add_special_tokens=False)
    require(torch.equal(actual['input_ids'], encoded['input_ids']) and
            torch.equal(actual['attention_mask'], encoded['attention_mask']),
            'Independent pinned processor text expansion differs')


def synthetic_processor_check(processor):
    import numpy as np
    import torch
    from PIL import Image
    patch = int(processor.video_processor.patch_size)
    temporal = int(processor.video_processor.temporal_patch_size)
    require(patch == 16 and temporal == 2 and processor.video_processor.merge_size == 2,
            'Measured processor dimensions must match the registered pairing implementation')
    array = np.random.default_rng(105).integers(0, 256, (5, 192, 288, 3), dtype=np.uint8)
    images = processor.image_processor(images=[Image.fromarray(x) for x in array],
                                       do_resize=False, return_tensors='pt')
    frames = list(images['pixel_values'].split(12*18))
    outputs = []
    for n in (4, 5):
        paired, grid = pair_image_pixels(frames[:n], [12, 18])
        direct = processor.video_processor(videos=[torch.from_numpy(array[:n]).permute(0,3,1,2)],
                                           do_sample_frames=False, do_resize=False, return_tensors='pt')
        require(torch.equal(paired, direct['pixel_values_videos']) and
                torch.equal(grid.unsqueeze(0), direct['video_grid_thw']),
                'Synthetic lossless pairing differs from actual video processor')
        outputs.append(dict(frames=n, actual_video_grid=grid.tolist(), tensor_sha256=tensor_sha(paired), bit_equal=True))
    return dict(status='PASS_DIRECT_VIDEO_PROCESSOR_BIT_EQUAL_EVEN_AND_ODD', results=outputs,
                original_media_decodes=0, original_successful_encodings_repeated=0)


def prepare(scope):
    assert_cpu()
    import numpy as np
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    protocol = read(ROOT/'protocol.json')
    prior = EXTERNAL if scope == 'external' else PRODUCTION
    sources = source_catalog(prior)
    if scope == 'external':
        annotations = {s['name']: s for s in protocol['external_sources']}
        require({s['name'] for s in sources} == set(annotations), 'Exact historical SumMe25 source set')
        ordered = sorted(sources, key=lambda x: hashlib.sha256(x['source_sha256'].encode()).hexdigest())
        training = {x['id'] for x in ordered[:20]}
        for s in sources:
            s['role'] = 'train' if s['id'] in training else 'dev'
            s['annotation_sha256'] = annotations[s['name']]['annotation_sha256']
    else:
        require({s['id'] for s in sources} == {str(i) for i in range(426)}, 'Complete426 production input set')
        for s in sources:
            s['role'] = 'production_no_labels'
    cfg = read(RUN/'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True)
    destination = ROOT/('inputs_'+scope)
    destination.mkdir(exist_ok=False)
    if scope == 'external':
        write(ROOT/'pairing_processor_acceptance.json', synthetic_processor_check(processor))
    else:
        checked(reference(ROOT/'pairing_processor_acceptance.json'))
    cases = []
    for source in sources:
        one = time.monotonic()
        checked(source['old_acceptance']);checked(source['native']);clock = read(checked(source['clock']))
        require(clock['source_sha256'] == source['source_sha256'] and sha(source['source_path']) == source['source_sha256'],
                'Actual source bytes differ from inherited native clock')
        frames, grid_hw, ordinals = source_pixels(source)
        native = np.load(source['native']['path'])
        require(native['sample_ordinals'].tolist() == ordinals, 'Actual observation/native order mismatch')
        groups = build_native_groups(native['groups'], len(frames))
        out = destination/source['id'];out.mkdir(exist_ok=False)
        native_file = out/'native_groups.npy';np.save(native_file, groups)
        windows = []
        points = [Fraction(x) for x in clock['normalized_exact_pts']]
        require(len(points) == source['native_frames'] and all(b>a for a,b in zip(points,points[1:])),
                'Complete strictly increasing original native clock')
        for index, (start, end) in enumerate(window_schedule(len(frames))):
            cid = source['id']+'_W%04d' % index
            exact_centers = group_centers(ordinals, points, start, end)
            origin = points[ordinals[start]]
            relative = [x-origin for x in exact_centers]
            pixels, grid = pair_image_pixels(frames[start:end], grid_hw)
            tokens, text = text_input(processor, relative, grid_hw)
            group_ids = list(range(start//2, (end+1)//2))
            require(grid.tolist() == [len(group_ids), *grid_hw], 'Measured video grid/time groups mismatch')
            token_path = out/(cid+'.pt');torch.save(tokens, token_path)
            request = dict(case_id=cid, source_id=source['id'], source_sha256=source['source_sha256'],
                           clock_sha256=source['clock']['sha256'], source_start_cell=start, source_end_cell=end,
                           source_ordinals=ordinals[start:end], global_group_ids=group_ids,
                           absolute_group_centers_exact=list(map(str, exact_centers)),
                           relative_group_centers_exact=list(map(str, relative)),
                           raw_template=text.pop('raw_template'), text_evidence=text,
                           tokens=reference(token_path), input_signature=signature(dict(**tokens,
                               pixel_values_videos=pixels, video_grid_thw=grid.unsqueeze(0))),
                           video_grid_thw=grid.tolist(), padded_last_observation=((end-start)%2 == 1),
                           reference_labels_read=False, original_decodes=0, original_processor_calls=0)
            independent_text_check(processor, request, grid_hw, tokens)
            # Independent structural and native ownership checks before any GPU.
            require(len(request['source_ordinals']) == end-start and
                    len(group_ids) == len(request['absolute_group_centers_exact']), 'Actual observed endpoint mapping')
            path = out/(cid+'.json');write(path, request)
            row = dict(case_id=cid, source_id=source['id'], request=reference(path),
                       source_start_cell=start, source_end_cell=end, global_group_ids=group_ids)
            windows.append(row);cases.append(row)
        source['native_groups'] = reference(native_file)
        source['windows'] = windows
        source['temporal_groups'] = (source['feature_cells']+1)//2
        event('SOURCE_NEW_VIDEO_INPUT_AND_FIRST_QA_ACCEPTED',scope=scope,source_id=source['id'],
              observations=len(frames),windows=len(windows),groups=source['temporal_groups'],seconds=time.monotonic()-one)
        del frames, native, pixels
    pilot = []
    if scope == 'external':
        for s in sorted(sources,key=lambda x:hashlib.sha256(x['source_sha256'].encode()).hexdigest()):
            pilot.append(min(s['windows'],key=lambda x:hashlib.sha256(x['case_id'].encode()).hexdigest())['case_id'])
        more = sorted([x for x in cases if x['case_id'] not in pilot],key=lambda x:hashlib.sha256(x['case_id'].encode()).hexdigest())
        pilot += [x['case_id'] for x in more[:32-len(pilot)]]
        require(len(pilot)==32 and len(set(pilot))==32, 'Fixed32 source-first hash pilot')
    result = dict(status='PASS_ALL_NEW_VIDEO_INPUTS_AND_FIRST_INDEPENDENT_QA',scope=scope,
                  sources=sources,cases=cases,pilot_case_ids=pilot,source_count=len(sources),window_count=len(cases),
                  original_decodes=0,original_processor_calls=0,reference_labels_read=False,
                  protocol=reference(ROOT/'protocol.json'),pairing_processor_acceptance=reference(ROOT/'pairing_processor_acceptance.json'))
    write(ROOT/('acceptance_'+scope+'.json'),result)
    write(ROOT/('source_lock_'+scope+'.json'),dict(status='FROZEN_NEW_VIDEO_INPUTS_AND_MAPPING',
          acceptance=reference(ROOT/('acceptance_'+scope+'.json')),code=read(ROOT/'code_manifest.json'),
          baseline_sha256=BASELINE_SHA,model_config=reference(RUN/'b_score_aligned_package_v4/config.json'),
          evidence_scope='External SumMe historical summaries, no official labels' if scope=='external' else 'Unlabelled formal inference only'))


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('scope',choices=['external','production'])
    args=parser.parse_args();prepare(args.scope)
