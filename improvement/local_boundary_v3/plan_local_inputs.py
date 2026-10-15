"""Plan frozen 10..20 external B candidates; no decoding or processor import.

This command is intentionally Linux-only and requires a main-agent registration.
It does not pick candidates from labels, expand the cohort or admit a GPU job.
"""
import argparse
import os
from pathlib import Path

from lb_contract import (SCHEMA, CONTRACT_REVISION, ORIGINAL_EMPTY_PROMPT_SHA256, fraction,
                         normalized_clock, plan_endpoint, prompt, valid_id)
import hashlib
import lb_io as io


REGISTRATION_STATUS = 'FROZEN_EXTERNAL_NONTEST_LOCAL_BOUNDARY_V3_REVISION03'


def scope_metadata(reg):
    """Pure registration gate; reads no coarse answer, label or metric file."""
    scope = reg['validation_scope']
    count = len(reg['events'])
    if scope == 'ONE_EVENT_INTERFACE_SMOKE':
        role, exposed, source_scope, count_allowed = 'dev', True, 'EXTERNAL_NONTEST_DEVELOPMENT_ONLY', count == 1
    elif scope == 'EXTERNAL_DEVELOPMENT_DIAGNOSTIC':
        role, exposed, source_scope, count_allowed = 'dev', True, 'EXTERNAL_NONTEST_DEVELOPMENT_ONLY', 10 <= count <= 20
    elif scope == 'EXTERNAL_CONFIRMATION_DIAGNOSTIC':
        role, exposed, source_scope, count_allowed = 'confirm', False, 'EXTERNAL_NONTEST_CONFIRMATION_ONLY', 10 <= count <= 20
    else:
        raise ValueError('Unknown v3 validation scope; no implicit development/confirmation conversion')
    if (reg['schema'] != SCHEMA or reg['contract_revision'] != CONTRACT_REVISION or
            reg['status'] != REGISTRATION_STATUS or reg['source_scope'] != source_scope or
            reg['selection_frozen_before_new_model_results'] is not True or
            reg['existing_sources_are_exposed_development_not_new_confirmation'] is not exposed or
            reg['half_window_exact'] != '3' or reg['frames_per_request'] != 64 or
            not count_allowed or reg['endpoint_sides'] != ['start', 'end'] or
            reg['actual_model_call_budget'] != 2*count or reg['download_media'] is not False or
            reg['training'] is not False or not reg['official_rule_check_sha256'] or not reg['protocol_sha256']):
        raise ValueError('Main-agent frozen v3 scope/count/role/exposure/protocol is required')
    if scope != 'ONE_EVENT_INTERFACE_SMOKE':
        if reg.get('confirmation_event_extraction_frozen_before_development_results') is not True:
            raise ValueError('Confirmation event extraction must be frozen before development results')
        _frozen_metadata_reference(reg, 'confirmation_event_extraction')
    if role == 'confirm':
        if reg.get('confirmation_metrics_sealed_until_development_selection_frozen') is not True:
            raise ValueError('Confirmation quality metrics must remain sealed until frozen development selection')
        _frozen_metadata_reference(reg, 'development_selection')
    return dict(validation_scope=scope, required_source_role=role, exposed_development=exposed,
                source_scope=source_scope, event_count=count)


def _frozen_metadata_reference(reg, name):
    path, digest = reg.get(name+'_path'), reg.get(name+'_sha256')
    if (not isinstance(path, str) or not Path(path).is_absolute() or
            not isinstance(digest, str) or len(digest) != 64 or
            any(letter not in '0123456789abcdef' for letter in digest) or
            reg['required_files'].get(path) != digest):
        raise ValueError('An exact required-files binding is missing for '+name)


def event_scope_metadata(meta, scope):
    """Only frozen Charades role metadata may enter v3 event scopes."""
    source_path = Path(meta['source_path']).resolve()
    source_name = valid_id(meta['source_name'])
    if (meta.get('source_role') != scope['required_source_role'] or
            source_name in ('.', '..') or
            meta.get('source_id') != source_name or meta.get('source_group') != 'Charades:'+source_name or
            not any(source_path.is_relative_to((root/'media_01').resolve()) and
                    source_path.is_relative_to((root/'media_01'/source_name).resolve())
                    for root in io.CHARADES_MEDIA_ROOTS)):
        raise ValueError('V3 requires the registered Charades source role and actual admitted media path')
    return source_path


