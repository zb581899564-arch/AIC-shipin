"""A single registered width-only arm on cached, accepted actual inputs."""
import argparse
import datetime as dt
import json
import os
import time
import traceback
from common import ROOT, RUN, paths, read, save, sha, tensor_info, width_value, geometry

def main(role):
    paths()
    import torch
    import transformers
    from spatial_baseline import Qwen3VL, parse_focus_norm, compute_crop_size, center_to_box
    from engine import frozen_identity
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    if not os.environ.get('CUDA_VISIBLE_DEVICES'): raise ValueError('registered GPU child needs a real visible device')
    if transformers.__version__ != '4.57.1': raise ValueError('frozen processor/runtime changed')
    if read(ROOT/'input_acceptance.json')['status'] != 'PASS_FORTY_REAL_STATIC_RGB_EIGHTY_PROCESSOR_INPUTS':
        raise ValueError('all registered real CPU inputs required')
    lock = read(ROOT/'source_lock.json')
    for rel,digest in lock['files'].items():
        if sha(ROOT/rel) != digest: raise ValueError('frozen source/input changed: '+rel)
    for p,digest in lock['external_files'].items():
        if sha(p) != digest: raise ValueError('frozen dependency changed: '+p)
    if role == 'confirm' and read(ROOT/'selected.json')['screen_result_sha256'] != sha(ROOT/'screen/result.json'):
        raise ValueError('screen selection not frozen')
    out = ROOT/role
    out.mkdir()
    save(out/'started.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'source_lock_sha256':sha(ROOT/'source_lock.json'),'reference_annotations_parsed':False})
    config = read(RUN/'b_score_aligned_package_v4/config.json')
    model = Qwen3VL(config['model_dir'], max_pixels=131072, device_map={'':'cuda:0'}, attn_implementation='sdpa')
    for p in model.model.parameters(): p.requires_grad_(False)
    identity = frozen_identity(model.model,config)
    save(out/'model_identity.json',{'base':identity,'time_adapter_enabled':False,
        'pipeline_parameters_if_integrated':8782459120,'optimizer_updates':0})
    rows = [r for r in read(ROOT/'inputs.json') if r['role'] == role]
    if len(rows) != read(ROOT/'protocol.json')['items_per_role']: raise ValueError('frozen denominator changed')
    model.reset_peak_memory()
    with (out/'calls.jsonl').open('x',encoding='utf-8') as calls,(out/'predictions.jsonl').open('x',encoding='utf-8') as predictions:
        for item in rows:
            proof = read(ROOT/item['proof'])
            answers = {}
            for stage,limit in [('baseline',128),('width',64)]:
                expected = proof['stages'][stage]
                path = ROOT/expected['path']
                if sha(path) != expected['file_sha256']: raise ValueError('cached tensor file changed')
                values = torch.load(path,map_location='cpu',weights_only=True)
                if tensor_info(values) != expected['tensors']: raise ValueError('actual cached tensor mismatch')
                prefix = int(values['input_ids'].shape[1])
                if prefix != expected['input_tokens']: raise ValueError('prefix changed')
                values = {k:v.to(model.device) for k,v in values.items()}
                started = time.monotonic()
                with torch.inference_mode():
                    generated = model.model.generate(**values,max_new_tokens=limit,do_sample=False,num_beams=1,use_cache=True)
                torch.cuda.synchronize()
                ids = generated[:,prefix:].detach().cpu()
                raw = model.processor.batch_decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)[0]
                rec = {'item_id':item['item_id'],'stage':stage,'raw':raw,'output_ids':ids[0].tolist(),
                    'input_tokens':prefix,'output_tokens':int(ids.shape[1]),'seconds':time.monotonic()-started,
                    'actual_tensor_file_sha256':expected['file_sha256'],'template_sha256':expected['template_sha256']}
                calls.write(json.dumps(rec,ensure_ascii=False)+'\n');calls.flush();os.fsync(calls.fileno())
                answers[stage] = raw
            record = {'item_id':item['item_id'],'source_sha256':item['source_sha256'],'status':'MODEL_OK',
                      'reference_annotations_parsed':False}
            try:
                center = parse_focus_norm(answers['baseline'],item['width'],item['height'])
                if center is None: raise ValueError('original center grammar failed')
                permille = width_value(answers['width'])
                cw,hf = compute_crop_size(item['width'],item['height'],16,9)
                baseline = center_to_box(*center,item['width'],item['height'],cw,hf)
                if geometry(center,item['width'],item['height'],1000) != baseline:
                    raise ValueError('new geometry no longer exactly preserves original baseline at1000')
                record.update(center=center,width_permille=permille,baseline_box=baseline,
                    candidate_box=geometry(center,item['width'],item['height'],permille))
            except Exception as e:
                record.update(status='INVALID_PRESERVED_NO_FALLBACK',error=repr(e),baseline_box=None,candidate_box=None)
            predictions.write(json.dumps(record,ensure_ascii=False)+'\n');predictions.flush()
            print(json.dumps({'item_id':item['item_id'],'status':record['status']}),flush=True)
    save(out/'inference_completion.json',{'status':'EXECUTION_COMPLETE_NOT_QUALITY',
        'items':len(rows),'calls':len(rows)*2,'predictions_sha256':sha(out/'predictions.jsonl'),
        'peak_memory_mib':model.peak_memory_mib(),'optimizer_updates':0,'source_lock_sha256':sha(ROOT/'source_lock.json')})

if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--role',choices=['screen','confirm'],required=True)
    args = parser.parse_args()
    try: main(args.role)
    except Exception as e:
        path = ROOT/f'{args.role}_inference_failure.json'
        if not path.exists(): save(path,{'status':'STOP_PRESERVE_RAW_SUCCESS_NO_AUTOMATIC_RETRY','error':repr(e),'traceback':traceback.format_exc()})
        raise
