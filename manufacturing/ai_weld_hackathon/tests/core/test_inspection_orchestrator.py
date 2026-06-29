import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock
from src.core.use_cases.inspection_orchestrator import InspectionOrchestrator
from src.core.domain.entities import Defect

# Mock Ports
class MockVisionPort:
    def detect(self, image_np):
        return [Defect(type="porosity", confidence=0.9, bbox=[0,0,10,10], dims={"length": 10.0})]

class MockDatabasePort:
    def save_record(self, record):
        return "mock_id_123"

class MockCompliancePort:
    def get_rules(self, thickness, standard="ASME_B31.3"):
        return "Test Rule: Pass"

import asyncio

def test_inspection_orchestrator_initialization():
    vision_port = MockVisionPort()
    db_port = MockDatabasePort()
    compliance_port = MockCompliancePort()
    
    orchestrator = InspectionOrchestrator(vision_port, db_port, compliance_port)
    assert orchestrator.vision_port == vision_port
    assert orchestrator.db_port == db_port
    assert orchestrator.compliance_port == compliance_port

