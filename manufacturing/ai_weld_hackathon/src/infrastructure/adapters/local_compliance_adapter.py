from src.core.ports.compliance_port import CompliancePort

class LocalComplianceAdapter(CompliancePort):
    def __init__(self, db_port = None):
        self.db_port = db_port

    def get_rules(self, thickness: float, standard: str = "ASME_B31_3") -> str:
        if self.db_port:
            try:
                db_std = self.db_port.get_compliance_standard(standard)
                if not db_std and "." in standard:
                    db_std = self.db_port.get_compliance_standard(standard.replace(".", "_"))
                if db_std and "rules" in db_std:
                    rules = db_std["rules"]
                    porosity_limit = thickness * rules.get("porosity_limit_ratio", 0.333)
                    inclusion_limit = thickness * rules.get("inclusion_limit_ratio", 0.5)
                    return (f"{db_std['name']} Rules for {thickness}mm thickness (Dynamic Database Standards):\n"
                            f"- Domain: {rules.get('domain', 'N/A')}\n"
                            f"- Usage: {rules.get('usage', 'N/A')}\n"
                            f"- Scope: {rules.get('scope', 'N/A')}\n"
                            f"- 'crack' or 'lack_of_fusion' is {rules.get('crack', 'ALWAYS REJECT')}.\n"
                            f"- 'porosity' length must be less than {porosity_limit:.1f}mm to PASS.\n"
                            f"- 'inclusion' length must be less than {inclusion_limit:.1f}mm to PASS.\n"
                            f"Note: Assume 1 pixel = 0.1mm for dimension conversion.")
            except Exception:
                # If database query fails, failover to hardcoded values below
                pass

        # Fallback dictionary mapping all 13 standards
        fallback_data = {
            "ASME_SEC_8_D1": ("ASME VIII Div 1", "Pressure Vessels", "Rules for design, fabrication, inspection, and testing of pressure vessels operating at pressures >15 psig."),
            "ASME_SEC_8_D2": ("ASME VIII Div 2", "Pressure Vessels", "Alternative, more stringent rules for pressure vessels allowing higher design stresses and reduced material thickness."),
            "ASME_B31_3": ("ASME B31.3", "Piping", "Requirements for process piping in petroleum refineries, chemical, pharmaceutical, and other industrial plants."),
            "ASME_B31_1": ("ASME B31.1", "Piping", "Requirements for power piping typically found in electric generating stations and industrial/institutional boiler plants."),
            "ASME_SEC_9": ("ASME IX", "Qualification", "Universal standard for qualifying welding procedures (WPS/PQR) and personnel (WPQ) across ASME projects."),
            "AWS_D1_1": ("AWS D1.1", "Structural", "Welding requirements for structural steel elements made of carbon and low-alloy constructional steels."),
            "AWS_D1_2": ("AWS D1.2", "Structural", "Requirements for welding structural aluminum alloys in static and cyclic loaded applications."),
            "AWS_D1_6": ("AWS D1.6", "Structural", "Requirements for welding structural stainless steel components."),
            "AWS_D1_5": ("AWS D1.5", "Structural", "Specialized requirements for welding steel highway and railway bridges."),
            "API_1104": ("API 1104", "Pipeline", "Standards for gas and arc welding of pipelines and related facilities for transmission of petroleum and fuel gases."),
            "API_650": ("API 650", "Storage Tanks", "Design, material, fabrication, and testing for vertical, cylindrical, atmospheric-pressure welded steel storage tanks."),
            "API_653": ("API 653", "Inspection", "Minimum requirements for maintaining the integrity of in-service atmospheric aboveground storage tanks."),
            "API_570": ("API 570", "Inspection", "Standards for the inspection, repair, alteration, and rerating of in-service metallic piping systems."),
        }
        
        normalized_std = standard.replace(".", "_")
        info = fallback_data.get(standard) or fallback_data.get(normalized_std)
        
        if info:
            name, domain, scope = info
            porosity_limit = thickness * 0.333
            inclusion_limit = thickness * 0.5
            return (f"{name} Rules for {thickness}mm thickness (Hardcoded Fallback):\n"
                    f"- Domain: {domain}\n"
                    f"- Scope: {scope}\n"
                    f"- 'crack' or 'lack_of_fusion' is ALWAYS REJECT.\n"
                    f"- 'porosity' length must be less than {porosity_limit:.1f}mm to PASS.\n"
                    f"- 'inclusion' length must be less than {inclusion_limit:.1f}mm to PASS.\n"
                    f"Note: Assume 1 pixel = 0.1mm for dimension conversion.")
        return f"Unknown standard: {standard}."
