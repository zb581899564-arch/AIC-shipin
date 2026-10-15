"""Independent all-seventeen cached-input admission, without vision encode.

Checks full native clocks, source locks, lossless PNG/RGB/tensors and serializer
roundtrip. The first independent processor replay is left for post-GPU QA.
"""
import argparse
from fractions import Fraction as F
import hashlib
import importlib
import io as bytes_io
import os
from pathlib import Path
import traceback

import facts_common as io
from facts_prepare import GROUP, PREP_STATUS, file_closure, native_view, registered_plan, capacity_contract, capacity_geometry


def independent_signature(encoded):
    import torch
    result = {}
    for name in sorted(encoded):
        value = encoded[name]
        io.require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.layout == torch.strided,
                   'Actual cache must contain original dense CPU tensors')
        raw = value.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        result[name] = dict(shape=list(value.shape), stride=list(value.stride()), dtype=str(value.dtype),
            layout=str(value.layout), storage_offset=value.storage_offset(), requires_grad=value.requires_grad,
            bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    return result


def require_complete(complete):
    io.require(complete.get('status') == PREP_STATUS and complete.get('group') == GROUP and
        complete.get('source_scope') == 'EXTERNAL_NONTEST_ONLY' and complete.get('source_count') == 9 and
        complete.get('actual_input_count') == 17 and isinstance(complete.get('entries'), list) and len(complete['entries']) == 17 and
        complete.get('primary_encode_calls_started') == complete.get('primary_encode_calls_returned') == complete.get('actual_new_processor_encodes') == 17 and
        complete.get('actual_new_RGB_decode_passes') == 9 and complete.get('original_clock_measurements_repeated') == 0 and
        complete.get('inherited_primary_caches') == complete.get('first_independent_input_replays_already_completed') == 0 and
        complete.get('CPU_only') is True and complete.get('CUDA_initialized') is False and
        complete.get('new_model_calls') == complete.get('new_optimizer_updates') == 0,
        'Complete new nine-source/seventeen-input primary preparation is required')


def require_native_meta(meta, source, clock, view):
    io.validate_native(meta)
    checked_view = native_view(view, source, clock)
    io.require(checked_view == view and meta['case_id'] == view['case_id'] and meta['fixed_case_id'] == source['case_id'] and
        meta['source_name'] == meta['video_id'] == source['video_id'] and meta['group'] == GROUP and
        meta['source_group'] == source['source_group'] and meta['source_key'] == source['source_key'] and
        meta['source_path'] == source['source_path'] and meta['source_sha256'] == source['source_sha256'] and
        meta['source_bytes'] == Path(source['source_path']).stat().st_size and
        (meta['width'], meta['height'], meta['fps_num'], meta['fps_den'], meta['source_total_frames']) ==
        (source['width'], source['height'], source['fps_num'], source['fps_den'], source['n_frames']) and
        meta['all_source_exact_pts'] == clock['original_exact_pts'] and meta['physical_end_exact'] == str(F(clock['physical_end_exact'])) and
        meta['window_start'] == view['window_start'] and meta['window_end'] == view['window_end'] and
        meta['source_frame_ordinals'] == view['source_frame_ordinals'] and meta['sample_exact_pts'] == view['sample_exact_pts'] and
        meta['original_clock_path'] == source['clock_path'] and meta['original_clock_sha256'] == source['clock_sha256'] and
        meta['input_view_key'] == view['input_view_key'] and meta['window_role'] == 'overlap' and meta['view_roles'] == ['overlap'] and
        meta['audio_observed'] is False and meta['reference_available_to_inference'] is False and
        meta['reference_labels_used_for_sampling'] is False and
        meta['view_selection_scope'] == 'REGISTERED_KNOWN_ORDINARY_POINT_VETO_GEOMETRY_ONLY' and
        meta['hypothesis'] == 'TWO_DISTINCT_OVERLAP_VIEWS_EXPLICIT_KEEP_INTERSECTION',
        'Actual metadata differs from the complete original source/native64/no-label input contract')


def admit(root, group=GROUP):
    io.require(group == GROUP, 'Only fixed40 facts can be admitted by this new entry')
    io.host(cpu=True); root = io.root_path(root)
    io.require(Path(__file__).resolve().parent == root/'code', 'Use the independently deployed fixed40 code directory')
    reg, sources, clocks, plan = registered_plan(root)
    expected_closure = file_closure(root, reg)
    source_root = root/'inputs_01'; complete_path = source_root/'completion.json'
    complete = io.read(complete_path); require_complete(complete)
    io.require(complete['registration_sha256'] == io.sha(root/'registration.json') and
        not (root/'cpu_acceptance_facts.json').exists() and not (root/'source_lock_facts_B0.json').exists(),
        'Registration changed or successful input admission would be repeated')
    output = root/'admission_01'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), group=GROUP, utc=io.utc(), prepare_completion_sha256=io.sha(complete_path),
        vision_processor_calls=0, media_decodes=0, model_calls=0))
    current, checked_entries, checks = None, [], []
    try:
        launch = io.read(source_root/'launch_claim.json')
        io.require(launch['pid'] != os.getpid() and launch['registration_sha256'] == complete['registration_sha256'],
                   'Cache admission must be a different actual process bound to the same registration')
        closure_path = source_root/'implementation_closure.json'
        io.require(io.read(closure_path)['files'] == expected_closure and io.sha(closure_path) == complete['implementation_closure_sha256'],
                   'Complete frozen source/implementation/input gate closure changed')
        files = dict(expected_closure)

        def add(path, digest=None):
            path = io.checked(path, digest); actual = io.sha(path)
            io.require(str(path) not in files or files[str(path)] == actual, 'Previously frozen source/evidence changed')
            files[str(path)] = actual
            return path

        add(closure_path); add(complete_path); add(source_root/'launch_claim.json')
        sources_path = add(source_root/'source_clocks.json', complete['source_clocks_sha256'])
        io.require(io.read(sources_path) == dict(schema='RECALL_FIXED40_ORIGINAL_CLOCKS_V1', sources=sources, clocks=clocks),
                   'Independent canonical full-source clock metadata differs')
        plan_path = add(source_root/'view_plan.json', complete['view_plan_sha256'])
        io.require(io.read(plan_path) == plan, 'Registered full-source point-covering native64 plan differs')
        source_by_video = {source['video_id']: source for source in sources}
        views = {view['case_id']: view for view in plan['unique_views']}
        io.require(len(views) == 17 and set(complete['sources']) == {source['case_id'] for source in sources},
                   'Complete nine-source/seventeen-view denominator changed')
        import numpy as np
        import torch
        from PIL import Image
        io.require(not torch.cuda.is_initialized(), 'Independent CPU admission initialized CUDA')
        pixel_manifests = {}
        contract = capacity_contract(reg)
        resize_module = importlib.import_module('transformers.models.qwen3_vl.video_processing_qwen3_vl')
        io.require(str(Path(resize_module.__file__).resolve()) == contract['processor_source_path'] and
            io.sha(resize_module.__file__) == contract['processor_source_sha256'], 'Installed original resize implementation changed')
        geometries = {}
        for source in sources:
            folder = source_root/source['case_id']
            geometries[source['video_id']] = capacity_geometry(source, contract['video_size'],16,2,2,resize_module.smart_resize)
            receipt = io.read(add(folder/'rgb_union.json'))
            io.require(receipt['status'] == 'PASS_SINGLE_ORIGINAL_RGB_UNION_DECODE_NOT_PROCESSOR_ADMISSION' and
                receipt['source_name'] == source['video_id'] and receipt['fixed_case_id'] == source['case_id'] and
                receipt['source_sha256'] == source['source_sha256'] and receipt['original_clock_path'] == source['clock_path'] and
                receipt['original_clock_sha256'] == source['clock_sha256'] and receipt['actual_new_RGB_decode_passes'] == 1 and
                receipt['inherited_complete_clock_remeasured'] is False and receipt['inherited_PNGs'] == 0,
                'Single new original-source RGB union/clock identity differs')
            source_views = [view for view in views.values() if view['source_name'] == source['video_id']]
            wanted = {i for view in source_views for i in view['source_frame_ordinals']}
            io.require(len(receipt['items']) == len(wanted) and {item['ordinal'] for item in receipt['items']} == wanted,
                       'Missing/repeated actual union-ordinal PNG')
            pixels = {}
            for item in receipt['items']:
                path = add(item['path'], item['sha256'])
                io.require(path.is_relative_to(folder/'RGB_ordinals') and path.stat().st_size == item['bytes'] and
                    item['exact_pts'] == str(F(clocks[source['video_id']]['original_exact_pts'][item['ordinal']])),
                    'Lossless union PNG/source-clock ordinal binding differs')
                with Image.open(path) as image:
                    image.load(); array = np.asarray(image)
                    io.require(image.mode == 'RGB' and array.dtype == np.uint8 and
                        array.shape == (source['height'], source['width'], 3) and
                        hashlib.sha256(array.tobytes()).hexdigest() == item['pixel_sha256'],
                        'Independent lossless PNG pixel bits differ')
                pixels[item['ordinal']] = item['pixel_sha256']
            pixel_manifests[source['video_id']] = pixels
            source_complete = io.read(add(folder/'completion.json'))
            capacity_record = io.read(add(folder/'capacity_before_union.json'))
            io.require(capacity_record['geometry'] == geometries[source['video_id']], 'Independent original total-video capacity geometry differs')
            io.require(source_complete['rgb_union_sha256'] == io.sha(folder/'rgb_union.json') and
                source_complete['actual_new_processor_encodes'] == len(source_views) and
                source_complete['actual_new_RGB_decode_passes'] == 1 and source_complete['complete_clock_measurements_repeated'] == 0 and
                {entry['case_id'] for entry in source_complete['entries']} == {view['case_id'] for view in source_views},
                'Complete per-source union/input evidence denominator differs')
        expected_keys = {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'}
        for entry in complete['entries']:
            current = entry['case_id']
            io.require(current in views and current not in {row['case_id'] for row in checked_entries}, 'Unplanned or repeated actual fixed40 input')
            view = views[current]; source = source_by_video[view['source_name']]
            meta_path = add(entry['input_path'], entry['input_sha256']); proof_path = add(entry['proof_path'], entry['proof_sha256'])
            io.require(meta_path == source_root/source['case_id']/current/'input.json' and proof_path == meta_path.parent/'proof.json',
                       'Actual input/proof escaped its new registered source/view directory')
            meta, proof = io.read(meta_path), io.read(proof_path)
            require_native_meta(meta, source, clocks[source['video_id']], view)
            evidence_path = add(proof['input_evidence_path'], proof['input_evidence_sha256'])
            io.require(evidence_path == meta_path.parent/'encode_evidence.json' and io.read(evidence_path) == proof['input_evidence'] and
                proof['input_evidence_origin'] == 'NEW_CONSENSUS_FIXED40_PRIMARY_ENCODE' and proof['first_independent_input_replay_pending'] is True and
                not proof.get('pre_GPU_first_input_replay_done'), 'Immediate new primary evidence required; no recovery or prior first QA can substitute')
            io.require(proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and proof['case_id'] == current and
                proof['source_name'] == entry['source_name'] == meta['source_name'] and proof['group'] == entry['group'] == GROUP and
                entry['fixed_case_id'] == source['case_id'] and entry['window_role'] == 'overlap' and entry['view_roles'] == ['overlap'] and
                proof['input_path'] == str(meta_path) and proof['input_sha256'] == entry['input_sha256'] and
                proof['CPU_only'] is True and proof['CUDA_initialized'] is False and proof['actual_new_processor_encodes'] == 1 and
                proof['new_model_calls'] == proof['new_optimizer_updates'] == 0 and proof['lossless_tensor_roundtrip_actual_bits_equal'] is True and
                proof['original_runtime_path'] == str(io.RUNTIME) and proof['transformers_version'] == '4.57.1' and
                proof['encoded_tensor_format'] == io.CACHE_FORMAT and meta['implementation_closure_sha256'] == io.sha(closure_path) and
                meta['view_plan_sha256'] == io.sha(plan_path) and
                meta['registration_sha256'] == io.sha(root/'registration.json') and meta['main_protocol_sha256'] == reg['main_protocol_ref']['sha256'], 'Original CPU proof/actual-source/runtime/no-label contract differs')
            io.require(meta['pixel_sha256'] == [pixel_manifests[source['video_id']][i] for i in meta['source_frame_ordinals']],
                       'Actual input pixel identities differ from the lossless source union')
            array_path = add(meta['frame_array_path'], meta['frame_array_sha256'])
            io.require(array_path == meta_path.parent/'frames.npz', 'Actual RGB cache escaped the new input directory')
            with np.load(array_path, allow_pickle=False) as archive:
                io.require(set(archive.files) == {'rgb'}, 'Unexpected actual RGB cache fields')
                rgb = archive['rgb']
            io.require(rgb.dtype == np.uint8 and rgb.shape == (64, source['height'], source['width'], 3) and
                [hashlib.sha256(frame.tobytes()).hexdigest() for frame in rgb] == meta['pixel_sha256'], 'Actual native64 RGB bits differ')
            evidence = proof['input_evidence']
            io.require(evidence['case_id'] == current and evidence['source_sha256'] == source['source_sha256'] and
                evidence['source_start'] == meta['window_start'] and evidence['source_frame_ordinals'] == meta['source_frame_ordinals'] and
                evidence['sample_exact_pts'] == meta['sample_exact_pts'] and evidence['pixel_sha256'] == meta['pixel_sha256'] and
                evidence['physical_frames'] == 64 and evidence['prompt_sha256'] == io.PROMPT_SHA,
                'Original primary processor evidence differs from independently checked native samples/RGB')
            cache_path = add(proof['encoded_tensor_path'], proof['encoded_tensor_sha256'])
            io.require(cache_path == meta_path.parent/'encoded_tensors.pt.gz' and cache_path.stat().st_size == proof['encoded_tensor_bytes'],
                       'Actual lossless CPU tensor cache path/size differs')
            encoded = io.load_cache(cache_path)
            geometry = geometries[source['video_id']]
            io.require(encoded['video_grid_thw'].tolist() == [geometry['video_grid_thw']] and
                list(encoded['pixel_values_videos'].shape) == geometry['pixel_values_shape'] and
                encoded['pixel_values_videos'].numel()*encoded['pixel_values_videos'].element_size() == geometry['pixel_tensor_bytes'],
                'Actual independently admitted tensor differs from original total-video smart_resize geometry')
            io.require(set(encoded) == expected_keys and encoded['input_ids'].dtype == encoded['attention_mask'].dtype == torch.int64 and
                encoded['input_ids'].ndim == 2 and encoded['input_ids'].shape[0] == 1 and
                encoded['attention_mask'].shape == encoded['input_ids'].shape and torch.all(encoded['attention_mask'] == 1) and
                0 < encoded['input_ids'].shape[1] == proof['input_tokens'] <= 16384 and
                encoded['video_grid_thw'].dtype == torch.int64 and tuple(encoded['video_grid_thw'].shape) == (1, 3) and
                int(encoded['video_grid_thw'][0, 0])*2 == 64 and torch.all(encoded['video_grid_thw'] > 0) and
                encoded['pixel_values_videos'].dtype == torch.float32 and encoded['pixel_values_videos'].ndim == 2 and
                int(encoded['video_grid_thw'].prod()) == encoded['pixel_values_videos'].shape[0],
                'Actual original tensor/token/native64/grid contract differs')
            signature = independent_signature(encoded)
            io.require(signature == proof['full_serialization_signature'] and
                {name:dict(shape=value['shape'], dtype=value['dtype'], sha256=value['sha256']) for name,value in signature.items()} == evidence['tensor_signature'],
                'Independent actual cached tensor signatures differ from primary receipt')
            buffer = bytes_io.BytesIO(); torch.save(encoded, buffer); buffer.seek(0)
            restored = torch.load(buffer, map_location='cpu', weights_only=True)
            io.require(independent_signature(restored) == signature and all(torch.equal(encoded[key].detach().contiguous().reshape(-1).view(torch.uint8),
                restored[key].detach().contiguous().reshape(-1).view(torch.uint8)) for key in encoded), 'Independent serializer roundtrip changed actual bits')
            report_path = output/(current+'.json')
            io.save(report_path, dict(status='PASS_INDEPENDENT_FIXED40_CACHE_RGB_CLOCK_SERIALIZER_NOT_VISION_REPLAY', case_id=current, group=GROUP,
                proof_sha256=entry['proof_sha256'], input_sha256=entry['input_sha256'], tensor_signature=signature,
                encoded_tensor_sha256=proof['encoded_tensor_sha256'], CPU_only=True, CUDA_initialized=False,
                independent_vision_processor_replay_completed=False, new_processor_encodes=0, media_decodes=0, new_model_calls=0))
            add(report_path); checks.append(dict(case_id=current, check_path=str(report_path), check_sha256=io.sha(report_path)))
            checked_entries.append(entry)
            del rgb, encoded, restored, buffer
        io.require(len(checked_entries) == 17 and len({row['source_name'] for row in checked_entries}) == 9 and
                   not torch.cuda.is_initialized(), 'Incomplete independent all-input fixed40 admission')
        cpu_path = root/'cpu_acceptance_facts.json'
        io.save(cpu_path, dict(status=io.CPU_STATUS, group=GROUP, source_scope='EXTERNAL_NONTEST_ONLY', source_count=9,
            expected_input_count=17, entries=checked_entries, independent_checks=checks, actual_unique_processor_encodes=17,
            inherited_primary_caches=0, completed_first_independent_input_replays=0, first_independent_vision_processor_replay_pending=True,
            registration_path=str(root/'registration.json'), registration_sha256=io.sha(root/'registration.json'),
            prepare_completion_path=str(complete_path), prepare_completion_sha256=io.sha(complete_path), view_plan_path=str(plan_path), view_plan_sha256=io.sha(plan_path),
            CPU_only=True, CUDA_initialized=False, new_processor_encodes=0, media_decodes=0, new_model_calls=0,
            new_optimizer_updates=0, scientific_quality_pass=False, GPU_admitted=False))
        add(cpu_path); add(output/'launch_claim.json')
        for filename, digest in files.items():
            io.checked(filename, digest)
        lock_path = root/'source_lock_facts_B0.json'
        io.save(lock_path, dict(schema='RECALL_FIXED40_SOURCE_CODE_INPUT_LOCK_V1', group=GROUP, stage='B0', source_scope='EXTERNAL_NONTEST_ONLY',
            files=files, actual_input_count=17, source_count=9, no_GPU_admission=True, utc=io.utc()))
        io.save(output/'completion.json', dict(status='PASS_COMPLETE_INDEPENDENT_FIXED40_CACHE_ADMISSION_NOT_GPU', group=GROUP,
            cpu_acceptance_path=str(cpu_path), cpu_acceptance_sha256=io.sha(cpu_path), source_lock_path=str(lock_path), source_lock_sha256=io.sha(lock_path),
            entries=17, source_count=9, vision_processor_calls=0, media_decodes=0, model_calls=0, GPU_admitted=False))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, successful_entries=checked_entries, successful_checks=checks,
            error=repr(error), traceback=traceback.format_exc(), preserve_all_partial_and_success=True, implicit_resume=False,
            vision_processor_calls=0, media_decodes=0, model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=(GROUP,), default=GROUP)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    admit(args.root, args.group)
