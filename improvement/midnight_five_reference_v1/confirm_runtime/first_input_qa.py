"""First independent actual native/processor QA of every new B0 input, pre-GPU."""
import argparse
from fractions import Fraction as F
import hashlib
import os
from pathlib import Path
import traceback

import model_common as io
from fresh_registration import registration, media_files, validate_source_grouped_order
from native_helpers import tensor_signature, capacity
from prepare_inputs import PREP_STATUS
from source_plan import source_document, unique_view_plan


def main(root):
    io.host(cpu=True); root = io.root_path(root); reg = registration(root)
    files, reference = media_files(root, reg)
    source = root/'confirm/inputs_01'; complete = io.read(source/'completion.json')
    io.require(complete['status'] == PREP_STATUS and complete['CPU_only'] is True and
        complete['CUDA_initialized'] is False and complete['actual_input_count'] == len(complete['entries']) and
        complete['new_model_calls'] == complete['new_optimizer_updates'] == 0 and
        complete['primary_encode_calls_started'] == complete['primary_encode_calls_returned'] == len(complete['entries']) and
        io.read(source/'launch_claim.json')['pid'] != os.getpid(), 'Complete primary input stage and independent process required')
    clocks = {row['video_id']: io.read(row['clock_path']) for row in reference['accepted']}
    sources = source_document(reference['accepted'], clocks, 'confirm'); plan = unique_view_plan(sources, 'confirm')
    io.require(io.read(root/'confirm/source_clocks.json') == sources and io.read(root/'confirm/view_plan.json') == plan and
        complete['registration_sha256'] == io.sha(root/'positive_fresh_registration.json'),
        'Independent complete native64 source/view plan differs')
    validate_source_grouped_order(plan, complete['entries'], [row['video_id'] for row in reference['accepted']])
    views = {v['case_id']: v for v in plan['unique_views']}
    sources_by_id = {value['video_id']: value for value in sources['sources']}
    output = root/'confirm/B0/input_qa_01'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), CPU_only=True,
        primary_completion_sha256=io.sha(source/'completion.json'), first_input_QA_before_GPU=True,
        first_vision_processor_observations=len(views), new_model_calls=0))
    proofs, accepted, current = [], [], None
    def add(path, digest=None):
        path = io.checked(path, digest); actual = io.sha(path)
        io.require(str(path) not in files or files[str(path)] == actual, 'Frozen source or input changed during first QA')
        files[str(path)] = actual; return path
    try:
        import numpy as np
        import torch
        from PIL import Image
        runtime, processor = io.cpu_processor()
        pixels = {}
        for row in reference['accepted']:
            vid = row['video_id']; union_path = add(source/vid/'rgb_union.json'); union = io.read(union_path)
            wanted = {i for view in plan['unique_views'] if view['source_name'] == vid for i in view['source_frame_ordinals']}
            io.require(union['actual_new_RGB_decode_passes'] == 1 and union['inherited_complete_clock_remeasured'] is False and
                len(union['items']) == len(wanted) and {p['ordinal'] for p in union['items']} == wanted and
                union['source_sha256'] == row['media']['sha256'] and union['original_clock_sha256'] == row['clock_sha256'],
                'Complete single-source original RGB union binding required')
            pixels[vid] = {}
            for item in union['items']:
                path = add(item['path'], item['sha256'])
                io.require(item['exact_pts'] == clocks[vid]['original_exact_pts'][item['ordinal']] and
                    path.is_relative_to(source/vid/'RGB_ordinals'), 'RGB bank original clock/path mismatch')
                pixels[vid][item['ordinal']] = item
            add(source/vid/'completion.json'); add(source/vid/'capacity_before_union.json')
        for entry in complete['entries']:
            current = entry['case_id']; view = views[current]
            io.save(output/(current+'.capacity.json'), capacity(output,
                sources_by_id[view['source_name']], 0, 1, processor, reg['capacity_contract']))
            meta = io.read(add(entry['input_path'], entry['input_sha256']))
            primary = io.read(add(entry['proof_path'], entry['proof_sha256'])); io.validate_native(meta)
            io.require(meta['source_frame_ordinals'] == view['source_frame_ordinals'] and
                meta['sample_exact_pts'] == view['sample_exact_pts'] and meta['view_roles'] == view['view_roles'] and
                primary['input_evidence_origin'] == 'NEW_MIDNIGHT_RELATIVE_FIRST_FRESH_CONFIRM_PRIMARY_ENCODE' and
                primary['actual_new_processor_encodes'] == 1 and primary['CPU_only'] is True and
                primary['CUDA_initialized'] is False and meta['audio_observed'] is False and
                meta['reference_available_to_inference'] is False and meta['reference_labels_used_for_sampling'] is False,
                'Actual first fresh input/native/no-label contract differs')
            with np.load(add(meta['frame_array_path'], meta['frame_array_sha256']), allow_pickle=False) as archive:
                io.require(set(archive.files) == {'rgb'}, 'Original frame NPZ has foreign members')
                rgb = archive['rgb']
            io.require(rgb.dtype == np.uint8 and rgb.shape == (64, meta['height'], meta['width'], 3) and
                [hashlib.sha256(frame.tobytes()).hexdigest() for frame in rgb] == meta['pixel_sha256'], 'Native original RGB NPZ differs')
            # Independent actual PNG/NPZ pixel equality; cached media is never decoded again.
            for array, ordinal, digest in zip(rgb, meta['source_frame_ordinals'], meta['pixel_sha256']):
                item = pixels[meta['source_name']][ordinal]
                with Image.open(item['path']) as image:
                    io.require(image.mode == 'RGB' and np.array_equal(np.asarray(image), array) and
                        item['pixel_sha256'] == digest, 'Original PNG/NPZ native pixel equality failed')
            encoded, evidence = runtime.encode(processor, meta,
                (rgb, meta['source_frame_ordinals'], meta['sample_exact_pts']), F(meta['window_start']), runtime.EMPTY_PROMPT)
            # Persist first independently observed evidence before cache/assert checks.
            evidence_path = output/(current+'.encode_evidence.json'); io.save(evidence_path, evidence); add(evidence_path)
            cached = io.load_cache(add(primary['encoded_tensor_path'], primary['encoded_tensor_sha256']))
            io.require(evidence == primary['input_evidence'] and runtime.tensor_signature(encoded) == runtime.tensor_signature(cached) and
                tensor_signature(encoded) == tensor_signature(cached) == primary['full_serialization_signature'] and
                all(torch.equal(encoded[k].contiguous().reshape(-1).view(torch.uint8), cached[k].contiguous().reshape(-1).view(torch.uint8)) for k in cached),
                'First independent actual vision-processor/native/tensor replay failed')
            old_evidence = add(primary['input_evidence_path'], primary['input_evidence_sha256'])
            io.require(io.read(old_evidence) == evidence, 'Saved original primary encode evidence changed')
            proof_path = output/(current+'.json')
            io.save(proof_path, dict(status='PASS_FIRST_INDEPENDENT_FRESH_B0_INPUT_QA_PRE_GPU', case_id=current,
                group='confirm', primary_proof_path=entry['proof_path'], primary_proof_sha256=entry['proof_sha256'],
                input_path=entry['input_path'], input_sha256=entry['input_sha256'], input_evidence=evidence,
                independent_encode_evidence_path=str(evidence_path), independent_encode_evidence_sha256=io.sha(evidence_path),
                actual_new_independent_processor_calls=1, primary_encodes_repeated=0, media_decodes=0,
                CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0)); add(proof_path)
            final_path = output/(current+'.accepted_input.json')
            final = dict(primary, first_input_QA_path=str(proof_path), first_input_QA_sha256=io.sha(proof_path),
                first_independent_input_replay_pending=False, pre_GPU_first_input_replay_done=True)
            io.save(final_path, final); add(final_path)
            accepted.append(dict(entry, proof_path=str(final_path), proof_sha256=io.sha(final_path)))
            proofs.append(dict(case_id=current, proof_ref=dict(path=str(proof_path), sha256=io.sha(proof_path))))
            print(__import__('json').dumps(dict(stage='FIRST_FRESH_B0_INPUT_QA', complete=len(proofs), expected=len(views))), flush=True)
            del encoded, cached, rgb
        io.require(len(proofs) == len(views) and not torch.cuda.is_initialized(), 'Complete pre-GPU first-input QA denominator failed')
        qa_path = output/'completion.json'
        io.save(qa_path, dict(status='PASS_FIRST_INDEPENDENT_FRESH_B0_INPUT_QA_PRE_GPU', group='confirm', calls=len(proofs), proofs=proofs,
            CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0, media_decodes=0,
            actual_first_independent_processor_calls=len(proofs), all_before_GPU=True)); add(qa_path)
        cpu_path = root/'cpu_acceptance_confirm.json'
        io.save(cpu_path, dict(status=io.CPU_STATUS, group='confirm', source_scope='EXTERNAL_NONTEST_ONLY',
            entries=accepted, expected_input_count=len(accepted), source_count=4,
            first_input_QA_completion_path=str(qa_path), first_input_QA_completion_sha256=io.sha(qa_path),
            all_first_independent_inputs_completed_pre_GPU=True, reference_available_to_inference=False,
            CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0,
            scientific_quality_pass=False, GPU_admitted=False)); add(cpu_path)
        for path in (source/'completion.json', source/'launch_claim.json', source/'implementation_closure.json',
                     root/'confirm/source_clocks.json', root/'confirm/view_plan.json', output/'launch_claim.json'):
            add(path)
        for path in output.glob('*.capacity.json'):
            add(path)
        io.save(root/'source_lock_confirm_B0.json', dict(files=files, group='confirm', stage='B0', utc=io.utc()))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, successful_proofs=proofs, successful_entries=accepted,
            error=repr(error), traceback=traceback.format_exc(), preserve_all_success=True, implicit_resume=False,
            new_model_calls=0, engineering_failure_is_not_UNKNOWN_or_EMPTY=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''; main(args.root)
