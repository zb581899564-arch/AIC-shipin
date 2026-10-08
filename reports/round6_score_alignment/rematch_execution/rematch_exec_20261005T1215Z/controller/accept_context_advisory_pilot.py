"""Independent complete pilot CPU replay; no model or optimizer calls."""
from collections import Counter
import datetime as dt
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
import traceback

RUN = Path(__file__).resolve().parent.parent
HERE = RUN / 'context_advisory_v1'
sys.path.insert(0, str(HERE))
import runtime as rt
import experiment as ex
import context_contract as cc


def main():
    receipt = RUN / 'controller/C_ADVISORY_pilot_acceptance_20261009.json'
    cc.require(socket.gethostname() == 'inspur-NP5570M5', 'actual host identity')
    cc.require(not receipt.exists(), 'pilot already independently accepted; do not repeat')
    lock = ex.verify()
    # Reuse only the CPU checking function, not its first-generation main.
    proof = rt.load(RUN / 'controller/accept_context_advisory_first_real.py', 'cad_cpu_attempt_check_only')
    student, old, _, _ = rt.bind_helpers()
    report = rt.load(HERE / 'report.py', 'cad_pilot_report_read_only')
    from transformers import AutoProcessor
    cfg = ex.read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True,
        min_pixels=131072, max_pixels=131072)
    plan = ex.read(HERE / 'input_01/developer_plan.json')
    jobs = [j for j in plan['developer_jobs'] if j['video_id'] in plan['pilot_video_ids']]
    sources = ex.source_tables(plan)
    needed = {j['source_key'] for j in jobs}
    needed |= {plan['shuffle_source_mapping'][j['source_key']] for j in jobs}
    cc.require(len(jobs) == len(needed) == len({j['source_group'] for j in jobs}) == 24,
        'original pilot24 file/group denominator')
    windows = sum(len(j['windows']) for j in jobs)
    cc.require(windows == 26, 'original pilot natural windows changed')
    out = HERE / 'developer_01'
    completion = ex.read(out / 'pilot.completion.json')
    model = ex.read(out / 'pilot.model.json')
    cc.require(completion['status'] == 'PASS_ALL_REGISTERED_ADVISORY_ATTEMPTS'
        and completion['stage'] == 'pilot' and completion['records'] == 24
        and completion['source_files'] == 24
        and completion['arms'] == ['B1', 'B0', 'N', 'R', 'X']
        and completion['fresh_local_calls'] == 130 and completion['reused_local_calls'] == 0
        and completion['fresh_overview_calls'] == 24 and completion['reused_overview_calls'] == 0
        and completion['model_identity'] == model, 'actual complete pilot counts/model')
    cc.require(model == ex.read(HERE / 'nontest_01/nontest.model.json')
        and model['logical_parameters'] == 8782459120
        and model['adapter_saved_tensor_equality'] == 288 and model['new_optimizer_updates'] == 0,
        'actual pilot frozen B identity')
    cc.require(ex.sha(Path(cfg['b_adapter']) / 'adapter_model.safetensors') == model['adapter_sha256']
        == cfg['b_adapter_sha256'], 'actual saved adapter byte identity')
    tables, overview, local = {}, [], []
    for key in sorted(needed):
        w = ex.overview_window(sources[key], key)
        request = {'kind': 'overview', 'window': w, 'prompt': rt.OVERVIEW_TEXT, 'model': model,
            'max_input': 16384, 'max_output': 1280, 'adapter_disabled': True}
        path = out / 'overview' / key / 'done.json'
        overview.append(proof.check_attempt(path, request, processor, student.decode_window(w), rt.OVERVIEW_TEXT))
        tables[key] = ex.read(path)
        print(json.dumps({'CPU_stage': 'PILOT_OVERVIEW_REPLAY', 'completed': len(overview),
            'total': 24, 'new_model_calls': 0}), flush=True)
    texts = ex.base_texts(old)
    for num, job in enumerate(jobs, 1):
        table = tables[job['source_key']]
        donor = tables[plan['shuffle_source_mapping'][job['source_key']]]
        for ix, part in enumerate(job['windows']):
            w = part['window']
            decoded = student.decode_window(w)
            for arm in ('B1', 'B0', 'N', 'R', 'X'):
                text, audit = ex.arm_text(arm, w, table, donor, texts)
                request = {'kind': 'local', 'window': w, 'arm': arm, 'prompt': text, 'model': model,
                    'max_input': 16384, 'max_output': 256, 'allow_empty': arm != 'B1', 'context_audit': audit}
                path = out / 'local' / cc.digest(job['video_id']) / str(ix) / arm / 'done.json'
                value = proof.check_attempt(path, request, processor, decoded, text)
                value.update(video_id=job['video_id'], window_index=ix, arm=arm)
                local.append(value)
            del decoded
        print(json.dumps({'CPU_stage': 'PILOT_LOCAL_REPLAY', 'videos': num,
            'total': 24, 'local_attempts': len(local), 'new_model_calls': 0}), flush=True)
    _, _, rows = report.records('pilot')
    cc.require(rows == ex.read(out / 'pilot.mechanism_rows.json'), 'original label-blind mechanism rows')
    actual_report = ex.read(out / 'pilot.report.json')
    cc.require(actual_report['status'] == 'PASS_LABEL_BLIND_MECHANISM_REPORT_NOT_QUALITY'
        and actual_report['records'] == actual_report['source_groups'] == 24
        and actual_report['weak_reference_used'] is False
        and actual_report['R_N_changed_native_sets'] == sum(not r['native_selected_sets_R_N_equal'] for r in rows)
        and actual_report['R_X_changed_native_sets'] == sum(not r['native_selected_sets_R_X_equal'] for r in rows),
        'reported pilot denominator and native-set comparisons')
    cc.require(len(local) == 130 and Counter(x['arm'] for x in local)
        == Counter({a: 26 for a in ('B1', 'B0', 'N', 'R', 'X')}), 'all original five-arm attempts')
    resource_path = RUN / 'controller/aic_CAD_v1_pilot.resource.json'
    resource = ex.read(resource_path)
    ledger = Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    matches = [r for r in old.rows(ledger) if r.get('name') == 'aic_CAD_v1_pilot']
    cc.require(len(matches) == 1 and matches[0] == resource and resource['status'] == 'completed'
        and resource['exit_code'] == 0 and resource['stop_reason'] is None
        and resource['charged_seconds'] > 0, 'unique actual pilot GPU terminal ledger')
    result = {'status': 'PASS_INDEPENDENT_COMPLETE_PILOT_CPU_NATIVE_PROCESSOR_REPLAY',
        'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'source_lock_sha256': ex.sha(HERE / 'source_lock.json'),
        'all_frozen_files_SHA': len(lock['files']), 'proof_code_sha256': ex.sha(Path(__file__)),
        'check_attempt_code_sha256': ex.sha(RUN / 'controller/accept_context_advisory_first_real.py'),
        'pilot_videos': 24, 'pilot_source_groups': 24, 'native_local_windows': 26,
        'original_new_overview_calls': 24, 'original_new_local_calls': 130,
        'overview_event_counts': dict(Counter(len(t['events']['events']) for t in tables.values())),
        'all_original_requests_raw_output_tokens_native_RGB_processor_validator_equal': True,
        'overview_proofs': overview, 'local_proofs': local,
        'original_label_blind_rows_sha256': ex.sha(out / 'pilot.mechanism_rows.json'),
        'original_report_sha256': ex.sha(out / 'pilot.report.json'),
        'R_N_changed_native_sets': actual_report['R_N_changed_native_sets'],
        'R_X_changed_native_sets': actual_report['R_X_changed_native_sets'],
        'actual_GPU_charge_seconds': resource['charged_seconds'], 'resource_sha256': ex.sha(resource_path),
        'ledger_unique_terminal_match': True, 'ledger_historical_offset': 7200,
        'new_acceptance_model_calls': 0, 'new_acceptance_optimizer_updates': 0,
        'not_semantic_truth_or_official_score': True, 'full104_investment_rule_still_required': True}
    rt.raw_write(receipt, result)
    print(json.dumps({'status': result['status'], 'utc': result['utc'], 'receipt': str(receipt),
        'sha256': ex.sha(receipt), 'pilot_videos': 24, 'overview_attempts': 24, 'local_attempts': 130,
        'GPU_charge_seconds': resource['charged_seconds'], 'new_model_calls': 0}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        path = RUN / 'controller' / ('C_ADVISORY_pilot_acceptance_failure_' + str(time.time_ns()) + '.json')
        rt.raw_write(path, {'traceback': traceback.format_exc(), 'CPU_only_model_calls': 0})
        raise
