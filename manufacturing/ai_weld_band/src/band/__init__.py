"""
Band of Agents — AI Weld NDT Inspector
Multi-agent coordination layer via Band platform.

Agents:
    - OrchestratorAgent  : coordinates the full inspection workflow
    - VisionAgent        : runs RT-DETR/YOLO defect detection
    - ComplianceAgent    : evaluates defects against ASME/AWS/API standards
    - ReviewAgent        : HITL sign-off and audit trail via Band
"""
