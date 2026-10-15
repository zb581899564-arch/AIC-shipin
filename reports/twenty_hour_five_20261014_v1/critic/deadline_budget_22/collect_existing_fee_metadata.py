"""Read existing timing scalars and fixed batch counts; no framework or payload."""
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import socket
import statistics

HOME=Path('/home/inspur/aic_video_work')
C=HOME/'twenty_hour_five_20261014_v1'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def stats(values):
    return dict(n=len(values),total=sum(values),minimum=min(values),median=statistics.median(values),
        mean=statistics.mean(values),maximum=max(values)) if values else dict(n=0)
def fee_scalar(path,key):
    # Only the already-recorded numeric fee field is extracted; no prediction
    # decision, output tokens, score or labels enter this collector or output.
    pattern=r'"'+re.escape(key)+r'"\s*:\s*([0-9.eE+\-]+)'
    found=re.search(pattern,Path(path).read_text(encoding='utf-8-sig'))
    return float(found.group(1)) if found else None
def resource_summary(path):
    if not path.is_file():return dict(path=str(path),present=False)
    r=read(path)
    fields={k:v for k,v in r.items() if not isinstance(v,(dict,list)) and
        (k in ('status','exit_code','name') or any(x in k.lower() for x in ('seconds','wall','started','finished','charged','elapsed')))}
    return dict(path=str(path),present=True,fields=fields)
def historical_gpu(root):
    p=root/'gpu_01/completion.json'
    if not p.is_file():return dict(root=str(root),completion_present=False)
    complete=read(p);values=[]
    for e in complete.get('entries',[]):
        d=read(e['done_path']);raw=Path(d['raw_path'])
        value=fee_scalar(raw,'generation_seconds')
        if value is not None:values.append(value)
    admission=read(root/'gpu_admission.json')
    name=admission.get('gpu_job_name',admission.get('job_name'))
    return dict(root=str(root),completion_present=True,status=complete['status'],
        actual_calls=complete['actual_model_calls'],recorded_generation_seconds=stats(values),
        resource=resource_summary(RUN/'controller'/(name+'.resource.json')),
        generation_excludes_input_load_signature_GPU_transfer_and_model_load=True,
        cold_load_and_cache_IO_breakdown_observed=False)

assert socket.gethostname()=='inspur-NP5570M5'
reg=read(C/'temporal_production_control_v5/registration.json')
index=read(reg['frozen_batch_index_ref']['path'])
batches=[read(ref['path']) for ref in index['batch_refs']]
actual=[rid for b in batches for rid in b['request_ids']]
logical=[rid for b in batches for rid in b['logical_request_ids']]
assert len(batches)==49 and len(actual)==len(set(actual))==1992 and len(logical)==1995
cpu_root=C/'local_boundary_v4/dev'
complete=read(cpu_root/'cpu_01/completion.json')
cpu={key:[] for key in ('request_wall_seconds','processor_seconds','compression_seconds')}
for binding in complete['proofs']:
    proof=read(binding['proof_path'])
    for key in cpu:
        if isinstance(proof.get(key),(int,float)):cpu[key].append(proof[key])
first_path=C/'production_stream_v5/permanent/proofs/P_266aa5886067fbbc1a3a39fe432fc5bb_W000_E00.end_CPU_input.json'
first=read(first_path)
manifest_ref=first['input_manifest_ref']
manifest=read(C/'production_stream_v5'/manifest_ref['relative'])
tensor_refs=[manifest[key] for key in ('private_ref','visual_ref') if manifest[key]]
out=dict(schema='READ_ONLY_EXISTING_FEE_AND_FROZEN_DEADLINE_METADATA_V1',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    launch_utc='2026-10-13T23:18:24Z',deadline=reg['deadline'],
    remaining_seconds=(dt.datetime.fromisoformat(reg['deadline'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds(),
    fixed_batches=dict(batch_count=49,actual_MODEL_count=1992,logical_count=1995,
        endpoint_MODEL_count=sum(r.endswith(('.start','.end')) for r in actual),
        VERIFY_MODEL_count=sum(r.endswith('.verify') for r in actual),
        calls_per_batch=stats([len(b['request_ids']) for b in batches]),
        sources_per_batch=stats([len(b['source_ids']) for b in batches]),
        sum_max_seconds=sum(b['gpu_max_seconds'] for b in batches if b['request_ids']),
        sum_queue_seconds=sum(b['gpu_queue_seconds'] for b in batches if b['request_ids']),
        empty_GPU_batches=sum(not b['request_ids'] for b in batches)),
    TIME37=historical_gpu(C/'local_boundary_v4/dev'),VERIFY20=historical_gpu(C/'candidate_verify_v2/dev'),
    old_TIME_CPU37=dict(proof_count=len(complete['proofs']),scalar_statistics={k:stats(v) for k,v in cpu.items()},
        decoder_and_wait_CPU_breakdown_observed=False),
    one_new_completed_CPU_input=dict(proof_path=str(first_path),status=first['status'],
        input_tokens=first['input_tokens'],request_wall_seconds=first.get('request_wall_seconds'),
        process_peak_rss_kib=first['process_peak_rss_kib'],logical_storage_bytes=first['actual_storage_bytes'],
        actual_reachable_encoded_bytes=first['actual_reachable_encoded_bytes'],
        canonical_payload_ref_bytes=[r['bytes'] for r in tensor_refs],
        canonical_codec=[r.get('storage_codec') for r in tensor_refs],
        logical_bytes_are_not_disk_bytes=True,whole_production_ratio_or_fit_claim=False,
        commit_lock_wait_or_hold_breakdown_observed=False),
    current_disk_available_bytes=shutil.disk_usage(C).free,
    framework_imports=0,media_or_RGB_or_tensor_or_weight_body_reads=0,
    source_decoder_processor_model_calls=0,prediction_decisions_or_labels_used=False,
    historical_success_reexecuted=False)
print(json.dumps(out,separators=(',',':'),allow_nan=False))
