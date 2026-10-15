"""Explicit remaining CPU preparation after one retained primary encode.

No old file is edited. The first source RGB union and first view NPZ/meta/tensor
are referenced. Its missing old evidence is supplied only by the separately
completed first independent pre-GPU input replay, never by another primary encode.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

import model_common as io
import prepare_inputs as original
from first_input_replay_recovery_v2 import (QA_STATUS, equal_bits, mapping_dict, recovery_closure,
                                           registration, tensor_signature)

PREP_STATUS = 'PASS_RECALL_REMAINING_CPU_RECOVERY_02_OLD_SUCCESSES_IMMUTABLE_NOT_GPU'


def prepare(root, group):
    io.host(cpu=True); root = io.root_path(root)
    reg, refs, registration_path = registration(root, group)
    original.check_protocol(io.read(root/'protocol.json'))
    reference = io.read(refs['reference_completion_ref']); rows = reference['accepted']
    io.require(reference['status'] == 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU' and
        reference['group'] == group and reference['registration_sha256'] == io.sha(root/'new8_source_registration_01.json'),
        'Frozen original four-source media/native completion changed')
    clocks, row_by_id = {}, {}
    for row in rows:
        vid = row['video_id']; io.require(vid not in row_by_id, 'Duplicate registered source')
        row_by_id[vid] = row
        io.checked(row['media']['path'], row['media']['sha256'])
        clocks[vid] = io.read(io.checked(row['clock_path'], row['clock_sha256']))
        io.checked(row['reference_path'], row['reference_sha256'])
    sources = original.source_document(rows, clocks, group)
    plan = original.unique_view_plan(sources, group)
    io.require(sources == io.read(refs['original_source_clocks_ref']) and plan == io.read(refs['original_view_plan_ref']),
               'Original frozen source/unique view/aliases must not change in recovery')
    qa_root = root/group/'first_input_replay_recovery_02'
    qa_complete = io.read(qa_root/'completion.json'); qa_path = qa_root/'proof.json'; qa = io.read(qa_path)
    io.require(qa_complete['status'] == qa['status'] == QA_STATUS and qa_complete['proof_sha256'] == io.sha(qa_path) and
        qa['case_id'] == reg['retained_actual_case_id'] and qa['input_path'] == str(refs['retained_input_ref']) and
        qa['input_sha256'] == reg['retained_input_ref']['sha256'] and qa['retained_tensor_sha256'] == reg['retained_tensor_ref']['sha256'] and
        qa['retained_primary_and_independent_tensors_bit_equal'] is True and qa['new_primary_processor_encodes'] == 0 and
        qa['actual_first_independent_input_replays'] == 1, 'One successful first independent input replay is required; never repeat it')
    output = root/group/'inputs_02'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group,
        registration_sha256=io.sha(registration_path), old_failure_ref=reg['original_failure_ref'],
        successful_primary_encode_repeated=False, successful_source_RGB_decode_repeated=False, new_model_calls=0))
    current, stage, entries, completed = None, 'FREEZE', [], []
    new_encodes, new_decodes = 0, 0
    try:
        closure = recovery_closure(root, reg, refs, registration_path)
        for path in (qa_root/'launch_claim.json', qa_root/'encode_evidence.json', qa_path, qa_root/'completion.json'):
            closure[str(path)] = io.sha(path)
        io.save(output/'implementation_closure.json', dict(files=closure))
        io.save(output/'source_clocks.json', sources); io.save(output/'view_plan.json', plan)
        runtime, processor = io.cpu_processor()
        import torch
        import numpy as np
        import transformers
        from PIL import Image
        io.require(transformers.__version__ == '4.57.1' and processor.video_processor.size == io.read(io.CONFIG)['video_size'],
                   'Original processor version/size must remain unchanged')
        by_source = {source['video_id']: source for source in sources['sources']}
        for row in rows:
            current, stage = row['video_id'], 'SOURCE_RGB'
            source, clock = by_source[current], clocks[current]
            views = [view for view in plan['unique_views'] if view['source_name'] == current]
            folder = output/current; folder.mkdir(exist_ok=False)
            wanted = {ordinal for view in views for ordinal in view['source_frame_ordinals']}
            inherited_union = current == reg['retained_source_name']
            bound = original.capacity(folder, source, 0 if inherited_union else len(wanted),
                len(views)-int(inherited_union), processor)
            io.save(folder/'capacity_before_union.json', bound)
            if inherited_union:
                union_path = refs['inherited_rgb_union_ref']; union = io.read(union_path)
                io.require(union['source_sha256'] == source['source_sha256'] and union['actual_new_RGB_decode_passes'] == 1 and
                    union['original_clock_sha256'] == row['clock_sha256'] and len(union['items']) == len(wanted) and
                    {item['ordinal'] for item in union['items']} == wanted, 'Complete retained source union must exactly cover frozen views')
                pixels = {item['ordinal']: item for item in union['items']}
                for item in pixels.values():
                    io.checked(item['path'], item['sha256'])
            else:
                pixels = original.decode_union_once(row, clock, wanted, folder); new_decodes += 1
                union_path = folder/'rgb_union.json'
            io.save(folder/'rgb_union_reference.json', dict(path=str(union_path), sha256=io.sha(union_path),
                inherited_success=inherited_union, new_RGB_decodes=0 if inherited_union else 1))
            source_entries = []
            for index, view in enumerate(views):
                current = view['case_id']; window = folder/current; window.mkdir(exist_ok=False)
                reused_primary = current == reg['retained_actual_case_id']
                if reused_primary:
                    stage = 'REFERENCE_OLD_PRIMARY_CACHE_AND_FIRST_INPUT_QA'
                    meta_path = refs['retained_input_ref']; meta = io.read(meta_path)
                    cache_path = refs['retained_tensor_ref']; encoded = io.load_cache(cache_path)
                    evidence = qa['input_evidence']; signature = tensor_signature(encoded)
                    io.require(signature == qa['full_serialization_signature'] and
                        runtime.tensor_signature(encoded) == evidence['tensor_signature'], 'Retained old cache changed after successful first independent QA')
                    io.save(window/'input_evidence_from_first_replay.json', evidence)
                    evidence_path = window/'input_evidence_from_first_replay.json'
                    encode_seconds = 'UNKNOWN_ORIGINAL_PRIMARY_NOT_RECORDED'
                else:
                    stage = 'NEW_PRIMARY_ENCODE'
                    original.capacity(folder, source, 0, len(views)-index, processor)
                    arrays_list = []
                    for ordinal in view['source_frame_ordinals']:
                        item = pixels[ordinal]; io.checked(item['path'], item['sha256'])
                        with Image.open(item['path']) as image:
                            image.load(); arrays_list.append(np.asarray(image).copy())
                    arrays = np.stack(arrays_list); del arrays_list
                    array_path = window/'frames.npz'
                    with array_path.open('xb') as stream:
                        np.savez_compressed(stream, rgb=arrays); stream.flush(); os.fsync(stream.fileno())
                    meta = dict(case_id=current, source_name=row['video_id'], video_id=row['video_id'], group=group,
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
                    meta_path = window/'input.json'; io.save(meta_path, meta)
                    started = time.monotonic()
                    encoded, evidence = runtime.encode(processor, meta,
                        (arrays, meta['source_frame_ordinals'], meta['sample_exact_pts']), F(meta['window_start']), runtime.EMPTY_PROMPT)
                    new_encodes += 1  # Record the successful primary return even if evidence persistence fails.
                    encode_seconds = time.monotonic()-started
                    evidence_path = window/'encode_evidence.json'; io.save(evidence_path, evidence)
                    encoded = mapping_dict(encoded)
                    signature = tensor_signature(encoded)
                    cache_path = window/'encoded_tensors.pt.gz'; io.save_cache(cache_path, encoded)
                    restored = io.load_cache(cache_path)
                    io.require(equal_bits(encoded, restored), 'Lossless original tensor serializer changed actual bits')
                    del arrays, restored
                tokens = int(encoded['input_ids'].shape[1])
                io.require(0 < tokens <= 16384 and evidence['physical_frames'] == 64 and
                    evidence['prompt_sha256'] == io.PROMPT_SHA and runtime.tensor_signature(encoded) == evidence['tensor_signature'] and
                    not torch.cuda.is_initialized(), 'Actual original CPU/native64/token cache contract failed')
                proof_path = window/'proof.json'
                proof = dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT', case_id=current, source_name=row['video_id'], group=group,
                    input_path=str(meta_path), input_sha256=io.sha(meta_path), input_tokens=tokens, input_evidence=evidence,
                    encoded_tensor_path=str(cache_path), encoded_tensor_sha256=io.sha(cache_path), encoded_tensor_format=io.CACHE_FORMAT,
                    encoded_tensor_bytes=cache_path.stat().st_size, full_serialization_signature=signature,
                    lossless_tensor_roundtrip_actual_bits_equal=True, actual_new_processor_encodes=0 if reused_primary else 1,
                    original_runtime_path=str(io.RUNTIME), transformers_version=transformers.__version__, torch_version=torch.__version__,
                    input_evidence_path=str(evidence_path), input_evidence_sha256=io.sha(evidence_path),
                    input_evidence_origin='FIRST_INDEPENDENT_CPU_REPLAY_PRE_GPU' if reused_primary else 'NEW_PRIMARY_ENCODE',
                    primary_encode_evidence_was_not_saved=reused_primary,
                    primary_processor_encodes_original_attempt=1 if reused_primary else 0,
                    new_primary_processor_encodes_in_recovery=0 if reused_primary else 1,
                    pre_GPU_first_input_replay_done=reused_primary,
                    pre_GPU_first_input_replay_path=str(qa_path) if reused_primary else None,
                    pre_GPU_first_input_replay_sha256=io.sha(qa_path) if reused_primary else None,
                    primary_encode_seconds=encode_seconds, CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0)
                io.save(proof_path, proof)
                entry = dict(case_id=current, source_name=row['video_id'], group=group, window_role=view['window_role'], view_roles=view['view_roles'],
                    input_path=str(meta_path), input_sha256=io.sha(meta_path), proof_path=str(proof_path), proof_sha256=io.sha(proof_path))
                entries.append(entry); source_entries.append(entry); del encoded
                print(json.dumps(dict(group=group, completed_unique_inputs=len(entries), expected=plan['actual_input_count'],
                    inherited_primary=reused_primary, new_primary_encodes=new_encodes)), flush=True)
            current, stage = row['video_id'], 'SOURCE_COMPLETION'
            io.save(folder/'completion.json', dict(source_name=current, entries=source_entries,
                new_RGB_decodes=0 if inherited_union else 1, old_successful_RGB_decodes_repeated=0,
                rgb_union_reference_sha256=io.sha(folder/'rgb_union_reference.json')))
            completed.append(current)
        original.verify_files(closure)
        io.require(len(entries) == plan['actual_input_count'] and new_encodes+1 == len(entries) and new_decodes+1 == len(completed) == 4,
                   'Explicit remaining stage counts or original successful-stage preservation differ')
        io.save(output/'completion.json', dict(status=PREP_STATUS, group=group, entries=entries, sources=completed,
            actual_input_count=len(entries), total_primary_processor_encodes=len(entries), actual_new_processor_encodes=new_encodes,
            actual_new_RGB_decode_passes=new_decodes, inherited_successful_primary_encodes=1, inherited_successful_RGB_decodes=1,
            pre_GPU_first_input_replays_completed=1, successful_old_operations_repeated=0,
            original_clock_measurements_repeated=0, reference_completion_path=str(refs['reference_completion_ref']),
            reference_completion_sha256=reg['reference_completion_ref']['sha256'],
            source_clocks_sha256=io.sha(output/'source_clocks.json'), view_plan_sha256=io.sha(output/'view_plan.json'),
            implementation_closure_sha256=io.sha(output/'implementation_closure.json'),
            recovery_registration_path=str(registration_path), recovery_registration_sha256=io.sha(registration_path),
            old_failure_ref=reg['original_failure_ref'], CPU_only=True, CUDA_initialized=False,
            new_model_calls=0, new_optimizer_updates=0, scientific_quality_pass=False, GPU_admitted=False))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, stage=stage, successful_entries=entries, complete_sources=completed,
            actual_new_primary_processor_encodes=new_encodes, actual_new_RGB_decode_passes=new_decodes,
            error=repr(error), traceback=traceback.format_exc(), old_failure_preserved=True,
            preserve_all_successful_evidence_cache_RGB_and_partial=True, implicit_resume=False, model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--group', choices=('dev', 'confirm'), required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    prepare(args.root, args.group)
