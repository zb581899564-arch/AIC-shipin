"""Explicit first independent input QA of one retained primary tensor cache.

The failed original attempt did not save its encode evidence. This new process
performs the already-required first independent native processor replay BEFORE
GPU, compares its in-memory result bit for bit with the retained original cache,
and saves genuinely newly observed evidence. It never rewrites the old cache.
"""
import argparse
from collections.abc import Mapping
from fractions import Fraction as F
import hashlib
import os
from pathlib import Path
import time
import traceback

import model_common as io
import prepare_inputs as original

REG_STATUS = 'REGISTERED_EXPLICIT_RECALL_INPUT_RECOVERY_V2'
QA_STATUS = 'PASS_FIRST_INDEPENDENT_RECALL_INPUT_REPLAY_RECOVERY_02'


def mapping_dict(value):
    io.require(isinstance(value, Mapping) and bool(value), 'Actual nonempty CPU tensor Mapping required')
    return dict(value)


def tensor_signature(encoded):
    values = mapping_dict(encoded)
    import torch
    result = {}
    for name, value in values.items():
        io.require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.layout == torch.strided,
                   'Only original dense CPU tensor values are allowed')
        bits = value.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        result[name] = dict(shape=list(value.shape), stride=list(value.stride()), dtype=str(value.dtype),
            layout=str(value.layout), storage_offset=value.storage_offset(), requires_grad=value.requires_grad,
            bytes=len(bits), sha256=hashlib.sha256(bits).hexdigest())
    return result


def equal_bits(left, right):
    import torch
    left, right = mapping_dict(left), mapping_dict(right)
    return tensor_signature(left) == tensor_signature(right) and all(torch.equal(
        left[name].detach().contiguous().reshape(-1).view(torch.uint8),
        right[name].detach().contiguous().reshape(-1).view(torch.uint8)) for name in left)


def registration(root, group):
    path = root/'input_recovery_registration_02.json'
    reg = io.read(path)
    io.require(reg['status'] == REG_STATUS and reg['group'] == group and
        reg['known_successful_primary_encodes'] == reg['known_successful_source_RGB_decodes'] == 1 and
        reg['known_successful_first_input_replays'] == 0, 'Explicit bounded successful-stage recovery registration required')
    refs = {}
    names = ('original_failure_ref', 'original_launch_ref', 'original_closure_ref', 'original_view_plan_ref',
             'original_source_clocks_ref', 'reference_completion_ref', 'inherited_rgb_union_ref',
             'retained_input_ref', 'retained_frames_ref', 'retained_tensor_ref')
    for name in names:
        ref = reg[name]; refs[name] = io.checked(ref['path'], ref['sha256'])
        io.require(refs[name].is_relative_to(root), 'Explicit inherited input artifact escaped the new project root')
    old = root/group/'inputs_01'
    io.require(refs['original_failure_ref'] == old/'failure.json' and refs['original_launch_ref'] == old/'launch_claim.json' and
        refs['original_view_plan_ref'] == old/'view_plan.json' and refs['original_source_clocks_ref'] == old/'source_clocks.json',
        'Recovery must retain the exact named failed original attempt')
    failure = io.read(refs['original_failure_ref'])
    io.require(failure['stage'] == 'ENCODE_UNIQUE_VIEW' and failure['current'] == reg['retained_actual_case_id'] and
        not failure['successful_entries'] and "Actual nonempty CPU tensor dictionary required" in failure['error'],
        'Recovery is limited to the recorded Mapping-signature failure after one successful cache save')
    for filename, digest in io.read(refs['original_closure_ref'])['files'].items():
        io.checked(filename, digest)  # Failed implementation and original libraries stay immutable.
    required = reg['required_code_files']
    io.require(isinstance(required, dict) and {str(Path(__file__).resolve()),
        str(Path(__file__).parent/'prepare_inputs_recovery_v2.py'),
        str(Path(__file__).parent/'admit_inputs_recovery_v2.py')} <= set(required), 'All independent recovery scripts must be frozen')
    for filename, digest in required.items():
        io.checked(filename, digest)
    meta = io.read(refs['retained_input_ref'])
    old_plan = io.read(refs['original_view_plan_ref'])
    io.require(meta['case_id'] == reg['retained_actual_case_id'] and meta['source_name'] == reg['retained_source_name'] and
        old_plan['unique_views'][0]['case_id'] == meta['case_id'] and
        Path(meta['frame_array_path']).resolve() == refs['retained_frames_ref'] and
        meta['frame_array_sha256'] == reg['retained_frames_ref']['sha256'] and
        refs['retained_tensor_ref'].parent == refs['retained_input_ref'].parent and
        not (refs['retained_input_ref'].parent/'proof.json').exists() and
        not (refs['retained_input_ref'].parent/'encode_evidence.json').exists() and
        refs['retained_frames_ref'].parent == refs['retained_input_ref'].parent,
        'Only exact retained NPZ/meta/cache with missing original proof/evidence can enter this recovery')
    return reg, refs, path


def recovery_closure(root, reg, refs, registration_path):
    files = dict(io.read(refs['original_closure_ref'])['files'])
    files.update(reg['required_code_files'])
    for name, ref in reg.items():
        if name.endswith('_ref') and isinstance(ref, dict) and {'path', 'sha256'} <= set(ref):
            files[str(io.checked(ref['path'], ref['sha256']))] = ref['sha256']
    files[str(registration_path)] = io.sha(registration_path)
    return files


