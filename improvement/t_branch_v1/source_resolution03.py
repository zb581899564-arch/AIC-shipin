"""One independent public DNS provider; original-host TLS remains mandatory."""
import traceback
from t_io import ROOT, read, save, identity, fetch
from source_resolution02 import pinned_api


def main():
    output = ROOT / 'source_resolution03'; output.mkdir()
    save(output / 'registration.json', dict(prior_failures=[identity(ROOT / name / 'completion.json')
        for name in ['source_metadata01', 'source_resolution02']],
        scope='One alternate read-only DNS metadata provider, max two original-host API TCP connections',
        no_system_DNS_hosts_proxy_route_or_service_changes=True, no_media=True))
    failures = []; accepted = None
    try:
        path = output / 'public_DNS_A.json'
        fetch('https://dns.alidns.com/resolve?name=huggingface.co&type=A', path, 65536)
        answer = read(path)
        if answer.get('Status') != 0: raise ValueError('Public resolver status differs')
        addresses = sorted({row['data'] for row in answer.get('Answer', []) if row.get('type') == 1})
        save(output / 'address_registration.json', dict(addresses=addresses, resolver=identity(path),
            already_failed_system_address='199.96.58.15', skip_prior_failed_address=True))
        for address in [a for a in addresses if a != '199.96.58.15'][:2]:
            try:
                accepted = pinned_api(address, output / 'mirror_api.json'); break
            except Exception: failures.append(dict(address=address, traceback=traceback.format_exc()))
    except Exception: failures.append(dict(stage='read_only_alternate_DNS', traceback=traceback.format_exc()))
    save(output / 'completion.json', dict(state='DIRECT_ORIGINAL_HOST_API_ACCEPTED' if accepted else 'NO_NEW_DIRECT_API_ADMISSION',
        accepted=accepted, failed=failures, no_media=True, no_system_network_changes=True))
    print('T_RESOLUTION03_COMPLETE', bool(accepted), len(failures), flush=True)


if __name__ == '__main__': main()
