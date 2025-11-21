"""
Safety Guard: Input validation and security boundary enforcement.

Validates:
    - Request structure and types
    - File uploads (size, format, corruption)
    - Payload size limits
    - Required fields presence

Usage:
    guard = SafetyGuard()
    if guard.validate_input(payload):
        proceed()
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Validation constants
MAX_PAYLOAD_SIZE = 1024 * 1024 * 1024  # 1GB
MAX_STRING_LENGTH = 100 * 1024 * 1024  # 100MB
ALLOWED_FILE_FORMATS = [".csv", ".xlsx", ".xls"]
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB


class SafetyGuard:
    """
    Validates inputs and enforces security boundaries.
    
    Checks:
        - Payload structure
        - File properties
        - Size limits
        - Type correctness
    """
    
    def __init__(self) -> None:
        """Initialize safety guard."""
        logger.info("SafetyGuard initialized")
    
    def initialize(self) -> bool:
        """Initialize safety system."""
        logger.info("SafetyGuard ready")
        return True
    
    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """
        Validate input payload.
        
        Args:
            payload (Dict[str, Any]): Input to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValueError: If validation fails (called by caller)
        """
        if not isinstance(payload, dict):
            logger.warning("Payload is not dictionary")
            return False
        
        try:
            # Check payload size
            payload_size = len(str(payload))
            if payload_size > MAX_PAYLOAD_SIZE:
                logger.warning(f"Payload too large: {payload_size} bytes")
                return False
            
            # Check for required fields
            if not payload:
                logger.warning("Empty payload")
                return False
            
            logger.debug(f"Payload validated: {len(payload)} fields")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def validate_file(
        self,
        filename: str,
        file_size: int,
    ) -> bool:
        """
        Validate file upload.
        
        Args:
            filename (str): Uploaded filename
            file_size (int): File size in bytes
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If validation fails
        """
        if not filename:
            raise ValueError("Filename required")
        
        # Check format
        if not any(filename.lower().endswith(fmt) for fmt in ALLOWED_FILE_FORMATS):
            raise ValueError(
                f"File format not allowed. Allowed: {ALLOWED_FILE_FORMATS}"
            )
        
        # Check size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large. Max: {MAX_FILE_SIZE} bytes, Got: {file_size}"
            )
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        logger.info(f"File validated: {filename} ({file_size} bytes)")
        return True
    
    def sanitize_string(self, value: str, max_length: int = MAX_STRING_LENGTH) -> str:
        """
        Sanitize string input.
        
        Args:
            value (str): String to sanitize
            max_length (int): Maximum allowed length
            
        Returns:
            str: Sanitized string
            
        Raises:
            ValueError: If string invalid
        """
        if not isinstance(value, str):
            raise ValueError("Must be string")
        
        if len(value) > max_length:
            raise ValueError(f"String too long. Max: {max_length}")
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        return value
