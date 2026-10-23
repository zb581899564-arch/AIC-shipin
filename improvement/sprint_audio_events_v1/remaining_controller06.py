"""Continue only after known zero-GPU ceil-contract engineering failure."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.append('/home/inspur/aic_video_work/sprint_audio_events_20261021_v1/code')
import json
import os
import subprocess
import traceback
from datetime import datetime, timezone
from common import ROOT, WORK, PY, WRAPPER, read, write, reference, checked
from controller import cpu, gpu, CODE


def main():
    write(ROOT/'remaining06_claim.json', dict(pid=os.getpid()))
    if read(ROOT/'first_pann_CPU_terminal.json')['exit_code'] != 1 or 'Original exact interval differs from retained waveform' not in (ROOT/'first_pann_CPU.log').read_text():
        raise ValueError('Only exact known pre-GPU input failure can resume')
    if (ROOT/'events_completion.json').exists() or (ROOT/'source_input_lock.json').exists():
        raise ValueError('Unexpected prior successful GPU or source lock')
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    with (ROOT/'first_remaining_inputs06.log').open('x') as log:
        result = subprocess.run([str(PY), '-u', '-B', str(Path(__file__).parent/'inputs_remaining06.py')],
            env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    write(ROOT/'first_remaining_inputs06_terminal.json', dict(exit_code=result.returncode))
    if result.returncode:
        raise ValueError('Actual remaining CPU preparation failed')
    protected = reference(WORK/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    if protected['sha256'] != 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3':
        raise ValueError('Protected40.47 changed')
    write(ROOT/'source_input_lock.json', dict(protocol=reference(ROOT/'protocol.json'), baseline=protected,
        code={str(p.relative_to(ROOT)):reference(p) for folder in [CODE, Path(__file__).parent] for p in sorted(folder.glob('*.py'))},
        inputs=reference(ROOT/'input_acceptance.json'), model=reference(ROOT/'model_cpu_acceptance.json'),
        author_source=reference(ROOT/'author_source_acceptance.json'), wrapper=reference(WRAPPER),
        recovery=reference(ROOT/'input_remaining06_registration.json')))
    count = read(ROOT/'model_cpu_acceptance.json')['actual_parameters']
    event = gpu('pann_timed_events8_20261021_v1', 'events.py', 180, count*4+32000*30*4*256)
    cpu('independent_events', 'event_review.py')
    cpu('first_augmented_inputs', 'text_inputs.py')
    write(ROOT/'TIME_input_lock.json', dict(original_lock=reference(ROOT/'source_input_lock.json'),
        actual_first16_inputs=reference(ROOT/'text_input_acceptance.json'), event_independent_QA=reference(ROOT/'first_event_output_acceptance.json')))
    temporal = gpu('pann_audio_correct_shift_TIME16_20261021_v1', 'time_calls.py', 1800,
        8782459120*2+65536*4096*2*8+2*1024**3)
    cpu('independent_TIME_review', 'review.py')
    checked(protected)
    for entry in read(ROOT/'source_input_lock.json')['code'].values():
        checked(entry)
    result = dict(status=read(ROOT/'review.json')['status'], review_ref=reference(ROOT/'review.json'),
        independent_qa=reference(ROOT/'independent_output_qa.json'), GPU_charged_seconds=event['charged_seconds']+temporal['charged_seconds'],
        model_forwards=dict(PANN=8, original_TIME=16), new_updates=0, new_ZIP=0,
        original40_47_unchanged=True, automatic_production=False,
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(ROOT/'completion.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT/'remaining06_failure.json', dict(status='ACTUAL_FAILURE_SUCCESS_AND_RAW_PRESERVED', traceback=traceback.format_exc()))
        raise
