"""Independent CPU pixel/tensor/token replay and fixed native-reference gate."""
import argparse
import hashlib
import json
import math
import traceback
from common import ROOT, RUN, paths, read, save, sha, WIDTH_PROMPT

def replay_encode(processor,messages):
    import torch
    from qwen_vl_utils import process_vision_info
    text = processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    ims,vids = process_vision_info(messages,image_patch_size=16)
    if vids or len(ims) != 1: raise ValueError('replay vision scope changed')
    values = processor(text=[text],images=ims,padding=True,truncation=False,return_tensors='pt')
    info = {k:{'shape':list(t.shape),'dtype':str(t.dtype),
        'sha256':hashlib.sha256(t.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()} for k,t in values.items()}
    return info,text

def box(center,W,H,p):
    w = max(1,min(W,math.floor(H*16/9))*p//1000)
    h = w*9/16
    x = round(min(max(center[0]*W-w/2,0),W-w))
    y = round(min(max(center[1]*H-h/2,0),max(0,math.floor(H-h+1e-9))))
    if x<0 or y<0 or x+w>W or y+h>H: raise ValueError('independent geometry invalid')
    return [int(x),int(y),int(w)]

def iou(pred,ref):
    x,y,w = pred;h=w*9/16
    a,b,c,d = ref
    overlap = max(0,min(x+w,a+c)-max(x,a))*max(0,min(y+h,b+d)-max(y,b))
    return overlap/(w*h+c*d-overlap)

def main(role):
    paths()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from spatial_baseline import Qwen3VL
    if role == 'confirm' and read(ROOT/'screen/result.json')['status'] != 'PASS_REGISTERED_STATIC_SCREEN_ONLY':
        raise ValueError('confirmation requires passed frozen screen')
    out = ROOT/role
    if (out/'result.json').exists(): raise ValueError('successful independent replay/evaluation is not repeated')
    config = read(RUN/'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    inputs = [r for r in read(ROOT/'inputs.json') if r['role'] == role]
    rawcalls = [json.loads(s) for s in (out/'calls.jsonl').read_text().splitlines() if s]
    predictions = [json.loads(s) for s in (out/'predictions.jsonl').read_text().splitlines() if s]
    if len(rawcalls) != 2*len(inputs) or len(predictions) != len(inputs): raise ValueError('real call denominator incomplete')
    lookup = {(r['item_id'],r['stage']):r for r in rawcalls}
    if len(lookup) != len(rawcalls): raise ValueError('duplicate calls')
    labels = {r['item_id']:r for r in read(ROOT/'reference/labels.json') if r['role'] == role}
    rows,checks,invalid = [],[],0
    for item,rec in zip(inputs,predictions):
        if rec['item_id'] != item['item_id']: raise ValueError('prediction order/identity changed')
        proof = read(ROOT/item['proof'])
        array = np.load(ROOT/'rgb'/f'{item["key"]}.npy',allow_pickle=False)
        if hashlib.sha256(array.tobytes()).hexdigest() != item['rgb_sha256'] or array.shape != (item['height'],item['width'],3):
            raise ValueError('original decoded RGB replay identity failed')
        image = Image.fromarray(array,'RGB')
        baseline = []
        class Capture:
            max_pixels = 131072
            def _generate(self,m,limit): baseline.extend(m);return ''
        Qwen3VL.predict_focus(Capture(),image,[16,9],128)
        width = [{'role':'user','content':[{'type':'image','image':image,'max_pixels':131072},
                                         {'type':'text','text':WIDTH_PROMPT}]}]
        for stage,messages in [('baseline',baseline),('width',width)]:
            tensors,text = replay_encode(processor,messages)
            call = lookup[item['item_id'],stage]
            p = proof['stages'][stage]
            if tensors != p['tensors'] or text != p['template_text'] or call['actual_tensor_file_sha256'] != p['file_sha256']:
                raise ValueError('independent actual processor input replay failed')
            decoded = processor.batch_decode([call['output_ids']],skip_special_tokens=True,clean_up_tokenization_spaces=False)[0]
            if decoded != call['raw'] or len(call['output_ids']) != call['output_tokens'] or call['input_tokens'] != p['input_tokens']:
                raise ValueError('real generated-token/raw replay failed')
        if rec['status'] != 'MODEL_OK':
            invalid += 1;rows.append({'item_id':item['item_id'],'baseline':0,'candidate':0,'delta':0,'invalid':True});continue
        c = json.loads(lookup[item['item_id'],'baseline']['raw'])['center']
        if len(c)!=2 or any(type(v) is not int or not 0<=v<=1000 for v in c): raise ValueError('independent center grammar failed')
        wp = json.loads(lookup[item['item_id'],'width']['raw'])
        if set(wp)!={'width'} or type(wp['width']) is not int or not 1<=wp['width']<=1000: raise ValueError('independent width grammar failed')
        center = [v/1000 for v in c]
        base = box(center,item['width'],item['height'],1000)
        candidate = box(center,item['width'],item['height'],wp['width'])
        if base != rec['baseline_box'] or candidate != rec['candidate_box']: raise ValueError('independent parsed geometry mismatch')
        gt = labels[item['item_id']]
        if gt['source_sha256'] != item['source_sha256']: raise ValueError('original human-reference identity changed')
        b,t = iou(base,gt['reference_xywh']),iou(candidate,gt['reference_xywh'])
        rows.append({'item_id':item['item_id'],'baseline':b,'candidate':t,'delta':t-b,'changed':base!=candidate})
        checks.append({'item_id':item['item_id'],'processor_tensor_token_grammar_geometry_native_RGB':'PASS'})
    n=len(rows);delta=sum(r['delta'] for r in rows)/n
    positive=sum(r['delta']>0 for r in rows);changed=sum(r.get('changed',False) for r in rows)
    gates = {'macro_gain_at_least_0_05':delta>=0.05,'positive_at_least_75_percent':positive*4>=n*3,
             'each_file_loss_no_more_than_0_05':all(r['delta']>=-0.05 for r in rows),
             'at_least_three_changed_files':changed>=3,'no_invalid_outputs':invalid==0,
             'full_registered_denominator':n==read(ROOT/'protocol.json')['items_per_role']}
    passed=all(gates.values())
    save(out/'replay_acceptance.json',{'status':'PASS_INDEPENDENT_PROCESSOR_TOKEN_RAW_GRAMMAR_GEOMETRY_REPLAY',
        'checks':checks,'invalid_preserved':invalid,'model_calls':0,'CUDA_initialized':torch.cuda.is_initialized()})
    save(out/'result.json',{'status':('PASS_REGISTERED_STATIC_SCREEN_ONLY' if role=='screen' else 'PASS_REGISTERED_STATIC_CONFIRM_ONLY') if passed else 'STOP_REGISTERED_STATIC_GATE_REJECTED',
        'role':role,'macro_baseline':sum(r['baseline'] for r in rows)/n,'macro_candidate':sum(r['candidate'] for r in rows)/n,
        'macro_delta':delta,'positive':positive,'changed':changed,'invalid':invalid,'gates':gates,'rows':rows,
        'scope':'native16:9 static file-level reference only; original source independence and video transfer UNKNOWN',
        'official_score':None,'production_admitted':False})
    print(json.dumps({k:v for k,v in read(out/'result.json').items() if k not in ('rows','scope')},ensure_ascii=False),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--role',choices=['screen','confirm'],required=True);a=ap.parse_args()
    try: main(a.role)
    except Exception as e:
        p=ROOT/f'{a.role}_replay_failure.json'
        if not p.exists(): save(p,{'status':'STOP_PRESERVE_SUCCESS_RAW','error':repr(e),'traceback':traceback.format_exc()})
        raise
