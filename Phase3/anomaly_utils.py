"""
anomaly_utils.py - Phase 3 API Utilities
CSV/XLSX loading, file validation, and result persistence
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import openpyxl for XLSX support
try:
    import openpyxl
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False
    logger.warning("openpyxl not available. XLSX support disabled.")


# ============================================================================
# CONSTANTS
# ============================================================================

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5GB
SUPPORTED_FORMATS = ['csv', 'xlsx']
RESULTS_DIR = Path(__file__).parent / "results"


# ============================================================================
# FILE VALIDATION
# ============================================================================

def validate_file_size(file_size_bytes: int) -> Tuple[bool, Optional[str]]:
    """
    Validate file size against maximum limit.
    
    Args:
        file_size_bytes (int): File size in bytes
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        max_gb = MAX_FILE_SIZE_BYTES / (1024**3)
        actual_gb = file_size_bytes / (1024**3)
        error = f"File size {actual_gb:.2f}GB exceeds limit of {max_gb:.0f}GB"
        return False, error
    
    if file_size_bytes == 0:
        return False, "File is empty"
    
    return True, None


def validate_file_format(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file format.
    
    Args:
        filename (str): Filename to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
    
    if ext not in SUPPORTED_FORMATS:
        return False, f"Format '{ext}' not supported. Use: {', '.join(SUPPORTED_FORMATS)}"
    
    if ext == 'xlsx' and not XLSX_AVAILABLE:
        return False, "XLSX support not available. Install openpyxl: pip install openpyxl"
    
    return True, None


# ============================================================================
# CSV/XLSX LOADING
# ============================================================================

def load_csv_data(filepath: str) -> pd.DataFrame:
    """
    Load CSV file with intelligent encoding and datetime handling.
    
    Args:
        filepath (str): Path to CSV file
        
    Returns:
        pd.DataFrame: Cleaned numeric data
    """
    logger.info(f"Loading CSV: {filepath}")
    
    # Try BOM-aware encoding first
    try:
        data = pd.read_csv(filepath, encoding='utf-8-sig')
    except Exception as e:
        logger.warning(f"Failed with utf-8-sig: {e}, trying default encoding")
        data = pd.read_csv(filepath)
    
    logger.info(f"Loaded: {data.shape[0]} rows, {data.shape[1]} columns")
    
    # Import intelligent loader for date detection
    try:
        from intelligent_csv_loader import load_kpi_data_intelligent
        # Use intelligent loader for consistent handling
        data = load_kpi_data_intelligent(filepath)
    except ImportError:
        logger.warning("intelligent_csv_loader not available, using basic cleanup")
        # Fallback: just drop non-numeric columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        data = data[numeric_cols].copy()
        data = data.dropna()
    
    return data


def load_xlsx_data(filepath: str) -> pd.DataFrame:
    """
    Load XLSX file.
    
    Args:
        filepath (str): Path to XLSX file
        
    Returns:
        pd.DataFrame: Cleaned numeric data
    """
    if not XLSX_AVAILABLE:
        raise RuntimeError("XLSX support not available. Install: pip install openpyxl")
    
    logger.info(f"Loading XLSX: {filepath}")
    
    # Load Excel file
    data = pd.read_excel(filepath, engine='openpyxl')
    logger.info(f"Loaded: {data.shape[0]} rows, {data.shape[1]} columns")
    
    # Drop non-numeric columns (similar to CSV handling)
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    data = data[numeric_cols].copy()
    data = data.dropna()
    
    logger.info(f"Cleaned: {data.shape[0]} rows, {data.shape[1]} numeric columns")
    
    return data


def load_any_format(filepath: str) -> pd.DataFrame:
    """
    Load data file in any supported format (CSV or XLSX).
    
    Args:
        filepath (str): Path to data file
        
    Returns:
        pd.DataFrame: Cleaned numeric data
        
    Raises:
        ValueError: If format not supported
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Get file format
    ext = filepath.rsplit('.', 1)[1].lower() if '.' in filepath else None
    
    if ext == 'csv':
        return load_csv_data(filepath)
    elif ext == 'xlsx':
        return load_xlsx_data(filepath)
    else:
        raise ValueError(f"Unsupported format: {ext}")


# ============================================================================
# RESULT PERSISTENCE
# ============================================================================

def ensure_results_dir() -> Path:
    """
    Ensure results directory exists.
    
    Returns:
        Path: Results directory path
    """
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)
    return RESULTS_DIR


def get_task_dir(task_id: str) -> Path:
    """
    Get task-specific results directory.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        Path: Task directory path
    """
    task_dir = ensure_results_dir() / task_id
    task_dir.mkdir(exist_ok=True, parents=True)
    return task_dir


def save_result_to_disk(task_id: str, result_data: dict, metadata: dict) -> bool:
    """
    Save analysis results to disk.
    
    Args:
        task_id (str): Task ID
        result_data (dict): Complete analysis result
        metadata (dict): Task metadata
        
    Returns:
        bool: True if saved successfully
    """
    try:
        task_dir = get_task_dir(task_id)
        
        # Save results
        results_file = task_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        logger.info(f"Saved results: {results_file}")
        
        # Save metadata
        metadata_file = task_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata: {metadata_file}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to save results for task {task_id}: {e}")
        return False


def load_result_from_disk(task_id: str) -> Optional[dict]:
    """
    Load analysis results from disk.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        Optional[dict]: Result data or None if not found
    """
    try:
        task_dir = RESULTS_DIR / task_id
        results_file = task_dir / "results.json"
        
        if not results_file.exists():
            logger.warning(f"Results not found for task {task_id}")
            return None
        
        with open(results_file, 'r') as f:
            result_data = json.load(f)
        
        logger.info(f"Loaded results: {results_file}")
        return result_data
    
    except Exception as e:
        logger.error(f"Failed to load results for task {task_id}: {e}")
        return None


def load_metadata_from_disk(task_id: str) -> Optional[dict]:
    """
    Load task metadata from disk.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        Optional[dict]: Metadata or None if not found
    """
    try:
        task_dir = RESULTS_DIR / task_id
        metadata_file = task_dir / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return metadata
    
    except Exception as e:
        logger.error(f"Failed to load metadata for task {task_id}: {e}")
        return None


def list_all_tasks() -> list:
    """
    List all completed tasks.
    
    Returns:
        list: List of task IDs
    """
    try:
        ensure_results_dir()
        tasks = []
        for item in RESULTS_DIR.iterdir():
            if item.is_dir():
                metadata = load_metadata_from_disk(item.name)
                if metadata:
                    tasks.append({
                        'task_id': item.name,
                        'status': metadata.get('status'),
                        'created_at': metadata.get('created_at'),
                        'filename': metadata.get('filename')
                    })
        return sorted(tasks, key=lambda x: x['created_at'], reverse=True)
    
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        return []


def delete_task(task_id: str) -> bool:
    """
    Delete task results from disk.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        bool: True if deleted successfully
    """
    try:
        import shutil
        task_dir = RESULTS_DIR / task_id
        
        if not task_dir.exists():
            logger.warning(f"Task directory not found: {task_id}")
            return False
        
        shutil.rmtree(task_dir)
        logger.info(f"Deleted task: {task_id}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        return False


def cleanup_old_results(days: int = 30) -> int:
    """
    Delete results older than specified days.
    
    Args:
        days (int): Age threshold in days
        
    Returns:
        int: Number of tasks deleted
    """
    try:
        from datetime import datetime, timedelta
        import shutil
        
        ensure_results_dir()
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for task_dir in RESULTS_DIR.iterdir():
            if not task_dir.is_dir():
                continue
            
            metadata = load_metadata_from_disk(task_dir.name)
            if not metadata:
                continue
            
            created_at = datetime.fromisoformat(metadata.get('created_at', ''))
            if created_at < cutoff_date:
                shutil.rmtree(task_dir)
                deleted_count += 1
                logger.info(f"Deleted old task: {task_dir.name}")
        
        logger.info(f"Cleanup complete: {deleted_count} tasks deleted")
        return deleted_count
    
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 0


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_task_id() -> str:
    """
    Generate unique task ID.
    
    Returns:
        str: Task ID (format: task_YYYYMMDD_HHMMSS_XXXXX)
    """
    from datetime import datetime
    import random
    import string
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"task_{timestamp}_{random_suffix}"


def get_file_size_mb(file_size_bytes: int) -> float:
    """
    Convert bytes to MB.
    
    Args:
        file_size_bytes (int): File size in bytes
        
    Returns:
        float: File size in MB
    """
    return file_size_bytes / (1024 ** 2)
