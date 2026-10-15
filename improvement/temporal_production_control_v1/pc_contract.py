"""Pure full-graph batch/resource/journal invariants. No production IO."""
import hashlib
import json
import math

SCHEMA='TEMPORAL_PRODUCTION_CONTROL_V1'


def require(ok,why):
    if not ok:raise ValueError(why)


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def full_coverage(plan,batches,batch_validator):
    seen_sources=[];actual=[];logical=[];names=[]
    for batch in batches:
        if batch.get('cpu_only_empty_batch') is True:
            original=[source['source_id'] for source in plan['sources']];positions=[original.index(sid) for sid in batch['source_ids']]
            require(positions and positions==list(range(positions[0],positions[0]+len(positions))), 'CPU-only empty source block must be contiguous')
            rows=[row for row in plan['requests'] if row['source_id'] in batch['source_ids']]
            require(not rows and batch['logical_request_ids']==batch['request_ids']==[] and batch['actual_model_call_budget']==0 and
                batch.get('gpu_job_name') is None,'CPU-only empty source block must not contain fake model requests/job')
        else:
            rows=batch_validator(batch,plan);names.append(batch['gpu_job_name'])
        seen_sources.extend(batch['source_ids']);actual.extend(batch['request_ids']);logical.extend(batch['logical_request_ids'])
        require([row['request_id'] for row in rows]==batch['logical_request_ids'],'Per-batch exact original graph differs')
    require(seen_sources==[source['source_id'] for source in plan['sources']] and len(set(seen_sources))==len(seen_sources),
            'Full source coverage/order or batch disjointness failed')
    require(actual==plan['consumers'] and len(set(actual))==len(actual) and
            logical==[row['request_id'] for row in plan['requests']] and len(set(logical))==len(logical),
            'Full actual/logical request coverage, order or uniqueness failed')
    require(len(set(names))==len(names),'Every real GPU batch must have a new unique shared job name')
    return dict(source_count=len(seen_sources),actual_model_calls=len(actual),logical_requests=len(logical),batches=len(batches))


def source_bound(source,rows,groups,video_size):
    """Conservative uncompressed bound; no fixed grid or compression ratio."""
    union={i for group in groups.values() for i in group['source_frame_ordinals']}
    one=64*source['width']*source['height']*3
    tensor=int(video_size['longest_edge'])*3*4+16384*16+65536
    consumers=sum(row['execution']=='MODEL' for row in rows)
    permanent=consumers*(tensor+tensor//1000+65536)
    staging=len(groups)*(one+one//1000+65536)
    transient=4*tensor+2*one
    return dict(memory_bytes=len(union)*source['width']*source['height']*3+2*one+4*tensor,
        disk_bytes=permanent+staging+transient,permanent_bytes=permanent,staging_bytes=staging,transient_bytes=transient,
        compression_assumed=False,source_id=source['source_id'])


def runnable(bound,snapshot,active_bounds):
    """Concurrency derives from current resource bytes/core pressure, never constants."""
    reserve_memory=sum(row['memory_bytes'] for row in active_bounds)
    reserve_disk=sum(row['disk_bytes'] for row in active_bounds)
    slots=max(0,snapshot['affinity_cpus']-math.ceil(snapshot['load_1min']))
    return (len(active_bounds)<slots and bound['memory_bytes']+reserve_memory<=snapshot['mem_available_bytes'] and
            bound['disk_bytes']+reserve_disk<=snapshot['disk_available_bytes'])


def guard_no_repeat(journal,phase,item):
    require(not any(row['phase']==phase and row['item']==item and row['event']=='BEGIN' for row in journal),
            'An attempted/successful operation cannot repeat; explicit new recovery required')


def validate_stage_journal(journal,expected):
    begin={};end={}
    for row in journal:
        key=(row['phase'],row['item'])
        require(key in expected,'Unfrozen journal operation')
        if row['event']=='BEGIN':require(key not in begin,'Repeated BEGIN');begin[key]=row
        elif row['event']=='COMPLETE':require(key in begin and key not in end and row['exit_code']==0,'Orphan/duplicate/nonzero completion');end[key]=row
        elif row['event']=='REUSE':
            require(key not in begin and key not in end and row['exit_code']==0 and row['actual_new_calls']==0,
                    'Reused successful operation was duplicated');begin[key]=row;end[key]=row
        else:raise ValueError('Failed/pending journal cannot claim global success')
    require(set(begin)==set(end)==set(expected),'Missing/pending complete global operation denominator')
    return True
