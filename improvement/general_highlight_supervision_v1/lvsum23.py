"""One explicit IPv4-only recheck of failed HEADs, never repeat accepted routes."""
import subprocess
from common import read, save, route_for
from lvsum20 import TARGET


def main():
    original=read(TARGET/'publisher_probe22.json')
    failed=[r for r in original if 'error' in r and r['source']['url'].startswith('https://')]
    peers={r['source']['host']:r['public_peer'] for r in original if r.get('status')==200}
    save(TARGET/'remaining23_registration.json',dict(
        failed_sources=[r['source'] for r in failed],accepted_heads_not_repeated=True,
        repair='IPv4 only; previously accepted same-host public peer may be pinned per process',
        no_global_DNS_hosts_route_or_service_change=True,media_bytes=0))
    results=[]
    for previous in failed:
        row=previous['source'];host=row['host']
        command=['curl','--noproxy','*','--ipv4','--head','--location','--max-redirs','3',
            '--proto','=https','--proto-redir','=https','--connect-timeout','5','--max-time','14',
            '--silent','--show-error','--dump-header','-', '--output','/dev/null',
            '--write-out','\nAICPEER:%{remote_ip}|%{http_code}|%{url_effective}',row['url']]
        if host in peers:command[1:1]=['--resolve',host+':443:'+peers[host]]
        process=subprocess.run(command,capture_output=True,text=True,timeout=18)
        headers,marker=process.stdout.rsplit('\nAICPEER:',1) if '\nAICPEER:' in process.stdout else ('','||')
        peer,status,final=marker.split('|',2)
        lengths=[int(line.split(':',1)[1]) for line in headers.splitlines() if line.lower().startswith('content-length:')]
        length=lengths[-1] if lengths else None
        result=dict(source=row,curl_exit=process.returncode,status=int(status) if status.isdigit() else status,
            bytes=length,stderr=process.stderr,final_url=final,body_bytes=0,explicit_ipv4=True,
            explicit_process_resolve=peers.get(host),media_route_admissible=False)
        if process.returncode==0 and status=='200':
            result.update(route_for(peer))
            result['media_route_admissible']=length is not None and 0<length<=150000000
        results.append(result)
        print('REMAINING_HEAD',host,status,length,process.stderr[:120],flush=True)
    save(TARGET/'remaining23.json',results)
    accepted=[r for r in original+results if r.get('status')==200]
    save(TARGET/'publisher_routes23.json',accepted)
    save(TARGET/'completion23.json',dict(state='REMAINING_IPV4_SOURCE_PROBES_COMPLETE',
        accepted_route_count=len(accepted),media_downloads=0,new_model_calls=0,
        original_failures_preserved=True))


if __name__=='__main__':main()
