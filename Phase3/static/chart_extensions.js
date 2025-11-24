// chart_extensions.js - Phase 3 Chart & Analytics Integration (FIXED)
// Handles chart rendering, tab switching, and insights display

// Store chart instances
const chartInstances = {};

// ============================================================================
// SHOW CHARTS SECTION
// ============================================================================

function showChartsSection() {
    const chartsSection = document.getElementById('chartsSection');
    if (chartsSection) {
        chartsSection.style.display = 'block';
        loadAllCharts();
    }
}

// ============================================================================
// LOAD CHARTS FROM API
// ============================================================================

async function loadAllCharts() {
    if (!appState.currentResults) return;
    
    const taskId = appState.currentResults.task_id;
    
    try {
        // Load chart data
        console.log('Loading chart data for task:', taskId);
        const chartResponse = await fetch(`/api/anomalies/charts/${taskId}`);
        if (!chartResponse.ok) throw new Error('Failed to load chart data');
        const chartData = await chartResponse.json();
        
        // Load trend data
        const trendResponse = await fetch(`/api/anomalies/trends/${taskId}`);
        if (!trendResponse.ok) throw new Error('Failed to load trend data');
        const trendData = await trendResponse.json();
        
        // Render all visualizations
        renderSeverityChart(chartData.severity_distribution);
        renderMethodChart(chartData.method_distribution);
        renderTopKpisChart(chartData.top_kpis);
        renderTrendsChart(chartData.trends);
        renderHealthScore(chartData.health_score);
        
        // Display insights
        displayTrendAnalysis(trendData);
        displayRecommendations(trendData.recommendations);
        
        console.log('✅ All charts loaded successfully');
    } catch (error) {
        console.error('Chart loading error:', error);
        showExportStatus('⚠️ Error loading charts: ' + error.message, true);
    }
}

// ============================================================================
// CHART RENDERING FUNCTIONS
// ============================================================================

function renderSeverityChart(data) {
    const ctx = document.getElementById('severityChart');
    if (!ctx) {
        console.warn('Chart element not found: severityChart');
        return;
    }
    
    // Destroy existing chart if it exists
    if (chartInstances.severity) {
        chartInstances.severity.destroy();
    }
    
    chartInstances.severity = new Chart(ctx, {
        type: data.type,
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: data.colors,
                borderColor: '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function renderMethodChart(data) {
    const ctx = document.getElementById('methodChart');
    if (!ctx) {
        console.warn('Chart element not found: methodChart');
        return;
    }
    
    if (chartInstances.method) {
        chartInstances.method.destroy();
    }
    
    chartInstances.method = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Anomalies Detected',
                data: data.data,
                backgroundColor: data.backgroundColor,
                borderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderTopKpisChart(data) {
    const ctx = document.getElementById('topKpisChart');
    if (!ctx) {
        console.warn('Chart element not found: topKpisChart');
        return;
    }
    
    if (chartInstances.topKpis) {
        chartInstances.topKpis.destroy();
    }
    
    chartInstances.topKpis = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Anomalies',
                data: data.data,
                backgroundColor: data.backgroundColor,
                borderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderTrendsChart(data) {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) {
        console.warn('Chart element not found: trendsChart');
        return;
    }
    
    if (chartInstances.trends) {
        chartInstances.trends.destroy();
    }
    
    chartInstances.trends = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Anomalies Over Time',
                data: data.data,
                borderColor: data.borderColor,
                backgroundColor: data.backgroundColor,
                tension: data.tension,
                fill: true,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderHealthScore(data) {
    const scoreEl = document.getElementById('healthScore');
    const statusEl = document.getElementById('healthStatus');
    
    if (scoreEl) {
        scoreEl.textContent = data.score;
        scoreEl.style.color = data.color;
    }
    
    if (statusEl) {
        statusEl.textContent = data.status;
        statusEl.style.color = data.color;
    }
}

// ============================================================================
// TAB SWITCHING
// ============================================================================

function setupTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Hide all tabs
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                selectedTab.classList.add('active');
                button.classList.add('active');
            }
            
            console.log('Switched to tab:', tabName);
        });
    });
}

// ============================================================================
// DISPLAY INSIGHTS & TRENDS
// ============================================================================

function displayTrendAnalysis(trendData) {
    const container = document.getElementById('trendAnalysisContent');
    if (!container) return;
    
    const trends = trendData.trends || {};
    const severity = trendData.severity_insights || {};
    const kpi = trendData.kpi_insights || {};
    
    let html = `
        <div class="insight-item">
            <h4>📊 Overall Trend Analysis</h4>
            <p><strong>Total Anomalies:</strong> ${trends.total_anomalies || 0}</p>
            <p><strong>Severity Distribution:</strong></p>
            <ul>
                <li>Critical: ${(trends.severity_distribution?.critical_percentage || 0)}%</li>
                <li>Warning: ${(trends.severity_distribution?.warning_percentage || 0)}%</li>
                <li>Normal: ${(trends.severity_distribution?.normal_percentage || 0)}%</li>
            </ul>
        </div>
        
        <div class="insight-item">
            <h4>📈 Severity Insights</h4>
            <p><strong>Risk Level:</strong> <span style="font-weight: bold; color: 
                ${severity.risk_level === 'CRITICAL' ? '#d32f2f' :
                  severity.risk_level === 'HIGH' ? '#f57c00' :
                  severity.risk_level === 'MEDIUM' ? '#ff9800' : '#388e3c'}">
                ${severity.risk_level || 'UNKNOWN'}</span></p>
            <p><strong>Critical Count:</strong> ${severity.critical?.count || 0} (${severity.critical?.percentage || 0}%)</p>
            <p><strong>Warning Count:</strong> ${severity.warning?.count || 0} (${severity.warning?.percentage || 0}%)</p>
        </div>
        
        <div class="insight-item">
            <h4>🎯 Top Affected KPIs</h4>
            <ul>
    `;
    
    if (kpi.most_affected && kpi.most_affected.length > 0) {
        kpi.most_affected.forEach(item => {
            html += `<li>${item.kpi}: ${item.anomalies} anomalies</li>`;
        });
    }
    
    html += `
            </ul>
            <p><strong>Average Anomalies per KPI:</strong> ${kpi.average_anomalies_per_kpi || 0}</p>
        </div>
    `;
    
    container.innerHTML = html;
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendationsContainer');
    if (!container || !recommendations || recommendations.length === 0) return;
    
    let html = '';
    
    recommendations.forEach(rec => {
        let className = 'recommendation-item';
        
        if (rec.includes('CRITICAL') || rec.includes('⚠️ CRITICAL')) {
            className += ' critical';
        } else if (rec.includes('HIGH') || rec.includes('⚠️ HIGH')) {
            className += ' warning';
        }
        
        html += `<div class="${className}">${rec}</div>`;
    });
    
    container.innerHTML = html;
}

// ============================================================================
// INITIALIZE
// ============================================================================

function initializeCharts() {
    console.log('✅ Initializing charts...');
    setupTabSwitching();
    showChartsSection();
}

// Make functions available globally
window.initializeCharts = initializeCharts;
window.showChartsSection = showChartsSection;

console.log('✅ chart_extensions.js loaded successfully');
