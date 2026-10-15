"""New CPU-only recovery arm; original dense128 artifacts and failed context stay immutable."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from source_domain import source_domains, window_context

HERE = Path(__file__).resolve().parent
PARENT = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/overnight_risk_20261012_v1/dense128_v2')
sys.path.insert(0, str(PARENT))
import dense_runtime as r


def main():
    recovery_lock = r.read(HERE/'recovery_source_lock.json')
    claim = r.read(HERE/'launch.claim.json')
    r.require(r.sha(HERE/'recovery_source_lock.json') == claim['recovery_source_lock_sha256'],
              'create-once recovery lock differs from actual launch claim')
    for path, expected in recovery_lock['files'].items():
        r.require(r.sha(path) == expected, 'frozen recovery source changed: '+path)
    registration = r.read(HERE/'registration.json')
    for path, expected in registration['new_files'].items():
        r.require(r.sha(path) == expected, 'new context recovery control changed: '+path)
    for path, expected in registration['parent_files'].items():
        r.require(r.sha(path) == expected, 'accepted parent or preserved failure changed: '+path)
    protocol = r.read(HERE/'PROTOCOL.json')
    r.require(protocol['schema'] == 'DENSE128_CONTEXT025_FROZEN_SOURCE_DOMAIN_RECOVERY_V1' and
              protocol['uniform_all_videos'] and protocol['padding_exact'] == '1/4' and
              protocol['new_model_calls'] == protocol['new_optimizer_updates'] == 0,
              'registered context recovery contract differs')
    from dense_production import GPU, prepared, key
    acceptance, extra = prepared()
    lock = r.verify_lock('rematch', extra)
    r.require(lock['sha256'] == registration['parent_source_lock_sha256'], 'parent source lock differs')
    parent_dir = PARENT/'rematch_01/package_01'
    parent = r.read(parent_dir/'completion.json')
    independent = r.read(parent_dir/'independent_validation.json')
    replay_path = PARENT/'rematch_01/replay_01/completion.json'
    replay = r.read(replay_path)
    terminal = r.read(GPU/'completion.json')
    resource = r.read(r.RUN/'controller/dense128_native_rematch521_20261012_v2.resource.json')
    matching = [x for x in r.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
                if x['name'] == 'dense128_native_rematch521_20261012_v2']
    r.require(matching == [resource] and resource['status'] == 'completed' and resource['exit_code'] == 0,
              'unique real parent GPU terminal differs')
    r.require(parent['status'] == 'PASS_COMPLETE_NEW_DENSE128_USER_AUTHORIZED_RISK_ZIP' and
              r.sha(parent['candidate']) == parent['zip_sha256'] and
              r.sha(parent_dir/'independent_validation.json') == parent['independent_validation_sha256'] and
              all(independent['checks'].values()) and len(independent['checks']) == 11,
              'accepted pure parent is missing')
    r.require(replay['status'] == 'PASS_521_DENSE128_INDEPENDENT_CPU_REPLAYS' and
              len(replay['proofs']) == 521 and replay['CPU_only'] and not replay['CUDA_initialized'] and
              replay['source_lock_sha256'] == terminal['source_lock_sha256'] == lock['sha256'] and
              replay['gpu_completion_sha256'] == r.sha(GPU/'completion.json') and
              r.sha(replay_path) == parent['independent_replay_sha256'], 'accepted521 independent parent replay differs')
    common, (_, _, _, _, old, frames, production) = r.original_helpers()
    ref, manifest, clocks = old.inputs('rematch')
    cache = r.RUN/'b_score_aligned_package_v4/rematch_01'
    cache_evidence = production.b2_cache_evidence('rematch', ref)
    frozen = r.read(r.RUN/'teacher_student_autopilot_v14/cache_01/rematch.json')
    r.require({k:v for k,v in frozen.items() if k != 'utc'} == cache_evidence, 'frozen full source field differs')
    field = old.rows(cache/'field_frames.jsonl')
    source_ids = {x['video_id'] for x in manifest['records']}
    r.require(len(source_ids) == 426, 'expected full426 identity differs')
    domains = source_domains(field, source_ids)
    domain_proof = r.read(HERE/'source_domain_preflight.json')
    r.require(domain_proof['status'] == 'PASS_ALL426_CONTIGUOUS_FROZEN_SOURCE_DOMAINS' and
              domain_proof['domain_digest'] == r.digest({k:list(v) for k,v in domains.items()}) and
              domain_proof['field_sha256'] == r.sha(cache/'field_frames.jsonl'),
              'frozen426 source-domain proof differs from actual field')
    field_by_key = {(x['video_id'],x['source_frame']):x for x in field}
    r.require(len(field_by_key) == len(field), 'duplicate source-field frame')
    entries = {e['key']:e for e in terminal['entries']}
    r.require(len(entries) == 521, 'actual parent-call denominator differs')
    baseline, chosen = set(), set()
    for job in acceptance['jobs']:
        for window in job['windows']:
            entry = entries[key(window)]
            done = r.read(entry['done_path'])
            r.require(r.sha(entry['done_path']) == entry['done_sha256'] and done['source_window'] == window and
                      done['output_valid'] and not done['parse_errors'], 'untouched parent answer differs')
            core, context = window_context(window, done['parsed_segments'], domains[window['source_id']])
            baseline.update((window['source_id'],i) for i in core)
            chosen.update((window['source_id'],i) for i in context)
    from package_contract import keyset, package, validate_predictions
    from field_contract import compose_from_field
    r.require(baseline == keyset(old.rows(parent_dir/'selected.jsonl')) and baseline <= chosen and chosen and
              chosen <= set(field_by_key), 'uniform recovered membership differs from accepted parent or field')
    selected = [field_by_key[k] for k in sorted(chosen)]
    projected = frames.legacy_manifest(manifest)
    predictions, provenance = compose_from_field(projected, selected, old.rows(cache/'field_shots.jsonl'),
        old.rows(cache/'anchor_requests.jsonl'), old.rows(cache/'anchor_output.jsonl'))
    out = HERE/'context025_package_01'
    out.mkdir(exist_ok=False)
    try:
        report = validate_predictions(projected, predictions, chosen, provenance)
        for name, rows in [('selected',selected),('predictions',predictions),('provenance',provenance)]:
            old.write_rows(out/(name+'.jsonl'),rows)
        r.save(out/'metadata.json',dict(records=manifest['records'],errors=[]))
        r.save(out/'source_domain_acceptance.json',dict(status='PASS_ALL426_CONTIGUOUS_FROZEN_SOURCE_DOMAINS',
            domains={k:list(v) for k,v in domains.items()},sources=426,field_frames=len(field),
            chosen_frames=len(chosen),parent_frames=len(baseline),core_removed=0,
            predicate='lo <= native_ordinal < hi AND clipped_window_lower <= exact_native_pts < clipped_window_upper',
            new_model_calls=0,new_native_decodes=0,new_processor_encodes=0))
        pending = out/'candidate_DENSE128_CONTEXT025_SOURCE_DOMAIN.PENDING.zip'
        report.update(package(out/'predictions.jsonl',pending))
        subprocess.run([sys.executable,'-B',str(r.RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
            '--strict-loader-root',str(r.RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
            '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
            '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
            '--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
        independent = r.read(out/'independent_validation.json')
        production.check_independent(independent,'rematch',len(selected))
        r.require(independent['zip_sha256'] == r.sha(pending) and
                  independent['predictions_sha256'] == r.sha(out/'predictions.jsonl') and
                  independent['provenance_sha256'] == r.sha(out/'provenance.jsonl'), 'new independent artifact SHA differs')
        with zipfile.ZipFile(pending) as archive:
            r.require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None and
                      archive.read('predictions.jsonl') == (out/'predictions.jsonl').read_bytes(), 'new ZIP CRC or roundtrip differs')
        old_boxes = {(x['video_id'],p['frame']):p['bboxes'] for x in old.rows(parent_dir/'predictions.jsonl') for p in x['predictions']}
        new_boxes = {(x['video_id'],p['frame']):p['bboxes'] for x in predictions for p in x['predictions']}
        r.require(all(new_boxes[k] == v for k,v in old_boxes.items()), 'accepted core boxes changed')
        import torch
        r.require(not torch.cuda.is_initialized(), 'CPU-only recovery initialized CUDA')
        final = out/'candidate_DENSE128_CONTEXT025_SOURCE_DOMAIN.zip'
        pending.rename(final)
        report.update(status='PASS_COMPLETE_DENSE128_CONTEXT025_SOURCE_DOMAIN_RISK_ZIP',utc=r.utc(),
            candidate=str(final),zip_bytes=final.stat().st_size,zip_sha256=r.sha(final),video_records=426,
            prediction_frames=len(selected),parent_frames=len(baseline),added_frames=len(chosen-baseline),
            removed_frames=0,original_boxes_unchanged=True,padding_exact='1/4',source_domain_uniform_all426=True,
            parent_completion_sha256=r.sha(parent_dir/'completion.json'),independent_replay_sha256=r.sha(replay_path),
            independent_validation_sha256=r.sha(out/'independent_validation.json'),
            source_domain_acceptance_sha256=r.sha(out/'source_domain_acceptance.json'),
            protocol_sha256=r.sha(HERE/'PROTOCOL.json'),registration_sha256=r.sha(HERE/'registration.json'),
            parent_source_lock_sha256=lock['sha256'],parent_actual_model_calls=521,new_model_calls_this_arm=0,
            new_native_decodes=0,new_processor_encodes=0,new_optimizer_updates=0,CUDA_initialized=False,
            complete_pipeline_parameters=8782459120,scientific_quality_pass=False,official_score=None,
            website_submitted=False,original_context_failure_preserved=True)
        r.save(out/'completion.json',report)
        print(json.dumps(report),flush=True)
    except BaseException as exc:
        r.failure(out,exc)
        raise


if __name__ == '__main__':
    main()
