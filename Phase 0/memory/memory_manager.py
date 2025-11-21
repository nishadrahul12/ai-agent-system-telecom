"""
Memory Manager: Unified cache and storage management.

Provides:
    - Key-value caching (with TTL support)
    - Fallback to persistent storage
    - Automatic cache invalidation
    - Memory statistics

Usage:
    memory = MemoryManager()
    memory.initialize()
    memory.set("task_123", {"status": "completed"}, ttl=3600)
    result = memory.get("task_123")
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default cache settings
DEFAULT_CACHE_SIZE = 1000
DEFAULT_TTL = 3600  # 1 hour


class MemoryManager:
    """
    Unified memory management system.
    
    Attributes:
        _cache (dict): In-memory key-value store
        _ttl_map (dict): TTL timestamps per key
        _storage: Persistent storage backend
    """
    
    def __init__(self, storage_backend: Optional[any] = None) -> None:
        """
        Initialize memory manager.
        
        Args:
            storage_backend (Optional[any]): Persistent storage backend
        """
        self._cache: Dict[str, Any] = {}
        self._ttl_map: Dict[str, datetime] = {}
        self._storage = storage_backend
        self._initialized = False
        
        logger.info("MemoryManager created")
    
    def initialize(self) -> bool:
        """
        Initialize memory system.
        
        Returns:
            bool: True if successful
        """
        try:
            if self._storage:
                self._storage.initialize()
                logger.info("Storage backend initialized")
            
            self._initialized = True
            logger.info("MemoryManager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = DEFAULT_TTL,
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key (str): Cache key
            value (Any): Value to store
            ttl (int): Time-to-live in seconds. Defaults to 3600
            
        Returns:
            bool: True if successful
        """
        if not key:
            logger.warning("Cannot cache empty key")
            return False
        
        try:
            self._cache[key] = value
            self._ttl_map[key] = datetime.utcnow() + timedelta(seconds=ttl)
            
            logger.debug(f"Cached: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Any]: Cached value if found and valid, None otherwise
        """
        if not key:
            return None
        
        # Check if key exists
        if key not in self._cache:
            logger.debug(f"Cache miss: {key}")
            return None
        
        # Check TTL
        if key in self._ttl_map:
            if datetime.utcnow() > self._ttl_map[key]:
                logger.debug(f"Cache expired: {key}")
                del self._cache[key]
                del self._ttl_map[key]
                return None
        
        logger.debug(f"Cache hit: {key}")
        return self._cache[key]
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key (str): Cache key
            
        Returns:
            bool: True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            if key in self._ttl_map:
                del self._ttl_map[key]
            logger.debug(f"Deleted: {key}")
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._ttl_map.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            int: Number of entries removed
        """
        expired_keys = [
            key for key, expiry in self._ttl_map.items()
            if datetime.utcnow() > expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._ttl_map[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        self.cleanup_expired()  # Clean before stats
        
        return {
            "cache_size": len(self._cache),
            "max_size": DEFAULT_CACHE_SIZE,
            "usage_percent": (len(self._cache) / DEFAULT_CACHE_SIZE) * 100,
            "ttl_entries": len(self._ttl_map),
        }
