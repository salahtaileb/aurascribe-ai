# Extrait à intégrer dans app/agents/orchestrator.py (après policy étape)
from .mado_agent import MADOAgent
from ..auth_oauth import require_scope  # utilisé côté endpoint pour valider scope

# dans __init__:
# self.mado = MADOAgent()

# dans run(...):
# après policy check:
if "potentielle_declaration_obligatoire" in policy["policy_result"].get("flags", []):
    # Ne transmettre QUE si payload indique mado_confirm=True et endpoint a vérifié le scope
    # On renvoie le formulaire pré-rempli pour revue UI si pas confirmé.
    mado_payload = {
        "transcript": transcript,
        "language": language,
        "patient_fhir_ref": payload.get("patient_fhir_ref"),  # recommandé: référence FHIR fournie par le client
        "encounter_fhir_ref": payload.get("encounter_fhir_ref"),
        "reporter": {"id": actor, "display": payload.get("reporter_display","Clinician")},
        "mado_confirm": payload.get("mado_confirm", False),  # default False -> UI must confirm
        "report_notes": payload.get("report_notes", "")
    }
    mado_res = await self.mado.run(session_id, mado_payload)
    # Inclure mado_res dans la réponse principale afin que la UI affiche le formulaire et la demande de confirmation
    result["mado"] = mado_res