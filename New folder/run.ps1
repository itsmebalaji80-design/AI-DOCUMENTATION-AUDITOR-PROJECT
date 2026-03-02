$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Require-Python {
  $py = Get-Command python -ErrorAction SilentlyContinue
  if (-not $py) {
    Write-Host "Python not found on PATH."
    Write-Host "Install Python 3.10+ from https://www.python.org/downloads/ and re-run."
    exit 1
  }
}

Require-Python

if (-not (Test-Path ".\.venv")) {
  python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip | Out-Null
pip install -r .\backend\requirements.txt

python -m uvicorn backend.app.main:app --reload --port 8000

