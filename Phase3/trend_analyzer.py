"""
trend_analyzer.py - Phase 3 Trend Analysis
Analyzes trends and provides insights
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Service for analyzing trends in anomaly data."""
    
    def __init__(self):
        """Initialize trend analyzer."""
        self.history = []
        logger.info("TrendAnalyzer initialized")
    
    # ========================================================================
    # TREND ANALYSIS
    # ========================================================================
    
    def add_analysis_result(self, results: Dict):
        """
        Add analysis result to history for trend tracking.
        
        Args:
            results (Dict): Analysis results
        """
        self.history.append({
            'timestamp': results.get('timestamp'),
            'task_id': results.get('task_id'),
            'total_anomalies': results.get('network_classification', {}).get('total_anomalies', 0),
            'critical': results.get('network_classification', {}).get('critical_count', 0),
            'warning': results.get('network_classification', {}).get('warning_count', 0),
        })
        logger.info(f"Added analysis to history (total: {len(self.history)})")
    
    def get_trend_direction(self, values: List[float]) -> str:
        """
        Determine trend direction (up, down, stable).
        
        Args:
            values (List[float]): List of values
            
        Returns:
            str: Direction (up, down, stable)
        """
        if len(values) < 2:
            return 'stable'
        
        # Calculate average change rate
        changes = [values[i+1] - values[i] for i in range(len(values)-1)]
        avg_change = sum(changes) / len(changes) if changes else 0
        
        if abs(avg_change) < 0.5:
            return 'stable'
        return 'up' if avg_change > 0 else 'down'
    
    def get_trend_analysis(self, results: Dict) -> Dict:
        """
        Generate comprehensive trend analysis.
        
        Args:
            results (Dict): Current analysis results
            
        Returns:
            Dict: Trend analysis data
        """
        anomalies = results.get('anomalies', [])
        summary = results.get('summary', {})
        
        if not anomalies:
            return {
                'total_trend': 'stable',
                'severity_distribution': {'critical_trend': 'stable', 'warning_trend': 'stable'},
                'method_effectiveness': {}
            }
        
        # Analyze severity trends
        severity_list = [a.get('severity', 'normal').lower() for a in anomalies]
        critical_ratio = severity_list.count('critical') / len(severity_list)
        warning_ratio = severity_list.count('warning') / len(severity_list)
        
        # Analyze method effectiveness
        anomalies_by_method = summary.get('anomalies_by_method', {})
        total_by_method = sum(anomalies_by_method.values()) if anomalies_by_method else 1
        
        method_effectiveness = {
            method: {
                'count': count,
                'percentage': round((count / total_by_method) * 100, 2),
                'effectiveness_score': round((count / total_by_method) * 100, 2)
            }
            for method, count in anomalies_by_method.items()
        }
        
        return {
            'total_anomalies': len(anomalies),
            'severity_distribution': {
                'critical_percentage': round(critical_ratio * 100, 2),
                'warning_percentage': round(warning_ratio * 100, 2),
                'normal_percentage': round((1 - critical_ratio - warning_ratio) * 100, 2)
            },
            'method_effectiveness': method_effectiveness,
            'anomaly_score_stats': {
                'average': round(statistics.mean([a.get('anomaly_score', 0) for a in anomalies]), 3),
                'median': round(statistics.median([a.get('anomaly_score', 0) for a in anomalies]), 3),
                'stdev': round(statistics.stdev([a.get('anomaly_score', 0) for a in anomalies]), 3) if len(anomalies) > 1 else 0
            }
        }
    
    # ========================================================================
    # KPI INSIGHTS
    # ========================================================================
    
    def get_kpi_insights(self, results: Dict) -> Dict:
        """
        Generate insights about affected KPIs.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: KPI insights
        """
        anomalies = results.get('anomalies', [])
        summary = results.get('summary', {})
        
        anomalies_by_kpi = summary.get('anomalies_by_kpi', {})
        
        # Get top and bottom KPIs
        sorted_kpis = sorted(anomalies_by_kpi.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'most_affected': [{'kpi': kpi, 'anomalies': count} for kpi, count in sorted_kpis[:5]],
            'least_affected': [{'kpi': kpi, 'anomalies': count} for kpi, count in sorted_kpis[-5:] if count > 0],
            'total_affected_kpis': len(anomalies_by_kpi),
            'average_anomalies_per_kpi': round(
                sum(anomalies_by_kpi.values()) / max(1, len(anomalies_by_kpi)), 2
            )
        }
    
    # ========================================================================
    # SEVERITY INSIGHTS
    # ========================================================================
    
    def get_severity_insights(self, results: Dict) -> Dict:
        """
        Generate severity-based insights.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Severity insights
        """
        network_class = results.get('network_classification', {})
        total = network_class.get('total_anomalies', 0)
        
        critical_count = network_class.get('critical_count', 0)
        warning_count = network_class.get('warning_count', 0)
        normal_count = total - critical_count - warning_count
        
        return {
            'critical': {
                'count': critical_count,
                'percentage': round((critical_count / max(1, total)) * 100, 2),
                'status': 'CRITICAL' if critical_count > 0 else 'OK'
            },
            'warning': {
                'count': warning_count,
                'percentage': round((warning_count / max(1, total)) * 100, 2),
                'status': 'WARNING' if warning_count > total * 0.3 else 'OK'
            },
            'normal': {
                'count': normal_count,
                'percentage': round((normal_count / max(1, total)) * 100, 2),
                'status': 'OK'
            },
            'risk_level': self._calculate_risk_level(critical_count, warning_count, total)
        }
    
    def _calculate_risk_level(self, critical: int, warning: int, total: int) -> str:
        """Calculate overall risk level."""
        if total == 0:
            return 'LOW'
        
        critical_ratio = critical / total
        warning_ratio = warning / total
        
        if critical_ratio > 0.2:
            return 'CRITICAL'
        elif critical_ratio > 0.1 or warning_ratio > 0.5:
            return 'HIGH'
        elif warning_ratio > 0.2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================
    
    def generate_recommendations(self, results: Dict) -> List[str]:
        """
        Generate recommendations based on analysis.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        network_class = results.get('network_classification', {})
        summary = results.get('summary', {})
        
        critical_count = network_class.get('critical_count', 0)
        warning_count = network_class.get('warning_count', 0)
        total_anomalies = network_class.get('total_anomalies', 0)
        
        # Critical anomalies
        if critical_count > 0:
            recommendations.append(
                f"⚠️ CRITICAL: {critical_count} critical anomalies detected. "
                "Immediate investigation required."
            )
        
        # High warning count
        if warning_count > total_anomalies * 0.5:
            recommendations.append(
                f"⚠️ HIGH VOLUME: {warning_count} warning-level anomalies. "
                "Consider threshold adjustment or investigation."
            )
        
        # Anomaly rate
        data_points = summary.get('data_points_analyzed', 1)
        anomaly_rate = (total_anomalies / max(1, data_points)) * 100
        if anomaly_rate > 30:
            recommendations.append(
                f"📊 HIGH RATE: Anomaly rate at {anomaly_rate:.1f}%. "
                "System may need recalibration."
            )
        
        # KPI concentration
        anomalies_by_kpi = summary.get('anomalies_by_kpi', {})
        if anomalies_by_kpi:
            top_kpi_anomalies = max(anomalies_by_kpi.values())
            if top_kpi_anomalies > total_anomalies * 0.3:
                top_kpi = max(anomalies_by_kpi, key=anomalies_by_kpi.get)
                recommendations.append(
                    f"🎯 FOCUS: KPI '{top_kpi}' shows {top_kpi_anomalies} anomalies. "
                    "Requires priority attention."
                )
        
        # Method comparison
        anomalies_by_method = summary.get('anomalies_by_method', {})
        if anomalies_by_method:
            most_effective = max(anomalies_by_method, key=anomalies_by_method.get)
            recommendations.append(
                f"✅ METHOD: {most_effective.replace('_', ' ').title()} "
                f"detected the most anomalies ({anomalies_by_method[most_effective]})."
            )
        
        # No anomalies
        if total_anomalies == 0:
            recommendations.append(
                "✅ EXCELLENT: No anomalies detected. Network operating normally."
            )
        
        return recommendations
    
    # ========================================================================
    # COMPARISON
    # ========================================================================
    
    def compare_analyses(self, current: Dict, previous: Dict) -> Dict:
        """
        Compare two analysis results.
        
        Args:
            current (Dict): Current analysis
            previous (Dict): Previous analysis
            
        Returns:
            Dict: Comparison results
        """
        current_total = current.get('network_classification', {}).get('total_anomalies', 0)
        previous_total = previous.get('network_classification', {}).get('total_anomalies', 0)
        
        change = current_total - previous_total
        change_percent = ((change / max(1, previous_total)) * 100) if previous_total > 0 else 0
        
        return {
            'current_total': current_total,
            'previous_total': previous_total,
            'absolute_change': change,
            'percentage_change': round(change_percent, 2),
            'trend': 'improved' if change < 0 else 'worsened' if change > 0 else 'stable',
            'change_indicator': '📉' if change < 0 else '📈' if change > 0 else '→'
        }
