"""Only registered missing native64 primary inputs and their first CPU QA."""
import argparse
from fractions import Fraction as F
import hashlib
import os
from pathlib import Path
import traceback

import facts_common as io
from registration import registration, metadata, ref
from native import capacity, decode_union_once, mapping_tensors, tensor_signature
from adoption import adopt


def prepare(root):
    io.host(cpu=True); reg = registration(root); sources, clocks, views, _ = metadata(root,reg)
    sources_by_id = {s['video_id']:s for s in sources}; view_by_id={v['case_id']:v for v in views}
    adopted=[]
    for row in reg['execution_plan']:
        if row['mode']=='ADOPT':
            view=view_by_id[row['case_id']]; adopted.append(adopt(row,view,sources_by_id[view['source_name']],clocks[view['source_name']],reg['required_files']))
    output=root/'inputs_01';output.mkdir(parents=True,exist_ok=False)
    io.save(output/'launch_claim.json',dict(pid=os.getpid(),utc=io.utc(),registration_ref=ref(root/'positive_fixed40_registration.json'),
        original_clock_measurements=0,adopted_successful_calls=len(adopted),actual_new_primary_count=reg['gpu_budget']['max_actual_calls'],new_model_calls=0))
    current=None;entries=[];completed=[]
    try:
        import numpy as np
        import torch
        from PIL import Image
        runtime,processor=io.cpu_processor()
        requested={r['case_id'] for r in reg['execution_plan'] if r['mode']=='NEW'}
        for source in sources:
            subset=[v for v in views if v['source_name']==source['video_id'] and v['case_id'] in requested]
            if not subset:continue
            folder=output/source['case_id'];folder.mkdir(exist_ok=False)
            wanted={i for v in subset for i in v['source_frame_ordinals']}
            io.save(folder/'capacity_before_union.json',capacity(folder,source,len(wanted),len(subset),processor,reg['capacity_contract']))
            pixels=decode_union_once(source,clocks[source['video_id']],wanted,folder)
            for index,view in enumerate(subset):
                current=view['case_id'];window=folder/current;window.mkdir(exist_ok=False)
                bound=capacity(folder,source,0,len(subset)-index,processor,reg['capacity_contract']);images=[]
                for ordinal in view['source_frame_ordinals']:
                    item=pixels[ordinal];io.checked(item['path'],item['sha256'])
                    with Image.open(item['path']) as image:image.load();images.append(np.asarray(image).copy())
                rgb=np.stack(images);del images
                frames=window/'frames.npz'
                with frames.open('xb') as stream:np.savez_compressed(stream,rgb=rgb);stream.flush();os.fsync(stream.fileno())
                clock=clocks[source['video_id']]
                meta=dict(view,group='facts',source_path=source['source_path'],source_key=source['source_key'],
                    source_group=source['source_group'],width=source['width'],height=source['height'],
                    fps_num=source['fps_num'],fps_den=source['fps_den'],source_total_frames=source['n_frames'],
                    all_source_exact_pts=clock['original_exact_pts'],physical_end_exact=clock['physical_end_exact'],
                    original_clock_path=source['clock_path'],original_clock_sha256=source['clock_sha256'],
                    frame_array_path=str(frames),frame_array_sha256=io.sha(frames),
                    pixel_sha256=[pixels[i]['pixel_sha256'] for i in view['source_frame_ordinals']],
                    audio_observed=False,reference_available_to_inference=False,reference_labels_used_for_sampling=False,
                    view_selection_scope='FIXED_KNOWN_FACT_GEOMETRY_ONLY',recipe='POSITIVE_B0_UPPER_BOUND_ONLY')
                io.validate_native(meta);path=window/'input.json';io.save(path,meta)
                encoded,evidence=runtime.encode(processor,meta,(rgb,meta['source_frame_ordinals'],meta['sample_exact_pts']),F(meta['window_start']),runtime.EMPTY_PROMPT)
                io.save(window/'encode_evidence.json',evidence);encoded=mapping_tensors(encoded)
                cache=window/'encoded_tensors.pt.gz';io.save_cache(cache,encoded);restored=io.load_cache(cache)
                geometry=bound['geometry']
                io.require(encoded['video_grid_thw'].tolist()==[geometry['video_grid_thw']] and
                    list(encoded['pixel_values_videos'].shape)==geometry['pixel_values_shape'] and
                    encoded['pixel_values_videos'].dtype==torch.float32 and
                    tensor_signature(encoded)==tensor_signature(restored) and 0<int(encoded['input_ids'].shape[1])<=16384 and
                    evidence['prompt_sha256']==io.PROMPT_SHA and evidence['physical_frames']==64 and not torch.cuda.is_initialized(),
                    'Actual primary geometry/serialization/token/original prompt contract failed')
                proof=window/'proof.json';io.save(proof,dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT',case_id=current,
                    source_name=meta['source_name'],group='facts',input_path=str(path),input_sha256=io.sha(path),
                    encoded_tensor_path=str(cache),encoded_tensor_sha256=io.sha(cache),input_tokens=int(encoded['input_ids'].shape[1]),
                    input_evidence=evidence,full_serialization_signature=tensor_signature(encoded),CPU_only=True,CUDA_initialized=False,
                    primary_processor_calls=1,new_model_calls=0))
                entries.append(dict(case_id=current,source_name=meta['source_name'],input_path=str(path),input_sha256=io.sha(path),proof_path=str(proof),proof_sha256=io.sha(proof)))
                del encoded,restored,rgb
            completed.append(source['case_id'])
        # Match immutable registration order, not incidental source loop order.
        by_id={entry['case_id']:entry for entry in entries};ordered=[by_id[row['case_id']] for row in reg['execution_plan'] if row['mode']=='NEW']
        io.require(len(ordered)==len(entries)==reg['gpu_budget']['max_actual_calls'],'Complete exact NEW input denominator required')
        io.save(output/'completion.json',dict(status='PASS_POSITIVE_FIXED40_NEW_PRIMARY_INPUTS_NOT_GPU',group='facts',entries=ordered,
            adopted=adopted,CPU_only=True,CUDA_initialized=False,new_model_calls=0,primary_processor_calls=len(entries),
            source_RGB_decode_passes=len(completed),original_clock_measurements=0))
    except BaseException as error:
        io.save(output/'failure.json',dict(current=current,successful_entries=entries,error=repr(error),traceback=traceback.format_exc(),
            preserve_all_success=True,no_automatic_retry=True,no_UNKNOWN_or_EMPTY_fallback=True));raise


