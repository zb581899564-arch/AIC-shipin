"""One shared image processor cache; no labels enter the BASE center prompt."""
import hashlib
import json
import numpy as np
import torch
from PIL import Image
from common import ROOT, RUN, TRAIN200, EXPAND, checked, read, ref, write, append, runtime_paths, signatures


def main():
    runtime_paths()
    from transformers import AutoProcessor
    from qwen_vl_utils import process_vision_info
    from spatial_baseline import Qwen3VL
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    rows = read(ROOT / 'cohort.json')['rows']
    (ROOT / 'pixels').mkdir()
    accepted = []
    for row in rows:
        array = np.load(checked(row['rgb']), allow_pickle=False)
        if hashlib.sha256(array.tobytes()).hexdigest() != row['RGB_sha256']:
            raise ValueError('Recovered RGB bytes differ from original accepted source')
        messages = []
        class Capture:
            max_pixels = 131072
            def _generate(self, values, limit):
                messages.extend(values)
                return ''
        Qwen3VL.predict_focus(Capture(), Image.fromarray(array), [16, 9], 96)
        template = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        images, videos = process_vision_info(messages, image_patch_size=16)
        if videos or len(images) != 1:
            raise ValueError('Single image contract')
        inputs = dict(processor(text=[template], images=images, padding=True, truncation=False, return_tensors='pt').items())
        if inputs['input_ids'].shape[1] >= 2048:
            raise ValueError('No input truncation')
        key = row['item_id'].replace(':', '_')
        target = ROOT / 'pixels' / f'{key}.pt'
        with target.open('xb') as stream:
            torch.save(inputs, stream)
        saved = torch.load(target, map_location='cpu', weights_only=True)
        sig = signatures(inputs)
        if signatures(saved) != sig:
            raise ValueError('First processor save/reload differs')
        item = dict(item_id=row['item_id'], role=row['role'], tensor=ref(target), signature=sig,
                    image_token_count=int((inputs['input_ids'] == processor.tokenizer.convert_tokens_to_ids('<|image_pad|>')).sum()))
        append(ROOT / 'pixels_journal.jsonl', item)
        accepted.append(item)
        if len(accepted) % 100 == 0:
            print('CPU_IMAGE_INPUT', len(accepted), flush=True)
    if len(accepted) != 762 or torch.cuda.is_initialized():
        raise ValueError('CPU input denominator/CUDA contract')
    write(ROOT / 'pixel_acceptance.json', dict(status='PASS762_FIRST_SHARED_CPU_PIXELS_AND_BASE_CENTER_PREFIX', rows=accepted,
         cohort=ref(ROOT / 'cohort.json'), original_expired_cache_reconstructed_explicitly=True,
         old_successful_pixels_rewritten=False, actual_processor_calls=762, CUDA_initialized=False))


if __name__ == '__main__':
    main()
