import streamlit as st
import sys

# Safe import wrapper with premium environment diagnostics
try:
    from src.preprocessing.processor import WeldProcessor
    from src.rule_engine.engine import WeldEngine
    from src.detection.detector import WeldDetector
    from src.detection.hf_detector import HFWeldDetector
except ModuleNotFoundError as e:
    st.error(f"### 🛑 Environment Configuration Error\n\n"
             f"**Failed to import core modules:** `{e}`\n\n"
             f"This usually happens because Streamlit cannot locate the project directory in your Python path.\n\n"
             f"**How to Fix:**\n"
             f"Please run the app from the root of the project with the `PYTHONPATH` set:\n"
             f"```bash\n"
             f"export PYTHONPATH=$(pwd)\n"
             f"streamlit run main.py\n"
             f"```")
    sys.exit(1)

import cv2
import datetime

def charter_page():
    st.title("Project Charter & Methodology")
    st.markdown("""
### 🚀 Introduction & Project Charter
This application is a Computer Vision-driven diagnostic tool designed specifically for **Non-Destructive Testing (NDT)** in the Oil & Gas, Power, and Manufacturing industries. 

The primary charter of this project is to automate the interpretation of digital radiography (RT) images, rapidly identifying and quantifying critical welding defects (such as porosity, inclusions, and cracks). By combining deep learning with codified engineering standards, this tool aims to reduce human error in X-ray interpretation and accelerate the "Review-to-Repair" cycle for critical assets.

### 🔬 Methodology
Our pipeline operates on a modular, multi-phase approach:

1. **Phase 1: Pre-processing & Enhancement**
   We apply Contrast Limited Adaptive Histogram Equalization (CLAHE) to enhance low-contrast radiographic films, ensuring that micro-defects are visible to the AI engine.

2. **Phase 2: AI Detection & Inference**
   The core engine utilizes state-of-the-art instance segmentation models. Trained on thousands of annotated radiographic images compiled from **various public NDT data sources**, the AI isolates defects with polygon-level precision. It acts as a purely objective "measuring tool," identifying what exists and its exact pixel dimensions.

3. **Phase 3: Engineering Rule Validation**
   Instead of relying solely on AI confidence, the system passes the detected dimensions through a deterministic Rule Engine. This engine cross-references the measurements against strict international engineering codes and standards (such as **ASME B31.3** and **ASME Section VIII**). Furthermore, because Oil and Gas clients often have their own stringent internal standards and proprietary project specifications that govern the acceptability of weld joints, this application includes a built-in provision to securely customize and tune the rule engine to fully comply with those bespoke client specifications alongside the baseline international codes. This ensures the final "Accept" or "Reject" disposition matches real-world operational requirements.

4. **Phase 4: Automated Report Generation**
   Upon completion of the analysis, the system automatically generates comprehensive **Radiographic Examination Reports** in both **PDF** and **Word (.docx)** formats. A critical feature of this phase is the "Human-in-the-Loop" provision: before finalization, NDE Level II/III human experts can manually modify the AI-annotated image, adjusting bounding boxes, overriding classifications, or adding custom observations. 

   The generated report follows a standardized industry format (anonymized template below) containing the project metadata, technical exposure parameters, and a joint-by-joint breakdown of observations and disposition results.

### 📄 Sample Radiographic Examination Report Template
*(Dummy data populated for demonstration purposes)*

**Header Information**
*   **Examination Date:** 15-08-2026 | **Report No:** RT-SAMPLE-001 | **Rev:** 0
*   **Project Name:** [Confidential Pipeline Expansion]
*   **Acceptance Criteria:** ASME B31.3 ED-2024 Table 341.3.2-1 (Normal and Category M fluid services)

**Technical Parameters**
| Parameter | Detail | Parameter | Detail |
| :--- | :--- | :--- | :--- |
| **Component Description** | Carbon Steel Pipe Spool | **Source Type & Size** | Ir-192 & 3.0x3.0mm |
| **Material Type** | ASTM A106 Grade B | **IQI Type & Placement** | ASTM 1B & Film Side |
| **Thickness + Reinf.** | 9.53 mm + 2.0 mm | **IQI Wire Required** | 6th Wire |
| **Diameter / Length** | 12" | **IQI Wire Achieved** | 6th Wire |
| **Welding Process** | GTAW / SMAW | **Film Brand & Type** | AGFA D4 (Class-I) |

**Inspection Results Log**
| Sr. No. | Line No. / Spool No. | Joint No. | Welder ID | Location (cm) | Film Size (cm) | Observations (cm) | Results |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| 01 | PL-100-SP-10 | J-01 | W-055 | 0-30 | 10x40 | NSD | Accept |
| | | | | 30-60 | 10x40 | NSD | Accept |
| | | | | 60-0 | 10x40 | P @ 65-66 | Accept |
| 02 | PL-100-SP-11 | J-02 | W-012 | 0-30 | 10x40 | NSD | Accept |
| | | | | 30-60 | 10x40 | LF @ 40-45 | Reject |
| | | | | 60-0 | 10x40 | NSD | Accept |

**Common Abbreviations Legend:**
`NSD`: No Significant Discontinuity | `P`: Porosity | `LF`: Lack of Fusion | `LP`: Lack of Penetration | `SI`: Slag Inclusion | `UC`: Undercut | `C`: Crack | `EP`: Excess Penetration | `BT`: Burn Through

### 🛠️ Technologies & Libraries Used
The architecture is built upon a modern, open-source AI and data science stack:

*   **Frontend UI:** Streamlit
*   **Computer Vision (Image Processing):** OpenCV (`cv2`)
*   **AI Architectures:**
    *   Hugging Face `transformers` (RT-DETR ResNet-50)
    *   Ultralytics YOLO (Segmentation)
*   **Deep Learning Backend:** PyTorch (`torch`, `torchvision`)
*   **Data Formatting:** COCO JSON & YOLO formats
""")

