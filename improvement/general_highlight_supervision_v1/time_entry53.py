"""Isolate the original B helper namespace; adopt all ten successful CPU caches."""
import importlib.util
from pathlib import Path
import runpy
import sys

import time_control50_common as context


def original_runtime():
    path=context.RUN/'b_score_aligned_package_v4/common.py'
    spec=importlib.util.spec_from_file_location('common',path)
    module=importlib.util.module_from_spec(spec)
    # The legacy engine does `from common import *`; new research common must not shadow it.
    sys.modules['common']=module;spec.loader.exec_module(module)
    bindings=module.bind_helpers()
    rt=context.runtime()
    if (rt.b_engine.require is not module.require or rt.b_engine.sha is not module.sha or
            Path(rt.b_engine.BASELINE)!=context.RUN/'baseline_a_pts_v1'):
        raise ValueError('Legacy original engine helper namespace remains shadowed')
    return rt,bindings


def cache_check(rt,bindings):
    import numpy as np
    import torch
    if torch.cuda.is_initialized():raise ValueError('Independent input audit initialized CUDA')
    acceptance=context.read(context.ROOT/'CPU_completion.json')
    for identity in acceptance['accepted']:
        record=context.read(context.checked(identity))
        with np.load(context.checked(record['encoded']),allow_pickle=False) as values:
            encoded={k:torch.from_numpy(values[k].copy()) for k in values.files}
        if rt.tensor_signature(encoded)!=record['detail']['tensor_signature']:
            raise ValueError('Adopted real CPU cache differs under canonical helper binding')
        meta=context.read(context.checked(record['input']))
        if (len(set(meta['source_frame_ordinals']))!=64 or
                record['exact_native64_ordinals']!=meta['source_frame_ordinals'] or
                record['native_sample_PTS']!=meta['sample_exact_pts']):
            raise ValueError('Independent adopted native target/PTS denominator differs')
    context.save(context.ROOT/'independent_adopted_CPU_QA53.json',dict(state='PASS',windows=len(acceptance['accepted']),
        canonical_engine_common=context.ref(context.RUN/'b_score_aligned_package_v4/common.py'),
        helpers={k:context.ref(v) for k,v in bindings.items()},
        no_decode_or_processor_or_model_repeated=True,CUDA_initialized=False))


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ['check','gpu','review']:
        raise ValueError('Only explicit remaining stage accepted')
    context.ROOT=context.ADMISSION/'time_control53'
    rt,bindings=original_runtime()
    if sys.argv[1]=='check':cache_check(rt,bindings);return
    if context.read(context.ROOT/'independent_adopted_CPU_QA53.json')['state']!='PASS':
        raise ValueError('Canonical namespace and adopted actual input QA required')
    target=Path(__file__).parent/('time_control50_'+sys.argv[1]+'.py')
    runpy.run_path(str(target),run_name='__main__')


if __name__=='__main__':main()
