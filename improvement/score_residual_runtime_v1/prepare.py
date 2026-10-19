"""First new 2Hz image feature inputs; prior native clocks/B0 answers adopted."""
import bisect
from fractions import Fraction as F
import sys
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from common_runtime import *

def main():
    import av
    import numpy as np
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    proto = read(ROOT/'protocol.json')
    cfg = read(RUN/'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True)
    exports = {}
    for dn in ('human_reference_iteration_20261013_v1','duration_guard_iteration_20261013_v1'):
        ex = read(WORK/dn/'developer_prediction_export.json')
        require(ex['status']=='PASS_NEW_B_NATIVE_INFERENCE_AND_INDEPENDENT_CPU_REPLAY','Old export unaccepted')
        exports.update({r['source_name']:(dn,r) for r in ex['rows']})
    accepted=[]
    for source in proto['sources']:
        sid=source['id']; name=source['name']; dn,row=exports[name]; c=row['native_clock']
        out=ROOT/'inputs'/sid; out.mkdir(parents=True, exist_ok=False)
        media=WORK/dn/'media_01'/(name+'.webm')
        require(media.stat().st_size==c['source_bytes'] and sha(media)==c['source_sha256'],'Media changed')
        pts=[F(x) for x in c['normalized_exact_pts']]; end=F(c['physical_end_exact'])
        require(len(pts)==c['n_frames'] and all(b>a for a,b in zip(pts,pts[1:])) and end>pts[-1], 'Clock')
        # Half-second exact cells. One closest actual native observation per cell.
        # Empty VFR/tail time cells contain no native ordinal labels. Do not
        # invent observations for them or duplicate the final image.
        original_cells=np.array([int(t*2) for t in pts],dtype=np.int64)
        occupied=np.unique(original_cells)
        groups=np.searchsorted(occupied,original_cells).astype(np.int64)
        ords=[]
        for cell in occupied.tolist():
            a=F(cell,2);b=min(a+F(1,2),end)
            lo=bisect.bisect_left(pts,a); hi=bisect.bisect_left(pts,b)
            require(hi>lo,'No actual observation in feature cell')
            mid=(a+b)/2; pos=bisect.bisect_left(pts,mid,lo,hi)
            candidates=[j for j in (pos-1,pos) if lo<=j<hi]
            ords.append(min(candidates,key=lambda j:(abs(pts[j]-mid),j)))
        baseline=np.zeros(len(pts),dtype=np.bool_)
        for w in row['windows']:
            start=F(w['start_exact']); stop=F(w['end_exact'])
            require(w['original_status']=='MODEL_OK','Original B0 failed')
            for a,b in w['segments']:
                a=start+F(str(a)); b=start+F(str(b))
                require(start<=a<b<=stop,'Original baseline domain')
                baseline[bisect.bisect_left(pts,a):bisect.bisect_left(pts,b)]=True
        np.savez(out/'native.npz',groups=groups,baseline=baseline,sample_ordinals=np.array(ords))
        write(out/'clock.json',c)
        desired=set(ords); batch=[]; batch_ids=[]; chunks=[]; observed=0; first=None
        def flush():
            if not batch:return
            enc=processor.image_processor(images=batch,return_tensors='pt',size={'shortest_edge':65536,'longest_edge':65536})
            pix=enc['pixel_values'].contiguous(); grid=enc['image_grid_thw'].contiguous()
            require(pix.device.type=='cpu' and torch.isfinite(pix).all() and grid.shape==(len(batch),3),'CPU processor')
            require(bool((grid[:,0]==1).all()),'Image rather than video input required')
            fn=out/('chunk_%04d.pt'%len(chunks))
            torch.save(dict(pixel_values=pix,image_grid_thw=grid,sample_ordinals=batch_ids.copy()),fn)
            chunks.append(dict(path=str(fn),bytes=fn.stat().st_size,sha256=sha(fn),samples=batch_ids.copy(),pixel_shape=list(pix.shape),grid=grid.tolist(),pixel_sha256=hashlib.sha256(pix.numpy().tobytes()).hexdigest()))
            batch.clear();batch_ids.clear()
        with av.open(str(media)) as container:
            stream=container.streams.video[0];stream.thread_count=2
            for i,frame in enumerate(container.decode(stream)):
                require(i<len(pts) and frame.pts is not None,'Unexpected decode frame')
                t=F(frame.pts)*F(frame.time_base)
                if first is None:first=t
                require(t-first==pts[i],'New-purpose decode differs from accepted native order')
                observed+=1
                if i in desired:
                    # Lossless processor inputs saved, no second successful encoding.
                    batch.append(frame.to_image());batch_ids.append(i)
                    if len(batch)==8:flush()
            flush()
        require(observed==len(pts) and [o for z in chunks for o in z['samples']]==ords,'Full source or observation mismatch')
        acceptance=dict(status='PASS_FIRST_NEW_IMAGE_CPU_INPUTS',id=sid,name=name,role=source['role'],native_frames=observed,feature_cells=len(ords),native_sha256=sha(out/'native.npz'),clock_sha256=sha(out/'clock.json'),chunks=chunks,old_B0_windows_adopted=len(row['windows']),old_B0_export_sha256=sha(WORK/dn/'developer_prediction_export.json'),new_generation_calls=0,new_feature_forwards=0,old_RGB_cleanup='Old20 deleted; explicitly new-purpose decode/encoding, not historical generation replay')
        write(out/'acceptance.json',acceptance);accepted.append(acceptance)
        event('CPU_SOURCE_ACCEPTED',id=sid,frames=observed,cells=len(ords))
    write(ROOT/'cpu_acceptance.json',dict(status='PASS_ALL_25_NEW_FEATURE_INPUTS',sources=accepted,protocol_sha256=sha(ROOT/'protocol.json'),total_cells=sum(x['feature_cells'] for x in accepted)))

if __name__=='__main__':main()
