"""One pre-fine metadata alias/plan join. No media/tensor/processor/model IO."""
import hashlib
import json
from pathlib import Path
import socket
import os

CAMPAIGN=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
BASE=CAMPAIGN/'charades_boundary_metric_v1'
COARSE=CAMPAIGN/'charades_coarse_v1'
V4=CAMPAIGN/'local_boundary_v4'


def require(value,why):
    if not value:raise ValueError(why)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
def metadata(path,digest=None):
    path=Path(path).resolve()
    require(path.is_relative_to(CAMPAIGN) and path.suffix=='.json','Named campaign JSON metadata only')
    if digest is not None:require(sha(path)==digest,'Frozen metadata changed '+str(path))
    return read(path)
def ref(path):return dict(path=str(path),sha256=sha(path))
def copy_witness(source,target):
    raw=Path(source).read_bytes()
    with target.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    require(sha(source)==sha(target),'New witness copy differs from original bytes')
    return ref(target)


def main():
    require(socket.gethostname()=='inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES')=='',
            'Linux CPU-only metadata join')
    require(Path(__file__).resolve()==BASE/'control/freeze_alias_plan_01.py','Frozen independent helper location')
    frozen=metadata(BASE/'freeze_01/frozen_matches.json')
    completion=metadata(BASE/'freeze_01/completion.json')
    require(completion['frozen_matches_sha256']==sha(BASE/'freeze_01/frozen_matches.json'),
            'Original pre-fine correspondence changed')
    extract_root=COARSE/'event_extraction_01'
    extraction=metadata(extract_root/'completion.json')
    require(extraction['role_event_counts']=={'dev':20,'confirm':18} and
            extraction['confirmation_extraction_frozen_before_development_refiner_results'] is True and
            extraction['confirmation_metrics_sealed'] is True and extraction['GT_reads']==0 and
            extraction['new_model_calls']==0,'Original pre-fine non-GT extraction changed')
    require(not (V4/'dev/gpu_01').exists() and not (V4/'confirm/gpu_01').exists(),
            'Alias/availability join must precede fine role calls')
    out=BASE/'alias_plan_01';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(helper_sha256=sha(__file__),pid=os.getpid(),
        frozen_matches_ref=ref(BASE/'freeze_01/frozen_matches.json'),
        extraction_completion_ref=ref(extract_root/'completion.json'),fine_outputs_read=False,new_model_calls=0))
    try:
        identities={};aliases=[];by_alias={}
        for event in frozen['events']:
            sid,case,index=event['source_id'],event['original_case_id'],event['original_segment_index']
            canonical=case+'.segment'+str(index);alias=case+'.S'+format(index,'02d')
            identity=(sid,case,index)
            require(canonical==event['event_id'] and identity not in identities and alias not in by_alias,
                    'Coarse source/case/segment alias is not one-to-one')
            row=dict(alias_event_id=alias,canonical_event_id=canonical,source_id=sid,
                source_role=event['source_role'],original_case_id=case,original_segment_index=index,
                original_interval_exact=event['original_interval_exact'])
            identities[identity]=row;aliases.append(row);by_alias[alias]=row
        alias_path=out/'event_aliases.json'
        save(alias_path,dict(schema='FROZEN_ORIGINAL_COARSE_SOURCE_CASE_SEGMENT_ALIAS_BIJECTION_V1',
            aliases=aliases,all_coarse_events=len(aliases),matching_key=['source_id','original_case_id','original_segment_index'],
            GT_used=False,fine_outputs_read=False,generated_from_prediction_quality=False,
            original_frozen_matches_ref=ref(BASE/'freeze_01/frozen_matches.json')))
        planned={};original={}
        for scope,expected in (('dev',20),('confirm',18)):
            path=extract_root/(scope+'_events.json');events=metadata(path)
            require(len(events)==expected,'Frozen planned event denominator changed')
            ids=[]
            for event in events:
                key=(event['source_id'],event['original_case_id'],event['original_segment_index'])
                row=identities[key]
                require(event['event_id']==row['alias_event_id'] and event['source_role']==scope==row['source_role'] and
                        event['original_interval_exact']==row['original_interval_exact'],
                        'Planned source/case/segment/interval alias differs from original coarse geometry')
                ids.append(row['canonical_event_id'])
            require(len(ids)==len(set(ids)),'Planned alias duplicated original event')
            original[scope]=events
            planned[scope]=dict(schema='FROZEN_BOUNDARY_ROLE_CANDIDATES_FROM_COARSE_NATIVE_GEOMETRY_ONLY_V1',
                scope=scope,event_ids=ids,coarse_complete_sha256=frozen['coarse_complete_sha256'],
                reference_labels_used_to_select=False,fine_results_available_at_freeze=False,
                source_case_segment_alias_ref=ref(alias_path),original_extracted_events_ref=ref(path),
                extraction_completion_ref=ref(extract_root/'completion.json'),max_events=20,
                no_replacement_from_GT_or_fine=True)
        plan=V4/'dev/plan_01';pc=metadata(plan/'completion.json')
        pe=metadata(plan/'events.json',pc['events_sha256'])
        av=metadata(plan/'endpoint_availability.json',pc['endpoint_availability_sha256'])
        require(pc['nominal_endpoints']==40 and pc['actionable_requests']==37 and pc['structural_skips']==3 and
                pc['events']==20 and pc['availability_frozen_before_fine_results'] is True and
                av['availability_frozen_before_fine_results'] is True and av['GT_used'] is False,
                'Complete pre-fine dev native availability denominator changed')
        require([(x['event_id'],x['source_id'],x['original_case_id'],x['original_segment_index'],x['original_interval_exact']) for x in pe]==
                [(x['event_id'],x['source_id'],x['original_case_id'],x['original_segment_index'],x['original_interval_exact']) for x in original['dev']],
                'V4 planned original identities differ from frozen extraction')
        witness_ref=av['independent_clock_geometry_witness']
        witness=metadata(witness_ref['path'],witness_ref['sha256'])
        require(witness['status']=='PASS_FIRST_INDEPENDENT_CLOCK_ONLY_FULL_NOMINAL_AVAILABILITY' and
                witness['availability_frozen_before_fine_results'] is True and
                witness['nominal_endpoints']==40 and witness['actionable_requests']==37 and witness['structural_skips']==3 and
                witness['new_media_reads']==witness['new_processor_encodes']==witness['new_model_calls']==0,
                'First independent complete nominal clock witness missing')
        require(len(av['endpoint_availability'])==len(witness['endpoint_availability'])==40,
                'Availability must include all nominal endpoints')
        rows=[];seen=set()
        for row,independent in zip(av['endpoint_availability'],witness['endpoint_availability']):
            keys=('event_id','side','request_id','status','native_frame_count','required_native_frames',
                  'full_clock_reference','window_start','window_end')
            require(all(row[k]==independent[k] for k in keys),'Dev availability differs from independent proof')
            alias=by_alias[row['event_id']];side=row['side'];key=(alias['canonical_event_id'],side)
            require(alias['source_role']=='dev' and alias['canonical_event_id'] in planned['dev']['event_ids'] and
                    side in ('start','end') and key not in seen and row['required_native_frames']==64 and
                    row['status'] in ('AVAILABLE_NATIVE_CONTEXT','SHORT_NATIVE_CONTEXT_UNAVAILABLE') and
                    (row['native_frame_count']>=64)==(row['status']=='AVAILABLE_NATIVE_CONTEXT'),
                    'Canonical dev availability/count partition failed')
            seen.add(key);rows.append({**row,'event_id':alias['canonical_event_id'],
                'original_alias_event_id':row['event_id']})
        require(seen=={(eid,s) for eid in planned['dev']['event_ids'] for s in ('start','end')},
                'Canonical planned dev endpoint denominator incomplete')
        witnesses=out/'witnesses';witnesses.mkdir()
        av_copy=copy_witness(plan/'endpoint_availability.json',witnesses/'dev_endpoint_availability.json')
        iw_copy=copy_witness(Path(witness_ref['path']),witnesses/'dev_availability_geometry_proof.json')
        planned['dev'].update(status='FROZEN_DEV_CANONICAL_EVENT_IDS_AND_FULL_NATIVE_AVAILABILITY_BEFORE_FINE',
            availability_frozen_before_fine_results=True,endpoint_availability=rows,
            availability_independent_clock_receipt_ref=iw_copy,original_availability_witness_ref=av_copy,
            original_v4_plan_completion_ref=ref(plan/'completion.json'),nominal_endpoints=40,
            actionable_requests=37,structural_skips=3)
        # There is no confirm V4 plan yet. Preserve fixed identities without
        # fabricating availability or admitting evaluation/model calls.
        planned['confirm'].update(status='WAITING_CONFIRM_V4_NATIVE_AVAILABILITY_FIXED_IDENTITIES_ONLY',
            availability_frozen_before_fine_results=False,endpoint_availability=None,
            availability_independent_clock_receipt_ref=None,evaluation_or_model_admitted=False,
            add_ready_availability_in_new_receipt_without_changing_original_ids=True)
        save(out/'planned_dev_event_ids.json',planned['dev'])
        save(out/'planned_confirm_event_ids.json',planned['confirm'])
        coverage=[]
        for scope in ('dev','confirm'):
            ids=set(planned[scope]['event_ids'])
            group=[e for e in frozen['events'] if e['source_role']==scope]
            chosen=[e for e in group if e['event_id'] in ids]
            coverage.append(dict(scope=scope,all_group_coarse_events=len(group),planned_events=len(chosen),
                unselected_coarse_events=len(group)-len(chosen),nominal_planned_endpoints=2*len(chosen),
                planned_geometric_diagnostic_endpoints=sum(p['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY' for e in chosen for p in e['endpoints']),
                planned_unknown_endpoints=sum(p['metric_status']=='UNKNOWN' for e in chosen for p in e['endpoints']),
                reachable_before_native_availability=sum(p['metric_status']=='GEOMETRIC_DIAGNOSTIC_ONLY' and
                    p['GT_two_sided_in_context'] is True for e in chosen for p in e['endpoints'])))
        result=dict(status='PASS_PRE_FINE_ALIAS_AND_DEV_AVAILABILITY_JOIN_CONFIRM_IDENTITIES_ONLY_NO_EVALUATION',
            event_aliases_ref=ref(alias_path),planned_dev_event_ids_ref=ref(out/'planned_dev_event_ids.json'),
            planned_confirm_event_ids_ref=ref(out/'planned_confirm_event_ids.json'),coverage=coverage,
            all_original_coarse_events=len(aliases),source_denominator=frozen['sources'],
            dev_nominal_endpoints=40,dev_actionable_requests=37,dev_structural_skips=3,
            confirm_availability_pending=True,fine_outputs_read=False,
            new_media_or_tensor_reads=0,new_processor_encodes=0,new_model_calls=0,role_evaluations=0,
            scientific_or_highlight_quality_admission=False,helper_sha256=sha(__file__))
        save(out/'completion.json',result);print(json.dumps(result))
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),preserve_original_and_partial=True,automatic_retry=False,
             new_model_calls=0,new_processor_encodes=0));raise


if __name__=='__main__':main()
