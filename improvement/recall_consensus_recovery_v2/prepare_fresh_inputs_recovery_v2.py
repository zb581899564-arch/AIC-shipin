"""Explicit capacity-only recovery; successful media/clocks/plans are read-only.

One source union decode, one Mapping-safe original primary encode per unique
baseline/overlap input. First independent processor replay remains post-B0.
"""
import argparse
from collections.abc import Mapping
from fractions import Fraction as F
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import traceback

import model_common as io
from overlap_plan import validate_sources

PREP_STATUS = 'PASS_FRESH_CONSENSUS_RECOVERY_V2_UNIQUE_NATIVE64_CPU_CACHES_NOT_GPU_ADMISSION'


def require_confirm_admission(root, group):
    return io.fresh_gate(root, group)


def check_protocol(protocol):
    io.check_protocol(protocol)


def digest(value):
    io.require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'Explicit frozen SHA256 required')
    return value


def validate_zero_input_failure(failure):
    io.require(failure.get('stage') == 'RGB_UNION' and failure.get('successful_entries') == [] and
        failure.get('complete_sources') == [] and failure.get('actual_primary_encode_calls_started') == 0 and
        failure.get('actual_primary_encode_calls_returned') == 0 and failure.get('model_calls') == 0 and
        'Actual resources cannot hold this source union/unique-view lossless outputs' in failure.get('error', ''),
        'Only the retained capacity failure before every real RGB/processor/model input is supported')


def require_fresh_inputs(root, group):
    io.require(group == 'confirm', 'Only explicit first fresh confirmation input recovery is supported')
    gate = require_confirm_admission(root, group)
    validate_zero_input_failure(io.read(gate['registration']['original_input_failure_ref']['path']))
    io.require(not (root/group/'inputs_02').exists() and not io.cpu_acceptance_path(root).exists() and
        not io.source_lock_path(root, 'B0').exists(), 'New recovery input/admission already exists; no implicit resume')
    old = root/group/'inputs_01'
    for pattern in ('RGB_ordinals', '*.png', 'frames.npz', 'encoded_tensors.pt.gz', 'encode_evidence.json', 'proof.json', 'completion.json'):
        io.require(not any(old.rglob(pattern)), 'Original attempt contains successful/partial RGB or input work requiring a different recovery: '+pattern)


def bound_reference_completion(root, group):
    io.require(group == 'confirm', 'Only this successful fresh confirm reference is supported')
    pointer_path = root/'reference_completion_confirm.json'; pointer = io.read(pointer_path)
    path = io.checked(pointer['path'], digest(pointer['sha256']))
    io.require(path == root/'confirm/reference_01/completion.json', 'Original completed reference stage must remain unchanged')
    return pointer_path, path


def fresh_media_files(root, group, selection=None):
    gate = selection or require_confirm_admission(root, group)
    registry = io.read(gate['original_registration_path'])
    pointer_path, completion_path = bound_reference_completion(root, group)
    complete = io.read(completion_path)
    io.require(complete.get('status') == 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU' and
        complete.get('group') == group and len(complete.get('accepted', [])) == 4 and
        complete.get('registration_sha256') == gate['original_registration_sha256'] and
        complete.get('development_selection_sha256') == gate['selection_sha256'] and
        complete.get('development_result_sha256') == gate['result_sha256'],
        'Completed fresh reference must bind this registration and actual exposed-development selection/result')
    files = dict(gate['files'])
    def add(path, expected=None):
        if expected is not None: digest(expected)
        actual = io.checked(path, expected); value = io.sha(actual)
        io.require(str(actual) not in files or files[str(actual)] == value, 'Previously registered source/code evidence changed')
        files[str(actual)] = value
        return actual
    add(pointer_path); add(completion_path); add(root/'fresh_confirm_registration.json', gate['original_registration_sha256']); add(root/'fresh_recovery_registration_02.json', gate['registration_sha256'])
    known_path = add(registry['known_exclusions_path'], digest(registry['known_exclusions_sha256']))
    known = io.read(known_path)
    excluded = {name if name.startswith('v_') else 'v_'+name for name in known['youtube_ids']}
    excluded.update(registry['old_exposed_and_reserved_ids'])
    known_bytes = set(known['known_media_sha256'])
    allowed = {row['video_id'] for row in registry['selection']+registry['ordered_engineering_reserves'] if row['group'] == group}
    add(registry['annotation_file_path'], digest(registry['annotation_file_sha256']))
    for ref in registry['prior_media_receipts']:
        previous = io.read(add(ref['path'], digest(ref['sha256'])))
        known_bytes.add(digest(previous['sha256']))
    seen_ids, seen_bytes = set(), set()
    for row in complete['accepted']:
        vid, media_sha = row['video_id'], row['media']['sha256']
        io.require(vid in allowed and vid not in excluded and vid not in seen_ids and media_sha not in known_bytes and
            media_sha not in seen_bytes and row['group'] == row['media']['group'] == group and
            row['media']['video_id'] == vid and row['media']['known_ID_and_byte_separation'] is True,
            'Fresh source is outside this new group or intersects previous/duplicate source identity or bytes')
        seen_ids.add(vid); seen_bytes.add(media_sha)
        media = add(row['media']['path'], digest(row['media']['sha256']))
        io.require(media.is_relative_to(completion_path.parent) and media.stat().st_size == row['media']['bytes'], 'Fresh source media escaped or changed')
        for key,sha_key in (('clock_path','clock_sha256'),('reference_path','reference_sha256')):
            io.require(add(row[key], digest(row[sha_key])).is_relative_to(completion_path.parent), 'Fresh original clock/reference escaped its stage')
        for name in ('media_receipt.json','route.json'):
            add(media.parent/name)
    return files


