"""Adopt25 successful audio sources; first remaining401 with header-only fix."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys,time
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path[:0]=[str(ROOT/'production_recovery_code_v2'),str(ROOT/'audio_code_v1'),str(ROOT/'code_v1')]
from event_runtime import *
from audio_event import independent_audio_qa
from audio_features_header_v2 import extract_audio,proposal_audio_features


def main():
    cpu();recovery=read(ROOT/'production_recovery_registration_02.json')
    require((ROOT/'production_controller_failure.json').exists(),'Actual initial production failed')
    folder=ROOT/'formal_audio_01';new=folder/'remaining_v2';new.mkdir();start=time.monotonic();receipts=[];summary=[]
    accepted=read(ROOT/'formal_inputs_01/completion.json');adopted=set(recovery['adopted_audio_sources'])
    for vref in accepted['sources']:
        row=read(bound(vref));sid=row['sid'];path=folder/(sid+'.json')
        if sid in adopted:
            done=read(path);bound(done['input_ref']);bound(done['manifest_ref'])
            require(done['visual_receipt_ref']==vref and done['clock_ref']==row['clock_ref'] and done['audio_QA']['status']=='PASS_FIRST_AUDIO_NATIVE_DESCRIPTOR_QA','Adopt exact successful source binding/firstQA, never repeat')
            receipts.append(ref(path));summary.append(dict(sid=sid,**done['audio_QA']));continue
        require(not path.exists(),'Unregistered existing source success')
        cpu();require(time.monotonic()-start<3600,'Registered remaining audio budget')
        v=np.load(bound(row['input_ref']));clock=read(bound(row['clock_ref']));media=Path(clock['source_path']);size=media.stat().st_size
        require('source_bytes'not in clock or clock['source_bytes']==size,'Exact original media bytes')
        clock=dict(clock,source_bytes=size)
        save(new/(sid+'_augmented_clock.json'),dict(clock=clock,original_clock_ref=row['clock_ref'],old_clock_unchanged=True,recovery_ref=ref(ROOT/'production_recovery_registration_02.json')))
        cache=extract_audio(media,clock,new/sid);features=proposal_audio_features(cache,clock,v['baseline'],row['candidates']);qa=independent_audio_qa(cache,clock,v['baseline'],row['candidates'],features)
        np.savez(new/(sid+'_proposals.npz'),x=features)
        save(path,dict(sid=sid,visual_receipt_ref=vref,clock_ref=row['clock_ref'],input_ref=ref(new/(sid+'_proposals.npz')),manifest_ref=ref(new/(sid+'.manifest.json')),audio_module_ref=ref(Path(__file__).parent/'audio_features_header_v2.py'),audio_QA=qa))
        receipts.append(ref(path));summary.append(dict(sid=sid,**qa));event('FORMAL_FIRST_AUDIO_INPUT_QA',sid=sid,**qa)
    require(len(receipts)==426 and {r['sid']for r in summary}=={str(i)for i in range(426)},'Complete426 exact source denominator')
    save(folder/'completion.json',dict(status='PASS426_FIRST_AUDIO_PROPOSAL_INPUT_QA',sources=receipts,summary=summary,audio_observed_sources=sum(v['audio_observed']for v in summary),successful_no_audio_sources=sum(v['no_audio']for v in summary),elapsed_remaining_seconds=time.monotonic()-start,adopted_successes=recovery['adopted_audio_sources'],recovery_ref=ref(ROOT/'production_recovery_registration_02.json'),admission_ref=ref(ROOT/'production_admission.json'),selection_ref=ref(ROOT/'event_audio_01/frozen_selection.json'),new_video_decode=0,new_8B=0,utc=utc()))


if __name__=='__main__':
    try:main()
    except BaseException as e:failure('formal_audio_remaining_v2',e);raise
