"""Explicit CPU adoption of50 completed outputs after a post-generation PEFT flag failure."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import inspect
import json
from pathlib import Path
import traceback

import torch

from development_data46 import development_sources
from event_memory69_common import CAPTION, INPUT
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'event_adoption73'
JOB = 'T_native_local_AV_event_memory50_20261022_v70'


def lifecycle():
    from peft import LoraConfig, get_peft_model

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.q_proj = torch.nn.Linear(8, 8, bias=False)

        def forward(self, value):
            return self.q_proj(value)

    torch.manual_seed(7319)
    model = get_peft_model(Tiny(), LoraConfig(r=2, lora_alpha=4, target_modules=['q_proj'], bias='none'))
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    before = {name: p.detach().clone() for name, p in model.named_parameters()}
    with model.disable_adapter(), torch.inference_mode():
        model(torch.ones(2, 8))
    flags = {name: p.requires_grad for name, p in model.named_parameters()}
    unchanged = all(torch.equal(before[name], p) for name, p in model.named_parameters())
    if not unchanged or not any(flags.values()) or any(p.grad is not None for p in model.parameters()):
        raise ValueError('Actual installed PEFT did not reproduce flag-only context restoration')
    for p in model.parameters():
        p.requires_grad_(False)
    if model.active_adapter != 'default' or any(p.requires_grad for p in model.parameters()):
        raise ValueError('Explicit inference-freeze mode restoration failed')
    return dict(state='PASS_ACTUAL_PEFT_DISABLE_CONTEXT_MARKER_REGRESSION',
        all_tiny_weights_bit_equal=True, no_gradients_or_optimizer=True,
        context_exit_restored_trainable_flags=flags, explicit_freeze_restores_mode=True,
        actual_original8B_postexit_flags_not_captured=True, no_original_model_forward=True)


def terminal_evidence(rt):
    record_path = RUN / 'controller' / (JOB + '.resource.json')
    record = read(record_path)
    rows = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status'] != 'failed' or record['exit_code'] != 1 or [x for x in rows if x.get('name') == JOB] != [record]:
        raise ValueError('Expected exact original natural failure/unique fee absent')
    log_path = RUN / 'controller' / (JOB + '.log'); log = log_path.read_text()
    expected = 'ValueError: trained B adapter disabled or a parameter trainable'
    if (expected not in log or 'line 35, in adapter_identity' not in log
            or log.count('EVENT70_FIRST_CAPTION_AND_CPU_PASS ') != 50):
        raise ValueError('Different original failure cannot use this explicit CPU adoption')
    source = inspect.getsource(rt.b_engine.adapter_identity)
    marker = "require(model.active_adapter == 'default' and not any(p.requires_grad for p in model.parameters()),"
    if not (source.index('torch.equal(value, expected.to(dtype=value.dtype))') < source.index(marker)):
        raise ValueError('Original error no longer proves preceding tensor comparisons completed')
    gpu_source = (ROOT / 'code/event_caption70_gpu.py').read_text()
    check(read(CAPTION / 'source_input_lock.json')['code']['event_caption70_gpu.py'])
    if "rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config)" not in gpu_source:
        raise ValueError('Original short-circuit control flow cannot prove base hash equality')
    return record, dict(resource=identity(record_path), worker_log=identity(log_path),
        engine_code=identity(Path(rt.b_engine.__file__)),
        original_natural_GPU_state_preserved='failed/exit1',
        evidence='Reached the final adapter mode guard after canonical base hash equality and all288 saved/actual tensor comparisons; failure was the mode/trainable-marker guard, not a weight comparison',
        base_and_adapter_byte_check_control_flow=True,
        no_fabricated_GPU_completion_or_original_postexit_mode_snapshot=True)


def adopt_outputs():
    inputs = read(INPUT / 'completion.json')['accepted']
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    outputs = {}; counted = 0
    for sid, source in sources.items():
        outputs[sid] = {}
        for case in source.cases:
            raw_path = CAPTION / 'raw' / (case.name + '.pt')
            proof_path = raw_path.with_suffix('.CPU.json'); retired_path = raw_path.with_suffix('.retirement.json')
            raw = torch.load(raw_path, map_location='cpu', weights_only=True)
            proof, retired = read(proof_path), read(retired_path)
            if (raw['case'] != case.name or raw['source'] != sid
                    or raw['model_role'] != 'original_BASE_TIME_disabled' or raw['actual_disabled_adapter_modules'] != 144
                    or raw['input_proof'] != inputs[sid][case.name]
                    or proof['state'] != 'PASS_FIRST_FULL_EVENT_GREEDY_TOKEN_AND_VOCABULARY_CPU'
                    or proof['raw'] != identity(raw_path) or retired['first_CPU_proof'] != identity(proof_path)):
                raise ValueError('A successful output/role/first CPU binding differs; never rerun it')
            outputs[sid][case.name] = dict(raw=identity(raw_path), CPU=identity(proof_path), retirement=identity(retired_path))
            counted += 1
    if counted != 50 or len(list((CAPTION / 'raw').glob('*.pt'))) != 50:
        raise ValueError('Original complete50 source-window output inventory differs')
    return outputs


def main():
    OUT.mkdir(); torch.set_num_threads(2); torch.set_num_interop_threads(1)
    rt = runtime()
    record, evidence = terminal_evidence(rt)
    save(OUT / 'PEFT_lifecycle_CPU.json', lifecycle())
    outputs = adopt_outputs()
    save(OUT / 'accepted_event_outputs.json', dict(outputs=outputs,
        all50_original_generations_and_first_CPU_proofs_adopted=True,
        original_GPU_status_remains_FAILED=True, byte_check_control_flow=evidence,
        first_marker_lifecycle_CPU=identity(OUT / 'PEFT_lifecycle_CPU.json'),
        new_model_or_QA_replay=0, no_factual_or_highlight_quality_claim=True))
    prior = read(ROOT / 'description_score67/completion.json')
    save(OUT / 'completion.json', dict(state='ADOPTED_ALL50_EVENT_OUTPUTS_AFTER_FLAG_ONLY_FINAL_CHECK_FAILURE',
        accepted_events=identity(OUT / 'accepted_event_outputs.json'), original_failure=evidence,
        original_model_generations_adopted=50, original_first_CPU_proofs_adopted=50,
        new_model_or_original_QA_replays=0, first_new_CPU_lifecycle_test=1,
        GPU_seconds=record['charged_seconds'], all_goal_GPU_seconds=prior['all_goal_GPU_seconds'] + record['charged_seconds'],
        original_GPU_state='failed/exit1', original_failure_and_fees_retained=True,
        original_weight_byte_checks_proven_by_actual_error_control_flow=True,
        original_postexit_mode_flags_unknown=True, original40_47_and40_48_unchanged=True,
        no_selection_quality_or_production_admission=True,
        next='Original event memory is complete and adopted without replay. Proceed only to registered first native memory/control CPU contract; no automatic candidate claim'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
