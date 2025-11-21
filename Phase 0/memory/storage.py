"""
Storage Backends: Persistent storage interfaces.

Provides:
    - Abstract StorageBackend interface
    - InMemoryStorage implementation (testing)
    - Future: SQLiteStorage (Phase 1)

Usage:
    storage = InMemoryStorage()
    storage.save("key", {"data": "value"})
    value = storage.load("key")
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """
    Abstract storage backend interface.
    
    All storage implementations must inherit from this.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize storage backend."""
        pass
    
    @abstractmethod
    def save(self, key: str, value: Any) -> bool:
        """Save value to storage."""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load value from storage."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from storage."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass


class InMemoryStorage(StorageBackend):
    """
    In-memory storage backend (for Phase 0 testing).
    
    Note: Data is volatile. Use SQLiteStorage in production.
    """
    
    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._store: Dict[str, Any] = {}
        logger.info("InMemoryStorage created")
    
    def initialize(self) -> bool:
        """Initialize storage."""
        logger.info("InMemoryStorage initialized")
        return True
    
    def save(self, key: str, value: Any) -> bool:
        """
        Save value.
        
        Args:
            key (str): Storage key
            value (Any): Value to save
            
        Returns:
            bool: True if successful
        """
        try:
            self._store[key] = value
            logger.debug(f"Saved: {key}")
            return True
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False
    
    def load(self, key: str) -> Optional[Any]:
        """
        Load value.
        
        Args:
            key (str): Storage key
            
        Returns:
            Optional[Any]: Stored value if found
        """
        return self._store.get(key)
    
    def delete(self, key: str) -> bool:
        """
        Delete value.
        
        Args:
            key (str): Storage key
            
        Returns:
            bool: True if deleted
        """
        if key in self._store:
            del self._store[key]
            logger.debug(f"Deleted: {key}")
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key (str): Storage key
            
        Returns:
            bool: True if exists
        """
        return key in self._store
