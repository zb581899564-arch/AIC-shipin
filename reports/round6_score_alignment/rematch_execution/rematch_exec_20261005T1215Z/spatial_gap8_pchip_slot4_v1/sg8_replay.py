"""One post-generation independent CPU replay per new probe, no model call."""
import argparse
import hashlib
import json
import sys
import traceback

from sg8_common import HERE,OLD,read,sha,digest,save,require,utc,old_helpers,inputs


def binding(tensor):
    import torch
    t=tensor.detach().cpu().contiguous()
    return dict(shape=list(t.shape),dtype=str(t.dtype),sha256=hashlib.sha256(t.view(torch.uint8).numpy().tobytes()).hexdigest())


def replay(request_sha):
    folder=HERE/'diagnostic_01/new'/request_sha
    require(not (folder/'cpu_replay.json').exists(),'successful replay must not be repeated')
    raw=read(folder/'raw.json');receipt=read(HERE/'input_01/observations'/request_sha/'input.json')
    request=receipt['request']
    require(raw['request_sha256']==request_sha and raw['input_receipt_sha256']==sha(HERE/'input_01/observations'/request_sha/'input.json'),
        'actual generation input binding differs')
    common,_,production=old_helpers();config,manifest,clocks=inputs('nontest')
    m=next(r for r in manifest['records'] if r['video_id']==request['video_id'])
    import cv2
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from qwen_vl_utils import process_vision_info
    require(sha(m['source_path'])==m['source_sha256'],'native source changed')
    reader=production.OrdinalReader(m,clocks[m['video_id']])
    try:frame,pixel=reader.get(request['source_frame'])
    finally:reader.close()
    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    require(pixel==request['expected_pixel_sha256']==receipt['native_bgr_sha256'] and
        hashlib.sha256(rgb.tobytes()).hexdigest()==receipt['native_rgb_sha256'],'independent actual native pixels differ')
    prepared=HERE/'input_01/observations'/request_sha
    require(sha(prepared/'native.png')==receipt['native_png_sha256'] and
        Image.open(prepared/'native.png').tobytes()==rgb.tobytes(),'lossless PNG and actual native RGB differ')
    baseline=common.load(OLD/'spatial_baseline.py','sg8_replay_original_spatial')
    shell=object.__new__(baseline.Qwen3VL);shell.max_pixels=baseline.DEFAULT_MAX_PIXELS
    shell._generate=lambda messages,max_new_tokens:(messages,max_new_tokens)
    messages,max_new=shell.predict_focus(Image.fromarray(rgb),tuple(request['target_ratio_wh']),
        max_new_tokens=baseline.DEFAULT_CROP_TOKENS)
    processor=AutoProcessor.from_pretrained(config['model_dir'],local_files_only=True,
        min_pixels=baseline.DEFAULT_MAX_PIXELS,max_pixels=baseline.DEFAULT_MAX_PIXELS)
    try:text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    except (TypeError,ValueError):text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    images,videos,kwargs=process_vision_info(messages,return_video_kwargs=True,return_video_metadata=True,image_patch_size=16)
    model_inputs=processor(text=[text],images=images,videos=videos,padding=True,return_tensors='pt',**kwargs)
    tensors={k:binding(v) for k,v in model_inputs.items()}
    require(text==receipt['prefix'] and tensors==receipt['input_tensors']==raw['actual_input_tensors'] and
        int(model_inputs['input_ids'].shape[-1])==receipt['input_tokens']==raw['input_tokens'] and
        max_new==raw['max_new_tokens']==128,'independent actual processor/prefix/input tensors differ')
    decoded=processor.batch_decode([raw['output_token_ids']],skip_special_tokens=True,clean_up_tokenization_spaces=False)[0]
    require(decoded==raw['raw_output'],'independent output-token decode differs from immutable raw')
    parser=sys.modules['contracts'].parse_focus_norm
    center=parser(decoded,m['width'],m['height']);require(center is not None,'original strict parser rejects new raw')
    cw,ch=baseline.compute_crop_size(m['width'],m['height'],*m['targetRatioWH'])
    box=baseline.center_to_box(*center,m['width'],m['height'],cw,ch)
    result=dict(status='PASS_REAL_NATIVE_SPACE_PROBE_AND_INDEPENDENT_CPU_REPLAY',utc=utc(),
        request_sha256=request_sha,raw_sha256=sha(folder/'raw.json'),input_receipt_sha256=sha(prepared/'input.json'),
        model_receipt_sha256=raw['model_receipt_sha256'],native_bgr_sha256=pixel,native_rgb_sha256=receipt['native_rgb_sha256'],
        actual_native_pts=str(clocks[m['video_id']]['pts'][request['source_frame']]),input_tokens=receipt['input_tokens'],
        prefix_sha256=hashlib.sha256(text.encode()).hexdigest(),input_tensors=tensors,
        center_norm=center,box_xyw=box,raw_output_sha256=hashlib.sha256(decoded.encode()).hexdigest(),
        new_model_calls=0,new_optimizer_updates=0,full_source_decode_claim=False)
    save(folder/'cpu_replay.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('request_sha256');a=p.parse_args()
    try:replay(a.request_sha256)
    except Exception:
        save(HERE/'diagnostic_01'/('replay_failure_'+a.request_sha256+'.json'),dict(utc=utc(),traceback=traceback.format_exc()))
        raise
