$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$dotnet = "C:\codingshit\.dotnet\dotnet.exe"
$cliHome = Join-Path $root ".dotnet-cli-home"

$env:DOTNET_CLI_HOME = $cliHome
$env:APPDATA = Join-Path $cliHome "AppData\Roaming"
$env:LOCALAPPDATA = Join-Path $cliHome "AppData\Local"
$env:NUGET_PACKAGES = Join-Path $cliHome ".nuget\packages"
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = "1"
$env:DOTNET_CLI_TELEMETRY_OPTOUT = "1"

$nugetDirectory = Join-Path $env:APPDATA "NuGet"
New-Item -ItemType Directory -Force -Path $nugetDirectory | Out-Null
Copy-Item -LiteralPath (Join-Path $root "NuGet.Config") -Destination (Join-Path $nugetDirectory "NuGet.Config") -Force

& $dotnet restore (Join-Path $root "web-dotnet\MetadataRag.Web.csproj") --configfile (Join-Path $root "NuGet.Config")
& $dotnet build (Join-Path $root "web-dotnet\MetadataRag.Web.csproj") --no-restore
