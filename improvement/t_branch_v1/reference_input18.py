"""Correct the task prefix, without decoding or processing successful video inputs again."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import hashlib
from pathlib import Path
import sys
import traceback

import numpy as np
import torch
from transformers import AutoTokenizer

from prompt_contract13 import prompt_binding
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'reference_input18'
OLD = WORK / 'general_highlight_supervision_20261021_v1/baseline_bridge57'
sys.path.insert(0, str(OLD.parent / 'code'))
from baseline_bridge57_common import RUN, legacy_runtime, verify_modules


def corrected_case(row, tokenizer, rt, contract, protocol):
    old = read(check(row['CPU']))
    request = read(check(row['request']))
    expected = protocol.verify_prompt(request, contract)
    if request['prompt'] != expected:
        raise ValueError('Stored declared task is not the original frozen VERIFY prompt')
    if old['detail']['prompt_sha256'] != hashlib.sha256(rt.EMPTY_PROMPT.encode()).hexdigest():
        raise ValueError('Expected independently verified wrong-prefix cache is absent')
    with np.load(check(old['encoded']), allow_pickle=False) as archive:
        values = {key: torch.from_numpy(archive[key].copy()) for key in archive.files}
    if set(values) != {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'}:
        raise ValueError('Unregistered input tensors need an explicit new correction protocol')
    if rt.tensor_signature(values) != old['detail']['tensor_signature']:
        raise ValueError('Adopted old tensor signature changed')
    original = values['input_ids'][0].tolist()
    text = tokenizer.decode(original, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if tokenizer.encode(text, add_special_tokens=False) != original:
        raise ValueError('Original actual prefix does not exactly roundtrip; do not guess a rewrite')
    if text.count(rt.EMPTY_PROMPT) != 1 or not torch.all(values['attention_mask'] == 1):
        raise ValueError('Ambiguous old prompt occurrence or attention mask')
    replacement = tokenizer.encode(text.replace(rt.EMPTY_PROMPT, expected), add_special_tokens=False)
    video_token = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    last_video = max(i for i, value in enumerate(original) if value == video_token)
    if original[:last_video + 1] != replacement[:last_video + 1] or len(replacement) > 16384:
        raise ValueError('Correction altered visual/timestamp prefix or exceeds native token budget')
    folder = OUT / request['request_id']
    folder.mkdir()
    values['input_ids'] = torch.tensor([replacement], dtype=torch.long)
    values['attention_mask'] = torch.ones_like(values['input_ids'])
    text_path = folder / 'encoded_text.npz'
    with text_path.open('xb') as stream:
        np.savez_compressed(stream, input_ids=values['input_ids'].numpy(),
                            attention_mask=values['attention_mask'].numpy())
    detail = dict(old['detail'], prompt_sha256=hashlib.sha256(expected.encode()).hexdigest(),
                  input_tokens=len(replacement), tensor_signature=rt.tensor_signature(values))
    proof = prompt_binding(tokenizer, values['input_ids'], detail, expected, 'VERIFY', rt.EMPTY_PROMPT)
    record = dict(input=old['input'], adopted_multimodal=old['encoded'],
                  encoded_text=identity(text_path), detail=detail,
                  non_tensor_inputs=old['non_tensor_inputs'], original_CPU=row['CPU'],
                  prompt_binding=proof, original_prefix_roundtrip_exact=True,
                  video_and_timestamp_prefix_tokens_unchanged=True,
                  no_new_decode_RGB_processor_or_video_tensor_copy=True,
                  first_distinct_correct_VERIFY_task=True)
    save(folder / 'CPU_acceptance.json', record)
    print('CORRECT_VERIFY_PREFIX18', request['request_id'], len(replacement), flush=True)
    return dict(event=row['event'], request=row['request'], CPU=identity(folder / 'CPU_acceptance.json'))


def main():
    OUT.mkdir()
    rt = legacy_runtime()
    contract, _, protocol = verify_modules()
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
    old = read(OLD / 'verify_CPU_completion.json')
    if len(old['cases']) != 14 or read(ROOT / 'cpu_prompt13/completion.json')['state'] != 'PASS':
        raise ValueError('Expected original cases and new prompt guard missing')
    save(OUT / 'registration.json', dict(
        purpose='First correct candidate-specific VERIFY text for14 existing external cases',
        old_failed_GPU_and_CPU_adoption_preserved=True,
        old_terminal=identity(OLD / 'failure.json'), old_CPU=identity(OLD / 'verify_CPU_completion.json'),
        old_generic_prompt_sha256=hashlib.sha256(rt.EMPTY_PROMPT.encode()).hexdigest(),
        original_declared_requests_and_native_context_unchanged=True,
        original_encoding_and_video_prefix_exact_roundtrip_required=True,
        only_task_text_prefix_replaced_no_media_or_processor_replay=True,
        old74_BASE_feature_batches_adopt_only_no_model_rerun=True,
        GPU_not_started=True, protected40_47_package_unchanged=True))
    cases = [corrected_case(row, tokenizer, rt, contract, protocol) for row in old['cases']]
    if torch.cuda.is_initialized():
        raise ValueError('CPU correction initialized CUDA')
    save(OUT / 'CPU_completion.json', dict(state='PASS_FIRST_CORRECT_TASK_PREFIX14', cases=cases,
        no_GPU_or_training=True, no_old_model_or_video_input_repeated=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
