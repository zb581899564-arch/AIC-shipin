"""Correct the owned pre-stage Windows/Linux path serialization failure once."""
import json
from pathlib import Path

from deploy_confirm_cpu_02 import remote, REPORT, PY
from sparse_stage_common_02 import read, save, sha

REMOTE = '/home/inspur/aic_video_work/sparse_context_iteration_20261013_v1'


def main():
    if (REPORT/'new_confirm_CPU_launch_03.json').exists():
        raise ValueError('Corrected CPU launch already recorded; do not repeat')
    failure = read(REPORT/'CPU_launch02_path_failure_actual_01.json')
    if failure['actual_owned_commands'] or failure['correct_exists'] or failure['correct_stage_exists'] or failure['old_wrong_stage_exists']:
        raise ValueError('Original pre-stage failure evidence changed; inspect, never duplicate')
    transfer = read(REPORT/'new_confirm_CPU_launch_02.json')['transfer']
    script = '''import pathlib,hashlib,json,os,socket,subprocess,datetime
assert socket.gethostname()=='inspur-NP5570M5'
source=pathlib.Path('/home/inspur')/(chr(92)+'home'+chr(92)+'inspur'+chr(92)+'aic_video_work'+chr(92)+'sparse_context_iteration_20261013_v1')
target=pathlib.Path(REMOTE)
assert source.resolve().parent==pathlib.Path('/home/inspur') and target.resolve().parent==pathlib.Path('/home/inspur/aic_video_work')
assert source.is_dir() and not source.is_symlink() and not target.exists()
assert not (source/'new_confirm_CPU_02').exists(), 'No prior successful or partial media/CPU stage permitted'
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  argv=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\\0') if x]
  assert not any(x.endswith('/code/prepare_confirm8_cohort_02.py') or x.endswith('/code/download_confirm_media_02.py') or x.endswith('/code/prepare_confirm_cpu_02.py') for x in argv),'Actual old child still running'
 except OSError:pass
manifest=MANIFEST
allowed=set(manifest)|{'new_confirm_CPU_launch_02.json','new_confirm_CPU_launch_receipt_02.json','new_confirm_CPU_02.log'}
actual={str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
assert actual==allowed and not any(p.is_symlink() for p in source.rglob('*'))
for name,item in manifest.items():
 p=source/name;assert p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
log=(source/'new_confirm_CPU_02.log').read_text();assert 'FileNotFoundError' in log and '/new_confirm_source_registration_01.json' in log
old_path=str(source)
source.rename(target)
proof=dict(status='FAILED_LAUNCH02_PRE_MEDIA_PRE_CPU_PRE_MODEL_PRESERVED_AFTER_OWNED_DIRECTORY_PATH_CORRECTION',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_path=old_path,correct_target=str(target),old_log_sha256=hashlib.sha256((target/'new_confirm_CPU_02.log').read_bytes()).hexdigest(),control_members_reverified=True,new_media_downloads_before_repair=0,new_CPU_decodes_before_repair=0,new_model_calls=0)
with (target/'CPU_launch02_failure_preserved.json').open('x') as stream:json.dump(proof,stream,indent=2)
argv=[PY,'-B',str(target/'code/prepare_confirm8_cohort_02.py'),str(target/'new_confirm_CPU_registration_02.json')]
claim=dict(utc=proof['utc'],argv=argv,old_launch_failure_preserved=True,new_model_calls=0,CPU_only=True)
with (target/'new_confirm_CPU_launch_03.json').open('x') as stream:json.dump(claim,stream,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
out=(target/'new_confirm_CPU_03.log').open('xb')
process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,env=env,start_new_session=True)
receipt=dict(status='ONE_CORRECTED_FRESH8_CPU_LAUNCH03_NO_SUCCESSFUL_STAGE_REPEATED',proof=proof,launch=dict(**claim,pid=process.pid))
with (target/'new_confirm_CPU_launch_receipt_03.json').open('x') as stream:json.dump(receipt,stream,indent=2)
print(json.dumps(receipt))'''.replace('REMOTE', repr(REMOTE)).replace('MANIFEST', repr(transfer['members'])).replace('PY', repr(PY))
    receipt = remote(script)
    save(REPORT/'new_confirm_CPU_launch_03.json', receipt)
    save(REPORT/'CPU_path_recovery_03.json', dict(status=receipt['status'], original_failure_sha256=sha(REPORT/'CPU_launch02_path_failure_actual_01.json'),
         old_launch02_preserved=True, transferred_control_members_not_reuploaded=True, source_registration_and_input_profile_unchanged=True,
         target_root=REMOTE, actual_corrected_argv=receipt['launch']['argv'], no_prior_success_repeated=True, new_model_calls=0))
    print(json.dumps(dict(status=receipt['status'],argv=receipt['launch']['argv'],old_failure_preserved=True,new_model_calls=0)))


if __name__ == '__main__':
    main()
