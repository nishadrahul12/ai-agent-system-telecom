"""
export_service.py - Phase 3 Export & Reporting Service
Handles exporting anomaly detection results to multiple formats
"""

import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Try to import PDF library (optional - skip if not available)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PDF library not available - PDF export disabled")

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting anomaly detection results."""
    
    def __init__(self, base_dir: str = "Phase3/exports"):
        """Initialize export service."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ExportService initialized with base_dir: {base_dir}")
    
    # ========================================================================
    # CSV EXPORT
    # ========================================================================
    
    def export_to_csv(self, task_id: str, results: Dict) -> Optional[str]:
        """
        Export analysis results to CSV format.
        
        Args:
            task_id (str): Task ID for naming
            results (Dict): Analysis results from API
            
        Returns:
            Optional[str]: Path to exported CSV file, or None if failed
        """
        try:
            # Create export directory
            export_dir = self.base_dir / task_id
            export_dir.mkdir(parents=True, exist_ok=True)
            
            csv_file = export_dir / f"anomalies_{task_id}.csv"
            
            # Extract anomalies
            anomalies = results.get('anomalies', [])
            
            if not anomalies:
                logger.warning(f"No anomalies to export for task {task_id}")
                return None
            
            # Write to CSV
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                # Get field names from first anomaly
                fieldnames = anomalies[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                writer.writerows(anomalies)
            
            logger.info(f"Exported {len(anomalies)} anomalies to CSV: {csv_file}")
            return str(csv_file)
        
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            return None
    
    # ========================================================================
    # JSON EXPORT
    # ========================================================================
    
    def export_to_json(self, task_id: str, results: Dict) -> Optional[str]:
        """
        Export analysis results to JSON format.
        
        Args:
            task_id (str): Task ID for naming
            results (Dict): Analysis results from API
            
        Returns:
            Optional[str]: Path to exported JSON file, or None if failed
        """
        try:
            # Create export directory
            export_dir = self.base_dir / task_id
            export_dir.mkdir(parents=True, exist_ok=True)
            
            json_file = export_dir / f"analysis_{task_id}.json"
            
            # Add metadata
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'task_id': task_id,
                'analysis': results
            }
            
            # Write to JSON with pretty formatting
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported analysis to JSON: {json_file}")
            return str(json_file)
        
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            return None
    
    # ========================================================================
    # PDF EXPORT
    # ========================================================================
    
    def export_to_pdf(self, task_id: str, results: Dict) -> Optional[str]:
        """
        Export analysis results to PDF format.
        
        Args:
            task_id (str): Task ID for naming
            results (Dict): Analysis results from API
            
        Returns:
            Optional[str]: Path to exported PDF file, or None if failed
        """
        if not PDF_AVAILABLE:
            logger.warning("PDF export not available - reportlab not installed")
            return None
        
        try:
            # Create export directory
            export_dir = self.base_dir / task_id
            export_dir.mkdir(parents=True, exist_ok=True)
            
            pdf_file = export_dir / f"report_{task_id}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_file), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2196F3'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Add title
            story.append(Paragraph("Telecom Anomaly Detection Report", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Add summary section
            story.append(Paragraph("Executive Summary", heading_style))
            
            summary = results.get('summary', {})
            network_class = results.get('network_classification', {})
            
            summary_text = f"""
            <b>Analysis Date:</b> {results.get('timestamp', 'N/A')}<br/>
            <b>Network Status:</b> <b style="color: {'red' if network_class.get('network_status') == 'critical' else 'orange' if network_class.get('network_status') == 'warning' else 'green'}">{network_class.get('network_status', 'N/A').upper()}</b><br/>
            <b>Total Anomalies:</b> {network_class.get('total_anomalies', 0)}<br/>
            <b>Critical:</b> {network_class.get('critical_count', 0)} | 
            <b>Warning:</b> {network_class.get('warning_count', 0)}<br/>
            <b>Data Points Analyzed:</b> {summary.get('data_points_analyzed', 0)}<br/>
            <b>KPIs Analyzed:</b> {summary.get('kpis_analyzed', 0)}<br/>
            <b>Sensitivity:</b> {summary.get('sensitivity', 'N/A')}<br/>
            """
            
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Add anomalies by method
            story.append(Paragraph("Anomalies by Detection Method", heading_style))
            
            anomalies_by_method = summary.get('anomalies_by_method', {})
            method_data = [
                ['Method', 'Count'],
            ]
            for method, count in anomalies_by_method.items():
                method_data.append([method, str(count)])
            
            method_table = Table(method_data)
            method_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(method_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Add top affected KPIs
            story.append(Paragraph("Top Affected KPIs", heading_style))
            
            anomalies_by_kpi = summary.get('anomalies_by_kpi', {})
            top_kpis = sorted(anomalies_by_kpi.items(), key=lambda x: x[1], reverse=True)[:10]
            
            kpi_data = [['KPI Name', 'Anomalies']]
            for kpi, count in top_kpis:
                kpi_data.append([kpi, str(count)])
            
            kpi_table = Table(kpi_data)
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F44336')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(kpi_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Add footer
            story.append(Paragraph(
                f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Task ID: {results.get('task_id', 'N/A')}</i>",
                styles['Normal']
            ))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Exported analysis to PDF: {pdf_file}")
            return str(pdf_file)
        
        except Exception as e:
            logger.error(f"PDF export failed: {str(e)}")
            return None
    
    # ========================================================================
    # BATCH EXPORT
    # ========================================================================
    
    def export_all_formats(self, task_id: str, results: Dict) -> Dict[str, Optional[str]]:
        """
        Export results to all available formats.
        
        Args:
            task_id (str): Task ID
            results (Dict): Analysis results
            
        Returns:
            Dict[str, Optional[str]]: Mapping of format to file path
        """
        return {
            'csv': self.export_to_csv(task_id, results),
            'json': self.export_to_json(task_id, results),
            'pdf': self.export_to_pdf(task_id, results),
        }
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def get_export_history(self) -> List[Dict]:
        """
        Get list of all exports.
        
        Returns:
            List[Dict]: List of export metadata
        """
        history = []
        
        for task_dir in self.base_dir.iterdir():
            if task_dir.is_dir():
                files = list(task_dir.glob('*'))
                if files:
                    history.append({
                        'task_id': task_dir.name,
                        'files': [f.name for f in files],
                        'timestamp': task_dir.stat().st_mtime
                    })
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_exports(self, days: int = 30) -> int:
        """
        Clean up old exports.
        
        Args:
            days (int): Delete exports older than this many days
            
        Returns:
            int: Number of exports deleted
        """
        import time
        
        deleted = 0
        threshold = time.time() - (days * 24 * 3600)
        
        for task_dir in self.base_dir.iterdir():
            if task_dir.is_dir() and task_dir.stat().st_mtime < threshold:
                import shutil
                shutil.rmtree(task_dir)
                deleted += 1
                logger.info(f"Deleted export directory: {task_dir}")
        
        return deleted
