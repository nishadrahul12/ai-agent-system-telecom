/**
 * Telecom AI Frontend Application
 * Phase 0 + Phase 1 + Phase 2 Integration
 *
 * Core functionality:
 * - File upload & management
 * - Tab navigation
 * - Phase 1: Correlation analysis
 * - Phase 2: Time-series forecasting (NEW)
 * - Phase 2.5: KPI selection (NEW)
 */

// ============================================================================
// CONFIGURATION
// ============================================================================
const API_BASE_URL = "http://127.0.0.1:8000";
const POLL_INTERVAL_MS = 2000;
const MAX_FILE_SIZE_GB = 1;

// ============================================================================
// STATE MANAGEMENT
// ============================================================================
const appState = {
    currentTaskId: null,
    currentFile: null,
    selectedAgent: null,
    isPolling: false,
    currentAnalysis: null,
    availableKPIs: [],           // NEW: Store list of KPI names
    selectedKPI: null            // NEW: Track selected KPI
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {
    initializeUI();
    setupEventListeners();
});

function initializeUI() {
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    // File upload
    const uploadArea = document.getElementById('upload-area');
    let isProcessing = false;
    uploadArea.addEventListener('click', () => {
        if (!isProcessing) {  
            isProcessing = true;  
            document.getElementById('file-input').click();
            setTimeout(() => { isProcessing = false; }, 500);  
        }  
    });
    uploadArea.addEventListener('dragover', e => e.preventDefault());
    uploadArea.addEventListener('drop', handleFileDrop);
    document.getElementById('file-input').addEventListener('change', handleFileSelect);
}

function setupEventListeners() {
    // Event listeners already set up in HTML onclick attributes
    // This function reserved for additional listeners
}

// ============================================================================
// TAB MANAGEMENT
// ============================================================================
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });

    // Hide all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Highlight selected button
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    appState.currentAnalysis = tabId;
}

