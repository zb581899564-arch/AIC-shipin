"""Separate integer geometry and provenance verifier, no test ground truth."""
import json
from fractions import Fraction as F
from pathlib import Path

def verify(base,rows,meta,arm):
    scale=F(98,100) if arm=='RBOTH_098' else F(99,100)
    ratios={(16,9),(9,16)} if arm=='RBOTH_098' else {(16,9)} if arm=='R16_099' else {(9,16)}
    if len(rows)!=426 or {r['video_id'] for r in rows}!=set(meta):raise ValueError('426 set')
    before={r['video_id']:r for r in base};changed=0;changed_videos=set();minimum=F(1)
    for row in rows:
        vid=row['video_id'];old=before[vid];m=meta[vid];tw,th=row['targetRatioWH']
        if row['targetRatioWH']!=old['targetRatioWH'] or row['model_params_b']!=8.78245912 or not row['predictions']:raise ValueError('ratio/params/nonempty')
        if [p['frame'] for p in row['predictions']]!=[p['frame'] for p in old['predictions']]:raise ValueError('D8 frame membership changed')
        for a,b in zip(old['predictions'],row['predictions']):
            if a['frame']!=b['frame'] or not 0<=b['frame']<m['n_frames']:raise ValueError('original native frame')
            x,y,w=a['bboxes'];u,v,z=b['bboxes']
            if any(type(q) is not int for q in (u,v,z)) or not (0<=u and 0<=v and 0<z and u+z<=m['width'] and F(v)+F(z*th,tw)<=m['height']):raise ValueError('strict geometry')
            if (tw,th) in ratios:
                expected=-((-w*scale.numerator)//scale.denominator)
                horizontal=(w-expected)//2;vertical=F((w-expected)*th,tw*2)
                if [u,v,z]!=[x+horizontal,y+vertical.numerator//vertical.denominator,expected]:raise ValueError('separate exact transform mismatch')
                if not (x<=u and y<=v and u+z<=x+w and F(v)+F(z*th,tw)<=F(y)+F(w*th,tw)):raise ValueError('not nested')
                pair=F(z*z,w*w)
                if pair<scale*scale:raise ValueError('bounded perturbation')
                minimum=min(minimum,pair)
                if abs(F(2*u+z-(2*x+w),2))>F(1,2) or abs(F(v-y)+F((z-w)*th,2*tw))>1:raise ValueError('box-center rounding bound')
            elif a!=b:raise ValueError('unselected target ratio changed')
            if a!=b:changed+=1;changed_videos.add(vid)
    if not changed:raise ValueError('zero prediction difference')
    return {'status':'PASS_INDEPENDENT_BOUNDED_NESTED_GEOMETRY_AND_D8_FRAME_IDENTITY',
            'frames':sum(len(r['predictions']) for r in rows),'changed_frames':changed,'changed_videos':len(changed_videos),
            'minimum_original_new_IoU':float(minimum),'mathematical_max_any_GT_IoU_loss_bound':float(1-minimum),
            'GT_read':False,'quality_proved':False}
