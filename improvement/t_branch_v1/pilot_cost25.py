"""Exactly four first original-TIME controls; measured cost, never window quality claims."""
import os
from pathlib import Path
import subprocess
import sys
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'pilot_cost25'
CODE = Path(__file__).parent
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_first_original_TIME_cost4_20261022_v25'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import legacy_runtime


def gpu():
    import torch
    rt = legacy_runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from coarse_call25 import generate_case
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if (loaded['logical_parameters'] != 8782459120 or
            loaded['base']['sha256'] != '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59' or
            loaded['adapter']['sha256'] != '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'):
        raise ValueError('Frozen original TIME identity differs')
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    save(OUT / 'model_identity.json', loaded)
    folder = OUT / 'outputs'
    folder.mkdir()
    refs = read(ROOT / 'pilot_remaining24/completion.json')['accepted']
    outputs = [generate_case(model, processor, rt, read(check(ref))['original_CPU'], folder) for ref in refs]
    if (rt.b_engine.frozen_identity(model, config) != loaded['base'] or
            rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Frozen original TIME changed')
    save(OUT / 'gpu_completion.json', dict(state='FOUR_FIRST_ORIGINAL_TIME_COST_CONTROLS_COMPLETE', outputs=outputs,
        first_calls=4, actual_parameters=loaded['logical_parameters'], updates=0,
        torch_peak_bytes=torch.cuda.max_memory_allocated(), no_quality_metric_or_training=True))


def review():
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import torch
    from transformers import AutoTokenizer
    rt = legacy_runtime()
    from coarse_call25 import load_case
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    from fractions import Fraction
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    candidates = ascii_token_candidates(tokenizer)
    records = []
    for ref in read(OUT / 'gpu_completion.json')['outputs']:
        row = read(check(ref))
        raw = read(check(row['raw']))
        _, meta, values, _ = load_case(row['CPU'], rt, tokenizer)
        if int(values['input_ids'].shape[1]) != raw['prefix']:
            raise ValueError('Independent input/prefix denominator differs')
        grammar = make_prefix_constraint(tokenizer, raw['prefix'], Fraction(row['source_end']) - Fraction(row['source_start']),
            candidate_token_ids=candidates, eos_token_ids=raw['eos'], allow_empty=True)
        grammar.assert_complete(torch.tensor(raw['token_ids'], dtype=torch.long))
        text = tokenizer.decode(raw['token_ids'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
        segments, errors, _ = rt.parse_segments(text, Fraction(row['source_end']) - Fraction(row['source_start']), allow_empty=True)
        if errors or segments != row['segments'] or text != raw['raw']:
            raise ValueError('Independent grammar/parser replay differs')
        records.append(dict(case=meta['case_id'], seconds=raw['generation_seconds'],
                            input_tokens=raw['prefix'], output_tokens=len(raw['token_ids']), status=row['status']))
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS', cases=records,
        labels_read=False, no_whole_source_quality_claim=True, CUDA_initialized=torch.cuda.is_initialized()))


def run_child(mode, wrapper=False):
    command = [str(PY), '-B', '-u', str(CODE / 'pilot_cost25.py'), mode]
    if wrapper:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '300',
            '--planned-output-bytes', '2000000', '--capacity-reason',
            'Four first original TIME controls from accepted profiles, permanent adoption into fixed97 pool; no training or label use',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (mode + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if wrapper else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (mode + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        code = process.wait()
    save(OUT / (mode + '_terminal.json'), dict(exit_code=code))
    if code:
        raise RuntimeError('Actual first cost stage failed: ' + mode)


def main():
    OUT.mkdir()
    if read(ROOT / 'pilot_remaining24/completion.json')['state'] != 'FIRST_FOUR_POLICY_COST_INPUTS_COMPLETE':
        raise ValueError('Actual four input acceptance missing')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('Protect external GPU compute; no first-cost launch')
    save(OUT / 'registration.json', dict(first_original_control_calls=4, max_GPU_seconds=300,
        original_cohort=identity(ROOT / 'pilot_profile21/registration.json'),
        accepted_inputs=identity(ROOT / 'pilot_remaining24/completion.json'),
        resource=dict(apps=apps, GPU=subprocess.check_output(['nvidia-smi'], text=True),
                      RAM=subprocess.check_output(['free', '-b'], text=True)),
        no_labels_training_or_quality_selection=True, protected40_47_unchanged=True))
    names = ['pilot_cost25.py', 'coarse_call25.py', 'prompt_contract13.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        registration=identity(OUT / 'registration.json'), wrapper=identity(WRAPPER)))
    run_child('gpu', True)
    run_child('review')
    import json
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == JOB] != [resource]:
        raise ValueError('Natural GPU completion/unique cost ledger differs')
    save(OUT / 'completion.json', dict(state='FOUR_ORIGINAL_CONTROL_COSTS_ACCEPTED', GPU_seconds=resource['charged_seconds'],
        independent_CPU=identity(OUT / 'independent_CPU_audit.json'), first_model_calls=4,
        training_updates=0, full_source_coverage_not_yet_complete=True))


if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            main()
        elif sys.argv[1:] == ['gpu']:
            gpu()
        elif sys.argv[1:] == ['review']:
            review()
        else:
            raise ValueError('Only explicit first-cost modes allowed')
    except Exception:
        if OUT.exists():
            path = OUT / ('failure_' + (sys.argv[1] if len(sys.argv) == 2 else 'controller') + '.json')
            save(path, dict(traceback=traceback.format_exc(), preserve_every_success=True))
        raise