def accepted_event(row, scope):
    event_id = valid_id(row['event_id'])
    refs = row['original_evidence']
    paths = {name: io.checked_ref(refs[name]) for name in
             ('input', 'cpu_proof', 'done', 'raw', 'request', 'independent_replay', 'clock', 'source_separation')}
    meta, cpu, done, raw, request, replay, separation = [io.read(paths[name]) for name in
        ('input', 'cpu_proof', 'done', 'raw', 'request', 'independent_replay', 'source_separation')]
    source_path = event_scope_metadata(meta, scope)
    for name in ('done', 'raw', 'request', 'independent_replay'):
        if not paths[name].is_relative_to(io.COARSE_RECEIPT_ROOT.resolve()):
            raise ValueError('V3 Charades coarse/raw/replay evidence must use its independent coarse root')
    for name in ('input', 'cpu_proof', 'clock'):
        if not any(paths[name].is_relative_to(root.resolve()) for root in io.CHARADES_MEDIA_ROOTS):
            raise ValueError('V3 original native/input/proof must use the bound Charades roots')
    clock = io.extract_clock(io.read(paths['clock']), row['clock_object_keys'])
    points, _, origin, physical_end = normalized_clock(clock)
    case_id = valid_id(meta['case_id'])
    if (row['original_case_id'] != case_id or done['case_id'] != case_id or
            cpu['case_id'] != case_id or replay['case_id'] != case_id or
            request['case_id'] != case_id or meta['reference_available_to_inference'] is not False or
            meta['audio_observed'] is not False or request['reference_labels_read'] is not False or
            raw['actual_model_call'] is not True or done['status'] != 'MODEL_OK' or
            not replay['status'].startswith('PASS_') or replay['new_model_calls'] != 0 or
            cpu['new_model_calls'] != 0 or cpu['CPU_only'] is not True or
            not cpu['status'].startswith('PASS_CPU_') or not separation['status'].startswith('PASS_')):
        raise ValueError('Original accepted external request/model/CPU replay denominator changed')
    # No truth/source annotations are read here. The independent separation
    # receipt only binds already admitted non-test media bytes and identities.
    if (not separation.get('known_current_b_training_and_426_test_identities_complete',
                           separation.get('known_identity_complete', False)) or
            separation.get('identity_intersections') or separation.get('byte_intersections')):
        raise ValueError('Known training/test source identity separation is not complete')
    if (done['raw_sha256'] != refs['raw']['sha256'] or
            done['request_sha256'] != refs['request']['sha256'] or
            request['input_sha256'] != refs['input']['sha256'] or
            request['CPU_proof_sha256'] != refs['cpu_proof']['sha256'] or
            cpu['input_sha256'] != refs['input']['sha256'] or
            replay['done_sha256'] != refs['done']['sha256'] or
            replay['raw_sha256'] != refs['raw']['sha256'] or
            done['input_evidence'] != request['input_evidence'] or
            done['input_evidence'] != raw['input_evidence'] or
            done['input_evidence'] != cpu['input_evidence'] or
            done['input_evidence'] != replay['input_evidence']):
        raise ValueError('Old source/request/token/raw/independent-replay binding changed')
    if (hashlib.sha256(request['prompt'].encode()).hexdigest() != ORIGINAL_EMPTY_PROMPT_SHA256 or
            cpu['input_evidence']['prompt_sha256'] != ORIGINAL_EMPTY_PROMPT_SHA256):
        raise ValueError('Candidate must come from the original empty-capable B0 prompt')
    if (clock['source_sha256'] != meta['source_sha256'] or
            [str(p) for p in points] != meta['all_source_exact_pts'] or
            str(origin) != meta['original_clock_origin_exact'] or
            len(points) != meta['source_total_frames']):
        raise ValueError('Accepted original full clock/input source binding differs')
    segment = row['original_segment_index']
    if type(segment) is not int or not 0 <= segment < len(done['segments']):
        raise ValueError('An existing nonempty original B segment index is required')
    local_start, local_end = map(fraction, done['segments'][segment])
    lo, hi = fraction(done['source_start_exact']), fraction(done['source_end_exact'])
    if not 0 <= local_start < local_end <= hi-lo or hi > physical_end:
        raise ValueError('Original B exact local/source window conversion failed')
    interval = [str(lo+local_start), str(lo+local_end)]
    if row['original_interval_exact'] != interval:
        raise ValueError('Registered endpoint identity differs from original B normalized seconds')
    if not any(source_path.is_relative_to(p.resolve()) for p in io.MEDIA_ROOTS):
        raise ValueError('A test or unregistered media path cannot enter local-boundary preparation')
    reuse = row['reuse_rgb_inputs']
    if not reuse or refs['input'] not in reuse:
        raise ValueError('At least the accepted old RGB input must be listed for immutable reuse')
    for entry in reuse:
        cached = io.read(io.checked_ref(entry))
        if (cached['source_sha256'] != meta['source_sha256'] or
                cached['source_name'] != meta['source_name'] or cached.get('source_role') != meta['source_role'] or
                cached['reference_available_to_inference'] is not False or
                cached['audio_observed'] is not False):
            raise ValueError('Registered old RGB cache is not the same admitted external source')
    event = dict(event_id=event_id, original_case_id=case_id,
        original_segment_index=segment, original_interval_exact=interval,
        original_window_start_exact=str(lo), original_window_end_exact=str(hi),
        original_segment_window_local_exact=[str(local_start), str(local_end)],
        source_name=meta['source_name'], source_group=meta['source_group'],
        source_id=meta['source_id'], source_role=meta['source_role'],
        source_path=str(source_path), source_sha256=meta['source_sha256'],
        source_bytes=meta['source_bytes'], width=meta['width'], height=meta['height'],
        fps_num=meta['fps_num'], fps_den=meta['fps_den'], source_total_frames=len(points),
        all_source_exact_pts=[str(p) for p in points],
        original_clock_origin_exact=str(origin), original_evidence=refs,
        clock_object_keys=row['clock_object_keys'], reuse_rgb_inputs=reuse,
        reference_available_to_inference=False, audio_observed=False)
    return event, clock


