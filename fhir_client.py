import os
import requests
from typing import Dict, Optional

class FHIRClient:
    def __init__(self, base_url: str, bearer_token: Optional[str] = None):
        if not base_url:
            self.base_url = None
            self.headers = {}
            return
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/fhir+json"}
        if bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"

    def post_resource(self, resource: Dict):
        if not self.base_url:
            raise RuntimeError("FHIR_BASE_URL non configuré")
        rt = resource.get("resourceType", "")
        url = f"{self.base_url}/{rt}"
        resp = requests.post(url, json=resource, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()