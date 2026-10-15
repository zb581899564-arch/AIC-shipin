"""Independent CPU replay and fixed static paired IoU gate; no production."""
import argparse
import hashlib
import json
import math
import traceback
from gws_common import ROOT,OLD,RUN,paths,read,save,sha,info,encode

def strict_geometry(raw,W,H,center):
    value=json.loads(raw.strip())
    if set(value)!={'width'} or type(value['width']) is not int or not 1<=value['width']<=1000: raise ValueError('width grammar')
    width=max(1,min(W,H*16//9)*value['width']//1000)
    left=round(min(max(center[0]*W-width/2,0),W-width))
    top=round(min(max(center[1]*H-width*9/32,0),max(0,math.floor(H-width*9/16+1e-9))))
    return [int(left),int(top),width]


def overlap(a,b):
    x,y,w=a;h=w*9/16;u,v,p,q=b
    area=max(0,min(x+w,u+p)-max(x,u))*max(0,min(y+h,v+q)-max(y,v))
    return area/(w*h+p*q-area)

def main(role):
    paths()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    if torch.cuda.is_initialized(): raise ValueError('CPU replay initialized CUDA')
    out=ROOT/role
    if read(out/'generation_completion.json')['predictions_sha256']!=sha(out/'predictions.jsonl'): raise ValueError('prediction bytes')
    cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    proc=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    items={x['item_id']:x for x in read(ROOT/'eval_inputs.json') if x['role']==role}
    preds={x['item_id']:x for x in [json.loads(l) for l in (out/'predictions.jsonl').read_text().splitlines()]}
    calls=[json.loads(l) for l in (out/'calls.jsonl').read_text().splitlines()]
    if set(preds)!=set(items) or len(calls)!=20*(2 if role=='confirm' else 1): raise ValueError('denominator/call count')
    rows=[]
    old={r['item_id']:r for r in [json.loads(x) for x in (OLD/'recovery_01/screen/predictions.jsonl').read_text().splitlines()]}
    for call in calls:
        item=items[call['item_id']]
        if proc.tokenizer.decode(call['output_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)!=call['raw']: raise ValueError('raw/token identity')
        if call['stage']=='trained_width':
            proof=read(item['new_proof']);image=Image.fromarray(np.load(item['reused_RGB'],allow_pickle=False))
            actual,text,_=encode(proc,image)
            if info(actual)!=proof['tensors'] or text!=proof['template_text'] or call['input_tokens']!=proof['input_tokens']:
                raise ValueError('independent real CPU input replay')
            if call['tensor_file_sha256']!=proof['file_sha256']: raise ValueError('call/input binding')
            try: box=strict_geometry(call['raw'],item['width'],item['height'],preds[item['item_id']]['preserved_center'])
            except Exception:
                if preds[item['item_id']]['status']!='INVALID_PRESERVED': raise
            else:
                if box!=preds[item['item_id']]['candidate_box']: raise ValueError('independent crop geometry')
        else:
            oldproof=read(OLD/item['proof'])['stages']['baseline']
            if call['tensor_file_sha256']!=oldproof['file_sha256'] or call['input_tokens']!=oldproof['input_tokens']: raise ValueError('baseline cached binding')
            from spatial_baseline import parse_focus_norm,compute_crop_size,center_to_box
            center=parse_focus_norm(call['raw'],item['width'],item['height'])
            if center is None: raise ValueError('baseline parser')
            cw,hf=compute_crop_size(item['width'],item['height'],16,9)
            if center_to_box(*center,item['width'],item['height'],cw,hf)!=preds[item['item_id']]['baseline_box']: raise ValueError('baseline geometry')
    refs={x['item_id']:x for x in read(OLD/'reference/labels.json') if x['role']==role}
    for key,item in items.items():
        ref=refs[key];pred=preds[key]
        if role=='screen' and (pred['baseline_box']!=old[key]['baseline_box'] or pred['preserved_center']!=old[key]['center']): raise ValueError('original center changed')
        if ref['source_sha256']!=item['source_sha256']: raise ValueError('reference/source identity')
        baseline=overlap(pred['baseline_box'],ref['reference_xywh'])
        candidate=overlap(pred['candidate_box'],ref['reference_xywh']) if pred['status']=='VALID' else 0.0
        rows.append({'item_id':key,'baseline':baseline,'candidate':candidate,'delta':candidate-baseline,
                     'changed':pred['candidate_box']!=pred['baseline_box'],'invalid':pred['status']!='VALID'})
    save(out/'replay_acceptance.json',{'status':'PASS_ALL_NEW_CALL_INPUT_TOKEN_RAW_GRAMMAR_NATIVE_GEOMETRY_BINDING',
         'calls':len(calls),'rows':len(rows),'original_JPEG_decode_repeated':False,'CUDA_initialized':False})
    gate=read(ROOT/'protocol.json')['quality_gates'];delta=sum(r['delta'] for r in rows)/20
    checks={'macro_gain':delta>=gate['macro_paired_IoU_gain_min'],
            'positive75_percent':sum(r['delta']>0 for r in rows)>=15,
            'each_loss':all(r['delta']>=-gate['each_file_IoU_loss_max'] for r in rows),
            'changed3':sum(r['changed'] for r in rows)>=3,'invalid0':not any(r['invalid'] for r in rows),'denominator20':len(rows)==20}
    save(out/'result.json',{'status':'PASS_REGISTERED_STATIC_GATE' if all(checks.values()) else 'STOP_REGISTERED_STATIC_GATE_REJECTED',
         'macro_baseline':sum(r['baseline'] for r in rows)/20,'macro_candidate':sum(r['candidate'] for r in rows)/20,
         'macro_delta':delta,'positive':sum(r['delta']>0 for r in rows),'changed':sum(r['changed'] for r in rows),
         'invalid':sum(r['invalid'] for r in rows),'checks':checks,'rows':rows,
         'scope':'native16 static file-level research; video transfer/original source independence UNKNOWN','production_admitted':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--role',choices=['screen','confirm'],required=True);args=p.parse_args()
    try: main(args.role)
    except Exception as e:
        save(ROOT/(args.role+'_replay_failure.json'),{'error':repr(e),'traceback':traceback.format_exc(),'preserve_all_success':True});raise
