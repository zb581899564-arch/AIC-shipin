<# ROOT explicit invocation only. No Mac disk writes, no video upload, no direct fallback/retry. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Zip,
    [Parameter(Mandatory=$true)][string]$Manifest,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedManifest,
    [switch]$RootAuthorizeUpload
)
$ErrorActionPreference = 'Stop'
if (-not $RootAuthorizeUpload) { throw 'Explicit ROOT -RootAuthorizeUpload required.' }
$tool = Join-Path $PSScriptRoot 'deploy_metadata.py'
$m = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $Manifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifest) { throw 'Manifest SHA differs.' }
if ((Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $m.zip.sha256 -or (Get-Item -LiteralPath $Zip).Length -ne $m.zip.bytes) { throw 'ZIP binding differs.' }
if ((Get-FileHash -LiteralPath $tool -Algorithm SHA256).Hash.ToLowerInvariant() -ne $m.deployment_script_sha256) { throw 'Deployment script changed.' }
function Invoke-Checked([string]$Program,[string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program exit $LASTEXITCODE; preserve all files, no retry." }
}
$sshArgs = @('-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15')
# Read required Mac workspace rules; existing runner performs read-only identity checks.
Invoke-Checked 'ssh' ($sshArgs + @('macmini','cat /Users/choubk/codex-workspace/AGENTS.md'))
$macOS = & ssh @sshArgs macmini '/Users/choubk/codex-workspace/bin/run uname -s'
if ($LASTEXITCODE -ne 0 -or "$macOS".Trim() -ne 'Darwin') { throw 'Mac unavailable/wrong identity; no direct transfer fallback.' }
$macUser = & ssh @sshArgs macmini '/Users/choubk/codex-workspace/bin/run whoami'
if ($LASTEXITCODE -ne 0 -or "$macUser".Trim() -ne 'choubk') { throw 'Mac user differs; STOP.' }
$linuxHost = & ssh @sshArgs aic-inspur-home hostname
if ($LASTEXITCODE -ne 0 -or "$linuxHost".Trim() -ne 'inspur-NP5570M5') { throw 'Linux host identity differs; STOP.' }
$linuxUser = & ssh @sshArgs aic-inspur-home whoami
if ($LASTEXITCODE -ne 0 -or "$linuxUser".Trim() -ne 'inspur') { throw 'Linux user identity differs; STOP.' }
$root = '/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1'
$stage = "$root/deployment_metadata_v1"
# Exclusive mkdir; never delete or reuse an old target, even after a failed attempt.
$mkdir = "test -d $root/native_sources && test ! -e $root/inputs && test ! -L $root/inputs && mkdir -- $stage"
Invoke-Checked 'ssh' ($sshArgs + @('aic-inspur-home',$mkdir))
$scpArgs = @('-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','-J','macmini')
Invoke-Checked 'scp' ($scpArgs + @($Zip,"aic-inspur-home:$stage/metadata.zip"))
Invoke-Checked 'scp' ($scpArgs + @($Manifest,"aic-inspur-home:$stage/manifest.json"))
Invoke-Checked 'scp' ($scpArgs + @($tool,"aic-inspur-home:$stage/deploy_metadata.py"))
Write-Output 'Only metadata ZIP/manifest/deployment script uploaded through macmini. Native sources unchanged.'
Write-Output 'Next ROOT command: use exact accept command printed by local prepare.'
