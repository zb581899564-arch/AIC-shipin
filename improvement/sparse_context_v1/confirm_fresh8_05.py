"""Exactly one frozen sparse recipe on the new, previously unscored eight sources."""
from fractions import Fraction as F
from pathlib import Path
import json
import random
import sys

from sparse_stage_common_02 import read, save, sha

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/sparse_context_iteration_20261013_v1'
EXTERNAL = REPORT/'new_confirm_export_05'
OUT = REPORT/'confirmation_05'
sys.path.insert(0, str(ROOT/'improvement/videoxum_reference_v1'))
from evaluate_sparse_screen_01 import source_comparison


def admission():
    transfer = read(EXTERNAL/'transfer_acceptance.json')
    if transfer['status'] != 'PASS_WINDOWS_LINUX_BYTES_SHA_CRC_AND_ALL_COHORT_EXPORT_MEMBERS':
        raise ValueError('Actual new complete evidence transfer required')
    for name, item in transfer['manifest'].items():
        p = EXTERNAL/name
        if p.stat().st_size != item['bytes'] or sha(p) != item['sha256']:
            raise ValueError('Transferred fresh8 evidence changed')
    chain, gpu, replay, exported, native, prediction = [read(EXTERNAL/p) for p in (
        'new_confirm_chain_04/completion.json', 'new_confirm_gpu_04/completion.json', 'new_confirm_replay_04/completion.json',
        'new_confirm_export_acceptance.json', 'new_confirm_input_acceptance_04.json', 'new_confirm_prediction_export.json')]
    resource = read(EXTERNAL/'resource.json')
    if (chain['status'] != 'PASS_FRESH_B8_EXPORT_PENDING_FROZEN_SPARSE_CONFIRM_NOT_PACKAGE' or
        gpu['status'] != 'PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY' or
        replay['status'] != 'PASS_ALL_HUMAN_EXTERNAL_B_INDEPENDENT_CPU_REPLAYS' or
        exported['status'] != 'PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY' or
        native['status'] != 'PASS_INDEPENDENT_FRESH_CONFIRM8_ACTUAL_CPU_INPUTS_BEFORE_B' or
        any(x['registered_sources'] != 8 for x in (chain, gpu, replay, exported, native, prediction)) or
        not native['accepted_windows'] == gpu['actual_model_calls'] == gpu['successful_windows'] == replay['windows'] == prediction['started_windows'] == prediction['successful_windows'] or
        gpu['model_parameters'] != 8782459120 or gpu['new_optimizer_updates'] or gpu['reference_labels_read'] or
        prediction['model_parameters'] != 8782459120 or prediction['new_optimizer_updates'] or prediction['reference_labels_read'] or
        not replay['CPU_only'] or replay['CUDA_initialized'] or
        read(EXTERNAL/'matching_gpu_ledger.json') != [resource] or resource['status'] != 'completed' or resource['exit_code'] or
        resource['name'] != 'sparse_confirm8_original_b_native64_20261013_v1'):
        raise ValueError('New unique B8 inference/replay/source/resource scope changed')
    for body, key, name in [(gpu, 'source_lock_sha256', 'new_confirm_source_lock_04.json'),
        (gpu, 'native_input_acceptance_sha256', 'new_confirm_input_acceptance_04.json'),
        (gpu, 'attempts_sha256', 'new_confirm_gpu_04/attempts.jsonl'), (gpu, 'model_identity_sha256', 'new_confirm_gpu_04/model_identity.json'),
        (replay, 'gpu_completion_sha256', 'new_confirm_gpu_04/completion.json'), (replay, 'resource_terminal_sha256', 'resource.json'),
        (exported, 'independent_replay_completion_sha256', 'new_confirm_replay_04/completion.json'),
        (exported, 'native_input_acceptance_sha256', 'new_confirm_input_acceptance_04.json'),
        (exported, 'developer_prediction_export_sha256', 'new_confirm_prediction_export.json'),
        (chain, 'developer_export_acceptance_sha256', 'new_confirm_export_acceptance.json'),
        (chain, 'prediction_export_sha256', 'new_confirm_prediction_export.json'), (chain, 'resource_terminal_sha256', 'resource.json')]:
        if body[key] != sha(EXTERNAL/name):
            raise ValueError('Actual complete B8 lineage changed')
    events = [json.loads(line) for line in (EXTERNAL/'new_confirm_gpu_04/attempts.jsonl').read_text().splitlines()]
    if len(events) != 2*native['accepted_windows']:
        raise ValueError('Actual unique call denominator differs')
    for index, proof in enumerate(native['proofs'], 1):
        begun, accepted = events[2*(index-1):2*index]
        if begun['event'] != 'BEGIN_MODEL_CALL' or accepted['event'] != 'ACCEPTED_MODEL_CALL' or begun['call_id'] != index or accepted['call_id'] != index or begun['case_id'] != proof['case_id'] or accepted['case_id'] != proof['case_id']:
            raise ValueError('Actual unique B8 call order differs')
    reg_name = 'new_confirm_source_registration_01.json'
    chosen_name = 'screen_01/selection_before_new_confirm.json'
    if sha(EXTERNAL/reg_name) != sha(REPORT/reg_name) or sha(EXTERNAL/chosen_name) != sha(REPORT/chosen_name):
        raise ValueError('Pre-model source and candidate registration changed')
    reg, chosen, rule = read(REPORT/reg_name), read(REPORT/chosen_name), read(REPORT/'registration_01.json')
    if chosen['chosen'] != 'SPARSE50_POST025' or not chosen['old_confirm8_forbidden'] or not chosen['no_threshold_retuning']:
        raise ValueError('Single frozen sparse candidate required')
    if rule['rule_sha256'] != sha(ROOT/'improvement/videoxum_reference_v1/sparse_context_v1.py') or rule['evaluation_sha256'] != sha(ROOT/'improvement/videoxum_reference_v1/evaluate_sparse_screen_01.py'):
        raise ValueError('Registered exact rule or metric changed')
    if chosen['screen_sha256'] != sha(REPORT/'screen_01/SPARSE50_POST025_screen.json') or not read(REPORT/'screen_01/SPARSE50_POST025_screen.json')['original_fixed_gates_pass']:
        raise ValueError('Frozen development admission changed')
    facts = read(REPORT/'screen_01/fixed_fact_veto.json')['SPARSE50_POST025']
    if chosen['fact_sha256'] != sha(REPORT/'screen_01/fixed_fact_veto.json'):
        raise ValueError('Pre-confirmation fixed fact evidence changed')
    if not facts['pass_gate'] or len(facts['checks']) != 40 or any(x['ordinary_added'] or x['core_lost'] for x in facts['checks']):
        raise ValueError('Fixed40 factual gate changed')
    allowed = {x['video_id'] for x in reg['selection']+reg['ordered_engineering_reserves']}
    old = set(reg['old_exposed_source_ids'])
    ids = {x['video_id'] for x in native['sources']}
    if len(ids) != 8 or not ids <= allowed or ids & old or ids != {x['video_id'] for x in prediction['rows']} or any(x['group'] != 'confirm' for x in prediction['rows']):
        raise ValueError('Fresh8 identities overlap exposed sources or denominator changed')
    references = {}
    prefix = '/home/inspur/aic_video_work/sparse_context_iteration_20261013_v1/'
    for row in native['sources']:
        path = row['reference_path']
        if not path.startswith(prefix):
            raise ValueError('Unexpected fresh reference path')
        p = EXTERNAL/path[len(prefix):]
        if sha(p) != row['reference_sha256']:
            raise ValueError('Original fresh human reference changed')
        references[row['video_id']] = read(p)[0]
    return prediction['rows'], references


