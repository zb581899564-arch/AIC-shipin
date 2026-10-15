"""One metadata-only freeze after accepted B0, before Charades fine roles.

Reads author timing references only in this evaluator, never generates inference
inputs. Fine planning must use original coarse events independently of matches.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import socket

from metric import SCHEMA, RULE, freeze

ROOT=Path('/home/inspur/aic_video_work')
CAMPAIGN=ROOT/'twenty_hour_five_20261014_v1'
COARSE=CAMPAIGN/'charades_coarse_v1'
SOURCES=CAMPAIGN/'charades_boundary_v2'
OUT=CAMPAIGN/'charades_boundary_metric_v1'
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def require(c,why):
    if not c:raise ValueError(why)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):
    with Path(p).open('x') as f:json.dump(value,f,indent=2,allow_nan=False)


def bound(path,digest,bindings):
    path=Path(path).resolve()
    require(path.is_relative_to(CAMPAIGN) and path.suffix in ('.json','.jsonl'),
            'Only named campaign metadata can enter the action proxy evaluator')
    require(sha(path)==digest,'Frozen metadata changed: '+str(path))
    bindings[str(path)]=digest
    return read(path)


def main():
    require(socket.gethostname()=='inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES')=='',
            'Linux-only metadata freeze with this CPU child CUDA hidden')
    protocol=read(OUT/'metric_protocol_01.json')
    require(protocol['schema']==SCHEMA and protocol['rule']==RULE and
            protocol['scientific_quality_claim'] is False and protocol['expected_sources']==21 and
            protocol['expected_source_roles']=={'dev':11,'confirm':10} and
            protocol['expected_coarse_windows']==38 and protocol['fine_results_read_for_matching'] is False,
            'Frozen pre-fine rules and exact current source/window denominator required')
    for name,digest in protocol['code_sha256'].items():
        require(sha(OUT/'code'/name)==digest,'Frozen metric code changed')
    output=OUT/'freeze_01';output.mkdir(exist_ok=False)
    save(output/'claim.json',dict(protocol_sha256=sha(OUT/'metric_protocol_01.json'),
        pid=os.getpid(),new_model_calls=0,new_media_reads=0,fine_role_outputs_read=False))
    bindings={str(OUT/'metric_protocol_01.json'):sha(OUT/'metric_protocol_01.json')}
    try:
        effective=read(SOURCES/'effective_source_registry_02.json')
        require(effective['sources']==21 and effective['dev']==11 and effective['confirm']==10,
                'Original21 source roles must remain, including zero-eligible sources')
        bindings[str(SOURCES/'effective_source_registry_02.json')]=sha(SOURCES/'effective_source_registry_02.json')
        registry={s['source_id']:s for s in effective['accepted']}
        sources=[]
        for row in effective['accepted']:
            completed=bound(row['CPU_completion_path'],row['CPU_completion_sha256'],bindings)
            reference=bound(completed['reference_validation_path'],completed['reference_validation_sha256'],bindings)
            media=bound(row['media_receipt_path'],row['media_receipt_sha256'],bindings)
            require(reference['status']=='PASS_PARTIAL_AUTHOR_ACTION_ELIGIBILITY_NOT_COMPLETE_HIGHLIGHT_GT'
                    and reference['whole_source_precision_recall_F1_admitted'] is False
                    and reference['seconds_shifted'] is False and reference['labels_stretched'] is False
                    and reference['endpoint_clipped'] is False,'Unchanged strict partial native reference required')
            sources.append(dict(source_id=row['source_id'],role=row['role'],source_sha256=media['sha256'],
                physical_end_exact=reference['actual_physical_end_exact'],actions=reference['actions'],
                reference_validation_path=completed['reference_validation_path'],
                reference_validation_sha256=completed['reference_validation_sha256']))
        require(len(registry)==21 and sum(s['role']=='dev' for s in sources)==11 and
                sum(s['role']=='confirm' for s in sources)==10,'All source/group denominators unchanged')
        admission=read(COARSE/'gpu_admission.json');complete=read(COARSE/'gpu_01/completion.json')
        replay=read(COARSE/'replay_01/completion.json');inputs=read(COARSE/'coarse_inputs.json')
        require(len(inputs)==38 and complete['calls']==38 and len(complete['entries'])==38
                and complete['status']=='PASS_NEW_CHARADES_COARSE_CALLS_NOT_QUALITY'
                and replay['calls']==38 and len(replay['proofs'])==38
                and replay['status']=='PASS_ALL_NEW_CHARADES_COARSE_INPUT_OUTPUT_REPLAYS_NOT_QUALITY'
                and replay['gpu_completion_sha256']==sha(COARSE/'gpu_01/completion.json'),
                'All38 original B0 calls and independent replays must be complete')
        resource_path=RUN/'controller'/(admission['gpu_job_name']+'.resource.json')
        resource=read(resource_path)
        ledger=[json.loads(x) for x in (ROOT/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x]
        require(resource['status']=='completed' and resource['exit_code']==0 and
                [e for e in ledger if e['name']==resource['name']]==[resource] and
                sha(resource_path)==replay['resource_terminal_sha256'],'Unique natural B0 terminal required')
        done_refs={r['case_id']:r for r in complete['entries']};replay_refs={r['case_id']:r for r in replay['proofs']}
        require(len(done_refs)==len(replay_refs)==38,'Unique original coarse/replay cases')
        events=[];windows=[]
        for entry in inputs:
            case=entry['case_id'];done_ref=done_refs[case];replay_ref=replay_refs[case]
            meta=bound(entry['input_path'],entry['input_sha256'],bindings)
            done=bound(done_ref['done_path'],done_ref['done_sha256'],bindings)
            proof=bound(replay_ref['proof_path'],replay_ref['proof_sha256'],bindings)
            sid=entry['source_id'];source=registry[sid]
            require(meta['case_id']==done['case_id']==proof['case_id']==case and
                    meta['source_name']==done['source_name']==sid and
                    source['role']==entry['source_role'] and proof['new_model_calls']==0 and
                    proof['status']=='PASS_INDEPENDENT_CPU_TENSOR_TOKEN_PARSER_NATIVE_REPLAY' and
                    done['segments']==proof['segments'] and not done['parse_errors'],
                    'Original coarse source/interval and independent replay binding differs')
            require(done['status'] in ('MODEL_OK','LEGAL_EMPTY') and
                    (bool(done['segments'])==(done['status']=='MODEL_OK')),
                    'Legal empty must remain in the original window denominator')
            lo,hi=F(done['source_start_exact']),F(done['source_end_exact'])
            windows.append(dict(case_id=case,source_id=sid,role=entry['source_role'],
                status=done['status'],coarse_events=len(done['segments']),done_sha256=done_ref['done_sha256']))
            for index,pair in enumerate(done['segments']):
                a,b=[F(str(v)) for v in pair]
                require(0<=a<b<=hi-lo,'Invalid original coarse segment must not disappear from denominator')
                events.append(dict(event_id=case+'.segment'+str(index),source_id=sid,
                    original_case_id=case,original_segment_index=index,
                    original_interval_exact=[str(lo+a),str(lo+b)]))
        require({w['source_id'] for w in windows}==set(registry),'Zero-event sources remain represented by their original windows')
        # Original coarse geometry only: no action/class/eligibility information.
        # Fine planning can bind this projection rather than read matching GT.
        save(output/'coarse_events_projection.json',dict(schema='ORIGINAL_B0_GEOMETRY_FOR_NON_GT_FINE_PLANNING_V1',
            coarse_complete_sha256=sha(COARSE/'gpu_01/completion.json'),events=events,
            source_roles={s['source_id']:s['role'] for s in sources},GT_available_to_inference=False))
        frozen=freeze(events,sources)
        frozen.update(input_bindings=bindings,source_registry_sha256=sha(SOURCES/'effective_source_registry_02.json'),
            protocol_sha256=sha(OUT/'metric_protocol_01.json'),original_windows=windows,
            coarse_complete_sha256=sha(COARSE/'gpu_01/completion.json'),
            coarse_replay_complete_sha256=sha(COARSE/'replay_01/completion.json'),
            coarse_input_manifest_sha256=sha(COARSE/'coarse_inputs.json'),
            coarse_resource_terminal_sha256=sha(resource_path),fine_outputs_read=False,
            correspondence_does_not_select_fine_events=True,GT_available_to_inference=False)
        save(output/'frozen_matches.json',frozen)
        result=dict(status='PASS_FROZEN_GEOMETRIC_DIAGNOSTIC_MATCHES_NOT_SEMANTIC_OR_QUALITY_ADMISSION',
            frozen_matches_sha256=sha(output/'frozen_matches.json'),sources=21,
            original_windows=38,original_coarse_events=len(events),expected_endpoints=2*len(events),
            diagnostic_endpoints=sum(s['diagnostic_endpoints'] for s in frozen['source_coverage']),
            source_coverage=frozen['source_coverage'],fine_results_read=False,
            media_or_processor_or_model_calls=0,scientific_quality_claim=False)
        save(output/'completion.json',result);print(json.dumps(result))
    except BaseException as error:
        save(output/'failure.json',dict(error=repr(error),preserve_all_success=True,automatic_retry=False))
        raise


if __name__=='__main__':
    os.environ['CUDA_VISIBLE_DEVICES']='';main()
