import os
import sys
import json
import logging
import requests
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

class AlibabaCloudHelper:
    """
    Official Alibaba Cloud Integration Helper for the Qwen Cloud AI Weld Inspector.
    Demonstrates active usage of Alibaba Cloud services (DashScope API and ApsaraDB for MongoDB).
    
    This file serves as the official proof file link for Alibaba Cloud Integration.
    """
    def __init__(self):
        self.dashscope_api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY")
        self.mongodb_uri = os.environ.get("MONGODB_URI") or os.environ.get("ALIBABA_CLOUD_MONGODB_URI")
        self.dashscope_endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def verify_dashscope_connection(self, model_name: str = "qwen-max") -> bool:
        """
        Verifies connectivity to Alibaba Cloud's DashScope ModelStudio Qwen API.
        Uses the official compatible-mode endpoint to perform a basic handshake.
        """
        if not self.dashscope_api_key:
            logging.error("Alibaba Cloud DashScope API Key is not set in environment (DASHSCOPE_API_KEY or QWEN_API_KEY).")
            return False

        headers = {
            "Authorization": f"Bearer {self.dashscope_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Ping: Verify connection to Qwen Cloud."}
            ]
        }
        
        logging.info("Testing connection to Alibaba Cloud DashScope API...")
        try:
            response = requests.post(self.dashscope_endpoint, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                resp_data = response.json()
                reply = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                logging.info(f"Successfully connected to Qwen Cloud! Response: '{reply}'")
                return True
            else:
                logging.error(f"DashScope handshake failed. HTTP Code: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Failed to connect to DashScope: {e}")
            return False

    def verify_apsaradb_mongodb_connection(self) -> bool:
        """
        Verifies connectivity to Alibaba Cloud ApsaraDB for MongoDB.
        Establishes a MongoClient connection and pings the database server.
        """
        if not self.mongodb_uri:
            logging.error("Alibaba Cloud MongoDB URI is not set in environment (MONGODB_URI or ALIBABA_CLOUD_MONGODB_URI).")
            return False

        logging.info("Testing connection to Alibaba Cloud ApsaraDB for MongoDB...")
        try:
            # Short timeout to avoid stalling CLI validation
            client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Send standard ping command
            client.admin.command('ping')
            logging.info("Successfully connected to Alibaba Cloud ApsaraDB MongoDB cluster!")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Alibaba Cloud ApsaraDB for MongoDB: {e}")
            return False

    def print_diagnostics(self):
        """Runs diagnostics and prints status reporting."""
        print("="*60)
        print(" ALIBABA CLOUD INTEGRATION DIAGNOSTICS & HACKATHON PROOF ")
        print("="*60)
        
        # 1. DashScope Status
        dashscope_ok = self.verify_dashscope_connection()
        print(f"Alibaba Cloud DashScope (Qwen) Connection: {'✅ SUCCESS' if dashscope_ok else '❌ FAILED/UNCONFIGURED'}")
        
        # 2. ApsaraDB MongoDB Status
        mongo_ok = self.verify_apsaradb_mongodb_connection()
        print(f"Alibaba Cloud ApsaraDB for MongoDB Connection: {'✅ SUCCESS' if mongo_ok else '❌ FAILED/UNCONFIGURED (Running in SQLite Failover Mode)'}")
        
        print("="*60)
        print("Diagnostic check completed.")
        print("="*60)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    helper = AlibabaCloudHelper()
    helper.print_diagnostics()
