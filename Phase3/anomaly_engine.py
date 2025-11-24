"""
Anomaly Detection Engine - Phase 3
Telecom AI Multi-Agent System

Detects anomalies using 3 methods:
1. Z-score (statistical outlier detection)
2. IQR (Interquartile Range method)
3. Isolation Forest (ML-based anomaly detection)

Includes data normalization, severity classification, and trend analysis.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import logging
from typing import Dict, List, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class SeverityLevel(Enum):
    """Severity classification levels."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyMethod(Enum):
    """Available anomaly detection methods."""
    ZSCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"


class TrendDirection(Enum):
    """Trend direction for anomalies."""
    STABLE = "stable"
    IMPROVING = "improving"
    WORSENING = "worsening"


# Constants for severity thresholds
SEVERITY_THRESHOLDS = {
    "z_score": {
        "warning": 2.0,      # 2 standard deviations = warning
        "critical": 3.0      # 3 standard deviations = critical
    },
    "iqr": {
        "warning": 1.5,      # 1.5x IQR = warning
        "critical": 3.0      # 3x IQR = critical
    },
    "isolation_forest": {
        "warning": -0.3,     # Anomaly score threshold for warning
        "critical": -0.5     # Anomaly score threshold for critical
    }
}


# ============================================================================
# ANOMALY DETECTION ENGINE
# ============================================================================

