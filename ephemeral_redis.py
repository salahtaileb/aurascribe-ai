# app/ephemeral_redis.py
import os, json
import aioredis
from typing import Optional, Dict, Any

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TRANSCRIPT_TTL = int(os.getenv("TRANSCRIPT_TTL", "300"))

redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

async def set_session_data(session_id: str, data: Dict[str, Any], ttl: int = TRANSCRIPT_TTL):
    key = f"aura:session:{session_id}"
    await redis.set(key, json.dumps(data), ex=ttl)

async def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    key = f"aura:session:{session_id}"
    raw = await redis.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

async def delete_session(session_id: str):
    key = f"aura:session:{session_id}"
    await redis.delete(key)