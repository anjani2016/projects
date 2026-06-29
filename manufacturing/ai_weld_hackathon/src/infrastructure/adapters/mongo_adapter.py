import sqlite3
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import MongoClient

from src.core.ports.database_port import DatabasePort
from src.core.domain.entities import InspectionRecord

class MongoAdapter(DatabasePort):
    def __init__(self, connection_string: str, sqlite_path: str = "data/local_ndt.db"):
        self.connection_string = connection_string
        self.sqlite_path = sqlite_path
        self.use_sqlite = False
        
        # Determine if we should force SQLite right away
        if not self.connection_string or self.connection_string == "mcp://mongodb.partner.local":
            self.use_sqlite = True
            logging.info("MongoDB URI is empty or placeholder. Forcing local SQLite fallback.")
            self._init_sqlite()
        
        # Prepopulate default standards
        try:
            self._prepopulate_standards()
        except Exception as e:
            logging.warning(f"Failed to prepopulate default standards on startup: {e}")

    def _init_sqlite(self):
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # Schema migration helper: Check if report_id column exists
        try:
            cursor.execute("SELECT report_id FROM weld_reports LIMIT 1")
        except sqlite3.OperationalError:
            logging.info("SQLite schema outdated. Recreating tables for unique report logging...")
            cursor.execute("DROP TABLE IF EXISTS weld_reports")
            
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weld_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT,
                image_id TEXT,
                thickness REAL,
                model_used TEXT,
                verdict TEXT,
                details TEXT,
                raw_image_path TEXT,
                annotated_image_path TEXT,
                timestamp TEXT,
                performer_comments TEXT,
                supervisor_comments TEXT,
                status_state INTEGER,
                material TEXT,
                regulatory_code TEXT,
                client_spec TEXT,
                other_standard TEXT,
                app_type TEXT,
                usage TEXT
            )
        """)

        # Run column migration check
        migration_cols = [
            ("performer_comments", "TEXT"),
            ("supervisor_comments", "TEXT"),
            ("status_state", "INTEGER"),
            ("material", "TEXT"),
            ("regulatory_code", "TEXT"),
            ("client_spec", "TEXT"),
            ("other_standard", "TEXT"),
            ("app_type", "TEXT"),
            ("usage", "TEXT")
        ]
        for col_name, col_type in migration_cols:
            try:
                cursor.execute(f"SELECT {col_name} FROM weld_reports LIMIT 1")
            except sqlite3.OperationalError:
                logging.info(f"Adding column {col_name} to weld_reports...")
                cursor.execute(f"ALTER TABLE weld_reports ADD COLUMN {col_name} {col_type} DEFAULT NULL")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technician_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT,
                technician_id TEXT,
                original_verdict TEXT,
                corrected_verdict TEXT,
                comments TEXT,
                timestamp TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vision_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_hash TEXT UNIQUE,
                detections TEXT,
                timestamp TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                standard_id TEXT UNIQUE,
                name TEXT,
                rules TEXT,
                markdown_content TEXT,
                timestamp TEXT
            )
        """)
        
        # Migration check for compliance_standards table
        try:
            cursor.execute("SELECT markdown_content FROM compliance_standards LIMIT 1")
        except sqlite3.OperationalError:
            logging.info("Adding column markdown_content to compliance_standards...")
            cursor.execute("ALTER TABLE compliance_standards ADD COLUMN markdown_content TEXT DEFAULT NULL")
            
        conn.commit()
        conn.close()

    def _prepopulate_standards(self):
        standards_list = [
            {
                "standard_id": "ASME_SEC_8_D1",
                "name": "ASME VIII Div 1",
                "rules": {
                    "domain": "Pressure Vessels",
                    "material": "Carbon Steel",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Rules for design, fabrication, inspection, and testing of pressure vessels operating at pressures >15 psig.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "ASME_SEC_8_D2",
                "name": "ASME VIII Div 2",
                "rules": {
                    "domain": "Pressure Vessels",
                    "material": "Carbon Steel",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Alternative, more stringent rules for pressure vessels allowing higher design stresses and reduced material thickness.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.25,
                    "inclusion_limit_ratio": 0.4
                }
            },
            {
                "standard_id": "ASME_B31_3",
                "name": "ASME B31.3",
                "rules": {
                    "domain": "Piping",
                    "material": "Carbon Steel | Stainless Steel",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Requirements for process piping in petroleum refineries, chemical, pharmaceutical, and other industrial plants.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "ASME_B31_1",
                "name": "ASME B31.1",
                "rules": {
                    "domain": "Piping",
                    "material": "Carbon Steel",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Requirements for power piping typically found in electric generating stations and industrial/institutional boiler plants.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "ASME_SEC_9",
                "name": "ASME IX",
                "rules": {
                    "domain": "Qualification",
                    "material": "Carbon Steel | Stainless Steel | Aluminum",
                    "usage": "Qualification",
                    "scope": "Universal standard for qualifying welding procedures (WPS/PQR) and personnel (WPQ) across ASME projects.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "AWS_D1_1",
                "name": "AWS D1.1",
                "rules": {
                    "domain": "Structural",
                    "material": "Carbon Steel",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Welding requirements for structural steel elements made of carbon and low-alloy constructional steels.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "AWS_D1_2",
                "name": "AWS D1.2",
                "rules": {
                    "domain": "Structural",
                    "material": "Aluminum",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Requirements for welding structural aluminum alloys in static and cyclic loaded applications.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "AWS_D1_6",
                "name": "AWS D1.6",
                "rules": {
                    "domain": "Structural",
                    "material": "Stainless Steel",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Requirements for welding structural stainless steel components.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "AWS_D1_5",
                "name": "AWS D1.5",
                "rules": {
                    "domain": "Structural",
                    "material": "Carbon Steel",
                    "usage": "Design | Fabrication | Inspection",
                    "scope": "Specialized requirements for welding steel highway and railway bridges.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "API_1104",
                "name": "API 1104",
                "rules": {
                    "domain": "Pipeline",
                    "material": "Carbon Steel",
                    "usage": "Fabrication | Inspection",
                    "scope": "Standards for gas and arc welding of pipelines and related facilities for transmission of petroleum and fuel gases.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "API_650",
                "name": "API 650",
                "rules": {
                    "domain": "Storage Tanks",
                    "material": "Carbon Steel | Stainless Steel | Aluminum",
                    "usage": "Design | Fabrication",
                    "scope": "Design, material, fabrication, and testing for vertical, cylindrical, atmospheric-pressure welded steel storage tanks.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "API_653",
                "name": "API 653",
                "rules": {
                    "domain": "Inspection",
                    "material": "Carbon Steel",
                    "usage": "Inspection",
                    "scope": "Minimum requirements for maintaining the integrity of in-service atmospheric aboveground storage tanks.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            },
            {
                "standard_id": "API_570",
                "name": "API 570",
                "rules": {
                    "domain": "Inspection",
                    "material": "Carbon Steel",
                    "usage": "Inspection",
                    "scope": "Standards for the inspection, repair, alteration, and rerating of in-service metallic piping systems.",
                    "crack": "ALWAYS REJECT",
                    "lack_of_fusion": "ALWAYS REJECT",
                    "porosity_limit_ratio": 0.333,
                    "inclusion_limit_ratio": 0.5
                }
            }
        ]
        for std in standards_list:
            std_id = std["standard_id"]
            markdown_content = ""
            # Load local markdown rules if available (checks standard folders)
            for folder in ["data/rules/standards", "rules/standards", "data/rules", "rules"]:
                for name in [std_id, std_id.lower(), std["name"], std["name"].lower()]:
                    for ext in [".md", ".txt"]:
                        path = os.path.join(folder, f"{name}{ext}")
                        if os.path.exists(path):
                            try:
                                with open(path, "r", encoding="utf-8") as f:
                                    markdown_content = f.read()
                                    break
                            except Exception:
                                pass
                    if markdown_content:
                        break
                if markdown_content:
                    break
            
            if markdown_content:
                std["markdown_content"] = markdown_content
            else:
                # Fallback to generated markdown content
                std["markdown_content"] = (
                    f"# {std['name']} Compliance Standard\n\n"
                    f"**Domain**: {std['rules']['domain']}\n"
                    f"**Material**: {std['rules']['material']}\n"
                    f"**Usage**: {std['rules']['usage']}\n\n"
                    f"### Acceptance Criteria:\n"
                    f"- Cracks and Lack of Fusion are **{std['rules']['crack']}**.\n"
                    f"- Porosity length must be less than `Thickness * {std['rules']['porosity_limit_ratio']}`.\n"
                    f"- Inclusions must be less than `Thickness * {std['rules']['inclusion_limit_ratio']}`.\n"
                )

            existing = self.get_compliance_standard(std_id)
            if not existing or "domain" not in existing.get("rules", {}) or not existing.get("markdown_content"):
                self.save_compliance_standard(std)

    def generate_report_id(self) -> str:
        today_str = datetime.utcnow().strftime("%Y%m%d")
        today_date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                collection = db["weld_reports"]
                
                count = collection.count_documents({"timestamp": {"$regex": f"^{today_date_str}"}})
                return f"REP-{today_str}-{(count + 1):03d}"
            except Exception as e:
                logging.warning(f"Failed to query MongoDB count, falling back to SQLite for ID generation: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        # SQLite ID generation
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM weld_reports WHERE timestamp LIKE ?", (f"{today_date_str}%",))
            count = cursor.fetchone()[0]
            conn.close()
            return f"REP-{today_str}-{(count + 1):03d}"
        except Exception as sqlite_err:
            logging.error(f"Failed to generate report ID from SQLite: {sqlite_err}")
            # Fallback to pure timestamp if database queries fail
            return f"REP-{today_str}-{datetime.utcnow().strftime('%H%M%S')}"

    def save_record(self, record: InspectionRecord) -> str:
        if not record.timestamp:
            record.timestamp = datetime.utcnow().isoformat() + "Z"

        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                # Quick ping to check connection
                client.admin.command('ping')
                db = client["ndt_inspections"]
                collection = db["weld_reports"]
                
                # Exclude 'id' field from document when inserting to Mongo if it is None
                doc = record.model_dump(exclude_none=True)
                if 'id' in doc:
                    del doc['id']
                insert_result = collection.insert_one(doc)
                return f"Successfully logged the {record.verdict} verdict to the MongoDB MCP server with ID {insert_result.inserted_id}."
            except Exception as e:
                logging.warning(f"Failed to connect to MongoDB, falling back to local SQLite: {e}")
                # Fall back to SQLite for this and future queries in this instance lifecycle
                self.use_sqlite = True
                self._init_sqlite()

        # Save to SQLite
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weld_reports (report_id, image_id, thickness, model_used, verdict, details, raw_image_path, annotated_image_path, timestamp, performer_comments, supervisor_comments, status_state, material, regulatory_code, client_spec, other_standard, app_type, usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (record.report_id, record.image_id, record.thickness, record.model_used, record.verdict, record.details, record.raw_image_path, record.annotated_image_path, record.timestamp, record.performer_comments, record.supervisor_comments, record.status_state, record.material, record.regulatory_code, record.client_spec, record.other_standard, record.app_type, record.usage))
            conn.commit()
            row_id = cursor.lastrowid
            conn.close()
            return f"Successfully logged the {record.verdict} verdict to the local SQLite database with ID {row_id}."
        except Exception as sqlite_err:
            return f"Database error: Failed to save record to either MongoDB or SQLite: {str(sqlite_err)}"

    def update_record(self, record: InspectionRecord) -> None:
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                collection = db["weld_reports"]
                
                doc = record.model_dump(exclude_none=True)
                if 'id' in doc:
                    del doc['id']
                collection.update_one({"report_id": record.report_id}, {"$set": doc})
                return
            except Exception as e:
                logging.warning(f"Failed to update record in MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE weld_reports
                SET performer_comments = ?, supervisor_comments = ?, status_state = ?, verdict = ?, details = ?, material = ?, regulatory_code = ?, client_spec = ?, other_standard = ?, app_type = ?, usage = ?
                WHERE report_id = ?
            """, (record.performer_comments, record.supervisor_comments, record.status_state, record.verdict, record.details, record.material, record.regulatory_code, record.client_spec, record.other_standard, record.app_type, record.usage, record.report_id))
            conn.commit()
            conn.close()
        except Exception as sqlite_err:
            logging.error(f"Failed to update record in SQLite: {sqlite_err}")

    def get_records(self) -> List[InspectionRecord]:
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                collection = db["weld_reports"]
                
                cursor = collection.find().sort("timestamp", -1)
                records = []
                for doc in cursor:
                    doc['id'] = str(doc.get('_id'))
                    records.append(InspectionRecord(**doc))
                return records
            except Exception as e:
                logging.warning(f"Failed to fetch from MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()

        # Fetch from SQLite
        try:
            conn = sqlite3.connect(self.sqlite_path)
            # Row factory to get dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM weld_reports ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            records = []
            for row in rows:
                record_dict = dict(row)
                record_dict['id'] = str(record_dict['id'])
                records.append(InspectionRecord(**record_dict))
            conn.close()
            return records
        except Exception as sqlite_err:
            logging.error(f"Failed to fetch from SQLite database: {sqlite_err}")
            return []

    def get_record_by_report_id(self, report_id: str) -> Optional[InspectionRecord]:
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                collection = db["weld_reports"]
                doc = collection.find_one({"report_id": report_id})
                if doc:
                    doc['id'] = str(doc.get('_id'))
                    return InspectionRecord(**doc)
            except Exception as e:
                logging.warning(f"Failed to fetch from MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM weld_reports WHERE report_id = ?", (report_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                record_dict = dict(row)
                record_dict['id'] = str(record_dict['id'])
                return InspectionRecord(**record_dict)
        except Exception as sqlite_err:
            logging.error(f"Failed to fetch from SQLite database for report {report_id}: {sqlite_err}")
        return None

    def clear_records(self):
        """Clears all records. Primarily used for unit testing."""
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                db["weld_reports"].delete_many({})
                db["technician_feedback"].delete_many({})
                db["vision_cache"].delete_many({})
                db["audit_logs"].delete_many({})
                db["compliance_standards"].delete_many({})
            except Exception as e:
                pass
        
        # Clear SQLite
        if os.path.exists(self.sqlite_path):
            try:
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM weld_reports")
                cursor.execute("DELETE FROM technician_feedback")
                cursor.execute("DELETE FROM vision_cache")
                cursor.execute("DELETE FROM audit_logs")
                cursor.execute("DELETE FROM compliance_standards")
                conn.commit()
                conn.close()
            except Exception:
                pass
                
        # Clean up local image files in inspections directory
        inspections_dir = "data/inspections"
        if os.path.exists(inspections_dir):
            try:
                for sub in ["raw", "annotated"]:
                    sub_path = os.path.join(inspections_dir, sub)
                    if os.path.exists(sub_path):
                        for f in os.listdir(sub_path):
                            file_path = os.path.join(sub_path, f)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
            except Exception as e:
                logging.error(f"Failed to clear files: {e}")

    # --- Technician Feedback ---
    def save_feedback(self, feedback: Dict[str, Any]) -> str:
        if "timestamp" not in feedback:
            feedback["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                # Exclude '_id' in the feedback if present
                doc = feedback.copy()
                if '_id' in doc:
                    del doc['_id']
                insert_result = db["technician_feedback"].insert_one(doc)
                return str(insert_result.inserted_id)
            except Exception as e:
                logging.warning(f"Failed to save feedback to MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO technician_feedback (report_id, technician_id, original_verdict, corrected_verdict, comments, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                feedback.get("report_id"),
                feedback.get("technician_id"),
                feedback.get("original_verdict"),
                feedback.get("corrected_verdict"),
                feedback.get("comments"),
                feedback["timestamp"]
            ))
            conn.commit()
            row_id = cursor.lastrowid
            conn.close()
            return str(row_id)
        except Exception as sqlite_err:
            logging.error(f"Failed to save feedback to SQLite: {sqlite_err}")
            return ""

    def get_feedback(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                cursor = db["technician_feedback"].find().sort("timestamp", -1)
                results = []
                for doc in cursor:
                    doc["id"] = str(doc.get("_id"))
                    del doc["_id"]
                    results.append(doc)
                return results
            except Exception as e:
                logging.warning(f"Failed to fetch feedback from MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM technician_feedback ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as sqlite_err:
            logging.error(f"Failed to fetch feedback from SQLite: {sqlite_err}")
            return []

    # --- Vision Inference Caching ---
    def get_vision_cache(self, image_hash: str) -> Optional[Dict[str, Any]]:
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                doc = db["vision_cache"].find_one({"image_hash": image_hash})
                if doc:
                    del doc["_id"]
                    return doc
                return None
            except Exception as e:
                logging.warning(f"Failed to fetch vision cache from MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vision_cache WHERE image_hash = ?", (image_hash,))
            row = cursor.fetchone()
            conn.close()
            if row:
                result = dict(row)
                result["detections"] = json.loads(result["detections"])
                return result
            return None
        except Exception as sqlite_err:
            logging.error(f"Failed to fetch vision cache from SQLite: {sqlite_err}")
            return None

    def save_vision_cache(self, image_hash: str, detections: Dict[str, Any]) -> str:
        timestamp = datetime.utcnow().isoformat() + "Z"
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                db["vision_cache"].update_one(
                    {"image_hash": image_hash},
                    {"$set": {"detections": detections, "timestamp": timestamp}},
                    upsert=True
                )
                return image_hash
            except Exception as e:
                logging.warning(f"Failed to save vision cache to MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO vision_cache (image_hash, detections, timestamp)
                VALUES (?, ?, ?)
            """, (image_hash, json.dumps(detections), timestamp))
            conn.commit()
            conn.close()
            return image_hash
        except Exception as sqlite_err:
            logging.error(f"Failed to save vision cache to SQLite: {sqlite_err}")
            return ""

    # --- Enterprise Audit Trails (SOC 2) ---
    def log_audit_event(self, event: Dict[str, Any]) -> str:
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                doc = event.copy()
                if '_id' in doc:
                    del doc['_id']
                insert_result = db["audit_logs"].insert_one(doc)
                return str(insert_result.inserted_id)
            except Exception as e:
                logging.warning(f"Failed to log audit event to MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, details, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                event.get("user_id"),
                event.get("action"),
                event.get("details"),
                event["timestamp"]
            ))
            conn.commit()
            row_id = cursor.lastrowid
            conn.close()
            return str(row_id)
        except Exception as sqlite_err:
            logging.error(f"Failed to log audit event to SQLite: {sqlite_err}")
            return ""

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                cursor = db["audit_logs"].find().sort("timestamp", -1)
                results = []
                for doc in cursor:
                    doc["id"] = str(doc.get("_id"))
                    del doc["_id"]
                    results.append(doc)
                return results
            except Exception as e:
                logging.warning(f"Failed to fetch audit logs from MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as sqlite_err:
            logging.error(f"Failed to fetch audit logs from SQLite: {sqlite_err}")
            return []

    # --- Compliance Standards ---
    def save_compliance_standard(self, standard: Dict[str, Any]) -> str:
        if "timestamp" not in standard:
            standard["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
        standard_id = standard.get("standard_id")
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                doc = standard.copy()
                if '_id' in doc:
                    del doc['_id']
                db["compliance_standards"].update_one(
                    {"standard_id": standard_id},
                    {"$set": doc},
                    upsert=True
                )
                return standard_id
            except Exception as e:
                logging.warning(f"Failed to save compliance standard to MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO compliance_standards (standard_id, name, rules, markdown_content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                standard_id,
                standard.get("name"),
                json.dumps(standard.get("rules")),
                standard.get("markdown_content"),
                standard["timestamp"]
            ))
            conn.commit()
            conn.close()
            return standard_id
        except Exception as sqlite_err:
            logging.error(f"Failed to save compliance standard to SQLite: {sqlite_err}")
            return ""

    def get_compliance_standard(self, standard_id: str) -> Optional[Dict[str, Any]]:
        ids_to_try = [standard_id]
        if "." in standard_id:
            ids_to_try.append(standard_id.replace(".", "_"))
        if "_" in standard_id:
            ids_to_try.append(standard_id.replace("_", "."))
            
        for sid in ids_to_try:
            res = self._get_compliance_standard_direct(sid)
            if res:
                return res
        return None

    def _get_compliance_standard_direct(self, standard_id: str) -> Optional[Dict[str, Any]]:
        if not self.use_sqlite:
            try:
                client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                db = client["ndt_inspections"]
                doc = db["compliance_standards"].find_one({"standard_id": standard_id})
                if doc:
                    del doc["_id"]
                    return doc
                return None
            except Exception as e:
                logging.warning(f"Failed to fetch compliance standard from MongoDB, falling back to SQLite: {e}")
                self.use_sqlite = True
                self._init_sqlite()
                
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compliance_standards WHERE standard_id = ?", (standard_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                result = dict(row)
                result["rules"] = json.loads(result["rules"])
                return result
            return None
        except Exception as sqlite_err:
            logging.error(f"Failed to fetch compliance standard from SQLite: {sqlite_err}")
            return None


