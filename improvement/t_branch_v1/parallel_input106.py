"""Compose new query text with accepted exact video signatures; no old pixel re-encoding."""
from copy import deepcopy
import hashlib
import json

import numpy as np
import torch

from native_input99 import QUESTION as OLD_QUESTION, values as old_values
from parallel_query105 import QUESTION, assemble
from prompt_contract13 import prompt_binding
from t_io import check, identity, read, save


def prepare(prior_ref, tokenizer, rt, code, folder, owners):
    prior = read(check(prior_ref))
    with np.load(check(prior['text']), allow_pickle=False) as archive:
        old = archive['input_ids'].copy()
    decoded = tokenizer.decode(old[0].tolist(), skip_special_tokens=False,
                               clean_up_tokenization_spaces=False)
    if (tokenizer.encode(decoded, add_special_tokens=False) != old[0].tolist()
            or decoded.count(OLD_QUESTION) != 1):
        raise ValueError('Adopted complete old prefix cannot bind exactly one new query task')
    encoded = tokenizer.encode(decoded.replace(OLD_QUESTION, QUESTION), add_special_tokens=False)
    pad = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    stop = max(j for j, value in enumerate(old[0]) if value == pad) + 1
    if encoded[:stop] != old[0, :stop].tolist() or encoded.count(pad) != int(np.count_nonzero(old == pad)):
        raise ValueError('New query text changed actual video/PTS token prefix')
    values = assemble(torch.tensor([encoded], dtype=torch.long), code)
    text = {key: values[key] for key in ['input_ids', 'attention_mask']}
    signature = deepcopy(prior['actual_signature'])
    signature.update(rt.tensor_signature(text))
    key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
    folder.mkdir()
    path = folder / 'text.npz'
    previous = owners.get(key)
    if previous is None:
        with path.open('xb') as stream:
            np.savez_compressed(stream, **{k: v.numpy() for k, v in text.items()})
        with np.load(path, allow_pickle=False) as archive:
            if any(not np.array_equal(archive[k], v.numpy()) for k, v in text.items()):
                raise ValueError('First exact query input serialization round-trip differs')
        text_ref = identity(path)
    else:
        accepted = read(check(previous))
        if accepted['actual_signature'] != signature:
            raise ValueError('Actual query input signature hash collision')
        text_ref = accepted['text']
    binding = prompt_binding(tokenizer, text['input_ids'],
        dict(prompt_sha256=hashlib.sha256(QUESTION.encode()).hexdigest()), QUESTION,
        'PARALLEL_NATIVE_SUMMARY_QUERIES')
    out = folder / 'CPU.json'
    save(out, dict(case=prior['case'], source=prior['source'], original_CPU=prior['original_CPU'],
        prior_native_input=prior_ref, text=text_ref, actual_signature=signature,
        physical_input_key=key, prompt_binding=binding, input_tokens=values['input_ids'].shape[1],
        prefix_tokens_before_queries=len(encoded), query_positions=values['logits_to_keep'],
        actual_query_code=code, source_native_cells=prior['source_native_cells'],
        ASR=prior['ASR'], video_temporal_group_roll=prior['video_temporal_group_roll'],
        visual_signature_adopted_from_first_accepted_native_input=True,
        actual_full_GPU_transfer_signature_required_before_any_forward=True,
        static_queries_have_no_answer_tokens=True, previous_model_choices_not_in_input=True,
        new_visual_decode_processor_or_ASR=0, no_human_reference_in_input=True))
    ref = identity(out)
    owners.setdefault(key, ref)
    return ref


def values(case, proof, tokenizer, rt):
    row = read(check(proof))
    if row['case'] != case.name or row['original_CPU'] != case.CPU:
        raise ValueError('New parallel query input belongs to a different original case')
    actual = old_values(case, row['prior_native_input'], tokenizer, rt)
    with np.load(check(row['text']), allow_pickle=False) as archive:
        actual.update({key: torch.from_numpy(archive[key].copy()) for key in archive.files})
    if rt.tensor_signature(actual) != row['actual_signature']:
        raise ValueError('Actual parallel query video/PTS/static text differs from input binding')
    suffix = actual['input_ids'][0, row['prefix_tokens_before_queries']:].tolist()
    expected = [token for anchor in row['actual_query_code']['anchors']
                for token in [anchor, row['actual_query_code']['Question']]]
    if suffix != expected or set(suffix) & {row['actual_query_code']['Yes'], row['actual_query_code']['No']}:
        raise ValueError('Parallel inference received supplied selection answers')
    return actual
