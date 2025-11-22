# Phase 1: Telecom AI Multi-Agent System - Deployment Guide

## Overview

This guide provides instructions for deploying the Phase 1 REST API system for correlation analysis of telecommunications KPI data.

**System Components:**
- CorrelationAgent: ML models for statistical analysis
- Orchestrator: Task management and agent coordination
- REST API: 5 endpoints for file upload and analysis
- File Storage: Secure CSV/Excel upload handling

**Status:** Production Ready ✓

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

**System Requirements:**
- Python 3.12+
- Windows 10+ / Linux / macOS
- 2GB RAM minimum
- 500MB disk space for data

**Dependencies:**
- FastAPI: REST framework
- Pydantic: Data validation
- SQLite: Data storage
- scikit-learn: ML models
- pandas: Data processing

---

## Installation

### Step 1: Clone Repository

git clone https://github.com/yourusername/AI-AGENT-SYSTEM-TELECOM.git
cd AI-AGENT-SYSTEM-TELECOM

text

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
python -m venv venv
.\venv\Scripts\Activate.ps1

text

**Linux/macOS:**
python -m venv venv
source venv/bin/activate

text

### Step 3: Install Dependencies

pip install -r requirements.txt

text

### Step 4: Verify Installation

python -m pytest Phase1/api/tests/ -v

Should show: 44 passed
text

---

## Configuration

### Environment Variables

Create `.env` file in project root:

Debug mode
PHASE1_DEBUG=False

File upload settings
PHASE1_UPLOAD_DIR=data/uploads
PHASE1_MAX_FILE_SIZE_MB=100
PHASE1_ALLOWED_EXTENSIONS=csv,xlsx

Server settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

text

### Configuration File

**Location:** `Phase1/config.py`

Key settings:
Config.DEBUG = False # Production mode
Config.MAX_FILE_SIZE_BYTES = 104857600 # 100MB
Config.ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
Config.TASK_TIMEOUT_SECONDS = 300 # 5 minutes

text

---

## Running the System

### Step 1: Start Orchestrator

The orchestrator manages all agents and tasks.

python Phase0/orchestrator.py

text

**Expected output:**
2025-11-22 17:00:00 - INFO - Orchestrator initialized
2025-11-22 17:00:01 - INFO - CorrelationAgent registered
2025-11-22 17:00:02 - INFO - Server running on http://localhost:8000

text

### Step 2: Verify Server Status

**Health Check:**
curl http://localhost:8000/api/health/detailed

text

**Expected response:**
{
"status": "healthy",
"components": {
"orchestrator": "operational",
"upload_handler": "operational",
"analysis_endpoint": "operational",
"result_formatter": "operational"
}
}

text

### Step 3: Access API Documentation

**Swagger UI:**
http://localhost:8000/api/docs

text

**OpenAPI JSON:**
http://localhost:8000/api/openapi.json

text

---

## API Endpoints

### 1. Upload File

**Endpoint:** `POST /api/correlation/upload`

**Request:**
curl -X POST http://localhost:8000/api/correlation/upload
-F "file=@telecom_data.csv"

text

**Response:**
{
"file_id": "550e8400-e29b-41d4-a716-446655440000",
"filename": "telecom_data.csv",
"size_bytes": 1024,
"uploaded_at": "2025-11-22T17:05:00Z"
}

text

### 2. Queue Analysis

**Endpoint:** `POST /api/correlation/analyze`

**Request:**
curl -X POST http://localhost:8000/api/correlation/analyze
-H "Content-Type: application/json"
-d '{
"file_id": "550e8400-e29b-41d4-a716-446655440000",
"target_variable": "drop_rate",
"correlation_method": "pearson",
"test_size": 0.2
}'

text

**Response:**
{
"task_id": "task_123abc",
"status": "queued",
"message": "Analysis task queued successfully",
"queued_at": "2025-11-22T17:05:30Z"
}

text

### 3. Check Status

**Endpoint:** `GET /api/correlation/status/{task_id}`

**Request:**
curl http://localhost:8000/api/correlation/status/task_123abc

text

**Response:**
{
"task_id": "task_123abc",
"status": "processing",
"progress_percent": 65,
"message": "Processing correlation analysis (65%)"
}

text

### 4. Get Results

**Endpoint:** `GET /api/correlation/result/{task_id}`

**Request:**
curl http://localhost:8000/api/correlation/result/task_123abc