def replay(root, group):
    io.host(cpu=True); root = io.root_path(root)
    reg, refs, registration_path = registration(root, group)
    output = root/group/'first_input_replay_recovery_02'; output.mkdir(parents=True, exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), group=group,
        registration_sha256=io.sha(registration_path), primary_encode_repeated=False, first_independent_input_replay=True,
        moved_before_GPU_due_to_missing_original_evidence=True, old_cache_modified=False, new_model_calls=0))
    began, evidence_saved = time.monotonic(), False
    try:
        io.require(io.read(refs['original_launch_ref'])['pid'] != os.getpid(), 'Independent replay requires a new process')
        meta = io.read(refs['retained_input_ref']); io.validate_native(meta)
        io.checked(meta['source_path'], meta['source_sha256'])
        io.checked(meta['original_clock_path'], meta['original_clock_sha256'])
        union = io.read(refs['inherited_rgb_union_ref'])
        by_ordinal = {item['ordinal']: item for item in union['items']}
        io.require(len(by_ordinal) == len(union['items']) and union['source_sha256'] == meta['source_sha256'] and
            union['original_clock_sha256'] == meta['original_clock_sha256'] and union['actual_new_RGB_decode_passes'] == 1,
            'Retained successful source RGB union/clock binding differs')
        for ordinal, digest in zip(meta['source_frame_ordinals'], meta['pixel_sha256']):
            item = by_ordinal[ordinal]; io.checked(item['path'], item['sha256'])
            io.require(item['pixel_sha256'] == digest and item['exact_pts'] == meta['all_source_exact_pts'][ordinal],
                       'Retained first-view RGB bytes/PTS differ from original union')
        runtime, processor = io.cpu_processor()
        original.capacity(output, dict(width=meta['width'], height=meta['height']), 0, 1, processor)
        import torch
        import numpy as np
        with np.load(refs['retained_frames_ref'], allow_pickle=False) as archive:
            io.require(set(archive.files) == {'rgb'}, 'Retained NPZ has unregistered members')
            rgb = archive['rgb']
        io.require(rgb.dtype == np.uint8 and rgb.shape == (64, meta['height'], meta['width'], 3) and
            [hashlib.sha256(image.tobytes()).hexdigest() for image in rgb] == meta['pixel_sha256'], 'Retained first native64 RGB cache changed')
        encoded, evidence = runtime.encode(processor, meta,
            (rgb, meta['source_frame_ordinals'], meta['sample_exact_pts']), F(meta['window_start']), runtime.EMPTY_PROMPT)
        # The first actual independent observation is persisted BEFORE any
        # post-encode container/signature/serializer check can fail again.
        io.save(output/'encode_evidence.json', evidence); evidence_saved = True
        kept = io.load_cache(refs['retained_tensor_ref'])
        io.require(equal_bits(encoded, kept) and runtime.tensor_signature(kept) == evidence['tensor_signature'] and
            0 < int(kept['input_ids'].shape[1]) <= 16384 and evidence['physical_frames'] == 64 and
            evidence['prompt_sha256'] == io.PROMPT_SHA and not torch.cuda.is_initialized(),
            'First independent input replay differs from the immutable retained primary tensor cache')
        proof = dict(status=QA_STATUS, case_id=meta['case_id'], source_name=meta['source_name'], group=group,
            input_path=str(refs['retained_input_ref']), input_sha256=reg['retained_input_ref']['sha256'],
            retained_tensor_path=str(refs['retained_tensor_ref']), retained_tensor_sha256=reg['retained_tensor_ref']['sha256'],
            frame_array_sha256=reg['retained_frames_ref']['sha256'], input_evidence=evidence,
            input_evidence_origin='FIRST_INDEPENDENT_CPU_REPLAY_PRE_GPU_NOT_OLD_PRIMARY_RECEIPT',
            encode_evidence_path=str(output/'encode_evidence.json'), encode_evidence_sha256=io.sha(output/'encode_evidence.json'),
            full_serialization_signature=tensor_signature(kept), retained_primary_and_independent_tensors_bit_equal=True,
            original_primary_evidence_was_not_saved=True, old_failure_ref=reg['original_failure_ref'],
            old_primary_processor_encodes=1, new_primary_processor_encodes=0, actual_first_independent_input_replays=1,
            actual_new_vision_processor_calls=1,
            post_GPU_vision_processor_replay_for_this_view_forbidden=True, new_first_input_replay_seconds=time.monotonic()-began,
            old_primary_encode_seconds='UNKNOWN_NOT_RECORDED', CPU_only=True, CUDA_initialized=False,
            media_decodes=0, new_model_calls=0, new_optimizer_updates=0)
        io.save(output/'proof.json', proof)
        io.save(output/'completion.json', dict(status=QA_STATUS, group=group, case_id=meta['case_id'],
            proof_path=str(output/'proof.json'), proof_sha256=io.sha(output/'proof.json'),
            old_failure_preserved=True, old_cache_modified=False, primary_encode_repeated=False,
            actual_first_independent_input_replays=1, new_model_calls=0))
    except BaseException as error:
        io.save(output/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
            actual_first_independent_input_replay_started=True, encode_evidence_saved=evidence_saved,
            primary_encode_repeated=False, preserve_all_old_and_new_success=True, implicit_resume=False, new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--group', choices=('dev', 'confirm'), required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    replay(args.root, args.group)
