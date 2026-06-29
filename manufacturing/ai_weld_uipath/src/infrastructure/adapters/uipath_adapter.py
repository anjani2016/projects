import os
import logging
import requests
from typing import Dict, Any, Optional
from src.core.ports.uipath_port import UiPathPort

class UiPathAdapter(UiPathPort):
    def __init__(self):
        # Read configurations from environment variables
        self.client_id = os.environ.get("UIPATH_CLIENT_ID", "")
        self.client_secret = os.environ.get("UIPATH_CLIENT_SECRET", "")
        self.org_name = os.environ.get("UIPATH_ORG_NAME", "")
        self.tenant_name = os.environ.get("UIPATH_TENANT_NAME", "")
        self.folder_id = os.environ.get("UIPATH_FOLDER_ID", "")
        self.api_url = os.environ.get("API_URL", "http://localhost:8000")
        self.uipath_domain = os.environ.get("UIPATH_DOMAIN", "cloud.uipath.com")
        
        # Determine if we are in real or mock mode
        self.is_mock = not (self.client_id and self.client_secret and self.org_name and self.tenant_name)
        if self.is_mock:
            logging.info("UiPathAdapter running in SIMULATION (Mock) mode. Connecting to local FastAPI simulator.")
        else:
            logging.info(f"UiPathAdapter initialized for Production Orchestrator Org: {self.org_name}, Tenant: {self.tenant_name} (Domain: {self.uipath_domain})")

    def _get_access_token(self) -> str:
        """Fetch access token from UiPath Identity Service via OAuth 2.0."""
        if self.is_mock:
            return "mock-access-token"
        
        url = f"https://{self.uipath_domain}/identity_/connect/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "OR.Queues OR.Jobs OR.Tasks OR.Assets"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("access_token", "")
        except Exception as e:
            logging.error(f"Failed to retrieve OAuth token from UiPath Cloud: {e}")
            raise RuntimeError(f"UiPath Authentication Failed: {e}")

    def start_bpmn_process(self, process_name: str, variables: Dict[str, Any]) -> str:
        """Start a new process instance on UiPath Orchestrator / Maestro."""
        if self.is_mock:
            # Under mock, redirect payload to local simulator endpoint
            url = f"{self.api_url}/api/uipath/bpmn/processes"
            try:
                response = requests.post(url, json={
                    "process_name": process_name,
                    "variables": variables
                }, timeout=5)
                if response.status_code in [200, 201]:
                    return response.json().get("process_id", "sim-proc-000")
            except Exception as ex:
                logging.error(f"Failed to post to local simulator process start: {ex}")
            return "sim-proc-fallback"

        # Production Endpoint
        token = self._get_access_token()
        url = f"https://{self.uipath_domain}/{self.org_name}/{self.tenant_name}/orchestrator_/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs"
        
        # Look up process release key first (assumes release key matches or is pre-stored)
        release_key = os.environ.get(f"UIPATH_RELEASE_KEY_{process_name.upper()}", "")
        if not release_key:
            logging.warning(f"No Release Key env found for {process_name}. Defaulting to process name.")
            release_key = process_name
            
        payload = {
            "startInfo": {
                "ReleaseKey": release_key,
                "Strategy": "All",
                "RobotIds": [],
                "NoOfRobots": 0,
                "InputArguments": str(variables)
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-UIPATH-OrganizationUnitId": self.folder_id,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            jobs = response.json().get("value", [])
            if jobs:
                return str(jobs[0].get("Id", "uipath-job-id"))
            return "uipath-job-triggered"
        except Exception as e:
            logging.error(f"Failed to start UiPath process: {e}")
            return f"uipath-err-{e}"

    def create_user_task(self, process_id: str, task_name: str, task_data: Dict[str, Any]) -> str:
        """Create a user review task (Action Center) for a human inspector."""
        if self.is_mock:
            # Under mock, call local simulator endpoint
            url = f"{self.api_url}/api/uipath/bpmn/processes/{process_id}/action"
            try:
                response = requests.post(url, json=task_data, timeout=5)
                if response.status_code == 200:
                    return response.json().get("task_id", "sim-task-000")
            except Exception as ex:
                logging.error(f"Failed to create user task in local simulator: {ex}")
            return "sim-task-fallback"

        # Production Endpoint
        token = self._get_access_token()
        url = f"https://{self.uipath_domain}/{self.org_name}/{self.tenant_name}/orchestrator_/odata/Tasks/UiPath.Server.Configuration.OData.CreateFormTask"
        
        payload = {
            "task": {
                "Title": f"Weld Inspection: {task_name}",
                "Type": "FormTask",
                "Priority": "High",
                "Data": str(task_data)
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-UIPATH-OrganizationUnitId": self.folder_id,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            task_id = response.json().get("Id", "")
            return str(task_id) if task_id else "uipath-task-id"
        except Exception as e:
            logging.error(f"Failed to create UiPath Action Center task: {e}")
            return f"uipath-task-err-{e}"

    def get_task_status(self, task_id: str) -> str:
        """Retrieve the completion status of a specific user task."""
        if self.is_mock:
            # Check local simulator
            url = f"{self.api_url}/api/uipath/bpmn/processes"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    processes = response.json().get("processes", [])
                    for p in processes:
                        if p.get("task_id") == task_id:
                            # Map statuses
                            status_val = p.get("status", "")
                            if status_val == "Awaiting Review":
                                return "Unassigned"
                            elif status_val == "Completed":
                                return "Completed"
                            elif status_val == "Rework":
                                return "ReworkRequested"
            except Exception as ex:
                logging.error(f"Failed to fetch user task status in simulator: {ex}")
            return "Unassigned"

        # Production Endpoint
        token = self._get_access_token()
        url = f"https://{self.uipath_domain}/{self.org_name}/{self.tenant_name}/orchestrator_/odata/Tasks({task_id})"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-UIPATH-OrganizationUnitId": self.folder_id
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("Status", "Unassigned")  # e.g., Unassigned, Assigned, Completed
        except Exception as e:
            logging.error(f"Failed to get task status from UiPath: {e}")
            return "Unknown"

    def complete_service_task(self, process_id: str, task_name: str, results: Dict[str, Any]) -> None:
        """Send completion signal and outputs from automated AI agent back to the process orchestrator."""
        if self.is_mock:
            # Under mock, update local simulator
            url = f"{self.api_url}/api/uipath/bpmn/processes/{process_id}/step"
            try:
                requests.post(url, json={"task_name": task_name, "results": results}, timeout=5)
            except Exception as ex:
                logging.error(f"Failed to signal local simulator service task completion: {ex}")
            return

        # Production: Update a transaction item status in Queue, or update process status
        # Typically, a service task is completed by resolving a queue item transaction
        token = self._get_access_token()
        queue_item_id = results.get("queue_item_id")
        if not queue_item_id:
            logging.info("No queue_item_id found in results, skipping service task queue callback.")
            return

        url = f"https://{self.uipath_domain}/{self.org_name}/{self.tenant_name}/orchestrator_/odata/QueueItems({queue_item_id})/UiPath.Server.Configuration.OData.SetTransactionResult"
        payload = {
            "transactionResult": {
                "Status": "Successful",
                "OutputArguments": str(results)
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-UIPATH-OrganizationUnitId": self.folder_id,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to callback service task status: {e}")
