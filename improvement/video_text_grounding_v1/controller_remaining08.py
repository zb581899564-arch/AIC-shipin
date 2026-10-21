"""Explicit natural403 remaining-only recovery before the first GPU call."""
import os
import traceback
from common import ROOT, read, write
from remaining_pipeline import run


if __name__ == '__main__':
    try:
        assert read(ROOT / 'assets_remaining04_terminal.json')['exit_code'] == 1
        assert not (ROOT / 'gpu_launch.json').exists()
        write(ROOT / 'controller_remaining08_claim.json', dict(pid=os.getpid(),
              natural403_preserved=True, same_asset_id=71848091,
              successful_ranges_repeated=0, science_unchanged=True))
        run('08', 'range_remaining08.py')
    except BaseException:
        write(ROOT / 'failure_remaining08.json', dict(status='ACTUAL_REMAINING_FAILURE_PRESERVED',
              traceback=traceback.format_exc()))
        raise
