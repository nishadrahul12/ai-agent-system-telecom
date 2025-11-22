"""
Phase 1 Configuration Management.

Centralizes all settings, paths, and constants for API operations.
Supports environment-based configuration (DEBUG, PROD modes).

Environment Variables:
    PHASE1_DEBUG: Enable debug mode (default: False)
    PHASE1_UPLOAD_DIR: Upload directory (default: data/uploads)
    PHASE1_MAX_FILE_SIZE_MB: Max file size in MB (default: 100)
    PHASE1_ALLOWED_EXTENSIONS: Comma-separated extensions (default: csv,xlsx)

Usage:
    from Phase1.config import Config, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
    
    if Config.DEBUG:
        print("Debug mode enabled")
    
    upload_dir = Config.upload_directory()
"""

import os
from pathlib import Path
from typing import Set


class Config:
    """Central configuration for Phase 1 API."""

    # ============= DEBUG MODE =============
    DEBUG: bool = os.getenv("PHASE1_DEBUG", "False").lower() == "true"

    # ============= PATHS =============
    # Project root: AI-AGENT-SYSTEM-TELECOM/
    PROJECT_ROOT: Path = Path(__file__).parent.parent

    # Data directories
    DATA_DIR: Path = PROJECT_ROOT / "data"
    UPLOAD_DIR: Path = PROJECT_ROOT / "data" / "uploads"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    TEMP_DIR: Path = PROJECT_ROOT / "data" / "temp"

    # Database
    DATABASE_FILE: Path = DATA_DIR / "ai_agent_system.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_FILE}"

    # ============= FILE HANDLING =============
    # Max file size: 100 MB (configurable)
    MAX_FILE_SIZE_BYTES: int = (
        int(os.getenv("PHASE1_MAX_FILE_SIZE_MB", "100")) * 1024 * 1024
    )

    # Allowed file extensions
    ALLOWED_EXTENSIONS: Set[str] = set(
        os.getenv("PHASE1_ALLOWED_EXTENSIONS", "csv,xlsx").split(",")
    )

    # ============= API SETTINGS =============
    # Task lifecycle
    TASK_TIMEOUT_SECONDS: int = 300  # 5 minutes for analysis
    TASK_POLLING_INTERVAL_MS: int = 500  # Check status every 500ms
    MAX_TASK_RETRIES: int = 3

    # ============= AGENT SETTINGS =============
    CORRELATION_AGENT_ID: str = "correlation_001"
    CORRELATION_AGENT_VERSION: str = "1.0.0"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create all required directories if they don't exist."""
        for directory in [cls.DATA_DIR, cls.UPLOAD_DIR, cls.LOGS_DIR, cls.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_upload_directory(cls) -> Path:
        """Get upload directory path, creating if needed."""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        return cls.UPLOAD_DIR

    @classmethod
    def is_allowed_extension(cls, filename: str) -> bool:
        """
        Check if file extension is allowed.

        Args:
            filename: Name of file to check

        Returns:
            True if extension is in allowed list, False otherwise
        """
        if "." not in filename:
            return False
        extension = filename.rsplit(".", 1)[1].lower()
        return extension in cls.ALLOWED_EXTENSIONS

    @classmethod
    def get_max_file_size_display(cls) -> str:
        """
        Get human-readable max file size.

        Returns:
            Formatted string like "100 MB"
        """
        mb = cls.MAX_FILE_SIZE_BYTES / (1024 * 1024)
        return f"{int(mb)} MB"


# Export commonly used settings for convenience
DEBUG_MODE: bool = Config.DEBUG
UPLOAD_DIRECTORY: Path = Config.UPLOAD_DIR
ALLOWED_EXTENSIONS: Set[str] = Config.ALLOWED_EXTENSIONS
MAX_FILE_SIZE_MB: int = Config.MAX_FILE_SIZE_BYTES // (1024 * 1024)
DATABASE_URL: str = Config.DATABASE_URL

# Initialize directories on import
Config.ensure_directories()