def main():
    if OUT.exists():
        raise ValueError('Fresh confirmation already scored; no repeated metrics or threshold tuning')
    predictions, references = admission()
    OUT.mkdir()
    save(OUT/'launch_claim.json', dict(script_sha256=sha(__file__),
        frozen_candidate_sha256=sha(REPORT/'screen_01/selection_before_new_confirm.json'),
        export_sha256=sha(EXTERNAL/'new_confirm_prediction_export.json'), transfer_sha256=sha(EXTERNAL/'transfer_acceptance.json'),
        old_confirm8_not_reused=True, new_model_calls=0, new_optimizer_updates=0))
    rows = [source_comparison(x, references[x['video_id']], 'SPARSE50_POST025') for x in predictions]
    deltas = [F(x['delta_exact']) for x in rows]
    macro = sum(deltas, F(0))/8
    changed = sum(x['actual_interval_changed'] and x['actual_native_frame_changed'] for x in rows)
    qualified = macro >= 0 and changed >= 3 and all(x['source_drop_gate'] for x in rows)
    rng = random.Random(20261013)
    boot = sorted(float(sum((deltas[rng.randrange(8)] for _ in range(8)), F(0))/8) for _ in range(5000))
    comparison = dict(group='new_confirm8', candidate='SPARSE50_POST025', sources=8, macro_delta_exact=str(macro),
        macro_delta=float(macro), paired_bootstrap95=[boot[125], boot[4874]], rows=rows, actual_changed_sources=changed,
        original_fixed_gates_pass=qualified, minimum_changed_sources=3, maximum_source_drop_exact='1/100',
        all_original_annotator_recalls_preserved=True, all_D8_frames_preserved=True,
        old_confirm_not_reused=True, no_threshold_retuning=True)
    save(OUT/'comparison.json', comparison)
    result = dict(status='PASS_FROZEN_SPARSE50_POST025_NEW8_CONFIRM_RISK_ADMISSION' if qualified else 'STOP_FROZEN_SPARSE50_POST025_NEW8_CONFIRM_REJECTED',
        qualified=qualified, candidate='SPARSE50_POST025', comparison_sha256=sha(OUT/'comparison.json'),
        launch_sha256=sha(OUT/'launch_claim.json'), new_model_calls=0, new_optimizer_updates=0, new_submission_zips=0,
        official_score='UNKNOWN', original20_exposed_and_old_failures_preserved=True,
        quality_scope='All original human interval summaries; temporal proxy only, no crop or official-score guarantee')
    save(OUT/'result.json', result)
    print(json.dumps(dict(status=result['status'],macro_delta=float(macro),changed_sources=changed,new_submission_zips=0)))


if __name__ == '__main__':
    main()
