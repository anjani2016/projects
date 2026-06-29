from abc import ABC, abstractmethod

class CompliancePort(ABC):
    @abstractmethod
    def get_rules(self, thickness: float, standard: str = "ASME_B31.3") -> str:
        """Retrieve the engineering compliance rules as a string."""
        pass
