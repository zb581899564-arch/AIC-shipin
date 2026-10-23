"""One frozen original TIME pass per complete native-control/event-memory input."""
from fractions import Fraction
import time

import torch

from causal_policy32 import actual_allowed_states
from development_data46 import development_sources
from event_native71 import bindings, constraint
from event_select72_common import ARMS, CPU, OUT, values
from frozen_branch46 import RUN
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime


def generate(model, tokenizer, rt, source, case, arm, task, candidates, folder):
    folder.mkdir()
    actual = values(case, task, rt, tokenizer)
    signature = rt.tensor_signature(actual)
    gpu = {k: v.cuda() if torch.is_tensor(v) else v for k, v in actual.items()}
    if rt.tensor_signature({k: v.cpu() if torch.is_tensor(v) else v for k, v in gpu.items()}) != signature:
        raise ValueError('Actual GPU-native input differs from its first CPU binding')
    prefix = actual['input_ids'].shape[1]
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    rule = constraint(tokenizer, prefix, case, source, eos, candidates)
    save(folder / 'request.json', dict(case=case.name, arm=arm, original_CPU=case.CPU,
        actual_input_proof=task, actual_GPU_input_signature=signature,
        prospective_native_grammar=True, no_human_labels_in_input=True))
    started = time.monotonic()
    with torch.inference_mode():
        result = model.generate(**gpu, do_sample=False, num_beams=1, max_new_tokens=256,
            repetition_penalty=1., prefix_allowed_tokens_fn=rule,
            return_dict_in_generate=True, output_scores=True)
    tokens = result.sequences[0, prefix:].tolist()
    text = tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    save(folder / 'raw.json', dict(tokens=tokens, text=text, prefix=prefix, eos=eos,
                                  seconds=time.monotonic() - started))
    allowed = actual_allowed_states(actual['input_ids'], tokens, rule)
    projected = [score[0, torch.tensor(ids, device=score.device)].detach().float().cpu()
                 for score, ids in zip(result.scores, allowed)]
    path = folder / 'allowed.pt'
    with path.open('xb') as stream:
        torch.save(dict(scores=projected, allowed=allowed, tokens=tokens), stream)
    rule.assert_complete(torch.tensor(tokens, dtype=torch.long))
    segments, errors, warnings = rt.parse_segments(text,
        Fraction(case.meta['window_end']) - Fraction(case.meta['window_start']), allow_empty=True)
    if segments is None or errors:
        raise ValueError('Actual constrained selector failure is not a legal empty')
    row = dict(case=case.name, arm=arm, original_CPU=case.CPU, actual_input_proof=task,
        raw=identity(folder / 'raw.json'), allowed_scores=identity(path), tokens=tokens,
        segments=segments, warnings=warnings, status='MODEL_OK' if segments else 'LEGAL_EMPTY')
    save(folder / 'acceptance.json', row)
    print('EVENT72_FIRST_NATIVE_GREEDY', arm, case.name, len(segments), flush=True)
    return identity(folder / 'acceptance.json')


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    for ref in lock['native_grammar'].values():
        check(ref)
    cpu = read(check(lock['complete_actual_CPU']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Original shared BASE/TIME parameter count differs')
    model.set_adapter('default'); model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    _, grammar = bindings(); candidates = grammar.ascii_token_candidates(processor.tokenizer)
    folder = OUT / 'outputs'; folder.mkdir(); outputs = {}
    for sid, source in sources.items():
        outputs[sid] = {}
        for arm in ARMS:
            outputs[sid][arm] = {}
            for case in source.cases:
                outputs[sid][arm][case.name] = generate(model, processor.tokenizer, rt, source, case, arm,
                    cpu['inputs'][sid][arm][case.name], candidates, folder / (arm + '_' + case.name))
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original BASE/TIME changed')
    save(OUT / 'GPU_completion.json', dict(state='FIRST150_NATIVE_EVENT_MEMORY_GREEDY_COMPLETE_NEEDS_CPU',
        outputs=outputs, actual_first_generations=150, original_weights_unchanged=True,
        prospective_full40_48_plus_ASR_parameters=8853994586,
        new_training=0, peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
