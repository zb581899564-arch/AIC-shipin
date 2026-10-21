"""Freeze all26 human caption queries; never feed event timestamps to the encoder."""
from fractions import Fraction
import json
import sys
import numpy as np

from common import ROOT,WORK,OLD,checked,ref,read,write,grouped_ap


def main():
    assets=read(ROOT/'asset_acceptance.json')
    sys.path.insert(0,str(ROOT/'vendor'))
    import clip
    annotation=WORK/'videoxum_reference_iteration_20261013_v1/metadata_02/val_videoxum.json'
    original={r['video_id']:r for r in read(annotation)}
    sources=sorted([s for s in read(OLD/'registration.json')['sources'] if s['role']=='held_dataset'],key=lambda s:s['sid'])
    assert len(sources)==8
    input_sources={s['sid']:s for s in read(OLD/'input_acceptance.json')['sources']}
    queries=[];rows=[]
    (ROOT/'targets').mkdir()
    for source in sources:
        row=original[source['name']]
        assert len(row['tsum'])==len(row['timestamps'])==len(row['vsum']) and len(row['tsum'])>=2
        c=read(checked(source['clock_ref']))
        exact=[Fraction(v) for v in c['original_exact_pts']]
        assert exact[0]==0 and c['source_sha256']==source['media']['sha256']
        pts=np.asarray([float(v) for v in exact]);groups=np.arange(len(pts))//64
        counts=np.bincount(groups)
        positive=[];ids=[]
        for event,(text,span) in enumerate(zip(row['tsum'],row['timestamps'])):
            start,end=map(Fraction,map(str,span))
            assert 0<=start<end<=Fraction(str(row['duration']))
            y=(pts>=float(start))&(pts<float(end))
            pos=np.bincount(groups,weights=y,minlength=len(counts)).astype(np.int64)
            assert grouped_ap(np.zeros(len(counts)),pos,counts) is not None
            ids.append(len(queries))
            queries.append(dict(query_id=len(queries),sid=source['sid'],event=event,text=text))
            positive.append(pos)
        target=ROOT/'targets'/f'{source["sid"]}.npz'
        np.savez(target,positive=np.stack(positive),counts=counts)
        rgb=checked(input_sources[source['sid']]['rgb'])
        data=np.load(rgb,mmap_mode='r',allow_pickle=False)
        assert data.dtype==np.uint8 and data.shape==(len(counts),8,224,224,3)
        rows.append(dict(sid=source['sid'],name=source['name'],rgb=ref(rgb),native_cells=len(counts),
                         native_frames=len(pts),query_ids=ids,target=ref(target),clock=source['clock_ref']))
    tokens=clip.tokenize([q['text'] for q in queries],truncate=False).numpy()
    assert len(queries)==26 and tokens.shape==(26,77)
    np.save(ROOT/'query_tokens.npy',tokens,allow_pickle=False)
    # Minimum necessary new mathematical checks. Existing RGB/clock QA is adopted.
    assert abs(grouped_ap([0,0],[1,0],[2,2])-.25)<1e-12
    assert grouped_ap([2,1],[1,0],[1,1])==1.0
    write(ROOT/'input_acceptance.json',dict(status='PASS8_CACHED_INPUTS_26_NONTRUNCATED_QUERIES',
              sources=rows,queries=queries,tokens=ref(ROOT/'query_tokens.npy'),
              author_annotation=ref(annotation),assets=ref(ROOT/'asset_acceptance.json'),
              inherited_I3D_center_view=True,standard_full_frame_CLIP_transform_claim=False,
              new_media_decode=0,new_image_encode=0,old_quality_replay=0,
              target='ActivityNet human broad event intervals, NOT shortened VideoXum highlights',
              timestamps_in_model_input=False,historical_exposure=True,tests=2))


if __name__=='__main__':
    main()
