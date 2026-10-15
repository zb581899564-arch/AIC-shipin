"""One first-confirm media stage followed by its registered CPU/model/QA chain."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import traceback

import model_common as io


def main(root):
    io.host(cpu=False)
    root = io.root_path(root)
    io.require(Path(__file__).resolve().parent == root/'code', 'Separate deployed root required')
    selected = io.read(root/'dev/selection_before_confirmation.json')
    io.require(selected['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION' and
        selected['protocol_sha256'] == io.sha(root/'protocol.json'), 'Actual frozen dev selection required')
    io.checked(root/'dev/comparison_01/result.json', selected['result_sha256'])
    state = root/'confirm/control_07'
    state.mkdir(parents=True, exist_ok=False)
    io.save(state/'started.json', dict(pid=os.getpid(), utc=io.utc(), parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'],
        new_model_calls_at_start=0, production_admitted=False, old_successes_repeated=False))
    stage = 'FIRST_CONFIRM_MEDIA_AND_NATIVE_CLOCK'
    try:
        for name, cpu in [('prepare_confirm_reference_v3.py', True), ('pilot_chain_confirm_v3.py', False)]:
            env = dict(os.environ)
            if cpu:
                env['CUDA_VISIBLE_DEVICES'] = ''
            argv = [sys.executable, '-B', '-u', str(root/'code'/name), '--root', str(root), '--group', 'confirm']
            io.save(state/(name+'.launch.json'), dict(argv=argv, utc=io.utc(), CPU_only=cpu))
            with (state/(name+'.log')).open('xb') as log:
                result = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            io.require(result.returncode == 0, 'Actual confirm child failed; preserve all success and never implicitly retry: '+name)
            stage = 'FIRST_CONFIRM_INPUT_MODEL_QA_COMPARISON'
        finished = root/'confirm/chain_03/completion.json'
        terminal = io.read(finished)
        io.save(state/'completion.json', dict(status=terminal['status'], utc=io.utc(),
            chain_completion_path=str(finished), chain_completion_sha256=io.sha(finished),
            production_admitted=False, no_426_model_or_package_started=True))
    except BaseException as error:
        io.save(state/'failure.json', dict(stage=stage, error=repr(error), traceback=traceback.format_exc(),
            preserve_all_success_and_failure=True, implicit_resume=False, production_admitted=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
