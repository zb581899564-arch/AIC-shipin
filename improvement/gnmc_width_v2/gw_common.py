import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/gnmc_width_iteration_20261013_v1')
OUT = ROOT / 'recovery_01'
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
PYTHON = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
WIDTH_PROMPT = ('Choose the width of a professional 16:9 crop around the main focal content of this image. '
    'Preserve important subjects and their necessary context; avoid cutting faces, hands, or essential objects. '
    'Remove distracting margins when useful, but do not zoom unnecessarily. '
    'The existing focal-center method will place the crop; you choose only its width. '
    'Width is an integer from 1 to 1000 relative to the largest legal 16:9 crop width: '
    '1000 means retain that maximum width, 500 means half that width. '
    'Keep 1000 when the wider composition is appropriate. Output only JSON: {"width":integer}.')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def paths():
    import sys
    sys.path[:0] = [str(RUN/'b_score_aligned_package_v4'), str(RUN/'baseline_a_pts_v1'),
                   str(RUN/'baseline_a_pts_v1/vendor'), str(RUN/'temporal_sft8b_v1')]

def tensor_info(values):
    import torch
    return {k: {'shape': list(t.shape), 'dtype': str(t.dtype),
        'sha256': hashlib.sha256(t.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()}
        for k,t in values.items()}

def width_value(raw):
    obj = json.loads(raw.strip())
    if set(obj) != {'width'} or type(obj['width']) is not int or not 1 <= obj['width'] <= 1000:
        raise ValueError('width must be the registered 1..1000 integer JSON')
    return obj['width']

def geometry(center, W, H, permille):
    largest = min(W, H*16//9)
    w = max(1, largest*permille//1000)
    hf = w*9/16
    xmax, ymax = W-w, max(0, math.floor(H-hf+1e-9))
    x = min(xmax, round(max(0, min(center[0]*W-w/2, xmax))))
    y = min(ymax, round(max(0, min(center[1]*H-hf/2, ymax))))
    return [int(x), int(y), int(w)]

def prompt_messages(image):
    return [{'role':'user','content':[{'type':'image','image':image,'max_pixels':131072},
                                    {'type':'text','text':WIDTH_PROMPT}]}]

def encode(processor, messages):
    from qwen_vl_utils import process_vision_info
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    images, videos = process_vision_info(messages, image_patch_size=16)
    if videos or len(images) != 1: raise ValueError('exactly one original static image is required')
    result = processor(text=[text], images=images, padding=True, truncation=False, return_tensors='pt')
    if result.input_ids.shape[1] > 16384: raise ValueError('untruncated input exceeds token budget')
    return dict(result.items()), text
