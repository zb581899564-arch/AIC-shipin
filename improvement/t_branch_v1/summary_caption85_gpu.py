"""First217 fit-only event records and streamed first independent output QA."""
import os
from pathlib import Path
import json
import subprocess
import time
from types import SimpleNamespace

import torch

from event_memory69_common import actual_values
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_caption85'
TEMP = Path('/dev/shm/aic_T_summary_caption85')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def start_CPU():
    command = [str(PY), '-B', '-u', str(Path(__file__).with_name('summary_caption85_cpu.py'))]
    log = (OUT / 'independent_CPU_service.log').open('x')
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
        text=True, bufsize=1, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'))
    save(OUT / 'CPU_service_launch.json', dict(pid=child.pid, command=command,
        start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
    response = child.stdout.readline()
    if not response or json.loads(response).get('state') != 'READY_CPU_ONLY_FIRST_NEW85_QA':
        raise RuntimeError('First independent CPU service failed to initialize')
    return child, log


def one_event(model, tokenizer, rt, case, proof, child):
    from peft.tuners.tuners_utils import BaseTunerLayer
    values = actual_values(case, proof, tokenizer, rt)
    gpu = {key: value.cuda() if torch.is_tensor(value) else value for key, value in values.items()}
    actual = rt.tensor_signature({k: v.cpu() if torch.is_tensor(v) else v for k, v in gpu.items()})
    if actual != read(check(proof))['actual_signature']:
        raise ValueError('Actual GPU input differs from its first complete CPU acceptance')
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    started = time.monotonic(); prefix = values['input_ids'].shape[1]
    with model.disable_adapter(), torch.inference_mode():
        layers = [m for m in model.modules() if isinstance(m, BaseTunerLayer)]
        if len(layers) != 144 or any(not bool(m.disable_adapters) for m in layers):
            raise ValueError('Actual BASE perception role did not disable original TIME')
        result = model.generate(**gpu, do_sample=False, num_beams=1, repetition_penalty=1.,
            max_new_tokens=128, return_dict_in_generate=True, output_scores=True)
    # PEFT disable_adapter restores old training flags; freeze again before any
    # strict original-role identity check (the explicit cause of old70 failure).
    model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    tokens = result.sequences[0, prefix:].tolist()
    scores = torch.cat(result.scores, dim=0).float()
    selected = scores[torch.arange(len(tokens), device=scores.device), torch.tensor(tokens, device=scores.device)]
    normalizer = torch.logsumexp(scores, dim=1); top = scores.topk(2, dim=1)
    temporary = TEMP / (case.name + '.activation.pt')
    with temporary.open('xb') as stream:
        torch.save(dict(scores=scores.cpu()), stream)
    raw = OUT / 'raw' / (case.name + '.pt')
    with raw.open('xb') as stream:
        torch.save(dict(case=case.name, source=case.meta['source_name'], input_proof=proof,
            actual_input_signature=actual, model_role='original_BASE_TIME_disabled',
            actual_disabled_adapter_modules=144, tokens=tokens, eos=eos,
            text=tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False),
            selected_logits=selected.cpu().tolist(), log_normalizers=normalizer.cpu().tolist(),
            selected_logp=(selected - normalizer).cpu().tolist(), top2_values=top.values.cpu().tolist(),
            top2_ids=top.indices.cpu().tolist(), original_interval_exact=[case.meta['window_start'], case.meta['window_end']],
            temporary_scores=identity(temporary), generation_seconds=time.monotonic() - started,
            output_is_unverified_machine_observation_not_annotation=True), stream)
    del result, gpu, values, scores, selected, normalizer, top
    child.stdin.write(json.dumps(dict(raw_path=str(raw))) + '\n'); child.stdin.flush()
    reply = child.stdout.readline()
    if not reply or not json.loads(reply).get('ok'):
        save(OUT / (case.name + '_CPU_failure.json'), dict(reply=reply, preserve_raw_and_activation=True))
        raise RuntimeError('First actual85 output CPU QA failed')
    accepted = json.loads(reply)['proof']
    if read(raw.with_suffix('.retirement.json'))['first_CPU_proof'] != accepted:
        raise ValueError('Current temporary retirement is not bound to complete first CPU QA')
    print('SUMMARY85_FIRST_EVENT_AND_CPU', case.name, len(tokens), flush=True)
    return dict(raw=identity(raw), CPU=accepted, retirement=identity(raw.with_suffix('.retirement.json')))


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    cpu = read(check(lock['complete_AV_inputs']))
    visual = read(check(cpu['original_visual']))['accepted']
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    count = sum(p.numel() for p in model.parameters())
    if count != 8782459120 or count + 98329 + 37184640 + 28043472 + 6209025 != 8853994586:
        raise ValueError('Actual original BASE/TIME and full auxiliary budget differs')
    model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    TEMP.mkdir(); (OUT / 'raw').mkdir(); child, log = start_CPU()
    outputs = {}
    with (OUT / 'accepted.jsonl').open('x') as journal:
        for sid, refs in visual.items():
            outputs[sid] = {}
            for ref in refs:
                meta = read(check(read(check(ref))['input']))
                case = SimpleNamespace(name=meta['case_id'], meta=meta, CPU=ref)
                result = one_event(model, processor.tokenizer, rt, case, cpu['accepted'][sid][case.name], child)
                outputs[sid][case.name] = result
                journal.write(json.dumps(dict(source=sid, case=case.name, result=result)) + '\n'); journal.flush()
    child.stdin.close(); status = child.wait(); log.close()
    save(OUT / 'CPU_service_terminal.json', dict(exit_code=status))
    if status or sum(map(len, outputs.values())) != 217:
        raise ValueError('Complete217 first event/independent CPU denominator differs')
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original BASE/TIME changed during first fit perception')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_ALL217_FIT_EVENTS_AND_CPU_PASS_NOT_HUMAN_LABELS',
        outputs=outputs, actual_new_generations=217, first_independent_CPU=217,
        actual_original_model_parameters=count, full_pipeline_before_summary_parameters=8853994586,
        original_weights_unchanged=True, new_training=0, quality_admission=False,
        peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
