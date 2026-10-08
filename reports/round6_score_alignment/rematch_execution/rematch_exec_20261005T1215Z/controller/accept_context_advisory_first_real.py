"""Independent CPU replay of the first real advisory attempts; never generates."""
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import socket
import sys
import traceback

RUN = Path(__file__).resolve().parent.parent
HERE = RUN / 'context_advisory_v1'
sys.path.insert(0, str(HERE))
import runtime as rt
import experiment as ex
import context_contract as cc


def check_attempt(path, request, processor, decoded, text):
    value = ex.checked_done(path, request)
    raw = ex.read(value['raw_receipt'])
    cc.require(raw['actual_model_call'] is True and raw['raw_output'] == value['raw_output'], 'real raw binding')
    cc.require(raw['overview_adapter_disabled'] == (request['kind'] == 'overview'), 'actual adapter branch')
    ids = raw['output_token_ids']
    cc.require(processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False) == raw['raw_output'], 'actual output token decoding')
    cc.require(len(ids) == len(raw['selected_token_scores']) == value['output_tokens'] and all(isinstance(x, (int, float)) and math.isfinite(x) for x in raw['selected_token_scores']), 'finite actual selected scores')
    encoded, identity = rt.encode_decoded(processor, decoded, text)
    cc.require(identity == raw['video_identity'] == value['video_identity'], 'actual CPU native/RGB/processor identity changed')
    cc.require(int(encoded['input_ids'].shape[1]) == raw['input_tokens'] == value['input_tokens'] <= 16384, 'actual input tokens')
    if request['kind'] == 'overview':
        parsed = cc.validate_overview(raw['raw_output'], request['window']['planned_actual_pts_sec'])
        cc.require(parsed == value['events'], 'original overview validator')
    else:
        from contracts import parse_segments
        from native_segment_contract import native_segment_ranges
        parsed, errors, _ = parse_segments(raw['raw_output'], request['window']['window_duration_sec'], allow_empty=request['allow_empty'])
        cc.require(not errors and parsed == value['parsed_segments'], 'original local validator')
        ranges = native_segment_ranges(parsed, identity['window_source_pts_sec'], request['window']['window_pts_start_sec'], request['window']['window_duration_sec'])
        cc.require([list(x) for x in ranges] == value['native_frame_realizability']['ranges'], 'actual native realizability')
        cc.require(ex.video_signature(encoded) == value['vision_tensor_signature'], 'actual encoded vision tensor signature')
    return {'done_path': str(path), 'done_sha256': ex.sha(path), 'raw_sha256': ex.sha(value['raw_receipt']),
        'request_sha256': value['request_sha256'], 'status': value['status'], 'input_tokens': raw['input_tokens'],
        'output_tokens': len(ids), 'generation_seconds': raw['generation_seconds'], 'CPU_native_RGB_processor_output_tokens_validator_equal': True}


def main():
    cc.require(socket.gethostname() == 'inspur-NP5570M5', 'host identity')
    receipt = RUN / 'controller/C_ADVISORY_first_real_acceptance_20261009.json'
    cc.require(not receipt.exists(), 'already independently accepted; never repeat')
    lock = ex.verify()
    student, old, _, _ = rt.bind_helpers()
    from transformers import AutoProcessor
    cfg = ex.read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    plan = ex.read(HERE / 'input_01/nontest_plan.json')
    cc.require(len(plan['jobs']) == len(plan['sources']) == 8, 'NONTEST8 denominator')
    model = ex.read(HERE / 'nontest_01/nontest.model.json')
    cc.require(model['base_hash']['sha256'] == '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59' and model['logical_parameters'] == 8782459120 and model['adapter_saved_tensor_equality'] == 288 and model['new_optimizer_updates'] == 0 and model['adapter_sha256'] == cfg['b_adapter_sha256'], 'actual frozen B model receipt')
    cc.require(ex.sha(Path(cfg['b_adapter']) / 'adapter_model.safetensors') == model['adapter_sha256'], 'current saved adapter SHA')
    key = sorted(plan['sources'])[0]
    job = next(j for j in plan['jobs'] if j['source_key'] == key)
    w = ex.overview_window(plan['sources'][key], key)
    path = HERE / 'nontest_01/overview' / key / 'done.json'
    req = {'kind': 'overview', 'window': w, 'prompt': rt.OVERVIEW_TEXT, 'model': model, 'max_input': 16384, 'max_output': 1280, 'adapter_disabled': True}
    over = check_attempt(path, req, processor, student.decode_window(w), rt.OVERVIEW_TEXT)
    table = ex.read(path)
    donor_key = plan['shuffle_source_mapping'][key]
    donor = ex.read(HERE / 'nontest_01/overview' / donor_key / 'done.json')
    window = job['windows'][0]['window']
    decoded = student.decode_window(window)
    arms = {}
    for arm in ('B1', 'B0', 'N', 'R', 'X'):
        text, audit = ex.arm_text(arm, window, table, donor, ex.base_texts(old))
        req = {'kind': 'local', 'window': window, 'arm': arm, 'prompt': text, 'model': model, 'max_input': 16384, 'max_output': 256, 'allow_empty': arm != 'B1', 'context_audit': audit}
        path = HERE / 'nontest_01/local' / cc.digest(job['video_id']) / '0' / arm / 'done.json'
        arms[arm] = check_attempt(path, req, processor, decoded, text)
    resource_path = RUN / 'controller/aic_CAD_v1_nontest.resource.json'
    resource = ex.read(resource_path)
    ledger_path = Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    rows = [x for x in old.rows(ledger_path) if x.get('name') == 'aic_CAD_v1_nontest']
    cc.require(len(rows) == 1 and rows[0] == resource and resource['status'] == 'completed' and resource['exit_code'] == 0 and resource['stop_reason'] is None and resource['charged_seconds'] > 0, 'unique actual GPU terminal cost')
    result = {'status': 'PASS_INDEPENDENT_FIRST_REAL_C_ADVISORY_CPU_REPLAY', 'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'source_lock_sha256': ex.sha(HERE / 'source_lock.json'), 'all_frozen_files_SHA': len(lock['files']),
        'proof_code_sha256': ex.sha(Path(__file__)), 'first_overview': over, 'first_source_five_local_arms': arms,
        'actual_model_identity': model, 'new_acceptance_model_calls': 0, 'new_acceptance_optimizer_updates': 0,
        'not_semantic_truth_or_official_score': True, 'resource_sha256': ex.sha(resource_path),
        'actual_NONTEST_GPU_charge_seconds': resource['charged_seconds'], 'ledger_unique_terminal_match': True,
        'ledger_historical_offset': 7200}
    rt.raw_write(receipt, result)
    print(json.dumps({'status': result['status'], 'utc': result['utc'], 'receipt': str(receipt), 'sha256': ex.sha(receipt), 'overview_status': over['status'], 'local_statuses': {k:v['status'] for k,v in arms.items()}, 'new_model_calls': 0, 'GPU_charge_seconds': resource['charged_seconds']}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        failure = RUN / 'controller' / ('C_ADVISORY_first_real_acceptance_failure_' + str(__import__('time').time_ns()) + '.json')
        rt.raw_write(failure, {'traceback': traceback.format_exc(), 'CPU_only_model_calls': 0})
        raise