def analyzer_page():
    st.title("Automated Weld Radiography Analyzer")
    
    # Sidebar Configuration (Simplified for Clean Demo Mode)
    st.sidebar.header("📋 Inspection Settings")
    category = st.sidebar.selectbox("Equipment Category", ["Process Piping", "Pressure Vessel", "Structural"])
    thickness = st.sidebar.number_input("Wall Thickness (mm)", min_value=0.1, value=10.0, step=0.1)
    
    # RT Exposure Parameters commented out to avoid distraction for client demo
    # with st.sidebar.expander("🎥 RT Exposure Parameters (ASME V)", expanded=False):
    #     weld_id = st.text_input("Weld ID / Tag", value="SPOOL-08-J70")
    #     welder_id = st.text_input("Welder ID", value="W-010")
    #     wps_no = st.text_input("WPS Number", value="CESML-WPS-010")
    #     material_type = st.selectbox("Material Type", ["S.S 316L", "Carbon Steel", "Alloy Steel"], index=0)
    #     welding_process = st.selectbox("Welding Process", ["GTAW", "SMAW", "GMAW"], index=0)
    #     st.markdown("---")
    #     st.markdown("**Geometric Unsharpness ($U_g$) Settings:**")
    #     focal_spot_size = st.number_input("Source Focal Spot (F) mm", min_value=0.1, value=3.0, step=0.1)
    #     sfd = st.number_input("SFD (Source to Film) mm", min_value=1.0, value=406.0, step=10.0)
    #     ofd = st.number_input("OFD (Object to Film) mm", min_value=1.0, value=60.0, step=1.0)

    # Defaults for background processing in clean demo mode
    weld_id = "SPOOL-08"
    welder_id = "W-010"
    focal_spot_size = 3.0
    sfd = 406.0
    ofd = 60.0

    # Model Selection
    st.sidebar.markdown("---")
    st.sidebar.header("🤖 AI Model Configuration")
    model_option = st.sidebar.selectbox(
        "Active Model",
        [
            "Hugging Face DETR (rf-detr-segmentation)",
            "Gazpromneft NDT Specialist (m60.pt)",
            "General Foundation Model (yolo11x)",
            "Standard COCO Placeholder (yolov8n)",
            "Ultralytics RT-DETR (rtdetr-l)"
        ]
    )
    
    # Map model option to path
    model_paths = {
        "Hugging Face DETR (rf-detr-segmentation)": "Roboflow/rf-detr-segmentation",
        "Gazpromneft NDT Specialist (m60.pt)": "weights/gazpromneft_kaggle/m60.pt",
        "General Foundation Model (yolo11x)": "weights/welding_defects_yolo11x.pt",
        "Standard COCO Placeholder (yolov8n)": "weights/yolov8n.pt",
        "Ultralytics RT-DETR (rtdetr-l)": "weights/rtdetr-l.pt"
    }
    selected_model_path = model_paths[model_option]
    
    # Mapping Categories to Standards
    std_map = {"Process Piping": "ASME_B31.3", "Pressure Vessel": "ASME_SEC_VIII"}
    engine = WeldEngine(standard=std_map.get(category, "ASME_B31.3"))
    processor = WeldProcessor()

    uploaded_file = st.file_uploader("Upload Radiography Image", type=['jpg', 'png', 'tiff'])

    if uploaded_file:
        # Save locally for processing (required for Phase 1)
        with open(f"data/raw/{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 1. Enhancement & IQI Check (Phase 1)
        enhanced_img = processor.enhance_image(f"data/raw/{uploaded_file.name}")
        st.image(enhanced_img, caption="CLAHE Enhanced Image")
        
        # ASME V Calculations
        sod = sfd - ofd
        geometric_unsharpness = (focal_spot_size * ofd) / sod if sod > 0 else 0
        ug_limit = 0.51  # ASME V limit for T <= 50.8mm (2")
        is_ug_compliant = geometric_unsharpness <= ug_limit
        
        is_iqi_valid, wires = processor.verify_iqi(enhanced_img)
        
        # Display ASME V Image Quality Board (Commented out for clean demo mode)
        # st.subheader("📋 ASME V Radiography Quality Verification")
        # col1, col2 = st.columns(2)
        # with col1:
        #     iqi_status = "✅ COMPLIANT" if is_iqi_valid else "❌ NON-COMPLIANT"
        #     st.markdown(f"**ASME V IQI Wire Verification**\n"
        #                 f"- IQI Required: **6th Wire**\n"
        #                 f"- IQI Achieved: **{wires} Wires**\n"
        #                 f"- Status: **{iqi_status}**")
        # with col2:
        #     ug_status = "✅ COMPLIANT" if is_ug_compliant else "❌ NON-COMPLIANT"
        #     st.markdown(f"**ASME V Geometric Unsharpness ($U_g$)**\n"
        #                 f"- Formula: $U_g = (F \\times OFD) / SOD$\n"
        #                 f"- Calculated $U_g$: **{geometric_unsharpness:.3f} mm**\n"
        #                 f"- Legal Limit: **{ug_limit:.2f} mm**\n"
        #                 f"- Status: **{ug_status}**")
            
        # is_film_compliant = is_iqi_valid and is_ug_compliant
        # if is_film_compliant:
        #     st.success("🎉 **ASME V Radiography Compliance Passed: Film is fully compliant and valid for inspection.**")
        # else:
        #     st.warning("⚠️ **ASME V Image Quality Alert: Radiography film does not meet sensitivity or unsharpness standards.**")

        if is_iqi_valid:
            # Multi-Agent Workflow Execution
            st.subheader("🤖 Multi-Agent Analysis (Band Framework)")
            
            with st.spinner("Initializing Band Network Agents..."):
                from src.agents.band_network import band_client
                from src.agents.inspector_agent import InspectorAgent
                from src.agents.compliance_agent import ComplianceAgent
                from src.agents.reviewer_agent import ReviewerAgent
                
                inspector = InspectorAgent(model_option, selected_model_path)
                compliance = ComplianceAgent()
                reviewer = ReviewerAgent()
                
            with st.spinner("🕵️‍♂️ Inspector Agent analyzing radiography..."):
                # Trigger Agent 1
                inspector.inspect(enhanced_img)
                insp_payload = band_client.wait_for("inspection_complete")
                
            with st.spinner("📐 Compliance Agent validating against ASME codes..."):
                # Agent 2 listens to Agent 1
                compliance.evaluate(insp_payload, thickness)
                comp_payload = band_client.wait_for("compliance_verdict")
                
            with st.spinner("⚖️ Reviewer Agent managing risk & reporting..."):
                # Agent 3 listens to Agent 2
                reviewer.final_review(comp_payload)
                final_payload = band_client.wait_for("report_ready")
            
            # Rendering final results
            disposition_color = "green" if final_payload['passed'] else "red"
            st.success(f"**Multi-Agent Workflow Complete!** Final Status: :{disposition_color}[{final_payload['final_status']}]")
            
            st.markdown("### 📝 Senior Reviewer Summary")
            if final_payload['passed']:
                st.success(final_payload['llm_summary'])
            else:
                st.error(final_payload['llm_summary'])
                
            if final_payload.get('report_path'):
                st.info(f"📄 Official Report Generated: `{final_payload['report_path']}`")
            
            st.subheader("📸 AI Inspection Visual Output")
            annotated_img = cv2.cvtColor(enhanced_img, cv2.COLOR_GRAY2BGR)
            
            # Draw on Image (Visualization)
            if not final_payload['defects']:
                h, w, _ = annotated_img.shape
                cv2.rectangle(annotated_img, (0, 0), (w - 1, h - 1), (0, 255, 0), 4)
                cv2.putText(annotated_img, "COMPLIANT / CLEAR", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            else:
                for d in final_payload['defects']:
                    x1, y1, x2, y2 = map(int, d['bbox'])
                    box_color = (0, 255, 0) if final_payload['passed'] else (0, 0, 255)
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), box_color, 2)
                    cv2.putText(annotated_img, d['type'], (x1, y1-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                                
            st.image(annotated_img, caption="Multi-Agent Defect Mapping", channels="BGR")
            
            # Expandable audit logs
            if final_payload['defects']:
                st.markdown("### 🔍 Technical Audits & Coordinates")
                for item_idx, d in enumerate(final_payload['defects'], 1):
                    with st.expander(f"Item {item_idx}: {d['type']} (Conf: {d['confidence']:.2f})"):
                        st.write(f"**Bounding Box (xyxy):** `{d['bbox']}`")
                        st.write(f"**ASME Code Validation:** {final_payload['reason']}")

        else:
            st.error(f"Insufficient Sensitivity: Only {wires} IQI wires detected. Stop.")


def main():
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Go to", ["Project Charter", "Weld Analyzer"])
    
    if page == "Project Charter":
        charter_page()
    else:
        analyzer_page()

if __name__ == "__main__":
    main()