"""CPU-only first missing speech information; never launch Qwen or production."""
from fractions import Fraction
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import traceback

from speech_scope58 import ADOPT, GENERAL, NEW, OUT, ROOT, WAVE, WORK
from speech_scope58 import check, identity, read, save, selected_sources

CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def adopt(sources):
    old = read(GENERAL / 'speech36/ASR_completion.json')
    inputs = {read(check(ref))['sid']: ref for ref in read(GENERAL / 'speech36/input_acceptance.json')['accepted']}
    outputs = {sid: [] for sid in ADOPT}
    for ref in old['outputs']:
        sid = read(check(ref))['sid']
        if sid in outputs:
            outputs[sid].append(ref)
    result = {}
    for sid in ADOPT:
        native = read(check(inputs[sid])); clock = read(check(sources[sid]['clock']))
        duration = Fraction(clock['physical_end_exact']) - Fraction(clock['first_PTS_exact'])
        if native['media']['sha256'] != sources[sid]['media']['sha256'] or Fraction(native['physical_duration_exact']) != duration:
            raise ValueError('Successful old full-ASR source/clock identity differs')
        if len(outputs[sid]) != len(native['chunks']):
            raise ValueError('Successful old ASR source incomplete')
        result[sid] = dict(source=sources[sid], native=inputs[sid], outputs=outputs[sid],
            old_summary=next(row for row in old['sources'] if row['sid'] == sid),
            new_audio_decode=0, new_ASR_calls=0)
    save(OUT / 'adopted_ASR.json', result)


def execute(name, deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError('CPU information budget exhausted before new phase')
    command = [str(PY), '-B', '-u', str(CODE / (name + '.py'))]
    with (OUT / (name + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
                AIC_SPEECH58_DEADLINE=str(deadline), PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (name + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (name + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First missing speech phase failed: ' + name)


def main():
    OUT.mkdir(); started = time.monotonic()
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Wrong actual shared host')
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Protected CONTROL5 state differs')
    if read(ROOT / 'development_remaining55/completion.json')['state'] != 'STOP_FROZEN_JOINT4_DEVELOPMENT':
        raise ValueError('Actual rejected fixed profile absent')
    sources = selected_sources()
    seconds = sum(float(Fraction(read(check(sources[sid]['clock']))['physical_end_exact'])
        - Fraction(read(check(sources[sid]['clock']))['first_PTS_exact'])) for sid in NEW)
    estimate = int(seconds * 16000 * 9 + 10000000)
    if shutil.disk_usage('/dev/shm').free < estimate or shutil.disk_usage(ROOT).free < 10000000:
        raise RuntimeError('Actual capacity cannot hold estimated first audio and short receipts')
    save(OUT / 'registration.json', dict(scope='First aligned speech information only, no candidate qualification',
        new_sources=list(NEW), adopted_sources=list(ADOPT), original_source_registry=identity(ROOT / 'source_registry09/registration.json'),
        code={name: identity(CODE / name) for name in ['speech_scope58.py', 'speech_native58.py', 'speech_decode58.py', 'speech_information58.py']},
        new_GPU_calls=0, new_Qwen_calls=0, new_training=0, confirmation_sources_read=0,
        CPU_wall_budget_seconds=600, waveform_storage=str(WAVE), waveform_estimate_bytes=estimate,
        source_use='Same original noncommercial human-summary preference scope; ASR is unverified machine text',
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:20],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True),
        no_new_model_download_or_dependency_install=True, original40_47_unchanged=True))
    adopt(sources); WAVE.mkdir()
    execute('speech_native58', started + 600)
    save(OUT / 'source_input_lock.json', dict(registration=identity(OUT / 'registration.json'),
        actual_new_native=identity(OUT / 'native_completion.json'), adopted_ASR=identity(OUT / 'adopted_ASR.json')))
    execute('speech_decode58', started + 600)
    save(OUT / 'completion.json', dict(state='FOUR_SOURCE_SPEECH_INFORMATION_AVAILABLE_NOT_MODEL_QUALITY',
        adopted_sources=identity(OUT / 'adopted_ASR.json'), new_sources=identity(OUT / 'ASR_completion.json'),
        first_native_QA=identity(OUT / 'native_completion.json'), CPU_wall_seconds=time.monotonic() - started,
        new_Qwen_or_GPU_calls=0, new_training=0, new_packages=0, fresh_confirmation_read=False,
        next='Inspect actual native-window intersections and availability before a separately frozen audiovisual information experiment'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
