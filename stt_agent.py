import os
from .base import AgentBase
from typing import Dict, Any
from deepgram import Deepgram

DEEPGRAM_KEY = os.getenv("DEEPGRAM_API_KEY")

class DeepgramSTTAgent(AgentBase):
    def __init__(self):
        if DEEPGRAM_KEY:
            self.dg = Deepgram(DEEPGRAM_KEY)
        else:
            self.dg = None

    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # payload: file_path or audio_bytes, language
        file_path = payload.get("file_path")
        language = payload.get("language", "fr")
        if self.dg and file_path:
            with open(file_path, "rb") as f:
                resp = await self.dg.transcription.pre_recorded({"buffer": f}, {"punctuate": True, "language": language})
            text = resp["results"]["channels"][0]["alternatives"][0]["transcript"]
            return {"text": text, "language": language}
        # Fallback: simple placeholder for dev
        return {"text": "(transcription stub — configurer Deepgram ou Whisper pour la production)", "language": language}