def confirm_media_files(root, group, selection=None):
    """Controller-compatible spelling, restricted to this fresh registration."""
    return fresh_media_files(root, group, selection)


def file_closure(root, group):
    gate = require_confirm_admission(root, group)
    files = fresh_media_files(root, group, gate)
    code = Path(__file__).resolve().parent
    required = set(io.code_files()) | io.runtime_dependencies() | io.processor_assets() | {str(io.CONFIG), str(io.RUNTIME)}
    required.update(str(path.resolve()) for path in code.glob('*.py'))
    required.update(str(io.CV_CODE/name) for name in ('cv_contract.py','cv_grammar.py','cv_tokens.py'))
    native = io.HOME_ROOT/'videoxum_reference_iteration_20261013_v1/code'
    required.update(str(native/name) for name in ('native_profile_01.py','native_profile_04.py'))
    io.require(required <= set(gate['files']), 'All new implementation/media/native/runtime/processor dependencies must be frozen before preparation')
    original_closure = io.read(gate['registration']['original_implementation_closure_ref']['path'])['files']
    for filename, value in original_closure.items():
        io.checked(filename, digest(value))
        io.require(filename not in files or files[filename] == value, 'Original frozen implementation/source identity changed')
        files[filename] = value
    contract = capacity_contract(root, gate)
    io.require(files.get(contract['processor_source_path']) == contract['processor_source_sha256'], 'Installed resize source missing from complete lock')
    for filename, value in files.items():
        io.require(Path(filename).is_absolute(), 'Absolute frozen source/dependency path required')
        io.checked(filename, digest(value))
    return files


def mapping_tensors(value):
    """Accept BatchFeature/UserDict Mapping while retaining original tensor objects."""
    io.require(isinstance(value, Mapping) and bool(value), 'Actual nonempty CPU tensor Mapping required')
    return dict(value)


def verify_files(files):
    for filename, digest in files.items():
        io.checked(filename, digest)


