"""
Agent MADO: gère la démarche de déclaration obligatoire (MADO) pour le Québec.
- Langue par défaut: fr (français)
- Trois étapes:
    1) Vérifier la liste des maladies à déclaration obligatoire (mado_list.json)
    2) Remplir un formulaire structuré (données minimales nécessaires)
    3) Transmettre la déclaration (POST via API configurable ou email SMTP) 
Notes de conformité:
- La transmission automatique vers l'autorité de santé n'est effectuée que si:
    - l'utilisateur/acteur a le scope approprié (ex: "mado.report" ou "emr.write")
    - le clinicien confirme explicitement la transmission (UI confirmation)
- L'agent attend des références FHIR pour patient/encounter (préféré) plutôt que des identifiants bruts.
"""
from typing import Dict, Any, List, Optional
import os
import json
import re
import requests
import smtplib
from email.message import EmailMessage
from .base import AgentBase
from ..audit import write_audit_event

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MADO_LIST_PATH = os.path.join(BASE_DIR, "mado", "mado_list.json")

MADO_API_URL = os.getenv("MADO_API_URL")  # endpoint configurable si existant
MADO_API_TOKEN = os.getenv("MADO_API_TOKEN")
MADO_EMAIL_TO = os.getenv("MADO_EMAIL_TO")  # fallback email for notification to santé publique
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

