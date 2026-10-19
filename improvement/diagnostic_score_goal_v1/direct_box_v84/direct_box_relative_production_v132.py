"""Unexecuted V132 conditional contract and owner checks only.

The actual V128 experiment STOPped. This module therefore contains no worker,
CLI, artifact reader/writer, model loader, processor, registrar or launcher.
Passing a synthetic contract test is not production admission. In particular,
neither the old105/106 qualification nor a positive combined39 mean can replace
the explicit posthoc V129 control promotion and separately completed V134
fresh8 gate. V129 does not retroactively qualify the failed V128 primary.

A future, separately authorized implementation would need explicit CPU32,
GPU32, independent raw QA/cost evidence, remaining-owner admission and a final
whole426 package check. The old estimate6563 owners/303 videos is not a bound.
All functions below consume already supplied metadata and perform no I/O.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
from pathlib import PurePosixPath

SCHEMA = 'CONDITIONAL_PROMOTED_GEOM129_PRODUCTION_V132'
PROMOTION_PASS = 'QUALIFIED_GEOM129_FOR_SEPARATE_FROZEN_FRESH8_TRIAL_NOT_PRODUCTION'
FRESH8_PASS = 'PASS_FRESH8_FIXED_GEOM129_FILE_CONFIRMATION_V134'
BASELINE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
SELECTION = 'OBS_INDEX_EVEN'
HIDDEN_TRANSFORM = 'F32_L2_UNIT_VECTOR_NO_EPS'
ADDITIONAL_PARAMETERS = 135393
PIPELINE_PARAMETERS = 8790372845
PHYSICAL_GPU_PARAMETERS = 8774803699
PILOT_OWNERS = 32
MODEL_REFS = ('training_completion', 'adapter_weights', 'head_weights')
REQUIRED_REFS = MODEL_REFS + ('development_result', 'promotion', 'fresh8_result', 'critic_state',
    'protected_baseline', 'accepted_observations', 'formal_metadata', 'source_clocks', 'domain', 'source_catalog')


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    """Stable metadata digest; never a replacement for artifact byte SHA."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode('utf-8')).hexdigest()


def _integer(value, *, positive=False):
    return type(value) is int and (value > 0 if positive else value >= 0)


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _ref(value):
    """Validate an explicit remote artifact identity without opening its path."""
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'Explicit path/SHA artifact reference required')
    path = value['path']
    require(isinstance(path, str) and PurePosixPath(path).is_absolute()
        and '..' not in PurePosixPath(path).parts and _sha(value['sha256']), 'Absolute non-traversing artifact path and SHA256')


def validate_schema(registration):
    """Validate a conditional plan. It deliberately never grants execution."""
    r = registration
    require(r['schema'] == SCHEMA and r['admitted_arms'] == ['GEOM11'], 'Only the explicitly promoted fixed GEOM11 control')
    require(r['selection'] == SELECTION and r['official_source_count'] == 426
        and r['whole426_protected'] is True and r['all_original_times_unchanged'] is True
        and r['all_vertical_boxes_unchanged'] is True and r['outside_D_boxes_unchanged'] is True
        and r['no_nearest_or_interpolation'] is True, 'Whole40.47 time/vertical/outside-domain protection')
    require(r['additional_parameters'] == ADDITIONAL_PARAMETERS
        and r['pipeline_parameters'] == PIPELINE_PARAMETERS
        and r['physical_GPU_parameters'] == PHYSICAL_GPU_PARAMETERS
        and PIPELINE_PARAMETERS <= 9_000_000_000, 'Count the frozen critic and every conservative pipeline component')
    require(r['hidden_transform'] == HIDDEN_TRANSFORM and r['policy'] == 'TRUST124_THEN_GEOM129_GAIN_STRICTLY_POSITIVE'
        and r['automatic_launch'] is False and r['automatic_production'] is False,
        'Fixed105 L2 coordinate model/124 projection/promoted129 positive gain policy; no automatic action')
    for key in REQUIRED_REFS:
        _ref(r[key])
    require(r['protected_baseline']['sha256'] == BASELINE_SHA, 'Exact protected40.47 ZIP identity')
    require(_integer(r['expected_sources'], positive=True) and r['expected_sources'] >= PILOT_OWNERS
        and _integer(r['expected_affected_videos'], positive=True) and r['expected_affected_videos'] <= 426,
        'Actual observation-owner count and affected-video count; neither is hardcoded303/6563')
    return dict(status='CONDITIONAL_SCHEMA_ONLY_NOT_EXECUTION_ADMISSION', execution_supported=False,
        expected_sources=r['expected_sources'], official_source_count=426,
        expected_affected_videos=r['expected_affected_videos'])


