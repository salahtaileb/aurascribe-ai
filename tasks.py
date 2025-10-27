# app/queues/tasks.py
import os, json
from redis import Redis
from rq import Queue
from typing import Dict, Any
from ..agents.billing_agent import RamqClient
from ..audit import write_audit_event

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)
queue_name = os.getenv("BILLING_QUEUE_NAME", "billing")
q = Queue(queue_name, connection=redis_conn)

def submit_claim_task(claim_payload: Dict[str, Any]):
    actor = claim_payload.get("clinician_id", "unknown")
    session_id = claim_payload.get("session_id", "unknown")
    client = RamqClient(os.getenv("RAMQ_API_URL"), os.getenv("RAMQ_API_TOKEN"))
    write_audit_event("billing_async_task_started", actor, session_id, "started", {"claim_id": claim_payload.get("claim_id")})
    result = client.submit_claim(claim_payload)
    status = result.get("status", "unknown")
    write_audit_event("billing_async_task_finished", actor, session_id, status, {"claim_id": claim_payload.get("claim_id"), "ramq_status": result.get("http_status")})
    return result