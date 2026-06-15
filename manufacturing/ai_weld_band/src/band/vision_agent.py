"""
VisionAgent — Band (Thenvoi) connected agent for weld defect detection.

Responsibilities:
- Registers on Band as the "weld-vision-agent"
- Listens for messages in its assigned Band room
- On receiving an inspection request, runs RT-DETR / YOLO detection
  via the existing UltralyticsAdapter (Hexagonal Port — zero changes)
- Returns structured defect results back to the Band room

Usage (standalone, for testing):
    python -m src.band.vision_agent
"""
import asyncio
import json
import os
import sys
import cv2
import logging
from dotenv import load_dotenv

load_dotenv()

from band import Agent
from band.adapters import GeminiAdapter
from band.config import load_agent_config

# Import existing Hexagonal adapters — untouched
from src.infrastructure.adapters.ultralytics_adapter import UltralyticsAdapter
from src.infrastructure.adapters.mongo_adapter import MongoAdapter

logger = logging.getLogger(__name__)

# ── Model path ─────────────────────────────────────────────────────────────────
DEFAULT_MODEL = os.path.join(os.path.dirname(__file__), "../../weights/welding_defects_yolo11x.pt")


def _build_vision_instructions() -> str:
    return """You are the Weld Vision Agent — a specialist in Non-Destructive Testing (NDT) radiography analysis.

Your role in the multi-agent AI Weld Inspector system:
- You receive inspection requests from the Orchestrator Agent via this Band room.
- Each request contains: image_path, image_hash, thickness_mm, model_path (optional).
- You must run the RT-DETR / YOLO vision model to detect weld defects.
- You respond with a structured JSON report of all detected defects.

Response format (always return valid JSON in your message):
{
  "agent": "weld-vision-agent",
  "status": "done",
  "report_id": "<report_id from request>",
  "defects": [
    {
      "type": "<defect_type>",
      "confidence": <float 0-1>,
      "bbox": [x1, y1, x2, y2],
      "dims": {"length": <px>, "width": <px>}
    }
  ],
  "defect_count": <int>,
  "summary": "<short human-readable summary>"
}

If no defects found:
{
  "agent": "weld-vision-agent",
  "status": "done",
  "report_id": "<report_id>",
  "defects": [],
  "defect_count": 0,
  "summary": "No defects detected. Weld appears clean."
}

If an error occurs:
{
  "agent": "weld-vision-agent",
  "status": "error",
  "report_id": "<report_id>",
  "error": "<error message>"
}

IMPORTANT: 
- Always parse the incoming request message as JSON to extract parameters.
- The vision model detects physical defects only. It is NOT trained on regulatory codes.
- Always include the report_id from the request in your response.
- After sending your JSON response, wait quietly for the next message.
"""


def run_vision_agent():
    """
    Start the VisionAgent connected to the Band (Thenvoi) platform.
    This function blocks indefinitely — the agent listens for Band room messages.
    """
    try:
        agent_id, api_key = load_agent_config("vision")
    except Exception:
        agent_id  = os.getenv("THENVOI_VISION_AGENT_ID")
        api_key   = os.getenv("THENVOI_VISION_API_KEY")
    model_path = os.getenv("VISION_MODEL_PATH", DEFAULT_MODEL)

    if not agent_id or not api_key:
        logger.error(
            "Missing vision agent credentials. Set in agent_config.yaml "
            "or via THENVOI_VISION_AGENT_ID / THENVOI_VISION_API_KEY env vars."
        )
        sys.exit(1)

    logger.info("Starting Weld Vision Agent (Thenvoi / Band platform)...")

    # Initialise the existing database and vision adapters
    mongo_uri   = os.getenv("MONGODB_URI", "")
    db_adapter  = MongoAdapter(mongo_uri)
    vision_adapter = UltralyticsAdapter(model_path, db_adapter)

    # The Gemini adapter exposes the agent's tool-calling LLM on Band
    # The system_instructions define how the agent interprets & responds to messages
    gemini_adapter = GeminiAdapter(
        model="gemini-2.5-flash",
        system_prompt=_build_vision_instructions(),
    )

    # Register native Python functions as tools the Gemini agent can call
    def detect_defects_tool(image_path: str, image_hash: str) -> str:
        """
        Run the RT-DETR / YOLO vision model on the given image.
        Returns a JSON string of detected defects.
        """
        try:
            if not os.path.exists(image_path):
                return json.dumps({"error": f"Image not found: {image_path}"})

            image_np = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image_np is None:
                return json.dumps({"error": "Could not decode image file."})

            defects = vision_adapter.detect(image_np, image_hash=image_hash)

            defect_list = [
                {
                    "type": d.type,
                    "confidence": round(d.confidence, 4),
                    "bbox": d.bbox,
                    "dims": d.dims,
                }
                for d in defects
            ]
            return json.dumps({"defects": defect_list, "count": len(defect_list)})

        except Exception as exc:
            logger.exception("Vision detection failed")
            return json.dumps({"error": str(exc)})

    # Attach native tool to the Gemini adapter
    gemini_adapter.tools = [detect_defects_tool]

    agent = Agent.create(
        adapter=gemini_adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Weld Vision Agent connected to Band. Waiting for inspection requests...")
    asyncio.run(agent.run())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [VisionAgent] %(levelname)s — %(message)s",
    )
    run_vision_agent()
