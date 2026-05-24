import streamlit as st
from src.processor import WeldProcessor
from src.engine import WeldEngine
from src.detector import WeldDetector
import cv2
# from src.reporter import WeldReporter
import datetime

def main():
    st.title("Automated Weld Radiography Analyzer")
    
    # Sidebar Configuration
    st.sidebar.header("Inspection Settings")
    category = st.sidebar.selectbox("Equipment Category", ["Process Piping", "Pressure Vessel", "Structural"])
    thickness = st.sidebar.number_input("Wall Thickness (mm)", min_value=1.0, value=10.0)
    
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
        is_valid, wires = processor.verify_iqi(enhanced_img)

        if is_valid:
            st.success(f"IQI Validated: {wires} wires detected.")

            # 2. Real AI Detection (Phase 2)
            detector = WeldDetector(model_path="yolov8n.pt") 
            
            st.subheader("Phase 3: AI Analysis Results")
            real_defects = detector.detect(enhanced_img)

            if not real_defects:
                st.success("No defects detected by the AI engine.")
            else:
                # 1. Calibration (Phase 3b)
                # For now, we assume 10 pixels = 0.8mm for testing
                engine.calibrate(reference_px=10, physical_mm=0.8)

                # Convert to BGR for color annotations
                annotated_img = cv2.cvtColor(enhanced_img, cv2.COLOR_GRAY2BGR)
                findings_for_report = []

                for d in real_defects:
                    # 3. Engineering Validation (Phase 3)
                    real_size = engine.get_mm(d['dims']['length'])
                    passed, reason = engine.validate_defect(d['type'], {'length': real_size}, thickness)
                    
                    # 4. Display Logic
                    color = "green" if passed else "red"
                    with st.expander(f"Detection: {d['type']} (Conf: {d['confidence']:.2f})"):
                        st.markdown(f"**Status:** :{color}[{reason}]")
                        st.write(f"**Real Size:** {real_size:.2f} mm")
                        st.write(f"**Raw Pixel Length:** {d['dims']['length']:.2f}")

                    # 2. Draw on Image (Visualization)
                    x1, y1, x2, y2 = map(int, d['bbox'])
                    # Green for pass, Red for fail
                    box_color = (0, 255, 0) if passed else (0, 0, 255)
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), box_color, 2)
                    cv2.putText(annotated_img, f"{real_size:.1f}mm", (x1, y1-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                    
                    findings_for_report.append({
                        'type': d['type'],
                        'size_mm': real_size,
                        'status': reason
                    })

                # Show annotated image
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