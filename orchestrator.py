# app/agents/orchestrator.py (modifié pour supporter Whisper et billing async)
from .base import AgentBase
from typing import Dict, Any
import asyncio
from .stt_agent import DeepgramSTTAgent
from .stt_whisper import WhisperSTTAgent
from .text_agents import ChiefComplaintAgent, HPIAgent, APAgent, MedicalScribeAgent
from .policy_agent import MADOPolicyAgent
from .mado_agent import MADOAgent
# BillingAgentAsync or BillingAgent selected by env
from .billing_agent import BillingAgent
from .billing_agent_async import BillingAgentAsync
from ..ephemeral_redis import set_session_data, delete_session, get_session_data
from ..fhir_client import FHIRClient
from ..audit import write_audit_event
import os

class MedicalDirectorAgent(AgentBase):
    def __init__(self, fhir_client: FHIRClient = None):
        stt_backend = os.getenv("STT_BACKEND", "whisper")
        if stt_backend == "whisper":
            self.stt = WhisperSTTAgent()
        else:
            self.stt = DeepgramSTTAgent()
        self.policy = MADOPolicyAgent()
        self.cc = ChiefComplaintAgent()
        self.hpi = HPIAgent()
        self.ap = APAgent()
        self.scribe = MedicalScribeAgent()
        self.mado = MADOAgent()
        use_async = os.getenv("USE_ASYNC_BILLING", "true").lower() in ("1","true","yes")
        self.billing = BillingAgentAsync() if use_async else BillingAgent()
        self.fhir = fhir_client

    async def run(self, session_id: str, payload: Dict[str, Any], actor: str = "unknown"):
        if "transcript" in payload and payload["transcript"]:
            transcript = payload["transcript"]
            language = payload.get("language","fr")
        else:
            stt_res = await self.stt.run(session_id, payload)
            transcript = stt_res["text"]
            language = stt_res.get("language","fr")
        session_obj = {"transcript": transcript, "language": language}
        await set_session_data(session_id, session_obj)
        write_audit_event("transcription_requested", actor, session_id, "success", {"size": len(transcript)})
        policy = await self.policy.run(session_id, {"transcript": transcript, "language": language})
        redacted_transcript = policy["policy_result"]["redacted_transcript"]
        tasks = [
            self.cc.run(session_id, {"transcript": redacted_transcript, "language": language}),
            self.hpi.run(session_id, {"transcript": redacted_transcript, "language": language}),
            self.ap.run(session_id, {"transcript": redacted_transcript, "language": language}),
        ]
        cc_res, hpi_res, ap_res = await asyncio.gather(*tasks)
        scribe_input = {
            "chief_complaint": cc_res.get("chief_complaint",""),
            "hpi": hpi_res.get("hpi",""),
            "assessment_and_plan": ap_res.get("assessment_and_plan",""),
            "language": language
        }
        scribe_res = await self.scribe.run(session_id, scribe_input)
        clinical_note = scribe_res.get("clinical_note","")
        session_obj.update({"clinical_note": clinical_note})
        await set_session_data(session_id, session_obj)
        mado_res = None
        if "potentielle_declaration_obligatoire" in policy["policy_result"].get("flags", []):
            mado_payload = {
                "transcript": transcript,
                "language": language,
                "patient_fhir_ref": payload.get("patient_fhir_ref"),
                "encounter_fhir_ref": payload.get("encounter_fhir_ref"),
                "reporter": {"id": actor, "display": payload.get("reporter_display","Clinician")},
                "mado_confirm": payload.get("mado_confirm", False),
                "report_notes": payload.get("report_notes", "")
            }
            mado_res = await self.mado.run(session_id, mado_payload)
        billing_res = await self.billing.propose(session_id, {"clinical_note": clinical_note, "language": language, "actor": actor})
        fhir_response = None
        if self.fhir and payload.get("fhir_write", False):
            fhir_resource = {
                "resourceType": "DocumentReference",
                "status": "current",
                "type": {"text": "Clinical note - sexual health"},
                "content": [{"attachment": {"contentType": "text/plain", "data": clinical_note.encode("utf-8").hex()}}]
            }
            try:
                fhir_response = self.fhir.post_resource(fhir_resource)
                write_audit_event("fhir_write_attempt", actor, session_id, "success", {"resourceType":"DocumentReference"})
            except Exception as e:
                write_audit_event("fhir_write_attempt", actor, session_id, "failed", {"error": str(e)})
        session_obj.pop("transcript", None)
        await set_session_data(session_id, session_obj)
        return {
            "chief_complaint": cc_res.get("chief_complaint",""),
            "hpi": hpi_res.get("hpi",""),
            "assessment_and_plan": ap_res.get("assessment_and_plan",""),
            "clinical_note": clinical_note,
            "policy_result": policy["policy_result"],
            "mado": mado_res,
            "billing_suggestions": billing_res.get("suggestions", []),
            "fhir_response": fhir_response
        }