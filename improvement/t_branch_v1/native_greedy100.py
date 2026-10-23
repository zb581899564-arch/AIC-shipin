"""One actual finite-codec call per model-state/input signature, with aliases."""
import time

import torch

from native_codec98 import NativeChoices
from native_input99 import values
from native_render100 import render
from t_io import check, identity, read, save


def generate(model, tokenizer, rt, source, case, proof, code, state, role, folder, cache):
    row = read(check(proof)); key = state + '/' + row['physical_input_key']
    folder.mkdir(); rule = NativeChoices(row['input_tokens'], code)
    previous = cache.get(key)
    if previous is None:
        actual = values(case, proof, tokenizer, rt)
        gpu = {k: v.cuda() if torch.is_tensor(v) else v for k, v in actual.items()}
        signature = rt.tensor_signature({k: v.cpu() if torch.is_tensor(v) else v for k, v in gpu.items()})
        if signature != row['actual_signature']:
            raise ValueError('Actual native action GPU transfer differs from first CPU input')
        model.eval(); started = time.monotonic()
        with torch.inference_mode():
            result = model.generate(**gpu, do_sample=False, num_beams=1, max_new_tokens=65,
                repetition_penalty=1., use_cache=True, prefix_allowed_tokens_fn=rule,
                return_dict_in_generate=True, output_scores=True)
        tokens = result.sequences[0, row['input_tokens']:].tolist()
        selected = rule.parse(tokens); allowed, scores = [], []
        for j, score in enumerate(result.scores):
            domain = rule.allowed(tokens[:j]); allowed.append(domain)
            projected = score[0, torch.tensor(domain, device=score.device)].detach().float().cpu()
            if not torch.isfinite(projected).all():
                raise ValueError('Actual finite native action domain has a nonfinite logit')
            scores.append(projected.tolist())
        raw = folder / 'raw.json'
        save(raw, dict(tokens=tokens, text=tokenizer.decode(tokens, skip_special_tokens=True,
            clean_up_tokenization_spaces=False), prefix=row['input_tokens'], codec=code,
            actual_input=proof, actual_GPU_signature=signature, actual_model_state=state,
            model_role=role, allowed=allowed, allowed_logits=scores,
            seconds=time.monotonic() - started, no_human_reference_in_input=True))
        ref, alias = identity(raw), None
        cache[key] = ref
        del result, actual, gpu
    else:
        raw = read(check(previous))
        if (raw['actual_model_state'] != state or raw['actual_GPU_signature'] != row['actual_signature']
                or raw['codec'] != code or raw['prefix'] != row['input_tokens']):
            raise ValueError('Claimed native action physical alias has a different actual task/state')
        selected = rule.parse(raw['tokens']); ref, alias = previous, previous
    accepted = dict(case=case.name, source=source.sid, CPU=proof, original_CPU=case.CPU,
        raw=ref, physical_alias=alias, physical_input_key=row['physical_input_key'],
        actual_model_state=state, model_role=role,
        **render(source, case, row['source_native_cells'], selected))
    path = folder / 'acceptance.json'; save(path, accepted)
    print('NATIVE100_FIRST_OR_ADOPTED', role, case.name, accepted['status'], bool(alias), flush=True)
    return identity(path)
