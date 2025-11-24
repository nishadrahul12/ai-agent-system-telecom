"""Verify anomaly_engine.py with real data."""
import sys
import os
import pandas as pd

# Fix path - use os.path.join for cross-platform compatibility
sys.path.insert(0, '..')

from anomaly_engine import AnomalyDetectionEngine

# Load sample data from Phase 0
try:
    # Proper path handling for Windows/Linux
    data_path = os.path.join('..', 'Phase 0', 'sample_kpi_data.csv')
    print(f"📂 Looking for data at: {data_path}")
    print(f"📂 Full path: {os.path.abspath(data_path)}")
    
    data = pd.read_csv(data_path, encoding='utf-8-sig')
    print(f"✅ Data loaded: {data.shape[0]} rows, {data.shape[1]} columns")
    print(f"✅ KPIs: {list(data.columns[:5])}... (showing first 5 of {len(data.columns)})")
    print()
    
    # Initialize engine
    engine = AnomalyDetectionEngine(sensitivity="medium")
    print(f"✅ Engine initialized with medium sensitivity")
    print()
    
    # Normalize data
    normalized = engine.normalize_data(data)
    print(f"✅ Data normalized: Mean={normalized.mean().mean():.6f}, Std={normalized.std().mean():.6f}")
    print()
    
    # Run detection
    anomalies = engine.detect_anomalies()
    print(f"✅ Anomaly detection complete: Found {len(anomalies)} anomalies")
    print()
    
    # Get summary
    summary = engine.get_summary()
    print(f"✅ Summary generated:")
    print(f"   - Network Status: {summary['network_status']['network_status']}")
    print(f"   - Critical Anomalies: {summary['network_status']['critical_count']}")
    print(f"   - Warning Anomalies: {summary['network_status']['warning_count']}")
    print(f"   - Total Anomalies: {summary['total_anomalies']}")
    print(f"   - Anomalies by method: {summary['anomalies_by_method']}")
    
    if len(anomalies) > 0:
        print()
        print(f"✅ Sample anomaly:")
        print(f"   {anomalies[0]}")
    
except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
    print()
    print("SOLUTION:")
    print("1. Check your folder structure:")
    print("   Project Root/")
    print("   ├── Phase 0/")
    print("   │   └── sample_kpi_data.csv")
    print("   ├── Phase 1/")
    print("   ├── Phase 2/")
    print("   └── Phase 3/")
    print("       └── verify_engine.py  (YOU ARE HERE)")
    print()
    print("2. Make sure you're running from Phase 3/ folder")
    print("3. Verify sample_kpi_data.csv exists in Phase 0/")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
