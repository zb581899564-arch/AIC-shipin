"""Frozen CPU/GPU stage contracts. No actions occur on import."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

QUESTION = ('Choose a professional 16:9 crop around the main focal content. '
            'Preserve important subjects and their necessary context, removing distracting margins only when useful. '
            'Consider how much of the largest legal crop width is necessary. Answer with a width from 1 to 1000.')
BACKBONE = 8_782_459_120
HEAD_PARAMETERS = 32_785
SEMANTIC_HEAD_PARAMETERS = 98_329
TRAINING = dict(seed=20261016,hidden_dim=8,updates=200,learning_rate=.001,
                weight_decay=.0001,gradient_clip=1.,normalization_std_min=.001,
                loss='SmoothL1',smooth_l1_beta=.1,scale_min=.001,scale_max=1.,checkpoint='final_only')
TARGET_SOURCE = 'original human native16:9 width quantization'
FINAL_STATUS = 'PASS_ENGINEERING_FROZEN_HEAD_ONLINE_EFFECT_UNKNOWN'


def require(condition, reason):
    if not condition: raise ValueError(reason)


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(8 << 20),b''): h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False); handle.write('\n')
        handle.flush(); os.fsync(handle.fileno())


def tensor_save(path, value):
    import torch
    with Path(path).open('xb') as handle:
        torch.save(value,handle); handle.flush(); os.fsync(handle.fileno())


def required(value, names, scope):
    require(isinstance(value,dict),scope+': object required')
    missing = [name for name in names if name not in value]
    require(not missing,scope+': missing schema fields '+','.join(missing))


def checked_ref(ref):
    required(ref,('path','sha256'),'file reference')
    path = Path(ref['path']); require(path.is_absolute() and path.is_file(),'Missing absolute existing file: '+str(path))
    require(sha(path) == ref['sha256'],'Frozen file SHA differs: '+str(path))
    return path


class Context:
    def __init__(self,root):
        self.root = Path(root)
        require(self.root.is_absolute(),'CLI --root must be absolute')
        self.proto = read(self.root/'protocol.json')
        p = self.proto
        required(p,('schema','root','run_root','model_config','source_manifest_sha256',
                    'original_accepted_journal','original_accepted_journal_sha','training',
                    'risk_exploration','data_use','known_exposure','origin_independence'),'protocol')
        require(p['schema'] == 'SPATIAL_WIDTH_LM602_ONLINE_EXPLORATION_V1' and Path(p['root']).resolve() == self.root.resolve(),'Protocol/CLI root binding')
        require(p['training'] == TRAINING,'Fixed recipe differs; no implicit parameter changes')
        require(p['risk_exploration'] is True and p['data_use']=='studentNC' and p['known_exposure']=='HISTORICALLY_EXPOSED_AUTHOR_TRAIN602' and p['origin_independence']=='UNKNOWN','Explicit research-use/historical-exposure/unknown-origin exploration scope')
        self.run=Path(p['run_root']);require(self.run.is_absolute(),'Existing RUN must be absolute')
        self.manifest_path=checked_ref(dict(path=str(self.root/'source_manifest.json'),sha256=p['source_manifest_sha256']))
        # GPU stages bind the labeled manifest by HASH ONLY, never parse labels.
        self.binding = dict(protocol_sha256=sha(self.root/'protocol.json'),source_manifest_sha256=sha(self.manifest_path))

    def labeled_manifest(self):
        items=read(self.manifest_path)
        require(isinstance(items,list) and len(items)==602,'Exactly original602 train rows in fixed accepted order')
        for item in items:
            required(item,('id','source','source_sha256','target_width','target_source','reference_original_xyxy'),'source manifest row')
            require(isinstance(item['id'],str) and item['id'].startswith('gnmc:train:') and Path(item['source']).is_absolute(),'Original GNMC train identity/JPEG')
            require(type(item['target_width']) is int and 1<=item['target_width']<=1000 and item['target_source']==TARGET_SOURCE,'Original width target/source')
            ref=item['reference_original_xyxy']
            require(len(ref)==4 and all(type(x) in (int,float) and math.isfinite(x) for x in ref) and 0<=ref[0]<ref[2]<=1 and 0<=ref[1]<ref[3]<=1,'Original normalized human reference XYXY')
        require(len({x['id'] for x in items})==602 and len({x['source_sha256'] for x in items})==602,'Duplicate fixed602 identity; no replacement')
        return items

    def model_config(self):
        path = checked_ref(self.proto['model_config'])
        require(path.resolve() == (self.run/'b_score_aligned_package_v4/config.json').resolve(),'Existing original-B config only')
        cfg = read(path); require(cfg['complete_parameters'] == BACKBONE,'Actual configured base+TIME parameter count')
        return cfg

    def claim(self,name):
        save(self.root/(name+'_started.json'),dict(pid=os.getpid(),stage=name,**self.binding,
                                                  success_resume='FORBIDDEN_EXPLICIT_RECOVERY_REQUIRED'))

    def checked_stage(self,name,status):
        value = read(self.root/(name+'.json'))
        require(value['status'] == status and all(value[k] == v for k,v in self.binding.items()),'Missing/frozen '+name+' stage')
        return value


def cli():
    parser = argparse.ArgumentParser(); parser.add_argument('--root',required=True)
    return Context(parser.parse_args().root)


def fail(ctx,stage,error):
    import traceback
    path = ctx.root/(stage+'_failure_%d.json'%os.getpid())
    if not path.exists(): save(path,dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,automatic_resume=False))


def cpu_only():
    import torch
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not torch.cuda.is_initialized(),'CPU child must mask only its own CUDA visibility')
    torch.set_num_threads(2)


def encode(processor,image):
    message = [{'role':'user','content':[{'type':'image','image':image}, {'type':'text','text':QUESTION}]}]
    text = processor.apply_chat_template(message,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    values = dict(processor(text=[text],images=[image],padding=True,truncation=False,return_tensors='pt').items())
    import torch
    require(set(values) == {'input_ids','attention_mask','pixel_values','image_grid_thw'},'Image-only original prefill tensor inventory')
    values = {key:value.contiguous() for key,value in values.items()}
    require(all(value.device.type == 'cpu' for value in values.values()) and values['input_ids'].shape[0] == 1 and
            values['input_ids'].shape == values['attention_mask'].shape and values['input_ids'].shape[1] <= 2048 and
            int(values['attention_mask'][0,-1]) == 1,'Actual CPU one-image token budget/readout')
    require(values['image_grid_thw'].shape == (1,3) and int(values['image_grid_thw'][0,0]) == 1 and
            torch.isfinite(values['pixel_values']).all(),'Actual finite one-image grid/pixels')
    return values,text


def tensor_info(values):
    import torch
    return {key:dict(shape=list(value.shape),dtype=str(value.dtype),
                     sha256=hashlib.sha256(value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
            for key,value in values.items()}


def checked_cpu_sources(ctx):
    accepted=ctx.checked_stage('cpu_acceptance','PASS_602_NEW_PURPOSE_JPEG_RGB_PREFIX_INPUTS')
    sources=accepted['sources']
    require(len(sources)==602 and [s['sample_id'] for s in sources]==['I%04d'%i for i in range(602)] and len({s['id'] for s in sources})==602,'Full original602 sanitized source order')
    for source in sources:
        require(not any(k in source for k in ('target_width','reference_original_xyxy','target','labels')),'No GT in GPU source/input manifests')
        require(source==read(ctx.root/'inputs'/source['sample_id']/'proof.json'),'Actual serialized input proof binding')
    return accepted,sources
