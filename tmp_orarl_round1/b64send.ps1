param([string]$ScriptPath)
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($ScriptPath))
ssh aic-inspur-home "printf %s $b64 | base64 -d | tr -d '\r' | bash"
