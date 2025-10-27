# app/agents/billing_agent_async.py
import os, uuid
from typing import Dict, Any
from redis import Redis
from rq import Queue
from ..queues.tasks import submit_claim_task
from .billing_agent import BillingAgent
from ..audit import write_audit_event

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)
billing_q = Queue(os.getenv("BILLING_QUEUE_NAME", "billing"), connection=redis_conn)

class BillingAgentAsync(BillingAgent):
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
        write_audit_event("billing_submit_requested", actor, session_id, "queued", {"codes_count": len(selected), "claim_id": claim["claim_id"]})
        job = billing_q.enqueue('app.queues.tasks.submit_claim_task', claim)
        return {"status": "queued", "job_id": job.get_id(), "claim_id": claim["claim_id"]}