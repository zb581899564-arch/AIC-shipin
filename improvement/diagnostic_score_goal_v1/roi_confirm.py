"""First original-BASE and frozen relative-ROI check on historical confirm20.

No head fitting. Existing accepted131072 baseline inputs are adopted;
new65536 vision inputs are made from stored RGB with first independent QA.
"""
import argparse
import hashlib
import os
from pathlib import Path
import sys
import time
import traceback

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'roi_code_06'),
              str(Path(__file__).resolve().parents[1]/'roi_relative_code_09')]
from roi_runtime import WORK,A,PYTHON,require,read,save,ref,bound,sha,utc,io_module,registration,check_pixels
from roi_pool import candidate_features
import crop_geometry as geom
from roi_ridge import ARMS,predict,choose


def config(root):
    registration(root)
    r=read(root/'roi_confirm_registration_10.json')
    require(r['new_BASE_generations']==20 and r['new_vision_readouts']==20 and r['new_head_fits']==0,
            'Exact new confirmation budget')
    for n,h in r['new_code'].items():require(sha(root/'roi_confirm_code_10'/n)==h,'Frozen confirmation code changed')
    relative=read(bound(r['relative_model_registration']))
    for n,h in relative['new_code'].items():
        require(sha(root/'roi_relative_code_09'/n)==h,'Actual frozen relative predictor code changed')
    require(Path(sys.modules['roi_ridge'].__file__).resolve()==root/'roi_relative_code_09/roi_ridge.py',
            'Relative model implementation was shadowed')
    for reference in r['frozen_predictor'].values():bound(reference)
    admission=read(bound(r['admission']))
    require(admission['status']=='ADMIT_FIRST_FROZEN_RELATIVE_ROI_CONFIRM20_NOT_PRODUCTION','Actual prospective screen decision')
    return r


