"""New fixed40 point-covering CPU inputs; no acquisition or implicit recovery.

Execution requires the independently registered complete dev/confirm PASS.
The source audit supplies nine original clocks and exactly seventeen views.
Only this CPU child hides CUDA; model inference and first replay are separate.
"""
import argparse
from collections.abc import Mapping
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import traceback

import facts_common as io
import source_audit

GROUP = 'facts'
PREP_STATUS = 'PASS_FIXED40_NEW_NATIVE64_CPU_CACHES_NOT_GPU_ADMISSION'
SCOPE = 'FULL_ORIGINAL_SOURCE_ZERO_ORIGIN_15_STRIDE7_5'


def safe_id(value):
    io.require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', value) and
               value not in ('.', '..'), 'Safe fixed40 source/view identity required')
    return value


def mapping_tensors(encoded):
    io.require(isinstance(encoded, Mapping) and bool(encoded), 'Actual nonempty CPU tensor Mapping required')
    return dict(encoded)


def require_digest(digest):
    io.require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest), 'Explicit frozen SHA256 required')
    return digest


def original_grid(end):
    """Complete original zero-origin geometry; never use an observed clip origin."""
    end = F(end)
    io.require(end > 0, 'Positive measured original physical endpoint required')
    if end <= 15:
        return {(F(0), end)}
    windows, start = set(), F(0)
    while start+15 <= end:
        windows.add((start, start+15)); start += F(15, 2)
    windows.add((end-15, end))
    return windows


def require_scientific_protocol(protocol):
    factor = protocol['single_factor']
    io.require(protocol['native_frames'] == 64 and protocol['max_input_tokens'] == 16384 and
        protocol['max_output_tokens'] == 256 and protocol['model_parameters'] == 8782459120 and
        protocol['optimizer_updates'] == 0 and protocol['labels_available_to_model'] is False and
        F(factor['candidate_window_seconds']) == 15 and F(factor['candidate_stride_seconds']) == F(15, 2) and
        factor['new_segment_padding'] == 'NONE' and factor['new_segment_addition'] == 'explicit KEEP only',
        'Frozen original model/native64/token/overlap/no-padding/explicit-KEEP scientific contract changed')


