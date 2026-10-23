"""All426 first CPU native64 inputs in existing Linux tmpfs, not the nearly full SSD."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import importlib.util
from fractions import Fraction
from pathlib import Path
import shutil
import uuid

from routing_production60_common import ROOT,ADMISSION,WORK,ENGINEERING,SPORT,read,ref,save,checked,activate_i3d


def memory_available():
    lines=Path('/proc/meminfo').read_text().splitlines()
    return next(int(line.split()[1])*1024 for line in lines if line.startswith('MemAvailable:'))


def renderer():
    activate_i3d()
    path=SPORT/'code/pilot15_prepare.py'
    specification=importlib.util.spec_from_file_location('_frozen_sport_RGB_renderer60',path)
    module=importlib.util.module_from_spec(specification);specification.loader.exec_module(module)
    return module,path


def project_clock(record, original, folder):
    origin=Fraction(original['first_original_pts_exact'])
    raw=original['original_exact_pts']
    if [Fraction(p) for p in raw]!=[Fraction(p)+origin for p in original['normalized_exact_pts']]:
        raise ValueError('Exact source clock projection differs')
    path=folder/'projected_clock.json'
    save(path,dict(PTS=raw,first_PTS_exact=str(origin),native_frames=len(raw),
        physical_end_exact=str(Fraction(original['physical_end_exact'])+origin),
        width=record['width'],height=record['height'],no_new_native_measurement=True,
        inherited_native_terminal_scope='Accepted original full PTS and positive packet/frame duration'))
    return ref(path)


def main():
    os.umask(0o077)
    registration=read(ROOT/'registration.json');assets=read(checked(registration['assets']))
    clocks=read(checked(assets['clocks']))
    total=assets['total_I3D_cells']*8*224*224*3
    max_geometry=max(s['width']*s['height']*3 for s in assets['sources'])
    required=total+64*max_geometry+len(assets['sources'])*65536
    available=memory_available();tmpfree=shutil.disk_usage('/dev/shm').free
    if required>available or required>tmpfree:
        raise RuntimeError('Actual full input-byte requirement exceeds existing tmpfs/availableRAM; no mount/service changes or precision fallback')
    cache=Path('/dev/shm')/('aic_routing60_'+uuid.uuid4().hex)
    cache.mkdir(mode=0o700);(cache/'inputs').mkdir(mode=0o700)
    save(ROOT/'RAM_cache_registration.json',dict(path=str(cache),owner_uid=os.getuid(),existing_mount='/dev/shm',
        expected_RGB_bytes=total,conservative_required_bytes=required,
        before_tmpfs_free=tmpfree,before_RAM_available=available,
        no_mount_or_network_service_changes=True,private_directory_mode='0700',
        all_inputs_first_CPU_before_GPU=True,ephemeral_after_complete_output_QA=True,
        original_media_and_durable_proofs_outputs_preserved=True))
    module,source=renderer();module.ROOT=cache
    (ROOT/'CPU').mkdir();accepted=[]
    for record in assets['sources']:
        sid=record['video_id'];folder=ROOT/'CPU'/sid;folder.mkdir()
        native=project_clock(record,clocks[sid],folder)
        media=dict(path=record['path'],bytes=record['bytes'],sha256=record['source_sha256'])
        required_source=record['RGB_I3D_native64_cells']*8*224*224*3
        if required_source>shutil.disk_usage(cache).free:raise RuntimeError('Shared tmpfs capacity changed; retain accepted inputs, no destructive fallback')
        raw=module.render(dict(source=sid,media=media,clock=native))
        receipt=read(checked(raw))
        if receipt['native_frames']!=record['native_frames'] or receipt['cells']!=record['RGB_I3D_native64_cells']:
            raise ValueError('First actual formal I3D cell/native count differs')
        durable=dict(receipt,video_id=sid,original_clock=assets['clocks'],projected_clock=native,
            original_renderer=ref(source),RAM_cache_ephemeral=True,not_training_or_labeling=True)
        save(folder/'input_acceptance.json',durable);accepted.append(ref(folder/'input_acceptance.json'))
        print('ROUTE426_CPU_ACCEPTED',len(accepted),426,flush=True)
    if len(accepted)!=426:raise ValueError('All426 first CPU inputs required')
    save(ROOT/'CPU_completion.json',dict(state='PASS_ALL426_FIRST_NATIVE64_RGB_INPUTS',accepted=accepted,
        cells=assets['total_I3D_cells'],native_frames=assets['total_native_frames'],
        RAM_cache=ref(ROOT/'RAM_cache_registration.json'),CPU_only=True,new_model_calls=0))


if __name__=='__main__':main()
