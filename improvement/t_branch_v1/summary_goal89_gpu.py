"""Actual first final-adapter goals on the exact adopted two-source BASE inputs."""
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import torch
from peft import get_peft_model_state_dict, set_peft_model_state_dict
from peft.tuners.tuners_utils import BaseTunerLayer
from safetensors.torch import load_file

from frozen_branch46 import RUN
from summary_actor88 import digest
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_goals89'
TEMP = Path('/dev/shm/aic_T_summary_goals89')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def generate(model, tokenizer, rt, ref, final):
    row = read(check(ref))
    with np.load(check(row['text']), allow_pickle=False) as data:
        values = {key: torch.from_numpy(data[key].copy()) for key in data.files}
    if rt.tensor_signature(values) != row['actual_signature']:
        raise ValueError('Adopted actual source-summary prefix differs')
    gpu = {k: v.cuda() for k, v in values.items()}
    signature = rt.tensor_signature({k: v.cpu() for k, v in gpu.items()})
    if signature != row['actual_signature']:
        raise ValueError('Actual trained source-goal GPU transfer differs')
    model.set_adapter('summary'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    layers = [m for m in model.modules() if isinstance(m, BaseTunerLayer)]
    if len(layers) != 144 or any(m.disable_adapters or m.active_adapters != ['summary'] for m in layers):
        raise ValueError('Actual final content adapter was not exclusively activated')
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    started = time.monotonic(); prefix = values['input_ids'].shape[1]
    with torch.inference_mode():
        result = model.generate(**gpu, do_sample=False, num_beams=1, repetition_penalty=1.,
            max_new_tokens=row['maximum_new_tokens'], return_dict_in_generate=True, output_scores=True)
    elapsed = time.monotonic() - started; tokens = result.sequences[0, prefix:].tolist()
    scores = torch.cat(result.scores, dim=0).float()
    selected = scores[torch.arange(len(tokens), device=scores.device), torch.tensor(tokens, device=scores.device)]
    norm = torch.logsumexp(scores, dim=1)
    temporary = TEMP / (row['source'] + '.activation.pt')
    with temporary.open('xb') as stream:
        torch.save(dict(scores=scores.cpu()), stream)
    raw = OUT / 'raw' / (row['source'] + '.pt')
    with raw.open('xb') as stream:
        torch.save(dict(source=row['source'], input_proof=ref, actual_GPU_signature=signature,
            model_role='final_trained_summary_only', active_summary_layers=144,
            actual_pipeline_parameters=8869330010, trained_adapter=final,
            tokens=tokens, eos=eos, text=tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False),
            selected_logits=selected.cpu().tolist(), log_normalizers=norm.cpu().tolist(),
            selected_logp=(selected - norm).cpu().tolist(), maximum_new_tokens=row['maximum_new_tokens'],
            temporary_scores=identity(temporary), generation_seconds=elapsed,
            human_reference_given_at_inference=False), stream)
    del result, gpu, values, scores, selected, norm
    child = subprocess.run([str(PY), '-B', str(Path(__file__).with_name('summary_goal89_cpu.py')), str(raw)],
        text=True, capture_output=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'))
    if child.returncode:
        save(OUT / (row['source'] + '_CPU_failure.json'), dict(exit_code=child.returncode,
            stdout=child.stdout, stderr=child.stderr, raw_and_current_activation_preserved=True))
        raise RuntimeError('First trained goal independent CPU QA failed')
    print('SUMMARY89_FIRST_TRAINED_GOAL', row['source'], len(tokens), elapsed, flush=True)
    return dict(raw=identity(raw), CPU=identity(raw.with_suffix('.CPU.json')),
        retirement=identity(raw.with_suffix('.retirement.json')), tokens=len(tokens), generation_seconds=elapsed)


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    final = read(check(lock['actual_training']))['final_adapter']
    weights = load_file(str(check(final['weights'])), device='cpu')
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    model.load_adapter(final['adapter_directory'], adapter_name='summary', is_trainable=False)
    set_peft_model_state_dict(model, weights, adapter_name='summary')
    actual = get_peft_model_state_dict(model, adapter_name='summary')
    if set(actual) != set(weights) or any(not torch.equal(actual[k].detach().cpu(), weights[k]) for k in weights):
        raise ValueError('Actual trained inference adapter load rounded its final FP32 weights')
    if sum(p.numel() for p in model.parameters()) + 98329 + 37184640 + 28043472 + 6209025 != 8869330010:
        raise ValueError('Actual complete final source-summary pipeline parameter budget differs')
    initial = digest(model); TEMP.mkdir(); (OUT / 'raw').mkdir()
    cpu = read(check(lock['adopted_two_goal_CPU']))['accepted']
    outputs = {sid: generate(model, processor.tokenizer, rt, ref, final) for sid, ref in cpu.items()}
    model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    if (len(outputs) != 2 or digest(model) != initial
            or rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Actual complete goal scope or frozen model bytes differ')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_TWO_FINAL_TRAINED_GOALS_AND_CPU_PASS_NOT_TIME_QUALITY',
        outputs=outputs, final_adapter=final, actual_pipeline_parameters=8869330010,
        original_BASE_TIME_and_final_summary_unchanged=True, first_new_generations=2,
        first_CPU=2, peak_torch_bytes=torch.cuda.max_memory_allocated(), new_training=0))


if __name__ == '__main__':
    main()
