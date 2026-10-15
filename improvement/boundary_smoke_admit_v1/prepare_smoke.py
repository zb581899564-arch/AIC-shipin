"""One fixed exposed-development event: metadata join, registration, pure plan.

No AV, processor, model, label parsing, source-media hashing or GPU invocation.
The archived identity-only catalog and historical receipts are unchanged copies.
"""
import datetime
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path('/home/inspur/aic_video_work')
BASE = ROOT/'twenty_hour_five_20261014_v1/local_boundary_v2'
OWN = ROOT/'twenty_hour_five_20261014_v1/boundary_smoke_admit_v1'
EXTERNAL = ROOT/'videoxum_reference_iteration_20261013_v1'
CASE = 'v_fVg3StD8LL0_W000'
SOURCE = 'v_fVg3StD8LL0'
KNOWN = ROOT/'human_reference_iteration_20261013_v1/known_identity_snapshot_01.json'
OLD_REG = ROOT/'twenty_hour_five_20261014_v1/base_only_pilot/registration_input_01.json'
EXPECTED_RULES_SHA = 'b3dc2b7c080145efa3d72f413f4bb6fa8081f55b00bda97000fe83ed8284945b'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def aliases(value):
    """Compare canonical ID and v_ alias, plus metadata path stems only."""
    value = str(value).strip().replace('\\', '/')
    if not value:
        return set()
    values = {value, value.rsplit('/', 1)[-1], Path(value).stem}
    for text in tuple(values):
        if text.startswith('v_'):
            values.add(text[2:])
        elif len(text) == 11 and '/' not in text:
            values.add('v_'+text)
    # Case folding is conservative: it can only create an additional rejection.
    return {text.casefold() for text in values}


def reference(path, expected=None):
    path = Path(path).resolve()
    digest = sha(path)
    if expected is not None:
        require(digest == expected, 'Frozen metadata changed: '+str(path))
    return dict(path=str(path), sha256=digest)