def first_qa(root):
    io.host(cpu=True);reg=registration(root);sources,clocks,views,_=metadata(root,reg)
    source_by_id={s['video_id']:s for s in sources};view_by_id={v['case_id']:v for v in views}
    primary=root/'inputs_01';complete=io.read(primary/'completion.json')
    io.require(complete['status']=='PASS_POSITIVE_FIXED40_NEW_PRIMARY_INPUTS_NOT_GPU' and io.read(primary/'launch_claim.json')['pid']!=os.getpid(),
        'Complete actual primary and independent first-QA process required')
    output=root/'first_input_qa_01';output.mkdir(exist_ok=False);proofs=[];entries=[];current=None
    io.save(output/'launch_claim.json',dict(pid=os.getpid(),utc=io.utc(),first_input_QA_before_GPU=True,CPU_only=True,new_model_calls=0))
    files=dict(reg['required_files'])
    def add(path,digest=None):
        path=io.checked(path,digest);value=io.sha(path);io.require(str(path) not in files or files[str(path)]==value,'Previously frozen input changed')
        files[str(path)]=value;return path
    try:
        import numpy as np
        import torch
        from PIL import Image
        runtime,processor=io.cpu_processor()
        for entry in complete['entries']:
            current=entry['case_id'];meta=io.read(add(entry['input_path'],entry['input_sha256']));proof=io.read(add(entry['proof_path'],entry['proof_sha256']))
            source=source_by_id[meta['source_name']];view=view_by_id[current];io.validate_native(meta)
            io.require(all(meta[k]==view[k] for k in view) and proof['input_sha256']==entry['input_sha256'],'New input changed from original audited geometry')
            observation=capacity(output,source,0,1,processor,reg['capacity_contract']);io.save(output/(current+'.capacity.json'),observation)
            with np.load(add(meta['frame_array_path'],meta['frame_array_sha256']),allow_pickle=False) as archive:
                io.require(set(archive.files)=={'rgb'},'Actual NPZ members differ');rgb=archive['rgb']
            union=io.read(add(primary/source['case_id']/'rgb_union.json'));by_ordinal={p['ordinal']:p for p in union['items']}
            io.require(union['actual_new_RGB_decode_passes']==1 and union['source_sha256']==source['source_sha256'] and
                union['original_clock_sha256']==source['clock_sha256'] and
                [hashlib.sha256(image.tobytes()).hexdigest() for image in rgb]==meta['pixel_sha256'],'Actual original RGB/clock identity differs')
            for ordinal,image in zip(meta['source_frame_ordinals'],rgb):
                item=by_ordinal[ordinal];path=add(item['path'],item['sha256'])
                io.require(F(item['exact_pts'])==F(clocks[meta['source_name']]['original_exact_pts'][ordinal]),'PNG/native timestamp differs')
                with Image.open(path) as png:io.require(png.mode=='RGB' and np.array_equal(np.asarray(png),image),'Independent PNG/NPZ original bits differ')
            encoded,evidence=runtime.encode(processor,meta,(rgb,meta['source_frame_ordinals'],meta['sample_exact_pts']),F(meta['window_start']),runtime.EMPTY_PROMPT)
            evidence_path=output/(current+'.encode_evidence.json');io.save(evidence_path,evidence);add(evidence_path)
            cache=io.load_cache(add(proof['encoded_tensor_path'],proof['encoded_tensor_sha256']))
            geometry=observation['geometry']
            io.require(evidence==proof['input_evidence'] and tensor_signature(encoded)==tensor_signature(cache)==proof['full_serialization_signature'] and
                encoded['video_grid_thw'].tolist()==[geometry['video_grid_thw']] and
                list(encoded['pixel_values_videos'].shape)==geometry['pixel_values_shape'] and
                all(torch.equal(encoded[k].contiguous().reshape(-1).view(torch.uint8),cache[k].contiguous().reshape(-1).view(torch.uint8)) for k in cache),
                'Actual first independent native/processor/cache input QA failed')
            path=output/(current+'.json');io.save(path,dict(status='PASS_FIRST_INDEPENDENT_POSITIVE_FIXED40_INPUT_QA_PRE_GPU',case_id=current,
                group='facts',input_evidence=evidence,input_sha256=entry['input_sha256'],primary_proof_sha256=entry['proof_sha256'],
                CPU_only=True,CUDA_initialized=False,vision_processor_calls=1,media_decodes=0,new_model_calls=0));add(path)
            accepted=output/(current+'.accepted_input.json');io.save(accepted,dict(proof,first_input_QA_path=str(path),first_input_QA_sha256=io.sha(path)));add(accepted)
            entries.append(dict(entry,proof_path=str(accepted),proof_sha256=io.sha(accepted)));proofs.append(dict(case_id=current,proof_path=str(path),proof_sha256=io.sha(path)))
            del encoded,cache,rgb
        io.require(len(entries)==reg['gpu_budget']['max_actual_calls'] and not torch.cuda.is_initialized(),'All NEW inputs need actual first independent QA before GPU')
        io.save(output/'completion.json',dict(status='PASS_POSITIVE_FIXED40_ALL_NEW_INPUTS_FIRST_QA_PRE_GPU',group='facts',calls=len(proofs),proofs=proofs,
            CPU_only=True,CUDA_initialized=False,new_model_calls=0))
        cpu=root/'cpu_acceptance.json';io.save(cpu,dict(status='PASS_POSITIVE_FIXED40_ALL_NEW_INPUTS_FIRST_QA_PRE_GPU',group='facts',entries=entries,
            adopted=complete['adopted'],first_input_QA_calls=len(proofs),first_input_QA_completion_ref=ref(output/'completion.json'),
            CPU_only=True,CUDA_initialized=False,new_model_calls=0));add(cpu)
        add(output/'completion.json');add(output/'launch_claim.json');add(primary/'completion.json');add(primary/'launch_claim.json');add(root/'positive_fixed40_registration.json')
        for path in output.glob('*.capacity.json'):add(path)
        io.save(root/'source_lock_B0.json',dict(files=files,group='facts',stage='B0',utc=io.utc()))
    except BaseException as error:
        io.save(output/'failure.json',dict(current=current,successful_proofs=proofs,error=repr(error),traceback=traceback.format_exc(),
            preserve_all_success=True,no_automatic_retry=True,no_UNKNOWN_or_EMPTY_fallback=True));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('prepare','first_qa'));parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';globals()[args.stage](io.root_path(args.root))
