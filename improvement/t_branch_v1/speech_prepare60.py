"""First new speech output QA; adopt identical old VERIFY input AND result."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from transformers import AutoTokenizer

from frozen_branch46 import RUN
from development_data46 import development_sources
from development_prepare55 import normalized_output
from development_verify46 import candidate_request, prepare
from joint_audit45 import trajectory
from speech_task60 import ARMS, OUT, values
from t_io import ROOT, check, identity, read, save
from t_runtime39 import grammar, runtime


def main():
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = development_sources(rt, tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'))
    inputs = read(ROOT / 'speech_inputs59/completion.json')['accepted']
    outputs = read(OUT / 'coarse_GPU_completion.json')['outputs']
    old_cpu = read(ROOT / 'development_remaining55/verify_CPU_completion.json')
    old_gpu = read(ROOT / 'development_remaining55/verify_GPU_completion.json')['outputs']
    candidates = grammar().ascii_token_candidates(tokenizer)
    replay = OUT / 'coarse_replay'; replay.mkdir()
    folder = OUT / 'verify_CPU'; folder.mkdir()
    tasks, policies, adopted, first = {}, {}, {}, []
    for sid, source in sources.items():
        policies[sid] = {}
        for arm in ARMS:
            policies[sid][arm] = []
            for case in source.cases:
                ref = outputs[sid][arm][case.name]
                if arm == 'original_correct':
                    result = read(check(ref))
                else:
                    proof = inputs[sid][arm][case.name]
                    original = read(check(ref))
                    if original['model_role'] != 'default' or original['actual_input_proof'] != proof:
                        raise ValueError('Actual speech role/input differs')
                    actual = values(case, proof, rt)
                    normalized = normalized_output(ref, actual, rt, tokenizer, candidates, replay / (arm + '_' + case.name + '.json'))
                    result, _ = trajectory(normalized, actual, source, rt, tokenizer)
                    first.append(normalized)
                for index, segment in enumerate(result['segments']):
                    event, request = candidate_request(case, source, segment, index)
                    key = request['request_id']
                    if key not in tasks:
                        if key in old_cpu['tasks']:
                            prior = old_cpu['tasks'][key]
                            if prior['event'] != event or read(check(prior['request'])) != request or read(check(prior['CPU']))['original_CPU'] != case.CPU:
                                raise ValueError('Previously successful VERIFY binding differs')
                            tasks[key] = prior; adopted[key] = old_gpu[key]
                        else:
                            tasks[key] = prepare(case, event, request, folder / key, tokenizer, rt)
                    policies[sid][arm].append(key)
    if len(first) != 100:
        raise ValueError('First new AV output set incomplete')
    save(OUT / 'verify_CPU_completion.json', dict(state='FIRST100_AV_OUTPUTS_AND_ALL_VERIFY_INPUTS_PASS',
        tasks=tasks, source_policies=policies, first100_output_QA=first, adopted_VERIFY_outputs=adopted,
        actual_missing_VERIFY_calls=len(tasks) - len(adopted), no_old_successful_QA_or_model_repeated=True,
        downstream_uses_original_correct_visual_input_no_ASR=True))


if __name__ == '__main__':
    main()
