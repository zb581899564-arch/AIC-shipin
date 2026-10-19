"""Five frozen native-frame set policies from actual accepted TIME/BASE outputs.

No learning, output repair, forced nonempty answer, fallback or automatic submit.
Only the original spatial availability intersection is inherited from scope16;
its old nonempty quality gate is not interpreted as an official format rule.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
import zipfile

from qa_outputs41 import (W, SCHEMA, PARAMETERS, QA_STATUS, require, read, sha,
                          bound, ref, identity, save)

BASELINE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
POLICIES = {
    1: ('BASELINE_PLUS_CONSENSUS', 'B union (T intersection C)'),
    2: ('BASELINE_SUPPORTED', 'B intersection (T union C)'),
    3: ('ORIGINAL_TIME_SUMMARY', 'T'),
    4: ('BASE_SUMMARY', 'C'),
    5: ('SUPPORTED_PLUS_CONSENSUS', '(B intersection (T union C)) union (T intersection C)'),
}


def lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def dump(path, rows):
    with Path(path).open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())


def canonical(rows):
    value = [{key:row[key] for key in ('video_id', 'targetRatioWH', 'predictions')}
             for row in sorted(rows, key=lambda item:item['video_id'])]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def policy_sets(baseline, time, base):
    b, t, c = set(baseline), set(time), set(base)
    return {1:b | (t & c), 2:b & (t | c), 3:t, 4:c, 5:(b & (t | c)) | (t & c)}


def accepted_selection(details, expected_sources, expected_windows):
    require(len(details) == expected_windows and len({row['uid'] for row in details}) == expected_windows,
            'Every unique accepted output window required')
    selected, seen = set(), set()
    for row in details:
        sid = row['sid']; require(sid in expected_sources, 'Unregistered accepted source')
        seen.add(sid)
        for left, right in row['native_ranges']:
            require(type(left) is int and type(right) is int and 0 <= left <= right,
                    'Only exact QA-accepted native ordinal ranges')
            selected.update((sid, ordinal) for ordinal in range(left, right))
    require(seen == expected_sources, 'All sources must have actual outputs, including successful empty answers')
    return selected


def keymap(rows):
    result = {(row['video_id'], item['frame']):item['bboxes'] for row in rows for item in row['predictions']}
    require(len(result) == sum(len(row['predictions']) for row in rows), 'Duplicate prediction source ordinals')
    return result


def checked_history(reg):
    values = reg['historical_prediction_sha256']
    require(isinstance(values, list) and values and all(isinstance(value, str) and len(value) == 64
            and set(value) <= set('0123456789abcdef') for value in values),
            'Explicit complete historical prediction fingerprints required')
    return set(values)


def main(registration_path):
    require(os.uname().nodename == 'inspur-NP5570M5', 'Only the actual registered Linux CPU host')
    regpath = Path(registration_path).resolve(strict=True); reg = read(regpath)
    require(regpath.is_relative_to(W) and reg['schema'] == SCHEMA
            and reg['expected_sources'] == 426 and reg['expected_windows'] == 522
            and reg['actual_resident_parameters'] == PARAMETERS
            and type(reg['actual_pipeline_parameters']) is int
            and PARAMETERS <= reg['actual_pipeline_parameters'] <= 9_000_000_000,
            'Fixed five-policy registration and complete shared model parameter count')
    pipeline = reg['actual_pipeline_parameters']
    by_policy = reg['actual_pipeline_parameters_by_policy']
    require(isinstance(by_policy, dict) and set(by_policy) == {str(index) for index in POLICIES}
            and all(type(value) is int and PARAMETERS <= value <= pipeline for value in by_policy.values())
            and max(by_policy.values()) == pipeline
            and all(by_policy[str(index)] == pipeline for index in (1, 2, 5))
            and all(by_policy[str(index)] == PARAMETERS for index in (3, 4)),
            'Exact per-policy complete dependency count; policies using B include its historical head')
    root = Path(reg['root']).resolve(strict=True)
    require(root.is_relative_to(W), 'Only the independent new sprint root')
    here = Path(__file__).resolve().parent
    for name in ('package_five41.py', 'qa_outputs41.py'):
        require(bound(reg['code'][name]) == here/name, 'Actual package/helper code binding')
    qa = read(bound(reg['formal_output_QA_ref']))
    require(qa['status'] == QA_STATUS and qa['sources'] == 426 and qa['windows_per_role'] == 522
            and qa['total_outputs'] == 1044 and qa['invalid_outputs'] == 0
            and qa['unique_ledger_equal'] is True and qa['job_name'] == reg['job_name']
            and qa['actual_resident_parameters'] == PARAMETERS and qa['actual_pipeline_parameters'] == pipeline
            and set(qa['roles']) == {'TIME', 'BASE'}, 'Actual first independent all-role output QA required')
    admission = read(bound(reg['package_admission_ref']))
    require(admission['status'] == 'ADMIT_REVIEWED_FIVE_SUMMARY_PACKAGES_41'
            and admission['production_allowed'] is True and admission['main_review_completed'] is True
            and admission['official_empty_predictions_allowed'] is True
            and admission['catastrophic_collapse_rejected'] is True
            and identity(admission['formal_output_QA_ref']) == identity(reg['formal_output_QA_ref'])
            and admission['actual_pipeline_parameters'] == pipeline
            and admission['fixed_spatial_eligibility_policy_ref'] == reg['spatial_eligibility_policy_ref'],
            'Actual post-generation main collapse review and package admission required')
    approved = admission['approved_policies']
    require(isinstance(approved, list) and approved and len(approved) == len(set(approved))
            and all(type(value) is int and value in POLICIES for value in approved), 'Explicit reviewed fixed policy IDs')
    reviews = admission['role_collapse_review']
    require(set(reviews) == {'TIME', 'BASE'} and all(value['review_completed'] is True
            and value['catastrophic_collapse'] is False for value in reviews.values()),
            'Main reviewer must actually reject all-empty or severe collapse in either new role')
    require(all(qa['roles'][role]['all_sources_empty'] is False for role in ('TIME', 'BASE')),
            'STOP_ALL_EMPTY_ROLE_NO_PRODUCTION: valid empty outputs remain raw evidence, never fallback')
    rules = read(bound(reg['rule_check_before_package_ref']))
    require(rules['summary_production_scope_checked'] is True and rules['not_official_special_permission'] is True
            and rules['official_empty_predictions_allowed'] is True,
            'Actual official empty-list rule and method scope must be explicitly checked')
    inventory = read(bound(reg['pipeline_inventory_ref']))
    require(inventory['actual_pipeline_parameters'] == pipeline
            and inventory['actual_pipeline_parameters_by_policy'] == by_policy
            and inventory['participating_roles_frozen'] is True,
            'Shared BASE, original TIME and inherited spatial model counted once within 9B')
    for reference in (qa['completion_ref'], qa['resource_ref']):
        bound(reference)
    # Retain the exact successful execution ledger join; never rely only on QA status text.
    resource = read(bound(qa['resource_ref']))
    ledger = [json.loads(line) for line in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip() and json.loads(line).get('name') == reg['job_name']]
    require(resource['status'] == 'completed' and type(resource['exit_code']) is int
            and resource['exit_code'] == 0 and ledger == [resource], 'Natural completed/exit0 unique ledger still exact')
    expected = {str(i) for i in range(426)}
    raw = {}
    for role in ('TIME', 'BASE'):
        report = qa['roles'][role]
        complete = read(bound(report['completion_ref']))
        require(complete['outputs'] == report['outputs'] and complete['model_role'] == role
                and complete['model_weights_ref'] == reg['original_TIME_ref'], 'Role QA immutable output and original TIME join')
        for reference in report['outputs']:
            bound(reference)
        raw[role] = accepted_selection(report['details'], expected, 522)
    inp = read(bound(reg['package_inputs_ref']))
    fields = {name:bound(reference) for name,reference in inp['source_field_files'].items()}
    policy = read(bound(reg['spatial_eligibility_policy_ref']))
    require(policy['status'] == 'FIXED_PREOUTPUT_ORIGINAL_SPATIAL_DOMAIN_ELIGIBILITY_NOT_NEW_QUALITY_RULE'
            and policy['formal_outputs_read'] is False and policy['final_dev_metrics_read'] is False
            and policy['field_ref']['sha256'] == inp['source_field_files']['field_frames.jsonl']['sha256']
            and reg['official_empty_predictions_allowed'] is True,
            'Only pre-output scope16 availability intersection; no inherited nonempty format restriction')
    field_rows = lines(fields['field_frames.jsonl'])
    field_by_key = {(row['video_id'], row['source_frame']):row for row in field_rows}
    domain = set(field_by_key)
    require(len(domain) == len(field_rows) and set(qa['source_native_counts']) == expected,
            'Unique original spatial field and all original native clocks')
    require(all(sid in expected and type(ordinal) is int and 0 <= ordinal < qa['source_native_counts'][sid]
                for sid,ordinal in domain | raw['TIME'] | raw['BASE']), 'Every selected or field ordinal is original native PTS')
    basepath = bound(reg['protected_baseline_ref'])
    require(reg['protected_baseline_ref']['sha256'] == BASELINE_SHA, 'Protected40.47 exact ZIP identity')
    with zipfile.ZipFile(basepath) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None, 'Protected baseline archive shape/CRC')
        baseline = [json.loads(line) for line in archive.read('predictions.jsonl').splitlines() if line.strip()]
    require(len(baseline) == 426 and {row['video_id'] for row in baseline} == expected, 'Protected baseline426 exact index set')
    old = keymap(baseline); b = set(old)
    require(b <= domain, 'Every protected baseline frame must retain its actual original spatial field')
    selected_sets = policy_sets(b, raw['TIME'] & domain, raw['BASE'] & domain)
    raw_sets = policy_sets(b, raw['TIME'], raw['BASE'])
    require(all(selected_sets[index] == raw_sets[index] & domain for index in POLICIES)
            and b <= selected_sets[1] and selected_sets[2] <= b, 'Frozen strategy algebra and baseline preservation/subset')
    for reference in reg['renderer_code_refs'].values():
        bound(reference)
    sys.path[:0] = reg['renderer_import_paths']
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    for name in ('field_contract.py', 'pts_contract.py'):
        require(Path(sys.modules[name[:-3]].__file__).resolve() == bound(reg['renderer_code_refs'][name]),
                'Only frozen original spatial composition modules')
    union = set().union(*selected_sets.values())
    selected_union = [row for row in field_rows if (row['video_id'], row['source_frame']) in union]
    rows_union, provenance_union = compose_from_field(legacy_manifest(read(bound(inp['source_manifest']))), selected_union,
        lines(fields['field_shots.jsonl']), lines(fields['anchor_requests.jsonl']), lines(fields['anchor_output.jsonl']))
    current_union = keymap(rows_union)
    require(len(rows_union) == 426 and {row['video_id'] for row in rows_union} == expected and set(current_union) == union
            and all(current_union[key] == old[key] for key in b), 'Real source fields reproduce every retained baseline box')
    ratios = {row['video_id']:row['targetRatioWH'] for row in baseline}
    require(all(row['targetRatioWH'] == ratios[row['video_id']] for row in rows_union), 'Original target ratios exact')
    history = checked_history(reg); history.add(canonical(baseline))
    out = root/'packages41'; out.mkdir(exist_ok=False)
    save(out/'fixed_field_eligibility41.json', dict(policy_ref=reg['spatial_eligibility_policy_ref'],
        inherited_only='original_field_availability_intersection', old_scope16_quality_gate_unchanged=True,
        official_empty_predictions_allowed=True, raw_model_outputs_unchanged=True,
        roles={role:dict(raw_native_frames=len(values), eligible_native_frames=len(values & domain),
              excluded_unavailable_field_frames=len(values-domain),
              excluded_original_source_ordinals=[dict(sid=sid,source_frame=ordinal) for sid,ordinal in sorted(values-domain)])
              for role,values in raw.items()}, no_new_spatial_model_or_guessed_box=True))
    results, seen_predictions = [], {}
    for index, (name, expression) in POLICIES.items():
        selected = selected_sets[index]
        actual_parameters = by_policy[str(index)]
        common = set(selected) & b
        rows = [dict(video_id=row['video_id'], targetRatioWH=row['targetRatioWH'], model_params_b=actual_parameters/1e9,
                     predictions=[item for item in row['predictions'] if (row['video_id'],item['frame']) in selected])
                for row in rows_union]
        actual = keymap(rows); checksum = canonical(rows)
        require(set(actual) == selected and all(actual[key] == old[key] for key in common), 'Exact policy and retained original boxes')
        require(index != 1 or all(key in actual and actual[key] == value for key,value in old.items()), 'Policy1 must keep all B frames/boxes')
        require(index != 2 or set(actual) <= b, 'Policy2 must be a B subset')
        entry = dict(policy=index, name=name, expression=expression, canonical_sha256=checksum,
            records=426, frames=len(selected), added_frames=len(selected-b), removed_frames=len(b-selected),
            empty_source_ids=sorted(expected-{sid for sid,ordinal in selected}, key=int),
            excluded_unavailable_field_frames=len(raw_sets[index]-domain), official_score='UNKNOWN',
            actual_resident_parameters=PARAMETERS, actual_pipeline_parameters=actual_parameters)
        reason = ('NOT_APPROVED_BY_MAIN_REVIEW' if index not in approved else
                  'STOP_ALL_EMPTY_POLICY_NO_PRODUCTION' if not selected else
                  'DUPLICATE_BASELINE_OR_HISTORY' if checksum in history else
                  'DUPLICATE_POLICY_'+str(seen_predictions[checksum]) if checksum in seen_predictions else None)
        if reason:
            entry.update(status='PENDING_NOT_PUBLISHED', reason=reason)
            results.append(entry); continue
        directory = out/('%02d_%s' % (index,name)); directory.mkdir(exist_ok=False)
        chosen = [row for row in field_rows if (row['video_id'],row['source_frame']) in selected]
        provenance = [row for row in provenance_union if (row['video_id'],row['source_frame']) in selected]
        dump(directory/'predictions.jsonl',rows); dump(directory/'selected.jsonl',chosen)
        dump(directory/'provenance.jsonl',provenance); save(directory/'metadata.json',read(bound(inp['metadata'])))
        pending = directory/('candidate_'+name+'.PENDING.zip')
        with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as archive:
            archive.write(directory/'predictions.jsonl','predictions.jsonl')
        subprocess.run([reg['python'],'-B',str(bound(reg['independent_validator_ref'])),
            '--strict-loader-root',reg['strict_loader_root'],'--metadata',str(directory/'metadata.json'),
            '--selected',str(directory/'selected.jsonl'),'--predictions',str(directory/'predictions.jsonl'),
            '--provenance',str(directory/'provenance.jsonl'),'--zip',str(pending),
            '--report',str(directory/'independent_validation.json')],check=True)
        validation = read(directory/'independent_validation.json'); checks=validation['checks']
        require(len(checks)==11 and all(value is True for value in checks.values())
                and not validation['strict_loader_issues'], 'All actual independent11strict checks must pass, including legal empty rows')
        with zipfile.ZipFile(pending) as archive:
            require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None
                    and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest()==sha(directory/'predictions.jsonl'),
                    'Single JSONL ZIP, CRC and member SHA')
        require(sha(basepath)==BASELINE_SHA, 'Original40.47 protected file changed')
        final=directory/('candidate_'+name+'.zip'); pending.rename(final)
        entry.update(status='NEW_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN',zip=ref(final),
            member_sha256=sha(directory/'predictions.jsonl'), independent11strict=True,
            output_QA_ref=reg['formal_output_QA_ref'],production_admission_ref=reg['production_admission_ref'],
            package_admission_ref=reg['package_admission_ref'],
            retained_baseline_boxes_exact=True, all_original_native_PTS=True, website_submitted=False)
        save(directory/'completion.json',entry); results.append(entry); seen_predictions[checksum]=index
    accepted_count=sum(row['status']=='NEW_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN' for row in results)
    save(out/'completion.json',dict(status='FIVE_POLICY_ENGINEERING_COMPLETE' if accepted_count==5 else 'PENDING_DISTINCT_ACCEPTED_PACKAGES_INSUFFICIENT',
        requested_packages=5,accepted_packages=accepted_count,pending_packages=5-accepted_count,results=results,
        official_empty_predictions_allowed=True, source_empty_results_preserved_not_fallback=True,
        policy_strategies_frozen=True, field_eligibility_ref=ref(out/'fixed_field_eligibility41.json'),
        output_QA_ref=reg['formal_output_QA_ref'],package_admission_ref=reg['package_admission_ref'],
        actual_resident_parameters=PARAMETERS, actual_pipeline_parameters=pipeline,
        actual_pipeline_parameters_by_policy=by_policy,
        original40_47_unchanged=True,original40_47_sha256=BASELINE_SHA,
        utc=datetime.now(timezone.utc).isoformat(),website_submitted=False))
    print(json.dumps(dict(accepted_packages=accepted_count,pending_packages=5-accepted_count)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True)
    argument=parser.parse_args().registration
    try:
        main(argument)
    except BaseException as error:
        root=Path(read(argument)['root']);failure=root/'formal_package41_failure.json'
        if root.is_dir() and not failure.exists():
            save(failure,dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_outputs=True,
                automatic_retry=False,no_model_rerun=True,failure_to_empty=False))
        raise
