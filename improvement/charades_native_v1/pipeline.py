"""Register then prepare twenty Charades sources once; GPU is never started."""
import argparse
import csv
import hashlib
import io
import os
import re
import traceback
import zipfile
from pathlib import Path
from fractions import Fraction as F
from charades_common import (ROOT, KNOWN, CACHE_DEPENDENCIES, append, assert_cpu_host,
    check_metadata, identity_hits, known_metadata, read, require, resource_snapshot,
    save, sha, utc, verify_registration)


def author_metadata(manifest):
    with zipfile.ZipFile(ROOT/'metadata_01/Charades.zip') as archive:
        readme = archive.read('Charades/README.txt').decode('utf-8')
        require('Unique identifier for each subject in the dataset' in readme, 'Subject identity definition missing')
        table = csv.DictReader(io.StringIO(archive.read('Charades/Charades_v1_train.csv').decode('utf-8-sig')))
        wanted = {x['source_id'] for x in manifest['rows']}
        references = {}
        for row in table:
            if row['id'] not in wanted:
                continue
            require(row['id'] not in references and re.fullmatch(r'[A-Za-z0-9]{4}', row['subject']),
                    'Distinct author row with real subject ID required')
            actions = []
            for token in row['actions'].split(';'):
                if not token:
                    continue
                fields = token.split()
                require(len(fields) == 3 and re.fullmatch(r'c[0-9]{3}', fields[0]), 'Original author action schema malformed')
                # Parsing is exact; domain is checked against actual native clock.
                F(fields[1]); F(fields[2])
                actions.append(dict(class_id=fields[0], start_exact=fields[1], end_exact=fields[2]))
            references[row['id']] = dict(source_id=row['id'], worker_subject_id=row['subject'],
                author_length_raw=row['length'], actions=actions, original_actions_raw=row['actions'],
                action_semantics='Author action localization, not unconditional highlight/crop truth',
                action_subsecond_boundary_precision='NOT_ESTABLISHED', reference_available_to_model=False,
                source_selection_fields=['id', 'subject_only_for_identity_group_separation'])
    require(set(references) == wanted, 'Complete fixed metadata source reference population required')
    return references


def take_reserve(reserve, role, owners, used, references, aliases):
    for candidate in reserve:
        sid = candidate['source_id']
        subject = references[sid]['worker_subject_id']
        if sid not in used and owners.get(subject, role) == role and not identity_hits(candidate, aliases):
            used.add(sid)
            owners[subject] = role
            return candidate
    raise ValueError('Frozen engineering/identity replacement pool exhausted for role '+role)


