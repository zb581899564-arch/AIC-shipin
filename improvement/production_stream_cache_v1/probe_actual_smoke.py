"""One newly authorized exact storage-codec probe of one completed smoke tensor.

No RGB, media decoder, processor, model, original cache writes or deletions.
"""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import socket
import time

from codec import exact_equal, signature
from pixel_dictionary import pack, unpack, FORMAT

ROOT=Path('/home/inspur/aic_video_work')
BASE=ROOT/'twenty_hour_five_20261014_v1/local_boundary_v2'
OUT=ROOT/'twenty_hour_five_20261014_v1/cache_codec_06/dictionary_actual_probe_01'
REQUEST='SMOKE_ORIGINAL_SCREEN_001.start'


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False)
def require(c,reason):
    if not c:raise ValueError(reason)


def main():
    require(socket.gethostname()=='inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES')=='',
            'One CPU-only codec probe on the verified Linux host')
    require(not OUT.exists(),'Actual successful codec probe must never be repeated')
    cpu_complete=read(BASE/'cpu_01/completion.json');gpu=read(BASE/'gpu_01/completion.json')
    replay_complete=read(BASE/'replay_01/completion.json');admission=read(BASE/'gpu_admission.json')
    require(cpu_complete['status']=='PASS_ALL_NEW_LOCAL_BOUNDARY_CPU_INPUTS_NOT_GPU_ADMISSION'
            and gpu['status']=='PASS_ALL_LOCAL_BOUNDARY_CALLS_NOT_QUALITY'
            and replay_complete['status']=='PASS_ALL_NEW_LOCAL_BOUNDARY_INDEPENDENT_REPLAYS_NOT_QUALITY'
            and replay_complete['gpu_completion_sha256']==sha(BASE/'gpu_01/completion.json'),
            'Prior actual CPU/GPU/independent replay success is required')
    entries=[e for e in cpu_complete['proofs'] if e['request_id']==REQUEST]
    replay_entries=[e for e in replay_complete['proofs'] if e['request_id']==REQUEST]
    require(len(entries)==len(replay_entries)==1,'Fixed first smoke start request only')
    entry,re=entries[0],replay_entries[0]
    require(sha(entry['proof_path'])==entry['proof_sha256'] and sha(re['proof_path'])==re['proof_sha256'],
            'Original proof metadata changed')
    cpu=read(entry['proof_path']);replay=read(re['proof_path'])
    require(cpu['request_id']==replay['request_id']==REQUEST and
            cpu['input_evidence']==replay['input_evidence'] and replay['CPU_only'] is True
            and replay['new_model_calls']==0,'Same independently accepted input')
    tensor=Path(cpu['encoded_tensor_path'])
    require(tensor==BASE/'cpu_01'/REQUEST/'encoded_tensors.pt.gz','No alternate actual tensor source')
    run=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    terminal_path=run/'controller'/(admission['gpu_job_name']+'.resource.json')
    terminal=read(terminal_path)
    ledger=[json.loads(x) for x in (ROOT/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x]
    require(terminal['status']=='completed' and terminal['exit_code']==0 and
            [e for e in ledger if e['name']==terminal['name']]==[terminal] and
            sha(terminal_path)==replay_complete['resource_terminal_sha256'],'Unique natural old GPU terminal')
    resources=dict(hostname=socket.gethostname(),load_average=os.getloadavg(),
        memory=Path('/proc/meminfo').read_text().splitlines()[:6],
        peers=__import__('subprocess').run(['ps','-eo','pid,ppid,pcpu,pmem,comm','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:15])
    OUT.mkdir()
    save(OUT/'claim.json',dict(request_id=REQUEST,source_tensor_path=str(tensor),
        expected_source_sha256=cpu['encoded_tensor_sha256'],script_sha256=sha(__file__),
        source_CPU_proof_sha256=entry['proof_sha256'],independent_replay_sha256=re['proof_sha256'],
        storage_schema=FORMAT,source_RGB_read=False,new_processor_or_model_calls=0,resources=resources))
    try:
        import torch
        torch.set_num_threads(1)
        # Exactly one original file body read, simultaneously verifying its old accepted SHA.
        source_bytes=tensor.read_bytes()
        require(hashlib.sha256(source_bytes).hexdigest()==cpu['encoded_tensor_sha256'],'Original accepted tensor changed')
        with gzip.GzipFile(fileobj=io.BytesIO(source_bytes),mode='rb') as stream:
            encoded=torch.load(stream,map_location='cpu',weights_only=True);stream.seek(0,os.SEEK_END)
        original_sig=signature(encoded)
        old_sig={k:{field:v[field] for field in ('shape','dtype','sha256')} for k,v in original_sig['tensors'].items()}
        require(old_sig==cpu['input_evidence']['tensor_signature'],'Old independent canonical tensor bytes differ')
        started=time.monotonic();payload,report=pack(encoded);packing_seconds=time.monotonic()-started
        packed_path=OUT/'exact_dictionary_tensors.pt.gz'
        started=time.monotonic()
        with packed_path.open('xb') as raw:
            with gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=1,mtime=0) as stream:torch.save(payload,stream)
            raw.flush();os.fsync(raw.fileno())
        write_seconds=time.monotonic()-started
        started=time.monotonic()
        with packed_path.open('rb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='rb') as stream:
                restored_payload=torch.load(stream,map_location='cpu',weights_only=True);stream.seek(0,os.SEEK_END)
        restored=unpack(restored_payload)
        require(exact_equal(encoded,restored),'Full actual tensor dictionary roundtrip failed')
        load_compare_seconds=time.monotonic()-started
        require(not torch.cuda.is_initialized(),'Storage codec probe initialized CUDA')
        result=dict(status='PASS_ONE_COMPLETED_SMOKE_EXACT_STORAGE_PROBE_NOT_PRODUCTION_FIT',
            source_path=str(tensor),source_sha256=cpu['encoded_tensor_sha256'],
            source_gzip_bytes=len(source_bytes),logical_tensor_bytes=sum(t.numel()*t.element_size() for t in encoded.values()),
            new_dictionary_gzip_bytes=packed_path.stat().st_size,new_dictionary_sha256=sha(packed_path),
            ratio_new_to_source_gzip=packed_path.stat().st_size/len(source_bytes),
            per_tensor_report=report,pixel_tensor_shape=list(encoded['pixel_values_videos'].shape),
            pixel_tensor_dtype=str(encoded['pixel_values_videos'].dtype),
            packing_seconds=packing_seconds,write_seconds=write_seconds,load_compare_seconds=load_compare_seconds,
            process_peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            all_actual_tensor_keys_dtype_shape_stride_alias_and_bitbytes_roundtrip_exact=True,
            source_file_body_reads=1,source_RGB_or_media_reads=0,processor_or_model_calls=0,
            original_source_writes_or_deletes=0,model_precision_changed=False,production_fit_claim=False,
            CUDA_initialized=False,torch_version=torch.__version__,
            code_sha256={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')})
        save(OUT/'completion.json',result);print(json.dumps(result),flush=True)
    except BaseException as error:
        save(OUT/'failure.json',dict(error=repr(error),preserve_all_partial=True,automatic_retry=False))
        raise


if __name__=='__main__':main()
