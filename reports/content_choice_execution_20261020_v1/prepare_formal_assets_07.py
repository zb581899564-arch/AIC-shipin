"""Only bind existing formal registrations. No official labels or inference."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
source=r'''
from pathlib import Path
from datetime import datetime,timezone
import json,os,subprocess,sys,time,socket
W=Path('/home/inspur/aic_video_work');R=W/'content_choice_20261019_v1'
assert socket.gethostname()=='inspur-NP5570M5'
assert json.loads((R/'user_resume_01.json').read_text())['explicit_human_resume'] is True
assert not (R/'formal_asset_setup_launch07.json').exists()
code=r"""
from pathlib import Path
import json,os,sys,time,traceback
W=Path('/home/inspur/aic_video_work');R=W/'content_choice_20261019_v1'
sys.path.insert(0,str(R/'code'))
from improvement.native_preference_v1.assets import read_json,bootstrap
try:
 old=read_json(W/'native_preference_20261019_v1/assets.private.json')
 out=bootstrap(workspace_root=W,output=R/'production_assets.private.json',rights_declaration=old['rights_declaration_ref']['path'],code_root=old['code_root'],
  train_registration='bottleneck_24h_20261019_v1/summary_CPU_registration_05.json',train_acceptance='bottleneck_24h_20261019_v1/summary_inputs_05/input_acceptance.json',
  check_registration='bottleneck_24h_20261019_v1/summary_dev_CPU_registration_09.json',check_acceptance='bottleneck_24h_20261019_v1/summary_dev_inputs_09/input_acceptance.json',
  generation_registration='bottleneck_24h_20261019_v1/summary_generation_registration_10.json',protected_registration='semantic_context_production_20261016_v1/production_registration.json',
  protected_zip='semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip',
  production_registration='five_summary_sprint_20261019_v41/input_registration41.json',production_acceptance='five_summary_sprint_20261019_v41/formal_inputs_41/input_acceptance.json',
  package_inputs='twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json',
  reference_completion=old['reference_generation_origin']['completion_ref']['path'],reference_output_qa=old['reference_generation_origin']['first_output_qa_ref']['path'])
 report=dict(status='FORMAL_ASSET_MANIFEST_BOUND_NOT_PRODUCTION_ADMISSION',output=out,official_label_reads=0,new_models=0,new_media_decode=0)
 with (R/'formal_asset_setup_completion07.json').open('x') as f:json.dump(report,f,indent=2)
except BaseException as e:
 with (R/'formal_asset_setup_failure07.json').open('x') as f:json.dump(dict(error=str(e),traceback=traceback.format_exc()),f,indent=2)
 raise
"""
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
with (R/'formal_asset_setup07.log').open('x') as log:
 p=subprocess.Popen([PYTHON,'-B','-c',code],cwd=R/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 s=Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()
 receipt=dict(utc=datetime.now(timezone.utc).isoformat(),pid=p.pid,start_ticks=s[19],purpose='EXISTING_FORMAL_ASSETS_ONLY_NO_MODEL',automatic_production=False)
 with (R/'formal_asset_setup_launch07.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
'''
source='PYTHON='+repr(PY)+'\n'+source
r=subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale',PY+' -B -'],input=source,text=True,capture_output=True,timeout=45)
print(r.stdout);print(r.stderr)
with (HERE/'formal_asset_setup_result07.json').open('x',encoding='utf8') as f:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),f,ensure_ascii=False,indent=2)
r.check_returncode()
