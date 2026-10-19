"""Conditional production input preparation. No labels or teacher service."""
import bisect
import os
import sys
import shutil
from fractions import Fraction as F
os.environ['CUDA_VISIBLE_DEVICES']=''
from common_runtime import *

def main():
    import av
    import numpy as np
    import torch
    import zipfile
    from transformers import AutoProcessor
    from PIL import Image
    torch.set_num_threads(2)
    registration=read(ROOT/'production_registration.json')
    quality=read(registration['external_result']['path'])
    require(sha(registration['external_result']['path'])==registration['external_result']['sha256'] and quality['new_production_allowed'] is True,'External quality gate required')
    cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    sys.path.insert(0,str(RUN/'b_score_aligned_package_v4'))
    from source_color import convert_frame
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True)
    prior=read(WORK/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json')
    meta=read(prior['metadata']['path']);clocks=read(prior['source_clocks']['path'])
    require(sha(prior['metadata']['path'])==prior['metadata']['sha256'] and sha(prior['source_clocks']['path'])==prior['source_clocks']['sha256'],'Frozen native source metadata changed')
    baseline_path=registration['baseline']['path']
    require(sha(baseline_path)=='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543','Original VERIFY changed')
    with zipfile.ZipFile(baseline_path) as z:
        require(z.namelist()==['predictions.jsonl'] and z.testzip() is None,'Original package CRC')
        rows=[json.loads(l) for l in z.read('predictions.jsonl').splitlines()]
    selected={x['video_id']:{p['frame'] for p in x['predictions']} for x in rows}
    require(set(selected)==set(clocks)=={str(i) for i in range(426)},'Full426 source identity')
    write(ROOT/'metadata.json',meta)
    accepted=[]
    for m in sorted(meta['records'],key=lambda x:int(x['video_id'])):
        sid=m['video_id'];c=clocks[sid];media=Path(m['source_path'])
        remaining_ids={x['video_id'] for x in meta['records']}-{x['id'] for x in accepted}
        predicted=sum(registration['CPU_tensor_estimates_by_source'][k] for k in remaining_ids)+registration['future_feature_and_package_bytes']
        require(shutil.disk_usage(WORK).free>=predicted,'Live capacity insufficient for remaining declared tensors/features; do not consume another job data')
        require(c['source_sha256']==m['source_sha256'] and sha(media)==m['source_sha256'],'Source bytes changed')
        pts=[F(x) for x in c['normalized_exact_pts']];end=F(c['physical_end_exact'])
        require(len(pts)==m['n_frames'] and all(b>a for a,b in zip(pts,pts[1:])) and end>pts[-1],'Native domain')
        original_cells=np.array([int(t*2) for t in pts],dtype=np.int64);occupied=np.unique(original_cells)
        groups=np.searchsorted(occupied,original_cells).astype(np.int64)
        ords=[]
        for cell in occupied.tolist():
            a=F(cell,2);b=min(a+F(1,2),end);lo=bisect.bisect_left(pts,a);hi=bisect.bisect_left(pts,b)
            require(hi>lo,'Occupied native cell');mid=(a+b)/2;pos=bisect.bisect_left(pts,mid,lo,hi)
            ords.append(min([j for j in (pos-1,pos) if lo<=j<hi],key=lambda j:(abs(pts[j]-mid),j)))
        baseline=np.array([i in selected[sid] for i in range(len(pts))],dtype=np.bool_)
        out=ROOT/'inputs'/sid;out.mkdir(parents=True,exist_ok=False)
        np.savez(out/'native.npz',groups=groups,baseline=baseline,sample_ordinals=np.array(ords))
        write(out/'clock.json',c)
        desired=set(ords);batch=[];batch_ids=[];chunks=[];observed=0;first=None
        def flush():
            if not batch:return
            enc=processor.image_processor(images=batch,return_tensors='pt',size={'shortest_edge':65536,'longest_edge':65536})
            pix=enc['pixel_values'].contiguous();grid=enc['image_grid_thw'].contiguous()
            require(pix.device.type=='cpu' and torch.isfinite(pix).all() and grid.shape==(len(batch),3) and bool((grid[:,0]==1).all()),'Real CPU image input gate')
            fn=out/('chunk_%04d.pt'%len(chunks));torch.save(dict(pixel_values=pix,image_grid_thw=grid,sample_ordinals=batch_ids.copy()),fn)
            chunks.append(dict(path=str(fn),bytes=fn.stat().st_size,sha256=sha(fn),samples=batch_ids.copy(),pixel_shape=list(pix.shape),grid=grid.tolist(),pixel_sha256=hashlib.sha256(pix.numpy().tobytes()).hexdigest()))
            batch.clear();batch_ids.clear()
        with av.open(str(media)) as container:
            stream=container.streams.video[0];stream.thread_count=2
            for i,frame in enumerate(container.decode(stream)):
                require(i<len(pts) and frame.pts is not None,'Decode ordinal')
                t=F(frame.pts)*F(frame.time_base)
                if first is None:first=t
                require(t-first==pts[i],'Actual input PTS differs from accepted source clock')
                observed+=1
                if i in desired:
                    batch.append(Image.fromarray(convert_frame(frame,m['source_sha256'],'rgb24')));batch_ids.append(i)
                    if len(batch)==8:flush()
            flush()
        require(observed==len(pts) and [o for z in chunks for o in z['samples']]==ords,'Complete actual native samples')
        acc=dict(status='PASS_FIRST_NEW_IMAGE_CPU_INPUTS',id=sid,name=sid,role='frozen_automatic_production',native_frames=observed,feature_cells=len(ords),native_sha256=sha(out/'native.npz'),clock_sha256=sha(out/'clock.json'),chunks=chunks,new_generation_calls=0,new_feature_forwards=0)
        write(out/'acceptance.json',acc);accepted.append(acc);event('PRODUCTION_CPU_SOURCE_ACCEPTED',id=sid,frames=observed,cells=len(ords))
    # Feature module expects this frozen status label; quantity is independently 426.
    write(ROOT/'cpu_acceptance.json',dict(status='PASS_ALL_REGISTERED_NEW_FEATURE_INPUTS',sources=accepted,protocol_sha256=sha(ROOT/'protocol.json'),total_cells=sum(x['feature_cells'] for x in accepted)))

if __name__=='__main__':main()