def load_mado_list() -> List[Dict[str, Any]]:
    try:
        with open(MADO_LIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Empty fallback; en production charger la liste officielle
        return []

def find_candidate_mado(transcript: str, language: str = "fr") -> List[Dict[str, Any]]:
    """
    Recherche de correspondances simples (mots-clés) entre la transcription et la liste MADO.
    Retourne une liste de maladies candidates (structures du fichier mado_list.json).
    """
    candidates = []
    mado_list = load_mado_list()
    text = transcript.lower()
    for item in mado_list:
        keywords = item.get("keywords", {}).get(language, []) + item.get("keywords", {}).get("en", [])
        for kw in keywords:
            # simple word boundary match
            if re.search(r"\b" + re.escape(kw.lower()) + r"\b", text):
                candidates.append(item)
                break
    return candidates

def build_mado_form(payload: Dict[str, Any], candidate: Dict[str, Any], language: str = "fr") -> Dict[str, Any]:
    """
    Remplit une structure de formulaire MADO minimaliste à partir du payload.
    Exige idéalement des références FHIR (patient_ref, encounter_ref); si manquant, on met des placeholders
    et la déclaration nécessite confirmation clinicien et vérification manuelle.
    """
    # minimal required fields - adapter selon les exigences de la santé publique
    patient_ref = payload.get("patient_fhir_ref")  # ex: "Patient/123"
    encounter_ref = payload.get("encounter_fhir_ref")
    reporter = payload.get("reporter", {})  # dict avec nom, contact (clinician)
    onset = payload.get("onset") or payload.get("date_onset") or None
    summary = payload.get("clinical_summary") or payload.get("transcript", "")[:2000]  # restreindre longueur

    form = {
        "reporter": reporter,
        "patient_reference": patient_ref,
        "encounter_reference": encounter_ref,
        "disease_code": candidate.get("code"),
        "disease_label": candidate.get("label", {}).get(language, candidate.get("label", {}).get("en")),
        "onset": onset,
        "clinical_summary": summary,
        "report_notes": payload.get("report_notes", ""),
        "language": language
    }
    return form

def transmit_mado(form: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transmission configurable:
     - Si MADO_API_URL défini: POST JSON à l'API (avec token si fourni)
     - Sinon, si SMTP configuré et MADO_EMAIL_TO présent: envoyer email (clinician -> santé publique)
     - Sinon: renvoyer le payload form pour examen manuel (UI téléchargeable)
    Retour: {'status': 'sent'/'queued'/'manual_review', 'details': {...}}
    """
    if MADO_API_URL:
        headers = {"Content-Type": "application/json"}
        if MADO_API_TOKEN:
            headers["Authorization"] = f"Bearer {MADO_API_TOKEN}"
        try:
            resp = requests.post(MADO_API_URL, json=form, headers=headers, timeout=10)
            resp.raise_for_status()
            return {"status": "sent", "details": {"http_status": resp.status_code, "response": resp.text}}
        except Exception as e:
            return {"status": "error", "details": {"error": str(e)}}
    elif SMTP_HOST and MADO_EMAIL_TO:
        try:
            msg = EmailMessage()
            subject = f"Déclaration MADO: {form.get('disease_label','(maladie inconnue)')}"
            msg["Subject"] = subject
            msg["From"] = SMTP_USER or "no-reply@example.com"
            msg["To"] = MADO_EMAIL_TO
            body = f"Formulaire MADO (automatique) - langue: {form.get('language')}\n\n{json.dumps(form, ensure_ascii=False, indent=2)}"
            msg.set_content(body)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
                s.starttls()
                if SMTP_USER and SMTP_PASS:
                    s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
            return {"status": "sent", "details": {"method": "smtp"}}
        except Exception as e:
            return {"status": "error", "details": {"error": str(e)}}
    else:
        # Pas de canal automatisé — retourner la forme pour examen manuel
        return {"status": "manual_review", "details": {"form": form}}

class MADOAgent(AgentBase):
    """
    Agent orchestrant la démarche MADO en 3 étapes:
     - Vérifier la liste MADO
     - Remplir le formulaire
     - Transmettre (seulement si autorisé et confirmé)
    Usage:
      payload doit contenir:
       - 'transcript' ou 'structured_clinical' (texte)
       - 'language' : 'fr' ou 'en' (fr par défaut)
       - optionally: patient_fhir_ref, encounter_fhir_ref, reporter (clinician info)
       - 'mado_confirm' : bool (indique que le clinicien a confirmé la transmission)
       - 'actor' : id de l'utilisateur qui déclenche (pour audit)
    """
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript = payload.get("transcript", "")
        language = payload.get("language", "fr")
        actor = payload.get("actor", "unknown")

        # Étape 1 — Vérifier la liste des MADO
        candidates = find_candidate_mado(transcript, language)
        if not candidates:
            write_audit_event("mado_check", actor, session_id, "no_candidate", {"size": len(transcript)})
            return {"mado_step": 1, "candidates": [], "message": {
                "fr": "Aucune maladie MADO détectée automatiquement. Vérifier manuellement si nécessaire.",
                "en": "No MADO disease detected automatically. Please verify manually if needed."
            }[language]}

        # Étape 2 — Remplir le formulaire (pour le premier candidat par défaut)
        candidate = candidates[0]
        form = build_mado_form(payload, candidate, language)
        write_audit_event("mado_form_filled", actor, session_id, "filled", {"disease": form["disease_code"]})

        # Étape 3 — Transmettre la déclaration (conditionnée)
        # Conditions:
        #  - payload['mado_confirm'] == True (clinician confirmed)
        #  - caller doit s'assurer que l'acteur a scope mado.report / emr.write (vérifier au niveau du endpoint)
        if not payload.get("mado_confirm", False):
            # Retourner la forme pour revue/confirmation côté UI
            return {
                "mado_step": 2,
                "form": form,
                "message": {
                    "fr": "Formulaire MADO prérempli. Confirmation clinique requise pour transmettre la déclaration.",
                    "en": "MADO form prefilled. Clinical confirmation required to transmit the declaration."
                }[language],
                "candidates": candidates
            }

        # Si confirmé: tenter la transmission
        tx_result = transmit_mado(form)
        # Audit: ne pas stocker PHI dans metadata — n'enregistrer que l'issue
        write_audit_event("mado_transmit", actor, session_id, tx_result.get("status","unknown"), {"method": tx_result.get("details", {}).get("method", "api_or_manual")})
        return {"mado_step": 3, "transmit_result": tx_result, "form": {"disease_label": form["disease_label"], "patient_reference": bool(form["patient_reference"])}}