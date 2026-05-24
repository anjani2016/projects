from ultralytics import YOLO
import torch
import logging
import os
import cv2
import numpy as np

class WeldDetector:
    """
    Phase 2: The Defect Engine.
    Updated to use the YOLO11x Welding Defects Detector.
    """
    def __init__(self, model_path=None, model_id=None):
        # Allow either model_path or model_id for compatibility
        path = model_path or model_id or os.path.join('weights', 'welding_defects_yolo11x.pt')
        # Use GPU (device 0) if available as per your model documentation
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        logging.info(f"Loading YOLO11x model on device {self.device}")
        
        # Load the specific weights you identified
        try:
            self.model = YOLO(path).to(self.device)
        except Exception as e:
            logging.error(f"Failed to load model weights: {e}")
            # Fallback to standard yolov8 if local weights aren't found
            self.model = YOLO("yolov8n.pt").to(self.device)

    def detect(self, image_np, confidence=0.25):
        """Runs inference and returns structured data for the Engineering Brain[cite: 1]."""
        # YOLO expects 3-channel (RGB) images. Radiography is often 1-channel grayscale.
        if len(image_np.shape) == 2:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        elif image_np.shape[2] == 1:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)

        results = self.model.predict(
            source=image_np, 
            conf=confidence, 
            device=self.device,
            save=False # We handle visualization in Streamlit[cite: 1]
        )
        
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                coords = box.xyxy[0].tolist() 
                
                # Calculate pixel length for the ASME rule engine[cite: 1]
                pixel_length = coords[2] - coords[0]
                
                detections.append({
                    "type": label, # 'porosity', 'Defect', etc.[cite: 1]
                    "confidence": float(box.conf[0]),
                    "bbox": coords,
                    "dims": {"length": pixel_length}
                })
        return detections