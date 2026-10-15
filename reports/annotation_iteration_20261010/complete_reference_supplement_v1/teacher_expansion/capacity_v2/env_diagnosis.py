from pathlib import Path
from datetime import datetime,timezone
import os,json,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'resume_w11/process.json').read_text(encoding='utf-8'))
print('registered command',json.dumps(p['command'],ensure_ascii=False))
source=(ROOT/'launch.py').read_text(encoding='utf-8')
lines=[x.strip() for x in source.splitlines() if 'env=' in x or 'env.update' in x or 'subprocess.Popen' in x]
print('executed launcher environment construction',json.dumps(lines))
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
probe="import os,json; print(json.dumps({k:os.environ.get(k) for k in ('HTTP_PROXY','HTTPS_PROXY','GODEBUG')}))"
result=subprocess.run([sys.executable,'-c',probe],env=env,capture_output=True,text=True,check=True)
values=json.loads(result.stdout);assert values==dict(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
print('identical environment benign child',json.dumps(values))
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='READ_ONLY_PROXY_TRANSPORT_DIAGNOSIS_NOT_AGY_AUTH_VERIFICATION',
  registered_command=p['command'],executed_launcher_env_source=lines,launcher_sha256=hashlib.sha256((ROOT/'launch.py').read_bytes()).hexdigest(),
  benign_child_actual_env_values=values,original_AGY_child_env_evidence='Executed launcher passes this constructed env dictionary directly to Popen; exited original child cannot be live-inspected retrospectively',
  curl_probes=[dict(method='HEAD',proxy='http://127.0.0.1:7892',http_version='HTTP1.1',endpoint='https://daily-cloudcode-pa.googleapis.com/v1internal:fetchUserInfo',curl_exit_code=0,http_status=404),
               dict(method='GET',proxy='http://127.0.0.1:7892',http_version='HTTP1.1',endpoint='https://daily-cloudcode-pa.googleapis.com/v1internal:fetchUserInfo',curl_exit_code=0,http_status=404)],
  actual_network_probes=2,response_body_and_cookies_not_read=True,no_credentials_sent_by_probes=True,
  inference='Existing proxy reached a HTTP response at endpoint for unauthenticated HEAD/GET. This does not verify authenticated AGY eligibility POST or prove no transient EOF.',
  original_resume_failure_preserved=True,global_CLI_calls=25,cash_cost='UNKNOWN_NOT_ZERO',new_model_calls=0,service_changes=0,automatic_retry=False)
dst=ROOT/'read_only_network_diagnosis.json'
with dst.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(str(dst))
