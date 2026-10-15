"""Explicit recovery cache admission; the retained first-view pre-GPU input QA is reused.

Run as a separate CPU child only after complete prepare_inputs.py success.
Serializer roundtrip is checked from actual lossless tensors; the first
independent real vision-processor replay belongs to the later B0 replay stage.
"""
import argparse
from fractions import Fraction as F
import hashlib
import io as bytes_io
import json
import os
from pathlib import Path
import traceback

import model_common as io
from overlap_plan import plan_baseline_sources, plan_overlapping_sources, validate_sources
from prepare_inputs import (bound_reference_completion, check_protocol, source_document, unique_view_plan)
from prepare_inputs_recovery_v2 import PREP_STATUS
from first_input_replay_recovery_v2 import QA_STATUS, registration, recovery_closure


def independent_serialization_signature(encoded):
    import torch
    result = {}
    for name in sorted(encoded):
        value = encoded[name]
        io.require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.layout == torch.strided,
                   'Admitted cache must retain original dense CPU tensors')
        contents = value.detach().contiguous().view(torch.uint8).numpy().tobytes()
        result[name] = dict(shape=list(value.shape), stride=list(value.stride()), dtype=str(value.dtype),
            layout=str(value.layout), storage_offset=value.storage_offset(), requires_grad=value.requires_grad,
            bytes=len(contents), sha256=hashlib.sha256(contents).hexdigest())
    return result


