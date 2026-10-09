"""Small authorized control; no model, decoder, or remote file write."""
import json,datetime
from register_b2_package_v1 import RUN,remote
def main():
    code=(RUN/'controller/inspect_balanced_two_window_risk_v3.py').read_text(encoding='utf-8')
    s=json.loads(remote(code+'\nprint(json.dumps(capture(),ensure_ascii=False))\n',echo=False))
    out=RUN/'controller/monitor_balanced_two_window_risk_v3';out.mkdir(exist_ok=True)
    before=json.loads((out/'latest.json').read_bytes()) if (out/'latest.json').exists() else {}
    a=s['artifacts'];b=before.get('artifacts',{})
    delta=dict(utc=s['utc'],previous_utc=before.get('utc'),stage=(s['stages'].get('progress.json') or {}).get('stage'),
        scopes={k:dict({key:v.get(key) for key in ('fresh_done','recovered_exact_prior_done','accepted_route_done','raw','failures')},
            accepted_new_requests=(v.get('replay_acceptance.json') or {}).get('accepted_new_requests')) for k,v in s['scopes'].items()},
        owned_process_count=len(s['processes']),all_new_done_bound_sha=s['all_new_done_bound_sha'],all_frozen_sha_pass=s['all_frozen_sha_pass'],
        added=len(set(a)-set(b)),changed=sum(v!=b.get(k) for k,v in a.items()),net_bytes=sum(v['bytes'] for v in a.values())-sum(v['bytes'] for v in b.values()),
        completion=s['stages'].get('completion.json'),execution_failure=s['stages'].get('execution_failure.json'))
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for name,v in ((stamp+'.json',s),('latest.json',s),('latest_delta.json',delta)):(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(delta,ensure_ascii=False))
if __name__=='__main__':main()