def validate_lineage(registration, development, promotion, fresh8, trained):
    """Require explicit129 promotion + actual134; retain failed128 as negative evidence."""
    validate_schema(registration)
    r, d, p, f, t = registration, development, promotion, fresh8, trained
    require(d['status'] == 'STOP_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC' and d['admitted_arms'] == []
        and d['state'] == r['critic_state'] and d['exact_save_reload'] is True
        and d['additional_parameters'] == ADDITIONAL_PARAMETERS
        and d['pipeline_parameters'] == PIPELINE_PARAMETERS, 'Original128 remains STOP with exact saved state; never invent128PASS')
    require(p['schema'] == 'FIXED_GEOM129_POSTHOC_CONTROL_PROMOTION_ONLY' and p['arm'] == 'GEOM11'
        and p['source_result'] == r['development_result'] and p['state'] == r['critic_state']
        and p['posthoc_control_promotion'] is True and p['old128_STOP_preserved'] is True
        and p['no_refit'] is True and p['development_only'] is True and p['new_file_test_only'] is True
        and p['fresh8_trials'] == 1 and p['production_admitted'] is False
        and p['pipeline_parameters'] == PIPELINE_PARAMETERS,
        'Explicit posthoc129 promotion keeps original negative evidence and unchanged fixed coefficients')
    require(set(p['existing_development']) == set(d['evaluations']) == {'native20', 'historical19'}, 'Both exposed GEOM development groups separately retained')
    for scope, count in (('native20', 20), ('historical19', 19)):
        e = d['evaluations'][scope]['arms']['GEOM11']
        require(e['summary']['sources'] == count and e['quality']['admitted'] is True and e['quality']['checks']
            and all(v is True for v in e['quality']['checks'].values())
            and any(x['trust_changed'] and not x['changed'] for x in e['rows']),
            'Promoted GEOM development groups independently meet original gates, without relabelling128 primary')
    require(f['status'] == FRESH8_PASS and f['admitted_arms'] == ['GEOM11']
        and f['quality']['admitted'] is True and f['quality']['checks']
        and all(v is True for v in f['quality']['checks'].values())
        and f['summary']['sources'] == 8 and f['development_result'] == r['development_result']
        and f['critic_state'] == r['critic_state'] and f['promotion'] == r['promotion']
        and f['pipeline_parameters'] == PIPELINE_PARAMETERS
        and f['new_fit'] == 0 and f['automatic_production'] is False,
        'Actual separately completed fresh8 V134 PASS required; a conditional worker is not evidence')
    require(t['status'] == 'COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY'
        and t['completed_updates'] == 778 and t['successful_micro'] == t['actual_training_forwards'] == 3112
        and t['original_successful_updates'] == 20 and t['original_successful_forwards'] == 88
        and t['total_adopted_plus_new_updates'] == 798 and t['hidden_transform'] == HIDDEN_TRANSFORM
        and t['adapter_reload_all288_exact'] is True and t['head_reload_all2_exact'] is True,
        'Only the unchanged completed105 final778+adopt20 model, not an earlier adapter')
    for key in MODEL_REFS:
        require(d[key] == p[key] == f[key] == r[key], 'Development/promotion/fresh8/current model references differ: ' + key)
    for key in ('adapter_weights', 'head_weights'):
        require(t[key] == r[key], 'Final105 weight identity differs: ' + key)
    return dict(status='CONDITIONAL_LINEAGE_VALID_NOT_EXECUTION_ADMISSION', execution_supported=False,
        automatic_launch=False, automatic_production=False, pipeline_parameters=PIPELINE_PARAMETERS)