class AnomalyDetectionEngine:
    """
    Core anomaly detection engine supporting 3 detection methods.
    
    Attributes:
        methods (List[AnomalyMethod]): Detection methods to use
        sensitivity (str): 'low', 'medium', 'high'
        scaler (StandardScaler): For data normalization
        data (pd.DataFrame): Original data
        normalized_data (pd.DataFrame): Normalized data
        anomalies (List[Dict]): Detected anomalies
    """
    
    def __init__(self, sensitivity: str = "medium", methods: List[str] = None):
        """
        Initialize anomaly detection engine.
        
        Args:
            sensitivity (str): 'low', 'medium', 'high' - affects thresholds
            methods (List[str]): List of methods to use. Defaults to all 3.
        """
        self.sensitivity = sensitivity
        self.scaler = StandardScaler()
        self.data = None
        self.normalized_data = None
        self.anomalies = []
        self.feature_stats = {}
        
        # Default to all 3 methods
        if methods is None:
            self.methods = [AnomalyMethod.ZSCORE, AnomalyMethod.IQR, AnomalyMethod.ISOLATION_FOREST]
        else:
            self.methods = [AnomalyMethod(m) for m in methods]
        
        logger.info(f"AnomalyDetectionEngine initialized with sensitivity={sensitivity}, methods={[m.value for m in self.methods]}")
    
    
    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data using StandardScaler.
        
        CRITICAL: Apply before anomaly detection (Phase 2 lesson)
        
        Args:
            data (pd.DataFrame): Raw data to normalize
            
        Returns:
            pd.DataFrame: Normalized data (mean=0, std=1)
        """
        logger.info(f"Normalizing data: {data.shape[0]} rows, {data.shape[1]} columns")
        
        self.data = data.copy()

        # Drop non-numeric columns (TIME, strings, etc.)
        non_numeric = self.data.select_dtypes(exclude=[np.number]).columns
        if len(non_numeric) > 0:
            logger.warning(f"Dropping non-numeric columns: {list(non_numeric)}")
            self.data = self.data.drop(columns=non_numeric)

        # Handle NaN values - drop rows with any NaN
        initial_rows = len(self.data)
        
        # Handle NaN values - drop rows with any NaN
        initial_rows = len(self.data)
        self.data = self.data.dropna()
        if len(self.data) < initial_rows:
            logger.warning(f"Dropped {initial_rows - len(self.data)} rows with NaN values")
        
        # Store original statistics for reporting
        self.feature_stats = {
            col: {
                "original_mean": self.data[col].mean(),
                "original_std": self.data[col].std(),
                "original_min": self.data[col].min(),
                "original_max": self.data[col].max()
            }
            for col in self.data.columns
        }
        
        # Normalize data
        self.normalized_data = pd.DataFrame(
            self.scaler.fit_transform(self.data),
            columns=self.data.columns,
            index=self.data.index
        )
        
        logger.info(f"Data normalized successfully. Mean={self.normalized_data.mean().mean():.6f}, Std={self.normalized_data.std().mean():.6f}")
        return self.normalized_data
    
    
    def _calculate_z_score_anomalies(self) -> List[Dict]:
        """
        Detect anomalies using Z-score method.
        
        Z-score = (value - mean) / std_dev
        - Score > 2: Warning (2% of data)
        - Score > 3: Critical (0.3% of data)
        
        Returns:
            List[Dict]: Detected anomalies with z-scores
        """
        logger.info("Running Z-score anomaly detection...")
        anomalies = []
        
        # Adjust thresholds based on sensitivity
        if self.sensitivity == "high":
            warning_threshold = 1.5
            critical_threshold = 2.5
        elif self.sensitivity == "low":
            warning_threshold = 2.5
            critical_threshold = 3.5
        else:  # medium
            warning_threshold = 2.0
            critical_threshold = 3.0
        
        for col in self.normalized_data.columns:
            col_data = self.normalized_data[col].values
            
            # Check for constant column (no variance)
            if self.normalized_data[col].std() == 0:
                logger.warning(f"Column {col} has zero variance - skipping Z-score")
                continue
            
            # Calculate z-scores
            z_scores = np.abs(col_data)
            
            # Find anomalies
            for idx, z_score in enumerate(z_scores):
                if z_score >= critical_threshold:
                    severity = SeverityLevel.CRITICAL
                    anomaly_score = z_score
                elif z_score >= warning_threshold:
                    severity = SeverityLevel.WARNING
                    anomaly_score = z_score
                else:
                    continue
                
                # Convert back to original scale for reporting
                original_value = self.data.iloc[idx][col]
                
                anomalies.append({
                    "kpi": col,
                    "index": idx,
                    "value": float(original_value),
                    "normalized_value": float(col_data[idx]),
                    "z_score": float(z_score),
                    "method": AnomalyMethod.ZSCORE.value,
                    "severity": severity.value,
                    "anomaly_score": float(anomaly_score),
                    "threshold": critical_threshold if severity == SeverityLevel.CRITICAL else warning_threshold
                })
        
        logger.info(f"Z-score detected {len(anomalies)} anomalies")
        return anomalies
    
    
    def _calculate_iqr_anomalies(self) -> List[Dict]:
        """
        Detect anomalies using Interquartile Range (IQR) method.
        
        IQR = Q3 - Q1
        Lower Bound = Q1 - 1.5 * IQR
        Upper Bound = Q3 + 1.5 * IQR
        
        Returns:
            List[Dict]: Detected anomalies with IQR info
        """
        logger.info("Running IQR anomaly detection...")
        anomalies = []
        
        # Adjust multipliers based on sensitivity
        if self.sensitivity == "high":
            warning_multiplier = 1.0
            critical_multiplier = 1.5
        elif self.sensitivity == "low":
            warning_multiplier = 2.0
            critical_multiplier = 3.0
        else:  # medium
            warning_multiplier = 1.5
            critical_multiplier = 3.0
        
        for col in self.normalized_data.columns:
            col_data = self.data[col].values  # Use original scale for IQR
            norm_col_data = self.normalized_data[col].values
            
            # Calculate quartiles
            Q1 = np.percentile(col_data, 25)
            Q3 = np.percentile(col_data, 75)
            IQR = Q3 - Q1
            
            if IQR == 0:
                logger.warning(f"Column {col} has zero IQR - skipping")
                continue
            
            lower_bound_warning = Q1 - warning_multiplier * IQR
            upper_bound_warning = Q3 + warning_multiplier * IQR
            lower_bound_critical = Q1 - critical_multiplier * IQR
            upper_bound_critical = Q3 + critical_multiplier * IQR
            
            # Find anomalies
            for idx, value in enumerate(col_data):
                if value < lower_bound_critical or value > upper_bound_critical:
                    severity = SeverityLevel.CRITICAL
                    distance = min(abs(value - lower_bound_critical), abs(value - upper_bound_critical))
                elif value < lower_bound_warning or value > upper_bound_warning:
                    severity = SeverityLevel.WARNING
                    distance = min(abs(value - lower_bound_warning), abs(value - upper_bound_warning))
                else:
                    continue
                
                anomalies.append({
                    "kpi": col,
                    "index": idx,
                    "value": float(value),
                    "normalized_value": float(norm_col_data[idx]),
                    "method": AnomalyMethod.IQR.value,
                    "severity": severity.value,
                    "q1": float(Q1),
                    "q3": float(Q3),
                    "iqr": float(IQR),
                    "anomaly_score": float(distance),
                    "lower_bound": float(lower_bound_critical if severity == SeverityLevel.CRITICAL else lower_bound_warning),
                    "upper_bound": float(upper_bound_critical if severity == SeverityLevel.CRITICAL else upper_bound_warning)
                })
        
        logger.info(f"IQR detected {len(anomalies)} anomalies")
        return anomalies
    
    
    def _calculate_isolation_forest_anomalies(self) -> List[Dict]:
        """
        Detect anomalies using Isolation Forest (ML-based).
        
        Isolation Forest isolates outliers by randomly selecting features
        and split values. Anomalies are isolated faster (shorter trees).
        
        Anomaly Score:
        - -1: Anomaly
        - 0: Uncertain
        - +1: Normal
        
        Returns:
            List[Dict]: Detected anomalies with anomaly scores
        """
        logger.info("Running Isolation Forest anomaly detection...")
        
        try:
            # Configure based on sensitivity
            if self.sensitivity == "high":
                contamination = 0.15  # Expect 15% anomalies
                random_state = 42
            elif self.sensitivity == "low":
                contamination = 0.05  # Expect 5% anomalies
                random_state = 42
            else:  # medium
                contamination = 0.10  # Expect 10% anomalies
                random_state = 42
            
            # Train Isolation Forest on normalized data
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=random_state,
                n_estimators=100
            )
            
            predictions = iso_forest.fit_predict(self.normalized_data)
            anomaly_scores = iso_forest.score_samples(self.normalized_data)
            
            anomalies = []
            
            # Adjust severity thresholds based on sensitivity
            if self.sensitivity == "high":
                critical_threshold = -0.3
                warning_threshold = -0.1
            elif self.sensitivity == "low":
                critical_threshold = -0.5
                warning_threshold = -0.3
            else:  # medium
                critical_threshold = -0.4
                warning_threshold = -0.2
            
            for idx, (prediction, score) in enumerate(zip(predictions, anomaly_scores)):
                # prediction: -1 = anomaly, 1 = normal
                # score: lower score = more anomalous
                
                if prediction == -1:  # Is anomaly
                    if score <= critical_threshold:
                        severity = SeverityLevel.CRITICAL
                    elif score <= warning_threshold:
                        severity = SeverityLevel.WARNING
                    else:
                        continue
                    
                    # Find which KPI contributed most to anomaly score
                    row_normalized = self.normalized_data.iloc[idx].values
                    max_deviation_idx = np.argmax(np.abs(row_normalized))
                    top_kpi = self.normalized_data.columns[max_deviation_idx]
                    top_value = self.data.iloc[idx][top_kpi]
                    
                    anomalies.append({
                        "kpi": top_kpi,
                        "index": idx,
                        "value": float(top_value),
                        "normalized_value": float(row_normalized[max_deviation_idx]),
                        "method": AnomalyMethod.ISOLATION_FOREST.value,
                        "severity": severity.value,
                        "anomaly_score": float(score),
                        "prediction": "anomaly" if prediction == -1 else "normal",
                        "contamination": contamination
                    })
            
            logger.info(f"Isolation Forest detected {len(anomalies)} anomalies")
            return anomalies
        
        except Exception as e:
            logger.error(f"Isolation Forest error: {str(e)}")
            return []
    
    
    def detect_anomalies(self) -> List[Dict]:
        """
        Run all enabled detection methods and combine results.
        
        Returns:
            List[Dict]: All detected anomalies from all methods
        """
        if self.normalized_data is None:
            logger.error("Data not normalized. Call normalize_data() first.")
            raise ValueError("Data not normalized. Call normalize_data() first.")
        
        logger.info("Starting anomaly detection...")
        all_anomalies = []
        
        try:
            # Run Z-score
            if AnomalyMethod.ZSCORE in self.methods:
                all_anomalies.extend(self._calculate_z_score_anomalies())
            
            # Run IQR
            if AnomalyMethod.IQR in self.methods:
                all_anomalies.extend(self._calculate_iqr_anomalies())
            
            # Run Isolation Forest
            if AnomalyMethod.ISOLATION_FOREST in self.methods:
                all_anomalies.extend(self._calculate_isolation_forest_anomalies())
        
        except Exception as e:
            logger.error(f"Error during anomaly detection: {str(e)}")
            raise
        
        self.anomalies = all_anomalies
        logger.info(f"Total anomalies detected: {len(all_anomalies)}")
        return all_anomalies
    
    
    def calculate_trend(self, kpi: str, lookback_periods: int = 5) -> Tuple[TrendDirection, List[float]]:
        """
        Calculate trend for a specific KPI.
        
        Args:
            kpi (str): KPI column name
            lookback_periods (int): Number of periods to look back
            
        Returns:
            Tuple[TrendDirection, List[float]]: Trend direction and values
        """
        if self.data is None:
            logger.error("Data not loaded")
            return TrendDirection.STABLE, []
        
        if kpi not in self.data.columns:
            logger.error(f"KPI '{kpi}' not found in data")
            return TrendDirection.STABLE, []
        
        # Get last N values
        values = self.data[kpi].tail(lookback_periods).values.tolist()
        
        if len(values) < 2:
            return TrendDirection.STABLE, values
        
        # Calculate trend
        direction_changes = sum(1 for i in range(len(values) - 1) if values[i+1] > values[i])
        decline_changes = len(values) - 1 - direction_changes
        
        if direction_changes > decline_changes:
            trend = TrendDirection.WORSENING
        elif decline_changes > direction_changes:
            trend = TrendDirection.IMPROVING
        else:
            trend = TrendDirection.STABLE
        
        logger.info(f"Trend for {kpi}: {trend.value}")
        return trend, values
    
    
    def classify_network_severity(self, anomalies: List[Dict] = None) -> Dict[str, Any]:
        """
        Classify overall network severity based on anomalies.
        
        Args:
            anomalies (List[Dict]): List of anomalies. Uses self.anomalies if None.
            
        Returns:
            Dict: Network health classification
        """
        if anomalies is None:
            anomalies = self.anomalies
        
        if not anomalies:
            return {
                "network_status": SeverityLevel.NORMAL.value,
                "critical_count": 0,
                "warning_count": 0,
                "affected_kpis": []
            }
        
        critical_count = sum(1 for a in anomalies if a["severity"] == SeverityLevel.CRITICAL.value)
        warning_count = sum(1 for a in anomalies if a["severity"] == SeverityLevel.WARNING.value)
        affected_kpis = list(set([a["kpi"] for a in anomalies]))
        
        # Determine network status
        if critical_count > 0:
            network_status = SeverityLevel.CRITICAL.value
        elif warning_count > 0:
            network_status = SeverityLevel.WARNING.value
        else:
            network_status = SeverityLevel.NORMAL.value
        
        logger.info(f"Network status: {network_status} (Critical: {critical_count}, Warning: {warning_count})")
        
        return {
            "network_status": network_status,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "total_anomalies": len(anomalies),
            "affected_kpis": affected_kpis,
            "affected_kpi_count": len(affected_kpis)
        }
    
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of anomaly detection results.
        
        Returns:
            Dict: Summary with statistics and recommendations
        """
        network_status = self.classify_network_severity()
        
        summary = {
            "detection_timestamp": datetime.now().isoformat(),
            "sensitivity": self.sensitivity,
            "methods_used": [m.value for m in self.methods],
            "data_points_analyzed": len(self.data) if self.data is not None else 0,
            "kpis_analyzed": len(self.data.columns) if self.data is not None else 0,
            "network_status": network_status,
            "anomalies_by_method": self._get_anomalies_by_method(),
            "anomalies_by_kpi": self._get_anomalies_by_kpi(),
            "total_anomalies": len(self.anomalies)
        }
        
        logger.info(f"Summary generated: {len(self.anomalies)} total anomalies found")
        return summary
    
    
    def _get_anomalies_by_method(self) -> Dict[str, int]:
        """Count anomalies by detection method."""
        by_method = {}
        for anomaly in self.anomalies:
            method = anomaly.get("method", "unknown")
            by_method[method] = by_method.get(method, 0) + 1
        return by_method
    
    
    def _get_anomalies_by_kpi(self) -> Dict[str, int]:
        """Count anomalies by KPI."""
        by_kpi = {}
        for anomaly in self.anomalies:
            kpi = anomaly.get("kpi", "unknown")
            by_kpi[kpi] = by_kpi.get(kpi, 0) + 1
        return by_kpi
    
    
    def export_anomalies_json(self) -> Dict[str, Any]:
        """
        Export anomalies in JSON format for API response.
        
        Returns:
            Dict: Complete anomaly report
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "anomalies": self.anomalies,
            "network_classification": self.classify_network_severity()
        }


# ============================================================================
# MAIN EXECUTION (FOR TESTING)
# ============================================================================

if __name__ == "__main__":
    print("Anomaly Detection Engine loaded successfully")
    print(f"Available Methods: {[m.value for m in AnomalyMethod]}")
    print(f"Available Severity Levels: {[s.value for s in SeverityLevel]}")
    print(f"Available Trend Directions: {[t.value for t in TrendDirection]}")