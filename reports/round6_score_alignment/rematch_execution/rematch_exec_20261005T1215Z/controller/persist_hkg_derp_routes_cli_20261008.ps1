$ErrorActionPreference = 'Stop'
$receiptPath = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z\controller\HKG_DERP_persistent_routes_cli_20261008.json'
$key = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\PersistentRoutes'
$addresses = @('103.6.84.152', '205.147.105.30', '205.147.105.78')
$record = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); status = 'PENDING'; scope = 'PERSIST_ONLY_THREE_OWNED_HKG_ROUTES'; route_results = @(); error = $null }
try {
    foreach ($ip in $addresses) {
        $actual = @(Find-NetRoute -RemoteIPAddress $ip | Where-Object { $_.DestinationPrefix -eq "$ip/32" -and $_.InterfaceAlias -eq 'WLAN' -and $_.NextHop -eq '192.168.0.1' -and $_.InterfaceIndex -eq 7 })
        if ($actual.Count -ne 1) { throw 'Previously accepted scoped route changed.' }
        if (Test-Path -LiteralPath $key) {
            $conflicts = @((Get-ItemProperty -LiteralPath $key).PSObject.Properties | Where-Object { $_.Name -like "$ip,*" })
            if ($conflicts.Count -gt 0) { throw 'Persistent entry already exists; refusing repeat or overwrite.' }
        }
    }
    foreach ($ip in $addresses) {
        $message = (& route.exe -p -4 ADD $ip MASK 255.255.255.255 192.168.0.1 METRIC 5 IF 7 2>&1 | Out-String)
        $code = $LASTEXITCODE
        $entryName = "$ip,255.255.255.255,192.168.0.1,5"
        $stored = (Get-Item -LiteralPath $key).GetValueNames() -contains $entryName
        $record.route_results += [pscustomobject]@{ address = $ip; cli_exit_code = $code; cli_message = $message.Trim(); persistent_entry_name = $entryName; persistent_entry_verified = $stored }
        if (-not $stored) { throw 'Builtin route command did not persist the audited entry.' }
    }
    $record.status = 'PASS_THREE_OWNED_HKG_ROUTES_PERSISTENT_REGISTRY_VERIFIED'
} catch {
    $record.status = 'STOP_PERSISTENCE_VERIFICATION_ACTIVE_CONNECTION_PRESERVED'
    $record.error = $_.Exception.Message
} finally {
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
if ($record.status -ne 'PASS_THREE_OWNED_HKG_ROUTES_PERSISTENT_REGISTRY_VERIFIED') { exit 1 }
