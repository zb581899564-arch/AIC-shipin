$ErrorActionPreference = 'Stop'
$receiptPath = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z\controller\HKG_DERP_persistent_routes_store_20261008.json'
$addresses = @('103.6.84.152', '205.147.105.30', '205.147.105.78')
$record = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); status = 'PENDING'; scope = 'PERSIST_ONLY_THREE_OWNED_HKG_ROUTES'; route_results = @(); error = $null }
try {
    if (Test-Path -LiteralPath $receiptPath) { throw 'Receipt already exists; refusing repeat.' }
    foreach ($ip in $addresses) {
        $active = @(Get-NetRoute -DestinationPrefix "$ip/32" -PolicyStore ActiveStore -ErrorAction SilentlyContinue)
        if ($active.Count -ne 1 -or $active[0].InterfaceIndex -ne 7 -or $active[0].NextHop -ne '192.168.0.1' -or $active[0].RouteMetric -ne 5) { throw 'Previously accepted scoped active route changed.' }
        $stored = @(Get-NetRoute -DestinationPrefix "$ip/32" -PolicyStore PersistentStore -ErrorAction SilentlyContinue)
        if ($stored.Count -gt 1 -or ($stored.Count -eq 1 -and ($stored[0].InterfaceIndex -ne 7 -or $stored[0].NextHop -ne '192.168.0.1' -or $stored[0].RouteMetric -ne 5))) { throw 'Conflicting persistent route; refusing overwrite.' }
    }
    foreach ($ip in $addresses) {
        $stored = @(Get-NetRoute -DestinationPrefix "$ip/32" -PolicyStore PersistentStore -ErrorAction SilentlyContinue)
        $created = $false
        $code = $null
        $message = $null
        if ($stored.Count -eq 0) {
            $message = (& route.exe -p -4 ADD $ip MASK 255.255.255.255 192.168.0.1 METRIC 5 IF 7 2>&1 | Out-String).Trim()
            $code = $LASTEXITCODE
            if ($code -ne 0) { throw "Builtin route command failed for $ip with exit $code." }
            $created = $true
        }
        $stored = @(Get-NetRoute -DestinationPrefix "$ip/32" -PolicyStore PersistentStore -ErrorAction SilentlyContinue)
        $active = @(Get-NetRoute -DestinationPrefix "$ip/32" -PolicyStore ActiveStore -ErrorAction SilentlyContinue)
        $valid = $stored.Count -eq 1 -and $active.Count -eq 1 -and $stored[0].InterfaceIndex -eq 7 -and $stored[0].NextHop -eq '192.168.0.1' -and $stored[0].RouteMetric -eq 5 -and $active[0].InterfaceIndex -eq 7 -and $active[0].NextHop -eq '192.168.0.1' -and $active[0].RouteMetric -eq 5
        $record.route_results += [pscustomobject]@{ address = $ip; created = $created; cli_exit_code = $code; cli_message = $message; persistent_and_active_verified = $valid; interface_index = 7; gateway = '192.168.0.1'; metric = 5 }
        if (-not $valid) { throw 'Native PersistentStore and ActiveStore verification failed.' }
    }
    $record.status = 'PASS_THREE_OWNED_HKG_ROUTES_PERSISTENT_AND_ACTIVE_STORE_VERIFIED'
} catch {
    $record.status = 'STOP_PERSISTENCE_VERIFICATION_ACTIVE_CONNECTION_PRESERVED'
    $record.error = $_.Exception.Message
} finally {
    if (-not (Test-Path -LiteralPath $receiptPath)) { $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8 }
}
if ($record.status -ne 'PASS_THREE_OWNED_HKG_ROUTES_PERSISTENT_AND_ACTIVE_STORE_VERIFIED') { exit 1 }