// ============================================================================
// FILE UPLOAD HANDLERS
// ============================================================================
function handleFileDrop(e) {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    console.log('handleFileSelect called, file count:', e.target.files.length);
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    console.log('handleFile called with:', file.name);
    const maxSize = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
        alert(`File too large! Max size: ${MAX_FILE_SIZE_GB}GB`);
        return;
    }
    if (!['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(file.type)) {
        alert('Please upload CSV or XLSX file');
        return;
    }

    appState.currentFile = file;
    document.getElementById('file-info').textContent = `✓ File: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
    document.getElementById('file-info').classList.remove('hidden');
    
    // NEW: Fetch available KPIs from the uploaded file
    getAvailableKPIs(file);
}

// ============================================================================
// NEW: GET AVAILABLE KPI COLUMNS (Phase 2.5)
// ============================================================================
/**
 * Fetch available KPI column names from the file
 * Used to populate the KPI selection dropdown
 */
async function getAvailableKPIs(fileData) {
    try {
        const formData = new FormData();
        formData.append('file', fileData);
        
        const response = await fetch(`${API_BASE_URL}/api/get-kpi-columns`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            appState.availableKPIs = result.kpi_columns || [];
            populateKPIDropdown();
            console.log('Available KPIs:', appState.availableKPIs);
        } else {
            console.error('Failed to get KPIs:', result.error);
        }
    } catch (error) {
        console.error('Error fetching KPIs:', error);
    }
}

/**
 * Populate the KPI selection dropdown with available columns
 */
function populateKPIDropdown() {
    const kpiSelect = document.getElementById('kpi-select');
    
    if (!kpiSelect) {
        console.warn('KPI select element not found');
        return;
    }
    
    // Clear existing options
    kpiSelect.innerHTML = '<option value="">-- Auto-select first KPI --</option>';
    
    // Add options for each available KPI
    appState.availableKPIs.forEach(kpi => {
        const option = document.createElement('option');
        option.value = kpi;
        option.textContent = kpi;
        kpiSelect.appendChild(option);
    });
    
    console.log('KPI dropdown populated with', appState.availableKPIs.length, 'options');
}

// ============================================================================
// PHASE 1: CORRELATION ANALYSIS
// ============================================================================
async function runCorrelationAnalysis() {
    if (!appState.currentFile) {
        alert('Please upload a file first');
        return;
    }

    const formData = new FormData();
    formData.append('file', appState.currentFile);

    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        appState.currentTaskId = result.task_id;
        displayResults(result, 'correlation');
    } catch (error) {
        console.error('Correlation analysis error:', error);
        alert('Correlation analysis failed');
    }
}

// ============================================================================
// PHASE 2: TIME-SERIES FORECASTING (NEW)
// ============================================================================
/**
 * Run time-series forecasting using Phase 2 forecasting agent
 * Supports: ARIMA, LSTM, Exponential Smoothing
 * Phase 2.5: Now supports KPI selection!
 */
async function runForecasting() {
    // Validation
    if (!appState.currentFile) {
        alert('Please upload a file first');
        return;
    }

    // Get form values
    const model = document.getElementById('forecast-model').value;
    const periods = document.getElementById('forecast-periods').value;
    const kpiName = document.getElementById('kpi-select').value;  // NEW: Get selected KPI
    
    // Prepare request
    const formData = new FormData();
    formData.append('file', appState.currentFile);
    formData.append('model', model);
    formData.append('periods', parseInt(periods));
    formData.append('kpi_name', kpiName);  // NEW: Send selected KPI to backend

    try {
        // Show loading state
        document.getElementById('forecast-results').innerHTML = '<p>⏳ Running forecast...</p>';

        // Call Phase 2 API endpoint
        const response = await fetch(`${API_BASE_URL}/api/forecast`, {
            method: 'POST',
            body: formData
        });

        // DEBUG: Log response
        console.log('API Response Status:', response.status);
        console.log('API Response OK:', response.ok);

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        // Get response text first to debug
        const responseText = await response.text();
        console.log('API Response Text:', responseText);

        if (!responseText) {
            throw new Error('Empty response from API');
        }

        // Parse JSON
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (parseError) {
            console.error('JSON Parse Error:', parseError);
            throw new Error(`Invalid JSON response: ${responseText}`);
        }

        console.log('Parsed Result:', result);

        // Check for errors
        if (!result) {
            throw new Error('Result is null or undefined');
        }

        if (result.status === 'error') {
            displayForecastError(result);
        } else if (result.status === 'success') {
            displayForecastResults(result);
        } else {
            throw new Error(`Unknown status: ${result.status}`);
        }

    } catch (error) {
        console.error('Forecasting error:', error);
        document.getElementById('forecast-results').innerHTML = `<p>❌ Forecasting failed: ${error.message}</p>`;
    }
}

/**
 * Display successful forecast results
 */
function displayForecastResults(result) {
    if (!result.result) {
        console.error('Invalid result structure:', result);
        return;
    }

    const forecast = result.result.forecast || [];
    const trend = result.result.trend || {};
    const metrics = result.result.metrics || {};
    const ci = result.result.confidence_intervals || {};
    const modelUsed = result.model_used || 'Unknown Model';

    let html = `
        <h3>📊 Forecast Results</h3>
        <p><strong>🤖 Model Used:</strong> ${modelUsed}</p>
        <h4>Forecast Values (Next ${forecast.length} periods)</h4>
        <p>${forecast.map(v => v.toFixed(2)).join(', ')}</p>
        
        <h4>📈 Trend Analysis</h4>
        <p><strong>Direction:</strong> ${trend.direction || 'N/A'}</p>
        <p><strong>Slope:</strong> ${trend.slope ? trend.slope.toFixed(4) : 'N/A'}</p>
        <p><strong>Strength (R²):</strong> ${trend.strength ? (trend.strength * 100).toFixed(2) : 'N/A'}%</p>
        
        <h4>📋 Performance Metrics</h4>
        <p><strong>MAE:</strong> ${metrics.mae ? metrics.mae.toFixed(4) : 'N/A'}</p>
        <p><strong>RMSE:</strong> ${metrics.rmse ? metrics.rmse.toFixed(4) : 'N/A'}</p>
        <p><strong>MAPE:</strong> ${metrics.mape ? metrics.mape.toFixed(2) : 'N/A'}%</p>
        
        <h4>📊 Confidence Intervals (95%)</h4>
        <p><strong>Lower:</strong> ${ci.lower ? ci.lower.map(v => v.toFixed(2)).join(', ') : 'N/A'}</p>
        <p><strong>Upper:</strong> ${ci.upper ? ci.upper.map(v => v.toFixed(2)).join(', ') : 'N/A'}</p>
    `;

    document.getElementById('forecast-results').innerHTML = html;
}

/**
 * Display forecast error
 */
function displayForecastError(result) {
    let html = `
        <h3>❌ Forecasting Error</h3>
        <p><strong>Error:</strong> ${result.error}</p>
        <p><strong>Details:</strong> ${result.details || 'No additional details'}</p>
    `;

    document.getElementById('forecast-results').innerHTML = html;
}

// ============================================================================
// DISPLAY HELPERS
// ============================================================================
function displayResults(result, type) {
    // Generic result display handler
    console.log(`Results for ${type}:`, result);
    const resultsDiv = document.getElementById('correlation-results') || document.getElementById('forecast-results');
    if (resultsDiv) {
        resultsDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    }
}
