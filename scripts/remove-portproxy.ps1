# Remove the manual portproxy we added earlier (花生壳客户端直接占用 0.0.0.0:28, rules conflict).
# Also drop the firewall rules that were added.

$ErrorActionPreference = 'SilentlyContinue'

Write-Host '[1/3] Remove netsh portproxy 0.0.0.0:28 -> 127.0.0.1:5173 ...'
try {
  netsh interface portproxy delete v4tov4 listenport=28 listenaddress=0.0.0.0 | Out-Null
  Write-Host '  - portproxy rule removed'
} catch { Write-Host '  = no rule to remove (already clean)' }

Write-Host ''
Write-Host '[2/3] After:'
netsh interface portproxy show all

Write-Host '[3/3] Drop firewall rules HD_Tunnel_28 ...'
Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like 'HD_Tunnel_28*' } |
  ForEach-Object {
    Remove-NetFirewallRule -Name $_.Name | Out-Null
    Write-Host ("  - removed firewall rule: " + $_.DisplayName)
  }
Write-Host ''
Write-Host 'Keep HD_Vite_5173 and HD_Backend_8001 (they are still needed if you later expose vite / backend directly).'
