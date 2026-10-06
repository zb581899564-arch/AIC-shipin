"""Reproduce/fix the path failure using two pinned dev inputs; no model loaded."""
from runtime import *
from lowres import decode_dev_av

def main():
    a=read(HERE/'admission.json');contract=read(HERE/'dev/input_contract.json')
    import torch
    import numpy as np
    from transformers import AutoProcessor
    from train_sft import verify_video_encoding
    tc=load(CODE/'vendor/temporal_common.py','mac_recovery_cpu_tc')
    p=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=p.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    results=[]
    for row in contract['records'][:2]:
        require(sha(row['source_path'])==row['source_sha256'],'pinned CPU media hash changed')
        arr,metadata,info=decode_dev_av(row,tc,np,None)
        encoded=lowres_encode(p,text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],
            video_metadata=[metadata],padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
        identity=verify_video_encoding(p,encoded,metadata,info)
        grid=encoded['video_grid_thw'][0].tolist();patch=p.video_processor.patch_size
        results.append(dict(sampled_frames=info['n_sampled'],tokens=int(encoded['input_ids'].shape[1]),
            actual_pixels_per_frame=int(grid[1]*grid[2]*patch*patch),video_identity=identity,passed=True))
    require(len(results)==2 and not torch.cuda.is_initialized(),'CPU preflight must not initialize GPU')
    write(HERE/'dev_input_cpu_01.json',dict(status='PASS_PINNED_DEV_PYAV_LOWRES_INPUTS',cases=2,records=results,
        input_contract_sha256=sha(HERE/'dev/input_contract.json'),model_loaded=False,model_generation_calls=0,contest_media_read=False))
    print('PASS 2/2 actual pinned dev PyAV/lowres inputs, zero generation calls')

if __name__=='__main__':main()
