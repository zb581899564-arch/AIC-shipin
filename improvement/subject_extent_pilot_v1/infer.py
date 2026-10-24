"""One exact frozen BASE grounding per external image, no crop-label input."""
import sys
import time
from common import ROOT, paths, read, checked, signature, write, append, ref


def main(role):
    if role != 'dev':
        raise ValueError('This first-stage entry is development only; confirmation requires frozen selection')
    paths()
    import numpy as np
    import torch
    from sft_contract import verify_live_gpu_reservation
    from improvement.final_sprint_v1.qwen_runtime import QwenRuntime
    from improvement.final_sprint_v1.grounding_grammar import GroundingGrammar
    from improvement.final_sprint_v1.spatial import parse_grounding
    verify_live_gpu_reservation()
    acceptance = read(ROOT / (role + '_cpu_acceptance.json'))
    manifest = read(ROOT / (role + '_rows.json'))
    by_id = {r['item_id']: r for r in manifest}
    runtime = QwenRuntime(read(ROOT / 'model_spec.json'))
    runtime.load()
    model, processor = runtime.model, runtime.processor
    grammar = GroundingGrammar(processor.tokenizer)
    started = time.monotonic()
    for item in acceptance['rows']:
        row = by_id[item['item_id']]
        value = torch.load(checked(item['tensor']), map_location='cpu', weights_only=True)
        if signature(value) != item['signature']:
            raise ValueError('Frozen real CPU input identity changed')
        n = value['input_ids'].shape[1]
        t0 = time.monotonic()
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else eos
        with torch.inference_mode():
            output = model.generate(**{k: v.cuda() for k, v in value.items()},
                max_new_tokens=192, do_sample=False,
                prefix_allowed_tokens_fn=grammar.constraint(value['input_ids'][0].tolist(), eos))
        ids = output[0, n:].cpu().tolist()
        raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        # Preserve even a failing raw before strict parser/geometry checks.
        record = dict(item_id=item['item_id'], raw=raw, output_token_ids=ids,
            tensor=item['tensor'], signature=item['signature'], seconds=time.monotonic() - t0,
            role='base', actual_parameters=runtime.inventory['parameter_count'])
        append(ROOT / (role + '_raw.jsonl'), record)
        if not ids or ids[-1] not in eos:
            raise ValueError('Truncated generation is not whole_scene')
        record['grounding'] = parse_grounding(raw)
        # Reuse historical BASE only for identical external source pixels.
        record['baseline'] = row['baseline']
        record['baseline_adopted'] = True
        append(ROOT / (role + '_accepted.jsonl'), record)
        print('GROUNDING_ACCEPTED', role, len(read_lines(ROOT / (role + '_accepted.jsonl'))), flush=True)
    write(ROOT / (role + '_model_completion.json'), dict(status='PASS20_FIRST_BASE_GROUNDING',
        role=role, count=20, seconds=time.monotonic() - started,
        identity=runtime.identity(), peak_gpu_bytes=torch.cuda.max_memory_allocated(),
        raw=ref(ROOT / (role + '_raw.jsonl')), accepted=ref(ROOT / (role + '_accepted.jsonl'))))


def read_lines(path):
    import json
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


if __name__ == '__main__':
    main(sys.argv[1])
