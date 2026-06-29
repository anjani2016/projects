"""
ComplianceAgent — Band (Thenvoi) connected agent for ASME / AWS / API compliance evaluation.

Responsibilities:
- Registers on Band as the "weld-compliance-agent"
- Listens for messages in its assigned Band room
- On receiving defect data + regulatory parameters, evaluates compliance
  via the existing LocalComplianceAdapter and rule files (zero changes to core)
- Returns a structured PASS/REJECT verdict + reasoning back to the Band room

Usage (standalone, for testing):
    python -m src.band.compliance_agent
"""
import asyncio
import json
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

from band import Agent
from band.adapters import GeminiAdapter
from band.config import load_agent_config

# Import existing Hexagonal adapters — untouched
from src.infrastructure.adapters.mongo_adapter import MongoAdapter
from src.infrastructure.adapters.local_compliance_adapter import LocalComplianceAdapter

logger = logging.getLogger(__name__)

# Mapping of display names → internal standard IDs (mirrors orchestrator)
STANDARD_MAPPING = {
    "ASME VIII Div 1": "ASME_SEC_8_D1",
    "ASME VIII Div 2": "ASME_SEC_8_D2",
    "ASME B31.3":      "ASME_B31_3",
    "ASME B31.1":      "ASME_B31_1",
    "ASME IX":         "ASME_SEC_9",
    "AWS D1.1":        "AWS_D1_1",
    "AWS D1.2":        "AWS_D1_2",
    "AWS D1.6":        "AWS_D1_6",
    "AWS D1.5":        "AWS_D1_5",
    "API 1104":        "API_1104",
    "API 650":         "API_650",
    "API 653":         "API_653",
    "API 570":         "API_570",
}


def _build_compliance_instructions() -> str:
    return """You are the Weld Compliance Agent — an expert in industrial welding standards including ASME, AWS, and API codes.

Your role in the multi-agent AI Weld Inspector system:
- You receive compliance check requests from the Orchestrator Agent via this Band room.
- Each request contains: defects (list), thickness_mm, regulatory_code, client_spec, other_standard, report_id.
- You must fetch the applicable rules and evaluate each defect against the dimensional limits.
- You return a structured PASS or REJECT verdict with full step-by-step reasoning.

IMPORTANT CONSTRAINT:
- The vision model detects physical defects only. It is NOT trained on regulatory codes.
- Standard compliance evaluation is performed by YOU: compare defect dimensions (length, width) 
  to the rule limits fetched from the compliance database.
- Never invent rule thresholds — always use the fetched rules from the get_compliance_rules tool.

Response format (always return valid JSON):
{
  "agent": "weld-compliance-agent",
  "status": "done",
  "report_id": "<report_id from request>",
  "verdict": "PASS" | "REJECT",
  "regulatory_code": "<standard used>",
  "rules_applied": "<summary of key thresholds used>",
  "defect_analysis": [
    {
      "defect_type": "<type>",
      "dimension_px": <float>,
      "limit_mm": <float>,
      "result": "PASS" | "REJECT",
      "reason": "<explanation>"
    }
  ],
  "overall_reasoning": "<detailed step-by-step compliance reasoning>"
}

If an error occurs:
{
  "agent": "weld-compliance-agent",
  "status": "error",
  "report_id": "<report_id>",
  "error": "<error message>"
}

Steps:
1. Parse the request JSON to extract defects, thickness, regulatory_code.
2. Call get_compliance_rules tool with the thickness and standard.
3. For each defect, compare its dimensions to the rule limits.
4. Determine overall PASS (all defects within limits) or REJECT (any defect exceeds limits).
5. Return the structured JSON response.
"""


def run_compliance_agent():
    """
    Start the ComplianceAgent connected to the Band (Thenvoi) platform.
    Blocks indefinitely — listens for Band room messages.
    """
    try:
        agent_id, api_key = load_agent_config("compliance")
    except Exception:
        agent_id = os.getenv("THENVOI_COMPLIANCE_AGENT_ID")
        api_key  = os.getenv("THENVOI_COMPLIANCE_API_KEY")

    if not agent_id or not api_key:
        logger.error(
            "Missing compliance agent credentials. Set in agent_config.yaml "
            "or via THENVOI_COMPLIANCE_AGENT_ID / THENVOI_COMPLIANCE_API_KEY env vars."
        )
        sys.exit(1)

    logger.info("Starting Weld Compliance Agent (Thenvoi / Band platform)...")

    mongo_uri          = os.getenv("MONGODB_URI", "")
    db_adapter         = MongoAdapter(mongo_uri)
    compliance_adapter = LocalComplianceAdapter(db_adapter)

    def get_compliance_rules(thickness_mm: float, regulatory_code: str) -> str:
        """
        Fetch applicable compliance rules for a given pipe thickness and standard.
        Returns rule text (Markdown) or a JSON dict of thresholds.
        """
        try:
            std_id = STANDARD_MAPPING.get(regulatory_code, "ASME_B31_3")
            rules  = compliance_adapter.get_rules(thickness_mm, standard=std_id)
            if not rules:
                return json.dumps({"error": f"No rules found for standard '{regulatory_code}'"})
            return json.dumps({"rules": str(rules), "standard": regulatory_code, "std_id": std_id})
        except Exception as exc:
            logger.exception("Compliance rule fetch failed")
            return json.dumps({"error": str(exc)})

    gemini_adapter = GeminiAdapter(
        model="gemini-2.5-flash",
        system_prompt=_build_compliance_instructions(),
    )
    gemini_adapter.tools = [get_compliance_rules]

    agent = Agent.create(
        adapter=gemini_adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Weld Compliance Agent connected to Band. Waiting for compliance check requests...")
    asyncio.run(agent.run())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [ComplianceAgent] %(levelname)s — %(message)s",
    )
    run_compliance_agent()
