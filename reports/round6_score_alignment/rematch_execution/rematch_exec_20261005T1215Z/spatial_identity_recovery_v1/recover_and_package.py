"""Restore only eight pre-model decode failures; all successful rows retained."""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
HERE = RUN/'spatial_identity_recovery_v1'
CODE = RUN/'baseline_a_pts_v1'
ORIGINAL = CODE/'rematch_e2e_recovery_01'
OUTPUT = HERE/'recover_01'
ORIGINAL_SHA = 'aa1b94a132886acea73d0951b84928a4b073d365f8b56b226ddc2c22cc910339'
REQUESTS_SHA = '1102ba4adbbe1c53acf481bca67bf23d3c6628251c5bb9e8008427b8d4254102'
MANIFEST = RUN/'baseline_pts_v4/scan_01/clean_manifest_v2.json'
MANIFEST_SHA = 'ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8'
CLOCKS = RUN/'baseline_pts_v4/scan_01/clock_registry.json'
CLOCKS_SHA = '1058aba02e5e959bc8e4842cbde0eadced192a8201d5c833ae50a7c0aac07909'
CONFIG = CODE/'config_a.json'
sys.path.insert(0, str(CODE))
from sequential_frames import SequentialReader
from pts_contract import BRANCH_CFR, load_clocks, validate_frame_request
from infer_anchors_pts import BASELINE, MODEL, PINNED_BASELINE, PINNED_MODEL
import run_pts


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2)+'\n')

def source_inputs():
    require(sha(ORIGINAL/'anchor_output.jsonl') == ORIGINAL_SHA, 'original spatial evidence changed')
    require(sha(ORIGINAL/'anchor_requests.jsonl') == REQUESTS_SHA, 'original requests changed')
    require(sha(MANIFEST) == MANIFEST_SHA and sha(CLOCKS) == CLOCKS_SHA, 'manifest/clock bytes changed')
    run_pts.verify_vendor()
    original = rows(ORIGINAL/'anchor_output.jsonl')
    requests = rows(ORIGINAL/'anchor_requests.jsonl')
    key = lambda r: (r['video_id'], r['source_frame'])
    require(len(original) == len(requests) == 13022 and len({key(r) for r in original}) == 13022,
            'original row count/key identity mismatch')
    require({key(r) for r in original} == {key(r) for r in requests}, 'spatial request/output key mismatch')
    failed = {key(r): r for r in original if r['status'] != 'MODEL_OK'}
    require(len(failed) == 8 and {k[0] for k in failed} == {'162'}, 'not the registered eight identity failures')
    require(all(r['status'] == 'DECODE_OR_MODEL_FAILURE' and
                r['parse_error'] == 'RuntimeError: decoded frame identity changed' and
                r['raw_output'] == '' and r['box_xyw'] is None and r['used_fallback'] is False
                for r in failed.values()), 'failure scope differs; no output repair allowed')
    manifest = read(MANIFEST)
    clocks = load_clocks(manifest, CLOCKS, CLOCKS_SHA)
    metadata = {r['video_id']: r for r in manifest['records']}
    require(len(metadata) == len(manifest['records']) == 426, 'full manifest count/key mismatch')
    subset = sorted([r for r in requests if key(r) in failed], key=lambda r: r['source_frame'])
    for request in subset:
        source = validate_frame_request(request, metadata)
        require(clocks[request['video_id']]['branch'] == BRANCH_CFR, 'recovery is CFR identity only')
        require(sha(request['source_path']) == source['source_sha256'], 'source bytes changed')
        require(request['anchor_request_sha256'] == failed[key(request)]['anchor_request_sha256'], 'failed request binding changed')
    return original, requests, subset, manifest, clocks

def restore_pixels(subset):
    require(len({r['source_path'] for r in subset}) == 1, 'registered source count changed')
    reader = SequentialReader(subset[0]['source_path'])
    frames = {}
    try:
        for r in subset:
            frames[(r['video_id'], r['source_frame'])] = reader.read(
                r['source_frame'], r['expected_pixel_sha256'], r['source_width'], r['source_height'])
    finally:
        reader.close()
    return frames

