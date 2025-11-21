"""
Memory Module: In-memory caching and persistent storage.

Provides unified access to:
    - In-memory cache (fast access)
    - Persistent storage backends (recovery)
    - Memory lifecycle management
    - Cache invalidation

Usage:
    memory = MemoryManager(storage_backend)
    memory.set("key", {"data": "value"})
    data = memory.get("key")
"""

__version__ = "0.1.0"

from memory.memory_manager import MemoryManager
from memory.storage import StorageBackend, InMemoryStorage

__all__ = ["MemoryManager", "StorageBackend", "InMemoryStorage"]