def resource_snapshot(directory):
    values = {line.split(':')[0]: int(line.split(':')[1].split()[0])*1024
              for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    return dict(utc=io.utc(), available_memory_bytes=values['MemAvailable'],
        free_output_disk_bytes=shutil.disk_usage(directory).free, load_average=list(os.getloadavg()), pid=os.getpid())


def tensor_signature(encoded):
    """Full serialization signature, including original strides and raw bits."""
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


def decode_union_once(row, clock, wanted, folder):
    """Decode RGB once against the inherited clock, not per candidate window."""
    import av
    import numpy as np
    from PIL import Image
    output = folder/'RGB_ordinals'; output.mkdir(exist_ok=False)
    items, cursor = [], 0
    points = list(map(F, clock['original_exact_pts']))
    with av.open(row['media']['path']) as container:
        io.require(len(container.streams.video) == 1, 'Original source stream is ambiguous')
        stream = container.streams.video[0]; stream.thread_count = 1
        io.require(stream.index == clock['video_stream_index'] and stream.time_base is not None and
            F(stream.time_base) == F(clock['stream_time_base_exact']) and stream.average_rate is not None and
            F(stream.average_rate) == F(clock['fps_num'], clock['fps_den']), 'Original native source stream identity changed')
        for ordinal, frame in enumerate(container.decode(stream)):
            io.require(ordinal < len(points) and frame.pts is not None and frame.time_base is not None and
                F(frame.pts)*F(frame.time_base) == points[ordinal] and
                (frame.width, frame.height) == (clock['width'], clock['height']), 'Union RGB decode differs from inherited full native clock')
            cursor += 1
            if ordinal not in wanted:
                continue
            image = frame.to_ndarray(format='rgb24')
            io.require(image.dtype == np.uint8 and image.shape == (clock['height'], clock['width'], 3), 'Original RGB24 geometry/dtype changed')
            path = output/(str(ordinal).zfill(9)+'.png')
            with path.open('xb') as stream_file:
                Image.fromarray(image).save(stream_file, format='PNG', compress_level=1, optimize=False)
                stream_file.flush(); os.fsync(stream_file.fileno())
            with Image.open(path) as restored:
                recovered = np.asarray(restored)
                io.require(restored.mode == 'RGB' and np.array_equal(image, recovered), 'Lossless PNG roundtrip changed original RGB')
            items.append(dict(ordinal=ordinal, exact_pts=str(points[ordinal]), path=str(path), bytes=path.stat().st_size,
                sha256=io.sha(path), pixel_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
    io.require(cursor == len(points) and {item['ordinal'] for item in items} == wanted and len(items) == len(wanted),
               'Incomplete single source RGB/union-ordinal denominator')
    receipt = dict(status='PASS_SINGLE_ORIGINAL_RGB_UNION_DECODE_NOT_PROCESSOR_ADMISSION', items=items,
        source_sha256=row['media']['sha256'], original_clock_path=row['clock_path'], original_clock_sha256=row['clock_sha256'],
        inherited_complete_clock_remeasured=False, actual_new_RGB_decode_passes=1, utc=io.utc())
    io.save(folder/'rgb_union.json', receipt)
    return {item['ordinal']: item for item in items}


def prepare(root, group):
    io.require(group == 'confirm', 'This entry cannot start or resume dev')
    io.host(cpu=True); root = io.root_path(root)
    selection = require_confirm_admission(root, group)
    fresh_media_files(root, group, selection)
    require_fresh_inputs(root, group)
    io.require(Path(__file__).resolve().parent == io.code_dir(root), 'Only the separately deployed confirm code directory is allowed')
    protocol = io.read(root/'protocol.json'); check_protocol(protocol)
    _, reference_path = bound_reference_completion(root, group)
    reference_root = reference_path.parent
    reference = io.read(reference_path)
    io.require(reference['status'] == 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU' and
        reference['group'] == group and reference['actual_new_model_calls'] == 0 and
        reference['registration_sha256'] == selection['original_registration_sha256'], 'Actual complete reference stage required')
    rows = reference['accepted']; clocks, references = {}, {}
    for row in rows:
        vid = row['video_id']; io.require(vid not in references, 'Repeated accepted source')
        media = io.checked(row['media']['path'], row['media']['sha256'])
        io.require(media.is_relative_to(reference_root) and media.stat().st_size == row['media']['bytes'], 'Actual new-root source media identity/size changed')
        for path_key, sha_key in (('clock_path', 'clock_sha256'), ('reference_path', 'reference_sha256')):
            io.require(io.checked(row[path_key], row[sha_key]).is_relative_to(reference_root), 'Reference artifact escaped registered group root')
        clocks[vid], references[vid] = io.read(row['clock_path']), row
    sources, plan, sources_path, plan_path = adopted_metadata(root, selection, rows, clocks)
    contract = capacity_contract(root, selection)
    output = root/group/'inputs_02'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), group=group, utc=io.utc(), reference_completion_sha256=io.sha(reference_path),
        development_selection=selection, no_recovered_primary_cache_or_first_QA=True,
        parent_CUDA_environment_not_modified=True, this_process_CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'], model_calls=0))
    current, stage, entries, completed = None, 'FREEZE', [], []
    encode_calls_started, encode_calls_returned, RGB_calls_started, RGB_calls_completed = 0, 0, 0, 0
    try:
        closure = file_closure(root, group); io.save(output/'implementation_closure.json', dict(files=closure))
        runtime, processor = io.cpu_processor()
        import transformers
        io.require(Path(runtime.__file__).resolve() == io.RUNTIME.resolve() and
            processor.video_processor.size == io.read(io.CONFIG)['video_size'] and transformers.__version__ == '4.57.1',
            'Exact original trained-B processor runtime/version required')
        import torch
        import numpy as np
        from PIL import Image
        source_index = {row['video_id']: row for row in sources['sources']}
        for row in rows:
            current, stage = row['video_id'], 'RGB_UNION'
            clock, source = clocks[current], source_index[current]
            views = [view for view in plan['unique_views'] if view['source_name'] == current]
            folder = output/current; folder.mkdir(exist_ok=False)
            wanted = {ordinal for view in views for ordinal in view['source_frame_ordinals']}
            bound = capacity(folder, source, len(wanted), len(views), processor, contract)
            io.save(folder/'capacity_before_union.json', bound)
            RGB_calls_started += 1
            pixels = decode_union_once(row, clock, wanted, folder)
            RGB_calls_completed += 1
            source_entries = []
            for index, view in enumerate(views):
                current, stage = view['case_id'], 'ENCODE_UNIQUE_VIEW'
                view_capacity = capacity(folder, source, 0, len(views)-index, processor, contract)
                window = folder/view['case_id']; window.mkdir(exist_ok=False)
                images = []
                for ordinal in view['source_frame_ordinals']:
                    item = pixels[ordinal]; io.checked(item['path'], item['sha256'])
                    with Image.open(item['path']) as image:
                        image.load(); images.append(np.asarray(image).copy())
                arrays = np.stack(images); del images
                array_path = window/'frames.npz'
                with array_path.open('xb') as destination:
                    np.savez_compressed(destination, rgb=arrays); destination.flush(); os.fsync(destination.fileno())
                meta = dict(case_id=view['case_id'], source_name=row['video_id'], video_id=row['video_id'], group=group,
                    source_path=row['media']['path'], source_sha256=source['source_sha256'], source_bytes=row['media']['bytes'],
                    width=source['width'], height=source['height'], fps_num=clock['fps_num'], fps_den=clock['fps_den'],
                    source_total_frames=source['n_frames'], all_source_exact_pts=source['normalized_exact_pts'],
                    physical_end_exact=source['physical_end_exact'], window_start=view['start_exact'], window_end=view['end_exact'],
                    source_frame_ordinals=view['source_frame_ordinals'], sample_exact_pts=view['sample_exact_pts'],
                    pixel_sha256=[pixels[i]['pixel_sha256'] for i in view['source_frame_ordinals']],
                    frame_array_path=str(array_path), frame_array_sha256=io.sha(array_path),
                    original_clock_path=row['clock_path'], original_clock_sha256=row['clock_sha256'],
                    window_role=view['window_role'], view_roles=view['view_roles'], input_view_key=view['input_view_key'],
                    audio_observed=False, reference_available_to_inference=False, reference_labels_used_for_sampling=False,
                    implementation_closure_sha256=io.sha(output/'implementation_closure.json'), view_plan_sha256=io.sha(plan_path))
                input_path = window/'input.json'; io.save(input_path, meta)
                evidence_path = window/'encode_evidence.json'
                encode_calls_started += 1
                encoded, evidence = runtime.encode(processor, meta,
                    (arrays, meta['source_frame_ordinals'], meta['sample_exact_pts']), F(meta['window_start']), runtime.EMPTY_PROMPT)
                encode_calls_returned += 1
                io.save(evidence_path, evidence)  # Persist before Mapping/signature/cache checks.
                encoded = mapping_tensors(encoded)
                cache_path = window/'encoded_tensors.pt.gz'; io.save_cache(cache_path, encoded)
                expected_geometry = view_capacity['geometry']
                io.require(encoded['video_grid_thw'].tolist() == [expected_geometry['video_grid_thw']] and
                    list(encoded['pixel_values_videos'].shape) == expected_geometry['pixel_values_shape'] and
                    encoded['pixel_values_videos'].dtype == torch.float32 and
                    encoded['pixel_values_videos'].numel()*encoded['pixel_values_videos'].element_size() == expected_geometry['pixel_tensor_bytes'],
                    'Actual first encoded tensor differs from original smart_resize capacity planning; preserve evidence and stop')
                tokens = int(encoded['input_ids'].shape[1])
                io.require(0 < tokens <= 16384 and evidence['physical_frames'] == 64 and
                    evidence['prompt_sha256'] == io.PROMPT_SHA and not torch.cuda.is_initialized(), 'Actual native64/token/CPU input contract failed')
                restored = io.load_cache(cache_path)
                signature = tensor_signature(encoded)
                io.require(signature == tensor_signature(restored) and all(torch.equal(encoded[key].detach().contiguous().reshape(-1).view(torch.uint8),
                    restored[key].detach().contiguous().reshape(-1).view(torch.uint8)) for key in encoded), 'Original CPU tensor serialization roundtrip changed actual bits')
                proof_path = window/'proof.json'
                proof = dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT', case_id=view['case_id'], source_name=row['video_id'], group=group,
                    input_path=str(input_path), input_sha256=io.sha(input_path), input_tokens=tokens, input_evidence=evidence,
                    input_evidence_path=str(evidence_path), input_evidence_sha256=io.sha(evidence_path),
                    input_evidence_origin='NEW_FRESH_CONSENSUS_CONFIRM_PRIMARY_ENCODE', first_independent_input_replay_pending=True,
                    encoded_tensor_path=str(cache_path), encoded_tensor_sha256=io.sha(cache_path), encoded_tensor_format=io.CACHE_FORMAT,
                    encoded_tensor_bytes=cache_path.stat().st_size, full_serialization_signature=signature,
                    lossless_tensor_roundtrip_actual_bits_equal=True, actual_new_processor_encodes=1,
                    original_runtime_path=str(io.RUNTIME), transformers_version=transformers.__version__, torch_version=torch.__version__,
                    CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0)
                io.save(proof_path, proof)
                entry = dict(case_id=view['case_id'], source_name=row['video_id'], group=group, window_role=view['window_role'], view_roles=view['view_roles'],
                    input_path=str(input_path), input_sha256=io.sha(input_path), proof_path=str(proof_path), proof_sha256=io.sha(proof_path))
                entries.append(entry); source_entries.append(entry)
                print(json.dumps(dict(group=group, accepted_unique_inputs=len(entries), expected=plan['actual_input_count'], case_id=current)), flush=True)
                del arrays, encoded, restored
            current, stage = row['video_id'], 'SOURCE_COMPLETION'
            io.save(folder/'completion.json', dict(source_name=current, entries=source_entries, actual_new_processor_encodes=len(source_entries),
                actual_new_RGB_decode_passes=1, complete_clock_measurements_repeated=0, rgb_union_sha256=io.sha(folder/'rgb_union.json')))
            completed.append(current)
        verify_files(closure)
        io.require(len(entries) == plan['actual_input_count'] and len(completed) == 4 and not torch.cuda.is_initialized(), 'Complete unique CPU group denominator failed')
        io.save(output/'completion.json', dict(status=PREP_STATUS, group=group, entries=entries, sources=completed,
            registration_sha256=selection['registration_sha256'], original_registration_sha256=selection['original_registration_sha256'], protocol_sha256=selection['protocol_sha256'],
            primary_encode_calls_started=encode_calls_started, primary_encode_calls_returned=encode_calls_returned,
            inherited_primary_caches=0, first_independent_input_replays_already_completed=0,
            actual_input_count=len(entries), actual_new_processor_encodes=len(entries), actual_new_RGB_decode_passes=len(completed),
            original_clock_measurements_repeated=0, reference_completion_path=str(reference_path), reference_completion_sha256=io.sha(reference_path),
            source_clocks_path=str(sources_path), source_clocks_sha256=io.sha(sources_path), view_plan_path=str(plan_path), view_plan_sha256=io.sha(plan_path),
            implementation_closure_sha256=io.sha(output/'implementation_closure.json'), CPU_only=True, CUDA_initialized=False,
            new_model_calls=0, new_optimizer_updates=0, scientific_quality_pass=False, GPU_admitted=False))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, stage=stage, successful_entries=entries, complete_sources=completed,
            error=repr(error), traceback=traceback.format_exc(), successful_stages_must_not_repeat=True,
            actual_primary_encode_calls_started=encode_calls_started, actual_primary_encode_calls_returned=encode_calls_returned,
            source_RGB_decode_calls_started=RGB_calls_started, source_RGB_decode_calls_completed=RGB_calls_completed,
            preserve_all_media_clocks_RGB_cache_and_partial=True, implicit_resume=False, model_calls=0))
        raise