text

**Response:**
{
"task_id": "task_123abc",
"status": "completed",
"file_id": "550e8400-e29b-41d4-a716-446655440000",
"target_variable": "drop_rate",
"correlation_matrix": {
"traffic": 0.85,
"prb_util": 0.72,
"latency": 0.91
},
"model_performance": {
"model_type": "GradientBoosting",
"r2_score": 0.89,
"rmse": 0.15,
"mae": 0.12
},
"p_values": {
"traffic": 0.001,
"prb_util": 0.05,
"latency": 0.0001
},
"completed_at": "2025-11-22T17:06:30Z",
"processing_time_seconds": 90.5
}

text

### 5. Health Check

**Endpoint:** `GET /api/health/detailed`

Returns detailed system status.

---

## Testing

### Unit Tests

Run all unit tests
python -m pytest Phase1/ -v

Run specific test file
python -m pytest Phase1/api/tests/test_upload_handler.py -v

Run with coverage
python -m pytest Phase1/ --cov=Phase1 --cov-report=html

text

### E2E Tests

Run end-to-end workflow tests
python -m pytest Phase1/api/tests/test_e2e_workflow.py -v -s

text

### Manual Testing (curl)

**Complete workflow:**
1. Upload
FILE_ID=$(curl -s -X POST http://localhost:8000/api/correlation/upload
-F "file=@data.csv" | jq -r '.file_id')

2. Queue analysis
TASK_ID=$(curl -s -X POST http://localhost:8000/api/correlation/analyze
-H "Content-Type: application/json"
-d "{"file_id": "$FILE_ID", "target_variable": "drop_rate"}"
| jq -r '.task_id')

3. Check status (repeat)
curl http://localhost:8000/api/correlation/status/$TASK_ID

4. Get results
curl http://localhost:8000/api/correlation/result/$TASK_ID

text

---

## Monitoring

### Log Files

**Location:** `logs/phase1_api.log`

**Log levels:**
- DEBUG: Detailed operational info
- INFO: General information
- WARNING: Warning messages
- ERROR: Error conditions

**View logs:**
tail -f logs/phase1_api.log

text

### Task Summary

curl http://localhost:8000/api/health/detailed | jq '.tasks'

text

### Performance Metrics

Monitor in logs:
- File upload time
- Analysis processing time
- Result formatting time
- Error rates

---

## Troubleshooting

### Issue: "Port 8000 already in use"

**Solution:**
Find process using port 8000
netstat -ano | findstr :8000

Kill process (Windows)
taskkill /PID <process_id> /F

Or use different port
python api_server.py --port 8001

text

### Issue: "File validation error"

**Causes:**
- Unsupported file format (use CSV or Excel only)
- File too large (max 100MB)
- File is empty

**Solution:**
Verify file format
file telecom_data.csv

Check file size
ls -lh telecom_data.csv

Preview content
head telecom_data.csv

text

### Issue: "Task timeout"

**Cause:** Analysis took >300 seconds

**Solution:**
- Try with smaller file
- Increase timeout in `Phase1/config.py`
- Check system resources

### Issue: "Storage error"

**Cause:** Disk space or permissions issue

**Solution:**
Check disk space
df -h

Verify data directory permissions
ls -la data/uploads/

Create missing directories
mkdir -p data/uploads logs

text

---

## Production Deployment

### Security Checklist

- [ ] Set `PHASE1_DEBUG=False`
- [ ] Use HTTPS (add SSL certificate)
- [ ] Implement authentication (JWT tokens)
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Enable logging and monitoring
- [ ] Regular backups of analysis results

### Performance Optimization

- [ ] Use production ASGI server (Gunicorn + Uvicorn)
- [ ] Enable caching for repeated analyses
- [ ] Use database connection pooling
- [ ] Implement request queuing
- [ ] Monitor and optimize ML model inference

### Deployment Platforms

**Docker:**
docker build -t telecom-api .
docker run -p 8000:8000 telecom-api

text

**Cloud (AWS/Azure/GCP):**
- Use managed container services
- Configure auto-scaling
- Set up monitoring and alerts
- Configure backups

---

## Support

**Issues:** File GitHub issues in repository
**Documentation:** See README.md
**API Docs:** http://localhost:8000/api/docs

---

**Last Updated:** November 22, 2025
**Version:** 1.0.0
**Status:** Production Ready
