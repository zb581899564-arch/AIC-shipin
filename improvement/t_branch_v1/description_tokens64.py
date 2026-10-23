"""Generic silent-caption prefix; human words remain separate supervised targets."""
import hashlib

import numpy as np
import torch

from prompt_contract13 import prompt_binding
from t_io import check, identity, read, save

QUESTION = 'Describe the main visible event in this silent video clip in one short sentence. Do not invent details that are not shown.'


def load_values(ref):
    row = read(check(ref))
    with np.load(check(row['encoded']), allow_pickle=False) as data:
        values = {name: torch.from_numpy(data[name].copy()) for name in data.files}
    values.update(row['non_tensor_inputs'])
    return values


def caption_values(values, tokenizer, rt):
    original = values['input_ids'][0].tolist()
    text = tokenizer.decode(original, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if tokenizer.encode(text, add_special_tokens=False) != original or text.count(rt.EMPTY_PROMPT) != 1:
        raise ValueError('Actual original caption view cannot support exact one-task replacement')
    replacement = tokenizer.encode(text.replace(rt.EMPTY_PROMPT, QUESTION), add_special_tokens=False)
    pad = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    end = max(i for i, token in enumerate(original) if token == pad) + 1
    if replacement[:end] != original[:end]:
        raise ValueError('Caption question changed actual visual/native timestamp prefix')
    actual = dict(values, input_ids=torch.tensor([replacement], dtype=torch.long))
    actual['attention_mask'] = torch.ones_like(actual['input_ids'])
    binding = prompt_binding(tokenizer, actual['input_ids'],
        dict(prompt_sha256=hashlib.sha256(QUESTION.encode()).hexdigest()), QUESTION, 'HUMAN_EVENT_DESCRIPTION')
    return actual, binding


def prepare_pair(example, physical, folder, tokenizer, rt):
    folder.mkdir()
    original = load_values(physical['correct']); wrong = load_values(physical['wrong'])
    if not torch.equal(original['video_grid_thw'], wrong['video_grid_thw']):
        raise ValueError('Same-source correct/control spatial grids differ; no implicit resizing')
    correct, binding = caption_values(original, tokenizer, rt)
    shifted = dict(correct, pixel_values_videos=wrong['pixel_values_videos'])
    target = tokenizer.encode(example['exact_original_description'], add_special_tokens=False)
    if not target or len(target) > 512 or correct['input_ids'].shape[1] + len(target) > 16384:
        raise ValueError('Whole original human text exceeds this bounded probe; never truncate or replace')
    path = folder / 'caption_text.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, input_ids=correct['input_ids'].numpy(),
            attention_mask=correct['attention_mask'].numpy(), target_tokens=np.asarray(target, dtype=np.int64))
    with np.load(path, allow_pickle=False) as data:
        if (not np.array_equal(data['input_ids'], correct['input_ids'].numpy())
                or not np.array_equal(data['target_tokens'], target)):
            raise ValueError('First caption input/target serialization differs')
    save(folder / 'CPU.json', dict(example_id=example['example_id'], source=example['source']['sid'],
        role=example['source']['role'], publisher=example['source']['publisher'], physical_inputs=physical,
        caption_text=identity(path), generic_question_binding=binding,
        exact_original_human_text_sha256=hashlib.sha256(example['exact_original_description'].encode()).hexdigest(),
        original_human_rows=example['original_human_rows'], original_interval_exact=example['original_interval_exact'],
        correct_signature=rt.tensor_signature(correct), control_signature=rt.tensor_signature(shifted),
        control_is_same_source_disjoint_REAL_pixels_under_same_correct_time_prefix=True,
        control_not_ordinary_ground_truth=True, target_tokens=len(target), input_tokens=correct['input_ids'].shape[1],
        human_target_not_part_of_inference_question=True, supervised_external_task_only=True))
    return identity(folder / 'CPU.json')
