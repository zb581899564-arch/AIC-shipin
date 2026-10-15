"""First new native RGB/input preparation; no source acquisition or implicit recovery."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import traceback
import model_common as io
from fresh_registration import registration, media_files
from source_plan import source_document, unique_view_plan
from native_helpers import (capacity, decode_union_once, mapping_tensors, tensor_signature, verify_files)
PREP_STATUS = 'PASS_POSITIVE_FIRST_FRESH_NATIVE64_PRIMARY_INPUTS_NOT_GPU_ADMISSION'

def prepare(root, group):
    io.require(group == 'confirm', 'Only first fresh confirmation is supported')
    io.host(cpu=True); root = io.root_path(root)
    reg = registration(root, group)
    closure, reference = media_files(root, reg)
    reference_path = io.checked(reg['reference_completion_ref']['path'], reg['reference_completion_ref']['sha256'])
    rows = reference['accepted']; clocks = {row['video_id']: io.read(row['clock_path']) for row in rows}
    sources = source_document(rows, clocks, group); plan = unique_view_plan(sources, group)
    sources_path = root/group/'source_clocks.json'; plan_path = root/group/'view_plan.json'
    io.save(sources_path, sources); io.save(plan_path, plan)
    closure[str(sources_path)] = io.sha(sources_path); closure[str(plan_path)] = io.sha(plan_path)
    contract = reg['capacity_contract']
    io.require(closure.get(contract['processor_source_path']) == contract['processor_source_sha256'],
               'Actual installed processor source must be frozen before preparation')
    selection = dict(registration_sha256=io.sha(root/'positive_fresh_registration.json'),
        original_registration_sha256=reg['source_registration_ref']['sha256'], protocol_sha256=reg['protocol_ref']['sha256'])
    output = root/group/'inputs_01'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), group=group, utc=io.utc(), reference_completion_sha256=io.sha(reference_path),
        development_selection=selection, no_recovered_primary_cache_or_first_QA=True,
        parent_CUDA_environment_not_modified=True, this_process_CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'], model_calls=0))
    current, stage, entries, completed = None, 'FREEZE', [], []
    encode_calls_started, encode_calls_returned, RGB_calls_started, RGB_calls_completed = 0, 0, 0, 0
    try:
        io.save(output/'implementation_closure.json', dict(files=closure))
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
                    input_evidence_origin='NEW_MIDNIGHT_RELATIVE_FIRST_FRESH_CONFIRM_PRIMARY_ENCODE', first_independent_input_replay_pending=True,
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


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--group',choices=('confirm',),default='confirm')
    args=parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES']=''
    prepare(args.root,args.group)