def require_original_native64(meta, source, view):
    io.validate_native(meta)
    points = list(map(F, source['normalized_exact_pts']))
    lo, hi = F(meta['window_start']), F(meta['window_end'])
    eligible = [i for i, point in enumerate(points) if lo <= point < hi]
    io.require(len(eligible) >= 64, 'Actual unique input has fewer than 64 original eligible frames')
    expected = [eligible[0] + j*(len(eligible)-1)//63 for j in range(64)]
    io.require(meta['source_frame_ordinals'] == expected == view['source_frame_ordinals'] and
        meta['sample_exact_pts'] == [str(points[i]) for i in expected] == view['sample_exact_pts'] and
        meta['all_source_exact_pts'] == source['normalized_exact_pts'] and meta['source_sha256'] == source['source_sha256'] and
        meta['source_total_frames'] == source['n_frames'] and meta['width'] == source['width'] and meta['height'] == source['height'] and
        meta['physical_end_exact'] == source['physical_end_exact'] and meta['window_start'] == view['start_exact'] and
        meta['window_end'] == view['end_exact'] and meta['view_roles'] == view['view_roles'] and
        meta['window_role'] == view['window_role'] and meta['input_view_key'] == view['input_view_key'],
        'Independent exact native64/source/window/role identity differs')


def admit(root, group):
    io.host(cpu=True); root = io.root_path(root)
    protocol = io.read(root/'protocol.json'); check_protocol(protocol)
    source_root = root/group/'inputs_02'; complete_path = source_root/'completion.json'
    complete = io.read(complete_path)
    io.require(complete['status'] == PREP_STATUS and complete['group'] == group and complete['CPU_only'] is True and
        complete['CUDA_initialized'] is False and complete['new_model_calls'] == complete['new_optimizer_updates'] == 0 and
        complete['original_clock_measurements_repeated'] == 0 and complete['actual_new_RGB_decode_passes'] == 3 and
        complete['inherited_successful_primary_encodes'] == complete['inherited_successful_RGB_decodes'] == 1 and
        complete['pre_GPU_first_input_replays_completed'] == 1 and complete['successful_old_operations_repeated'] == 0,
        'Complete original real CPU preparation group required')
    io.require(not (root/('cpu_acceptance_'+group+'.json')).exists() and not (root/('source_lock_'+group+'_B0.json')).exists(),
               'Successful group admission cannot be overwritten or implicitly resumed')
    output = root/group/'admission_02'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), group=group, utc=io.utc(), prepare_completion_sha256=io.sha(complete_path),
        processor_encodes=0, media_decodes=0, model_calls=0))
    current, checked_entries, checks = None, [], []
    try:
        launch = io.read(source_root/'launch_claim.json')
        io.require(launch['pid'] != os.getpid(), 'Independent admission must run in a different process')
        reg, inherited_refs, reg_path = registration(root, group)
        expected_closure = recovery_closure(root, reg, inherited_refs, reg_path)
        first_qa_root = root/group/'first_input_replay_recovery_02'
        for path in (first_qa_root/'launch_claim.json', first_qa_root/'encode_evidence.json',
                     first_qa_root/'proof.json', first_qa_root/'completion.json'):
            expected_closure[str(path)] = io.sha(path)
        closure_path = source_root/'implementation_closure.json'; closure = io.read(closure_path)['files']
        io.require(closure == expected_closure and io.sha(closure_path) == complete['implementation_closure_sha256'], 'Frozen implementation/processor/code closure changed')
        files = dict(closure)
        def add(path, digest=None):
            path = io.checked(path, digest); files[str(path)] = io.sha(path); return path
        add(closure_path); add(complete_path); add(source_root/'launch_claim.json')
        reference_path = add(complete['reference_completion_path'], complete['reference_completion_sha256'])
        pointer_path, pointed_path = bound_reference_completion(root, group)
        io.require(reference_path == pointed_path, 'Wrong pointer-bound original group reference completion')
        add(pointer_path)
        reference = io.read(reference_path)
        io.require(reference['status'] == 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU' and reference['group'] == group and
            reference['registration_sha256'] == io.sha(root/'new8_source_registration_01.json'), 'Reference group/registration identity changed')
        registry = io.read(root/'new8_source_registration_01.json')
        known_path = add(registry['known_exclusions_path'], registry['known_exclusions_sha256'])
        known = io.read(known_path)
        excluded = {('v_'+name if not name.startswith('v_') else name) for name in known['youtube_ids']}
        excluded.update(registry['old_exposed_and_reserved_ids'])
        allowed = {row['video_id'] for row in registry['selection'] + registry['ordered_engineering_reserves'] if row['group'] == group}
        known_bytes = set(known['known_media_sha256'])
        clocks, row_by_id, actual_bytes = {}, {}, set()
        for row in reference['accepted']:
            vid = row['video_id']; io.require(vid not in row_by_id and vid in allowed and vid not in excluded and
                row['group'] == group and row['media']['known_ID_and_byte_separation'] is True and
                row['media']['sha256'] not in known_bytes and row['media']['sha256'] not in actual_bytes,
                'Source is outside registered external group or intersects known/duplicate ID/bytes')
            row_by_id[vid] = row
            actual_bytes.add(row['media']['sha256'])
            io.require(add(row['media']['path'], row['media']['sha256']).is_relative_to(reference_path.parent),
                       'Actual media escaped the pointer-bound original reference stage')
            io.require(Path(row['media']['path']).stat().st_size == row['media']['bytes'], 'Original source file size changed')
            clock_path = add(row['clock_path'], row['clock_sha256'])
            reference_member = add(row['reference_path'], row['reference_sha256'])
            io.require(clock_path.is_relative_to(reference_path.parent) and reference_member.is_relative_to(reference_path.parent),
                       'Original clock/reference escaped the pointer-bound stage')
            clocks[vid] = io.read(clock_path)
            for filename in ('route.json', 'media_receipt.json'):
                add(Path(row['media']['path']).parent/filename)
        sources_document = source_document(reference['accepted'], clocks, group)
        sources_path = add(source_root/'source_clocks.json', complete['source_clocks_sha256'])
        io.require(io.read(sources_path) == sources_document, 'Independent original-clock conversion differs')
        source_index = {row['video_id']: row for row in sources_document['sources']}
        view_plan_path = add(source_root/'view_plan.json', complete['view_plan_sha256'])
        view_plan = io.read(view_plan_path)
        io.require(view_plan == unique_view_plan(sources_document, group), 'Frozen unique native view/role aliases changed')
        views = {view['case_id']: view for view in view_plan['unique_views']}
        io.require(len(views) == view_plan['actual_input_count'] == complete['actual_input_count'] == len(complete['entries']) and
            complete['actual_new_processor_encodes']+1 == complete['total_primary_processor_encodes'] == len(views) and set(complete['sources']) == set(source_index), 'Complete unique input denominator differs')
        pixel_manifests = {}
        for vid, source in source_index.items():
            union_ref = io.read(add(source_root/vid/'rgb_union_reference.json'))
            io.require(union_ref['inherited_success'] == (vid == reg['retained_source_name']) and
                union_ref['new_RGB_decodes'] == (0 if vid == reg['retained_source_name'] else 1) and
                (vid != reg['retained_source_name'] or union_ref['sha256'] == reg['inherited_rgb_union_ref']['sha256']),
                'Only the explicitly registered old source RGB success can be inherited')
            receipt = io.read(add(union_ref['path'], union_ref['sha256']))
            io.require(receipt['actual_new_RGB_decode_passes'] == 1 and receipt['inherited_complete_clock_remeasured'] is False and
                receipt['source_sha256'] == source['source_sha256'] and receipt['original_clock_path'] == row_by_id[vid]['clock_path'] and
                receipt['original_clock_sha256'] == row_by_id[vid]['clock_sha256'], 'One original source RGB union/clock binding differs')
            wanted = {i for view in views.values() if view['source_name'] == vid for i in view['source_frame_ordinals']}
            io.require(len(receipt['items']) == len(wanted) and {item['ordinal'] for item in receipt['items']} == wanted, 'Union RGB manifest repeated/missing ordinals')
            pixel_manifests[vid] = {item['ordinal']: item['pixel_sha256'] for item in receipt['items']}
            for item in receipt['items']:
                path = add(item['path'], item['sha256'])
                io.require(path.is_relative_to(Path(union_ref['path']).parent/'RGB_ordinals') and path.stat().st_size == item['bytes'] and
                    item['exact_pts'] == source['normalized_exact_pts'][item['ordinal']], 'Original union PNG/PTS binding differs')
            add(source_root/vid/'capacity_before_union.json'); add(source_root/vid/'completion.json')
        import numpy as np
        import torch
        io.require(not torch.cuda.is_initialized(), 'Admission initialized CUDA')
        expected_keys = {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'}
        for entry in complete['entries']:
            current = entry['case_id']; io.require(current in views and current not in {row['case_id'] for row in checked_entries}, 'Duplicate or unplanned actual case')
            view, source = views[current], source_index[entry['source_name']]
            meta_path, proof_path = add(entry['input_path'], entry['input_sha256']), add(entry['proof_path'], entry['proof_sha256'])
            io.require(proof_path.is_relative_to(source_root) and (meta_path.is_relative_to(source_root) or meta_path == inherited_refs['retained_input_ref']), 'Actual new input/proof escaped new group root')
            meta, proof = io.read(meta_path), io.read(proof_path)
            pre_qa = proof.get('pre_GPU_first_input_replay_done') is True
            io.require(pre_qa == (current == reg['retained_actual_case_id']) and
                proof['primary_processor_encodes_original_attempt'] == int(pre_qa) and
                proof['new_primary_processor_encodes_in_recovery'] == int(not pre_qa) and
                proof['primary_encode_evidence_was_not_saved'] == pre_qa,
                'Explicit old primary/new primary accounting differs')
            evidence_file = add(proof['input_evidence_path'], proof['input_evidence_sha256'])
            io.require(io.read(evidence_file) == proof['input_evidence'], 'First observed encode evidence was not persisted exactly')
            if pre_qa:
                qa_path = add(proof['pre_GPU_first_input_replay_path'], proof['pre_GPU_first_input_replay_sha256'])
                io.require(qa_path == first_qa_root/'proof.json', 'Wrong pre-GPU independent input proof')
                qa = io.read(qa_path)
                io.require(qa['status'] == QA_STATUS and qa['case_id'] == current and
                    qa['input_evidence_origin'] == 'FIRST_INDEPENDENT_CPU_REPLAY_PRE_GPU_NOT_OLD_PRIMARY_RECEIPT' and
                    qa['input_evidence'] == proof['input_evidence'] and qa['full_serialization_signature'] == proof['full_serialization_signature'] and
                    qa['retained_primary_and_independent_tensors_bit_equal'] is True and qa['new_primary_processor_encodes'] == 0 and
                    qa['actual_first_independent_input_replays'] == 1 and
                    proof['input_evidence_origin'] == 'FIRST_INDEPENDENT_CPU_REPLAY_PRE_GPU' and
                    entry['input_sha256'] == reg['retained_input_ref']['sha256'] and
                    proof['encoded_tensor_sha256'] == reg['retained_tensor_ref']['sha256'],
                    'Retained primary input must use the successful new FIRST independent input QA, not invented old evidence')
            else:
                io.require(proof['input_evidence_origin'] == 'NEW_PRIMARY_ENCODE' and
                    proof['pre_GPU_first_input_replay_path'] is None and proof['pre_GPU_first_input_replay_sha256'] is None,
                    'New primary inputs must remain pending their own first independent vision replay')
            io.require(proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and proof['CPU_only'] is True and
                proof['CUDA_initialized'] is False and proof['actual_new_processor_encodes'] == int(not pre_qa) and
                proof['new_model_calls'] == proof['new_optimizer_updates'] == 0 and
                proof['case_id'] == meta['case_id'] == current and proof['source_name'] == meta['source_name'] == entry['source_name'] and
                proof['group'] == meta['group'] == entry['group'] == group and proof['input_path'] == str(meta_path) and
                proof['input_sha256'] == entry['input_sha256'] and proof['encoded_tensor_format'] == io.CACHE_FORMAT and
                proof['lossless_tensor_roundtrip_actual_bits_equal'] is True and meta['audio_observed'] is False and
                proof['original_runtime_path'] == str(io.RUNTIME) and proof['transformers_version'] == '4.57.1' and
                meta['reference_available_to_inference'] is False and meta['reference_labels_used_for_sampling'] is False and
                meta['implementation_closure_sha256'] == (reg['original_closure_ref']['sha256'] if proof.get('pre_GPU_first_input_replay_done') else io.sha(closure_path)) and
                meta['view_plan_sha256'] == (reg['original_view_plan_ref']['sha256'] if proof.get('pre_GPU_first_input_replay_done') else io.sha(view_plan_path)),
                'Actual unique CPU proof/no-label/source/implementation binding differs')
            require_original_native64(meta, source, view)
            io.require(meta['source_path'] == row_by_id[entry['source_name']]['media']['path'] and
                meta['original_clock_path'] == row_by_id[entry['source_name']]['clock_path'] and
                meta['original_clock_sha256'] == row_by_id[entry['source_name']]['clock_sha256'] and
                meta['pixel_sha256'] == [pixel_manifests[entry['source_name']][i] for i in meta['source_frame_ordinals']],
                'Input uses another source/full clock/original union RGB')
            array_path = add(meta['frame_array_path'], meta['frame_array_sha256'])
            with np.load(array_path, allow_pickle=False) as archive:
                io.require(set(archive.files) == {'rgb'}, 'Actual RGB cache has unexpected fields')
                rgb = archive['rgb']
            io.require(rgb.dtype == np.uint8 and rgb.shape == (64, source['height'], source['width'], 3) and
                [hashlib.sha256(frame.tobytes()).hexdigest() for frame in rgb] == meta['pixel_sha256'], 'Actual native64 cached RGB bytes changed')
            evidence = proof['input_evidence']
            io.require(evidence['case_id'] == current and evidence['source_sha256'] == source['source_sha256'] and
                evidence['source_start'] == meta['window_start'] and evidence['source_frame_ordinals'] == meta['source_frame_ordinals'] and
                evidence['sample_exact_pts'] == meta['sample_exact_pts'] and evidence['pixel_sha256'] == meta['pixel_sha256'] and
                evidence['physical_frames'] == 64 and evidence['prompt_sha256'] == io.PROMPT_SHA,
                'Original encoded evidence differs from independently checked pixels/native samples')
            cache_path = add(proof['encoded_tensor_path'], proof['encoded_tensor_sha256'])
            io.require(cache_path.is_relative_to(meta_path.parent) and cache_path.stat().st_size == proof['encoded_tensor_bytes'], 'Actual lossless tensor cache identity/size differs')
            encoded = io.load_cache(cache_path)
            io.require(set(encoded) == expected_keys and encoded['input_ids'].dtype == encoded['attention_mask'].dtype == torch.int64 and
                encoded['input_ids'].ndim == 2 and encoded['input_ids'].shape[0] == 1 and
                encoded['attention_mask'].shape == encoded['input_ids'].shape and torch.all(encoded['attention_mask'] == 1) and
                0 < encoded['input_ids'].shape[1] == proof['input_tokens'] <= 16384 and
                encoded['video_grid_thw'].dtype == torch.int64 and tuple(encoded['video_grid_thw'].shape) == (1, 3) and
                int(encoded['video_grid_thw'][0, 0]) * 2 == 64 and torch.all(encoded['video_grid_thw'] > 0) and
                encoded['pixel_values_videos'].dtype == torch.float32 and encoded['pixel_values_videos'].ndim == 2 and
                int(encoded['video_grid_thw'].prod()) == encoded['pixel_values_videos'].shape[0], 'Actual original tensor keys/dtypes/grid/native64/token contract differs')
            signature = independent_serialization_signature(encoded)
            io.require(signature == proof['full_serialization_signature'], 'Actual independent lossless serialization signature differs')
            io.require({key: dict(shape=value['shape'], dtype=value['dtype'], sha256=value['sha256']) for key,value in signature.items()}
                == evidence['tensor_signature'], 'Actual encoded tensor bits differ from accepted original processor evidence')
            buffer = bytes_io.BytesIO(); torch.save(encoded, buffer); buffer.seek(0)
            restored = torch.load(buffer, map_location='cpu', weights_only=True)
            io.require(independent_serialization_signature(restored) == signature and all(torch.equal(
                encoded[key].detach().contiguous().view(torch.uint8), restored[key].detach().contiguous().view(torch.uint8))
                for key in encoded), 'Independent CPU serializer roundtrip changed cached actual bits')
            report_path = output/(current+'.json')
            io.save(report_path, dict(status='PASS_INDEPENDENT_CACHE_RGB_CLOCK_SERIALIZER_CHECK_NOT_VISION_REPLAY', case_id=current, group=group,
                proof_sha256=entry['proof_sha256'], input_sha256=entry['input_sha256'], tensor_signature=signature,
                encoded_tensor_sha256=proof['encoded_tensor_sha256'], CPU_only=True, CUDA_initialized=False,
                independent_vision_processor_replay_completed=pre_qa,
                completed_first_input_replay_path=proof['pre_GPU_first_input_replay_path'],
                completed_first_input_replay_sha256=proof['pre_GPU_first_input_replay_sha256'],
                new_processor_encodes=0, media_decodes=0, new_model_calls=0))
            add(report_path); checks.append(dict(case_id=current, check_path=str(report_path), check_sha256=io.sha(report_path)))
            checked_entries.append(entry)
            del rgb, encoded, restored, buffer
        io.require(len(checked_entries) == len(views) and not torch.cuda.is_initialized(), 'Incomplete independent cache admission group')
        # The acceptance has no lock SHA, avoiding circular file identities.
        # The lock written next includes the final immutable acceptance bytes.
        cpu_path = root/('cpu_acceptance_'+group+'.json')
        io.save(cpu_path, dict(status=io.CPU_STATUS, group=group, source_scope='EXTERNAL_NONTEST_ONLY',
            recovery_status='PASS_EXPLICIT_MAPPING_RECOVERY_PRIMARY_SUCCESSES_NOT_REPEATED',
            old_failure_ref=reg['original_failure_ref'], inherited_primary_encodes=1, new_primary_encodes=len(checked_entries)-1,
            pre_GPU_first_input_replay_cases=[reg['retained_actual_case_id']],
            post_GPU_first_input_replay_pending_cases=[row['case_id'] for row in checked_entries if row['case_id'] != reg['retained_actual_case_id']],
            registered_known_ID_and_byte_isolation_checked=True, hidden_alias_semantic_or_pretraining_overlap='UNKNOWN',
            entries=checked_entries, independent_checks=checks,
            expected_input_count=len(checked_entries), source_count=4, actual_unique_processor_encodes=len(checked_entries),
            prepare_completion_path=str(complete_path), prepare_completion_sha256=io.sha(complete_path),
            view_plan_path=str(view_plan_path), view_plan_sha256=io.sha(view_plan_path),
            role_aliases=view_plan['role_aliases'], first_independent_vision_processor_replay_pending=True,
            CPU_only=True, CUDA_initialized=False, new_processor_encodes=0, media_decodes=0,
            new_model_calls=0, new_optimizer_updates=0, scientific_quality_pass=False, GPU_admitted=False))
        add(cpu_path); add(output/'launch_claim.json')
        lock_path = root/('source_lock_'+group+'_B0.json')
        io.save(lock_path, dict(schema='RECALL_SOURCE_CODE_INPUT_LOCK_V1', group=group, stage='B0',
            source_scope='EXTERNAL_NONTEST_ONLY', files=files,
            actual_input_count=len(checked_entries), no_GPU_admission=True, utc=io.utc()))
        io.save(output/'completion.json', dict(status='PASS_COMPLETE_INDEPENDENT_RECALL_CACHE_ADMISSION_NOT_GPU', group=group,
            cpu_acceptance_path=str(cpu_path), cpu_acceptance_sha256=io.sha(cpu_path),
            source_lock_path=str(lock_path), source_lock_sha256=io.sha(lock_path), entries=len(checked_entries),
            vision_processor_calls=0, media_decodes=0, model_calls=0, GPU_admitted=False))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, successful_entries=checked_entries, successful_checks=checks,
            error=repr(error), traceback=traceback.format_exc(), preserve_all_partial_and_success=True,
            implicit_resume=False, vision_processor_calls=0, media_decodes=0, model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--group', choices=('dev', 'confirm'), required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''  # This CPU child only.
    admit(args.root, args.group)
