"""One CPU-only delivery pass for admitted frozen duration arms; no experiments."""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from receive_new5_export import ROOT,REPORT,read,sha,save

OUT=REPORT/'delivery_chain_01'

def main():
    result=read(REPORT/'confirm_new5_01/result.json')
    if result['status']!='PASS_FROZEN_D_SCREEN_FACT_AND_RESERVED5_CONFIRM_RISK_ADMISSION':
        raise ValueError('No candidate is admitted to packaging')
    chosen=result['qualified']
    if not chosen or len(set(chosen))!=len(chosen) or any(a not in ('D2','D4','D8') for a in chosen):
        raise ValueError('Fixed candidate selection differs')
    OUT.mkdir(exist_ok=False)
    import psutil
    save(OUT/'launch_claim.json',dict(script_sha256=sha(__file__),confirmation_sha256=sha(REPORT/'confirm_new5_01/result.json'),
        qualified=chosen,new_model_calls=0,CPU_only=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        actual_available_memory_bytes=psutil.virtual_memory().available,actual_disk_free_bytes=shutil.disk_usage(ROOT).free))
    deliveries,failures=[],[]
    for arm in chosen:
        existing=REPORT/('candidate_'+arm+'_01')
        if existing.exists() or (REPORT/('package_failure_'+arm+'_01.json')).exists():
            raise ValueError('Previously launched candidate must use its terminal result, never repeat packaging')
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
        argv=[sys.executable,'-B',str(Path(__file__).with_name('package_duration_candidate.py')),arm]
        with (OUT/(arm+'.log')).open('xb') as log:
            code=subprocess.run(argv,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT).returncode
        if code:
            failure=dict(arm=arm,exit_code=code,failure_path=str(REPORT/('package_failure_'+arm+'_01.json')))
            failures.append(failure);save(OUT/(arm+'.terminal.json'),failure)
            continue
        completion=read(existing/'completion.json')
        source=Path(completion['zip_path'])
        if (completion['status']!='PASS_ONE_NEW_DURATION_GUARD_CONFIRM_SCREENED_RISK_ZIP' or
                completion['arm']!=arm or completion['removed'] or not completion['baseline_boxes_unchanged'] or
                completion['model_params_b']!=8.78245912 or completion['new_model_calls'] or
                source.stat().st_size!=completion['bytes'] or sha(source)!=completion['sha256']):
            raise ValueError('Completed candidate delivery lineage differs')
        delivery=ROOT/'deliveries'/(completion['candidate']+'_20261013')
        delivery.mkdir(exist_ok=False)
        destination=delivery/source.name
        shutil.copyfile(source,destination)
        if destination.stat().st_size!=source.stat().st_size or sha(destination)!=sha(source):
            raise ValueError('Windows delivery copy size/SHA differs')
        with zipfile.ZipFile(destination) as z:
            if z.namelist()!=['predictions.jsonl'] or z.testzip() is not None:
                raise ValueError('Windows delivered ZIP member/CRC differs')
            member_sha=hashlib.sha256(z.read('predictions.jsonl')).hexdigest()
            if member_sha!=sha(existing/'predictions.jsonl'):
                raise ValueError('Windows delivered prediction member changed')
        for name in ('completion.json','independent_validation.json','parameter_validation.json','native_selection_acceptance.json'):
            shutil.copyfile(existing/name,delivery/name)
        receipt=dict(status='PASS_NEW_DURATION_GUARD_WINDOWS_DELIVERY_BYTES_SHA_CRC_SINGLE_MEMBER',
            arm=arm,candidate=completion['candidate'],zip_path=str(destination.resolve()),bytes=destination.stat().st_size,
            sha256=sha(destination),prediction_member_sha256=member_sha,frames=completion['frames'],added_frames=completion['added'],
            removed=0,baseline_boxes_unchanged=True,source_package_completion_sha256=sha(existing/'completion.json'),
            actual_model_parameters=8782459120,official_score='UNKNOWN',new_model_calls=0,new_optimizer_updates=0)
        save(delivery/'local_delivery_receipt.json',receipt)
        deliveries.append(receipt);save(OUT/(arm+'.terminal.json'),receipt)
        print(json.dumps(receipt,ensure_ascii=False),flush=True)
        state=read(REPORT/'current_state.json')
        state.update(stage='DURATION_GUARD_NEW_ZIP_DELIVERY_IN_PROGRESS',qualified_new_submission_zips=deliveries,
            candidate_package_admitted=True,new5_confirmation_completed=True,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        (REPORT/'current_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    completion=dict(status='THREE_DIFFERENT_NEW_DURATION_PACKAGES_DELIVERED' if len(deliveries)==3 else 'DURATION_DELIVERY_PARTIAL_TARGET_NOT_COMPLETE',
        deliveries=deliveries,failures=failures,new_model_calls=0,new_optimizer_updates=0,official_scores='UNKNOWN')
    save(OUT/'completion.json',completion)
    state=read(REPORT/'current_state.json');state.update(stage=completion['status'],qualified_new_submission_zips=deliveries,
        package_failures=failures,target_delivered=len(deliveries)==3,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (REPORT/'current_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(completion,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
