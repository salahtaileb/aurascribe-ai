from .base import AgentBase
from typing import Dict, Any
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini")  # remplacer selon disponibilité

class ChiefComplaintAgent(AgentBase):
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript = payload["transcript"]
        language = payload.get("language", "fr")
        sys = "Vous êtes un assistant clinique bilingue (FR/EN). Extraiter la plainte principale en 1-2 phrases."
        if language == "en":
            sys = "You are a bilingual clinical assistant (EN/FR). Extract the chief complaint in 1-2 short sentences."
        prompt = [SystemMessage(content=sys), HumanMessage(content=f"Transcription:\n{transcript}\n\nRetournez: chief_complaint.")]
        resp = await llm.agenerate(messages=[prompt])
        text = resp.generations[0][0].message.content.strip()
        return {"chief_complaint": text}

class HPIAgent(AgentBase):
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript = payload["transcript"]
        language = payload.get("language", "fr")
        sys = ("Vous êtes un assistant clinique bilingue. Extraire l'HPI structuré: début, localisation, durée, qualité, "
               "sévérité, facteurs, symptômes associés. Fournir en puces.")
        if language == "en":
            sys = ("You are a bilingual clinical assistant. Extract HPI structured into: onset, location, duration, quality, "
                   "severity, modifying factors, associated symptoms. Provide bullet points.")
        prompt = [SystemMessage(content=sys), HumanMessage(content=f"Transcription:\n{transcript}")]
        resp = await llm.agenerate(messages=[prompt])
        text = resp.generations[0][0].message.content.strip()
        return {"hpi": text}

class APAgent(AgentBase):
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript = payload["transcript"]
        language = payload.get("language", "fr")
        sys = "Vous êtes un assistant clinique bilingue. Résumer l'Assessment & Plan brièvement, adapté à l'EMR."
        if language == "en":
            sys = "You are a bilingual clinical assistant. Summarize Assessment & Plan briefly and clearly for EMR insertion."
        prompt = [SystemMessage(content=sys), HumanMessage(content=f"Transcription:\n{transcript}")]
        resp = await llm.agenerate(messages=[prompt])
        text = resp.generations[0][0].message.content.strip()
        return {"assessment_and_plan": text}

class MedicalScribeAgent(AgentBase):
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        chief = payload.get("chief_complaint", "")
        hpi = payload.get("hpi", "")
        ap = payload.get("assessment_and_plan", "")
        language = payload.get("language", "fr")
        sys = ("Vous êtes un rédacteur médical bilingue produisant une note clinique pour la santé sexuelle au Québec. "
               "Respectez les meilleures pratiques et n'incluez pas d'identifiants patients.")
        if language == "en":
            sys = ("You are a bilingual medical scribe creating a clinical note for sexual health in Québec. "
                   "Follow documentation best practices and do NOT include patient identifiers.")
        prompt = [SystemMessage(content=sys), HumanMessage(content=f"Chief complaint:\n{chief}\n\nHPI:\n{hpi}\n\nA&P:\n{ap}\n\nReturn clinical note.")]
        resp = await llm.agenerate(messages=[prompt])
        text = resp.generations[0][0].message.content.strip()
        return {"clinical_note": text}