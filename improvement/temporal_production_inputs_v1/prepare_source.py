"""Future admitted source-serial new materialization; never starts a model."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import resource
import time

import tp_io as io
from tp_contract import compare_clock,digest,materialized_request,measured_clock,require


def load_plan(reg):
    completion=io.read(io.BASE/'plan_01/completion.json')
    path=io.BASE/'plan_01/full_plan.json'
    require(completion['full_plan_sha256']==io.sha(path),'Whole frozen request/consumer table changed')
    require(completion['registration_path']==reg['_registration_path'] and
        completion['registration_sha256']==reg['_registration_sha256'],'Original plan/control registration changed')
    return io.read(path),completion


def initialize(reg,path):
    io.actual_permission(reg)
    plan,completion=load_plan(reg)
    cachebase=Path(reg['cache_root']).resolve()
    require(cachebase.parent==io.CAMPAIGN and cachebase.name.startswith('production_stream_v'), 'Independent critic-approved cache root required')
    lib=io.libraries(reg)
    policy=dict(reg['cache_policy'],root=str(cachebase),frozen_RGB_leases={key:
        dict(rgb_relative=row['rgb_relative'],consumers=row['consumers']) for key,row in plan['RGB_groups'].items()})
    require(policy['input_storage_codec']=='PIXEL_UINT8_BIT_LUT_V1','Exact LUT with original-gzip fallback policy required')
    store=lib['cache'].LeaseStore.create(cachebase,plan['consumers'],policy)
    store.write_metadata('permanent/proofs/global_source_request_lock.json',dict(
        control_registration_path=str(path),control_registration_sha256=io.sha(path),
        whole_plan_path=str(io.BASE/'plan_01/full_plan.json'),whole_plan_sha256=completion['full_plan_sha256'],
        sources=[dict(source_id=source['source_id'],source_sha256=source['source_sha256'],source_path=source['source_path'],
                      original_clock_ref=source['original_clock_ref']) for source in plan['sources']],
        all_requests=plan['requests'],all_consumers=plan['consumers'],old_spatial_field_refs=plan['old_spatial_field_refs'],
        selected_uniform_development_role_ref=reg['selected_uniform_development_role_ref'],
        immutable_request_membership=True,source_media_and_space_fields_never_modified=True))
    io.save(io.BASE/'cache_initialization.json',dict(cache_root=str(cachebase),policy_sha256=io.sha(cachebase/'policy.json'),
        control_registration_path=str(path.resolve()),control_registration_sha256=io.sha(path),
        frozen_consumers_ref=store.frozen_ref,whole_plan_sha256=completion['full_plan_sha256'],model_calls=0,processor_calls=0,media_decodes=0))


def capacity(store,source,requests,groups,processor):
    union=set(i for row in groups.values() for i in row['source_frame_ordinals'])
    rgb=len(union)*source['width']*source['height']*3
    one=64*source['width']*source['height']*3
    size=processor.video_processor.size
    require(set(size)=={'shortest_edge','longest_edge'},'Actual frozen processor total-video size missing')
    tensor_bound=int(size['longest_edge'])*3*4+16384*16+65536
    permanent=len(requests)*(tensor_bound+tensor_bound//1000+65536)
    staging=len(groups)*(one+one//1000+65536)
    transient=4*tensor_bound+2*one
    result=store.capacity(permanent,staging,transient)
    current=io.snapshot();memory=rgb+2*one+4*tensor_bound
    require(result['status']!='STOP_RETAIN_ALL' and current['mem_available_bytes']>=memory,
        'Current bytes cannot cover next complete source; STOP retains all canonical/staging, no precision or member changes')
    return dict(disk=result,memory=current,required_memory_bytes=memory,source_union_RGB_bytes=rgb,
        tensor_bound_bytes=tensor_bound,remaining_source_permanent_bound=permanent,
        model_grid_not_assumed=True,compression_ratio_not_used_for_admission=True)


def decode_once(source,wanted):
    """One new AV pass measures every original PTS and collects union RGB."""
    import av
    raw,durations,images=[],[],{}
    geometry=None
    with av.open(source['source_path']) as container:
        require(len(container.streams.video)==1,'Ambiguous source video stream')
        stream=container.streams.video[0];stream.thread_count=1
        require(stream.time_base is not None,'Source native time base missing')
        info=dict(index=stream.index,time_base=str(F(stream.time_base)),
            average_rate=str(F(stream.average_rate)) if stream.average_rate is not None else None)
        for index,frame in enumerate(container.decode(stream)):
            require(frame.pts is not None and frame.time_base is not None,'New native frame missing exact PTS')
            point=F(frame.pts)*F(frame.time_base)
            require(not raw or point>raw[-1],'New full native clock is not chronological')
            shape=(frame.width,frame.height)
            if geometry is None:geometry=shape
            require(shape==geometry,'Native geometry changed during source materialization')
            raw.append(point)
            value=getattr(frame,'duration',None)
            durations.append(F(value)*F(frame.time_base) if value is not None else None)
            if index in wanted:images[index]=frame.to_ndarray(format='rgb24')
    # Preserve a complete actual PTS measurement even when last duration later
    # fails admission. Never turn missing duration into guessed N/fps duration.
    return dict(original_exact_pts=list(map(str,raw)),
        native_duration_by_ordinal={str(i):str(value) if value is not None else None for i,value in enumerate(durations)},
        geometry=list(geometry) if geometry else None,stream=info),images


def prepare(reg,source_id):
    io.host();io.actual_permission(reg)
    lib=io.libraries(reg,cpu=True)
    plan,completion=load_plan(reg)
    init=io.read(io.BASE/'cache_initialization.json')
    require(init['whole_plan_sha256']==completion['full_plan_sha256'] and init['cache_root']==reg['cache_root'], 'Cache/control/source lock changed')
    store=lib['cache'].LeaseStore(reg['cache_root'])
    require(io.sha(Path(reg['cache_root'])/'policy.json')==init['policy_sha256'] and store.frozen_ref==init['frozen_consumers_ref'],
            'Permanent global consumer/policy lock changed')
    source=next(source for source in plan['sources'] if source['source_id']==source_id)
    rows=[row for row in plan['requests'] if row['source_id']==source_id]
    model_rows=[row for row in rows if row['execution']=='MODEL']
    groups={key:row for key,row in plan['RGB_groups'].items() if row['source_id']==source_id}
    done_rel='permanent/proofs/source_'+source_id+'_completion.json'
    require(not store.path(done_rel,'permanent').exists() and
            not store.path('permanent/proofs/source_'+source_id+'_launch.json','permanent').exists(),
            'Already prepared/attempted source; preserve success and require explicit independent recovery')
    require(Path(source['source_path']).resolve().is_relative_to(io.MEDIA_ROOT) and
            Path(source['source_path']).stat().st_size==source['source_bytes'] and io.sha(source['source_path'])==source['source_sha256'],
            'Immutable original source bytes/path changed')
    io.bound(source['original_clock_ref'],(io.RUN,))
    receipt=capacity(store,source,model_rows,groups,lib['processor'])
    prepare_pid=os.getpid();started=time.monotonic();accepted=[];leases={};stage='NEW_NATIVE_CLOCK_AND_RGB_UNION'
    store.write_metadata('permanent/proofs/source_'+source_id+'_launch.json',dict(prepare_pid=prepare_pid,
        source_id=source_id,whole_plan_sha256=completion['full_plan_sha256'],capacity=receipt,
        new_native_RGB_materialization_intended=True,old_successful_clock_not_rerun_or_rewritten=True,model_calls=0))
    try:
        wanted={i for row in groups.values() for i in row['source_frame_ordinals']}
        measured,images=decode_once(source,wanted)
        store.write_metadata('permanent/proofs/native_measurement_'+source_id+'.json',dict(
            status='COMPLETE_NEW_NATIVE_MEASUREMENT_BEFORE_DOMAIN_ADMISSION',source_id=source_id,
            source_sha256=source['source_sha256'],measurement=measured,new_native_RGB_materialization_decodes=1,
            original_clock_ref=source['original_clock_ref'],old_clock_overwritten=False))
        clock=measured_clock(source,list(map(F,measured['original_exact_pts'])),
            [F(measured['native_duration_by_ordinal'][str(i)]) if measured['native_duration_by_ordinal'][str(i)] is not None else None
             for i in range(len(measured['original_exact_pts']))],measured['geometry'],measured['stream'])
        clock_ref=store.write_metadata('permanent/proofs/clock_'+source_id+'.json',dict(
            status='NEW_COMPLETE_NATIVE_MEASUREMENT_NOT_OLD_CLOCK_OVERWRITE',clock=clock,original_clock_ref=source['original_clock_ref']))
        compare_clock(source,clock)
        require(set(images)==wanted,'New source RGB union did not recover every frozen native frame')
        import numpy as np
        stage='NEW_EPHEMERAL_RGB_GROUPS'
        metadata_by_group={}
        for key,group in groups.items():
            arrays=np.stack([images[i] for i in group['source_frame_ordinals']])
            require(arrays.dtype==np.uint8 and arrays.shape==(64,source['height'],source['width'],3),'New actual RGB dtype/shape differs')
            path=store.path(group['rgb_relative'],'staging')
            with path.open('xb') as stream:np.savez_compressed(stream,rgb=arrays)
            pixels=[hashlib.sha256(image.tobytes()).hexdigest() for image in arrays]
            metadata=dict(frame_array_path=str(path),frame_array_sha256=io.sha(path),pixel_sha256=pixels,
                source_sha256=source['source_sha256'],source_frame_ordinals=group['source_frame_ordinals'],sample_exact_pts=group['sample_exact_pts'])
            leases[key]=store.register_rgb(key,group['rgb_relative'],group['consumers'],metadata)
            metadata_by_group[key]=metadata
            del arrays
        del images
        stage='FIRST_NEW_PROCESSOR_AND_PERMANENT_EXACT_CACHE'
        import torch
        for row in rows:
            rid=row['request_id']
            if row['execution']!='MODEL':
                store.write_metadata('permanent/proofs/'+rid+'_structural_unknown.json',row['structural_endpoint_result'])
                continue
            request_started=time.monotonic()
            groupmeta=metadata_by_group[row['lease_id']]
            with np.load(groupmeta['frame_array_path'],allow_pickle=False) as archive:arrays=archive['rgb']
            if row['kind']=='VERIFY':
                require(groupmeta['pixel_sha256']==row['original_frame_pixel_sha256'],
                        'New AV coarse RGB differs from frozen original pixel evidence; no decode/colour fallback')
            meta=materialized_request(source,row,clock,lib['boundary'],lib['continuity'],lib['verify'],clock['native_duration_by_ordinal'])
            meta.update(groupmeta,case_id=rid,native_duration_by_ordinal=clock['native_duration_by_ordinal'],
                new_clock_ref=clock_ref,original_clock_ref=source['original_clock_ref'],source_id=source_id,
                provenance=dict(new_native_RGB_materialization=True,old_RGB_or_tensor_cache_reused=False,
                    prepare_pid=prepare_pid,source_ref=dict(path=source['source_path'],sha256=source['source_sha256']),
                    original_coarse_window_sha256=row['accepted_window_sha256'],old_spatial_field_refs=plan['old_spatial_field_refs']))
            encoded,evidence=lib['runtime'].encode(lib['processor'],meta,
                (arrays,meta['source_frame_ordinals'],meta['sample_exact_pts']),F(meta['window_start']),meta['prompt'])
            tokens=int(encoded['input_ids'].shape[1])
            require(tokens<=16384 and evidence['physical_frames']==64 and not torch.cuda.is_initialized(),'New actual token/native64/CPU gate failed')
            full=lib['cache'].signature(dict(encoded))
            actual_storage=sum({(tensor.untyped_storage().data_ptr(),tensor.untyped_storage().nbytes()):
                tensor.untyped_storage().nbytes() for tensor in encoded.values()}.values())
            actual_fit=store.capacity(actual_storage+actual_storage//1000+65536,0,actual_storage*4)
            require(actual_fit['status']!='STOP_RETAIN_ALL','Actual complete tensor/storage byte bound does not fit; retain all')
            identity=dict(source_sha256=source['source_sha256'],source_ordinals=meta['source_frame_ordinals'],exact_pts=meta['sample_exact_pts'],
                context_origin_exact=meta['window_start'],grid=encoded['video_grid_thw'].tolist(),
                processor_assets=lib['runtime_identity']['processor_assets'],preprocessing_code=reg['required_code_files'])
            visual=[key for key in encoded if key in lib['cache'].codec.VISUAL_KEYS]
            manifest_ref=store.save_input(rid,dict(encoded),visual,identity,meta)
            manifest=io.read(store.checked_ref(manifest_ref))
            tensor_refs=[manifest['private_ref']]+([manifest['visual_ref']] if manifest['visual_ref'] else [])
            proof_ref=store.write_metadata('permanent/proofs/'+rid+'_CPU_input.json',dict(
                status='PASS_NEW_FORMAL_NATIVE64_CPU_INPUT_NOT_GPU_OR_QUALITY',consumer=rid,prepare_pid=prepare_pid,CPU_only=True,
                input_manifest_ref=manifest_ref,input_evidence=evidence,full_input_signature=full,input_tokens=tokens,
                RGB_lease_ref=leases[row['lease_id']],original_RGB_ref=store.ref(plan['RGB_groups'][row['lease_id']]['rgb_relative'],'staging'),
                processor_runtime_identity=lib['runtime_identity'],actual_storage_bytes=actual_storage,
                encoded_tensor_refs=tensor_refs,actual_reachable_encoded_bytes=sum(ref['bytes'] for ref in tensor_refs),
                request_wall_seconds=time.monotonic()-request_started,
                process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                actual_new_processor_encodes=1,new_model_calls=0,optimizer_updates=0,CPU_GPU_signature_verified=False,
                new_native_RGB_materialization=True,old_input_success_not_reexecuted=True))
            accepted.append(dict(consumer=rid,input_manifest_ref=manifest_ref,CPU_input_proof_ref=proof_ref,lease_id=row['lease_id']))
            del encoded,arrays
        store.write_metadata(done_rel,dict(status='PASS_COMPLETE_SOURCE_NEW_INPUTS_NOT_GPU_OR_QUALITY',source_id=source_id,
            consumers=accepted,new_clock_ref=clock_ref,RGB_lease_refs=leases,prepare_pid=prepare_pid,
            new_native_RGB_materialization_decodes=1,actual_new_processor_encodes=len(accepted),new_model_calls=0,
            wall_seconds=time.monotonic()-started,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            no_lease_release_performed=True,old_successes_or_space_fields_modified=False))
    except BaseException as error:
        store.write_metadata('permanent/proofs/source_'+source_id+'_failure.json',dict(status='FAILED_SOURCE_RETAIN_ALL_NEW_CANONICAL_AND_STAGING',
            source_id=source_id,stage=stage,error_type=type(error).__name__,error=str(error),successful_consumers=accepted,
            registered_new_RGB_leases=leases,new_model_calls=0,no_old_or_new_canonical_deleted=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('initialize','source'));parser.add_argument('--registration',required=True,type=Path)
    parser.add_argument('--source-id');args=parser.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';io.host();reg=io.registration(args.registration)
    if args.stage=='initialize':initialize(reg,args.registration)
    else:require(args.source_id is not None,'Frozen source ID required');prepare(reg,args.source_id)
