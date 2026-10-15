"""New author-train JPEGs only; reuse all previously accepted evaluation RGB."""
import concurrent.futures
import hashlib
import os
import struct
import traceback
import urllib.request
import zlib
from pathlib import Path
from gs_common import ROOT,OLD,RUN,paths,read,save,sha,info,fingerprint,encode,geometry,iou

def fetch(row):
    member=read(ROOT/'control/train_index.json')['GNMC/train/'+row['filename']]
    p=read(ROOT/'protocol.json');offset=member['header_offset'];length=member['range_bytes']
    req=urllib.request.Request(p['origin_url'],headers={'Range':f'bytes={offset}-{offset+length-1}',
                                                     'Accept-Encoding':'identity'})
    with urllib.request.urlopen(req,timeout=60) as response:
        if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {offset}-{offset+length-1}/{p["archive_bytes"]}':
            raise ValueError('exact range required; no whole archive fallback')
        packed=response.read(length+1)
    if len(packed)!=length: raise ValueError('range bytes mismatch')
    path=ROOT/'media'/row['filename'];path.with_suffix('.range').write_bytes(packed)
    header=struct.unpack('<4s5H3I2H',packed[:30]);start=30+header[-2]+header[-1]
    if header[0]!=b'PK\x03\x04' or header[3]!=member['compression']: raise ValueError('member header changed')
    name=packed[30:30+header[-2]].decode('utf-8')
    if name!='GNMC/train/'+row['filename']: raise ValueError('wrong original member')
    payload=packed[start:start+member['compressed_bytes']]
    raw=zlib.decompress(payload,-15) if member['compression']==8 else payload
    if len(raw)!=member['bytes'] or zlib.crc32(raw)&0xffffffff!=member['crc32']: raise ValueError('member CRC/bytes')
    path.write_bytes(raw)
    return row,path

