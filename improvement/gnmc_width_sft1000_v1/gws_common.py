"""Independent native16 human spatial SFT research; no production entry."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/gnmc_width_sft1000_iteration_20261013_v1')
PREVIOUS = Path('/home/inspur/aic_video_work/gnmc_width_sft_iteration_20261013_v1')
TRAINOLD = Path('/home/inspur/aic_video_work/gnmc_spatial_sft_iteration_20261013_v1')
OLD = Path('/home/inspur/aic_video_work/gnmc_width_iteration_20261013_v1')
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
PYTHON = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
PROMPT = ('Choose the width of a professional 16:9 crop around the main focal content of this image. '
    'Preserve important subjects and their necessary context; avoid cutting faces, hands, or essential objects. '
    'Remove distracting margins when useful, but do not zoom unnecessarily. '
    'The existing focal-center method will place the crop; you choose only its width. '
    'Width is an integer from 1 to 1000 relative to the largest legal 16:9 crop width: '
    '1000 means retain that maximum width, 500 means half that width. '
    'Keep 1000 when the wider composition is appropriate. Output only JSON: {"width":integer}.')

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))

def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def paths():
    import sys
    sys.path[:0] = [str(RUN/'b_score_aligned_package_v4'),str(RUN/'baseline_a_pts_v1'),
                   str(RUN/'baseline_a_pts_v1/vendor'),str(RUN/'temporal_sft8b_v1')]

def info(values):
    import torch
    return {k:{'shape':list(t.shape),'dtype':str(t.dtype),
        'sha256':hashlib.sha256(t.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()}
        for k,t in values.items()}

def fingerprint(image):
    import numpy as np
    a=np.asarray(image.convert('L').resize((9,8)))
    return sum(int(v)<<i for i,v in enumerate((a[:,1:]>a[:,:-1]).reshape(-1)))

def messages(image):
    return [{'role':'user','content':[{'type':'image','image':image,'max_pixels':131072},
                                    {'type':'text','text':PROMPT}]}]

def encode(processor,image,answer=None):
    from qwen_vl_utils import process_vision_info
    msg=messages(image)
    text=processor.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    imgs,vids=process_vision_info(msg,image_patch_size=16)
    if vids or len(imgs)!=1: raise ValueError('image input identity')
    suffix='' if answer is None else answer+'<|im_end|>\n'
    values=dict(processor(text=[text+suffix],images=imgs,padding=True,truncation=False,return_tensors='pt').items())
    if values['input_ids'].shape[1]>2048: raise ValueError('sequence overflow; truncation forbidden')
    return values,text,suffix

def parse(raw):
    obj=json.loads(raw.strip())
    if set(obj)!={'width'} or type(obj['width']) is not int or not 1<=obj['width']<=1000: raise ValueError('width grammar')
    return obj

def geometry(obj,W,H,center):
    width=max(1,min(W,H*16//9)*obj['width']//1000)
    hf=width*9/16
    return [int(round(max(0,min(center[0]*W-width/2,W-width)))),
            int(round(max(0,min(center[1]*H-hf/2,max(0,math.floor(H-hf+1e-9)))))),width]


def iou(a,b):
    ax,ay,aw,ah=a;bx,by,bw,bh=b
    inter=max(0,min(ax+aw,bx+bw)-max(ax,bx))*max(0,min(ay+ah,by+bh)-max(ay,by))
    union=aw*ah+bw*bh-inter
    return inter/union if union>0 else 0.0

def verify_lock():
    lock=read(ROOT/'source_lock.json')
    for p,h in lock['files'].items():
        if sha(p)!=h: raise ValueError('frozen research input changed: '+p)
    return sha(ROOT/'source_lock.json')
