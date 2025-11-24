# ============================================================================
# Phase 3: Multi-Model Forecasting Testing Script
# test_all_models.ps1 - PowerShell script for Windows
# ============================================================================
#
# WHAT THIS DOES:
# 1. Tests all 4 forecasting models (Auto, ARIMA, LSTM, Exponential Smoothing)
# 2. Uploads sample_kpi_data.csv
# 3. Runs forecast for each model
# 4. Verifies different models produce different results
# 5. Reports metrics and model selection
#
# USAGE:
# 1. Start server in PowerShell (Terminal 1):
#    cd Phase 0
#    python api_server.py
#
# 2. Run tests in new PowerShell (Terminal 2):
#    cd Phase 3
#    .\test_all_models.ps1
#
# REQUIREMENTS:
# - Server running on http://127.0.0.1:8000
# - sample_kpi_data.csv in accessible location
# - PowerShell 5.0+ on Windows
#
# ============================================================================

# Configuration
$API_URL = "http://127.0.0.1:8000/api/forecast"
$FILE_PATH = "..\Phase 0\sample_kpi_data.csv"  # Adjust path if needed
$KPI_NAME = "RRC stp att"  # KPI to test with
$PERIODS = 7

# Color output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error-Custom { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }

# ============================================================================
# CHECK PRECONDITIONS
# ============================================================================

Write-Info "======================================================================"
Write-Info "PHASE 3: MULTI-MODEL FORECASTING TEST SUITE"
Write-Info "======================================================================"
Write-Info ""

# Check if file exists
if (-not (Test-Path $FILE_PATH)) {
    Write-Error-Custom "❌ ERROR: CSV file not found at $FILE_PATH"
    Write-Warn "Please adjust `$FILE_PATH in the script"
    exit 1
}

Write-Success "✅ CSV file found: $FILE_PATH"

# Check if server is running
Write-Info ""
Write-Info "Testing server connection..."
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -ErrorAction Stop
    Write-Success "✅ Server is running on http://127.0.0.1:8000"
} catch {
    Write-Error-Custom "❌ ERROR: Cannot connect to server at http://127.0.0.1:8000"
    Write-Warn "Make sure to start the server first:"
    Write-Warn "  cd Phase 0"
    Write-Warn "  python api_server.py"
    exit 1
}

# ============================================================================
# TEST FUNCTION
# ============================================================================

function Test-Model {
    param(
        [string]$ModelName,
        [string]$ModelParam
    )
    
    Write-Info ""
    Write-Info "────────────────────────────────────────────────────────────────"
    Write-Info "Testing Model: $ModelName"
    Write-Info "────────────────────────────────────────────────────────────────"
    
    try {
        # Create multipart form data
        $form = @{
            file = Get-Item $FILE_PATH
            model = $ModelParam
            kpi_name = $KPI_NAME
            periods = $PERIODS
        }
        
        # Send request
        Write-Info "Sending request... (model=$ModelParam, kpi=$KPI_NAME, periods=$PERIODS)"
        $response = Invoke-WebRequest -Uri $API_URL -Method Post -Form $form -ErrorAction Stop
        
        # Parse response
        $result = $response.Content | ConvertFrom-Json
        
        # Check status
        if ($result.status -eq "success") {
            Write-Success "✅ SUCCESS: $ModelName"
            
            # Extract results
            $modelUsed = $result.model_used
            $forecast = $result.result.forecast
            $metrics = $result.result.metrics
            $trend = $result.result.trend
            
            Write-Info "  Model Used: $modelUsed"
            Write-Info "  Forecast (7 periods): $($forecast -join ', ')"
            Write-Info "  Metrics:"
            Write-Info "    • MAE:  $([Math]::Round($metrics.mae, 4))"
            Write-Info "    • RMSE: $([Math]::Round($metrics.rmse, 4))"
            Write-Info "    • MAPE: $([Math]::Round($metrics.mape, 2))%"
            Write-Info "  Trend:"
            Write-Info "    • Direction: $($trend.direction)"
            Write-Info "    • Slope: $([Math]::Round($trend.slope, 4))"
            Write-Info "    • Strength: $([Math]::Round($trend.strength, 4))"
            
            return @{
                Success = $true
                ModelName = $ModelName
                ModelUsed = $modelUsed
                Forecast = $forecast
                Metrics = $metrics
                Trend = $trend
            }
        } else {
            Write-Error-Custom "❌ FAILED: $ModelName"
            Write-Error-Custom "  Error: $($result.error)"
            Write-Warn "  Details: $($result.details)"
            return @{
                Success = $false
                ModelName = $ModelName
                Error = $result.error
            }
        }
        
    } catch {
        Write-Error-Custom "❌ EXCEPTION: $ModelName"
        Write-Error-Custom "  Error: $($_.Exception.Message)"
        return @{
            Success = $false
            ModelName = $ModelName
            Error = $_.Exception.Message
        }
    }
}

