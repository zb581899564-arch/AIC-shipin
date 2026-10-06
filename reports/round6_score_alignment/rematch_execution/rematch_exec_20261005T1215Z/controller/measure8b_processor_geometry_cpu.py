import importlib.util,json,sys
from pathlib import Path
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
a=json.loads((RUN/'temporal_sft8b_dev_v1/admission.json').read_text())
import torch,numpy as np
from transformers import AutoProcessor
s=importlib.util.spec_from_file_location('tc',RUN/'baseline_a_pts_v1/vendor/temporal_common.py');tc=importlib.util.module_from_spec(s);s.loader.exec_module(tc)
p=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
prompt=p.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
cases=[]
for h,w in [(360,640),(720,1280),(1080,1920),(1920,1080)]:
    frames=torch.zeros((64,3,h,w),dtype=torch.uint8)
    e=p(text=[prompt],videos=[frames],video_metadata=[dict(fps=30,frames_indices=list(range(0,900,14))[:64],total_num_frames=900,video_backend='decord')],padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
    cases.append(dict(h=h,w=w,frames=64,tokens=int(e['input_ids'].shape[1]),grid=e['video_grid_thw'].tolist()))
    del e,frames
result=dict(status='MEASURED_SYNTHETIC_GEOMETRY_NO_CONTEST_MEDIA',cases=cases,context_limit=json.loads((Path(a['model_dir'])/'config.json').read_text())['text_config']['max_position_embeddings'],processor_size=p.video_processor.size,GPU_used=False,model_loaded=False)
(RUN/'controller/b8b_geometry_cpu_01.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
