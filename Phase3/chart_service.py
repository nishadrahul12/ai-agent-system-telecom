"""
chart_service.py - Phase 3 Chart Service
Generates chart data for dashboard visualization
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ChartService:
    """Service for generating chart data."""
    
    def __init__(self):
        """Initialize chart service."""
        logger.info("ChartService initialized")
    
    # ========================================================================
    # ANOMALIES DISTRIBUTION CHARTS
    # ========================================================================
    
    def get_anomalies_by_severity(self, results: Dict) -> Dict:
        """
        Get anomalies grouped by severity.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Chart data for pie/bar chart
        """
        anomalies = results.get('anomalies', [])
        severity_counts = {'critical': 0, 'warning': 0, 'normal': 0}
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'normal').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            'labels': ['Critical', 'Warning', 'Normal'],
            'data': [
                severity_counts['critical'],
                severity_counts['warning'],
                severity_counts['normal']
            ],
            'colors': ['#D32F2F', '#F57C00', '#388E3C'],
            'type': 'doughnut'
        }
    
    def get_anomalies_by_method(self, results: Dict) -> Dict:
        """
        Get anomalies grouped by detection method.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Chart data for bar chart
        """
        summary = results.get('summary', {})
        anomalies_by_method = summary.get('anomalies_by_method', {})
        
        return {
            'labels': [method.replace('_', ' ').title() for method in anomalies_by_method.keys()],
            'data': list(anomalies_by_method.values()),
            'backgroundColor': ['#2196F3', '#FF9800', '#4CAF50'],
            'type': 'bar'
        }
    
    def get_top_kpis_chart(self, results: Dict, limit: int = 10) -> Dict:
        """
        Get top affected KPIs for bar chart.
        
        Args:
            results (Dict): Analysis results
            limit (int): Number of top KPIs
            
        Returns:
            Dict: Chart data for bar chart
        """
        summary = results.get('summary', {})
        anomalies_by_kpi = summary.get('anomalies_by_kpi', {})
        
        # Sort and take top N
        top_kpis = sorted(anomalies_by_kpi.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return {
            'labels': [kpi for kpi, _ in top_kpis],
            'data': [count for _, count in top_kpis],
            'backgroundColor': '#FF6B6B',
            'type': 'horizontalBar'
        }
    
    # ========================================================================
    # TREND ANALYSIS
    # ========================================================================
    
    def get_anomaly_trends(self, results: Dict) -> Dict:
        """
        Generate trend data for anomalies over time.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Trend chart data
        """
        anomalies = results.get('anomalies', [])
        
        # Simulate time-based distribution (in real scenario, use actual timestamps)
        time_buckets = {}
        
        for i, anomaly in enumerate(anomalies):
            # Distribute anomalies across time buckets
            bucket = (i // max(1, len(anomalies) // 10)) * 10
            time_buckets[bucket] = time_buckets.get(bucket, 0) + 1
        
        sorted_buckets = sorted(time_buckets.items())
        
        return {
            'labels': [f"Period {i+1}" for i in range(len(sorted_buckets))],
            'data': [count for _, count in sorted_buckets],
            'type': 'line',
            'tension': 0.4,
            'borderColor': '#2196F3',
            'backgroundColor': 'rgba(33, 150, 243, 0.1)'
        }
    
    # ========================================================================
    # KPI COMPARISON
    # ========================================================================
    
    def get_kpi_comparison(self, current_results: Dict, previous_results: Optional[Dict] = None) -> Dict:
        """
        Compare current vs previous analysis.
        
        Args:
            current_results (Dict): Current analysis results
            previous_results (Optional[Dict]): Previous analysis results
            
        Returns:
            Dict: Comparison data
        """
        current_summary = current_results.get('summary', {})
        current_total = current_results.get('network_classification', {}).get('total_anomalies', 0)
        
        if previous_results:
            previous_summary = previous_results.get('summary', {})
            previous_total = previous_results.get('network_classification', {}).get('total_anomalies', 0)
            
            change_percent = ((current_total - previous_total) / max(1, previous_total)) * 100
        else:
            previous_total = current_total
            change_percent = 0
        
        return {
            'current': current_total,
            'previous': previous_total,
            'change': current_total - previous_total,
            'change_percent': round(change_percent, 2),
            'trend': 'up' if change_percent > 0 else 'down' if change_percent < 0 else 'stable'
        }
    
    # ========================================================================
    # STATISTICAL SUMMARY
    # ========================================================================
    
    def get_statistics_summary(self, results: Dict) -> Dict:
        """
        Generate statistical summary for dashboard.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Statistics data
        """
        anomalies = results.get('anomalies', [])
        summary = results.get('summary', {})
        network_class = results.get('network_classification', {})
        
        # Calculate statistics
        if anomalies:
            anomaly_scores = [a.get('anomaly_score', 0) for a in anomalies]
            avg_score = sum(anomaly_scores) / len(anomaly_scores)
            max_score = max(anomaly_scores)
            min_score = min(anomaly_scores)
        else:
            avg_score = max_score = min_score = 0
        
        return {
            'total_anomalies': network_class.get('total_anomalies', 0),
            'critical_count': network_class.get('critical_count', 0),
            'warning_count': network_class.get('warning_count', 0),
            'data_points': summary.get('data_points_analyzed', 0),
            'kpis_analyzed': summary.get('kpis_analyzed', 0),
            'anomaly_rate': round((network_class.get('total_anomalies', 0) / max(1, summary.get('data_points_analyzed', 1))) * 100, 2),
            'avg_anomaly_score': round(avg_score, 3),
            'max_anomaly_score': round(max_score, 3),
            'min_anomaly_score': round(min_score, 3)
        }
    
    # ========================================================================
    # HEATMAP DATA
    # ========================================================================
    
    def get_kpi_severity_matrix(self, results: Dict) -> Dict:
        """
        Get KPI vs Severity matrix for heatmap.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Heatmap data
        """
        anomalies = results.get('anomalies', [])
        
        # Create matrix: KPIs x Severities
        matrix = {}
        
        for anomaly in anomalies:
            kpi = anomaly.get('kpi', 'Unknown')
            severity = anomaly.get('severity', 'normal').lower()
            
            if kpi not in matrix:
                matrix[kpi] = {'critical': 0, 'warning': 0, 'normal': 0}
            
            if severity in matrix[kpi]:
                matrix[kpi][severity] += 1
        
        # Convert to chart format (top 15 KPIs)
        top_kpis = sorted(matrix.keys(), 
                         key=lambda k: sum(matrix[k].values()), 
                         reverse=True)[:15]
        
        return {
            'kpis': top_kpis,
            'severities': ['critical', 'warning', 'normal'],
            'matrix': [
                [matrix.get(kpi, {}).get(sev, 0) for sev in ['critical', 'warning', 'normal']]
                for kpi in top_kpis
            ],
            'type': 'heatmap'
        }
    
    # ========================================================================
    # NETWORK HEALTH GAUGE
    # ========================================================================
    
    def get_network_health_score(self, results: Dict) -> Dict:
        """
        Calculate network health score (0-100).
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Health score data
        """
        network_class = results.get('network_classification', {})
        summary = results.get('summary', {})
        
        total_anomalies = network_class.get('total_anomalies', 0)
        critical_count = network_class.get('critical_count', 0)
        warning_count = network_class.get('warning_count', 0)
        data_points = summary.get('data_points_analyzed', 1)
        
        # Calculate health score
        # Base: 100
        # Deduct: 5 per warning, 10 per critical
        # Deduct: anomaly_rate (0-30)
        
        anomaly_rate = min(30, (total_anomalies / max(1, data_points)) * 100)
        health_score = 100 - (warning_count * 5) - (critical_count * 10) - (anomaly_rate / 3)
        health_score = max(0, min(100, health_score))
        
        # Determine status
        if health_score >= 80:
            status = 'Excellent'
            color = '#4CAF50'
        elif health_score >= 60:
            status = 'Good'
            color = '#8BC34A'
        elif health_score >= 40:
            status = 'Fair'
            color = '#FF9800'
        else:
            status = 'Poor'
            color = '#F44336'
        
        return {
            'score': round(health_score, 1),
            'status': status,
            'color': color,
            'max': 100
        }
    
    # ========================================================================
    # COMPREHENSIVE DASHBOARD DATA
    # ========================================================================
    
    def get_dashboard_data(self, results: Dict) -> Dict:
        """
        Get all dashboard data at once.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Complete dashboard data
        """
        return {
            'severity_distribution': self.get_anomalies_by_severity(results),
            'method_distribution': self.get_anomalies_by_method(results),
            'top_kpis': self.get_top_kpis_chart(results),
            'trends': self.get_anomaly_trends(results),
            'statistics': self.get_statistics_summary(results),
            'health_score': self.get_network_health_score(results),
            'kpi_matrix': self.get_kpi_severity_matrix(results),
            'timestamp': datetime.now().isoformat()
        }