def native_view(view, source, clock):
    """Pure full-clock/native64 validator and stable actual-input identity."""
    points = list(map(F, clock['original_exact_pts']))
    end = F(clock['physical_end_exact'])
    io.require(points and points[0] == 0 and len(points) == clock['native_frames'] == source['n_frames'] and
        all(a < b for a, b in zip(points, points[1:])) and end > points[-1] and
        clock['original_zero_origin_verified'] is True and F(clock['first_original_pts_exact']) == 0 and
        clock['timeline_shift_applied'] is False and F(clock['last_frame_duration_exact']) == end-points[-1] and
        (clock['width'], clock['height'], clock['fps_num'], clock['fps_den']) ==
        (source['width'], source['height'], source['fps_num'], source['fps_den']) and
        F(source['physical_end_exact']) == end and source['source_sha256'] == source['source_key'],
        'Inherited complete original clock/source identity changed; no endpoint/fps repair')
    io.require(type(source['width']) is int and type(source['height']) is int and
        source['width'] > 0 and source['height'] > 0 and type(source['fps_num']) is int and
        type(source['fps_den']) is int and source['fps_num'] > 0 and source['fps_den'] > 0,
        'Actual positive source geometry and nominal fps required')
    start, stop = F(view['window_start']), F(view['window_end'])
    io.require((start, stop) in original_grid(end) and 0 <= start < stop <= end,
               'Fixed40 view is not an original-source zero-origin 15/7.5 grid window')
    eligible = [i for i, point in enumerate(points) if start <= point < stop]
    io.require(len(eligible) >= 64, 'Fewer than 64 distinct original frames; retain and reject without padding')
    ordinals = [eligible[0]+j*(len(eligible)-1)//63 for j in range(64)]
    samples = [str(points[i]) for i in ordinals]
    io.require(view['source_frame_ordinals'] == ordinals and list(map(F, view['sample_exact_pts'])) == list(map(F, samples)) and
        view['source_name'] == source['video_id'] and view['fixed_case_id'] == source['case_id'] and
        view['source_sha256'] == source['source_sha256'] and view['source_clock_sha256'] == source['clock_sha256'] and
        view['window_role'] == 'overlap' and view['view_roles'] == ['overlap'],
        'Registered fixed40 view/native64/full-source/overlap identity differs')
    identity = dict(source_sha256=source['source_sha256'], source_clock_sha256=source['clock_sha256'],
        window_start=str(start), window_end=str(stop), source_frame_ordinals=ordinals, sample_exact_pts=samples)
    return dict(view, window_start=str(start), window_end=str(stop), sample_exact_pts=samples,
        input_view_key=hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest())


def registered_plan(root):
    reg = io.registration(root)
    require_scientific_protocol(io.read(io.checked(reg['main_protocol_ref']['path'], reg['main_protocol_ref']['sha256'])))
    io.require(reg.get('group') == GROUP and reg.get('source_scope') == 'EXTERNAL_NONTEST_ONLY' and
        reg.get('scope') == SCOPE and reg.get('source_count') == 9 and reg.get('unique_input_count') == 17,
        'Exact registered nine-source/seventeen-view external fixed40 scope required')
    ref = reg['source_plan_ref']; path = io.checked(ref['path'], require_digest(ref['sha256']))
    io.require(reg['required_files'].get(str(path)) == ref['sha256'], 'Source plan must be frozen in required_files')
    stored = io.read(path)
    io.require(stored.get('scope') == SCOPE and stored.get('sources') == reg['sources'] and stored.get('views') == reg['views'],
               'Registered source plan/inline source and view identities differ')
    sources, views = source_audit.validate_registered_sources(reg)
    io.require(len(sources) == 9 and len(views) == 17 and
        len({source['case_id'] for source in sources}) == len({source['video_id'] for source in sources}) == 9 and
        len({source['source_sha256'] for source in sources}) == 9 and len({view['case_id'] for view in views}) == 17,
        'Complete unique fixed40 source/view denominator required')
    by_video, clocks = {}, {}
    for source in sources:
        safe_id(source['case_id']); safe_id(source['video_id'])
        for path_key, sha_key in (('source_path', 'source_sha256'), ('clock_path', 'clock_sha256')):
            actual = io.checked(source[path_key], source[sha_key])
            io.require(reg['required_files'].get(str(actual)) == source[sha_key], 'Original source/clock absent from registration lock')
        by_video[source['video_id']] = source
        clocks[source['video_id']] = source_audit.load_source_clock(source)
    actual = []
    for view in views:
        safe_id(view['case_id'])
        io.require(view['source_name'] in by_video, 'Unregistered fixed40 view source')
        actual.append(native_view(view, by_video[view['source_name']], clocks[view['source_name']]))
    io.require(len({view['input_view_key'] for view in actual}) == 17 and
        {view['source_name'] for view in actual} == set(by_video), 'Repeated actual view or unused registered source')
    plan = dict(schema='RECALL_FIXED40_ACTUAL_NATIVE64_VIEW_PLAN_V1', group=GROUP, scope=SCOPE,
        source_count=9, actual_input_count=17, unique_views=actual, baseline_windows=0,
        native_frames=64, max_input_tokens=16384, max_output_tokens=256, processor_min_pixels=131072,
        processor_max_pixels=131072, source_plan_path=str(path), source_plan_sha256=ref['sha256'],
        first_independent_input_replay_pending=True, model_calls=0, GPU_admitted=False)
    return reg, sources, clocks, plan


def file_closure(root, reg):
    files = dict(reg['required_files'])
    required = set(io.code_files()) | io.runtime_dependencies() | io.processor_assets() | {str(io.CONFIG), str(io.RUNTIME)}
    required.update(str(io.CV_CODE/name) for name in ('cv_contract.py', 'cv_grammar.py', 'cv_tokens.py'))
    io.require(required <= set(files), 'Every actual fixed40 implementation/processor/config dependency must be registered')
    io.require(set(reg['required_code_files']) <= set(files) and
        all(files[name] == digest for name, digest in reg['required_code_files'].items()), 'Code subset disagrees with complete registration lock')
    for name in ('main_protocol_ref', 'authorization_ref', 'dev_result_ref', 'confirm_result_ref', 'reference_ref', 'source_plan_ref'):
        ref = reg[name]; path = io.checked(ref['path'], ref['sha256'])
        io.require(files.get(str(path)) == ref['sha256'], 'Required fixed40 gate/reference is absent from lock: '+name)
    for filename, digest in files.items():
        io.require(Path(filename).is_absolute(), 'Absolute registered dependency path required')
        io.checked(filename, require_digest(digest))
    registration_path = io.checked(root/'registration.json')
    files[str(registration_path)] = io.sha(registration_path)
    return files


def verify_files(files):
    for filename, digest in files.items():
        io.checked(filename, digest)


def resource_snapshot(directory):
    values = {line.split(':')[0]: int(line.split(':')[1].split()[0])*1024
              for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    return dict(utc=io.utc(), available_memory_bytes=values['MemAvailable'],
        free_output_disk_bytes=shutil.disk_usage(directory).free, load_average=list(os.getloadavg()), pid=os.getpid())


def capacity(directory, source, wanted_count, view_count, processor):
    pixel_bytes = source['width']*source['height']*3
    size = processor.video_processor.size
    io.require(set(size) == {'shortest_edge', 'longest_edge'}, 'Original explicit video processor size changed')
    tensor_bound = 64*int(size['longest_edge'])*3*4+16384*2*8+3*8
    png_bound = pixel_bytes+((pixel_bytes//65535)+1)*32+65536
    rgb64_bound = 64*pixel_bytes
    need_disk = wanted_count*png_bound+view_count*(rgb64_bound+tensor_bound+(rgb64_bound+tensor_bound)//1000+262144)
    need_memory = 3*rgb64_bound+4*tensor_bound+32*pixel_bytes
    snapshot = resource_snapshot(directory)
    io.require(snapshot['available_memory_bytes'] > need_memory and snapshot['free_output_disk_bytes'] > need_disk,
               'Current shared capacity cannot hold these actual source/remaining-view outputs; retain and stop')
    return dict(snapshot=snapshot, upcoming_memory_bound_bytes=need_memory, remaining_output_bound_bytes=need_disk,
        wanted_original_ordinals=wanted_count, remaining_unique_views=view_count, resource_threshold_derived_from_geometry=True)


def tensor_signature(encoded):
    import torch
    encoded = mapping_tensors(encoded)
    result = {}
    for key, value in encoded.items():
        io.require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.layout == torch.strided,
                   'Only original dense CPU tensors can be cached')
        raw = value.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        result[key] = dict(shape=list(value.shape), stride=list(value.stride()), dtype=str(value.dtype),
            layout=str(value.layout), storage_offset=value.storage_offset(), requires_grad=value.requires_grad,
            bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    return result


def decode_union_once(source, clock, wanted, folder):
    """Only new fixed40 RGB is decoded, once per registered complete source."""
    import av
    import numpy as np
    from PIL import Image
    output = folder/'RGB_ordinals'; output.mkdir(exist_ok=False)
    points = list(map(F, clock['original_exact_pts'])); items, cursor = [], 0
    with av.open(source['source_path']) as container:
        io.require(len(container.streams.video) == 1, 'Original source must have one unambiguous video stream')
        stream = container.streams.video[0]
        io.require(stream.average_rate is not None and F(stream.average_rate) == F(source['fps_num'], source['fps_den']),
                   'Actual original nominal fps differs from the bound successful clock')
        for ordinal, frame in enumerate(container.decode(stream)):
            io.require(ordinal < len(points) and frame.pts is not None and frame.time_base is not None and
                F(frame.pts)*F(frame.time_base) == points[ordinal] and
                (frame.width, frame.height) == (source['width'], source['height']), 'Decoded source differs from bound full native clock')
            cursor += 1
            if ordinal not in wanted:
                continue
            image = frame.to_ndarray(format='rgb24')
            io.require(image.dtype == np.uint8 and image.shape == (source['height'], source['width'], 3), 'Original RGB geometry changed')
            path = output/(str(ordinal).zfill(9)+'.png')
            with path.open('xb') as destination:
                Image.fromarray(image).save(destination, format='PNG', compress_level=1, optimize=False)
                destination.flush(); os.fsync(destination.fileno())
            with Image.open(path) as restored:
                restored.load()
                io.require(restored.mode == 'RGB' and np.array_equal(image, np.asarray(restored)), 'Lossless original PNG roundtrip changed bits')
            items.append(dict(ordinal=ordinal, exact_pts=str(points[ordinal]), path=str(path), bytes=path.stat().st_size,
                sha256=io.sha(path), pixel_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
    io.require(cursor == len(points) and len(items) == len(wanted) and {item['ordinal'] for item in items} == wanted,
               'Incomplete single-source full-clock decode or wanted RGB union')
    io.save(folder/'rgb_union.json', dict(status='PASS_SINGLE_ORIGINAL_RGB_UNION_DECODE_NOT_PROCESSOR_ADMISSION',
        source_name=source['video_id'], fixed_case_id=source['case_id'], source_sha256=source['source_sha256'],
        original_clock_path=source['clock_path'], original_clock_sha256=source['clock_sha256'], items=items,
        actual_new_RGB_decode_passes=1, inherited_complete_clock_remeasured=False, inherited_PNGs=0, utc=io.utc()))
    return {item['ordinal']: item for item in items}


def prepare(root, group=GROUP):
    io.require(group == GROUP, 'This new CPU entry only supports fixed40 facts')
    io.host(cpu=True); root = io.root_path(root)
    io.require(Path(__file__).resolve().parent == root/'code', 'Use the separately deployed fixed40 implementation directory')
    io.require(not (root/'inputs_01').exists() and not (root/'cpu_acceptance_facts.json').exists(),
               'Existing fixed40 preparation cannot be implicitly resumed or repeated')
    reg, sources, clocks, plan = registered_plan(root)
    closure = file_closure(root, reg)
    output = root/'inputs_01'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), group=GROUP, utc=io.utc(), registration_sha256=io.sha(root/'registration.json'),
        source_count=9, expected_input_count=17, complete_original_clock_measurements=0, inherited_primary_caches=0,
        parent_CUDA_environment_not_modified=True, this_process_CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'], model_calls=0))
    current, stage, entries, completed = None, 'FREEZE', [], []
    encode_started, encode_returned, decode_started, decode_completed = 0, 0, 0, 0
    try:
        io.save(output/'implementation_closure.json', dict(files=closure))
        io.save(output/'source_clocks.json', dict(schema='RECALL_FIXED40_ORIGINAL_CLOCKS_V1', sources=sources, clocks=clocks))
        io.save(output/'view_plan.json', plan)
        runtime, processor = io.cpu_processor()
        import transformers
        import torch
        import numpy as np
        from PIL import Image
        io.require(Path(runtime.__file__).resolve() == io.RUNTIME.resolve() and transformers.__version__ == '4.57.1' and
            processor.video_processor.size == io.read(io.CONFIG)['video_size'] and not torch.cuda.is_initialized(),
            'Exact original trained-B runtime/processor/config/CPU contract required')
        for source in sources:
            current, stage = source['case_id'], 'RGB_UNION'
            clock = clocks[source['video_id']]
            views = [view for view in plan['unique_views'] if view['source_name'] == source['video_id']]
            folder = output/source['case_id']; folder.mkdir(exist_ok=False)
            wanted = {ordinal for view in views for ordinal in view['source_frame_ordinals']}
            io.save(folder/'capacity_before_union.json', capacity(folder, source, len(wanted), len(views), processor))
            decode_started += 1
            pixels = decode_union_once(source, clock, wanted, folder)
            decode_completed += 1
            source_entries = []
            for index, view in enumerate(views):
                current, stage = view['case_id'], 'ENCODE_UNIQUE_VIEW'
                capacity(folder, source, 0, len(views)-index, processor)
                window = folder/current; window.mkdir(exist_ok=False)
                images = []
                for ordinal in view['source_frame_ordinals']:
                    item = pixels[ordinal]; io.checked(item['path'], item['sha256'])
                    with Image.open(item['path']) as image:
                        image.load(); images.append(np.asarray(image).copy())
                arrays = np.stack(images); del images
                array_path = window/'frames.npz'
                with array_path.open('xb') as destination:
                    np.savez_compressed(destination, rgb=arrays); destination.flush(); os.fsync(destination.fileno())
                meta = dict(case_id=current, fixed_case_id=source['case_id'], source_name=source['video_id'], video_id=source['video_id'],
                    source_group=source['source_group'], source_key=source['source_key'], group=GROUP,
                    source_path=source['source_path'], source_sha256=source['source_sha256'], source_bytes=Path(source['source_path']).stat().st_size,
                    width=source['width'], height=source['height'], fps_num=source['fps_num'], fps_den=source['fps_den'],
                    source_total_frames=source['n_frames'], all_source_exact_pts=clock['original_exact_pts'], physical_end_exact=str(F(clock['physical_end_exact'])),
                    window_start=view['window_start'], window_end=view['window_end'], source_frame_ordinals=view['source_frame_ordinals'],
                    sample_exact_pts=view['sample_exact_pts'], pixel_sha256=[pixels[i]['pixel_sha256'] for i in view['source_frame_ordinals']],
                    frame_array_path=str(array_path), frame_array_sha256=io.sha(array_path), original_clock_path=source['clock_path'],
                    original_clock_sha256=source['clock_sha256'], window_role='overlap', view_roles=['overlap'], input_view_key=view['input_view_key'],
                    audio_observed=False, reference_available_to_inference=False, reference_labels_used_for_sampling=False,
                    view_selection_scope='REGISTERED_KNOWN_ORDINARY_POINT_VETO_GEOMETRY_ONLY',
                    implementation_closure_sha256=io.sha(output/'implementation_closure.json'), view_plan_sha256=io.sha(output/'view_plan.json'))
                io.validate_native(meta)
                input_path = window/'input.json'; io.save(input_path, meta)
                evidence_path = window/'encode_evidence.json'
                encode_started += 1
                encoded, evidence = runtime.encode(processor, meta,
                    (arrays, meta['source_frame_ordinals'], meta['sample_exact_pts']), F(meta['window_start']), runtime.EMPTY_PROMPT)
                encode_returned += 1
                io.save(evidence_path, evidence)
                encoded = mapping_tensors(encoded)
                tokens = int(encoded['input_ids'].shape[1])
                io.require(0 < tokens <= 16384 and evidence['physical_frames'] == 64 and
                    evidence['prompt_sha256'] == io.PROMPT_SHA and not torch.cuda.is_initialized(), 'Actual original native64/token/CPU input contract failed')
                cache_path = window/'encoded_tensors.pt.gz'; io.save_cache(cache_path, encoded)
                restored = io.load_cache(cache_path); signature = tensor_signature(encoded)
                io.require(signature == tensor_signature(restored) and all(torch.equal(encoded[key].detach().contiguous().reshape(-1).view(torch.uint8),
                    restored[key].detach().contiguous().reshape(-1).view(torch.uint8)) for key in encoded), 'Primary cache serialization changed actual tensor bits')
                proof_path = window/'proof.json'
                io.save(proof_path, dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT', case_id=current, source_name=source['video_id'], group=GROUP,
                    input_path=str(input_path), input_sha256=io.sha(input_path), input_tokens=tokens, input_evidence=evidence,
                    input_evidence_path=str(evidence_path), input_evidence_sha256=io.sha(evidence_path), input_evidence_origin='NEW_FIXED40_PRIMARY_ENCODE',
                    first_independent_input_replay_pending=True, encoded_tensor_path=str(cache_path), encoded_tensor_sha256=io.sha(cache_path),
                    encoded_tensor_format=io.CACHE_FORMAT, encoded_tensor_bytes=cache_path.stat().st_size, full_serialization_signature=signature,
                    lossless_tensor_roundtrip_actual_bits_equal=True, actual_new_processor_encodes=1, original_runtime_path=str(io.RUNTIME),
                    transformers_version=transformers.__version__, torch_version=torch.__version__, CPU_only=True, CUDA_initialized=False,
                    new_model_calls=0, new_optimizer_updates=0))
                entry = dict(case_id=current, fixed_case_id=source['case_id'], source_name=source['video_id'], group=GROUP,
                    window_role='overlap', view_roles=['overlap'], input_path=str(input_path), input_sha256=io.sha(input_path),
                    proof_path=str(proof_path), proof_sha256=io.sha(proof_path))
                entries.append(entry); source_entries.append(entry)
                print(json.dumps(dict(group=GROUP, accepted_unique_inputs=len(entries), expected=17, case_id=current)), flush=True)
                del arrays, encoded, restored
            io.save(folder/'completion.json', dict(source_name=source['video_id'], fixed_case_id=source['case_id'], entries=source_entries,
                actual_new_processor_encodes=len(source_entries), actual_new_RGB_decode_passes=1, complete_clock_measurements_repeated=0,
                rgb_union_sha256=io.sha(folder/'rgb_union.json')))
            completed.append(source['case_id'])
        verify_files(closure)
        io.require(len(entries) == encode_started == encode_returned == 17 and len(completed) == decode_started == decode_completed == 9 and
                   not torch.cuda.is_initialized(), 'Complete fixed40 CPU denominator failed')
        io.save(output/'completion.json', dict(status=PREP_STATUS, group=GROUP, source_scope='EXTERNAL_NONTEST_ONLY', entries=entries, sources=completed,
            source_count=9, actual_input_count=17, primary_encode_calls_started=encode_started, primary_encode_calls_returned=encode_returned,
            actual_new_processor_encodes=17, actual_new_RGB_decode_passes=9, original_clock_measurements_repeated=0, inherited_primary_caches=0,
            first_independent_input_replays_already_completed=0, source_clocks_sha256=io.sha(output/'source_clocks.json'),
            view_plan_sha256=io.sha(output/'view_plan.json'), implementation_closure_sha256=io.sha(output/'implementation_closure.json'),
            registration_sha256=io.sha(root/'registration.json'), CPU_only=True, CUDA_initialized=False, new_model_calls=0,
            new_optimizer_updates=0, scientific_quality_pass=False, GPU_admitted=False))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, stage=stage, successful_entries=entries, complete_sources=completed,
            error=repr(error), traceback=traceback.format_exc(), actual_primary_encode_calls_started=encode_started,
            actual_primary_encode_calls_returned=encode_returned, source_RGB_decode_calls_started=decode_started,
            source_RGB_decode_calls_completed=decode_completed, preserve_all_clocks_RGB_cache_evidence_and_partial=True,
            successful_stages_must_not_repeat=True, implicit_resume=False, model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=(GROUP,), default=GROUP)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    prepare(args.root, args.group)
