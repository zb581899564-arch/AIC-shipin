"""First missing whole-source fit views; reuse all accepted inputs and RGB."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import time
import traceback
import zipfile

import torch
from transformers import AutoProcessor

from coarse_call25 import load_case
from frozen_branch46 import RUN
from pilot_input_qa29 import native_case
from pilot_inputs27 import source_pixels, window_meta
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_inputs82'
CACHE = Path('/dev/shm/aic_T_summary_inputs82')


def known_inputs():
    refs = read(ROOT / 'pilot_input_qa29/completion.json')['accepted']
    physical = read(ROOT / 'description_inputs64/all_physical_CPU_completion.json')['views']
    for views in physical.values():
        refs.extend(views.values())
    pixels, exact = {}, {}
    for ref in refs:
        cpu = read(check(ref)); meta = read(check(cpu['input']))
        pixels[meta['case_id']] = dict(input=meta)
        if meta['case_id'].split('_W')[0] == meta['source_name']:
            exact[meta['case_id']] = ref
    return pixels, exact


def capacity(planned, exact):
    remaining = []
    for row in planned:
        source = row['source']; clock = read(check(source['clock']))
        todo = [w for w in row['windows'] if case_name(source, w) not in exact]
        remaining.append((clock, len(todo)))
    # Actual same-processor serialized tensor sizes, with a conservative rounding
    # allowance; raw native dimensions remain per-source, never a free-GiB gate.
    sizes = []
    for ref in exact.values():
        cpu = read(check(ref))
        with zipfile.ZipFile(cpu['encoded']['path']) as archive:
            sizes.append(sum(m.file_size for m in archive.infolist()))
    if not sizes:
        raise ValueError('No actual same-processor input cost reference')
    estimate = sum(n * (64 * c['width'] * c['height'] * 3 + 2 * max(sizes) + 1000000)
                   for c, n in remaining)
    free = shutil.disk_usage(CACHE.parent).free
    if estimate > free:
        raise RuntimeError('Specific first input cache estimate exceeds live tmpfs capacity')
    return dict(first_missing_inputs=sum(n for _, n in remaining),
                estimated_cache_bytes=estimate, actual_tmpfs_free=free,
                observed_same_processor_tensor_max_bytes=max(sizes))


def case_name(source, window):
    return source['sid'] + '_W' + str(window['index']).zfill(3)


def prepare_source(row, prior_pixels, exact, rt, processor, journal, deadline):
    from time_control50_prepare import encode_case, source_windows
    source = row['source']; check(source['media'])
    clock, points, windows = source_windows(source)
    if windows != row['windows']:
        raise ValueError('Original native source plan changed')
    todo = [w for w in windows if case_name(source, w) not in exact]
    if not todo:
        return [exact[case_name(source, w)] for w in windows], []
    pictures = source_pixels(source, clock, points, todo, prior_pixels)
    uses = Counter(i for w in todo for i in w['source_frame_ordinals'])
    result, first = [], []
    for window in windows:
        name = case_name(source, window)
        if name in exact:
            result.append(exact[name]); continue
        if time.monotonic() > deadline:
            raise TimeoutError('First input budget expired; retain successful journal')
        folder = CACHE / name; folder.mkdir()
        started = time.monotonic()
        meta = window_meta(source, clock, points, window, pictures, folder)
        ref = encode_case(rt, processor, meta, folder)
        journal.write(json.dumps(dict(case=name, CPU=ref)) + '\n'); journal.flush()
        # First independent native/RGB/tensor/prompt QA, no new processor call.
        _, independent_meta = native_case(ref, {name: (source, window)})
        _, _, values, _ = load_case(ref, rt, processor.tokenizer)
        grid = values['video_grid_thw']
        if tuple(grid.shape) != (1, 3) or int(grid[0, 0]) * 2 != 64 or independent_meta != meta:
            raise ValueError('First independent input/native grid differs')
        del values
        proof = OUT / 'first_independent_CPU' / (name + '.json')
        save(proof, dict(state='PASS_FIRST_NEW_SOURCE_NATIVE64_INPUT_AND_TOKEN_QA',
            actual_CPU=ref, source_media=source['media'], source_clock=source['clock'],
            no_labels_in_input=True, no_old_processor_or_independent_QA_repeated=True))
        first.append(identity(proof)); result.append(ref)
        print('SUMMARY82_FIRST_INPUT_AND_QA', name, time.monotonic() - started, flush=True)
        for ordinal in window['source_frame_ordinals']:
            uses[ordinal] -= 1
            if not uses[ordinal]:
                del pictures[ordinal]
    return result, first


def main():
    OUT.mkdir(); started = time.monotonic(); torch.set_num_threads(2)
    inventory = read(ROOT / 'summary_content81/completion.json')
    if inventory['source_count'] != 9 or inventory['whole_source_windows'] != 217:
        raise ValueError('Actual nine-fit whole-source inventory differs')
    prior, exact = known_inputs(); costs = capacity(inventory['planned'], exact)
    live = subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True)
    save(OUT / 'registration.json', dict(inventory=identity(ROOT / 'summary_content81/completion.json'),
        old_independent_QA=identity(ROOT / 'pilot_input_qa29/completion.json'),
        old_description_views=identity(ROOT / 'description_inputs64/all_physical_CPU_completion.json'),
        actual_capacity=costs, cache_root=str(CACHE), CPU_budget_seconds=2400,
        scientific_scope='Preparation for selected-content supervision feasibility; no GPU admission',
        no_human_target_in_vision_or_audio_inputs=True, no_fresh_confirmation_read=True,
        live_CPU=live.splitlines()[:12], RAM=subprocess.check_output(['free', '-b'], text=True),
        permanent_inputs_and_raw_not_retired=True, model_or_training_admitted=False))
    CACHE.mkdir(); (OUT / 'first_independent_CPU').mkdir()
    rt = runtime(); config = read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
        min_pixels=131072, max_pixels=131072)
    all_inputs, first = {}, []
    with (OUT / 'accepted.jsonl').open('x') as journal:
        for row in inventory['planned']:
            refs, qa = prepare_source(row, prior, exact, rt, processor, journal, started + 2400)
            all_inputs[row['source']['sid']] = refs; first.extend(qa)
    count = sum(map(len, all_inputs.values()))
    if count != 217 or len(first) != costs['first_missing_inputs'] or torch.cuda.is_initialized():
        raise ValueError('Complete input/first QA denominator or CPU role differs')
    save(OUT / 'completion.json', dict(state='FIRST_ALL217_FIT_NATIVE64_INPUTS_AND_QA_PASS',
        accepted=all_inputs, first_independent_CPU=first, first_new_inputs=len(first),
        adopted_successful_inputs=count - len(first), original_source_count=9,
        CPU_seconds=time.monotonic() - started, no_old_model_decode_processor_or_QA_repeated=True,
        new_GPU_calls=0, new_training=0, training_admitted=False,
        remaining='Exact AV prefixes and summary task/context/budget registration before new inference'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
