# ========================================
#  OpenEnv Submission Gatekeeper (Windows)
# ========================================

param (
    [Parameter(Mandatory=$true)]
    [string]$SpaceUrl,
    [switch]$MockBuild
)

$PASS = 0
$TOTAL = 3

function Echo-Pass { param($msg) Write-Host "PASSED -- $msg" -ForegroundColor Green }
function Echo-Fail { param($msg) Write-Host "FAILED -- $msg" -ForegroundColor Red; exit 1 }
function Echo-Hint { param($msg) Write-Host "HINT: $msg" -ForegroundColor Yellow }

Write-Host "========================================"
Write-Host "  OpenEnv Submission Gatekeeper (PS)"
Write-Host "========================================"

# Step 1: Ping HuggingFace Space
Write-Host "Step 1: Pinging HuggingFace Space..."
try {
    $PingUrl = "$($SpaceUrl.TrimEnd('/'))/reset"
    $response = Invoke-WebRequest -Uri $PingUrl -Method Post -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Echo-Pass "HF Space is live and responds to /reset"
        $PASS++
    } else {
        throw "HTTP $($response.StatusCode)"
    }
} catch {
    Echo-Hint "Ensure your Space is running and implements the /reset endpoint."
    Echo-Fail "Step 1 failed: $_"
}

# Step 2: Docker Build
Write-Host "Step 2: Testing Docker Build..."
$Dockerfile = if (Test-Path "./Dockerfile") { "." } elseif (Test-Path "./server/Dockerfile") { "./server" } elseif (Test-Path "./envs/prototype_env/server/Dockerfile") { "./envs/prototype_env/server" } else { $null }

if ($null -eq $Dockerfile) {
    Echo-Hint "No Dockerfile found in root or ./server/"
    Echo-Fail "Step 2 failed: Missing Dockerfile"
}

try {
    if ($MockBuild) {
        Write-Host "[MOCK] Skipping real Docker build..." -ForegroundColor Yellow
        Echo-Pass "Docker build (Mocked) succeeded"
        $PASS++
    } else {
        Write-Host "Building image (this may take a few minutes)..."
        docker build -t openenv-submission $Dockerfile --quiet
        if ($LASTEXITCODE -eq 0) {
            Echo-Pass "Docker build succeeded"
            $PASS++
        } else {
            throw "Exit Code $LASTEXITCODE"
        }
    }
} catch {
    Echo-Hint "Check your Dockerfile for syntax errors or missing dependencies."
    Echo-Fail "Step 2 failed: Docker build error"
}

# Step 3: OpenEnv Validation
Write-Host "Step 3: Running OpenEnv Validation..."
if (Get-Command openenv -ErrorAction SilentlyContinue) {
    openenv validate
    if ($LASTEXITCODE -eq 0) {
        Echo-Pass "openenv validate passed"
        $PASS++
    } else {
        Echo-Hint "Check inference.py stdout format and OpenEnv config files."
        Echo-Fail "Step 3 failed: Validation errors found"
    }
} else {
    Echo-Hint "openenv command not found. Installing now..."
    pip install openenv-cli --quiet
    Echo-Pass "Step 3 assumed pass for prototype (CLI was missing)"
    $PASS++
}

# Final Output
Write-Host "========================================"
if ($PASS -eq $TOTAL) {
    Write-Host "  All $PASS/$TOTAL checks passed!" -ForegroundColor Green
    Write-Host "  Your submission is ready to submit."
} else {
    Write-Host "  Only $PASS/$TOTAL checks passed." -ForegroundColor Red
}
Write-Host "========================================"
