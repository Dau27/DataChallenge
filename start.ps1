param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run .\scripts\setup.ps1 first' }
    if (-not $SkipBuild) {
        Push-Location -LiteralPath 'frontend'
        try {
            npm run build
            if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
        } finally { Pop-Location }
    }
    if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) { throw 'Built frontend missing; run npm run build in frontend' }
    Write-Host 'CQA: http://127.0.0.1:8000   API documentation: http://127.0.0.1:8000/docs'
    & .\.venv\Scripts\python.exe -m uvicorn backend.app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
} finally { Pop-Location }
