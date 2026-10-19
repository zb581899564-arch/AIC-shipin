"""Explicit first full-branch likelihood readout of saved external VERIFY cases.

No generation, optimizer, media decoding, new teacher or official-data read.
Three teacher-forced sequences differ in their complete canonical response.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

from branch_math import (BRANCHES, CANONICAL_RESPONSES, validate_branch_token_ids,
                         build_teacher_forced_sequence, summarize_branch_log_probs)

WORK = Path('/home/inspur/aic_video_work')
PRIOR = WORK/'recall_expansion_verify40_46_20261014_v1'
PYTHON = WORK/'env/qwen3vl_isolated_20260910/bin/python'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    p = Path(path).resolve()
    return dict(path=str(p), sha256=sha(p))


def bound(value):
    p = Path(value['path']).resolve()
    require(p.is_file() and p.is_relative_to(WORK) and sha(p) == value['sha256'], 'Frozen reference changed: '+str(p))
    return p


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def original_io():
    p = PRIOR/'code/model_common.py'
    spec = importlib.util.spec_from_file_location('_original_recall_io_branch_readout', p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_registration(root):
    r = read(root/'branch_registration_03.json')
    require(r['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and r['new_training_updates'] == 0,
            'Explicit external-only no-training registration')
    for filename, digest in r['runtime_code'].items():
        require(sha(root/'branch_code_03'/filename) == digest, 'New frozen branch code changed')
    for filename, digest in read(bound(r['old_runtime_binding']))['files'].items():
        require(sha(filename) == digest, 'Adopted original runtime dependency changed')
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(r['deadline_utc'].replace('Z', '+00:00')),
            'No new work after registered deadline')
    return r


def load_input(io, row):
    meta = read(bound(row['original_input']))
    proof = read(bound(row['original_proof']))
    require(proof['input_sha256'] == row['original_input']['sha256']
            and proof['status'] == 'PASS_CPU_RECALL_VERIFY_PROMPT_ONLY_UNCHANGED_VISION', 'Original input proof')
    encoded = io.load_cache(bound(dict(path=meta['original_vision_cache_path'], sha256=meta['original_vision_cache_sha256'])))
    tokens = io.load_cache(bound(dict(path=meta['token_cache_path'], sha256=meta['token_cache_sha256'])))
    encoded.update(tokens)
    return encoded, meta, proof


def prepare(root, group):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU child must hide only own CUDA')
    r = check_registration(root)
    require(group in r['permitted_groups'], 'Group not registered')
    import torch
    from transformers import AutoTokenizer
    torch.set_num_threads(2)
    io = original_io()
    old = PRIOR/group/'VERIFY/cpu_01/completion.json'
    acceptance = read(old)
    require(acceptance['status'] == 'PASS_ALL_RECALL_VERIFY_TOKEN_INPUTS_NOT_GPU_ADMISSION'
            and acceptance['group'] == group
            and len(acceptance['entries']) == acceptance['expected_input_count'] == r['expected_cases'][group],
            'Exact existing successful CPU group and case denominator')
    tokenizer = AutoTokenizer.from_pretrained(io.read(io.CONFIG)['model_dir'], local_files_only=True)
    ids = validate_branch_token_ids({key: tokenizer.encode(text, add_special_tokens=False)
                                     for key, text in CANONICAL_RESPONSES.items()})
    require(all(tokenizer.decode(ids[key], skip_special_tokens=False, clean_up_tokenization_spaces=False) == text
                for key, text in CANONICAL_RESPONSES.items()), 'Canonical full branch roundtrip')
    dst = root/('branch_'+group+'_03'); dst.mkdir(exist_ok=False)
    entries = []
    for old_row in acceptance['entries']:
        row = dict(case_id=old_row['case_id'],
                   original_input=dict(path=old_row['input_path'], sha256=old_row['input_sha256']),
                   original_proof=dict(path=old_row['proof_path'], sha256=old_row['proof_sha256']))
        encoded, meta, proof = load_input(io, row)
        require(meta['reference_labels_read'] is False and meta['audio_observed'] is False, 'Original observation scope')
        require(set(meta['allowed_decisions']) == set(BRANCHES),
                'Unknown-only observation must not be treated as three-state semantic evidence')
        prefix = encoded['input_ids'][0].tolist()
        plans = {key: build_teacher_forced_sequence(prefix, answer) for key, answer in ids.items()}
        require(all(len(p['input_ids']) <= 16448 for p in plans.values()), 'Teacher-forced total input budget')
        item = dict(**row, source_sha256=meta['source_sha256'], source_name=meta['source_name'],
                    original_prompt=meta['prompt'], event_id=meta['event_id'], group=group,
                    original_interval_exact=meta['original_interval_exact'],
                    branch_token_ids=ids, plans=plans, original_input_evidence=proof['input_evidence'],
                    model_parameters=8782459120, adapter_role='ORIGINAL_ENABLED_TIME',
                    labels_read=False, new_processor_calls=0, old_QA_reference_only=True)
        path = dst/(row['case_id']+'.json'); save(path, item); entries.append(ref(path))
        del encoded
    save(dst/'prepared.json', dict(status='PREPARED_NEW_TEACHER_FORCED_BRANCHES_NOT_GPU_ADMISSION',
         entries=entries, original_cpu_acceptance=ref(old), cases=len(entries), full_branch_forwards=3*len(entries),
         new_decode_or_processor_calls=0, new_training_updates=0, original_comparisons_repeated=0))
    require(not torch.cuda.is_initialized(), 'CPU preparation initialized CUDA')


def input_qa(root, group):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent CPU child must hide own CUDA')
    check_registration(root)
    import torch
    from transformers import AutoTokenizer
    torch.set_num_threads(2)
    io = original_io(); runtime = io.runtime_only()
    tokenizer = AutoTokenizer.from_pretrained(io.read(io.CONFIG)['model_dir'], local_files_only=True)
    dst = root/('branch_'+group+'_03'); ready = read(dst/'prepared.json')
    seen = []
    for reference in ready['entries']:
        row = read(bound(reference)); encoded, meta, proof = load_input(io, row)
        require(runtime.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'], 'Adopted real visual input differs from original QA')
        require(meta['source_sha256'] == row['source_sha256'] and meta['prompt'] == row['original_prompt'], 'Source/task changed')
        prefix = encoded['input_ids'][0].tolist()
        for branch in BRANCHES:
            plan = row['plans'][branch]; labels = row['branch_token_ids'][branch]
            require(tokenizer.decode(labels, skip_special_tokens=False, clean_up_tokenization_spaces=False) == CANONICAL_RESPONSES[branch], 'Actual canonical response')
            require(plan['input_ids'] == prefix+labels[:-1] and plan['labels'] == labels, 'Independent teacher-force input prefix')
            require(plan['logit_positions'] == list(range(len(prefix)-1, len(prefix)+len(labels)-1))
                    and plan['prefix_length'] == len(prefix), 'Independent causal next-token alignment')
            require(encoded['attention_mask'].eq(1).all(), 'Unpadded single-case attention mask expected')
            seen.append((row['case_id'], branch))
        del encoded
    require(len(seen) == len(set(seen)) == ready['full_branch_forwards'], 'Complete first QA denominator')
    require(not torch.cuda.is_initialized(), 'Independent input QA initialized CUDA')
    save(dst/'input_acceptance.json', dict(status='PASS_ALL_FIRST_NEW_FULL_BRANCH_INPUT_QA',
         prepared=ref(dst/'prepared.json'), cases=ready['cases'], full_branch_forwards=len(seen),
         explicit_case_branches=seen, original_cpu_QA_repeated=False, new_CPU_input_QA_only=True,
         new_decode_or_processor_calls=0, labels_read=False, CUDA_initialized=False))


def infer(root, group):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'GPU chain retains actual nonempty CUDA index')
    registration = check_registration(root)
    io = original_io(); runtime = io.runtime_only()
    sys.path.insert(0, str(io.RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    torch.set_num_threads(2)
    dst = root/('branch_'+group+'_03')
    acceptance = read(dst/'input_acceptance.json')
    require(acceptance['status'] == 'PASS_ALL_FIRST_NEW_FULL_BRANCH_INPUT_QA', 'Actual first input QA before GPU')
    prepared = read(bound(acceptance['prepared']))
    out = dst/'GPU'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), pid=os.getpid(), registration=ref(root/'branch_registration_03.json'),
         input_acceptance=ref(dst/'input_acceptance.json'), expected_forwards=prepared['full_branch_forwards']))
    config = io.read(io.CONFIG)
    model, processor, identity = runtime.b_engine.load_model(config)
    io.verify_model(model, identity)
    native = model.get_base_model(); core = native.model
    require(sum(p.numel() for p in model.parameters()) == 8782459120, 'Actual all-loaded parameter inventory')
    save(out/'model_identity.json', dict(identity=identity, all_144_TIME_layers_enabled=True,
         original_adapter_disable_flags=io.enabled_layers(model), new_optimizer_updates=0))
    attempts = out/'attempts.jsonl'; attempts.touch(exist_ok=False)
    def event(value):
        with attempts.open('a') as stream:
            stream.write(json.dumps(dict(utc=utc(), **value))+'\n'); stream.flush(); os.fsync(stream.fileno())
    successful = []
    try:
        for reference in prepared['entries']:
            row = read(bound(reference)); encoded, meta, proof = load_input(io, row)
            require(runtime.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'], 'Real accepted input changed')
            for branch in BRANCHES:
                plan = row['plans'][branch]
                call_id = row['case_id']+'.'+branch
                request = dict(case_id=row['case_id'], branch=branch, case=reference,
                               label_token_ids=plan['labels'], logit_positions=plan['logit_positions'],
                               input_ids_sha256=hashlib.sha256(torch.tensor(plan['input_ids'], dtype=torch.int64).numpy().tobytes()).hexdigest())
                save(out/(call_id+'.request.json'), request)
                cpu = dict(encoded)
                cpu['input_ids'] = torch.tensor([plan['input_ids']], dtype=encoded['input_ids'].dtype)
                cpu['attention_mask'] = torch.ones_like(cpu['input_ids'], dtype=encoded['attention_mask'].dtype)
                gpu = {key: value.to('cuda') for key, value in cpu.items()}
                positions = torch.tensor(plan['logit_positions'], device='cuda', dtype=torch.long)
                captured = []
                def capture(_module, _inputs, output):
                    captured.append(native.lm_head(output[0, positions]).float())
                handle = core.language_model.norm.register_forward_hook(capture)
                event(dict(event='BEGIN_NEW_COMPLETE_BRANCH_LIKELIHOOD', call_id=call_id))
                start = time.monotonic()
                try:
                    with torch.inference_mode():
                        result = core(**gpu, use_cache=False, return_dict=True)
                    torch.cuda.synchronize()
                finally:
                    handle.remove()
                require(len(captured) == 1 and captured[0].shape[0] == len(plan['labels'])
                        and torch.isfinite(captured[0]).all(), 'Actual finite unprocessed full-vocabulary logits')
                logits = captured.pop()
                labels = torch.tensor(plan['labels'], device='cuda', dtype=torch.long)
                token_lp = logits.log_softmax(-1).gather(1, labels[:, None]).flatten().cpu().tolist()
                raw = logits.cpu().contiguous()
                tensor_path = out/(call_id+'.logits.pt'); torch.save(raw, tensor_path)
                output = dict(status='ACCEPTED_NEW_RAW_FULL_BRANCH_LOG_LIKELIHOOD', call_id=call_id,
                              case_id=row['case_id'], branch=branch, request=ref(out/(call_id+'.request.json')),
                              raw_logits=ref(tensor_path), shape=list(raw.shape), full_vocab_unprocessed=True,
                              token_log_probs=token_lp, complete_sequence_log_prob=sum(token_lp),
                              elapsed_seconds=time.monotonic()-start, actual_new_forward=True,
                              generation_calls=0, optimizer_updates=0, labels_read=False)
                path = out/(call_id+'.json'); save(path, output); successful.append(ref(path))
                event(dict(event='ACCEPTED_NEW_COMPLETE_BRANCH_LIKELIHOOD', call_id=call_id, output=ref(path)))
                print(json.dumps(dict(group=group, accepted=len(successful), expected=prepared['full_branch_forwards'])), flush=True)
                del result, logits, raw, gpu, cpu
            del encoded
        require(len(successful) == prepared['full_branch_forwards']
                and io.enabled_layers(model) == [False]*144, 'Complete expected unique branch denominator')
        require(runtime.b_engine.frozen_identity(model, config) == identity['base']
                and runtime.b_engine.adapter_identity(model, config) == identity['adapter'], 'Original frozen actual model changed')
        save(out/'completion.json', dict(status='PASS_ALL_FIRST_COMPLETE_BRANCH_LIKELIHOODS_NOT_QUALITY',
             entries=successful, cases=prepared['cases'], actual_new_forwards=len(successful), labels_read=False,
             model_identity=ref(out/'model_identity.json'), generation_calls=0, training_updates=0))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), successful=successful,
             preserve_all_success=True, do_not_repeat_success=True, failure_is_not_empty=True))
        raise


def output_qa(root, group):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent output QA is CPU only')
    import torch
    import numpy as np
    torch.set_num_threads(2)
    dst = root/('branch_'+group+'_03'); done = read(dst/'GPU/completion.json')
    cases = {}
    for reference in done['entries']:
        row = read(bound(reference)); request = read(bound(row['request']))
        logits = torch.load(bound(row['raw_logits']), map_location='cpu', weights_only=True).numpy().astype(np.float64)
        require(list(logits.shape) == row['shape'] and np.isfinite(logits).all(), 'Independent actual raw logits')
        m = logits.max(1)
        denom = m+np.log(np.exp(logits-m[:, None]).sum(1))
        expected = logits[np.arange(len(logits)), request['label_token_ids']]-denom
        require(np.allclose(expected, row['token_log_probs'], atol=1e-4, rtol=1e-6), 'Independent unprocessed full-vocabulary normalization')
        group_row = cases.setdefault(row['case_id'], {})
        require(row['branch'] not in group_row, 'No repeated successful branch')
        group_row[row['branch']] = expected.tolist()
    values = []
    for case_id, branches in cases.items():
        require(set(branches) == set(BRANCHES), 'Complete three canonical answers')
        values.append(dict(case_id=case_id, **summarize_branch_log_probs(branches)))
    require(len(cases) == done['cases'] and len(done['entries']) == 3*len(cases), 'Complete independent output denominator')
    save(dst/'output_acceptance.json', dict(status='PASS_ALL_FIRST_INDEPENDENT_BRANCH_OUTPUT_QA_NOT_QUALITY',
         GPU_completion=ref(dst/'GPU/completion.json'), cases=values, raw_logits_recomputed_without_new_forward=True,
         new_model_forwards=0, label_metric_comparison_not_yet_run=True,
         probability_scope='Conditional finite canonical-answer set, not calibrated P(highlight)'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'input_qa', 'infer', 'output_qa'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=['dev', 'confirm'], required=True)
    args = parser.parse_args()
    globals()[args.mode](args.root, args.group)
