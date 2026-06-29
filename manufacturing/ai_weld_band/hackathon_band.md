# Band of Agents Hackathon Submission Guide

This project is a **distributed multi-agent system** that automates Non-Destructive Testing (NDT) weld quality control. It is built using the **Band SDK** (`band-sdk`) and runs on the **Band.ai** platform, backed by Google Cloud Platform (GCP) Cloud Run and MongoDB Atlas.

---

## 🔗 Live URLs

*   **Frontend User Interface (Streamlit)**: [Weld NDT Portal](https://weld-frontend-732680621081.us-central1.run.app)
*   **Backend REST Service (FastAPI)**: [Weld REST API Service](https://weld-backend-732680621081.us-central1.run.app)
*   **API OpenDocs Swagger**: [API Swagger Specs](https://weld-backend-732680621081.us-central1.run.app/docs)

---

## 🎭 The Multi-Agent Collaboration Room

The pipeline is coordinated inside a Band room containing 4 remote agents:

1.  **Weld Orchestrator Agent** (UUID: `b0c1269c-4d84-4e4a-806c-9941ab848986`): Dispatches inputs, tracks statuses, synthesizes final verdicts, logs audit events.
2.  **Weld Vision Agent** (UUID: `f89e3592-fc66-4c3d-8ccc-d052ae5c0ccd`): Runs custom-trained RT-DETR / YOLOv11 computer vision inference on radiography images to localize defects.
3.  **Weld Compliance Agent** (UUID: `b65bb3b0-5e8e-4466-8a5c-7c406402505f`): Compares defect pixel measurements with ASME B31.3 / API 1104 / AWS D1.1 tolerances.
4.  **Weld Review Agent** (UUID: `027c7f2f-cd79-4450-990d-8f6b2d2e4b12`): Enforces mandatory overrides (e.g. crack classifications must be rejected).

---

## ⚡ Deployment & Hosting Architecture

*   **Serverless Compute**: Frontend and Backend run as decoupled microservices on **GCP Cloud Run** with auto-scaling.
*   **Database**: Inspection records and event logs are stored in a new database (`weld_band`) inside the **MongoDB Atlas** cluster.
*   **Failover Resiliency**: If connection to MongoDB Atlas is lost, backend automatically defaults to local **SQLite** (`data/local_ndt.db`), preventing downtime in industrial facilities.
*   **Vision Cache**: Defect detections are cached using SHA-256 image hashes, allowing instant sub-second lookup on duplicate submissions.

---

## 🛠️ Verification & Running Instructions

### Local Environment Setup
To run the agent listeners locally:

1. Clone the repository and install requirements:
   ```bash
   python -m venv weld_env
   source weld_env/bin/activate
   pip install -r requirements.txt
   ```
2. Start the FastAPI backend and Streamlit UI:
   ```bash
   # Run backend API
   PYTHONPATH=. uvicorn src.api.server:app --port 8000
   
   # Run UI
   streamlit run frontend/app.py --server.port 8501
   ```
3. Start the Band listeners (remote agents):
   ```bash
   PYTHONPATH=. python src/band/orchestrator_agent.py
   PYTHONPATH=. python src/band/vision_agent.py
   PYTHONPATH=. python src/band/compliance_agent.py
   PYTHONPATH=. python src/band/review_agent.py
   ```