def register():
    assert_cpu_host()
    require(not (ROOT/'registration_01.json').exists(), 'Already registered; do not repeat')
    protocol, manifest, bindings = check_metadata()
    snapshot, aliases, known_hashes, provenance = known_metadata()
    refs = author_metadata(manifest)
    preflight = ROOT/'preflight_01'
    preflight.mkdir(exist_ok=False)
    references_path = preflight/'author_reference_pool_01.json'
    save(references_path, dict(status='EXACT_AUTHOR_SELECTED60_REFERENCES_ISOLATED_FROM_MODEL',
         metadata_source_manifest_sha256=sha(ROOT/'metadata_01/source_manifest_01.json'),
         references=[refs[x['source_id']] for x in manifest['rows']], new_model_calls=0))
    used, owners, slots, excluded = set(), {}, [], []
    reserves = manifest['rows'][20:]
    alias_checks = [dict(source_id=x['source_id'], hits=identity_hits(x, aliases)) for x in manifest['rows']]
    # Original dev precedes confirm. Retain those source/group identities unless
    # there is an explicit metadata identity intersection, never action quality.
    for slot_index, original in enumerate(manifest['rows'][:20], 1):
        role = 'dev' if slot_index <= 10 else 'confirm'
        candidate = original
        subject = refs[candidate['source_id']]['worker_subject_id']
        cross_subject = subject in owners and owners[subject] != role
        hits = identity_hits(candidate, aliases)
        if cross_subject or hits:
            excluded.append(dict(slot=slot_index, original_source_id=original['source_id'], role=role,
                worker_subject_id=subject, reason='CROSS_DEV_CONFIRM_WORKER_SUBJECT_IDENTITY' if cross_subject else 'KNOWN_B602_OR426_METADATA_ALIAS',
                known_alias_hits=hits, media_will_not_be_downloaded=True))
            candidate = take_reserve(reserves, role, owners, used, refs, aliases)
            subject = refs[candidate['source_id']]['worker_subject_id']
        else:
            used.add(candidate['source_id']); owners[subject] = role
        slots.append(dict(slot=slot_index, role=role, source={**candidate, 'role':role},
                          original_primary_source_id=original['source_id'], worker_subject_id=subject))
    require(len(slots) == 20 and len({x['source']['source_id'] for x in slots}) == 20, 'Twenty final metadata primary identities')
    dev_subjects = {x['worker_subject_id'] for x in slots if x['role'] == 'dev'}
    confirm_subjects = {x['worker_subject_id'] for x in slots if x['role'] == 'confirm'}
    require(not dev_subjects & confirm_subjects, 'Primary worker groups still cross roles')
    registry_path = ROOT/'source_registry_02.json'
    registry = dict(status='FROZEN_PRE_MEDIA_WORKER_GROUP_IDENTITY_CORRECTION_NOT_NATIVE_ADMISSION',
        utc=utc(), original_metadata_manifest_sha256=sha(ROOT/'metadata_01/source_manifest_01.json'),
        slots=slots, original_ordered_engineering_reserves=reserves, excluded_original_primary=excluded,
        primary_sources=20, dev_sources=10, confirm_sources=10, worker_subject_owners=owners,
        dev_worker_subjects=sorted(dev_subjects), confirm_worker_subjects=sorted(confirm_subjects),
        worker_groups_disjoint=True, all_visible_actor_household_or_scene_disjoint='UNKNOWN',
        pretraining_overlap='UNKNOWN', primary_compressed_media_bytes=sum(x['source']['member']['compressed_bytes'] for x in slots),
        primary_uncompressed_media_bytes=sum(x['source']['member']['bytes'] for x in slots),
        all60_compressed_media_cap=protocol['all60_compressed_media_bytes_budget'],
        selection='Original source SHA rank; exclude exact known aliases/cross-group subject; substitute first compatible preordered reserve. No action/quality/prediction field selects a source.',
        later_replacement='Only native endpoint/insufficient-native engineering or actual byte identity failure. Always first unused same-role-compatible original reserve; never network/processor/model/quality-based swapping.',
        all_effective_source_ids_and_group_owners_must_freeze_before_first_model=True)
    save(registry_path, registry)
    isolation_path = preflight/'known_metadata_identity_01.json'
    save(isolation_path, dict(status='PASS_METADATA_ONLY_B602_PROTECTED426_ALIAS_AND_WORKER_GROUP_PRECHECK',
        snapshot_path=str(KNOWN), snapshot_sha256=sha(KNOWN), known_B_original_groups=602,
        known_B_registered_clips=704, protected_test_metadata_sources=426,
        alias_checks=alias_checks, known_bytes_sha256=sorted(known_hashes),
        current_training_metadata_provenance=provenance, worker_groups_disjoint=True,
        unknowns=['Global base pretraining overlap', 'Reencoded/excerpt source overlaps',
                  'Hidden official original source IDs', 'All visible actors/households/scenes independence'],
        protected_test_media_or_GT_read=False, new_model_calls=0))
    for path, digest in CACHE_DEPENDENCIES.items():
        require(sha(path) == digest, 'Frozen lossless tensor helper changed or not deployed')
        bindings[path] = digest
    bindings.update(provenance)
    for path in [KNOWN, registry_path, references_path, isolation_path]:
        bindings[str(path)] = sha(path)
    for path in sorted(Path(__file__).resolve().parent.glob('*.py')):
        bindings[str(path)] = sha(path)
    require(any(p.endswith('/charades_cpu.py') for p in bindings), 'CPU implementation must be deployed before registration')
    resources = resource_snapshot()
    require(protocol['max_working_output_estimate_bytes']+registry['primary_uncompressed_media_bytes']
            +registry['primary_compressed_media_bytes'] < resources['disk_available_bytes'],
            'Registered concrete expected output does not fit current capacity')
    save(ROOT/'registration_01.json', dict(status='REGISTERED_UNIQUE_NEW20_MEDIA_NATIVE_CPU_CHAIN_NOT_GPU',
        utc=utc(), input_and_code_bindings=bindings, registry_path=str(registry_path),
        reference_pool_path=str(references_path), known_isolation_path=str(isolation_path),
        archive=manifest['archive'], protocol_path=str(ROOT/'media_native_protocol_01.json'),
        sources=20, dev=10, confirm=10, new_GPU_admitted=False, new_optimizer_updates=0,
        new_model_parameters_plan=8782459120, source_licenses='Original AI2 author license: academic/nonprofit/evaluation only, no third-party media/data distribution or modified public release.',
        downloaded_media_and_original_clock_success_must_not_repeat=True,
        CPU_scope='New exact native64 RGB and original B0 processor once per new coarse window; save lossless gzip original tensors. No labels in request, no GPU/optimizer.',
        resources_before_chain=resources))
    print(__import__('json').dumps(dict(status='REGISTERED_READY_FOR_MAIN_REVIEW_NOT_LAUNCHED',
        registration_path=str(ROOT/'registration_01.json'), registration_sha256=sha(ROOT/'registration_01.json'),
        registry_path=str(registry_path), metadata_excluded=excluded,
        primary_compressed_media_bytes=registry['primary_compressed_media_bytes'],
        primary_uncompressed_media_bytes=registry['primary_uncompressed_media_bytes'],
        sources=20, dev=10, confirm=10, new_model_calls=0)), flush=True)


