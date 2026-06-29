import torch
from ultralytics import YOLO
import logging

class WeldDetector:
    """
    Phase 2: The Defect Engine.
    Loads AI models from Hugging Face or local storage to detect weld defects.
    """
    def __init__(self, model_id="yolov8n.pt"):
        """
        Initialize the detector.
        :param model_id: Hugging Face model path or local weights file[cite: 1].
        """
        # Select device: Use CUDA (GPU) if available for faster RT image processing
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logging.info(f"Loading model {model_id} on {self.device}")
        
        # Load the model using Ultralytics (works seamlessly with many HF models)
        self.model = YOLO(model_id).to(self.device)

    def detect(self, image_np, confidence=0.25):
        """
        Runs inference on an enhanced image.
        :param image_np: The image array from WeldProcessor[cite: 1].
        :param confidence: The detection threshold.
        :return: List of detected defect dictionaries.
        """
        results = self.model.predict(source=image_np, conf=confidence, device=self.device)
        
        detections = []
        for r in results:
            for box in r.boxes:
                # Extracting data for the Engineering Brain[cite: 1]
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
                # Calculate approximate length in pixels (for Phase 3 measurement)
                pixel_length = coords[2] - coords[0]
                
                detections.append({
                    "type": label,
                    "confidence": float(box.conf[0]),
                    "bbox": coords,
                    "dims": {"length": pixel_length} # To be calibrated in engine.py[cite: 1]
                })
                
        return detections