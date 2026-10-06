function Invoke-BoundedNative {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(ValueFromRemainingArguments)][string[]]$Arguments
    )
    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Executable
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($arg in @('-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3') + $Arguments) {
        $info.ArgumentList.Add($arg)
    }
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { throw 'Native process did not start.' }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $timeout = if ($Executable -eq 'scp') { 1800000 } else { 120000 }
        if (-not $process.WaitForExit($timeout)) {
            $process.Kill($true)
            $process.WaitForExit()
            $global:LASTEXITCODE = 124
            [Console]::Error.WriteLine("Bounded task-owned $Executable timed out, child PID $($process.Id).")
        } else {
            $global:LASTEXITCODE = $process.ExitCode
        }
        $outText = $stdout.GetAwaiter().GetResult()
        $errText = $stderr.GetAwaiter().GetResult()
        if ($outText) { $outText.TrimEnd() }
        if ($errText) { [Console]::Error.WriteLine($errText.TrimEnd()) }
    } finally {
        $process.Dispose()
    }
}
