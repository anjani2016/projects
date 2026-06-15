import streamlit as st
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Page configuration for premium UI feel
st.set_page_config(
    page_title="Weld NDT AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI styling override
st.markdown("""
    <style>
    .main {
        background-color: #0f1115;
        color: #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1a1e26;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #94a3b8;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2e3748 !important;
        color: #38bdf8 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #38bdf8;
    }
    .card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 5px solid #38bdf8;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration from Environment
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Sidebar Page Navigation
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to Page", ["🚀 Project Charter & Architecture", "🕵️‍♂️ Autonomous NDT Inspector", "📄 Open Source License"])

if page == "📄 Open Source License":
    st.title("📄 Open Source License")
    st.markdown("""
    This project is open-source software licensed under the **MIT License**.
    
    ```text
    MIT License

    Copyright (c) 2026 Anjani D / Centauri Research Services

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    ```
    """)
    st.stop()

if page == "🚀 Project Charter & Architecture":
    st.title("🚀 Project Charter & Methodology")
    
    st.markdown("""
    ### Introduction & Core Charter
    This application is a **Computer Vision-driven diagnostic tool** designed specifically for **Non-Destructive Testing (NDT)** quality control in the oil & gas, piping, power, and manufacturing industries.
    
    The primary charter of this project is to automate the interpretation of digital radiography (RT) images, rapidly identifying and quantifying critical welding defects (such as porosity, inclusions, and cracks). By combining deep learning with codified engineering standards, this tool aims to reduce human error in X-ray interpretation and accelerate the **"Review-to-Repair"** quality assurance cycle for critical assets.
    
    ---
    
    ### 🔬 Methodology & Core Pipeline
    
    Our pipeline operates on a modular, multi-phase approach:
    
    1. **Phase 1: Pre-processing & Enhancement (CLAHE)**
       We apply Contrast Limited Adaptive Histogram Equalization (CLAHE) on the backend to enhance low-contrast radiographic films, ensuring that micro-defects are visible to the AI engine.
    
    2. **Phase 2: AI Detection & Inference**
       The core engine utilises state-of-the-art instance detection/segmentation models. The AI acts as a purely objective **"measuring tool"** to output bounding boxes, defect classes, and pixel dimensions.
    
    3. **Phase 3: Engineering Rule Validation**
       Instead of relying solely on AI confidence, the system passes the detected dimensions through a deterministic Rule Engine. This engine cross-references the measurements against strict international engineering codes and standards (such as **ASME B31.3** and **ASME Section VIII**). The application also includes a built-in provision to tune the rule engine against bespoke client specifications alongside the baseline international codes.
    
    4. **Phase 4: Autonomous Agent Reasoning**
       The Generative AI Agent synthesises vision findings and rule-engine verdicts into a structured reasoning log — explaining *why* a weld passes or fails in plain language traceable to the exact standard clause.
    
    5. **Phase 5: Automated Report Generation & Review Workflow**
       The system generates a gated PDF radiographic examination report. The report evolves through a structured review lifecycle — Performer → Supervisor — with digital signature stamps applied at each stage.
    """)
    
    st.markdown("---")

    # ── Agent Workflow Section ──────────────────────────────────────────────────
    st.subheader("🤖 Agent Workflow & Orchestration")

    st.markdown("""
    The AI Agent is the reasoning core of the inspection pipeline. It operates as an **autonomous orchestrator** that dynamically selects and invokes a set of specialised tools, then synthesises their outputs into a final, standards-traceable verdict.

    #### Step-by-Step Agent Execution Flow

    | Step | Agent Action | Tool / System Invoked |
    |------|-------------|----------------------|
    | **1. Receive Task** | Agent receives the inspection job: image path, wall thickness, regulatory code, material, and client spec | `FastAPI /inspect` endpoint |
    | **2. Enhance Image** | Calls the pre-processing tool to apply CLAHE contrast enhancement to the raw radiograph | `WeldProcessor.enhance_image()` |
    | **3. Run Vision Inference** | Invokes the computer vision model to detect, classify, and measure weld discontinuities | `VisionPort` → `UltralyticsAdapter` (RT-DETR / YOLO) |
    | **4. Query Compliance Rules** | Retrieves the applicable acceptance criteria for the detected defect types against the selected standard | `CompliancePort` → `LocalComplianceAdapter` (ASME B31.3 / ASME VIII / AWS / API) |
    | **5. Apply Client Overrides** | If a client specification is active, overlays stricter thresholds on top of the base code | Rule Engine — client spec merge layer |
    | **6. Compute Verdict** | Cross-references measured defect dimensions against the retrieved acceptance criteria to determine PASS / FAIL | `InspectionOrchestrator.run()` |
    | **7. Generate Reasoning Log** | Composes a human-readable reasoning statement that cites the exact standard and clause supporting the verdict | Agent LLM synthesis (Gemini / Claude) |
    | **8. Persist Record** | Writes the full `InspectionRecord` (verdict, defects, reasoning, image paths, metadata) to the database | `DatabasePort` → `MongoAdapter` (MongoDB Atlas primary, SQLite fallback) |
    | **9. Log Audit Event** | Appends an immutable audit entry with user identity, action, image hash, and timestamp | `MongoAdapter.log_audit_event()` |
    | **10. Generate PDF Report** | Compiles a gated, stage-aware PDF report embedding all findings and branding | `reporter.py` → `fpdf2` |
    | **11. Reviewer Feedback Loop** | Performer submits remarks → Agent updates the record in DB → Supervisor approves → Final report sealed with dual digital signatures | `POST /records/{id}/feedback` → `MongoAdapter.update_record()` |

    #### Key Architectural Decisions

    - **Tool Isolation**: Each agent tool (vision, compliance, database) is accessed through a **Port interface**, making the agent's reasoning loop independent of the underlying model or database technology.
    - **Deterministic Rules + Generative Reasoning**: The pass/fail verdict is always computed by the deterministic rule engine — the LLM is used only for *explanation*, not for the binary decision. This ensures repeatability and auditability.
    - **Stage-Gated PDF**: The PDF report is compiled on-demand at each download event, reflecting only the content that exists at that workflow stage (no future signature stamps are shown).
    - **Dual-Write Persistence**: Every record is first attempted to MongoDB Atlas; on any connection failure, the SQLite local adapter transparently takes over with schema auto-migration.
    """)

    st.markdown("---")

    # ── Architecture Diagram ────────────────────────────────────────────────────
    st.subheader("📐 System Architecture Diagram")

    st.markdown("""
    The application follows the **Hexagonal Architecture (Ports and Adapters)** pattern, split into two phases shown in separate diagrams below.
    """)

    arch_tab1, arch_tab2 = st.tabs(["🔬 Phase 1 — AI Weld Analysis Pipeline", "✍️ Phase 2 — HITL Review & Approval"])

    with arch_tab1:
        st.markdown("""
        **Automated pipeline sequence — numbers show order of execution, letters show parallel branches.**

        | Symbol | Meaning |
        |---|---|
        | `1`, `2`, `3` … | Sequential steps — each waits for the previous |
        | `4a` / `4b` | **Parallel** tool invocations — fired concurrently by the agent |
        | `5` | Waits for both 4a and 4b results before proceeding |
        | `6a` / `6b` / `6c` | **Parallel** DB writes — fired simultaneously after persist |
        | `7` | Returns verdict after all writes are confirmed |
        | `8a` / `8b` | **Parallel** PDF read + compile inputs |
        """)
        dot_phase1 = """
        digraph Phase1 {
            bgcolor="#0f1115"
            rankdir=TB
            node [shape=box, style="filled,rounded", color="#38bdf8", fontcolor="#e2e8f0", fillcolor="#1e293b", fontname="Helvetica", fontsize=11]
            edge [color="#94a3b8", fontname="Helvetica", fontcolor="#94a3b8", fontsize=9]

            Inspector [label="Inspector\\n(Streamlit UI)", shape=ellipse, fillcolor="#1a1e26"]
            API       [label="FastAPI Backend\\nPOST /inspect", fillcolor="#2e3748"]
            { rank=same; Inspector; API }

            subgraph cluster_agent {
                label = "AI Agent Orchestrator (Gemini / Claude)"
                color = "#38bdf8"
                fontcolor = "#38bdf8"
                style = "rounded"
                Orchestrator [label="InspectionOrchestrator\\n(use_cases layer)", fillcolor="#1e3a5f"]
            }

            PreProc [label="3: WeldProcessor\\n(CLAHE Enhancement)", color="#6366f1", fillcolor="#1e293b"]

            subgraph cluster_parallel_tools {
                label = "Parallel Tool Invocations (4a + 4b run concurrently)"
                color = "#6366f1"
                fontcolor = "#a5b4fc"
                style = "dashed"
                Vision  [label="4a: VisionPort\\n(RT-DETR / YOLO)", color="#6366f1"]
                Rules   [label="4b: CompliancePort\\n(ASME / AWS / API + Client Spec)", color="#6366f1"]
                { rank=same; Vision; Rules }
            }

            Reasoning [label="5: LLM Reasoning Engine\\n(Synthesise Verdict - waits for 4a + 4b)", fillcolor="#1e3a5f"]

            subgraph cluster_db {
                label = "Database Layer - Parallel Writes (6a + 6b + 6c run concurrently)"
                color = "#10b981"
                fontcolor = "#6ee7b7"
                style = "rounded"
                DBPort   [label="6: MongoAdapter", color="#10b981", fillcolor="#0f2d1e"]
                MongoDB  [label="6a: MongoDB Atlas\\n(Primary - cloud write)", shape=cylinder, fillcolor="#0f2d1e", color="#10b981"]
                AuditLog [label="6b: Audit Event Log\\n(immutable trail)",    shape=note,     fillcolor="#0f2d1e", color="#10b981"]
                SQLite   [label="6c: SQLite\\n(Failover write)",               shape=cylinder, fillcolor="#0f2d1e", color="#10b981"]
                { rank=same; MongoDB; AuditLog; SQLite }
            }

            Inspector2 [label="Inspector\\n(Receives Verdict + Image)", shape=ellipse, fillcolor="#1a1e26"]

            subgraph cluster_pdf {
                label = "On-Demand PDF Generation - Parallel Inputs (8a + 8b)"
                color = "#f59e0b"
                fontcolor = "#fde68a"
                style = "dashed"
                Reporter [label="8: ReporterTool\\n(fpdf2 PDF Builder)", color="#f59e0b"]
                PDF0     [label="Stage 0 PDF Report\\n(No signatures)", fillcolor="#1a1e26"]
                { rank=same; Reporter; PDF0 }
            }

            Inspector    -> API          [label="1: Upload Image + Inspection Params", color="#38bdf8", fontcolor="#38bdf8"]
            API          -> Orchestrator [label="2: Dispatch Job",                     color="#38bdf8", fontcolor="#38bdf8"]
            Orchestrator -> PreProc      [label="3: Enhance Image (must complete first)", color="#38bdf8", fontcolor="#38bdf8"]

            PreProc -> Vision [label="4a: Detect Defects (parallel)",          color="#a5b4fc", fontcolor="#a5b4fc"]
            PreProc -> Rules  [label="4b: Query Acceptance Criteria (parallel)", color="#a5b4fc", fontcolor="#a5b4fc"]

            Vision  -> Reasoning [label="4a return: BBoxes, Classes, Dims",    style=dashed, color="#6366f1", fontcolor="#6366f1"]
            Rules   -> Reasoning [label="4b return: Pass/Fail Thresholds",      style=dashed, color="#6366f1", fontcolor="#6366f1"]

            Reasoning -> DBPort [label="5: Persist InspectionRecord", color="#38bdf8", fontcolor="#38bdf8"]

            DBPort -> MongoDB  [label="6a: Write Record (primary)",      color="#10b981", fontcolor="#10b981"]
            DBPort -> AuditLog [label="6b: Write Audit Event",           color="#10b981", fontcolor="#10b981"]
            DBPort -> SQLite   [label="6c: Write Failover (if needed)",  style=dashed, color="#10b981", fontcolor="#10b981"]

            Reasoning    -> API        [label="7: Return Verdict + Annotated Image", color="#38bdf8", fontcolor="#38bdf8"]
            API          -> Inspector2 [label="8: JSON Response + Base64 Image",     color="#38bdf8", fontcolor="#38bdf8"]

            Inspector2 -> Reporter [label="8a: Request PDF (Stage 0) (parallel)",   color="#f59e0b", fontcolor="#f59e0b"]
            DBPort     -> Reporter [label="8b: Read Record from DB (parallel)",       color="#f59e0b", fontcolor="#f59e0b"]
            Reporter   -> PDF0     [label="9: Compile Stage-Gated PDF",               color="#f59e0b", fontcolor="#f59e0b"]
        }
        """
        st.graphviz_chart(dot_phase1)

    with arch_tab2:
        st.markdown("""
        **HITL sequence — numbers show stage order, letters show parallel actions within a stage.**

        | Symbol | Meaning |
        |---|---|
        | `S1-1`, `S1-2` … | Stage 1 sequential steps (Performer review) |
        | `S1-3a` / `S1-3b` | **Parallel**: DB persist + PDF compile happen simultaneously |
        | `S2-1`, `S2-2` … | Stage 2 sequential steps (Supervisor approval) |
        | `S2-3a` / `S2-3b` | **Parallel**: DB update + final PDF compile happen simultaneously |
        """)
        dot_phase2 = """
        digraph Phase2 {
            bgcolor="#0f1115"
            rankdir=TB
            node [shape=box, style="filled,rounded", color="#38bdf8", fontcolor="#e2e8f0", fillcolor="#1e293b", fontname="Helvetica", fontsize=11]
            edge [color="#94a3b8", fontname="Helvetica", fontcolor="#94a3b8", fontsize=9]

            ReportStage0 [label="Stage 0 Report\\n(AI-Generated - Phase 1 Output)", fillcolor="#1e293b"]
            API          [label="FastAPI Backend\\nPOST /records/{id}/feedback", fillcolor="#2e3748"]

            subgraph cluster_db {
                label = "Database Layer (MongoAdapter)"
                color = "#10b981"
                fontcolor = "#6ee7b7"
                style = "rounded"
                DBPort  [label="MongoAdapter\\n(Port Interface)", color="#10b981", fillcolor="#0f2d1e"]
                MongoDB [label="MongoDB Atlas\\n(Primary)",  shape=cylinder, fillcolor="#0f2d1e", color="#10b981"]
                SQLite  [label="SQLite\\n(Failover)",         shape=cylinder, fillcolor="#0f2d1e", color="#10b981"]
            }

            subgraph cluster_performer {
                label = "STAGE 1 - Performer Review  [Sequential then Parallel writes]"
                color = "#f59e0b"
                fontcolor = "#fde68a"
                style = "rounded"
                Performer   [label="S1-1: Andy Flower\\n(ASNT Level II)\\nReviews AI Findings", shape=ellipse, color="#f59e0b", fillcolor="#2d1f0f"]
                PerfRemarks [label="S1-2: Enter Remarks\\n+ Apply Digital Signature",           color="#f59e0b", fillcolor="#2d1f0f"]
                PDF1        [label="S1-3b: Stage 1 PDF\\n(Performer Signed)",                   color="#f59e0b", fillcolor="#2d1f0f"]
            }

            subgraph cluster_supervisor {
                label = "STAGE 2 - Supervisor Approval  [Sequential then Parallel writes]"
                color = "#22c55e"
                fontcolor = "#86efac"
                style = "rounded"
                Supervisor   [label="S2-1: Richard Campbell\\n(PCN Level III)\\nReviews Stage 1 Report", shape=ellipse, color="#22c55e", fillcolor="#0f2d1e"]
                SuperRemarks [label="S2-2: Enter Evaluation Comments\\n+ Apply Digital Signature",        color="#22c55e", fillcolor="#0f2d1e"]
                PDF2         [label="S2-3b: Stage 2 PDF\\n(Dual-Signed - Final Release)",                 color="#22c55e", fillcolor="#0f2d1e"]
            }

            ReportStage0 -> Performer   [label="S1-0: Performer receives Stage 0 Report",    color="#f59e0b", fontcolor="#f59e0b"]
            Performer    -> PerfRemarks [label="S1-1: Review findings, enter remarks",        color="#f59e0b", fontcolor="#f59e0b"]
            PerfRemarks  -> API         [label="S1-2: POST feedback (role=performer)",         color="#f59e0b", fontcolor="#f59e0b"]

            API -> DBPort [label="S1-3a (parallel): update_record()\\nperformer_comments, status_state=1", color="#10b981", fontcolor="#10b981"]
            API -> PDF1   [label="S1-3b (parallel): Compile Stage 1 PDF",                                  color="#f59e0b", fontcolor="#f59e0b"]

            DBPort -> MongoDB [label="S1-3a-i: Persist primary",   color="#10b981", fontcolor="#10b981"]
            DBPort -> SQLite  [label="S1-3a-ii: Persist failover",  color="#10b981", fontcolor="#10b981", style=dashed]

            PDF1 -> Supervisor [label="S2-0: Supervisor receives Performer-Signed Report", color="#22c55e", fontcolor="#22c55e"]

            Supervisor   -> SuperRemarks [label="S2-1: Enter evaluation comments",         color="#22c55e", fontcolor="#22c55e"]
            SuperRemarks -> API          [label="S2-2: POST feedback (role=supervisor)",    color="#22c55e", fontcolor="#22c55e"]

            API -> DBPort [label="S2-3a (parallel): update_record()\\nsupervisor_comments, status_state=2", color="#10b981", fontcolor="#10b981"]
            API -> PDF2   [label="S2-3b (parallel): Compile Final Dual-Signed PDF",                        color="#22c55e", fontcolor="#22c55e"]

            PDF2 -> Supervisor [label="S2-4: Download and Release to Client", color="#22c55e", fontcolor="#22c55e"]
        }
        """
        st.graphviz_chart(dot_phase2)

    st.stop()

# ── NDT Inspector page ─────────────────────────────────────────────────────────
st.title("🤖 Autonomous NDT Quality Inspector")
st.markdown("""
This enterprise-grade QA system is powered by an **autonomous Generative AI Agent** built on the `google-antigravity-sdk`. 

**Key System Capabilities:**
*   🔬 **Dual-Model Vision Inference**: Autonomously deploys fine-tuned computer vision models (such as YOLO and RT-DETR) to pinpoint and size physical weld discontinuities.
*   📜 **Standards-Driven Compliance**: Integrates a dynamic rules engine that cross-references defect dimensions against international codes (ASME B31.3, ASME VIII, AWS, API) and client-specific overrides.
*   🛡️ **Decoupled Fallback Storage**: Follows Hexagonal Architecture principles to securely log compliance records and audit logs to MongoDB Atlas, with automatic failover to local SQLite storage.
""")

# Sidebar Configuration
st.sidebar.header("📋 Inspection Parameters")

thickness = st.sidebar.number_input(
    "Wall Thickness (mm)",
    min_value=1.0,
    value=10.0,
    step=0.5
)

# Scan for available weights files in weights/ folder dynamically (both .pt and HF folders)
available_models = ["weights/m60.pt"]
if os.path.exists("weights"):
    pt_files  = [f"weights/{f}" for f in os.listdir("weights") if f.endswith(".pt")]
    hf_dirs   = [f"weights/{f}" for f in os.listdir("weights") if os.path.isdir(f"weights/{f}") and os.path.exists(f"weights/{f}/config.json")]
    all_models = list(set(pt_files + hf_dirs))
    if all_models:
        def model_sort_key(m_path):
            name = os.path.basename(m_path).lower()
            if name == "m60.pt":
                return (0, name)
            elif "rtdetr" in name:
                return (2, name)
            return (1, name)
        available_models = sorted(all_models, key=model_sort_key)

model_path = st.sidebar.selectbox(
    "Vision Model Weights",
    options=available_models,
    help="Select the fine-tuned vision model weights to run on the backend"
)

# Model training status commentary helper
model_info = {
    "m60.pt":                    "🟢 **Production Ready**: Fully trained YOLO model with optimized weights. Recommended for compliance testing.",
    "welding_defects_yolo11x.pt":"🟡 **Candidate Model**: YOLO11x model trained on welding defect datasets.",
    "hf_weld_rtdetr_final":      "🔴 **Experimental (In-Training)**: RT-DETR model checkpoint. Showing low confidence threshold and high false-positive defect counts.",
    "rtdetr-l.pt":               "⚪ **Baseline**: Standard RT-DETR baseline model without custom fine-tuning.",
}
selected_filename = os.path.basename(model_path)
info_text = model_info.get(selected_filename, "⚪ Custom uploaded model weights.")
st.sidebar.markdown(f"<div style='font-size:13px;margin-top:-10px;margin-bottom:15px;color:#94a3b8;'>{info_text}</div>", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📐 Application & Code Standards")

app_type = st.sidebar.selectbox(
    "Application Type (Domain)",
    options=["Piping", "Pipeline", "Structural", "Pressure Vessels", "Storage Tanks", "Other"]
)

material = st.sidebar.selectbox(
    "Material",
    options=["Carbon Steel", "Stainless Steel", "Aluminum", "Copper Nickel", "Other"]
)

usage = st.sidebar.selectbox(
    "Functional Intent / Usage",
    options=["Fabrication", "Design", "Inspection", "Qualification", "Other"]
)

code_standards = {
    "ASME (Pressure/Piping/Qualification)": [
        "ASME B31.3", "ASME B31.1", "ASME VIII Div 1", "ASME VIII Div 2", "ASME IX"
    ],
    "AWS (Structural)": [
        "AWS D1.1", "AWS D1.2", "AWS D1.6", "AWS D1.5"
    ],
    "API (Pipelines/Storage/Inspection)": [
        "API 1104", "API 650", "API 653", "API 570"
    ]
}

code_options = []
for group, codes in code_standards.items():
    code_options.extend(codes)

code_selected = st.sidebar.selectbox("Regulatory Code Standard", options=code_options)

client_spec = st.sidebar.selectbox(
    "Client Specifications (Placeholder)",
    options=["None", "Client 1 Specification", "Client 2 Specification"]
)

other_standard = st.sidebar.selectbox(
    "Other Standards (Placeholder)",
    options=["None", "Weld Tolerances Standard ASME UW-33 UW-35", "Standard 1", "Standard 2"]
)

st.sidebar.warning(
    "⚠️ **Compliance Disclaimer**: The underlying AI vision model is trained solely to detect and "
    "size physical defects, and is NOT trained on regulatory codes or standards (including ASME, AWS, "
    "or API). Standard compliance evaluation is simulated programmatically by the backend rules engine. "
    "Selections currently serve as placeholder routing configurations."
)

# ══════════════════════════════════════════════════════════════════════════════
# FOUR-TAB LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "🔬 Weld Analysis",
    "✍️ Human Review & Approval",
    "📜 Database Explorer",
    "🤖 UiPath Maestro BPMN",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — WELD ANALYSIS  (AI model pipeline only — no review forms)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Source Radiograph")
        uploaded_file = st.file_uploader(
            "Upload Radiography Image (TIFF, PNG, JPG, JPEG)",
            type=["jpg", "png", "tiff", "jpeg"]
        )
        if uploaded_file:
            st.image(uploaded_file, caption="Raw Uploaded Image", use_container_width=True)

    with col2:
        st.subheader("Agent Output & Verdict")

        if uploaded_file:
            # Clear stale results when a new file is selected
            if (
                "inspected_file_name" in st.session_state
                and st.session_state.inspected_file_name != uploaded_file.name
            ):
                st.session_state.pop("inspection_results", None)
                st.session_state.pop("inspected_file_name", None)

            if st.button("Run Autonomous Agent Inspection", type="primary"):
                with st.spinner("Uploading image to backend API & running agent reasoning..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        data  = {
                            "thickness":      thickness,
                            "model_path":     model_path,
                            "app_type":       app_type,
                            "material":       material,
                            "regulatory_code": code_selected,
                            "client_spec":    client_spec,
                            "other_standard": other_standard,
                            "usage":          usage,
                        }
                        response = requests.post(f"{API_URL}/inspect", files=files, data=data)
                        if response.status_code == 200:
                            res_json = response.json()
                            if res_json.get("status") == "success":
                                st.session_state.inspection_results  = res_json
                                st.session_state.inspected_file_name = uploaded_file.name
                            else:
                                st.error(f"Backend Processing Error: {res_json.get('result')}")
                        else:
                            st.error(f"API Connection Error: HTTP {response.status_code}")
                    except Exception as e:
                        st.error(f"Could not connect to FastAPI backend at {API_URL}.\n\nError: {e}")
        else:
            st.info("Please upload a radiography image to begin the inspection.")

    # ── Results panel — full-width below the two upload/output columns ─────────
    if (
        uploaded_file
        and "inspection_results" in st.session_state
        and st.session_state.get("inspected_file_name") == uploaded_file.name
    ):
        res_json     = st.session_state.inspection_results
        agent_output = res_json.get("result", "")
        img_b64      = res_json.get("annotated_image", "")
        defects      = res_json.get("defects", [])
        report_id    = res_json.get("report_id", "N/A")

        st.markdown("---")

        # Header row with PDF download
        hc1, hc2 = st.columns([3, 1])
        with hc1:
            st.subheader("🕵️‍♂️ Inspection Results & Analysis")
        with hc2:
            st.markdown(
                f'<div style="text-align:right;margin-top:10px;">'
                f'<a href="{API_URL}/static/reports/{report_id}.pdf" target="_blank" style="text-decoration:none;">'
                f'<button style="background-color:#38bdf8;color:#0f1115;border:none;padding:8px 16px;border-radius:4px;font-weight:bold;cursor:pointer;">📄 Download PDF Report</button>'
                f'</a></div>',
                unsafe_allow_html=True
            )

        # Verdict banner
        if "STATUS: PASS" in agent_output:
            st.success(f"✅ **FINAL VERDICT: PASS  |  Report ID: {report_id}**")
        elif "STATUS: REJECT" in agent_output:
            st.error(f"❌ **FINAL VERDICT: REJECT  |  Report ID: {report_id}**")
        else:
            st.warning(f"⚠️ **VERDICT UNCLEAR — Refer to Report ID: {report_id}**")

        # Annotated image
        if img_b64:
            try:
                st.image(base64.b64decode(img_b64), caption="AI Inspection Visual Mapping", use_container_width=True)
            except Exception as img_err:
                st.error(f"Failed to decode returned image: {img_err}")

        # Metrics
        st.markdown("### 📊 Metrics")
        m1, m2 = st.columns(2)
        m1.metric("Defects Detected", len(defects))
        m2.metric("Wall Thickness",   f"{thickness} mm")

        # Defect details
        if defects:
            st.markdown("### 🔍 Technical Audits & Coordinates")
            for idx, d in enumerate(defects, 1):
                d_type = d.get("type", "unknown")
                d_conf = d.get("confidence", 0.0)
                d_bbox = d.get("bbox", [])
                px_len = d.get("dims", {}).get("length", 0.0)
                mm_len = px_len * 0.1
                with st.expander(f"Item {idx}: {d_type.upper()} (Conf: {d_conf:.2f})"):
                    st.write(f"**Classification:** `{d_type}`")
                    st.write(f"**Confidence Score:** `{d_conf:.2f}`")
                    st.write(f"**Bounding Box (xyxy):** `{d_bbox}`")
                    st.write(f"**Calculated Length:** `{px_len:.1f} px` (~`{mm_len:.2f} mm` at 0.1 mm/px)")

        # Agent Reasoning Log
        st.markdown("### 📝 Agent Reasoning Log")
        st.info(agent_output)

        # Prompt to proceed to review tab
        st.markdown("---")
        st.info(
            "🔔 **Analysis complete.** Switch to the **✍️ Human Review & Approval** tab to add "
            "Performer remarks and route the report through the supervisor approval workflow."
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HUMAN REVIEW & APPROVAL  (HITL — gated on completed analysis)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("✍️ Human-in-the-Loop (HITL) Review & Approval Workflow")

    if "inspection_results" not in st.session_state:
        st.warning(
            "⚠️ **No active inspection report in this session.**  \n\n"
            "Run a **Weld Analysis** first (Tab 1), then return here to start the review workflow.  \n"
            "To continue reviewing a previously saved report, use the **📜 Database Explorer** tab."
        )
        st.stop()

    res_json             = st.session_state.inspection_results
    report_id            = res_json.get("report_id", "N/A")
    agent_output         = res_json.get("result", "")
    status_state         = res_json.get("status_state", 0)
    performer_comments   = res_json.get("performer_comments", "")
    supervisor_comments  = res_json.get("supervisor_comments", "")

    # ── Summary card ──────────────────────────────────────────────────────────
    verdict_color = "#22c55e" if "STATUS: PASS" in agent_output else "#ef4444"
    verdict_label = "PASS ✅" if "STATUS: PASS" in agent_output else "REJECT ❌"
    st.markdown(f"""
    <div style="background:#1e293b;border-left:5px solid #38bdf8;padding:16px 20px;border-radius:6px;margin-bottom:20px;">
        <b style="color:#38bdf8;font-size:16px;">📋 Report: {report_id}</b><br>
        <span style="color:#94a3b8;">Verdict: <b style="color:{verdict_color};">{verdict_label}</b>
        &nbsp;|&nbsp; Thickness: <b>{res_json.get('thickness', '—')} mm</b>
        &nbsp;|&nbsp; Model: <b>{res_json.get('model_used', '—')}</b></span>
    </div>
    """, unsafe_allow_html=True)

    # ── Workflow stage progress bar ───────────────────────────────────────────
    sc0, sc1, sc2 = st.columns(3)

    def _stage_card(label, sublabel, active, done):
        border  = "#22c55e" if done else ("#38bdf8" if active else "#2e3748")
        icon    = "✅" if done else ("🔵" if active else "⏳")
        color   = "#22c55e" if done else ("#38bdf8" if active else "#64748b")
        bg      = "#1e3a5f" if (active or done) else "#1e293b"
        return (
            f"<div style='text-align:center;padding:10px;background:{bg};"
            f"border-radius:6px;border:1px solid {border};'>"
            f"<b style='color:{color};'>{icon} {label}</b><br>"
            f"<small style='color:#94a3b8;'>{sublabel}</small></div>"
        )

    sc0.markdown(_stage_card("Stage 0", "Report Generated",    status_state == 0, status_state > 0), unsafe_allow_html=True)
    sc1.markdown(_stage_card("Stage 1", "Performer Review",    status_state == 1, status_state > 1), unsafe_allow_html=True)
    sc2.markdown(_stage_card("Stage 2", "Supervisor Approval", status_state == 2, status_state > 2), unsafe_allow_html=True)

    st.markdown("---")

    # ── Stage 0: Await Performer ──────────────────────────────────────────────
    if status_state == 0:
        st.markdown("#### 🔵 Stage 1 — Performer Review")
        st.info(
            "Andy Flower (ASNT Level II) must review the AI findings, add evaluation remarks, "
            "and digitally sign the report before it can proceed to the supervisor."
        )
        st.markdown(
            f'<a href="{API_URL}/static/reports/{report_id}.pdf" target="_blank" style="text-decoration:none;">'
            f'<button style="background-color:#1e293b;color:#38bdf8;border:1px solid #38bdf8;'
            f'padding:6px 14px;border-radius:4px;font-weight:bold;cursor:pointer;font-size:13px;margin-bottom:16px;">'
            f'📄 Download Stage 0 Report (No signatures)</button></a>',
            unsafe_allow_html=True
        )
        with st.form(key=f"perf_form_{report_id}"):
            perf_remarks = st.text_area(
                "Performer Remarks — Andy Flower",
                placeholder="Enter evaluation observations, defect assessment notes, code reference checks, or site conditions..."
            )
            if st.form_submit_button("✍️ Submit Remarks & Sign Digitally (Stage 1)"):
                if not perf_remarks.strip():
                    st.error("Please enter remarks before submitting.")
                else:
                    with st.spinner("Submitting remarks and applying digital signature..."):
                        try:
                            f_res = requests.post(
                                f"{API_URL}/records/{report_id}/feedback",
                                data={"comments": perf_remarks, "role": "performer"}
                            )
                            if f_res.status_code == 200:
                                st.success("Performer remarks submitted. Report digitally signed by Andy Flower.")
                                st.session_state.inspection_results.update(f_res.json())
                                st.rerun()
                            else:
                                st.error(f"Failed to submit: {f_res.text}")
                        except Exception as e:
                            st.error(f"Connection error: {e}")

    # ── Stage 1: Await Supervisor ─────────────────────────────────────────────
    elif status_state == 1:
        st.success("✅ **Stage 1 Complete** — Report signed digitally by Andy Flower (Performer).")
        st.markdown(f"> **Andy Flower's Remarks:** *\"{performer_comments}\"*")
        st.markdown("---")
        st.markdown("#### 🟡 Stage 2 — Supervisor Evaluator Review")
        st.warning(
            "Richard Campbell (PCN Level III) must review the performer-signed report, "
            "add final disposition comments, and approve release to the client."
        )
        st.markdown(
            f'<a href="{API_URL}/static/reports/{report_id}.pdf" target="_blank" style="text-decoration:none;">'
            f'<button style="background-color:#1e293b;color:#f59e0b;border:1px solid #f59e0b;'
            f'padding:6px 14px;border-radius:4px;font-weight:bold;cursor:pointer;font-size:13px;margin-bottom:16px;">'
            f'📄 Download Stage 1 Report (Performer Signed)</button></a>',
            unsafe_allow_html=True
        )
        with st.form(key=f"super_form_{report_id}"):
            super_remarks = st.text_area(
                "Supervisor Evaluator Comments — Richard Campbell",
                placeholder="Enter final disposition review, engineering standard validation notes, approval or exception remarks..."
            )
            if st.form_submit_button("🚀 Approve & Release to Client (Stage 2)"):
                if not super_remarks.strip():
                    st.error("Please enter supervisor comments before approving.")
                else:
                    with st.spinner("Applying supervisor signature and releasing report..."):
                        try:
                            f_res = requests.post(
                                f"{API_URL}/records/{report_id}/feedback",
                                data={"comments": super_remarks, "role": "supervisor"}
                            )
                            if f_res.status_code == 200:
                                st.success("Report approved and digitally signed by Richard Campbell. Released to client.")
                                st.session_state.inspection_results.update(f_res.json())
                                st.rerun()
                            else:
                                st.error(f"Failed to approve: {f_res.text}")
                        except Exception as e:
                            st.error(f"Connection error: {e}")

    # ── Stage 2: Workflow complete ────────────────────────────────────────────
    elif status_state == 2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0f2d1e,#1e293b);border:1px solid #22c55e;
             border-radius:8px;padding:24px;text-align:center;margin-bottom:20px;">
            <h3 style="color:#22c55e;margin:0;">🌟 HITL Workflow Complete</h3>
            <p style="color:#94a3b8;margin:8px 0 0 0;">Report fully reviewed, dual-signed, and released to client.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**✍️ Andy Flower (Performer) Remarks:** *\"{performer_comments}\"*")
        st.markdown(f"**✅ Richard Campbell (Supervisor) Remarks:** *\"{supervisor_comments}\"*")
        st.markdown(
            f'<a href="{API_URL}/static/reports/{report_id}.pdf" target="_blank" style="text-decoration:none;">'
            f'<button style="background-color:#22c55e;color:#0f1115;border:none;padding:10px 20px;'
            f'border-radius:4px;font-weight:bold;cursor:pointer;font-size:14px;">'
            f'📄 Download Final Dual-Signed Report</button></a>',
            unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DATABASE EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Inspection History Database")

    col_ctrl1, _ = st.columns([1, 4])
    refresh    = col_ctrl1.button("🔄 Refresh Logs",   type="secondary")
    clear_logs = col_ctrl1.button("🗑️ Clear Database", type="secondary")

    if clear_logs:
        try:
            clear_res = requests.post(f"{API_URL}/records/clear")
            if clear_res.status_code == 200:
                st.success("Database logs cleared.")
            else:
                st.error("Failed to clear database logs.")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

    try:
        res = requests.get(f"{API_URL}/records")
        if res.status_code == 200:
            records = res.json().get("records", [])
            if not records:
                st.info("No inspection records found in the database.")
            else:
                st.write(f"Showing {len(records)} recent records:")
                for r in records:
                    timestamp              = r.get("timestamp",            "N/A")
                    verdict                = r.get("verdict",              "UNKNOWN")
                    rec_id                 = r.get("id",                   "N/A")
                    report_id              = r.get("report_id",            "N/A")
                    image_id               = r.get("image_id",             "N/A")
                    thick                  = r.get("thickness",            "N/A")
                    model                  = r.get("model_used",           "N/A")
                    details                = r.get("details",              "")
                    annotated_image_path   = r.get("annotated_image_path")
                    db_status_state        = r.get("status_state",         0)
                    db_performer_comments  = r.get("performer_comments",   "")
                    db_supervisor_comments = r.get("supervisor_comments",  "")

                    status_emoji = "✅" if "PASS" in verdict.upper() else "❌"

                    with st.expander(f"{status_emoji} Report: {report_id}  |  {timestamp}  |  {verdict}"):
                        st.markdown(f"**Image:** `{image_id}`  |  **DB ID:** `{rec_id}`")
                        st.markdown(f"**Thickness:** `{thick} mm`  |  **Model:** `{model}`")
                        st.markdown(
                            f'<div style="margin-bottom:12px;">'
                            f'<a href="{API_URL}/static/reports/{report_id}.pdf" target="_blank" style="text-decoration:none;">'
                            f'<button style="background-color:#1e293b;color:#38bdf8;border:1px solid #38bdf8;'
                            f'padding:6px 12px;border-radius:4px;font-weight:bold;cursor:pointer;font-size:13px;">'
                            f'📄 Download PDF Copy</button></a></div>',
                            unsafe_allow_html=True
                        )

                        if annotated_image_path:
                            st.image(
                                f"{API_URL}/static/{annotated_image_path}",
                                caption=f"Stored Visual Mapping ({report_id})",
                                use_container_width=True
                            )

                        st.markdown("**Agent Reasoning Details & Report:**")
                        st.text(details)

                        # Approval status in Database Explorer
                        st.markdown("---")
                        st.markdown("##### 🛠️ Approval Status")

                        if db_status_state == 0:
                            st.info("🕒 **Stage 1: Awaiting Performer Review** — Use the **✍️ Human Review & Approval** tab.")

                        elif db_status_state == 1:
                            st.success("✅ **Stage 1 Complete** — Signed by Andy Flower.")
                            st.markdown(f"**Performer Remarks:** *\"{db_performer_comments}\"*")
                            st.warning("🕒 **Stage 2: Awaiting Supervisor Approval**")
                            with st.form(key=f"db_super_form_{report_id}_{rec_id}"):
                                super_remarks = st.text_area(
                                    "Supervisor Comments (Richard Campbell)",
                                    key=f"db_super_rmk_{report_id}_{rec_id}"
                                )
                                if st.form_submit_button("🚀 Approve & Release to Client"):
                                    if not super_remarks.strip():
                                        st.error("Please enter comments.")
                                    else:
                                        f_res = requests.post(
                                            f"{API_URL}/records/{report_id}/feedback",
                                            data={"comments": super_remarks, "role": "supervisor"}
                                        )
                                        if f_res.status_code == 200:
                                            st.success("Approved. Please refresh logs.")
                                            st.rerun()
                                        else:
                                            st.error("Failed to approve.")

                        elif db_status_state == 2:
                            st.success("🌟 **Workflow Complete** — Dual-signed & released to client.")
                            st.markdown(f"**Performer:** *\"{db_performer_comments}\"*")
                            st.markdown(f"**Supervisor:** *\"{db_supervisor_comments}\"*")
        else:
            st.error(f"Failed to fetch records. API returned code {res.status_code}")
    except Exception as e:
        st.error(f"Could not load database logs: {e}")


# ==========================================
# TAB 4 — UIPATH MAESTRO BPMN PROCESS SIMULATOR
# ==========================================
with tab4:
    import time
    st.subheader("🤖 UiPath Maestro BPMN Process Orchestration")
    st.markdown("""
    This dashboard simulates how **UiPath Maestro** acts as the single enterprise control plane to orchestrate
    AI agents, human decision points, and robot integrations in a structured BPMN 2.0 flow.
    """)
    
    # Refresh processes list
    try:
        proc_res = requests.get(f"{API_URL}/api/uipath/bpmn/processes")
        if proc_res.status_code == 200:
            processes = proc_res.json().get("processes", [])
        else:
            processes = []
            st.error("Failed to load BPMN processes from backend.")
    except Exception as e:
        processes = []
        st.error(f"Could not connect to backend API: {e}")
        
    # Start a new process section
    with st.expander("🆕 Start New Weld Inspection Process (BPMN Trigger)", expanded=(not processes)):
        sp_col1, sp_col2 = st.columns([1, 1])
        with sp_col1:
            bpmn_file = st.file_uploader(
                "Upload Weld Radiography Scan",
                type=["jpg", "png", "tiff", "jpeg"],
                key="bpmn_file"
            )
        with sp_col2:
            st.markdown("##### Configuration Variables")
            bpmn_thickness = st.number_input("Wall Thickness (mm)", min_value=1.0, value=10.0, step=0.5, key="bpmn_thick")
            bpmn_code = st.selectbox("Regulatory Standard Code", options=code_options, key="bpmn_code")
            bpmn_material = st.selectbox("Base Material", options=["Carbon Steel", "Stainless Steel", "Aluminum", "Other"], key="bpmn_mat")
            bpmn_usage = st.selectbox("Functional Intent", options=["Fabrication", "Design", "Inspection"], key="bpmn_usage")
            
        if bpmn_file:
            if st.button("🚀 Trigger BPMN Process Start Event", type="primary"):
                with st.spinner("Starting process instance..."):
                    try:
                        files = {"file": (bpmn_file.name, bpmn_file.getvalue(), bpmn_file.type)}
                        data = {
                            "thickness": bpmn_thickness,
                            "model_path": model_path,
                            "regulatory_code": bpmn_code,
                            "material": bpmn_material,
                            "app_type": app_type,
                            "client_spec": client_spec,
                            "other_standard": other_standard,
                            "usage": bpmn_usage,
                            "process_name": "Weld_Quality_Maestro"
                        }
                        start_res = requests.post(f"{API_URL}/api/uipath/bpmn/processes", files=files, data=data)
                        if start_res.status_code == 200:
                            res_json = start_res.json()
                            proc_id = res_json.get("process_id")
                            st.session_state.active_bpmn_id = proc_id
                            st.success(f"BPMN Process Started: {proc_id}")
                            st.rerun()
                        else:
                            st.error("Failed to start process.")
                    except Exception as e:
                        st.error(f"Error starting process: {e}")
                        
    if processes:
        st.markdown("---")
        # Process Selector
        proc_options = [p["process_id"] for p in processes]
        if "active_bpmn_id" not in st.session_state or st.session_state.active_bpmn_id not in proc_options:
            st.session_state.active_bpmn_id = proc_options[-1]
            
        selected_proc_id = st.selectbox(
            "🔎 Select Running Process Instance:",
            options=proc_options,
            index=proc_options.index(st.session_state.active_bpmn_id)
        )
        st.session_state.active_bpmn_id = selected_proc_id
        
        # Get details of the active process
        active_proc = next(p for p in processes if p["process_id"] == selected_proc_id)
        current_task = active_proc["current_task"]
        status = active_proc["status"]
        history = active_proc["history"]
        vars = active_proc["variables"]
        defects = active_proc["defects"]
        agent_reasoning = active_proc["agent_reasoning"]
        
        # Visual Stepper for BPMN Tasks
        st.markdown("#### 📐 BPMN 2.0 Process Map & Active Task Highlight")
        
        # Define tasks and status mapping for visual stepper
        task_nodes = [
            ("Start", "Start Event", "🟢"),
            ("AI Inspection", "AI Scan (Service Task)", "🤖"),
            ("Human Review", "Inspector (User Task)", "🕵️‍♂️"),
            ("Repair Planning", "Repair Planner (Service Task)", "🧠"),
            ("Welder Rework", "Welder Repair (User Task)", "🛠️"),
            ("Exporting Report", "Export Certificate (Service)", "📄"),
            ("End Event", "End Event", "🏁")
        ]
        
        stepper_cols = st.columns(len(task_nodes))
        for idx, (node_id, node_label, emoji) in enumerate(task_nodes):
            is_active = (current_task == node_id)
            is_done = False
            
            # Simple check if node is completed
            node_order = [n[0] for n in task_nodes]
            active_idx = node_order.index(current_task)
            current_idx = node_order.index(node_id)
            
            # Exception routing handles loops, so let's check by status
            if status == "Completed":
                is_done = True
            elif current_idx < active_idx:
                is_done = True
                
            # Custom styling for status cards
            if is_active:
                border_color = "#f59e0b" if node_id in ["Human Review", "Welder Rework"] else "#38bdf8"
                bg_color = "linear-gradient(135deg, #1e3a8a, #0f172a)"
                text_color = "#38bdf8"
                glow = "box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);"
            elif is_done:
                border_color = "#22c55e"
                bg_color = "#0f2d1e"
                text_color = "#22c55e"
                glow = ""
            else:
                border_color = "#475569"
                bg_color = "#1e293b"
                text_color = "#94a3b8"
                glow = ""
                
            card_html = f"""
            <div style="text-align:center; padding:12px 6px; background:{bg_color}; 
                 border: 1px solid {border_color}; border-radius: 8px; min-height: 90px; {glow}">
                <div style="font-size: 20px; margin-bottom:4px;">{emoji}</div>
                <div style="font-size: 11px; font-weight: bold; color:{text_color}; line-height: 1.2;">{node_label}</div>
            </div>
            """
            stepper_cols[idx].markdown(card_html, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Details & Simulation Control
        sc_col1, sc_col2 = st.columns([3, 2])
        
        with sc_col1:
            st.markdown(f"#### 🎭 Current Actor Assigned: " + (
                "**RPA Robot** (System)" if current_task in ["Start", "Exporting Report"]
                else "**Coding Agent** (Gemini)" if current_task in ["AI Inspection"]
                else "**Repair Planning Agent** (Gemini)" if current_task in ["Repair Planning"]
                else "**ASNT Level III NDT Inspector** (Human)" if current_task == "Human Review"
                else f"**Welder: {active_proc.get('selected_welder', {}).get('name', 'Marcus Vance')}** (Human)" if current_task == "Welder Rework"
                else "**Completed / Process Terminated**"
            ))
            
            # --- TASK INTERFACE PANELS ---
            if current_task == "AI Inspection":
                st.info("🤖 **Active Task: AI Inspection & Standard Code Evaluation**")
                st.markdown("""
                The process has received the radiograph film and is awaiting the automated inspection task. 
                In a production run, the **UiPath Robot** starts a background thread that enhances the image, 
                passes it to our fine-tuned RT-DETR model, and validates compliance against standard rules.
                """)
                if st.button("🤖 Trigger AI Agent Service Task Execution", type="primary"):
                    with st.spinner("AI Agent executing inspection and ASME compliance checks..."):
                        try:
                            step_res = requests.post(f"{API_URL}/api/uipath/bpmn/processes/{selected_proc_id}/step")
                            if step_res.status_code == 200:
                                st.success("AI Service Task Completed!")
                                st.rerun()
                            else:
                                st.error("Failed to run step.")
                        except Exception as e:
                            st.error(f"Error stepping process: {e}")
                            
            elif current_task == "Human Review":
                st.warning("🕵️‍♂️ **Active Task: Level III NDT Inspector Compliance Review**")
                st.markdown("""
                **UiPath Action Center Simulation**: Since the AI pipeline identified defects or marked the weld compliance as fail, 
                Maestro BPMN created an exception task. The process has paused and generated a task form in the Action Center.
                """)
                
                # Show annotated image
                report_id = vars["report_id"]
                st.image(f"{API_URL}/static/annotated/{report_id}.jpg", caption="Radiograph with AI Bounding Boxes (ASME Evaluation Failure)", use_container_width=True)
                st.markdown("**AI Agent Reasoning Summary:**")
                st.info(agent_reasoning)
                
                # Decision Form
                with st.form(key=f"action_form_{selected_proc_id}"):
                    inspector_comments = st.text_area("Audit Comments", placeholder="Enter review remarks (e.g. approve deviation, or explain repair requirements)...")
                    col_b1, col_b2 = st.columns(2)
                    approve_btn = col_b1.form_submit_button("✅ Approve Weld (Override & Release)")
                    reject_btn = col_b2.form_submit_button("❌ Reject Weld (Order Repair)")
                    
                    if approve_btn:
                        if not inspector_comments.strip():
                            st.error("Please add audit comments for approval override.")
                        else:
                            requests.post(f"{API_URL}/api/uipath/bpmn/processes/{selected_proc_id}/action", json={
                                "decision": "Approve",
                                "comments": inspector_comments
                            })
                            st.success("Weld manual override submitted.")
                            st.rerun()
                    if reject_btn:
                        if not inspector_comments.strip():
                            st.error("Please add audit comments explaining the weld rejection.")
                        else:
                            requests.post(f"{API_URL}/api/uipath/bpmn/processes/{selected_proc_id}/action", json={
                                "decision": "Reject",
                                "comments": inspector_comments
                            })
                            st.error("Weld rejected. Transitioning to Repair Planning.")
                            st.rerun()
                            
            elif current_task == "Repair Planning":
                st.info("🧠 **Active Task: Agentic Repair Planning Service Task**")
                st.markdown("""
                The weld was rejected. The **Maestro BPMN** process now triggers the **Agentic Repair Planning Service Task**.
                The Repair Agent will:
                1. Analyze defect coordinates and material parameters.
                2. Search the certified technicians database.
                3. Design a step-by-step grinding and welding Action Plan.
                """)
                if st.button("🧠 Trigger Repair Agent Execution", type="primary"):
                    with st.spinner("Repair Planning Agent matching welder and drafting procedure..."):
                        try:
                            step_res = requests.post(f"{API_URL}/api/uipath/bpmn/processes/{selected_proc_id}/step")
                            if step_res.status_code == 200:
                                st.success("Repair Action Plan Generated!")
                                st.rerun()
                            else:
                                st.error("Failed to execute repair planner.")
                        except Exception as e:
                            st.error(f"Error stepping process: {e}")
                            
            elif current_task == "Welder Rework":
                st.warning("🛠️ **Active Task: Welder Repair & Radiography Re-Scan**")
                st.markdown("""
                **Welder Workspace Task**: The assigned welding technician has received the repair work order and instructions.
                """)
                
                # Display Assigned Welder Card
                welder = active_proc.get("selected_welder", {})
                st.markdown(f"""
                <div style="background:#1e293b;border:1px solid #f59e0b;padding:15px;border-radius:6px;margin-bottom:15px;">
                    <span style="font-size:24px;float:left;margin-right:12px;">👨‍🏭</span>
                    <b style="color:#f59e0b;font-size:15px;">Assigned Welding Specialist</b><br>
                    Name: <b>{welder.get('name', 'N/A')}</b> (ID: {welder.get('id', 'N/A')})<br>
                    <small style="color:#94a3b8;">Reasoning: {welder.get('reasoning', 'Matched on certification standards')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Display Repair Plan Markdown
                st.markdown("**🔧 Custom Repair Action Plan:**")
                st.markdown(active_proc.get("repair_plan", "No plan available."))
                
                st.markdown("---")
                # Rework Upload
                st.markdown("##### Upload Repaired Weld Radiography Film (Re-Inspection)")
                rework_file = st.file_uploader("Upload Repaired Weld Scan", type=["jpg", "png", "tiff", "jpeg"], key="rework_file")
                rework_comments = st.text_area("Rework Notes", placeholder="Enter welder comments (e.g. grinded porosity, rewelded GTAW, visual check clean)...")
                
                if rework_file:
                    if st.button("🛠️ Submit Repaired Weld for Re-Audit", type="primary"):
                        with st.spinner("Uploading repair film..."):
                            try:
                                files = {"file": (rework_file.name, rework_file.getvalue(), rework_file.type)}
                                data = {"comments": rework_comments}
                                rework_res = requests.post(f"{API_URL}/api/uipath/bpmn/processes/{selected_proc_id}/rework", files=files, data=data)
                                if rework_res.status_code == 200:
                                    st.success("Repaired weld submitted! Process loops back to AI Ingestion.")
                                    st.rerun()
                                else:
                                    st.error("Failed to submit rework.")
                            except Exception as e:
                                st.error(f"Error submitting rework: {e}")
                                
            elif current_task == "Exporting Report":
                st.info("📄 **Active Task: Certificate Export & Database Sync**")
                st.markdown("""
                The weld inspection has successfully passed (or was manually overridden). 
                The background process now runs the final service task:
                1. Compiles the final signed PDF Compliance Certificate.
                2. Syncs the audit results with MongoDB Atlas.
                3. Updates the enterprise system (local SQLite).
                """)
                if st.button("📄 Generate and Publish Inspection Certificate", type="primary"):
                    with st.spinner("Generating certificate and saving to database adapters..."):
                        try:
                            step_res = requests.post(f"{API_URL}/api/uipath/bpmn/processes/{selected_proc_id}/step")
                            if step_res.status_code == 200:
                                st.success("Certificate generated and process completed!")
                                st.rerun()
                            else:
                                st.error("Failed to step process.")
                        except Exception as e:
                            st.error(f"Error stepping process: {e}")
                            
            elif current_task == "End Event":
                st.markdown("""
                <div style="background:#0f2d1e;border:1px solid #22c55e;border-radius:8px;padding:20px;text-align:center;">
                    <h4 style="color:#22c55e;margin:0;">🏁 Process Completed Successfully</h4>
                    <p style="color:#94a3b8;margin:8px 0 0 0;">The BPMN process has terminated at the End Event. The weld is verified compliant.</p>
                </div>
                """, unsafe_allow_html=True)
                report_id = vars["report_id"]
                st.markdown(
                    f'<div style="text-align:center;margin-top:15px;">'
                    f'<a href="{API_URL}/static/reports/{report_id}.pdf" target="_blank" style="text-decoration:none;">'
                    f'<button style="background-color:#22c55e;color:#0f1115;border:none;padding:10px 20px;border-radius:4px;font-weight:bold;cursor:pointer;font-size:14px;">📄 Download Published Certificate</button>'
                    f'</a></div>',
                    unsafe_allow_html=True
                )
                
        with sc_col2:
            st.markdown("#### ⚡ UiPath REST API Logs")
            st.markdown("""
            Showcasing simulated REST API interactions sent to/received from the UiPath Orchestrator:
            """)
            
            # API Calls log simulator
            api_logs = []
            if current_task == "AI Inspection":
                api_logs = [
                    "POST /api/OrchestratorData/Queues/AddQueueItem HTTP/1.1",
                    "Host: cloud.uipath.com",
                    "Authorization: Bearer mock-oauth-token",
                    "Content-Type: application/json",
                    "",
                    "{",
                    '  "itemData": {',
                    f'    "QueueName": "Weld_Scan_Queue",',
                    f'    "Reference": "{selected_proc_id}",',
                    '    "SpecificContent": {',
                    f'      "raw_image_path": "{vars["raw_image_path"]}",',
                    f'      "thickness": {vars["thickness"]}',
                    '    }',
                    '  }',
                    "}",
                    "--------------------------------------------------",
                    "Response: 201 Created",
                    "QueueItem ID: qi-10928374"
                ]
            elif current_task == "Human Review":
                api_logs = [
                    "POST /api/Tasks/CreateFormTask HTTP/1.1",
                    "Host: cloud.uipath.com",
                    "Authorization: Bearer mock-oauth-token",
                    "Content-Type: application/json",
                    "",
                    "{",
                    '  "task": {',
                    f'    "Title": "Weld Defect Compliance Audit",',
                    '    "Type": "FormTask",',
                    f'    "Data": "{{\\"process_id\\":\\"{selected_proc_id}\\",\\"defects\\":{len(defects)}}}"',
                    '  }',
                    "}",
                    "--------------------------------------------------",
                    "Response: 201 Created",
                    f"Task ID: {active_proc.get('task_id', 'TSK-REVIEW-1092')}",
                    "",
                    "Status Check: GET /odata/Tasks Status=Unassigned"
                ]
            elif current_task == "Repair Planning":
                api_logs = [
                    "POST /odata/Jobs/StartJobs HTTP/1.1",
                    "Host: cloud.uipath.com",
                    "Authorization: Bearer mock-oauth-token",
                    "",
                    "{",
                    '  "startInfo": {',
                    '    "ReleaseKey": "Repair_Planner_Agent_Key",',
                    f'    "InputArguments": "{{\\"process_id\\":\\"{selected_proc_id}\\"}}"',
                    '  }',
                    "}",
                    "--------------------------------------------------",
                    "Response: 201 Created",
                    "Job ID: job-49273"
                ]
            elif current_task == "Welder Rework":
                api_logs = [
                    "POST /api/Tasks/CreateFormTask HTTP/1.1",
                    "Host: cloud.uipath.com",
                    "Authorization: Bearer mock-oauth-token",
                    "",
                    "{",
                    '  "task": {',
                    f'    "Title": "Welder Rework Order - {active_proc.get("selected_welder", {}).get("name", "Marcus")}",',
                    '    "Type": "FormTask",',
                    f'    "Data": "{{\\"selected_welder_id\\":\\"{active_proc.get("selected_welder", {}).get("id", "")}\\"}}"',
                    '  }',
                    "}",
                    "--------------------------------------------------",
                    "Response: 201 Created",
                    "Task ID: TSK-WELDER-9082",
                    "",
                    "Status Check: GET /odata/Tasks Status=AwaitingInput"
                ]
            elif current_task == "Exporting Report":
                api_logs = [
                    "POST /odata/QueueItems(qi-10928374)/SetTransactionResult HTTP/1.1",
                    "Host: cloud.uipath.com",
                    "Authorization: Bearer mock-oauth-token",
                    "",
                    "{",
                    '  "transactionResult": {',
                    '    "Status": "Successful",',
                    f'    "OutputArguments": "{{\\"verdict\\":\\"PASS\\",\\"report_id\\":\\"{vars["report_id"]}\\"}}"',
                    '  }',
                    "}",
                    "--------------------------------------------------",
                    "Response: 200 OK"
                ]
            else:
                api_logs = ["No active API calls. Process completed or idle."]
                
            log_text = "\n".join(api_logs)
            st.markdown(f"""
            <pre style="background:#0f172a; color:#10b981; border:1px solid #1e293b; 
                 padding:10px; border-radius:6px; font-family:Courier, monospace; font-size:11px; max-height:220px; overflow-y:auto;">
{log_text}
            </pre>
            """, unsafe_allow_html=True)
            
        # History Logs section
        st.markdown("---")
        with st.expander("📜 BPMN Audit Trail & History Log"):
            st.markdown("Immutable event log tracking handoffs between Coding Agents, RPA, and Inspectors:")
            for event in reversed(history):
                actor_badge = (
                    "🟢 Robot" if event["actor"] == "RPA Robot"
                    else "🔵 Agent" if event["actor"] in ["Coding Agent", "Repair Agent"]
                    else "🕵️‍♂️ Inspector" if event["actor"] == "Level III NDT Inspector"
                    else "🛠️ Welder"
                )
                st.markdown(f"**{event['timestamp']}** | `{actor_badge}` : {event['event']}")

