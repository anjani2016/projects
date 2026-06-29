import os
import pytest
import sqlite3
from src.infrastructure.adapters.mongo_adapter import MongoAdapter
from src.core.domain.entities import InspectionRecord

@pytest.fixture
def temp_db_path(tmp_path):
    # Returns a temporary path for the SQLite database
    db_file = tmp_path / "test_ndt.db"
    return str(db_file)

def test_sqlite_fallback_on_placeholder(temp_db_path):
    # Arrange: Initialize adapter with the placeholder MongoDB URI
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    
    # Assert: It should automatically set use_sqlite to True
    assert adapter.use_sqlite is True
    assert os.path.exists(temp_db_path)

def test_sqlite_save_and_retrieve(temp_db_path):
    # Arrange: Initialize adapter and create a dummy record
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    
    record1 = InspectionRecord(
        image_id="weld_image_001.png",
        thickness=10.5,
        model_used="weights/rtdetr-l.pt",
        verdict="PASS",
        details="No significant discontinuities found.",
        timestamp="2026-06-06T12:00:00Z"
    )
    
    record2 = InspectionRecord(
        image_id="weld_image_002.png",
        thickness=8.0,
        model_used="weights/rtdetr-l.pt",
        verdict="REJECT",
        details="Defect: Porosity found.",
        timestamp="2026-06-06T12:05:00Z"
    )
    
    # Act: Save records
    msg1 = adapter.save_record(record1)
    msg2 = adapter.save_record(record2)
    
    # Assert messages
    assert "local SQLite database" in msg1
    assert "local SQLite database" in msg2
    
    # Act: Retrieve records
    records = adapter.get_records()
    
    # Assert list order (timestamp descending: record2 then record1)
    assert len(records) == 2
    assert records[0].image_id == "weld_image_002.png"
    assert records[0].verdict == "REJECT"
    assert records[0].id == "2"
    
    assert records[1].image_id == "weld_image_001.png"
    assert records[1].verdict == "PASS"
    assert records[1].id == "1"

def test_sqlite_clear_records(temp_db_path):
    # Arrange: Initialize adapter and insert records
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    
    record = InspectionRecord(
        image_id="test.png",
        thickness=12.0,
        model_used="test_model",
        verdict="PASS",
        details="Clean"
    )
    
    adapter.save_record(record)
    assert len(adapter.get_records()) == 1
    
    # Act: Clear database
    adapter.clear_records()
    
    # Assert: Empty
    assert len(adapter.get_records()) == 0

def test_sqlite_generate_report_id(temp_db_path):
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    
    # Generate first ID for today
    id1 = adapter.generate_report_id()
    assert id1.startswith("REP-")
    assert id1.endswith("-001")
    
    # Save a record
    record = InspectionRecord(
        image_id="img.png",
        thickness=10.0,
        model_used="model",
        verdict="PASS",
        details="details",
        report_id=id1
    )
    adapter.save_record(record)
    
    # Generate second ID for today
    id2 = adapter.generate_report_id()
    assert id2.endswith("-002")

def test_sqlite_get_record_by_report_id(temp_db_path):
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    
    # Save a record
    record = InspectionRecord(
        image_id="img_test_id.png",
        thickness=10.0,
        model_used="model",
        verdict="PASS",
        details="detailed info",
        report_id="REP-TEST-ID-001"
    )
    adapter.save_record(record)
    
    # Retrieve
    retrieved = adapter.get_record_by_report_id("REP-TEST-ID-001")
    assert retrieved is not None
    assert retrieved.image_id == "img_test_id.png"
    assert retrieved.details == "detailed info"
    
    # Non-existent
    assert adapter.get_record_by_report_id("REP-NONEXISTENT") is None

def test_sqlite_technician_feedback(temp_db_path):
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    feedback = {
        "report_id": "REP-20260606-001",
        "technician_id": "TECH-01",
        "original_verdict": "PASS",
        "corrected_verdict": "REJECT",
        "comments": "Slag inclusion missed by detector."
    }
    
    # Save feedback
    fid = adapter.save_feedback(feedback)
    assert fid != ""
    
    # Retrieve feedback
    feedbacks = adapter.get_feedback()
    assert len(feedbacks) == 1
    assert feedbacks[0]["report_id"] == "REP-20260606-001"
    assert feedbacks[0]["corrected_verdict"] == "REJECT"

def test_sqlite_vision_cache(temp_db_path):
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    image_hash = "abc123hash"
    detections = {
        "boxes": [[10, 20, 100, 200]],
        "scores": [0.95],
        "classes": ["porosity"]
    }
    
    # Save cache
    hid = adapter.save_vision_cache(image_hash, detections)
    assert hid == image_hash
    
    # Fetch cache
    cached = adapter.get_vision_cache(image_hash)
    assert cached is not None
    assert cached["image_hash"] == image_hash
    assert cached["detections"]["classes"][0] == "porosity"

def test_sqlite_audit_logs(temp_db_path):
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    event = {
        "user_id": "AUDITOR-07",
        "action": "DOWNLOAD_REPORT",
        "details": "Downloaded REP-20260606-001 PDF report."
    }
    
    # Log event
    aid = adapter.log_audit_event(event)
    assert aid != ""
    
    # Fetch audit logs
    logs = adapter.get_audit_logs()
    assert len(logs) == 1
    assert logs[0]["user_id"] == "AUDITOR-07"
    assert logs[0]["action"] == "DOWNLOAD_REPORT"

def test_sqlite_compliance_standards(temp_db_path):
    adapter = MongoAdapter(connection_string="mcp://mongodb.partner.local", sqlite_path=temp_db_path)
    standard = {
        "standard_id": "ASME-B31.3",
        "name": "Process Piping Quality Specs",
        "rules": {
            "max_porosity_size": 1.5,
            "undercut_limit": 0.5
        }
    }
    
    # Save compliance standard
    sid = adapter.save_compliance_standard(standard)
    assert sid == "ASME-B31.3"
    
    # Retrieve standard
    retrieved = adapter.get_compliance_standard("ASME-B31.3")
    assert retrieved is not None
    assert retrieved["name"] == "Process Piping Quality Specs"
    assert retrieved["rules"]["max_porosity_size"] == 1.5
