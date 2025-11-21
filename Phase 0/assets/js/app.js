/**
 * Telecom AI Frontend Application
 * Core utility functions and UI interactions
 * 
 * Phase 0: File upload, task queuing, status polling
 * Phase 1: Analysis-specific features (forecasting, correlation, anomaly)
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_BASE_URL = "http://127.0.0.1:8000";
const POLL_INTERVAL_MS = 2000; // Check task status every 2 seconds
const MAX_FILE_SIZE_GB = 1;

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const appState = {
    currentTaskId: null,
    currentFile: null,
    selectedAgent: null,
    isPolling: false,
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
    console.log("App initialized");
    initializeEventListeners();
    checkSystemHealth();
});

function initializeEventListeners() {
    // File upload
    const fileInput = document.getElementById("file-input");
    const uploadArea = document.getElementById("upload-area");

    fileInput.addEventListener("change", handleFileSelect);
    uploadArea.addEventListener("dragover", handleDragOver);
    uploadArea.addEventListener("dragleave", handleDragLeave);
    uploadArea.addEventListener("drop", handleFileDrop);

    // Analysis buttons
    const analysisBtns = document.querySelectorAll(".analysis-options .btn");
    analysisBtns.forEach((btn) => {
        btn.addEventListener("click", handleAnalysisSelect);
    });

    // Poll button
    const pollBtn = document.getElementById("poll-button");
    if (pollBtn) {
        pollBtn.addEventListener("click", checkTaskStatus);
    }
}

// ============================================================================
// SYSTEM HEALTH CHECK
// ============================================================================

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const health = await response.json();

        const statusBadge = document.getElementById("system-status");
        if (response.ok) {
            statusBadge.textContent = "✅ System Ready";
            statusBadge.style.backgroundColor = "#2d8a8d";
        } else {
            statusBadge.textContent = "⚠️ System Initializing";
            statusBadge.style.backgroundColor = "#a84b2f";
        }

        console.log("System health:", health);
    } catch (error) {
        console.error("Health check failed:", error);
        const statusBadge = document.getElementById("system-status");
        statusBadge.textContent = "❌ API Unavailable";
        statusBadge.style.backgroundColor = "#c0152f";
    }
}

// ============================================================================
// FILE UPLOAD HANDLERS
// ============================================================================

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById("upload-area").classList.add("drag-over");
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById("upload-area").classList.remove("drag-over");
}

function handleFileDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById("upload-area").classList.remove("drag-over");

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function processFile(file) {
    // Validate file
    const allowedFormats = ["csv", "xlsx", "xls"];
    const fileExtension = file.name.split(".").pop().toLowerCase();

    if (!allowedFormats.includes(fileExtension)) {
        alert("Invalid file format. Allowed: CSV, XLSX");
        return;
    }

    const fileSizeGB = file.size / (1024 * 1024 * 1024);
    if (fileSizeGB > MAX_FILE_SIZE_GB) {
        alert(`File too large. Max: ${MAX_FILE_SIZE_GB}GB`);
        return;
    }

    // Store file
    appState.currentFile = file;

    // Update UI
    const fileInfo = document.getElementById("file-info");
    fileInfo.innerHTML = `
        <p><strong>✅ File selected:</strong> ${file.name}</p>
        <p><small>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</small></p>
    `;
    fileInfo.classList.remove("hidden");

    // Show analysis section
    document.getElementById("analysis-section").classList.remove("hidden");
}

// ============================================================================
// ANALYSIS SELECTION
// ============================================================================

function handleAnalysisSelect(event) {
    const agentId = event.currentTarget.dataset.agent;
    appState.selectedAgent = agentId;

    // Store agent ID in button for visual feedback
    const btns = document.querySelectorAll(".analysis-options .btn");
    btns.forEach((btn) => btn.style.opacity = "0.5");
    event.currentTarget.style.opacity = "1";

    // Submit analysis
    submitAnalysis(agentId);
}

// ============================================================================
// ANALYSIS SUBMISSION
// ============================================================================

async function submitAnalysis(agentId) {
    if (!appState.currentFile) {
        alert("Please select a file first");
        return;
    }

    try {
        const payload = {
            file_id: "file_" + Date.now(),
            agent_id: `${agentId}_agent_001`,
            payload: {
                filename: appState.currentFile.name,
                file_size: appState.currentFile.size,
            },
        };

        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        appState.currentTaskId = result.task_id;

        // Show status section
        document.getElementById("status-section").classList.remove("hidden");
        document.getElementById("task-id").textContent = result.task_id;

        // Start polling
        startPolling();

        console.log("Analysis submitted:", result.task_id);
    } catch (error) {
        console.error("Submit failed:", error);
        alert("Failed to submit analysis: " + error.message);
    }
}

// ============================================================================
// STATUS POLLING
// ============================================================================

function startPolling() {
    if (appState.isPolling) return;

    appState.isPolling = true;
    checkTaskStatus();
}

async function checkTaskStatus() {
    if (!appState.currentTaskId) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/status/${appState.currentTaskId}`
        );

        if (!response.ok) {
            throw new Error(`Status check failed: ${response.status}`);
        }

        const taskData = await response.json();
        updateStatusUI(taskData.status);

        // If completed, fetch results
        if (taskData.status === "completed") {
            appState.isPolling = false;
            fetchResults();
            return;
        }

        // If error, stop polling
        if (taskData.status === "error") {
            appState.isPolling = false;
            return;
        }

        // Continue polling
        if (appState.isPolling) {
            setTimeout(checkTaskStatus, POLL_INTERVAL_MS);
        }
    } catch (error) {
        console.error("Status check error:", error);
        appState.isPolling = false;
    }
}

function updateStatusUI(status) {
    const statusBadge = document.getElementById("status-badge");
    const progressFill = document.querySelector(".progress-fill");

    const statusMap = {
        pending: { text: "Pending", class: "badge-pending", progress: 25 },
        running: { text: "Running", class: "badge-running", progress: 75 },
        completed: { text: "Completed", class: "badge-completed", progress: 100 },
        error: { text: "Error", class: "badge-error", progress: 0 },
    };

    const statusInfo = statusMap[status] || statusMap.pending;

    statusBadge.textContent = statusInfo.text;
    statusBadge.className = `badge ${statusInfo.class}`;
    progressFill.style.width = `${statusInfo.progress}%`;
}

// ============================================================================
// RESULTS
// ============================================================================

async function fetchResults() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/api/result/${appState.currentTaskId}`
        );

        if (!response.ok) {
            if (response.status === 202) {
                console.log("Task still processing...");
                return;
            }
            throw new Error(`Result fetch failed: ${response.status}`);
        }

        const result = await response.json();
        displayResults(result);
    } catch (error) {
        console.error("Fetch results error:", error);
    }
}

function displayResults(result) {
    const resultsContainer = document.getElementById("results-container");
    const resultsSection = document.getElementById("results-section");

    resultsContainer.innerHTML = `
        <div class="result-item">
            <h3>Analysis Complete</h3>
            <p><strong>Status:</strong> ${result.status}</p>
            <pre>${JSON.stringify(result.output, null, 2)}</pre>
        </div>
    `;

    resultsSection.classList.remove("hidden");
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

window.addEventListener("error", (event) => {
    console.error("Unhandled error:", event.error);
});

window.addEventListener("unhandledrejection", (event) => {
    console.error("Unhandled promise rejection:", event.reason);
});
