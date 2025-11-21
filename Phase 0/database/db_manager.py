"""
Database Manager: SQLite connection and CRUD operations.

Database Path: data/ai_agent_system.db
Schema: TASKS, FILES, ANALYSES, CACHE tables

Operations:
    - Create/read/update/delete tasks
    - Store file metadata
    - Persist analysis results
    - Cache management

Configuration:
    - WAL mode (Write-Ahead Logging)
    - Connection pooling
    - Foreign keys enabled
    - 30-second timeout
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_PATH = Path("data/ai_agent_system.db")
JOURNAL_MODE = "WAL"
TIMEOUT = 30
FOREIGN_KEYS = True
CONNECTION_POOL_SIZE = 5


class DatabaseManager:
    """
    SQLite database connection and operations.
    
    Attributes:
        db_path (Path): Database file path
        _connections (list): Connection pool
    """
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize database manager.
        
        Args:
            db_path (Optional[Path]): Database path. Defaults to configured path
        """
        self.db_path = db_path or DATABASE_PATH
        self._connections: List[sqlite3.Connection] = []
        self._initialized = False
        
        logger.info(f"DatabaseManager created ({self.db_path})")
    
    def initialize(self) -> bool:
        """
        Initialize database and create schema.
        
        Returns:
            bool: True if successful
            
        Raises:
            OSError: If database directory doesn't exist
            sqlite3.Error: If schema creation fails
        """
        try:
            # Create data directory
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection
            conn = self._get_connection()
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Set journal mode
            conn.execute(f"PRAGMA journal_mode = {JOURNAL_MODE}")
            
            # Create schema
            self._create_schema(conn)
            
            conn.commit()
            conn.close()
            
            self._initialized = True
            logger.info(f"Database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            return False
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.
        
        Returns:
            sqlite3.Connection: Active connection
            
        Raises:
            sqlite3.Error: If connection fails
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=TIMEOUT,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """
        Create database schema.
        
        Args:
            conn (sqlite3.Connection): Database connection
        """
        schema_sql = """
        -- Tasks table
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            payload JSON,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        -- Files table
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            size_bytes INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Analyses table
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id TEXT UNIQUE NOT NULL,
            file_id TEXT NOT NULL,
            feature_type TEXT,
            input_params JSON,
            results JSON,
            execution_time_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        );
        
        -- Cache table
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            value JSON,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_task_created ON tasks(created_at);
        CREATE INDEX IF NOT EXISTS idx_file_uploaded ON files(uploaded_at);
        CREATE INDEX IF NOT EXISTS idx_analysis_file ON analyses(file_id);
        CREATE INDEX IF NOT EXISTS idx_cache_expiry ON cache(expires_at);
        """
        
        conn.executescript(schema_sql)
        logger.info("Schema created")
    
    def insert_task(
        self,
        task_id: str,
        agent_name: str,
        status: str,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Insert task record.
        
        Args:
            task_id (str): Unique task ID
            agent_name (str): Target agent
            status (str): Task status
            payload (Dict): Task payload
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO tasks (task_id, agent_name, status, payload)
                   VALUES (?, ?, ?, ?)""",
                (task_id, agent_name, status, json.dumps(payload))
            )
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Task inserted: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Insert task failed: {e}")
            return False
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update task status.
        
        Args:
            task_id (str): Task ID
            status (str): New status
            error_message (Optional[str]): Error if failed
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if status == "completed":
                cursor.execute(
                    """UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP
                       WHERE task_id = ?""",
                    (status, task_id)
                )
            elif status == "running":
                cursor.execute(
                    """UPDATE tasks SET status = ?, started_at = CURRENT_TIMESTAMP
                       WHERE task_id = ?""",
                    (status, task_id)
                )
            else:
                cursor.execute(
                    """UPDATE tasks SET status = ?, error_message = ?
                       WHERE task_id = ?""",
                    (status, error_message, task_id)
                )
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Task updated: {task_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Update task failed: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Retrieve task by ID.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            Optional[Dict]: Task record if found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Get task failed: {e}")
            return None
    
    def insert_file(
        self,
        file_id: str,
        original_name: str,
        file_path: str,
        size_bytes: int,
    ) -> bool:
        """
        Insert file metadata.
        
        Args:
            file_id (str): Unique file ID
            original_name (str): Original filename
            file_path (str): Storage path
            size_bytes (int): File size
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO files (file_id, original_name, file_path, size_bytes)
                   VALUES (?, ?, ?, ?)""",
                (file_id, original_name, file_path, size_bytes)
            )
            
            conn.commit()
            conn.close()
            
            logger.debug(f"File inserted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Insert file failed: {e}")
            return False
