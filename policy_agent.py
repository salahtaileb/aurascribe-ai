from .base import AgentBase
from typing import Dict, Any
from ..policy_redaction import policy_check_and_redact

class MADOPolicyAgent(AgentBase):
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript = payload.get("transcript","")
        language = payload.get("language","fr")
        result = policy_check_and_redact(transcript, language)
        return {"policy_result": result}