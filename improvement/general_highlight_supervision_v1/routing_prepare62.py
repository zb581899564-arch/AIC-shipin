"""Remaining329-or-fewer inputs; adopt97 successes and frozen baseline color-tag recipe."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import importlib.util
import shutil
import uuid
import numpy as np
import av
from fractions import Fraction

from routing_production60_common import ADMISSION,WORK,RUN,ENGINEERING,SPORT,read,ref,save,checked,activate_i3d

ROOT=ADMISSION/'routing_production62';OLD=ADMISSION/'routing_production60'


def resize(frame,source_sha,policy):
    from prepare_raw import resize_crop
    profile=policy['sources'].get(source_sha)
    if profile is None:return resize_crop(frame)
    keys=['color_trc','colorspace','color_primaries','color_range']
    if (frame.format.name!=profile['format'] or frame.width!=profile['width'] or frame.height!=profile['height']
            or any(getattr(frame,k)!=profile[k] for k in keys)):
        raise ValueError('Pre-existing SHA-pinned unsupported transfer metadata differs')
    original=frame.color_trc;scale=256/min(frame.width,frame.height)
    try:
        frame.color_trc=policy['transfer_tag_for_conversion']
        image=frame.reformat(width=round(frame.width*scale),height=round(frame.height*scale),format='rgb24',
            src_colorspace=policy['matrix'],dst_colorspace=policy['matrix']).to_ndarray()
    finally:frame.color_trc=original
    top=(image.shape[0]-224)//2;left=(image.shape[1]-224)//2
    result=image[top:top+224,left:left+224].copy()
    if result.shape!=(224,224,3) or result.dtype!=np.uint8:raise ValueError('Declared corrected RGB shape/dtype differs')
    return result


def render(record,clock_ref,cache,policy):
    from pilot15_common import native_cells
    clock=read(checked(clock_ref));pts=list(map(Fraction,clock['PTS']))
    media=dict(path=record['path'],bytes=record['bytes'],sha256=record['source_sha256']);checked(media)
    sid=record['video_id'];folder=cache/'inputs'/sid;folder.mkdir()
    bounds,samples,groups=native_cells(len(pts));np.save(folder/'groups.npy',groups,allow_pickle=False)
    path=folder/'rgb.npy';rgb=np.lib.format.open_memmap(path,mode='w+',dtype=np.uint8,shape=(len(bounds),8,224,224,3))
    wanted={}
    for group,indices in enumerate(samples):
        for slot,index in enumerate(indices):wanted.setdefault(int(index),[]).append((group,slot))
    observed=0;seen=set()
    with av.open(str(checked(media))) as container:
        stream=container.streams.video[0];stream.codec_context.thread_count=1
        for ordinal,frame in enumerate(container.decode(stream)):
            if ordinal>=len(pts) or Fraction(frame.pts)*frame.time_base!=pts[ordinal]:
                raise ValueError('Remaining input does not match accepted full native PTS')
            if ordinal in wanted:
                image=resize(frame,media['sha256'],policy)
                for group,slot in wanted[ordinal]:rgb[group,slot]=image
                seen.add(ordinal)
            observed+=1
    if observed!=len(pts) or seen!=set(wanted):raise ValueError('Incomplete first remaining source input')
    rgb.flush();del rgb
    result=dict(source=sid,video_id=sid,rgb=ref(path),groups=ref(folder/'groups.npy'),cells=len(bounds),native_frames=observed,
        exact_pts_sample=[[str(pts[i]) for i in row] for row in samples],accepted_clock_adopted=clock_ref,
        first_real_I3D_RGB_render=True,short_final_bin_pixel_repeats_only=True,no_label_padding=True,
        prior_best_source_color_policy_applied=media['sha256'] in policy['sources'],
        color_rule='Frozen original40.47 transfer-tag/matrix adaptation inside same short256/center224 geometry; no recovered gamma claim',
        RAM_cache_ephemeral=True,not_training_or_labeling=True)
    save(folder/'acceptance.json',result)
    return result


def main():
    os.umask(0o077);activate_i3d()
    # Import only the pure accepted clock projection and memory estimator, not an old launcher.
    from routing_production60_prepare import project_clock,memory_available
    reg=read(ROOT/'registration.json');assets=read(checked(reg['assets']));clocks=read(checked(assets['clocks']))
    policy=read(RUN/'b_score_aligned_package_v4/config.json')['source_color_repair']
    old={p.parent.name:ref(p) for p in (OLD/'CPU').glob('*/input_acceptance.json')}
    remaining=[r for r in assets['sources'] if r['video_id'] not in old]
    required=sum(r['RGB_I3D_native64_cells']*8*224*224*3 for r in remaining)+64*max(r['width']*r['height']*3 for r in remaining)
    if required>memory_available() or required>shutil.disk_usage('/dev/shm').free:
        raise RuntimeError('Actual remaining byte bound cannot fit current RAM/tmpfs; preserve97 accepted sources')
    cache=Path('/dev/shm')/('aic_routing62_'+uuid.uuid4().hex);cache.mkdir(mode=0o700);(cache/'inputs').mkdir(mode=0o700)
    save(ROOT/'RAM_cache_registration.json',dict(path=str(cache),owner_uid=os.getuid(),existing_mount='/dev/shm',
        adopted_RAM_root=read(OLD/'RAM_cache_registration.json')['path'],remaining_uncompressed_bound=required,
        actual_old_successes=len(old),private_directory_mode='0700',no_mount_service_or_network_change=True))
    (ROOT/'CPU').mkdir();accepted=[];adopted=[]
    for record in assets['sources']:
        sid=record['video_id']
        if sid in old:
            data=read(checked(old[sid]));checked(data['rgb']);checked(data['groups'])
            if data['native_frames']!=record['native_frames']:raise ValueError('Old accepted source count changed')
            accepted.append(old[sid]);adopted.append(sid)
        else:
            folder=ROOT/'CPU'/sid;folder.mkdir();clock_ref=project_clock(record,clocks[sid],folder)
            data=render(record,clock_ref,cache,policy)
            save(folder/'input_acceptance.json',data);accepted.append(ref(folder/'input_acceptance.json'))
        print('ROUTE426_CPU_REMAINING',len(accepted),426,flush=True)
    save(ROOT/'CPU_completion.json',dict(state='PASS_ALL426_FIRST_NATIVE64_RGB_INPUTS',accepted=accepted,
        cells=assets['total_I3D_cells'],native_frames=assets['total_native_frames'],adopted_successful_sources=adopted,
        new_remaining_sources=len(remaining),CPU_only=True,new_model_calls=0,
        input_color_repair_config=ref(RUN/'b_score_aligned_package_v4/config.json')))


if __name__=='__main__':main()
