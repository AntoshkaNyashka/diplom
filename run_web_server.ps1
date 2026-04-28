$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BundledPython = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectDir

if (Test-Path $BundledPython) {
    & $BundledPython tourism_web_app.py
}
else {
    py tourism_web_app.py
}
