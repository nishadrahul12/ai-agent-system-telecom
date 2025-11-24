"""
FastAPI Main Application: api_server.py

This is the PRIMARY API ENTRY POINT for the system.

Endpoints:
    GET  /health              - System health check
    POST /api/analyze         - Queue analysis task
    GET  /api/status/:task_id - Get task status
    GET  /api/result/:task_id - Get task result
    POST /api/upload          - Upload file

Configuration:
    - Host: 127.0.0.1
    - Port: 8000
    - Workers: 1 (CPU optimization)
    - Timeout: 120s (large analyses)

Setup:
    python api_server.py

The server automatically:
    1. Creates database (data/ai_agent_system.db)
    2. Initializes memory and safety systems
    3. Registers agents
    4. Listens on port 8000
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn
from forecasting_models import forecast_with_fallback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ai_agent_system.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_HOST = "127.0.0.1"
API_PORT = 8000
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Telecom AI Multi-Agent System",
    description="Local, offline AI analysis for telecom networks",
    version="0.1.0",
)

# Mount static files (frontend)
try:
    from pathlib import Path
    
    # Get the Phase 0 directory where api_server.py is located
    phase0_dir = Path(__file__).parent
    assets_path = phase0_dir / "assets"
    
    logger.info(f"Assets directory: {assets_path}")
    logger.info(f"Assets exists: {assets_path.exists()}")
    
    if assets_path.exists():
        css_file = assets_path / "css" / "style.css"
        js_file = assets_path / "js" / "app.js"
        logger.info(f"CSS file exists: {css_file.exists()}")
        logger.info(f"JS file exists: {js_file.exists()}")
    
    app.mount(
        "/assets",
        StaticFiles(directory=str(assets_path)),
        name="assets",
    )
    logger.info("Static files mounted successfully at /assets")
except Exception as e:
    logger.error(f"Could not mount static files: {e}", exc_info=True)


    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Favicon endpoint - prevents 404 browser spam."""
        return {"detail": "Not Found"}, 404

    @app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
    async def devtools():
        """Chrome devtools endpoint - prevents 404."""
        return {"detail": "Not Found"}, 404



# Global system state (initialized on startup)
system_state = {
    "orchestrator": None,
    "db_manager": None,
    "memory_manager": None,
    "safety_guard": None,
    "initialized": False,
}

# ============================================================================
# MODELS
# ============================================================================


class AnalysisRequest(BaseModel):
    """Request model for analysis task."""
    file_id: str
    agent_id: str
    payload: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    initialized: bool
    components: Dict[str, str]


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    try:
        logger.info("Starting application...")
        
        # Import components (lazy import to avoid circular dependencies)
        from orchestrator import Orchestrator
        from orchestrator.agent_registry import AgentRegistry
        from orchestrator.task_manager import TaskManager
        from database import DatabaseManager
        from memory import MemoryManager
        from trust_safety import SafetyGuard
        
        # Create data directory
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("data/uploads").mkdir(exist_ok=True)
        
        # Initialize components
        registry = AgentRegistry()
        task_manager = TaskManager()
        db_manager = DatabaseManager()
        memory_manager = MemoryManager()
        safety_guard = SafetyGuard()
        
        # Initialize database
        db_manager.initialize()
        logger.info("Database initialized")
        
        # Create orchestrator
        orchestrator = Orchestrator(
            registry=registry,
            task_manager=task_manager,
            db_manager=db_manager,
            memory_manager=memory_manager,
            safety_guard=safety_guard,
        )
        
        # Initialize orchestrator
        orchestrator.initialize()
        logger.info("Orchestrator initialized")
        
        # Store in state
        system_state["orchestrator"] = orchestrator
        system_state["db_manager"] = db_manager
        system_state["memory_manager"] = memory_manager
        system_state["safety_guard"] = safety_guard
        system_state["initialized"] = True

        # ✨ Phase 1: Initialize agents
        try:
            import sys
            
            # Add project root to Python path
            project_root = Path(__file__).parent.parent  # Go up from Phase 0 to project root
            sys.path.insert(0, str(project_root))
            
            from Phase1.startup import initialize_phase1_agents
            phase1_init = initialize_phase1_agents(orchestrator)
            logger.info(f"Phase 1 Status: {phase1_init['status']}")
        except Exception as phase1_err:
            logger.warning(f"Phase 1 initialization skipped: {phase1_err}")
            logger.info("System running with Phase 0 only")
        
        logger.info("[OK] Application startup complete")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        system_state["initialized"] = False
        raise



