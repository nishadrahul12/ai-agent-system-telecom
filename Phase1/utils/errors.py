"""
Custom exception types for Phase 1 API.

Provides granular error classification for better debugging and monitoring.

Exception Hierarchy:
    Phase1Error (base)
    ├── UploadError
    │   ├── FileValidationError
    │   └── StorageError
    ├── AnalysisError
    │   ├── AgentInitializationError
    │   └── TaskQueueError
    └── FormatterError
        └── ResultNormalizationError

Usage:
    from Phase1.utils.errors import FileValidationError, TaskQueueError
    
    try:
        validate_file(filename)
    except FileValidationError as e:
        logger.error(f"Invalid file: {e}")
        raise
"""

from typing import Optional


class Phase1Error(Exception):
    """Base exception for all Phase 1 API errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "PHASE1_ERROR",
        details: Optional[dict] = None
    ) -> None:
        """
        Initialize Phase1Error.

        Args:
            message: Human-readable error description
            error_code: Machine-readable error identifier
            details: Additional context (file size, line number, etc.)
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert error to API response format."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class UploadError(Phase1Error):
    """Base exception for file upload operations."""

    def __init__(
        self,
        message: str,
        error_code: str = "UPLOAD_ERROR",
        details: Optional[dict] = None
    ) -> None:
        """Initialize UploadError."""
        super().__init__(message, error_code, details)


class FileValidationError(UploadError):
    """Raised when file validation fails."""

    def __init__(
        self,
        message: str,
        filename: str = "",
        details: Optional[dict] = None
    ) -> None:
        """
        Initialize FileValidationError.

        Args:
            message: Error description
            filename: Name of invalid file
            details: Additional validation context
        """
        full_details = details or {}
        full_details["filename"] = filename
        super().__init__(
            message,
            error_code="FILE_VALIDATION_ERROR",
            details=full_details
        )


class StorageError(UploadError):
    """Raised when file storage operation fails."""

    def __init__(
        self,
        message: str,
        filename: str = "",
        details: Optional[dict] = None
    ) -> None:
        """
        Initialize StorageError.

        Args:
            message: Error description
            filename: Name of file causing storage error
            details: Additional storage context
        """
        full_details = details or {}
        full_details["filename"] = filename
        super().__init__(
            message,
            error_code="STORAGE_ERROR",
            details=full_details
        )


class AnalysisError(Phase1Error):
    """Base exception for analysis operations."""

    def __init__(
        self,
        message: str,
        error_code: str = "ANALYSIS_ERROR",
        details: Optional[dict] = None
    ) -> None:
        """Initialize AnalysisError."""
        super().__init__(message, error_code, details)


class AgentInitializationError(AnalysisError):
    """Raised when agent fails to initialize."""

    def __init__(
        self,
        message: str,
        agent_id: str = "",
        details: Optional[dict] = None
    ) -> None:
        """
        Initialize AgentInitializationError.

        Args:
            message: Error description
            agent_id: ID of failed agent
            details: Initialization context
        """
        full_details = details or {}
        full_details["agent_id"] = agent_id
        super().__init__(
            message,
            error_code="AGENT_INIT_ERROR",
            details=full_details
        )


class TaskQueueError(AnalysisError):
    """Raised when task queuing fails."""

    def __init__(
        self,
        message: str,
        task_id: str = "",
        details: Optional[dict] = None
    ) -> None:
        """
        Initialize TaskQueueError.

        Args:
            message: Error description
            task_id: ID of failed task
            details: Queue context
        """
        full_details = details or {}
        full_details["task_id"] = task_id
        super().__init__(
            message,
            error_code="TASK_QUEUE_ERROR",
            details=full_details
        )


class FormatterError(Phase1Error):
    """Base exception for result formatting operations."""

    def __init__(
        self,
        message: str,
        error_code: str = "FORMATTER_ERROR",
        details: Optional[dict] = None
    ) -> None:
        """Initialize FormatterError."""
        super().__init__(message, error_code, details)


class ResultNormalizationError(FormatterError):
    """Raised when result normalization fails."""

    def __init__(
        self,
        message: str,
        field: str = "",
        details: Optional[dict] = None
    ) -> None:
        """
        Initialize ResultNormalizationError.

        Args:
            message: Error description
            field: Field causing normalization error
            details: Normalization context
        """
        full_details = details or {}
        full_details["field"] = field
        super().__init__(
            message,
            error_code="RESULT_NORMALIZATION_ERROR",
            details=full_details
        )
