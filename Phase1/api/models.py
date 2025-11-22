"""
Pydantic Models for Phase 1 API.

Request/response schemas with automatic validation and documentation.

Models:
    FileUploadRequest: File metadata for upload
    AnalysisRequest: Request to start correlation analysis
    AnalysisStatusResponse: Current status of running analysis
    AnalysisResultResponse: Final results of completed analysis
    ErrorResponse: Standard error format for all endpoints

Usage:
    from Phase1.api.models import AnalysisRequest, AnalysisResultResponse
    
    request = AnalysisRequest(file_id="f123", target_variable="drop_rate")
    result = AnalysisResultResponse(
        task_id="t456",
        status="completed",
        ...
    )
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class FileUploadRequest(BaseModel):
    """Metadata for uploaded file."""

    filename: str = Field(
        ...,
        description="Name of uploaded file",
        example="telecom_kpi_data.csv"
    )
    file_id: str = Field(
        ...,
        description="Unique file identifier",
        example="file_12345"
    )
    file_size_bytes: int = Field(
        ...,
        description="File size in bytes",
        example=1024000
    )

    class Config:
        """Pydantic model config."""
        json_schema_extra = {
            "example": {
                "filename": "telecom_kpi_data.csv",
                "file_id": "file_12345",
                "file_size_bytes": 1024000
            }
        }


class AnalysisRequest(BaseModel):
    """Request to start correlation analysis."""

    file_id: str = Field(
        ...,
        description="ID of uploaded file to analyze",
        example="file_12345"
    )
    target_variable: str = Field(
        ...,
        description="Target variable for regression analysis",
        example="drop_rate"
    )
    correlation_method: str = Field(
        default="pearson",
        description="Correlation method: 'pearson' or 'spearman'",
        example="pearson"
    )
    test_size: float = Field(
        default=0.2,
        description="Train/test split ratio (0.0 to 1.0)",
        example=0.2
    )

    class Config:
        """Pydantic model config."""
        json_schema_extra = {
            "example": {
                "file_id": "file_12345",
                "target_variable": "drop_rate",
                "correlation_method": "pearson",
                "test_size": 0.2
            }
        }


class AnalysisStatusResponse(BaseModel):
    """Current status of analysis task."""

    task_id: str = Field(
        ...,
        description="Unique task identifier",
        example="task_abc123"
    )
    status: str = Field(
        ...,
        description="Task status: 'queued', 'processing', 'completed', 'failed'",
        example="processing"
    )
    progress_percent: int = Field(
        default=0,
        description="Progress percentage (0-100)",
        example=45
    )
    created_at: datetime = Field(
        ...,
        description="Task creation timestamp",
        example="2025-11-22T15:30:00Z"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Task start timestamp (if processing)",
        example="2025-11-22T15:31:00Z"
    )
    message: str = Field(
        default="",
        description="Status message or error description",
        example="Processing correlation analysis..."
    )

    class Config:
        """Pydantic model config."""
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "processing",
                "progress_percent": 45,
                "created_at": "2025-11-22T15:30:00Z",
                "started_at": "2025-11-22T15:31:00Z",
                "message": "Processing correlation analysis..."
            }
        }


class AnalysisResultResponse(BaseModel):
    """Final results of completed analysis."""

    task_id: str = Field(
        ...,
        description="Unique task identifier",
        example="task_abc123"
    )
    status: str = Field(
        default="completed",
        description="Task status",
        example="completed"
    )
    file_id: str = Field(
        ...,
        description="Original file ID",
        example="file_12345"
    )
    target_variable: str = Field(
        ...,
        description="Target variable analyzed",
        example="drop_rate"
    )
    correlation_matrix: Dict[str, float] = Field(
        ...,
        description="Correlation coefficients with target",
        example={"traffic": 0.85, "prb_util": 0.72, "latency": 0.91}
    )
    model_performance: Dict[str, Any] = Field(
        ...,
        description="Best model metrics (R², RMSE, MAE)",
        example={
            "model_type": "GradientBoosting",
            "r2_score": 0.89,
            "rmse": 0.15,
            "mae": 0.12
        }
    )
    p_values: Dict[str, float] = Field(
        ...,
        description="Statistical significance p-values",
        example={"traffic": 0.001, "prb_util": 0.05, "latency": 0.0001}
    )
    completed_at: datetime = Field(
        ...,
        description="Analysis completion timestamp",
        example="2025-11-22T15:32:30Z"
    )
    processing_time_seconds: float = Field(
        ...,
        description="Total processing time",
        example=90.5
    )

    class Config:
        """Pydantic model config."""
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "completed",
                "file_id": "file_12345",
                "target_variable": "drop_rate",
                "correlation_matrix": {
                    "traffic": 0.85,
                    "prb_util": 0.72,
                    "latency": 0.91
                },
                "model_performance": {
                    "model_type": "GradientBoosting",
                    "r2_score": 0.89,
                    "rmse": 0.15,
                    "mae": 0.12
                },
                "p_values": {
                    "traffic": 0.001,
                    "prb_util": 0.05,
                    "latency": 0.0001
                },
                "completed_at": "2025-11-22T15:32:30Z",
                "processing_time_seconds": 90.5
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(
        ...,
        description="Error code",
        example="FILE_VALIDATION_ERROR"
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="File format not supported. Allowed: csv, xlsx"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context",
        example={"filename": "data.txt", "supported_formats": ["csv", "xlsx"]}
    )

    class Config:
        """Pydantic model config."""
        json_schema_extra = {
            "example": {
                "error": "FILE_VALIDATION_ERROR",
                "message": "File format not supported. Allowed: csv, xlsx",
                "details": {
                    "filename": "data.txt",
                    "supported_formats": ["csv", "xlsx"]
                }
            }
        }
