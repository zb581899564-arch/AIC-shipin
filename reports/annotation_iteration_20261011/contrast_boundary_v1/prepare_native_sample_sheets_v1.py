"""Actual local CPU sourceRGB and processor views; no labels/model weights."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,hashlib,importlib.util,sys,time,gc,traceback
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
OLD=PROJECT/'reports/annotation_iteration_20261010/slot6_silver24_v1'
RUN=PROJECT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
sys.path[:0]=[str(RUN/'teacher_student_autopilot_v14'),str(RUN/'baseline_a_pts_v1'),str(RUN/'baseline_a_pts_v1/vendor')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,default=str)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser();p.add_argument('--indices',required=True);args=p.parse_args()
 indices=[int(x) for x in args.indices.split(',')];assert indices and len(indices)==len(set(indices))
 planpath=ROOT/'source_window_plan_v1.json';plan=read(planpath)
 import numpy as np,torch,transformers
 from PIL import Image,ImageDraw
 from transformers import AutoProcessor
 assert transformers.__version__=='4.57.1' and not torch.cuda.is_initialized()
 for row in read(OLD/'actual_processor_binding.json')['rows']:assert sha(OLD/'actual_processor_snapshot'/row['file'])==row['sha256']
 rt=load(RUN/'context_advisory_v1/runtime.py','contrast_actual_cpu_encoder');student,_,_,_=rt.bind_helpers()
 from contracts import EMPTY_PROMPT
 processor=AutoProcessor.from_pretrained(OLD/'actual_processor_snapshot',local_files_only=True)
 base=ROOT/'observations';base.mkdir(exist_ok=True);done=[]
 for index in indices:
  job=plan['jobs'][index];w=job['window'];out=base/f'{index:03d}';out.mkdir(exist_ok=False)
  try:
   started=time.monotonic();decoded=student.decode_window(w);arr=decoded[0]
   assert len(arr)==64 and decoded[3]['source_frame_ids']==w['planned_source_frame_ordinals']
   assert decoded[3]['actual_pts_sec']==w['planned_actual_pts_sec']
   native_dir=out/'native';native_dir.mkdir();frames=[]
   for i,rgb in enumerate(arr):
    point=w['planned_exact_pts'][i];path=native_dir/f'F{i:02d}.png';Image.fromarray(rgb).save(path)
    assert sha(path) and hashlib.sha256(Image.open(path).tobytes()).hexdigest()==decoded[3]['frame_pixel_sha256'][i]
    frames.append({'frame_id':f'F{i:02d}','ordinal':w['planned_source_frame_ordinals'][i],
       'pts_exact':point,'local_seconds_exact':str(F(point)-F(w['domain_start_exact'])),
       'width':w['width'],'height':w['height'],'pixel_sha256':decoded[3]['frame_pixel_sha256'][i],
       'png':{'path':str(path),'sha256':sha(path)}})
   def sheets(rows,directory,prefix):
    directory.mkdir(exist_ok=False);result=[]
    for batch in range(8):
     subset=rows[batch*8:batch*8+8];images=[Image.open(r['png']['path']).convert('RGB') for r in subset]
     width,height=images[0].size;assert all(im.size==(width,height) for im in images)
     canvas=Image.new('RGB',(width*2,(height+26)*4),'white');draw=ImageDraw.Draw(canvas)
     for k,(im,row) in enumerate(zip(images,subset)):
      x=(k%2)*width;y=(k//2)*(height+26)
      canvas.paste(im,(x,y+26));draw.text((x+3,y+3),row['frame_id']+' O'+str(row['ordinal'])+' localPTS='+row['local_seconds_exact'],fill='black')
      assert hashlib.sha256(canvas.crop((x,y+26,x+width,y+26+height)).tobytes()).hexdigest()==hashlib.sha256(im.tobytes()).hexdigest()
     path=directory/f'{prefix}{batch:02d}.png';canvas.save(path)
     result.append({'index':batch,'frame_ordinals':[row['ordinal'] for row in subset],'frame_indices':list(range(batch*8,batch*8+8)),
        'scale_exact':'1','image':{'path':str(path),'sha256':sha(path)}})
    return result
   native_sheets=sheets(frames,out/'native_sheets','native_')
   manifest={'status':'PASS_ACTUAL_NATIVE64_SOURCE_RGB_UNSCALED_SHEETS','window_id':w['window_id'],'source_sha256':w['source_sha256'],
    'source_rgb_unscaled':True,'source_plan':{'path':str(planpath),'sha256':sha(planpath)},'frames':frames,'sheets':native_sheets,
    'native_source_pts_alignment':'Exact old frozen full-source native_pts byte binding; actual new decoded float PTS equal all planned float values, no newly introduced epsilon.',
    'domain_local_seconds_exact':['0',str(F(w['domain_end_exact'])-F(w['domain_start_exact']))],
    'full_native_frames_observed':False,'native_video_delivered':False,'original_window':w,'role':job['role'],'source_id':job['source_id']}
   save(out/'contact_sheet_manifest.json',manifest)
   encoded,evidence=rt.encode_decoded(processor,decoded,EMPTY_PROMPT);del decoded,arr;gc.collect()
   pixels=encoded['pixel_values_videos'];grid=encoded['video_grid_thw'].tolist();assert len(grid)==1
   gt,gh,gw=grid[0];vp=processor.video_processor;p,ms,tp=vp.patch_size,vp.merge_size,vp.temporal_patch_size
   assert gt*tp==64 and list(pixels.shape)==[gt*gh*gw,3*tp*p*p]
   tensor_sha=hashlib.sha256(memoryview(pixels.detach().cpu().numpy()).cast('B')).hexdigest()
   mean=torch.tensor(vp.image_mean).view(3,1,1);std=torch.tensor(vp.image_std).view(3,1,1)
   sd=out/'student';sd.mkdir();student_rows=[];sheet_rows=[]
   for t in range(gt):
    block=pixels[t*gh*gw:(t+1)*gh*gw];patch=block.reshape(gh//ms,gw//ms,ms,ms,3,tp,p,p)
    view=patch.permute(5,4,0,2,6,1,3,7).reshape(tp,3,gh*p,gw*p)
    rebuilt=view.reshape(tp,3,gh//ms,ms,p,gw//ms,ms,p).permute(2,5,3,6,1,0,4,7).reshape(gh*gw,3*tp*p*p)
    assert torch.equal(block,rebuilt)
    for j in range(tp):
     i=t*tp+j;rgb=((view[j]*std+mean)/vp.rescale_factor).round().clamp(0,255).to(torch.uint8).permute(1,2,0).numpy()
     path=sd/f'F{i:02d}_student.png';Image.fromarray(rgb).save(path);row=frames[i]
     student_rows.append({'frame_id':row['frame_id'],'source_ordinal':row['ordinal'],'global_seconds_exact':row['pts_exact'],
      'local_seconds_exact':row['local_seconds_exact'],'path':str(path),'png_sha256':sha(path),'rgb_pixel_sha256':hashlib.sha256(rgb.tobytes()).hexdigest()})
     sheet_rows.append({'frame_id':row['frame_id'],'ordinal':row['ordinal'],'local_seconds_exact':row['local_seconds_exact'],'png':{'path':str(path),'sha256':sha(path)}})
    del patch,view,rebuilt
   effective_sheets=sheets(sheet_rows,out/'student_sheets','student_')
   receipt={'status':'PASS_ACTUAL_LOCAL_CPU_NATIVE_PROCESSOR_TENSOR_VIEWS','window_id':w['window_id'],'source_sha256':w['source_sha256'],
    'contact_sheet_manifest_sha256':sha(out/'contact_sheet_manifest.json'),'processor_binding_sha256':sha(OLD/'actual_processor_binding.json'),
    'evidence':evidence,'video_grid_thw':grid,'actual_tensor_shape':list(pixels.shape),'normalized_tensor_sha256':tensor_sha,
    'student_width':gw*p,'student_height':gh*p,'patch_inverse_exact':True,'frames':student_rows,'sheets':effective_sheets,
    'input_tokens':int(encoded['input_ids'].shape[1]),'linux_execution':False,'cuda_initialized':torch.cuda.is_initialized(),
    'new_model_calls':0,'new_optimizer_updates':0,'wall_seconds':time.monotonic()-started}
   assert not receipt['cuda_initialized'] and evidence['frame_pixel_sha256']==[row['pixel_sha256'] for row in frames]
   save(out/'student_processor.json',receipt);done.append({'index':index,'manifest_sha256':sha(out/'contact_sheet_manifest.json'),'processor_sha256':sha(out/'student_processor.json')})
   print(json.dumps({'index':index,'window':w['window_id'],'status':'PASS_ACTUAL_CPU_NATIVE64_AND_PROCESSOR_SHEETS','input_tokens':receipt['input_tokens'],'wall_seconds':receipt['wall_seconds']}),flush=True)
   del pixels,encoded,evidence;gc.collect()
  except BaseException:
   save(out/'preparation_failure.json',{'status':'STOP_ACTUAL_CPU_PREPARATION','traceback':traceback.format_exc(),'old_success_outputs_preserved':True,'new_model_calls':0});raise
 index_digest=hashlib.sha256(json.dumps(indices,separators=(',',':')).encode('ascii')).hexdigest()[:16]
 save(ROOT/f'native_preparation_batch_{indices[0]}_{indices[-1]}_{index_digest}.json',{'status':'PASS_ACTUAL_CPU_NATIVE_AND_PROCESSOR_PREPARATION','indices':indices,'rows':done,'new_model_calls':0,'new_optimizer_updates':0})

if __name__=='__main__':main()
