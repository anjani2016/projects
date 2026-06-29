from src.agents.band_network import band_client
from src.reporting.reporter import ReportGenerator

class ReviewerAgent:
    """
    Agent 3: The NDE Reviewer
    Responsible for final decision making, risk assessment, and report generation.
    """
    def __init__(self):
        self.reporter = ReportGenerator()
        
    def final_review(self, verdict_payload):
        print("⚖️ [Reviewer Agent] Finalizing disposition and managing risk...")
        
        passed = verdict_payload.get("passed")
        reason = verdict_payload.get("reason")
        defects = verdict_payload.get("defects")
        image = verdict_payload.get("image")
        
        # Here we mock an LLM evaluating the strict rule engine output
        if passed:
            llm_summary = "All defects are within acceptable ASME tolerances. Code compliant. Approved."
        else:
            llm_summary = f"Reject. Critical defect found exceeding code limits: {reason}. Escalation required."
            
        print(f"⚖️ [Reviewer Agent] LLM Summary: {llm_summary}")
        
        # Generate the final report
        try:
            report_path = self.reporter.create_report(image, passed, llm_summary)
        except Exception as e:
            # Fallback if the reporter fails for some reason
            print(f"[Reviewer Agent] Warning - Reporter failed: {e}")
            report_path = None
            
        final_payload = {
            "report_path": report_path,
            "llm_summary": llm_summary,
            "final_status": "Accept" if passed else "Reject",
            "passed": passed,
            "reason": reason,
            "defects": defects
        }
        
        # Signal that the workflow is complete
        band_client.dispatch("report_ready", final_payload)
