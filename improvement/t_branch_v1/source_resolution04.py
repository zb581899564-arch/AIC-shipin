"""Last bounded DNS bootstrap: public resolver IP with normal certificate checks."""
import traceback

from t_io import ROOT, fetch, identity, read, save
from source_resolution02 import pinned_api


def main():
    output = ROOT / 'source_resolution04'
    output.mkdir()
    save(output / 'registration.json', dict(
        previous=identity(ROOT / 'source_resolution03/completion.json'),
        resolver='https://1.1.1.1/dns-query?name=huggingface.co&type=A',
        scope='One IP-literal HTTPS DNS lookup, max two original-host API connections',
        certificate_checks='Default CA and original hostname or IP SAN; never disabled',
        no_system_network_configuration_changes=True, no_media=True,
        final_bounded_bootstrap_for_this_source=True))
    failed = []
    accepted = None
    try:
        path = output / 'public_DNS_A.json'
        fetch('https://1.1.1.1/dns-query?name=huggingface.co&type=A', path,
              65536, headers={'Accept': 'application/dns-json'})
        answer = read(path)
        if answer.get('Status') != 0:
            raise ValueError('Public resolver returned nonzero status')
        addresses = sorted({row['data'] for row in answer.get('Answer', [])
                            if row.get('type') == 1})
        save(output / 'addresses.json', dict(addresses=addresses, source=identity(path)))
        for address in [a for a in addresses if a != '199.96.58.15'][:2]:
            try:
                accepted = pinned_api(address, output / 'mirror_api.json')
                break
            except Exception:
                failed.append(dict(address=address, traceback=traceback.format_exc()))
    except Exception:
        failed.append(dict(stage='public_IP_read_only_DNS', traceback=traceback.format_exc()))
    save(output / 'completion.json', dict(
        state='DIRECT_API_ACCEPTED' if accepted else 'STOP_THIS_MIRROR_ROUTE',
        accepted=accepted, failed=failed, media_downloaded=0,
        system_network_configuration_changed=False))
    print('T_RESOLUTION04_COMPLETE', bool(accepted), len(failed), flush=True)


if __name__ == '__main__':
    main()
