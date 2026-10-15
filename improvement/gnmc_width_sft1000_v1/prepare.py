"""Expand fixed author-train order; never repeat successful old member/RGB/tensor work."""
import hashlib
import json
import struct
import time
import traceback
import urllib.error
import urllib.request
import zlib
from pathlib import Path
from gws_common import ROOT,OLD,TRAINOLD,PREVIOUS,RUN,paths,read,save,sha,info,encode

def fp(image):
    import numpy as np
    a=np.asarray(image.convert('L').resize((9,8)))
    return sum(int(v)<<i for i,v in enumerate((a[:,1:]>a[:,:-1]).reshape(-1)))

def media(name,index,protocol):
    target=ROOT/'media'/name;old=TRAINOLD/'media'/name
    m=index['GNMC/train/'+name]
    if old.exists():
        raw=old.read_bytes()
        if len(raw)!=m['bytes'] or zlib.crc32(raw)&0xffffffff!=m['crc32']:raise ValueError('existing member changed')
        return old
    if target.exists():raise ValueError('successful new file exists: explicit recovery required')
    offset=m['header_offset'];length=m['range_bytes']
    req=urllib.request.Request(protocol['origin_url'],headers={'Range':f'bytes={offset}-{offset+length-1}','Accept-Encoding':'identity'})
    for attempt in range(5):
        time.sleep(1.25)
        try:
            with urllib.request.urlopen(req,timeout=60) as response:
                if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {offset}-{offset+length-1}/{protocol["archive_bytes"]}':
                    raise ValueError('exact range required; no whole archive fallback')
                packed=response.read(length+1)
            break
        except urllib.error.HTTPError as error:
            if error.code!=429:raise
            after=error.headers.get('Retry-After');delay=max(60,float(after)) if after and after.isdigit() else 60*(attempt+1)
            with (ROOT/'rate_limit_events.jsonl').open('a') as f:f.write(json.dumps({'filename':name,'attempt':attempt,'HTTP':429,'Retry_After':after,'wait_seconds':delay})+'\n')
            if attempt==4:raise
            print('AUTHOR_RATE_LIMIT_WAIT',delay,flush=True);time.sleep(delay)
    if len(packed)!=length:raise ValueError('range bytes')
    target.with_suffix('.range').write_bytes(packed)
    header=struct.unpack('<4s5H3I2H',packed[:30]);start=30+header[-2]+header[-1]
    if header[0]!=b'PK\x03\x04' or header[3]!=m['compression'] or packed[30:30+header[-2]].decode('utf-8')!='GNMC/train/'+name:
        raise ValueError('original member header/name changed')
    data=packed[start:start+m['compressed_bytes']]
    raw=zlib.decompress(data,-15) if m['compression']==8 else data
    if len(raw)!=m['bytes'] or zlib.crc32(raw)&0xffffffff!=m['crc32']:raise ValueError('source member CRC/size')
    target.write_bytes(raw);return target

