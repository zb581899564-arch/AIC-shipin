"""Bounded direct UPM author pages; never follow their media links blindly."""
import ipaddress
import json
import re
import subprocess
from direct import ROOT, save, ref


def page(name, url):
    path = ROOT/'metadata'/(name+'.html')
    headers = path.with_suffix('.headers')
    command = ['curl', '--noproxy', '*', '--ipv4', '--location', '--connect-timeout', '6',
        '--max-time', '20', '--max-filesize', '2000000', '--silent', '--show-error',
        '--dump-header', str(headers), '--output', str(path),
        '--write-out', '%{remote_ip}|%{http_code}|%{url_effective}', url]
    result = subprocess.run(command, capture_output=True, text=True, timeout=25)
    parts = result.stdout.strip().split('|')
    peer = parts[0] if parts else ''
    route = subprocess.run(['ip', 'route', 'get', peer], capture_output=True,
        text=True).stdout.strip() if peer else ''
    receipt = dict(url=url, exit_code=result.returncode, status=parts[1] if len(parts)>1 else '',
        peer=peer, route=route, stderr=result.stderr, bytes=path.stat().st_size if path.exists() else 0,
        proxy='explicit noproxyall', IPv4_only=True)
    if result.returncode==0 and receipt['status']=='200':
        if not ipaddress.ip_address(peer).is_global or ' dev eno2 ' not in ' '+route+' ':
            raise ValueError('Direct physical public peer not verified')
        receipt['accepted'] = ref(path)
        links = re.findall(r'href=[\"\']([^\"\']+)', path.read_text(errors='replace'))
        print('LINKS', name, [value for value in links if any(key in value.lower()
            for key in ['.zip', '.rar', '.7z', 'download', 'drive', 'data/', 'license'])][-30:], flush=True)
    save(ROOT/'metadata'/(name+'.route.json'), receipt)
    print('FETCH', json.dumps(receipt), flush=True)


def main():
    urls = [('upm_sportclip03', 'https://www.gti.ssr.upm.es/data/sportclip'),
            ('upm_matdat03', 'https://www.gti.ssr.upm.es/data/matdat')]
    save(ROOT/'upm_primary03_registration.json', dict(
        scope='Fresh author-owned video recordings with HL/NHL/UN; metadata only',
        urls=[url for name,url in urls], no_author_contact=True,
        wall_timeout_per_request=25, body_cap_bytes=2000000))
    for name,url in urls:
        try:
            page(name,url)
        except Exception as error:
            save(ROOT/'metadata'/(name+'_failure.json'), dict(error=repr(error)))
            print(name, repr(error), flush=True)


if __name__=='__main__':
    main()
