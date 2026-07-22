# Add Windows TCP port forwarding 10.0.0.110:28 -> 127.0.0.1:5173 (vite)
# Run once as Administrator so 10.0.0.110:28 (internal tunnel target) reaches the vite dev server.
# Vite then proxies /api/* -> 127.0.0.1:8001 (FastAPI).

$ErrorActionPreference = 'Stop'

Write-Host '[1/5] Ensure iphlpsvc is running...'
Set-Service iphlpsvc -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service iphlpsvc    -ErrorAction SilentlyContinue

Write-Host '[2/5] Current portproxy rules:'
netsh interface portproxy show all

# Idempotent remove (in case re-run with different listen address).
try {
  netsh interface portproxy delete v4tov4 listenport=28 listenaddress=0.0.0.0 | Out-Null
} catch {}

Write-Host '[3/5] Adding 0.0.0.0:28 -> 127.0.0.1:5173...'
netsh interface portproxy add v4tov4 listenport=28 listenaddress=0.0.0.0 connectport=5173 connectaddress=127.0.0.1

Write-Host '[4/5] After:'
netsh interface portproxy show all

Write-Host '[5/5] Firewall rules...'
function Ensure-Rule($name, $port) {
  $existing = Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq $name }
  if (-not $existing) {
    New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $port | Out-Null
    Write-Host ("  + added firewall rule: " + $name + " (port " + $port + ")")
  } else { Write-Host ("  = exists            : " + $name) }
}
Ensure-Rule 'HD_Tunnel_28'     28
Ensure-Rule 'HD_Vite_5173'     5173
Ensure-Rule 'HD_Backend_8001'  8001

Write-Host ''
Write-Host 'Done. Verify with: netsh interface portproxy show all'
Write-Host 'Then hit externally: http://11gv92qt74799.vicp.fun/'
Write-Host '                  -> 10.0.0.110:28 -> 127.0.0.1:5173 (vite, which proxies /api to 8001)'
