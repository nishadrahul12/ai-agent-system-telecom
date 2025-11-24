"""
UPDATE FOR api_server.py - Phase 3 Integration
===============================================

THIS IS THE SECTION TO REPLACE in your existing api_server.py

Location: Find the @app.post("/api/forecast") endpoint (around line 280)

REPLACE the entire forecast_endpoint() function and its implementation
with the code below.

KEY CHANGES:
✅ Imports forecasting_models module
✅ Routes model selection (auto, arima, lstm, exponential_smoothing)
✅ Uses forecast_with_fallback() for robust error handling
✅ Returns model_used in response
✅ Each model produces different forecasts

HOW TO APPLY:
1. Open your Phase 0/api_server.py
2. Find line with: @app.post("/api/forecast")
3. Replace the entire function below (from the decorator to "except Exception")
4. Save the file
5. Server will automatically use new models on next restart

IMPORTANT: Keep all the existing imports at the top of api_server.py
This update only replaces one endpoint function.
"""

# ============================================================================
# PHASE 3: UPDATED FORECAST ENDPOINT
# ============================================================================
# ADD THIS IMPORT AT TOP OF api_server.py (around line 1-10):
# from forecasting_models import forecast_with_fallback

@app.post("/api/forecast")
async def forecast_endpoint(
    file: UploadFile = File(...),
    model: str = Form("auto"),
    periods: int = Form(7),
    kpi_name: str = Form(None)
):
    """
    Phase 3: Multi-Model Time-Series Forecasting Endpoint
    
    Parameters:
        - file: CSV/XLSX file with KPI data
        - model: Forecasting model choice
                 'auto' = Auto-select best model
                 'arima' = ARIMA forecasting
                 'lstm' = LSTM neural network
                 'exponential_smoothing' = Exponential smoothing
        - periods: Number of periods to forecast (7, 14, 30)
        - kpi_name: KPI column name to forecast
    
    Returns:
        - status: 'success' or 'error'
        - model_used: Which model was actually used
        - forecast: Array of forecast values
        - trend: Trend analysis
        - metrics: Performance metrics (MAE, RMSE, MAPE)
        - confidence_intervals: 95% CI bounds
    
    Phase 3 Changes:
        ✅ Imports forecasting_models for multi-model support
        ✅ Routes to correct model based on 'model' parameter
        ✅ Auto-selects best model when model='auto'
        ✅ Fallback mechanism ensures robustness
        ✅ Returns model_used so UI knows which was used
    """
    try:
        # Import dependencies
        import pandas as pd
        import io
        import numpy as np
        from uuid import uuid4
        from datetime import datetime
        from forecasting_models import forecast_with_fallback
        
        logger.info(f"Forecast request: model={model}, periods={periods}, kpi={kpi_name}")
        
        # ====================================================================
        # STEP 1: Read and validate file
        # ====================================================================
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {
                "status": "error",
                "error": "Unsupported file type",
                "details": "Please upload CSV or XLSX file"
            }
        
        # ====================================================================
        # STEP 2: Get numeric columns and select KPI
        # ====================================================================
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            return {
                "status": "error",
                "error": "No numeric columns found",
                "details": "File must contain numeric data for forecasting"
            }
        
        # Use user-selected KPI or default to first column
        if kpi_name and kpi_name in numeric_cols:
            target_col = kpi_name
        else:
            target_col = numeric_cols[0]
        
        logger.info(f"Forecasting KPI: {target_col}")
        
        # ====================================================================
        # STEP 3: Extract and clean data
        # ====================================================================
        data = df[target_col].dropna().values
        
        if len(data) < periods:
            return {
                "status": "error",
                "error": "Insufficient data",
                "details": f"Need at least {periods} data points. Got {len(data)}"
            }
        
        # Convert to float array
        data = data.astype(float)
        
        logger.info(f"Data extracted: {len(data)} observations")
        
        # ====================================================================
        # STEP 4: PHASE 3 - Route to forecasting models
        # ====================================================================
        # This is where Phase 3 magic happens!
        # forecast_with_fallback() will:
        #   1. Try the requested model (auto, arima, lstm, exponential_smoothing)
        #   2. If it fails, fall back to next in chain
        #   3. Return model name + results
        
        logger.info(f"Phase 3: Calling {model} forecasting model...")
        
        model_used, forecast_result = forecast_with_fallback(
            data=data,
            periods=periods,
            model=model
        )
        
        logger.info(f"Phase 3: {model_used} forecasting complete!")
        
        # ====================================================================
        # STEP 5: Prepare response
        # ====================================================================
        response = {
            "status": "success",
            "task_id": f"forecast_{uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "model_used": model_used,  # ← Phase 3: Show which model was used
            "kpi_name": target_col,
            "data_points": len(data),
            "forecast_periods": periods,
            "result": {
                "forecast": forecast_result["forecast"],
                "trend": forecast_result["trend"],
                "metrics": forecast_result["metrics"],
                "confidence_intervals": forecast_result["confidence_intervals"]
            }
        }
        
        logger.info(f"Forecast response prepared successfully")
        return response
        
    except Exception as e:
        logger.error(f"Forecast error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "details": "Error during forecasting. Check server logs.",
            "model_attempted": model
        }


# ============================================================================
# END OF PHASE 3 FORECAST ENDPOINT
# ============================================================================
"""
INTEGRATION CHECKLIST:

☐ 1. Copy forecasting_models.py to Phase 0/ folder
☐ 2. Add import at top of api_server.py:
     from forecasting_models import forecast_with_fallback
☐ 3. Replace entire @app.post("/api/forecast") function with code above
☐ 4. Save api_server.py
☐ 5. Update requirements.txt (add tensorflow, pmdarima, statsmodels)
☐ 6. Run: pip install -r requirements.txt
☐ 7. Restart server: python api_server.py
☐ 8. Test with UI: Upload CSV → Select Model → Run Forecast
☐ 9. Verify different models produce different results
☐ 10. Commit to GitHub: "Phase 3.4: Wire model routing to forecasting_models"

SUCCESS INDICATORS:
✅ No import errors on startup
✅ Each model produces different forecast values
✅ model_used shows correct model name
✅ Confidence intervals and metrics displayed
✅ All 4 models (auto, arima, lstm, exp_smoothing) work
✅ Fallback works (bad model falls back to next)
"""
