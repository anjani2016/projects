from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import cv2
import base64
import logging
import hashlib
from dotenv import load_dotenv

from src.core.use_cases.inspection_orchestrator import InspectionOrchestrator
from src.infrastructure.adapters.ultralytics_adapter import UltralyticsAdapter
from src.infrastructure.adapters.mongo_adapter import MongoAdapter
from src.infrastructure.adapters.local_compliance_adapter import LocalComplianceAdapter
from src.preprocessing.processor import WeldProcessor

from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI(title="AI Weld Inspector Backend", version="1.0.0")

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create raw/annotated storage directories
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/inspections/annotated", exist_ok=True)

# Mount static folder to serve files (images) to frontend
app.mount("/static", StaticFiles(directory="data/inspections"), name="static")

@app.post("/inspect")
async def inspect_weld(
    file: UploadFile = File(...),
    thickness: float = Form(...),
    model_path: str = Form(...),
    gemini_api_key: str = Form(None),
    x_user_role: str = Header("Inspector"),
    app_type: str = Form("Piping"),
    material: str = Form("Carbon Steel"),
    regulatory_code: str = Form("ASME B31.3"),
    client_spec: str = Form("None"),
    other_standard: str = Form("None"),
    usage: str = Form("Fabrication")
):
    """
    Receives an image and inspection parameters, runs the AI multi-agent orchestrator,
    and returns the verdict, text output, and base64-encoded annotated image.
    """
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        
    mcp_url = os.environ.get("MONGODB_URI", "")
    db_adapter = MongoAdapter(mcp_url)
    
    # Compute SHA-256 image hash
    file.file.seek(0)
    file_bytes = file.file.read()
    file.file.seek(0)
    image_hash = hashlib.sha256(file_bytes).hexdigest()
    
    # Log Audit Event
    db_adapter.log_audit_event({
        "user_id": x_user_role,
        "action": "RUN_INSPECTION",
        "details": f"User '{x_user_role}' ran inspection for thickness {thickness}mm using model {model_path} (Code: {regulatory_code}, Material: {material}, App: {app_type}, Usage: {usage}, Client Spec: {client_spec}, Other Standard: {other_standard}, Image hash: {image_hash})"
    })
    
    # Generate unique report ID
    report_id = db_adapter.generate_report_id()
    
    raw_storage_path = f"data/raw/{report_id}.jpg"
    annotated_storage_path = f"data/inspections/annotated/{report_id}.jpg"
    
    # Save the uploaded file directly to our raw storage path
    with open(raw_storage_path, "wb") as buffer:
        buffer.write(file_bytes)
        
    try:
        # 2. Enhance the uploaded image using WeldProcessor on the backend
        processor = WeldProcessor()
        enhanced_img = processor.enhance_image(raw_storage_path)
        # Overwrite the raw storage file with the enhanced version so agent reads it
        cv2.imwrite(raw_storage_path, enhanced_img)
        
        # 3. Instantiate Adapters and Core Orchestrator (Injecting DB for caching & standards)
        vision_adapter = UltralyticsAdapter(model_path, db_adapter)
        compliance_adapter = LocalComplianceAdapter(db_adapter)
        
        orchestrator = InspectionOrchestrator(vision_adapter, db_adapter, compliance_adapter)
        
        # 4. Set report properties for the database save lifecycle inside agent tools
        orchestrator.report_id = report_id
        orchestrator.raw_image_path = f"raw/{report_id}.jpg"
        orchestrator.annotated_image_path = f"annotated/{report_id}.jpg"
        
        # 5. Run the agent workflow
        agent_output = await orchestrator.run(
            raw_storage_path, 
            model_path, 
            thickness, 
            image_hash=image_hash,
            app_type=app_type,
            material=material,
            regulatory_code=regulatory_code,
            client_spec=client_spec,
            other_standard=other_standard,
            usage=usage
        )
        
        # 6. Detect defects to build annotations (leveraging vision cache)
        defects = vision_adapter.detect(enhanced_img, image_hash=image_hash)
        
        # Check if agent_output is empty or indicates a rate-limit/API-key/quota error
        is_error = (
            not agent_output or 
            "Error during agent execution" in agent_output or 
            "credits are depleted" in agent_output or 
            "request failed" in agent_output
        )
        
        if is_error:
            # Run deterministic WeldEngine as a fallback
            from src.rule_engine.engine import WeldEngine
            engine = WeldEngine(standard="ASME_B31.3")
            engine.calibrate(reference_px=10, physical_mm=1.0) # assume 1px = 0.1mm
            
            weld_verdict = "PASS"
            defect_details = []
            
            for idx, d in enumerate(defects):
                mm_len = d.dims.get("length", 0.0) * 0.1
                passed, reason = engine.validate_defect(d.type, {"length": mm_len}, thickness)
                if not passed:
                    weld_verdict = "REJECT"
                defect_details.append(
                    f"{idx+1}. Type: {d.type}, Confidence: {d.confidence:.2f}, Length: {mm_len:.2f}mm, Status: {reason}"
                )
            
            defect_list_str = "\n".join(defect_details) if defect_details else "No defects detected."
            
            if weld_verdict == "PASS" and not defects:
                status_str = f"STATUS: PASS No defects were detected in the weld radiography image. Therefore, the weld complies with {regulatory_code} standards."
            else:
                status_str = f"STATUS: {weld_verdict}"

            agent_output = (
                f"{status_str}\n\n"
                f"⚠️ **FALLBACK COMPLIANCE REPORT**\n"
                f"(Google AI Studio Gemini API is offline or out of credits. Running deterministic local rules engine fallback.)\n\n"
                f"Evaluation details against standard '{regulatory_code}':\n"
                f"- Pipe Thickness: {thickness}mm\n"
                f"- Total Defects Detected: {len(defects)}\n\n"
                f"Defect Log:\n{defect_list_str}\n\n"
                f"Verification Completed."
            )
            
            # Save fallback record to database since the agent couldn't
            from src.core.domain.entities import InspectionRecord
            record = InspectionRecord(
                report_id=report_id,
                image_id=raw_storage_path,
                thickness=thickness,
                model_used=model_path,
                verdict=weld_verdict,
                details=agent_output,
                raw_image_path=f"raw/{report_id}.jpg",
                annotated_image_path=f"annotated/{report_id}.jpg",
                performer_comments="",
                supervisor_comments="",
                status_state=0,
                material=material,
                regulatory_code=regulatory_code,
                client_spec=client_spec,
                other_standard=other_standard,
                app_type=app_type,
                usage=usage
            )
            db_adapter.save_record(record)
        
        # 7. Draw bounding boxes on enhanced image
        annotated_img = cv2.cvtColor(enhanced_img, cv2.COLOR_GRAY2BGR)
        is_passed = "STATUS: PASS" in agent_output
        box_color = (0, 255, 0) if is_passed else (0, 0, 255)
        
        for d in defects:
            x1, y1, x2, y2 = map(int, d.bbox)
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(annotated_img, d.type, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            
        # 8. Save the annotated image to disk for static serving
        cv2.imwrite(annotated_storage_path, annotated_img)
            
        # 9. Generate and save the PDF report to disk
        try:
            from src.reporting.reporter import WeldReporter
            pdf_dir = "data/inspections/reports"
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = f"{pdf_dir}/{report_id}.pdf"
            
            findings = []
            for d in defects:
                mm_len = d.dims.get("length", 0.0) * 0.1
                status = "Accept"
                d_type_lower = d.type.lower()
                if d_type_lower in ["crack", "lack_of_fusion", "lack of fusion"]:
                    status = "Reject"
                elif d_type_lower in ["porosity", "pora", "hidden_porosity", "pora-skrytaya"]:
                    if mm_len > (thickness * 0.333):
                        status = "Reject"
                elif d_type_lower in ["inclusion", "vkljuchenie"]:
                    if mm_len > (thickness * 0.5):
                        status = "Reject"
                
                findings.append({
                    "type": str(d.type).encode('latin-1', 'replace').decode('latin-1'),
                    "size_mm": mm_len,
                    "status": status
                })
            
            report_data = {
                "report_id": report_id,
                "thickness": thickness,
                "material": str(material).encode('latin-1', 'replace').decode('latin-1'),
                "regulatory_code": str(regulatory_code).encode('latin-1', 'replace').decode('latin-1'),
                "client_spec": str(client_spec).encode('latin-1', 'replace').decode('latin-1'),
                "other_standard": str(other_standard).encode('latin-1', 'replace').decode('latin-1'),
                "app_type": str(app_type).encode('latin-1', 'replace').decode('latin-1'),
                "usage": str(usage).encode('latin-1', 'replace').decode('latin-1'),
                "findings": findings,
                "agent_reasoning": agent_output,
                "performer_comments": "",
                "supervisor_comments": "",
                "status_state": 0
            }
            
            reporter = WeldReporter()
            reporter.create_report(pdf_path, report_data, annotated_storage_path)
            logging.info(f"Generated PDF report for {report_id} at {pdf_path}")
        except Exception as pdf_err:
            logging.error(f"Failed to generate PDF report for {report_id}: {pdf_err}")
            
        # 10. Ensure the report is saved to the database (MongoDB/SQLite fallback)
        try:
            record_check = db_adapter.get_record_by_report_id(report_id)
            if not record_check:
                logging.info(f"Report {report_id} was not saved by the agent. Saving manually to database.")
                from src.core.domain.entities import InspectionRecord
                record = InspectionRecord(
                    report_id=report_id,
                    image_id=raw_storage_path,
                    thickness=thickness,
                    model_used=model_path,
                    verdict="PASS" if "STATUS: PASS" in agent_output else "REJECT",
                    details=agent_output,
                    raw_image_path=f"raw/{report_id}.jpg",
                    annotated_image_path=f"annotated/{report_id}.jpg",
                    performer_comments="",
                    supervisor_comments="",
                    status_state=0,
                    material=material,
                    regulatory_code=regulatory_code,
                    client_spec=client_spec,
                    other_standard=other_standard,
                    app_type=app_type,
                    usage=usage
                )
                db_adapter.save_record(record)
        except Exception as db_save_err:
            logging.error(f"Failed to ensure record saving in database: {db_save_err}")

        # Convert annotated image to base64
        _, img_buffer = cv2.imencode('.jpg', annotated_img)
        img_b64 = base64.b64encode(img_buffer).decode('utf-8')
        
        return {
            "status": "success",
            "report_id": report_id,
            "result": agent_output,
            "annotated_image": img_b64,
            "defects": [d.model_dump() for d in defects]
        }
    except Exception as e:
        logging.error(f"Error during inspection endpoint run: {e}")
        # Cleanup incomplete raw image if it exists and run failed
        if os.path.exists(raw_storage_path):
            os.remove(raw_storage_path)
        return {"status": "error", "result": str(e)}

@app.get("/license")
async def get_license():
    """
    Returns the MIT License text for open-source compliance.
    """
    try:
        with open("LICENSE", "r") as f:
            return {"license": f.read()}
    except Exception:
        return {"license": "MIT License\n\nCopyright (c) 2026 Anjani D / Centauri Research Services\n\nPermission is hereby granted..."}

@app.get("/records")
async def get_records(x_user_role: str = Header("Inspector")):
    """
    Fetches all saved NDT reports from the database adapter.
    """
    mcp_url = os.environ.get("MONGODB_URI", "")
    try:
        db_adapter = MongoAdapter(mcp_url)
        # Log Audit event
        db_adapter.log_audit_event({
            "user_id": x_user_role,
            "action": "FETCH_RECORDS",
            "details": f"User '{x_user_role}' fetched historical weld reports."
        })
        records = db_adapter.get_records()
        return {"status": "success", "records": [r.model_dump() for r in records]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/records/clear")
async def clear_records(x_user_role: str = Header("Inspector")):
    """
    Clears all saved NDT reports from the database.
    Only users with Auditor or Admin roles are permitted to perform this action.
    """
    # RBAC authorization gate
    if x_user_role not in ["Admin", "Auditor"]:
        mcp_url = os.environ.get("MONGODB_URI", "")
        db_adapter = MongoAdapter(mcp_url)
        db_adapter.log_audit_event({
            "user_id": x_user_role,
            "action": "UNAUTHORIZED_CLEAR_ATTEMPT",
            "details": f"User '{x_user_role}' attempted to clear database records but was denied access."
        })
        raise HTTPException(status_code=403, detail="Role unauthorized to perform this operation.")

    mcp_url = os.environ.get("MONGODB_URI", "")
    try:
        db_adapter = MongoAdapter(mcp_url)
        # Log Audit event
        db_adapter.log_audit_event({
            "user_id": x_user_role,
            "action": "CLEAR_RECORDS",
            "details": f"User '{x_user_role}' cleared all database reports and files."
        })
        db_adapter.clear_records()
        return {"status": "success", "message": "All records cleared successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/records/{report_id}/feedback")
async def submit_feedback(
    report_id: str,
    comments: str = Form(...),
    role: str = Form(...), # "performer" or "supervisor"
    x_user_role: str = Header("Inspector")
):
    """
    Submits performer remarks or supervisor review, updates workflow state,
    and regenerates the signed PDF report dynamically.
    """
    mcp_url = os.environ.get("MONGODB_URI", "")
    db_adapter = MongoAdapter(mcp_url)
    
    # 1. Fetch record from database
    record = db_adapter.get_record_by_report_id(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inspection record not found.")
        
    # 2. Update comments and status state
    if role.lower() == "performer":
        record.performer_comments = comments
        record.status_state = 1
    elif role.lower() == "supervisor":
        record.supervisor_comments = comments
        record.status_state = 2
    else:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'performer' or 'supervisor'.")
        
    # 3. Save updated record back to DB
    db_adapter.update_record(record)
    
    # Log Audit Event
    db_adapter.log_audit_event({
        "user_id": x_user_role,
        "action": "SUBMIT_FEEDBACK",
        "details": f"User '{x_user_role}' submitted {role} comments for report {report_id} (State: {record.status_state})"
    })
    
    # 4. Regenerate the PDF report
    try:
        from src.reporting.reporter import WeldReporter
        pdf_dir = "data/inspections/reports"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = f"{pdf_dir}/{report_id}.pdf"
        
        # Load image to re-detect (hitting cache)
        raw_storage_path = f"data/{record.raw_image_path}"
        if not os.path.exists(raw_storage_path):
            raw_storage_path = f"data/inspections/{record.raw_image_path}"
        annotated_storage_path = f"data/inspections/{record.annotated_image_path}"
        
        if os.path.exists(raw_storage_path):
            img_np = cv2.imread(raw_storage_path, cv2.IMREAD_GRAYSCALE)
            with open(raw_storage_path, "rb") as f:
                file_bytes = f.read()
            img_hash = hashlib.sha256(file_bytes).hexdigest()
            
            from src.infrastructure.adapters.ultralytics_adapter import UltralyticsAdapter
            vision_adapter = UltralyticsAdapter(record.model_used, db_adapter)
            defects = vision_adapter.detect(img_np, image_hash=img_hash)
        else:
            defects = []
            
        findings = []
        for d in defects:
            mm_len = d.dims.get("length", 0.0) * 0.1
            status = "Accept"
            d_type_lower = d.type.lower()
            if d_type_lower in ["crack", "lack_of_fusion", "lack of fusion"]:
                status = "Reject"
            elif d_type_lower in ["porosity", "pora", "hidden_porosity", "pora-skrytaya"]:
                if mm_len > (record.thickness * 0.333):
                    status = "Reject"
            elif d_type_lower in ["inclusion", "vkljuchenie"]:
                if mm_len > (record.thickness * 0.5):
                    status = "Reject"
            
            findings.append({
                "type": str(d.type).encode('latin-1', 'replace').decode('latin-1'),
                "size_mm": mm_len,
                "status": status
            })
            
        report_data = {
            "report_id": record.report_id,
            "thickness": record.thickness,
            "material": str(record.material).encode('latin-1', 'replace').decode('latin-1'),
            "regulatory_code": str(record.regulatory_code).encode('latin-1', 'replace').decode('latin-1'),
            "client_spec": str(record.client_spec).encode('latin-1', 'replace').decode('latin-1'),
            "other_standard": str(record.other_standard).encode('latin-1', 'replace').decode('latin-1'),
            "app_type": str(record.app_type).encode('latin-1', 'replace').decode('latin-1'),
            "usage": str(record.usage).encode('latin-1', 'replace').decode('latin-1'),
            "findings": findings,
            "agent_reasoning": record.details,
            "performer_comments": record.performer_comments,
            "supervisor_comments": record.supervisor_comments,
            "status_state": record.status_state
        }
        
        reporter = WeldReporter()
        reporter.create_report(pdf_path, report_data, annotated_storage_path)
        logging.info(f"Regenerated PDF report for {report_id} at {pdf_path}")
    except Exception as pdf_err:
        logging.error(f"Failed to regenerate PDF report for {report_id}: {pdf_err}")
        return {"status": "error", "message": f"Failed to regenerate PDF: {str(pdf_err)}"}
        
    return {
        "status": "success",
        "report_id": report_id,
        "status_state": record.status_state,
        "performer_comments": record.performer_comments,
        "supervisor_comments": record.supervisor_comments
    }


