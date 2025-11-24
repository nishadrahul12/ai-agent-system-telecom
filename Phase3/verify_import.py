"""Verify import functionality."""
import sys
sys.path.insert(0, '..')

try:
    from anomaly_engine import (
        AnomalyDetectionEngine,
        SeverityLevel,
        AnomalyMethod,
        TrendDirection
    )
    print("✅ Import successful!")
    print(f"✅ SeverityLevel options: {[s.value for s in SeverityLevel]}")
    print(f"✅ AnomalyMethod options: {[m.value for m in AnomalyMethod]}")
    print(f"✅ TrendDirection options: {[t.value for t in TrendDirection]}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
