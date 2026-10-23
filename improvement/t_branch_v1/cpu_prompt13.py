"""Only the four newly required task/prefix binding checks; no old checks rerun."""
from pathlib import Path
import unittest

from t_io import ROOT, identity, save


def main():
    import test_prompt13
    output = ROOT / 'cpu_prompt13'
    output.mkdir()
    save(output / 'registration.json', dict(
        files={name: identity(Path(__file__).parent / name) for name in
               ['prompt_contract13.py', 'test_prompt13.py', 'cpu_prompt13.py']},
        prior_native_and_policy_checks_not_repeated=True, no_model=True))
    with (output / 'checks.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromModule(test_prompt13))
    save(output / 'completion.json', dict(state='PASS' if result.wasSuccessful() else 'FAILED',
        checks=result.testsRun, failures=len(result.failures), errors=len(result.errors), model_calls=0))
    if not result.wasSuccessful():
        raise RuntimeError('New prompt-binding contract failed')
    print('CPU_PROMPT13_PASS', result.testsRun, flush=True)


if __name__ == '__main__':
    main()
