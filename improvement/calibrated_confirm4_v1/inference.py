"""Unique shared-wrapper GPU entries; no preparation, downloads or labels."""
from fractions import Fraction as F
import math
import os
import socket
from pathlib import Path
import time

import numpy as np
from confirm_common import bound, read, ref, require, save, utc, verify_model


def _entry(run, family):
    require(socket.gethostname() == run.c['hostname'], 'Registered GPU host identity')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == run.c['cuda_visible_devices']
            and bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Registered nonempty GPU child visibility')
    lock = run.accepted(family)
    run.deadline()
    out = run.begin(family+'_gpu')
    rt = run.runtime()
    run.module('sft_contract').verify_live_gpu_reservation()
    import torch
    torch.set_num_threads(run.c['gpu_cpu_threads'])
    return lock, out, rt, torch


def _identity(run, rt, out):
    model, processor, identity = rt.b_engine.load_model(run.model_config())
    verify_model(model, identity)
    save(out/'model_identity.json', identity)
    from peft.tuners.tuners_utils import BaseTunerLayer
    layers = [layer for layer in model.modules() if isinstance(layer, BaseTunerLayer)]
    require(len(layers) == 144 and all(not layer.disable_adapters for layer in layers), 'Actual TIME adapter activation')
    return model, processor, identity, layers


def _model_unchanged(run, rt, model, identity):
    require(rt.b_engine.frozen_identity(model, run.model_config()) == identity['base']
            and rt.b_engine.adapter_identity(model, run.model_config()) == identity['adapter'], 'Base/TIME changed at terminal')


def _raw_generate(run, folder, model, processor, encoded, expected_signature, grammar, torch, rt):
    run.deadline()
    require(rt.tensor_signature(encoded) == expected_signature, 'Accepted serialized CPU input changed')
    gpu = {key: value.to('cuda:0') for key, value in encoded.items()}
    require(rt.tensor_signature(gpu) == expected_signature, 'Actual GPU input tensor mismatch')
    prefix = int(gpu['input_ids'].shape[1]); started = time.monotonic()
    save(folder/'request.json', dict(input_signature=expected_signature, input_tokens=prefix,
         model_role='TIME_ENABLED', reference_labels_read=False, model_call_begin_utc=utc(),
         actual_model_call_started=True))
    with torch.inference_mode():
        generated = model.generate(**gpu, do_sample=False, max_new_tokens=256,
            prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)
    torch.cuda.synchronize()
    ids = generated.sequences[0, prefix:]
    raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
    eos = model.generation_config.eos_token_id; eos = [eos] if isinstance(eos, int) else list(eos)
    save(folder/'raw.json', dict(raw_output=raw, output_token_ids=ids.tolist(), input_tokens=prefix,
         output_tokens=len(ids), generated_score_count=len(generated.scores), eos=eos,
         selected_scores=[value if math.isfinite(value) else str(value) for value in scores],
         seconds=time.monotonic()-started, grammar_stats=grammar.stats, actual_model_call=True))
    require(0 < len(ids) <= 256 and len(ids) == len(scores) == len(generated.scores)
            and all(map(math.isfinite, scores)), 'Untouched raw token/score denominator')
    parsed = grammar.assert_complete(ids)
    del gpu, generated
    return raw, parsed


