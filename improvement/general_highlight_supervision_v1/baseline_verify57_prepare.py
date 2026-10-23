"""New VERIFY requests adopt original64 RGB; original B0 answers are not rerun."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from bisect import bisect_left
from fractions import Fraction
import torch
from transformers import AutoProcessor
from baseline_bridge57_common import ROOT,DATA,RUN,read,ref,save,checked,legacy_runtime,verify_modules


def main():
    torch.set_num_threads(2)
    source=read(ROOT/'registration.json')['source'];clock=read(checked(source['clock']))
    origin=Fraction(clock['first_PTS_exact']);pts=[Fraction(p)-origin for p in clock['PTS']]
    physical=Fraction(clock['physical_end_exact'])-origin
    rt=legacy_runtime();contract,_,protocol=verify_modules()
    from time_control50_prepare import encode_case
    processor=AutoProcessor.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'],
        local_files_only=True,min_pixels=131072,max_pixels=131072)
    cases={}
    for record in read(DATA/'CPU_completion.json')['accepted']:
        proof=read(checked(record));meta=read(checked(proof['input']));cases[meta['case_id']]=meta
    folder=ROOT/'verify';folder.mkdir();events=[];accepted=[]
    for record in read(DATA/'gpu_completion.json')['outputs']:
        answer=read(checked(record));meta=cases[answer['case']]
        lo=Fraction(meta['window_start']);hi=Fraction(meta['window_end'])
        first=meta['source_frame_ordinals'][0];stop=meta['source_frame_ordinals'][-1]+1
        view_start=pts[first];view_end=pts[stop] if stop<len(pts) else physical
        for index,(a,b) in enumerate(answer['segments']):
            start=lo+Fraction(str(a));end=lo+Fraction(str(b))
            i,j=bisect_left(pts,start),bisect_left(pts,end)
            if not first<=i<j<=stop:raise ValueError('Original B0 event has no complete native support')
            native_end=pts[j] if j<len(pts) else physical
            event_id=meta['case_id']+'_E'+str(index).zfill(2)
            event=dict(event_id=event_id,original_segment_index=index,
                original_interval_exact=[str(start),str(end)],original_window_exact=[str(lo),str(hi)],
                original_native_cut_interval_exact=[str(pts[i]),str(native_end)])
            request_meta=dict(meta,case_id=event_id+'.verify',window_start=str(view_start),window_end=str(view_end))
            native_event=dict(event,original_interval_exact=event['original_native_cut_interval_exact'])
            request=contract.request(native_event,dict(request_meta,case_id=meta['case_id']))
            request['prompt']=protocol.verify_prompt(request,contract)
            case_folder=folder/(event_id+'.verify');case_folder.mkdir()
            save(case_folder/'input.json',request_meta);save(case_folder/'request.json',request)
            proof=encode_case(rt,processor,request_meta,case_folder)
            accepted.append(dict(event=event,request=ref(case_folder/'request.json'),CPU=proof))
            events.append(event)
            print('FULL_BASELINE_VERIFY_CPU',len(accepted),flush=True)
    save(ROOT/'verify_CPU_completion.json',dict(state='PASS_FIRST_VERIFY_INPUTS',cases=accepted,events=events,
        prior_B0_successes_adopted=True,new_decode=0,
        first_new_VERIFY_processor=True,new_timing_context_and_prompt=True,
        physical_end_exact=str(physical),source_clock=source['clock']))


if __name__=='__main__':main()
