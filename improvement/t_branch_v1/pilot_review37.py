"""CPU-only first review of97 successful outputs; repair proven import-order failure."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pathlib import Path
import sys
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'pilot_review37'
SOURCE = ROOT / 'pilot_control30'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime


def main():
    OUT.mkdir()
    log = (SOURCE / 'review.log').read_text()
    if "ModuleNotFoundError: No module named 'constrained_json'" not in log:
        raise ValueError('Expected actual first-import failure absent')
    if (SOURCE / 'independent_CPU_audit.json').exists():
        raise ValueError('Completed review must be adopted, not repeated')
    gpu = read(SOURCE / 'gpu_completion.json')
    if len(gpu['outputs']) != 97 or gpu['first_remaining_calls'] != 93 or gpu['adopted_calls'] != 4:
        raise ValueError('Successful fixed97 model output denominator differs')
    job = 'T_original_TIME_whole97_remaining93_20261022_v30'
    resource = read(RUN / 'controller' / (job + '.resource.json'))
    import json
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == job] != [resource]:
        raise ValueError('Actual unique natural model completion differs')
    check(read(SOURCE / 'source_input_lock.json')['code']['pilot_review30.py'])
    save(OUT / 'registration.json', dict(failure=identity(SOURCE / 'failure_controller.json'),
        exact_first_import_trace=identity(SOURCE / 'review.log'), source_outputs=identity(SOURCE / 'gpu_completion.json'),
        actual_first_remaining_model_calls=93, adopted_model_calls=4, new_GPU_calls=0,
        recovery='Load canonical original runtime once before grammar import; reuse same bound runtime',
        no_prior_successful_output_replay=True, old_parent_failure_preserved=True))
    runtime = legacy_runtime()
    import pilot_review30 as original
    original.legacy_runtime = lambda: runtime
    original.review()
    save(OUT / 'completion.json', dict(state='WHOLE97_ORIGINAL_COARSE_REFERENCE_REVIEW_COMPLETE',
        independent_CPU=identity(SOURCE / 'independent_CPU_audit.json'),
        GPU_seconds=resource['charged_seconds'], adopted_original_calls=4, first_remaining_calls=93,
        new_GPU_calls=0, training_updates=0, new_ZIP=0,
        exact_complete40_47_control=False, old30_failure_preserved=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_every_success=True))
        raise
