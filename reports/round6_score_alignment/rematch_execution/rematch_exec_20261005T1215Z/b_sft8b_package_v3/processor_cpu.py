"""Actual pinned 8B processor with synthetic native timestamps; CPU only."""
from runtime import *

def main():
    a=read(RUN/'temporal_sft8b_dev_v1/admission.json')
    for name in ('config.json','tokenizer.json','preprocessor_config.json','video_preprocessor_config.json'):
        p=str(Path(a['model_dir'])/name);require(sha(p)==a['files'][p],'processor byte changed')
    import torch
    import numpy as np
    from transformers import AutoProcessor
    from exact_pts import exact_native_pts,verify_native_encoding
    from native_frames import prepare_native_processor_input
    tc=load(CODE/'vendor/temporal_common.py','synthetic8b_tc')
    processor=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=processor.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    original=processor._calculate_timestamps;result=[]
    for n in (1,3,63,64):
        ids=list(range(5,5+2*n,2));pts=[7.01+.04*i+(.4 if i>=max(1,n//2) else 0) for i in range(n)]
        plan=dict(source_frame_ids=ids,source_relative_pts=pts,window_start=7.0)
        frames=np.zeros((n,64,64,3),dtype=np.uint8)
        md=dict(fps=25.0,frames_indices=ids,total_num_frames=2*n+10,video_backend='decord')
        frames,md=prepare_native_processor_input(frames,md,plan)
        with exact_native_pts(processor,plan,25.0) as identity:
            encoded=processor(text=[prompt],videos=[torch.from_numpy(frames).permute(0,3,1,2)],video_metadata=[md],padding=True,do_sample_frames=False,return_tensors='pt')
            verify_native_encoding(processor,encoded,identity)
        require(processor._calculate_timestamps==original,'instance timestamp override leaked')
        require(identity['explicit_input_padding_copies']==int(n==1) and identity['implicit_processor_padding_copies']==int(n%2 and n>1),'single/odd temporal padding changed')
        result.append(dict(frames=n,pass_=True,identity=identity,tokens=int(encoded['input_ids'].shape[1])))
    write(HERE/'processor_cpu_01.json',dict(status='PASS_ACTUAL_8B_NATIVE_PROCESSOR',cases=4,records=result,
        model_dir=a['model_dir'],labels_read=False,contest_media_read=False,models_loaded=False,GPU_used=False,
        runtime_sha256=sha(HERE/'runtime.py'),test_sha256=sha(__file__)))
    print('PASS 4/4 actual 8B native processor synthetic CPU cases')

if __name__=='__main__':main()
