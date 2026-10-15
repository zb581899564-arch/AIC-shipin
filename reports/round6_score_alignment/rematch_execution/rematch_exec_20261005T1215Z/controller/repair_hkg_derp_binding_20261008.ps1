$ErrorActionPreference = 'Stop'
$receiptPath = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z\controller\HKG_DERP_binding_repair_20261008.json'
$serviceKey = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tailscale'
$flag = 'TS_BIND_TO_INTERFACE_BY_ROUTE'
$record = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); status = 'PENDING'; scope = 'TAILSCALE_SERVICE_ENVIRONMENT_ONLY'; flag = $flag; value = 'true'; prior_flag = @(); property_existed = $false; local_tailscale_restarted = $false; error = $null }
$changed = $false
$old = @()
try {
    $principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator permission is required for scoped service environment.' }
    $ts = (Get-Command tailscale -ErrorAction Stop).Source
    $state = (& $ts status --json | ConvertFrom-Json)
    if ($state.BackendState -ne 'Running') { throw 'Local Tailscale backend is not Running.' }
    $unrelatedActive = @($state.Peer.PSObject.Properties.Value | Where-Object { $_.Active -and -not ($_.TailscaleIPs -contains '100.127.244.47') })
    if ($unrelatedActive.Count -gt 0) { throw 'Unrelated active Tailscale peers; refusing service refresh.' }
    $property = Get-ItemProperty -LiteralPath $serviceKey
    $record.property_existed = $property.PSObject.Properties.Name -contains 'Environment'
    if ($record.property_existed) { $old = @($property.Environment) }
    $record.prior_flag = @($old | Where-Object { $_ -like "$flag=*" })
    if ($record.prior_flag.Count -gt 1) { throw 'Ambiguous existing flag values; refusing edit.' }
    $new = @($old | Where-Object { $_ -notlike "$flag=*" }) + @("$flag=true")
    New-ItemProperty -LiteralPath $serviceKey -Name Environment -PropertyType MultiString -Value $new -Force | Out-Null
    $changed = $true
    $actual = @((Get-ItemProperty -LiteralPath $serviceKey -Name Environment).Environment)
    if (@($actual | Where-Object { $_ -eq "$flag=true" }).Count -ne 1) { throw 'Scoped service flag did not save correctly.' }
    if (@($actual | Where-Object { $_ -notlike "$flag=*" }) -join "`n" -cne (@($old | Where-Object { $_ -notlike "$flag=*" }) -join "`n")) { throw 'Unrelated service environment changed.' }
    Restart-Service -Name Tailscale -ErrorAction Stop
    (Get-Service Tailscale).WaitForStatus('Running', [TimeSpan]::FromSeconds(15))
    $record.local_tailscale_restarted = $true
    $record.status = 'PASS_TAILSCALE_ROUTE_BINDING_FLAG_PENDING_SSH'
} catch {
    $record.status = 'FAILED_SCOPED_BINDING_REPAIR'
    $record.error = $_.Exception.Message
    if ($changed) {
        if ($record.property_existed) { New-ItemProperty -LiteralPath $serviceKey -Name Environment -PropertyType MultiString -Value $old -Force | Out-Null }
        else { Remove-ItemProperty -LiteralPath $serviceKey -Name Environment -ErrorAction SilentlyContinue }
        $record.status = 'FAILED_OWN_SERVICE_ENVIRONMENT_ROLLED_BACK'
    }
} finally {
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
if ($record.status -ne 'PASS_TAILSCALE_ROUTE_BINDING_FLAG_PENDING_SSH') { exit 1 }
