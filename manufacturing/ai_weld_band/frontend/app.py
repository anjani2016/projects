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

orchestration_mode = st.sidebar.radio(
    "🔄 Orchestration Mode",
    ["Standard Agent Pipeline", "Band Multi-Agent Platform"],
    index=1,
    help="Select whether to use the local single-agent pipeline or coordinate via the Band of Agents platform"
)

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
# THREE-TAB LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🔬 Weld Analysis",
    "✍️ Human Review & Approval",
    "📜 Database Explorer",
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
                        endpoint = "/inspect/band" if orchestration_mode == "Band Multi-Agent Platform" else "/inspect"
                        response = requests.post(f"{API_URL}{endpoint}", files=files, data=data)
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
        if res_json.get("mode") == "band_multi_agent":
            st.markdown("### 🤝 Band.ai Multi-Agent Collaboration Room")
            band_res = res_json.get("band_result", {})
            
            st.markdown("#### 💬 Room Activity Trace")
            
            # Step 1: Orchestrator dispatch
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**Weld Orchestrator Agent** (UUID: `b0c1269c`)  \n"
                            f"Initiated NDT pipeline for image `{uploaded_file.name}` under regulatory standard `{code_selected}`.")
            
            # Step 2: Vision agent
            with st.chat_message("user", avatar="🔬"):
                st.markdown(f"**Weld Vision Agent** (UUID: `f89e3592`)  \n"
                            f"Analyzed radiography image. Found **{len(defects)}** weld defect(s).")
            
            # Step 3: Compliance Agent
            with st.chat_message("assistant", avatar="📜"):
                st.markdown(f"**Weld Compliance Agent** (UUID: `b65bb3b0`)  \n"
                            f"Queried rules database. Acceptance rules for thickness `{thickness} mm` under `{code_selected}` applied.  \n"
                            f"Reasoning: {band_res.get('compliance_reasoning')}")
            
            # Step 4: Review Agent
            with st.chat_message("user", avatar="🛡️"):
                override_text = "⚠️ **SAFETY OVERRIDE APPLIED!** " if band_res.get("override_applied") else "✅ Safety check passed. "
                st.markdown(f"**Weld Review Agent** (UUID: `027c7f2f`)  \n"
                            f"{override_text}{band_res.get('review_notes')}")
            
            # Step 5: Orchestrator wrap-up
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**Weld Orchestrator Agent** (UUID: `b0c1269c`)  \n"
                            f"Inspection run completed. Final Status: **{band_res.get('final_verdict')}**. Logged audit event to MongoDB Atlas.")
        else:
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