def run():
    assert_cpu_host()
    reg, reg_sha = verify_registration()
    registry = read(reg['registry_path'])
    refs = {x['source_id']:x for x in read(reg['reference_pool_path'])['references']}
    isolated = read(reg['known_isolation_path'])
    known_hashes = set(isolated['known_bytes_sha256'])
    _, aliases, current_hashes, _ = known_metadata()
    require(current_hashes == known_hashes, 'Known current identity hash metadata changed')
    from archive_member import download_member
    from charades_cpu import prepare_source, NativeEndpointError
    chain = ROOT/'native_chain_01'
    chain.mkdir(exist_ok=False)
    (ROOT/'media_01').mkdir(exist_ok=False)
    (ROOT/'native_01').mkdir(exist_ok=False)
    save(chain/'claim.json', dict(pid=os.getpid(), utc=utc(), registration_sha256=reg_sha,
         sources=20, model_calls=0, original_metadata_success_repeated=False))
    accepted, downloaded, rejected, seen_bytes = [], [], [], set()
    used = {x['source']['source_id'] for x in registry['slots']}
    owners = dict(registry['worker_subject_owners'])
    current = None
    try:
        for slot in registry['slots']:
            role, source = slot['role'], slot['source']
            while True:
                current = source['source_id']
                assert_cpu_host()
                require(not identity_hits(source, aliases), 'Candidate known metadata alias intersection')
                subject = refs[current]['worker_subject_id']
                require(owners.get(subject, role) == role, 'Cross-group worker replacement forbidden')
                owners[subject] = role
                append(chain/'events.jsonl', dict(event='SOURCE_BEGIN', slot=slot['slot'], source_id=current,
                     role=role, worker_subject_id=subject, utc=utc()))
                media = download_member(source, reg['archive'], known_hashes, reg_sha)
                downloaded.append(media)
                if media['sha256'] in seen_bytes or not media['known_byte_separation_pass']:
                    reason = 'ACTUAL_BYTE_IDENTITY_INTERSECTION'
                    rejected.append(dict(slot=slot['slot'], source_id=current, role=role, reason=reason,
                         media_receipt_path=str(ROOT/'media_01'/current/'completion.json'), utc=utc()))
                else:
                    source_out = ROOT/'native_01'/current
                    reference = refs[current]
                    reference_path = ROOT/'references_01'/(current+'.json')
                    save(reference_path, reference)
                    try:
                        prepared = prepare_source(source, media, reference, source_out,
                            dict(registration_sha256=reg_sha, source_registry_02_sha256=sha(reg['registry_path']),
                                 media_receipt_sha256=sha(ROOT/'media_01'/current/'completion.json'),
                                 original_metadata_manifest_sha256=read(reg['protocol_path'])['source_manifest_sha256']))
                    except NativeEndpointError as err:
                        rejected.append(dict(slot=slot['slot'], source_id=current, role=role,
                            reason='ACTUAL_NATIVE_ENDPOINT_OR_NATIVE64_ENGINEERING_UNUSABLE',
                            error=str(err), native_complete_clock_preserved=(source_out/'native_clock.json').exists(),
                            media_success_preserved=True, utc=utc()))
                        save(source_out/'engineering_failure.json', rejected[-1])
                    else:
                        seen_bytes.add(media['sha256'])
                        accepted.append(dict(slot=slot['slot'], source_id=current, role=role,
                            worker_subject_id=subject, source_rank=source['rank'],
                            reference_path=str(reference_path), reference_sha256=sha(reference_path),
                            media_receipt_path=str(ROOT/'media_01'/current/'completion.json'),
                            media_receipt_sha256=sha(ROOT/'media_01'/current/'completion.json'),
                            CPU_completion_path=str(source_out/'completion.json'),
                            CPU_completion_sha256=sha(source_out/'completion.json'), preparation=prepared))
                        append(chain/'events.jsonl', dict(event='SOURCE_NATIVE_CPU_ACCEPTED', source_id=current,
                             accepted_sources=len(accepted), slot=slot['slot'], utc=utc()))
                        print(__import__('json').dumps(dict(accepted_sources=len(accepted), source_id=current,
                             CPU_windows=len(prepared['proofs']), new_model_calls=0)), flush=True)
                        break
                append(chain/'events.jsonl', dict(event='ENGINEERING_SOURCE_REJECTED_PRESERVE_SUCCESS', **rejected[-1]))
                replacement = take_reserve(registry['original_ordered_engineering_reserves'], role, owners, used, refs, aliases)
                source = {**replacement, 'role':role}
            resources = resource_snapshot()
            require(resources['own_output_bytes'] <= read(reg['protocol_path'])['max_working_output_estimate_bytes'],
                    'Actual working output exceeded registered estimate; stop for capacity review')
        require(len(accepted) == 20 and sum(x['role']=='dev' for x in accepted)==10
                and sum(x['role']=='confirm' for x in accepted)==10, 'All exact twenty role slots required')
        require(not {x['worker_subject_id'] for x in accepted if x['role']=='dev'} &
                    {x['worker_subject_id'] for x in accepted if x['role']=='confirm'}, 'Effective worker group separation')
        effective_path = ROOT/'effective_source_registry_03.json'
        save(effective_path, dict(status='FROZEN_ALL20_ACTUAL_NATIVE_CPU_SOURCES_BEFORE_ANY_MODEL',
             registration_sha256=reg_sha, source_registry_02_sha256=sha(reg['registry_path']),
             sources=20, dev=10, confirm=10, accepted=accepted, rejected_engineering_or_identity=rejected,
             worker_subject_owners=owners, worker_groups_disjoint=True,
             all_visible_actor_household_scene_or_global_pretraining_overlap='UNKNOWN',
             source_selection_uses_model_or_annotation_quality=False, new_model_calls=0))
        coarse_path = ROOT/'coarse_inputs_01.json'
        coarse_rows = [{**proof, 'source_id':source['source_id'], 'source_role':source['role'],
                        'worker_subject_id':source['worker_subject_id'],
                        'CPU_completion_path':source['CPU_completion_path'],
                        'CPU_completion_sha256':source['CPU_completion_sha256']}
                       for source in accepted for proof in source['preparation']['proofs']]
        require(len({x['case_id'] for x in coarse_rows}) == len(coarse_rows), 'Unique actual new coarse cases')
        save(coarse_path, dict(status='PASS_CHARADES20_ACTUAL_NATIVE64_COARSE_INPUT_MANIFEST_NOT_GPU_ADMISSION',
             effective_source_registry_sha256=sha(effective_path), sources=20,
             windows=len(coarse_rows), rows=coarse_rows, new_model_calls=0,
             new_optimizer_updates=0, GPU_launch_admitted=False,
             encoded_cache_format='TORCH_SAVE_GZIP_LOSSLESS_LEVEL1'))
        save(ROOT/'media_01/completion.json', dict(status='PASS_ALL_NEEDED_PINNED_ORIGINAL_MEMBER_DOWNLOADS',
             registration_sha256=reg_sha, downloaded_members=downloaded,
             successful_downloads=len(downloaded), effective_sources=20,
             compressed_body_bytes=sum(x['compressed_bytes'] for x in downloaded),
             uncompressed_bytes=sum(x['bytes'] for x in downloaded), new_model_calls=0))
        result = dict(status='PASS_CHARADES20_NEW_MEDIA_NATIVE64_CPU_INPUTS_PENDING_MAIN_INDEPENDENT_GPU_ADMISSION',
             utc=utc(), registration_sha256=reg_sha, effective_registry_path=str(effective_path),
             effective_registry_sha256=sha(effective_path), sources=20, dev=10, confirm=10,
             accepted=accepted, rejected_engineering_or_identity=rejected,
             media_completion_sha256=sha(ROOT/'media_01/completion.json'),
             CPU_windows=sum(len(x['preparation']['proofs']) for x in accepted),
             coarse_input_manifest_path=str(coarse_path), coarse_input_manifest_sha256=sha(coarse_path),
             new_model_calls=0, new_optimizer_updates=0, new_GPU_admitted=False,
             complete_resource_snapshot=resource_snapshot(), no_label_semantics_or_endpoints_in_model_input=True,
             old_successful_stage_repeated=False)
        save(chain/'completion.json', result)
        print(__import__('json').dumps(dict(status=result['status'], sources=20,
             CPU_windows=result['CPU_windows'], compressed_bytes=sum(x['compressed_bytes'] for x in downloaded),
             new_model_calls=0)), flush=True)
    except BaseException as err:
        save(chain/'failure.json', dict(status='STOP_KEEP_SUCCESSFUL_MEMBER_CLOCK_RGB_CACHE_CPU_PROOFS',
             utc=utc(), current_source=current, error=repr(err), traceback=traceback.format_exc(),
             accepted=accepted, successful_downloads=downloaded, engineering_rejections=rejected,
             recovery='Explicit separately registered remaining-work recovery only; do not run original chain twice, redownload accepted headers/bodies or reprepare successful clocks/RGB/processor caches.',
             new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['register', 'run'])
    args = parser.parse_args()
    globals()[args.stage]()
