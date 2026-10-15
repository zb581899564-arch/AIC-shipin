$ErrorActionPreference = 'Stop'
$root = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z\controller'
$receiptPath = Join-Path $root 'HKG_DERP_persistent_routes_20261008.json'
$originalReceipt = Get-Content -LiteralPath (Join-Path $root 'HKG_DERP_route_repair_20261008.json') -Raw | ConvertFrom-Json
$record = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); status = 'PENDING'; scope = 'PERSIST_ONLY_THREE_ALREADY_ACCEPTED_HKG_ROUTES'; created_routes = @(); error = $null }
try {
    if ($originalReceipt.status -ne 'PASS_THREE_HKG_DERP_ACTIVE_ROUTES' -or $originalReceipt.created_routes.Count -ne 3) { throw 'Original audited ownership receipt is invalid.' }
    foreach ($entry in $originalReceipt.created_routes) {
        if ($entry.DestinationPrefix -notin @('103.6.84.152/32', '205.147.105.30/32', '205.147.105.78/32') -or $entry.InterfaceIndex -ne 7 -or $entry.NextHop -ne '192.168.0.1') { throw 'Unexpected original owned route.' }
        $active = @(Get-NetRoute -DestinationPrefix $entry.DestinationPrefix -InterfaceIndex $entry.InterfaceIndex -PolicyStore ActiveStore | Where-Object { $_.NextHop -eq $entry.NextHop })
        if ($active.Count -ne 1) { throw 'Previously accepted route is no longer active.' }
        $existing = @(Get-NetRoute -DestinationPrefix $entry.DestinationPrefix -PolicyStore PersistentStore -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) { throw 'Persistent route already exists; refusing overwrite or repeat.' }
    }
    foreach ($entry in $originalReceipt.created_routes) {
        New-NetRoute -DestinationPrefix $entry.DestinationPrefix -InterfaceIndex $entry.InterfaceIndex -NextHop $entry.NextHop -RouteMetric 5 -PolicyStore PersistentStore | Out-Null
        $record.created_routes += $entry
    }
    foreach ($entry in $originalReceipt.created_routes) {
        $check = @(Get-NetRoute -DestinationPrefix $entry.DestinationPrefix -InterfaceIndex $entry.InterfaceIndex -PolicyStore PersistentStore | Where-Object { $_.NextHop -eq $entry.NextHop })
        if ($check.Count -ne 1) { throw 'Persistent route verification failed.' }
    }
    $record.status = 'PASS_THREE_OWNED_HKG_PERSISTENT_ROUTES'
} catch {
    $record.status = 'FAILED_PERSISTENCE_ACTIVE_REPAIR_PRESERVED'
    $record.error = $_.Exception.Message
    foreach ($entry in $record.created_routes) {
        Get-NetRoute -DestinationPrefix $entry.DestinationPrefix -InterfaceIndex $entry.InterfaceIndex -PolicyStore PersistentStore -ErrorAction SilentlyContinue | Where-Object { $_.NextHop -eq $entry.NextHop } | Remove-NetRoute -Confirm:$false -ErrorAction SilentlyContinue
    }
    $record.created_routes = @()
} finally {
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
if ($record.status -ne 'PASS_THREE_OWNED_HKG_PERSISTENT_ROUTES') { exit 1 }
