"""First CPU bridge review after adopting16 successful outputs; fix optional-size schema."""
import hashlib
import json
from pathlib import Path
import sys

CONTROL=Path('/home/inspur/aic_video_work/highlight_source_control_20261021_v1')
sys.path.insert(0,str(CONTROL))
import transfer18 as bridge


def declared_identity(record):
    path=Path(record['path'])
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if len(record.get('sha256',''))!=64 or digest!=record['sha256']:
        raise ValueError('Actual declared SHA changed: '+str(path))
    if 'bytes' in record and path.stat().st_size!=record['bytes']:
        raise ValueError('Actual declared bytes changed: '+str(path))
    return path


def main():
    root=bridge.ROOT
    failure=bridge.read(root/'controller_failure.json')
    if 'Content-bound dependency changed' not in failure['error'] or (root/'review.json').exists():
        raise ValueError('Explicit remaining review boundary differs')
    refs=[]
    for row in bridge.read(root/'registration.json')['sources']:
        for key in ['clock_ref','comparison_clock_ref']:
            record=row['source'][key];path=declared_identity(record)
            refs.append(dict(original_record=record,actual_bytes=path.stat().st_size,
                declared_sha_unchanged=True,optional_bytes_missing='bytes' not in record))
    resource=bridge.read(bridge.RUN/'controller'/(bridge.JOB+'.resource.json'))
    ledger=[json.loads(line) for line in (bridge.WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status']!='completed' or resource['exit_code']!=0 or [row for row in ledger if row.get('name')==bridge.JOB]!=[resource]:
        raise ValueError('Original GPU unique natural terminal differs')
    bridge.save(root/'review_remaining19_registration.json',dict(
        old_failure=bridge.ref(root/'controller_failure.json'),
        diagnosis='Native clock ref intentionally has path+SHA without optional bytes; strict dict equality rejected matching content',
        original_content_hash_unchanged=refs,new_GPU=0,new_model_calls=0,new_training=0,
        old16_successful_temporal_outputs_adopted=True,code=bridge.ref(Path(__file__))))
    bridge.checked=declared_identity
    bridge.review()
    declared_identity(bridge.read(bridge.PILOT/'registration.json')['protected_baseline'])
    bridge.save(root/'completion_remaining19.json',dict(state=bridge.read(root/'review.json')['state'],
        original_GPU_seconds=resource['charged_seconds'],new_model_calls_in_recovery=0,
        original_failure_preserved=True,new_ZIP=0,baseline40_47_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        bridge.save(bridge.ROOT/'review_remaining19_failure.json',dict(error=repr(error)))
        raise
