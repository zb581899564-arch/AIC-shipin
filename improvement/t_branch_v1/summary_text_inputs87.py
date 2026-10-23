"""Freeze all machine-only source prefixes before attaching original human targets."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer

from causal_policy32 import causal_suffix
from frozen_branch46 import RUN
from summary_content85_common import generation_budget, prefix_tokens
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_text_inputs87'


def machine_prefix(sid, refs, events, tokenizer, rt):
    descriptions = []; binding = []
    if set(events) != {read(check(read(check(ref))['input']))['case_id'] for ref in refs}:
        raise ValueError('Source event pool incomplete or assigned to another source')
    for ref in refs:
        meta = read(check(read(check(ref))['input'])); case = meta['case_id']
        output = events[case]; proof = read(check(output['CPU']))
        if proof['raw'] != output['raw'] or proof['state'] != 'PASS_FIRST_FULL_EVENT_GREEDY_TOKEN_AND_VOCABULARY_CPU':
            raise ValueError('First fit event output/independent proof binding differs')
        raw = torch.load(check(output['raw']), map_location='cpu', weights_only=True)
        if (raw['case'] != case or raw['source'] != sid or raw['model_role'] != 'original_BASE_TIME_disabled'
                or raw['original_interval_exact'] != [meta['window_start'], meta['window_end']]
                or not raw['text'].strip()):
            raise ValueError('Machine event does not bind this actual original native excerpt')
        descriptions.append(raw['text']); binding.append(dict(original_CPU=ref, event=output))
    ids = prefix_tokens(tokenizer, descriptions)
    values = dict(input_ids=torch.tensor([ids], dtype=torch.long),
                  attention_mask=torch.ones((1, len(ids)), dtype=torch.long))
    path = OUT / (sid + '_prefix.npz')
    with path.open('xb') as stream:
        np.savez_compressed(stream, **{k: v.numpy() for k, v in values.items()})
    with np.load(path, allow_pickle=False) as data:
        if any(not np.array_equal(data[k], values[k].numpy()) for k in data.files):
            raise ValueError('Actual source-summary text serialization differs')
    return dict(prefix=identity(path), actual_signature=rt.tensor_signature(values),
        original_native_windows=len(refs), maximum_new_tokens=generation_budget(len(refs)),
        full_event_binding=binding, human_target_or_reference_not_in_prefix=True), values['input_ids']


def main():
    OUT.mkdir(); torch.set_num_threads(2); rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    captions = read(ROOT / 'summary_caption85/GPU_completion.json')
    visual = read(ROOT / 'summary_inputs84/completion.json')['accepted']
    prefixes, values = {}, {}
    for sid in sorted(visual):
        prefixes[sid], values[sid] = machine_prefix(sid, visual[sid], captions['outputs'][sid], tokenizer, rt)
    save(OUT / 'all_machine_prefixes_before_targets.json', prefixes)
    target_gate = read(ROOT / 'summary_contract85/completion.json')
    targets = read(check(target_gate['whole_target_tokens']))['source_rows']
    source_rows = {row['source']['sid']: row['source'] for row in read(ROOT / 'summary_content81/completion.json')['planned']}
    accepted, total = {}, 0
    for sid, rows in targets.items():
        if sid not in prefixes or source_rows[sid]['role'] != 'fit':
            raise ValueError('A target belongs to a non-fit or unprepared source')
        accepted[sid] = []
        for row in rows:
            suffix = causal_suffix(values[sid], row['target_ids'])
            if suffix['input_ids'].shape[1] > 16384 or len(row['target_ids']) > prefixes[sid]['maximum_new_tokens']:
                raise ValueError('Complete original target/context cannot fit; never truncate')
            tf_values = {k: suffix[k] for k in ['input_ids', 'attention_mask', 'targets']}
            accepted[sid].append(dict(original_row=row['original_row'], target_ids=row['target_ids'],
                target_sha256=row['target_sha256'], actual_causal_signature=rt.tensor_signature(tf_values),
                logits_to_keep=suffix['logits_to_keep'], causal_positions=suffix['causal_positions'],
                global_publisher_source_reviewer_weight=row['equal_publisher_source_reviewer_weight']))
            total += 1
    if total != 86 or len(accepted) != 9 or torch.cuda.is_initialized():
        raise ValueError('Actual complete86 target/9fit source or CPU role denominator differs')
    save(OUT / 'completion.json', dict(state='PASS_FIRST_ALL86_SOURCE_CONTENT_CAUSAL_INPUTS',
        source_prefixes=prefixes, source_targets=accepted,
        original_sources=source_rows, actual_review_count=86, sources=9, publisher_groups=5,
        no_target_in_inference_prefix=True, original_target_token_QA_adopted=target_gate['whole_target_tokens'],
        all_machine_prefixes_frozen_before_targets=identity(OUT / 'all_machine_prefixes_before_targets.json'),
        actual_new8B_calls=0, training_admitted=False))


if __name__ == '__main__':
    main()
