import cv2
import numpy as np

class WeldProcessor:
    """
    Handles Phase 1: Digital Eye.
    Responsible for image enhancement and IQI sensitivity validation.
    """
    def __init__(self, clip_limit=3.0, tile_grid=(8, 8)):
        # CLAHE parameters: clip_limit helps prevent over-amplification of noise
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)

    def enhance_image(self, image_path):
        """Applies CLAHE to raw RT images to reveal defects[cite: 1]."""
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"Could not find image at {image_path}")
        
        enhanced = self.clahe.apply(img)
        # Denoise while preserving edges for crack detection
        return cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

    def verify_iqi(self, image):
        """
        Counts IQI wires to ensure image quality meets ASME standards[cite: 1].
        Returns: (bool, int) - (Success status, wire count)
        """
        edges = cv2.Canny(image, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
        
        count = len(lines) if lines is not None else 0
        # ASME V typically requires specific wire visibility[cite: 1]
        is_valid = count >= 3 
        return is_valid, count