"""Bounded existing SSH control; no file-route changes or stdin dependence."""
import base64,hashlib,json,shlex,subprocess,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
kind=sys.argv[1]
settings={
 'catalog':('prepare_catalog_remote.py','supplement_catalog_selection.json'),
 'dense':('prepare_dense_remote.py','dense_anchor_registration.json'),
 'dense02':('prepare_dense02_remote.py','dense_anchor_registration.json'),
 'supplement01':('prepare_supplement01_remote.py','supplement_review_selection.json'),
 'detail01':('prepare_detail_remote.py','detail_anchor_registration.json'),
 'detail02':('prepare_detail02_remote.py','detail02_anchor_registration.json'),
 'supplement_dense01':('prepare_supplement_dense_remote.py','supplement_dense_anchor_registration.json'),
}
script,registration=settings[kind]
report=ROOT/'reports/reliable_reference_20261012_v1'
data=(report/registration).read_text(encoding='utf-8-sig')
program=(Path(__file__).parent/script).read_text()+ '\nmain(json.loads('+repr(data)+'))\n'
encoded=base64.b64encode(zlib.compress(program.encode())).decode()
command='python3 -u -c '+shlex.quote('import base64,zlib;exec(zlib.decompress(base64.b64decode('+repr(encoded)+')))')
claim=dict(kind=kind,script=script,registration=registration,command_chars=len(command),program_sha256=hashlib.sha256(program.encode()).hexdigest(),stage='SSH_CONTROL_DISPATCH')
with (report/(kind+'_launch_claim.json')).open('x',encoding='utf-8') as f:json.dump(claim,f,indent=2)
args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-home',command]
with (report/(kind+'_prepare.log')).open('x',encoding='utf-8') as log:
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
 for line in p.stdout:
  print(line,end='',flush=True);log.write(line);log.flush()
 code=p.wait()
with (report/(kind+'_ssh_completion.json')).open('x',encoding='utf-8') as f:json.dump(dict(exit_code=code,transport='STRICT_EXISTING_SSH_CONTROL',new_model_calls=0),f)
sys.exit(code)