def synthetic_decoder_test():
    import cv2
    import numpy as np
    directory = HERE/'cpu_decoder_fixture_01'
    directory.mkdir(exist_ok=False)
    media = directory/'ordinals.avi'
    writer = cv2.VideoWriter(str(media), cv2.VideoWriter_fourcc(*'FFV1'), 25, (64, 48))
    require(writer.isOpened(), 'lossless CPU fixture codec unavailable')
    expected = []
    try:
        for ordinal in range(17):
            frame = np.full((48, 64, 3), ordinal*13, dtype=np.uint8)
            frame[0, 0] = [ordinal, 255-ordinal, 2*ordinal]
            expected.append(hashlib.sha256(memoryview(frame).cast('B')).hexdigest())
            writer.write(frame)
    finally:
        writer.release()
    reader = SequentialReader(media)
    try:
        for ordinal in [0, 3, 8, 16]:
            reader.read(ordinal, expected[ordinal], 64, 48)
        reader.read(16, expected[16], 64, 48)
        try:
            reader.read(3, expected[3], 64, 48)
        except ValueError:
            pass
        else:
            raise RuntimeError('backward ordinal did not fail')
        try:
            reader.read(16, '0'*64, 64, 48)
        except RuntimeError:
            pass
        else:
            raise RuntimeError('wrong expected pixels did not fail')
    finally:
        reader.close()
    return {'lossless_ordinal_checks': 5, 'backward_rejected': True, 'wrong_pixel_hash_rejected': True}

def prepare():
    started = time.monotonic()
    original, requests, subset, manifest, clocks = source_inputs()
    frames = restore_pixels(subset)
    synthetic = synthetic_decoder_test()
    report = dict(status='PASS_CPU_EXACT_REGISTERED_PIXEL_IDENTITY', failed_requests=8,
                  restored_pixel_identities=len(frames), original_successes=13014,
                  original_spatial_sha256=ORIGINAL_SHA, requests_sha256=REQUESTS_SHA,
                  synthetic_decoder=synthetic, media_or_raw_model_text_displayed=False,
                  GPU_used=False, wall_seconds=time.monotonic()-started)
    write(HERE/'cpu_identity_01.json', report)
    print(json.dumps(report), flush=True)

