"""Pay once for the actual two-source untrained planner control and its cost."""
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import torch

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_baseline86'
TEMP = Path('/dev/shm/aic_T_summary_goal86')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def one_goal(model, tokenizer, rt, ref):
    from peft.tuners.tuners_utils import BaseTunerLayer
    row = read(check(ref))
    with np.load(check(row['text']), allow_pickle=False) as data:
        values = {k: torch.from_numpy(data[k].copy()) for k in data.files}
    if rt.tensor_signature(values) != row['actual_signature']:
        raise ValueError('Actual pure text goal input differs from first CPU contract')
    gpu = {k: v.cuda() for k, v in values.items()}; prefix = values['input_ids'].shape[1]
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    started = time.monotonic()
    with model.disable_adapter(), torch.inference_mode():
        layers = [m for m in model.modules() if isinstance(m, BaseTunerLayer)]
        if len(layers) != 144 or any(not bool(m.disable_adapters) for m in layers):
            raise ValueError('Actual original BASE role was not used for planner control')
        result = model.generate(**gpu, do_sample=False, num_beams=1, repetition_penalty=1.,
            max_new_tokens=row['maximum_new_tokens'], return_dict_in_generate=True, output_scores=True)
    elapsed = time.monotonic() - started
    model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    tokens = result.sequences[0, prefix:].tolist(); scores = torch.cat(result.scores, dim=0).float()
    selected = scores[torch.arange(len(tokens), device=scores.device), torch.tensor(tokens, device=scores.device)]
    norm = torch.logsumexp(scores, dim=1)
    temporary = TEMP / (row['source'] + '.activation.pt')
    with temporary.open('xb') as stream:
        torch.save(dict(scores=scores.cpu()), stream)
    raw = OUT / 'raw' / (row['source'] + '.pt')
    with raw.open('xb') as stream:
        torch.save(dict(source=row['source'], input_proof=ref, actual_input_signature=row['actual_signature'],
            model_role='original_BASE_TIME_disabled', actual_disabled_adapter_modules=144,
            tokens=tokens, eos=eos, selected_logp=(selected - norm).cpu().tolist(),
            selected_logits=selected.cpu().tolist(), log_normalizers=norm.cpu().tolist(),
            text=tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False),
            maximum_new_tokens=row['maximum_new_tokens'], generation_seconds=elapsed,
            temporary_scores=identity(temporary), human_labels_or_targets_used=False), stream)
    del result, values, gpu, scores, selected, norm
    child = subprocess.run([str(PY), '-B', str(Path(__file__).with_name('summary_goal86_cpu.py')), str(raw)],
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'),
        text=True, capture_output=True)
    if child.returncode:
        save(OUT / (row['source'] + '_CPU_failure.json'), dict(exit_code=child.returncode,
            stdout=child.stdout, stderr=child.stderr, preserve_raw_and_activation=True))
        raise RuntimeError('First BASE source-summary goal output QA failed')
    print('SUMMARY86_FIRST_BASE_GOAL', row['source'], len(tokens), elapsed, flush=True)
    return dict(raw=identity(raw), CPU=identity(raw.with_suffix('.CPU.json')),
        retirement=identity(raw.with_suffix('.retirement.json')), tokens=len(tokens), generation_seconds=elapsed)


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    accepted = read(check(lock['first_pure_text_CPU']))['accepted']
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    count = sum(p.numel() for p in model.parameters())
    if count != 8782459120:
        raise ValueError('Actual original shared BASE/TIME parameter count differs')
    model.eval(); model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    TEMP.mkdir(); (OUT / 'raw').mkdir()
    outputs = {sid: one_goal(model, processor.tokenizer, rt, ref) for sid, ref in accepted.items()}
    if len(outputs) != 2:
        raise ValueError('Actual first two-source planner control scope differs')
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Actual original BASE/TIME changed during source-goal control')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_TWO_BASE_CONTENT_GOALS_AND_CPU_PASS_NOT_TIME_QUALITY',
        outputs=outputs, original_BASE_TIME_unchanged=True, actual_model_parameters=count,
        actual_new_generations=2, first_CPU=2, new_training=0,
        peak_torch_bytes=torch.cuda.max_memory_allocated(), no_new_temporal_selection_or_package=True))


if __name__ == '__main__':
    main()
