# Install the project venv and put `attendance-parse` on PATH.
# After a clone, from the project root:  .\scripts\install.ps1

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not on PATH. Install it from https://docs.astral.sh/uv/ then re-run this script."
}

# Documents/ is often OneDrive-backed; hardlinks fail there.
$env:UV_LINK_MODE = "copy"

Write-Host "Syncing project environment..."
uv sync --extra dev

Write-Host "Installing attendance-parse as a uv tool (editable)..."
uv tool install --editable --force .

$binDir = Join-Path $env:USERPROFILE ".local\bin"
$cmd = Get-Command attendance-parse -ErrorAction SilentlyContinue
if (-not $cmd) {
    $exe = Join-Path $binDir "attendance-parse.exe"
    if (Test-Path $exe) {
        Write-Host ""
        Write-Host "attendance-parse is installed at: $exe"
        Write-Host "That folder is not on PATH in this session."
        Write-Host "Run this, then open a new terminal:"
        Write-Host "  uv tool update-shell"
        Write-Host ""
        Write-Host "Or add this folder to PATH:"
        Write-Host "  $binDir"
    } else {
        Write-Host "uv tool install finished, but attendance-parse.exe was not found."
        Write-Host "Try: uv tool run attendance-parse --help"
    }
} else {
    Write-Host ""
    Write-Host "attendance-parse is on PATH: $($cmd.Source)"
    Write-Host "Try:  attendance-parse --help"
    Write-Host "      attendance-parse --version"
}

Write-Host ""
Write-Host "In this repo you can also run:"
Write-Host "  uv run attendance-parse --help"
Write-Host "  uv run pytest"
