"""
reporting_engine.py - Phase 3 Reporting Engine
Generates and manages reports with email delivery
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

logger = logging.getLogger(__name__)


class ReportingEngine:
    """Engine for generating and sending reports."""
    
    def __init__(self):
        """Initialize reporting engine."""
        self.report_history = []
        logger.info("ReportingEngine initialized")
    
    # ========================================================================
    # REPORT GENERATION
    # ========================================================================
    
    def generate_html_report(self, task_id: str, results: Dict) -> str:
        """
        Generate an HTML report from analysis results.
        
        Args:
            task_id (str): Task ID
            results (Dict): Analysis results
            
        Returns:
            str: HTML report content
        """
        summary = results.get('summary', {})
        network_class = results.get('network_classification', {})
        status = network_class.get('network_status', 'UNKNOWN').upper()
        
        # Determine color based on status
        status_color = {
            'CRITICAL': '#D32F2F',
            'WARNING': '#F57C00',
            'NORMAL': '#388E3C'
        }.get(status, '#999999')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #2196F3, #1976D2);
                    color: white;
                    padding: 30px;
                    border-radius: 8px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .status-box {{
                    background-color: {status_color};
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 20px 0;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .section {{
                    background: white;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .section h2 {{
                    color: #1976D2;
                    border-bottom: 2px solid #2196F3;
                    padding-bottom: 10px;
                    margin-top: 0;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 15px;
                }}
                .stat-card {{
                    background: #f9f9f9;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #2196F3;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #1976D2;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 15px;
                }}
                th {{
                    background-color: #2196F3;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px 12px;
                    border-bottom: 1px solid #eee;
                }}
                tr:hover {{
                    background-color: #f9f9f9;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #999;
                    margin-top: 30px;
                }}
                .critical {{ color: #D32F2F; font-weight: bold; }}
                .warning {{ color: #F57C00; font-weight: bold; }}
                .normal {{ color: #388E3C; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Telecom Anomaly Detection Report</h1>
                <p>Real-time Network Analysis Results</p>
            </div>
            
            <div class="status-box">{status}</div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Anomalies</div>
                        <div class="stat-value">{network_class.get('total_anomalies', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Critical</div>
                        <div class="stat-value critical">{network_class.get('critical_count', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Warning</div>
                        <div class="stat-value warning">{network_class.get('warning_count', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Data Points</div>
                        <div class="stat-value">{summary.get('data_points_analyzed', 0)}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Analysis Details</h2>
                <table>
                    <tr>
                        <td><strong>Analysis Timestamp:</strong></td>
                        <td>{results.get('timestamp', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td><strong>Sensitivity Level:</strong></td>
                        <td>{summary.get('sensitivity', 'N/A').title()}</td>
                    </tr>
                    <tr>
                        <td><strong>KPIs Analyzed:</strong></td>
                        <td>{summary.get('kpis_analyzed', 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Detection Methods:</strong></td>
                        <td>{', '.join(summary.get('methods_used', []))}</td>
                    </tr>
                    <tr>
                        <td><strong>Task ID:</strong></td>
                        <td>{results.get('task_id', 'N/A')}</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Anomalies by Detection Method</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Method</th>
                            <th>Anomalies Detected</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add method data
        for method, count in summary.get('anomalies_by_method', {}).items():
            html += f"""
                        <tr>
                            <td>{method.replace('_', ' ').title()}</td>
                            <td>{count}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>Top 10 Affected KPIs</h2>
                <table>
                    <thead>
                        <tr>
                            <th>KPI Name</th>
                            <th>Anomalies Count</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add top KPIs
        anomalies_by_kpi = summary.get('anomalies_by_kpi', {})
        top_kpis = sorted(anomalies_by_kpi.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for kpi, count in top_kpis:
            html += f"""
                        <tr>
                            <td>{kpi}</td>
                            <td>{count}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                <p>Telecom Anomaly Detection System - Phase 3</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    # ========================================================================
    # EMAIL SENDING
    # ========================================================================
    
    def send_email_report(
        self,
        to_email: str,
        task_id: str,
        results: Dict,
        subject: Optional[str] = None,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        from_email: Optional[str] = None,
        password: Optional[str] = None
    ) -> bool:
        """
        Send analysis report via email.
        
        Args:
            to_email (str): Recipient email
            task_id (str): Task ID
            results (Dict): Analysis results
            subject (Optional[str]): Email subject
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP port
            from_email (Optional[str]): Sender email
            password (Optional[str]): Sender password
            
        Returns:
            bool: Success status
        """
        try:
            if not from_email or not password:
                logger.warning("Email credentials not provided - skipping send")
                return False
            
            # Generate HTML report
            html_content = self.generate_html_report(task_id, results)
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject or f"Anomaly Detection Report - {task_id}"
            msg['From'] = from_email
            msg['To'] = to_email
            
            # Attach HTML
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send via SMTP
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(from_email, password)
                server.send_message(msg)
            
            logger.info(f"Email report sent to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"Email send failed: {str(e)}")
            return False
    
    # ========================================================================
    # REPORT SUMMARY
    # ========================================================================
    
    def generate_summary(self, results: Dict) -> Dict:
        """
        Generate a concise summary of analysis results.
        
        Args:
            results (Dict): Analysis results
            
        Returns:
            Dict: Summary information
        """
        summary = results.get('summary', {})
        network_class = results.get('network_classification', {})
        
        return {
            'task_id': results.get('task_id'),
            'timestamp': results.get('timestamp'),
            'network_status': network_class.get('network_status'),
            'total_anomalies': network_class.get('total_anomalies', 0),
            'critical_count': network_class.get('critical_count', 0),
            'warning_count': network_class.get('warning_count', 0),
            'data_points': summary.get('data_points_analyzed', 0),
            'kpis_count': summary.get('kpis_analyzed', 0),
            'sensitivity': summary.get('sensitivity'),
            'methods_used': summary.get('methods_used', []),
            'top_kpis': sorted(
                summary.get('anomalies_by_kpi', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
