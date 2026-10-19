"""One new external-only spatial ROI readout; no old decode or model replay.

Inference receives source-bound pixels/grid and GT-free candidate geometry.
Human references remain in a separate CPU-only target file.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

import crop_geometry as geom
from roi_pool import candidate_features

WORK = Path('/home/inspur/aic_video_work')
A = WORK/'gnmc_width_iteration_20261013_v1'
D = WORK/'sprint45_spatial_width602_20261016_v1'
PYTHON = WORK/'env/qwen3vl_isolated_20260910/bin/python'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    p = Path(path).resolve()
    require(p.is_file() and p.is_relative_to(WORK), 'Missing/out-of-project evidence')
    return dict(path=str(p), sha256=sha(p))


def bound(value):
    p = Path(value['path']).resolve()
    require(p.is_file() and p.is_relative_to(WORK) and sha(p) == value['sha256'], 'Frozen reference changed: '+str(p))
    return p


def save(path, value):
    path = Path(path)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def io_module(root):
    sys.path.insert(0, str(root/'branch_code_03'))
    from branch_pilot import original_io
    return original_io()


def registration(root):
    r = read(root/'roi_registration_06.json')
    require(r['source_scope'] == 'GNMC_STUDENT_NONCOMMERCIAL_RESEARCH_EXTERNAL_ONLY'
            and r['new_8B_updates'] == 0 and r['train_sources'] == 482 and r['dev_sources'] == 120,
            'Explicit new spatial research scope')
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(r['deadline_utc'].replace('Z','+00:00')),
            'Registered deadline reached')
    for name, digest in r['runtime_code'].items():
        require(sha(root/'roi_code_06'/name) == digest, 'New frozen ROI code changed: '+name)
    old = read(bound(r['original_runtime_binding']))
    for path, digest in old['files'].items():
        require(sha(path) == digest, 'Original runtime dependency changed')
    for path,digest in r['implementation_files'].items():
        require(sha(path)==digest,'Pinned patch/processor implementation changed')
    return r


def check_pixels(encoded):
    import torch
    require(set(encoded) == {'pixel_values', 'image_grid_thw'}, 'Vision-only two-key input expected')
    pixels, grid = encoded['pixel_values'], encoded['image_grid_thw']
    require(pixels.device.type == grid.device.type == 'cpu' and grid.shape == (1,3), 'One actual CPU image')
    t, h, w = map(int, grid[0].tolist())
    require(t == 1 and h > 0 and w > 0 and h%2 == w%2 == 0
            and list(pixels.shape) == [h*w,1536] and torch.isfinite(pixels).all(),
            'Actual patch16 temporal2 merge2 image grid/finite pixel payload')
    return h//2, w//2


def prepare(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU preparation must hide own CUDA only')
    reg = registration(root)
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    io = io_module(root); runtime = io.runtime_only()
    out = root/'roi_inputs_06'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), pid=os.getpid(), registration=ref(root/'roi_registration_06.json')))
    manifest = read(bound(reg['original_train_manifest']))
    old_acceptance = read(bound(reg['original_train_acceptance']))
    diagnostic = read(bound(reg['geometry_diagnostic']))
    split = geom.source_split(manifest)
    require(len(manifest) == len(old_acceptance['sources']) == 602, 'Exact historical author-train602')
    screen = {x['item_id']: x for x in diagnostic['screen20']['sources']}
    old_eval = read(bound(reg['original_eval_inputs']))
    labels = {x['item_id']:x for x in read(bound(reg['original_eval_labels']))}
    processor = AutoProcessor.from_pretrained(io.read(io.CONFIG)['model_dir'], local_files_only=True,
                                             min_pixels=65536, max_pixels=65536)
    import inspect
    require(str(Path(inspect.getfile(processor.image_processor.__class__)).resolve())==reg['image_processor_implementation'],
            'Actual processor class differs from independently reviewed implementation')
    entries, targets = [], []
    for i, (item, proof) in enumerate(zip(manifest, old_acceptance['sources'])):
        require(proof['sample_id'] == 'I%04d'%i and item['id'] == proof['id']
                and item['source_sha256'] == proof['source_sha256'] and proof['labels_in_input'] is False,
                'Original source/input binding changed')
        require(read(D/'inputs'/proof['sample_id']/'proof.json') == proof, 'Original accepted proof changed')
        require(sha(proof['tensor_path']) == proof['tensor_sha256'], 'Original accepted tensor changed')
        encoded = torch.load(proof['tensor_path'], map_location='cpu', weights_only=True)
        require(runtime.tensor_signature(encoded) == proof['tensors'], 'Adopted original tensor signature')
        vision = {k:encoded[k] for k in ('pixel_values','image_grid_thw')}
        check_pixels(vision)
        width, height = proof['width'], proof['height']
        boxes = geom.candidate_pool(width, height, geom.place_crop(width,height,(.5,.5)))
        human = geom.reference_from_normalized(item['reference_original_xyxy'],width,height)
        row = dict(item_id=item['id'], source_sha256=item['source_sha256'], role=split[item['id']],
                   width=width,height=height, candidate_boxes=boxes, input=ref(proof['tensor_path']),
                   original_proof=ref(D/'inputs'/proof['sample_id']/'proof.json'),
                   input_signature=runtime.tensor_signature(vision), adopted_old_input=True,
                   baseline_is_observed_model=False, reference_available_to_inference=False)
        p = out/('train_%04d.json'%i);save(p,row);entries.append(ref(p))
        targets.append(dict(item_id=row['item_id'],source_sha256=row['source_sha256'],role=row['role'],
                            original_reference_xywh=human, candidate_ious=[geom.crop_iou(b,human) for b in boxes]))
        del encoded,vision
    for item in old_eval:
        if item['role'] != 'screen':
            continue
        key=item['item_id']; old=screen[key]; proof=read(A/item['proof'])
        rgb_path=A/'rgb'/(item['key']+'.npy')
        rgb=np.load(rgb_path,allow_pickle=False)
        require(rgb.shape==(item['height'],item['width'],3) and rgb.dtype==np.uint8
                and hashlib.sha256(rgb.tobytes()).hexdigest()==proof['RGB_sha256']==item['rgb_sha256']
                and proof['source_sha256']==item['source_sha256'], 'Original screen RGB/source identity')
        encoded=dict(processor.image_processor(images=[Image.fromarray(rgb)],return_tensors='pt'))
        require(set(encoded)=={'pixel_values','image_grid_thw'},'First new65536 image processor output')
        check_pixels(encoded)
        p=out/(item['key']+'.pt');torch.save(encoded,p)
        row=dict(item_id=key,source_sha256=item['source_sha256'],role='screen',width=item['width'],height=item['height'],
                 candidate_boxes=old['candidate_boxes'],input=ref(p), original_proof=ref(A/item['proof']),
                 original_RGB=ref(rgb_path),input_signature=runtime.tensor_signature(encoded),adopted_old_input=False,
                 baseline_is_observed_model=True,reference_available_to_inference=False,
                 new_image_processor_pixels=65536,original131072_input_repeated=False,new_JPEG_decode=False)
        q=out/(item['key']+'.json');save(q,row);entries.append(ref(q))
        human=labels[key]['reference_xywh']
        require(human==old['original_float_reference_xywh'],'Unaltered original screen reference')
        targets.append(dict(item_id=key,source_sha256=item['source_sha256'],role='screen',
                            original_reference_xywh=human,candidate_ious=[geom.crop_iou(b,human) for b in row['candidate_boxes']]))
    require(len(entries)==622 and len({read(bound(e))['item_id'] for e in entries})==622,'Unique602+20 inputs')
    save(out/'CPU_targets.json',dict(status='CPU_ONLY_HUMAN_REFERENCE_NEVER_GPU_INPUT',sources=targets,
         historical_exposure=True,global_source_independence='UNKNOWN',new_blind_sources=0))
    save(out/'prepared.json',dict(status='PREPARED_NOT_GPU_ADMISSION',entries=entries,adopted_old_tensors=602,
         new_processor_calls=20,new_decode_calls=0,train=482,dev=120,screen=20,
         CPU_targets=ref(out/'CPU_targets.json'),original_train_acceptance=reg['original_train_acceptance']))
    require(not torch.cuda.is_initialized(),'CPU preparation initialized CUDA')


def input_qa(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'First input QA is CPU only')
    registration(root)
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    io=io_module(root);runtime=io.runtime_only()
    processor=AutoProcessor.from_pretrained(io.read(io.CONFIG)['model_dir'],local_files_only=True,
                                           min_pixels=65536,max_pixels=65536)
    out=root/'roi_inputs_06';ready=read(out/'prepared.json');seen=set();accepted=[]
    for reference in ready['entries']:
        row=read(bound(reference));require(row['reference_available_to_inference'] is False,'GT in GPU input')
        encoded=torch.load(bound(row['input']),map_location='cpu',weights_only=True)
        vision={k:encoded[k] for k in ('pixel_values','image_grid_thw')}
        mh,mw=check_pixels(vision)
        require(runtime.tensor_signature(vision)==row['input_signature'],'First new ROI input QA tensor mismatch')
        require(row['item_id'] not in seen and row['candidate_boxes']
                and len(set(map(tuple,row['candidate_boxes'])))==len(row['candidate_boxes'])
                and all(geom.legal(b,row['width'],row['height']) for b in row['candidate_boxes']),
                'Unique source/legal fixed candidate pool')
        if row['adopted_old_input']:
            proof=read(bound(row['original_proof']))
            require(proof['source_sha256']==row['source_sha256'] and proof['tensor_sha256']==row['input']['sha256'],
                    'Adopted successful original source/input binding')
        else:
            proof=read(bound(row['original_proof']));rgb=np.load(bound(row['original_RGB']),allow_pickle=False)
            require(hashlib.sha256(rgb.tobytes()).hexdigest()==proof['RGB_sha256']
                    and proof['source_sha256']==row['source_sha256'],'New65536 input inherited original RGB identity')
            # The first independent QA of these new20 inputs connects original
            # RGB to the actual processor pixels; self-signed cache hashes alone
            # cannot establish that connection. No old131072 or602 encoding.
            independent=dict(processor.image_processor(images=[Image.fromarray(rgb)],return_tensors='pt'))
            require(set(independent)==set(vision) and all(torch.equal(independent[k],vision[k]) for k in vision),
                    'First independent RGB-to65536 input QA pixel/grid mismatch')
        seen.add(row['item_id']);accepted.append(dict(entry=reference,merged_grid=[mh,mw],vision_signature=row['input_signature']))
        del encoded,vision
    require(len(seen)==622 and not torch.cuda.is_initialized(),'Complete actual CPU admission')
    # This source/input lock is frozen only after every actual new input was read.
    save(out/'source_lock.json',dict(registration=ref(root/'roi_registration_06.json'),prepared=ref(out/'prepared.json'),
         entries=accepted,source_scope='EXTERNAL_ONLY',human_targets_not_in_GPU=True,
         original_runtime_binding=read(root/'roi_registration_06.json')['original_runtime_binding']))
    save(out/'input_acceptance.json',dict(status='PASS_ALL622_FIRST_ROI_INPUT_QA',source_lock=ref(out/'source_lock.json'),
         actual_inputs=622,old_processor_calls_repeated=0,new65536_prepare_calls=20,
         first_independent65536_QA_calls=20,new_decode=0,CUDA_initialized=False))


def rows_for_stage(root,stage):
    gate=read(root/'roi_inputs_06/input_acceptance.json')
    require(gate['status']=='PASS_ALL622_FIRST_ROI_INPUT_QA','Complete actual input gate before model')
    lock=read(bound(gate['source_lock']));rows=lock['entries']
    require(len(rows)==622,'Complete source lock')
    if stage=='pilot32':
        return rows[:32]
    require(stage=='remaining590' and (root/'roi_pilot32_06/output_acceptance.json').is_file()
            and (root/'roi_remaining_admission_07.json').is_file(),'First32 actual mapping/cost acceptance before remaining590')
    return rows[32:]


def infer(root,stage):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'GPU parent needs actual nonempty CUDA index')
    registration(root)
    io=io_module(root);runtime=io.runtime_only()
    sys.path.insert(0,str(io.RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import numpy as np
    import torch
    torch.set_num_threads(2)
    rows=rows_for_stage(root,stage);out=root/('roi_'+stage+'_06');out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(pid=os.getpid(),utc=utc(),inputs=len(rows),purpose='FIRST_NEW_SPATIAL_PATCH_ROI_READOUT'))
    config=io.read(io.CONFIG);model,processor,identity=runtime.b_engine.load_model(config);io.verify_model(model,identity)
    require(sum(p.numel() for p in model.parameters())==8782459120,'Actual original B/TIME parameter inventory')
    core=model.get_base_model().model
    vc=core.visual.config
    require(vc.spatial_merge_size==2 and vc.patch_size==16 and vc.temporal_patch_size==2,'Actual pinned visual architecture')
    save(out/'model_identity.json',dict(identity=identity,adapter_disable_flags=io.enabled_layers(model),
         patch_size=vc.patch_size,merge_size=vc.spatial_merge_size,temporal_patch_size=vc.temporal_patch_size,
         output_order='T1_MERGED_ROW_MAJOR_FROM_PINNED_PROCESSOR_AND_MERGER',ROI_contains_global_attention=True))
    attempts=out/'attempts.jsonl';attempts.touch(exist_ok=False);success=[]
    def event(value):
        with attempts.open('a') as s:
            s.write(json.dumps(dict(utc=utc(),**value))+'\n');s.flush();os.fsync(s.fileno())
    try:
        for idx,source in enumerate(rows):
            row=read(bound(source['entry']));encoded=torch.load(bound(row['input']),map_location='cpu',weights_only=True)
            vision={k:encoded[k] for k in ('pixel_values','image_grid_thw')};mh,mw=check_pixels(vision)
            require(runtime.tensor_signature(vision)==source['vision_signature'],'Actual frozen input before first call')
            gpu={k:v.to('cuda') for k,v in vision.items()};t0=time.monotonic()
            event(dict(event='BEGIN_NEW_VISION_ONLY_ROI',item_id=row['item_id']))
            with torch.inference_mode():
                embeds,deep=core.get_image_features(**gpu)
            torch.cuda.synchronize()
            require(isinstance(embeds,tuple) and len(embeds)==1 and list(embeds[0].shape)==[mh*mw,4096]
                    and torch.isfinite(embeds[0]).all(),'Actual per-image merged token mapping/finite width4096')
            tokens=embeds[0].detach().cpu().contiguous();grid=tokens.float().numpy().reshape(mh,mw,4096)
            features=candidate_features(grid,row['candidate_boxes'],row['width'],row['height'])
            require(features.shape==(len(row['candidate_boxes']),12296) and np.isfinite(features).all(),'Actual fixed ROI feature shape')
            name='F%04d'%idx;tp=out/(name+'.tokens.pt');fp=out/(name+'.features.npy')
            torch.save(tokens,tp)
            with fp.open('xb') as s:np.save(s,features,allow_pickle=False)
            result=dict(status='ACCEPTED_FIRST_NEW_VISION_ROI_NOT_QUALITY',item_id=row['item_id'],source=source['entry'],
                 source_sha256=row['source_sha256'],role=row['role'],tokens=ref(tp),features=ref(fp),
                 merged_grid=[mh,mw],feature_shape=list(features.shape),new_forward=True,generation_calls=0,
                 optimizer_updates=0,labels_read=False,elapsed_seconds=time.monotonic()-t0)
            rp=out/(name+'.json');save(rp,result);success.append(ref(rp))
            event(dict(event='ACCEPTED_NEW_VISION_ONLY_ROI',item_id=row['item_id'],result=ref(rp)))
            print(json.dumps(dict(stage=stage,accepted=len(success),expected=len(rows))),flush=True)
            del encoded,vision,gpu,embeds,deep,tokens,grid,features
        require(io.enabled_layers(model)==[False]*144 and runtime.b_engine.frozen_identity(model,config)==identity['base']
                and runtime.b_engine.adapter_identity(model,config)==identity['adapter'],'Frozen full model changed')
        save(out/'completion.json',dict(status='PASS_ALL_FIRST_VISION_ROI_READOUTS_NOT_QUALITY',entries=success,
             actual_new_forwards=len(success),generation_calls=0,optimizer_updates=0,labels_read=False,
             actual_loaded_model_parameters=8782459120,model_identity=ref(out/'model_identity.json')))
    except BaseException as e:
        save(out/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),successful=success,
             preserve_all_success=True,do_not_repeat_success=True,failure_is_not_empty=True));raise


def output_qa(root,stage):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent first output QA CPU only')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    out=root/('roi_'+stage+'_06');done=read(out/'completion.json');seen=set();accepted=[]
    for reference in done['entries']:
        result=read(bound(reference));row=read(bound(result['source']))
        tokens=torch.load(bound(result['tokens']),map_location='cpu',weights_only=True)
        mh,mw=result['merged_grid'];require(tokens.shape==(mh*mw,4096) and torch.isfinite(tokens).all(),'Actual raw merged token shape')
        features=np.load(bound(result['features']),allow_pickle=False)
        expected=candidate_features(tokens.float().numpy().reshape(mh,mw,4096),row['candidate_boxes'],row['width'],row['height'])
        require(features.dtype==np.float32 and np.array_equal(features,expected),'Independent raw-token ROI recompute mismatch')
        require(row['source_sha256']==result['source_sha256'] and row['item_id'] not in seen,'Unique first output source binding')
        seen.add(row['item_id']);accepted.append(reference)
    require(len(seen)==done['actual_new_forwards']==(32 if stage=='pilot32' else 590),'All first outputs independently checked')
    save(out/'output_acceptance.json',dict(status='PASS_ALL_FIRST_INDEPENDENT_ROI_OUTPUT_QA_NOT_QUALITY',
         entries=accepted,completion=ref(out/'completion.json'),sources=len(seen),new_model_calls=0,
         raw_merged_tokens_recomputed_CPU=True,GT_used=False,CUDA_initialized=torch.cuda.is_initialized()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','input_qa','infer','output_qa'])
    p.add_argument('--root',type=Path,required=True);p.add_argument('--stage',choices=['pilot32','remaining590'])
    a=p.parse_args()
    if a.mode in ('prepare','input_qa'):globals()[a.mode](a.root)
    else:globals()[a.mode](a.root,a.stage)
