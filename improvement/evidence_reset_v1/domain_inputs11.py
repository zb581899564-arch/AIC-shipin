"""First new65K individual-image profile of retained VideoXum RGB caches.

No media decode/download, no old native64 video re-encoding, no model. Each
first processor result is durable before QA; success is losslessly coded once.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import time
import traceback


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def unpatchify_image(torch,pixels,h,w):
    if h%2 or w%2 or tuple(pixels.shape)!=(h*w,1536):raise ValueError('Actual even image grid/1536 patch channels required')
    return pixels.reshape(h//2,w//2,2,2,3,2,16,16).permute(4,5,0,2,6,1,3,7).reshape(3,2,h*16,w*16)


def context(root):
    N=Path(root).resolve(strict=True);R=N.parent;W=R.parent
    old=R/'relative_ranker06';trainer=module(old/'rank_train07.py','ranker07_inputs_contract11')
    _,_,api,old_protocol,common,manifest,Store,canonical,admission,accepted=trainer.context(old)
    reg=json.loads((N/'registration11.json').read_text());api.require(reg['code_ref']==api.ref(__file__),'Exact first new image-profile implementation')
    inv=api.loadref(reg['inventory_ref'],W);protocol=api.loadref(reg['protocol_ref'],W)
    api.require(inv['matched_sources_per_arm']==18 and inv['matched_pairs_per_arm']==36,'Frozen18source36pair domain control')
    return N,R,W,api,old_protocol,common,manifest,Store,reg,inv,protocol


def load_source11(source,api,workspace,torch,dictionary):
    frames=[];ordinals=[];grid=None
    for item in source['patch_chunks']:
        path=api.checked(item['cache_ref'],workspace)
        payload=torch.load(io.BytesIO(gzip.decompress(path.read_bytes())),map_location='cpu',weights_only=True)
        values=dictionary.unpack(payload);h,w=item['grid_hw']
        api.require(grid is None or grid==(h,w),'One actual geometric image grid per native source')
        grid=(h,w);frames.append(values['pixel_values_videos'].reshape(len(item['ordinals']),h*w,1536));ordinals.extend(item['ordinals'])
    api.require(ordinals==source['sample_ordinals']==sorted(set(ordinals)),'Native unique image ownership must remain ordered')
    return torch.cat(frames).contiguous(),grid,ordinals


def prepare(root):
    N,R,W,api,p,common,manifest,Store,reg,inv,protocol=context(root)
    import torch,numpy as np
    from PIL import Image
    from transformers import AutoProcessor
    from torchvision.transforms.v2 import functional as TVF
    from torchvision.transforms import InterpolationMode
    require=api.require;start=time.monotonic();store=Store(manifest,'check');dictionary=store._dictionary_helper()
    processor=AutoProcessor.from_pretrained(manifest['model_spec']['model_dir'],revision=manifest['model_spec']['revision'],local_files_only=True,trust_remote_code=False)
    expected=json.loads(Path(manifest['scopes']['check']['sources'][0]['patches'][0]['profile_ref']['path']).read_text())
    require(processor.image_processor.to_dict()==expected['processor_dict'] and expected['explicit_call_size']==dict(shortest_edge=65536,longest_edge=65536),'Same actual accepted65K image processor factory, no new synthetic image call')
    api.save(N/'processor_metadata11.json',dict(status='PASS_EXISTING_FACTORY_METADATA_IDENTITY_NOT_NEW_IMAGE_QA',
        original_profile_ref=api.ref(manifest['scopes']['check']['sources'][0]['patches'][0]['profile_ref']['path']),
        processor_dict=processor.image_processor.to_dict(),explicit_call_size=expected['explicit_call_size']))
    out=N/'inputs11';out.mkdir();source_dir=N/'sources11';source_dir.mkdir();case_refs={};sources=[];targets=[];new_images=0
    def event(name,**fields):
        with (N/'input_events11.jsonl').open('a') as f:f.write(json.dumps(dict(event=name,**fields),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def remaining():
        require(time.monotonic()-start<protocol['max_cpu_prepare_seconds'],'Bounded first new source image profile')
        size=sum(f.stat().st_size for f in N.rglob('*') if f.is_file())
        require(size<protocol['planned_output_bytes'],'New profile output budget exceeded; preserve all, no automatic cleanup')
    for source_index,selected in enumerate(inv['selected_VideoXum']):
        remaining();record=api.loadref(selected['record_ref'],W);sid=f'D{source_index:02d}';folder=source_dir/sid;folder.mkdir()
        clock=json.loads(api.checked(record['clock_ref'],W).read_text());pts=clock['original_exact_pts']
        canonical_clock=dict(source_sha256=record['source_sha256'],normalized_exact_pts=pts,physical_end_exact=clock['physical_end_exact'],
            last_frame_duration_exact=clock['last_frame_duration_exact'],original_clock_ref=record['clock_ref'],native_count=len(pts),shift_applied=False)
        api.save(folder/'clock11.json',canonical_clock)
        blocks={b['index']:b for b in record['blocks']};needed=set(record['overview_ordinals'])
        for pair in record['selected_pairs']:
            for index in [pair['left_block'],pair['right_block']]:needed.update(blocks[index]['native_observation_ordinals'])
        required=sorted(needed);catalog={v['ordinal']:v for v in record['sample_catalog']};rgb={}
        for wi,window in enumerate(record['cache_windows']):
            wanted=[o for o in required if catalog[o]['window']==wi]
            if not wanted:continue
            fp=Path(window['RGB_path']);actual=api.ref(fp)
            require(actual['sha256']==window['RGB_sha256'] and actual['bytes']==window['RGB_bytes'],'Adopt actual retained RGB bytes, no new decode')
            with np.load(fp,allow_pickle=False) as z:
                require(z.files==['rgb'],'Original native64 RGB array schema')
                arrays=z['rgb'];require(arrays.dtype==np.uint8 and arrays.ndim==4 and arrays.shape[-1]==3,'Original uint8 RGB frames')
                require(tuple(arrays.shape[1:3])==(clock['height'],clock['width']),'Native geometry unchanged')
                for o in wanted:
                    image=arrays[catalog[o]['offset']].copy()
                    require(hashlib.sha256(image.tobytes()).hexdigest()==catalog[o]['pixel_sha256'],'Retained actual native RGB pixel ownership')
                    rgb[o]=image
            event('RGB_CACHE_ADOPTED',source=sid,window=wi,actual_native_images=len(wanted))
        require(set(rgb)==needed,'All real unique Overview/Excerpt frames present without padding')
        chunks=[];common_grid=None
        for index,lo in enumerate(range(0,len(required),8)):
            remaining();ordinals=required[lo:lo+8];batch=[Image.fromarray(rgb[o]) for o in ordinals]
            primary=folder/'active_primary11.pt';require(not primary.exists(),'Unaccepted primary must be explicitly recovered, never re-encoded')
            pending_bytes=len(ordinals)*65536*6*(4+1)+1048576
            require(shutil.disk_usage(N).free>=pending_bytes,'Actual next primary+packed-cache working set cannot fit; preserve prior batches')
            event('BEGIN_FIRST_NEW_IMAGE_BATCH',source=sid,index=index,ordinals=ordinals)
            encoded=processor.image_processor(images=batch,return_tensors='pt',size=dict(shortest_edge=65536,longest_edge=65536))
            values={k:encoded[k].contiguous() for k in ['pixel_values','image_grid_thw']}
            # An incomplete new QA can adopt this exact result without any second processor call.
            with primary.open('xb') as f:torch.save(dict(values=values,ordinals=ordinals,source_sha256=record['source_sha256']),f);f.flush();os.fsync(f.fileno())
            grids=values['image_grid_thw'].tolist();require(len(grids)==len(ordinals),'One native image grid per real image')
            for j,(t,h,w) in enumerate(grids):
                require(t==1 and h%2==w%2==0 and (common_grid is None or common_grid==(h,w)),'Same-source native image geometry')
                common_grid=(h,w);pixels=values['pixel_values'][j*h*w:(j+1)*h*w]
                image=unpatchify_image(torch,pixels,h,w)
                require(torch.equal(image[:,0].view(torch.uint8),image[:,1].view(torch.uint8)),'Single-image temporal duplication exact')
                restored=((image[:,0]+1)*127.5).round().clamp(0,255).to(torch.uint8)
                original=torch.from_numpy(rgb[ordinals[j]]).permute(2,0,1).contiguous()
                resized=TVF.resize(original,size=[h*16,w*16],interpolation=InterpolationMode.BICUBIC,antialias=True)
                require(torch.equal(restored,resized),'Independent native RGB resize/channel/patch/order proof')
            payload,report=dictionary.validate_roundtrip(dict(pixel_values_videos=values['pixel_values'],image_grid_thw=values['image_grid_thw']))
            require(report['pixel_values_videos']['storage']=='PIXEL_UINT8_BIT_LUT_V1','No large original-tensor fallback or model quantization')
            buffer=io.BytesIO();torch.save(payload,buffer);data=gzip.compress(buffer.getvalue(),compresslevel=3)
            path=folder/(f'pixels11_{index:03d}.pt.gz')
            with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            reloaded=dictionary.unpack(torch.load(io.BytesIO(gzip.decompress(path.read_bytes())),map_location='cpu',weights_only=True))
            require(torch.equal(reloaded['pixel_values_videos'].view(torch.uint8),values['pixel_values'].view(torch.uint8)),'Durable packed cache preserves every FP32 model-input bit')
            chunk=dict(cache_ref=api.ref(path),ordinals=ordinals,grid_hw=list(common_grid),original_processor_signature=common.signature(values),
                profile='FIRST_NEW65K_INDIVIDUAL_IMAGE_NOT_OLD_NATIVE64_VIDEO',new_images=len(ordinals),first_independent_RGB_patch_QA=True,
                packed_roundtrip='ALL_FP32_BITS_EXACT',primary_mutable_working_buffer_deletable_after_exact_coding=True)
            api.save(folder/(f'pixels11_{index:03d}.json'),chunk);chunks.append(chunk);new_images+=len(ordinals)
            event('IMAGE_BATCH_ACCEPTED',source=sid,index=index,cache_ref=chunk['cache_ref'],new_images=len(ordinals))
            # Only this registered transient buffer is removed after its exact replacement is accepted.
            require(primary.resolve().is_relative_to(N),'Transient buffer must remain in this run')
            primary.unlink();del payload,reloaded,encoded,values,buffer
        source=dict(sid=sid,original_video_id=record['video_id'],source_sha256=record['source_sha256'],source_record_ref=selected['record_ref'],
            clock_ref=api.ref(folder/'clock11.json'),sample_ordinals=required,patch_chunks=chunks,grid_hw=list(common_grid),
            Overview_ordinals=record['overview_ordinals'],registered_novel_profile=True)
        source_path=folder/'source11.json';api.save(source_path,source);frames,grid,ordinals=load_source11(source,api,W,torch,dictionary)
        lookup={o:i for i,o in enumerate(ordinals)};overview=dict(role='Overview',cells=[lookup[o] for o in record['overview_ordinals']],origin_exact='0')
        for index in sorted({k for pair in record['selected_pairs'] for k in [pair['left_block'],pair['right_block']]}):
            block=dict(blocks[index]);block['observations']=[lookup[o] for o in block['native_observation_ordinals']]
            uid=f'train_{sid}_B{index:04d}'
            v,plan=api.build_pixels(torch,frames,grid,ordinals,pts,overview,block,sid,source['source_sha256'])
            store._helpers().independent_pixels(frames,grid,v,plan,ordinals,pts)
            prefix,text=api.build_text(processor,plan,v['video_grid_thw'],clock['physical_end_exact'],p);v.update(prefix)
            store._helpers().independent_text(processor,plan,v,text)
            pp=out/(uid+'.prefix.pt');torch.save(prefix,pp)
            require(all(torch.equal(prefix[k],torch.load(pp,map_location='cpu',weights_only=True)[k]) for k in prefix),'Exact first new prefix reload')
            case=dict(uid=uid,scope='train',sid=sid,block=block,plan=plan,text=text,source_sha256=source['source_sha256'],
                source_ref=api.ref(source_path),source_clock_ref=source['clock_ref'],prefix_ref=api.ref(pp),input_signature=common.signature(v),labels_in_text=False)
            cp=out/(uid+'.json');api.save(cp,case);case_refs[uid]=api.ref(cp);event('NATIVE_INPUT_ACCEPTED',uid=uid,case_ref=case_refs[uid])
        for pi,pair in enumerate(record['selected_pairs']):
            targets.append(dict(pair_id=f'train_{sid}_P{pi:02d}',source_id=sid,left=f'train_{sid}_B{pair["left_block"]:04d}',
                right=f'train_{sid}_B{pair["right_block"]:04d}',preference_left=pair['preference_left'],source_pair_count=2))
        sources.append(api.ref(source_path));event('SOURCE_ACCEPTED',sid=sid,source_ref=sources[-1]);del frames,rgb
    require(len(sources)==18 and len(case_refs)==72 and len(targets)==36,'All fixed18source/72cases/36pairs before GPU')
    api.save(N/'VideoXum_targets11.json',targets)
    result=dict(status='PASS_FIRST72_DOMAIN_FEATURE_INPUTS',case_refs=case_refs,source_refs=sources,training_target_ref=api.ref(N/'VideoXum_targets11.json'),
        real_sources=18,real_cases=72,actual_new_individual_image_encodings=new_images,new_media_decodes=0,
        old_native64_video_encodings_repeated=0,model_calls=0,seconds=time.monotonic()-start,registration_ref=api.ref(N/'registration11.json'))
    api.save(N/'input_acceptance11.json',result)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);args=a.parse_args()
    try:prepare(args.run_root)
    except BaseException:
        with (Path(args.run_root)/'failure_prepare11.json').open('x') as f:json.dump(dict(status='ACTUAL_FAILURE_RETAIN_PRIMARY_AND_ACCEPTED_CHUNKS_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()),f,indent=2)
        raise
