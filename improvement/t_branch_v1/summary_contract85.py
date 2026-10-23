"""Actual installed-PEFT zero-B role and complete original content-token CPU gates."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import hashlib
import json
from pathlib import Path
import traceback

import torch
from peft import LoraConfig, get_peft_model, get_peft_model_state_dict, set_peft_model_state_dict
from transformers import AutoTokenizer

from actor_contract33 import TinyAttention
from actor_roles33 import activate_actor
from frozen_branch46 import RUN
from summary_content85_common import all_review_weights, generation_budget, prefix_tokens, target_content
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_contract85'


def fresh_role_contract():
    torch.manual_seed(7385)
    config = LoraConfig(r=2, lora_alpha=4, target_modules=['q_proj', 'v_proj'], lora_dropout=0., bias='none')
    model = get_peft_model(TinyAttention().to(torch.bfloat16), config)
    with torch.no_grad():
        for name, p in model.named_parameters():
            if 'lora_' in name:
                p.fill_(.012345)
    before = {name: p.detach().clone() for name, p in model.named_parameters()}
    model.add_adapter('summary', config)
    trainable = activate_actor(model, 'summary')
    for _, p in trainable:
        p.data = p.data.float()
    values = torch.arange(12, dtype=torch.bfloat16).reshape(3, 4) / 10
    with model.disable_adapter(), torch.inference_mode():
        expected = model(values).clone()
    trainable = activate_actor(model, 'summary'); model.eval()
    actual = model(values)
    if not torch.equal(actual.detach(), expected):
        raise ValueError('Fresh zero-B summary is not actual original BASE')
    loss = actual.float().square().mean(); loss.backward()
    if not any(p.grad is not None and torch.count_nonzero(p.grad) for _, p in trainable):
        raise ValueError('Fresh summary has no actual gradient')
    if any(p.grad is not None for name, p in model.named_parameters() if '.summary.' not in name):
        raise ValueError('Summary backward touched original BASE/TIME')
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=5e-5, weight_decay=0., foreach=False)
    optimizer.step()
    if any(not torch.equal(before[name], p) for name, p in model.named_parameters() if name in before):
        raise ValueError('Fresh summary update changed a protected original parameter')
    state = {k: v.detach().clone() for k, v in get_peft_model_state_dict(model, adapter_name='summary').items()}
    path = OUT / 'synthetic_FP32_state.pt'
    with path.open('xb') as stream:
        torch.save(state, stream)
    state = torch.load(path, map_location='cpu', weights_only=True)
    model.add_adapter('summary_reload', config)
    for name, p in model.named_parameters():
        if '.summary_reload.' in name:
            p.data = p.data.float()
    set_peft_model_state_dict(model, state, adapter_name='summary_reload')
    loaded = get_peft_model_state_dict(model, adapter_name='summary_reload')
    if set(state) != set(loaded) or any(not torch.equal(state[k], loaded[k]) for k in state):
        raise ValueError('New summary FP32 state cannot reload exactly')
    return dict(zero_B_equals_BASE=True, new_role_only_gradient=True,
        original_BASE_TIME_unchanged=True, exact_FP32_state_reload=True,
        synthetic_optimizer_steps=1, actual8B_training_steps=0)


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    protocol = read(Path(__file__).with_name('summary_protocol85.json'))
    inventory = read(ROOT / protocol['fit_inventory'])
    targets = {row['source']['sid']: read(check(row['targets']))['reviews'] for row in inventory['planned']}
    publishers, weights = all_review_weights(inventory['planned'], targets)
    if sorted(targets) != sorted(protocol['fit_sources']) or len(publishers) != 5:
        raise ValueError('Actual fit/publisher identities differ from protocol')
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids('<|im_end|>')
    if '<|im_end|>' not in tokenizer.get_vocab() or eos not in tokenizer.all_special_ids:
        raise ValueError('Actual chat assistant EOS is unknown')
    token_rows = {}; lengths = []
    windows = {row['source']['sid']: len(row['windows']) for row in inventory['planned']}
    for sid, rows in targets.items():
        token_rows[sid] = []
        for row, weight in zip(rows, weights[sid]):
            escaped = target_content(row['target'])
            ids = tokenizer.encode(escaped, add_special_tokens=False)
            if (set(ids) & set(tokenizer.all_special_ids) or not ids
                    or len(ids) + 1 > min(generation_budget(windows[sid]),
                        protocol['summary_training']['maximum_whole_target_tokens_including_EOS'])):
                raise ValueError('Whole human target contains special tokens or exceeds fixed token budget')
            if json.loads(tokenizer.decode(ids, clean_up_tokenization_spaces=False)) != json.loads(row['target']):
                raise ValueError('Actual whole original human text changed in tokenization')
            token_rows[sid].append(dict(original_row=row['original_row'], target_ids=ids + [eos],
                target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                equal_publisher_source_reviewer_weight=str(weight)))
            lengths.append(len(ids) + 1)
    prefix = prefix_tokens(tokenizer, ['Observed activity.'])
    if not prefix or prefix[-1] == eos:
        raise ValueError('Source-summary prefix is not an open assistant turn')
    save(OUT / 'whole_target_tokens.json', dict(source_rows=token_rows, EOS=eos,
        all_original_reviewers_preserved=True, human_targets_not_in_prefix=True,
        unselected_semantics='UNKNOWN', timestamps_and_scores_as_target=False))
    role = fresh_role_contract()
    if torch.cuda.is_initialized():
        raise ValueError('CPU contract initialized CUDA')
    save(OUT / 'completion.json', dict(state='PASS_FIRST_SUMMARY_TARGET_AND_FRESH_ROLE_CPU_CONTRACT',
        protocol=identity(Path(__file__).with_name('summary_protocol85.json')),
        original_fit_inventory=identity(ROOT / protocol['fit_inventory']),
        whole_target_tokens=identity(OUT / 'whole_target_tokens.json'),
        all_original_reviews=len(lengths), minimum_target_tokens=min(lengths), maximum_target_tokens=max(lengths),
        publisher_groups=5, role_checks=role, actual8B_calls=0, actual8B_training=0,
        training_admitted=False, first_fit_caption_requires_all217_AV_inputs=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
