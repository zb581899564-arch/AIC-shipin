"""Record the scoped, verified Windows repair and refresh only unbound handoffs."""
import base64
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

from register_b2_package_v1 import REMOTE, RUN, remote


def main():
    controller = RUN / 'controller'
    target = controller / 'V14_network_repair_acceptance_20261008.json'
    if target.exists():
        raise RuntimeError('Acceptance already exists; refusing overwrite or repeat.')
    receipt_names = ('HKG_DERP_route_repair_20261008.json',
        'HKG_DERP_dns_repair_20261008.json', 'HKG_DERP_binding_repair_20261008.json',
        'HKG_DERP_persistent_routes_store_20261008.json')
    receipts = {}
    for name in receipt_names:
        data = (controller / name).read_bytes()
        value = json.loads(data)
        assert value['status'].startswith('PASS_'), name
        receipts[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'utc': value['utc'], 'status': value['status']}
    check = subprocess.run(['pwsh', '-NoProfile', '-Command', """
$ErrorActionPreference = 'Stop'
$addresses = @('103.6.84.152','205.147.105.30','205.147.105.78')
$rows = foreach ($ip in $addresses) {
    $a = @(Get-NetRoute -DestinationPrefix "$ip/32" -PolicyStore ActiveStore)
    $p = @(Get-NetRoute -DestinationPrefix "$ip/32" -PolicyStore PersistentStore)
    if ($a.Count -ne 1 -or $p.Count -ne 1) { throw 'Scoped route count changed' }
    foreach ($r in @($a[0],$p[0])) { if ($r.InterfaceIndex -ne 7 -or $r.NextHop -ne '192.168.0.1' -or $r.RouteMetric -ne 5) { throw 'Scoped route identity changed' } }
    [pscustomobject]@{ address = $ip; active = $true; persistent = $true; interface_index = 7; gateway = '192.168.0.1'; metric = 5 }
}
$dns = foreach ($name in @('derp20b.tailscale.com','derp20c.tailscale.com','derp20d.tailscale.com')) {
    [pscustomobject]@{ name = $name; addresses = @([Net.Dns]::GetHostAddresses($name) | ForEach-Object { $_.IPAddressToString }) }
}
$envs = @((Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Services\Tailscale' -Name Environment).Environment)
if (@($envs | Where-Object { $_ -eq 'TS_BIND_TO_INTERFACE_BY_ROUTE=true' }).Count -ne 1) { throw 'Scoped service flag changed' }
[pscustomobject]@{ routes = @($rows); dns = @($dns); service_binding_flag_verified = $true; service_status = (Get-Service Tailscale).Status.ToString() } | ConvertTo-Json -Depth 8 -Compress
"""], capture_output=True, text=True, encoding='utf-8', check=True, timeout=30)
    network = json.loads(check.stdout)
    assert network['service_status'] == 'Running'
    expected_dns = {'derp20b.tailscale.com':'103.6.84.152', 'derp20c.tailscale.com':'205.147.105.30', 'derp20d.tailscale.com':'205.147.105.78'}
    for row in network['dns']:
        assert row['addresses'] == [expected_dns[row['name']]]
    ping = subprocess.run([r'C:\Program Files\Tailscale\tailscale.exe', 'ping', '--c', '3', '--timeout', '5s', '100.127.244.47'],
        capture_output=True, text=True, encoding='utf-8', timeout=25)
    pongs = [line for line in ping.stdout.splitlines() if line.startswith('pong from ') and '(100.127.244.47)' in line and 'via DERP(hkg)' in line]
    assert len(pongs) == 3, (ping.returncode, ping.stdout, ping.stderr)
    actual = json.loads(remote("""import datetime,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r)/'teacher_student_autopilot_v14'
names=('progress.json','completion.json','rematch_01/progress.json','rematch_01/temporal.stage.json','rematch_01/failure.json')
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'artifacts':{n:json.loads((r/n).read_bytes()) if (r/n).exists() else None for n in names}}))
""" % REMOTE, echo=False))
    snapshot = json.loads((controller / 'monitor_teacher_v14/latest.json').read_bytes())['snapshot']
    report = snapshot['student_report']
    result = dict(status='PASS_SCOPED_WINDOWS_HKG_DERP_REPAIR_ACTUAL_SSH_RESTORED', utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        cause='Fake-IP DERP DNS and Tailscale default-interface binding to the local proxy interface prevented the TLS relay connection; same-IP physical-WLAN TLS succeeded.',
        installed_tailscale='1.102.2', official_implementation='https://github.com/tailscale/tailscale/blob/v1.102.2/net/netns/netns_windows.go',
        repair_scope='Three audited HK DERP hostnames/IP /32 routes plus one per-service route-binding flag; local Tailscale refresh only.',
        previous_gap_receipt='V14_monitor_connection_20261008T141744Z.json', previous_gap_preserved=True,
        before_tls_evidence={'default_interface_error':'UNEXPECTED_EOF_WHILE_READING', 'physical_WLAN_same_IP_verified_TLS_HTTP_status':200},
        repair_receipts=receipts, actual_windows_state=network, tailscale_ping_exit_code=ping.returncode,
        tailscale_ping=ping.stdout.strip(), actual_path='DERP(hkg)', UDP_direct_established=False,
        actual_linux=actual, comprehensive_snapshot_utc=snapshot['utc'], source_lock_sha256=snapshot['source_lock_sha256'],
        actual_T_optimizer_updates=report['optimizer_steps'], actual_backward_examples=report['backward_examples'],
        selected_epoch=report['selected_epoch'], selected_original_B=report['selected_candidate_original_B'],
        selected_adapter_sha256=report['selected_adapter_sha256'], new_T_improvement_claim=False,
        non_test_package_status=(snapshot.get('nontest8_package') or {}).get('status'),
        final_ZIP_complete=bool(snapshot.get('completion')), remote_processes_signalled=False,
        frozen_source_modified=False, launchers_repeated=False, large_transfer_bytes=0)
    assert report['optimizer_steps'] == 15 and report['selected_candidate_original_B'] is True
    data = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    with target.open('xb') as handle:
        handle.write(data)
    latest = controller / 'monitor_teacher_v14/connection_latest.json'
    if latest.exists():
        old = latest.read_bytes()
        history = latest.with_name('connection_prior_' + hashlib.sha256(old).hexdigest() + '.json')
        if not history.exists():
            history.write_bytes(old)
    latest.write_bytes(data)
    progress = actual['artifacts'].get('rematch_01/progress.json') or {}
    header = f"""## 2026-10-08 网络修复与实际训练终态（UTC {actual['utc']}）

用户明确要求修复连接。本地FlClash fake-IP DNS及Tailscale默认代理接口绑定阻断HK DERP TLS；同IP物理WLAN TLS返回200。已限定修复3个香港DERP hostname/IP的hosts与/32持久路由，并给本地Tailscale服务登记官方v1.102.2支持的TS_BIND_TO_INTERFACE_BY_ROUTE=true，重启该本地服务后实际SSH恢复到inspur-NP5570M5。真实链路为DERP(hkg)，UDP直连仍未建立。3路由ActiveStore/PersistentStore、3DNS与服务标志均实际复核。历史14:17不可达证据保留，当前已恢复；本次授权不扩大到其他连接/代理/服务。精确修复与回滚范围见controller/V14_NETWORK_REPAIR_20261008.md；聚合证据SHA {hashlib.sha256(data).hexdigest()}。

实际8B T已自然完成3epochs/15次optimizer更新/195次样本反向；4更新前缀及独立CPU288adapter重载PASS，冻结基座保持。同production输入14个弱dev上，原B与epoch1同为0.3786251362162477，epoch2/3较低，登记选点实际选择epoch0原B，adapter SHA {report['selected_adapter_sha256']}；新训练发生，但新权重没有胜出，不宣称新T提高或官网分。原教师160标签/160盲选择、UNKNOWN81及科学历史保持。

NONTEST8完整11项独立strict PASS；当前426复赛时间进度为{progress}，root completion={actual['artifacts'].get('completion.json')}。完整426/空间/strict与ZIP仍以真实终态为准；不把8个非测试ZIP当最终包。完整命令/父子PGID见实际快照{snapshot['utc']}，训练期间连接中断未重开任何launcher、教师成功生成或训练。每15分钟继续静默巡检，最终全验收前不删除自动任务。

<!-- END_V14_NETWORK_REPAIR_ACCEPTANCE -->

"""
    targets = [RUN.parents[3] / 'AGENTS.md', RUN / 'STATUS_AUTOPILOT_20261007.md',
        controller / 'AUTONOMOUS_EXECUTION_20261008.md', controller / 'V8_REPAIR_AND_EXECUTION_20261008.md']
    payload = {}
    for path in targets:
        text = path.read_text(encoding='utf-8')
        if path.name == 'AGENTS.md' and '<!-- END_V14_CONNECTION_MONITOR_GAP -->' in text:
            old, tail = text.split('<!-- END_V14_CONNECTION_MONITOR_GAP -->', 1)
            archive = controller / 'V14_connection_gap_AGENTS_original_20261008.md'
            if not archive.exists():
                archive.write_text(old + '<!-- END_V14_CONNECTION_MONITOR_GAP -->\n', encoding='utf-8')
            text = tail.lstrip('\n')
        path.write_text(header + text, encoding='utf-8', newline='\n')
        if path.name != 'AGENTS.md':
            payload[path.relative_to(RUN).as_posix()] = base64.b64encode(path.read_bytes()).decode()
    payload[target.relative_to(RUN).as_posix()] = base64.b64encode(data).decode()
    remote("""import base64,hashlib,json
from pathlib import Path
r=Path(%r);items=json.loads(base64.b64decode(%r));bound=set()
for lock in r.glob('*/source_lock.json'):
 v=json.loads(lock.read_bytes());entries=v.get('files',v.get('production_files'))
 if isinstance(entries,dict):names=list(entries)
 elif isinstance(entries,list) and all(isinstance(x,dict) and isinstance(x.get('path'),str) for x in entries):names=[x['path'] for x in entries]
 else:raise RuntimeError('unknown source-lock schema')
 bound.update(str((lock.parent/n).resolve()) for n in names)
for name,encoded in items.items():
 p=r/name;assert p.resolve().is_relative_to(r.resolve()) and str(p.resolve()) not in bound
 new=base64.b64decode(encoded)
 if p.exists() and p.read_bytes()!=new:
  old=p.read_bytes();a=r/'controller/handoff_history_v14';a.mkdir(exist_ok=True);q=a/(p.name+'.'+hashlib.sha256(old).hexdigest())
  if not q.exists():q.write_bytes(old)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(new)
print(json.dumps({'status':'PASS_UNBOUND_NETWORK_REPAIR_HANDOFF_ONLY','files':len(items)}))
""" % (REMOTE, base64.b64encode(json.dumps(payload).encode()).decode()), echo=False)
    print(json.dumps({'status':result['status'], 'proof_sha256':hashlib.sha256(data).hexdigest(), 'actual_path':result['actual_path'],
        'linux_utc':actual['utc'], 'rematch_progress':progress, 'optimizer_steps':report['optimizer_steps'],
        'selected_original_B':report['selected_candidate_original_B'], 'root_completion':actual['artifacts'].get('completion.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