def main():
    require(sys.platform == 'linux' and socket.gethostname() == 'inspur-NP5570M5',
            'Only the verified Linux compute host is admitted')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'This metadata/plan child is CPU-only')
    protocol_path, rules_path = BASE/'protocol.json', BASE/'official_rule_check.json'
    protocol, protocol_ref = read(protocol_path), reference(protocol_path)
    rules_ref = reference(rules_path, EXPECTED_RULES_SHA)
    require(protocol['status'] == 'APPROVED_NEW_EXPOSED_DEVELOPMENT_INTERFACE_ONLY'
            and protocol['case_id'] == CASE and protocol['events'] == 1
            and protocol['calls'] == 2 and protocol['sides'] == ['start', 'end']
            and protocol['science_quality_claim'] is False
            and protocol['production_admission'] is False, 'Fixed smoke protocol scope changed')
    require(datetime.datetime.now(datetime.timezone.utc) <
            datetime.datetime.fromisoformat(protocol['deadline']), 'Campaign deadline reached')
    claim = OWN/'metadata_registration_claim_01.json'
    save(claim, dict(status='ONE_METADATA_JOIN_REGISTRATION_AND_PURE_PLAN_CLAIM',
         utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), pid=os.getpid(),
         script_sha256=sha(__file__), protocol=protocol_ref, official_rules=rules_ref,
         original_case_id=CASE, model_calls=0, processor_calls=0, source_media_hashes=0))
    try:
        old_registration = read(OLD_REG)
        row = old_registration['rows'][0]
        require(row['case_id'] == CASE and row['source_name'] == SOURCE
                and row['original_group'] == 'screen' and row['already_exposed'] is True,
                'Only first pre-registered exposed original-B screen event is allowed')
        fields = dict(input=('input_path', 'input_sha256'),
            cpu_proof=('CPU_proof_path', 'CPU_proof_sha256'),
            done=('original_done_path', 'original_done_sha256'),
            raw=('old_trained_B_raw_path', 'old_trained_B_raw_sha256'),
            request=('old_trained_B_request_path', 'old_trained_B_request_sha256'),
            independent_replay=('old_independent_replay_path', 'old_independent_replay_sha256'),
            clock=('source_clock_path', 'source_clock_sha256'))
        refs = {key: reference(row[path], row[digest]) for key, (path, digest) in fields.items()}
        meta, done = read(refs['input']['path']), read(refs['done']['path'])
        require(meta['source_name'] == SOURCE and meta['source_sha256'] == row['source_sha256'],
                'Original CPU input source identity changed')
        require(Path(meta['frame_array_path']).is_file(), 'Existing immutable old RGB cache absent')
        require(done['status'] == 'MODEL_OK' and len(done['segments']) == 1,
                'Original accepted B event identity changed')

        slot_path = EXTERNAL/'direct_cohort_06/accepted_slot_01.json'
        slot = read(slot_path)
        media_ref = reference(slot['media_completion_path'], meta['bindings']['media_completion_sha256'])
        media = read(media_ref['path'])
        require(media['status'] == 'PASS_REGISTERED_LOCATED_MEDIA_BATCH_NOT_ALL20_OR_NATIVE_ADMISSION'
                and media['sources'] == 1 and len(media['members']) == 1,
                'Existing successful source-media receipt missing')
        member = media['members'][0]
        require(member['video_id'] == SOURCE and member['group'] == 'screen'
                and member['path'] == meta['source_path'] and member['sha256'] == meta['source_sha256']
                and member['bytes'] == meta['source_bytes']
                and member['known_identity_and_whole_file_byte_separation'] is True,
                'Old source SHA/bytes/provenance receipt differs')

        snapshot = read(KNOWN)
        require(snapshot['status'] == 'COMPLETE_KNOWN_B_TRAINING_AND_FROZEN_426_IDENTITIES_NOT_NEW_MEDIA_SEPARATION',
                'Complete known identity snapshot is required')
        train, test = snapshot['training']['sources'], snapshot['testing']['records']
        require(len(train) == 704 and len({x['youtube_id'] for x in train}) == 602
                and len(test) == 426 and {int(x['video_id']) for x in test} == set(range(426)),
                'Current known training/test identity denominator changed')
        provenance = {}
        for name, digest in snapshot['provenance_bindings'].items():
            parts = name.replace('\\', '/').split('/')
            require(parts[:2] == ['reports', 'round6_score_alignment'], 'Unexpected provenance path')
            path = ROOT.joinpath(*parts[1:])
            provenance[str(path)] = reference(path, digest)
        archive_specs = {
            'frozen_test_identity_catalog.json': 'frozen_test_identity_catalog_sha256',
            'existing_runtime_readonly_01.json': 'current_remote_readonly_receipt_sha256',
            'existing_runtime_dependency_followup_01.json': 'dependency_followup_sha256'}
        for filename, key in archive_specs.items():
            path = OWN/'historical_provenance'/filename
            provenance[str(path)] = reference(path, snapshot[key])
        # Parse only identity metadata from the catalog; never image or GT fields.
        catalog = read(OWN/'historical_provenance/frozen_test_identity_catalog.json')['records']
        keys = ('video_id', 'source_group', 'source_path', 'source_sha256')
        projected = [{key: item[key] for key in keys} for item in catalog]
        require(projected == test, 'Original frozen 426 identity catalog differs from snapshot')
        known_aliases, known_hashes = set(), set()
        for item in train+test:
            digest = item['source_sha256']
            require(len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
                    'Known whole-file SHA metadata is incomplete')
            known_hashes.add(digest)
            for key in ('source_name', 'source_group', 'video_id', 'youtube_id', 'parent_sample_id'):
                known_aliases.update(aliases(item.get(key, '')))
            known_aliases.update(aliases(Path(item['source_path']).stem))
        candidate_aliases = aliases(SOURCE) | aliases(meta['source_group']) | aliases(Path(meta['source_path']).stem)
        id_intersections = sorted(candidate_aliases & known_aliases)
        byte_intersections = sorted({meta['source_sha256']} & known_hashes)
        require(not id_intersections and not byte_intersections, 'Known source identity or byte intersection')
        sep_path = EXTERNAL/'twenty_hour_metadata_separation_01'/f'{CASE}.json'
        separation = dict(status='PASS_EXISTING_SOURCE_METADATA_KNOWN_IDENTITIES_AND_BYTE_JOIN_ONLY',
            scope='KNOWN_CURRENT_B_TRAINING_AND_FROZEN426_IDENTITY_AND_BYTE_EXCLUSION',
            known_current_b_training_and_426_test_identities_complete=True,
            known_identity_complete=True, source_name=SOURCE, source_group=meta['source_group'],
            source_sha256=meta['source_sha256'], source_bytes=meta['source_bytes'],
            candidate_aliases=sorted(candidate_aliases), identity_intersections=id_intersections,
            byte_intersections=byte_intersections, known_training_clips=704, known_training_youtube_groups=602,
            known_test_sources=426, known_distinct_byte_hashes=len(known_hashes),
            known_distinct_canonical_aliases=len(known_aliases), known_snapshot=reference(KNOWN),
            provenance_bindings_verified=provenance, old_successful_media_receipt=media_ref,
            original_registration=reference(OLD_REG), original_accepted_slot=reference(slot_path),
            script_sha256=sha(__file__), new_source_media_hashes=0, media_read=False,
            new_CPU_encode_calls=0, new_model_calls=0, labels_parsed=False,
            hidden_source_or_subclip_semantic_overlap='UNKNOWN', reencoded_source_overlap='UNKNOWN',
            base_model_pretraining_overlap='UNKNOWN', global_source_independence_verified=False,
            new_confirmation=False, scientific_quality_claim=False)
        save(sep_path, separation)
        refs['source_separation'] = reference(sep_path)
        lo = Fraction(str(done['source_start_exact']))
        start, end = [lo+Fraction(str(value)) for value in done['segments'][0]]
        interval = [str(start), str(end)]
        require(interval == ['324/25', '476/25'], 'Frozen original-B segment changed')
        required = {str(path): sha(path) for path in sorted((BASE/'code').glob('*.py'))}
        required.update({ref['path']: ref['sha256'] for ref in (protocol_ref, rules_ref)})
        registration = dict(schema='LOCAL_BOUNDARY_NATIVE64_V2_REVISION03',
            contract_revision='SOURCE_EDGE_INWARD_REVISION_03',
            status='FROZEN_EXTERNAL_NONTEST_LOCAL_BOUNDARY_PILOT_V2_REVISION03',
            source_scope='EXTERNAL_NONTEST_DEVELOPMENT_ONLY', validation_scope='ONE_EVENT_INTERFACE_SMOKE',
            selection_frozen_before_new_model_results=True,
            existing_sources_are_exposed_development_not_new_confirmation=True,
            model_parameters=8782459120, optimizer_updates=0, half_window_exact='3', frames_per_request=64,
            endpoint_sides=['start', 'end'], actual_model_call_budget=2, download_media=False, training=False,
            official_rule_check_path=rules_ref['path'], official_rule_check_sha256=rules_ref['sha256'],
            protocol_path=protocol_ref['path'], protocol_sha256=protocol_ref['sha256'], required_files=required,
            registration_helper_path=str(Path(__file__).resolve()), registration_helper_sha256=sha(__file__),
            source_separation_scope=separation['scope'], scientific_quality_claim=False,
            production_admission=False, new_confirmation=False,
            events=[dict(event_id='SMOKE_ORIGINAL_SCREEN_001', original_case_id=CASE,
                original_segment_index=0, original_interval_exact=interval, clock_object_keys=[],
                reuse_rgb_inputs=[refs['input']], original_evidence=refs)])
        registration_path = BASE/'registration_smoke_input_01.json'
        save(registration_path, registration)
        argv = [sys.executable, '-B', str(BASE/'code/plan_local_inputs.py'),
                '--base', str(BASE), '--registration', str(registration_path)]
        save(OWN/'pure_plan_launch_01.json', dict(argv=argv, calls_allowed=0,
            registration=reference(registration_path), processor_allowed=False, GPU_allowed=False))
        # Exactly one pure plan; no preparation, replay, model or GPU chain follows.
        with (OWN/'pure_plan_01.log').open('xb') as log:
            completed = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       env=os.environ.copy(), check=False)
        require(completed.returncode == 0, 'Pure plan failed; preserve all partials and do not rerun')
        completion_path = BASE/'plan_01/completion.json'
        completion = read(completion_path)
        requests = read(BASE/'plan_01/requests.json')
        require(completion['status'] == 'PASS_FROZEN_LOCAL_BOUNDARY_PLAN_NOT_CPU_ADMISSION'
                and completion['requests'] == 2 and completion['new_model_calls'] == 0,
                'Pure plan completion differs')
        # Small metadata only; no prompts, old/raw answers, pixels or references leave Linux.
        summaries = []
        old_ordinals = set(meta['source_frame_ordinals'])
        for request in requests:
            summaries.append({key: request[key] for key in
                ('side', 'window_start', 'window_end', 'original_endpoint_exact',
                 'same_candidate_inner_anchor_exact')})
            ordinals = request['source_frame_ordinals']
            summaries[-1].update(sampled_frames=len(ordinals),
                new_native_ordinals=len(set(ordinals)-old_ordinals),
                old_native_ordinals_reused=len(set(ordinals)&old_ordinals))
        result = dict(status='PASS_METADATA_JOIN_REGISTRATION_AND_PURE_PLAN_ONLY',
            source_separation=reference(sep_path), registration=reference(registration_path),
            plan_completion=reference(completion_path), known_training_clips=704,
            known_training_groups=602, known_test_sources=426,
            identity_intersections=0, byte_intersections=0, requests=summaries,
            original_case_id=CASE, original_interval_exact=interval,
            global_source_independence_verified=False, new_confirmation=False,
            scientific_quality_claim=False, source_media_read=False, source_media_rehash=False,
            processor_calls=0, GPU_calls=0, new_model_calls=0, actual_future_model_call_budget=2)
        save(OWN/'completion_01.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        save(OWN/'failure_01.json', dict(status='FAILED_PRESERVE_PARTIAL_NO_AUTOMATIC_REPEAT',
            error=repr(error), new_model_calls=0, processor_calls=0))
        raise


if __name__ == '__main__':
    main()
