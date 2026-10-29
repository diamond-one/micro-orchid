$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
python (Join-Path $PSScriptRoot "verify_orchid.py")
exit $LASTEXITCODE
