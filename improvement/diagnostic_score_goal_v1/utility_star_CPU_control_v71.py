"""One explicitly registered CPU68 child, with actual exit evidence."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import read, save, ref, bound, require, utc


def run(root):
    registration = root/'utility_star_CPU_registration_68.json'
    reg = read(registration)
    require(reg['schema'] == 'UTILITY_CONNECTED_STAR_CPU_V68'
            and bound(reg['controller_code']) == Path(__file__).resolve(), 'Exact new registered CPU supervisor')
    prefix = 'utility_star_CPU_71'
    save(root/(prefix+'_claim.json'), dict(utc=utc(), registration=ref(registration), pid=os.getpid()))
    argv = [sys.executable, '-B', '-u', str(bound(reg['preparation_code'])), '--root', str(root)]
    entry = None
    try:
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
                   OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
        with (root/(prefix+'.log')).open('xb') as log:
            child = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=subprocess.STDOUT)
            ticks = Path('/proc', str(child.pid), 'stat').read_text().split(') ', 1)[1].split()[19]
            entry = dict(argv=argv, pid=child.pid, start_ticks=ticks, CPU_child=True)
            save(root/(prefix+'_launch.json'), entry)
            code = child.wait()
            save(root/(prefix+'_exit.json'), dict(utc=utc(), actual_exit_code=code, entry=entry))
            require(code == 0, 'Actual CPU68 exit '+str(code))
        gate = read(root/'utility_star_inputs_68/input_acceptance.json')
        require(gate['status'] == 'PASS_UTILITY68_CONNECTED_STAR_ALL_INPUTS_FIRST_CPU_QA'
                and gate['registration'] == ref(registration), 'Actual bound CPU68 input gate')
        save(root/(prefix+'_terminal.json'), dict(status='REGISTERED_STAR_CPU_NATURAL_COMPLETE_EXIT0',
             utc=utc(), exit_code=0, entry=entry, input_acceptance=ref(root/'utility_star_inputs_68/input_acceptance.json'),
             automatic_GPU=False, automatic_training=False, automatic_packaging=False))
    except BaseException as error:
        save(root/(prefix+'_failure.json'), dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
             entry=entry, preserve_all_success=True, no_automatic_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    run(parser.parse_args().root)
