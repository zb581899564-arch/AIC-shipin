"""Pure mask construction and bound cached-input I/O. Never masks CUDA or launches work."""
import hashlib
import json
import os
from pathlib import Path
import torch
from summary_contract import require, signature, build_pixels, MAX_SEQUENCE_TOKENS
WORK=Path('/home/inspur/aic_video_work')


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8 << 20), b''): result.update(block)
    return result.hexdigest()


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(WORK) and path.is_file() and sha(path) == reference['sha256'], 'Bound input bytes changed/outside workspace: '+str(path))
    return path


def ref(path):
    path=Path(path).resolve(strict=True)
    return dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size)


def build_training_tokens(prefix, suffix):
    """Batch1 prefix + complete answer/EOS; only suffix is causally supervised."""
    ids = prefix['input_ids'] if isinstance(prefix,dict) else prefix
    require(ids.device.type == 'cpu' and ids.dtype == torch.int64 and ids.ndim == 2 and
            ids.shape[0] == 1 and ids.shape[1] > 0, 'CPU batch1 int64 prefix required')
    if isinstance(prefix,dict):
        mask=prefix['attention_mask']
        require(mask.shape == ids.shape and mask.dtype == torch.int64 and bool((mask == 1).all()), 'Unpadded prefix mask required')
    require(isinstance(suffix,list) and suffix and all(type(v) is int and v >= 0 for v in suffix), 'Nonempty exact suffix token list required')
    tail=torch.tensor([suffix],dtype=torch.int64);size=ids.shape[1]
    full=torch.cat((ids,tail),dim=1).contiguous()
    require(full.shape[1] <= MAX_SEQUENCE_TOKENS, 'Complete supervised sequence budget')
    labels=torch.full_like(full,-100);labels[:,size:]=tail
    return dict(full_input_ids=full,attention_mask=torch.ones_like(full),labels=labels,
                causal_logits_indices=torch.arange(size-1,full.shape[1]-1,dtype=torch.int64),targets=tail)


def validate_training_tokens(prefix, suffix, actual, eos_token_id=None):
    """Independent first mask/causal-shift oracle, including terminal EOS supervision."""
    ids=prefix['input_ids'] if isinstance(prefix,dict) else prefix
    p=ids.shape[1];total=p+len(suffix)
    require(set(actual)=={'full_input_ids','attention_mask','labels','causal_logits_indices','targets'}, 'Exact training token helper keys')
    full,mask,labels=actual['full_input_ids'],actual['attention_mask'],actual['labels']
    require(full.shape==mask.shape==labels.shape==(1,total) and
            full.dtype==mask.dtype==labels.dtype==torch.int64 and bool((mask==1).all()), 'Full training batch geometry')
    require(torch.equal(full[:,:p],ids) and full[0,p:].tolist()==suffix, 'Prefix/suffix concatenation identity')
    require(labels[0,:p].tolist()==[-100]*p and labels[0,p:].tolist()==suffix,
            'Prefix fully ignored; every suffix token including EOS supervised')
    positions=actual['causal_logits_indices']
    require(positions.dtype==torch.int64 and positions.tolist()==list(range(p-1,total-1)) and
            actual['targets'].shape==(1,len(suffix)) and actual['targets'][0].tolist()==suffix,
            'Exact causal predecessor indices and all suffix targets')
    require(labels[:,1:][:,positions].tolist()==[suffix], 'Independent conventional shifted label selection')
    if eos_token_id is not None: require(suffix[-1]==eos_token_id and labels[0,-1].item()==eos_token_id, 'EOS must remain supervised')
    return dict(status='PASS_FIRST_EXACT_SUFFIX_MASK_CAUSAL_SHIFT_EOS',prefix_tokens=p,
                supervised_tokens=len(suffix),total_tokens=total,eos_checked=eos_token_id is not None)


def source_pixels(source):
    frames,grids,ordinals=[],[],[]
    for chunk in source['chunks']:
        payload=torch.load(bound(chunk),map_location='cpu',weights_only=True)
        pixels,grid=payload['pixel_values'],payload['image_grid_thw']
        require(list(pixels.shape)==chunk['pixel_shape'] and grid.tolist()==chunk['grid'] and
                payload['sample_ordinals']==chunk['samples'], 'Retained chunk geometry/order changed')
        require(signature({'pixels':pixels})['pixels']['sha256']==chunk['pixel_sha256'], 'Retained source pixel bytes changed')
        offset=0
        for t,h,w in grid.tolist():
            require(t==1,'Accepted individual image patches only')
            frames.append(pixels[offset:offset+h*w]);grids.append([h,w]);offset+=h*w
        require(offset==len(pixels),'Complete old patch rows')
        ordinals.extend(chunk['samples'])
    require(len(frames)==source['feature_cells']==len(ordinals) and all(g==grids[0] for g in grids), 'Complete consistent retained source')
    return frames,grids[0],ordinals


class InputCache:
    """All25 immutable source patches in CPU RAM; composed request signatures checked."""
    def __init__(self, catalog_ref):
        catalog=read(bound(catalog_ref));self.sources={s['id']:s for s in catalog['sources']}
        require(len(self.sources)==25,'Exactly25 source catalog')
        self.pixels={sid:source_pixels(source) for sid,source in self.sources.items()}
        self.clocks={sid:read(bound(source['clock'])) for sid,source in self.sources.items()}

    def request(self, request_ref):
        request=read(bound(request_ref));sid=request['sid'];source=self.sources[sid]
        require(request['source_sha256']==source['source_sha256'] and request['source_clock_ref']==source['clock'] and
                request['first_new_pixel_text_native_QA'] is True,'Adopted successful source/request identity')
        frames,grid,ordinals=self.pixels[sid];plan=request['plan']
        pixels,actual_plan=build_pixels(frames,grid,ordinals,self.clocks[sid]['normalized_exact_pts'],
            plan['window_start_exact'],plan['window_end_exact'],dict(source_id=sid,source_sha256=source['source_sha256']))
        require(actual_plan==plan,'Actual adopted Overview/Excerpt plan changed')
        prefix=torch.load(bound(request['prefix_ref']),map_location='cpu',weights_only=True)
        require(set(prefix)=={'input_ids','attention_mask'} and signature(dict(**pixels,**prefix))==request['input_signature'],
                'Reconstructed actual input signature differs from first CPU acceptance')
        return request,prefix,pixels


def save_json(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def atomic_torch(path,value,replace=False):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    require((replace or not path.exists()) and not temporary.exists(),'Progress destination or temporary already exists')
    with temporary.open('xb') as stream:
        torch.save(value,stream);stream.flush();os.fsync(stream.fileno())
    if replace:os.replace(temporary,path)
    else:os.rename(temporary,path)
    directory=os.open(str(path.parent),os.O_RDONLY)
    try:os.fsync(directory)
    finally:os.close(directory)
