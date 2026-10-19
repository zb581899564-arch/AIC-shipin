"""Pure conditional width renderer. No files, models, labels or validators.

Consumes CURRENT40.47 predictions/provenance supplied by the caller. native.npz
baseline is intentionally absent from this interface. Caller binds original
field files and independently verifies new provenance/format after this returns.
"""
from bisect import bisect_left
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
import math
try:
    from .prod_common import require,HEAD_SHA,NORM_SHA,TOTAL
except ImportError:
    from prod_common import require,HEAD_SHA,NORM_SHA,TOTAL

SOURCE='QWEN_BASE_LM_WIDTH_HEAD_SAME_SHOT'


def shots(rows):
    ordered=sorted(rows,key=lambda r:(r['video_id'],r['source_frame']))
    require(len(ordered)==len({(r['video_id'],r['source_frame']) for r in ordered}),'Duplicate field shot frame')
    groups=[];previous=None
    for row in ordered:
        key=(row['video_id'],row['source_frame'])
        require(type(row['source_frame']) is int and row['source_frame']>=0 and type(row['is_shot_start']) is bool,'Actual native shot schema')
        if previous is None or key[0]!=previous[0] or key[1]!=previous[1]+1 or row['is_shot_start']:groups.append([])
        groups[-1].append(row);previous=key
    return groups


