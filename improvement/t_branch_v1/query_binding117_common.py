"""Bijective query transforms without changing accepted real observations."""
from copy import deepcopy
import hashlib
import json

import numpy as np
import torch

from event_memory69_common import quoted, speech_text
from native_codec98 import ANCHORS
from native_input99 import geometry
from parallel_input106 import values as prior_values
from parallel_query105 import QUESTION
from prompt_contract13 import prompt_binding
from t_io import check, identity, read, save


def layout(arm):
    if arm == 'reverse_query_order':
        cells = list(reversed(range(32)))
        labels = cells.copy()
    elif arm == 'rename_anchors_half_cycle':
        cells = list(range(32))
        labels = [(j + 16) % 32 for j in cells]
    else:
        raise ValueError('Unregistered query transformation')
    if sorted(cells) != list(range(32)) or sorted(labels) != list(range(32)):
        raise ValueError('Actual query transform is not a complete bijection')
    return cells, labels


def remap(binary, query_to_native):
    if len(binary) != 32 or sorted(query_to_native) != list(range(32)):
        raise ValueError('Cannot inverse-map incomplete query decisions')
    result = torch.empty_like(binary) if torch.is_tensor(binary) else np.empty_like(binary)
    result[query_to_native] = binary
    return result


def transformed_prefix(case, source, prior, tokenizer, arm):
    with np.load(check(prior['text']), allow_pickle=False) as data:
        original = data['input_ids'][0].tolist()
    before = prior['prefix_tokens_before_queries']
    prefix = tokenizer.decode(original[:before], skip_special_tokens=False,
                              clean_up_tokenization_spaces=False)
    if tokenizer.encode(prefix, add_special_tokens=False) != original[:before]:
        raise ValueError('Original complete prefix does not round-trip exactly')
    native, table = geometry(case, source.timeline)
    if native != [tuple(pair) for pair in prior['source_native_cells']]:
        raise ValueError('Query transform attempted to alter accepted native cells')
    speech = speech_text(prior['ASR'])
    original_task = QUESTION + quoted(dict(cells=table, quoted_unverified_speech=speech))
    if prefix.count(original_task) != 1:
        raise ValueError('Original exact cell table/task not found once')
    cells, labels = layout(arm)
    renamed = table if arm == 'reverse_query_order' else {
        ANCHORS[(j + 16) % 32]: table[ANCHORS[j]] for j in range(32)}
    if any(renamed[ANCHORS[label]] != table[ANCHORS[cell]] for cell, label in zip(cells, labels)):
        raise ValueError('Consistent relabeling changed a query observation assignment')
    expected = QUESTION + quoted(dict(cells=renamed, quoted_unverified_speech=speech))
    changed = tokenizer.encode(prefix.replace(original_task, expected), add_special_tokens=False)
    pad = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    end = max(j for j, token in enumerate(original[:before]) if token == pad) + 1
    if changed[:end] != original[:end] or changed.count(pad) != original[:before].count(pad):
        raise ValueError('Text-only query permutation changed video or native timestamp prefix')
    return changed, expected, cells, labels


def prepare(case, source, prior_ref, tokenizer, rt, code, arm, folder):
    prior = read(check(prior_ref))
    prefix, expected, cells, labels = transformed_prefix(case, source, prior, tokenizer, arm)
    suffix = [token for j in labels for token in [code['anchors'][j], code['Question']]]
    all_ids = prefix + suffix
    if len(all_ids) > 16384 or set(suffix) & {code['Yes'], code['No']}:
        raise ValueError('Counterfactual query exceeds context or contains supplied answers')
    values = dict(input_ids=torch.tensor([all_ids], dtype=torch.long),
                  attention_mask=torch.ones((1, len(all_ids)), dtype=torch.long))
    signature = deepcopy(prior['actual_signature']); signature.update(rt.tensor_signature(values))
    folder.mkdir(); path = folder / 'text.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, **{k: v.numpy() for k, v in values.items()})
    with np.load(path, allow_pickle=False) as data:
        if any(not np.array_equal(data[k], v.numpy()) for k, v in values.items()):
            raise ValueError('First query-transform text serialization differs')
    binding = prompt_binding(tokenizer, values['input_ids'],
        dict(prompt_sha256=hashlib.sha256(expected.encode()).hexdigest()), expected, 'QUERY_BINDING_DIAGNOSIS')
    proof = folder / 'CPU.json'
    save(proof, dict(case=case.name, source=source.sid, arm=arm, original_CPU=case.CPU,
        prior_query_CPU=prior_ref, text=identity(path), actual_signature=signature,
        physical_input_key=hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest(),
        prefix_tokens_before_queries=len(prefix), input_tokens=len(all_ids),
        query_positions=list(range(len(prefix) + 1, len(all_ids), 2)),
        actual_query_code=code, query_to_native=cells, actual_query_anchor_indices=labels,
        source_native_cells=prior['source_native_cells'], ASR=prior['ASR'],
        prompt_binding=binding, no_observations_or_labels_changed=True,
        existing_visual_signature_and_first_CPU_adopted=True))
    return identity(proof)


def values(case, proof, tokenizer, rt):
    row = read(check(proof))
    if row['case'] != case.name or row['original_CPU'] != case.CPU:
        raise ValueError('Query-binding input belongs to another native case')
    actual = prior_values(case, row['prior_query_CPU'], tokenizer, rt)
    with np.load(check(row['text']), allow_pickle=False) as data:
        actual.update({k: torch.from_numpy(data[k].copy()) for k in data.files})
    suffix = actual['input_ids'][0, row['prefix_tokens_before_queries']:].tolist()
    cells, labels = layout(row['arm']); code = row['actual_query_code']
    expected = [token for j in labels for token in [code['anchors'][j], code['Question']]]
    if (suffix != expected or cells != row['query_to_native'] or labels != row['actual_query_anchor_indices']
            or rt.tensor_signature(actual) != row['actual_signature']):
        raise ValueError('Actual transformed suffix/inverse mapping or video/PTS signature differs')
    return actual
