"""Continue a registered download-only transport upgrade, never inference retry."""
import os
import traceback
from common import ROOT, read, write
from remaining_pipeline import run


if __name__ == '__main__':
    try:
        assert read(ROOT / 'assets_remaining03_terminal.json')['exit_code'] == -15
        assert not (ROOT / 'gpu_launch.json').exists()
        write(ROOT / 'controller_remaining04_claim.json', dict(pid=os.getpid(),
              transport_only=True, accepted_source_and_partial_bytes_adopted=True,
              previous_stop='ControlledSIGTERM of exact owned network child, not natural network/model failure'))
        run('04', 'range_weight04.py')
    except BaseException:
        write(ROOT / 'failure_remaining04.json', dict(status='ACTUAL_REMAINING_FAILURE_PRESERVED',
              traceback=traceback.format_exc()))
        raise
