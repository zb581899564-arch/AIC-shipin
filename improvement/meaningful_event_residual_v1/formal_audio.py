"""First audio-specific formal descriptors; fixed model and source identities."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys,time
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path[:0]=[str(ROOT/'audio_code_v1'),str(ROOT/'code_v1')]
from audio_event import independent_audio_qa
from event_runtime import *
from audio_features import extract_audio,proposal_audio_features


def main():
    cpu();admission=read(ROOT/'production_admission.json')
    require('EVENT_AUDIO_VISUAL'in admission['mechanisms'],'Explicit frozen audiovisual formal admission required')
    frozen=read(ROOT/'event_audio_01/frozen_selection.json');bound(frozen['weights_ref'])
    accepted=read(ROOT/'formal_inputs_01/completion.json')
    require(accepted['status']=='PASS426_FIRST_NATIVE_EVENT_DESCRIPTOR_QA','Adopt426 all accepted visual event inputs')
    require(read(ROOT/'event_audio_01/completion.json')['status']=='COMPLETED_ONE_AUDIO_VISUAL_RESEARCH_MODEL','External audio firstQA/model/evaluation completed before formal audio')
    folder=ROOT/'formal_audio_01';folder.mkdir();start=time.monotonic();receipts=[];summary=[]
    save(folder/'start.json',dict(admission_ref=ref(ROOT/'production_admission.json'),selection_ref=ref(ROOT/'event_audio_01/frozen_selection.json'),visual_completion_ref=ref(ROOT/'formal_inputs_01/completion.json'),code_ref=ref(Path(__file__)),audio_module_ref=ref(ROOT/'audio_code_v1/audio_features.py'),new_video_decode=0,new_8B=0,utc=utc()))
    for vref in accepted['sources']:
        cpu();require(time.monotonic()-start<3600,'Registered formal audio preparation wall budget')
        row=read(bound(vref));sid=row['sid'];v=np.load(bound(row['input_ref']));clock=read(bound(row['clock_ref']));media=Path(clock['source_path']);size=media.stat().st_size
        require('source_bytes'not in clock or clock['source_bytes']==size,'Original formal media bytes consistent')
        clock=dict(clock,source_bytes=size)
        save(folder/(sid+'_augmented_clock.json'),dict(clock=clock,original_clock_ref=row['clock_ref'],source_bytes_added_from_current_SHA_bound_media=True,old_clock_unchanged=True))
        cache=extract_audio(media,clock,folder/sid);features=proposal_audio_features(cache,clock,v['baseline'],row['candidates'])
        qa=independent_audio_qa(cache,clock,v['baseline'],row['candidates'],features)
        np.savez(folder/(sid+'_proposals.npz'),x=features)
        path=folder/(sid+'.json')
        save(path,dict(sid=sid,visual_receipt_ref=vref,clock_ref=row['clock_ref'],input_ref=ref(folder/(sid+'_proposals.npz')),manifest_ref=ref(folder/(sid+'.manifest.json')),audio_QA=qa))
        receipts.append(ref(path));summary.append(dict(sid=sid,**qa));event('FORMAL_FIRST_AUDIO_INPUT_QA',sid=sid,**qa)
    require(len(receipts)==426,'Complete426 formal audio denominator')
    save(folder/'completion.json',dict(status='PASS426_FIRST_AUDIO_PROPOSAL_INPUT_QA',sources=receipts,summary=summary,audio_observed_sources=sum(v['audio_observed']for v in summary),successful_no_audio_sources=sum(v['no_audio']for v in summary),elapsed_seconds=time.monotonic()-start,admission_ref=ref(ROOT/'production_admission.json'),selection_ref=ref(ROOT/'event_audio_01/frozen_selection.json'),new_video_decode=0,new_8B=0,utc=utc()))


if __name__=='__main__':
    try:main()
    except BaseException as e:failure('formal_first_audio',e);raise
