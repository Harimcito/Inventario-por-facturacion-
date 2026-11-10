$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = (Get-Command python -ErrorAction Stop).Source

# 8501 is reserved exclusively for Giovalia. Find a free local preview port.
$port = 0
foreach ($candidate in 8506..8599) {
    if ($candidate -eq 8501) { continue }
    $used = Get-NetTCPConnection -LocalPort $candidate -State Listen -ErrorAction SilentlyContinue
    if (-not $used) { $port = $candidate; break }
}
if (-not $port) { throw "No encontré un puerto libre entre 8506 y 8599." }

Start-Process -FilePath $python -ArgumentList @("-m", "streamlit", "run", "app.py", "--server.address", "127.0.0.1", "--server.port", "$port", "--server.headless", "true") -WorkingDirectory $root -WindowStyle Hidden
$url = "http://127.0.0.1:$port"
$deadline = (Get-Date).AddSeconds(60)
do {
    Start-Sleep -Seconds 1
    try {
        if ((Invoke-WebRequest "$url/_stcore/health" -TimeoutSec 2).Content -match "ok") {
            Start-Process $url
            exit 0
        }
    } catch { }
} while ((Get-Date) -lt $deadline)
throw "La app no inició. Prueba abrirla desde PowerShell y revisa la instalación de Python y Streamlit."
