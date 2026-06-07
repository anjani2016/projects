import requests
import os
import time

API_URL = "http://localhost:8000"

print("=== STARTING E2E WORKFLOW TEST ===")

# 1. Run inspect to generate a new report
image_path = "data/raw/ri_sample1.png"
if not os.path.exists(image_path):
    print(f"Error: {image_path} does not exist. Cannot run test.")
    exit(1)

print(f"\n1. Submitting '{image_path}' to /inspect...")
with open(image_path, "rb") as f:
    files = {"file": (os.path.basename(image_path), f.read(), "image/png")}
    data = {
        "model_path": "weights/m60.pt",
        "thickness": 10.0,
        "material": "Carbon Steel",
        "regulatory_code": "ASME B31.3",
        "client_spec": "None",
        "other_standard": "None",
        "app_type": "Piping",
        "usage": "Fabrication"
    }
    
    res = requests.post(f"{API_URL}/inspect", files=files, data=data)

if res.status_code != 200:
    print(f"Error: Inspect request failed with status {res.status_code}: {res.text}")
    exit(1)

res_json = res.json()
if res_json.get("status") != "success":
    print(f"Error: Backend reported failure: {res_json.get('result')}")
    exit(1)

report_id = res_json.get("report_id")
print(f"Success! Report generated. Report ID: {report_id}")

# Verify Stage 0 PDF exists
pdf_path = f"data/inspections/reports/{report_id}.pdf"
if os.path.exists(pdf_path):
    stage0_size = os.path.getsize(pdf_path)
    print(f"Stage 0 PDF exists. Size: {stage0_size} bytes")
else:
    print("Error: PDF report was not created.")
    exit(1)

# 2. Performer submits remarks
print("\n2. Submitting Performer Remarks (Stage 1)...")
perf_data = {
    "comments": "The butt weld joints are clean with normal root penetration. Only minor surface porosities were identified but well within ASME B31.3 limits.",
    "role": "performer"
}
res1 = requests.post(f"{API_URL}/records/{report_id}/feedback", data=perf_data)
if res1.status_code == 200:
    r_json = res1.json()
    print("Success! Performer remarks logged.")
    print(f"Workflow State: {r_json.get('status_state')}")
    time.sleep(1) # wait a tiny bit for file I/O to flush
    stage1_size = os.path.getsize(pdf_path)
    print(f"Stage 1 PDF size: {stage1_size} bytes (Initial was {stage0_size})")
else:
    print(f"Error submitting performer remarks: {res1.status_code} - {res1.text}")
    exit(1)

# 3. Supervisor submits comments and sends to client
print("\n3. Submitting Supervisor Comments & Releasing (Stage 2)...")
super_data = {
    "comments": "Weld joint is approved. Ultrasonic alignment and radiography results verified against ASME standards. Released to client.",
    "role": "supervisor"
}
res2 = requests.post(f"{API_URL}/records/{report_id}/feedback", data=super_data)
if res2.status_code == 200:
    r_json = res2.json()
    print("Success! Supervisor review complete.")
    print(f"Workflow State: {r_json.get('status_state')}")
    time.sleep(1) # wait a tiny bit for file I/O to flush
    stage2_size = os.path.getsize(pdf_path)
    print(f"Stage 2 PDF size: {stage2_size} bytes (Stage 1 was {stage1_size})")
else:
    print(f"Error submitting supervisor remarks: {res2.status_code} - {res2.text}")
    exit(1)

print("\n=== E2E WORKFLOW TEST COMPLETED SUCCESSFULLY ===")
