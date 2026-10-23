"""First Linux native/reward/policy CPU contracts, no model/assets loaded."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import time
import unittest

from t_io import ROOT, identity, save


def main():
    import torch
    import test_native_reward
    import test_policy_contract
    output = ROOT / 'cpu_contracts12'
    output.mkdir()
    names = ['native_sets.py', 'preference_reward.py', 'policy_contract.py',
             'test_native_reward.py', 'test_policy_contract.py', 'cpu_contracts12.py']
    save(output / 'registration.json', dict(
        code={name: identity(Path(__file__).parent / name) for name in names},
        scope='Native overlap, reviewer/UNKNOWN isolation, constrained-policy probability and CPU gradient only',
        no_real_model_or_quality_claim=True, no_input_preparation_or_GPU=True))
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(module)
                               for module in [test_native_reward, test_policy_contract]])
    started = time.monotonic()
    with (output / 'checks.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    record = dict(state='PASS' if result.wasSuccessful() else 'FAILED', checks=result.testsRun,
                  failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
                  elapsed_seconds=time.monotonic() - started, torch_version=torch.__version__,
                  CUDA_initialized=torch.cuda.is_initialized(), training_updates=0, model_calls=0)
    save(output / 'completion.json', record)
    print('CPU_CONTRACTS12', record, flush=True)
    if not result.wasSuccessful() or record['CUDA_initialized']:
        raise RuntimeError('Actual targeted CPU contract did not pass')


if __name__ == '__main__':
    main()