@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application...")
    system_state["orchestrator"] = None
    logger.info("Application shutdown complete")


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    System health check.
    
    Returns:
        Dict with system status and component health
    """
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    orchestrator = system_state["orchestrator"]
    return orchestrator.health_check()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serves frontend HTML."""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>Error: index.html not found</h1>
                <p>API is running, but frontend file is missing.</p>
            </body>
        </html>
        """


@app.post("/api/analyze")
async def submit_analysis(request: AnalysisRequest):
    """
    Submit analysis task.
    
    Args:
        request: AnalysisRequest with file_id, agent_id, payload
        
    Returns:
        Dict with task_id for tracking
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        if not system_state["initialized"]:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        orchestrator = system_state["orchestrator"]
        
        # Validate input
        if not request.agent_id or not request.payload:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Queue task
        task_id = orchestrator.execute_task(
            agent_id=request.agent_id,
            payload=request.payload,
        )
        
        logger.info(f"Task queued: {task_id}")
        
        return {
            "status": "queued",
            "task_id": task_id,
            "message": "Analysis task queued for processing",
        }
        
    except Exception as e:
        logger.error(f"Analysis submission failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/get-kpi-columns")
async def get_kpi_columns(file: UploadFile = File(...)):
    """
    Get list of numeric column names from uploaded file
    Used to populate KPI selection dropdown in UI
    
    Returns:
        status: 'success' or 'error'
        kpi_columns: List of numeric column names
    """
    try:
        import pandas as pd
        import io
        
        contents = await file.read()
        
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {
                "status": "error",
                "error": "Unsupported file type",
                "kpi_columns": []
            }
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        return {
            "status": "success",
            "kpi_columns": numeric_cols,
            "count": len(numeric_cols)
        }
        
    except Exception as e:
        logger.error(f"Error getting KPI columns: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "kpi_columns": []
        }

@app.post("/api/forecast")
async def forecast_endpoint(
    file: UploadFile = File(...),
    model: str = Form("auto"),
    periods: int = Form(7),
    kpi_name: str = Form(None)
):
    """Phase 3: Multi-Model Time-Series Forecasting Endpoint"""
    try:
        import pandas as pd
        import io
        import numpy as np
        from uuid import uuid4
        from datetime import datetime
        
        logger.info(f"Forecast request: model={model}, periods={periods}, kpi={kpi_name}")
        
        # Read file
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {"status": "error", "error": "Unsupported file type"}
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            return {"status": "error", "error": "No numeric columns found"}
        
        # Select KPI
        target_col = kpi_name if kpi_name and kpi_name in numeric_cols else numeric_cols
        data = df[target_col].dropna().values.astype(float)
        
        if len(data) < periods:
            return {"status": "error", "error": "Insufficient data"}
        
        logger.info(f"Forecasting KPI: {target_col}")
        
        # PHASE 3: Call forecasting models
        model_used, forecast_result = forecast_with_fallback(
            data=data,
            periods=periods,
            model=model
        )
        
        # Prepare response
        response = {
            "status": "success",
            "task_id": f"forecast_{uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "model_used": model_used,
            "kpi_name": target_col,
            "result": {
                "forecast": forecast_result["forecast"],
                "trend": forecast_result["trend"],
                "metrics": forecast_result["metrics"],
                "confidence_intervals": forecast_result["confidence_intervals"]
            }
        }
        
        logger.info(f"Forecast response: {model_used}")
        return response
        
    except Exception as e:
        logger.error(f"Forecast error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "model_attempted": model
        }


@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get task status.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Dict with task status
    """
    try:
        if not system_state["initialized"]:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        orchestrator = system_state["orchestrator"]
        status = orchestrator.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task_id,
            "status": status,
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/result/{task_id}")
async def get_task_result(task_id: str):
    """
    Get task result.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Dict with result if completed
        
    Raises:
        HTTPException: If not found or still running
    """
    try:
        if not system_state["initialized"]:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        orchestrator = system_state["orchestrator"]
        result = orchestrator.get_task_result(task_id)
        
        if not result:
            status = orchestrator.get_task_status(task_id)
            if status == "pending" or status == "running":
                raise HTTPException(
                    status_code=202,
                    detail=f"Task still {status}",
                )
            raise HTTPException(status_code=404, detail="Result not found")
        
        return result
        
    except Exception as e:
        logger.error(f"Result retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload analysis file.
    
    Args:
        file: Uploaded file
        
    Returns:
        Dict with file_id and metadata
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        if not system_state["initialized"]:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        
        allowed_formats = [".csv", ".xlsx", ".xls"]
        if not any(file.filename.lower().endswith(fmt) for fmt in allowed_formats):
            raise HTTPException(status_code=400, detail="File format not allowed")
        
        # Read file
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save file
        from uuid import uuid4
        file_id = str(uuid4())
        file_path = Path("data/uploads") / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"File uploaded: {file_id} ({len(contents)} bytes)")
        
        return {
            "status": "uploaded",
            "file_id": file_id,
            "filename": file.filename,
            "size_bytes": len(contents),
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        workers=1,  # Single worker for CPU optimization
        log_level="info",
    )
