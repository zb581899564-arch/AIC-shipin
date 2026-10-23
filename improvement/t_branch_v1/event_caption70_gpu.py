"""First local AV event memory; shared BASE perception, original TIME reserved for selection."""
import os
from pathlib import Path
import subprocess
import time

import torch

from development_data46 import development_sources
from event_memory69_common import CAPTION, INPUT, actual_values
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

TEMP = Path('/dev/shm/aic_T_event_caption70')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def first_event(model, tokenizer, rt, case, proof):
    from peft.tuners.tuners_utils import BaseTunerLayer
    values = actual_values(case, proof, tokenizer, rt)
    gpu = {k: v.cuda() if torch.is_tensor(v) else v for k, v in values.items()}
    actual = rt.tensor_signature({k: v.cpu() if torch.is_tensor(v) else v for k, v in gpu.items()})
    if actual != read(check(proof))['actual_signature']:
        raise ValueError('Actual GPU input differs from first CPU-native token contract')
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    started = time.monotonic(); prefix = values['input_ids'].shape[1]
    with model.disable_adapter(), torch.inference_mode():
        layers = [m for m in model.modules() if isinstance(m, BaseTunerLayer)]
        if len(layers) != 144 or any(not bool(m.disable_adapters) for m in layers):
            raise ValueError('Original BASE perception role was not actually activated')
        result = model.generate(**gpu, do_sample=False, max_new_tokens=128,
            num_beams=1, repetition_penalty=1., return_dict_in_generate=True, output_scores=True)
    tokens = result.sequences[0, prefix:].tolist()
    scores = torch.cat(result.scores, dim=0).float()
    index = torch.tensor(tokens, device=scores.device)
    selected = scores[torch.arange(len(tokens), device=scores.device), index]
    norm = torch.logsumexp(scores, dim=1)
    top = scores.topk(2, dim=1)
    temporary = TEMP / (case.name + '.activation.pt')
    with temporary.open('xb') as stream:
        torch.save(dict(scores=scores.cpu()), stream)
    raw = CAPTION / 'raw' / (case.name + '.pt')
    text = tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    with raw.open('xb') as stream:
        torch.save(dict(case=case.name, source=case.meta['source_name'], input_proof=proof,
            actual_input_signature=actual, model_role='original_BASE_TIME_disabled',
            actual_disabled_adapter_modules=144, tokens=tokens, text=text, eos=eos,
            selected_logits=selected.cpu().tolist(), log_normalizers=norm.cpu().tolist(),
            selected_logp=(selected - norm).cpu().tolist(), top2_values=top.values.cpu().tolist(),
            top2_ids=top.indices.cpu().tolist(), original_interval_exact=[case.meta['window_start'], case.meta['window_end']],
            temporary_scores=identity(temporary), generation_seconds=time.monotonic() - started,
            output_is_unverified_machine_observation_not_annotation=True), stream)
    del result, gpu, values, scores, selected, norm, top
    command = [str(PY), '-B', str(Path(__file__).with_name('event_caption70_cpu.py')), str(raw)]
    child = subprocess.run(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'),
        text=True, capture_output=True)
    if child.returncode:
        save(CAPTION / (case.name + '_CPU_failure.json'), dict(exit_code=child.returncode,
            stdout=child.stdout, stderr=child.stderr, raw_and_activation_preserved=True))
        raise RuntimeError('First independent event output QA failed')
    proof = identity(raw.with_suffix('.CPU.json'))
    if read(raw.with_suffix('.retirement.json'))['first_CPU_proof'] != proof:
        raise ValueError('Temporary retirement lacks complete independent CPU proof')
    print('EVENT70_FIRST_CAPTION_AND_CPU_PASS', case.name, len(tokens), flush=True)
    return dict(raw=identity(raw), CPU=proof, retirement=identity(raw.with_suffix('.retirement.json')))


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(CAPTION / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    cpu = read(check(lock['first_complete_CPU']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    count = sum(p.numel() for p in model.parameters())
    if count != 8782459120 or count + 98329 + 37184640 != 8819742089:
        raise ValueError('Actual original model/ASR pipeline budget differs')
    model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    TEMP.mkdir(); (CAPTION / 'raw').mkdir()
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    outputs = {}
    for sid, source in sources.items():
        outputs[sid] = {}
        for case in source.cases:
            outputs[sid][case.name] = first_event(model, processor.tokenizer, rt, case, cpu['accepted'][sid][case.name])
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original BASE/TIME changed')
    save(CAPTION / 'GPU_completion.json', dict(state='FIRST50_LOCAL_EVENT_GENERATIONS_AND_CPU_PASS_NOT_QUALITY',
        outputs=outputs, actual_new_generations=sum(len(v) for v in outputs.values()),
        actual_original_model_parameters=count, original_pipeline_with_ASR_parameters=8819742089,
        prospective_full40_48_with_ASR_parameters=8853994586,
        original_weights_unchanged=True, new_training=0, new_candidates=0,
        peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
