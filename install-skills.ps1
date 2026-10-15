# Native Windows Skills updater. Requires an existing Python 3.11+ environment.
[CmdletBinding()]
param(
    [string]$SkillsRoot = (Join-Path $HOME '.codex/skills'),
    [string]$StateDir = (Join-Path $HOME '.local/share/ai-video-workstation/skill-releases'),
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
& $Python -X utf8 -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
if ($LASTEXITCODE -ne 0) { throw 'A working Python 3.11+ installation is required.' }
& $Python -X utf8 (Join-Path $PSScriptRoot 'scripts/install_skills.py') --skills-root $SkillsRoot --state-dir $StateDir
if ($LASTEXITCODE -ne 0) { throw 'Skills installation failed.' }
Write-Host 'Installed Skills and independent runtime snapshot. Open a new Codex conversation.'
