from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class UiPathPort(ABC):
    @abstractmethod
    def start_bpmn_process(self, process_name: str, variables: Dict[str, Any]) -> str:
        """Start a new BPMN process instance on UiPath Orchestrator."""
        pass

    @abstractmethod
    def create_user_task(self, process_id: str, task_name: str, task_data: Dict[str, Any]) -> str:
        """Create a user review task (Action Center) for a human inspector/technician."""
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> str:
        """Retrieve the completion status of a specific user task."""
        pass

    @abstractmethod
    def complete_service_task(self, process_id: str, task_name: str, results: Dict[str, Any]) -> None:
        """Send completion signal and outputs from an automated AI agent back to the process orchestrator."""
        pass
