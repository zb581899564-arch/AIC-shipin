"""Resume only missing weight/input/model work, preserving the original failure."""
import os
import traceback
from common import ROOT, read, ref, write
from controller import stage, WRAPPER
from complete import complete


def main():
    assert read(ROOT / 'assets_terminal.json')['exit_code'] == 1
    assert not (ROOT / 'gpu_launch.json').exists()
    write(ROOT / 'controller_remaining02_claim.json', dict(pid=os.getpid(),
          initial_failure_preserved=True, old_successful_source_downloads_repeated=0,
          science_and_model_budget_unchanged=True))
    for name, script in [('assets_remaining02', 'assets_remaining02.py'),
                         ('model_gate', 'model_io.py'), ('torch', 'contracts.py'), ('input', 'prepare.py')]:
        stage(name, script)
    write(ROOT / 'source_input_lock.json', dict(protocol=ref(ROOT / 'protocol.json'),
          recovery=ref(ROOT / 'recovery_registration02.json'),
          code={p.name: ref(p) for p in sorted((ROOT / 'code').glob('*.py'))},
          assets=ref(ROOT / 'download_acceptance.json'), model=ref(ROOT / 'model_acceptance.json'),
          torch=ref(ROOT / 'torch_contracts.json'), input=ref(ROOT / 'input_acceptance.json'),
          wrapper=ref(WRAPPER)))
    stage('gpu', 'infer.py', True)
    stage('review', 'review.py')
    stage('audit', 'audit.py')
    complete()


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'failure_remaining02.json', dict(status='ACTUAL_REMAINING_FAILURE_PRESERVED',
              traceback=traceback.format_exc()))
        raise
