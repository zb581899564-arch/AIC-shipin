"""Explicit transport recovery; failed home upload left no remote file or stage."""
from pathlib import Path
import hashlib,json,subprocess,datetime as dt
R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
archive=R/'unique_production_control_09.zip';size=archive.stat().st_size;digest=hashlib.sha256(archive.read_bytes()).hexdigest()
authorization=dict(UTC=dt.datetime.now(dt.timezone.utc).isoformat(),question='默认EasyTier入口SSH握手超时，是否允许临时使用已有aic-inspur-tailscale部署小量控制、启动推理并接收最终ZIP，不改配置且可能境外中继',human_answer='允许临时用Tailscale继续',old_home_SCP_exit=255,read_only_tailscale_host='inspur-NP5570M5',remote_control_file_absent=True,remote_code_and_stage_absent=True,control_bytes=size,control_sha256=digest,no_existing_success_repeated=True)
with (R/'user_temporary_tailscale_authorization_10.json').open('x',encoding='utf8') as f:json.dump(authorization,f,ensure_ascii=False,indent=2)
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(archive),'aic-inspur-tailscale:'+ROOT+'/'+archive.name],check=True,capture_output=True)
source=(R/'deploy_unique_production_09.py').read_text(encoding='utf8')
start=source.index("code=f'''")+5;end=source.index("'''\nres=",start)+3
code=eval(source[start:end],dict(ROOT=ROOT,PY=PY,archive=archive,size=size,digest=digest))
prefix='''from pathlib import Path
import json
'''+f"r=Path({ROOT!r})\n"+f"authorization={authorization!r}\n"+"with (r/'temporary_tailscale_authorization_10.json').open('x') as f:json.dump(authorization,f,ensure_ascii=False,indent=2)\n"
res=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-tailscale','python3','-'],input=prefix+code,text=True,capture_output=True)
print(res.stdout);print(res.stderr[-3000:])
with (R/'unique_transport_recovery_10_result.json').open('x',encoding='utf8') as f:json.dump(dict(bytes=size,sha256=digest,exit=res.returncode,stdout=res.stdout,stderr=res.stderr[-3000:]),f,indent=2)
res.check_returncode()
