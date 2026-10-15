"""Engineering-only reserve replacement before any reference prediction or score."""
import argparse
import json
import os
import socket
import subprocess
import sys
import traceback
from fractions import Fraction as F
from pathlib import Path

from sparse_stage_common_02 import BASE, check_file, read, save, sha, utc


def run_child(script,registration,log):
    with log.open('xb') as stream:
        result=subprocess.run([sys.executable,'-B',str(BASE/'code'/script),str(registration)],
                              stdout=stream,stderr=subprocess.STDOUT)
    return result.returncode


def main(registration_path):
    if socket.gethostname()!='inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES')!='':
        raise ValueError('CPU-only Linux engineering cohort required')
    reg_path=Path(registration_path);reg=read(reg_path)
    for name,digest in reg['required_files'].items():check_file(BASE/name,digest)
    out=BASE/reg['output_directory'];out.mkdir(exist_ok=False)
    save(out/'launch_claim.json',dict(pid=os.getpid(),utc=utc(),registration_sha256=sha(reg_path),new_model_calls=0))
    registry=read(BASE/'new_confirm_source_registration_01.json')
    initial=registry['selection']
    routes={row['video_id']:row for row in read(BASE/reg['routes_path'])}
    used={row['video_id'] for row in initial}
    reserves=iter([row for row in registry['ordered_engineering_reserves'] if row['video_id'] not in used and row['video_id'] in routes])
    original_refs={row['video_id']:row for row in read(BASE/'new_confirm_reference_pool_01.json')}
    accepted,replacements=[],[]
    current=None
    try:
        for slot,initial_row in enumerate(initial,1):
            row=dict(initial_row)
            while True:
                current=vid=row['video_id']
                if vid not in routes or vid in {x['video_id'] for x in accepted}:
                    raise ValueError('Duplicate or unavailable registered reserve candidate')
                candidate=out/f'{slot:02d}_{vid}'
                candidate.mkdir(exist_ok=False)
                selection_path=candidate/'selection.json'
                save(selection_path,dict(selection=[row],group=row['group'],original_slot=slot,
                    original_source_registration_sha256=reg['required_files']['new_confirm_source_registration_01.json']))
                ref=original_refs.get(vid)
                if ref is not None:
                    ref=dict(ref,group=row['group'],reuse_original_reference_export=True)
                else:
                    raise ValueError('Frozen original reference pool entry missing')
                ref_path=candidate/'references.json';save(ref_path,[ref])
                route_path=candidate/'routes.json';save(route_path,[routes[vid]])
                relative=lambda p:str(p.relative_to(BASE))
                required=dict(reg['required_files'])
                required.update({relative(selection_path):sha(selection_path),relative(ref_path):sha(ref_path),relative(route_path):sha(route_path)})
                media_reg_path=candidate/'media_registration.json'
                media_dir=relative(candidate/'media')
                media_reg=dict(required_files=required,selection_path=relative(selection_path),
                    routes_path=relative(route_path),routes_sha256=sha(route_path),output_directory=media_dir,
                    bytes=routes[vid]['bytes'],new_model_calls=0)
                save(media_reg_path,media_reg)
                code=run_child('download_confirm_media_02.py',media_reg_path,candidate/'download.log')
                if code:
                    # Network/service failure is not evidence for source replacement.
                    raise ValueError('Actual direct download failed; preserve partial, do not call this native source invalid')
                cpu_reg_path=candidate/'cpu_registration.json'
                cpu_dir=relative(candidate/'cpu')
                save(cpu_reg_path,dict(required_files=required,selection_path=relative(selection_path),
                    reference_path=relative(ref_path),media_directory=media_dir,
                    media_completion_sha256=sha(BASE/media_dir/'completion.json'),output_directory=cpu_dir,
                    native_frames=64,maximum_window_seconds=30,max_input_tokens=16384,
                    model_params_b='8.78245912',GPU_launch_admitted=False))
                code=run_child('prepare_confirm_cpu_02.py',cpu_reg_path,candidate/'cpu.log')
                if code:
                    failure=read(BASE/cpu_dir/'failure.json')
                    trace=failure['traceback']
                    endpoint_failure='Unmodified original manual interval exceeds actual native video presentation domain' in trace
                    origin_failure='Original zero origin unverified' in trace
                    if not(endpoint_failure or origin_failure) or failure['accepted_windows']:
                        raise ValueError('Unexpected CPU/processor failure; retain successful evidence, requires explicit engineering recovery')
                    failed=vid;next_row=next(reserves)
                    row={**next_row,'group':row['group']}
                    replacements.append(dict(slot=slot,failed_source=failed,replacement_source=row['video_id'],group=row['group'],
                         reason='Actual native original seconds admission failed; no model answer or metric examined',
                         failure_path=str(BASE/cpu_dir/'failure.json'),failure_sha256=sha(BASE/cpu_dir/'failure.json')))
                    continue
                complete=read(BASE/cpu_dir/'completion.json')
                accepted.append(dict(video_id=vid,group=row['group'],slot=slot,selection_path=str(selection_path),
                    reference_path=str(ref_path),reference_sha256=sha(ref_path),
                    media_completion_path=str(BASE/media_dir/'completion.json'),media_completion_sha256=sha(BASE/media_dir/'completion.json'),
                    cpu_completion_path=str(BASE/cpu_dir/'completion.json'),cpu_completion_sha256=sha(BASE/cpu_dir/'completion.json'),
                    proofs=complete['proofs']))
                save(out/f'accepted_slot_{slot:02d}.json',accepted[-1])
                print(json.dumps(dict(accepted_sources=len(accepted),video_id=vid,windows=complete['windows'])),flush=True)
                break
        if len(accepted)!=8 or any(x['group']!='confirm' for x in accepted):
            raise ValueError('Original fixed source and group denominator changed')
        save(out/'completion.json',dict(status='PASS_FRESH_CONFIRM8_NATIVE64_CPU_INPUTS_PENDING_INDEPENDENT_ADMISSION',
            utc=utc(),registration_sha256=sha(reg_path),sources=8,screen=0,confirm=8,
            windows=sum(len(x['proofs']) for x in accepted),accepted=accepted,replacements=replacements,
            source_selection_uses_predictions_or_quality_scores=False,new_model_calls=0,new_optimizer_updates=0,
            require_independent_all_input_review_frozen_source_lock_and_unique_wrapper=True))
    except BaseException:
        save(out/'failure.json',dict(status='FAILED_ENGINEERING_COHORT_KEEP_ALL_MEDIA_CLOCKS_RGB_CPU_PROOFS',
            utc=utc(),source=current,accepted_sources=accepted,replacements=replacements,
            traceback=traceback.format_exc(),new_model_calls=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('registration');main(parser.parse_args().registration)
