# app/agents/billing_agent.py
from typing import Dict, Any, List, Optional
import os, json, uuid, requests
from .base import AgentBase
from ..audit import write_audit_event

MAPPING_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mappings", "ramq_codes.json")
RAMQ_API_URL = os.getenv("RAMQ_API_URL")
RAMQ_API_TOKEN = os.getenv("RAMQ_API_TOKEN")

def load_mappings() -> List[Dict[str, Any]]:
    try:
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

MAPPINGS = load_mappings()

def simple_match_codes(clinical_text: str, language: str = "fr") -> List[Dict[str, Any]]:
    text = clinical_text.lower() if clinical_text else ""
    suggestions = []
    for entry in MAPPINGS:
        keywords = entry.get("keywords", {}).get(language, []) + entry.get("keywords", {}).get("en", [])
        for kw in keywords:
            if kw.lower() in text:
                suggestions.append({
                    "icd10ca": entry.get("icd10ca"),
                    "ccp": entry.get("ccp"),
                    "label": entry.get("label", {}).get(language, entry.get("label", {}).get("en")),
                    "confidence": 0.8
                })
                break
    return suggestions

class RamqClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token

    def submit_claim(self, claim_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.base_url:
            return {"status": "manual_review", "details": {"reason": "RAMQ_API_URL not configured"}}
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            resp = requests.post(self.base_url, json=claim_payload, headers=headers, timeout=15)
            resp.raise_for_status()
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            return {"status": "sent", "http_status": resp.status_code, "response": body}
        except Exception as e:
            return {"status": "error", "details": {"error": str(e)}}

class BillingAgent(AgentBase):
    def __init__(self, ramq_client: Optional[RamqClient] = None):
        self.ramq = ramq_client or RamqClient(RAMQ_API_URL, RAMQ_API_TOKEN)

    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "propose")
        if action == "propose":
            return await self.propose(session_id, payload)
        elif action == "submit":
            return await self.submit(session_id, payload)
        else:
            return {"error": "action_unknown"}

    async def propose(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        clinical_note = payload.get("clinical_note", "")
        language = payload.get("language", "fr")
        actor = payload.get("actor", "unknown")
        write_audit_event("billing_propose_requested", actor, session_id, "requested", {"len": len(clinical_note)})
        suggestions = simple_match_codes(clinical_note, language)
        if not suggestions:
            write_audit_event("billing_propose_no_suggestions", actor, session_id, "no_suggestions", {})
            return {"suggestions": [], "message": {
                "fr": "Aucune proposition automatique. Veuillez sélectionner manuellement les codes.",
                "en": "No automatic suggestions. Please select codes manually."
            }[language]}
        return {"suggestions": suggestions, "message": {
            "fr": "Propositions de codes (à vérifier). Confirmez pour soumettre.",
            "en": "Proposed codes (review). Confirm to submit."
        }[language]}

    async def submit(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        actor = payload.get("actor", "unknown")
        if not payload.get("confirm", False):
            write_audit_event("billing_submit_attempt_without_confirm", actor, session_id, "forbidden", {})
            return {"status": "forbidden", "message": {"fr":"Confirmation manquante","en":"Missing confirmation"}[payload.get("language","fr")]}
        selected = payload.get("selected_codes", [])
        if not selected:
            write_audit_event("billing_submit_no_codes", actor, session_id, "failed", {})
            return {"status": "failed", "message": {"fr":"Aucun code sélectionné","en":"No codes selected"}[payload.get("language","fr")]}
        claim = {
            "claim_id": str(uuid.uuid4()),
            "session_id": session_id,
            "clinician_id": payload.get("clinician", {}).get("id", actor),
            "patient_fhir_ref": payload.get("patient_fhir_ref"),
            "encounter_ref": payload.get("encounter_fhir_ref"),
            "codes": selected,
            "language": payload.get("language","fr")
        }
        write_audit_event("billing_submit_requested", actor, session_id, "requested", {"codes_count": len(selected)})
        result = self.ramq.submit_claim(claim)
        status = result.get("status","unknown")
        write_audit_event("billing_submit_result", actor, session_id, status, {"ramq_status": result.get("http_status")})
        return {"status": status, "details": result}