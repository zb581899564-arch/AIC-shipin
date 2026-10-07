"""Real installed processor equality, assistant empty target and strict-loader checks."""
from common import *
from video_contract import encode, identity
from training_target import build_target, target_text

def main():
    import torch
    from transformers import AutoProcessor
    from engine import prompt_for, encode_window
    from package_contract import package
    from tempfile import TemporaryDirectory
    import subprocess
    config=read(HERE/'config.json');out=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'cpu_01';out.mkdir()
    processor=AutoProcessor.from_pretrained(config['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    require(processor.video_processor.size==config['video_size'],'default video contract drift')
    cases=[]
    for physical in (1,63,64):
        n=max(2,physical)
        frames=torch.zeros((n,3,72,128),dtype=torch.uint8)
        md=dict(fps=30,frames_indices=([0,0] if physical==1 else list(range(n))),total_num_frames=64,video_backend='decord')
        prompt=prompt_for(processor,False)
        old=processor(text=[prompt],videos=[frames],video_metadata=[dict(md)],padding=True,do_sample_frames=False,return_tensors='pt')
        new=encode(processor,text=[prompt],videos=[frames],video_metadata=[dict(md)],video_size=config['video_size'])
        for key in ('input_ids','attention_mask','pixel_values_videos','video_grid_thw'):
            require(torch.equal(old[key],new[key]),'explicit video size changed actual input: '+key)
        cases.append(dict(physical_frames=physical,processor_frames=n,encoding_byte_equal=True,identity=identity(processor,new,n)))
    hd=torch.zeros((64,3,1080,1920),dtype=torch.uint8)
    md=dict(fps=30,frames_indices=[14*i for i in range(64)],total_num_frames=900,video_backend='decord')
    prompt=prompt_for(processor,False)
    old=processor(text=[prompt],videos=[hd],video_metadata=[dict(md)],padding=True,do_sample_frames=False,return_tensors='pt')
    new=encode(processor,text=[prompt],videos=[hd],video_metadata=[dict(md)],video_size=config['video_size'])
    for key in ('input_ids','attention_mask','pixel_values_videos','video_grid_thw'):
        require(torch.equal(old[key],new[key]),'HD input no longer matches original production')
    cases.append(dict(physical_frames=64,hd=True,encoding_byte_equal=True,identity=identity(processor,new,64)))
    del hd,old,new
    frames=torch.zeros((4,3,72,128),dtype=torch.uint8)
    md=dict(fps=2,frames_indices=[0,1,2,3],total_num_frames=4,video_backend='decord')
    label=dict(observation_complete=True,status='OBSERVED_EMPTY',segments=[])
    plan=dict(source_frame_ids=[0,1,2,3],source_relative_pts=[0,.4,1.1,1.5],window_start=0)
    _,target=build_target(processor,prompt_for(processor,True),frames,md,label,2,config['video_size'],native_plan=plan,source_fps=2)
    require(target['answer']=='{"segments":[]}' and target['assistant_tokens']>0,'empty CE target missing')
    try:target_text(dict(observation_complete=False,status='UNKNOWN',segments=[]),2)
    except ValueError:pass
    else:raise RuntimeError('UNKNOWN became negative label')
    # Real open developer media only; no teacher labels needed for this equality check.
    dev=read(config['open_dev_contract'])['records'][:2]
    for row in dev:
        item=dict(row,fps_num=row['source_avg_fps'],fps_den=1,n_frames=row['decoded_source_frames'])
        _,info=encode_window(processor,prompt_for(processor,False),item,None,row['clip_start_sec'],min(row['clip_end_sec'],row['clip_start_sec']+30),config)
        cases.append(dict(open_dev=True,video_id=row['video_id'],identity=info))
    empty=out/'empty426';empty.mkdir()
    metadata=[dict(video_id='fixture_%03d'%i,targetRatioWH=[16,9],width=160,height=90,n_frames=20) for i in range(426)]
    predictions=[dict(video_id=r['video_id'],targetRatioWH=r['targetRatioWH'],predictions=[]) for r in metadata]
    write(empty/'metadata.json',dict(records=metadata));write_rows(empty/'predictions.jsonl',predictions)
    write_rows(empty/'selected.jsonl',[]);write_rows(empty/'provenance.jsonl',[])
    package(empty/'predictions.jsonl',empty/'fixture.zip')
    subprocess.run([sys.executable,'-B',str(BASELINE/'vendor/independent_validate.py'),'--strict-loader-root',str(BASELINE/'vendor/frozen_strict_loader'),
        '--metadata',str(empty/'metadata.json'),'--selected',str(empty/'selected.jsonl'),'--predictions',str(empty/'predictions.jsonl'),
        '--provenance',str(empty/'provenance.jsonl'),'--zip',str(empty/'fixture.zip'),'--report',str(empty/'independent.json')],check=True)
    require(read(empty/'independent.json')['status']=='PASS_INDEPENDENT_STRICT_VALIDATION','historical independent loader rejects empty')
    write(out/'processor_acceptance.json',dict(status='PASS_REAL_PROCESSOR_AND_EMPTY_TARGET',cases=cases,empty_target=target,
        empty426_independent_strict=True,unknown_target_rejected=True,official_quality_claim=False,confirm_read=False,contest_media_read=False))
    print('PASS_REAL_PROCESSOR_AND_EMPTY_TARGET',flush=True)

if __name__=='__main__':main()
