import json
import os
import logging
from typing import Dict, Any, List
from google.antigravity import Agent, LocalAgentConfig, GeminiConfig

class RepairPlanner:
    def __init__(self):
        self.providers_db_path = "data/repair_providers.json"

    def _load_providers(self) -> List[Dict[str, Any]]:
        """Load available repair technicians from database."""
        try:
            if os.path.exists(self.providers_db_path):
                with open(self.providers_db_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load repair providers: {e}")
        
        # In-memory backup if file cannot be read
        return [
            {
                "id": "welder-01",
                "name": "Marcus Vance",
                "avatar": "👨‍🏭",
                "certifications": ["ASME Section IX", "ASME B31.3", "AWS D1.1"],
                "material_specialties": ["Carbon Steel", "Low-Alloy Steel"],
                "process_specialties": ["SMAW (Stick)", "GMAW (MIG)"],
                "rate_per_hour": 75.0,
                "availability": "Available",
                "rating": 4.9,
                "location": "Fabrication Bay 2"
            }
        ]

    def run_deterministic_fallback(
        self, 
        material: str, 
        regulatory_code: str, 
        thickness: float, 
        defects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Deterministic fallback matching logic if AI API is offline."""
        providers = self._load_providers()
        selected = providers[0] # Default
        
        # Rule-based matching
        material_lower = material.lower()
        code_upper = regulatory_code.upper()
        
        if "stainless" in material_lower or "aluminum" in material_lower:
            # Elena Rostova matches Stainless Steel
            for p in providers:
                if p["id"] == "welder-02":
                    selected = p
                    break
        elif "inconel" in material_lower or "titanium" in material_lower or thickness > 25.0:
            # Kenji Sato matches Exotic Alloys or thick joints
            for p in providers:
                if p["id"] == "welder-04":
                    selected = p
                    break
        elif "1104" in code_upper:
            # Carlos Mendez matches API 1104 Pipelines
            for p in providers:
                if p["id"] == "welder-03":
                    selected = p
                    break
        else:
            # Marcus Vance matches Carbon Steel/ASME
            for p in providers:
                if p["id"] == "welder-01":
                    selected = p
                    break

        # Generate a template-based Action Plan
        defect_summary = []
        grinding_steps = []
        for i, d in enumerate(defects):
            d_type = d.get("type", "Defect")
            bbox = d.get("bbox", [0, 0, 0, 0])
            dims = d.get("dims", {"length": 0})
            length_mm = dims.get("length", 0) * 0.1
            defect_summary.append(f"- Defect #{i+1}: {d_type} (Size: {length_mm:.1f}mm) at Bounding Box {bbox}")
            grinding_steps.append(f"Excavate defect #{i+1} ({d_type}) by grinding precisely within coordinates {bbox[0]}-{bbox[2]} along the weld axis.")

        defect_str = "\n".join(defect_summary) if defect_summary else "- Defect: Undefined compliance exception."
        grinding_str = "\n".join([f"   {idx+1}. {step}" for idx, step in enumerate(grinding_steps)])
        
        process = "GTAW (TIG)" if "GTAW" in str(selected["process_specialties"]) else "SMAW (Stick)"
        filler = "ER308L" if "Stainless" in material else "E7018"
        preheat = "150°C" if "Carbon" in material and thickness > 19.0 else "50°C"

        action_plan = (
            f"### Weld Repair Action Plan (Deterministic Fallback)\n\n"
            f"**Assigned Technician**: {selected['name']} ({selected['id']}) — *Matched on certification: {selected['certifications'][0]}*\n\n"
            f"#### 1. Defect Diagnosis\n"
            f"The following defect(s) exceed {regulatory_code} limitations for thickness {thickness}mm:\n"
            f"{defect_str}\n\n"
            f"#### 2. Excavation Instructions\n"
            f"To repair this weld, follow these instructions:\n"
            f"{grinding_str}\n"
            f"- Perform Dye Penetrant Testing (PT) to ensure the crack/defect is fully removed before welding.\n\n"
            f"#### 3. Welding Procedure Specifications (WPS)\n"
            f"- **Welding Process**: {process}\n"
            f"- **Filler Metal / Electrode**: {filler}\n"
            f"- **Preheat Temperature**: {preheat} minimum\n"
            f"- **Interpass Temperature**: 250°C maximum\n\n"
            f"#### 4. Post-Repair Quality Inspection\n"
            f"- Clean weld slag and perform visual inspection.\n"
            f"- Resubmit joint for radiography re-testing to check for volumetric defects."
        )

        return {
            "selected_welder_id": selected["id"],
            "selected_welder_name": selected["name"],
            "selection_reasoning": f"Automatically selected based on material ({material}) and standard ({regulatory_code}) matching rules.",
            "action_plan": action_plan
        }

    async def generate_plan(
        self, 
        material: str, 
        regulatory_code: str, 
        thickness: float, 
        defects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate repair plan using Gemini or local fallback."""
        # Check if Gemini key exists
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            logging.info("No GEMINI_API_KEY found. Running deterministic repair planning agent.")
            return self.run_deterministic_fallback(material, regulatory_code, thickness, defects)

        providers = self._load_providers()
        providers_json = json.dumps(providers, indent=2)
        defects_json = json.dumps(defects, indent=2)

        # Context for the agent
        prompt = (
            f"You are the Welding Repair Specialist Agent.\n"
            f"A weld joint has FAILED radiography inspection. We need to select the best welding technician "
            f"and formulate a detailed Repair Action Plan.\n\n"
            f"**Weld Details**:\n"
            f"- Base Material: {material}\n"
            f"- Regulatory Standard Code: {regulatory_code}\n"
            f"- Pipe Wall Thickness: {thickness}mm\n\n"
            f"**Defect Details (from AI model)**:\n"
            f"{defects_json}\n\n"
            f"**Available Certified Technicians**:\n"
            f"{providers_json}\n\n"
            f"**Instructions**:\n"
            f"1. Select the MOST QUALIFIED available technician from the database. Match by certifications and material specialties first. (e.g. ASME B31.3/Section IX for ASME, API 1104 for pipelines. Stainless specialties for stainless steel, etc.).\n"
            f"2. Formulate a custom step-by-step Repair Action Plan in Markdown.\n"
            f"   - Outline the defects by coordinate bounding boxes and explain where to grind/excavate.\n"
            f"   - Recommend the welding process (e.g. GTAW, SMAW, GMAW) based on the welder's skills and material.\n"
            f"   - Recommend the preheat rules and appropriate filler metal electrode (e.g. E7018 for carbon steel, ER308L for stainless steel, ERNiCr-3 for Inconel).\n"
            f"   - Give explicit post-repair verification steps (radiography re-test).\n"
            f"3. Return your response in JSON format containing the following fields: 'selected_welder_id', 'selected_welder_name', 'selection_reasoning', and 'action_plan' (markdown string)."
        )

        try:
            # Vertex AI check
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

            # Setup reasoning agent config
            config = LocalAgentConfig(
                gemini_config=g_config,
                model=model_name,
                system_instructions=(
                    "You are a welding engineering assistant. You always respond in a structured JSON format containing "
                    "keys: 'selected_welder_id', 'selected_welder_name', 'selection_reasoning', and 'action_plan'. "
                    "Ensure your JSON is valid and clean. The 'action_plan' field must contain structured markdown."
                )
            )

            async with Agent(config) as agent:
                response = await agent.chat(prompt)
                resp_text = await response.text()
                
                # Clean up JSON formatting from code fences
                if "```json" in resp_text:
                    resp_text = resp_text.split("```json")[1].split("```")[0].strip()
                elif "```" in resp_text:
                    resp_text = resp_text.split("```")[1].split("```")[0].strip()
                
                plan_data = json.loads(resp_text)
                # Verify keys
                if all(k in plan_data for k in ["selected_welder_id", "selected_welder_name", "selection_reasoning", "action_plan"]):
                    return plan_data
                raise ValueError("JSON missing required fields")

        except Exception as e:
            logging.error(f"Gemini Repair Agent failed: {e}. Executing fallback logic.")
            return self.run_deterministic_fallback(material, regulatory_code, thickness, defects)
