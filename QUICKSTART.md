# Quick Start Guide

Get the Telecom AI Multi-Agent System running in 5 minutes.

---

## 1. Install (1 minute)

Clone & enter directory
git clone <repo-url>
cd AI-AGENT-SYSTEM-TELECOM

Create virtual environment
python -m venv venv

Activate (Windows)
.\venv\Scripts\Activate.ps1

Install dependencies
pip install -r requirements.txt

text

---

## 2. Verify (1 minute)

Run tests
python -m pytest Phase1/api/tests/ -v

Should show: 44 passed ✓
text

---

## 3. Start Server (1 minute)

Start orchestrator & API
python Phase0/orchestrator.py

Opens on http://localhost:8000
text

---

## 4. Try It (2 minutes)

### Create test data

**telecom_data.csv:**
traffic,prb_util,latency,drop_rate
100,80,15,0.5
150,85,20,0.8
200,90,25,1.2
250,95,30,1.5

text

### Upload & Analyze

1. Upload
curl -X POST http://localhost:8000/api/correlation/upload
-F "file=@telecom_data.csv"

Returns: file_id (copy this)
2. Analyze
curl -X POST http://localhost:8000/api/correlation/analyze
-H "Content-Type: application/json"
-d '{
"file_id": "YOUR_FILE_ID",
"target_variable": "drop_rate"
}'

Returns: task_id (copy this)
3. Check Status
curl http://localhost:8000/api/correlation/status/YOUR_TASK_ID

4. Get Results
curl http://localhost:8000/api/correlation/result/YOUR_TASK_ID

text

---

## 5. View Documentation

**Interactive Swagger UI:**
http://localhost:8000/api/docs

text

Click any endpoint to test it directly in browser!

---

## Next Steps

- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Check [README.md](README.md) for full documentation
- Review API endpoints at `/api/docs`

---

**That's it! System is running.** 🚀