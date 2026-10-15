"""Read new external predictions only after all registered human inputs pass."""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from human_metrics import mean_pairwise, paired_summary
from native_mapping_v3 import validate_mapping

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/human_reference_iteration_20261013_v1'
sys.path.insert(0, str(ROOT / 'improvement/boundary_refinement_v1'))
from intervals import expanded_windows, native_membership

ARMS = {'baseline': ('3/4', '1/2'), 'A': ('1', '1/2'),
        'B': ('3/4', '3/4'), 'C': ('1', '3/4')}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def admission(input_root):
    value = read(input_root / 'native_input_acceptance.json')
    if value.get('status') != 'PASS_ALL_REGISTERED_HUMAN_NATIVE_INPUTS':
        raise ValueError('All registered media/native inputs must pass before prediction access')
    if (value.get('registered_sources') != 20 or value.get('accepted_sources') != 20 or
            value.get('frame_mapping_failures') or not value.get('known_source_separation_pass')):
        raise ValueError('Incomplete or ambiguous human-source denominator')
    if value['registration_sha256'] != sha(REPORT / 'human_source_registration_01.json'):
        raise ValueError('Registered reference changed')
    if value['evaluation_policy_sha256'] != sha(REPORT / 'EVALUATION_POLICY.md'):
        raise ValueError('Pre-registered evaluation policy changed')
    if value['mapping_contract_sha256'] != sha(REPORT / 'NATIVE_MAPPING_CONTRACT_V3.md'):
        raise ValueError('Native acceptance does not bind the corrected pre-media mapping contract')
    if value['new_optimizer_updates'] != 0:
        raise ValueError('This protocol admits current B evaluation only')
    return value


def evaluate_role(registration, exported, role, arm_names):
    results = []
    for expected in registration['rows']:
        if expected['role'] != role:
            continue
        row = exported[expected['source_name']]
        proof = validate_mapping(expected, row['native_clock'])
        annotation = Path(expected['annotation_path'])
        if sha(annotation) != expected['annotation_sha256']:
            raise ValueError('Frozen original human annotation changed')
        human = loadmat(annotation)['user_score']
        if human.shape != (expected['annotation_frames'], expected['human_summary_columns']):
            raise ValueError('Human summary denominator changed')
        points = [F(t) for t in row['native_clock']['normalized_exact_pts']]
        windows = row['windows']
        if not windows or F(windows[0]['start_exact']) != 0:
            raise ValueError('Missing source beginning')
        if F(windows[-1]['end_exact']) != F(row['native_clock']['physical_end_exact']):
            raise ValueError('Missing source ending')
        if any(F(a['end_exact']) != F(b['start_exact']) for a, b in zip(windows, windows[1:])):
            raise ValueError('Source inference windows have a gap or overlap')
        for window in windows:
            if window['original_status'] != ('MODEL_OK' if window['segments'] else 'LEGAL_EMPTY'):
                raise ValueError('Failed or unrun model window must not become empty')
        masks = {}
        metrics = {}
        for arm in arm_names:
            indices = native_membership(points, expanded_windows(windows, *ARMS[arm]))
            mask = np.zeros(len(points), dtype=bool)
            mask[list(indices)] = True
            masks[arm] = mask
            metrics[arm] = mean_pairwise(mask, human)
        for arm in arm_names:
            if np.any(masks['baseline'] & ~masks[arm]):
                raise ValueError('Registered expansion removed baseline source frames')
            if metrics[arm]['recall'] < metrics['baseline']['recall']:
                raise ValueError('Expansion contradicted native recall monotonicity')
            metrics[arm]['added_frames'] = int((masks[arm] & ~masks['baseline']).sum())
        results.append(dict(source_name=expected['source_name'], source_group=expected['source_group'],
                            role=role, mapping=proof, metrics=metrics))
    assert len(results) == (12 if role == 'screen' else 8)
    return results


def summarize(results, arms):
    baseline = [row['metrics']['baseline']['f1'] for row in results]
    return {arm: paired_summary(baseline, [row['metrics'][arm]['f1'] for row in results])
            for arm in arms}


def main(input_root):
    accepted = admission(input_root)  # No prediction read or output directory precedes this gate.
    registration = read(REPORT / 'human_source_registration_01.json')
    expected = {row['source_name'] for row in registration['rows']}
    export_acceptance = read(input_root / 'developer_export_acceptance.json')
    if (export_acceptance.get('status') != 'PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY' or
            export_acceptance['native_input_acceptance_sha256'] != sha(input_root / 'native_input_acceptance.json') or
            export_acceptance['registered_sources'] != 20):
        raise ValueError('Export must bind the unchanged pre-GPU native acceptance')
    export_path = input_root / 'developer_prediction_export.json'
    if sha(export_path) != export_acceptance['developer_prediction_export_sha256']:
        raise ValueError('Successful prediction export changed')
    payload = read(export_path)
    if (payload['status'] != 'PASS_NEW_B_NATIVE_INFERENCE_AND_INDEPENDENT_CPU_REPLAY' or
            payload['model_parameters'] != 8782459120 or payload['new_optimizer_updates'] != 0 or
            payload['registered_sources'] != 20 or payload['successful_windows'] != payload['started_windows']):
        raise ValueError('Prediction export lacks complete successful B and independent CPU proof')
    exported = {row['source_name']: row for row in payload['rows']}
    if len(exported) != len(payload['rows']) or set(exported) != expected:
        raise ValueError('Missing, duplicate or additional prediction source')
    output = REPORT / 'comparison_v3_01'
    output.mkdir(exist_ok=False)
    save(output / 'launch_claim.json', dict(admission_sha256=sha(input_root / 'native_input_acceptance.json'),
             export_acceptance_sha256=sha(input_root / 'developer_export_acceptance.json'),
             source_registration_sha256=sha(REPORT / 'human_source_registration_01.json'),
             policy_sha256=sha(REPORT / 'EVALUATION_POLICY.md'), export_sha256=sha(export_path),
             script_sha256=sha(Path(__file__)), new_model_calls=0))
    screen_rows = evaluate_role(registration, exported, 'screen', tuple(ARMS))
    screen = summarize(screen_rows, ('A', 'B', 'C'))
    chosen = [arm for arm in ('A', 'B', 'C') if screen[arm]['diagnostic_risk_pass']]
    selection_path = output / 'screen_selection.json'
    save(selection_path, dict(chosen=chosen, screen=screen, frozen_before_confirm_metrics=True,
                             padding_exact={arm: ARMS[arm] for arm in chosen}))
    confirm_rows = evaluate_role(registration, exported, 'confirm', ('baseline', *chosen)) if chosen else []
    confirm = summarize(confirm_rows, chosen) if chosen else {}
    human_eligible = [arm for arm in chosen if confirm[arm]['diagnostic_risk_pass']]
    # Local silver veto remains a separate required step; it cannot grant human admission itself.
    result = dict(status='HUMAN_PROXY_COMPLETE_PENDING_PARTIAL_SILVER_FACT_VETO',
                  screen=screen, confirm=confirm, human_eligible=human_eligible,
                  candidate_package_admitted=False, screen_rows=screen_rows, confirm_rows=confirm_rows,
                  screen_selection_sha256=sha(selection_path), old_reference_quality_failed_preserved=True,
                  new_model_calls=0, new_optimizer_updates=0, official_score='UNKNOWN',
                  human_summary_proxy_not_official_crop_quality=True,
                  confirm_fallback_or_retuning=False)
    save(output / 'human_comparison.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('screen_rows', 'confirm_rows')}, ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
