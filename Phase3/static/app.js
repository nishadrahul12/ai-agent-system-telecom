/**
 * Telecom Anomaly Detection Dashboard - JavaScript
 * Handles all interactive features and API communication
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_BASE_URL = 'http://localhost:8000';
const POLL_INTERVAL = 1000; // 1 second
const MAX_POLL_ATTEMPTS = 300; // 5 minutes max

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

let appState = {
    currentTaskId: null,
    currentFile: null,
    currentResults: null,
    pollAttempts: 0,
    isPollActive: false
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    
    // Check API health
    checkApiHealth();
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup drag & drop
    setupDragDrop();
});

// ============================================================================
// API COMMUNICATION
// ============================================================================

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            updateApiStatus(true);
        } else {
            updateApiStatus(false);
        }
    } catch (error) {
        console.log('API not available:', error);
        updateApiStatus(false);
    }
}

async function uploadAndAnalyze() {
    if (!appState.currentFile) {
        alert('Please select a file');
        return;
    }

    const sensitivity = document.getElementById('sensitivity').value;
    const methods = Array.from(document.querySelectorAll('input[name="methods"]:checked'))
        .map(el => el.value)
        .join(',');

    if (methods.length === 0) {
        alert('Please select at least one detection method');
        return;
    }

    const formData = new FormData();
    formData.append('file', appState.currentFile);

    try {
        // Disable button & show progress
        document.getElementById('analyzeBtn').disabled = true;
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('noResults').style.display = 'none';

        // Upload file
        const response = await fetch(`${API_BASE_URL}/api/anomalies/analyze?sensitivity=${sensitivity}&methods=${methods}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Upload failed');
        }

        const result = await response.json();
        appState.currentTaskId = result.task_id;

        console.log('Task created:', appState.currentTaskId);

        // Start polling for results
        startPolling();

    } catch (error) {
        console.error('Upload error:', error);
        alert('Error: ' + error.message);
        resetUploadUI();
    }
}

async function getTaskStatus() {
    if (!appState.currentTaskId) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/api/anomalies/status/${appState.currentTaskId}`);
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Failed to get status');
    } catch (error) {
        console.error('Status fetch error:', error);
        return null;
    }
}

async function getTaskResult() {
    if (!appState.currentTaskId) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/api/anomalies/result/${appState.currentTaskId}`);
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Failed to get results');
    } catch (error) {
        console.error('Result fetch error:', error);
        return null;
    }
}

async function listAllTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/anomalies/list`);
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Failed to list tasks');
    } catch (error) {
        console.error('List tasks error:', error);
        return [];
    }
}

// ============================================================================
// POLLING LOGIC
// ============================================================================

function startPolling() {
    appState.isPollActive = true;
    appState.pollAttempts = 0;
    pollForResults();
}

async function pollForResults() {
    if (!appState.isPollActive) return;
    if (appState.pollAttempts >= MAX_POLL_ATTEMPTS) {
        alert('Analysis timeout - please try again');
        resetUploadUI();
        return;
    }

    const status = await getTaskStatus();
    if (!status) {
        setTimeout(pollForResults, POLL_INTERVAL);
        return;
    }

    // Update progress
    const progress = status.progress_percent;
    document.getElementById('progressFill').style.width = progress + '%';
    document.getElementById('progressText').textContent = progress + '%';
    document.getElementById('taskStatus').textContent = status.status;

    // Check if completed
    if (status.status === 'completed') {
        appState.isPollActive = false;
        const results = await getTaskResult();
        if (results) {
            appState.currentResults = results;
            displayResults(results);
            document.getElementById('progressSection').style.display = 'none';
        }
        return;
    }

    // Check if failed
    if (status.status === 'failed') {
        appState.isPollActive = false;
        alert('Analysis failed: ' + (status.error || 'Unknown error'));
        resetUploadUI();
        return;
    }

    // Continue polling
    appState.pollAttempts++;
    setTimeout(pollForResults, POLL_INTERVAL);
}

// ============================================================================
// RESULTS DISPLAY
// ============================================================================

function displayResults(results) {
    const { summary, anomalies, network_classification } = results;

    // Update network status
    const status = network_classification.network_status.toUpperCase();
    const statusEl = document.getElementById('statusValue');
    statusEl.textContent = status;
    statusEl.className = `status-value ${network_classification.network_status}`;

    // Update counts
    document.getElementById('criticalCount').textContent = network_classification.critical_count;
    document.getElementById('warningCount').textContent = network_classification.warning_count;
    document.getElementById('totalAnomalies').textContent = network_classification.total_anomalies;

    // Update summary stats
    document.getElementById('dataPoints').textContent = summary.data_points_analyzed.toLocaleString();
    document.getElementById('kpisAnalyzed').textContent = summary.kpis_analyzed;

    // Calculate analysis time
    const created = new Date(results.timestamp);
    const now = new Date();
    const seconds = Math.round((now - created) / 1000);
    document.getElementById('analysisTime').textContent = seconds + 's';

    // Update method counts
    for (const [method, count] of Object.entries(summary.anomalies_by_method)) {
        const methodKey = method.replace(/_/g, '_');
        const el = document.getElementById(`method-${method}`);
        if (el) el.textContent = count;
    }

    // Update top KPIs
    const topKpis = Object.entries(summary.anomalies_by_kpi)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    const topKpisHtml = topKpis.map(([kpi, count]) => `
        <div class="kpi-item">
            <span class="kpi-name">${kpi}</span>
            <span class="kpi-count">${count} anomalies</span>
        </div>
    `).join('');

    document.getElementById('topKpis').innerHTML = topKpisHtml || '<p>No data</p>';

    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
    initializeCharts();
    document.getElementById('noResults').style.display = 'none';
}

// ============================================================================
// MODAL FUNCTIONALITY
// ============================================================================

function openAnomaliesModal() {
    if (!appState.currentResults) return;

    const anomalies = appState.currentResults.anomalies;
    const tbody = document.getElementById('anomaliesBody');

    tbody.innerHTML = anomalies.map(a => `
        <tr>
            <td>${a.kpi}</td>
            <td>${a.value.toFixed(2)}</td>
            <td>${a.normalized_value.toFixed(2)}</td>
            <td><span class="severity-${a.severity.toLowerCase()}">${a.severity}</span></td>
            <td>${a.method}</td>
            <td>${a.anomaly_score.toFixed(2)}</td>
        </tr>
    `).join('');

    document.getElementById('anomaliesModal').style.display = 'flex';
}

function closeAnomaliesModal() {
    document.getElementById('anomaliesModal').style.display = 'none';
}

async function openHistoryModal() {
    const tasks = await listAllTasks();
    const historyHtml = tasks.map(task => `
        <div class="task-item">
            <div class="task-item-header">
                <span class="task-item-name">${task.filename}</span>
                <span class="task-item-status">${task.status}</span>
            </div>
            <div class="task-item-meta">
                <p>Task ID: ${task.task_id}</p>
                <p>Created: ${new Date(task.created_at).toLocaleString()}</p>
            </div>
        </div>
    `).join('');

    document.getElementById('taskHistoryList').innerHTML = historyHtml || '<p>No tasks found</p>';
    document.getElementById('historyModal').style.display = 'flex';
}

function closeHistoryModal() {
    document.getElementById('historyModal').style.display = 'none';
}

// ============================================================================
// FILE HANDLING
// ============================================================================

function setupDragDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFileSelect(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });
}

function handleFileSelect(file) {
    if (!file) return;

    // Validate file
    const validFormats = ['csv', 'xlsx'];
    const ext = file.name.split('.').pop().toLowerCase();
    
    if (!validFormats.includes(ext)) {
        alert('Invalid file format. Please use CSV or XLSX.');
        return;
    }

    if (file.size > 5 * 1024 * 1024 * 1024) { // 5GB
        alert('File too large. Maximum size is 5GB.');
        return;
    }

    appState.currentFile = file;

    // Update UI
    document.getElementById('uploadArea').style.display = 'none';
    document.getElementById('fileInfo').style.display = 'block';
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('analyzeBtn').disabled = false;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// ============================================================================
// UI UPDATES
// ============================================================================

function updateApiStatus(isOnline) {
    const dot = document.getElementById('api-status');
    const text = document.getElementById('api-status-text');
    const footer = document.getElementById('footerApiStatus');

    if (isOnline) {
        dot.classList.remove('offline');
        text.textContent = 'API Online';
        footer.textContent = 'Online';
    } else {
        dot.classList.add('offline');
        text.textContent = 'API Offline';
        footer.textContent = 'Offline';
    }
}

function resetUploadUI() {
    document.getElementById('analyzeBtn').disabled = true;
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('fileInfo').style.display = 'none';
    appState.currentFile = null;
    appState.currentTaskId = null;
    appState.isPollActive = false;
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // Upload
    document.getElementById('analyzeBtn').addEventListener('click', uploadAndAnalyze);
    
    // Results
    document.getElementById('viewDetailsBtn').addEventListener('click', openAnomaliesModal);
    document.getElementById('downloadBtn').addEventListener('click', downloadResults);
    document.getElementById('newAnalysisBtn').addEventListener('click', resetUploadUI);
    
    // Modals
    document.getElementById('closeModal').addEventListener('click', closeAnomaliesModal);
    document.getElementById('closeHistory').addEventListener('click', closeHistoryModal);
    document.getElementById('historyBtn').addEventListener('click', openHistoryModal);

    // Export & Reporting
    document.getElementById('downloadBtn').addEventListener('click', openExportModal);
    document.getElementById('closeExport').addEventListener('click', closeExportModal);
    document.getElementById('exportCsvBtn').addEventListener('click', exportToCsv);
    document.getElementById('exportJsonBtn').addEventListener('click', exportToJson);
    document.getElementById('exportPdfBtn').addEventListener('click', exportToPdf);
    document.getElementById('sendEmailBtn').addEventListener('click', sendEmailReport);

    
    // Close modals on outside click
    window.addEventListener('click', (e) => {
        if (e.target === document.getElementById('anomaliesModal')) {
            closeAnomaliesModal();
        }
        if (e.target === document.getElementById('historyModal')) {
            closeHistoryModal();
        }
    });
}

// ============================================================================
// EXPORT FUNCTIONALITY
// ============================================================================

function downloadResults() {
    // Open export modal instead of auto-downloading
    openExportModal();
}

// ============================================================================
// EXPORT & REPORTING FUNCTIONS
// ============================================================================

function openExportModal() {
    if (!appState.currentResults) return;
    document.getElementById('exportModal').style.display = 'flex';
}

function closeExportModal() {
    document.getElementById('exportModal').style.display = 'none';
    document.getElementById('exportStatus').style.display = 'none';
}

function exportToCsv() {
    if (!appState.currentResults) return;
    
    const results = appState.currentResults;
    const anomalies = results.anomalies;
    
    if (!anomalies || anomalies.length === 0) {
        showExportStatus('❌ No anomalies to export', true);
        return;
    }
    
    // Create CSV header from first anomaly
    const headers = Object.keys(anomalies[0]);
    
    // Create CSV rows
    const csvRows = [
        headers.join(','),
        ...anomalies.map(row => 
            headers.map(header => {
                const value = row[header];
                // Escape quotes and wrap in quotes if contains comma
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return '"' + value.replace(/"/g, '""') + '"';
                }
                return value;
            }).join(',')
        )
    ];
    
    const csvContent = csvRows.join('\n');
    
    console.log('CSV Export - Total rows:', anomalies.length);
    console.log('CSV Export - Sample:', csvRows.slice(0, 3).join('\n'));
    
    downloadFile(csvContent, `anomalies_${results.task_id}.csv`, 'text/csv;charset=utf-8;');
    showExportStatus(`✅ CSV exported successfully! (${anomalies.length} anomalies)`, false);
}


function exportToJson() {
    if (!appState.currentResults) return;
    
    const results = appState.currentResults;
    const json = JSON.stringify(results, null, 2);
    
    downloadFile(json, `analysis_${results.task_id}.json`, 'application/json');
    showExportStatus('✅ JSON exported successfully!', false);
}

function exportToPdf() {
    if (!appState.currentResults) return;
    
    const results = appState.currentResults;
    
    // Call backend API to generate PDF
    fetch(`/api/anomalies/export/${results.task_id}/pdf`)
        .then(response => {
            if (!response.ok) throw new Error('PDF generation failed');
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `report_${results.task_id}.pdf`;
            link.click();
            URL.revokeObjectURL(url);
            showExportStatus('✅ PDF generated and downloaded!', false);
        })
        .catch(error => {
            console.error('PDF error:', error);
            showExportStatus('❌ PDF generation failed. Try JSON or CSV instead.', true);
        });
}


function sendEmailReport() {
    const email = document.getElementById('emailRecipient').value;
    
    if (!email || !email.includes('@')) {
        showExportStatus('❌ Please enter a valid email address', true);
        return;
    }
    
    alert('📧 Email feature will be available with backend integration. For now, download and share the report manually.');
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type: type });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    
    URL.revokeObjectURL(url);
}

function showExportStatus(message, isError = false) {
    const statusEl = document.getElementById('exportStatus');
    const textEl = document.getElementById('exportStatusText');
    
    statusEl.style.display = 'block';
    statusEl.className = 'export-status' + (isError ? ' error' : '');
    textEl.textContent = message;
    
    if (!isError) {
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 3000);
    }
}

// Close modal on outside click
window.addEventListener('click', (e) => {
    if (e.target === document.getElementById('exportModal')) {
        closeExportModal();
    }
});


// ============================================================================
// UTILITIES
// ============================================================================

console.log('Dashboard script loaded successfully');