def main(base, registration_path):
    io.host(cpu=True)
    base = io.base_path(base)
    registration_path = io.checked_ref(dict(path=str(registration_path),
        sha256=io.sha(registration_path)), roots=(base,))
    reg = io.read(registration_path)
    scope = scope_metadata(reg)
    io.checked_required(reg, base)
    out = base/'plan_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(registration_sha256=io.sha(registration_path),
        pid=os.getpid(), utc=io.utc(), new_model_calls=0, new_optimizer_updates=0))
    events, requests, current = [], [], None
    try:
        seen = set()
        for row in reg['events']:
            current = row['event_id']
            event, clock = accepted_event(row, scope)
            identity = (event['source_sha256'], event['original_case_id'], event['original_segment_index'])
            if event['event_id'] in seen or identity in seen:
                raise ValueError('Duplicate original candidate/event denominator')
            seen.update((event['event_id'], identity))
            events.append(event)
            for side in reg['endpoint_sides']:
                request = {**event, **plan_endpoint(event, side, clock)}
                request['prompt'] = prompt(request)
                requests.append(request)
        io.save(out/'events.json', events)
        io.save(out/'requests.json', requests)
        io.save(out/'completion.json', dict(status='PASS_FROZEN_LOCAL_BOUNDARY_PLAN_NOT_CPU_ADMISSION',
            registration_path=str(registration_path), registration_sha256=io.sha(registration_path),
            events=len(events), requests=len(requests), events_sha256=io.sha(out/'events.json'),
            validation_scope=scope['validation_scope'], scope_metadata=scope, scientific_quality_claim=False,
            requests_sha256=io.sha(out/'requests.json'), own_code_files=io.own_code_files(),
            new_media_downloads=0, new_complete_clock_decodes=0, new_model_calls=0,
            new_optimizer_updates=0, GPU_launch_admitted=False))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_PLAN_KEEP_OLD_AND_NEW_SUCCESS_EVIDENCE',
            event_id=current, error=repr(error), planned_events=events,
            new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('--registration', type=Path, required=True)
    args = parser.parse_args()
    # CPU child only; this module is never a chain-parent launcher.
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main(args.base, args.registration)
