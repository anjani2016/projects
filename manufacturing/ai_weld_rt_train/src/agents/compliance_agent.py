from src.agents.band_network import band_client
from src.rule_engine.engine import WeldEngine

class ComplianceAgent:
    """
    Agent 2: The Compliance Officer
    Responsible for cross-referencing findings against ASME and Client Specs.
    """
    def __init__(self):
        self.engine = WeldEngine()
        
    def evaluate(self, payload, thickness=10.0):
        print("📐 [Compliance Agent] Reviewing inspection data against ASME codes...")
        defects = payload.get("defects", [])
        
        # Evaluate against strict engineering rules
        passed, reason = self.engine.validate_defect(defects, thickness)
        
        # Push verdict back to Band network
        verdict_payload = {
            "image": payload.get("image"),
            "defects": defects,
            "passed": passed,
            "reason": reason,
            "status": "compliance_verdict"
        }
        band_client.dispatch("compliance_verdict", verdict_payload)
