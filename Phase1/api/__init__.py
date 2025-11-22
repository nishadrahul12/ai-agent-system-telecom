"""
Phase 1 API Package.

Main entry point for all REST API functionality.

Submodules:
    config: API configuration and constants
    models: Pydantic request/response schemas
    upload_handler: File upload and validation (coming Day 2)
    analysis_endpoint: Task lifecycle management (coming Day 2)
    result_formatter: Result normalization (coming Day 3)
    router: FastAPI router with all endpoints (coming Day 4)
    tests: Comprehensive test suite

Example Usage:
    from Phase1.api.models import AnalysisRequest, AnalysisResultResponse
    from Phase1.api.router import create_api_router
    
    app = FastAPI()
    api_router = create_api_router()
    app.include_router(api_router, prefix="/api")
"""

from Phase1.api.models import (
    FileUploadRequest,
    AnalysisRequest,
    AnalysisStatusResponse,
    AnalysisResultResponse,
    ErrorResponse,
)

__version__ = "1.3.0"
__all__ = [
    "FileUploadRequest",
    "AnalysisRequest",
    "AnalysisStatusResponse",
    "AnalysisResultResponse",
    "ErrorResponse",
]