def geometry(width,W,H,center):
    require(type(width) is int and 1<=width<=1000 and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in center) and len(center)==2,'Width/raw normalized center domain')
    crop=max(1,min(W,H*16//9)*width//1000)
    left=round(min(max(center[0]*W-crop/2,0),W-crop))
    top=round(min(max(center[1]*H-crop*9/32,0),max(0,math.floor(H-crop*9/16+1e-9))))
    box=[int(left),int(top),crop]
    require(left>=0 and top>=0 and left+crop<=W and top+crop*9/16<=H+1e-9,'Actual strict legal integer native16 geometry')
    return box


def interpolated_width(frame,observations,widths,pts):
    require(observations,'Missing same-shot observation must be handled explicitly')
    pos=bisect_left(observations,frame)
    if pos==0:left=right=observations[0]
    elif pos==len(observations):left=right=observations[-1]
    else:left,right=observations[pos-1],observations[pos]
    if frame in widths:left=right=frame
    alpha=F(0) if left==right else (pts[frame]-pts[left])/(pts[right]-pts[left])
    value=F(widths[left])+(widths[right]-widths[left])*alpha
    result=int(round(value));require(1<=result<=1000,'Same-shot interpolation escaped width domain')
    return result,dict(left_sample_ordinal=left,right_sample_ordinal=right,left_width=widths[left],right_width=widths[right],
                       alpha_exact=str(alpha),axis='native_pts_exact',predicted_width=result)


def raw_center(frame,shot,anchors):
    frames=[r['source_frame'] for r in shot];schedule=frames[::8]
    if schedule[-1]!=frames[-1]:schedule.append(frames[-1])
    vid=shot[0]['video_id'];actual=[]
    for ordinal in schedule:
        require((vid,ordinal) in anchors,'Original max-gap8 center anchor missing')
        row=anchors[(vid,ordinal)]
        require(row['status']=='MODEL_OK' and row['used_fallback'] is False and row['spatial_source']=='QWEN_ANCHOR_SAME_FRAME' and
                isinstance(row['raw_output'],str) and bool(row['raw_output']) and len(row['center_norm'])==2 and
                all(type(x) in (int,float) and math.isfinite(x) and 0<=x<=1 for x in row['center_norm']),'Actual original raw focal center only, no bbox-center surrogate')
        actual.append(ordinal)
    pos=bisect_left(actual,frame)
    if pos<len(actual) and actual[pos]==frame:left=right=frame
    else:
        require(0<pos<len(actual),'Original same-shot centers must bracket selected native frame')
        left,right=actual[pos-1],actual[pos]
    alpha=0. if left==right else (frame-left)/(right-left)
    a,b=anchors[(vid,left)],anchors[(vid,right)]
    center=[a['center_norm'][j]+alpha*(b['center_norm'][j]-a['center_norm'][j]) for j in range(2)]
    def evidence(row):
        return dict(source_frame=row['source_frame'],center_norm=deepcopy(row['center_norm']),
                    anchor_request_sha256=row['anchor_request_sha256'],decoded_pixel_sha256=row['decoded_pixel_sha256'],
                    raw_output_sha256=hashlib.sha256(row['raw_output'].encode()).hexdigest())
    return center,dict(left_anchor=evidence(a),right_anchor=evidence(b),alpha=alpha,axis='native_frame_ordinal',max_anchor_gap=8)


def apply_to_predictions(predictions,provenance,width_by_video,field_shots,anchor_outputs,metadata):
    """Return (new_rows,new_provenance), preserving selected frames and portrait.

    width_by_video[sid] = {sample_ordinals:[native ordinals],
      predicted_width:[1..1000 ints],native_pts_exact:[exact seconds],
      head_sha256:ACTUAL_FROZEN_SHA,normalization_sha256:...,...}
    Widths interpolate only observations inside the same CONTIGUOUS field shot;
    a field gap is also a hard boundary. Empty-shot observation -> exact baseline
    copy, an explicit unobserved-domain rule rather than an engineering failure.
    """
    records=metadata['records'] if isinstance(metadata,dict) else metadata
    meta={r['video_id']:r for r in records}
    require(len(meta)==len(records) and len(predictions)==len(meta) and {p['video_id'] for p in predictions}==set(meta),'Complete current prediction/metadata source identities')
    require(all(m['targetRatioWH'] in ([16,9],[9,16]) and all(type(m[k]) is int and m[k]>0 for k in ('width','height','n_frames')) for m in records),'Exact registered ratio/native geometry metadata')
    landscape={sid for sid,m in meta.items() if m['targetRatioWH']==[16,9]}
    require(set(width_by_video)==landscape,'Fixed metadata native16 width routing, no target-based source selection')
    original={(r['video_id'],p['frame']):deepcopy(p['bboxes']) for r in predictions for p in r['predictions']}
    require(len(original)==sum(len(r['predictions']) for r in predictions),'Duplicate original selected frame')
    old_prov={(r['video_id'],r['source_frame']):r for r in provenance}
    require(len(old_prov)==len(provenance) and set(old_prov)==set(original),'Original accepted selected provenance membership')
    grouped=shots(field_shots);shot_for={}
    for number,shot in enumerate(grouped):
        for row in shot:shot_for[(row['video_id'],row['source_frame'])]=(number,shot)
    require(set(original)<=set(shot_for),'Current selected frame outside original spatial field/shot domain')
    anchors={(r['video_id'],r['source_frame']):r for r in anchor_outputs}
    require(len(anchors)==len(anchor_outputs),'Duplicate original raw center anchor')
    widths={};clocks={};observations={}
    for sid,data in width_by_video.items():
        samples=data['sample_ordinals'];values=data['predicted_width']
        require(all(not isinstance(t,(float,bool)) for t in data['native_pts_exact']),'Exact rational native PTS required')
        pts=[F(t) for t in data['native_pts_exact']]
        require(data['head_sha256']==HEAD_SHA and data['normalization_sha256']==NORM_SHA and len(samples)==len(values)>0 and samples==sorted(set(samples)) and
                all(type(x) is int and 0<=x<len(pts) for x in samples) and all(type(x) is int and 1<=x<=1000 for x in values),'Actual frozen width sample/shape/domain')
        require(len(pts)==meta[sid]['n_frames'] and all(b>a for a,b in zip(pts,pts[1:])),'Actual complete strictly increasing native PTS')
        widths[sid]=dict(zip(samples,values));clocks[sid]=pts
    # Precompute observations once per shot rather than searching all samples
    # per selected frame. No observation is borrowed across a cut or field gap.
    for number,shot in enumerate(grouped):
        sid=shot[0]['video_id'];low=shot[0]['source_frame'];high=shot[-1]['source_frame']
        if sid in widths:observations[number]=[f for f in width_by_video[sid]['sample_ordinals'] if low<=f<=high]
    rows=deepcopy(predictions);new_prov=deepcopy(provenance);prov={(r['video_id'],r['source_frame']):r for r in new_prov}
    for row in rows:
        sid=row['video_id'];m=meta[sid];row['model_params_b']=TOTAL/1e9
        require(row['targetRatioWH']==m['targetRatioWH'],'Current ratio metadata binding')
        if sid not in landscape:continue
        for prediction in row['predictions']:
            frame=prediction['frame'];key=(sid,frame);number,shot=shot_for[key];current=prov[key]
            require(current['box_xyw']==original[key],'Original baseline/provenance box equality')
            observed=observations[number]
            if not observed:
                current['width_head_application']=dict(decision='NO_SAME_SHOT_OBSERVATION_KEEP_BASELINE',width=1000,
                     head_sha256=HEAD_SHA,shot_first=shot[0]['source_frame'],shot_last=shot[-1]['source_frame'])
                continue
            width,width_proof=interpolated_width(frame,observed,widths[sid],clocks[sid])
            if width==1000:
                current['width_head_application']=dict(decision='WIDTH1000_COPY_ACCEPTED_BASELINE',head_sha256=HEAD_SHA,**width_proof)
                continue  # EXACT original box; never reconstruct from centers.
            center,center_proof=raw_center(frame,shot,anchors)
            box=geometry(width,m['width'],m['height'],center);prediction['bboxes']=box
            current.update(box_xyw=box,spatial_source=SOURCE,legal=True,old_spatial_provenance=deepcopy(old_prov[key]),
                 width_model=dict(head_sha256=HEAD_SHA,normalization_sha256=width_by_video[sid]['normalization_sha256'],**width_proof),
                 old_center_anchors=center_proof,raw_center_norm=center,shot_first=shot[0]['source_frame'],shot_last=shot[-1]['source_frame'])
    after={(r['video_id'],p['frame']):p['bboxes'] for r in rows for p in r['predictions']}
    require(set(after)==set(original),'Current40.47 selected frame membership changed')
    require(all(after[k]==original[k] and prov[k]==old_prov[k] for k in original if meta[k[0]]['targetRatioWH']==[9,16]),'Portrait box/provenance changed')
    return rows,new_prov
