"""First frozen BASE-role43 on adopted development inputs, no training/labels."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import os
from pathlib import Path
import sys
import time
import traceback

import torch
from summary_generate import DevInputs, read, bound, ref, save, event, sha, RUN
from summary_contract import require
from summary_grammar6 import PrefixConstraint, ascii_token_candidates
from summary_output import parse_summary


def flags(model, disabled):
    layers = [m for m in model.modules() if hasattr(m, 'lora_A')]
    require(len(layers) == 144 and all(set(m.lora_A) == {'summary'} and
        list(m.active_adapters) == ['summary'] and m.disable_adapters == disabled for m in layers),
        'All144 real forward layers must have the registered adapter state')
    require(not any(p.requires_grad for p in model.parameters()), 'Inference parameters frozen')
    return dict(layers=144, disabled=disabled, active_name='summary')


def run(path):
    reg = read(path); root = Path(reg['root']); out = root/'pilot_BASE43'
    require(reg['schema'] == 'FIVE_SUMMARY_BASE_PILOT_V41', 'Exact new pilot registration')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == str(reg['gpu_index']), 'Actual reserved parent CUDA')
    for name, reference in reg['code'].items():
        require(bound(reference) == Path(__file__).resolve().parent/name, 'Executed pilot code binding')
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(registration_ref=ref(path), pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
        argv=Path('/proc/self/cmdline').read_bytes().replace(b'\0', b' ').decode()))
    outputs = []; raw_records = []; start = time.monotonic()
    try:
        sys.path.insert(0, str(RUN/'temporal_sft8b_v1'))
        from sft_contract import verify_live_gpu_reservation
        from verify_saved_smoke import canonical_frozen_hash
        from transformers import Qwen3VLForConditionalGeneration, AutoTokenizer
        from peft import PeftModel, get_peft_model_state_dict
        from safetensors.torch import load_file
        verify_live_gpu_reservation()
        cfg = read(bound(reg['model_config_ref'])); original = bound(reg['initial_TIME_ref'])
        require(str(original.parent) == cfg['b_adapter'] and sha(original) == cfg['b_adapter_sha256'],
                'Original TIME identity, never failed corrected weights')
        inputs = DevInputs(reg)
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=cfg['model_revision'],
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        for p in base.parameters(): p.requires_grad_(False)
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == 8767123696 and before['sha256'] == cfg['expected_base_sha256'],
                'Actual BASE tensor bytes')
        model = PeftModel.from_pretrained(base, str(original.parent), adapter_name='summary', is_trainable=False).eval()
        for p in model.parameters(): p.requires_grad_(False)
        state = get_peft_model_state_dict(model, adapter_name='summary'); stored = load_file(str(original), device='cpu')
        require(set(state) == set(stored) and len(state) == 288 and
                all(state[k].dtype == stored[k].dtype and torch.equal(state[k].detach().cpu(), stored[k]) for k in state),
                'Resident original TIME must equal saved FP32 exactly')
        del state, stored
        require(sum(p.numel() for p in model.parameters()) == 8782459120 <= 9000000000, 'Shared BASE+TIME actual parameters')
        flags(model, False)
        tok = AutoTokenizer.from_pretrained(cfg['model_dir'], local_files_only=True)
        eos = tok.convert_tokens_to_ids('<|im_end|>'); require(eos == 151645, 'Actual terminal EOS')
        allowed = ascii_token_candidates(tok)
        with model.disable_adapter():
            flags(model, True)
            for reference in inputs.prepared['inputs']:
                require(datetime.now(timezone.utc) < datetime.fromisoformat(reg['model_start_cutoff_utc'].replace('Z', '+00:00'))
                        and time.monotonic()-start < reg['max_gpu_seconds'], 'Registered call/time budget')
                request, values = inputs.get(reference); uid = request['uid']
                duration = Fraction(request['plan']['window_end_exact'])-Fraction(request['plan']['window_start_exact'])
                prefix = values['input_ids'].shape[1]
                grammar = PrefixConstraint(tok, prefix, duration, max_segments=6, candidate_token_ids=allowed,
                    eos_token_ids=[eos], allow_empty=True)
                state_flags = flags(model, True)
                event(out/'journal.jsonl', 'BEGIN_GENERATION', uid=uid, model_role='BASE', role_flags=state_flags)
                gpu = {k:v.to('cuda:0') for k,v in values.items()}
                with torch.inference_mode():
                    generated = model.generate(**gpu, max_new_tokens=512, do_sample=False, num_beams=1,
                        use_cache=True, eos_token_id=eos, pad_token_id=eos, prefix_allowed_tokens_fn=grammar)
                torch.cuda.synchronize()
                ids = generated[0, prefix:].detach().cpu().tolist()
                rawpath = out/(uid+'.tokens.json')
                save(rawpath, dict(uid=uid, sid=request['sid'], request_ref=reference, generated_ids=ids,
                    model_role='BASE', model_weights_ref=reg['initial_TIME_ref'], role_flags=state_flags))
                raw_records.append(ref(rawpath))
                require(torch.equal(generated[0, :prefix].detach().cpu(), values['input_ids'][0]), 'Actual prefix identity')
                grammar.assert_complete(ids); require(ids and ids[-1] == eos, 'Natural complete output, no forced prefix')
                text = tok.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
                parsed = parse_summary(text, duration)
                output = out/(uid+'.output.json')
                save(output, dict(uid=uid, sid=request['sid'], raw_text=text, generated_ids=ids,
                    raw_token_ref=ref(rawpath), request_ref=reference, model_role='BASE',
                    model_weights_ref=reg['initial_TIME_ref'], active_adapter=False, role_flags=state_flags,
                    parsed_exact_segments=[[str(a), str(b)] for a,b in parsed], grammar_stats=grammar.stats))
                outputs.append(ref(output)); event(out/'journal.jsonl', 'RAW_ACCEPTED', uid=uid, output_ref=outputs[-1])
                del gpu, generated
            flags(model, True)
        flags(model, False)
        require(len(outputs) == 43 and canonical_frozen_hash(model, torch) == before and
                sha(original) == reg['initial_TIME_ref']['sha256'], 'All43 exact, frozen bytes unchanged')
        save(out/'completion.json', dict(status='PASS_ALL43_BASE_SPRINT41', model_role='BASE', outputs=outputs,
            model_weights_ref=reg['initial_TIME_ref'], input_acceptance_ref=reg['first_dev_input_acceptance_ref'],
            base_fingerprint=before, actual_resident_parameters=8782459120, active_adapter=False,
            forward_role_flag_checks=43, restored_TIME_flags=True, optimizer_updates=0,
            old_TIME_unchanged=True, elapsed_seconds=time.monotonic()-start))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), outputs=outputs,
            raw_records=raw_records, automatic_retry=False, failure_to_empty=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--registration', required=True)
    run(parser.parse_args().registration)
