import cv2
import os
import json
from google.antigravity import Agent, LocalAgentConfig

from src.core.ports.vision_port import VisionPort
from src.core.ports.database_port import DatabasePort
from src.core.ports.compliance_port import CompliancePort
from src.core.domain.entities import InspectionRecord

class InspectionOrchestrator:
    def __init__(self, vision_port: VisionPort, db_port: DatabasePort, compliance_port: CompliancePort):
        self.vision_port = vision_port
        self.db_port = db_port
        self.compliance_port = compliance_port
        
        # Unique report identification properties
        self.report_id = None
        self.raw_image_path = None
        self.annotated_image_path = None

    async def run(
        self, 
        image_path: str, 
        model_path: str, 
        thickness: float, 
        image_hash: str = None,
        app_type: str = "Piping",
        material: str = "Carbon Steel",
        regulatory_code: str = "ASME B31.3",
        client_spec: str = "None",
        other_standard: str = "None",
        usage: str = "Fabrication"
    ) -> str:
        # Wrap Port methods into functions for the Antigravity Agent tools
        def detect_weld_defects(path: str) -> str:
            if not os.path.exists(path):
                return f"Error: Image {path} not found."
            image_np = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if image_np is None:
                return "Error: Could not load image."
            
            defects = self.vision_port.detect(image_np, image_hash=image_hash)
            if not defects:
                return "No defects found. The weld appears clean."
            
            report = ["Defects Detected:"]
            for i, d in enumerate(defects):
                report.append(f"{i+1}. Type: {d.type}, Confidence: {d.confidence:.2f}, Dimensions (pixels): {d.dims['length']}, Bounding Box: {d.bbox}")
            return "\n".join(report)

        def get_compliance_rules(thick: float) -> str:
            # Mapping selected standard strings to standard IDs
            standard_mapping = {
                "ASME VIII Div 1": "ASME_SEC_8_D1",
                "ASME VIII Div 2": "ASME_SEC_8_D2",
                "ASME B31.3": "ASME_B31_3",
                "ASME B31.1": "ASME_B31_1",
                "ASME IX": "ASME_SEC_9",
                "AWS D1.1": "AWS_D1_1",
                "AWS D1.2": "AWS_D1_2",
                "AWS D1.6": "AWS_D1_6",
                "AWS D1.5": "AWS_D1_5",
                "API 1104": "API_1104",
                "API 650": "API_650",
                "API 653": "API_653",
                "API 570": "API_570",
            }
            std_id = standard_mapping.get(regulatory_code, "ASME_B31_3")
            
            rules_context = []
            
            # Load standard rules (database-first via adapter)
            std_rules = self.compliance_port.get_rules(thick, standard=std_id)
            if std_rules:
                rules_context.append(f"--- Regulatory Code Standard: {regulatory_code} Rules ---\n{std_rules}")
                
            # Load client spec if not "None" (database-first via adapter)
            if client_spec != "None":
                client_rules = self.compliance_port.get_rules(thick, standard=client_spec)
                if client_rules:
                    rules_context.append(f"--- Client Specification override: {client_spec} Rules ---\n{client_rules}")
                    
            # Load other standard if not "None" (database-first via adapter)
            if other_standard != "None":
                other_rules = self.compliance_port.get_rules(thick, standard=other_standard)
                if other_rules:
                    rules_context.append(f"--- Other Standard: {other_standard} Rules ---\n{other_rules}")
                    
            return "\n\n".join(rules_context)

        def log_inspection_to_database(image_id: str, verdict: str, details: str) -> str:
            record = InspectionRecord(
                report_id=self.report_id,
                image_id=image_id,
                thickness=thickness,
                model_used=model_path,
                verdict=verdict,
                details=details,
                raw_image_path=self.raw_image_path,
                annotated_image_path=self.annotated_image_path
            )
            return self.db_port.save_record(record)

        from google.antigravity import GeminiConfig
        
        # Check if Vertex AI mode is active in .env
        use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() in ["true", "1"]
        g_config = None
        model_name = None
        if use_vertex:
            g_config = GeminiConfig(
                vertex=True,
                project=os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-weld-inspector-hackathon"),
                location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            )
            model_name = "gemini-2.5-flash"
            
        # Agent Configuration
        config = LocalAgentConfig(
            gemini_config=g_config,
            model=model_name,
            tools=[detect_weld_defects, get_compliance_rules, log_inspection_to_database],
            system_instructions=(
                "You are the Senior Welding Quality Reviewer.\n"
                "Your job is to analyze a radiographic image for defects and determine if the weld passes or fails compliance.\n"
                "Important: The underlying AI vision model is only trained to detect and size physical defects, and is NOT trained on standard codes/regulatory rules. Standard compliance evaluation must be done by comparing the defect dimensions (from 'detect_weld_defects') to the rules fetched via 'get_compliance_rules'.\n"
                "1. Use the 'detect_weld_defects' tool to get the raw defects from the AI Vision model.\n"
                "2. Use the 'get_compliance_rules' tool to fetch the rules for the given pipe thickness.\n"
                "3. Reason step-by-step to calculate if the defects exceed the rule limits.\n"
                "4. You MUST use the 'log_inspection_to_database' tool to permanently save your verdict and reasoning. Use the image path as the image_id.\n"
                "5. Finally, provide a final summary starting with either 'STATUS: PASS' or 'STATUS: REJECT' followed by your reasoning."
            )
        )
        
        prompt = (
            f"Please analyze the weld radiography image located at '{image_path}'. "
            f"The pipe wall thickness is {thickness}mm.\n"
            f"Application Type (Domain): {app_type}\n"
            f"Material: {material}\n"
            f"Functional Intent / Usage: {usage}\n"
            f"Regulatory Code Standard: {regulatory_code}\n"
            f"Client Specification: {client_spec}\n"
            f"Other Standard: {other_standard}\n\n"
            f"Note: The underlying AI vision model is NOT trained on regulatory codes or standards. It only detects and sizes physical defects. Standard compliance evaluation is performed programmatically by comparing the defect dimensions to the rules fetched from the compliance database. Only the selected standard rules are used; if no database record exists, evaluation uses fallback rules."
        )
        
        try:
            async with Agent(config) as agent:
                response = await agent.chat(prompt)
                return await response.text()
        except Exception as e:
            return f"Error during agent execution: {str(e)}"
