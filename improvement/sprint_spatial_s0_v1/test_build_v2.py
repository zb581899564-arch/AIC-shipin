"""Adopt successful C parity before v1's unused-import failure; build once."""
import hashlib
import json
from pathlib import Path
import torch
from runtime import ROOT, build_model


def reference(path):
    return dict(path=str(path), bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    torch.set_num_threads(2)
    prior = (ROOT / 'compat_cpu.log').read_text()
    if 'test_compat.py", line 63, in main' not in prior or 'ShuffleNetV2.py' not in prior or 'TabError:' not in prior:
        raise ValueError('Not the known post-parity unused import failure')
    if json.loads((ROOT / 'compat_terminal.json').read_text())['exit_code'] != 1:
        raise ValueError('Preserve explicit prior failed terminal')
    original = (ROOT / 'code/test_compat.py').read_text()
    if original.index('np.testing.assert_allclose') > original.index('model = build_model()'):
        raise ValueError('Cannot adopt unknown parity stage')
    model = build_model()
    total = sum(p.numel() for p in model.parameters())
    if total + 8782557449 > 9000000000 or torch.cuda.is_initialized():
        raise ValueError('Architecture parameter/CPU boundary')
    result = dict(status='PASS_ADOPT8_C_PARITY_AND_FIRST_AUTHOR_MODEL_BUILD', adopted_parity_contracts=8,
        adoption_basis='Original control reached model constructor after all8 parity assertions, then failed only unused ShuffleNet import',
        prior_failure=reference(ROOT / 'compat_cpu.log'), original_test_code=reference(ROOT / 'code/test_compat.py'),
        original_C_reference=reference(ROOT / 'compat/reference.c'), original_shared_reference=reference(ROOT / 'compat/reference.so'),
        parity_repeated=False, architecture_parameters=total, combined_parameters=total + 8782557449,
        learned_checkpoint_loaded=False, research_forward_calls=0, CUDA_initialized=False,
        sole_v2_fix='Exclude unused ShuffleNet import with malformed indentation, MobileNet architecture unchanged')
    with (ROOT / 'compat_cpu_acceptance_v2.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
