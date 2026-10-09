"""First real answer replay in a separate CPU-only process and processor."""
import sys
import bw_common as c
from bw_engine import replay
def main(scope,video_id,index):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers();_,jobs=c.jobs_for(scope)
    job=next(j for j in jobs if j['video_id']==video_id);ix=int(index)
    from transformers import AutoProcessor
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    path=c.done_path(scope,job,ix,'BW',cc)
    proof=replay(path,job,ix,ex,rt,student,processor)
    import torch
    c.require(not torch.cuda.is_initialized(),'independent CPU replay initialized CUDA')
    c.save(c.HERE/'first_real_acceptance.json',dict(proof,status='PASS_REAL_FIRST_BALANCED_WINDOW_AND_INDEPENDENT_CPU_REPLAY',
        utc=c.utc(),pid=__import__('os').getpid(),separate_CPU_process=True,CUDA_initialized=False))
    print('PASS_REAL_FIRST_BALANCED_WINDOW_AND_INDEPENDENT_CPU_REPLAY',flush=True)
if __name__=='__main__':main(*sys.argv[1:])