def capacity_contract(root, gate):
    reg = gate['registration']
    ref = reg['capacity_evidence_ref']; evidence_path = io.checked(ref['path'], digest(ref['sha256']))
    evidence = io.read(evidence_path)
    io.require(evidence.get('schema') == 'CONSENSUS_PRE_ENCODE_CAPACITY_RECOVERY_EVIDENCE_V2' and
        evidence.get('source_RGB_decode_passes') == evidence.get('actual_primary_encode_calls_started') ==
        evidence.get('actual_primary_encode_calls_returned') == evidence.get('model_calls') == 0 and
        evidence.get('successful_entries') == evidence.get('complete_sources') == [] and
        evidence.get('source_reference_success_count') == 4 and
        evidence.get('original_failures_and_code_preserved') is True and
        evidence.get('successful_download_clock_and_plan_repeated') is False,
        'Bound original zero-input failure/capacity proof is required')
    source_ref = reg['processor_source_ref']; source_path = io.checked(source_ref['path'], digest(source_ref['sha256']))
    io.require(gate['files'].get(str(source_path)) == source_ref['sha256'] and
        evidence['installed_processor_path'] == str(source_path) and
        evidence['original_video_size'] == io.read(io.CONFIG)['video_size'] and
        't_bar*h_bar*w_bar' in evidence['installed_source_budget_definition'] and
        'size.longest_edge' in evidence['installed_source_budget_definition'],
        'Original installed total-video resize/config implementation must be explicitly frozen')
    return dict(video_size=evidence['original_video_size'], processor_source_path=str(source_path),
        processor_source_sha256=source_ref['sha256'], evidence_path=str(evidence_path), evidence_sha256=ref['sha256'])


