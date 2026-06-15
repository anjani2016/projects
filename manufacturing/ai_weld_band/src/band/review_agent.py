"""
ReviewAgent — Band (Thenvoi) connected agent for HITL audit and sign-off.

Responsibilities:
- Registers on Band as the "weld-review-agent"
- Listens for verdict messages from the OrchestratorAgent in the Band room
- Applies deterministic safety override rules (any critical defect = mandatory REJECT)
- Posts HITL approval or escalation back to the Band room
- Logs audit events to MongoDB for tamper-evident traceability

Usage (standalone, for testing):
    python -m src.band.review_agent
"""
import asyncio
import json
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from band import Agent
from band.adapters import GeminiAdapter
from band.config import load_agent_config

from src.infrastructure.adapters.mongo_adapter import MongoAdapter

logger = logging.getLogger(__name__)

# Defect types that always trigger a mandatory REJECT regardless of size
CRITICAL_DEFECT_TYPES = {
    "crack",
    "cold_crack",
    "hot_crack",
    "longitudinal_crack",
    "transverse_crack",
    "lamellar_tear",
}


def _build_review_instructions() -> str:
    return """You are the Weld Review Agent — the final human-in-the-loop (HITL) safety gate 
in the AI Weld NDT Inspector multi-agent system.

Your role:
- You receive the combined inspection verdict from the Orchestrator Agent via this Band room.
- You apply final safety override rules before the report is written to the database.
- You post a structured sign-off JSON response back to the room.

Safety Override Rules (mandatory — cannot be overridden by any other agent):
1. If ANY defect type is in the CRITICAL set (cracks, lamellar tears), the verdict MUST be REJECT 
   regardless of size or compliance agent assessment.
2. If the compliance verdict is REJECT, the review verdict must also be REJECT.
3. Only if both the compliance verdict is PASS and no critical defects are present 
   can the review verdict be PASS.

Response format (always return valid JSON):
{
  "agent": "weld-review-agent",
  "status": "done",
  "report_id": "<report_id from request>",
  "review_verdict": "PASS" | "REJECT" | "ESCALATE",
  "override_applied": true | false,
  "override_reason": "<reason if override was applied, else null>",
  "reviewer_notes": "<safety assessment notes>",
  "reviewed_at": "<ISO 8601 UTC timestamp>",
  "audit_logged": true
}

Use ESCALATE if the request is malformed, data is missing, or there is genuine ambiguity 
that requires human intervention.

Steps:
1. Parse the incoming verdict JSON.
2. Call check_safety_overrides tool with the defects list and compliance verdict.
3. Apply override rules.
4. Call log_review_audit tool to persist the review event.
5. Return the structured JSON sign-off.
"""


def run_review_agent():
    """
    Start the ReviewAgent connected to the Band (Thenvoi) platform.
    Blocks indefinitely — listens for Band room messages.
    """
    try:
        agent_id, api_key = load_agent_config("review")
    except Exception:
        agent_id = os.getenv("THENVOI_REVIEW_AGENT_ID")
        api_key  = os.getenv("THENVOI_REVIEW_API_KEY")

    if not agent_id or not api_key:
        logger.error(
            "Missing review agent credentials. Set in agent_config.yaml "
            "or via THENVOI_REVIEW_AGENT_ID / THENVOI_REVIEW_API_KEY env vars."
        )
        sys.exit(1)

    logger.info("Starting Weld Review Agent (Thenvoi / Band platform)...")

    mongo_uri  = os.getenv("MONGODB_URI", "")
    db_adapter = MongoAdapter(mongo_uri)

    def check_safety_overrides(
        defects_json: str,
        compliance_verdict: str,
    ) -> str:
        """
        Apply deterministic safety override rules.
        
        Args:
            defects_json: JSON string — list of defect dicts with 'type' field
            compliance_verdict: "PASS" or "REJECT" from ComplianceAgent

        Returns:
            JSON string with override decision.
        """
        try:
            defects = json.loads(defects_json) if isinstance(defects_json, str) else defects_json

            # Check for critical defect types
            critical_found = []
            for d in defects:
                defect_type = str(d.get("type", "")).lower().replace(" ", "_")
                if defect_type in CRITICAL_DEFECT_TYPES:
                    critical_found.append(d.get("type"))

            if critical_found:
                return json.dumps({
                    "override_applied": True,
                    "override_verdict": "REJECT",
                    "reason": (
                        f"Mandatory REJECT: critical defect type(s) detected — "
                        f"{', '.join(critical_found)}. Cracks and lamellar tears "
                        f"are never acceptable under any standard."
                    ),
                })

            if compliance_verdict.upper() == "REJECT":
                return json.dumps({
                    "override_applied": False,
                    "override_verdict": "REJECT",
                    "reason": "Compliance Agent issued REJECT verdict — confirmed by Review Agent.",
                })

            return json.dumps({
                "override_applied": False,
                "override_verdict": "PASS",
                "reason": "No critical defects. Compliance Agent issued PASS verdict — confirmed.",
            })

        except Exception as exc:
            logger.exception("Safety override check failed")
            return json.dumps({"error": str(exc)})

    def log_review_audit(
        report_id: str,
        review_verdict: str,
        override_applied: bool,
        reviewer_notes: str,
    ) -> str:
        """
        Persist the review audit event to MongoDB for tamper-evident traceability.
        """
        try:
            event = {
                "event_type": "BAND_REVIEW_AGENT_SIGNOFF",
                "report_id": report_id,
                "review_verdict": review_verdict,
                "override_applied": override_applied,
                "reviewer_notes": reviewer_notes,
                "agent": "weld-review-agent",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            db_adapter.log_audit_event(event)
            return json.dumps({"audit_logged": True, "report_id": report_id})
        except Exception as exc:
            logger.exception("Audit log write failed")
            return json.dumps({"audit_logged": False, "error": str(exc)})

    gemini_adapter = GeminiAdapter(
        model="gemini-2.5-flash",
        system_prompt=_build_review_instructions(),
    )
    gemini_adapter.tools = [check_safety_overrides, log_review_audit]

    agent = Agent.create(
        adapter=gemini_adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Weld Review Agent connected to Band. Waiting for verdict sign-off requests...")
    asyncio.run(agent.run())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [ReviewAgent] %(levelname)s — %(message)s",
    )
    run_review_agent()
