"""
Centralized logging configuration for Phase 1 API.

Features:
- UTF-8 safe file handlers (prevents UnicodeEncodeError on Windows)
- Separate DEBUG (file) and INFO (console) levels
- Structured log format with timestamps and context
- No emoji in production code
- Lazy initialization to prevent duplicate handlers

Usage:
    from Phase1.utils.logging_config import setup_logging
    logger = setup_logging(__name__)
    logger.info("System initialized")
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.DEBUG
) -> logging.Logger:
    """
    Configure logger with file and console handlers.

    Args:
        name: Logger name (typically __name__)
        log_file: Path to log file. If None, uses logs/phase1_api.log
        level: Logging level (default: DEBUG)

    Returns:
        Configured logger instance

    Example:
        logger = setup_logging(__name__)
        logger.debug("Detailed info")
        logger.info("General info")
        logger.warning("Warning message")
        logger.error("Error occurred")
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Default log file path
    if log_file is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "phase1_api.log"
    
    # Console handler: INFO level (user-facing)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler: DEBUG level (detailed diagnostics)
    # UTF-8 encoding prevents Windows UnicodeEncodeError
    file_handler = logging.FileHandler(
        log_file,
        mode="a",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Attach handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Module-level logger for this file
_logger = setup_logging(__name__)
_logger.debug("Logging system initialized")