def b0_gpu(run):
    lock, out, rt, torch = _entry(run, 'b0')
    inputs = run.receipt('b0_prepare')['inputs']
    require(len(inputs) == lock['expected_calls'], 'Registered B0 call denominator')
    model, processor, identity, layers = _identity(run, rt, out)
    grammar_module = run.module('constrained_json')
    candidates = grammar_module.ascii_token_candidates(processor.tokenizer)
    eos = model.generation_config.eos_token_id; eos = [eos] if isinstance(eos, int) else list(eos)
    outputs = []
    for item in inputs:
        proof = read(bound(item)); meta = read(bound(proof['meta_ref']))
        folder = out/proof['case_id']; folder.mkdir()
        encoded = torch.load(bound(proof['encoded_ref']), map_location='cpu', weights_only=True)
        prefix = int(encoded['input_ids'].shape[1]); duration = F(meta['window_end'])-F(meta['window_start'])
        grammar = grammar_module.make_prefix_constraint(processor.tokenizer, prefix, duration,
                    candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
        require(all(not layer.disable_adapters for layer in layers), 'B0 must retain TIME role')
        raw, _ = _raw_generate(run, folder, model, processor, encoded, proof['input_evidence']['tensor_signature'], grammar, torch, rt)
        segments, errors, warnings = rt.parse_segments(raw, duration, allow_empty=True)
        require(segments is not None and not errors, 'Original B0 parser rejected actual untouched raw')
        save(folder/'done.json', dict(case_id=proof['case_id'], sid=proof['sid'], input_ref=item, raw_ref=ref(folder/'raw.json'),
             request_ref=ref(folder/'request.json'), status='MODEL_OK' if segments else 'LEGAL_EMPTY', segments=segments,
             parse_warnings=warnings, labels_read=False))
        outputs.append(ref(folder/'done.json'))
        del encoded
    _model_unchanged(run, rt, model, identity)
    run.finish('b0_gpu', outputs=outputs, actual_calls=len(outputs), input_lock_ref=ref(run.root/'locks/b0.json'), optimizer_updates=0)


def verify_gpu(run):
    lock, out, rt, torch = _entry(run, 'verify')
    inputs = run.receipt('verify_prepare')['inputs']
    require(len(inputs) == lock['expected_calls'], 'Registered VERIFY call denominator')
    outputs = []
    if inputs:
        model, processor, identity, layers = _identity(run, rt, out)
        gm = run.module('cv_grammar')
        candidates = gm.candidate_tokens(processor.tokenizer, ('{"decision":"KEEP"}', '{"decision":"UNKNOWN"}', '{"decision":"DROP"}'))
        eos = model.generation_config.eos_token_id; eos = [eos] if isinstance(eos, int) else list(eos)
        for item in inputs:
            row = read(bound(item)); folder = out/row['case_id']; folder.mkdir()
            original = torch.load(bound(row['vision_ref']), map_location='cpu', weights_only=True)
            text = torch.load(bound(row['text_ref']), map_location='cpu', weights_only=True)
            encoded = {**{key: original[key] for key in ('pixel_values_videos', 'video_grid_thw')}, **text}
            grammar = gm.VerifyConstraint(processor.tokenizer, int(text['input_ids'].shape[1]), row['request'], eos, candidates)
            require(all(not layer.disable_adapters for layer in layers), 'VERIFY must retain TIME role')
            raw, parsed = _raw_generate(run, folder, model, processor, encoded, row['full_signature'], grammar, torch, rt)
            require(raw == __import__('json').dumps(parsed, separators=(',', ':')), 'Canonical actual VERIFY raw')
            save(folder/'done.json', dict(case_id=row['case_id'], sid=row['sid'], input_ref=item, raw_ref=ref(folder/'raw.json'),
                 request_ref=ref(folder/'request.json'), event_id=row['request']['event_id'], decision=parsed['decision']))
            outputs.append(ref(folder/'done.json')); del original, text, encoded
        _model_unchanged(run, rt, model, identity)
    run.finish('verify_gpu', outputs=outputs, actual_calls=len(outputs), input_lock_ref=ref(run.root/'locks/verify.json'),
               zero_event_success_without_model_load=not bool(inputs), optimizer_updates=0)


def context_gpu(run):
    lock, out, rt, torch = _entry(run, 'context')
    produced = run.receipt('context_prepare')
    require(len(produced['inputs']) == lock['expected_calls'], 'Registered context batch denominator')
    model, processor, identity, layers = _identity(run, rt, out)
    native = model.get_base_model(); core = native.model
    yes, no = [processor.tokenizer.encode(text, add_special_tokens=False) for text in ('Yes', 'No')]
    require(len(yes) == len(no) == 1, 'Original single-token Yes/No definition')
    outputs, queries = [], 0
    flags = [(parameter, parameter.requires_grad) for parameter in model.parameters()]
    with model.disable_adapter(), torch.inference_mode():
        require(all(layer.disable_adapters for layer in layers), 'BASE context must disable TIME adapter')
        for source in produced['sources']:
            folder = out/source['sid']; folder.mkdir()
            language, pairs, cases = [], [], []
            for case in source['cases']:
                run.deadline()
                data = torch.load(bound(case), map_location='cpu', weights_only=True); k = case['queries']
                gpu = {key: data[key].to('cuda:0') for key in ('input_ids', 'attention_mask')}
                gpu['pixel_values'] = data['pixel_values'].repeat(k, 1).to('cuda:0')
                gpu['image_grid_thw'] = data['image_grid_thw'].repeat(k, 1).to('cuda:0')
                expected = dict(input_ids=data['input_ids'], attention_mask=data['attention_mask'],
                    pixel_values=data['pixel_values'].repeat(k, 1), image_grid_thw=data['image_grid_thw'].repeat(k, 1))
                signature = rt.tensor_signature(expected)
                require(rt.tensor_signature(gpu) == signature, 'Actual BASE repeated image/text GPU transfer differs')
                request_path = folder/('context_%04d.request.json'%case['index'])
                save(request_path, dict(input_ref=case,
                     model_role='BASE_DISABLED', actual_model_call_started=True, model_call_begin_utc=utc(),
                     actual_gpu_signature=signature, labels_read=False))
                require(all(layer.disable_adapters for layer in layers), 'BASE role changed during context')
                result = core(**gpu, use_cache=False, return_dict=True)
                last = result.last_hidden_state[:, -1, :]
                logits = native.lm_head(last).float(); pair = logits[:, [yes[0], no[0]]].cpu(); last = last.float().cpu()
                require(last.shape == (k, 4096) and pair.shape == (k, 2)
                        and torch.isfinite(last).all() and torch.isfinite(pair).all(), 'Actual complete BASE language4096 outputs')
                path = folder/('context_%04d.pt'%case['index'])
                with path.open('xb') as stream:
                    torch.save(dict(language=last, yes_no=pair), stream)
                record = dict(input_ref=case, output_ref=ref(path), request_ref=ref(request_path), role='BASE_DISABLED')
                save(folder/('context_%04d.json'%case['index']), record); cases.append(record)
                language.append(last.numpy()); pairs.append(pair.numpy()); queries += k
                del gpu, data, expected, result, last, logits, pair
            with (folder/'language.npy').open('xb') as stream:
                np.save(stream, np.concatenate(language))
            with (folder/'yes_no.npy').open('xb') as stream:
                np.save(stream, np.concatenate(pairs))
            outputs.append(dict(sid=source['sid'], cases=cases, cells=source['cells'], language_ref=ref(folder/'language.npy'), yes_no_ref=ref(folder/'yes_no.npy')))
    for parameter, flag in flags:
        parameter.requires_grad_(flag)
    require(all(not layer.disable_adapters for layer in layers), 'TIME role not restored')
    _model_unchanged(run, rt, model, identity)
    require(queries == produced['expected_queries'], 'Complete BASE query denominator')
    run.finish('context_gpu', sources=outputs, actual_calls=lock['expected_calls'], context_queries=queries,
               input_lock_ref=ref(run.root/'locks/context.json'), optimizer_updates=0)
