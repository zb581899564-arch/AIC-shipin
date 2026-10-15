"""Export actual CPU processor tensor views; no weights, predictions or labels."""
from pathlib import Path
import json, hashlib, importlib.util, sys, time, gc, traceback
HERE = Path(__file__).resolve().parent / 'slot6_silver24_v1'
RUN = HERE.parents[1] / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
sys.path[:0] = [str(RUN/'teacher_student_autopilot_v14'), str(RUN/'baseline_a_pts_v1'), str(RUN/'baseline_a_pts_v1/vendor')]

def sha(p):
    with Path(p).open('rb') as f:
        h=hashlib.sha256()
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)

def load(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

started=time.monotonic()
try:
    import numpy as np, torch, transformers, psutil
    from PIL import Image
    from transformers import AutoProcessor
    assert transformers.__version__=='4.57.1'
    binding=json.loads((HERE/'actual_processor_binding.json').read_text())
    for r in binding['rows']:assert sha(HERE/'actual_processor_snapshot'/r['file'])==r['sha256']
    rt=load(RUN/'context_advisory_v1/runtime.py','slot6_actual_runtime')
    student, common, fc, production=rt.bind_helpers()
    from contracts import EMPTY_PROMPT
    processor=AutoProcessor.from_pretrained(HERE/'actual_processor_snapshot',local_files_only=True)
    jobs=json.loads((HERE/'observations/jobs.json').read_text())['first_four']
    rows=[]
    for folder in map(Path,jobs):
        out=folder/'student_views';out.mkdir(exist_ok=False)
        m=json.loads((folder/'manifest.json').read_text());w=m['original_window']
        decoded=student.decode_window(w)
        assert decoded[3]['frame_pixel_sha256']==[r['rgb_pixel_sha256'] for r in m['frames']]
        encoded,evidence=rt.encode_decoded(processor,decoded,EMPTY_PROMPT)
        del decoded;gc.collect()
        pixels=encoded['pixel_values_videos'];grid=encoded['video_grid_thw'].tolist()
        assert len(grid)==1
        gt,gh,gw=grid[0];vp=processor.video_processor
        p,ms,tp=vp.patch_size,vp.merge_size,vp.temporal_patch_size
        assert gt*tp==len(m['frames'])==64 and pixels.ndim==2
        assert list(pixels.shape)==[gt*gh*gw,3*tp*p*p]
        tensor_sha=hashlib.sha256(memoryview(pixels.detach().cpu().numpy()).cast('B')).hexdigest()
        mean=torch.tensor(vp.image_mean).view(3,1,1);std=torch.tensor(vp.image_std).view(3,1,1)
        frames=[]
        # Inverse of upstream permute(0,1,4,7,5,8,3,2,6,9), one temporal group at a time.
        for t in range(gt):
            block=pixels[t*gh*gw:(t+1)*gh*gw]
            patch=block.reshape(gh//ms,gw//ms,ms,ms,3,tp,p,p)
            view=patch.permute(5,4,0,2,6,1,3,7).reshape(tp,3,gh*p,gw*p)
            rebuilt=view.reshape(tp,3,gh//ms,ms,p,gw//ms,ms,p).permute(2,5,3,6,1,0,4,7).reshape(gh*gw,3*tp*p*p)
            assert torch.equal(block,rebuilt), 'Patch reconstruction is not exactly invertible'
            for j in range(tp):
                i=t*tp+j
                rgb=((view[j]*std+mean)/vp.rescale_factor).round().clamp(0,255).to(torch.uint8).permute(1,2,0).numpy()
                path=out/f'F{i:02d}_student.png';Image.fromarray(rgb).save(path)
                frames.append(dict(frame_id=m['frames'][i]['frame_id'],source_ordinal=m['frames'][i]['source_ordinal'],
                    global_seconds_exact=m['frames'][i]['global_seconds_exact'],local_seconds_exact=m['frames'][i]['local_seconds_exact'],
                    path=str(path),png_sha256=sha(path),rgb_pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
            del patch,view,rebuilt
        receipt=dict(status='PASS_ACTUAL_LOCAL_CPU_NATIVE_PROCESSOR_TENSOR_VIEWS',window_id=m['window_id'],
            manifest_sha256=sha(folder/'manifest.json'),processor_binding_sha256=sha(HERE/'actual_processor_binding.json'),
            runtime_sha256=sha(RUN/'context_advisory_v1/runtime.py'),decoder_sha256=sha(RUN/'teacher_student_autopilot_v14/train_student.py'),
            evidence=evidence,video_grid_thw=grid,actual_tensor_shape=list(pixels.shape),normalized_tensor_sha256=tensor_sha,
            student_width=gw*p,student_height=gh*p,patch_inverse_exact=True,
            rendered_view='Inverse patch rearrangement, inverse normalization, rounded uint8 PNG. Display reconstruction; normalized model tensor SHA bound separately.',
            frames=frames,input_tokens=int(encoded['input_ids'].shape[1]),linux_execution=False,
            torch_version=torch.__version__,transformers_version=transformers.__version__,cuda_initialized=torch.cuda.is_initialized(),
            memory=psutil.Process().memory_info()._asdict(),new_model_calls=0,new_optimizer_updates=0,training_admitted=False)
        save(out/'receipt.json',receipt)
        rows.append(dict(window_id=w['window_id'],receipt=str(out/'receipt.json'),sha256=sha(out/'receipt.json'),
            width=gw*p,height=gh*p,input_tokens=receipt['input_tokens']))
        print(json.dumps(rows[-1]),flush=True)
        del pixels,encoded,evidence;gc.collect()
    save(HERE/'student_views_cpu_receipt.json',dict(status='PASS_FOUR_ACTUAL_CPU_STUDENT_VIEW_EXPORTS',rows=rows,
        seconds=time.monotonic()-started,linux_execution=False,new_model_calls=0,new_optimizer_updates=0))
except BaseException:
    save(HERE/'student_views_cpu_failure_01.json',dict(status='STOP_CPU_PREPARATION',traceback=traceback.format_exc(),
        seconds=time.monotonic()-started,new_model_calls=0,new_optimizer_updates=0))
    raise
