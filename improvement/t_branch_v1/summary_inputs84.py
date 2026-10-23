"""Explicit first-input recovery after82 capacity-only failure; same scientific inputs."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import subprocess
import time
import traceback

import torch
from transformers import AutoProcessor

from frozen_branch46 import RUN
from summary_capacity84 import check_actual_geometry, remaining_capacity
from summary_inputs82 import CACHE, OUT as ORIGINAL, known_inputs, prepare_source
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_inputs84'


def main():
    OUT.mkdir(); started = time.monotonic(); torch.set_num_threads(2)
    if (ORIGINAL / 'completion.json').exists() or CACHE.exists() or (ORIGINAL / 'accepted.jsonl').exists():
        raise ValueError('Recovery84 requires actual82 pre-input failure, not ambiguous successful preparation')
    failure = read(ORIGINAL / 'failure.json')
    if 'Specific first input cache estimate exceeds' not in failure['traceback']:
        raise ValueError('Recovery84 does not cover a different failed phase')
    inventory = read(ROOT / 'summary_content81/completion.json')
    prior, exact = known_inputs(); costs = remaining_capacity(inventory['planned'], exact)
    save(OUT / 'registration.json', dict(original_failure=identity(ORIGINAL / 'failure.json'),
        original82_attempt_preserved=True, new_version='capacity geometry correction; scientific inputs unchanged',
        same_native_planner_and_processor=True, capacity=costs, CPU_budget_seconds=2400,
        reused_immutable82_functions=identity(Path(__file__).with_name('summary_inputs82.py')),
        original_source_inventory=identity(ROOT / 'summary_content81/completion.json'),
        cache_root=str(CACHE), first_CPU_proofs=str(ORIGINAL / 'first_independent_CPU'),
        new_RGB_retained=True, old_SUCCESS_never_repeated=True, no_GPU_or_training_admission=True,
        live_CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12]))
    CACHE.mkdir(); (ORIGINAL / 'first_independent_CPU').mkdir()
    rt = runtime(); config = read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
        min_pixels=131072, max_pixels=131072)
    geometry = {row['source']: row['same_geometry_reference'] for row in costs['per_source']}
    accepted, proofs = {}, []
    with (OUT / 'accepted.jsonl').open('x') as journal:
        for row in inventory['planned']:
            sid = row['source']['sid']
            refs, qa = prepare_source(row, prior, exact, rt, processor, journal, started + 2400)
            for ref in refs:
                if ref not in exact.values():
                    check_actual_geometry(ref, geometry[sid])
            accepted[sid] = refs; proofs.extend(qa)
    count = sum(map(len, accepted.values()))
    if count != 217 or len(proofs) != costs['first_missing_inputs'] or torch.cuda.is_initialized():
        raise ValueError('Actual217 input/first QA scope or CPU execution differs')
    save(OUT / 'completion.json', dict(state='FIRST_ALL217_FIT_NATIVE64_INPUTS_AND_QA_PASS',
        accepted=accepted, first_independent_CPU=proofs, first_new_inputs=len(proofs),
        adopted_successful_inputs=count - len(proofs), original_source_count=9,
        CPU_seconds=time.monotonic() - started, capacity=identity(OUT / 'registration.json'),
        original82_failure_preserved=True, no_old_model_decode_processor_or_QA_repeated=True,
        new_GPU_calls=0, new_training=0, training_admitted=False,
        remaining='Exact AV prefixes and semantic-summary protocol/budget before new GPU'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
