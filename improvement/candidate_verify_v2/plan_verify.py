"""Read-only external candidate plan; needs actual B0/raw/replay success first."""
import hashlib
import os
from pathlib import Path

import cv_contract as c
import cv_io as io


def event_request(row, allowed_roles):
    refs = row['original_evidence']
    paths = {key: io.checked(refs[key]) for key in
        ('input', 'cpu_proof', 'done', 'raw', 'request', 'independent_replay', 'model_identity', 'source_separation', 'clock')}
    meta, cpu, done, raw, request, replay, model, separated = [io.read(paths[key]) for key in
        ('input', 'cpu_proof', 'done', 'raw', 'request', 'independent_replay', 'model_identity', 'source_separation')]
    io.model_identity(model['identity'])
    case_id = c.safe_id(meta['case_id'])
    if (case_id != row['original_case_id'] or any(v['case_id'] != case_id for v in (cpu, done, request, replay)) or
            done['status'] != 'MODEL_OK' or not replay['status'].startswith('PASS_') or
            replay['new_model_calls'] != 0 or raw['actual_model_call'] is not True or
            cpu['CPU_only'] is not True or cpu['new_model_calls'] != 0 or
            meta['reference_available_to_inference'] is not False or meta['audio_observed'] is not False or
            request['reference_labels_read'] is not False):
        raise ValueError('Actual original external B0/coarse CPU/raw/replay identity incomplete')
    if (done['raw_sha256'] != refs['raw']['sha256'] or done['request_sha256'] != refs['request']['sha256'] or
            request['CPU_proof_sha256'] != refs['cpu_proof']['sha256'] or
            cpu['input_sha256'] != refs['input']['sha256'] or request['input_sha256'] != refs['input']['sha256'] or
            replay['done_sha256'] != refs['done']['sha256'] or replay['raw_sha256'] != refs['raw']['sha256'] or
            not cpu['input_evidence'] == done['input_evidence'] == raw['input_evidence'] == request['input_evidence'] == replay['input_evidence']):
        raise ValueError('Actual original B0 source/request/token/raw bindings changed')
    if (hashlib.sha256(request['prompt'].encode()).hexdigest() != c.EMPTY_PROMPT_SHA256 or
            cpu['input_evidence']['prompt_sha256'] != c.EMPTY_PROMPT_SHA256):
        raise ValueError('Original candidate does not come from the empty-capable B0 prompt')
    if (cpu['input_evidence']['source_sha256'] != meta['source_sha256'] or
            cpu['input_evidence']['source_frame_ordinals'] != meta['source_frame_ordinals'] or
            cpu['input_evidence']['sample_exact_pts'] != meta['sample_exact_pts']):
        raise ValueError('Original native pixel/timestamp evidence differs from accepted metadata')
    if (not separated['status'].startswith('PASS_') or
            separated.get('known_current_b_training_and_426_test_identities_complete') is not True or
            separated.get('identity_intersections') or separated.get('byte_intersections')):
        raise ValueError('Complete frozen actual external source separation receipt required')
    if meta.get('source_role', meta.get('source_split')) not in allowed_roles:
        raise ValueError('Candidate source role is outside the frozen development/confirmation scope')
    index = row['original_segment_index']
    if type(index) is not int or not 0 <= index < len(done['segments']):
        raise ValueError('Existing original B0 segment index required')
    origin = c.exact(done['source_start_exact'])
    interval = [str(origin+c.exact(value)) for value in done['segments'][index]]
    if row['original_interval_exact'] != interval:
        raise ValueError('Registered exact candidate differs from actual original B0 interval')
    if ('encoded_tensor_path' not in cpu or 'encoded_tensor_sha256' not in cpu or
            cpu.get('encoded_tensor_format') != io.TENSOR_CACHE_FORMAT):
        raise io.MissingOriginalCacheError('Original '+case_id+' has no accepted gzip vision tensor cache; '
            'existing RGB/hash/raw does not authorize repeated processor or decode')
    cache_path = io.checked(dict(path=cpu['encoded_tensor_path'], sha256=cpu['encoded_tensor_sha256']))
    clock = io.read(paths['clock'])
    for key in row['clock_object_keys']:
        clock = clock[key]
    points = clock['normalized_exact_pts'] if 'normalized_exact_pts' in clock else clock['original_exact_pts']
    if points != meta['all_source_exact_pts'] or clock['source_sha256'] != meta['source_sha256']:
        raise ValueError('Original complete clock/metadata/source identity changed')
    event = dict(event_id=c.safe_id(row['event_id']), original_case_id=case_id,
        original_segment_index=index, original_interval_exact=interval)
    req = c.request(event, meta)
    req.update(original_evidence=refs, clock_object_keys=row['clock_object_keys'],
        original_input_path=str(paths['input']), original_input_sha256=refs['input']['sha256'],
        original_CPU_proof_path=str(paths['cpu_proof']), original_CPU_proof_sha256=refs['cpu_proof']['sha256'],
        original_vision_cache_path=str(cache_path), original_vision_cache_sha256=cpu['encoded_tensor_sha256'],
        original_model_identity_sha256=refs['model_identity']['sha256'], source_role=meta.get('source_role', meta.get('source_split')),
        all_source_exact_pts=points, physical_end_exact=clock['physical_end_exact'],
        original_input_evidence=cpu['input_evidence'])
    req['prompt'] = c.prompt(req)
    return req


def main():
    io.check_host(cpu=True)
    reg, reg_sha = io.registration()
    out = io.BASE/'plan_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(registration_sha256=reg_sha, pid=os.getpid(), utc=io.utc(), model_calls=0))
    planned, current = [], None
    try:
        identities = set()
        for row in reg['events']:
            current = row['event_id']
            req = event_request(row, reg['allowed_source_roles'])
            identity = (req['source_sha256'], req['original_case_id'], req['original_segment_index'])
            if identity in identities or req['request_id'] in {r['request_id'] for r in planned}:
                raise ValueError('Duplicate VERIFY event denominator')
            identities.add(identity)
            planned.append(req)
        io.save(out/'requests.json', planned)
        io.save(out/'completion.json', dict(status='PASS_EXTERNAL_VERIFY_PLAN_NOT_CPU_ADMISSION',
            registration_sha256=reg_sha, requests=len(planned), requests_sha256=io.sha(out/'requests.json'),
            code_files=io.code_files(), media_decodes=0, vision_processor_calls=0, model_calls=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_VERIFY_PLAN_NO_CACHE_FALLBACK',
            event_id=current, error_type=type(error).__name__, error=str(error), successful_requests=planned,
            report_original_cache_absence_to_main=isinstance(error, io.MissingOriginalCacheError),
            media_decodes=0, vision_processor_calls=0, model_calls=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main()
