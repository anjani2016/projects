from abc import ABC, abstractmethod
from typing import List
import numpy as np
from src.core.domain.entities import Defect

class VisionPort(ABC):
    @abstractmethod
    def detect(self, image_np: np.ndarray, image_hash: str = None) -> List[Defect]:
        """Detect defects in a radiographic image, optionally utilizing cache."""
        pass
