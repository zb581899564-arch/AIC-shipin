"""First independent full-cohort RGB/native/prompt/tensor acceptance before97 controls."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import hashlib
import sys
import traceback

import numpy as np

from coarse_call25 import load_case
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'pilot_input_qa29'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime


def native_case(ref, lookup):
    cpu = read(check(ref))
    meta = read(check(cpu['input']))
    source, window = lookup[meta['case_id']]
    if (meta['source_sha256'] != source['media']['sha256'] or
            meta['source_frame_ordinals'] != window['source_frame_ordinals'] or
            meta['sample_exact_pts'] != window['sample_exact_pts'] or
            meta['window_start'] != window['start_exact'] or meta['window_end'] != window['end_exact'] or
            meta['reference_available_to_inference'] or meta['audio_observed']):
        raise ValueError('Independent full source/native window identity differs')
    rgb = identity(meta['frame_array_path'])
    if rgb['sha256'] != meta['frame_array_sha256']:
        raise ValueError('First independent serialized RGB identity differs')
    with np.load(rgb['path'], allow_pickle=False) as archive:
        arrays = archive['rgb']
        if arrays.shape != (64, meta['height'], meta['width'], 3) or arrays.dtype != np.uint8:
            raise ValueError('Actual native64 RGB shape or dtype differs')
        if [hashlib.sha256(image.tobytes()).hexdigest() for image in arrays] != meta['pixel_sha256']:
            raise ValueError('Independent original64 pixel hashes differ')
    detail = cpu['detail']
    if (detail['pixel_sha256'] != meta['pixel_sha256'] or
            detail['sample_exact_pts'] != meta['sample_exact_pts'] or detail['physical_frames'] != 64 or
            detail['source_frame_ordinals'] != meta['source_frame_ordinals']):
        raise ValueError('Actual processor evidence does not bind accepted native pictures')
    return cpu, meta


def main():
    OUT.mkdir()
    terminal = read(ROOT / 'pilot_inputs27/completion.json')
    if len(terminal['accepted']) != 97:
        raise ValueError('Complete fixed97 inputs required')
    plan = read(ROOT / 'pilot_profile21/registration.json')
    lookup = {row['source']['sid'] + '_W' + str(window['index']).zfill(3): (row['source'], window)
              for row in plan['planned'] for window in row['windows']}
    old_qa = read(ROOT / 'pilot_cost25/independent_CPU_audit.json')
    if old_qa['state'] != 'PASS' or len(old_qa['cases']) != 4:
        raise ValueError('Actual independent first4 tensor/token checks missing')
    adopted = {row['case'] for row in old_qa['cases']}
    save(OUT / 'registration.json', dict(inputs=identity(ROOT / 'pilot_inputs27/completion.json'),
        first4_actual_tensor_replay_adopted=identity(ROOT / 'pilot_cost25/independent_CPU_audit.json'),
        original_cohort=identity(ROOT / 'pilot_profile21/registration.json'),
        first_native_RGB_replay_for97=True, first_tensor_prompt_replay_for93=True,
        source_labels_not_read=True, no_model_or_processor_replay=True))
    rt = legacy_runtime()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    accepted = []
    for ref in terminal['accepted']:
        cpu, meta = native_case(ref, lookup)
        if meta['case_id'] not in adopted:
            _, _, values, _ = load_case(ref, rt, tokenizer)
            grid = values['video_grid_thw']
            if tuple(grid.shape) != (1, 3) or int(grid[0, 0]) * 2 != 64:
                raise ValueError('Actual native video temporal grid differs')
        accepted.append(ref)
        print('INDEPENDENT_INPUT29', len(accepted), 97, meta['case_id'], flush=True)
    save(OUT / 'completion.json', dict(state='PASS_ALL97_FIRST_INDEPENDENT_INPUT_QA', accepted=accepted,
        first_native_RGB_cases=97, first_tensor_prompt_cases=93, adopted_tensor_cases=4,
        source_labels_read=False, no_decode_processor_model_or_success_repeated=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_every_success=True))
        raise
