"""Portable Qwen3-VL image SFT contract; assistant-only loss and exact source pixels."""
import json
from pathlib import Path

import torch
from PIL import Image


def load_rows(path, root):
    root = Path(root).resolve(strict=True)
    rows = [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines()]
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Empty dataset or duplicate row ID')
    for row in rows:
        if [m['role'] for m in row['messages']] != ['user', 'assistant']:
            raise ValueError('Expected one user message and one assistant answer')
        if row['messages'][0]['content'].count('<image>') != len(row['images']):
            raise ValueError('Image placeholders and real images must match exactly')
        answer = json.loads(row['messages'][1]['content'])
        if row['task'] == 'spatial_pixel_crop':
            if set(answer) != {'box_xyw'} or len(answer['box_xyw']) != 3:
                raise ValueError('Wrong crop target')
            if not all(type(v) is int for v in answer['box_xyw']):
                raise ValueError('Crop coordinates must be integer pixels')
        elif row['task'] == 'temporal_tvsum_frame_importance':
            if set(answer) != {'scores'} or len(answer['scores']) != len(row['images']):
                raise ValueError('Wrong temporal target length')
            if not all(type(v) is int and 1 <= v <= 5 for v in answer['scores']):
                raise ValueError('TVSum scores must be integers 1..5')
        else:
            raise ValueError('Unrecognized task')
        for image in row['images']:
            relative = Path(image)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Only contained portable image paths are allowed')
            path = (root / relative).resolve(strict=True)
            if not path.is_relative_to(root):
                raise ValueError('Image escapes dataset root')
    return rows


def typed_messages(row, images):
    text = row['messages'][0]['content']
    parts = text.split('<image>')
    if len(parts) - 1 != len(images):
        raise ValueError('Image count mismatch')
    content = []
    for i, part in enumerate(parts):
        if part:
            content.append({'type': 'text', 'text': part})
        if i < len(images):
            content.append({'type': 'image', 'image': images[i]})
    return [{'role': 'user', 'content': content},
            {'role': 'assistant', 'content': [{'type': 'text', 'text': row['messages'][1]['content']}]}]


class ImageSFTCollator:
    def __init__(self, processor, dataset_root, max_tokens=16384, image_loader=None):
        self.processor = processor
        self.root = Path(dataset_root)
        self.max_tokens = max_tokens
        self.image_loader = image_loader

    def _images(self, row):
        if self.image_loader is not None:
            return self.image_loader(row)
        images = []
        for path in row['images']:
            with Image.open(self.root / path) as im:
                rgb = im.convert('RGB')
                rgb.load()
                images.append(rgb)
        return images

    def encode(self, row):
        images = self._images(row)
        messages = typed_messages(row, images)
        full = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prefix = self.processor.apply_chat_template(messages[:1], tokenize=False, add_generation_prompt=True)
        encoded = self.processor(text=[full], images=images, return_tensors='pt', padding=False)
        prompt = self.processor(text=[prefix], images=images, return_tensors='pt', padding=False)
        ids = encoded['input_ids']
        n = prompt['input_ids'].shape[1]
        if ids.shape[1] > self.max_tokens:
            raise ValueError(f'No silent truncation: {ids.shape[1]} > {self.max_tokens}')
        if n >= ids.shape[1] or not torch.equal(ids[:, :n], prompt['input_ids']):
            raise ValueError('Full token sequence must have an exact user/generation prefix')
        labels = ids.clone()
        labels[:, :n] = -100
        labels[encoded['attention_mask'] == 0] = -100
        if not bool((labels != -100).any()):
            raise ValueError('No assistant target tokens')
        if 'pixel_values' not in encoded or 'image_grid_thw' not in encoded:
            raise ValueError('Real image vision tensors missing')
        if encoded['image_grid_thw'].shape[0] != len(images):
            raise ValueError('Vision grids and images disagree')
        encoded['labels'] = labels
        return encoded

    def __call__(self, rows):
        values = [self.encode(r) for r in rows]
        longest = max(v['input_ids'].shape[1] for v in values)
        pad = self.processor.tokenizer.pad_token_id
        if pad is None:
            raise ValueError('Tokenizer must define a padding token')
        batch = {}
        for key, fill in [('input_ids', pad), ('attention_mask', 0), ('labels', -100)]:
            target = values[0][key].new_full((len(values), longest), fill)
            for i, value in enumerate(values):
                n = value[key].shape[1]
                target[i, :n] = value[key][0]
            batch[key] = target
        expected = {'input_ids', 'attention_mask', 'labels', 'pixel_values', 'image_grid_thw'}
        for value in values:
            if set(value) != expected:
                raise ValueError(f'Unexpected processor tensors require explicit handling: {set(value) - expected}')
        for key in ('pixel_values', 'image_grid_thw'):
            batch[key] = torch.cat([v[key] for v in values], dim=0)
        return batch


