from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.core.domain.entities import InspectionRecord

class DatabasePort(ABC):
    @abstractmethod
    def save_record(self, record: InspectionRecord) -> str:
        """Save the inspection record to the database and return the document ID."""
        pass

    @abstractmethod
    def update_record(self, record: InspectionRecord) -> None:
        """Update an existing inspection record."""
        pass

    @abstractmethod
    def get_records(self) -> List[InspectionRecord]:
        """Retrieve all inspection records from the database."""
        pass

    @abstractmethod
    def get_record_by_report_id(self, report_id: str) -> Optional[InspectionRecord]:
        """Retrieve a specific inspection record by its report ID."""
        pass

    @abstractmethod
    def generate_report_id(self) -> str:
        """Generate a unique report ID for the day (e.g. REP-YYYYMMDD-001)."""
        pass

    # --- Technician Feedback ---
    @abstractmethod
    def save_feedback(self, feedback: Dict[str, Any]) -> str:
        """Log technician correction feedback (HITL review) for model tuning."""
        pass

    @abstractmethod
    def get_feedback(self) -> List[Dict[str, Any]]:
        """Retrieve all technician correction feedback."""
        pass

    # --- Vision Inference Caching ---
    @abstractmethod
    def get_vision_cache(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached vision detections for a given image hash."""
        pass

    @abstractmethod
    def save_vision_cache(self, image_hash: str, detections: Dict[str, Any]) -> str:
        """Cache vision model outputs to save inference resources."""
        pass

    # --- Enterprise Audit Trails (SOC 2) ---
    @abstractmethod
    def log_audit_event(self, event: Dict[str, Any]) -> str:
        """Log secure access, report downloads, or model overrides for compliance audit trails."""
        pass

    @abstractmethod
    def get_audit_logs(self) -> List[Dict[str, Any]]:
        """Retrieve security audit logs."""
        pass

    # --- Compliance Standards ---
    @abstractmethod
    def save_compliance_standard(self, standard: Dict[str, Any]) -> str:
        """Store compliance rules/standards (e.g., ASME B31.3 specs)."""
        pass

    @abstractmethod
    def get_compliance_standard(self, standard_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve compliance standard rules by standard ID."""
        pass


