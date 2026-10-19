"""Conditional native16 width production contracts. No work occurs on import."""
import argparse
import hashlib
import json
import os
from pathlib import Path

SCHEMA='NATIVE16_WIDTH_PREFIX_PRODUCTION_V1'
DOMAIN='OFFICIAL_NATIVE16_SAME_QUERY_BASE_FEATURES'
QUESTION=('Choose a professional 16:9 crop around the main focal content. '
          'Preserve important subjects and their necessary context, removing distracting margins only when useful. '
          'Consider how much of the largest legal crop width is necessary. Answer with a width from 1 to 1000.')
DONE_SHA='9fad9e7cefd3209952f645ca6294cfc9b9aecaacb105a47dee776ba3056aa683'
HEAD_SHA='0a1cb13e90e48da1a349bf9dfba9f2beca7e9fbc8487ec3451c4148a92e3c954'
NORM_SHA='df64d309fed205402bff5429ad367ab5bf7ad366715d45a7fac407127ec032aa'
BASELINE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
FINAL='PASS_ENGINEERING_FROZEN_HEAD_ONLINE_EFFECT_UNKNOWN'
BACKBONE=8782459120
TOTAL=8782590234


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for data in iter(lambda:handle.read(8<<20),b''):h.update(data)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n');handle.flush();os.fsync(handle.fileno())


def tensor_save(path,value):
    import torch
    with Path(path).open('xb') as handle:torch.save(value,handle);handle.flush();os.fsync(handle.fileno())


def ref(value):
    p=Path(value['path']);require(p.is_absolute() and p.is_file() and sha(p)==value['sha256'],'Missing/changed frozen file '+str(p));return p


def info(values):
    import torch
    return {key:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()) for key,v in sorted(values.items())}


def signature(values):
    """Exact effective single-image input: strips ONLY masked left padding."""
    import torch
    ids,mask=values['input_ids'],values['attention_mask']
    require(ids.ndim==mask.ndim==2 and ids.shape==mask.shape and ids.shape[0]==1 and bool(((mask==0)|(mask==1)).all()) and bool((mask[:,1:]>=mask[:,:-1]).all()) and int(mask[0,-1])==1,'Independent-image effective token/mask domain')
    effective=dict(values)
    effective['input_ids']=ids[:,mask[0].bool()].contiguous();effective['attention_mask']=torch.ones_like(effective['input_ids'])
    require(set(effective)=={'input_ids','attention_mask','pixel_values','image_grid_thw'},'No extra/label tensors in effective inputs')
    return hashlib.sha256(json.dumps(info(effective),sort_keys=True,separators=(',',':')).encode()).hexdigest()


