"""Four explicit online-only temporal probes; no model or accuracy evaluation."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import traceback
import zipfile

W = Path('/home/inspur/aic_video_work')
P = W / 'content_choice_20261019_v1'
R = W / 'online_temporal_probe4_20261020_v1'
sys.path[:0] = [str(R / 'code'), str(P / 'code')]
from improvement.native_preference_v1.assets import (
    check_ref, read_json, path_ref, write_new, _clock, PROTECTED_SHA256, PROTECTED_BYTES)
from improvement.native_preference_v1.render import (
    bound_renderer, lines, keymap, canonical, dump_lines, validate_selections)
from improvement.content_choice_v1.contracts import code_identity
from improvement.content_choice_v1.selection import choose, validate_source_candidates
from improvement.content_choice_v1.critic import score_source
from clock_bridge19 import compare_clock_frames


def current_time():
    return datetime.now(timezone.utc).isoformat()


def main():
    phase = 'CLAIM'
    try:
        def deadline(signum, frame):
            raise TimeoutError('Frozen CPU-only risk package budget1800s exceeded')
        signal.signal(signal.SIGALRM, deadline)
        signal.alarm(1800)
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        protocol = read_json(R / 'protocol21.json')
        registration = read_json(R / 'registration21.json')
        assert protocol['approved'] is True and protocol['local_proxy_score_runs'] == 0
        assert registration['new_model_calls'] == 0
        for ref in registration['code_refs'].values():
            check_ref(ref, W)
        write_new(R / 'started21.json', dict(utc=current_time(), pid=os.getpid(), argv=sys.argv,
            start_ticks=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]))
        comp_path = check_ref(registration['production_ref'], W)
        comp = read_json(comp_path)
        assert comp['status'] == 'COMPLETE_PRODUCTION_NOT_PACKAGED'
        assert comp['source_count'] == 426 and comp['window_count'] == 522
        assert comp['code_identity'] == code_identity() and comp['labels_read'] is False
        qa = read_json(check_ref(registration['first_output_QA_ref'], W))
        assert qa['status'] == 'PASS_REREAD_ALL522_OUTPUTS_AND426_SOURCE_DECISIONS'
        assert qa['production_completion_ref'] == path_ref(comp_path)
        # Reuse all successful input/token/native QA.  Only immutable output bytes
        # are read to execute the newly frozen decisions; no tensor/model replay.
        write_new(R / 'adopted_first_output_QA21.json', dict(
            status='ADOPT_ALL522_FIRST_INDEPENDENT_QA_NO_REPLAY', original_ref=registration['first_output_QA_ref'],
            source_count=426, window_count=522, new_model_calls=0, replay_calls=0))
        baseline = check_ref(registration['baseline_ref'], W)
        assert baseline.stat().st_size == PROTECTED_BYTES and path_ref(baseline)['sha256'] == PROTECTED_SHA256
        with zipfile.ZipFile(baseline) as z:
            assert z.namelist() == ['predictions.jsonl'] and z.testzip() is None
            base_rows = lines(z.read('predictions.jsonl'))
        base = {v['video_id']: {p['frame'] for p in v['predictions']} for v in base_rows}
        old_map = keymap(base_rows)
        expected = {str(i) for i in range(426)}
        assert set(base) == set(comp['sources']) == expected
        phase = 'FIXED_RISK_DECISIONS_NO_LABELS'
        selections = {m['key']: {} for m in protocol['methods']}
        selections.update({key: {} for key in protocol['exact_duplicate_or_zero_effect_fallback_order']})
        head = read_json(check_ref(registration['critic_weights_ref'], W))
        assert head['parameters'] == 131 and head['feature_kind'] == 'content'
        for sid, source in comp['sources'].items():
            validate_source_candidates(source)
            groups = [set(c['selected_ordinals']) for c in source['candidates'][:3]]
            union = set.union(*groups)
            intersection = set.intersection(*groups)
            vote = Counter(i for group in groups for i in group)
            selections['BASELINE_PLUS_TRIPLE'][sid] = base[sid] | intersection
            selections['BASELINE_UNANIMOUS_REJECT'][sid] = base[sid] & union
            selections['CONTENT_CRITIC_RISK'][sid] = set(choose(source, score_source(head, source))['selected_ordinals'])
            selections['FRAME_MAJORITY_2_OF_3'][sid] = {i for i, count in vote.items() if count >= 2}
            selections['DIVERSE_NATURAL_UNION'][sid] = union
            scores = [c['mean_logprob'] for c in source['candidates']]
            selections['SOURCE_REAL_PROBABILITY'][sid] = set(choose(source, scores)['selected_ordinals'])
            selections['WINDOW_CONDITIONAL_CHOICE'][sid] = set()
        window_decisions = []
        for uid, ref in comp['window_refs'].items():
            row = read_json(check_ref(ref, W))
            assert row['status'] == 'ACCEPTED' and row['uid'] == uid and row['labels_read'] is False
            sid = row['source_id']
            assert row['source_sha256'] == comp['sources'][sid]['source_sha256']
            scores = []
            for c in row['slots']:
                assert c['status'] == 'ACCEPTED'
                a, b = c['real'], c['permuted']
                n = a['suffix_tokens']
                assert n == b['suffix_tokens'] == len(c['ids']) and n > 0
                value = (a['logprob'] - b['logprob']) / n
                assert math.isfinite(value)
                scores.append(value)
            index = max(range(4), key=lambda i: (scores[i], -i))
            selections['WINDOW_CONDITIONAL_CHOICE'][sid].update(row['slots'][index]['selected_ordinals'])
            window_decisions.append(dict(uid=uid, sid=sid, slot=index, scores=scores, output_ref=ref))
        assert len(window_decisions) == 522
        dump_lines(R / 'window_choice_decisions21.jsonl', window_decisions)
        phase = 'FROZEN_SPATIAL_IDENTITY_AND_CLOCKS'
        manifest = read_json(check_ref(registration['production_assets_ref'], W))
        renderer = manifest['renderer']
        source_manifest = read_json(check_ref(renderer['source_manifest_ref'], W))
        sources = {s['id']: s for s in manifest['scopes']['production']['sources']}
        records = {r['video_id']: r for r in source_manifest['records']}
        assert set(sources) == set(records) == expected
        clocks, counts = {}, {}
        for sid, source in sources.items():
            clocks[sid] = read_json(check_ref(source['clock_ref'], W))
            points, end = _clock(clocks[sid])
            counts[sid] = len(points)
            assert clocks[sid]['source_sha256'] == source['source_sha256'] == records[sid]['source_sha256']
            assert source['source_sha256'] == comp['sources'][sid]['source_sha256']
            assert len(points) == records[sid]['n_frames'] == comp['sources'][sid]['native_count']
        fields = {name: check_ref(ref, W) for name, ref in renderer['field_files'].items()}
        field_rows = lines(fields['field_frames.jsonl'])
        field_map = {(r['video_id'], r['source_frame']): r for r in field_rows}
        assert len(field_map) == len(field_rows)
        domain = set(field_map)
        assert set(old_map) <= domain
        history = read_json(R / 'history_fingerprints21.json')
        used = {r['canonical_sha256'] for r in history['packages']}
        candidate_order = [m['key'] for m in protocol['methods']]
        candidate_order.extend(protocol['exact_duplicate_or_zero_effect_fallback_order'])
        accepted, skipped = [], []
        final = R / 'final'; final.mkdir(exist_ok=False)
        with bound_renderer(renderer, W) as (field, pts):
            original_clocks = pts.load_clocks(source_manifest,
                check_ref(renderer['clock_registry_ref'], W), renderer['clock_registry_ref']['sha256'])
            shot_rows, anchor_requests, anchor_outputs = (lines(fields[name]) for name in
                ['field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl'])
            for key in candidate_order:
                if len(accepted) == 4:
                    break
                phase = 'RENDER_AND_FORMAT_' + key
                raw_document = {sid: dict(status='ACCEPTED', selected_ordinals=sorted(values))
                                for sid, values in selections[key].items()}
                raw = validate_selections(raw_document, counts)
                # This is one global prior availability rule, not per-test editing.
                available = raw & domain
                if not available:
                    skipped.append(dict(method=key, reason='TOTAL_ZERO_FRAMES_NO_MEANINGFUL_OUTPUT'))
                    continue
                index = str(len(accepted) + 1).zfill(2)
                stage = R / ('candidate_' + index + '_' + key); stage.mkdir(exist_ok=False)
                clock_checks = {}
                by_source = {sid: [] for sid in expected}
                for sid, ordinal in available:
                    by_source[sid].append(ordinal)
                for sid in expected:
                    clock_checks[sid] = compare_clock_frames(*_clock(clocks[sid]),
                        original_clocks[sid]['pts'], original_clocks[sid]['duration'], by_source[sid])
                chosen = [field_map[k] for k in sorted(available)]
                rows, provenance = field.compose_from_field(pts.legacy_manifest(source_manifest), chosen,
                    shot_rows, anchor_requests, anchor_outputs)
                params = protocol['parameter_counts']['critic' if key == 'CONTENT_CRITIC_RISK' else 'default']
                assert params <= 9_000_000_000
                for row in rows:
                    row['model_params_b'] = params / 1e9
                current = keymap(rows)
                assert len(rows) == 426 and {r['video_id'] for r in rows} == expected
                assert set(current) == available and all(current[k] == old_map[k] for k in available & set(old_map))
                ratios = {r['video_id']: r['targetRatioWH'] for r in base_rows}
                assert all(r['targetRatioWH'] == ratios[r['video_id']] for r in rows)
                checksum = canonical(rows)
                if checksum in used:
                    skipped.append(dict(method=key, reason='EXACT_HISTORICAL_OR_NEW_PREDICTION_DUPLICATE', canonical_sha256=checksum))
                    write_new(stage / 'duplicate_skipped21.json', skipped[-1])
                    continue
                write_new(stage / 'selection_decisions21.json', dict(method=key, sources=raw_document,
                    raw_frames=len(raw), submitted_frames=len(available), unavailable_exclusions=len(raw - domain),
                    excluded=[dict(sid=sid, ordinal=i) for sid, i in sorted(raw - domain)],
                    clock_checks=clock_checks, no_labels_or_metrics=True, official_score='UNKNOWN'))
                dump_lines(stage / 'predictions.jsonl', rows)
                dump_lines(stage / 'selected.jsonl', chosen)
                dump_lines(stage / 'provenance.jsonl', provenance)
                write_new(stage / 'metadata.json', read_json(check_ref(renderer['metadata_ref'], W)))
                pending = final / ('candidate_' + index + '_' + key + '.PENDING.zip')
                with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as z:
                    z.write(stage / 'predictions.jsonl', 'predictions.jsonl')
                subprocess.run([manifest['runtime_python'], '-B', str(check_ref(renderer['independent_validator_ref'], W)),
                    '--strict-loader-root', renderer['strict_loader_root'], '--metadata', str(stage / 'metadata.json'),
                    '--selected', str(stage / 'selected.jsonl'), '--predictions', str(stage / 'predictions.jsonl'),
                    '--provenance', str(stage / 'provenance.jsonl'), '--zip', str(pending),
                    '--report', str(stage / 'independent_validation.json')], check=True, timeout=600,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                validation = read_json(stage / 'independent_validation.json')
                assert len(validation['checks']) == 11 and all(validation['checks'].values()) and not validation['strict_loader_issues']
                with zipfile.ZipFile(pending) as z:
                    assert z.namelist() == ['predictions.jsonl'] and z.testzip() is None
                    payload = z.read('predictions.jsonl')
                    assert hashlib.sha256(payload).hexdigest() == path_ref(stage / 'predictions.jsonl')['sha256']
                dest = final / pending.name.replace('.PENDING.zip', '.zip'); pending.rename(dest)
                receipt = dict(index=index, method=key, status='RISK_FORMAT_ACCEPTED_NO_OFFLINE_QUALITY_CLAIM',
                    zip_ref=path_ref(dest), member_sha256=hashlib.sha256(payload).hexdigest(),
                    member_bytes=len(payload), canonical_sha256=checksum, records=426, frames=len(available),
                    added_frames=len(available - set(old_map)), removed_frames=len(set(old_map) - available),
                    empty_sources=sum(not by_source[sid] for sid in expected), actual_pipeline_parameters=params,
                    field_domain_exclusions=len(raw - domain), independent_validation_ref=path_ref(stage / 'independent_validation.json'),
                    selection_ref=path_ref(stage / 'selection_decisions21.json'), local_proxy_score_runs=0,
                    new_model_calls=0, new_training_updates=0, official_score='UNKNOWN', automatic_submission=False,
                    prior_critic_scientific_stop_preserved=(key == 'CONTENT_CRITIC_RISK'))
                write_new(stage / 'receipt21.json', receipt)
                accepted.append(receipt); used.add(checksum)
                write_new(R / ('accepted_' + index + '.json'), receipt)
        phase = 'FINAL_BUNDLE'
        assert len(accepted) == 4, 'Cannot produce four distinct nonzero candidates from the frozen list'
        check_ref(registration['baseline_ref'], W)
        assert comp['code_identity'] == code_identity()
        for ref in registration['code_refs'].values():
            check_ref(ref, W)
        result = dict(status='FOUR_DISTINCT_RISK_ZIPS_LINUX_ACCEPTED_PENDING_WINDOWS', utc=current_time(),
            candidates=accepted, skipped=skipped, protocol_ref=path_ref(R / 'protocol21.json'),
            registration_ref=path_ref(R / 'registration21.json'), baseline_unchanged=True,
            accuracy_metric_runs=0, model_calls=0, successful_replays_repeated=0, website_submitted=False)
        write_new(final / 'delivery_manifest21.json', result)
        bundle = R / 'final_four_probe21.zip'
        with zipfile.ZipFile(bundle, 'x', zipfile.ZIP_STORED) as z:
            z.write(final / 'delivery_manifest21.json', 'delivery_manifest21.json')
            for item in accepted:
                z.write(item['zip_ref']['path'], Path(item['zip_ref']['path']).name)
        result['bundle_ref'] = path_ref(bundle)
        write_new(R / 'completion21.json', result)
        signal.alarm(0)
    except BaseException as error:
        write_new(R / 'failure21.json', dict(utc=current_time(), phase=phase, error=str(error),
            traceback=traceback.format_exc(), automatic_retry=False))
        raise


if __name__ == '__main__':
    main()
