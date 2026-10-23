"""Read-only DNS comparison and original-host TLS; no DNS/hosts/route configuration changes."""
import http.client
import json
import socket
import ssl
import traceback
from urllib.parse import urlparse
from t_io import ROOT, read, save, identity, fetch, public_route


def pinned_api(address, destination):
    hostname = 'huggingface.co'
    context = ssl.create_default_context()
    stream = socket.create_connection((address, 443), timeout=15)
    tls = context.wrap_socket(stream, server_hostname=hostname)
    route = public_route(tls.getpeername()[0])
    conn = http.client.HTTPSConnection(hostname, timeout=15); conn.sock = tls
    try:
        conn.request('GET', '/api/datasets/jhanglee/youtube-highlights-full',
            headers={'Host': hostname, 'User-Agent': 'AIC-academic-direct-source-admission', 'Accept-Encoding': 'identity'})
        response = conn.getresponse(); cap = 2 << 20
        declared = response.getheader('Content-Length')
        if response.status != 200 or (declared is not None and int(declared) > cap):
            raise ValueError('Direct original-host API status/size differs')
        data = response.read(cap + 1)
        if len(data) > cap or (declared is not None and len(data) != int(declared)):
            raise ValueError('Direct API payload cap/length differs')
        json.loads(data)
        with destination.open('xb') as stream: stream.write(data)
        return dict(source=identity(destination), **route, original_hostname=hostname,
                    Host_header=hostname, TLS_hostname_and_chain_verified=True, TLS=tls.version(),
                    explicit_TCP_to_public_A_record=True, proxy=None, system_network_configuration_changed=False)
    finally: conn.close()


def main():
    output = ROOT / 'source_resolution02'; output.mkdir()
    old = ROOT / 'source_metadata01/completion.json'
    save(output / 'registration.json', dict(actual_prior_failure=identity(old),
        original_successful_README_adopted=identity(ROOT / 'source_metadata01/author_README.md'),
        scope='One read-only public resolver comparison, then at most two original-host TLS API connections; no media',
        no_changes_to_system_DNS_hosts_proxy_routes_or_services=True))
    failures = []; accepted = None
    path = output / 'public_DNS_A.json'
    try:
        fetch('https://cloudflare-dns.com/dns-query?name=huggingface.co&type=A', path, 65536,
              headers={'Accept': 'application/dns-json'})
        dns = read(path)
        if dns.get('Status') != 0: raise ValueError('Public resolver returned nonzero status')
        addresses = sorted({row['data'] for row in dns.get('Answer', []) if row.get('type') == 1})
        save(output / 'address_registration.json', dict(addresses=addresses, resolver=identity(path)))
        for index, address in enumerate(addresses[:2]):
            try:
                accepted = pinned_api(address, output / 'mirror_api.json'); break
            except Exception: failures.append(dict(address=address, traceback=traceback.format_exc()))
    except Exception: failures.append(dict(stage='read_only_DNS_metadata', traceback=traceback.format_exc()))
    save(output / 'completion.json', dict(state='DIRECT_ORIGINAL_HOST_API_ACCEPTED' if accepted else 'NO_NEW_DIRECT_API_ADMISSION',
        accepted=accepted, failed=failures, new_media=0, new_model_calls=0, system_network_configuration_changed=False))
    print('T_RESOLUTION02_COMPLETE', bool(accepted), len(failures), flush=True)


if __name__ == '__main__': main()
