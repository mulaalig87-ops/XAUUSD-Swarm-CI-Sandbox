# WP8-01 setup for XAUUSD Swarm (Register §34; OD-08, OD-09; §26 غ-11, غ-12).
# Run from the extracted package folder:
#   powershell -ExecutionPolicy Bypass -File .\XAUUSD_SWARM_BUILD\scripts\wp801_setup.ps1
# Resumable: if a run fails, fix the cause and run the same command again.
# It never deletes or replaces anything in the target. Resume rules: scripts\wp801_sync.py.
# .wp801_state is a consistency/resume marker, NOT proof of ownership (see wp801_sync.py).
$ErrorActionPreference = "Stop"
$Target = "C:\XAUUSD_SWARM_BUILD"
$Source = Split-Path -Parent $PSScriptRoot

function Fail($m) {
  Write-Host "FAILED: $m" -ForegroundColor Red
  Write-Host "Nothing was deleted. Fix the cause and run the same command again; the script resumes." -ForegroundColor Yellow
  exit 1
}

# 0-2. Tools first, then claim/resume the target and copy ONLY missing files (scripts\wp801_sync.py).
#      A file that exists and differs from the package stops the run; nothing is replaced or deleted.
try { $py = (& py -3.13 -c "import sys; print(sys.executable)") 2>$null } catch { $py = $null }
if (-not $py) { Fail "Python 3.13 not found through 'py -3.13'. Install Python 3.13 from python.org." }
if ($py -match "(?i)oracle") { Fail "Interpreter '$py' belongs to ORACLE INFINITY. Not allowed." }
$pyver = (& py -3.13 -c "import sys; print(sys.version.split()[0])")
try { $gitver = (& git --version) } catch { Fail "git not found. Install Git for Windows." }
$claim = (& py -3.13 -I "$Source\scripts\wp801_sync.py" claim "$Source" "$Target")
if ($LASTEXITCODE -ne 0) { Fail "target check refused (see REFUSED message above)" }
$claim | ForEach-Object { Write-Host $_ }
$runid = (($claim | Where-Object { $_ -like "run_id *" }) -split " ")[1]
# Generated outputs go to a staging folder OUTSIDE the target; they enter the target only via
# "wp801_sync.py place" (copy if missing, skip if identical, STOP if different).
$Stage = Join-Path $env:TEMP "wp801_$runid"
New-Item -ItemType Directory -Force -Path "$Stage\env", "$Stage\docs" | Out-Null
Set-Location $Target
# If the initial commit already exists, steps 3-6 are done: never regenerate committed files.
$committed = $false
if (Test-Path "$Target\.git\HEAD") { & git rev-parse --verify -q HEAD | Out-Null; if ($LASTEXITCODE -eq 0) { $committed = $true } }
if (-not $committed) {

# 3. Two separate environments, installed from the fully pinned lock files (no resolver choice)
& py -3.13 -I scripts\wp801_sync.py stamp "$Target" _envs; if ($LASTEXITCODE -ne 0) { Fail "_envs check refused" }
# Each env is built in _envs\.build-<uuid>, installed from the lock with --no-deps, verified
# (frozen set == lock), then renamed into place (scripts\wp801_sync.py venv). Never half-built.
$prefix = @{}
foreach ($n in @("dev","test")) {
  $out = (& py -3.13 -I scripts\wp801_sync.py venv "$Target" $n "$Stage\env\$n.installed.txt")
  if ($LASTEXITCODE -ne 0) { Fail "$n environment refused or failed (see REFUSED message)" }
  $prefix[$n] = $out
}
"python $pyver`nbase_interpreter $py" | Out-File -Encoding utf8 "$Stage\env\python.txt"

# 4. Environment separation check
$pdev = $prefix["dev"]; $ptest = $prefix["test"]
if ($pdev -eq $ptest) { Fail "dev and test environments are not separate" }
"dev_prefix $pdev`ntest_prefix $ptest`nseparate yes" | Out-File -Encoding utf8 "$Stage\env\separation.txt"

# 5. Unit tests in the TEST environment (synthetic only; Register §34)
$ut = & "$Target\_envs\test\Scripts\python.exe" -m pytest -q -p no:cacheprovider 2>&1
$utCode = $LASTEXITCODE
# Duration is removed so that a rerun with the same results produces an identical file.
$ut | ForEach-Object { "$_" -replace " in [0-9.]+s", "" } | Out-File -Encoding utf8 "$Stage\env\unit_tests.txt"
$ut | ForEach-Object { Write-Host $_ }
if ($utCode -ne 0) { Fail "unit tests failed (see $Stage\env\unit_tests.txt)" }
& py -3.13 -I scripts\wp801_sync.py place "$Stage" "$Target"
if ($LASTEXITCODE -ne 0) { Fail "generated outputs could not be placed without replacing existing files (see REFUSED message)" }

# 6. Repository, provenance, initial commit
& py -3.13 -I scripts\wp801_sync.py stamp "$Target" .git; if ($LASTEXITCODE -ne 0) { Fail ".git check refused" }
& git init -q -b main   # into the stamped .git folder (safe to re-run)
& git rev-parse --verify -q HEAD | Out-Null
if ($LASTEXITCODE -ne 0) {
  if (-not (& git config user.name)) { & git config user.name "XAUUSD Swarm Builder"; & git config user.email "builder@localhost" }
  $lines = @("# Provenance (WP8-01)", "", "- Authority: Stage 7 Register §34 (B7 closed, B8 open)",
    "- Python: $pyver ($py)", "- Git: $gitver", "- Reused code: none (OD-08)", "- Gold data: none (OD-10)", "",
    "## File hashes at initial commit (SHA-256)", "", "| File | SHA-256 |", "|---|---|")
  Get-ChildItem -Recurse -File -Force | Where-Object { $_.FullName -notmatch "\\(_envs|\.git|\.wp801_tmp)\\" -and $_.Name -notin @("PROVENANCE.md",".wp801_state") -and $_.FullName -notmatch "\\__pycache__\\" } |
    Sort-Object FullName | ForEach-Object {
      $rel = $_.FullName.Substring($Target.Length + 1)
      $lines += "| $rel | $((Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLower()) |" }
  $lines | Out-File -Encoding utf8 "$Stage\docs\PROVENANCE.md"
  & py -3.13 -I scripts\wp801_sync.py place "$Stage" "$Target"
  if ($LASTEXITCODE -ne 0) { Fail "generated outputs could not be placed without replacing existing files (see REFUSED message)" }
  & git add -A
  & git commit -q -m "WP8-01: initial clean repository (Register §34; OD-08, OD-09)"
  if ($LASTEXITCODE -ne 0) { Fail "initial commit" }
}

}  # end of steps 3-6 (skipped when the initial commit exists)

# 7. Local branch-policy barrier (after the initial commit; see docs\BRANCH_POLICY.md)
& py -3.13 -I scripts\wp801_sync.py install_hook "$Target"; if ($LASTEXITCODE -ne 0) { Fail "hook check refused (see REFUSED message)" }
& py -3.13 -I scripts\wp801_sync.py complete "$Target"; if ($LASTEXITCODE -ne 0) { Fail "could not mark complete" }

# 8. Report
Write-Host "`n=== WP8-01 REPORT (send this to Claude) ===" -ForegroundColor Green
Write-Host "repo: $Target"; Write-Host "commit: $(& git rev-parse HEAD)"; Write-Host "branch: $(& git branch --show-current)"
Write-Host "python: $pyver"; Write-Host $gitver
Get-Content env\separation.txt
Write-Host "unit tests:"; Get-Content env\unit_tests.txt | Select-Object -Last 3
Write-Host "provenance sha256: $((Get-FileHash -Algorithm SHA256 docs\PROVENANCE.md).Hash.ToLower())"
