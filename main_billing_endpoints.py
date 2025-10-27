"""
Extraits à ajouter dans app/main.py (ou à fusionner) : endpoints pour proposer et soumettre la facturation.
Protection OIDC requise; soumission nécessite le scope 'billing.submit'.
"""
from fastapi import APIRouter, Depends, HTTPException
from .agents.billing_agent import BillingAgent
from .auth_oauth import verify_token, require_scope
from .agents.orchestrator import MedicalDirectorAgent

router = APIRouter()

billing_agent = BillingAgent()

@router.post("/billing/propose", dependencies=[Depends(verify_token)])
async def billing_propose(session_id: str, language: str = "fr", token: dict = Depends(verify_token)):
    """
    Retourne des propositions de codes à partir de la note clinique associée à session_id.
    Le client peut aussi POST un clinical_note dans le body pour générer des propositions immédiates.
    """
    # Option: récupérer note depuis ephemeral store si existante
    from .ephemeral_redis import get_transcript
    session = await get_transcript(session_id)
    clinical_note = ""
    if session and session.get("clinical_note"):
        clinical_note = session["clinical_note"]
    else:
        # le client peut fournir clinical_note en param POST; ici on suppose query minimal
        raise HTTPException(status_code=400, detail="Clinical note required for propose or session must contain clinical_note")
    payload = {"clinical_note": clinical_note, "language": language, "actor": token.get("sub")}
    res = await billing_agent.propose(session_id, payload)
    return res

@router.post("/billing/submit", dependencies=[Depends(require_scope("billing.submit"))])
async def billing_submit(body: dict, token: dict = Depends(verify_token)):
    """
    Soumission des codes sélectionnés. body doit contenir: session_id, selected_codes, confirm(True), patient_fhir_ref optional, encounter_fhir_ref optional.
    """
    session_id = body.get("session_id")
    selected_codes = body.get("selected_codes", [])
    confirm = body.get("confirm", False)
    clinician = {"id": token.get("sub"), "display": token.get("name", "clinician")}
    payload = {
        "selected_codes": selected_codes,
        "confirm": confirm,
        "clinician": clinician,
        "patient_fhir_ref": body.get("patient_fhir_ref"),
        "encounter_fhir_ref": body.get("encounter_fhir_ref"),
        "language": body.get("language","fr"),
        "actor": token.get("sub")
    }
    res = await billing_agent.submit(session_id, payload)
    return res