def prepare(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU child hides own CUDA')
    reg=config(root)
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2);io=io_module(root);runtime=io.runtime_only()
    processor=AutoProcessor.from_pretrained(io.read(io.CONFIG)['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
    old_lock=read(bound(reg['original_eval_source_lock']))
    require(not (A/'recovery_01/confirm/inference_completion.json').exists(),'Never repeat an old successful confirm BASE generation')
    items=[v for v in read(bound(reg['original_inputs'])) if v['role']=='confirm'];require(len(items)==20,'Original fixed20 confirm sources')
    out=root/'roi_confirm_inputs_10';out.mkdir(exist_ok=False);entries=[]
    for i,item in enumerate(items):
        proof=read(A/item['proof']);rgbp=A/'rgb'/(item['key']+'.npy');rgb=np.load(rgbp,allow_pickle=False)
        require(sha(A/item['proof'])==old_lock['files'][item['proof']], 'Original frozen confirm proof changed')
        require(rgb.shape==(item['height'],item['width'],3) and rgb.dtype==np.uint8
                and hashlib.sha256(rgb.tobytes()).hexdigest()==proof['RGB_sha256']==item['rgb_sha256']
                and proof['source_sha256']==item['source_sha256'],'Confirm original source/RGB identity')
        vision=dict(processor.image_processor(images=[Image.fromarray(rgb)],return_tensors='pt'));check_pixels(vision)
        vp=out/('C%02d.pt'%i);torch.save(vision,vp)
        baseline=proof['stages']['baseline'];bp=A/baseline['path']
        require(sha(bp)==baseline['file_sha256'],'Original accepted baseline input bytes')
        require(sha(bp)==old_lock['files'][baseline['path']], 'Original frozen BASE tensor reference differs')
        original=torch.load(bp,map_location='cpu',weights_only=True)
        require(runtime.tensor_signature(original)==baseline['tensors'],'Original accepted BASE prefix pixels/grid')
        row=dict(item_id=item['item_id'],source_sha256=item['source_sha256'],width=item['width'],height=item['height'],
                 role='confirm',RGB=ref(rgbp),original_proof=ref(A/item['proof']),original_BASE_input=ref(bp),
                 original_BASE_signature=baseline['tensors'],new_vision=ref(vp),new_vision_signature=runtime.tensor_signature(vision),
                 reference_available_to_inference=False,new_decode=False)
        rp=out/('C%02d.json'%i);save(rp,row);entries.append(ref(rp))
    save(out/'prepared.json',dict(entries=entries,new65536_prepare_calls=20,old131072_processor_repeated=0,new_decode=0))


def input_qa(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','First independent confirm input QA CPU only')
    config(root)
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2);io=io_module(root);runtime=io.runtime_only()
    processor=AutoProcessor.from_pretrained(io.read(io.CONFIG)['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
    out=root/'roi_confirm_inputs_10';prepared=read(out/'prepared.json');seen=set()
    for reference in prepared['entries']:
        row=read(bound(reference));proof=read(bound(row['original_proof']));rgb=np.load(bound(row['RGB']),allow_pickle=False)
        require(row['item_id'] not in seen and proof['source_sha256']==row['source_sha256']
                and hashlib.sha256(rgb.tobytes()).hexdigest()==proof['RGB_sha256'],'Independent source/RGB identity')
        base=torch.load(bound(row['original_BASE_input']),map_location='cpu',weights_only=True)
        require(runtime.tensor_signature(base)==row['original_BASE_signature']==proof['stages']['baseline']['tensors'],
                'Independent inherited BASE input/template binding')
        vision=torch.load(bound(row['new_vision']),map_location='cpu',weights_only=True);check_pixels(vision)
        independent=dict(processor.image_processor(images=[Image.fromarray(rgb)],return_tensors='pt'))
        require(runtime.tensor_signature(vision)==row['new_vision_signature'] and set(vision)==set(independent)
                and all(torch.equal(vision[k],independent[k]) for k in vision),'Independent RGB→new65536 input bit identity')
        require(row['reference_available_to_inference'] is False,'Reference leaked to inference')
        seen.add(row['item_id'])
    require(len(seen)==20 and not torch.cuda.is_initialized(),'Actual complete CPU confirmation acceptance')
    save(out/'input_acceptance.json',dict(status='PASS_FIRST_ALL20_CONFIRM_BASE_AND_NEW_VISION_INPUTS',
         prepared=ref(out/'prepared.json'),registration=ref(root/'roi_confirm_registration_10.json'),
         actual_sources=20,first_new65536_prepare_calls=20,first_independent65536_QA_calls=20,
         old131072_processor_repeated=0,new_decode=0,CUDA_initialized=False))


def infer(root):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Actual GPU child retains nonempty CUDA')
    reg=config(root);io=io_module(root);runtime=io.runtime_only()
    sys.path.insert(0,str(io.RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    from contracts import parse_focus_norm
    verify_live_gpu_reservation()
    import numpy as np
    import torch
    torch.set_num_threads(2)
    gate=read(root/'roi_confirm_inputs_10/input_acceptance.json')
    require(gate['status']=='PASS_FIRST_ALL20_CONFIRM_BASE_AND_NEW_VISION_INPUTS','All actual first inputs before GPU')
    entries=read(bound(gate['prepared']))['entries'];out=root/'roi_confirm_GPU_10';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(pid=os.getpid(),utc=utc(),input_acceptance=ref(root/'roi_confirm_inputs_10/input_acceptance.json')))
    cfg=io.read(io.CONFIG);model,processor,identity=runtime.b_engine.load_model(cfg);io.verify_model(model,identity)
    require(sum(p.numel() for p in model.parameters())==8782459120,'Actual complete base/TIME model inventory')
    native=model.get_base_model();core=native.model;success_base=[];success_vision=[]
    attempts=out/'attempts.jsonl';attempts.touch(exist_ok=False)
    def event(**value):
        with attempts.open('a') as f:f.write(__import__('json').dumps(dict(utc=utc(),**value))+'\n');f.flush();os.fsync(f.fileno())
    try:
        for i,reference in enumerate(entries):
            row=read(bound(reference));base=torch.load(bound(row['original_BASE_input']),map_location='cpu',weights_only=True)
            require(runtime.tensor_signature(base)==row['original_BASE_signature'],'Actual original BASE input changed')
            gpu={k:v.to('cuda') for k,v in base.items()};prefix=int(base['input_ids'].shape[1]);t0=time.monotonic()
            event(event='BEGIN_FIRST_ORIGINAL_BASE_CENTER',item_id=row['item_id'])
            with model.disable_adapter(),torch.inference_mode():
                require(all(bool(m.disable_adapters) for m in model.modules() if hasattr(m,'disable_adapters') and hasattr(m,'lora_A')),
                        'Actual BASE spatial role requires disabled TIME')
                generated=model.generate(**gpu,max_new_tokens=128,do_sample=False,num_beams=1,use_cache=True)
            torch.cuda.synchronize();io.enabled_layers(model)
            ids=generated[0,prefix:].detach().cpu().tolist();raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            rp=out/('C%02d.base_raw.json'%i)
            save(rp,dict(item_id=row['item_id'],source=reference,raw=raw,output_token_ids=ids,prefix_tokens=prefix,
                 elapsed_seconds=time.monotonic()-t0,first_BASE_generation=True,actual_TIME_disabled_during_BASE=True,
                 generation_config='Original128 greedy no-beam BASE behavior; no new grammar/prompt',labels_read=False))
            success_base.append(ref(rp));center=parse_focus_norm(raw,row['width'],row['height'])
            require(center is not None and len(ids)>0,'Original strict center parser failed; preserve raw, no fallback')
            box=geom.place_crop(row['width'],row['height'],center)
            save(out/('C%02d.base.json'%i),dict(item_id=row['item_id'],source_sha256=row['source_sha256'],source=reference,
                 original_BASE_raw=ref(rp),center=center,original_BASE_box=box,candidate_boxes=geom.candidate_pool(row['width'],row['height'],box)))
            event(event='ACCEPTED_FIRST_ORIGINAL_BASE_CENTER',item_id=row['item_id'])
            del gpu,base,generated
        for i,reference in enumerate(entries):
            row=read(bound(reference));baseline=read(out/('C%02d.base.json'%i))
            vision=torch.load(bound(row['new_vision']),map_location='cpu',weights_only=True);mh,mw=check_pixels(vision)
            gpu={k:v.to('cuda') for k,v in vision.items()};t0=time.monotonic();event(event='BEGIN_FIRST_CONFIRM_VISION',item_id=row['item_id'])
            with torch.inference_mode():embeds,deep=core.get_image_features(**gpu)
            torch.cuda.synchronize()
            require(isinstance(embeds,tuple) and len(embeds)==1 and embeds[0].shape==(mh*mw,4096)
                    and torch.isfinite(embeds[0]).all(),'Actual confirm merged-token mapping')
            tokens=embeds[0].detach().cpu().contiguous()
            features=candidate_features(tokens.float().numpy().reshape(mh,mw,4096),baseline['candidate_boxes'],row['width'],row['height'])
            tp=out/('C%02d.tokens.pt'%i);fp=out/('C%02d.features.npy'%i);torch.save(tokens,tp)
            with fp.open('xb') as f:np.save(f,features,allow_pickle=False)
            result=dict(item_id=row['item_id'],source_sha256=row['source_sha256'],source=reference,
                 original_BASE=ref(out/('C%02d.base.json'%i)),tokens=ref(tp),features=ref(fp),merged_grid=[mh,mw],
                 elapsed_seconds=time.monotonic()-t0,labels_read=False,first_new_vision_readout=True)
            rp=out/('C%02d.result.json'%i);save(rp,result);success_vision.append(ref(rp))
            event(event='ACCEPTED_FIRST_CONFIRM_VISION',item_id=row['item_id'])
            del gpu,vision,embeds,deep,tokens,features
        require(len(success_base)==len(success_vision)==20 and io.enabled_layers(model)==[False]*144
                and runtime.b_engine.frozen_identity(model,cfg)==identity['base']
                and runtime.b_engine.adapter_identity(model,cfg)==identity['adapter'],'Complete actual frozen confirmation')
        save(out/'completion.json',dict(status='PASS_FIRST20_BASE_AND20_VISION_CONFIRM_EXECUTION_NOT_QUALITY',
             base_calls=success_base,entries=success_vision,first_new_BASE_generations=20,first_new_vision_readouts=20,
             new_optimizer_updates=0,labels_read=False,model_identity=identity))
    except BaseException as e:
        save(out/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),successful_BASE=success_base,
             successful_vision=success_vision,preserve_all_success=True,do_not_repeat_success=True,failure_not_empty=True));raise


def output_qa(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent output check CPU only')
    reg=config(root);io=io_module(root);io.runtime_only()
    from contracts import parse_focus_norm
    from transformers import AutoTokenizer
    import torch
    import numpy as np
    tokenizer=AutoTokenizer.from_pretrained(io.read(io.CONFIG)['model_dir'],local_files_only=True)
    out=root/'roi_confirm_GPU_10';done=read(out/'completion.json');seen=set()
    for reference in done['entries']:
        result=read(bound(reference));row=read(bound(result['source']));baseline=read(bound(result['original_BASE']));raw=read(bound(baseline['original_BASE_raw']))
        require(result['item_id']==row['item_id']==baseline['item_id']==raw['item_id']
                and baseline['source']==raw['source']==result['source']
                and 0<len(raw['output_token_ids'])<=128
                and raw['prefix_tokens']==row['original_BASE_signature']['input_ids']['shape'][1],
                'Independent raw generation/source/prefix binding')
        text=tokenizer.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
        center=parse_focus_norm(text,row['width'],row['height'])
        require(text==raw['raw'] and center==baseline['center'] and geom.place_crop(row['width'],row['height'],center)==baseline['original_BASE_box'],
                'Independent original raw/parser/BASE geometry mismatch')
        boxes=geom.candidate_pool(row['width'],row['height'],baseline['original_BASE_box'])
        require(boxes==baseline['candidate_boxes'] and result['source_sha256']==row['source_sha256'] and row['item_id'] not in seen,
                'Independent fixed candidate/source identity')
        tokens=torch.load(bound(result['tokens']),map_location='cpu',weights_only=True);mh,mw=result['merged_grid']
        actual=np.load(bound(result['features']),allow_pickle=False)
        expected=candidate_features(tokens.float().numpy().reshape(mh,mw,4096),boxes,row['width'],row['height'])
        require(np.array_equal(actual,expected),'Independent raw merged-token ROI pooling differs')
        seen.add(row['item_id'])
    require(len(seen)==20 and not torch.cuda.is_initialized(),'Complete first independent confirm outputs')
    save(root/'roi_confirm_output_acceptance_10.json',dict(status='PASS_ALL_FIRST20_BASE_AND_ROI_OUTPUT_QA_NOT_QUALITY',
         completion=ref(out/'completion.json'),actual_sources=20,new_model_calls=0,original_GT_read=False))


def evaluate(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only CPU reference comparison')
    reg=config(root);qa=read(root/'roi_confirm_output_acceptance_10.json')
    require(qa['status']=='PASS_ALL_FIRST20_BASE_AND_ROI_OUTPUT_QA_NOT_QUALITY','Actual complete confirm QA first')
    import numpy as np
    labels={x['item_id']:x for x in read(bound(reg['original_labels']))}
    with np.load(bound(reg['frozen_predictor']['projection']),allow_pickle=False) as f:state={k:f[k] for k in f.files}
    beta={arm:np.load(bound(reg['frozen_predictor'][arm]),allow_pickle=False) for arm in ARMS}
    output={arm:[] for arm in ARMS};done=read(bound(qa['completion']))
    for reference in done['entries']:
        result=read(bound(reference));row=read(bound(result['source']));baseline=read(bound(result['original_BASE']));human=labels[row['item_id']]
        require(human['role']=='confirm' and human['source_sha256']==row['source_sha256'],'Original confirm human/source scope')
        truth=human['reference_xywh'];geom.validate_reference(truth,row['width'],row['height'])
        require(geom.reference_from_normalized(human['original_normalized_xyxy'],row['width'],row['height'])==truth,'Unmodified float human reference')
        features=np.load(bound(result['features']),allow_pickle=False);boxes=baseline['candidate_boxes'];ious=[geom.crop_iou(b,truth) for b in boxes]
        for arm in ARMS:
            score=predict(state,beta[arm],features,arm);j=choose(score)
            output[arm].append(dict(item_id=row['item_id'],source_sha256=row['source_sha256'],candidate_boxes=boxes,
                 predicted_relative_IoU=score.tolist(),chosen_index=j,baseline_iou=ious[0],selected_iou=ious[j],
                 delta_iou=ious[j]-ious[0],real_box_changed=(boxes[j]!=boxes[0]),original_human_reference_xywh=truth))
    summary={}
    for arm,rows in output.items():
        summary[arm]=dict(mean_baseline_iou=float(np.mean([x['baseline_iou'] for x in rows])),
             mean_selected_iou=float(np.mean([x['selected_iou'] for x in rows])),mean_delta_iou=float(np.mean([x['delta_iou'] for x in rows])),
             changed_sources=sum(x['real_box_changed'] for x in rows),improved_sources=sum(x['delta_iou']>0 for x in rows),
             degraded_sources=sum(x['delta_iou']<0 for x in rows),worst_source_delta=min(x['delta_iou'] for x in rows))
    save(root/'roi_confirm_result_10.json',dict(status='COMPLETE_FIRST_FROZEN_RELATIVE_ROI_CONFIRM_RESEARCH',
         summary=summary,sources=output,historical_exposure=True,new_blind_sources=0,original_GT_changed=False,
         new_fitting=False,automatic_426=False,production_admitted=False,scope='File-level static native16 research; video/joint quality UNKNOWN'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','input_qa','infer','output_qa','evaluate'])
    p.add_argument('--root',type=Path,required=True);a=p.parse_args();globals()[a.mode](a.root)