def _identity(row):
    return {k: row[k] for k in ('video_id', 'source_sha256', 'native_ordinal', 'native_pts_exact', 'observation_index')}


def validate_owner_domain(registration, domain, sources, baseline_rows, clocks):
    """Check the supplied fixed domain against original native clocks/selected frames.

    This is metadata validation, not proof that an accepted observation inventory
    was completely read. That inventory must remain explicitly byte-bound by a
    future authorized preparer. Repeated video SHA across distinct frame owners
    is valid; repeated owner IDs or native frames are not.
    """
    validate_schema(registration)
    r = registration
    require(isinstance(sources, list) and len(sources) == r['expected_sources'], 'Exact registered observation-owner denominator')
    rows = {row['video_id']: row for row in baseline_rows}
    require(len(rows) == len(baseline_rows) == 426 and set(rows) == {str(i) for i in range(426)}, 'All original426 baseline records must remain present')
    require(domain['selection'] == SELECTION and domain['official_source_count'] == 426
        and domain['no_nearest_or_interpolation'] is True
        and domain['protected_baseline_sha256'] == BASELINE_SHA, 'Fixed exact even-observation domain and original baseline')
    all_d = domain['all_D']
    selected = domain['selected_D']
    require(isinstance(all_d, list) and isinstance(selected, list) and len(selected) == len(sources)
        and domain['all_D_count'] == len(all_d) and domain['selected_D_count'] == len(selected)
        and domain['all_D_sha256'] == digest(all_d) and domain['selected_D_sha256'] == digest(selected), 'Exact domain metadata digests/counts')
    require(selected == sources and sources == sorted(sources, key=lambda s: (s['source_sha256'], s['video_id'], s['native_ordinal'])),
        'No score/source postselection or reordering of the fixed sourceSHA domain')
    identities = []
    native_pairs = set()
    observed_pairs = set()
    for row in all_d:
        vid, native, observation = row['video_id'], row['native_ordinal'], row['observation_index']
        require(vid in rows and _sha(row['source_sha256']) and _integer(native) and _integer(observation), 'Actual integer native/observation identity')
        require((vid, native) not in native_pairs and (vid, observation) not in observed_pairs, 'No duplicate source/native or observation owner')
        native_pairs.add((vid, native)); observed_pairs.add((vid, observation))
        b, c = rows[vid], clocks[vid]
        selected_frames = {p['frame']: p['bboxes'] for p in b['predictions']}
        require(len(selected_frames) == len(b['predictions']) and b['targetRatioWH'] == [16, 9]
            and native in selected_frames, 'Every domain point is an originally selected native16:9 frame')
        require(c['video_id'] == vid and c['source_sha256'] == row['source_sha256']
            and native < len(c['normalized_exact_pts'])
            and Fraction(row['native_pts_exact']) == Fraction(c['normalized_exact_pts'][native]), 'Exact native PTS/owner hash; no nearest/interpolated substitution')
        if observation % 2 == 0:
            identities.append(_identity(row))
    identities.sort(key=lambda s: (s['source_sha256'], s['video_id'], s['native_ordinal']))
    require(identities == [_identity(s) for s in sources], 'Selected D must equal the entire supplied all-D even intersection')
    seen_ids = set()
    for s in sources:
        owner = 'official:%s:native:%d' % (s['video_id'], s['native_ordinal'])
        require(s['source_id'] == owner and owner not in seen_ids and s['role'] == 'formal'
            and s['original_BASE_observed'] is True and s['targetRatioWH'] == [16, 9], 'Distinct exact virtual frame owner, not a whole-video surrogate')
        seen_ids.add(owner)
        require(_integer(s['width'], positive=True) and _integer(s['height'], positive=True), 'Original positive native dimensions')
        original = {p['frame']: p['bboxes'] for p in rows[s['video_id']]['predictions']}[s['native_ordinal']]
        require(s['baseline_box'] == original, 'Source baseline must be the exact original40.47 selected frame box')
    affected = len({s['video_id'] for s in sources})
    require(domain['affected_video_count'] == r['expected_affected_videos'] == affected, 'Actual affected-video count, within426; no historical303 assumption')
    ids = [s['source_id'] for s in sources]
    require(domain['pilot_source_ids'] == ids[:PILOT_OWNERS] and domain['remaining_source_ids'] == ids[PILOT_OWNERS:], 'Pilot32 and exact remaining-owner partition')
    return dict(status='SUPPLIED_OWNER_METADATA_VALID_NOT_INPUT_QA', sources=len(sources),
        official_source_count=426, affected_video_count=affected, owner_ids=ids,
        source_set_sha256=digest([_identity(s) for s in sources]), execution_supported=False)


