"""CPU-only C now, then D after the already-running global chain completes."""
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from pack_common import read, reference, require, save


def main(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only packaging parent')
    save(root / 'chain_started.json', dict(pid=os.getpid(), argv=sys.argv,
         start_ticks=Path('/proc/self/stat').read_text().split()[21],
         utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    control = read(root / 'controller_registration.json')
    width = Path(control['width_root'])
    require(read(width / 'chain_completion.json')['status'] ==
            'PASS_NATIVE16_WIDTH_MODEL_OUTPUTS_READY_FOR_ENGINEERING_PACK', 'Natural width chain complete')
    common = dict(control['package_registration_template'], out_root=str(root / 'packages_01'),
                  width_root=str(width), width_resource=reference(width / 'GPU_resource.json'),
                  width_unique_resource=reference(width / 'unique_resource_verified.json'),
                  width_by_video=reference(width / 'width_by_video.json'),
                  width_output_QA=reference(width / 'width_output_QA.json'))
    (root / 'packages_01').mkdir()

    def pack(arm, reg):
        path = root / ('registration_' + arm + '.json')
        save(path, reg)
        subprocess.run([sys.executable, str(root / 'code/package_width.py'),
                        '--width-root', str(width), '--out-root', str(root / 'packages_01'),
                        '--registration', str(path), '--arm', arm], check=True)

    pack('C', common)
    global_root = Path(control['global_root'])
    started = time.monotonic()
    while not (global_root / 'chain_completion.json').exists():
        require(not (global_root / 'chain_failure.json').exists(), 'Global chain failed; retain completed C')
        require(time.monotonic() - started < control['max_wait_seconds'], 'D dependency wait expired; retain C')
        time.sleep(20)
    require(read(global_root / 'chain_completion.json')['status'] ==
            'GLOBAL_LOCAL_TWO_RISK_DIRECTIONS_NATURAL_COMPLETE', 'Natural global chain terminal')
    comparisons = []
    for name in ['GLOBAL_CONTEXT', 'EVENT_PAYOFF']:
        path = global_root / 'packages_01' / name / 'completion.json'
        if read(path).get('independent11strict') is True:
            comparisons.append(reference(path))
    c = root / 'packages_01/NATIVE16_LEARNED_WIDTH/completion.json'
    if read(c).get('independent11strict') is True:
        comparisons.append(reference(c))
    pack('D', dict(common, global_root=str(global_root),
                   global_resource=reference(global_root / 'GPU_resource.json'),
                   global_unique_resource=reference(global_root / 'unique_resource_verified.json'),
                   global_output_QA=reference(global_root / 'output_acceptance.json'),
                   comparison_completion_refs=comparisons))
    save(root / 'chain_completion.json', dict(status='C_D_ENGINEERING_PACKAGES_COMPLETE',
         new_model_calls=0, offline_effect_validation=False, online_effect='UNKNOWN', website_submitted=False))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    root = Path(parser.parse_args().root)
    try:
        main(root)
    except BaseException as error:
        if not (root / 'chain_failure.json').exists():
            save(root / 'chain_failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
                 preserve_all_success=True, no_automatic_restart=True))
        raise
