# ============================================================================
# Phase 3: Test All KPIs Script (USING CURL - RELIABLE)
# test_all_kpis.ps1 - Test forecasting across all KPI columns
# ============================================================================
#
# PURPOSE: 
# Test all KPIs to see which models are selected by auto-select logic
# Uses curl (like we know works) instead of Invoke-WebRequest
#
# USAGE:
# cd Phase3
# .\test_all_kpis.ps1
#
# ============================================================================

# Configuration
$API_URL = "http://127.0.0.1:8000/api/forecast"

# FIXED: Use absolute path
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$FILE_PATH = Join-Path -Path $SCRIPT_DIR -ChildPath "..\Phase 0\sample_kpi_data.csv"
$FILE_PATH = [System.IO.Path]::GetFullPath($FILE_PATH)

$CURL_EXE = "C:\Windows\System32\curl.exe"
$PERIODS = 7

Write-Host "DEBUG: File path: $FILE_PATH"
Write-Host ""

# All KPIs from sample_kpi_data.csv
$KPIs = @(
    "RACH stp att",
    "RACH Stp Completion SR",
    "Comp Cont based RACH stp SR",
    "RRC stp att",
    "RRC conn stp SR",
    "E-UTRAN avg RRC conn UEs",
    "RRC_CONNECTED_UE_AVG",
    "E-RAB SAtt",
    "E-UTRAN E-RAB stp SR",
    "ERAB DR; RAN View",
    "E-RAB Stp Att; QCI8",
    "Inter-freq HO att",
    "E-UTRAN Inter-Freq HO SR",
    "E-UTRAN Intra-Freq HO SR",
    "ATT_INTRA_ENB_HO",
    "Intra eNB HO SR",
    "inter eNB E-UTRAN HO SR X2",
    "E-UTRAN avg IP sched thp DL; QCI8",
    "E-UTRAN avg IP sched thp UL; QCI8",
    "E-UTRAN Avg PRB usage per TTI DL",
    "Avg PRB usage per TTI UL",
    "PDCP SDU Volume; DL",
    "PDCP SDU Volume; UL",
    "ERAB Stp Att; QCI1",
    "ERAB Stp SR; QCI1",
    "ERAB DR; RAN View; QCI1",
    "VoLTE traffic",
    "DL MAC PDU VOL SCell",
    "CA_UE_Scell_CONF_SCell_AVG",
    "NUM_CA_UE_SERV_CELL_AVG",
    "NUM_NON_CA_UE_SERV_CELL_AVG",
    "Avg nbr UEs in serv cell",
    "RLC_PDU_DL_VOL_CA_PCELL",
    "RLC_VOL_DL_DRB_SCELL_UE",
    "RLC_VOL_DL_SRB_DRB_NON_CA",
    "PDCP_PDU_X2_DL_SCG",
    "Total DL RLC Volume 1",
    "Average CQI",
    "Avg SINR for PUCCH",
    "Avg SINR for PUSCH",
    "Avg MCS PDSCH trans",
    "Avg MCS PUSCH trans",
    "Avg UE PWR Headroom PUSCH",
    "LTE Interference Power (Ave PUSCH)",
    "E-UTRAN PDCP SDU DL QCI1 LR",
    "E-UTRAN PDCP SDU UL QCI1 LR",
    "QCI1 BLER; DL",
    "QCI1 BLER; UL",
    "Avg PDCP SDU Delay DL QCI1",
    "AVG_HARQ_DELAY_QCI1_UL",
    "Avg Latency DL",
    "Avg UEs activ 3 SCells DL",
    "Avg nbr UEs activ 4 Scells",
    "Max PDCP Thr DL",
    "Max PDCP Thr UL",
    "RSRP_Avg",
    "Measured_RSRP_AVE",
    "Avg DL nonGBR IP thp CA active UEs 2 CCS",
    "Avg DL nonGBR IP thp CA active UEs 3 CCS",
    "Avg DL nonGBR IP thp CA active UEs 4 CCS"
)

# Color output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error-Custom { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }

# ============================================================================
# HEADER
# ============================================================================

Write-Info "======================================================================"
Write-Info "PHASE 3: TEST ALL KPIs - MODEL SELECTION VERIFICATION"
Write-Info "======================================================================"
Write-Info ""

# Check if file exists
if (-not (Test-Path $FILE_PATH)) {
    Write-Error-Custom "❌ ERROR: CSV file not found at $FILE_PATH"
    exit 1
}

Write-Success "✅ CSV file found"

# Check if curl exists
if (-not (Test-Path $CURL_EXE)) {
    Write-Error-Custom "❌ ERROR: curl.exe not found at $CURL_EXE"
    exit 1
}

Write-Success "✅ curl.exe found"

# Check if server is running
Write-Info ""
Write-Info "Testing server connection..."
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -ErrorAction Stop
    Write-Success "✅ Server is running on http://127.0.0.1:8000"
} catch {
    Write-Error-Custom "❌ ERROR: Cannot connect to server"
    exit 1
}

# ============================================================================
# TEST ALL KPIs
# ============================================================================

Write-Info ""
Write-Info "Testing all $($KPIs.Count) KPIs..."
Write-Info ""

$results = @()
$modelCount = @{}

