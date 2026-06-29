import requests
import os

API_URL = "http://localhost:8000"
report_id = "REP-20260607-015" # our previously generated report

print("=== STAGE 0: Initial PDF Inspection ===")
pdf_path = f"data/inspections/reports/{report_id}.pdf"
if os.path.exists(pdf_path):
    print(f"Generated PDF exists. Initial size: {os.path.getsize(pdf_path)} bytes")
else:
    print("Error: Report PDF doesn't exist.")
    exit(1)

print("\n=== STAGE 1: Performer Andy Flower Submits Remarks ===")
perf_data = {
    "comments": "The butt weld joints are clean with normal root penetration. Only minor surface porosities were identified but well within ASME B31.3 limits.",
    "role": "performer"
}
res1 = requests.post(f"{API_URL}/records/{report_id}/feedback", data=perf_data)
if res1.status_code == 200:
    r_json = res1.json()
    print("Success! Performer comments logged.")
    print(f"Workflow State: {r_json.get('status_state')}")
    print(f"Performer Comments: {r_json.get('performer_comments')}")
    print(f"PDF size after Stage 1 regeneration: {os.path.getsize(pdf_path)} bytes")
else:
    print(f"Error submitting performer remarks: {res1.status_code} - {res1.text}")
    exit(1)

print("\n=== STAGE 2: Supervisor Richard Campbell Evaluates & Releases ===")
super_data = {
    "comments": "Weld joint is approved. Ultrasonic alignment and radiography results verified against ASME standards. Released to client.",
    "role": "supervisor"
}
res2 = requests.post(f"{API_URL}/records/{report_id}/feedback", data=super_data)
if res2.status_code == 200:
    r_json = res2.json()
    print("Success! Supervisor review complete.")
    print(f"Workflow State: {r_json.get('status_state')}")
    print(f"Supervisor Comments: {r_json.get('supervisor_comments')}")
    print(f"PDF size after Stage 2 regeneration: {os.path.getsize(pdf_path)} bytes")
else:
    print(f"Error submitting supervisor remarks: {res2.status_code} - {res2.text}")
    exit(1)

print("\n=== Verification Completed successfully ===")
