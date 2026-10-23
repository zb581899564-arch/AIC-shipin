"""Prepare only remaining windows of the fixed97-window cohort in source order."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
import shutil
import zipfile

import av
import numpy as np

from prompt_contract13 import prompt_binding
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'pilot_inputs27'
CACHE = Path('/dev/shm/aic_T_policy27_remaining_inputs')
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime


def adopted_map():
    profiles = read(ROOT / 'pilot_remaining24/completion.json')['accepted']
    result = {}
    for ref in profiles:
        row = read(check(ref))
        cpu = read(check(row['original_CPU']))
        meta = read(check(cpu['input']))
        result[meta['case_id']] = dict(profile=ref, CPU=row['original_CPU'], input=meta)
    if len(result) != 4:
        raise ValueError('Four successful original cost inputs must be adopted')
    return result


def source_pixels(source, clock, points, windows, adopted):
    wanted = {index for window in windows for index in window['source_frame_ordinals']}
    pictures = {}
    # Reuse any exact original RGB already materialized in the four accepted profiles.
    for row in adopted.values():
        meta = row['input']
        if meta['source_sha256'] != source['media']['sha256']:
            continue
        if not wanted.intersection(meta['source_frame_ordinals']):
            continue
        with np.load(meta['frame_array_path'], allow_pickle=False) as archive:
            values = archive['rgb']
            for ordinal, image, digest in zip(meta['source_frame_ordinals'], values, meta['pixel_sha256']):
                if hashlib.sha256(image.tobytes()).hexdigest() != digest:
                    raise ValueError('Adopted original RGB differs')
                if ordinal in wanted:
                    pictures[ordinal] = image.copy()
    remaining = wanted - set(pictures)
    origin = Fraction(clock['first_PTS_exact'])
    with av.open(source['media']['path']) as container:
        stream = container.streams.video[0]
        stream.codec_context.thread_count = 1
        for ordinal, frame in enumerate(container.decode(stream)):
            if not remaining:
                break
            if ordinal >= len(points) or frame.pts is None or Fraction(frame.pts) * frame.time_base != points[ordinal] + origin:
                raise ValueError('Sequential native order no longer equals accepted source clock')
            if ordinal in remaining:
                pictures[ordinal] = frame.to_ndarray(format='rgb24')
                remaining.remove(ordinal)
    if remaining:
        raise ValueError('Remaining original ordinal union not fully decoded; no nearest-frame repair')
    return pictures


def window_meta(source, clock, points, window, pictures, folder):
    ordinals = window['source_frame_ordinals']
    arrays = np.stack([pictures[index] for index in ordinals])
    path = folder / 'frames.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, rgb=arrays)
    rate = Fraction(clock['rate_diagnostic_only'])
    meta = dict(case_id=folder.name, source_name=source['sid'], source_path=source['media']['path'],
        source_sha256=source['media']['sha256'], source_bytes=source['media']['bytes'],
        source_total_frames=clock['native_frames'], width=clock['width'], height=clock['height'],
        fps_num=rate.numerator, fps_den=rate.denominator, all_source_exact_pts=list(map(str, points)),
        original_clock_origin_exact=clock['first_PTS_exact'], window_start=window['start_exact'],
        window_end=window['end_exact'], source_frame_ordinals=ordinals, sample_exact_pts=window['sample_exact_pts'],
        pixel_sha256=[hashlib.sha256(image.tobytes()).hexdigest() for image in arrays],
        frame_array_path=str(path), frame_array_sha256=identity(path)['sha256'],
        reference_available_to_inference=False, audio_observed=False)
    save(folder / 'input.json', meta)
    return meta


def prepare_source(rt, processor, row, adopted, journal):
    from time_control50_prepare import source_windows, encode_case
    source = row['source']
    check(source['media'])
    clock, points, windows = source_windows(source)
    if windows != row['windows']:
        raise ValueError('Frozen complete-source window plan changed')
    todo = [window for window in windows if source['sid'] + '_W' + str(window['index']).zfill(3) not in adopted]
    pictures = source_pixels(source, clock, points, todo, adopted)
    uses = Counter(index for window in todo for index in window['source_frame_ordinals'])
    accepted = []
    for window in windows:
        case = source['sid'] + '_W' + str(window['index']).zfill(3)
        if case in adopted:
            accepted.append(adopted[case]['CPU'])
            continue
        folder = CACHE / case
        folder.mkdir()
        start = time.monotonic()
        meta = window_meta(source, clock, points, window, pictures, folder)
        cpu_ref = encode_case(rt, processor, meta, folder)
        cpu = read(check(cpu_ref))
        with np.load(check(cpu['encoded']), allow_pickle=False) as archive:
            binding = prompt_binding(processor.tokenizer, archive['input_ids'], cpu['detail'], rt.EMPTY_PROMPT, 'COARSE')
        save(folder / 'explicit_prompt_acceptance.json', binding)
        journal.write(json.dumps(dict(case=case, CPU=cpu_ref, seconds=time.monotonic() - start)) + '\n')
        journal.flush()
        accepted.append(cpu_ref)
        print('WHOLE_SOURCE_INPUT27_ACCEPTED', case, len(accepted), len(windows), flush=True)
        for index in window['source_frame_ordinals']:
            uses[index] -= 1
            if not uses[index]:
                del pictures[index]
    return accepted


def capacity_plan(planned, adopted):
    estimate, peak_source_RGB = 0, 0
    for row in planned['planned']:
        source = row['source']
        clock = read(check(source['clock']))
        count = len(row['windows']) - 1
        profile = next(value for value in adopted.values() if value['input']['source_sha256'] == source['media']['sha256'])
        cpu = read(check(profile['CPU']))
        with zipfile.ZipFile(cpu['encoded']['path']) as archive:
            encoded_bytes = sum(member.file_size for member in archive.infolist())
        raw_bytes = 64 * clock['width'] * clock['height'] * 3
        metadata_allowance = Path(source['clock']['path']).stat().st_size * 4 + Path(cpu['input']['path']).stat().st_size + Path(profile['CPU']['path']).stat().st_size
        estimate += count * (raw_bytes + encoded_bytes + metadata_allowance)
        peak_source_RGB = max(peak_source_RGB, count * raw_bytes)
    free = shutil.disk_usage('/dev/shm').free
    if estimate > free:
        raise RuntimeError('Specific remaining raw/tensor artifact estimate exceeds current tmpfs capacity')
    return dict(remaining_uncompressed_artifact_estimate=estimate,
                actual_tmpfs_free=free, largest_one_source_raw_pool_upper=peak_source_RGB,
                no_fixed_free_GiB_threshold=True)


def main():
    OUT.mkdir()
    planned = read(ROOT / 'pilot_profile21/registration.json')
    adopted = adopted_map()
    capacity = capacity_plan(planned, adopted)
    CACHE.mkdir()
    save(OUT / 'registration.json', dict(frozen_cohort=identity(ROOT / 'pilot_profile21/registration.json'),
        first_cost_terminal=identity(ROOT / 'pilot_remaining24/completion.json'),
        adopted_successful_inputs=4, first_remaining_inputs=planned['full_source_windows'] - 4,
        measured_first4_cache_bytes=243227263, cache_root=str(CACHE),
        actual_capacity_plan=capacity,
        source_union_decoded_once_for_remaining_RGB=True, successful_profiles_not_reencoded=True,
        no_labels_in_input=True, no_model_or_training_admission=True))
    rt = legacy_runtime()
    from transformers import AutoProcessor
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    accepted = []
    with (OUT / 'accepted.jsonl').open('x') as journal:
        for row in planned['planned']:
            accepted.extend(prepare_source(rt, processor, row, adopted, journal))
    if len(accepted) != planned['full_source_windows']:
        raise ValueError('Actual complete-source input count differs')
    save(OUT / 'completion.json', dict(state='COMPLETE_FIXED97_SOURCE_INPUTS_PREPARED', accepted=accepted,
        new_inputs=len(accepted) - 4, adopted_inputs=4, new_model_calls=0,
        training_admission=False, remaining='Independent full input QA and frozen scientific policy protocol'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                accepted_journal_is_explicit_remaining_recovery_basis=True))
        raise
