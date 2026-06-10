$ErrorActionPreference = "Stop"

Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)

Write-Host "EMAIL presente:" ([bool]$env:CONTROL_CENTER_ADMIN_EMAIL)
Write-Host "PASSWORD presente:" ([bool]$env:CONTROL_CENTER_ADMIN_PASSWORD)

if (-not $env:CONTROL_CENTER_ADMIN_EMAIL -or -not $env:CONTROL_CENTER_ADMIN_PASSWORD) {
    throw "CAPTURES_BLOCKED_AUTH: CONTROL_CENTER_ADMIN_EMAIL y CONTROL_CENTER_ADMIN_PASSWORD deben estar cargadas en esta PowerShell."
}

node --check .\work\r4_ai_company_auth_screenshots.mjs
node .\work\r4_ai_company_auth_screenshots.mjs

$mobile = ".\outputs\ecosystem-ai-company-operating-system-production-auth-mobile-390x844.png"
$desktop = ".\outputs\ecosystem-ai-company-operating-system-production-auth-desktop-1280x720.png"

if (-not (Test-Path -LiteralPath $mobile)) {
    throw "R4 mobile capture missing: $mobile"
}
if (-not (Test-Path -LiteralPath $desktop)) {
    throw "R4 desktop capture missing: $desktop"
}

Write-Host "R4_AUTH_CAPTURES_PASS"