class Context:
    def __init__(self,root):
        self.root=Path(root);require(self.root.is_absolute(),'Explicit absolute --root')
        self.p=read(self.root/'protocol.json');p=self.p
        require(p['schema']==SCHEMA and Path(p['root']).resolve()==self.root.resolve(),'Protocol/CLI root binding')
        self.run=Path(p['run_root']);self.adopted=Path(p['adopted_root'])
        require(self.run.is_absolute() and self.adopted.is_absolute(),'Existing absolute RUN/adopted roots')
        self.done=read(ref(p['training_completion']))
        require(p['training_completion']['sha256']==DONE_SHA and self.done['status']==FINAL and self.done['head_parameters']==32785 and self.done['future_joint_resident_parameters']==TOTAL,'Actual602 final engineering completion, no quality gate')
        chain=read(ref(p['training_chain']));resource=read(ref(p['training_resource']))
        require(chain['status']==FINAL and chain['completion_sha256']==DONE_SHA and chain['resource_sha256']==p['training_resource']['sha256'] and
                chain['first_feature_forwards']==602 and chain['new_head_updates']==200 and chain['production_admitted'] is False and chain['online_effect']=='UNKNOWN','Actual602 natural chain terminal')
        require(resource['status']=='completed' and resource['exit_code']==0,'Actual602 shared GPU completed/exit0')
        self.training=Path(p['training_completion']['path']).parent
        require(self.done['weights_sha256']==HEAD_SHA and sha(self.done['weights_path'])==HEAD_SHA and
                self.done['normalization_sha256']==NORM_SHA and sha(self.done['normalization_path'])==NORM_SHA,'Actual frozen602 final head/normalization')
        require(p['baseline_zip']['sha256']==BASELINE_SHA,'Current40.47 baseline binding');ref(p['baseline_zip'])
        self.cfg=read(ref(p['model_config']));require(Path(p['model_config']['path']).resolve()==(self.run/'b_score_aligned_package_v4/config.json').resolve() and self.cfg['complete_parameters']==BACKBONE,'Existing physical original-B config')
        require(Path(p['adopted_cpu_acceptance']['path']).resolve()==(self.adopted/'cpu_acceptance.json').resolve() and
                Path(p['metadata']['path']).resolve()==(self.adopted/'metadata.json').resolve(),'Original adopted CPU/meta paths')
        self.cpu=read(ref(p['adopted_cpu_acceptance']));self.metadata=read(ref(p['metadata']))
        sources=self.cpu['sources'];records=self.metadata['records']
        require(len(sources)==len(records)==426 and {s['id'] for s in sources}=={r['video_id'] for r in records}=={str(i) for i in range(426)},'Exact adopted426 source identity')
        require(self.cpu['status']=='PASS_ALL_REGISTERED_NEW_FEATURE_INPUTS','Adopted real CPU input acceptance')
        self.sources={s['id']:s for s in sources}
        self.landscape=[r for r in sorted(records,key=lambda r:int(r['video_id'])) if r['targetRatioWH']==[16,9]]
        require(self.landscape and all(r['targetRatioWH'] in ([16,9],[9,16]) for r in records),'Fixed metadata ratio routing only')
        import zipfile
        with zipfile.ZipFile(p['baseline_zip']['path']) as archive:
            require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None,'Current baseline single JSONL/CRC')
            base=[json.loads(line) for line in archive.read('predictions.jsonl').splitlines()]
        keys=[(r['video_id'],x['frame']) for r in base for x in r['predictions']]
        require(len(base)==426 and len(keys)==len(set(keys))==123506 and {r['video_id'] for r in base}=={r['video_id'] for r in records},'Exact current40.47 selected frame set; never use native.baseline')
        self.binding=dict(protocol_sha256=sha(self.root/'protocol.json'),training_completion_sha256=DONE_SHA,baseline_sha256=BASELINE_SHA,
                          adopted_cpu_acceptance_sha256=p['adopted_cpu_acceptance']['sha256'],question_sha256=hashlib.sha256(QUESTION.encode()).hexdigest())

    def claim(self,name):save(self.root/(name+'_started.json'),dict(stage=name,pid=os.getpid(),automatic_resume=False,**self.binding))

    def stage(self,name,status):
        value=read(self.root/(name+'.json'));require(value['status']==status and all(value[k]==v for k,v in self.binding.items()),'Actual frozen '+name+' stage');return value


def cli():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--phase',required=True);args=p.parse_args();return Context(args.root),args.phase


def failure(ctx,phase,error):
    import traceback
    path=ctx.root/(phase+'_failure_%d.json'%os.getpid())
    if not path.exists():save(path,dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,automatic_resume=False))


def cpu_only():
    import torch
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and not torch.cuda.is_initialized(),'CPU child-only CUDA masking required')
    torch.set_num_threads(2)


def one_input(case,index,loaded=None):
    """Reference saved pixels; returns only a CPU view/slice, never disk copies."""
    import torch
    chunk=case['chunk']
    if loaded is None:
        require(sha(chunk['path'])==chunk['sha256'] and sha(case['query_path'])==case['query_sha256'],'Actual adopted pixel/new token bytes')
        original=torch.load(chunk['path'],map_location='cpu',weights_only=True);text=torch.load(case['query_path'],map_location='cpu',weights_only=True)
    else:original,text=loaded
    grid=original['image_grid_thw'];require(grid.tolist()==chunk['grid'] and original['sample_ordinals']==chunk['samples'],'Actual saved image/grid/native order')
    counts=grid.prod(-1).tolist();require(sum(counts)==original['pixel_values'].shape[0] and grid.shape==(len(chunk['samples']),3) and bool((grid[:,0]==1).all()),'Actual adopted patch split')
    lo=sum(counts[:index]);hi=lo+counts[index]
    ids=text['input_ids'][index:index+1];mask=text['attention_mask'][index:index+1]
    return dict(input_ids=ids[:,mask[0].bool()].contiguous(),attention_mask=torch.ones_like(ids[:,mask[0].bool()]),
                pixel_values=original['pixel_values'][lo:hi],image_grid_thw=grid[index:index+1])
