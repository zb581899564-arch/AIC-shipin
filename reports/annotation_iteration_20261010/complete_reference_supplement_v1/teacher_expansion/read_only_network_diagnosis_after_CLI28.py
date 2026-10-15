from pathlib import Path
from datetime import datetime,timezone
import ast,json,hashlib,os,subprocess,sys
BASE=Path(__file__).resolve().parent;V3=BASE/'capacity_v3_network';V4=BASE/'capacity_v4_tool_batches'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=[]
for v in (V3,V4):
    p=v/'launch.py';s=p.read_text(encoding='utf-8-sig');lines=[x.strip() for x in s.splitlines() if 'env=' in x or 'env.update' in x or 'subprocess.Popen' in x]
    tree=ast.parse(s);calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Popen']
    assert len(calls)==1 and any(k.arg=='env' and isinstance(k.value,ast.Name) and k.value.id=='env' for k in calls[0].keywords)
    sources.append(dict(path=str(p),sha256=sha(p),environment_and_Popen_lines=lines,Popen_env_keyword_is_constructed_env=True))
assert sources[0]['environment_and_Popen_lines']==sources[1]['environment_and_Popen_lines']
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
probe="import os,json; print(json.dumps({k:os.environ.get(k) for k in ('HTTP_PROXY','HTTPS_PROXY','GODEBUG')}))"
r=subprocess.run([sys.executable,'-c',probe],env=env,capture_output=True,text=True,check=True);values=json.loads(r.stdout)
assert values==dict(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
failed=V4/'call02';prior=V3/'call01';old=BASE/'capacity_v2/read_only_network_diagnosis.json'
observed=read(V4/'network_HTTP1_probe_observations_after_CLI28.json')
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='READONLY_ENV_AND_HTTP1_CONNECTIVITY_NOT_AUTHENTICATED_POST_ROOT_CAUSE',original_diagnosis={'path':str(old),'sha256':sha(old)},launch_env_probe_reference={'path':str(BASE/'capacity_v2/env_diagnosis.py'),'sha256':sha(BASE/'capacity_v2/env_diagnosis.py')},executed_launcher_sources=sources,CLI27_and_CLI28_env_construction_byte_exact_equal=True,benign_child_actual_env_values=values,historical_child_env_limit='Original AGY children have exited; exact live process environment cannot be retrospectively inspected. Executed source passes this constructed env directly to child.',prior_CLI27_terminal={'path':str(prior/'terminal.json'),'sha256':sha(prior/'terminal.json')},failed_CLI28_terminal={'path':str(failed/'terminal.json'),'sha256':sha(failed/'terminal.json')},failed_CLI28_raw={'path':str(failed/'stream.jsonl'),'sha256':sha(failed/'stream.jsonl')},failed_CLI28_process=read(failed/'process.json'),HTTP1_probes=observed,actual_network_probes=2,response_headers_body_cookies_credentials_not_read=True,new_AGY_or_model_probes=0,service_proxy_account_changes=0,global_CLI_calls=28,cash_cost='UNKNOWN_NOT_ZERO',conclusions=['No difference was found in the executed proxy/GODEBUG construction or Popen environment handoff.','Existing 7892 proxy currently reaches Google HTTP404 for unauthenticated HEAD/GET over HTTP1.1.','Unauthenticated HTTP reachability does not verify authenticated loadCodeAssist POST, server/route behavior, or prevent transient EOF. Exact authenticated POST EOF root cause remains unproven.','EOF occurred before any model/tool turn, so batch dispatch throughput has not been tested and this is not a semantic annotation failure.'],automatic_retry=False)
out=V4/'read_only_network_diagnosis_after_CLI28.json'
with out.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out),same_env=True,HTTP_statuses=[p['http_status'] for p in observed['probes']],new_AGY_or_model_probes=0),ensure_ascii=False))
