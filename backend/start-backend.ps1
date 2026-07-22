# Start uvicorn as a detached Windows process with proper stdout/stderr capture
$logDir = "D:\one_agent\backend"
$stdout = Join-Path $logDir "uvicorn-8001.log"
$stderr = Join-Path $logDir "uvicorn-8001.err.log"
"" | Set-Content $stdout
"" | Set-Content $stderr

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "D:\one_agent\backend\.venv\Scripts\uvicorn.exe"
$psi.Arguments = "app.main:app --host 127.0.0.1 --port 8001 --log-level info"
$psi.WorkingDirectory = "D:\one_agent\backend"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.WindowStyle = "Hidden"
$psi.CreateNoWindow = $true

$proc = [System.Diagnostics.Process]::Start($psi)

# Async readers to pump stdout/stderr into log files (survives script exit)
$job1 = Start-Job -ScriptBlock {
  param($p, $f) while (-not $p.HasExited) { $line = $p.StandardOutput.ReadLine(); if ($null -ne $line) { Add-Content -Path $f -Value $line } }
} -ArgumentList $proc, $stdout

$job2 = Start-Job -ScriptBlock {
  param($p, $f) while (-not $p.HasExited) { $line = $p.StandardError.ReadLine(); if ($null -ne $line) { Add-Content -Path $f -Value $line } }
} -ArgumentList $proc, $stderr

Start-Sleep -Milliseconds 800

Write-Host "Started uvicorn (pid=$($proc.Id)) on http://127.0.0.1:8001"
Write-Host "Logs: $stdout / $stderr"
