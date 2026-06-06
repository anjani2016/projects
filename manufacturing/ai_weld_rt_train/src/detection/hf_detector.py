from transformers import pipeline
import torch
import logging
import cv2
import numpy as np
from PIL import Image

# Monkey-patch to fix transformers bug passing overlap_mask_area_threshold to RF-DETR
try:
    from transformers.models.rf_detr.image_processing_rf_detr import RfDetrImageProcessor
    _orig_post_process = RfDetrImageProcessor.post_process_instance_segmentation
    def patched_post_process(self, *args, **kwargs):
        kwargs.pop('overlap_mask_area_threshold', None)
        return _orig_post_process(self, *args, **kwargs)
    RfDetrImageProcessor.post_process_instance_segmentation = patched_post_process
except ImportError:
    pass

class _HFModelProxy:
    def __init__(self, names):
        self.names = names

class HFWeldDetector:
    def __init__(self, model_id="Roboflow/rf-detr-segmentation"):
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        logging.info(f"Loading HF model {model_id} on device {self.device}")
        
        task = "image-segmentation" if "segmentation" in model_id.lower() else "object-detection"
        try:
            self.pipe = pipeline(task, model=model_id, device=self.device)
            # Try to get class names from the model config
            if hasattr(self.pipe.model, "config") and hasattr(self.pipe.model.config, "id2label"):
                names = self.pipe.model.config.id2label
            else:
                names = {0: "Defect", 1: "crack", 2: "porosity", 3: "inclusion", 4: "lack_of_fusion"}
        except Exception as e:
            logging.error(f"Failed to load HF model: {e}")
            self.pipe = None
            names = {0: "Defect"}
            
        self.model = _HFModelProxy(names)

    def detect(self, image_np, confidence=0.25):
        if self.pipe is None:
            return []
            
        # Convert to PIL Image for the pipeline
        if len(image_np.shape) == 2:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        elif image_np.shape[2] == 1:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
            
        pil_image = Image.fromarray(image_np)
        
        results = self.pipe(pil_image)
        
        detections = []
        for r in results:
            score = r.get('score', 1.0)
            if score < confidence:
                continue
                
            label = r.get('label', 'Defect')
            mask = r.get('mask')
            
            if mask is not None:
                mask_np = np.array(mask)
                # Find bounding box from mask
                y_indices, x_indices = np.where(mask_np > 0)
                if len(y_indices) > 0 and len(x_indices) > 0:
                    x1, y1 = int(np.min(x_indices)), int(np.min(y_indices))
                    x2, y2 = int(np.max(x_indices)), int(np.max(y_indices))
                else:
                    continue
            elif 'box' in r:
                box = r['box']
                x1, y1 = int(box['xmin']), int(box['ymin'])
                x2, y2 = int(box['xmax']), int(box['ymax'])
            else:
                continue

            coords = [x1, y1, x2, y2]
            pixel_length = x2 - x1
            
            detections.append({
                "type": label,
                "confidence": float(score),
                "bbox": coords,
                "dims": {"length": pixel_length}
            })
        return detections
