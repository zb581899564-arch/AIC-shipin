$ErrorActionPreference = 'Stop'
$repairRoot = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z\controller'
$receiptPath = Join-Path $repairRoot 'HKG_DERP_route_repair_20261008.json'
$expectedAddresses = @('103.6.84.152', '205.147.105.30', '205.147.105.78')
$created = @()
$record = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); status = 'PENDING'; scope = 'THREE_HKG_DERP_IPV4_ROUTES_ONLY'; policy_store = 'ActiveStore'; created_routes = @(); existing_routes = @(); error = $null }
try {
    $principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator permission is required for targeted Windows routes.' }
    $adapter = Get-NetAdapter -Name 'WLAN'
    if ($adapter.Status -ne 'Up') { throw 'Expected WLAN adapter is not Up.' }
    $address = @(Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 | Where-Object { $_.IPAddress -eq '192.168.0.2' })
    if ($address.Count -ne 1) { throw 'Audited WLAN IPv4 changed; refusing stale repair.' }
    $gateway = @(Get-NetRoute -InterfaceIndex $adapter.ifIndex -DestinationPrefix '0.0.0.0/0' | Where-Object { $_.NextHop -eq '192.168.0.1' })
    if ($gateway.Count -ne 1) { throw 'Audited WLAN default gateway changed; refusing stale repair.' }
    foreach ($ip in $expectedAddresses) {
        $prefix = "$ip/32"
        $old = @(Get-NetRoute -DestinationPrefix $prefix -ErrorAction SilentlyContinue)
        if ($old.Count -gt 0) {
            if (@($old | Where-Object { $_.InterfaceIndex -ne $adapter.ifIndex -or $_.NextHop -ne $gateway[0].NextHop }).Count -gt 0) { throw "Existing route conflicts with audited repair: $prefix" }
            $record.existing_routes += @($old | Select-Object DestinationPrefix, InterfaceIndex, NextHop, RouteMetric)
            continue
        }
        $route = New-NetRoute -DestinationPrefix $prefix -InterfaceIndex $adapter.ifIndex -NextHop $gateway[0].NextHop -RouteMetric 5 -PolicyStore ActiveStore
        $created += [pscustomobject]@{ DestinationPrefix = $prefix; InterfaceIndex = $adapter.ifIndex; NextHop = $gateway[0].NextHop }
    }
    $record.created_routes = $created
    foreach ($ip in $expectedAddresses) {
        $actual = @(Find-NetRoute -RemoteIPAddress $ip | Where-Object { $_.DestinationPrefix -eq "$ip/32" -and $_.InterfaceIndex -eq $adapter.ifIndex -and $_.NextHop -eq $gateway[0].NextHop })
        if ($actual.Count -ne 1) { throw "Targeted route did not take effect: $ip" }
    }
    $record.status = 'PASS_THREE_HKG_DERP_ACTIVE_ROUTES'
} catch {
    $record.status = 'FAILED_ROLLED_BACK_OWN_ROUTES'
    $record.error = $_.Exception.Message
    foreach ($route in $created) {
        Get-NetRoute -DestinationPrefix $route.DestinationPrefix -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue | Where-Object { $_.NextHop -eq $route.NextHop } | Remove-NetRoute -Confirm:$false -ErrorAction SilentlyContinue
    }
    $record.created_routes = @()
} finally {
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
if ($record.status -ne 'PASS_THREE_HKG_DERP_ACTIVE_ROUTES') { exit 1 }
