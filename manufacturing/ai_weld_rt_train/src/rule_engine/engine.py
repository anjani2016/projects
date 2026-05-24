import logging
import os

# Ensure logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Set up logging for Phase 4 Audit Trail
logging.basicConfig(filename='logs/audit_trail.log', level=logging.INFO)

class WeldEngine:
    """
    Phase 3: The Engineering Brain.
    Determines Accept/Reject status based on engineering codes.
    """
    
    def __init__(self, standard="ASME_B31.3"):
        self.standard = standard
        self.px_to_mm = None # Will be set during calibration

    def validate_defect(self, defect_type, dimensions, wall_thickness):
        """
        Routes the defect to the correct code-based validation logic[cite: 1].
        """
        if self.standard == "ASME_B31.3":
            return self._validate_b31_3(defect_type, dimensions, wall_thickness)
        # Placeholder for future standards
        elif self.standard == "ASME_SEC_VIII":
            return self._validate_sec_viii(defect_type, dimensions, wall_thickness)
        else:
            logging.error(f"Standard {self.standard} not implemented.")
            return False, "Standard Not Found"

    def _validate_b31_3(self, defect_type, dimensions, T):
        """
        Consolidated ASME B31.3 Validation Pipeline.
        Checks all 5 elements in a single unified logic block.
        """
        length = dimensions.get('length', 0)
        label = defect_type.lower()
        
        # Define the 5-element verification list
        # Format: {label: (limit_calculation_func, reject_message)}
        rules = {
            "crack": {
                "limit": 0, 
                "msg": "Zero Tolerance per ASME B31.3"
            },
            "slag": {
                "limit": T / 3, 
                "msg": f"Exceeds T/3 ({T/3:.2f}mm)"
            },
            "lop": {
                "limit": min(3.0, 0.2 * T), 
                "msg": f"Exceeds LOP limit ({min(3.0, 0.2 * T):.2f}mm)"
            },
            "porosity": {
                "limit": min(6.0, T / 4), 
                "msg": f"Exceeds rounded indication limit ({min(6.0, T/4):.2f}mm)"
            },
            "defect": {
                "limit": min(6.0, T / 4), 
                "msg": "General defect exceeds allowable dimensions"
            }
        }

        # Verification Process[cite: 1]
        if label in rules:
            rule = rules[label]
            
            # Specialized check for Cracks (Always Reject)[cite: 1]
            if label == "crack":
                return False, f"REJECT: {rule['msg']}"
            
            # Numeric check for others
            if length > rule['limit']:
                return False, f"REJECT: {label.upper()} - {rule['msg']}"
        
        return True, "ACCEPT"

    def _validate_sec_viii(self, defect_type, dimensions, T):
        # Placeholder for Pressure Vessel specific logic
        pass

    def calibrate(self, reference_px, physical_mm=0.8):
        """
        Sets the calibration ratio. 
        reference_px: The width/diameter of an IQI wire in pixels.
        physical_mm: The actual diameter of that wire in mm.
        """
        if reference_px > 0:
            self.px_to_mm = physical_mm / reference_px
        return self.px_to_mm

    def get_mm(self, pixels):
        """Converts pixels to real-world millimeters."""
        return pixels * self.px_to_mm if self.px_to_mm else pixels