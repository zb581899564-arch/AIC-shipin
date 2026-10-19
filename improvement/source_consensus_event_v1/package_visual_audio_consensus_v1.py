"""Conditional CPU whole-event visual/audio consensus; no new model or fit.

Requires an independently accepted first visual package and an explicit second
registration with accurate total parameters and the previously frozen policy.
Importing the sibling producer uses pure helpers only; its main is never called.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import traceback
import uuid
import zipfile

_path = Path(__file__).with_name('package_visual_pair_formal_v1.py')
_spec = importlib.util.spec_from_file_location('_visual_audio_adopted_package_helpers', _path)
helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helper)
ROOT, W, EVENT, RELATIVE, OLD = helper.ROOT, helper.W, helper.EVENT, helper.RELATIVE, helper.OLD
RUN, PY, SOURCE_CLEAR = helper.RUN, helper.PY, helper.SOURCE_CLEAR
read, save, ref, bound, require = helper.read, helper.save, helper.ref, helper.bound, helper.require
POLICY_SCHEMA = 'VISUAL_AUDIO_WHOLE_EVENT_CONSENSUS_POLICY_V1'
POLICY_RULE = 'KEEP_WHOLE_EVENT_IFF_ALL_ADDED_NATIVE_FRAMES_IN_OLD_AUDIO_VISUAL'
POLICY_SHA = 'c2a41a8f1c62d556090eaf4742876e0db42ef1424e13dbcff5266a8a31e1aea9'


def select_whole_events(kept_sids, decisions, baseline_keys, first_keys, audio_keys):
    """Membership-only, whole original half-open ranges; no scores or clipping."""
    selected = set(baseline_keys)
    retained, rejected = [], []
    require(len(kept_sids) == len(set(kept_sids)), 'Unique first-package event IDs')
    for sid in sorted(kept_sids, key=int):
        require(sid in decisions and decisions[sid]['chosen'] is not None, 'Only original relative chosen events')
        choice = decisions[sid]['chosen']
        left, right = choice['left'], choice['right']
        require(type(left) is int and type(right) is int and 0 <= left < right, 'Original exact native event range')
        event = {(sid, index) for index in range(left, right)}
        added = event-set(baseline_keys)
        first_added = {key for key in first_keys if key[0] == sid}-set(baseline_keys)
        require(added and added == first_added and len(added) == choice['added_frames'],
                'First ZIP must contain exactly the entire original event addition')
        if added <= audio_keys:
            selected.update(event)
            retained.append(sid)
        else:
            rejected.append(sid)
    require({sid for sid, index in first_keys-set(baseline_keys)} == set(kept_sids),
            'Every first-package addition belongs to one bound original event')
    return selected, retained, rejected


def main():
    require(os.name == 'posix' and socket.gethostname() == 'inspur-NP5570M5', 'Registered Linux CPU host only')
    require(os.environ['CUDA_VISIBLE_DEVICES'] == '', 'CPU-only consensus package')
    registration_path = ROOT/'second_candidate_registration_01.json'
    registration = read(registration_path)
    require(registration['schema'] == 'VISUAL_AUDIO_WHOLE_EVENT_CONSENSUS_V1', 'Explicit second candidate schema')
    helper.deadline(registration)
    actual = registration['actual_pipeline_parameters']
    require(type(actual) is int and 0 < actual <= 9_000_000_000, 'Accurately registered unique resident parameter total<=9B')
    policy_path = bound(registration['policy_ref'])
    require(policy_path.resolve() == (ROOT/'second_policy_before_formal_outputs_01.json').resolve(),
            'Use the policy frozen before formal outputs')
    require(registration['policy_ref']['sha256'] == POLICY_SHA, 'Exact before-formal-output policy identity')
    policy = read(policy_path)
    require(policy['schema'] == POLICY_SCHEMA and policy['rule'] == POLICY_RULE
            and policy['coverage_fraction'] == '1/1' and policy['clip_intervals'] is False
            and policy['rerank'] is False and policy['new_model_calls'] == 0,
            'Exact frozen whole-event100% native-addition coverage policy')
    first_path = bound(registration['first_package_completion_ref'])
    audio_path = bound(registration['audio_package_completion_ref'])
    require(first_path.resolve() == (ROOT/'package_01/completion.json').resolve()
            and audio_path.resolve() == (EVENT/'packages/EVENT_AUDIO_VISUAL/completion.json').resolve(),
            'Only the accepted first package and unchanged original audio/visual package')
    first, audio = read(first_path), read(audio_path)
    require(first['status'] == 'NEW_ENGINEERING_ACCEPTED_PAIRWISE_VISUAL_GATED_EVENT_OFFICIAL_EFFECT_UNKNOWN'
            and first['independent11strict'] is True and first['all_baseline_boxes_preserved'] is True
            and first['added_boxes_equal_original_relative'] is True,
            'First package must already be genuinely accepted; never rerun its producer or QA')
    require(audio['mechanism'] == 'EVENT_AUDIO_VISUAL' and audio['independent11strict'] is True
            and audio['all_baseline_boxes_preserved'] is True, 'Original audio/visual package acceptance')
    first_zip, audio_zip = bound(first['zip']), bound(audio['zip'])
    first_rows, audio_rows = helper.archive_rows(first_zip), helper.archive_rows(audio_zip)
    require(helper.canonical(first_rows) == first['canonical_sha256']
            and helper.canonical(audio_rows) == audio['canonical_sha256'], 'Both accepted ZIP prediction identities')
    first_boxes, audio_boxes = helper.frame_boxes(first_rows), helper.frame_boxes(audio_rows)
    formal = read(ROOT/'registration_01.json')
    admission = read(bound(formal['admission_ref']))
    base_ref = admission['original_baseline_ref']
    require(base_ref['sha256'] == helper.BASE_SHA, 'Protect unchanged40.47 baseline')
    base = helper.archive_rows(bound(base_ref)); baseline = helper.frame_boxes(base)
    require(len(baseline) == 123506 and set(baseline) <= set(first_boxes) and set(baseline) <= set(audio_boxes)
            and all(first_boxes[key] == box and audio_boxes[key] == box for key, box in baseline.items()),
            'Both adopted packages retain all123506 original frames and boxes')
    original_path = bound(admission['original_proposals_ref'])
    require(original_path.resolve() == (RELATIVE/'production_01/completion.json').resolve(), 'Unchanged original event ranges')
    original = read(original_path)
    decisions = {row['sid']: row for row in original['decisions']}
    require(len(decisions) == 426, 'Original complete426 event decision metadata')
    selected, kept, rejected = select_whole_events(first['kept_sids'], decisions, set(baseline),
                                                  set(first_boxes), set(audio_boxes))
    additions = selected-set(baseline)
    require(0 < len(additions) <= 12350 and selected < set(first_boxes),
            'Require real additions and a strict change from first package; never manufacture a second ZIP')
    require(additions <= set(audio_boxes), 'Every retained event addition is100% covered by original audio/visual selection')
    out = ROOT/'package_audio_consensus_01'
    out.mkdir(exist_ok=False)
    save(out/'start.json', dict(registration_ref=ref(registration_path), policy_ref=registration['policy_ref'],
         first_package_completion_ref=registration['first_package_completion_ref'],
         audio_package_completion_ref=registration['audio_package_completion_ref'], original_proposals_ref=ref(original_path),
         producer_code_ref=ref(__file__), helper_code_ref=ref(_path),
         actual_resident_parameters=actual, no_first_package_QA_or_production_repeated=True, utc=helper.utc()))
    sys.path[:0] = [str(SOURCE_CLEAR/'code')]
    spec = importlib.util.spec_from_file_location('_audio_consensus_original_renderer', SOURCE_CLEAR/'code/render.py')
    renderer = importlib.util.module_from_spec(spec); spec.loader.exec_module(renderer)
    rows, provenance, chosen, inputs = renderer.render(selected)
    current = helper.frame_boxes(rows)
    require(set(current) == selected and all(current[key] == box for key, box in baseline.items()),
            'All original40.47 frames and boxes remain exact')
    require(all(current[key] == first_boxes[key] for key in additions),
            'Every new frame box equals the accepted first visual package')
    ratios = {row['video_id']: row['targetRatioWH'] for row in base}
    require(all(row['targetRatioWH'] == ratios[row['video_id']] for row in rows), 'Original source aspect-ratio contract')
    inventory_path = OLD/'feature_completion.json'
    inventory = {row['id']: row for row in read(inventory_path)['sources']}
    require(set(inventory) == set(map(str, range(426))), 'Complete426 original native-clock bindings')
    selected_by_sid = {sid: [] for sid in inventory}
    for sid, ordinal in selected:
        selected_by_sid[sid].append(ordinal)
    for sid, feature in inventory.items():
        helper.deadline(registration)
        clock = read(bound(dict(path=str(OLD/'inputs'/sid/'clock.json'), sha256=feature['clock_sha256'])))
        points = list(map(helper.Fraction, clock['normalized_exact_pts']))
        require(points and all(a < b for a, b in zip(points, points[1:]))
                and points[-1] < helper.Fraction(clock['physical_end_exact'])
                and all(0 <= index < len(points) for index in selected_by_sid[sid]), 'Every selected frame belongs to exact original native PTS')
    for row in rows:
        row['model_params_b'] = actual/1e9
    digest = helper.canonical(rows)
    old_admission = read(RELATIVE/'production_admission_02.json')
    history_ref = old_admission['current_delivered_history_ref']
    history = set(helper.histories(read(bound(history_ref))))
    history.update(helper.histories(read(bound(inputs['history']))))
    history.update(read(OLD/'production_registration.json')['historical_prediction_sha256'])
    history.update((helper.canonical(base), first['canonical_sha256'], audio['canonical_sha256'],
                    original['canonical_sha256'], read(SOURCE_CLEAR/'completion.json')['canonical_sha256']))
    protected = old_admission['protected_risk_completion_refs']
    require(len(protected) == 3 and len({value['path'] for value in protected}) == 3, 'Protect all original three risk packages')
    for value in protected:
        previous = read(bound(value)); bound(previous['zip']); history.add(previous['canonical_sha256'])
    for path in (EVENT/'packages').glob('*/completion.json'):
        history.add(read(path)['canonical_sha256'])
    require(digest not in history, 'Second candidate must differ from first, original and every historical prediction')
    save(out/'prediction_acceptance.json', dict(status='PASS_FIRST_WHOLE_EVENT_VISUAL_AUDIO_CONSENSUS_NATIVE_FRAME_BOX_QA',
         kept_sids=kept, rejected_sids=rejected, kept_events=len(kept), rejected_events=len(rejected),
         added_frames=len(additions), removed_frames=0, whole_events_only=True, clipped_intervals=0,
         newly_ranked_events=0, all_baseline_frames_and_boxes_exact=True, added_boxes_equal_first_package=True,
         native_clock_inventory_ref=ref(inventory_path), canonical_sha256=digest,
         historical_canonical_count=len(history), actual_resident_parameters=actual, utc=helper.utc()))
    helper.dump(out/'predictions.jsonl', rows); helper.dump(out/'selected.jsonl', chosen)
    helper.dump(out/'provenance.jsonl', provenance); save(out/'metadata.json', read(bound(inputs['metadata'])))
    helper.deadline(registration)
    pending = out/'candidate_VISUAL_AUDIO_CONSENSUS_EVENT.PENDING.zip'
    with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(out/'predictions.jsonl', 'predictions.jsonl')
    subprocess.run([str(PY), '-B', str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
        '--strict-loader-root', str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
        '--metadata', str(out/'metadata.json'), '--selected', str(out/'selected.jsonl'),
        '--predictions', str(out/'predictions.jsonl'), '--provenance', str(out/'provenance.jsonl'),
        '--zip', str(pending), '--report', str(out/'independent_validation.json')], check=True)
    checks = read(out/'independent_validation.json')['checks']
    require(len(checks) == 11 and all(value is True for value in checks.values()), 'Independent second-package11strict')
    member_sha = ref(out/'predictions.jsonl')['sha256']
    with zipfile.ZipFile(pending) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
                and helper.hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == member_sha,
                'Single JSONL member, CRC and member SHA')
    bound(base_ref); bound(first['zip']); bound(audio['zip'])
    bound(registration['first_package_completion_ref']); bound(registration['audio_package_completion_ref'])
    bound(registration['policy_ref'])
    for value in protected:
        bound(value); bound(read(bound(value))['zip'])
    helper.deadline(registration)
    final = out/'candidate_VISUAL_AUDIO_CONSENSUS_EVENT.zip'
    require(not final.exists(), 'Never overwrite any accepted ZIP')
    pending.rename(final)
    result = dict(status='NEW_ENGINEERING_ACCEPTED_VISUAL_AUDIO_CONSENSUS_EVENT_OFFICIAL_EFFECT_UNKNOWN',
         mechanism='VISUAL_AUDIO_WHOLE_EVENT_CONSENSUS', zip=ref(final), member_sha256=member_sha,
         canonical_sha256=digest, records=426, frames=len(current), added_frames=len(additions), removed_frames=0,
         changed_sources=len(kept), kept_sids=kept, rejected_sids=rejected,
         actual_added_seconds=sum(float(helper.Fraction(decisions[sid]['chosen']['added_duration_exact'])) for sid in kept),
         actual_resident_parameters=actual, all_baseline_boxes_preserved=True, added_boxes_equal_first_package=True,
         original_three_risk_packages_preserved=True, independent11strict=True, policy_ref=registration['policy_ref'],
         registration_ref=ref(registration_path), first_package_completion_ref=registration['first_package_completion_ref'],
         audio_package_completion_ref=registration['audio_package_completion_ref'], whole_events_only=True,
         clipped_intervals=0, reranking=False, new_8B_calls=0, new_fit=0, media_decode=0, processor_calls=0,
         first_package_QA_or_production_repeated=False, official_labels_read=False, website_submitted=False,
         official_score='UNKNOWN', utc=helper.utc())
    save(out/'completion.json', result)
    save(out/'delivery_receipt.json', {key: result[key] for key in (
        'status', 'zip', 'member_sha256', 'canonical_sha256', 'records', 'frames', 'added_frames', 'removed_frames',
        'changed_sources', 'actual_resident_parameters', 'independent11strict', 'all_baseline_boxes_preserved',
        'added_boxes_equal_first_package', 'official_score', 'utc')})


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if ROOT.is_dir():
            save(ROOT/('audio_consensus_package_failure_'+uuid.uuid4().hex+'.json'), dict(error=repr(error),
                 traceback=traceback.format_exc(), successes_preserved=True, no_automatic_retry=True, utc=helper.utc()))
        raise
