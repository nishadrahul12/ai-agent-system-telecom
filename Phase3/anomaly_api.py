"""
anomaly_api.py - Phase 3 Anomaly Detection API
FastAPI endpoints for file upload, analysis, and results retrieval
UPDATED: Frontend integration with static file serving
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from anomaly_models import (
    AnalysisParameters,
    UploadResponse,
    TaskStatusResponse,
    ErrorResponse,
    AnalysisResult,
    AnomalyDetail,
    NetworkClassification,
    AnalysisSummary
)
from anomaly_utils import (
    validate_file_size,
    validate_file_format,
    load_any_format,
    save_result_to_disk,
    load_result_from_disk,
    load_metadata_from_disk,
    list_all_tasks,
    delete_task,
    cleanup_old_results,
    generate_task_id,
    get_file_size_mb
)
from anomaly_engine import AnomalyDetectionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Telecom Anomaly Detection API",
    description="Phase 3 - Real-time anomaly detection for telecom networks",
    version="1.0.0"
)

# ============================================================================
# ENABLE CORS - Allow Frontend to Access API
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (localhost:8000, 127.0.0.1:8000, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


# ============================================================================
# MOUNT STATIC FILES - SERVES FRONTEND DASHBOARD
# ============================================================================

# Mount static folder for CSS, JS, images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Task storage (in-memory for quick status checks)
task_store = {}

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)


# ============================================================================
# BACKGROUND TASK: Process Anomaly Detection
# ============================================================================

def process_anomaly_detection(
    task_id: str,
    filepath: str,
    sensitivity: str,
    methods: list
):
    """
    Background task to process anomaly detection.
    
    Args:
        task_id (str): Unique task ID
        filepath (str): Path to data file
        sensitivity (str): Sensitivity level
        methods (list): Detection methods to use
    """
    try:
        # Update task status
        task_store[task_id]['status'] = 'processing'
        task_store[task_id]['started_at'] = datetime.now().isoformat()
        logger.info(f"Processing task {task_id}")
        
        # Load data
        logger.info(f"Loading data from {filepath}")
        data = load_any_format(filepath)
        
        task_store[task_id]['progress'] = 30
        task_store[task_id]['data_points'] = len(data)
        task_store[task_id]['kpis'] = data.shape[1]
        
        # Initialize engine
        engine = AnomalyDetectionEngine(
            sensitivity=sensitivity,
            methods=methods
        )
        
        task_store[task_id]['progress'] = 40
        logger.info(f"Normalizing data for task {task_id}")
        engine.normalize_data(data)
        
        task_store[task_id]['progress'] = 60
        logger.info(f"Running anomaly detection for task {task_id}")
        anomalies = engine.detect_anomalies()
        
        task_store[task_id]['progress'] = 80
        logger.info(f"Generating summary for task {task_id}")
        summary = engine.get_summary()
        network_classification = engine.classify_network_severity()
        
        # Build response
        anomaly_details = []
        for anomaly in anomalies:
            detail = AnomalyDetail(
                kpi=anomaly.get('kpi'),
                value=anomaly.get('value'),
                normalized_value=anomaly.get('normalized_value'),
                severity=anomaly.get('severity'),
                method=anomaly.get('method'),
                anomaly_score=anomaly.get('anomaly_score'),
                index=anomaly.get('index')
            )
            anomaly_details.append(detail.dict())
        
        result = {
            'task_id': task_id,
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'anomalies': anomaly_details,
            'network_classification': network_classification
        }
        
        # Save to disk
        task_store[task_id]['progress'] = 90
        logger.info(f"Saving results to disk for task {task_id}")
        
        metadata = {
            'task_id': task_id,
            'filename': Path(filepath).name,
            'file_size_bytes': os.path.getsize(filepath),
            'format': 'csv' if filepath.endswith('.csv') else 'xlsx',
            'sensitivity': sensitivity,
            'methods': methods,
            'created_at': task_store[task_id]['created_at'],
            'started_at': task_store[task_id]['started_at'],
            'completed_at': datetime.now().isoformat(),
            'status': 'completed',
            'error_message': None,
            'data_points': len(data),
            'kpis_count': data.shape[1]
        }
        
        save_result_to_disk(task_id, result, metadata)
        
        # Update final status
        task_store[task_id]['status'] = 'completed'
        task_store[task_id]['progress'] = 100
        task_store[task_id]['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"Task {task_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        task_store[task_id]['status'] = 'failed'
        task_store[task_id]['error'] = str(e)


# ============================================================================
# ENDPOINTS: Health & Status
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Telecom Anomaly Detection API"
    }


@app.get("/api/anomalies/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a specific task.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        TaskStatusResponse: Current task status
    """
    if task_id not in task_store:
        # Try to load from disk
        metadata = load_metadata_from_disk(task_id)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return TaskStatusResponse(
            task_id=task_id,
            status=metadata.get('status'),
            created_at=metadata.get('created_at'),
            progress_percent=100 if metadata.get('status') == 'completed' else 0,
            message=None,
            error=metadata.get('error_message')
        )
    
    task = task_store[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        status=task.get('status'),
        created_at=task.get('created_at'),
        progress_percent=task.get('progress', 0),
        message=f"Processing: {task.get('progress', 0)}% complete",
        error=task.get('error')
    )


# ============================================================================
# ENDPOINTS: File Upload & Analysis
# ============================================================================

