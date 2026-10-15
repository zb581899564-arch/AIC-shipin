"""Publish only the fifth arm after the one registered short-source confirmation.

No model, media preparation, metric recomputation or retry is performed here.
The original no-application FAIL remains immutable and separately referenced.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import socket
import subprocess
import sys
import traceback

HOME = Path('/home/inspur/aic_video_work')
ROOT = HOME / 'midnight_five_verify40_46_20261015_v1'
NEW = HOME / 'midnight_pair_applicability_20261015_v1'
PY = HOME / 'env/qwen3vl_isolated_20260910/bin/python'
CODE = ROOT / 'pair_supplement_package_code_v1'
DEPLOYMENT = ROOT / 'pair_supplement_package_deployment_25.json'
STATE = ROOT / 'pair_supplement_finalization_25'
EXPECTED_COUNTS = dict(logical_cases=519, actual_model_calls=518,
    adopted_identical_input_aliases=1, first_model_output_QA_count=518,
    alias_application_QA_count=1)


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def checked(reference):
    path = Path(reference['path'])
    require(path.is_absolute() and path.resolve().is_relative_to(HOME) and
            sha(path) == reference['sha256'], 'Actual referenced bytes changed')
    return path


def save(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    require(socket.gethostname() == 'inspur-NP5570M5' and
            os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Linux CPU-only finalization required')
    require(not STATE.exists() and not (ROOT / 'packages/package_REDUNDANT').exists(),
            'An existing attempt must not be overwritten or automatically repeated')
    deployment = read(DEPLOYMENT)
    for path, digest in deployment['code_files'].items():
        checked(dict(path=path, sha256=digest))
    require(sha(__file__) == deployment['code_files'][str(Path(__file__).resolve())],
            'Finalizer not bound to its own deployment')
    for name in ('original_package_inputs_ref', 'original_quality_admission_ref',
                 'original_nonapplicable_confirmation_ref', 'history_ref'):
        checked(deployment[name])
    STATE.mkdir()
    save(STATE / 'started.json', dict(pid=os.getpid(),
         start_ticks=Path('/proc/self/stat').read_text().split()[21], UTC=utc()))
    try:
        control_path = NEW / 'control_01/completion.json'
        control = read(control_path)
        require(control['status'] in ('NATURAL_COMPLETE_FIRST_SHORT_SOURCE_PAIR_APPLICABILITY_CONFIRMATION',
                                    'STOP_FIRST_SHORT_SOURCE_PAIR_NOT_APPLICABLE'),
                'The registered new short-source parent must naturally complete or report genuine nonapplicability')
        result_path = NEW / 'policy_fresh_comparison.json'
        result = read(result_path)
        require(result['schema'] == 'MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1' and
                result['group'] == 'confirm' and result['full_source_count'] == 4 and
                result['selected_policies'] == ['PAIR_ONLY'], 'Exact one-cohort frozen policy result required')
        if result['passed_policies']['PAIR_ONLY'] is not True:
            save(STATE / 'completion.json', dict(status='SUPPLEMENTAL_SCIENTIFIC_REJECTED_NO_FIFTH',
                 comparison_ref=ref(result_path), parent_completion_ref=ref(control_path),
                 actual_total_new_packages=4, old_failures_unchanged=True,
                 new_model_calls=0, automatic_retry=False, UTC=utc()))
            print('SUPPLEMENTAL_SCIENTIFIC_REJECTED_NO_FIFTH', flush=True)
            return
        require(control['status'] == 'NATURAL_COMPLETE_FIRST_SHORT_SOURCE_PAIR_APPLICABILITY_CONFIRMATION',
                'Only the complete first real model/QA comparison can qualify the fifth arm')
        original_inputs = read(checked(deployment['original_package_inputs_ref']))
        original_quality = read(checked(deployment['original_quality_admission_ref']))
        protocol = read(checked(original_inputs['protocol_ref']))
        arm = dict(status='PASS',
            reference_scope_kind='SHORT_SOURCE_PAIR_APPLICABILITY_SUPPLEMENT_ONLY',
            reference_scope='One new hash-registered four-source author-duration<=30-second applicability stratum; unchanged PAIR_ONLY rule and original eight all-rater human-summary proxy gates. Original four-source zero-application FAIL is unchanged. This limited scope does not establish official highlight quality or global/pretraining independence.',
            supplemental_scope_only=True, independent_confirmation=True, test_labels_used=False,
            actual_model_parsed_unchanged=True, deterministic_deletion_policy='WORST_PAIR_ONLY',
            old_result_unchanged=True, policy_and_gates_unchanged=True,
            development_ref=original_quality['arms']['REDUNDANT']['development_ref'],
            confirmation_ref=ref(result_path), supplemental_confirmation_ref=ref(result_path),
            original_nonapplicable_confirmation_ref=deployment['original_nonapplicable_confirmation_ref'],
            supplementary_source_registration_ref=ref(NEW / 'positive_fresh_registration.json'),
            supplemental_parent_completion_ref=ref(control_path),
            supplemental_media_registration_ref=ref(NEW / 'media_registration.json'),
            frozen_rule_ref=original_inputs['protocol_ref'], official_improvement='UNKNOWN')
        sys.path.insert(0, str(CODE))
        from supplement_quality import validate_quality
        from production_evidence import validate_production_evidence
        validate_quality(arm, original_quality, original_inputs['protocol_ref'], protocol,
                         lambda reference: read(checked(reference)))
        production = read(checked(original_inputs['production_completion_ref']))
        _, counts = validate_production_evidence(production, lambda reference: read(checked(reference)), 8782459120)
        require(counts == EXPECTED_COUNTS, 'Original completed full-production denominator changed')
        quality_path = ROOT / 'quality_admission_pair_supplement.json'
        save(quality_path, dict(schema='ONE_SHORT_SOURCE_PAIR_APPLICABILITY_ADMISSION_V1',
             arms=dict(REDUNDANT=arm), old_result_unchanged=True, UTC=utc()))
        permit = dict(status='PASS_NEW_FIVE_WAY_CPU_PACKAGE_ENGINEERING_ADMISSION',
            actual_parameters=8782459120,
            production_completion_sha256=original_inputs['production_completion_ref']['sha256'],
            automatic_removal_and_recall_authorized=True, three_risk_arms_without_offline_quality_screening=True,
            test_labels_or_manual_edits_used=False, current_official_rules_rechecked=True,
            history_complete_for_all_preexisting_deliveries=True, production_evidence_counts=counts,
            original_package_inputs_ref=deployment['original_package_inputs_ref'],
            original_quality_admission_ref=deployment['original_quality_admission_ref'],
            supplementary_quality_admission_ref=ref(quality_path),
            existing_four_package_refs=deployment['existing_four_package_refs'], UTC=utc())
        permit_path = ROOT / 'pair_supplement_engineering_admission_25.json'
        save(permit_path, permit)
        inputs = dict(original_inputs, history_ref=deployment['history_ref'],
            code_files=deployment['code_files'], package_admission_ref=ref(permit_path),
            original_package_inputs_ref=deployment['original_package_inputs_ref'],
            original_quality_admission_ref=deployment['original_quality_admission_ref'],
            quality_admission_ref=ref(quality_path), existing_four_package_refs=deployment['existing_four_package_refs'])
        save(ROOT / 'package_inputs_pair_supplement.json', inputs)
        with (STATE / 'package.log').open('x') as log:
            subprocess.run([str(PY), '-B', str(CODE / 'package_five.py'), '--arms', 'REDUNDANT'],
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
                stdout=log, stderr=subprocess.STDOUT, check=True)
        receipt_path = ROOT / 'packages/package_REDUNDANT/completion.json'
        receipt = read(receipt_path)
        require(receipt['arm'] == 'REDUNDANT' and receipt['quality_pass_claimed'] is True and
                receipt['records'] == 426 and receipt['independent11strict'] is True,
                'Fifth package must actually complete all engineering checks')
        for name in ('original_package_inputs_ref', 'original_quality_admission_ref',
                     'original_nonapplicable_confirmation_ref'):
            checked(deployment[name])
        save(STATE / 'completion.json', dict(status='FIFTH_DISTINCT_LINUX_PACKAGE_COMPLETE_AWAIT_WINDOWS_DELIVERY',
             package_completion_ref=ref(receipt_path), supplemental_comparison_ref=ref(result_path),
             old_result_unchanged=True, actual_total_new_packages=5, new_model_calls=0, UTC=utc()))
        print('FIFTH_DISTINCT_LINUX_PACKAGE_COMPLETE_AWAIT_WINDOWS_DELIVERY', flush=True)
    except BaseException as error:
        save(STATE / 'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
             automatic_retry=False, keep_all_successful=True, UTC=utc()))
        raise


if __name__ == '__main__':
    main()
