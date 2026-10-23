"""Acquire four fresh publishers for a whole-source speech-semantic pilot, no blind retries."""
import shutil
import traceback
from common import ROOT,read,ref,save
from media_io35 import receive

TARGET=ROOT/'media35'


def main():
    TARGET.mkdir()
    rows=read(ROOT/'lvsum34/completion.json')['viable']
    pool=sorted([r for r in rows if r['source']['max_ms']<=900000],key=lambda r:r['source']['source_hash'])
    if len(pool)<4:raise ValueError('Four new publisher recordings unavailable')
    selected=pool[:4];reserves=pool[4:]
    planned=sum(r['bytes'] for r in selected)
    if shutil.disk_usage(ROOT).free<planned+sum(r['source']['max_ms']*64 for r in selected):
        raise ValueError('New media plus actual16k float waveform estimate do not fit current capacity')
    save(TARGET/'registration.json',dict(selected=selected,ordered_reserves=reserves,
        source_choice='Original publisher SHA order, original valid max endpoint<=900s; no model quality selection',
        planned_primary_bytes=planned,source_annotation=ref(ROOT/'lvsum20/annotations__lvsum_72_dataset.json'),
        mechanism_to_evaluate='Whole-source time-anchored speech semantics versus original excerpt-only ASR/pooling failures',
        no_previous_LVSum7_or_HF_media_repeated=True,
        original_license='Author CC BY-NC-ND annotations, local noncommercial only; original publisher media rights not blanket-relicensed',
        research_data_not_redistributed=True,baseline40_47_unchanged=True,
        no_automatic_model_call_or_production=True,all_new_metric_unseen=True))
    accepted=[];failed=[]
    for row in selected:
        sid='N'+row['source']['source_hash'][:12]
        try:
            value=receive(row,TARGET/(sid+'.mp4'))
            result=dict(sid=sid,source=row['source'],**value)
            save(TARGET/(sid+'_acceptance.json'),result);accepted.append(result)
            print('NEW_MEDIA_ACCEPTED',sid,row['source']['host'],row['bytes'],flush=True)
        except Exception as error:
            failure=dict(sid=sid,source=row['source'],error=repr(error),traceback=traceback.format_exc())
            failed.append(failure);save(TARGET/(sid+'_failure.json'),failure)
            print('NEW_MEDIA_FAILED',sid,repr(error),flush=True)
    save(TARGET/'completion.json',dict(state='NEW_PUBLISHER_MEDIA_TERMINAL',accepted=accepted,failed=failed,
        successful_sources=len(accepted),new_model_calls=0,no_repeat_successful_download=True))


if __name__=='__main__':main()
