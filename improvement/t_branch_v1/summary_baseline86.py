"""First paid phase: actual later BASE summary controls and source-goal cost."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import traceback

import numpy as np
import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from event_table71 import event_table
from frozen_branch46 import RUN
from prompt_contract13 import prompt_binding
from summary_content85_common import SUMMARY_QUESTION, generation_budget, prefix_tokens
from event_memory69_common import quoted
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_baseline86'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_first_two_BASE_source_content_goals_20261022_v86'


def first_text_inputs(rt, protocol):
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    adopted = read(ROOT / 'event_adoption73/completion.json')
    outputs = read(check(adopted['accepted_events']))['outputs']
    if set(sources) != set(protocol['development_sources']):
        raise ValueError('Actual full development source identities differ')
    folder = OUT / 'prefixes'; folder.mkdir(); accepted = {}
    for sid in sorted(sources):
        source = sources[sid]
        table, binding = event_table(source, outputs[sid])
        events = [row['quoted_unverified_event'] for row in table]
        ids = prefix_tokens(tokenizer, events); budget = generation_budget(len(table))
        if len(ids) + budget > 16384:
            raise ValueError('Whole source text/response budget exceeds context; never truncate')
        value = torch.tensor([ids], dtype=torch.long)
        values = dict(input_ids=value, attention_mask=torch.ones_like(value))
        expected = SUMMARY_QUESTION + quoted(events)
        prompt = prompt_binding(tokenizer, value, dict(prompt_sha256=hashlib.sha256(expected.encode()).hexdigest()),
                                expected, 'SOURCE_CONTENT_SUMMARY')
        path = folder / (sid + '.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, input_ids=value.numpy(), attention_mask=values['attention_mask'].numpy())
        with np.load(path, allow_pickle=False) as data:
            if any(not np.array_equal(data[k], values[k].numpy()) for k in data.files):
                raise ValueError('First pure text source-summary serialization differs')
        proof = folder / (sid + '.CPU.json')
        save(proof, dict(source=sid, text=identity(path), actual_signature=rt.tensor_signature(values),
            actual_prompt_binding=prompt, native_windows=len(table), maximum_new_tokens=budget,
            all_original_events_and_CPU_adopted=binding, labels_or_human_descriptions_read=False,
            no_old8B_or_independent_output_replay=True))
        accepted[sid] = identity(proof)
    if torch.cuda.is_initialized():
        raise ValueError('Actual first input preparation initialized CUDA')
    save(OUT / 'CPU_completion.json', dict(state='FIRST_TWO_PURE_TEXT_SOURCE_GOAL_INPUTS_PASS', accepted=accepted))


def main():
    OUT.mkdir(); protocol = read(Path(__file__).with_name('summary_protocol85.json'))
    contract = read(ROOT / 'summary_contract85/completion.json')
    if contract['state'] != 'PASS_FIRST_SUMMARY_TARGET_AND_FRESH_ROLE_CPU_CONTRACT':
        raise ValueError('Actual new whole-target and zero-B role CPU gate absent')
    if protocol['Goal_already_settled_GPU_seconds'] + 300 > protocol['Goal_all_GPU_seconds_max']:
        raise ValueError('Fixed total Goal budget cannot fund first control phase')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    if shutil.disk_usage(ROOT).free < 10000000 or shutil.disk_usage('/dev/shm').free < 151936 * 4 * 2048:
        raise RuntimeError('Specific first raw/proof/full-score temporary capacity insufficient')
    rt = runtime(); first_text_inputs(rt, protocol)
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU compute present; keep inputs, no automatic collision')
    code = {name: identity(Path(__file__).with_name(name)) for name in [
        'summary_protocol85.json', 'summary_content85_common.py', 'summary_baseline86.py',
        'summary_goal86_gpu.py', 'summary_goal86_cpu.py', 'summary_score86.py',
        't_io.py', 't_runtime39.py', 'event_table71.py', 'development_data46.py']}
    save(OUT / 'source_input_lock.json', dict(code=code,
        protocol=identity(Path(__file__).with_name('summary_protocol85.json')),
        first_pure_text_CPU=identity(OUT / 'CPU_completion.json'),
        target_contract=identity(ROOT / 'summary_contract85/completion.json'),
        adopted_event_completion=identity(ROOT / 'event_adoption73/completion.json'),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        wrapper=identity(WRAPPER), actual_GPU_apps_at_admission=apps, new_training_admitted=False))
    command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '300',
        '--planned-output-bytes', '10000000', '--capacity-reason',
        'Only2 first pure-text source-summary controls; adopt50 complete original events; new projected raw/proofs and one temporary full-vocabulary activation, no new image/model/download',
        '--queue-seconds', '0', '--', str(PY), '-B', '-u', str(Path(__file__).with_name('summary_goal86_gpu.py'))]
    with (OUT / 'GPU.log').open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(__import__('os').environ, CUDA_VISIBLE_DEVICES='0', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'))
        save(OUT / 'GPU_launch.json', dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / 'GPU_terminal.json', dict(exit_code=status))
    record = read(RUN / 'controller' / (JOB + '.resource.json'))
    rows = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if status or record['status'] != 'completed' or record['exit_code'] != 0 or [r for r in rows if r.get('name') == JOB] != [record]:
        raise ValueError('First two control natural GPU terminal/unique ledger differs; keep all successes')
    result = read(OUT / 'GPU_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], first_new_BASE_goals=2, first_CPU=2,
        actual_outputs=identity(OUT / 'GPU_completion.json'), GPU_seconds=record['charged_seconds'],
        all_goal_GPU_seconds=protocol['Goal_already_settled_GPU_seconds'] + record['charged_seconds'],
        profile_development_GPU_seconds=record['charged_seconds'],
        observed_per_source={sid: {k: row[k] for k in ['tokens', 'generation_seconds']} for sid, row in result['outputs'].items()},
        no_temporal_quality_or_new_training_or_package=True,
        next='Adopt these exact2 BASE goals later. Inspect measured goal cost and all217 AV input terminal before first fit captions; no auto training or426.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_and_cost=True))
        raise
