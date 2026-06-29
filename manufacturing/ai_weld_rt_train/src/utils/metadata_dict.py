# 2. Metadata Dictionary (for Rule Engine / ETL)

RT_METADATA_MODEL = {
    "image_id": "Unique identifier for RT image",
    "stream": "piping | pipeline | structural | castings",
    "welding_process": "TIG | SMAW | SAW | ARC | LSAW | HSAW",
    "material": "Carbon Steel | DSS | SDSS | Cu-Ni | Alloy",
    "iqi_detected": True,
    "iqi_wire_number": "Integer wire index",
    "pixel_to_mm_scale": "Float conversion factor",
    "environment": "Open Yard | Controlled Shed",
    "temperature": "Ambient temperature at time of weld",
    "timestamp": "ISO 8601 datetime",
    "operator_id": "Welder or machine ID",
    "inspector_id": "Level II/III inspector",
    "client": "Shell | BP | ADNOC | Other",
    "weld_procedure": "WPS/PQR reference",
    "ndt_corroboration": ["MPT", "DPT"],
    "regulatory_code": "ASME B31.3 | API 1104 | AWS D1.1 | ASME VIII",
    "defects_detected": [
        {
            "type": "porosity | slag | crack | lack_of_penetration",
            "bbox": [x1, y1, x2, y2],
            "size_mm": "Float",
            "acceptance_status": "ACCEPT | REJECT"
        }
    ]
}
