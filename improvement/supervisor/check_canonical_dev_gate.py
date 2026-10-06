"""Exercise the canonical-dev regression using completed development artifacts, without GPU calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
DEV = ROOT / 'runs/improvement_dev_v2'


def main():
    summary = json.loads((DEV / 'summary.json').read_text())
    if not summary['qualified']:
        raise ValueError('regression needs an actually qualified development comparison')
    spec = importlib.util.spec_from_file_location('holdout_gate_under_test', CAMPAIGN / 'run_holdout_suite.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='canonical-dev-regression-', dir=CAMPAIGN) as temporary:
        directory = Path(temporary)
        fixture_campaign = directory / 'campaign'
        (fixture_campaign / 'frozen_data').mkdir(parents=True)
        for name in ('train.jsonl', 'dev.jsonl', 'holdout.jsonl', 'lock.json'):
            shutil.copyfile(CAMPAIGN / 'frozen_data' / name, fixture_campaign / 'frozen_data' / name)
        copied = directory / 'dev'
        copied.mkdir()
        names = ['summary.json', 'input_lock.json', 'dev_frozen.jsonl', 'single_report.json', 'single_predictions.jsonl']
        for policy in summary['qualified']:
            names += [policy + '_report.json', policy + '_predictions.jsonl']
        for name in names:
            shutil.copyfile(DEV / name, copied / name)
        # Same parsed records but a different self-consistent file identity:
        # the historical bug accepted this run's self-declared dev hash.
        changed = (copied / 'dev_frozen.jsonl').read_bytes() + b'\n'
        (copied / 'dev_frozen.jsonl').write_bytes(changed)
        lock = json.loads((copied / 'input_lock.json').read_text())
        lock['dev'] = hashlib.sha256(changed).hexdigest()
        (copied / 'input_lock.json').write_text(json.dumps(lock))
        with patch.object(module, 'CAMPAIGN', fixture_campaign), \
             patch.object(sys, 'argv', ['run_holdout_suite.py', '--dev-run', str(copied),
                 '--output', str(directory / 'out'), '--name-prefix', 'never_execute']), \
             patch.object(module.subprocess, 'run', side_effect=AssertionError('GPU scheduling is forbidden in this regression')):
            try:
                module.main()
            except ValueError as error:
                if 'canonical dev split' not in str(error):
                    raise
            else:
                raise AssertionError('noncanonical dev was accepted')
        if (directory / 'out').exists():
            raise AssertionError('rejected development run created a holdout output')
        if (fixture_campaign / 'holdout_comparison_lock.json').exists():
            raise AssertionError('rejected development run consumed the holdout lock')
    result = {'status': 'passed', 'noncanonical_self_consistent_dev_rejected': True,
              'gpu_calls': 0, 'source': str(DEV), 'test': str(Path(__file__))}
    (ROOT / 'reports/supervisor_canonical_dev_gate_test.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
