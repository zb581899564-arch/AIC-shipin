"""Independent native width evidence recomputation; never imports the renderer."""
from bisect import bisect_right
from fractions import Fraction
import hashlib
import math
import zipfile
from pack_common import *


def verify_arrays(metadata,old_rows,old_provenance,rows,provenance,widths,shot_rows,anchor_rows,baseline,arm):
    """Independent formulas on actual serialized input/output evidence."""
    meta={r['video_id']:r for r in metadata['records']};before=boxes(old_rows);after=boxes(rows);base=boxes(baseline)
    oldp={(r['video_id'],r['source_frame']):r for r in old_provenance};newp={(r['video_id'],r['source_frame']):r for r in provenance}
    require(set(before)==set(after)==set(oldp)==set(newp) and len(oldp)==len(old_provenance) and len(newp)==len(provenance),'Actual selected/pre-width/provenance native membership')
    require(set(base)<=set(after) and (arm!='C' or set(base)==set(after)),'C exact baseline frames; D only declared additions')
    require(all(r['model_params_b']==TOTAL/1e9 for r in rows),'Actual physical model parameter declaration')
    require(all(before[k]==v for k,v in base.items()),'Frozen composed baseline box identity')
    landscape={sid for sid,m in meta.items() if m['targetRatioWH']==[16,9]}
    require(set(widths)==landscape,'Only fixed landscape metadata routes to width model')
    for k in before:
        require(before[k]==oldp[k]['box_xyw'] and after[k]==newp[k]['box_xyw'],'Actual serialized box/provenance equality')
        if meta[k[0]]['targetRatioWH']==[9,16]:require(after[k]==before[k] and newp[k]==oldp[k],'All portrait composed boxes/provenance preserved')
    # Independent contiguous shot reconstruction: source switch, integer gap or
    # explicit shot start are hard boundaries. No production helper imported.
    ordered=sorted(shot_rows,key=lambda r:(r['video_id'],r['source_frame']));segments=[];previous=None;seen=set()
    for row in ordered:
        key=(row['video_id'],row['source_frame']);require(key not in seen and type(row['is_shot_start']) is bool,'Unique actual shot domain');seen.add(key)
        if previous is None or key[0]!=previous[0] or key[1]!=previous[1]+1 or row['is_shot_start']:segments.append([])
        segments[-1].append(row['source_frame']);previous=key
    # Source is recovered from first frame's unique ordered group in a second
    # linear scan, keeping this checker structurally separate from the renderer.
    groups=[];cursor=0
    for frames in segments:
        sid=ordered[cursor]['video_id'];groups.append((sid,frames));cursor+=len(frames)
    anchors={(r['video_id'],r['source_frame']):r for r in anchor_rows}
    require(len(anchors)==len(anchor_rows),'Unique original raw center anchors')
    group_index={};observed={};schedules={};clocks={};width_maps={}
    for sid,data in widths.items():
        samples=data['sample_ordinals'];values=data['predicted_width']
        require(data['head_sha256']==HEAD and data['normalization_sha256']==NORM and len(samples)==len(values)>0 and
                samples==sorted(set(samples)) and all(type(x) is int for x in samples) and all(type(w) is int and 1<=w<=1000 for w in values),'Actual frozen legal sample widths')
        require(all(not isinstance(t,(float,bool)) for t in data['native_pts_exact']),'No float/CFR replacement for actual PTS')
        pts=[Fraction(t) for t in data['native_pts_exact']]
        require(len(pts)==meta[sid]['n_frames'] and all(b>a for a,b in zip(pts,pts[1:])) and all(0<=s<len(pts) for s in samples),'Actual native sample/PTS domain')
        clocks[sid]=pts;width_maps[sid]=dict(zip(samples,values))
    for number,(sid,frames) in enumerate(groups):
        for frame in frames:group_index[(sid,frame)]=number
        if sid not in landscape:continue
        samples=widths[sid]['sample_ordinals'];a=bisect_right(samples,frames[0]-1);b=bisect_right(samples,frames[-1]);observed[number]=samples[a:b]
        schedule=frames[::8]
        if schedule[-1]!=frames[-1]:schedule.append(frames[-1])
        schedules[number]=schedule
    require(set(before)<=set(group_index),'All selected frames in original field shot domain')
    checked_new=0
    for key,oldbox in before.items():
        sid,frame=key
        if sid not in landscape:continue
        number=group_index[key];frames=groups[number][1];samples=observed[number];proof=newp[key]
        if not samples:
            require(after[key]==oldbox and proof==dict(oldp[key],width_head_application=dict(decision='NO_SAME_SHOT_OBSERVATION_KEEP_BASELINE',width=1000,head_sha256=HEAD,shot_first=frames[0],shot_last=frames[-1])),'Explicit no same-shot observation preserves exact old box/provenance')
            continue
        j=bisect_right(samples,frame);left=samples[max(0,j-1)];right=samples[min(j,len(samples)-1)]
        if frame in width_maps[sid]:left=right=frame
        pts=clocks[sid];alpha=Fraction(0) if left==right else (pts[frame]-pts[left])/(pts[right]-pts[left])
        value=Fraction(width_maps[sid][left])+(width_maps[sid][right]-width_maps[sid][left])*alpha;width=int(round(value))
        width_evidence=dict(left_sample_ordinal=left,right_sample_ordinal=right,left_width=width_maps[sid][left],right_width=width_maps[sid][right],alpha_exact=str(alpha),axis='native_pts_exact',predicted_width=width)
        if width==1000:
            require(after[key]==oldbox and proof==dict(oldp[key],width_head_application=dict(decision='WIDTH1000_COPY_ACCEPTED_BASELINE',head_sha256=HEAD,**width_evidence)),'Width1000 exact accepted-box identity')
            continue
        require(proof['spatial_source']==SOURCE and proof['width_model']==dict(head_sha256=HEAD,normalization_sha256=NORM,**width_evidence) and
                proof['old_spatial_provenance']==oldp[key] and proof['shot_first']==frames[0] and proof['shot_last']==frames[-1],'Accurate new width source and original evidence')
        schedule=schedules[number];j=bisect_right(schedule,frame);cl=schedule[max(0,j-1)];cr=schedule[min(j,len(schedule)-1)]
        if frame in schedule:cl=cr=frame
        require(cl<=frame<=cr and cr-cl<=8 and (sid,cl) in anchors and (sid,cr) in anchors,'Actual same-shot max-gap8 centers bracket frame')
        la,ra=anchors[(sid,cl)],anchors[(sid,cr)]
        for anchor in (la,ra):
            require(anchor['status']=='MODEL_OK' and anchor['used_fallback'] is False and anchor['spatial_source']=='QWEN_ANCHOR_SAME_FRAME' and
                    len(anchor['center_norm'])==2 and all(type(x) in (int,float) and math.isfinite(x) and 0<=x<=1 for x in anchor['center_norm']) and isinstance(anchor['raw_output'],str) and anchor['raw_output'],'Original successful raw focal-center evidence, no bbox-center substitution')
        t=0. if cl==cr else (frame-cl)/(cr-cl);center=[la['center_norm'][d]+t*(ra['center_norm'][d]-la['center_norm'][d]) for d in (0,1)]
        require(center==proof['raw_center_norm'],'Independent exact original raw-center interpolation')
        def anchor_evidence(row):return dict(source_frame=row['source_frame'],center_norm=row['center_norm'],anchor_request_sha256=row['anchor_request_sha256'],decoded_pixel_sha256=row['decoded_pixel_sha256'],raw_output_sha256=hashlib.sha256(row['raw_output'].encode()).hexdigest())
        expected_center_proof=dict(left_anchor=anchor_evidence(la),right_anchor=anchor_evidence(ra),alpha=t,axis='native_frame_ordinal',max_anchor_gap=8)
        require(proof['old_center_anchors']==expected_center_proof,'Actual original raw anchor/request/pixel/output SHA evidence')
        W,H=meta[sid]['width'],meta[sid]['height'];cw=max(1,min(W,(H*16)//9)*width//1000)
        # Recompute from original anchors, never the claimed output center.
        cx,cy=center
        x=int(round(max(0,min(cx*W-cw/2,W-cw))))
        y=int(round(max(0,min(cy*H-cw*9/32,max(0,math.floor(H-cw*9/16+1e-9))))))
        require(after[key]==[x,y,cw] and 0<=x<=W-cw and 0<=y and y+cw*9/16<=H+1e-9 and proof['legal'] is True,'Independent strict legal integer width geometry')
        checked_new+=1
    return dict(native_membership_preserved=True,baseline_C_exact_D_superset=True,portrait_unchanged=True,
                same_shot_real_PTS_width_interpolation=True,actual_original_raw_centers=True,width1000_identity=True,
                independent_strict_geometry=True,physical_parameters_exact=True),checked_new


def validate(evidence_path,metadata,rows,provenance):
    evidence=read(evidence_path)
    require(evidence['schema']=='SPRINT45_WIDTH_PACKAGE_EVIDENCE_V1','Width package evidence schema')
    width_payload=read(bound(evidence['width_by_video']));qa=read(bound(evidence['width_output_QA']))
    require(qa['status']=='PASS_NATIVE16_FROZEN_HEAD_NATIVE_SAMPLE_OUTPUT_AND_SAVE_QA' and qa['width_by_video_sha256']==evidence['width_by_video']['sha256'] and
            width_payload['head_sha256']==HEAD and width_payload['normalization_sha256']==NORM,'Actual frozen head/readout QA and save SHA')
    clock_registry=read(bound(evidence['source_clocks']))
    require(all([Fraction(t) for t in data['native_pts_exact']]==[Fraction(t) for t in clock_registry[sid]['normalized_exact_pts']] for sid,data in width_payload['width_by_video'].items()),'Actual width PTS equal immutable original native source clock registry')
    with zipfile.ZipFile(bound(evidence['baseline'])) as archive:baseline=[json.loads(x) for x in archive.read('predictions.jsonl').splitlines()]
    require(evidence['baseline']['sha256']==BASELINE,'Current40.47 baseline identity')
    field=lines(bound(evidence['field_frames']));requests=lines(bound(evidence['anchor_requests']));outputs=lines(bound(evidence['anchor_outputs']))
    request_map={(r['video_id'],r['source_frame']):r for r in requests};output_map={(r['video_id'],r['source_frame']):r for r in outputs}
    require(len(request_map)==len(requests) and len(output_map)==len(outputs) and set(request_map)==set(output_map),'Complete actual original anchor request/output identity')
    require(all(o['anchor_request_sha256']==request_map[k]['anchor_request_sha256'] and o['decoded_pixel_sha256']==request_map[k]['expected_pixel_sha256'] for k,o in output_map.items()),'Actual original request and same-frame decoded pixel bindings')
    if evidence['arm']=='D':
        import numpy as np
        output=read(bound(evidence['global_output_QA']))
        require(output['status']=='PASS_ALL426_GLOBAL_LOCAL_BINARY_OUTPUT_QA' and len(output['sources'])==426 and {s['id'] for s in output['sources']}=={str(i) for i in range(426)},'Actual full global/payoff first QA')
        expected=set(boxes(baseline));domain={(r['video_id'],r['source_frame']) for r in field};meta={r['video_id']:r for r in metadata['records']}
        for source in output['sources']:
            native=np.load(bound(dict(path=source['native_path'],sha256=source['native_sha256'])),allow_pickle=False)
            g=np.load(bound(dict(path=source['global_mask_path'],sha256=source['global_sha256'])),allow_pickle=False)
            p=np.load(bound(dict(path=source['payoff_mask_path'],sha256=source['payoff_sha256'])),allow_pickle=False)
            groups=native['groups'];require(g.dtype==p.dtype==np.bool_ and g.shape==p.shape==(source['cells'],) and len(groups)==meta[source['id']]['n_frames'],'Independent actual native cell mask domain')
            require(np.issubdtype(groups.dtype,np.integer) and groups.min()==0 and int(groups.max())+1==len(g) and bool((np.diff(groups)>=0).all()),'Independent original native ordinal groups')
            chosen=np.flatnonzero(np.logical_or(g,p)[groups]).tolist()
            expected.update((source['id'],frame) for frame in chosen if (source['id'],frame) in domain)
        require(set(boxes(rows))==expected,'Independent actual global/payoff native union + current baseline')
    checks,count=verify_arrays(metadata,lines(bound(evidence['prewidth_predictions'])),lines(bound(evidence['prewidth_provenance'])),rows,provenance,
        width_payload['width_by_video'],lines(bound(evidence['field_shots'])),outputs,baseline,evidence['arm'])
    checks.update(original_anchor_requests_and_pixels_bound=True,actual_C_or_D_native_selection_recomputed=True)
    return checks,count
