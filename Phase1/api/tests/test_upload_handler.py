"""
Unit tests for FileUploadHandler.

Test coverage:
- File validation (size, extension, format)
- Successful file storage
- File retrieval
- File deletion
- Error handling
- Edge cases
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from Phase1.api.upload_handler import FileUploadHandler
from Phase1.utils.errors import FileValidationError, StorageError


class TestFileUploadHandler(unittest.TestCase):
    """Test suite for FileUploadHandler."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.handler = FileUploadHandler()
        self.test_filename = "test_data.csv"
        self.test_content = b"col1,col2,col3\n1,2,3\n4,5,6"
        self.test_size = len(self.test_content)

    def test_validate_file_valid(self) -> None:
        """Test validation passes for valid file."""
        is_valid, error = self.handler.validate_file(
            self.test_filename,
            self.test_size
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_file_empty_filename(self) -> None:
        """Test validation fails for empty filename."""
        with self.assertRaises(FileValidationError) as context:
            self.handler.validate_file("", self.test_size)
        
        self.assertIn("empty", str(context.exception).lower())

    def test_validate_file_invalid_extension(self) -> None:
        """Test validation fails for unsupported extension."""
        with self.assertRaises(FileValidationError) as context:
            self.handler.validate_file("data.txt", self.test_size)
        
        self.assertIn("not allowed", str(context.exception).lower())

    def test_validate_file_zero_size(self) -> None:
        """Test validation fails for zero-size file."""
        with self.assertRaises(FileValidationError) as context:
            self.handler.validate_file(self.test_filename, 0)
        
        self.assertIn("invalid", str(context.exception).lower())

    def test_validate_file_too_large(self) -> None:
        """Test validation fails for oversized file."""
        from Phase1.config import Config
        oversized = Config.MAX_FILE_SIZE_BYTES + 1

        with self.assertRaises(FileValidationError) as context:
            self.handler.validate_file(self.test_filename, oversized)
        
        self.assertIn("too large", str(context.exception).lower())

    def test_save_file_success(self) -> None:
        """Test successful file storage."""
        file_id = self.handler.save_uploaded_file(
            self.test_filename,
            self.test_content,
            self.test_size
        )

        self.assertIsNotNone(file_id)
        self.assertTrue(len(file_id) > 0)

        # Verify file exists
        file_path = self.handler.get_file_path(file_id)
        self.assertTrue(file_path.exists())

    def test_save_file_invalid(self) -> None:
        """Test storage fails for invalid file."""
        with self.assertRaises(FileValidationError):
            self.handler.save_uploaded_file(
                "invalid.txt",
                self.test_content,
                self.test_size
            )

    def test_get_file_content(self) -> None:
        """Test file content retrieval."""
        file_id = self.handler.save_uploaded_file(
            self.test_filename,
            self.test_content,
            self.test_size
        )

        retrieved = self.handler.get_file_content(file_id)
        self.assertEqual(retrieved, self.test_content)

    def test_get_file_not_found(self) -> None:
        """Test retrieval fails for non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.handler.get_file_content("nonexistent_id")

    def test_delete_file_success(self) -> None:
        """Test successful file deletion."""
        file_id = self.handler.save_uploaded_file(
            self.test_filename,
            self.test_content,
            self.test_size
        )

        result = self.handler.delete_file(file_id)
        self.assertTrue(result)

        # Verify file is deleted
        with self.assertRaises(FileNotFoundError):
            self.handler.get_file_path(file_id)

    def test_delete_file_not_found(self) -> None:
        """Test deletion returns False for non-existent file."""
        result = self.handler.delete_file("nonexistent_id")
        self.assertFalse(result)

    def test_metadata_saved(self) -> None:
        """Test metadata is saved alongside file."""
        file_id = self.handler.save_uploaded_file(
            self.test_filename,
            self.test_content,
            self.test_size
        )

        file_path = self.handler.get_file_path(file_id)
        meta_path = file_path.with_suffix(".meta")
        
        self.assertTrue(meta_path.exists())

        # Verify metadata content
        import json
        metadata = json.loads(meta_path.read_text())
        self.assertEqual(metadata["file_id"], file_id)
        self.assertEqual(metadata["original_filename"], self.test_filename)
        self.assertEqual(metadata["file_size_bytes"], self.test_size)


if __name__ == "__main__":
    unittest.main()
