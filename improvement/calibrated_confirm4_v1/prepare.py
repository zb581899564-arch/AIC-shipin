"""New CPU inputs and first independent input QA; no labels or GPU entry."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import importlib
import math
from pathlib import Path
import shutil
import sys

import numpy as np
from confirm_common import bound, read, ref, require, save, sha


def _torch(run):
    run.cpu()
    import torch
    torch.set_num_threads(run.c['cpu_threads'])
    require(not torch.cuda.is_initialized(), 'CPU child initialized CUDA')
    return torch


def _capacity(run, needed):
    run.ram.mkdir(parents=True, exist_ok=True)
    available = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    require(needed <= shutil.disk_usage(run.ram).free and needed <= available,
            'Current RAM/tmpfs capacity insufficient for this actual source; never clean existing work')


def _tensor_save(path, value, torch):
    with Path(path).open('xb') as stream:
        torch.save(value, stream)


def _processor(run, video=False):
    from transformers import AutoProcessor
    args = dict(local_files_only=True)
    if video:
        args.update(min_pixels=131072, max_pixels=131072)
    processor = AutoProcessor.from_pretrained(run.model_config()['model_dir'], **args)
    processor.tokenizer.padding_side = 'left'
    if video:
        require(processor.video_processor.size == run.model_config()['video_size'], 'Original native-video profile')
    return processor


def image_grid65(height, width, patch, merge):
    """Independent Qwen smart-resize geometry, including small-image rounding."""
    factor = patch*merge
    require(min(height, width, patch, merge) > 0 and max(height, width)/min(height, width) <= 200,
            'Supported fixed Qwen image geometry')
    resized_h = max(factor, round(height/factor)*factor)
    resized_w = max(factor, round(width/factor)*factor)
    if resized_h*resized_w > 65536:
        beta = math.sqrt(height*width/65536)
        resized_h = math.floor(height/beta/factor)*factor
        resized_w = math.floor(width/beta/factor)*factor
    elif resized_h*resized_w < 65536:
        beta = math.sqrt(65536/(height*width))
        resized_h = math.ceil(height*beta/factor)*factor
        resized_w = math.ceil(width*beta/factor)*factor
    require(resized_h > 0 and resized_w > 0, 'Positive exact resized image grid')
    return [1, resized_h//patch, resized_w//patch]


class _RecordingAV:
    """Preserve already measured PTS even when the unchanged profile rejects."""
    def __init__(self, av):
        self.av = av
        self.observed = dict(frames=[], headers=[])

    def __getattr__(self, name):
        return getattr(self.av, name)

    def open(self, path):
        owner = self
        original = self.av.open(path)
        owner.observed['headers'] = [dict(index=s.index, type=s.type, start_time=s.start_time,
            time_base=None if s.time_base is None else str(s.time_base)) for s in original.streams]
        owner.observed['container_start_time'] = original.start_time

        class Container:
            def __getattr__(self, name):
                return getattr(original, name)

            def __enter__(self):
                original.__enter__()
                return self

            def __exit__(self, *args):
                return original.__exit__(*args)

            def decode(self, stream):
                for frame in original.decode(stream):
                    owner.observed['frames'].append(dict(pts=frame.pts,
                        time_base=None if frame.time_base is None else str(frame.time_base),
                        exact_pts=None if frame.pts is None or frame.time_base is None else str(F(frame.pts)*F(frame.time_base)),
                        duration=getattr(frame, 'duration', None), width=frame.width, height=frame.height))
                    yield frame
        return Container()


def _rgb_pass(run, source, clock, windows, samples):
    import av
    color = run.module('source_color')
    b0_wanted = {i for window in windows for i in window['source_frame_ordinals']}
    context_wanted = set(map(int, samples))
    wanted = b0_wanted | context_wanted
    needed = len(wanted)*clock['width']*clock['height']*3*3
    _capacity(run, needed)
    base_images, context_images = {}, {}
    points = list(map(F, clock['original_exact_pts']))
    with av.open(source['media']['path']) as container:
        stream = container.streams.video[0]
        require(stream.index == clock['video_stream_index'], 'New RGB video stream identity')
        for ordinal, frame in enumerate(container.decode(stream)):
            require(ordinal < len(points) and frame.pts is not None and frame.time_base is not None
                    and F(frame.pts)*F(frame.time_base) == points[ordinal], 'New RGB/source ordinal/exact PTS mismatch')
            if ordinal in b0_wanted:
                base_images[ordinal] = frame.to_ndarray(format='rgb24')
            if ordinal in context_wanted:
                context_images[ordinal] = color.convert_frame(frame, source['media']['sha256'], 'rgb24')
            if ordinal >= max(wanted):
                break
    require(set(base_images) == b0_wanted and set(context_images) == context_wanted, 'All first actual RGB observations')
    return base_images, context_images


def b0_prepare(run):
    torch = _torch(run)
    out = run.begin('b0_prepare')
    import av
    profile = run.module('native_profile_04')
    rt = run.runtime()
    sample_clock = run.module('prepare_v3').sample_clock
    processor = _processor(run, video=True)
    sources, inputs = [], []
    for source in run.sources:
        run.deadline()
        media = bound(source['media'])
        folder = out/source['sid']; folder.mkdir()
        ram = run.ram/source['sid']; ram.mkdir(exist_ok=False)
        if 'clock_ref' in source:
            clock = read(bound(source['clock_ref']))
            require(clock['source_sha256'] == source['media']['sha256'] and clock['source_bytes'] == source['media']['bytes'],
                    'Adopted new native clock must bind this actual media')
        else:
            recorder = _RecordingAV(av)
            try:
                clock = profile.measure_original_video(media, recorder)
            except BaseException as error:
                save(folder/'native_measurement_failure.json', dict(error=repr(error), already_observed=recorder.observed,
                     media_ref=source['media'], complete_native_measurement=False, repeat_success_forbidden=True))
                raise
        clock.update(source_path=str(media), source_sha256=source['media']['sha256'], source_bytes=source['media']['bytes'],
                     normalized_exact_pts=clock['original_exact_pts'], n_frames=clock['native_frames'])
        save(folder/'clock.json', clock)  # Commit measurement before zero-origin admission.
        profile.validate_original_origin(clock)
        require(F(clock['physical_end_exact']) <= F(str(run.c['maximum_source_seconds'])), 'Actual source exceeds fixed metadata duration cap')
        windows = profile.native64_windows(clock)
        groups, samples = sample_clock(clock)
        with (folder/'native.npz').open('xb') as stream:
            np.savez(stream, groups=groups, sample_ordinals=samples)
        base_images, context_images = _rgb_pass(run, source, clock, windows, samples)
        image_path = ram/'context_rgb.npz'
        with image_path.open('xb') as stream:
            np.savez_compressed(stream, ordinals=samples, rgb=np.stack([context_images[int(i)] for i in samples]))
        row = dict(sid=source['sid'], name=source['name'], media_ref=source['media'], clock_ref=ref(folder/'clock.json'),
                   native_ref=ref(folder/'native.npz'), context_rgb_ref=ref(image_path), cells=len(samples), windows=[])
        for window in windows:
            case = source['sid']+'_W%03d'%window['index']
            target = folder/case; target.mkdir()
            rgb_path = ram/(case+'.rgb.npz')
            images = np.stack([base_images[i] for i in window['source_frame_ordinals']])
            with rgb_path.open('xb') as stream:
                np.savez_compressed(stream, rgb=images)
            meta = dict(case_id=case, source_name=source['name'], source_group='NEW_CONFIRM_EXTERNAL',
                source_path=str(media), source_sha256=source['media']['sha256'], source_bytes=source['media']['bytes'],
                source_total_frames=clock['native_frames'], width=clock['width'], height=clock['height'],
                fps_num=clock['fps_num'], fps_den=clock['fps_den'], all_source_exact_pts=clock['original_exact_pts'],
                original_clock_origin_exact='0', window_start=window['start_exact'], window_end=window['end_exact'],
                source_frame_ordinals=window['source_frame_ordinals'], sample_exact_pts=window['sample_exact_pts'],
                pixel_sha256=[hashlib.sha256(a.tobytes()).hexdigest() for a in images],
                frame_array_path=str(rgb_path), frame_array_sha256=sha(rgb_path), audio_observed=False,
                reference_available_to_inference=False)
            save(target/'meta.json', meta)
            encoded, evidence = rt.encode(processor, meta, (images, meta['source_frame_ordinals'], meta['sample_exact_pts']),
                                           F(meta['window_start']), rt.EMPTY_PROMPT)
            require(evidence['physical_frames'] == 64 and len(set(meta['source_frame_ordinals'])) == 64, 'Actual64 unique frames')
            require(set(encoded) == {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'}, 'Original B0 encoded keys')
            _capacity(run, sum(t.numel()*t.element_size() for t in encoded.values()))
            encoded_path = ram/(case+'.b0.pt'); _tensor_save(encoded_path, dict(encoded), torch)
            proof = dict(sid=source['sid'], case_id=case, meta_ref=ref(target/'meta.json'), encoded_ref=ref(encoded_path),
                         input_evidence=evidence, input_tokens=int(encoded['input_ids'].shape[1]))
            save(target/'input.json', proof)
            item = ref(target/'input.json'); inputs.append(item); row['windows'].append(item)
            del encoded, images
        save(folder/'source_completion.json', row); sources.append(row)
        del base_images, context_images
    require(not torch.cuda.is_initialized(), 'CPU preparation initialized CUDA')
    run.finish('b0_prepare', sources=sources, inputs=inputs, expected_calls=len(inputs),
               fresh_clock_measurements=sum('clock_ref' not in source for source in run.sources), new_rgb_decode_passes=len(sources),
               ram_lifecycle='Retain successful task-owned RAM caches; no automatic cleanup/reconstruction')


def b0_input_qa(run):
    torch = _torch(run)
    admission_ref = run.native_admission()  # Can be absent before first preparation, never before GPU admission.
    run.begin('b0_input_qa')
    produced = run.receipt('b0_prepare'); rt = run.runtime(); profile = run.module('native_profile_04')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(run.model_config()['model_dir'], local_files_only=True)
    count = 0
    for source in produced['sources']:
        clock = read(bound(source['clock_ref'])); profile.validate_original_origin(clock)
        expected = profile.native64_windows(clock)
        require(len(expected) == len(source['windows']), 'Independent native64 plan count')
        for item, window in zip(source['windows'], expected):
            proof = read(bound(item)); meta = read(bound(proof['meta_ref']))
            require(meta['source_frame_ordinals'] == window['source_frame_ordinals']
                    and meta['sample_exact_pts'] == window['sample_exact_pts']
                    and meta['window_start'] == window['start_exact'] and meta['window_end'] == window['end_exact'], 'Independent64 exact native plan')
            with np.load(meta['frame_array_path'], allow_pickle=False) as data:
                images = data['rgb']
            require(sha(meta['frame_array_path']) == meta['frame_array_sha256']
                    and [hashlib.sha256(a.tobytes()).hexdigest() for a in images] == meta['pixel_sha256'], 'Independent native RGB bytes')
            encoded = torch.load(bound(proof['encoded_ref']), map_location='cpu', weights_only=True)
            require(rt.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'], 'First serialized B0 tensor replay')
            require(0 < proof['input_tokens'] <= 16384 and encoded['input_ids'].shape[1] == proof['input_tokens']
                    and torch.all(encoded['attention_mask'] == 1), 'Original unpadded B0 token budget')
            text = tok.decode(encoded['input_ids'][0], skip_special_tokens=False, clean_up_tokenization_spaces=False)
            native = proof['input_evidence']['native_processor_identity']
            require(text.count(rt.EMPTY_PROMPT) == 1 and proof['input_evidence']['physical_frames'] == 64
                    and native['source_frame_ids'] == meta['source_frame_ordinals'], 'Independent original prompt/native processor identity')
            require(proof['input_evidence']['sample_exact_pts'] == meta['sample_exact_pts'], 'Independent exact shown PTS')
            count += 1
    require(count == produced['expected_calls'] and not torch.cuda.is_initialized(), 'Complete first B0 input QA')
    run.finish('b0_input_qa', calls=count, producer_ref=ref(run.stage_dir('b0_prepare')/'completion.json'),
               native_admission_ref=admission_ref, new_processor_calls=0)
    run.lock('b0', 'b0_prepare', 'b0_input_qa', count)


def verify_prepare(run):
    torch = _torch(run); out = run.begin('verify_prepare')
    accepted = run.receipt('b0_output_qa'); rt = run.runtime()
    cv, tokens = run.module('cv_contract'), run.module('cv_tokens')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(run.model_config()['model_dir'], local_files_only=True)
    inputs = []
    for window in accepted['windows']:
        proof = read(bound(window['input_ref'])); meta = read(bound(proof['meta_ref']))
        original = torch.load(bound(proof['encoded_ref']), map_location='cpu', weights_only=True)
        for event in window['events']:
            request = cv.request(event, meta); request['prompt'] = cv.prompt(request)
            text, combined, evidence = tokens.retarget(original, tok, rt.EMPTY_PROMPT, request['prompt'], rt.tensor_signature)
            path = run.ram/proof['sid']/(request['request_id']+'.text.pt'); _tensor_save(path, text, torch)
            row = dict(sid=proof['sid'], case_id=request['request_id'], request=request, event=event,
                       b0_input_ref=window['input_ref'], vision_ref=proof['encoded_ref'], text_ref=ref(path),
                       full_signature=rt.tensor_signature(combined), retarget_evidence=evidence)
            target = out/(request['request_id']+'.json'); save(target, row); inputs.append(ref(target))
    run.finish('verify_prepare', inputs=inputs, expected_calls=len(inputs), b0_output_qa_ref=ref(run.stage_dir('b0_output_qa')/'completion.json'),
               new_video_encodes=0, new_media_decodes=0)


def verify_input_qa(run):
    torch = _torch(run); run.begin('verify_input_qa')
    produced = run.receipt('verify_prepare'); rt = run.runtime(); cv = run.module('cv_contract')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(run.model_config()['model_dir'], local_files_only=True)
    ids = []
    for item in produced['inputs']:
        row = read(bound(item)); b0 = read(bound(row['b0_input_ref'])); meta = read(bound(b0['meta_ref']))
        req = cv.request(row['event'], meta); req['prompt'] = cv.prompt(req)
        require(req == row['request'] and row['vision_ref'] == b0['encoded_ref'], 'Original candidate and same B0 vision reference')
        original = torch.load(bound(row['vision_ref']), map_location='cpu', weights_only=True)
        text = torch.load(bound(row['text_ref']), map_location='cpu', weights_only=True)
        vision = {k: original[k] for k in ('pixel_values_videos', 'video_grid_thw')}
        require(rt.tensor_signature({**vision, **text}) == row['full_signature'], 'Independent VERIFY text/vision cache replay')
        require(tok.decode(text['input_ids'][0], skip_special_tokens=False).count(req['prompt']) == 1
                and text['input_ids'].shape[1] <= 16384 and torch.all(text['attention_mask'] == 1), 'Independent VERIFY prompt/token budget')
        require(rt.tensor_signature(vision) == {k: b0['input_evidence']['tensor_signature'][k] for k in vision}, 'Native64 vision retained exactly')
        ids.append(req['request_id'])
    require(len(ids) == len(set(ids)) == produced['expected_calls'] and not torch.cuda.is_initialized(), 'Complete independent VERIFY denominator')
    run.finish('verify_input_qa', calls=len(ids), new_processor_calls=0)
    run.lock('verify', 'verify_prepare', 'verify_input_qa', len(ids))


def context_prepare(run):
    torch = _torch(run); out = run.begin('context_prepare')
    run.receipt('verify_output_qa')
    produced = run.receipt('b0_prepare')
    processor = _processor(run, video=False)  # Never reuse the131072 video factory.
    context_leaf = run.module('prepare_v5'); cases, sources = [], []
    from PIL import Image
    for source in produced['sources']:
        clock = read(bound(source['clock_ref']))
        with np.load(bound(source['native_ref']), allow_pickle=False) as data:
            samples = data['sample_ordinals']
        with np.load(bound(source['context_rgb_ref']), allow_pickle=False) as data:
            require(np.array_equal(data['ordinals'], samples), 'Context actual native sample order')
            images = {int(i): a for i, a in zip(samples, data['rgb'])}
        profile = processor.image_processor(images=[Image.new('RGB', (clock['width'], clock['height']))], return_tensors='pt',
                    size=dict(shortest_edge=65536, longest_edge=65536))
        contract = dict(expected_grid=profile['image_grid_thw'].tolist()[0], processor_dict=processor.image_processor.to_dict(),
                        explicit_size=dict(shortest_edge=65536, longest_edge=65536), patch_size=processor.image_processor.patch_size,
                        merge_size=processor.image_processor.merge_size, independent_video_factory=True,
                        native_geometry=[clock['width'], clock['height']])
        target = out/source['sid']; target.mkdir()
        save(target/'profile.json', contract)
        ram = run.ram/source['sid']/'context65'; ram.mkdir(exist_ok=False)
        new = context_leaf.context_input65(processor, images, samples, clock, ram)
        for case in new:
            require(all(g == contract['expected_grid'] for g in case['grids']), 'Every actual new image uses65K factory')
            case.update(sid=source['sid'], bytes=Path(case['path']).stat().st_size, profile_ref=ref(target/'profile.json'),
                        input_pixel_sha256=[hashlib.sha256(images[i].tobytes()).hexdigest() for i in case['samples']])
            cases.append(case)
        sources.append(dict(sid=source['sid'], cells=len(samples), cases=new, clock_ref=source['clock_ref'], native_ref=source['native_ref'],
                            context_rgb_ref=source['context_rgb_ref']))
    run.finish('context_prepare', inputs=cases, sources=sources, expected_calls=len(cases), expected_queries=sum(c['queries'] for c in cases),
               fresh_image_budget=65536, new_video_encodes=0, media_decodes=0)


def context_input_qa(run):
    torch = _torch(run); run.begin('context_input_qa')
    produced = run.receipt('context_prepare')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(run.model_config()['model_dir'], local_files_only=True)
    imagepad = tok.convert_tokens_to_ids('<|image_pad|>')
    queries = 0
    source_pixels = {}
    for source in produced['sources']:
        with np.load(bound(source['context_rgb_ref']), allow_pickle=False) as rgb:
            source_pixels[source['sid']] = {int(i): hashlib.sha256(a.tobytes()).hexdigest() for i, a in zip(rgb['ordinals'], rgb['rgb'])}
    for case in produced['inputs']:
        contract = read(bound(case['profile_ref']))
        data = torch.load(bound(case), map_location='cpu', weights_only=True)
        ids, mask = data['input_ids'], data['attention_mask']
        grids = data['image_grid_thw'].tolist()
        require(grids == case['grids'] and all(g == contract['expected_grid'] for g in grids), 'Independent persisted image grid profile')
        width, height = contract['native_geometry']
        expected_grid = image_grid65(height, width, contract['patch_size'], contract['merge_size'])
        require(all(g == expected_grid for g in grids), 'Independent65K smart-resize geometry rejects video-factory pollution')
        require(case['input_pixel_sha256'] == [source_pixels[case['sid']][i] for i in case['samples']], 'Independent observed image ordinals/pixel hashes')
        require(ids.shape == mask.shape and ids.shape[0] == case['queries'] and ids.shape[1] <= 4096
                and torch.isfinite(data['pixel_values']).all(), 'Independent image/text shapes and finite pixels')
        expected = [g[0]*g[1]*g[2]//contract['merge_size']**2 for g in grids]
        for target in range(case['queries']):
            row = ids[target][mask[target].bool()].tolist(); lengths, count = [], 0
            for token in row+[None]:
                if token == imagepad:
                    count += 1
                elif count:
                    lengths.append(count); count = 0
            require(lengths == expected and ('Does frame %d depict a visual highlight'%(target+1)) in tok.decode(row),
                    'Independent actual target/image order and expanded token blocks')
        queries += case['queries']
    require(queries == produced['expected_queries'] and not torch.cuda.is_initialized(), 'Full independent context input denominator')
    run.finish('context_input_qa', calls=produced['expected_calls'], queries=queries, new_processor_calls=0)
    run.lock('context', 'context_prepare', 'context_input_qa', produced['expected_calls'])
