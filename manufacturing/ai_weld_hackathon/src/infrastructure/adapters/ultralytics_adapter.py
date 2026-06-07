from typing import List
import numpy as np
import cv2
import os
import logging
from ultralytics import YOLO, RTDETR
import torch
from transformers import AutoImageProcessor, AutoModelForObjectDetection

from src.core.ports.vision_port import VisionPort
from src.core.domain.entities import Defect

class UltralyticsAdapter(VisionPort):
    def __init__(self, model_path: str, db_port = None):
        self.model_path = model_path
        self.db_port = db_port
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        logging.info(f"Loading Vision Model on device {self.device}")
        
        # Check if this is a Hugging Face checkpoint directory
        self.is_hf = os.path.isdir(model_path) and os.path.exists(os.path.join(model_path, "config.json"))
        
        try:
            if self.is_hf:
                self.hf_processor = AutoImageProcessor.from_pretrained(model_path)
                self.hf_model = AutoModelForObjectDetection.from_pretrained(model_path).to(self.device)
            elif "rtdetr" in model_path.lower():
                self.model = RTDETR(model_path).to(self.device)
            else:
                self.model = YOLO(model_path).to(self.device)
        except Exception as e:
            logging.error(f"Failed to load model weights: {e}")
            raise e
            
        ru_to_en = {
            "пора": "porosity",
            "включение": "inclusion",
            "подрез": "undercut",
            "прожог": "burn_through",
            "трещина": "crack",
            "наплыв": "overlap",
            "несплавление": "lack_of_fusion",
            "непровар корня": "incomplete_root_penetration",
            "эталон1": "iqi_wire_1",
            "эталон2": "iqi_wire_2",
            "эталон3": "iqi_wire_3",
            "пора-скрытая": "hidden_porosity",
            "утяжина": "concavity"
        }
        
        if not self.is_hf and hasattr(self.model, 'names') and self.model.names:
            translated = {}
            for cls_id, name in self.model.names.items():
                name_clean = str(name).lower().strip()
                translated[cls_id] = ru_to_en.get(name_clean, name)
            
            try:
                if hasattr(self.model, 'model') and hasattr(self.model.model, 'names'):
                    self.model.model.names = translated
                else:
                    self.model.names = translated
            except AttributeError:
                try:
                    self.model.names.update(translated)
                except Exception as err:
                    pass

    def detect(self, image_np: np.ndarray, image_hash: str = None) -> List[Defect]:
        cache_key = None
        if image_hash:
            model_name = os.path.basename(self.model_path)
            import hashlib
            cache_key = hashlib.sha256(f"{image_hash}_{model_name}".encode('utf-8')).hexdigest()

        if cache_key and self.db_port:
            try:
                cached = self.db_port.get_vision_cache(cache_key)
                if cached and "detections" in cached:
                    logging.info(f"Vision Inference Cache Hit for hash {image_hash} (Model: {model_name})")
                    self.db_port.log_audit_event({
                        "user_id": "SYSTEM",
                        "action": "VISION_CACHE_HIT",
                        "details": f"Retrieved cached detections for image hash {image_hash} and model {model_name}"
                    })
                    return [Defect(**d) for d in cached["detections"]]
            except Exception as e:
                logging.warning(f"Failed to retrieve vision cache: {e}")

        if len(image_np.shape) == 2:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        elif image_np.shape[2] == 1:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)

        detections = []

        if self.is_hf:
            from PIL import Image
            import torch
            pil_image = Image.fromarray(image_np)
            inputs = self.hf_processor(images=pil_image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.hf_model(**inputs)
            
            target_sizes = torch.tensor([pil_image.size[::-1]]).to(self.device)
            results = self.hf_processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.25)[0]
            
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                coords = box.tolist()  # [xmin, ymin, xmax, ymax]
                class_name = self.hf_model.config.id2label[label.item()]
                pixel_length = coords[2] - coords[0]
                
                detections.append(Defect(
                    type=class_name,
                    confidence=float(score.item()),
                    bbox=coords,
                    dims={"length": pixel_length}
                ))
        else:
            results = self.model.predict(
                source=image_np, 
                conf=0.25, 
                device=self.device,
                save=False 
            )
            
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = self.model.names[cls_id]
                    coords = box.xyxy[0].tolist() 
                    pixel_length = coords[2] - coords[0]
                    
                    detections.append(Defect(
                        type=label,
                        confidence=float(box.conf[0]),
                        bbox=coords,
                        dims={"length": pixel_length}
                    ))
                
        # Save to cache if hash & DB port exists
        if cache_key and self.db_port and detections:
            try:
                self.db_port.save_vision_cache(cache_key, [d.model_dump() for d in detections])
            except Exception as e:
                logging.warning(f"Failed to save vision cache: {e}")
                
        return detections
