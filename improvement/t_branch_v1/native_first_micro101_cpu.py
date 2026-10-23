"""First new greedy/gradient recovery audit and actual complete-scope cost bound."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from joint_data44 import Case, Source
from native_audit100 import audit
from native_sets import NativeTimeline
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_first_micro101'


def projection(raw):
    control = read(ROOT / 'native_action_control100/completion.json')
    outputs = read(check(control['actual_outputs']))
    seconds = [read(check(ref))['seconds'] for ref in outputs['physical_raw'].values()]
    own = read(check(read(check(raw['actual_greedy']))['raw']))['seconds']
    input_overhead = max(0., raw['greedy_wall_seconds'] - own)
    dev_rate = max(raw['greedy_wall_seconds'], max(seconds) + input_overhead)
    fixed_overhead = max(60., control['GPU_seconds'] - math.fsum(seconds))
    return dict(remaining_micro_cases=216, remaining_final_dev_calls=150,
        observed_first_micro_seconds_excluding_first_CPU=raw['first_micro_seconds_excluding_one_off_CPU'],
        observed_initial_control_max_model_seconds=max(seconds), projected_dev_per_case_seconds=dev_rate,
        conservative_remaining_GPU_seconds=216 * raw['first_micro_seconds_excluding_one_off_CPU']
            + 150 * dev_rate + fixed_overhead + 5 * (raw['gradient_persistence_seconds'] + 2),
        one_off_first_CPU_not_repeated=True, no_time_or_quality_guarantee=True)


def main():
    torch.set_num_threads(2); rt = runtime()
    raw = read(OUT / 'GPU_completion.json'); target = raw['target_binding']
    data = read(ROOT / 'native_action_loss99/completion.json')
    sid = raw['cursor']['source']; item = data['sources'][sid]
    source = Source(sid, [], NativeTimeline.from_clock(read(check(item['source']['clock']))), [], {})
    meta = read(check(read(check(target['original_CPU']))['input']))
    case = Case(target['case'], target['original_CPU'], meta, {}, {})
    code = read(ROOT / 'native_action_contract98/completion.json')['actual_token_codec']
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    folder = OUT / 'first_greedy_CPU'; folder.mkdir()
    _, proof = audit(raw['actual_greedy'], source, case, target['actual_input_CPU'], code, tokenizer, folder, {})
    gradient = torch.load(check(raw['exact_successful_gradient']['file']), map_location='cpu', weights_only=True)
    if gradient['cursor'] != raw['cursor'] or gradient['publisher_checkpoint'] != raw['initial_actor_optimizer']:
        raise ValueError('First exact gradient does not bind its actual source/case/initial optimizer')
    values = gradient['gradients']
    if (len(values) != 288 or sum(v.numel() for v in values.values()) != 15335424
            or any(('.lora_A.actor.' not in n and '.lora_B.actor.' not in n)
                or '.visual.' in n or v.dtype != torch.float32 or not torch.isfinite(v).all()
                for n, v in values.items())):
        raise ValueError('First saved native gradient inventory/role/dtype invalid')
    norm = math.sqrt(math.fsum(float(v.double().square().sum()) for v in values.values()))
    if not math.isclose(norm, raw['exact_successful_gradient']['norm_float64'], abs_tol=1e-7, rel_tol=1e-7):
        raise ValueError('Independent first native accumulated gradient norm differs')
    checkpoint = torch.load(check(raw['initial_actor_optimizer']), map_location='cpu', weights_only=True)
    normalized = {n.replace('.lora_A.actor.', '.lora_A.').replace('.lora_B.actor.', '.lora_B.') for n in values}
    if checkpoint['completed_episode'] != 0 or normalized != set(checkpoint['actor']):
        raise ValueError('Exact recovery actor/optimizer role or update cursor differs')
    if torch.cuda.is_initialized() or raw['optimizer_updates'] != 0:
        raise ValueError('First cost micro must not claim a completed publisher update')
    save(OUT / 'CPU_completion.json', dict(state='FIRST_NATIVE_MICRO_GRADIENT_RECOVERY_AND_COST_CPU_PASS',
        actual_greedy_CPU=proof, first_full_teacher_CPU=raw['first_independent_TF_CPU'],
        gradient_tensors=288, gradient_parameters=15335424, gradient_norm_FP64=norm,
        exact_initial_actor_optimizer=raw['initial_actor_optimizer'],
        exact_gradient_and_RNG=raw['exact_successful_gradient'], actual_optimizer_updates=0,
        actual_greedy_calls=1, actual_teacher_backwards=1, cost_projection=projection(raw),
        complete217_scope_not_reduced=True, no_model_quality_or_package_admission=True,
        actual_parameters=8869330010, next='Use actual remaining5600 minus100/101 fees; if complete216micro+5publisher updates+150dev fits, explicit restore/adopt this micro, never re-run it.'))


if __name__ == '__main__':
    main()
