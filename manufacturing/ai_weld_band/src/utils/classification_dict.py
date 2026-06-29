#1. Classification Dictionary (Python‑ready)

RT_CLASSIFICATION = {
    "primary_streams": {
        "piping": "Process piping for refineries, chemical plants, power generation",
        "pipeline": "Transmission pipelines including HSAW and LSAW",
        "structural": "Load-bearing weldments, offshore and civil structures",
        "castings": "Valves, pumps, and complex casting geometries"
    },

    "welding_processes": {
        "standard": ["TIG (GTAW)", "SMAW", "SAW", "ARC"],
        "pipeline_specific": ["LSAW", "HSAW"]
    },

    "material_of_construction": {
        "carbon_steel": ["ASTM A106", "ASTM A333"],
        "corrosion_resistant": ["SS", "DSS", "SDSS"],
        "special_alloys": ["Cu-Ni", "High-performance alloys"]
    },

    "regulatory": {
        "global_codes": [
            "ASME B31.3",
            "API 1104",
            "AWS D1.1",
            "ASME Section VIII"
        ],
        "client_specs": {
            "Shell": "DEP",
            "BP": "GP",
            "ADNOC": "Technical Standards"
        }
    },

    "environmental_metadata": {
        "environment": ["Open Yard", "Controlled Shed"],
        "temperature_effects": "High/low ambient temperature affecting HAZ cooling",
        "temporal": "Timestamped logging"
    },

    "actors": {
        "operators": "Welding personnel + machine IDs",
        "inspectors": "Level II/III RT technicians",
        "clients": "Final acceptance authority"
    },

    "documentation": {
        "procedures": ["WPS", "PQR"],
        "corroborative_reports": ["MPT", "DPT"]
    }
}
