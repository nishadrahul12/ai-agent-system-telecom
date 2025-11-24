"""Verify network severity classification."""
import sys
import os
import pandas as pd

sys.path.insert(0, '..')

from anomaly_engine import AnomalyDetectionEngine

try:
    data_path = os.path.join('..', 'Phase 0', 'sample_kpi_data.csv')
    data = pd.read_csv(data_path, encoding='utf-8-sig')
    
    engine = AnomalyDetectionEngine(sensitivity="medium")
    engine.normalize_data(data)
    anomalies = engine.detect_anomalies()
    
    classification = engine.classify_network_severity()
    
    print("Network Classification Results:")
    print(f"✅ Network Status: {classification['network_status']}")
    print(f"✅ Critical Count: {classification['critical_count']}")
    print(f"✅ Warning Count: {classification['warning_count']}")
    print(f"✅ Total Anomalies: {classification['total_anomalies']}")
    print(f"✅ Affected KPIs: {len(classification['affected_kpis'])} KPIs")
    print()
    
    if classification['affected_kpis']:
        print(f"Affected KPIs (first 10):")
        for kpi in classification['affected_kpis'][:10]:
            print(f"   - {kpi}")
    
except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
    print("Make sure sample_kpi_data.csv exists in Phase 0/")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
