from fpdf import FPDF
import datetime

class WeldReporter(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'NDT Radiography Inspection Report', 0, 1, 'C')
        self.ln(5)

    def create_report(self, output_path, data, image_path):
        """
        Assembles the final PDF document.
        """
        self.add_page()
        self.set_font('Arial', '', 12)
        
        # Project Metadata
        self.cell(0, 10, f"Date: {datetime.date.today()}", 0, 1)
        self.cell(0, 10, f"Standard: {data['standard']}", 0, 1)
        self.ln(10)

        # Annotated Image
        self.image(image_path, x=10, w=180)
        self.ln(10)

        # Results Table
        self.set_fill_color(230, 230, 230)
        self.cell(50, 10, 'Defect Type', 1, 0, 'C', True)
        self.cell(40, 10, 'Size (mm)', 1, 0, 'C', True)
        self.cell(100, 10, 'ASME B31.3 Status', 1, 1, 'C', True)

        for finding in data['findings']:
            self.cell(50, 10, finding['type'], 1)
            self.cell(40, 10, f"{finding['size_mm']:.2f}", 1)
            self.cell(100, 10, finding['status'], 1, 1)

        self.output(output_path)