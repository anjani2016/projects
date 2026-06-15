# AI Weld Inspector — Band.ai Multi-Agent Architecture

This document details the multi-agent orchestration architecture built using the **Band SDK** (`band-sdk[google_adk]`) and coordinated via the **Band of Agents** platform.

---

## 🏗️ System Architecture & Boundaries

The project integrates a **decoupled, event-driven multi-agent system** alongside our Hexagonal (Ports & Adapters) backend, allowing both local single-agent routing and distributed multi-agent collaboration rooms.

```mermaid
graph TD
    subgraph "Streamlit UI (Frontend Client)"
        UI[Streamlit Web App] -->|Toggle: Band Platform| ModeSelect{Orchestration Mode}
    end

    subgraph "GCP Cloud Run Backend"
        ModeSelect -->|POST /inspect/band| API[FastAPI Server]
        API -->|Orchestrate| BandOrch[BandInspectionOrchestrator]
    end

    subgraph "Band.ai Platform (Room)"
        BandOrch -->|1. Dispatch Context| Room[Band Room WebSocket]
        Room -.->|2. Run Detection| Vision[Weld Vision Agent]
        Room -.->|3. Evaluate Acceptance| Compliance[Weld Compliance Agent]
        Room -.->|4. Verify Safety Sign-off| Review[Weld Review Agent]
    end

    subgraph "Data & Storage Layers"
        BandOrch -->|5. Log Audit Event & Record| Mongo[MongoDB Atlas Cloud]
        Mongo -.->|Resilient Fallback| SQLite[Local SQLite DB]
    end
```

---

## 👥 The 4 Remote Agents

All agents run as remote, long-lived Python listeners utilizing the `band-sdk`. They connect via secure WebSockets to the Band platform (`wss://app.band.ai`).

| Agent Name | Role | Core Technologies |
| :--- | :--- | :--- |
| **Weld Orchestrator** | Hosts and manages the inspection room, dispatches contexts, and wraps up final verdicts. | Python, `band-sdk[google_adk]` |
| **Weld Vision** | Detects physical discontinuities and cracks from grey-scale radiography scans. | RT-DETR / YOLOv11x, OpenCV |
| **Weld Compliance** | Dynamically evaluates defect sizes against regulatory standard acceptance criteria (ASME/AWS/API). | Gemini 2.5 Flash, Rules Engine |
| **Weld Review** | Final safety auditor enforcing human-in-the-loop (HITL) overrides (e.g., crack = mandatory reject). | Gemini 2.5 Flash, MongoDB Adapter |

---

## 📈 Multi-Agent Message Sequence Flow

Below is the message coordination sequence within the Band room during an inspection request:

```mermaid
sequenceDiagram
    autonumber
    actor User as Streamlit Client
    participant Orch as Weld Orchestrator
    participant Vis as Weld Vision Agent
    participant Comp as Weld Compliance Agent
    participant Rev as Weld Review Agent
    participant DB as MongoDB Atlas

    User->>Orch: POST /inspect/band (radiography upload)
    Note over Orch: Enhanced contrast with CLAHE
    Orch->>Vis: Send inspection task payload
    Note over Vis: Runs RT-DETR model on gray-scale image
    Vis-->>Orch: Return detected defect list (type, conf, bbox, px_dims)
    
    Orch->>Comp: Dispatch defect coordinates & thickness
    Note over Comp: Queries ASME/AWS rules threshold
    Comp-->>Orch: Return Compliance Verdict (PASS / REJECT) + standards reasoning
    
    Orch->>Rev: Send final verdict & defect list for sign-off
    Note over Rev: Enforces mandatory safety overrides (cracks = REJECT)
    Rev-->>Orch: Return final signed review verdict & audit-logged flag
    
    Orch->>DB: Save complete inspection record
    Orch->>User: JSON report + annotated image + Room Activity Trace
```

---

## 💾 Failover & Resiliency Principles
- **Vision Caching**: Cryptographic SHA-256 hashes of radiography scans are indexed. If an identical scan is re-submitted, the system returns cached detection bboxes, skipping redundant inference overhead.
- **Failover Databases**: If connection to the cloud MongoDB Atlas instance drops, the core domain automatically routes storage and audit events to a local SQLite fallback database (`data/local_ndt.db`), synchronizing when the connection recovers.
