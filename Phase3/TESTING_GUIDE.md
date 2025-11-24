"""
TESTING GUIDE - Choose Your Approach
"""

# ============================================================================
# OPTION 1: QUICK TEST (Basic - handles BOM only)
# ============================================================================

# File: quick_test.py
# What it does:
#   - Loads CSV with encoding='utf-8-sig' (removes BOM)
#   - Filters to numeric columns only
#   - Runs anomaly detection
#
# Date formats it handles:
#   - Works if dates already removed or in numeric columns only
#
# When to use:
#   - Your CSV has minimal datetime columns
#   - Just want to verify anomaly engine works
#
# Command:
#   python quick_test.py


# ============================================================================
# OPTION 2: ADVANCED TEST (Recommended - auto-detects dates)
# ============================================================================

# Files needed:
#   - intelligent_csv_loader.py (in Phase 3/)
#   - advanced_test.py (in Phase 3/)
#   - anomaly_engine.py (already in Phase 3/)
#
# What it does:
#   - Auto-detects date columns by name and content
#   - Tries multiple date formats (US, ISO, European, with time, etc.)
#   - Removes datetime columns (not needed for anomaly detection)
#   - Converts remaining columns to numeric
#   - Runs anomaly detection
#
# Date formats it handles:
#   ✅ 3/1/2024 (US format)
#   ✅ 03/01/2024 (US with leading zeros)
#   ✅ 1/3/2024 (alternative US)
#   ✅ 2025-03-10 (ISO format)
#   ✅ 2025-03-10 14:30:45 (ISO with time)
#   ✅ 10/03/2025 (European format)
#   ✅ 2025-03-10T14:30:00Z (ISO 8601)
#   ✅ 3/1/20243 (malformed - will handle gracefully)
#
# When to use:
#   - Your CSV has many datetime columns
#   - Dates in various formats
#   - Want automatic format detection
#   - Most reliable approach
#
# Command:
#   python advanced_test.py


# ============================================================================
# STEP-BY-STEP VERIFICATION PROCESS
# ============================================================================

"""
STEP 1: Run the basic test
        python quick_test.py

        Expected output:
        ✅ Loaded: XXXX rows, XX columns
        ✅ Cleaned: XXXX rows, XX numeric columns
        ✅ Detection complete: Found XXX anomalies
        ✅ SUCCESS!

        If PASSED → Go to STEP 2
        If FAILED → Check error message


STEP 2: Run the advanced test (with intelligent loader)
        python advanced_test.py

        Expected output:
        INFO - Column 'TIME': Detected format '%m/%d/%Y'
        INFO - Successfully parsed 'TIME' as datetime
        ✅ Data loaded: XXXX rows, XX columns
        ✅ Detection complete: Found XXX anomalies
        ✅ SUCCESS!

        If PASSED → Component 1 is VERIFIED ✅
        If FAILED → Check error message


STEP 3: Run all 5 original verification scripts
        python verify_import.py
        python verify_engine_fixed.py
        python verify_methods.py
        python verify_sensitivity.py
        python verify_classification.py

        All should pass → Ready for Component 2 ✅
"""


# ============================================================================
# YOUR CURRENT FILES IN PHASE 3/
# ============================================================================

"""
Phase 3/
├── anomaly_engine.py              ✅ Core engine (already created)
├── quick_test.py                  ✅ Basic test (handles BOM)
├── intelligent_csv_loader.py      ✅ Auto-detect dates (NEW!)
├── advanced_test.py               ✅ Advanced test (NEW!)
├── verify_import.py               ✅ Import test
├── verify_engine_fixed.py         ✅ Engine with fixed CSV handling
├── verify_methods.py              ✅ Test each method
├── verify_sensitivity.py          ✅ Test sensitivity levels
└── verify_classification.py       ✅ Test network classification
"""


# ============================================================================
# QUICK ANSWER: YOUR QUESTION
# ============================================================================

"""
Q: Can the code detect date formats automatically?
   (e.g., 3/1/2024, 2025-03-10, 2025-03-10 00:00:00)

A: YES! Absolutely!

   intelligent_csv_loader.py provides:
   
   1. auto_detect_datetime_column()
      - Tries common formats first (fast)
      - Falls back to flexible parser (handles edge cases)
      - Returns >90% success rate
   
   2. load_kpi_data_intelligent()
      - Identifies datetime columns by name (TIME, DATE, etc.)
      - Identifies by content (contains /, -, etc.)
      - Auto-parses each column with best format
      - Removes datetime columns (not needed for metrics)
      - Returns clean numeric data
   
   Supported formats:
   ✅ US: 3/1/2024, 03/01/2024
   ✅ ISO: 2025-03-10, 2025-03-10 14:30:45
   ✅ European: 10/03/2025
   ✅ ISO 8601: 2025-03-10T14:30:00Z
   ✅ Malformed: Handles gracefully (returns warnings)
   
   How it works:
   1. Detect column likely contains dates
   2. Try: %Y-%m-%d → %m/%d/%Y → %d/%m/%Y → %Y-%m-%d %H:%M:%S
   3. If format works for >90% of values → use it
   4. Otherwise use flexible parser (handles edge cases)
   5. Drop the datetime column (keep only numeric metrics)
   
   Result: Clean data ready for anomaly detection!
"""


# ============================================================================
# INTEGRATION WITH ANOMALY_ENGINE
# ============================================================================

"""
You have 3 ways to use the intelligent loader:

OPTION A: Use in verification scripts
from intelligent_csv_loader import load_kpi_data_intelligent
from anomaly_engine import AnomalyDetectionEngine

data = load_kpi_data_intelligent('path/to/data.csv')  # Auto-detects dates
engine = AnomalyDetectionEngine()
engine.normalize_data(data)  # Works with any numeric data
anomalies = engine.detect_anomalies()


OPTION B: Use in API endpoints (coming in Component 2)
# anomaly_api.py will use intelligent loader automatically


OPTION C: Integrate into anomaly_engine.py normalize_data()
# Update normalize_data() to handle date columns automatically
# Add auto-detection logic there
"""
