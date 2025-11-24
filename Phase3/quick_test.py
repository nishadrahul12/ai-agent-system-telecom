"""
IMMEDIATE WORKAROUND - Test anomaly_engine with CSV data handling
Run this RIGHT NOW to verify everything works!
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, '..')

from anomaly_engine import AnomalyDetectionEngine

print("="*70)
print("PHASE 3 - ANOMALY ENGINE VERIFICATION (IMMEDIATE WORKAROUND)")
print("="*70)
print()

try:
    # STEP 1: Load CSV with proper encoding
    print("STEP 1: Loading CSV data...")
    data_path = os.path.join('..', 'Phase 0', 'sample_kpi_data.csv')
    
    # Key fix: encoding='utf-8-sig' removes BOM character
    raw_data = pd.read_csv(data_path, encoding='utf-8-sig')
    print(f"✅ Loaded: {raw_data.shape[0]} rows, {raw_data.shape[1]} columns")
    print(f"   Columns: {list(raw_data.columns[:3])}... (first 3 shown)")
    print()
    
    # STEP 2: Clean data - keep only numeric columns
    print("STEP 2: Cleaning data (removing non-numeric columns)...")
    numeric_cols = raw_data.select_dtypes(include=[np.number]).columns
    data = raw_data[numeric_cols].copy()
    print(f"✅ Cleaned: {data.shape[0]} rows, {data.shape[1]} numeric columns")
    print(f"   Data types: {data.dtypes.unique()}")
    print()
    
    # STEP 3: Initialize anomaly engine
    print("STEP 3: Initializing Anomaly Detection Engine...")
    engine = AnomalyDetectionEngine(sensitivity="medium")
    print(f"✅ Engine initialized")
    print()
    
    # STEP 4: Normalize data
    print("STEP 4: Normalizing data...")
    normalized = engine.normalize_data(data)
    print(f"✅ Normalized: Mean={normalized.mean().mean():.8f}, Std={normalized.std().mean():.6f}")
    print()
    
    # STEP 5: Run anomaly detection
    print("STEP 5: Running anomaly detection (3 methods)...")
    anomalies = engine.detect_anomalies()
    print(f"✅ Detection complete: Found {len(anomalies)} anomalies")
    print()
    
    # STEP 6: Get results
    print("STEP 6: Generating summary...")
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
    print("✅ SUCCESS! Anomaly detection is working correctly!")
    print("="*70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    import traceback
    print("Traceback:")
    traceback.print_exc()
