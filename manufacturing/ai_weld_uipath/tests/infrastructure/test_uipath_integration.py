import os
import pytest
import cv2
import numpy as np
from fastapi.testclient import TestClient
from src.api.server import app
from src.infrastructure.adapters.uipath_adapter import UiPathAdapter
from src.core.use_cases.repair_planner import RepairPlanner
from src.core.domain.entities import Defect

client = TestClient(app)

def test_uipath_adapter_mock_mode(monkeypatch):
    """Verify that UiPathAdapter operates correctly in local simulation mode."""
    # Ensure environment variables are clear for mock mode testing
    monkeypatch.delenv("UIPATH_CLIENT_ID", raising=False)
    monkeypatch.delenv("UIPATH_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("UIPATH_ORG_NAME", raising=False)
    monkeypatch.delenv("UIPATH_TENANT_NAME", raising=False)

    adapter = UiPathAdapter()
    assert adapter.is_mock is True
    
    # Test process start simulation
    proc_id = adapter.start_bpmn_process("Weld_NDT_Audit", {"thickness": 10.0})
    assert "sim-proc" in proc_id
    
    # Test task creation simulation
    task_id = adapter.create_user_task("proc-123", "HumanReview", {"reason": "porosity"})
    assert "sim-task" in task_id
    
    # Test task status check
    status = adapter.get_task_status(task_id)
    assert status in ["Unassigned", "Completed", "ReworkRequested"]


def test_repair_planner_deterministic_fallback():
    """Test the RepairPlanner agent fallback matching logic for different materials/standards."""
    planner = RepairPlanner()
    
    fake_defects = [
        {"type": "porosity", "bbox": [10, 20, 30, 40], "dims": {"length": 20}}
    ]
    
    # 1. Stainless Steel -> Welder 2 (Elena Rostova)
    plan = planner.run_deterministic_fallback("Stainless Steel", "ASME B31.3", 10.0, fake_defects)
    assert plan["selected_welder_id"] == "welder-02"
    assert "Elena Rostova" in plan["selected_welder_name"]
    assert "action_plan" in plan
    
    # 2. API 1104 -> Welder 3 (Carlos Mendez)
    plan = planner.run_deterministic_fallback("Carbon Steel", "API 1104", 8.0, fake_defects)
    assert plan["selected_welder_id"] == "welder-03"
    assert "Carlos Mendez" in plan["selected_welder_name"]
    
    # 3. Exotic Alloy Inconel -> Welder 4 (Kenji Sato)
    plan = planner.run_deterministic_fallback("Inconel", "ASME VIII", 15.0, fake_defects)
    assert plan["selected_welder_id"] == "welder-04"
    assert "Kenji Sato" in plan["selected_welder_name"]


@pytest.mark.asyncio
async def test_bpmn_workflow_end_to_end(monkeypatch, tmp_path):
    """Test the entire simulated BPMN process lifecycle from Start Event to End Event."""
    # Ensure temporary folder paths for raw/annotated files during testing
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: None)
    
    # Mock Ultralytics detect to simulate defects on the first run
    defect_detected = True
    def mock_detect(self, image, image_hash=None):
        if defect_detected:
            return [Defect(type="crack", confidence=0.85, bbox=[10, 10, 40, 40], dims={"length": 30.0})]
        return []
        
    from src.infrastructure.adapters.ultralytics_adapter import UltralyticsAdapter
    monkeypatch.setattr(UltralyticsAdapter, "detect", mock_detect)
    
    # Prepare mock upload file bytes
    img = np.zeros((100, 100), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.jpg', img)
    img_bytes = img_encoded.tobytes()
    
    # 1. Start Event: Ingest film and initiate process
    response = client.post(
        "/api/uipath/bpmn/processes",
        files={"file": ("weld.jpg", img_bytes, "image/jpeg")},
        data={
            "thickness": 10.0,
            "model_path": "weights/m60.pt",
            "regulatory_code": "ASME B31.3",
            "material": "Carbon Steel",
            "app_type": "Piping",
            "usage": "Fabrication"
        }
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    process_id = res_json["process_id"]
    
    # 2. Step 1: Execute AI Inspection (Service Task)
    # The scan should fail compliance due to mocked defect and route to Human Review
    step_resp = client.post(f"/api/uipath/bpmn/processes/{process_id}/step")
    assert step_resp.status_code == 200
    proc_state = step_resp.json()
    assert proc_state["current_task"] == "Human Review"
    assert proc_state["status"] == "Awaiting Review"
    assert proc_state["task_id"] is not None
    
    # 3. Action Step: Simulate inspector Rejecting the weld (triggering Rework)
    action_resp = client.post(
        f"/api/uipath/bpmn/processes/{process_id}/action",
        json={"decision": "Reject", "comments": "Cracks detected, please grind and weld."}
    )
    assert action_resp.status_code == 200
    proc_state = action_resp.json()
    assert proc_state["current_task"] == "Repair Planning"
    assert proc_state["status"] == "Awaiting Repair Plan"
    
    # 4. Step 2: Run Agentic Repair Planning (Service Task)
    # Planner agent selects welder and generates step-by-step grinding plan
    step_resp2 = client.post(f"/api/uipath/bpmn/processes/{process_id}/step")
    assert step_resp2.status_code == 200
    proc_state = step_resp2.json()
    assert proc_state["current_task"] == "Welder Rework"
    assert proc_state["status"] == "In Rework"
    assert proc_state["selected_welder"]["id"] == "welder-01"  # Marcus Vance for Carbon Steel
    assert "Repair Action Plan" in proc_state["repair_plan"]
    
    # 5. Rework Step: Welder uploads repaired weld scan
    # Toggle mock defect state so the second scan passes compliance
    defect_detected = False
    rework_resp = client.post(
        f"/api/uipath/bpmn/processes/{process_id}/rework",
        files={"file": ("repaired_weld.jpg", img_bytes, "image/jpeg")},
        data={"comments": "Defect grinded out, weld repaired with GTAW root."}
    )
    assert rework_resp.status_code == 200
    proc_state = rework_resp.json()
    assert proc_state["current_task"] == "AI Inspection"
    assert proc_state["status"] == "Running"
    
    # 6. Step 3: Run AI Inspection again
    # This time the scan is clean and routes to Report Export
    step_resp3 = client.post(f"/api/uipath/bpmn/processes/{process_id}/step")
    assert step_resp3.status_code == 200
    proc_state = step_resp3.json()
    assert proc_state["current_task"] == "Exporting Report"
    assert proc_state["status"] == "Awaiting Export"
    
    # 7. Step 4: Run Export Report Service Task (Saves to DB and generates PDF)
    step_resp4 = client.post(f"/api/uipath/bpmn/processes/{process_id}/step")
    assert step_resp4.status_code == 200
    proc_state = step_resp4.json()
    assert proc_state["current_task"] == "End Event"
    assert proc_state["status"] == "Completed"
