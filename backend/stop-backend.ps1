# Kill any uvicorn python process for this project
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
  $_.MainModule.FileName -like "*D:\one_agent\backend\.venv\*"
} | ForEach-Object {
  Write-Host "Stopping pid=$($_.Id)"
  Stop-Process -Id $_.Id -Force
}
Write-Host "Done."
