"""
Database Module: SQLite connection and schema management.

Provides:
    - SQLite connection pooling
    - Database initialization
    - Schema management
    - CRUD operations for tasks, files, analyses

Usage:
    db = DatabaseManager()
    db.initialize()
    db.insert_task(task_id, agent_name, status, payload)
"""

__version__ = "0.1.0"

from database.db_manager import DatabaseManager

__all__ = ["DatabaseManager"]
