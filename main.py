# app/main.py (extraits modifiés: endpoints billing/propose and /billing/submit)
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from .agents.orchestrator import MedicalDirectorAgent
from .agents.billing_agent import BillingAgent
from .agents.billing_agent_async import BillingAgentAsync
from .auth_oauth import verify_token, require_scope
from .ephemeral_redis import get_session_data, set_session_data, delete_session
from .fhir_client import FHIRClient
import os, uuid, aiofiles

app = FastAPI(title="AuraScribe - Québec (FR default)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST","GET","OPTIONS"],
    allow_headers=["*"],
)

FHIR_BASE = os.getenv("FHIR_BASE_URL")
FHIR_TOKEN = os.getenv("FHIR_BEARER_TOKEN")
fhir_client = FHIRClient(FHIR_BASE, FHIR_TOKEN) if FHIR_BASE else None

orchestrator = MedicalDirectorAgent(fhir_client=fhir_client)
billing_agent = BillingAgentAsync() if os.getenv("USE_ASYNC_BILLING","true").lower() in ("1","true") else BillingAgent()

@app.post("/transcribe")
async def transcribe(session: str, language: str = "fr", audio: UploadFile = File(...), anonymous: bool = False, token: dict = Depends(verify_token)):
    temp_file = f"/tmp/{uuid.uuid4().hex}_{audio.filename}"
    async with aiofiles.open(temp_file, "wb") as out:
        content = await audio.read()
        await out.write(content)
    payload = {"file_path": temp_file, "language": language, "anonymous": anonymous}
    try:
        res = await orchestrator.run(session, payload, actor=token.get("sub"))
    finally:
        try:
            await aiofiles.os.remove(temp_file)
        except Exception:
            pass
    return res

@app.post("/scribe")
async def scribe(session_id: str = Body(...), language: str = Body("fr"), transcript: str = Body(...), token: dict = Depends(verify_token)):
    payload = {"transcript": transcript, "language": language}
    res = await orchestrator.run(session_id, payload, actor=token.get("sub"))
    return res

@app.post("/billing/propose", dependencies=[Depends(verify_token)])
async def billing_propose(body: dict = Body(...), token: dict = Depends(verify_token)):
    session_id = body.get("session_id")
    clinical_note = body.get("clinical_note")
    language = body.get("language", "fr")
    actor = token.get("sub")
    if not clinical_note:
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id or clinical_note required")
        session = await get_session_data(session_id)
        if not session or not session.get("clinical_note"):
            raise HTTPException(status_code=404, detail="Clinical note not found for session")
        clinical_note = session.get("clinical_note")
    res = await billing_agent.propose(session_id or "unknown", {"clinical_note": clinical_note, "language": language, "actor": actor})
    return res

@app.post("/billing/submit", dependencies=[Depends(require_scope("billing.submit"))])
async def billing_submit(body: dict = Body(...), token: dict = Depends(verify_token)):
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    payload = {
        "selected_codes": body.get("selected_codes", []),
        "confirm": body.get("confirm", False),
        "clinician": {"id": token.get("sub"), "display": token.get("name", "clinician")},
        "patient_fhir_ref": body.get("patient_fhir_ref"),
        "encounter_fhir_ref": body.get("encounter_fhir_ref"),
        "language": body.get("language", "fr"),
        "actor": token.get("sub")
    }
    res = await billing_agent.submit(session_id, payload)
    return res