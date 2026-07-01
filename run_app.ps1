$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$python = "C:\Users\krish\.conda\envs\HCL\python.exe"
$apiJob = $null

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python environment not found at $python"
}

try {
    Write-Host "Starting RAG API..."
    $apiJob = Start-Job -ScriptBlock {
        param($workingDirectory, $pythonPath)
        Set-Location -LiteralPath $workingDirectory
        & $pythonPath run_web.py
    } -ArgumentList $root, $python

    $deadline = (Get-Date).AddMinutes(2)
    $apiReady = $false

    while (-not $apiReady -and (Get-Date) -lt $deadline) {
        if ($apiJob.State -in @("Completed", "Failed", "Stopped")) {
            Receive-Job $apiJob
            throw "The RAG API stopped during startup."
        }

        try {
            $health = Invoke-RestMethod `
                -Uri "http://127.0.0.1:8000/api/health" `
                -TimeoutSec 2
            $apiReady = $health.status -eq "ok"
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $apiReady) {
        throw "The RAG API did not become ready within two minutes."
    }

    Write-Host "API ready. Web app: http://127.0.0.1:5050"
    & (Join-Path $root "run_dotnet.ps1")
}
finally {
    if ($apiJob) {
        if ($apiJob.State -eq "Running") {
            Stop-Job $apiJob
        }

        Remove-Job $apiJob -Force -ErrorAction SilentlyContinue
    }
}
