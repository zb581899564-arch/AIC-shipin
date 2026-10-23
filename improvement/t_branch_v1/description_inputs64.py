"""First CPU-only evidence-bound caption views; no optimization or inference."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import shutil
import subprocess
import time
import traceback

import torch
from transformers import AutoProcessor

from frozen_branch46 import RUN
from description_pixels64 import prepare_views
from description_tokens64 import prepare_pair, QUESTION
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'description_inputs64'
CACHE = Path('/dev/shm/aic_T_human_description64')


def main():
    OUT.mkdir(); started = time.monotonic()
    inventory = read(ROOT / 'description_inventory63/completion.json')
    if inventory['state'] != 'HUMAN_DESCRIPTION_INPUT_INVENTORY_PASS':
        raise ValueError('Actual diverse human-description input scope insufficient')
    selected = read(check(inventory['selected_examples']))
    examples = selected['fit'] + selected['development']
    if len(examples) != 24 or any(row['source']['role'] == 'confirmation' for row in examples):
        raise ValueError('Frozen24 description targets differ or include fresh confirmation')
    estimate = 0
    for row in examples:
        clock = read(check(row['source']['clock']))
        estimate += 2 * (int(clock['width']) * int(clock['height']) * 3 * 64 + 120000000)
    if shutil.disk_usage('/dev/shm').free < estimate or shutil.disk_usage(ROOT).free < 10000000:
        raise RuntimeError('Current capacity cannot hold estimated new input artifacts')
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Protected CONTROL5 identity/state differs')
    save(OUT / 'registration.json', dict(actual_inventory=identity(ROOT / 'description_inventory63/completion.json'),
        exact_selected_labels=inventory['selected_examples'], pairs=24, first_views=48,
        generic_caption_question=QUESTION, human_targets_used_only_as_external_supervised_labels=True,
        annotation_text_and_endpoints_unchanged=True, fixed_max_target_tokens=512, no_target_truncation=True,
        no_repeated_original97_processor_or_model_work=True, new_model_calls=0,
        new_training=0, no_GPU_admission=True, cache_root=str(CACHE), estimated_input_bytes=estimate,
        code={name: identity(Path(__file__).parent / name) for name in ['description_inputs64.py',
            'description_pixels64.py', 'description_tokens64.py', 'description_inventory63.py']},
        RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True),
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:16]))
    CACHE.mkdir(); rt = runtime()
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
        min_pixels=131072, max_pixels=131072)
    views = CACHE / 'native'; views.mkdir()
    physical = prepare_views(examples, views, rt, processor)
    save(OUT / 'all_physical_CPU_completion.json', dict(state='FIRST48_ORIGINAL_NATIVE64_HUMAN_CLIP_VIEWS_PASS',
        views=physical, no_new_video_clock_or_old_processor_repeated=True))
    pairs = CACHE / 'caption_pairs'; pairs.mkdir()
    accepted = [prepare_pair(row, physical[row['example_id']], pairs / row['example_id'], processor.tokenizer, rt)
                for row in examples]
    if torch.cuda.is_initialized():
        raise ValueError('Caption CPU preparation initialized CUDA')
    save(OUT / 'completion.json', dict(state='ALL24_REAL_HUMAN_CONTENT_PAIRS_CPU_PASS_NO_MODEL_QUALITY',
        accepted=accepted, first_physical_views=48, fit_pairs=16, dev_pairs=8,
        actual_fit_recordings=inventory['fit_recordings'], actual_fit_publishers=inventory['fit_publishers'],
        CPU_wall_seconds=time.monotonic() - started, new_model_calls=0, training=0,
        targets_original_human_text_not_JSON_timestamps=True, no_fresh_confirmation_read=True,
        next='Separately freeze matched/misaligned BASE conditional human-text likelihood probe and budget before first GPU; no optimization yet'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
