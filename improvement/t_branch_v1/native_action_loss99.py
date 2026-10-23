"""First complete fit loss/input binding after label-free417 CPU inputs pass."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import time
import traceback

from native_training_data99 import bind_training
from t_io import ROOT, identity, read, save

OUT = ROOT / 'native_action_loss99'


def await_inputs():
    launch = read(ROOT / 'native_action_inputs99_launch.json')
    folder = ROOT / 'native_action_inputs99'; deadline = time.monotonic() + 1800
    while True:
        if (folder / 'failure.json').exists():
            raise RuntimeError('New input phase actually failed; never repeat its successes')
        if (folder / 'completion.json').exists():
            result = read(folder / 'completion.json')
            if result['state'] != 'FIRST_ALL417_LOGICAL_NATIVE_ACTION_INPUTS_CPU_PASS':
                raise ValueError('Actual complete label-free input terminal differs')
            return result
        p = Path('/proc') / str(launch['pid'])
        if not p.exists():
            raise RuntimeError('Actual input handle absent without terminal; inspect before any recovery')
        stat = (p / 'stat').read_text().rsplit(')', 1)[1].split()
        if stat[19] != str(launch['start_ticks']) or stat[0] == 'Z' or time.monotonic() > deadline:
            raise RuntimeError('Actual input dependency handle/bounded wait differs')
        time.sleep(5)


def main():
    OUT.mkdir(); inputs = await_inputs(); values = bind_training(inputs)
    save(OUT / 'completion.json', dict(state='FIRST217_NATIVE_ACTION_LOSS_INPUT_BINDINGS_PASS',
        **values, actual_inputs=identity(ROOT / 'native_action_inputs99/completion.json'),
        code={n: identity(Path(__file__).with_name(n)) for n in
              ['native_action_loss99.py', 'native_training_data99.py']},
        all_original_reviewers=86, fit_sources=9, publisher_updates=5,
        physical_windows=217, no_target_coefficients_in_input=True,
        source_global_coefficients_not_per_window=True, no_new_model_calls=True,
        no_training_or_production_admission=True,
        next='Freeze actual full source/code/input/remaining-budget/resource lock for one native action100 job, then live original actor-copy parameters/first-micro cost checks.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
