"""First complete150 final parallel-policy outputs; initial50 adopted from107."""
import time

from development_data46 import development_sources
from native_prepared103 import Prefetch, transfer
from parallel_forward107 import infer
from parallel_input106 import values
from t_io import ROOT, identity, read, save


def development(model, processor, rt, inputs, protocol, code, state, out):
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    folder = out / 'development'
    folder.mkdir()
    outputs = {}
    for index, arm in enumerate(protocol['development_matrix'][1:], 1):
        (folder / arm).mkdir()
        input_arm = protocol['input_arm_keys'][index]
        entries = [(sid, source, case, inputs['development'][sid][input_arm][case.name])
                   for sid, source in sources.items() for case in source.cases]
        def loader(entry):
            started = time.monotonic()
            actual = values(entry[2], entry[3], processor.tokenizer, rt)
            return actual, time.monotonic() - started
        outputs[arm] = {}
        with Prefetch(entries, loader) as pending:
            for (sid, source, case, proof), (actual, cpu_seconds) in pending:
                gpu, signature, _ = transfer(actual, proof, rt)
                ref, _ = infer(model, source, case, proof, code, state, 'actor',
                    gpu, signature, folder / arm / case.name)
                outputs[arm].setdefault(sid, {})[case.name] = ref
                del actual, gpu
                print('PARALLEL108_FIRST_DEV', arm, sid, case.name, cpu_seconds, flush=True)
    if sum(len(cases) for arm in outputs.values() for cases in arm.values()) != 150:
        raise ValueError('Complete three-arm150 final parallel policy calls not reached')
    save(out / 'development_GPU.json', dict(outputs=outputs, actual_new_calls=150,
        original_initial50_adopted=identity(ROOT / 'parallel_cost107/initial_controls_GPU.json'),
        complete_source50_each_arm=True, frozen_final_state=state, quality_or_confirmation_admitted=False))
    return identity(out / 'development_GPU.json')
