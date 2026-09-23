param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("portable", "codex", "cursor", "gemini-cli", "github-copilot", "claude-code", "opencode")]
    [string]$Platform,
    [ValidateSet("project", "user")]
    [string]$Scope = "project",
    [string]$Target = (Get-Location).Path,
    [switch]$Native,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $PSScriptRoot

if ($Scope -eq "project") {
    $ProjectRoot = (Resolve-Path $Target).Path
    switch ($Platform) {
        "portable"       { $Parent = Join-Path $ProjectRoot ".agents/skills" }
        "codex"          { $Parent = Join-Path $ProjectRoot ".agents/skills" }
        "cursor"         { $Parent = Join-Path $ProjectRoot ($(if ($Native) { ".cursor/skills" } else { ".agents/skills" })) }
        "gemini-cli"     { $Parent = Join-Path $ProjectRoot ($(if ($Native) { ".gemini/skills" } else { ".agents/skills" })) }
        "github-copilot" { $Parent = Join-Path $ProjectRoot ($(if ($Native) { ".github/skills" } else { ".agents/skills" })) }
        "claude-code"    { $Parent = Join-Path $ProjectRoot ".claude/skills" }
        "opencode"       { $Parent = Join-Path $ProjectRoot ".opencode/skills" }
    }
}
else {
    $HomeDir = [Environment]::GetFolderPath("UserProfile")
    if (-not $HomeDir) { throw "Cannot resolve the user home directory." }
    switch ($Platform) {
        "portable"       { $Parent = Join-Path $HomeDir ".agents/skills" }
        "codex"          { $Parent = Join-Path $HomeDir ".agents/skills" }
        "cursor"         { $Parent = Join-Path $HomeDir ($(if ($Native) { ".cursor/skills" } else { ".agents/skills" })) }
        "gemini-cli"     { $Parent = Join-Path $HomeDir ($(if ($Native) { ".gemini/skills" } else { ".agents/skills" })) }
        "github-copilot" { $Parent = Join-Path $HomeDir ($(if ($Native) { ".copilot/skills" } else { ".agents/skills" })) }
        "claude-code"    { $Parent = Join-Path $HomeDir ".claude/skills" }
        "opencode"       { $Parent = Join-Path $HomeDir ".config/opencode/skills" }
    }
}

$Dest = Join-Path $Parent "pair-programming"
if (Test-Path $Dest) {
    if (-not $Force) {
        $extra = if ($Parent -like "*.agents\skills") {
            " This shared Agent Skills installation may already serve multiple compatible hosts."
        } else { "" }
        throw "Pair Programming Skill already exists at: $Dest.$extra Re-run with -Force to replace it."
    }
    Remove-Item -Recurse -Force $Dest
}

$Tmp = "$Dest.tmp.$PID"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

try {
    Copy-Item (Join-Path $SourceRoot "SKILL.md") (Join-Path $Tmp "SKILL.md")
    Copy-Item -Recurse (Join-Path $SourceRoot "reference") (Join-Path $Tmp "reference")
    Copy-Item -Recurse (Join-Path $SourceRoot "templates") (Join-Path $Tmp "templates")
    Copy-Item -Recurse (Join-Path $SourceRoot "examples") (Join-Path $Tmp "examples")
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    Move-Item $Tmp $Dest
}
catch {
    if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
    throw
}

Write-Host "Installed pair-programming for $Platform ($Scope):"
Write-Host "  $Dest"

switch ($Platform) {
    "codex"          { Write-Host 'Codex: $pair-programming status' }
    "portable"       { Write-Host 'Installed in shared .agents/skills location.' }
    "cursor"         { Write-Host 'Cursor: /pair-programming status' }
    "gemini-cli"     { Write-Host 'Gemini CLI: ask it to use the pair-programming skill.' }
    "github-copilot" { Write-Host 'Copilot: Use the /pair-programming skill and run status.' }
    default          { Write-Host 'Try: /pair-programming status' }
}
