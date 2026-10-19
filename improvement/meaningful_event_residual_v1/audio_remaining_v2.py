"""Explicit remaining-only recovery for missing VideoXum clock path field."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys,time
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path[:0]=[str(ROOT/'audio_code_v1'),str(ROOT/'code_v1')]
from audio_event import *


def remaining():
    cpu();start=time.monotonic();folder=OUT/'audio_inputs_01'
    require((ROOT/'audio_controller_failure.json').exists()and not(OUT/'input_completion.json').exists(),'Actual failed prepare, no completed remaining chain')
    recovery=read(ROOT/'audio_recovery_registration_02.json');reg=read(ROOT/'registration.json');sources=reg['sources'];lookup={s['sid']:s for s in sources};raw={s['sid']:s for s in read(SRC/'registration.json')['sources']}
    pilot=['S05','V00','S18'];ordered=[lookup[s]for s in pilot]+[s for s in sources if s['sid']not in pilot];receipts=[]
    for s in ordered:
        done=folder/(s['sid']+'.json')
        if done.exists():
            require(s['sid']in recovery['adopted_successes'],'Only explicitly adopted previous successful sources')
            row=read(done);bound(row['input_ref']);bound(row['manifest_ref'])
            require(row['audio_QA']['status']=='PASS_FIRST_AUDIO_NATIVE_DESCRIPTOR_QA','Adopt actual first successful QA, never rerun')
            receipts.append(ref(done));continue
        require(time.monotonic()-start<1800,'Remaining audio-specific extraction wall budget')
        d=load_source(s);c,_=adopted_input(s);clock=dict(d['clock'])
        if 'media'in raw[s['sid']]:media=bound(raw[s['sid']]['media'])
        else:media=Path(clock['source_path'])
        require(clock['source_sha256']==sha(media),'Registered known media path must match original native source SHA')
        size=media.stat().st_size
        require('source_bytes'not in clock or clock['source_bytes']==size,'Observed source byte count must match registered media')
        clock['source_bytes']=size
        save(folder/(s['sid']+'_augmented_clock.json'),dict(clock=clock,original_clock_ref=s['clock_ref'],resolved_registered_media_path=str(media),size_added_from_bound_current_media_stat=True,old_clock_unchanged=True,recovery_ref=ref(ROOT/'audio_recovery_registration_02.json')))
        cache=extract_audio(media,clock,folder/s['sid']);features=proposal_audio_features(cache,clock,d['baseline'],c['candidates']);qa=independent_audio_qa(cache,clock,d['baseline'],c['candidates'],features)
        np.savez(folder/(s['sid']+'_proposals.npz'),x=features)
        save(done,dict(sid=s['sid'],group=s['group'],input_ref=ref(folder/(s['sid']+'_proposals.npz')),manifest_ref=ref(folder/(s['sid']+'.manifest.json')),adopted_visual_ref=ref(ROOT/('train_inputs'if s['group']=='train'else'diagnostic_inputs')/(s['sid']+'.json')),audio_QA=qa))
        receipts.append(ref(done));event('FIRST_AUDIO_DESCRIPTOR_QA',sid=s['sid'],**qa)
        if len(receipts)==3:save(OUT/'pilot3_completion.json',dict(status='PASS3_ACTUAL_AUDIO_EXTRACTION_FIRST_QA',sources=receipts.copy(),elapsed_remaining_seconds=time.monotonic()-start,adopted_sources=['S05'],remaining_sources=30,recovery_ref=ref(ROOT/'audio_recovery_registration_02.json'),utc=utc()))
    require(len(receipts)==33,'Full33 source audio-specific first input denominator')
    save(OUT/'input_completion.json',dict(status='PASS33_ALL_FIRST_AUDIO_NATIVE_INPUTS',sources=receipts,elapsed_remaining_seconds=time.monotonic()-start,adopted_successes=recovery['adopted_successes'],recovery_ref=ref(ROOT/'audio_recovery_registration_02.json'),new_video_decode=0,new_GPU=0,utc=utc()))


if __name__=='__main__':
    try:remaining()
    except BaseException as e:failure('event_audio_remaining_v2',e);raise
