"""
File Upload Handler for Phase 1.3 API.

Responsibilities:
- File validation (size, extension, format)
- Secure file storage
- File metadata management
- Error handling with custom exceptions
- Integration with storage system

Architecture:
- Single responsibility: Handle uploads
- Type-safe: 100% type hints
- Error classification: Use custom exceptions
- Logging: All operations logged
- Testable: Pure functions where possible

Usage:
    from Phase1.api.upload_handler import FileUploadHandler
    
    handler = FileUploadHandler()
    file_id = handler.save_uploaded_file(
        filename="data.csv",
        file_content=b"...",
        file_size_bytes=1024
    )
"""

import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from Phase1.config import Config
from Phase1.utils.errors import FileValidationError, StorageError

logger = logging.getLogger(__name__)


class FileUploadHandler:
    """Handle file uploads with validation and storage."""

    def __init__(self) -> None:
        """Initialize upload handler."""
        self.upload_dir = Config.get_upload_directory()
        logger.debug(f"FileUploadHandler initialized with dir: {self.upload_dir}")

    def validate_file(
        self,
        filename: str,
        file_size_bytes: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file before storage.

        Args:
            filename: Name of file to validate
            file_size_bytes: Size of file in bytes

        Returns:
            Tuple of (is_valid, error_message)

        Raises:
            FileValidationError: If validation fails
        """
        logger.debug(f"Validating file: {filename}, size: {file_size_bytes} bytes")

        # Check filename not empty
        if not filename or not filename.strip():
            error_msg = "Filename cannot be empty"
            logger.warning(error_msg)
            raise FileValidationError(error_msg, filename)

        # Check extension is allowed
        if not Config.is_allowed_extension(filename):
            allowed = ", ".join(Config.ALLOWED_EXTENSIONS)
            error_msg = f"File extension not allowed. Supported: {allowed}"
            logger.warning(f"{error_msg} - File: {filename}")
            raise FileValidationError(
                error_msg,
                filename,
                details={"allowed_extensions": list(Config.ALLOWED_EXTENSIONS)}
            )

        # Check file size
        if file_size_bytes <= 0:
            error_msg = f"Invalid file size: {file_size_bytes} bytes"
            logger.warning(error_msg)
            raise FileValidationError(error_msg, filename)

        if file_size_bytes > Config.MAX_FILE_SIZE_BYTES:
            max_mb = Config.get_max_file_size_display()
            error_msg = f"File too large. Max: {max_mb}"
            logger.warning(f"{error_msg} - Actual: {file_size_bytes} bytes")
            raise FileValidationError(
                error_msg,
                filename,
                details={
                    "max_bytes": Config.MAX_FILE_SIZE_BYTES,
                    "actual_bytes": file_size_bytes,
                    "max_display": max_mb
                }
            )

        logger.debug(f"File validation passed: {filename}")
        return True, None

    def save_uploaded_file(
        self,
        filename: str,
        file_content: bytes,
        file_size_bytes: int
    ) -> str:
        """
        Save uploaded file to storage.

        Args:
            filename: Original filename
            file_content: File bytes
            file_size_bytes: File size in bytes

        Returns:
            Unique file ID for later retrieval

        Raises:
            FileValidationError: If file validation fails
            StorageError: If storage operation fails
        """
        logger.info(f"Processing upload: {filename}, size: {file_size_bytes} bytes")

        try:
            # Validate file
            self.validate_file(filename, file_size_bytes)

            # Generate unique file ID
            file_id = self._generate_file_id()
            logger.debug(f"Generated file_id: {file_id}")

            # Create storage subdirectory by date for organization
            date_dir = self._get_date_directory()
            storage_path = self.upload_dir / date_dir / file_id

            # Create directory structure
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {storage_path.parent}")

            # Save file
            storage_path.write_bytes(file_content)
            logger.info(f"File saved successfully: {file_id}")

            # Save metadata
            metadata_path = storage_path.with_suffix(".meta")
            self._save_metadata(metadata_path, filename, file_size_bytes, file_id)
            logger.debug(f"Metadata saved: {metadata_path}")

            return file_id

        except FileValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to save file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg, filename)

    def get_file_path(self, file_id: str) -> Path:
        """
        Get path to stored file.

        Args:
            file_id: Unique file identifier

        Returns:
            Path to file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        logger.debug(f"Looking up file path for: {file_id}")

        # Search for file in date subdirectories
        for date_dir in self.upload_dir.iterdir():
            if not date_dir.is_dir():
                continue

            file_path = date_dir / file_id
            if file_path.exists():
                logger.debug(f"Found file: {file_path}")
                return file_path

        error_msg = f"File not found: {file_id}"
        logger.warning(error_msg)
        raise FileNotFoundError(error_msg)

    def get_file_content(self, file_id: str) -> bytes:
        """
        Retrieve file content by ID.

        Args:
            file_id: Unique file identifier

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If read operation fails
        """
        logger.debug(f"Retrieving file content: {file_id}")

        try:
            file_path = self.get_file_path(file_id)
            content = file_path.read_bytes()
            logger.debug(f"File content retrieved: {len(content)} bytes")
            return content
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg)

    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_id: Unique file identifier

        Returns:
            True if deleted, False if not found

        Raises:
            StorageError: If deletion fails
        """
        logger.debug(f"Deleting file: {file_id}")

        try:
            file_path = self.get_file_path(file_id)
            file_path.unlink()
            logger.info(f"File deleted: {file_id}")

            # Also delete metadata
            meta_path = file_path.with_suffix(".meta")
            if meta_path.exists():
                meta_path.unlink()
                logger.debug(f"Metadata deleted: {meta_path}")

            return True
        except FileNotFoundError:
            logger.warning(f"File not found for deletion: {file_id}")
            return False
        except Exception as e:
            error_msg = f"Failed to delete file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg, file_id)

    def _generate_file_id(self) -> str:
        """
        Generate unique file identifier.

        Returns:
            UUID-based file ID
        """
        return str(uuid.uuid4())

    def _get_date_directory(self) -> str:
        """
        Get date-based directory name for file organization.

        Returns:
            Directory name in format YYYY-MM-DD
        """
        return datetime.now().strftime("%Y-%m-%d")

    def _save_metadata(
        self,
        metadata_path: Path,
        filename: str,
        file_size_bytes: int,
        file_id: str
    ) -> None:
        """
        Save file metadata for tracking.

        Args:
            metadata_path: Path to metadata file
            filename: Original filename
            file_size_bytes: File size in bytes
            file_id: Unique file ID
        """
        import json

        metadata = {
            "file_id": file_id,
            "original_filename": filename,
            "file_size_bytes": file_size_bytes,
            "uploaded_at": datetime.now().isoformat(),
            "status": "ready"
        }

        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        logger.debug(f"Metadata saved: {metadata}")
