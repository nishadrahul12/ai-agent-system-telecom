"""
anomaly_models.py - Phase 3 API Data Models (FIXED FOR PYDANTIC V2)
Pydantic models for API requests, responses, and persistent storage
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class SensitivityLevel(str, Enum):
    """Sensitivity levels for anomaly detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnomalyMethod(str, Enum):
    """Available anomaly detection methods."""
    ZSCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"


class TaskStatus(str, Enum):
    """Task processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class NetworkStatus(str, Enum):
    """Network health status."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class AnalysisParameters(BaseModel):
    """Parameters for anomaly analysis."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sensitivity": "medium",
            "methods": ["z_score", "iqr", "isolation_forest"]
        }
    })
    
    sensitivity: SensitivityLevel = Field(default=SensitivityLevel.MEDIUM, description="Detection sensitivity")
    methods: List[AnomalyMethod] = Field(
        default=[AnomalyMethod.ZSCORE, AnomalyMethod.IQR, AnomalyMethod.ISOLATION_FOREST],
        description="Detection methods to use"
    )


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class AnomalyDetail(BaseModel):
    """Single detected anomaly."""
    kpi: str = Field(..., description="KPI name")
    value: float = Field(..., description="Anomalous value")
    normalized_value: float = Field(..., description="Normalized value")
    severity: str = Field(..., description="CRITICAL, WARNING, or NORMAL")
    method: str = Field(..., description="Detection method used")
    anomaly_score: float = Field(..., description="Anomaly score (higher = more anomalous)")
    index: int = Field(..., description="Row index in data")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "kpi": "latency",
            "value": 200.5,
            "normalized_value": 3.2,
            "severity": "critical",
            "method": "z_score",
            "anomaly_score": 3.5,
            "index": 42
        }
    })


class NetworkClassification(BaseModel):
    """Overall network health classification."""
    network_status: str = Field(..., description="NORMAL, WARNING, or CRITICAL")
    critical_count: int = Field(..., description="Number of critical anomalies")
    warning_count: int = Field(..., description="Number of warning anomalies")
    total_anomalies: int = Field(..., description="Total anomalies detected")
    affected_kpis: List[str] = Field(..., description="List of affected KPI names")
    affected_kpi_count: int = Field(..., description="Count of affected KPIs")


class AnalysisSummary(BaseModel):
    """Summary of anomaly detection analysis."""
    detection_timestamp: str = Field(..., description="ISO timestamp of analysis")
    sensitivity: str = Field(..., description="Sensitivity level used")
    methods_used: List[str] = Field(..., description="Detection methods used")
    data_points_analyzed: int = Field(..., description="Number of rows analyzed")
    kpis_analyzed: int = Field(..., description="Number of KPIs analyzed")
    total_anomalies: int = Field(..., description="Total anomalies found")
    anomalies_by_method: Dict[str, int] = Field(..., description="Count by method")
    anomalies_by_kpi: Dict[str, int] = Field(..., description="Count by KPI")
    network_status: NetworkClassification = Field(..., description="Network health")


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    timestamp: str = Field(..., description="ISO timestamp")
    summary: AnalysisSummary = Field(..., description="Analysis summary")
    anomalies: List[AnomalyDetail] = Field(..., description="Detected anomalies")
    network_classification: NetworkClassification = Field(..., description="Network status")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "task_id": "task_20251124_001",
            "status": "completed",
            "timestamp": "2025-11-24T16:50:00Z",
            "summary": {
                "detection_timestamp": "2025-11-24T16:50:00Z",
                "sensitivity": "medium",
                "methods_used": ["z_score", "iqr", "isolation_forest"],
                "data_points_analyzed": 1000,
                "kpis_analyzed": 60,
                "total_anomalies": 45,
                "anomalies_by_method": {"z_score": 15, "iqr": 20, "isolation_forest": 10},
                "anomalies_by_kpi": {"KPI_1": 5, "KPI_2": 3}
            },
            "anomalies": [],
            "network_classification": {
                "network_status": "warning",
                "critical_count": 5,
                "warning_count": 40,
                "total_anomalies": 45,
                "affected_kpis": ["KPI_1", "KPI_2"],
                "affected_kpi_count": 2
            }
        }
    })


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status: pending, processing, completed, failed")
    created_at: str = Field(..., description="ISO timestamp of task creation")
    progress_percent: int = Field(..., description="Progress percentage (0-100)")
    message: Optional[str] = Field(default=None, description="Status message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "task_id": "task_20251124_001",
            "status": "processing",
            "created_at": "2025-11-24T16:50:00Z",
            "progress_percent": 65,
            "message": "Running anomaly detection methods...",
            "error": None
        }
    })


class UploadResponse(BaseModel):
    """Response after file upload."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Human-readable message")
    filename: str = Field(..., description="Uploaded filename")
    file_size_mb: float = Field(..., description="File size in MB")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "task_id": "task_20251124_001",
            "status": "processing",
            "message": "File uploaded successfully. Analysis started.",
            "filename": "network_data.csv",
            "file_size_mb": 25.5
        }
    })


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": "ValidationError",
            "message": "File size exceeds 5GB limit",
            "details": {"max_size_gb": 5, "provided_size_gb": 6.5}
        }
    })


# ============================================================================
# DATABASE MODELS (For disk persistence)
# ============================================================================

class TaskMetadata(BaseModel):
    """Task metadata for persistent storage."""
    task_id: str
    filename: str
    file_size_bytes: int
    format: str  # "csv" or "xlsx"
    sensitivity: str
    methods: List[str]
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    data_points: int
    kpis_count: int
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "task_id": "task_20251124_001",
            "filename": "network_data.csv",
            "file_size_bytes": 26843545,
            "format": "csv",
            "sensitivity": "medium",
            "methods": ["z_score", "iqr", "isolation_forest"],
            "created_at": "2025-11-24T16:50:00Z",
            "started_at": "2025-11-24T16:50:02Z",
            "completed_at": "2025-11-24T16:52:30Z",
            "status": "completed",
            "error_message": None,
            "data_points": 1000,
            "kpis_count": 60
        }
    })
