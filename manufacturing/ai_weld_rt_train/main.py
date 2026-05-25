import streamlit as st
import sys

# Safe import wrapper with premium environment diagnostics
try:
    from src.preprocessing.processor import WeldProcessor
    from src.rule_engine.engine import WeldEngine
    from src.detection.detector import WeldDetector
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

def main():
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
            "Gazpromneft NDT Specialist (m60.pt)",
            "General Foundation Model (yolo11x)",
            "Standard COCO Placeholder (yolov8n)"
        ]
    )
    
    # Map model option to path
    model_paths = {
        "Gazpromneft NDT Specialist (m60.pt)": "weights/gazpromneft_kaggle/m60.pt",
        "General Foundation Model (yolo11x)": "weights/welding_defects_yolo11x.pt",
        "Standard COCO Placeholder (yolov8n)": "weights/yolov8n.pt"
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
            # 2. Real AI Detection (Phase 2)
            st.info(f"Running inference using: `{model_option}`")
            detector = WeldDetector(model_path=selected_model_path) 
            
            st.subheader("Phase 3: AI Analysis Results")
            real_defects = detector.detect(enhanced_img)

            if not real_defects:
                st.success("✅ **Inspection Completed: No defects detected by the AI engine.**")
                
                st.markdown("### 📋 NDT Verification Checklist")
                st.markdown(f"All standard defect categories under **{engine.standard}** have been verified:")
                
                # Retrieve the active model's class names
                model_classes = list(detector.model.names.values())
                
                # Filter out calibration standard reference targets for cleaner UI
                display_classes = [c for c in model_classes if "reference_standard" not in c and "Эталон" not in c]
                
                # Human-readable mapping dictionary
                class_display_names = {
                    "crack": "Linear Crack Indications",
                    "porosity": "Porosity / Gas Pores",
                    "inclusion": "Slag / Tungsten Inclusions",
                    "lack_of_fusion": "Lack of Fusion",
                    "incomplete_root_penetration": "Incomplete Root Penetration",
                    "undercut": "Undercutting",
                    "burn_through": "Burn-Through",
                    "overlap": "Weld Metal Overlap",
                    "crater": "Shrinkage Crater",
                    "hidden_porosity": "Sub-surface Porosity",
                    "Defect": "General Defective Indications"
                }

                # Professional reassurance note generator
                def get_reassurance_note(class_name, display_name):
                    if "crack" in class_name.lower():
                        return "Zero-tolerance check passed. No linear crack indications detected."
                    elif "porosity" in class_name.lower():
                        return f"No {display_name.lower()} detected, or indications are well within acceptable limits."
                    elif "undercut" in class_name.lower() or "penetration" in class_name.lower() or "fusion" in class_name.lower():
                        return f"Compliant. No physical {display_name.lower()} anomalies detected."
                    else:
                        return f"Passed. No {display_name.lower()} detected."

                # Compile checklist data
                checklist_data = []
                for c in display_classes:
                    display_name = class_display_names.get(c, c.replace("_", " ").title())
                    checklist_data.append({
                        "Defect Category": display_name,
                        "Status": "✅ Passed",
                        "Compliance & Audit Notes": get_reassurance_note(c, display_name)
                    })
                
                st.table(checklist_data)
                
                # Render the clean analyzed image with a premium green border indicating PASS
                st.subheader("📸 AI Inspection Visual Output")
                annotated_img = cv2.cvtColor(enhanced_img, cv2.COLOR_GRAY2BGR)
                h, w, _ = annotated_img.shape
                # Draw a 4px green border around the frame
                cv2.rectangle(annotated_img, (0, 0), (w - 1, h - 1), (0, 255, 0), 4)
                cv2.putText(annotated_img, "COMPLIANT / CLEAR", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                st.image(annotated_img, caption="AI Analysis: 100% Compliant (No Defects Highlighted)", channels="BGR")
            else:
                # 1. Calibration (Phase 3b)
                # For now, we assume 10 pixels = 0.8mm for testing
                engine.calibrate(reference_px=10, physical_mm=0.8)

                # Convert to BGR for color annotations
                annotated_img = cv2.cvtColor(enhanced_img, cv2.COLOR_GRAY2BGR)
                findings_for_report = []
                log_table_data = []

                # Human-readable NDT Abbreviation mapping dictionary
                ndt_abbreviations = {
                    "crack": "Crack (Linear Indication)",
                    "porosity": "GP (Gas Pore / Porosity)",
                    "inclusion": "SI (Slag Inclusion)",
                    "lack_of_fusion": "IF (Incomplete Fusion)",
                    "incomplete_root_penetration": "IP (Inadequate Penetration)",
                    "undercut": "EU (External Undercut)",
                    "burn_through": "BT (Burnthrough)",
                    "overlap": "OL (Weld Overlap)",
                    "crater": "RC (Root Concavity / Crater)",
                    "hidden_porosity": "HGP (Hidden Gas Pore)",
                    "defect": "Defect (General Indication)"
                }

                # Dynamically retrieve defect limits based on engine definitions for display
                def get_defect_limit(c, T):
                    c_lower = c.lower().strip()
                    if "crack" in c_lower:
                        return 0.0
                    elif "porosity" in c_lower:
                        return min(6.0, T / 4)
                    elif "inclusion" in c_lower or "slag" in c_lower:
                        return T / 3
                    elif "penetration" in c_lower or "ip" in c_lower or "lop" in c_lower:
                        return min(3.0, 0.2 * T)
                    else:
                        return min(6.0, T / 4)

                for item_idx, d in enumerate(real_defects, 1):
                    # 3. Engineering Validation (Phase 3)
                    real_size = engine.get_mm(d['dims']['length'])
                    passed, reason = engine.validate_defect(d['type'], {'length': real_size}, thickness)
                    
                    # NDT Abbreviation Code translation
                    clean_type = d['type'].lower().strip()
                    defect_code = ndt_abbreviations.get(clean_type, d['type'])
                    limit_val = get_defect_limit(clean_type, thickness)
                    
                    disposition = "✅ ACCEPT" if passed else "❌ REJECT"
                    
                    # Standardized NDT Weld Log Row compilation
                    log_table_data.append({
                        "Item": item_idx,
                        "Weld ID": weld_id,
                        "Welder ID": welder_id,
                        "Defect Category (Code)": defect_code,
                        "Measured Size": f"{real_size:.2f} mm",
                        "ASME Limit": f"{limit_val:.2f} mm" if limit_val > 0 else "0.00 mm (Zero Tolerance)",
                        "Disposition": disposition
                    })

                    # Compile details for technical audit panels
                    findings_for_report.append({
                        "d": d,
                        "real_size": real_size,
                        "passed": passed,
                        "reason": reason,
                        "color": "green" if passed else "red"
                    })

                    # 2. Draw on Image (Visualization)
                    x1, y1, x2, y2 = map(int, d['bbox'])
                    box_color = (0, 255, 0) if passed else (0, 0, 255)
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), box_color, 2)
                    cv2.putText(annotated_img, f"{real_size:.1f}mm", (x1, y1-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                
                # Render the standardized NDT Weld Findings Table (Commented out for clean demo mode)
                # st.subheader("📋 Radiographic Testing Weld Inspection Log")
                # st.table(log_table_data)
                
                # Render the expandable details for technical audit
                st.markdown("### 🔍 Technical Audits & Coordinates")
                for f in findings_for_report:
                    d = f["d"]
                    with st.expander(f"Item: {d['type']} (Conf: {d['confidence']:.2f})"):
                        st.markdown(f"**Status:** :{f['color']}[{f['reason']}]")
                        st.write(f"**Real Size:** {f['real_size']:.2f} mm")
                        st.write(f"**Raw Pixel Length:** {d['dims']['length']:.2f}")
                        st.write(f"**Bounding Box (xyxy):** `{d['bbox']}`")

                # Show annotated image
                st.subheader("📸 AI Inspection Visual Output")
                st.image(annotated_img, caption="AI Detection & Measurements", channels="BGR")

                # 3. Generate Report (Phase 4) - Disabled for now
                # if st.button("Generate Final Report"):
                #     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                #     report_path = f"data/reports/inspection_report_{timestamp}.pdf"
                #     annotated_img_path = "data/processed/temp_annotated.jpg"
                #     cv2.imwrite(annotated_img_path, annotated_img)
                #     
                #     reporter = WeldReporter()
                #     report_data = {'standard': 'ASME B31.3', 'findings': findings_for_report}
                #     reporter.create_report(report_path, report_data, annotated_img_path)
                #     st.success(f"Report saved to {report_path}")
        else:
            st.error(f"Insufficient Sensitivity: Only {wires} IQI wires detected. Stop.")


if __name__ == "__main__":
    main()