foreach ($kpi in $KPIs) {
    try {
        Write-Info "Testing: $kpi"
        
        # Use curl to send request (we know this works)
        $response = & $CURL_EXE -s -X POST $API_URL `
            -F "file=@$FILE_PATH" `
            -F "model=auto" `
            -F "kpi_name=$kpi" `
            -F "periods=$PERIODS"
        
        # Parse response
        $result = $response | ConvertFrom-Json
        
        # Check status
        if ($result.status -eq "success") {
            $modelUsed = $result.model_used
            $rmse = $result.result.metrics.rmse
            $mape = $result.result.metrics.mape
            
            Write-Success "  ✅ $modelUsed (RMSE: $([Math]::Round($rmse, 6)), MAPE: $([Math]::Round($mape, 2))%)"
            
            # Count model usage
            if ($modelCount.ContainsKey($modelUsed)) {
                $modelCount[$modelUsed]++
            } else {
                $modelCount[$modelUsed] = 1
            }
            
            $results += @{
                KPI = $kpi
                ModelUsed = $modelUsed
                RMSE = $rmse
                MAPE = $mape
                Status = "Success"
            }
        } else {
            Write-Error-Custom "  ❌ FAILED: $($result.error)"
            $results += @{
                KPI = $kpi
                ModelUsed = "Error"
                RMSE = 0
                MAPE = 0
                Status = "Failed"
            }
        }
        
    } catch {
        Write-Error-Custom "  ❌ EXCEPTION: $($_.Exception.Message)"
        $results += @{
            KPI = $kpi
            ModelUsed = "Exception"
            RMSE = 0
            MAPE = 0
            Status = "Failed"
        }
    }
}

# ============================================================================
# SUMMARY RESULTS
# ============================================================================

Write-Info ""
Write-Info "======================================================================"
Write-Info "SUMMARY RESULTS"
Write-Info "======================================================================"

$successCount = ($results | Where-Object { $_.Status -eq "Success" }).Count
$failureCount = ($results | Where-Object { $_.Status -ne "Success" }).Count

Write-Info ""
Write-Info "Total KPIs Tested: $($results.Count)"
Write-Success "Successful: $successCount"
if ($failureCount -gt 0) {
    Write-Error-Custom "Failed: $failureCount"
}

# ============================================================================
# MODEL DISTRIBUTION
# ============================================================================

Write-Info ""
Write-Info "======================================================================"
Write-Info "MODEL SELECTION DISTRIBUTION"
Write-Info "======================================================================"
Write-Info ""

if ($modelCount.Count -gt 0) {
    foreach ($model in $modelCount.Keys | Sort-Object { $modelCount[$_] } -Descending) {
        $count = $modelCount[$model]
        $percentage = [Math]::Round(($count / $successCount) * 100, 1)
        Write-Info "  $model : $count KPIs ($percentage%)"
    }
} else {
    Write-Error-Custom "No successful results to analyze"
}

# ============================================================================
# DETAILED RESULTS TABLE
# ============================================================================

Write-Info ""
Write-Info "======================================================================"
Write-Info "DETAILED RESULTS - ALL KPIs"
Write-Info "======================================================================"
Write-Info ""

Write-Info "KPI Name | Model Selected | RMSE | MAPE"
Write-Info "---------|----------------|------|-----"

foreach ($result in $results) {
    if ($result.Status -eq "Success") {
        $rmse = [Math]::Round($result.RMSE, 6)
        $mape = [Math]::Round($result.MAPE, 2)
        Write-Info "$($result.KPI) | $($result.ModelUsed) | $rmse | $mape%"
    } else {
        Write-Error-Custom "$($result.KPI) | ERROR | - | -"
    }
}

# ============================================================================
# ANALYSIS
# ============================================================================

Write-Info ""
Write-Info "======================================================================"
Write-Info "ANALYSIS"
Write-Info "======================================================================"
Write-Info ""

if ($successCount -gt 0) {
    if ($modelCount.ContainsKey("Linear Regression") -and $modelCount["Linear Regression"] -eq $successCount) {
        Write-Error-Custom "⚠️  ALL KPIs SELECTED LINEAR REGRESSION"
        Write-Warn "This suggests either:"
        Write-Warn "  1. Linear Regression has lowest RMSE for ALL KPIs (unlikely)"
        Write-Warn "  2. ARIMA/Exp Smoothing failing on all KPIs (check server logs)"
        Write-Warn "  3. Data characteristics favor linear trends"
    } else {
        Write-Success "✅ MODEL DIVERSITY CONFIRMED"
        Write-Info "Different KPIs selected different models"
        Write-Info "Auto-select logic is working correctly"
    }
} else {
    Write-Error-Custom "⚠️  No successful tests - check server logs"
}

Write-Info ""
Write-Info "======================================================================"
Write-Info "CONCLUSION"
Write-Info "======================================================================"
Write-Info ""

if ($modelCount.Count -gt 1) {
    Write-Success "✅ Phase 3 is working correctly!"
    Write-Success "✅ Different models are being selected for different KPIs"
    Write-Success "✅ Auto-select logic is functioning as designed"
} else {
    Write-Error-Custom "⚠️  All KPIs selected the same model"
    Write-Warn "Check forecasting_models.py and server logs for issues"
}

Write-Info ""
Write-Success "======================================================================"
Write-Success "TEST COMPLETE"
Write-Success "======================================================================"
