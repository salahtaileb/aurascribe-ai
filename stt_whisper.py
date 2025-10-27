# app/agents/stt_whisper.py
"""
STT Agent utilisant whisper / whisperx (local).
Par défaut: FR. Conçu comme fallback principal pour éviter les coûts d'API externes.
"""
import os
import tempfile
from typing import Dict, Any
from .base import AgentBase
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

# try importing whisperx / whisper if available
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except Exception:
    WHISPERX_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except Exception:
    WHISPER_AVAILABLE = False

def _run_whisper_in_thread(file_path: str, language: str = "fr") -> Dict[str, Any]:
    if WHISPERX_AVAILABLE:
        model_name = os.getenv("WHISPER_MODEL", "medium")
        device = "cuda" if whisperx.utils.get_torch_device().type == "cuda" else "cpu"
        model = whisperx.load_model(model_name, device)
        result = model.transcribe(file_path, language=language, task="transcribe")
        text = result.get("text", "")
        segments = result.get("segments", [])
        return {"text": text, "segments": segments, "language": language, "model_meta": {"engine": "whisperx", "model": model_name}}
    elif WHISPER_AVAILABLE:
        model_name = os.getenv("WHISPER_MODEL", "small")
        model = whisper.load_model(model_name)
        res = model.transcribe(file_path, language=language)
        text = res.get("text", "")
        segments = res.get("segments", [])
        return {"text": text, "segments": segments, "language": language, "model_meta": {"engine": "whisper", "model": model_name}}
    else:
        return {"text": "", "segments": [], "language": language, "model_meta": {"engine": "none"}}

class WhisperSTTAgent(AgentBase):
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        file_path = payload.get("file_path")
        language = payload.get("language", "fr")
        if not file_path:
            audio_bytes = payload.get("audio_bytes")
            if not audio_bytes:
                raise ValueError("No audio provided")
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp.write(audio_bytes)
            tmp.flush()
            file_path = tmp.name
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, _run_whisper_in_thread, file_path, language)
        confidence = 0.9 if result["segments"] else 0.6
        return {"text": result["text"], "segments": result.get("segments", []), "language": result.get("language", language), "confidence": confidence, "model_meta": result.get("model_meta", {})}