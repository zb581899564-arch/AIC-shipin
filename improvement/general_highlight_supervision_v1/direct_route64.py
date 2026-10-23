"""Read-only current EasyTier direct-path evidence; never sends test payloads."""
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import time
from urllib.parse import urlparse

CLI = r'G:\vpn\EasyTier\bin\easytier-cli.exe'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'ConnectTimeout=12', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2']


def run(command, timeout=30):
    result = subprocess.run(command, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[:700])
    return result.stdout.decode(encoding='utf-8', errors='replace')


def direct_peer(port, hostname):
    peers = json.loads(run([CLI, '-p', f'127.0.0.1:{port}', '-v', '-o', 'json', 'peer']))
    matches = [p for p in peers if p['route']['hostname'] == hostname]
    if len(matches) != 1:
        raise ValueError('Exact current direct peer missing or ambiguous')
    peer = matches[0]; route = peer['route']
    if route['cost'] != 1 or route['next_hop_peer_id'] != route['peer_id']:
        raise ValueError('Actual next hop is a relay; no file transfer permitted')
    connections = [c for c in peer['peer']['conns'] if not c['is_closed'] and c['tunnel']['tunnel_type'] == 'udp']
    if len(connections) != 1:
        raise ValueError('Single actual UDP direct connection not confirmed')
    connection = connections[0]; remote = connection['tunnel'].get('resolved_remote_addr') or connection['tunnel']['remote_addr']
    address = urlparse(remote['url']).hostname
    if not ipaddress.ip_address(address).is_global:
        raise ValueError('Direct UDP remote is not a public address')
    return dict(hostname=hostname, peer_id=route['peer_id'], local_peer_id=connection['my_peer_id'], next_hop=route['next_hop_peer_id'],
                cost=route['cost'], proxy_cidrs=route['proxy_cidrs'], connection_id=connection['conn_id'],
                tunnel=connection['tunnel'], stats=connection['stats'], public_address=address)


def snapshot():
    local = direct_peer(15889, 'linux-direct-test')
    if '172.18.60.60' not in local['proxy_cidrs']:
        raise ValueError('Existing strict SSH forwarding destination is not owned by the direct Linux peer')
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0)); port = available.getsockname()[1]
    process = subprocess.Popen(SSH + ['-N', '-o', 'ExitOnForwardFailure=yes', '-L',
        f'127.0.0.1:{port}:127.0.0.1:15889', 'aic-inspur-home'],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline = time.monotonic() + 12
        while True:
            if process.poll() is not None:
                raise RuntimeError('Read-only RPC tunnel exited: ' + process.stderr.read().decode(errors='replace')[:300])
            with socket.socket() as check:
                check.settimeout(.2)
                if check.connect_ex(('127.0.0.1', port)) == 0: break
            if time.monotonic() > deadline: raise TimeoutError('Current remote peer RPC unavailable')
            time.sleep(.1)
        remote = direct_peer(port, 'win-direct-test')
    finally:
        process.terminate(); process.wait(timeout=10)
    if local['peer_id'] != remote['local_peer_id'] or remote['peer_id'] != local['local_peer_id']:
        raise ValueError('The two current direct peer identities do not bind each other')
    command = 'Find-NetRoute -RemoteIPAddress ' + local['public_address'] + ' | Select-Object InterfaceAlias,InterfaceIndex,IPAddress,DestinationPrefix,NextHop,RouteMetric | ConvertTo-Json -Depth 4'
    windows_route = json.loads(run(['powershell', '-NoProfile', '-Command', command]))
    if not isinstance(windows_route, list): windows_route = [windows_route]
    indices = {int(row['InterfaceIndex']) for row in windows_route}
    if len(indices) != 1: raise ValueError('Ambiguous Windows outgoing physical route')
    index = indices.pop()
    adapter = json.loads(run(['powershell', '-NoProfile', '-Command',
        f'Get-NetAdapter -IncludeHidden | Where-Object {{$_.ifIndex -eq {index}}} | Select-Object InterfaceAlias,HardwareInterface,Virtual,Status | ConvertTo-Json']))
    if adapter.get('HardwareInterface') is not True or adapter.get('Virtual') is not False:
        raise ValueError('Actual Windows route is not a physical adapter')
    remote_code = """import json,pathlib,subprocess,re
peer=PEER
route=subprocess.check_output(['ip','route','get',peer],text=True).strip()
device=re.search(r'\\bdev\\s+(\\S+)',route).group(1)
policy=pathlib.Path('/home/inspur/codex-network-test-20261013/direct-test.toml').read_text()
print(json.dumps(dict(route=route,device=device,physical=(pathlib.Path('/sys/class/net')/device/'device').exists(),p2p_only=bool(re.search(r'(?m)^\\s*p2p_only\\s*=\\s*true\\s*$',policy)))))
""".replace('PEER', repr(remote['public_address']))
    result = subprocess.run(SSH + ['aic-inspur-home', 'python3 -'], input=remote_code.encode(), capture_output=True, timeout=20)
    if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace')[:500])
    linux_route = json.loads(result.stdout)
    if not linux_route['physical'] or not linux_route['p2p_only']:
        raise ValueError('Current Linux physical/P2P-only policy not confirmed')
    import re
    local_config = Path(r'G:\vpn\EasyTier\easytier-win.toml').read_text()
    if not re.search(r'(?m)^\s*p2p_only\s*=\s*true\s*$', local_config):
        raise ValueError('Current Windows P2P-only policy not confirmed')
    required_forward = ['bind_addr = "127.0.0.1:22022"', 'dst_addr = "172.18.60.60:22"', 'proto = "tcp"']
    if not all(line in local_config for line in required_forward):
        raise ValueError('The existing SSH forward configuration is different')
    owner = json.loads(run(['powershell', '-NoProfile', '-Command',
        'Get-NetTCPConnection -LocalPort 22022 -State Listen | ForEach-Object {Get-Process -Id $_.OwningProcess} | Select-Object Id,ProcessName | ConvertTo-Json']))
    if owner['ProcessName'] != 'easytier-core':
        raise ValueError('The current original SSH listener is not EasyTier')
    ssh_effective = run(['ssh', '-G', 'aic-inspur-home'])
    required = ['hostname 127.0.0.1', 'port 22022', 'stricthostkeychecking true', 'hostkeyalias 100.127.244.47']
    if not all(line in ssh_effective.splitlines() for line in required):
        raise ValueError('Current original strict SSH endpoint differs')
    return dict(windows_peer=local, linux_peer=remote, windows_route=windows_route,
                windows_adapter=adapter, linux_route=linux_route, new_payload_test=False,
                SSH_forward='127.0.0.1:22022 -> 172.18.60.60:22', actual_listener=owner,
                persistent_connection_or_route_changes=False)
