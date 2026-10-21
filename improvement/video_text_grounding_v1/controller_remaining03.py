"""Explicit same-asset API transport recovery, with no repeated success."""
import os
import traceback
from common import ROOT, read, write
from remaining_pipeline import run


if __name__ == '__main__':
    try:
        assert read(ROOT / 'assets_remaining02_terminal.json')['exit_code'] == 1
        assert not (ROOT / 'gpu_launch.json').exists()
        write(ROOT / 'controller_remaining03_claim.json', dict(pid=os.getpid(),
              old_failures_preserved=True, same_official_asset_id=71848091, weight_successes=0))
        run('03', 'assets_remaining03.py')
    except BaseException:
        write(ROOT / 'failure_remaining03.json', dict(status='ACTUAL_REMAINING_FAILURE_PRESERVED',
              traceback=traceback.format_exc()))
        raise
