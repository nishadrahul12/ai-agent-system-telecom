"""
Unit tests for Phase 1 utilities.

Tests:
- Logging configuration (file creation, handler setup)
- Custom exception classes (instantiation, serialization)
- Error code generation
"""

import unittest
import logging
import tempfile
from pathlib import Path
from Phase1.utils.logging_config import setup_logging
from Phase1.utils.errors import (
    FileValidationError,
    AgentInitializationError,
    ResultNormalizationError,
)


class TestLoggingConfig(unittest.TestCase):
    """Test logging setup utilities."""

    def test_logger_creation(self) -> None:
        """Test that logger is created successfully."""
        logger = setup_logging("test_logger_unique_001")
        self.assertIsNotNone(logger)
        self.assertIn("test_logger", logger.name)

    def test_logger_level(self) -> None:
        """Test logger level is set correctly."""
        logger = setup_logging("test_level_unique_002", level=logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_logger_handlers(self) -> None:
        """Test logger has both console and file handlers."""
        logger = setup_logging("test_handlers_unique_003")
        # Should have at least 2 handlers (console + file)
        self.assertGreaterEqual(len(logger.handlers), 2)
        handler_types = {type(h).__name__ for h in logger.handlers}
        self.assertIn("StreamHandler", handler_types)
        self.assertIn("FileHandler", handler_types)

    def test_default_log_directory_created(self) -> None:
        """Test that default logs directory is created."""
        logger = setup_logging("test_default_dir_unique_004")
        
        # Check that logs directory exists
        log_dir = Path(__file__).parent.parent.parent / "logs"
        self.assertTrue(
            log_dir.exists(),
            f"Logs directory not created at {log_dir}"
        )
        
        # Check that log file was created
        log_file = log_dir / "phase1_api.log"
        self.assertTrue(
            log_file.exists(),
            f"Log file not created at {log_file}"
        )

        
        # Remove handlers to release file lock before temp cleanup
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)



class TestCustomErrors(unittest.TestCase):
    """Test custom exception classes."""

    def test_file_validation_error(self) -> None:
        """Test FileValidationError creation and serialization."""
        error = FileValidationError(
            message="Invalid CSV format",
            filename="test.txt"
        )
        self.assertEqual(error.error_code, "FILE_VALIDATION_ERROR")
        self.assertIn("filename", error.details)
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict["error"], "FILE_VALIDATION_ERROR")
        self.assertIn("message", error_dict)

    def test_agent_initialization_error(self) -> None:
        """Test AgentInitializationError creation."""
        error = AgentInitializationError(
            message="Agent failed to start",
            agent_id="correlation_001"
        )
        self.assertEqual(error.error_code, "AGENT_INIT_ERROR")
        self.assertEqual(error.details["agent_id"], "correlation_001")

    def test_result_normalization_error(self) -> None:
        """Test ResultNormalizationError creation."""
        error = ResultNormalizationError(
            message="Invalid field format",
            field="correlation_matrix"
        )
        self.assertEqual(error.error_code, "RESULT_NORMALIZATION_ERROR")
        self.assertEqual(error.details["field"], "correlation_matrix")

    def test_error_to_dict(self) -> None:
        """Test error serialization to dictionary."""
        error = FileValidationError(
            message="File too large",
            filename="huge.csv",
            details={"size_mb": 550}
        )
        error_dict = error.to_dict()
        self.assertIn("error", error_dict)
        self.assertIn("message", error_dict)
        self.assertIn("details", error_dict)
        self.assertEqual(error_dict["details"]["size_mb"], 550)


if __name__ == "__main__":
    unittest.main()
