"""
FastAPI Router for Phase 1.3 API.

Responsibilities:
- Register all REST API endpoints
- Orchestrate file upload → analysis → result workflow
- Request/response validation with Pydantic models
- Error handling and response formatting
- Integration with orchestrator and handlers

Endpoints:
    POST /api/correlation/analyze - Queue analysis
    GET /api/correlation/status/{task_id} - Get task status
    GET /api/correlation/result/{task_id} - Get results
    POST /api/correlation/upload - Upload file
    GET /api/health/detailed - Infrastructure status

Architecture:
- Single responsibility: Endpoint coordination
- Type-safe: 100% type hints
- Error handling: Comprehensive with custom exceptions
- Logging: All requests/responses logged
- Testable: Dependency injection for orchestrator

Usage:
    from Phase1.api.router import create_api_router
    
    app = FastAPI()
    router = create_api_router(orchestrator, upload_handler, analysis_endpoint)
    app.include_router(router, prefix="/api")
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from datetime import datetime

from Phase1.api.models import (
    AnalysisRequest,
    AnalysisStatusResponse,
    AnalysisResultResponse,
    ErrorResponse,
)
from Phase1.api.upload_handler import FileUploadHandler
from Phase1.api.analysis_endpoint import AnalysisEndpoint
from Phase1.api.result_formatter import ResultFormatter
from Phase1.utils.errors import (
    FileValidationError,
    TaskQueueError,
    ResultNormalizationError,
)

logger = logging.getLogger(__name__)


def create_api_router(
    orchestrator: Any,
    upload_handler: FileUploadHandler,
    analysis_endpoint: AnalysisEndpoint,
    result_formatter: ResultFormatter
) -> APIRouter:
    """
    Create FastAPI router with all endpoints.

    Args:
        orchestrator: Phase 0 orchestrator instance
        upload_handler: File upload handler
        analysis_endpoint: Analysis task manager
        result_formatter: Result formatting utility

    Returns:
        Configured FastAPI router
    """
    router = APIRouter()

    logger.info("Creating API router with all endpoints")

    @router.post(
        "/correlation/upload",
        response_model=Dict[str, str],
        status_code=status.HTTP_200_OK,
        summary="Upload file for analysis",
        tags=["File Operations"]
    )
    async def upload_file(
        file: UploadFile = File(...)
    ) -> Dict[str, str]:
        """
        Upload CSV/Excel file for correlation analysis.

        Args:
            file: File to upload (CSV or Excel)

        Returns:
            File ID for later retrieval

        Raises:
            HTTPException: If upload fails
        """
        logger.info(f"File upload request: {file.filename}")

        try:
            # Read file content
            content = await file.read()
            file_size = len(content)

            logger.debug(f"Read file: {file.filename}, size: {file_size} bytes")

            # Save file
            file_id = upload_handler.save_uploaded_file(
                filename=file.filename or "unknown",
                file_content=content,
                file_size_bytes=file_size
            )

            logger.info(f"File uploaded successfully: {file_id}")

            return {
                "file_id": file_id,
                "filename": file.filename,
                "size_bytes": file_size,
                "uploaded_at": datetime.now().isoformat()
            }

        except FileValidationError as e:
            logger.warning(f"File validation failed: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "UPLOAD_FAILED", "message": str(e)}
            )

    @router.post(
        "/correlation/analyze",
        response_model=Dict[str, str],
        status_code=status.HTTP_202_ACCEPTED,
        summary="Queue correlation analysis",
        tags=["Analysis"]
    )
    async def queue_analysis(
        request: AnalysisRequest
    ) -> Dict[str, str]:
        """
        Queue a new correlation analysis task.

        Args:
            request: Analysis request with file_id and parameters

        Returns:
            Task ID for status tracking

        Raises:
            HTTPException: If queuing fails
        """
        logger.info(f"Analysis request: file={request.file_id}, target={request.target_variable}")

        try:
            # Queue analysis
            task_id = analysis_endpoint.queue_analysis(
                file_id=request.file_id,
                target_variable=request.target_variable,
                correlation_method=request.correlation_method,
                test_size=request.test_size
            )

            logger.info(f"Analysis queued: {task_id}")

            return {
                "task_id": task_id,
                "status": "queued",
                "message": "Analysis task queued successfully",
                "queued_at": datetime.now().isoformat()
            }

        except TaskQueueError as e:
            logger.warning(f"Queue failed: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        except Exception as e:
            logger.error(f"Queue failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "QUEUE_FAILED", "message": str(e)}
            )

    @router.get(
        "/correlation/status/{task_id}",
        response_model=Dict[str, Any],
        status_code=status.HTTP_200_OK,
        summary="Get analysis task status",
        tags=["Analysis"]
    )
    async def get_analysis_status(task_id: str) -> Dict[str, Any]:
        """
        Get current status of analysis task.

        Args:
            task_id: Task identifier

        Returns:
            Task status with progress

        Raises:
            HTTPException: If task not found
        """
        logger.debug(f"Status request: {task_id}")

        try:
            status_dict = analysis_endpoint.get_task_status(task_id)
            logger.debug(f"Status retrieved: {task_id}")
            return status_dict

        except TaskQueueError as e:
            logger.warning(f"Task not found: {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.to_dict()
            )
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "STATUS_FAILED", "message": str(e)}
            )

    @router.get(
        "/correlation/result/{task_id}",
        response_model=Dict[str, Any],
        status_code=status.HTTP_200_OK,
        summary="Get analysis results",
        tags=["Results"]
    )
    async def get_analysis_result(task_id: str) -> Dict[str, Any]:
        """
        Get results of completed analysis.

        Args:
            task_id: Task identifier

        Returns:
            Analysis results if completed

        Raises:
            HTTPException: If task not found or still processing
        """
        logger.debug(f"Result request: {task_id}")

        try:
            # Get result from endpoint
            result = analysis_endpoint.get_task_result(task_id)

            if result is None:
                logger.debug(f"Result not ready: {task_id}")
                raise HTTPException(
                    status_code=status.HTTP_202_ACCEPTED,
                    detail={
                        "task_id": task_id,
                        "message": "Analysis still processing, check status endpoint"
                    }
                )

            logger.info(f"Result retrieved: {task_id}")
            return result

        except TaskQueueError as e:
            logger.warning(f"Task error: {task_id}, {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        except Exception as e:
            logger.error(f"Result retrieval failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "RESULT_FAILED", "message": str(e)}
            )

    @router.get(
        "/health/detailed",
        response_model=Dict[str, Any],
        status_code=status.HTTP_200_OK,
        summary="Detailed system health check",
        tags=["Health"]
    )
    async def health_check_detailed() -> Dict[str, Any]:
        """
        Get detailed system health status.

        Returns:
            Health status of all components
        """
        logger.debug("Health check requested")

        try:
            task_summary = analysis_endpoint.get_task_summary()

            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "orchestrator": "operational",
                    "upload_handler": "operational",
                    "analysis_endpoint": "operational",
                    "result_formatter": "operational"
                },
                "tasks": task_summary,
                "api_version": "1.3.0"
            }

            logger.debug("Health check completed")
            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return {
                "status": "degraded",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    logger.info("API router created successfully")
    return router
