"""
INTELLIGENT CSV LOADER - Auto-detects date formats
Handles: 3/1/2024, 2025-03-10, 2025-03-10 00:00:00, etc.
"""

import pandas as pd
import numpy as np
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)


def auto_detect_datetime_column(series: pd.Series, column_name: str) -> pd.Series:
    """
    Automatically detect and parse datetime column with any common format.
    
    Handles:
    - US format: 3/1/2024, 03/01/2024
    - ISO format: 2025-03-10, 2025-03-10 00:00:00
    - European: 10/03/2025
    - With time: 2025-03-10 14:30:45
    - Timestamps: 1609459200
    - Text: "2025-03-10T14:30:00Z"
    
    Args:
        series (pd.Series): Series to parse
        column_name (str): Column name for logging
        
    Returns:
        pd.Series: Parsed datetime column
    """
    
    if series.dtype == 'object':  # String column
        try:
            # Try common formats first (faster)
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    result = pd.to_datetime(series, format=fmt, errors='coerce')
                    if result.notna().sum() / len(series) > 0.9:  # >90% success
                        logger.info(f"Column '{column_name}': Detected format '{fmt}'")
                        return result
                except:
                    continue
            
            # Fallback: use dateutil parser (slower but very flexible)
            logger.info(f"Column '{column_name}': Using flexible date parser")
            result = pd.to_datetime(series, errors='coerce', infer_datetime_format=True)
            
            if result.notna().sum() / len(series) > 0.9:
                return result
            else:
                logger.warning(f"Column '{column_name}': Could not parse as datetime")
                return series
                
        except Exception as e:
            logger.warning(f"Column '{column_name}': Parse error: {e}")
            return series
    
    else:
        # Already numeric/datetime, try conversion
        try:
            return pd.to_datetime(series, errors='coerce')
        except:
            return series


def load_kpi_data_intelligent(filepath: str) -> pd.DataFrame:
    """
    Load KPI CSV with intelligent handling:
    - Auto-detects and removes BOM
    - Auto-detects datetime columns
    - Converts to numeric where possible
    - Returns clean numeric data
    
    Args:
        filepath (str): Path to CSV file
        
    Returns:
        pd.DataFrame: Cleaned numeric data ready for anomaly detection
    """
    
    logger.info(f"Loading data from: {filepath}")
    
    # Load with BOM handling
    try:
        data = pd.read_csv(filepath, encoding='utf-8-sig')
    except:
        # Fallback to default encoding
        data = pd.read_csv(filepath)
    
    logger.info(f"Raw data loaded: {data.shape[0]} rows, {data.shape[1]} columns")
    
    # Identify potential datetime columns
    datetime_candidates = []
    for col in data.columns:
        # Check if column name suggests datetime
        if any(x in col.lower() for x in ['time', 'date', 'timestamp', 'dt']):
            datetime_candidates.append(col)
        # Check if column contains date-like strings
        elif data[col].dtype == 'object':
            sample = data[col].dropna().head(5)
            if any('/' in str(x) or '-' in str(x) for x in sample):
                datetime_candidates.append(col)
    
    # Process datetime columns
    for col in datetime_candidates:
        logger.info(f"Attempting to parse column '{col}' as datetime...")
        parsed = auto_detect_datetime_column(data[col], col)
        
        if parsed.dtype == 'datetime64[ns]':
            logger.info(f"✅ Successfully parsed '{col}' as datetime")
            # Drop datetime columns (not needed for anomaly detection on numeric metrics)
            data = data.drop(col, axis=1)
        else:
            logger.warning(f"Could not parse '{col}' as datetime, keeping as-is")
    
    # Convert all remaining columns to numeric
    logger.info("Converting columns to numeric...")
    for col in data.columns:
        if data[col].dtype != 'object':
            continue
        
        # Try to convert to numeric
        try:
            converted = pd.to_numeric(data[col], errors='coerce')
            if converted.notna().sum() / len(data[col]) > 0.9:  # >90% success
                data[col] = converted
                logger.info(f"✅ Converted '{col}' to numeric")
            else:
                logger.warning(f"Cannot convert '{col}' to numeric, dropping column")
                data = data.drop(col, axis=1)
        except:
            logger.warning(f"Cannot convert '{col}' to numeric, dropping column")
            data = data.drop(col, axis=1)
    
    # Keep only numeric columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    data = data[numeric_cols].copy()
    
    # Remove rows with NaN
    initial_rows = len(data)
    data = data.dropna()
    if len(data) < initial_rows:
        logger.info(f"Dropped {initial_rows - len(data)} rows with NaN values")
    
    logger.info(f"✅ Final data: {data.shape[0]} rows, {data.shape[1]} numeric columns")
    return data


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import os
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test with your data
    data_path = os.path.join('..', 'Phase 0', 'sample_kpi_data.csv')
    
    print("="*70)
    print("INTELLIGENT CSV LOADER TEST")
    print("="*70)
    print()
    
    try:
        data = load_kpi_data_intelligent(data_path)
        
        print()
        print("="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"✅ Data loaded: {data.shape[0]} rows, {data.shape[1]} columns")
        print(f"✅ All columns are numeric: {data.dtypes.unique()}")
        print(f"✅ Ready for anomaly detection!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