def decode_output(text, task, image_count=None, source_size=None, ratio=None):
    """Strict JSON parsing. Never clamp, silently fall back, or infer empty as negative."""
    obj = json.loads(text)
    if task == 'temporal_tvsum_frame_importance':
        if set(obj) != {'scores'} or len(obj['scores']) != image_count:
            raise ValueError('Temporal output count mismatch')
        if not all(type(v) is int and 1 <= v <= 5 for v in obj['scores']):
            raise ValueError('Temporal output outside TVSum scale')
        return obj
    if task == 'spatial_pixel_crop':
        if set(obj) != {'box_xyw'} or len(obj['box_xyw']) != 3:
            raise ValueError('Wrong crop output')
        x, y, w = obj['box_xyw']
        if not all(type(v) is int for v in (x, y, w)):
            raise ValueError('Non-integer crop output')
        rw, rh = ratio
        if w <= 0 or w * rh % rw:
            raise ValueError('Crop height must be positive and exact integer')
        h = w * rh // rw
        iw, ih = source_size
        if x < 0 or y < 0 or x + w > iw or y + h > ih:
            raise ValueError('Crop outside source')
        return {'box_xywh': [x, y, w, h]}
    raise ValueError('Unrecognized task')

if __name__ == '__main__':
 import hashlib,importlib.util,transformers
 from transformers import AutoProcessor
 model_path='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/models/Qwen3-VL-8B-Instruct'
 results=[]
 for task,max_pixels,counts in [('spatial_pixel_crop',262144,[1,1]),('temporal_tvsum_frame_importance',65536,[16,3])]:
  proc=AutoProcessor.from_pretrained(model_path,local_files_only=True,min_pixels=4096,max_pixels=max_pixels)
  examples=[]
  for n in counts:
   answer={'box_xyw':[187,4,198]} if task=='spatial_pixel_crop' else {'scores':[1,2,3,4,5,1,2,3,4,5,1,2,3,4,5,1][:n]}
   examples.append({'images':['placeholder.png']*n,'task':task,'messages':[{'role':'user','content':'<image>\n'*n+'Rate frames or return a legal pixel crop. Source size 640x360. '+str(list(range(n)))},{'role':'assistant','content':json.dumps(answer,separators=(',',':'))}]})
  collator=ImageSFTCollator(proc,'.',image_loader=lambda row:[Image.new('RGB',(640,360),(80,100,120)) for _ in row['images']])
  batch=collator(examples)
  assert batch['image_grid_thw'].shape[0]==sum(counts)
  assert bool((batch['labels'][batch['attention_mask']==0]==-100).all())
  for i,row in enumerate(examples):
   supervised=batch['labels'][i][batch['labels'][i]!=-100]
   decoded=proc.tokenizer.decode(supervised,skip_special_tokens=True).strip()
   assert json.loads(decoded)==json.loads(row['messages'][1]['content']),decoded
  results.append({'task':task,'batch_shape':list(batch['input_ids'].shape),'images':sum(counts),'assistant_tokens':[int((x!=-100).sum()) for x in batch['labels']],'pixel_shape':list(batch['pixel_values'].shape),'padding_and_prompt_masked':True,'answer_roundtrip_exact':True,'max_pixels':max_pixels})
 bad=['{"scores": [0]}','{"scores": [6]}','{"scores": [true]}','{"scores": [1,2]}']
 for text in bad:
  try: decode_output(text,'temporal_tvsum_frame_importance',image_count=1)
  except ValueError: pass
  else: raise AssertionError('invalid temporal output accepted')
 try: decode_output('{"box_xyw":[630,0,198]}','spatial_pixel_crop',source_size=(640,360),ratio=(9,16))
 except ValueError: pass
 else: raise AssertionError('out-of-bounds crop accepted')
 assert decode_output('{"box_xyw":[187,4,198]}','spatial_pixel_crop',source_size=(640,360),ratio=(9,16))=={'box_xywh':[187,4,198,352]}
 assert not torch.cuda.is_initialized()
 print('READINESS_JSON='+json.dumps({'status':'PASS_REAL_QWEN3VL_PROCESSOR_SYNTHETIC_IMAGE_CONTRACT','processor':proc.__class__.__name__,'transformers':transformers.__version__,'torch':torch.__version__,'model_config_sha256':hashlib.sha256((Path(model_path)/'config.json').read_bytes()).hexdigest(),'cases':results,'CUDA_initialized':False,'model_weights_loaded':False,'optimizer_started':False,'input_pixels':'Synthetic CPU RGB images, not real dataset images','dependencies':{x:bool(importlib.util.find_spec(x)) for x in ['peft','accelerate','safetensors']}}))
