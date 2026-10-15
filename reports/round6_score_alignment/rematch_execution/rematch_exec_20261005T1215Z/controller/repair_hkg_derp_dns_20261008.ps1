$ErrorActionPreference = 'Stop'
$repairRoot = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z\controller'
$receiptPath = Join-Path $repairRoot 'HKG_DERP_dns_repair_20261008.json'
$hostsPath = 'C:\Windows\System32\drivers\etc\hosts'
$backupPath = Join-Path $repairRoot 'HKG_DERP_hosts_before_20261008.bin'
$entries = @(
    @{ HostName = 'derp20b.tailscale.com'; IPAddress = '103.6.84.152' },
    @{ HostName = 'derp20c.tailscale.com'; IPAddress = '205.147.105.30' },
    @{ HostName = 'derp20d.tailscale.com'; IPAddress = '205.147.105.78' }
)
$record = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); status = 'PENDING'; scope = 'THREE_HKG_DERP_HOSTS_ONLY_AND_LOCAL_TAILSCALE_REFRESH'; before_sha256 = $null; after_sha256 = $null; entries = $entries; local_tailscale_restarted = $false; error = $null }
$original = $null
$written = $false
function Byte-Sha256([byte[]]$bytes) { return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() }
try {
    $principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator permission is required for targeted hosts entries.' }
    $ts = (Get-Command tailscale -ErrorAction Stop).Source
    $state = (& $ts status --json | ConvertFrom-Json)
    if ($state.BackendState -ne 'Running') { throw 'Local Tailscale backend is not Running.' }
    $unrelatedActive = @($state.Peer.PSObject.Properties.Value | Where-Object { $_.Active -and -not ($_.TailscaleIPs -contains '100.127.244.47') })
    if ($unrelatedActive.Count -gt 0) { throw 'Unrelated active Tailscale peers; refusing service refresh.' }
    foreach ($entry in $entries) {
        $route = @(Find-NetRoute -RemoteIPAddress $entry.IPAddress | Where-Object { $_.DestinationPrefix -eq ($entry.IPAddress + '/32') -and $_.InterfaceAlias -eq 'WLAN' -and $_.NextHop -eq '192.168.0.1' })
        if ($route.Count -ne 1) { throw 'Required audited direct WLAN route is missing.' }
    }
    $original = [IO.File]::ReadAllBytes($hostsPath)
    $text = [Text.Encoding]::UTF8.GetString($original)
    foreach ($entry in $entries) {
        if ($text -match ('(?im)^\s*[^#\r\n]+\s' + [Regex]::Escape($entry.HostName) + '(?:\s|$)')) { throw 'Existing hosts mapping found; refusing overwrite.' }
    }
    if (Test-Path -LiteralPath $backupPath) { throw 'Previous backup exists; refusing repeat repair.' }
    [IO.File]::WriteAllBytes($backupPath, $original)
    $record.before_sha256 = Byte-Sha256 $original
    $block = "`r`n# BEGIN AIC HKG DERP scoped repair 20261008`r`n"
    foreach ($entry in $entries) { $block += $entry.IPAddress + ' ' + $entry.HostName + "`r`n" }
    $block += "# END AIC HKG DERP scoped repair 20261008`r`n"
    [byte[]]$after = $original + [Text.Encoding]::ASCII.GetBytes($block)
    [IO.File]::WriteAllBytes($hostsPath, $after)
    $written = $true
    $record.after_sha256 = Byte-Sha256 $after
    Clear-DnsClientCache
    foreach ($entry in $entries) {
        $answers = @(Resolve-DnsName -Name $entry.HostName -Type A | Where-Object { $_.IPAddress -eq $entry.IPAddress })
        if ($answers.Count -lt 1) { throw 'Scoped hosts mapping did not resolve to registered DERP address.' }
    }
    Restart-Service -Name Tailscale -ErrorAction Stop
    (Get-Service Tailscale).WaitForStatus('Running', [TimeSpan]::FromSeconds(15))
    $record.local_tailscale_restarted = $true
    $record.status = 'PASS_THREE_HKG_DERP_DNS_AND_LOCAL_REFRESH_PENDING_SSH'
} catch {
    $record.status = 'FAILED_SCOPED_DNS_REPAIR'
    $record.error = $_.Exception.Message
    if ($written -and (Byte-Sha256 ([IO.File]::ReadAllBytes($hostsPath))) -eq $record.after_sha256) {
        [IO.File]::WriteAllBytes($hostsPath, $original)
        Clear-DnsClientCache
        $record.status = 'FAILED_OWN_HOSTS_BYTES_ROLLED_BACK'
    }
} finally {
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
if ($record.status -ne 'PASS_THREE_HKG_DERP_DNS_AND_LOCAL_REFRESH_PENDING_SSH') { exit 1 }
