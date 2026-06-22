$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$dotnet = "C:\codingshit\.dotnet\dotnet.exe"
$cliHome = Join-Path $root ".dotnet-cli-home"

$env:DOTNET_CLI_HOME = $cliHome
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = "1"
$env:DOTNET_CLI_TELEMETRY_OPTOUT = "1"

& $dotnet run --project (Join-Path $root "web-dotnet") --no-restore
