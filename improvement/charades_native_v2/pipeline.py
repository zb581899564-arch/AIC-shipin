"""Immutable inherited successes plus first remaining Charades preparation.

Registration is separate from run. No GPU, model, evaluation or training here.
Partial author references are not whole-source complete GT.
"""
import argparse
import json
import os
import traceback
from pathlib import Path

from charades_v2_common import (ROOT, V1ROOT, KNOWN, CACHE_DEPENDENCIES,
    append, assert_cpu_host, check_metadata, identity_hits, known_metadata,
    read, require, resource_snapshot, save, sha, utc, verify_registration)


def bound(path, digest, bindings):
    path = Path(path)
    require(path.is_file() and sha(path) == digest, 'Frozen inherited artifact changed: '+str(path))
    bindings[str(path)] = digest
    return read(path)


def take_reserve(reserves, role, owners, used, references, aliases):
    for candidate in reserves:
        sid = candidate['source_id']
        subject = references[sid]['worker_subject_id']
        if sid not in used and owners.get(subject, role) == role and not identity_hits(candidate, aliases):
            require(not (V1ROOT/'media_01'/sid).exists(), 'Attempted old member is never a new replacement')
            used.add(sid)
            owners[subject] = role
            return {**candidate, 'role': role}
    raise ValueError('Frozen unused worker-compatible engineering pool exhausted for '+role)


