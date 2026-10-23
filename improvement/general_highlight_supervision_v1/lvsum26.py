"""Explicit 0-input import recovery; adopt exact original resize helper dependencies."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
import traceback
from common import ROOT, WORK, save, ref

sys.path.append(str(WORK/'i3d_umt_cross_domain_20261021_v1'))


def main():
    if (ROOT/'native25').exists():raise ValueError('No successful native work may be repeated')
    log=(ROOT/'lvsum25.log').read_text()
    if "No module named 'provenance'" not in log:raise ValueError('Import recovery boundary differs')
    save(ROOT/'native26_remaining_registration.json',dict(
        prior_failure_log=ref(ROOT/'lvsum25.log'),new_native_successes_before_recovery=0,
        exact_dependency=ref(WORK/'i3d_umt_cross_domain_20261021_v1/provenance.py'),
        original_source_and_input_protocol_unchanged=True))
    from lvsum25 import main as prepare
    prepare()


if __name__=='__main__':
    try:main()
    except BaseException:
        save(ROOT/'native26_failure.json',dict(traceback=traceback.format_exc(),no_silent_retry=True))
        raise
