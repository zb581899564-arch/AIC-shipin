"""First16 exact token inputs: correct versus fixed half-window audio shift."""
import json
import torch
from common import ROOT, read, write, checked, reference
from context import legacy


def main():
    from transformers import AutoTokenizer
    registration, old, module = legacy()
    from summary_contract import signature, MAX_SEQUENCE_TOKENS, MAX_ANSWER_TOKENS
    descriptor_refs = read(ROOT/'first_event_output_acceptance.json')['rows']
    descriptors = [read(checked(value)) for value in descriptor_refs]
    cfg = read(checked(old['model_config_ref']))
    tokenizer = AutoTokenizer.from_pretrained(cfg['model_dir'], local_files_only=True)
    cache = module.VisualCache(old, {row['sid'] for row in descriptors})
    folder = ROOT/'text_inputs';folder.mkdir()
    tail = '<|im_end|>\n<|im_start|>assistant\n'
    rows = []
    for desc, desc_ref in zip(descriptors, descriptor_refs):
        request, original = cache.get(desc['input']['request_ref'])
        text = request['text']['expanded_text']
        if not text.endswith(tail) or text.count(tail) != 1:
            raise ValueError('Original accepted prompt suffix changed')
        if tokenizer.encode(text, add_special_tokens=False) != original['input_ids'][0].tolist():
            raise ValueError('Original text/token identity differs')
        for condition in ['correct', 'shifted']:
            audio = desc[condition+'_block']
            expanded = text[:-len(tail)]+audio+tail
            encoded = tokenizer(expanded, add_special_tokens=False, return_tensors='pt', truncation=False)
            prefix = {key:encoded[key].contiguous() for key in ['input_ids', 'attention_mask']}
            if prefix['input_ids'].shape[1]+MAX_ANSWER_TOKENS > MAX_SEQUENCE_TOKENS:
                raise ValueError('New exact input token budget exceeded')
            previous = tokenizer.encode(text[:-len(tail)], add_special_tokens=False)
            if prefix['input_ids'][0, :len(previous)].tolist() != previous:
                raise ValueError('Appending events altered original video-token text')
            values = dict(original);values.update(prefix)
            sig = signature(values)
            if any(sig[key] != request['input_signature'][key] for key in ['pixel_values_videos', 'video_grid_thw']):
                raise ValueError('Audio ablation changed visual tensor or time groups')
            target = folder/(desc['uid']+'_'+condition+'.pt');torch.save(prefix, target)
            saved = torch.load(target, map_location='cpu', weights_only=True)
            if not all(torch.equal(saved[key], value) for key, value in prefix.items()):
                raise ValueError('First augmented prefix save/load differs')
            row = dict(uid=desc['uid'], sid=desc['sid'], condition=condition,
                request_ref=desc['input']['request_ref'], prefix_ref=reference(target),
                input_signature=sig, descriptor_ref=desc_ref, expanded_text=expanded)
            target = folder/(desc['uid']+'_'+condition+'.json');write(target, row)
            rows.append(reference(target))
    write(ROOT/'text_input_acceptance.json', dict(status='PASS16_FIRST_AUDIO_TEXT_NATIVE_INPUTS',
        rows=rows, sources=len({row['sid'] for row in descriptors}),
        original_pixel_tensors_unchanged=True, new_decode_or_processor=0,
        no_labels_or_old_outputs_in_audio_descriptors=True))
    print('PASS_FIRST16_AUGMENTED_CPU_INPUTS', flush=True)


if __name__ == '__main__':
    main()
