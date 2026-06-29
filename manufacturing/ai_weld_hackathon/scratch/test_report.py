import requests
import json
import os

API_URL = "http://localhost:8000"
image_path = "data/raw/ri_sample1.png"

if not os.path.exists(image_path):
    print(f"Error: {image_path} not found.")
    exit(1)

print("Sending inspect request to backend API...")
with open(image_path, "rb") as f:
    files = {"file": (os.path.basename(image_path), f, "image/png")}
    data = {
        "thickness": 8.5,
        "model_path": "weights/m60.pt",
        "app_type": "Piping",
        "material": "Stainless Steel",
        "regulatory_code": "ASME B31.3",
        "client_spec": "Client 1 Specification",
        "other_standard": "Weld Tolerances Standard ASME UW-33 UW-35",
        "usage": "Inspection"
    }
    
    response = requests.post(f"{API_URL}/inspect", files=files, data=data)
    
if response.status_code == 200:
    res_json = response.json()
    if res_json.get("status") == "success":
        report_id = res_json.get("report_id")
        print(f"Success! Generated Report ID: {report_id}")
        pdf_path = f"data/inspections/reports/{report_id}.pdf"
        if os.path.exists(pdf_path):
            print(f"PDF successfully generated at: {pdf_path}")
            print(f"PDF file size: {os.path.getsize(pdf_path)} bytes")
        else:
            print("Error: PDF file was not found on disk after successful API call!")
    else:
        print(f"API returned error status: {res_json}")
else:
    print(f"HTTP Error {response.status_code}: {response.text}")