def capacity_geometry(source, size, patch_size, merge_size, temporal_patch_size, resize):
    """Pure original smart_resize planning, not a processor/encoder call."""
    io.require(set(size) == {'shortest_edge', 'longest_edge'} and all(type(size[key]) is int and size[key] > 0 for key in size) and
        (patch_size, merge_size, temporal_patch_size) == (16, 2, 2), 'Original explicit Qwen3 video patch/resize contract required')
    height, width = resize(num_frames=64, height=source['height'], width=source['width'], temporal_factor=temporal_patch_size,
        factor=patch_size*merge_size, min_pixels=size['shortest_edge'], max_pixels=size['longest_edge'])
    padded_frames = ((64+temporal_patch_size-1)//temporal_patch_size)*temporal_patch_size
    io.require(type(height) is int and type(width) is int and height > 0 and width > 0 and
        height % (patch_size*merge_size) == width % (patch_size*merge_size) == 0 and padded_frames == 64 and
        padded_frames*height*width <= size['longest_edge'], 'Original smart_resize total-video geometry exceeds the bound; no resource-gate bypass')
    grid = [padded_frames//temporal_patch_size, height//patch_size, width//patch_size]
    shape = [grid[0]*grid[1]*grid[2], 3*temporal_patch_size*patch_size*patch_size]
    pixel_bytes = shape[0]*shape[1]*4
    io.require(pixel_bytes == padded_frames*height*width*3*4, 'Dense float32 patch tensor accounting differs')
    return dict(native_frames=64, resized_height=height, resized_width=width, video_grid_thw=grid,
        pixel_values_shape=shape, pixel_values_dtype='torch.float32', pixel_tensor_bytes=pixel_bytes,
        maximum_input_ids_and_attention_bytes=16384*2*8, grid_tensor_bytes=3*8,
        tensor_payload_bound_bytes=pixel_bytes+16384*2*8+3*8,
        size_longest_edge_scope='TOTAL_VIDEO_TEMPORAL_SPATIAL_PIXELS', actual_processor_calls=0)


def capacity_numbers(source, wanted_count, view_count, geometry):
    io.require(type(wanted_count) is int and wanted_count >= 0 and type(view_count) is int and view_count >= 1,
               'Actual remaining source/view denominator required')
    pixel_bytes = source['width']*source['height']*3
    rgb64 = 64*pixel_bytes; tensor = geometry['tensor_payload_bound_bytes']
    png = pixel_bytes+((pixel_bytes//65535)+1)*32+65536
    need_disk = wanted_count*png+view_count*(rgb64+tensor+(rgb64+tensor)//1000+262144)
    # Include full original-size float32 transform scratch as well as the
    # resized patch tensor, serializer signatures and restored cached tensors.
    need_memory = 4*rgb64+6*max(4*rgb64,tensor)+32*pixel_bytes
    return dict(upcoming_memory_bound_bytes=need_memory, remaining_output_bound_bytes=need_disk,
        wanted_original_ordinals=wanted_count, remaining_unique_views=view_count,
        original_rgb64_bytes=rgb64, geometry=geometry, resource_threshold_derived_from_original_implementation=True)


def capacity(directory, source, wanted_count, view_count, processor, contract):
    video = processor.video_processor
    module = importlib.import_module(video.__class__.__module__)
    io.require(str(Path(module.__file__).resolve()) == contract['processor_source_path'] and
        io.sha(module.__file__) == contract['processor_source_sha256'] and video.size == contract['video_size'],
        'Actual original smart_resize source/config differs from the registered capacity proof')
    geometry = capacity_geometry(source, dict(video.size), video.patch_size, video.merge_size, video.temporal_patch_size, module.smart_resize)
    result = capacity_numbers(source, wanted_count, view_count, geometry)
    result['snapshot'] = resource_snapshot(directory)
    result['capacity_evidence_sha256'] = contract['evidence_sha256']
    io.require(result['snapshot']['available_memory_bytes'] > result['upcoming_memory_bound_bytes'] and
        result['snapshot']['free_output_disk_bytes'] > result['remaining_output_bound_bytes'],
        'Actual resources cannot hold this source union/unique-view lossless outputs; retain and stop')
    return result


def adopted_metadata(root, gate, rows, clocks):
    reg = gate['registration']
    def original(name):
        ref = reg[name]; path = io.checked(ref['path'], digest(ref['sha256']))
        io.require(gate['files'].get(str(path)) == ref['sha256'], 'Original successful metadata missing from recovery lock')
        return path, io.read(path)
    sources_path, sources = original('original_source_clocks_ref')
    plan_path, plan = original('original_view_plan_ref')
    validate_sources(sources)
    io.require(len(sources['sources']) == len(rows) == 4 and plan['schema'] == 'RECALL_UNIQUE_ACTUAL_VIEW_PLAN_V1' and
        plan['group'] == 'confirm' and 0 < plan['actual_input_count'] == len(plan['unique_views']) <= 48 and
        plan['model_calls'] == 0 and plan['GPU_admitted'] is False and
        len({view['case_id'] for view in plan['unique_views']}) == len(plan['unique_views']), 'Original successful source/view metadata denominator differs')
    source_index = {source['video_id']:source for source in sources['sources']}
    io.require(set(source_index) == {row['video_id'] for row in rows}, 'Original source plan/media set differs')
    for row in rows:
        source = source_index[row['video_id']]; clock = clocks[row['video_id']]
        io.require(source['source_sha256'] == row['media']['sha256'] and source['normalized_exact_pts'] == clock['original_exact_pts'] and
            source['n_frames'] == clock['native_frames'] and source['width'] == clock['width'] and source['height'] == clock['height'] and
            F(source['physical_end_exact']) == F(clock['physical_end_exact']) and clock['original_zero_origin_verified'] is True and
            clock['timeline_shift_applied'] is False and F(clock['first_original_pts_exact']) == 0 and
            F(clock['last_frame_duration_exact']) > 0 and F(clock['original_exact_pts'][-1])+F(clock['last_frame_duration_exact']) == F(clock['physical_end_exact']),
            'Original full clock is not the already accepted source-clock metadata')
    for view in plan['unique_views']:
        source = source_index[view['source_name']]; points = list(map(F,source['normalized_exact_pts']))
        start,stop = F(view['start_exact']),F(view['end_exact'])
        eligible = [i for i,point in enumerate(points) if start <= point < stop]
        io.require(0 <= start < stop <= F(source['physical_end_exact']) and len(eligible) >= 64, 'Original successful native64 view domain differs')
        expected = [eligible[0]+j*(len(eligible)-1)//63 for j in range(64)]
        io.require(view['source_frame_ordinals'] == expected and view['sample_exact_pts'] == [str(points[i]) for i in expected] and
            view['source_sha256'] == source['source_sha256'] and view['group'] == 'confirm' and
            view['view_roles'] and view['window_role'] in view['view_roles'] and set(view['view_roles']) <= {'baseline','overlap'},
            'Original successful plan native64/source/role identity differs')
    return sources, plan, sources_path, plan_path




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--group', choices=('confirm',), required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    prepare(args.root, args.group)