def stage_partition(domain, sources, *, stage, accepted_pilot=None):
    """Pure stage plan; accepted pilot owners can never be scheduled again.

    Cost/deadline admission and actual resource/ledger/QA evidence are purposely
    not fabricated here. A completed future controller would have to bind them
    before launching any remaining work.
    """
    require(stage in ('pilot32', 'remaining'), 'Only two separately authorized stages')
    ids = [s['source_id'] for s in sources]
    require(len(ids) >= PILOT_OWNERS and len(set(ids)) == len(ids)
        and domain['pilot_source_ids'] == ids[:PILOT_OWNERS]
        and domain['remaining_source_ids'] == ids[PILOT_OWNERS:], 'Exact fixed owner partition')
    if stage == 'pilot32':
        require(accepted_pilot is None, 'A successful pilot must be adopted rather than repeated')
        chosen = sources[:PILOT_OWNERS]
    else:
        require(isinstance(accepted_pilot, dict) and accepted_pilot.get('status') == 'PASS_RELATIVE132_PILOT32_FIRST_RAW_CPU_QA'
            and accepted_pilot.get('owner_ids') == ids[:PILOT_OWNERS]
            and accepted_pilot.get('new_forward_calls') == PILOT_OWNERS
            and accepted_pilot.get('first_input_QA_complete') is True
            and accepted_pilot.get('first_output_QA_complete') is True, 'Remaining requires exact actual successful32; no guessed completion')
        chosen = sources[PILOT_OWNERS:]
    return dict(stage=stage, owner_ids=[s['source_id'] for s in chosen], sources=copy.deepcopy(chosen),
        scheduled_new_owners=len(chosen), adopted_pilot_owners=0 if stage == 'pilot32' else PILOT_OWNERS,
        requires_separate_budget_and_execution_admission=True, execution_supported=False,
        automatic_launch=False, automatic_production=False)


def validate_protected_overlay(original_rows, proposed_rows, owner_sources):
    """Metadata-only invariant for a hypothetical completed whole426 overlay."""
    before = {r['video_id']: r for r in original_rows}
    after = {r['video_id']: r for r in proposed_rows}
    require(len(original_rows) == len(proposed_rows) == len(before) == len(after) == 426
        and set(before) == set(after) == {str(i) for i in range(426)}, 'Whole426 records retained')
    owners = {(s['video_id'], s['native_ordinal']) for s in owner_sources}
    require(len(owners) == len(owner_sources), 'No duplicate overlay owner')
    changed = []
    total = 0
    for vid, old in before.items():
        new = after[vid]
        require(new['targetRatioWH'] == old['targetRatioWH'], 'Every original target aspect remains unchanged')
        require([p['frame'] for p in new['predictions']] == [p['frame'] for p in old['predictions']], 'Exact original frame/time set and order preserved')
        total += len(old['predictions'])
        for a, b in zip(old['predictions'], new['predictions']):
            if a['bboxes'] != b['bboxes']:
                require(old['targetRatioWH'] == [16, 9] and (vid, a['frame']) in owners,
                    'No vertical or outside-D frame box change')
                changed.append((vid, a['frame']))
    return dict(records=426, original_frames=total, changed_owners=changed,
        all_original_times_unchanged=True, all_vertical_boxes_unchanged=True,
        outside_D_boxes_unchanged=True, independent11strict_verified=False,
        CRC_verified=False, package_qualified=False, execution_supported=False)
