"""Compare tensor forward with the author's exact CPU C loops, no ML quality."""
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
import torch
from legacy_align import legacy_align
from runtime import ROOT, build_model


def extract_forward(source, name):
    needle = 'void ' + name + '(';
    position = source.index(needle, source.index(needle) + len(needle))
    opening = source.index('{', position)
    level = 0
    for index in range(opening, len(source)):
        level += (source[index] == '{') - (source[index] == '}')
        if level == 0:
            return source[position:index + 1]
    raise ValueError('Unclosed frozen author C function')


def compiled_reference(folder):
    names = ['ROIAlignForwardCpu', 'RODAlignForwardCpu']
    body = '#include <math.h>\n' + '\n'.join(extract_forward((ROOT / 'upstream' / path).read_text(), name)
        for path, name in zip(['roi_align/src/roi_align.c', 'rod_align/src/rod_align.c'], names))
    source, library = folder / 'reference.c', folder / 'reference.so'
    source.write_text(body)
    done = subprocess.run(['cc', '-O2', '-shared', '-fPIC', str(source), '-lm', '-o', str(library)], capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError('Bounded plain-C reference compile failed: ' + done.stderr[-1200:])
    loaded = ctypes.CDLL(str(library))
    ptr = np.ctypeslib.ndpointer(dtype=np.float32, flags='C_CONTIGUOUS')
    functions = {}
    for mode, name in zip(['roi', 'rod'], names):
        function = getattr(loaded, name)
        function.argtypes = [ptr, ctypes.c_float] + [ctypes.c_int] * 6 + [ptr, ptr]
        function.restype = None
        functions[mode] = function
    return functions, hashlib.sha256(body.encode()).hexdigest()


def main():
    folder = ROOT / 'compat'
    folder.mkdir()
    torch.set_num_threads(2)
    functions, source_sha = compiled_reference(folder)
    rng = np.random.default_rng(20261021)
    data = rng.normal(size=(2, 3, 7, 9)).astype(np.float32)
    rois = np.array([[0, 0, 0, 8, 6], [1, .5, 1.3, 6.8, 5.5], [0, -1, -.5, 9, 7],
                     [1, 2.9, 2.5, 4.5, 4.1]], dtype=np.float32)
    errors = []
    for mode in ['roi', 'rod']:
        for scale in [1., .5]:
            for ah, aw in [(3, 4), (10, 10)]:
                output = np.zeros((len(rois), data.shape[1], ah, aw), dtype=np.float32)
                functions[mode](data, scale, len(rois), data.shape[2], data.shape[3], data.shape[1], ah, aw, rois, output)
                actual = legacy_align(torch.from_numpy(data), torch.from_numpy(rois), ah, aw, scale, mode).numpy()
                np.testing.assert_allclose(actual, output, rtol=3e-5, atol=3e-6)
                errors.append(dict(mode=mode, scale=scale, grid=[ah, aw], max_abs=float(abs(actual - output).max())))
    model = build_model()
    parameters = sum(p.numel() for p in model.parameters())
    result = dict(status='PASS_EXACT_C_PARITY_AND_UNTRAINED_AUTHOR_ARCHITECTURE_BUILD', contracts=len(errors),
        rows=errors, compiled_reference_source_sha256=source_sha, architecture_parameters=parameters,
        combined_with_protected_pipeline=8782557449 + parameters, trained_checkpoint_loaded=False,
        actual_research_forward=0, GPU_initialized=torch.cuda.is_initialized(),
        compatibility_changes=['Pure tensor forward for frozen ROI/ROD C semantics', 'Restore missing eval-identity dropout declaration',
                               'loadweightFalse suppresses unrelated ImageNet downloads', 'Drop unused thop import'])
    if result['combined_with_protected_pipeline'] > 9000000000 or result['GPU_initialized']:
        raise ValueError('Parameter/CPU contract')
    with (ROOT / 'compat_cpu_acceptance.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
