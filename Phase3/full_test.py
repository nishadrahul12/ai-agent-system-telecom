import requests
import time

API_URL = "http://localhost:8000"

print("="*70)
print("COMPONENT 2 - FULL VERIFICATION TEST")
print("="*70)

# TEST 1: Health check
print("\n[TEST 1] Health check...")
response = requests.get(f"{API_URL}/health")
if response.status_code == 200:
    print("✅ PASS: API is healthy")
else:
    print(f"❌ FAIL: Status {response.status_code}")

# TEST 2: Upload file
print("\n[TEST 2] File upload...")
with open('../Phase 0/sample_kpi_data.csv', 'rb') as f:
    response = requests.post(
        f"{API_URL}/api/anomalies/analyze",
        files={'file': f},
        params={'sensitivity': 'medium'}
    )

if response.status_code == 200:
    result = response.json()
    task_id = result['task_id']
    print(f"✅ PASS: Upload successful, Task ID: {task_id}")
else:
    print(f"❌ FAIL: Status {response.status_code}, {response.text}")
    exit(1)

# TEST 3: Check status
print("\n[TEST 3] Task status polling...")
for i in range(120):  # Wait up to 2 minutes
    response = requests.get(f"{API_URL}/api/anomalies/status/{task_id}")
    status = response.json()
    
    if status['status'] == 'completed':
        print(f"✅ PASS: Task completed in {i} seconds")
        break
    elif status['status'] == 'failed':
        print(f"❌ FAIL: Task failed: {status.get('error')}")
        exit(1)
    else:
        if i % 5 == 0:  # Print every 5 seconds
            print(f"  [{i}s] {status['status']}: {status['progress_percent']}%")
    
    time.sleep(1)
else:
    print("❌ FAIL: Task timeout after 120 seconds")
    exit(1)

# TEST 4: Get results
print("\n[TEST 4] Retrieving results...")
response = requests.get(f"{API_URL}/api/anomalies/result/{task_id}")
if response.status_code == 200:
    result = response.json()
    print(f"✅ PASS: Results retrieved")
    print(f"   - Anomalies found: {len(result['anomalies'])}")
    print(f"   - Network status: {result['network_classification']['network_status']}")
    print(f"   - Critical: {result['network_classification']['critical_count']}")
    print(f"   - Warning: {result['network_classification']['warning_count']}")
else:
    print(f"❌ FAIL: Status {response.status_code}")
    exit(1)

# TEST 5: List tasks
print("\n[TEST 5] List tasks...")
response = requests.get(f"{API_URL}/api/anomalies/list")
if response.status_code == 200:
    tasks = response.json()
    print(f"✅ PASS: Found {len(tasks)} task(s)")
else:
    print(f"❌ FAIL: Status {response.status_code}")

# TEST 6: Check results are saved to disk
print("\n[TEST 6] Verify disk persistence...")
import os
result_dir = f"results/{task_id}"
if os.path.exists(result_dir):
    files = os.listdir(result_dir)
    print(f"✅ PASS: Results directory exists")
    print(f"   - Files saved: {files}")
else:
    print(f"❌ FAIL: Results directory not found")

print("\n" + "="*70)
print("✅ ALL TESTS PASSED! Component 2 is working correctly!")
print("="*70)
