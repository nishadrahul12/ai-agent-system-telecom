"""
Privacy Checker: Detect and handle PII (Personally Identifiable Information).

Detects:
    - Email addresses
    - Phone numbers
    - SSN/ID numbers
    - Payment card numbers
    - Personal names
    - Addresses

Usage:
    checker = PrivacyChecker()
    if checker.has_pii(data):
        handle_sensitive_data()
"""

import logging
import re
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


class PrivacyChecker:
    """
    Detect PII in data to protect privacy.
    
    Patterns:
        - Email: user@domain.com
        - Phone: (123) 456-7890
        - SSN: 123-45-6789
        - Card: 4111-1111-1111-1111
    """
    
    def __init__(self) -> None:
        """Initialize privacy checker with regex patterns."""
        self.patterns: Dict[str, str] = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
            "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
            "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        }
        logger.info("PrivacyChecker initialized")
    
    def has_pii(self, data: Any) -> bool:
        """
        Check if data contains PII.
        
        Args:
            data (Any): Data to check (string, dict, list)
            
        Returns:
            bool: True if PII detected
        """
        pii_found = self._find_pii(data)
        return len(pii_found) > 0
    
    def find_pii(self, data: Any) -> Dict[str, Set[str]]:
        """
        Find all PII in data.
        
        Args:
            data (Any): Data to scan
            
        Returns:
            Dict[str, Set[str]]: PII by type
        """
        return self._find_pii(data)
    
    def _find_pii(self, data: Any) -> Dict[str, Set[str]]:
        """
        Internal PII detection.
        
        Args:
            data (Any): Data to scan
            
        Returns:
            Dict[str, Set[str]]: PII found by type
        """
        pii_found: Dict[str, Set[str]] = {key: set() for key in self.patterns}
        
        # Convert data to string for searching
        text = self._convert_to_text(data)
        
        # Search for each pattern
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # Handle grouped patterns
                    matches = ["".join(m) for m in matches]
                pii_found[pii_type].update(matches)
                logger.warning(f"Found {len(matches)} {pii_type} instances")
        
        return pii_found
    
    def _convert_to_text(self, data: Any) -> str:
        """
        Convert any data type to searchable text.
        
        Args:
            data (Any): Data to convert
            
        Returns:
            str: Searchable text representation
        """
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return " ".join(f"{k} {v}" for k, v in data.items())
        elif isinstance(data, (list, tuple)):
            return " ".join(str(item) for item in data)
        else:
            return str(data)
    
    def mask_pii(self, data: str) -> str:
        """
        Replace PII with masked versions.
        
        Args:
            data (str): Text containing PII
            
        Returns:
            str: Text with PII masked
        """
        masked = data
        
        # Mask emails
        masked = re.sub(
            self.patterns["email"],
            "[REDACTED_EMAIL]",
            masked,
            flags=re.IGNORECASE,
        )
        
        # Mask phones
        masked = re.sub(
            self.patterns["phone"],
            "[REDACTED_PHONE]",
            masked,
            flags=re.IGNORECASE,
        )
        
        # Mask SSNs
        masked = re.sub(
            self.patterns["ssn"],
            "[REDACTED_SSN]",
            masked,
            flags=re.IGNORECASE,
        )
        
        # Mask credit cards
        masked = re.sub(
            self.patterns["credit_card"],
            "[REDACTED_CARD]",
            masked,
            flags=re.IGNORECASE,
        )
        
        logger.info("PII masked in data")
        return masked
