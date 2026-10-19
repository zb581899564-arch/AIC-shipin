import ast,hashlib,json,subprocess
from pathlib import Path
from remote_control import OPTIONS,REPORT,ssh
here=Path(__file__).parent
codes={}
for name in ['trajectory.py','replay.py']:
 p=here/name;ast.parse(p.read_text());data=p.read_bytes();codes[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 subprocess.run(['scp']+OPTIONS+[str(p),'aic-inspur-tailscale:/home/inspur/aic_video_work/incoming_trajectory_20261017_'+name],check=True,timeout=90)
code='EXPECTED_CODES='+repr(codes)+'\n'+(here/'register_and_launch.py').read_text()
result=ssh(code,220)
(REPORT/'launch.json').write_text(result,encoding='utf-8');print(result)
