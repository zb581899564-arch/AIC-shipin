"""First originalTIME same-codec control, no actor, labels or training."""
import torch

from development_data46 import development_sources
from frozen_branch46 import RUN
from native_greedy100 import generate
from native_state100 import fingerprint
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_action_control100'


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    inputs = read(check(lock['actual_inputs']))
    code = read(ROOT / 'native_action_contract98/completion.json')['actual_token_codec']
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if sum(p.numel() for p in model.parameters()) != 8782459120 or set(model.peft_config) != {'default'}:
        raise ValueError('Initial native-codec control is not protected originalTIME only')
    model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    if code['EOS'] not in ([model.generation_config.eos_token_id] if isinstance(
            model.generation_config.eos_token_id, int) else model.generation_config.eos_token_id):
        raise ValueError('Actual original model EOS differs from first CPU native codec')
    state = fingerprint(model, 'default', loaded['base'])
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    arm = read(ROOT / 'code/native_action_protocol98.json')['development_matrix'][0]
    folder = OUT / 'outputs'; folder.mkdir(); outputs, cache = {}, {}
    for sid, source in sources.items():
        outputs[sid] = {}
        for case in source.cases:
            outputs[sid][case.name] = generate(model, processor.tokenizer, rt, source, case,
                inputs['development'][sid][arm][case.name], code, state, 'default', folder / case.name, cache)
    if (sum(map(len, outputs.values())) != 50 or rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Complete original50 native-codec control changed protected weights')
    save(OUT / 'GPU_completion.json', dict(state='FIRST50_ORIGINAL_TIME_NATIVE_CODEC_COMPLETE_NEEDS_CPU',
        outputs=outputs, first_physical_calls=len(cache), logical_calls=50, physical_raw=cache,
        original_BASE_TIME_unchanged=True, original_loaded=loaded,
        actual_resident_parameters=8782459120, prospective_new_method_parameters=8869330010,
        no_actual_actor_or_summary_role_loaded=True, updates=0,
        peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
