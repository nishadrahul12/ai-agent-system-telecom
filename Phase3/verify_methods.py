"""Verify each anomaly detection method individually."""
import sys
import os
import pandas as pd

sys.path.insert(0, '..')

from anomaly_engine import AnomalyDetectionEngine, AnomalyMethod

try:
    data_path = os.path.join('..', 'Phase 0', 'sample_kpi_data.csv')
    data = pd.read_csv(data_path, encoding='utf-8-sig')
    
    # Test each method separately
    methods = [AnomalyMethod.ZSCORE, AnomalyMethod.IQR, AnomalyMethod.ISOLATION_FOREST]
    
    for method in methods:
        print(f"\n{'='*60}")
        print(f"Testing: {method.value.upper()}")
        print(f"{'='*60}")
        
        try:
            # Create engine with single method
            engine = AnomalyDetectionEngine(
                sensitivity="medium",
                methods=[method.value]
            )
            
            # Normalize and detect
            engine.normalize_data(data)
            anomalies = engine.detect_anomalies()
            
            print(f"✅ {method.value}: {len(anomalies)} anomalies detected")
            
            if anomalies:
                # Show sample
                sample = anomalies[0]
                print(f"\n   Sample:")
                print(f"   - KPI: {sample['kpi']}")
                print(f"   - Severity: {sample['severity']}")
                print(f"   - Value: {sample.get('value', 'N/A')}")
                
        except Exception as e:
            print(f"❌ {method.value} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ All methods verified!")
    
except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
    print("Make sure sample_kpi_data.csv exists in Phase 0/")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