def cache(processor,image,key,answer=None):
    import torch
    values,text,suffix=encode(processor,image,answer)
    proof={'template_text':text,'template_sha256':hashlib.sha256(text.encode()).hexdigest(),
           'tensors':info(values),'input_tokens':int(values['input_ids'].shape[1]),'answer':answer,'suffix':suffix}
    if answer is not None:
        from sft_contract import assistant_labels
        prompt,_,_=encode(processor,image)
        if not torch.equal(values['pixel_values'],prompt['pixel_values']) or not torch.equal(values['image_grid_thw'],prompt['image_grid_thw']):
            raise ValueError('assistant text changed visual encoding')
        mask=assistant_labels(values['input_ids'][0].tolist(),values['attention_mask'][0].tolist(),
                              prompt['input_ids'][0].tolist(),prompt['attention_mask'][0].tolist())
        if processor.tokenizer.decode(mask['assistant_token_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)!=suffix:
            raise ValueError('assistant-only token boundary changed')
        proof['assistant_mask']=mask
        values['labels']=torch.tensor([mask['tail_labels']],dtype=torch.long)
    target=ROOT/'tensors'/f'{key}.pt';torch.save(values,target)
    proof.update(path=str(target),file_sha256=sha(target),saved_tensors=info(values))
    save(ROOT/'proofs'/f'{key}.json',proof)
    return str(target),str(ROOT/'proofs'/f'{key}.json')

def main():
    paths()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    if read(OLD/'purpose_reply.json')['answer']!='仅学生参赛/科研，不涉及商业产品': raise ValueError('research purpose binding')
    p=read(ROOT/'protocol.json')
    for name in ('media','rgb','tensors','proofs'): (ROOT/name).mkdir()
    cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    proc=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    denied=read(OLD/'control/protected.json');names=set(denied['filenames']);hashes=set(denied['media_sha256']);fps=[]
    evaluation=[]
    for item in read(OLD/'inputs.json'):
        names.add(Path(item['path']).name.split('_',1)[-1]);hashes.add(item['source_sha256'])
        image=Image.fromarray(np.load(OLD/'rgb'/f'{item["key"]}.npy',allow_pickle=False));fps.append(fingerprint(image))
        tensor,proof=cache(proc,image,item['key'])
        evaluation.append({**item,'tensor':tensor,'new_proof':proof,'reused_RGB':str(OLD/'rgb'/f'{item["key"]}.npy')})
    save(ROOT/'eval_inputs.json',evaluation)
    rows=read(ROOT/'control/train_candidates.json');train=[];skipped=[]
    # Bounded network concurrency: small original members; no image/score-based source selection.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for start in range(0,len(rows),4):
            batch=rows[start:start+4]
            results=list(pool.map(fetch,batch))
            for row,path in results:
                if len(train)==p['train_count']: break
                with Image.open(path) as original:
                    if original.getexif().get(274,1)!=1: raise ValueError('nontrivial EXIF orientation')
                    image=original.convert('RGB')
                fp=fingerprint(image);digest=sha(path)
                if row['filename'] in names or digest in hashes or any((fp^x).bit_count()<=6 for x in fps):
                    skipped.append({'filename':row['filename'],'reason':'protected/exact/near duplicate','sha256':digest});continue
                W,H=image.size;x1,y1,x2,y2=row['crop_bboxes']['16:9']
                ref=[x1*W,y1*H,(x2-x1)*W,(y2-y1)*H]
                if not (0<=x1<x2<=1 and 0<=y1<y2<=1) or abs(ref[2]*9/16-ref[3])>2: raise ValueError('native author annotation invalid')
                target={'center':[round((x1+x2)*500),round((y1+y2)*500)],
                        'width':max(1,min(1000,round(ref[2]/min(W,H*16//9)*1000)))}
                box=geometry(target,W,H);quant_iou=iou([*box,box[2]*9/16],ref)
                if quant_iou<p['label_quantization_min_IoU']: raise ValueError('target quantization failed; no quality replacement')
                key='train_'+row['filename'];rgb=ROOT/'rgb'/f'{key}.npy';np.save(rgb,np.asarray(image),allow_pickle=False)
                tensor,proof=cache(proc,image,key,json_compact(target))
                train.append({'item_id':'gnmc:train:'+row['filename'],'source':str(path),'source_sha256':digest,
                    'rgb':str(rgb),'RGB_sha256':hashlib.sha256(np.asarray(image).tobytes()).hexdigest(),
                    'tensor':tensor,'proof':proof,'reference_original_xyxy':[x1,y1,x2,y2],'target':target,'quantized_IoU':quant_iou})
                hashes.add(digest);names.add(row['filename']);fps.append(fp)
                if len(train)%20==0: print('TRAIN_INPUT_ACCEPTED',len(train),flush=True)
            if len(train)==p['train_count']: break
    if len(train)!=200 or len(evaluation)!=40 or torch.cuda.is_initialized(): raise ValueError('CPU count/CUDA gate')
    save(ROOT/'train_inputs.json',train)
    save(ROOT/'cpu_acceptance.json',{'status':'PASS_200_HUMAN_TRAIN_40_EVAL_REAL_CPU_INPUTS','train':200,'eval':40,
         'skipped':skipped,'global_source_independence':'UNKNOWN','CUDA_initialized':False})
    files={str(x):sha(x) for x in ROOT.rglob('*') if x.is_file() and x.suffix not in ('.log',) and x.name not in
           ('chain_launch.json','chain_launch_claim.json','chain_started.json','deployment.json')}
    for x in [OLD/'inputs.json',OLD/'reference/labels.json',OLD/'recovery_01/screen/predictions.jsonl',
              OLD/'recovery_01/screen/result.json',OLD/'purpose_reply.json',OLD/'control/LICENSE.txt']:
        files[str(x)]=sha(x)
    for item in evaluation:
        files[item['reused_RGB']]=sha(item['reused_RGB'])
        oldproof=OLD/item['proof'];files[str(oldproof)]=sha(oldproof)
        baseline=OLD/read(oldproof)['stages']['baseline']['path'];files[str(baseline)]=sha(baseline)
    for name in ['b_score_aligned_package_v4/engine.py','b_score_aligned_package_v4/common.py',
                 'b_score_aligned_package_v4/spatial_baseline.py','b_score_aligned_package_v4/config.json',
                 'temporal_sft8b_v1/sft_contract.py','temporal_sft8b_v1/train_sft.py']:
        files[str(RUN/name)]=sha(RUN/name)
    save(ROOT/'source_lock.json',{'files':files,'train_inputs_sha256':sha(ROOT/'train_inputs.json'),
                                  'eval_inputs_sha256':sha(ROOT/'eval_inputs.json')})

def json_compact(value):
    import json
    return json.dumps(value,separators=(',',':'))

if __name__=='__main__':
    try: main()
    except Exception as e:
        save(ROOT/'prepare_failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'preserve_success_no_retry':True});raise