def execute(admission_path):
    started = time.monotonic()
    original, requests, subset, manifest, clocks = source_inputs()
    admission = run_pts.verify_admission(admission_path, MANIFEST_SHA, manifest['kind'], OUTPUT, CLOCKS_SHA, 'spatial')
    lock = read(HERE/'source_lock.json')
    require(sha(HERE/'source_lock.json') == admission['identity_recovery_source_lock_sha256'], 'recovery source lock changed')
    for name, digest in lock['files'].items():
        require(sha(HERE/name) == digest, 'recovery source/test changed: '+name)
    require(read(HERE/'cpu_identity_01.json')['status'] == 'PASS_CPU_EXACT_REGISTERED_PIXEL_IDENTITY', 'CPU recovery identity not accepted')
    require(sha(BASELINE) == PINNED_BASELINE, 'original baseline code changed')
    require({name: sha(MODEL/name) for name in PINNED_MODEL} == PINNED_MODEL, 'original model bytes changed')
    OUTPUT.mkdir(exist_ok=False)
    report = dict(status='RUNNING_SPATIAL_IDENTITY_RECOVERY_ONLY', original_spatial_sha256=ORIGINAL_SHA,
                  original_successes=13014, recovery_requests=8, uploaded=False)
    try:
        frames = restore_pixels(subset)
        import cv2
        from PIL import Image
        spec = importlib.util.spec_from_file_location('identity_frozen_baseline', BASELINE)
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        model = baseline.Qwen3VL(str(MODEL))
        replacements = {}
        for request in subset:
            key = (request['video_id'], request['source_frame'])
            frame = frames[key]
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            tw, th = request['target_ratio_wh']
            one = time.monotonic()
            raw = model.predict_focus(image, (tw, th), max_new_tokens=baseline.DEFAULT_CROP_TOKENS)
            center = baseline.parse_focus_norm(raw, image.width, image.height)
            require(center is not None, 'recovery model output parse failure; no retry/fallback')
            crop_w, crop_h = baseline.compute_crop_size(image.width, image.height, tw, th)
            box = baseline.center_to_box(center[0], center[1], image.width, image.height, crop_w, crop_h)
            require(baseline.validate_box(box, image.width, image.height, tw, th), 'recovery box invalid')
            replacements[key] = dict(video_id=key[0], source_frame=key[1],
                anchor_request_sha256=request['anchor_request_sha256'], spatial_source='QWEN_ANCHOR_SAME_FRAME',
                used_fallback=False, box_xyw=[int(v) for v in box], raw_output=raw, parse_error=None,
                status='MODEL_OK', decoded_pixel_sha256=request['expected_pixel_sha256'],
                decoder_identity='SEQUENTIAL_FROM_SOURCE_ORDINAL_ZERO_EXACT_REGISTERED_PIXELS',
                seconds=round(time.monotonic()-one, 6), peak_memory_mib=round(float(model.peak_memory_mib()), 2))
        require(len(replacements) == 8, 'recovery count incomplete')
        import gc
        import torch
        del model
        gc.collect()
        torch.cuda.empty_cache()
        unchanged = 0
        with (ORIGINAL/'anchor_output.jsonl').open('rb') as source, (OUTPUT/'anchor_output.jsonl').open('xb') as target:
            for line in source:
                old = json.loads(line)
                key = (old['video_id'], old['source_frame'])
                if key in replacements:
                    target.write((json.dumps(replacements[key], sort_keys=True)+'\n').encode())
                else:
                    require(old['status'] == 'MODEL_OK', 'unregistered failed row encountered')
                    target.write(line)
                    unchanged += 1
        merged = rows(OUTPUT/'anchor_output.jsonl')
        require(len(merged) == 13022 and unchanged == 13014 and all(r['status'] == 'MODEL_OK' for r in merged), 'complete merged spatial gate failed')
        old_lines = {(json.loads(line)['video_id'], json.loads(line)['source_frame']): line
                     for line in (ORIGINAL/'anchor_output.jsonl').read_bytes().splitlines(keepends=True)}
        new_lines = {(json.loads(line)['video_id'], json.loads(line)['source_frame']): line
                     for line in (OUTPUT/'anchor_output.jsonl').read_bytes().splitlines(keepends=True)}
        require(all(new_lines[k] == v for k, v in old_lines.items() if k not in replacements), 'successful spatial bytes changed')
        reused = {}
        require(len(rows(ORIGINAL/'selected.jsonl')) == 93155, 'original selection count changed')
        for name in ['temporal.jsonl', 'selected.jsonl', 'shots.jsonl', 'anchor_requests.jsonl', 'metadata.json']:
            shutil.copyfile(ORIGINAL/name, OUTPUT/name)
            require(sha(OUTPUT/name) == sha(ORIGINAL/name), 'reused artifact changed: '+name)
            reused[name] = sha(OUTPUT/name)
        write(OUTPUT/'spatial.stage.json', dict(status='PASS_SPATIAL_IDENTITY_RECOVERY', rows=13022, invalid=0,
              unchanged_successful_rows=13014, recovered_decode_failures=8, output_sha256=sha(OUTPUT/'anchor_output.jsonl')))
        for stage in ['compose', 'package']:
            subprocess.run([sys.executable, '-B', str(CODE/'run_pts.py'), '--stage', stage,
                '--manifest', str(MANIFEST), '--expected-manifest-sha256', MANIFEST_SHA,
                '--clock-registry', str(CLOCKS), '--expected-clock-registry-sha256', CLOCKS_SHA,
                '--run-dir', str(OUTPUT), '--config', str(CONFIG), '--admission', str(admission_path)], check=True)
        package = read(OUTPUT/'package.stage.json')
        candidate = OUTPUT/'candidate_A_PTS.zip'
        with zipfile.ZipFile(candidate) as archive:
            require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None, 'strict ZIP entry/CRC gate failed')
            require(hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == sha(OUTPUT/'predictions.jsonl'), 'ZIP prediction bytes differ')
        require(sha(ORIGINAL/'anchor_output.jsonl') == ORIGINAL_SHA, 'original failed evidence modified')
        source_inputs()
        report.update(status='PASS_COMPLETE_426_CANDIDATE_NOT_UPLOADED', videos=426,
            frames=93155, anchors=13022, restored_pixel_identities=8, unchanged_successful_spatial_rows=13014,
            unchanged_successful_spatial_lines_byte_identical=True, reused_artifacts=reused,
            candidate=str(candidate), candidate_sha256=sha(candidate), candidate_bytes=candidate.stat().st_size,
            package_stage=package, original_failed_run_preserved=True, silent_fallbacks=0,
            peak_memory_mib=round(float(torch.cuda.max_memory_allocated())/2**20, 2))
    except Exception as exc:
        report.update(status='STOP_SPATIAL_IDENTITY_RECOVERY', failure_type=type(exc).__name__,
                      failure=str(exc), traceback=traceback.format_exc())
    report['wall_seconds'] = time.monotonic()-started
    write(OUTPUT/'recovery_completion.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'traceback'}), flush=True)
    return 0 if report['status'].startswith('PASS_') else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--admission', type=Path)
    args = parser.parse_args()
    if args.prepare_only:
        prepare()
    else:
        require(args.admission is not None, 'registered GPU admission required')
        raise SystemExit(execute(args.admission))
