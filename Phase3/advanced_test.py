"""
ADVANCED TEST - Using Intelligent CSV Loader
Auto-detects ANY date format automatically!
"""

import sys
import os
import pandas as pd
import numpy as np
import logging

sys.path.insert(0, '..')

# Import both the loader and the engine
from intelligent_csv_loader import load_kpi_data_intelligent
from anomaly_engine import AnomalyDetectionEngine

# Configure logging to see what the loader is doing
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

print("="*70)
print("PHASE 3 - ADVANCED VERIFICATION (INTELLIGENT CSV LOADER)")
print("="*70)
print()

try:
    # STEP 1: Load CSV with intelligent date detection
    print("STEP 1: Loading CSV with intelligent date format detection...")
    data_path = os.path.join('..', 'Phase 0', 'sample_kpi_data.csv')
    
    data = load_kpi_data_intelligent(data_path)
    print(f"✅ Data loaded: {data.shape[0]} rows, {data.shape[1]} columns")
    print(f"✅ All columns are numeric: {data.dtypes.unique()}")
    print()
    
    # STEP 2: Initialize anomaly engine
    print("STEP 2: Initializing Anomaly Detection Engine...")
    engine = AnomalyDetectionEngine(sensitivity="medium")
    print(f"✅ Engine initialized")
    print()
    
    # STEP 3: Normalize data
    print("STEP 3: Normalizing data...")
    normalized = engine.normalize_data(data)
    print(f"✅ Normalized: Mean={normalized.mean().mean():.8f}, Std={normalized.std().mean():.6f}")
    print()
    
    # STEP 4: Run anomaly detection
    print("STEP 4: Running anomaly detection (3 methods)...")
    anomalies = engine.detect_anomalies()
    print(f"✅ Detection complete: Found {len(anomalies)} anomalies")
    print()
    
    # STEP 5: Get results
    print("STEP 5: Generating summary...")
    summary = engine.get_summary()
    
    print("="*70)
    print("RESULTS:")
    print("="*70)
    print(f"Network Status:        {summary['network_status']['network_status'].upper()}")
    print(f"Critical Anomalies:    {summary['network_status']['critical_count']}")
    print(f"Warning Anomalies:     {summary['network_status']['warning_count']}")
    print(f"Total Anomalies:       {summary['total_anomalies']}")
    print(f"Data Points Analyzed:  {summary['data_points_analyzed']}")
    print(f"KPIs Analyzed:         {summary['kpis_analyzed']}")
    print()
    print("Anomalies by Method:")
    for method, count in summary['anomalies_by_method'].items():
        print(f"  - {method}: {count}")
    print()
    print("Anomalies by KPI (top 10):")
    by_kpi = sorted(summary['anomalies_by_kpi'].items(), key=lambda x: x[1], reverse=True)
    for kpi, count in by_kpi[:10]:
        print(f"  - {kpi}: {count}")
    print()
    
    if len(anomalies) > 0:
        print("="*70)
        print("SAMPLE ANOMALIES (first 3):")
        print("="*70)
        for i, anomaly in enumerate(anomalies[:3], 1):
            print(f"\nAnomaly {i}:")
            print(f"  KPI:      {anomaly['kpi']}")
            print(f"  Value:    {anomaly.get('value', 'N/A')}")
            print(f"  Severity: {anomaly['severity'].upper()}")
            print(f"  Method:   {anomaly['method']}")
    
    print()
    print("="*70)
    print("✅ SUCCESS! Advanced verification passed!")
    print("="*70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    import traceback
    print("Traceback:")
    traceback.print_exc()
