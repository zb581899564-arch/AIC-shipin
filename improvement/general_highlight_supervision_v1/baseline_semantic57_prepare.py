"""Exact original half-second native image/target query recipe on the external recording."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from bisect import bisect_left
from fractions import Fraction
import hashlib
import av
import numpy as np
from PIL import Image
import torch
from transformers import AutoProcessor
from baseline_bridge57_common import ROOT,RUN,read,ref,save,checked,legacy_runtime,semantic_modules


def frame_plan(clock):
    origin=Fraction(clock['first_PTS_exact']);points=[Fraction(p)-origin for p in clock['PTS']]
    end=Fraction(clock['physical_end_exact'])-origin
    original=np.array([int(p*2) for p in points],dtype=np.int64);occupied=np.unique(original)
    groups=np.searchsorted(occupied,original).astype(np.int64);samples=[]
    for cell in occupied:
        a=Fraction(int(cell),2);b=min(a+Fraction(1,2),end)
        lo=bisect_left(points,a);hi=bisect_left(points,b);mid=(a+b)/2;at=bisect_left(points,mid,lo,hi)
        samples.append(min([j for j in [at-1,at] if lo<=j<hi],key=lambda j:(abs(points[j]-mid),j)))
    return points,groups,samples


def save_chunk(processor, production, points, images, ordinals, folder, index):
    encoded=processor.image_processor(images=images,return_tensors='pt',size={'shortest_edge':65536,'longest_edge':65536})
    pixel=encoded['pixel_values'].contiguous();grid=encoded['image_grid_thw'].contiguous()
    if pixel.device.type!='cpu' or not torch.isfinite(pixel).all() or grid.shape!=(len(images),3) or not (grid[:,0]==1).all():
        raise ValueError('Actual native image processor/grid gate failed')
    chunk=dict(samples=ordinals.copy(),grid=grid.tolist())
    texts=production.exact_texts(processor,points,chunk)
    tokens=processor.tokenizer(texts,return_tensors='pt',padding=True,add_special_tokens=False)
    text={k:tokens[k].contiguous() for k in ['input_ids','attention_mask']}
    image_id=processor.tokenizer.convert_tokens_to_ids('<|image_pad|>')
    expected=sum(int(np.prod(g))//4 for g in chunk['grid'])
    if text['input_ids'].shape[1]>4096 or not ((text['input_ids']==image_id).sum(1)==expected).all():
        raise ValueError('Exact image placeholder/native text budget differs')
    path=folder/f'context_{index:04d}.pt'
    with path.open('xb') as out:torch.save(dict(pixel_values=pixel,image_grid_thw=grid,sample_ordinals=ordinals.copy(),**text),out)
    restored=torch.load(path,map_location='cpu',weights_only=True)
    if not torch.equal(restored['pixel_values'],pixel) or not torch.equal(restored['input_ids'],text['input_ids']):
        raise ValueError('First actual serialized image/query reload differs')
    for target in range(len(images)):
        decoded=processor.tokenizer.decode(text['input_ids'][target][text['attention_mask'][target].bool()],skip_special_tokens=False)
        if f'Does frame {target+1} depict a visual highlight in this context? Answer exactly Yes or No.' not in decoded:
            raise ValueError('Independent target query/position mapping differs')
    return dict(input=ref(path),samples=ordinals.copy(),grid=grid.tolist(),queries=len(images),
        text_SHA=[hashlib.sha256(t.encode()).hexdigest() for t in texts])


def main():
    torch.set_num_threads(2);source=read(ROOT/'registration.json')['source'];clock=read(checked(source['clock']))
    points,groups,samples=frame_plan(clock);legacy_runtime();production,_,_=semantic_modules()
    from source_color import convert_frame
    processor=AutoProcessor.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'],local_files_only=True)
    processor.tokenizer.padding_side='left'
    words={w:processor.tokenizer.encode(w,add_special_tokens=False) for w in ['Yes','No']}
    if not all(len(v)==1 for v in words.values()):raise ValueError('Frozen single-token semantic readout differs')
    folder=ROOT/'semantic';folder.mkdir();np.savez(folder/'native.npz',groups=groups,sample_ordinals=np.asarray(samples))
    desired=set(samples);images=[];ordinals=[];accepted=[];observed=0
    with av.open(source['media']['path']) as container:
        stream=container.streams.video[0];stream.codec_context.thread_count=1
        origin=Fraction(clock['first_PTS_exact'])
        for i,frame in enumerate(container.decode(stream)):
            if i>=len(points) or Fraction(frame.pts)*frame.time_base-origin!=points[i]:
                raise ValueError('New semantic input differs from measured original native PTS')
            observed+=1
            if i in desired:
                images.append(Image.fromarray(convert_frame(frame,source['media']['sha256'],'rgb24')));ordinals.append(i)
                if len(images)==8:
                    accepted.append(save_chunk(processor,production,points,images,ordinals,folder,len(accepted)));images=[];ordinals=[]
                    print('FULL_BASELINE_SEMANTIC_CPU',len(accepted),flush=True)
        if images:accepted.append(save_chunk(processor,production,points,images,ordinals,folder,len(accepted)))
    if observed!=len(points) or [o for row in accepted for o in row['samples']]!=samples:
        raise ValueError('Complete source/sample input denominator differs')
    save(ROOT/'semantic_CPU_completion.json',dict(state='PASS_FIRST_FROZEN_SEMANTIC_INPUTS',chunks=accepted,
        cells=len(samples),native=ref(folder/'native.npz'),words={k:v[0] for k,v in words.items()},
        exact_original_semantic_question=True,actual_new_semantic_source_decode=1,new_model_calls=0))


if __name__=='__main__':main()
