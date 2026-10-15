"""First new role-confirmation media, prior proven pure/native helpers only.

Does not execute the old media registration, main, downloader launcher or any
successful old acquisition. New exact source order and byte budget are bound.
"""
import argparse
import datetime as dt
from decimal import Decimal
from fractions import Fraction as F
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import traceback

HOME=Path('/home/inspur/aic_video_work')
MAIN=HOME/'recall_adapter_role_verify40_46_20261015_v1'
ROOT=MAIN/'fresh_01'
SELECTED=('v_1VDNFR3vQR4','v_SFfB6qvT5FI','v_d0woFZ26Cx0','v_CV9n0jgThLY')
RESERVES=('v_RTwa2d6Oqvo','v_Nj_fvFbf56I')
SIZES=(4607018,3549249,3597547,6002921,4078362,2006560)
POOL=sum(SIZES)


def require(ok,message):
    if not ok:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def checked(ref):
    import hashlib
    path=Path(ref['path']).resolve();require(path.is_relative_to(HOME) and path.is_file(),'Missing/escaped resident dependency')
    require(hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256'],'Changed frozen resident metadata')
    return path


def validate_development(protocol,result,selection,chain,refs):
    require(protocol['schema']=='ADAPTER_ROLE_SAME_INPUT_EXTERNAL_DEV_ABLATION_V1' and
        protocol['candidate']=='BASE_ONLY_POSITIVE_ADMISSION_SAME_INPUT_PAIR' and
        protocol['single_factor']=='BASE_ONLY_FOR_NEW_ADMISSION_TIME_FOR_PROPOSALS' and
        protocol['confirmation_requires_new_registration_and_unexposed_sources'] is True,
        'Exact frozen role development design required')
    conditions={'full_group','macro_F1_not_lower','macro_recall_gain','every_source_loss_within_gate','macro_precision_not_lower',
        'all_rater_recall_retained','all_baseline_native_frames_retained','real_changed_sources'}
    require(result['status']==chain['status']=='PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM' and result['group']=='dev' and
        len(result['cases'])==4 and set(result['conditions'])==conditions and all(v is True for v in result['conditions'].values()) and
        result['bindings']['protocol_ref']==refs['protocol_ref'] and
        chain['comparison_ref']==refs['development_result_ref'] and result['production_admitted'] is False,
        'Real complete dev eight-gate PASS required before first new media')
    require(selection['status']=='PASS_ROLE_DEV_FROZEN_REQUIRES_NEW_UNEXPOSED_CONFIRMATION' and
        selection['protocol_ref']==refs['protocol_ref'] and selection['result_ref']==refs['development_result_ref'] and
        selection['new_confirm_metrics_examined'] is False and selection['production_admitted'] is False,
        'Frozen completed dev selection required before new unexposed source stage')
    gates=protocol['quality_gates']
    require(F(gates['macro_paired_all_rater_duration_F1_delta_min'])==0 and F(gates['macro_all_rater_recall_delta_min'])==F(1,100) and
        F(gates['per_source_F1_delta_min'])==F(-1,100) and F(gates['macro_all_rater_precision_delta_min'])==0 and
        gates['full_group_denominator']==4 and gates['minimum_sources_with_real_new_native_frames']==2,
        'Original eight quality gates cannot be changed')


def registration(root):
    import hashlib
    reg=read(root/'media_registration.json')
    require(reg['schema']=='ROLE_FIRST_FRESH_MEDIA_REGISTRATION_V1' and reg['status']=='REGISTERED_ROLE_FIRST_FRESH_MEDIA_NATIVE' and
        reg['group']=='confirm' and reg['maximum_media_pool_bytes']==POOL and reg['expected_accepted_sources']==4 and
        reg['windows_video_body_bytes']==0 and reg['production_admitted'] is False,'New role-only bounded source authority')
    for name,digest in reg['required_files'].items():checked(dict(path=name,sha256=digest))
    require(reg['purpose']=='NONCOMMERCIAL_STUDENT_PRIVATE_RESEARCH_ONLY' and reg['public_author_to_Linux_route_continuously_authorized'] is True,
        'Retain the actual authorized project/private-research route and use scope')
    scope_paths={HOME/'videoxum_reference_iteration_20261013_v1/direct_source_scope_05.json',HOME/'sparse_context_iteration_20261013_v1/source_scope_02.json'}
    require(len(reg['source_scope_refs'])==2 and {checked(x) for x in reg['source_scope_refs']}==scope_paths,
        'Original media-use and annotation-scope receipts must remain bound')
    checked(reg['authorization_ref'])
    refs={key:reg[key] for key in ['protocol_ref','development_result_ref','development_selection_ref','development_chain_ref']}
    validate_development(*(read(checked(refs[k])) for k in ['protocol_ref','development_result_ref','development_selection_ref','development_chain_ref']),refs)
    candidate=read(checked(reg['source_candidates_ref']));rows=candidate['selection']+candidate['ordered_engineering_reserves']
    require(tuple(x['video_id'] for x in rows)==SELECTED+RESERVES and tuple(x['provider']['size_bytes'] for x in rows)==SIZES and
        candidate['budget']['historical_maximum_pool_bytes']==POOL and reg['selection']==candidate['selection'] and
        reg['ordered_engineering_reserves']==candidate['ordered_engineering_reserves'],'Exact pre-exposure original-hash source order/bytes required')
    hashes=[x['selection_hash'] for x in rows];require(hashes==sorted(hashes) and len(set(hashes))==6,'No source reseeding/reordering')
    known=read(checked(reg['known_exclusions_ref']));excluded={x if x.startswith('v_') else 'v_'+x for x in known['youtube_ids']}
    excluded.update(candidate['all_old_protected_and_acquired_IDs'])
    prohibited=set(known['known_media_sha256']);prior=[]
    for ref in reg['prior18_media_receipts']:
        path=checked(ref);v=read(path)
        require(path.name=='media_receipt.json' and v['video_id'] not in {x['video_id'] for x in prior} and
            v['known_ID_and_byte_separation'] is True,'All exact prior acquired receipt identities required')
        excluded.add(v['video_id']);prohibited.add(v['sha256']);prior.append(v)
    require(len(prior)==18 and not set(SELECTED+RESERVES)&excluded,'Fresh cannot intersect old exposed/acquired/known IDs')
    helper_path=checked(reg['media_helper_ref']);spec=importlib.util.spec_from_file_location('_frozen_positive_native_helpers',helper_path)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.require(reg['annotation_file_ref']['sha256']==helper.ANNOTATION_SHA and reg['known_exclusions_ref']['sha256']==helper.KNOWN_SHA,
        'Original annotation/exclusion bytes unchanged')
    require(reg['required_files'].get(str(Path(__file__).resolve()))==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'Freeze own implementation')
    routes=read(checked(reg['public_routes_ref']))
    require(routes['windows_video_body_bytes']==0 and len(routes['routes'])==6,'Only HEAD publisher route metadata')
    route_by_id={x['video_id']:x for x in routes['routes']};require(set(route_by_id)==set(SELECTED+RESERVES),'All fixed six routes required')
    from urllib.parse import urlparse
    for row in rows:
        route=route_by_id[row['video_id']]
        require(row['provider']['video_url']==helper.public_url(row['youtube_id'])==route['initial_public_url'] and
            route['metadata_only'] is True and route['bytes']==row['provider']['size_bytes'] and
            route['status'] in ('PINNED_NORMAL_PUBLIC_REDIRECT','PUBLIC_OBJECT_404'),'Exact normal publisher route identity')
        if route['status']=='PINNED_NORMAL_PUBLIC_REDIRECT':
            url=urlparse(route['publisher_redirect_url'])
            require(url.scheme=='https' and url.hostname.endswith('.cdn.hf.co') and url.username is None and url.password is None and
                url.port in (None,443) and bool(route['etag']),'HTTPS public publisher CDN only; no custom relay')
    return reg,helper,rows,route_by_id,prohibited,prior


def main(root):
    require(root.resolve()==ROOT and Path(__file__).resolve()==ROOT/'media_code/role_media.py' and sys.platform=='linux' and
        socket.gethostname()=='inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES')=='','Exact new Linux CPU-only root')
    reg,h,rows,routes,prohibited,prior=registration(root)
    output=root/'reference_01';output.mkdir(exist_ok=False)
    h.save(output/'launch_claim.json',dict(utc=h.utc(),pid=os.getpid(),registration_sha256=h.sha(root/'media_registration.json'),
        maximum_media_pool_bytes=POOL,CPU_only=True,actual_new_model_calls=0))
    raw_all=json.loads(checked(reg['annotation_file_ref']).read_text(encoding='utf-8-sig'),parse_float=Decimal,object_pairs_hook=h.unique_object)
    wanted=set(SELECTED+RESERVES);raw={row['video_id']:row for row in raw_all if row['video_id'] in wanted};del raw_all
    require(set(raw)==wanted,'All registered source author rows required')
    accepted=[];rejected=[];current=None;reserved=0;reserve_index=4;measured=0;transfer=dict(actual_new_media_payload_bytes=0)
    try:
        native04,native01=h.native_helpers();import av
        for slot,initial in enumerate(rows[:4]):
            row=initial
            while True:
                current=row['video_id'];folder=output/current;folder.mkdir(exist_ok=False)
                reserved+=row['provider']['size_bytes'];require(reserved<=POOL,'New exact media pool cannot expand')
                receipt,reason=h.download(folder,row,routes[current],prohibited,transfer);require(transfer['actual_new_media_payload_bytes']<=POOL,'Actual body bytes exceed fixed pool')
                rejection=None
                if receipt is None:rejection=dict(video_id=current,reason=reason,downloaded=False,no_model_or_quality_observed=True)
                else:
                    prohibited.add(receipt['sha256']);measured+=1
                    try:clock=native04.measure_original_video(receipt['path'],av)
                    except ValueError as error:
                        if str(error) not in h.NATIVE_MEASUREMENT_REJECTIONS:raise
                        rejection=dict(video_id=current,reason='EXPLICIT_ORIGINAL_NATIVE_DOMAIN_REJECTED',error=str(error),no_model_or_quality_observed=True)
                    if rejection is None:
                        h.save(folder/'clock.json',clock);reference=h.original_reference(raw[current]);h.save(folder/'reference.json',reference)
                        try:h.validate_reference_domain(clock,reference)
                        except h.NativeDomainRejected as error:rejection=dict(video_id=current,reason='EXPLICIT_ORIGINAL_REFERENCE_NATIVE_DOMAIN_REJECTED',error=str(error),no_model_or_quality_observed=True,original_endpoints_changed=False)
                        if rejection is None:native04.validate_original_origin(clock);native01.native64_windows(clock)
                if rejection is not None:
                    rejected.append(rejection);h.save(folder/'source_rejection.json',rejection)
                    require(reserve_index<len(rows),'Exactly two engineering reserves exhausted; stop')
                    row=rows[reserve_index];reserve_index+=1;continue
                accepted.append(dict(video_id=current,slot=slot,group='confirm',media=receipt,clock_path=str(folder/'clock.json'),clock_sha256=h.sha(folder/'clock.json'),
                    reference_path=str(folder/'reference.json'),reference_sha256=h.sha(folder/'reference.json')))
                h.save(output/('accepted_slot_%02d.json'%slot),accepted[-1]);print('Accepted role first fresh native source '+current,flush=True);break
        require(len(accepted)==len({x['video_id'] for x in accepted})==4,'Four complete distinct sources required')
        h.save(output/'completion.json',dict(status='PASS_ROLE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU',group='confirm',accepted=accepted,rejected=rejected,
            registration_sha256=h.sha(root/'media_registration.json'),source_registration_ref=dict(path=str(root/'media_registration.json'),sha256=h.sha(root/'media_registration.json')),
            dev_selection_ref=reg['development_selection_ref'],dev_result_ref=reg['development_result_ref'],source_candidates_ref=reg['source_candidates_ref'],
            protocol_sha256=reg['protocol_ref']['sha256'],reserved_bytes_counted=reserved,actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'],
            maximum_media_pool_bytes=POOL,prior_actual_media_count=18,prior_actual_media_bytes=sum(x['bytes'] for x in prior),native_clock_measurements_started=measured,
            original_labels_unmodified=True,reference_scope=h.SCOPE,windows_video_body_bytes=0,original_annotation_downloads_repeated=0,
            successful_media_and_clocks_repeated=0,actual_new_model_calls=0,new_RGB_or_processor_calls=0,CPU_only=True,GPU_admitted=False,production_admitted=False,utc=h.utc()))
        h.save(root/'reference_completion_confirm.json',dict(path=str(output/'completion.json'),sha256=h.sha(output/'completion.json')))
    except BaseException as error:
        text,trace=repr(error),traceback.format_exc()
        for route in routes.values():
            if route.get('publisher_redirect_url'):text=text.replace(route['publisher_redirect_url'],'<PUBLISHER_CDN>');trace=trace.replace(route['publisher_redirect_url'],'<PUBLISHER_CDN>')
        h.save(output/'failure.json',dict(current=current,accepted=accepted,rejected=rejected,error=text,traceback=trace,reserved_bytes_counted=reserved,
            actual_new_media_payload_bytes=transfer['actual_new_media_payload_bytes'],successful_media_and_clocks_must_not_repeat=True,implicit_resume=False,actual_new_model_calls=0));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);args=parser.parse_args();main(args.root)
