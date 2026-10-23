"""First actual source-memory/native action CPU contract; no new model calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
from fractions import Fraction
import traceback

import torch
from transformers import AutoTokenizer

from coarse_call25 import load_case
from development_data46 import development_sources
from event_native71 import bindings, first_binding_contract
from event_table71 import ARMS, event_table, half_shift, prepare_prefix
from frozen_branch46 import RUN
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'event_inputs71'


def main():
    OUT.mkdir(); torch.set_num_threads(2); torch.set_num_interop_threads(1)
    previous = read(ROOT / 'event_adoption73/completion.json')
    if previous['state'] != 'ADOPTED_ALL50_EVENT_OUTPUTS_AFTER_FLAG_ONLY_FINAL_CHECK_FAILURE':
        raise ValueError('Actual complete source event memory must pass first')
    rt = runtime()
    original_helpers = (rt.b_engine.require, rt.b_engine.sha)
    native_contract = first_binding_contract()
    if (rt.b_engine.require, rt.b_engine.sha) != original_helpers:
        raise ValueError('Native grammar import rebound original model helpers')
    protocol = read(ROOT / 'code/event_memory_protocol69.json')
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    if set(sources) != set(protocol['development_sources']):
        raise ValueError('Registered source set differs; no new confirmation exposure')
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    event_gpu = read(check(previous['accepted_events']))
    native, _ = bindings(); tables, inputs, exact_native = {}, {}, {}
    for sid, source in sources.items():
        rows, binding = event_table(source, event_gpu['outputs'][sid]); shifted = half_shift(rows)
        table_path = OUT / (sid + '_memory.json')
        save(table_path, dict(correct=rows, shifted=shifted, original_native_binding=binding,
                             labels_or_human_descriptions_used=False))
        tables[sid] = identity(table_path)
        inputs[sid] = {arm: {} for arm in ARMS}
        exact_native[sid] = {}
        for case in source.cases:
            # Only a read of already accepted values, no decode or processor.
            case.values = load_case(case.CPU, rt, tokenizer)[2]
            inputs[sid][ARMS[0]][case.name] = dict(original_CPU_adopted=case.CPU)
            for arm, content in zip(ARMS[1:], [rows, shifted]):
                inputs[sid][arm][case.name] = dict(first_event_text_CPU=prepare_prefix(case, content, tokenizer, rt,
                    OUT / (arm + '_' + case.name)))
            start = Fraction(case.meta['window_start'])
            duration = Fraction(case.meta['window_end']) - start
            rule = native.NativeSegmentsGrammar(duration, source.timeline.points, start)
            if not rule.points or not rule.allow_empty:
                raise ValueError('Actual original window lacks native action domain or legal empty')
            exact_native[sid][case.name] = dict(native_points=len(rule.points), start=str(start), duration=str(duration))
            case.values = {}
            print('EVENT71_FIRST_MEMORY_AND_NATIVE_CPU', case.name, flush=True)
    if torch.cuda.is_initialized():
        raise ValueError('First source-memory CPU preparation initialized CUDA')
    save(OUT / 'completion.json', dict(state='FIRST_ALL150_NATIVE_MEMORY_SELECTOR_INPUTS_PASS',
        native_grammar_contract=native_contract, source_tables=tables, inputs=inputs,
        actual_native_domains=exact_native, first_new_text_prefixes=100,
        original50_video_inputs_adopted=True, first_selector_calls_max=150,
        no_training_or_new_model_calls=True, fresh_confirmation_read=False,
        no_factual_or_highlight_quality_claim=True, code={n: identity(Path(__file__).parent / n)
            for n in ['event_prepare71.py', 'event_native71.py', 'event_table71.py']}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
