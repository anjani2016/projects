from src.agents.band_network import band_client
from src.detection.hf_detector import HFWeldDetector
from src.detection.detector import WeldDetector

class InspectorAgent:
    """
    Agent 1: The Inspector
    Responsible for parsing the raw image through the ML model to find defects.
    """
    def __init__(self, model_option="Hugging Face", model_path=None):
        if "Hugging Face" in model_option:
            self.detector = HFWeldDetector(model_id=model_path) if model_path else HFWeldDetector()
        else:
            self.detector = WeldDetector(model_path=model_path) if model_path else WeldDetector()
            
    def inspect(self, image):
        print("🕵️‍♂️ [Inspector Agent] Analyzing radiographic image...")
        
        # Execute ML detection
        real_defects = self.detector.detect(image)
        
        # Format payload and push to Band network
        payload = {
            "image": image,
            "defects": real_defects,
            "status": "inspection_complete"
        }
        band_client.dispatch("inspection_complete", payload)
