from typing import Any, Dict
from abc import ABC, abstractmethod

class AgentBase(ABC):
    @abstractmethod
    async def run(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError