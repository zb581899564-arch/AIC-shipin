"""Fixed eight-input, two-adapter likelihood probe; no generation or optimizer."""
import argparse
from collections import Counter
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

from diagnose_underselection28 import read, ref, bound, save


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def prepare(root):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    reg = read(root/'input_registration29.json')
    assert reg['maximum_new_teacher_forced_forwards'] == 32
    evidence = read(bound(reg['CPU28_result_ref']))
    assert evidence['grammar_blocked_paths'] == 0
    from transformers import AutoTokenizer
    import torch
    tok = AutoTokenizer.from_pretrained(reg['model_directory'], local_files_only=True)
    rows = []
    opening = tok.encode('{"segments":[', add_special_tokens=False)
    empty = tok.encode('{"segments":[]}', add_special_tokens=False) + [151645]
    assert opening == evidence['opening_tokens'] and empty == evidence['empty_tokens']
    for selected in evidence['fixed_next_probe_selection']:
        request = read(bound(selected['input_ref']))
        prefix = torch.load(bound(request['prefix_ref']), map_location='cpu', weights_only=True)
        ids = tok.encode(selected['nonempty_probe_text'], add_special_tokens=False) + [151645]
        assert ids[:len(opening)] == opening and json.loads(selected['nonempty_probe_text'])['segments']
        assert tok.decode(ids[:-1]) == selected['nonempty_probe_text']
        assert all(x.device.type == 'cpu' for x in prefix.values())
        assert set(prefix) == {'input_ids','attention_mask'}
        assert prefix['input_ids'].shape == prefix['attention_mask'].shape
        rows.append(dict(**selected, request_ref=selected['input_ref'], nonempty_canonical_ids=ids,
                         empty_ids=empty, prefix_tokens=prefix['input_ids'].shape[1],
                         original_proposal_tokenization_changed=ids != selected['nonempty_probe_ids']))
    save(root/'prepared29.json', dict(status='PASS_FIRST_FIXED8_NEW_PROBABILITY_SUFFIX_INPUTS',
         samples=rows, opening_ids=opening, empty_ids=empty, first_common_ids=opening[:2],
         new_image_or_processor_calls=0, old_actual_pixel_input_QA_adopted=True,
         new_human_or_quality_based_selection=False, reference_labels_not_in_prompt=True))


def generate_probe(root):
    import torch
    reg = read(root/'registration29.json')
    prepared = read(bound(reg['prepared_ref']))
    assert prepared['status'] == 'PASS_FIRST_FIXED8_NEW_PROBABILITY_SUFFIX_INPUTS'
    assert os.environ.get('CUDA_VISIBLE_DEVICES') not in (None,'')
    for name, r in reg['code'].items():
        assert bound(r) == Path(__file__).resolve().parent/name
    for r in reg['adopted_code'].values():
        bound(r)
    save(root/'gpu_claim29.json', dict(pid=os.getpid(), registration_ref=ref(root/'registration29.json')))
    W = Path('/home/inspur/aic_video_work')
    P = W/'bottleneck_24h_20261019_v1'
    N = P/'summary_objective_v20'
    RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    sys.path.insert(0,str(N/'evaluation_code21'))
    from summary_contract import build_pixels, signature
    from summary_grammar6 import PrefixConstraint, ascii_token_candidates
    from summary_generate import DevInputs
    runtime = module('probe29_training_runtime', N/'code/summary_runtime.py')
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    from transformers import Qwen3VLForConditionalGeneration, AutoTokenizer
    from peft import PeftModel, get_peft_model_state_dict
    from peft.utils.save_and_load import set_peft_model_state_dict
    from safetensors.torch import load_file
    from fractions import Fraction
    from datetime import datetime, timezone
    started = time.monotonic()
    def deadline():
        assert datetime.now(timezone.utc) < datetime.fromisoformat(reg['main_cutoff_utc'].replace('Z','+00:00'))
        assert time.monotonic()-started < reg['max_gpu_seconds']
    cfg = read(bound(reg['model_config_ref']))
    tok = AutoTokenizer.from_pretrained(reg['model_directory'],local_files_only=True)
    candidates = ascii_token_candidates(tok)
    base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=cfg['model_revision'],
        local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,
        attn_implementation='sdpa')
    for p in base.parameters():
        p.requires_grad_(False)
    base_before = canonical_frozen_hash(base,torch)
    assert base_before['sha256'] == cfg['expected_base_sha256']
    weights = {role:bound(reg[role+'_weights_ref']) for role in ('original','trained')}
    model = PeftModel.from_pretrained(base,str(weights['original'].parent),adapter_name='original',is_trainable=False)
    model.load_adapter(str(weights['trained'].parent),adapter_name='trained',is_trainable=False)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    parameter_count = sum(p.numel() for p in model.parameters())
    assert parameter_count == 8797794544 and parameter_count <= 9000000000
    load_diagnostics = {}
    for role in weights:
        actual = get_peft_model_state_dict(model,adapter_name=role)
        saved = load_file(str(weights[role]),device='cpu')
        assert set(actual) == set(saved)
        mismatches = [k for k in actual if not torch.equal(actual[k].detach().cpu(),saved[k].to(actual[k].dtype))]
        rounded_matches = sum(torch.equal(actual[k].detach().cpu(),saved[k].to(torch.bfloat16).to(actual[k].dtype)) for k in mismatches)
        load_diagnostics[role] = dict(matrices=len(actual),pre_restore_mismatches=len(mismatches),
            mismatches_equal_saved_bfloat16_roundtrip=rounded_matches,
            actual_dtypes=dict(Counter(str(v.dtype) for v in actual.values())),
            saved_dtypes=dict(Counter(str(v.dtype) for v in saved.values())))
        save(root/('adapter_load_diagnostic31_'+role+'.json'),load_diagnostics[role])
        assert reg['runtime_precision_recovery_from_ref'] and rounded_matches == len(mismatches), 'Unexplained model difference; stop before any forward'
        # PEFT 0.17.1 adds the second adapter in base dtype, loads, then upcasts.
        # Reload the same bound FP32 saved state into the now-FP32 slots.
        assert all(v.dtype == torch.float32 for v in actual.values())
        set_peft_model_state_dict(model,saved,adapter_name=role)
        restored = get_peft_model_state_dict(model,adapter_name=role)
        assert all(torch.equal(restored[k].detach().cpu(),saved[k]) for k in saved)
        load_diagnostics[role]['post_restore_all288_bit_equal_saved'] = True
        del actual,saved,restored
    save(root/'exact_adapter_load_acceptance31.json',dict(status='PASS_BOTH_ADAPTERS_EXACT_SAVED_FP32_BEFORE_ANY_FORWARD',
         roles=load_diagnostics,source_weights_files_modified=False,old_failed_attempt_forwards=0))
    train = read(bound(reg['training_prepared_ref']))
    sources = {x['id']:x for x in read(bound(train['source_catalog']))['sources']}
    train_cache = {}
    dev_reg = read(N/'summary_generation_registration_10.json')
    dev = DevInputs(dev_reg)
    def inputs(row):
        if row['domain'] == 'development':
            return dev.get(row['request_ref'])
        request = read(bound(row['request_ref']))
        sid = request['sid']
        if sid not in train_cache:
            frames,grid,ordinals = runtime.source_pixels(sources[sid])
            clock = read(bound(sources[sid]['clock']))
            train_cache[sid] = (frames,grid,ordinals,clock)
        frames,grid,ordinals,clock = train_cache[sid]
        plan = request['plan']
        values,actual_plan = build_pixels(frames,grid,ordinals,clock['normalized_exact_pts'],
            plan['window_start_exact'],plan['window_end_exact'],
            dict(source_id=sid,source_sha256=request['source_sha256']))
        assert actual_plan == plan
        values.update(torch.load(bound(request['prefix_ref']),map_location='cpu',weights_only=True))
        assert signature(values) == request['input_signature']
        return request,values
    results = []
    number = 0
    for row in prepared['samples']:
        request,values = inputs(row)
        duration = Fraction(request['plan']['window_end_exact'])-Fraction(request['plan']['window_start_exact'])
        constraint = PrefixConstraint(tok,0,duration,max_segments=6,candidate_token_ids=candidates,
                                      eos_token_ids=[151645],allow_empty=True)
        prefix_size = values['input_ids'].shape[1]
        opening = prepared['opening_ids']
        def decision(logits, generated_prefix):
            allowed = constraint(0,list(generated_prefix))
            lp = torch.log_softmax(logits.float(),-1)
            normalizer = torch.logsumexp(lp[allowed],0)
            text = tok.decode(generated_prefix,clean_up_tokenization_spaces=False)
            groups = {'empty':[],'nonempty':[],'undecided':[]}
            for t in allowed:
                continuation = tok.decode(list(generated_prefix)+[t],clean_up_tokenization_spaces=False)
                remaining = continuation[len('{"segments":['):] if continuation.startswith('{"segments":[') else ''
                kind = 'nonempty' if remaining.startswith('[') else 'empty' if remaining.startswith(']') else 'undecided'
                groups[kind].append(t)
            mass = {k:(float(torch.exp(torch.logsumexp(lp[v],0)-normalizer).cpu()) if v else 0.) for k,v in groups.items()}
            ranked = sorted(allowed,key=lambda t:float(lp[t]),reverse=True)[:5]
            return dict(prefix_ids=list(generated_prefix),prefix_text=text,grammar_normalized_branch_mass=mass,
                legal_mass_unmasked=float(torch.exp(normalizer).cpu()),
                top_legal=[dict(id=t,text=tok.decode([t]),log_probability=float(lp[t].cpu())) for t in ranked],
                canonical_empty_route_log_probability=float(lp[prepared['empty_ids'][2]].cpu()),
                canonical_nonempty_route_log_probability=float(lp[opening[2]].cpu()))
        per_role = {}
        for role in ('original','trained'):
            deadline()
            model.set_adapter(role)
            for p in model.parameters():
                p.requires_grad_(False)
            layers = [m for m in model.modules() if hasattr(m,'lora_A')]
            assert len(layers)==144 and all(list(m.active_adapters)==[role] and not m.disable_adapters for m in layers)
            per_suffix = {}
            for kind,suffix in [('nonempty',row['nonempty_canonical_ids']),('empty',row['empty_ids'])]:
                deadline()
                tokens = runtime.build_training_tokens(values,suffix)
                gpu = {k:v.to('cuda:0') for k,v in values.items() if k not in ('input_ids','attention_mask')}
                gpu.update(input_ids=tokens['full_input_ids'].to('cuda:0'),attention_mask=tokens['attention_mask'].to('cuda:0'))
                with (root/'forward_journal29.jsonl').open('a') as log:
                    log.write(json.dumps(dict(event='BEGIN_NEW_PROBABILITY_FORWARD',uid=row['uid'],role=role,suffix=kind))+'\n')
                    log.flush(); os.fsync(log.fileno())
                with torch.inference_mode():
                    hidden = model.get_base_model().model(**gpu,use_cache=False,return_dict=True).last_hidden_state
                    logits = model.get_base_model().lm_head(hidden.index_select(1,tokens['causal_logits_indices'].to('cuda:0'))).float()[0]
                    targets = tokens['targets'][0].to('cuda:0')
                    ce = torch.nn.functional.cross_entropy(logits,targets,reduction='none')
                    record = dict(tokens=len(suffix),token_CE=ce.detach().cpu().tolist(),
                        mean_CE=float(ce.mean().cpu()),sum_CE=float(ce.sum().cpu()),
                        common_prefix_decision=decision(logits[2],prepared['first_common_ids']))
                    if kind == 'nonempty':
                        record['canonical_opening_decision'] = decision(logits[len(opening)],opening)
                    per_suffix[kind] = record
                save(root/('forward29_%s_%s_%s.json'%(row['uid'],role,kind)),
                     dict(uid=row['uid'],role=role,suffix=kind,request_ref=row['request_ref'],
                          suffix_ids=suffix,measurements=record))
                number += 1
                del gpu,hidden,logits,targets,ce,tokens
            per_role[role] = per_suffix
            assert all(p.grad is None and not p.requires_grad for p in model.parameters())
        value = dict(uid=row['uid'],sid=row['sid'],domain=row['domain'],stratum=row['stratum'],
                     human_empty_fraction=row.get('human_empty_fraction'),roles=per_role)
        results.append(value)
        save(root/('probabilities29_'+row['uid']+'.json'),value)
        print(json.dumps(dict(event='PROBE_INPUT_COMPLETE',uid=row['uid'],new_forwards=number)),flush=True)
    assert number == 32 and len(results) == 8
    assert canonical_frozen_hash(model,torch)==base_before
    for role in weights:
        assert ref(weights[role])==reg[role+'_weights_ref']
    save(root/'probability_completion29.json',dict(status='COMPLETE_FIXED8_TWO_ADAPTER32_PROBABILITY_FORWARDS',
         results=results,actual_new_forwards=number,free_generations=0,optimizer_updates=0,
         media_decode_processor_calls=0,parameters_resident=parameter_count,base_unchanged=True,
         adapter_weights_unchanged=True,elapsed_seconds=time.monotonic()-started,
         raw_answer_length_NLL_not_candidate_quality=True,all_samples_exposed_not_blind=True,
         no_automatic_production_or_package=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--phase',choices=['prepare','probe'],required=True)
    args = parser.parse_args()
    try:
        (prepare if args.phase=='prepare' else generate_probe)(args.root)
    except BaseException as error:
        save(args.root/('%s_failure29_%s.json'%(args.phase,os.getpid())),dict(error=repr(error),traceback=traceback.format_exc(),
             successful_files_preserved=True,automatic_retry=False))
        raise
