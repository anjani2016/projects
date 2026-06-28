"""
DynamoDB adapter implementing the DatabasePort.

Table design (single-table pattern):
  PK (partition key)  = entity type prefix + ID
  SK (sort key)       = sub-type or timestamp

  Examples:
    PK="INSPECTION#REP-20260621-001"  SK="RECORD"
    PK="FEEDBACK#<uuid>"              SK="FEEDBACK"
    PK="VISION_CACHE#<image_hash>"    SK="CACHE"
    PK="AUDIT#<uuid>"                 SK="AUDIT"
    PK="STANDARD#<standard_id>"       SK="STANDARD"

Credential resolution (three-tier, automatic):
  1. Vercel Marketplace OIDC  — VERCEL_OIDC_TOKEN + AWS_ROLE_ARN (no static keys)
  2. Static IAM keys          — AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
  3. Default boto3 session    — ~/.aws/credentials or EC2/ECS instance role
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError

from src.core.domain.entities import InspectionRecord
from src.core.ports.database_port import DatabasePort

# ---------------------------------------------------------------------------
# Table name from environment (default matches .env template)
# ---------------------------------------------------------------------------
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "weld-inspections")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def _resolve_boto3_session() -> boto3.Session:
    """
    Resolve AWS credentials in priority order:
      1. Vercel Marketplace OIDC  (VERCEL_OIDC_TOKEN + AWS_ROLE_ARN)
      2. Static IAM keys          (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY)
      3. Default boto3 chain      (~/.aws/credentials, instance role, etc.)
    """
    oidc_token = os.getenv("VERCEL_OIDC_TOKEN")
    role_arn = os.getenv("AWS_ROLE_ARN")

    # ── Tier 1: Vercel OIDC ──────────────────────────────────────────────────
    if oidc_token and role_arn:
        sts = boto3.client("sts", region_name=AWS_REGION)
        assumed = sts.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName="vercel-python-oidc",
            WebIdentityToken=oidc_token,
        )["Credentials"]
        return boto3.Session(
            aws_access_key_id=assumed["AccessKeyId"],
            aws_secret_access_key=assumed["SecretAccessKey"],
            aws_session_token=assumed["SessionToken"],
            region_name=AWS_REGION,
        )

    # ── Tier 2: Static IAM keys ──────────────────────────────────────────────
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    if access_key and secret_key and access_key != "your_access_key_here":
        return boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=AWS_REGION,
        )

    # ── Tier 3: Default boto3 chain (local ~/.aws, EC2/ECS instance role) ───
    return boto3.Session(region_name=AWS_REGION)


def _record_to_item(record: InspectionRecord) -> Dict[str, Any]:
    """Serialize an InspectionRecord to a DynamoDB item dict."""
    item = record.__dict__.copy()
    item["PK"] = f"INSPECTION#{record.report_id}"
    item["SK"] = "RECORD"
    item["entity_type"] = "INSPECTION"
    item["updated_at"] = datetime.now(timezone.utc).isoformat()
    return item


def _item_to_record(item: Dict[str, Any]) -> InspectionRecord:
    """Deserialize a DynamoDB item dict back to an InspectionRecord."""
    # Remove DynamoDB-specific keys before reconstructing
    clean = {k: v for k, v in item.items() if k not in ("PK", "SK", "entity_type", "updated_at")}
    return InspectionRecord(**clean)


class DynamoDBAdapter(DatabasePort):
    """AWS DynamoDB implementation of DatabasePort (single-table design).

    Credentials are resolved automatically via _resolve_boto3_session():
      Tier 1 → Vercel OIDC  (Vercel Marketplace integration)
      Tier 2 → Static keys  (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)
      Tier 3 → Default boto3 chain (~/.aws, instance role)
    """

    def __init__(self) -> None:
        session = _resolve_boto3_session()
        dynamodb = session.resource("dynamodb")
        self.table = dynamodb.Table(TABLE_NAME)
        # Validate connection on startup
        try:
            self.table.load()
        except NoCredentialsError as exc:
            raise RuntimeError(
                "AWS credentials not found. Set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY in .env, or use the SQLite fallback."
            ) from exc
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ResourceNotFoundException":
                raise RuntimeError(
                    f"DynamoDB table '{TABLE_NAME}' does not exist in region "
                    f"'{AWS_REGION}'. Please provision it first."
                ) from exc
            raise

    # ── Inspections ─────────────────────────────────────────────────────────

    def save_record(self, record: InspectionRecord) -> str:
        item = _record_to_item(record)
        item["created_at"] = datetime.now(timezone.utc).isoformat()
        self.table.put_item(Item=item)
        return record.report_id

    def update_record(self, record: InspectionRecord) -> None:
        item = _record_to_item(record)
        # Build a dynamic UpdateExpression from the item fields
        expr_names: Dict[str, str] = {}
        expr_values: Dict[str, Any] = {}
        updates: List[str] = []
        for key, val in item.items():
            if key in ("PK", "SK"):
                continue
            safe_key = f"#f_{key}"
            expr_names[safe_key] = key
            expr_values[f":v_{key}"] = val
            updates.append(f"{safe_key} = :v_{key}")
        self.table.update_item(
            Key={"PK": item["PK"], "SK": "RECORD"},
            UpdateExpression="SET " + ", ".join(updates),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    def get_records(self) -> List[InspectionRecord]:
        # Scan for all INSPECTION records (fine for hackathon scale)
        response = self.table.scan(
            FilterExpression=Key("entity_type").eq("INSPECTION")
            # For production, use a GSI on entity_type
        )
        return [_item_to_record(item) for item in response.get("Items", [])]

    def get_record_by_report_id(self, report_id: str) -> Optional[InspectionRecord]:
        response = self.table.get_item(Key={"PK": f"INSPECTION#{report_id}", "SK": "RECORD"})
        item = response.get("Item")
        return _item_to_record(item) if item else None

    def generate_report_id(self) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"INSPECTION#{today}"
        # Count today's records to generate a sequential suffix
        response = self.table.scan(
            FilterExpression="begins_with(PK, :prefix)",
            ExpressionAttributeValues={":prefix": prefix},
            Select="COUNT",
        )
        seq = response.get("Count", 0) + 1
        return f"REP-{today}-{seq:03d}"

    # ── Technician Feedback ──────────────────────────────────────────────────

    def save_feedback(self, feedback: Dict[str, Any]) -> str:
        feedback_id = str(uuid.uuid4())
        item = {
            **feedback,
            "PK": f"FEEDBACK#{feedback_id}",
            "SK": "FEEDBACK",
            "entity_type": "FEEDBACK",
            "feedback_id": feedback_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.table.put_item(Item=item)
        return feedback_id

    def get_feedback(self) -> List[Dict[str, Any]]:
        response = self.table.scan(
            FilterExpression=Key("entity_type").eq("FEEDBACK")
        )
        return response.get("Items", [])

    # ── Vision Inference Cache ───────────────────────────────────────────────

    def get_vision_cache(self, image_hash: str) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(Key={"PK": f"VISION_CACHE#{image_hash}", "SK": "CACHE"})
        return response.get("Item")

    def save_vision_cache(self, image_hash: str, detections: Dict[str, Any]) -> str:
        item = {
            **detections,
            "PK": f"VISION_CACHE#{image_hash}",
            "SK": "CACHE",
            "entity_type": "VISION_CACHE",
            "image_hash": image_hash,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        self.table.put_item(Item=item)
        return image_hash

    # ── Enterprise Audit Trails ──────────────────────────────────────────────

    def log_audit_event(self, event: Dict[str, Any]) -> str:
        audit_id = str(uuid.uuid4())
        item = {
            **event,
            "PK": f"AUDIT#{audit_id}",
            "SK": "AUDIT",
            "entity_type": "AUDIT",
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.table.put_item(Item=item)
        return audit_id

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        response = self.table.scan(
            FilterExpression=Key("entity_type").eq("AUDIT")
        )
        return response.get("Items", [])

    # ── Compliance Standards ─────────────────────────────────────────────────

    def save_compliance_standard(self, standard: Dict[str, Any]) -> str:
        standard_id = standard.get("standard_id", str(uuid.uuid4()))
        item = {
            **standard,
            "PK": f"STANDARD#{standard_id}",
            "SK": "STANDARD",
            "entity_type": "STANDARD",
            "standard_id": standard_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.table.put_item(Item=item)
        return standard_id

    def get_compliance_standard(self, standard_id: str) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(
            Key={"PK": f"STANDARD#{standard_id}", "SK": "STANDARD"}
        )
        return response.get("Item")

    def clear_records(self) -> None:
        """Scan and delete all items from the DynamoDB table."""
        try:
            scan = self.table.scan()
            with self.table.batch_writer() as batch:
                for each in scan.get("Items", []):
                    batch.delete_item(
                        Key={
                            "PK": each["PK"],
                            "SK": each["SK"]
                        }
                    )
        except Exception as e:
            raise RuntimeError(f"Failed to clear DynamoDB table: {e}")
