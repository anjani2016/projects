from fastapi.testclient import TestClient
import os
import pytest
from src.api.server import app
from src.infrastructure.adapters.mongo_adapter import MongoAdapter

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db(tmp_path, monkeypatch):
    # Force the app to use a temporary SQLite file for testing
    db_file = tmp_path / "test_api_ndt.db"
    monkeypatch.setenv("MONGODB_URI", "mcp://mongodb.partner.local")
    
    original_init = MongoAdapter.__init__
    def patched_init(self, connection_string, sqlite_path=None):
        original_init(self, connection_string, sqlite_path=str(db_file))
        
    monkeypatch.setattr(MongoAdapter, "__init__", patched_init)
    
    # Clear records before and after each test
    adapter = MongoAdapter("mcp://mongodb.partner.local", sqlite_path=str(db_file))
    adapter.clear_records()
    yield
    adapter.clear_records()

def test_api_rbac_gating():
    # Attempt to clear records with Inspector role (should fail)
    response = client.post("/records/clear", headers={"x-user-role": "Inspector"})
    assert response.status_code == 403
    assert "Role unauthorized" in response.json()["detail"]
    
    # Attempt to clear records with Admin role (should succeed)
    response = client.post("/records/clear", headers={"x-user-role": "Admin"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_api_audit_trail_logging():
    # Run fetch records
    response = client.get("/records", headers={"x-user-role": "Inspector"})
    assert response.status_code == 200
    
    # Fetch logs from DB directly
    adapter = MongoAdapter("mcp://mongodb.partner.local")
    logs = adapter.get_audit_logs()
    assert len(logs) > 0
    assert logs[0]["user_id"] == "Inspector"
    assert logs[0]["action"] == "FETCH_RECORDS"

def test_api_dynamic_standards():
    adapter = MongoAdapter("mcp://mongodb.partner.local")
    
    # Prepopulated ASME_B31.3 standard should exist
    std = adapter.get_compliance_standard("ASME_B31.3")
    assert std is not None
    assert std["rules"]["porosity_limit_ratio"] == 0.333
    
    # Save a custom standard
    custom_std = {
        "standard_id": "ASME_B31.3",
        "name": "Customized Piping Spec",
        "rules": {
            "crack": "ALWAYS REJECT",
            "lack_of_fusion": "ALWAYS REJECT",
            "porosity_limit_ratio": 0.1,  # Strict limit
            "inclusion_limit_ratio": 0.2
        }
    }
    adapter.save_compliance_standard(custom_std)
    
    # Query standard rules from LocalComplianceAdapter
    from src.infrastructure.adapters.local_compliance_adapter import LocalComplianceAdapter
    comp = LocalComplianceAdapter(adapter)
    rules_str = comp.get_rules(10.0, "ASME_B31.3")
    
    assert "Customized Piping Spec" in rules_str
    assert "less than 1.0mm" in rules_str  # 10.0 * 0.1 = 1.0mm limit
