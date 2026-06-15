from fpdf import FPDF
import datetime
import os
import random

class WeldReporter(FPDF):
    def header(self):
        # Header is generated custom in create_report to support layout
        pass

    def footer(self):
        # Position 12mm from the bottom of the page
        self.set_y(-12)

        # ── Left: File Reference ───────────────────────────────────────────────
        self.set_x(10)
        self.set_font('Helvetica', 'I', 6.5)
        self.set_text_color(120, 120, 120)
        self.cell(70, 6, 'File Ref: NDT-FRM-038-09-Radiographic Testing Report', 0, 0, 'L')

        # ── Centre: Legal disclaimer ───────────────────────────────────────────
        # Page width 210mm, margins 10mm each side → usable 190mm
        # Centre block is 100mm wide, starting at (210 - 100) / 2 = 55mm
        self.set_x(55)
        self.set_font('Helvetica', 'B', 6)
        self.set_text_color(80, 80, 80)
        self.cell(100, 6,
                  'THIS DOCUMENT SHALL NOT BE PRODUCED IN PART OR FULL WITHOUT THE WRITTEN PERMISSION OF CENTAURI AND CLIENT',
                  0, 0, 'C')

        # ── Right: Page number ─────────────────────────────────────────────────
        # Right edge at 200mm (210 - 10), cell width 30mm → start at 170mm
        self.set_x(170)
        self.set_font('Helvetica', 'I', 6.5)
        self.set_text_color(120, 120, 120)
        self.cell(30, 6, f'Page {self.page_no()} of {{nb}}', 0, 0, 'R')


    def write_kv(self, k1, v1, k2, v2):
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(245, 247, 250)
        self.cell(35, 5, k1, 1, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 7)
        self.cell(60, 5, str(v1), 1, 0, 'L')
        
        self.set_font('Helvetica', 'B', 7)
        self.cell(35, 5, k2, 1, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 7)
        self.cell(60, 5, str(v2), 1, 1, 'L')

    def write_kv_full(self, k, v):
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(245, 247, 250)
        self.cell(35, 5, k, 1, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 7)
        self.cell(155, 5, str(v), 1, 1, 'L')

    def write_kv_4(self, k1, v1, k2, v2, k3, v3, k4, v4):
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(245, 247, 250)
        self.cell(25, 5, k1, 1, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 7)
        self.cell(22, 5, str(v1), 1, 0, 'L')
        
        self.set_font('Helvetica', 'B', 7)
        self.cell(25, 5, k2, 1, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 7)
        self.cell(23, 5, str(v2), 1, 0, 'L')
        
        self.set_font('Helvetica', 'B', 7)
        self.cell(22, 5, k3, 1, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 7)
        self.cell(23, 5, str(v3), 1, 0, 'L')
        
        self.set_font('Helvetica', 'B', 7)
        self.cell(15, 5, k4, 1, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 7)
        self.cell(35, 5, str(v4), 1, 1, 'L')

    def draw_continuation_header(self, logo_path, report_id, client_name, project_name):
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=10, w=20)
            
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(26, 54, 93)
        self.set_xy(35, 10)
        self.cell(0, 5, 'Centauri Research Services - Radiographic Testing Continuation Report', 0, 1, 'L')
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(100, 116, 139)
        self.set_x(35)
        self.cell(0, 4, f'Report ID: {report_id} | Client: {client_name} | Project: {project_name}', 0, 1, 'L')
        self.ln(5)
        self.set_text_color(0, 0, 0) # reset

    def check_page_break_before_section(self, height_needed, logo_path, report_id, client_name, project_name):
        if self.get_y() + height_needed > 275:
            self.add_page()
            self.draw_continuation_header(logo_path, report_id, client_name, project_name)

    def draw_findings_table_header(self):
        self.set_fill_color(226, 232, 240)
        self.set_font('Helvetica', 'B', 7.5)
        
        # Save current position
        start_x = self.get_x()
        start_y = self.get_y()
        
        self.cell(15, 10, 'Item No', 1, 0, 'C', True)
        self.cell(45, 10, 'Weld ID / Spool No', 1, 0, 'C', True)
        self.cell(20, 10, 'Welder ID', 1, 0, 'C', True)
        self.cell(20, 10, 'Location', 1, 0, 'C', True)
        self.cell(50, 10, 'Observation', 1, 0, 'C', True)
        
        self.cell(40, 5, 'Disposition', 1, 1, 'C', True)
        
        # Position for ACCEPT / REJECT
        self.set_xy(start_x + 15 + 45 + 20 + 20 + 50, start_y + 5)
        self.cell(20, 5, 'ACCEPT', 1, 0, 'C', True)
        self.cell(20, 5, 'REJECT', 1, 1, 'C', True)
        self.set_font('Helvetica', '', 7)

    def create_report(self, output_path, data, image_path):
        """
        Assembles the high-fidelity NDT inspection report.
        """
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(True, 22)
        self.alias_nb_pages()
        self.add_page()
        
        # Retrieve values passed from the server
        report_id = data.get("report_id", "REP-20260607-001")
        thickness = data.get("thickness", 10.0)
        material = data.get("material", "Carbon Steel")
        reg_code = data.get("regulatory_code", "ASME B31.3")
        client_spec = data.get("client_spec", "None")
        other_std = data.get("other_standard", "None")
        app_type = data.get("app_type", "Piping")
        usage = data.get("usage", "Fabrication")
        
        # Seed random based on report ID to make it consistent for this report
        random.seed(hash(report_id))
        random_tel = f"+1 ({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        # 1. Logo and Header Layout
        logo_path = "assets/CR_logo.png"
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=10, w=35)
        
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(26, 54, 93)  # Dark Blue
        self.set_xy(50, 10)
        self.cell(85, 5, 'Centauri Research Services (L.L.C.)', 0, 0, 'L')
        
        self.set_font('Helvetica', '', 7)
        self.set_text_color(71, 85, 105)
        self.cell(65, 5, f'Tel: {random_tel}', 0, 1, 'L')
        
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(100, 116, 139)  # Slate Gray
        self.set_x(50)
        self.cell(85, 4, '(NDT & Inspection Services)', 0, 0, 'L')
        
        self.set_font('Helvetica', '', 7)
        self.set_text_color(71, 85, 105)
        self.cell(65, 4, 'Email: info@centauri-research.net', 0, 1, 'L')
        
        self.set_x(50)
        self.cell(85, 3.5, 'GTA, Toronto, Ontario', 0, 0, 'L')
        self.cell(65, 3.5, 'Website: www.centauri-research.net', 0, 1, 'L')
        
        self.set_x(50)
        self.cell(85, 3.5, '', 0, 1, 'L')
        self.set_x(50)
        self.cell(85, 3.5, '', 0, 1, 'L')
        
        self.ln(4)
        
        # Report Title Banner
        self.set_fill_color(226, 232, 240)  # Light gray-blue
        self.set_text_color(15, 23, 42)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 7, 'RADIOGRAPHIC TESTING REPORT', 1, 1, 'C', fill=True)
        
        # Parameters already retrieved at the start of the function
        
        clients = ["Chevron Corp.", "ExxonMobil NDT", "Shell Global Quality", "BP Pipeline Division", "Saudi Aramco Inspection", "TotalEnergies QA"]
        projects = ["CALL-OUT SERVICES AGREEMENT", "PIPELINE EXPANSION PHASE II", "OFFSHORE J-JACKET FABRICATION", "REFINERY CRACKER MAINTENANCE"]
        locations = ["RAK FZ", "Jebel Ali Free Zone", "Abu Dhabi Refinery", "Fujairah Port Terminal", "Mussafah Industrial Area"]
        procedures = ["P30379-30-99-90-9621 Rev-1", "P30379-30-99-90-9622 Rev-2", "P30379-30-99-90-9620 Rev-0"]
        drawings = ["P30379-14-71-25-9601-1-C / ISO-300087-101-1", "P30379-14-71-25-9602-2-C / ISO-300087-101-2"]
        equipments = ["D-7911-059", "D-7911-060", "D-7911-061"]
        
        client_name = random.choice(clients)
        project_name = random.choice(projects)
        job_no = str(random.randint(110000, 119999))
        project_no = str(random.randint(300000, 309999))
        welder_id = f"W-{random.randint(10, 99)}"
        wps_no = f"CESML-WPS-01{random.randint(0, 9)}"
        ins_location = random.choice(locations)
        procedure_ref = random.choice(procedures)
        drawing_ref = random.choice(drawings)
        equipment_sr = random.choice(equipments)
        
        current_date = datetime.date.today().strftime("%d-%m-%y")
        
        # Setup specific metadata routing details
        deviation_val = "NO"
        if other_std != "None":
            deviation_val = other_std
            
        procedure_val = procedure_ref
        if client_spec != "None":
            procedure_val = f"{procedure_ref} (Spec: {client_spec})"
            
        # 2. Metadata Grid block - 22 rows of metadata aligning with Lonestar structure
        # Row 1
        self.write_kv_4(
            "Inspection Date", current_date,
            "Issue Date", current_date,
            "Report No", report_id.split("-")[-1],
            "Rev #", "0"
        )
        # Row 2
        self.write_kv("Client", client_name, "Job #", job_no)
        # Row 3
        self.write_kv("Project", project_name, "Project no", project_no)
        # Row 4
        self.write_kv_full("Inspection Description", f"RT ON BUTT WELD JOINTS ({usage.upper()})")
        # Row 5
        self.write_kv("Inspection Location", ins_location, "Standard Method", "ASME SEC.V")
        # Row 6
        self.write_kv("Procedure", procedure_val, "Acceptance Criteria", reg_code)
        # Row 7
        self.write_kv("Standard Method Edition", "2023", "Acceptance Criteria Edition", "2023")
        # Row 8
        self.write_kv("DRG/ISO NO", drawing_ref, "Technique", "DWDI")
        # Row 9
        self.write_kv("Material Type", material, "IQI Used", "ASTM 1A")
        # Row 10
        self.write_kv("Material Thickness", f"{thickness} mm", "IQI Placement", "Source Side [X]  Film Side [ ]")
        # Row 11
        self.write_kv("Welding Process", "GTAW", "IQI Wire Required", "6th")
        # Row 12
        self.write_kv("Welding Reinforcement", "3 MM", "IQI Wire Achieved", "6th")
        # Row 13
        self.write_kv("Diameter/Length", "2\"", "Density", "2.2 to 3.5")
        # Row 14
        self.write_kv("Source Type", "IR-192", "Screens Thick (Front & Back)", "0.125MM")
        # Row 15
        self.write_kv("Source Size / Strength", "3.0x3.0MM / 20Ci", "Film Type / Manufacturer", "KODAK MX125")
        # Row 16
        self.write_kv("Exposure Time", "4 Mints", "Film Size/No of Radiographs", "10X24  NOS 2")
        # Row 17
        self.write_kv("SFD", "406 MM", "No of Films in Each Cassette", "1")
        # Row 18
        self.write_kv("SOD", "342.67 MM", "Equipement Sr.No", equipment_sr)
        # Row 19
        self.write_kv("OFD", "60.33+3 MM", "Omitted Scope (If Any)", "NO")
        # Row 20
        self.write_kv("Any Deviation / Addition to Scope", deviation_val, "Environmental Condition", "AMBIENT")
        # Row 21
        self.write_kv_full("Film Viewing", "Single [ ]  Double [X]")
        # Row 22
        self.write_kv_full("Equipment", f"{material.upper()} PIPE SPOOLS / WPS NO: {wps_no}")
        
        # 3. Results Table
        self.ln(2)
        self.draw_findings_table_header()
        
        findings = data.get("findings", [])
        
        if not findings:
            self.cell(15, 5, '1', 1, 0, 'C')
            self.cell(45, 5, f"SPOOL NO: 8TAG NO: 14-71-U-940P-01-J70", 1, 0, 'C')
            self.cell(20, 5, welder_id, 1, 0, 'C')
            self.cell(20, 5, 'A', 1, 0, 'C')
            self.cell(50, 5, 'NSI (No Significant Indication)', 1, 0, 'C')
            self.cell(20, 5, 'ACCEPT', 1, 0, 'C')
            self.cell(20, 5, '-', 1, 1, 'C')
        else:
            for idx, finding in enumerate(findings, 1):
                if self.get_y() + 5 > 275:
                    self.add_page()
                    self.draw_findings_table_header()
                    
                self.cell(15, 5, str(idx), 1, 0, 'C')
                self.cell(45, 5, f"SPOOL NO: 8TAG NO: 14-71-U-940P-01-J70", 1, 0, 'C')
                self.cell(20, 5, welder_id, 1, 0, 'C')
                
                # Letter locations A, B, C...
                loc_letter = chr(64 + idx) if idx <= 26 else str(idx)
                self.cell(20, 5, loc_letter, 1, 0, 'C')
                
                obs_text = f"{finding['type'].upper()} ({finding['size_mm']:.2f} mm)"
                self.cell(50, 5, obs_text, 1, 0, 'C')
                
                if finding['status'] == 'Accept':
                    self.cell(20, 5, 'ACCEPT', 1, 0, 'C')
                    self.cell(20, 5, '-', 1, 1, 'C')
                else:
                    self.cell(20, 5, '-', 1, 0, 'C')
                    self.cell(20, 5, 'REJECT', 1, 1, 'C')
                    
        # --- PAGE BREAK: Force Page 2 for Visuals, Comments, Signatures ---
        self.add_page()
        self.draw_continuation_header(logo_path, report_id, client_name, project_name)
        
        # 4. Radiograph Bounding Box Mapping Section
        # Needs 87mm of space
        self.check_page_break_before_section(87, logo_path, report_id, client_name, project_name)
        
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(241, 245, 249)
        self.cell(0, 5, 'RADIOGRAPHIC FILM ANALYSIS VISUAL MAPPING', 1, 1, 'L', True)
        self.ln(1)
        
        # Add visual image
        if os.path.exists(image_path):
            self.image(image_path, x=15, w=180, h=40)
            self.ln(41)  # Leave spacing for the image height
            
        # 5. Agent Reasoning Log Section
        reasoning_text = data.get("agent_reasoning", "No agent reasoning log available.")
        reasoning_text = str(reasoning_text).encode('latin-1', 'replace').decode('latin-1')
        approx_lines = max(2, len(reasoning_text) // 90)
        reasoning_height = approx_lines * 4 + 10.5
        
        self.check_page_break_before_section(reasoning_height, logo_path, report_id, client_name, project_name)
        
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(241, 245, 249)
        self.cell(0, 5, 'Agent Reasoning Log', 1, 1, 'L', True)
        self.ln(1.5)
        
        self.set_font('Helvetica', '', 7)
        self.multi_cell(0, 4, reasoning_text, 1, 'L')
        self.ln(2)
        
        status_state = data.get("status_state", 0)
        performer_comments = data.get("performer_comments", "")
        supervisor_comments = data.get("supervisor_comments", "")
        
        # 6. Performer Review Remarks Section (only if Stage >= 1)
        if status_state >= 1 and performer_comments:
            perf_text = str(performer_comments).encode('latin-1', 'replace').decode('latin-1')
            approx_lines = max(2, len(perf_text) // 90)
            performer_height = approx_lines * 4 + 14.5
            
            self.check_page_break_before_section(performer_height, logo_path, report_id, client_name, project_name)
            
            self.set_font('Helvetica', 'B', 8)
            self.set_fill_color(241, 245, 249)
            self.cell(0, 5, 'PERFORMER REVIEW REMARKS', 1, 1, 'L', True)
            self.ln(1.5)
            
            self.set_font('Helvetica', 'B', 7)
            self.cell(0, 4, 'Performed By: Andy Flower (ASNT Level II)', 0, 1, 'L')
            self.set_font('Helvetica', '', 7)
            self.multi_cell(0, 4, perf_text, 1, 'L')
            self.ln(2)
            
        # 7. Supervisor Evaluator Review Remarks Section (only if Stage >= 2)
        if status_state >= 2 and supervisor_comments:
            super_text = str(supervisor_comments).encode('latin-1', 'replace').decode('latin-1')
            approx_lines = max(2, len(super_text) // 90)
            supervisor_height = approx_lines * 4 + 14.5
            
            self.check_page_break_before_section(supervisor_height, logo_path, report_id, client_name, project_name)
            
            self.set_font('Helvetica', 'B', 8)
            self.set_fill_color(241, 245, 249)
            self.cell(0, 5, 'SUPERVISOR EVALUATOR REVIEW REMARKS', 1, 1, 'L', True)
            self.ln(1.5)
            
            self.set_font('Helvetica', 'B', 7)
            self.cell(0, 4, 'Evaluated By: Richard Campbell (PCN Level III)', 0, 1, 'L')
            self.set_font('Helvetica', '', 7)
            self.multi_cell(0, 4, super_text, 1, 'L')
            self.ln(2)
            
        # 8. Signatures blocks
        # Needs 18mm
        self.check_page_break_before_section(18, logo_path, report_id, client_name, project_name)
        
        self.set_font('Helvetica', 'B', 7.5)
        # Symmetrical blocks: 4 columns, total 190mm
        self.cell(47.5, 4, 'CENTAURI Performed By', 0, 0, 'L')
        self.cell(47.5, 4, 'CENTAURI Evaluated By', 0, 0, 'L')
        self.cell(47.5, 4, 'Contractor', 0, 0, 'L')
        self.cell(47.5, 4, 'Client', 0, 1, 'L')
        
        self.set_font('Helvetica', '', 7)
        self.cell(47.5, 4, 'Andy Flower', 0, 0, 'L')
        self.cell(47.5, 4, 'Richard Campbell', 0, 0, 'L')
        self.cell(47.5, 4, '', 0, 0, 'L')
        self.cell(47.5, 4, '', 0, 1, 'L')
        
        self.set_font('Helvetica', 'I', 6.5)
        self.cell(47.5, 4, 'ASNT Level II', 0, 0, 'L')
        self.cell(47.5, 4, 'PCN Level III', 0, 0, 'L')
        self.cell(47.5, 4, '', 0, 0, 'L')
        self.cell(47.5, 4, '', 0, 1, 'L')
        
        # Digital Signature stamp row
        self.set_font('Helvetica', 'B', 6.5)
        
        # Green text color for signed status
        if status_state >= 1:
            self.set_text_color(22, 163, 74)
            perf_sign = "[DIGITALLY SIGNED]"
        else:
            perf_sign = ""
            
        self.cell(47.5, 4, perf_sign, 0, 0, 'L')
        
        if status_state >= 2:
            self.set_text_color(22, 163, 74)
            super_sign = "[DIGITALLY SIGNED]"
        else:
            super_sign = ""
            
        self.cell(47.5, 4, super_sign, 0, 0, 'L')
        
        self.set_text_color(120, 120, 120) # reset to standard print color
        self.cell(47.5, 4, 'Signature & Stamp', 0, 0, 'L')
        self.cell(47.5, 4, 'Signature & Stamp', 0, 1, 'L')
        self.set_text_color(0, 0, 0)
        
        # 9. Abbreviations & Film Artifact Legend Block
        # Needs 27mm
        self.check_page_break_before_section(27, logo_path, report_id, client_name, project_name)
        
        self.ln(2)
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(226, 232, 240)
        self.cell(142.5, 4, 'ABBREVIATIONS', 1, 0, 'C', fill=True)
        self.cell(47.5, 4, 'FILM ARTIFACT', 1, 1, 'C', fill=True)
        
        self.set_font('Helvetica', '', 6)
        # Symmetrical blocks: 4 columns of 47.5mm each
        # Row 1
        self.cell(47.5, 3.5, 'NSI: No Significant Indication', 1, 0, 'L')
        self.cell(47.5, 3.5, 'BT: Burnthrough', 1, 0, 'L')
        self.cell(47.5, 3.5, 'SOD: Source to Object Distance', 1, 0, 'L')
        self.cell(47.5, 3.5, 'NM: Nail Mark', 1, 1, 'L')
        # Row 2
        self.cell(47.5, 3.5, 'RUC: Root Undercut', 1, 0, 'L')
        self.cell(47.5, 3.5, 'EP: Excessive Penetration', 1, 0, 'L')
        self.cell(47.5, 3.5, 'ELP: Elongated Porosity', 1, 0, 'L')
        self.cell(47.5, 3.5, 'FM: Film Mark', 1, 1, 'L')
        # Row 3
        self.cell(47.5, 3.5, 'RD: Root Depression', 1, 0, 'L')
        self.cell(47.5, 3.5, 'RRI: Random Rounded Indication', 1, 0, 'L')
        self.cell(47.5, 3.5, 'IF: Incomplete Fusion', 1, 0, 'L')
        self.cell(47.5, 3.5, 'PM: Process Mark', 1, 1, 'L')
        # Row 4
        self.cell(47.5, 3.5, 'External Undercut', 1, 0, 'L')
        self.cell(47.5, 3.5, 'LI: Linear Indication', 1, 0, 'L')
        self.cell(47.5, 3.5, 'I: Inclusion', 1, 0, 'L')
        self.cell(47.5, 3.5, 'CM: Chemical Mark', 1, 1, 'L')
        # Row 5
        self.cell(47.5, 3.5, 'SD: Surface Depression', 1, 0, 'L')
        self.cell(47.5, 3.5, 'IP: Inadequate Penetration', 1, 0, 'L')
        self.cell(47.5, 3.5, 'IGP: Isolated Gas Pore', 1, 0, 'L')
        self.cell(47.5, 3.5, 'SM: Screen Mark', 1, 1, 'L')
        # Row 6
        self.cell(47.5, 3.5, 'Root Concavity', 1, 0, 'L')
        self.cell(47.5, 3.5, 'TI: Tungsten Inclusion', 1, 0, 'L')
        self.cell(47.5, 3.5, 'Crack', 1, 0, 'L')
        self.cell(47.5, 3.5, '', 1, 1, 'L')

        # Output the PDF
        self.output(output_path)