def register():
    assert_cpu_host()
    require(not (ROOT/'registration_01.json').exists(), 'Already registered; do not repeat')
    protocol = read(ROOT/'partial_native_protocol_01.json')
    require(protocol['approved'] and protocol['linux_root'] == str(ROOT), 'New explicit independent scope required')
    require(protocol['sources'] == 21 and protocol['dev'] == 11 and protocol['confirm'] == 10,
            'Explicit v2 inherited11 plus corrected10 scope')
    _, metadata, bindings = check_metadata()
    snapshot, aliases, known_hashes, provenance = known_metadata()
    bindings.update(provenance)
    for path in [ROOT/'partial_native_protocol_01.json', ROOT/'scope_02.json', KNOWN,
                 V1ROOT/'registration_01.json', V1ROOT/'source_registry_02.json',
                 V1ROOT/'partial_v2_cohort_draft_01.json', V1ROOT/'native_chain_stop_receipt_01.json',
                 V1ROOT/'native_chain_01/failure.json', V1ROOT/'preflight_01/author_reference_pool_01.json',
                 V1ROOT/'preflight_01/known_metadata_identity_01.json',
                 ROOT/'cpu_revision01_pure_check.json', ROOT/'cpu_revision02_pure_check.json',
                 ROOT/'preparation_smoke_01.json', ROOT/'endpoint_resolution_diagnostic_01.json']:
        bindings[str(path)] = sha(path)
    scope = read(ROOT/'scope_02.json')
    require(scope['source_count'] == 21 and scope['role_counts'] == {'dev': 11, 'confirm': 10}
            and scope['model_admitted'] is False, 'Current exact partial reference scope required')
    pure02 = read(ROOT/'cpu_revision02_pure_check.json')
    require(pure02['code_sha256'] == sha(ROOT/'code/charades_cpu.py') and
            pure02['strict_physical_domain_actions_eligible'] is True and
            pure02['original_text_preserved'] is True and pure02['model_calls'] == 0,
            'Current CPU revision short-action pure evidence required')
    draft = read(V1ROOT/'partial_v2_cohort_draft_01.json')
    original_registry = read(V1ROOT/'source_registry_02.json')
    refs_path = V1ROOT/'preflight_01/author_reference_pool_01.json'
    refs = {x['source_id']: x for x in read(refs_path)['references']}
    require(len(refs) == 60, 'Reuse exact already successful author metadata; no ZIP/schema repeat')
    rows = {x['source_id']: x for x in metadata['rows']}
    require(len(draft['dev']) == 11 and len(draft['confirm']) == 10, 'Fixed inherited and fresh cohort counts')
    old_complete = {p.parent.name for p in (V1ROOT/'media_01').glob('*/completion.json')}
    old_clocks = {p.parent.name for p in (V1ROOT/'native_01').glob('*/native_clock.json')}
    require(old_complete == old_clocks == {x['source_id'] for x in draft['dev']},
            'Every complete old media/native success must be inherited, never selected by reference quality')
    require([x['source_id'] for x in draft['confirm']] ==
            [x['source']['source_id'] for x in original_registry['slots'] if x['role'] == 'confirm'],
            'Original corrected confirmation identity/order must remain')
    require(not Path('/proc/'+str(read(V1ROOT/'native_chain_01/claim.json')['pid'])).exists(),
            'Old chain must really have terminated before independent remaining preparation')
    slots, owners, inherited_proofs, inherited_hashes = [], {}, [], set()
    for index, entry in enumerate(draft['dev']+draft['confirm'], 1):
        sid, role = entry['source_id'], entry['role']
        subject = refs[sid]['worker_subject_id']
        require(subject == entry['subject'] and owners.get(subject, role) == role,
                'Author worker group identity changed or crossed roles')
        require(not identity_hits(rows[sid], aliases), 'Known B/protected426 metadata alias intersection')
        owners[subject] = role
        slot = dict(slot=index, role=role, source={**rows[sid], 'role':role},
                    worker_subject_id=subject, inherited=role == 'dev')
        if role == 'dev':
            media = bound(entry['old_media_receipt_path'], entry['old_media_receipt_sha256'], bindings)
            wrapper = bound(entry['old_clock_path'], entry['old_clock_sha256'], bindings)
            clock = wrapper['clock']
            require(media['source_id'] == sid and clock['source_id'] == sid and
                    clock['source_sha256'] == media['sha256'] and media['known_byte_separation_pass']
                    and media['sha256'] not in known_hashes and media['sha256'] not in inherited_hashes,
                    'Exact inherited media/native identity or byte separation failed')
            require(Path(media['path']).resolve().is_relative_to(V1ROOT/'media_01') and
                    Path(media['path']).stat().st_size == media['bytes'], 'Inherited media receipt/size changed')
            inherited_hashes.add(media['sha256'])
            slot['inherited_entry'] = entry
            if 'old_CPU_completion_path' in entry:
                completed = bound(entry['old_CPU_completion_path'], entry['old_CPU_completion_sha256'], bindings)
                require(completed['status'] == 'PASS_CHARADES_SOURCE_NATIVE64_CPU_INPUTS_NOT_GPU_ADMISSION'
                        and completed['source_id'] == sid and completed['role'] == 'dev'
                        and completed['native_clock_sha256'] == entry['old_clock_sha256'],
                        'Exact old CPU success identity changed')
                for proof in completed['proofs']:
                    oldproof = bound(proof['proof_path'], proof['proof_sha256'], bindings)
                    require(oldproof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT', 'Old actual CPU proof required')
                    bound(proof['input_path'], proof['input_sha256'], bindings)
                    require(Path(proof['encoded_tensor_path']).is_file(), 'Old lossless CPU tensor must remain resident')
                    inherited_proofs.append(dict(case_id=proof['case_id'], proof_path=proof['proof_path'], proof_sha256=proof['proof_sha256']))
        else:
            require(not (V1ROOT/'media_01'/sid).exists(), 'Fresh confirmation media was already attempted')
            require(entry['member'] == rows[sid]['member'], 'Fresh confirmation frozen CD member changed')
        slots.append(slot)
    require(inherited_proofs == draft['old_CPU_proofs'] and len(inherited_proofs) == 4,
            'All four actual successful CPU proofs must be referenced exactly')
    dev_workers = {x['worker_subject_id'] for x in slots if x['role'] == 'dev'}
    confirm_workers = {x['worker_subject_id'] for x in slots if x['role'] == 'confirm'}
    require(not dev_workers & confirm_workers and len({x['source']['source_id'] for x in slots}) == 21,
            'Worker-disjoint21 frozen source identities required')
    fresh = [x['source']['member'] for x in slots if not x['inherited']]
    require(sum(x['compressed_bytes'] for x in fresh) == 43197028 and sum(x['bytes'] for x in fresh) == 43450502,
            'Specific fresh ten-member budgets changed')
    used = {x['source']['source_id'] for x in slots} | {p.name for p in (V1ROOT/'media_01').iterdir() if p.is_dir()}
    registry_path = ROOT/'source_registry_01.json'
    save(registry_path, dict(status='FROZEN_V2_21_WORKER_GROUPS_AND_SUCCESS_INHERITANCE_BEFORE_MODEL',
        utc=utc(), slots=slots, sources=21, dev=11, confirm=10, inherited_native_sources=11,
        inherited_CPU_sources=2, inherited_CPU_proofs=inherited_proofs,
        original_ordered_engineering_reserves=original_registry['original_ordered_engineering_reserves'],
        used_or_prior_attempted_source_ids=sorted(used), worker_subject_owners=owners,
        dev_worker_subjects=sorted(dev_workers), confirm_worker_subjects=sorted(confirm_workers),
        worker_intersection=[], worker_groups_disjoint=True, all_visible_actor_scene_household_disjoint='UNKNOWN',
        global_pretraining_overlap='UNKNOWN', fresh_compressed_bytes=43197028, fresh_raw_bytes=43450502,
        partial_KPNJ5_preserved_not_resumed=True,
        selection='All11 old complete media/native in actual order plus original corrected10confirmation. No action counts, endpoints, quality or model output choose sources.',
        replacements='Only unused original SHA-ranked same-role-compatible engineer/identity failures; never reference eligibility, network or processor errors.'))
    isolation_path = V1ROOT/'preflight_01/known_metadata_identity_01.json'
    require(set(read(isolation_path)['known_bytes_sha256']) == known_hashes, 'Old metadata identity population changed')
    bindings[str(registry_path)] = sha(registry_path)
    for path, digest in CACHE_DEPENDENCIES.items():
        require(sha(path) == digest, 'Frozen helper2 dependency changed')
        bindings[path] = digest
    for path in sorted(Path(__file__).resolve().parent.glob('*.py')):
        bindings[str(path)] = sha(path)
    require(any(p.endswith('/charades_cpu.py') for p in bindings), 'CPU module must be deployed before registration')
    resources = resource_snapshot()
    require(protocol['max_working_output_estimate_bytes']+43197028+43450502 < resources['disk_available_bytes'],
            'Concrete remaining output does not fit current capacity')
    reg_path = ROOT/'registration_01.json'
    save(reg_path, dict(status='REGISTERED_UNIQUE_V2_REMAINING_PREPARATION_NOT_GPU', utc=utc(),
        input_and_code_bindings=bindings, registry_path=str(registry_path), reference_pool_path=str(refs_path),
        known_isolation_path=str(isolation_path), archive=metadata['archive'], protocol_path=str(ROOT/'partial_native_protocol_01.json'),
        sources=21, dev=11, confirm=10, new_GPU_admitted=False, new_optimizer_updates=0,
        new_model_parameters_plan=8782459120, inherited_native_clocks=11, inherited_successful_CPU_proofs=4,
        new_clock_decodes_plan=10, old_domain_rejected_first_RGB_CPU_plan=9,
        fresh_media_compressed_bytes=43197028, fresh_media_raw_bytes=43450502,
        scope='Clear-boundary author action timing proxy only. Partial eligible-action union is never complete whole-source GT.',
        old_successes_and_old_full_domain_failures_preserved=True,
        resources_before_chain=resources))
    print(json.dumps(dict(status='V2_REGISTERED_READY_FOR_MAIN_REVIEW_NOT_LAUNCHED',
        registration_path=str(reg_path), registration_sha256=sha(reg_path), source_registry_path=str(registry_path),
        sources=21, dev=11, confirm=10, inherited_clocks=11, inherited_CPU_proofs=4,
        fresh_compressed_bytes=43197028, fresh_raw_bytes=43450502, new_model_calls=0)), flush=True)


def run():
    assert_cpu_host()
    reg, reg_sha = verify_registration()
    registry = read(reg['registry_path'])
    refs = {x['source_id']:x for x in read(reg['reference_pool_path'])['references']}
    known_hashes = set(read(reg['known_isolation_path'])['known_bytes_sha256'])
    _, aliases, current_hashes, _ = known_metadata()
    require(current_hashes == known_hashes, 'Known metadata identity changed')
    from archive_member import download_member
    from charades_cpu import prepare_source, NativeEndpointError
    chain = ROOT/'native_chain_01'
    chain.mkdir(exist_ok=False)
    (ROOT/'media_01').mkdir(exist_ok=False)
    (ROOT/'native_01').mkdir(exist_ok=False)
    save(chain/'claim.json', dict(pid=os.getpid(), utc=utc(), registration_sha256=reg_sha,
        sources=reg['sources'], dev=reg['dev'], confirm=reg['confirm'], model_calls=0,
        original_complete_clock_decodes_to_repeat=0, original_CPU_encodes_to_repeat=0))
    accepted, downloaded, rejected, seen_bytes = [], [], [], set()
    used = set(registry['used_or_prior_attempted_source_ids'])
    owners = dict(registry['worker_subject_owners'])
    current = None
    try:
        for slot in registry['slots']:
            source, role, inherited = slot['source'], slot['role'], slot['inherited']
            while True:
                current = source['source_id']
                assert_cpu_host()
                require(not identity_hits(source, aliases), 'Known metadata alias intersects candidate')
                subject = refs[current]['worker_subject_id']
                require(owners.get(subject, role) == role, 'Cross-worker role identity forbidden')
                owners[subject] = role
                append(chain/'events.jsonl', dict(event='SOURCE_BEGIN', source_id=current, slot=slot['slot'],
                    role=role, inherited_media_native=inherited, worker_subject_id=subject, utc=utc()))
                if inherited:
                    entry = slot['inherited_entry']
                    media_path = Path(entry['old_media_receipt_path'])
                    require(sha(media_path) == entry['old_media_receipt_sha256'], 'Inherited media receipt changed')
                    media = dict(read(media_path), existing_native_clock_path=entry['old_clock_path'],
                                 existing_native_clock_sha256=entry['old_clock_sha256'])
                    if 'old_CPU_completion_path' in entry:
                        media.update(existing_CPU_completion_path=entry['old_CPU_completion_path'],
                                     existing_CPU_completion_sha256=entry['old_CPU_completion_sha256'])
                else:
                    media = download_member(source, reg['archive'], known_hashes, reg_sha)
                    downloaded.append(media)
                    media_path = ROOT/'media_01'/current/'completion.json'
                if media['sha256'] in seen_bytes or not media['known_byte_separation_pass']:
                    rejected.append(dict(slot=slot['slot'], source_id=current, role=role,
                        reason='ACTUAL_BYTE_IDENTITY_INTERSECTION', media_receipt_path=str(media_path), utc=utc()))
                else:
                    reference_path = ROOT/'references_01'/(current+'.json')
                    save(reference_path, refs[current])
                    source_out = ROOT/'native_01'/current
                    try:
                        prepared = prepare_source(source, media, refs[current], source_out,
                            dict(registration_sha256=reg_sha, source_registry_sha256=sha(reg['registry_path']),
                                 media_receipt_sha256=sha(media_path), original_metadata_manifest_sha256=
                                 read(V1ROOT/'media_native_protocol_01.json')['source_manifest_sha256']))
                    except NativeEndpointError as err:
                        rejected.append(dict(slot=slot['slot'], source_id=current, role=role,
                            reason='NATIVE_CLOCK_OR_NATIVE64_ENGINEERING_UNUSABLE', error=str(err),
                            media_success_preserved=True, utc=utc()))
                        save(source_out/'engineering_failure.json', rejected[-1])
                    else:
                        seen_bytes.add(media['sha256'])
                        accepted.append(dict(slot=slot['slot'], source_id=current, role=role,
                            worker_subject_id=subject, source_rank=source['rank'], inherited_media_native=inherited,
                            reference_path=str(reference_path), reference_sha256=sha(reference_path),
                            media_receipt_path=str(media_path), media_receipt_sha256=sha(media_path),
                            CPU_completion_path=str(source_out/'completion.json'),
                            CPU_completion_sha256=sha(source_out/'completion.json'), preparation=prepared))
                        append(chain/'events.jsonl', dict(event='SOURCE_NATIVE_CPU_ACCEPTED', source_id=current,
                            accepted_sources=len(accepted), slot=slot['slot'], utc=utc()))
                        print(json.dumps(dict(source_id=current, accepted_sources=len(accepted),
                            CPU_windows=len(prepared['proofs']), new_processor_encodes=prepared['actual_new_processor_encodes'],
                            new_model_calls=0)), flush=True)
                        break
                # No annotation-domain exception can enter this replacement branch.
                append(chain/'events.jsonl', dict(event='ENGINEERING_REJECTION_PRESERVE_SUCCESS', **rejected[-1]))
                require(not inherited, 'All11 inherited native sources remain in v2; unexpected engineering failure requires review')
                source = take_reserve(registry['original_ordered_engineering_reserves'], role, owners, used, refs, aliases)
                inherited = False
            require(resource_snapshot()['own_output_bytes'] <= read(reg['protocol_path'])['max_working_output_estimate_bytes'],
                    'Actual working output exceeded registered capacity estimate')
        require(len(accepted) == reg['sources'] and sum(x['role']=='dev' for x in accepted) == reg['dev']
                and sum(x['role']=='confirm' for x in accepted) == reg['confirm'], 'Exact registered source/role denominator')
        require(not {x['worker_subject_id'] for x in accepted if x['role']=='dev'} &
                    {x['worker_subject_id'] for x in accepted if x['role']=='confirm'}, 'Effective worker role separation')
        effective_path = ROOT/'effective_source_registry_02.json'
        save(effective_path, dict(status='FROZEN_V2_ALL_ACTUAL_NATIVE_CPU_SOURCES_BEFORE_MODEL',
            registration_sha256=reg_sha, source_registry_sha256=sha(reg['registry_path']),
            sources=reg['sources'], dev=reg['dev'], confirm=reg['confirm'], accepted=accepted,
            rejected_engineering_or_identity=rejected, worker_subject_owners=owners, worker_groups_disjoint=True,
            all_visible_actor_household_scene_global_pretraining_disjoint='UNKNOWN',
            source_selection_uses_reference_quality_or_model=False, new_model_calls=0))
        coarse_rows = [{**proof, 'source_id':source['source_id'], 'source_role':source['role'],
                       'worker_subject_id':source['worker_subject_id'],
                       'CPU_completion_path':source['CPU_completion_path'],
                       'CPU_completion_sha256':source['CPU_completion_sha256']}
                      for source in accepted for proof in source['preparation']['proofs']]
        require(len({x['case_id'] for x in coarse_rows}) == len(coarse_rows), 'Unique real coarse cases')
        coarse_path = ROOT/'coarse_inputs_01.json'
        save(coarse_path, dict(status='PASS_V2_NATIVE64_COARSE_INPUTS_NOT_GPU_ADMISSION',
            effective_source_registry_sha256=sha(effective_path), sources=reg['sources'], rows=coarse_rows,
            windows=len(coarse_rows), new_model_calls=0, new_optimizer_updates=0, GPU_launch_admitted=False,
            encoded_cache_format='TORCH_SAVE_GZIP_LOSSLESS_LEVEL1', inherited_CPU_inputs=4))
        coverage = []
        for source in accepted:
            c = read(source['CPU_completion_path'])
            coverage.append(dict(source_id=source['source_id'], role=source['role'],
                reference_validation_path=c['reference_validation_path'],
                reference_validation_sha256=c['reference_validation_sha256']))
        save(ROOT/'reference_coverage_manifest_01.json', dict(status='PARTIAL_AUTHOR_BOUNDARY_PROXY_COVERAGE_NOT_WHOLE_SOURCE_GT',
            sources=reg['sources'], rows=coverage,
            complete_source_precision_F1_against_partial_action_union_permitted=False,
            original_or_censored_reference_quality_used_to_select_source=False))
        save(ROOT/'media_01/completion.json', dict(status='PASS_ONLY_REMAINING_PINNED_MEMBERS_NO_OLD_MEDIA_REPEATS',
            registration_sha256=reg_sha, downloaded_members=downloaded, successful_downloads=len(downloaded),
            inherited_complete_media=11, compressed_body_bytes=sum(x['compressed_bytes'] for x in downloaded),
            uncompressed_bytes=sum(x['bytes'] for x in downloaded), new_model_calls=0))
        result = dict(status='PASS_V2_NATIVE_CPU_INPUTS_PENDING_MAIN_INDEPENDENT_GPU_ADMISSION', utc=utc(),
            registration_sha256=reg_sha, effective_registry_path=str(effective_path), effective_registry_sha256=sha(effective_path),
            sources=reg['sources'], dev=reg['dev'], confirm=reg['confirm'], accepted=accepted,
            rejected_engineering_or_identity=rejected, CPU_windows=len(coarse_rows), inherited_CPU_inputs=4,
            coarse_input_manifest_path=str(coarse_path), coarse_input_manifest_sha256=sha(coarse_path),
            media_completion_sha256=sha(ROOT/'media_01/completion.json'),
            new_model_calls=0, new_optimizer_updates=0, new_GPU_admitted=False,
            no_reference_labels_in_model_input=True, old_successful_stage_repeated=False,
            resource_snapshot=resource_snapshot())
        save(chain/'completion.json', result)
        print(json.dumps(dict(status=result['status'], sources=reg['sources'], CPU_windows=len(coarse_rows),
            compressed_body_bytes=sum(x['compressed_bytes'] for x in downloaded), new_model_calls=0)), flush=True)
    except BaseException as err:
        save(chain/'failure.json', dict(status='STOP_KEEP_INHERITED_AND_ALL_NEW_SUCCESS_PARTIAL',
            utc=utc(), current_source=current, error=repr(err), traceback=traceback.format_exc(),
            accepted=accepted, successful_downloads=downloaded, engineering_rejections=rejected,
            recovery='Separate explicit remaining recovery only; never repeat successful media, complete clocks, RGB or processor.',
            new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['register', 'run'])
    args = parser.parse_args()
    globals()[args.stage]()