def main():
    paths()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from sft_contract import assistant_labels
    if read(PREVIOUS/'completion.json')['status']!='STOP_TRAINED_SCREEN_REJECTED_CONFIRM_NOT_RUN':raise ValueError('previous actual terminal required')
    prior=read(PREVIOUS/'source_lock.json')
    for p,h in prior['files'].items():
        if sha(p)!=h:raise ValueError('previous accepted input/code changed')
    protocol=read(ROOT/'protocol.json');cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    for n in ['media','rgb','tensors','proofs']:(ROOT/n).mkdir()
    index=read(ROOT/'control/train_index.json');candidates=read(ROOT/'control/train_candidates.json')
    cached={x['item_id'].rsplit(':',1)[-1]:x for x in read(PREVIOUS/'train_inputs.json')}
    protected=read(OLD/'control/protected.json');names=set(protected['filenames']);hashes=set(protected['media_sha256']);fingerprints=[]
    for row in read(OLD/'inputs.json'):
        names.add(row['key'].split('_',1)[-1]);hashes.add(row['source_sha256']);fingerprints.append(fp(Image.fromarray(np.load(OLD/'rgb'/f'{row["key"]}.npy',allow_pickle=False))))
    denied_old_skips={r['filename'] for r in read(TRAINOLD/'cpu_acceptance.json')['skipped']}
    train=[];skipped=[];reused=0
    for record in candidates:
        name=record['filename']
        if len(train)==1000:break
        if name in denied_old_skips or name in names:
            skipped.append({'filename':name,'reason':'previous registered identity exclusion'});continue
        if name in cached:
            row=cached[name];array=np.load(row['rgb'],allow_pickle=False)
            if sha(row['source'])!=row['source_sha256'] or hashlib.sha256(array.tobytes()).hexdigest()!=row['RGB_sha256']:raise ValueError('existing train source/RGB changed')
            proof=read(row['proof'])
            if sha(row['tensor'])!=proof['file_sha256']:raise ValueError('existing successful width input changed')
            image=Image.fromarray(array);finger=fp(image);digest=row['source_sha256'];reused+=1
        else:
            path=media(name,index,protocol)
            with Image.open(path) as original:
                if original.getexif().get(274,1)!=1:raise ValueError('nontrivial EXIF')
                image=original.convert('RGB')
            finger=fp(image);digest=sha(path)
            if digest in hashes or any((finger^f).bit_count()<=6 for f in fingerprints):
                skipped.append({'filename':name,'reason':'protected exact/near duplicate','sha256':digest});continue
            W,H=image.size;x1,y1,x2,y2=record['crop_bboxes']['16:9'];ref=[x1*W,y1*H,(x2-x1)*W,(y2-y1)*H]
            if not (0<=x1<x2<=1 and 0<=y1<y2<=1) or abs(ref[2]*9/16-ref[3])>2:raise ValueError('native original annotation')
            width=max(1,min(1000,round(ref[2]/min(W,H*16//9)*1000)))
            cx=(x1+x2)/2;cy=(y1+y2)/2;w=max(1,min(W,H*16//9)*width//1000);h=w*9/16
            bx=min(max(cx*W-w/2,0),W-w);by=min(max(cy*H-h/2,0),H-h)
            inter=max(0,min(bx+w,ref[0]+ref[2])-max(bx,ref[0]))*max(0,min(by+h,ref[1]+ref[3])-max(by,ref[1]))
            quant=inter/(w*h+ref[2]*ref[3]-inter)
            if quant<protocol['label_quantization_min_IoU']:raise ValueError('width target quantization; no label quality replacement')
            rgb=ROOT/'rgb'/f'{name}.npy';np.save(rgb,np.asarray(image),allow_pickle=False)
            answer=json.dumps({'width':width},separators=(',',':'));full,text,suffix=encode(processor,image,answer);prompt,_,_=encode(processor,image)
            if not torch.equal(full['pixel_values'],prompt['pixel_values']) or not torch.equal(full['image_grid_thw'],prompt['image_grid_thw']):raise ValueError('assistant changed visual tensors')
            mask=assistant_labels(full['input_ids'][0].tolist(),full['attention_mask'][0].tolist(),prompt['input_ids'][0].tolist(),prompt['attention_mask'][0].tolist())
            if processor.tokenizer.decode(mask['assistant_token_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)!=suffix:raise ValueError('assistant-only boundary')
            full['labels']=torch.tensor([mask['tail_labels']],dtype=torch.long);tensor=ROOT/'tensors'/f'{name}.pt';torch.save(full,tensor)
            proof=ROOT/'proofs'/f'{name}.json';save(proof,{'path':str(tensor),'file_sha256':sha(tensor),'saved_tensors':info(full),
                 'assistant_mask':mask,'answer':answer,'template_text':text,'source_RGB':str(rgb),'original_source_sha256':digest})
            row={'item_id':'gnmc:train:'+name,'source':str(path),'source_sha256':digest,'rgb':str(rgb),
                 'RGB_sha256':hashlib.sha256(np.asarray(image).tobytes()).hexdigest(),'tensor':str(tensor),'proof':str(proof),
                 'reference_original_xyxy':[x1,y1,x2,y2],'target':{'width':width},'quantized_IoU':quant}
        train.append(row);names.add(name);hashes.add(digest);fingerprints.append(finger)
        # Small persistent progress references allow explicit remaining-only recovery.
        with (ROOT/'accepted_train.jsonl').open('a') as journal:journal.write(json.dumps(row)+'\n')
        if len(train)%50==0:print('TRAIN_ACCEPTED',len(train),'REUSED',reused,flush=True)
    if len(train)!=1000 or reused!=200:raise ValueError('fixed1000/old200 denominator')
    save(ROOT/'train_inputs.json',train)
    evaluation=read(PREVIOUS/'eval_inputs.json')
    for row in evaluation:
        if sha(row['tensor'])!=read(row['new_proof'])['file_sha256']:raise ValueError('old successful eval input changed')
    save(ROOT/'eval_inputs.json',evaluation)
    if len(evaluation)!=40 or torch.cuda.is_initialized():raise ValueError('CPU-only1040 acceptance')
    save(ROOT/'cpu_acceptance.json',{'status':'PASS_1000_HUMAN_TRAIN_40_EVAL_REAL_CPU_INPUTS','train':1000,'eval':40,
         'reused_success_train_inputs':reused,'old_success_download_decode_encode_repeated':False,'skipped_identity':skipped,
         'CUDA_initialized':False,'global_original_source_independence':'UNKNOWN'})
    files={str(p):sha(p) for p in ROOT.rglob('*') if p.is_file() and p.suffix!='.log' and p.name not in
          ('chain_launch.json','chain_launch_claim.json','deployment.json','chain_started.json')}
    files.update({str(p):sha(p) for p in [PREVIOUS/'source_lock.json',PREVIOUS/'train/train_report.json',
         PREVIOUS/'train/adapter/adapter_model.safetensors',PREVIOUS/'train/adapter/adapter_config.json',OLD/'reference/labels.json',OLD/'recovery_01/screen/predictions.jsonl']})
    for row in train:
        for key in ['source','rgb','tensor','proof']:files[row[key]]=sha(row[key])
    for row in evaluation:
        for key in ['tensor','new_proof','reused_RGB']:files[row[key]]=sha(row[key])
        proof=OLD/row['proof'];files[str(proof)]=sha(proof);baseline=OLD/read(proof)['stages']['baseline']['path'];files[str(baseline)]=sha(baseline)
    for n in ['b_score_aligned_package_v4/config.json','b_score_aligned_package_v4/engine.py','b_score_aligned_package_v4/common.py',
              'b_score_aligned_package_v4/spatial_baseline.py','temporal_sft8b_v1/sft_contract.py','temporal_sft8b_v1/train_sft.py']:
        files[str(RUN/n)]=sha(RUN/n)
    save(ROOT/'source_lock.json',{'files':files,'original_successes_repeated':False})

if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/'prepare_failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'preserve_success_explicit_recovery_only':True});raise
