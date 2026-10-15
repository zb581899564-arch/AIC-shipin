"""First fresh consensus confirmation CPU inputs; no acquisition or resume.

One source union decode, one Mapping-safe original primary encode per unique
baseline/overlap input. First independent processor replay remains post-B0.
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

import model_common as io
from overlap_plan import SOURCE_SCHEMA, plan_baseline_sources, plan_overlapping_sources, validate_sources

PREP_STATUS = 'PASS_FRESH_CONSENSUS_CONFIRM_UNIQUE_NATIVE64_CPU_CACHES_NOT_GPU_ADMISSION'


def require_confirm_admission(root, group):
    return io.fresh_gate(root, group)


def require_fresh_inputs(root, group):
    io.require(group == 'confirm', 'Only the first fresh confirmation group is supported')
    io.require(not any((root/group).glob('inputs_*')), 'Earlier fresh input attempt requires explicit separately registered recovery')


def check_protocol(protocol):
    io.check_protocol(protocol)


def bound_reference_completion(root, group):
    io.require(group == 'confirm', 'Only fresh confirm reference is supported')
    pointer_path = root/'reference_completion_confirm.json'
    pointer = io.read(pointer_path)
    digest(pointer.get('sha256'))
    path = io.checked(pointer['path'], pointer['sha256'])
    io.require(path == root/'confirm/reference_01/completion.json', 'Exact new fresh confirmation reference_01 completion required')
    return pointer_path, path


def digest(value):
    io.require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'Explicit frozen SHA256 required')
    return value


def fresh_media_files(root, group, selection=None):
    gate = selection or require_confirm_admission(root, group)
    registry = gate['registration']
    pointer_path, completion_path = bound_reference_completion(root, group)
    complete = io.read(completion_path)
    io.require(complete.get('status') == 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU' and
        complete.get('group') == group and len(complete.get('accepted', [])) == 4 and
        complete.get('registration_sha256') == gate['registration_sha256'] and
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
    add(pointer_path); add(completion_path); add(root/'fresh_confirm_registration.json', gate['registration_sha256'])
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
    notes = io.checked(code/'input_fresh_notes.md'); files[str(notes)] = io.sha(notes)
    for filename, value in files.items():
        io.require(Path(filename).is_absolute(), 'Absolute frozen source/dependency path required')
        io.checked(filename, digest(value))
    return files


def mapping_tensors(value):
    """Accept BatchFeature/UserDict Mapping while retaining original tensor objects."""
    io.require(isinstance(value, Mapping) and bool(value), 'Actual nonempty CPU tensor Mapping required')
    return dict(value)


def source_document(accepted, clocks, group):
    """Pure conversion: use original zero-origin PTS, never subtract an offset."""
    io.require(group == 'confirm' and len(accepted) == 4 and len(clocks) == 4,
               'Complete explicit four-source group required')
    sources = []
    for row in accepted:
        vid = row['video_id']; io.safe_id(vid)
        io.require(row['group'] == group and row['media']['group'] == group and row['media']['video_id'] == vid,
                   'Cross-group or mismatched source media receipt')
        clock = clocks[vid]
        points = clock['original_exact_pts']; end = F(clock['physical_end_exact'])
        io.require(clock['original_zero_origin_verified'] is True and F(clock['first_original_pts_exact']) == 0 and
            points and F(points[0]) == 0 and F(clock['last_frame_duration_exact']) > 0 and
            F(points[-1]) + F(clock['last_frame_duration_exact']) == end and
            clock['timeline_shift_applied'] is False and clock['native_frames'] == len(points),
            'Original accepted clock/positive native endpoint changed; no measurement or repair')
        io.require(type(clock['fps_num']) is int and type(clock['fps_den']) is int and
                   clock['fps_num'] > 0 and clock['fps_den'] > 0, 'Actual positive nominal-rate metadata required')
        sources.append(dict(video_id=vid, source_sha256=row['media']['sha256'], width=clock['width'],
            height=clock['height'], n_frames=clock['native_frames'], targetRatioWH=[16, 9],
            normalized_exact_pts=points, physical_end_exact=str(end), diagnostic_ratio_only=True))
    document = dict(schema=SOURCE_SCHEMA, sources=sources)
    validate_sources(document)
    return document


def unique_view_plan(document, group):
    io.require(group == 'confirm', 'Only new confirm view planning is allowed in this entry')
    baseline, overlap = plan_baseline_sources(document), plan_overlapping_sources(document)
    unique, aliases = {}, []
    for role, plan in (('baseline', baseline), ('overlap', overlap)):
        for source in plan['sources']:
            for window in source['windows']:
                key = window['input_view_key']
                if key not in unique:
                    unique[key] = dict(window, case_id=window['case_id'], group=group,
                        source_name=source['video_id'], video_id=source['video_id'],
                        source_sha256=source['source_sha256'], window_role=role, view_roles=[])
                view = unique[key]
                io.require(view['source_name'] == source['video_id'] and
                    view['source_frame_ordinals'] == window['source_frame_ordinals'] and
                    view['sample_exact_pts'] == window['sample_exact_pts'] and
                    view['start_exact'] == window['start_exact'] and view['end_exact'] == window['end_exact'],
                    'Shared view key has inconsistent actual input identity')
                if role not in view['view_roles']:
                    view['view_roles'].append(role)
                aliases.append(dict(video_id=source['video_id'], role=role, planned_case_id=window['case_id'],
                    actual_case_id=view['case_id'], input_view_key=key))
    io.require(0 < len(unique) <= 48, 'Actual unique B0 inputs exceed the frozen group budget; do not change windows/sources')
    return dict(schema='RECALL_UNIQUE_ACTUAL_VIEW_PLAN_V1', group=group, baseline_plan=baseline,
        overlap_plan=overlap, unique_views=list(unique.values()), role_aliases=aliases,
        actual_input_count=len(unique), baseline_alias_count=baseline['window_count'],
        overlap_alias_count=overlap['window_count'], shared_actual_inputs=sum(len(v['view_roles']) == 2 for v in unique.values()),
        maximum_possible_VERIFY_calls=5 * len(unique), same_view_actual_calls=1,
        scientific_quality_pass=False, GPU_admitted=False, model_calls=0)


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
    # Lossless PNG/zlib and serialization bounds derive from this source and
    # the actual explicit original video_size, not fixed free-GiB thresholds.
    png_bound = pixel_bytes + ((pixel_bytes//65535)+1)*32 + 65536
    rgb64_bound = 64*pixel_bytes
    need_disk = wanted_count*png_bound + view_count*(rgb64_bound + tensor_bound +
        (rgb64_bound + tensor_bound)//1000 + 262144)
    need_memory = 3*rgb64_bound + 4*tensor_bound + 32*pixel_bytes
    snapshot = resource_snapshot(directory)
    io.require(snapshot['available_memory_bytes'] > need_memory and snapshot['free_output_disk_bytes'] > need_disk,
               'Actual resources cannot hold this source union/unique-view lossless outputs; retain and stop')
    return dict(snapshot=snapshot, upcoming_memory_bound_bytes=need_memory,
        remaining_output_bound_bytes=need_disk, wanted_original_ordinals=wanted_count, remaining_unique_views=view_count,
        resource_threshold_derived_from_geometry_and_original_processor=True)


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
    io.require(Path(__file__).resolve().parent == root/'code', 'Only the separately deployed confirm code directory is allowed')
    protocol = io.read(root/'protocol.json'); check_protocol(protocol)
    _, reference_path = bound_reference_completion(root, group)
    reference_root = reference_path.parent
    reference = io.read(reference_path)
    io.require(reference['status'] == 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU' and
        reference['group'] == group and reference['actual_new_model_calls'] == 0 and
        reference['registration_sha256'] == io.sha(root/'fresh_confirm_registration.json'), 'Actual complete reference stage required')
    rows = reference['accepted']; clocks, references = {}, {}
    for row in rows:
        vid = row['video_id']; io.require(vid not in references, 'Repeated accepted source')
        media = io.checked(row['media']['path'], row['media']['sha256'])
        io.require(media.is_relative_to(reference_root) and media.stat().st_size == row['media']['bytes'], 'Actual new-root source media identity/size changed')
        for path_key, sha_key in (('clock_path', 'clock_sha256'), ('reference_path', 'reference_sha256')):
            io.require(io.checked(row[path_key], row[sha_key]).is_relative_to(reference_root), 'Reference artifact escaped registered group root')
        clocks[vid], references[vid] = io.read(row['clock_path']), row
    sources = source_document(rows, clocks, group); plan = unique_view_plan(sources, group)
    output = root/group/'inputs_01'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), group=group, utc=io.utc(), reference_completion_sha256=io.sha(reference_path),
        development_selection=selection, no_recovered_primary_cache_or_first_QA=True,
        parent_CUDA_environment_not_modified=True, this_process_CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'], model_calls=0))
    current, stage, entries, completed = None, 'FREEZE', [], []
    encode_calls_started, encode_calls_returned = 0, 0
    try:
        closure = file_closure(root, group); io.save(output/'implementation_closure.json', dict(files=closure))
        io.save(output/'source_clocks.json', sources); io.save(output/'view_plan.json', plan)
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
            bound = capacity(folder, source, len(wanted), len(views), processor)
            io.save(folder/'capacity_before_union.json', bound)
            pixels = decode_union_once(row, clock, wanted, folder)
            source_entries = []
            for index, view in enumerate(views):
                current, stage = view['case_id'], 'ENCODE_UNIQUE_VIEW'
                capacity(folder, source, 0, len(views)-index, processor)
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
                    implementation_closure_sha256=io.sha(output/'implementation_closure.json'), view_plan_sha256=io.sha(output/'view_plan.json'))
                input_path = window/'input.json'; io.save(input_path, meta)
                evidence_path = window/'encode_evidence.json'
                encode_calls_started += 1
                encoded, evidence = runtime.encode(processor, meta,
                    (arrays, meta['source_frame_ordinals'], meta['sample_exact_pts']), F(meta['window_start']), runtime.EMPTY_PROMPT)
                encode_calls_returned += 1
                io.save(evidence_path, evidence)  # Persist before Mapping/signature/cache checks.
                encoded = mapping_tensors(encoded)
                tokens = int(encoded['input_ids'].shape[1])
                io.require(0 < tokens <= 16384 and evidence['physical_frames'] == 64 and
                    evidence['prompt_sha256'] == io.PROMPT_SHA and not torch.cuda.is_initialized(), 'Actual native64/token/CPU input contract failed')
                cache_path = window/'encoded_tensors.pt.gz'; io.save_cache(cache_path, encoded)
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
            registration_sha256=selection['registration_sha256'], protocol_sha256=selection['protocol_sha256'],
            primary_encode_calls_started=encode_calls_started, primary_encode_calls_returned=encode_calls_returned,
            inherited_primary_caches=0, first_independent_input_replays_already_completed=0,
            actual_input_count=len(entries), actual_new_processor_encodes=len(entries), actual_new_RGB_decode_passes=len(completed),
            original_clock_measurements_repeated=0, reference_completion_path=str(reference_path), reference_completion_sha256=io.sha(reference_path),
            source_clocks_sha256=io.sha(output/'source_clocks.json'), view_plan_sha256=io.sha(output/'view_plan.json'),
            implementation_closure_sha256=io.sha(output/'implementation_closure.json'), CPU_only=True, CUDA_initialized=False,
            new_model_calls=0, new_optimizer_updates=0, scientific_quality_pass=False, GPU_admitted=False))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, stage=stage, successful_entries=entries, complete_sources=completed,
            error=repr(error), traceback=traceback.format_exc(), successful_stages_must_not_repeat=True,
            actual_primary_encode_calls_started=encode_calls_started, actual_primary_encode_calls_returned=encode_calls_returned,
            preserve_all_media_clocks_RGB_cache_and_partial=True, implicit_resume=False, model_calls=0))
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--group', choices=('confirm',), required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    prepare(args.root, args.group)
