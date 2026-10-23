"""Frozen original TIME,16 first calls, no training or discarded success."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fractions import Fraction
import json
import time
import torch
from common import ROOT, RUN, read, write, checked, reference
from context import legacy


def frozen_model(old):
    sys.path.insert(0, str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    from summary_generate import inventory
    from transformers import Qwen3VLForConditionalGeneration, AutoTokenizer
    from peft import PeftModel, get_peft_model_state_dict
    from safetensors.torch import load_file
    verify_live_gpu_reservation()
    cfg = read(checked(old['model_config_ref']))
    weight = checked(old['initial_TIME_ref'])
    if old['initial_TIME_ref']['sha256'] != cfg['b_adapter_sha256']:
        raise ValueError('Original TIME differs from protected original adapter')
    base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=cfg['model_revision'],
        local_files_only=True, torch_dtype=torch.bfloat16, device_map={'':'cuda:0'},
        low_cpu_mem_usage=True, attn_implementation='sdpa')
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    before = canonical_frozen_hash(base, torch)
    if before['sha256'] != cfg['expected_base_sha256']:
        raise ValueError('BASE fingerprint changed')
    model = PeftModel.from_pretrained(base, str(weight.parent), adapter_name='summary', is_trainable=False).eval()
    saved = load_file(str(weight), device='cpu')
    actual = get_peft_model_state_dict(model, adapter_name='summary')
    if set(saved) != set(actual) or not all(torch.equal(actual[key].cpu(), value.to(actual[key].dtype)) for key,value in saved.items()):
        raise ValueError('Adapter strict save/load identity failed')
    return model, AutoTokenizer.from_pretrained(cfg['model_dir'], local_files_only=True), before, inventory(model)


def generate_one(model, tokenizer, candidates, cache, row, old, folder):
    from summary_contract import signature
    from summary_grammar6 import PrefixConstraint
    from summary_output import parse_summary
    request, values = cache.get(row['request_ref'])
    values.update(torch.load(checked(row['prefix_ref']), map_location='cpu', weights_only=True))
    if signature(values) != row['input_signature']:
        raise ValueError('Actual first input differs from independent CPU lock')
    length = values['input_ids'].shape[1]
    duration = Fraction(request['plan']['window_end_exact'])-Fraction(request['plan']['window_start_exact'])
    constraint = PrefixConstraint(tokenizer, length, duration, max_segments=6,
        candidate_token_ids=candidates, eos_token_ids=[151645], allow_empty=True)
    print('BEGIN_TIME', row['uid'], row['condition'], flush=True)
    with torch.inference_mode():
        generated = model.generate(**{key:value.to('cuda:0') for key,value in values.items()},
            max_new_tokens=512, do_sample=False, num_beams=1, use_cache=True,
            eos_token_id=151645, pad_token_id=151645, prefix_allowed_tokens_fn=constraint)
    torch.cuda.synchronize()
    ids = generated[0, length:].detach().cpu().tolist()
    key = row['uid']+'_'+row['condition']
    raw = folder/(key+'.tokens.json')
    write(raw, dict(uid=row['uid'], condition=row['condition'], generated_ids=ids,
        input_ref=reference(ROOT/'text_inputs'/(key+'.json')), weight_ref=old['initial_TIME_ref']))
    if not torch.equal(generated[0, :length].cpu(), values['input_ids'][0]):
        raise ValueError('Returned prefix changed; raw output retained')
    constraint.assert_complete(ids)
    text = tokenizer.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
    spans = parse_summary(text, duration)
    target = folder/(key+'.json')
    write(target, dict(uid=row['uid'], sid=row['sid'], condition=row['condition'], raw_text=text,
        generated_ids=ids, raw_token_ref=reference(raw), request_ref=row['request_ref'],
        input_ref=reference(ROOT/'text_inputs'/(key+'.json')), weight_ref=old['initial_TIME_ref'],
        parsed_exact_segments=[[str(a),str(b)] for a,b in spans]))
    print('ACCEPTED_TIME', row['uid'], row['condition'], flush=True)
    return reference(target)


def main():
    registration, old, module = legacy()
    from summary_grammar6 import ascii_token_candidates
    rows = [read(checked(value)) for value in read(ROOT/'text_input_acceptance.json')['rows']]
    cache = module.VisualCache(old, {row['sid'] for row in rows})
    model, tokenizer, before, inventory = frozen_model(old)
    from verify_saved_smoke import canonical_frozen_hash
    candidates = ascii_token_candidates(tokenizer)
    folder = ROOT/'time_outputs';folder.mkdir()
    start, outputs = time.monotonic(), []
    for row in rows:
        outputs.append(generate_one(model, tokenizer, candidates, cache, row, old, folder))
    if canonical_frozen_hash(model, torch) != before or checked(old['initial_TIME_ref']) is None:
        raise ValueError('Frozen model changed during no-training ablation')
    write(ROOT/'time_completion.json', dict(status='COMPLETE_ALL16_FIXED_AUDIO_EVENT_TIME_CALLS',
        outputs=outputs, actual_new_calls=len(outputs), original_visual_control_calls_adopted=8,
        optimizer_updates=0, model_inventory=inventory, BASE_fingerprint=before,
        actual_complete_pipeline_parameters=read(ROOT/'model_cpu_acceptance.json')['total_complete_pipeline_parameters'],
        elapsed_seconds=time.monotonic()-start, torch_peak_allocated_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
