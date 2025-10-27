import time
from typing import Dict
from collections import defaultdict

# Very small in-memory ephemeral store (NOT persisted). Use Redis with TTL in prod.
class EphemeralStore:
    def __init__(self):
        self.store: Dict[str, Dict] = {}
        self.ttl: Dict[str, float] = {}

    def set(self, session_id: str, data: Dict, ttl_seconds: int = 300):
        self.store[session_id] = data
        self.ttl[session_id] = time.time() + ttl_seconds

    def get(self, session_id: str):
        if session_id not in self.store:
            return None
        if time.time() > self.ttl.get(session_id, 0):
            self.delete(session_id)
            return None
        return self.store[session_id]

    def delete(self, session_id: str):
        self.store.pop(session_id, None)
        self.ttl.pop(session_id, None)

ephemeral = EphemeralStore()