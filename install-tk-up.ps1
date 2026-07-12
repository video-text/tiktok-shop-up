$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Join-Path $env:LOCALAPPDATA 'TK-UP\marketplace'

function Find-Executable([string]$name, [string[]]$fallbacks) {
  $found = Get-Command $name -ErrorAction SilentlyContinue
  if ($found) { return $found.Source }
  foreach ($item in $fallbacks) { if (Test-Path $item) { return $item } }
  return $null
}

Write-Host "TK-UP installer" -ForegroundColor Cyan

# Install to one stable path so re-running a newly downloaded ZIP is a real update.
if (Test-Path $root) { Remove-Item -LiteralPath $root -Recurse -Force }
New-Item -ItemType Directory -Path $root -Force | Out-Null
Get-ChildItem -LiteralPath $sourceRoot -Force | Where-Object { $_.Name -ne '.git' } |
  Copy-Item -Destination $root -Recurse -Force

$npm = Find-Executable 'npm.cmd' @("$env:ProgramFiles\nodejs\npm.cmd")
if (-not $npm) {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Node.js is required, but winget is unavailable. Install Node.js LTS, then run this installer again.' }
  Write-Host 'Installing Node.js LTS (one-time)...'
  winget install --id OpenJS.NodeJS.LTS --exact --accept-package-agreements --accept-source-agreements
  $npm = "$env:ProgramFiles\nodejs\npm.cmd"
  if (-not (Test-Path $npm)) { throw 'Node.js was installed. Close this window and run 安装TK-UP.cmd once more.' }
}

$codex = Find-Executable 'codex.cmd' @("$env:APPDATA\npm\codex.cmd")
if (-not $codex) {
  Write-Host 'Installing Codex CLI (one-time)...'
  & $npm install -g @openai/codex
  $codex = "$env:APPDATA\npm\codex.cmd"
  if (-not (Test-Path $codex)) { throw 'Codex CLI install did not complete. Run 安装TK-UP.cmd again.' }
}

$python = Find-Executable 'python.exe' @("$env:LocalAppData\Programs\Python\Python312\python.exe")
if (-not $python) {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Python is required for Excel templates. Install Python 3.12, then run this installer again.' }
  Write-Host 'Installing Python 3.12 (one-time)...'
  winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
  $python = "$env:LocalAppData\Programs\Python\Python312\python.exe"
  if (-not (Test-Path $python)) { throw 'Python was installed. Close this window and run 安装TK-UP.cmd once more.' }
}

Write-Host 'Installing Excel support...'
& $python -m pip install --user --quiet openpyxl

Write-Host 'Registering TK-UP with Codex...'
# A previous package may point at an old ZIP folder; replace it with the stable path above.
& $codex plugin marketplace remove tk-up-marketplace 2>$null
& $codex plugin marketplace add $root
& $codex plugin add tk-up@tk-up-marketplace

Write-Host ''
Write-Host 'TK-UP is installed. Close and reopen Codex, then start a new task.' -ForegroundColor Green
Write-Host 'If Codex asks you to sign in in a terminal, complete that sign-in once.' -ForegroundColor Yellow