# ============================================================================
# RUN ALL TESTS
# ============================================================================

Write-Info ""
Write-Info "Starting test suite..."
Write-Info ""

$results = @()

# Test 1: Auto Model
$results += Test-Model "Auto (Best Model)" "auto"

# Test 2: ARIMA Model
$results += Test-Model "ARIMA" "arima"

# Test 3: LSTM Model
$results += Test-Model "LSTM" "lstm"

# Test 4: Exponential Smoothing Model
$results += Test-Model "Exponential Smoothing" "exponential_smoothing"

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

Write-Info ""
Write-Info "======================================================================"
Write-Info "TEST RESULTS SUMMARY"
Write-Info "======================================================================"

$successCount = ($results | Where-Object { $_.Success }).Count
$failureCount = ($results | Where-Object { -not $_.Success }).Count

Write-Info ""
Write-Info "Total Tests: $($results.Count)"
Write-Success "Passed: $successCount"
if ($failureCount -gt 0) {
    Write-Error-Custom "Failed: $failureCount"
}

# Show which models succeeded
Write-Info ""
Write-Info "Model Results:"
foreach ($result in $results) {
    if ($result.Success) {
        Write-Success "  ✅ $($result.ModelName) → Used: $($result.ModelUsed)"
    } else {
        Write-Error-Custom "  ❌ $($result.ModelName) → Error: $($result.Error)"
    }
}

# ============================================================================
# VERIFICATION: Different forecasts for different models?
# ============================================================================

Write-Info ""
Write-Info "======================================================================"
Write-Info "VERIFICATION: Forecast Diversity Check"
Write-Info "======================================================================"

$successfulResults = $results | Where-Object { $_.Success }

if ($successfulResults.Count -ge 2) {
    Write-Info ""
    Write-Info "Comparing forecasts across successful models..."
    Write-Info ""
    
    $first = $null
    $identical = 0
    $different = 0
    
    foreach ($result in $successfulResults) {
        $forecast = $result.Forecast
        Write-Info "  $($result.ModelUsed): $($forecast -join ', ')"
        
        if ($first -eq $null) {
            $first = $forecast
        } else {
            # Simple comparison (converted to string)
            $forecast1Str = ($first -join ",")
            $forecast2Str = ($forecast -join ",")
            
            if ($forecast1Str -eq $forecast2Str) {
                $identical++
            } else {
                $different++
            }
        }
    }
    
    Write-Info ""
    if ($different -gt 0) {
        Write-Success "✅ PASS: Different models produce different forecasts!"
        Write-Info "   Models with identical forecasts: $identical"
        Write-Info "   Models with different forecasts: $different"
    } else {
        Write-Warn "⚠️  WARNING: All models produced identical forecasts"
        Write-Warn "   This may indicate fallback is occurring"
    }
} else {
    Write-Warn "⚠️  Skipping diversity check (fewer than 2 successful models)"
}

# ============================================================================
# FINAL STATUS
# ============================================================================

Write-Info ""
Write-Info "======================================================================"

if ($failureCount -eq 0) {
    Write-Success "✅ ALL TESTS PASSED!"
    Write-Info "Phase 3 multi-model forecasting is ready!"
} else {
    Write-Error-Custom "❌ SOME TESTS FAILED"
    Write-Warn "Check error messages above and review logs"
}

Write-Info "======================================================================"

# ============================================================================
# NEXT STEPS
# ============================================================================

Write-Info ""
Write-Info "NEXT STEPS:"
Write-Info ""
Write-Info "1. Test in UI:"
Write-Info "   • Open http://127.0.0.1:8000 in browser"
Write-Info "   • Upload sample_kpi_data.csv"
Write-Info "   • Select different models from dropdown"
Write-Info "   • Verify different forecasts appear"
Write-Info ""
Write-Info "2. Git commit:"
Write-Info "   git add ."
Write-Info "   git commit -m 'Phase 3: Multi-Model Forecasting Complete'"
Write-Info "   git push origin main"
Write-Info ""
Write-Info "3. Documentation:"
Write-Info "   • Review Phase-3-Implementation.md"
Write-Info "   • Update README with new features"
Write-Info ""

# ============================================================================
# END OF SCRIPT
# ============================================================================
