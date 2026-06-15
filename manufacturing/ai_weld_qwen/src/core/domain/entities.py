from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Defect(BaseModel):
    type: str
    confidence: float
    bbox: List[float]
    dims: Dict[str, float]

class InspectionRecord(BaseModel):
    id: Optional[str] = None
    report_id: Optional[str] = None
    image_id: str
    thickness: float
    model_used: str
    verdict: str
    details: str
    raw_image_path: Optional[str] = None
    annotated_image_path: Optional[str] = None
    timestamp: Optional[str] = None
    performer_comments: Optional[str] = ""
    supervisor_comments: Optional[str] = ""
    status_state: Optional[int] = 0
    material: Optional[str] = ""
    regulatory_code: Optional[str] = ""
    client_spec: Optional[str] = ""
    other_standard: Optional[str] = ""
    app_type: Optional[str] = ""
    usage: Optional[str] = ""