@app.post("/api/anomalies/analyze", response_model=UploadResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    sensitivity: str = Query("medium", description="Detection sensitivity: low, medium, high"),
    methods: Optional[str] = Query(None, description="Comma-separated methods: z_score, iqr, isolation_forest"),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a data file and start anomaly detection analysis.
    
    Args:
        file (UploadFile): CSV or XLSX file (max 5GB)
        sensitivity (str): Detection sensitivity level
        methods (Optional[str]): Detection methods to use
        background_tasks (BackgroundTasks): FastAPI background tasks
        
    Returns:
        UploadResponse: Task ID and initial status
    """
    try:
        # Validate file format
        is_valid, error = validate_file_format(file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        # Read file and validate size
        content = await file.read()
        file_size_bytes = len(content)
        
        is_valid, error = validate_file_size(file_size_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        # Save uploaded file
        task_id = generate_task_id()
        upload_dir = Path(__file__).parent / "uploads"
        upload_dir.mkdir(exist_ok=True, parents=True)
        
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filepath = upload_dir / f"{task_id}.{file_ext}"
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        logger.info(f"Saved upload: {filepath}")
        
        # Parse methods
        if methods:
            method_list = [m.strip() for m in methods.split(',')]
        else:
            method_list = ['z_score', 'iqr', 'isolation_forest']
        
        # Create task entry
        task_store[task_id] = {
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'progress': 0,
            'error': None,
            'data_points': 0,
            'kpis': 0
        }
        
        # Start background task
        background_tasks.add_task(
            process_anomaly_detection,
            task_id,
            str(filepath),
            sensitivity,
            method_list
        )
        
        logger.info(f"Task created: {task_id}")
        
        return UploadResponse(
            task_id=task_id,
            status='processing',
            message='File uploaded successfully. Analysis started.',
            filename=file.filename,
            file_size_mb=get_file_size_mb(file_size_bytes)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# ENDPOINTS: Results Retrieval
# ============================================================================

@app.get("/api/anomalies/result/{task_id}", response_model=AnalysisResult)
async def get_task_result(task_id: str):
    """
    Get complete analysis results for a task.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        AnalysisResult: Complete analysis results
    """
    try:
        # Try to load from disk first
        result = load_result_from_disk(task_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Results not found for task {task_id}"
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")
    
# ============================================================================
# CHART & ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/anomalies/charts/{task_id}")
async def get_chart_data(task_id: str):
    """Get all chart data for dashboard."""
    try:
        from chart_service import ChartService
        
        logger.info(f"[CHARTS] Loading chart data for task: {task_id}")
        result = load_result_from_disk(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Results not found for task {task_id}")
        
        chart_service = ChartService()
        dashboard_data = chart_service.get_dashboard_data(result)
        
        logger.info(f"[CHARTS] Chart data generated successfully")
        return dashboard_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHARTS] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chart error: {str(e)}")


@app.get("/api/anomalies/trends/{task_id}")
async def get_trend_analysis(task_id: str):
    """Get trend analysis for task."""
    try:
        from trend_analyzer import TrendAnalyzer
        
        logger.info(f"[TRENDS] Loading trend data for task: {task_id}")
        result = load_result_from_disk(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Results not found for task {task_id}")
        
        analyzer = TrendAnalyzer()
        trends = analyzer.get_trend_analysis(result)
        severity_insights = analyzer.get_severity_insights(result)
        kpi_insights = analyzer.get_kpi_insights(result)
        recommendations = analyzer.generate_recommendations(result)
        
        response_data = {
            'trends': trends,
            'severity_insights': severity_insights,
            'kpi_insights': kpi_insights,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"[TRENDS] Trend analysis completed successfully")
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TRENDS] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trend error: {str(e)}")


# ============================================================================
# ENDPOINTS: Task Management
# ============================================================================

@app.get("/api/anomalies/export/{task_id}/pdf")
async def export_pdf(task_id: str):
    """Export analysis results as PDF."""
    try:
        from export_service import ExportService
        
        # Load results
        result = load_result_from_disk(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Results not found")
        
        # Export to PDF
        export_service = ExportService()
        pdf_path = export_service.export_to_pdf(task_id, result)
        
        if not pdf_path:
            raise HTTPException(status_code=500, detail="PDF generation failed")
        
        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename=f"report_{task_id}.pdf"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")


@app.get("/api/anomalies/list")
async def list_tasks(limit: int = Query(50, ge=1, le=500)):
    """
    List all completed tasks.
    
    Args:
        limit (int): Maximum number of tasks to return
        
    Returns:
        list: List of tasks with metadata
    """
    try:
        tasks = list_all_tasks()
        return tasks[:limit]
    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing tasks: {str(e)}")


@app.delete("/api/anomalies/task/{task_id}")
async def delete_task_endpoint(task_id: str):
    """
    Delete a task and its results.
    
    Args:
        task_id (str): Task ID to delete
        
    Returns:
        dict: Deletion status
    """
    try:
        success = delete_task(task_id)
        
        if task_id in task_store:
            del task_store[task_id]
        
        if success:
            return {"status": "deleted", "task_id": task_id}
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")


@app.post("/api/anomalies/cleanup")
async def cleanup_results(days: int = Query(30, ge=1, le=365)):
    """
    Clean up old results.
    
    Args:
        days (int): Delete results older than this many days
        
    Returns:
        dict: Cleanup status
    """
    try:
        deleted_count = cleanup_old_results(days)
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} tasks older than {days} days"
        }
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPError",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN HANDLERS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Anomaly Detection API starting...")
    from anomaly_utils import ensure_results_dir
    ensure_results_dir()
    logger.info("Results directory initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Anomaly Detection API shutting down...")
    executor.shutdown(wait=True)
    logger.info("Background tasks completed")


# ============================================================================
# ROOT ENDPOINT - SERVES FRONTEND DASHBOARD
# ============================================================================

@app.get("/")
async def root():
    """Serve dashboard homepage."""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
