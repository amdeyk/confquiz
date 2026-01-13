import json
import time
from typing import Dict, List, Optional

import redis.asyncio as redis

from config import settings


def _registry_key(session_id: int) -> str:
    return f"display:registry:{session_id}"


async def _get_redis():
    return await redis.from_url(settings.redis_url, decode_responses=True)


def _merge_display(current: Optional[Dict], updates: Dict) -> Dict:
    now = int(time.time())
    merged = current.copy() if current else {}
    merged.setdefault("display_id", updates.get("display_id"))
    merged["last_seen"] = now
    for key, value in updates.items():
        if value is None:
            continue
        if key == "metrics":
            metrics = merged.get("metrics", {})
            metrics.update(value)
            merged["metrics"] = metrics
        else:
            merged[key] = value
    return merged


async def list_displays(session_id: int) -> List[Dict]:
    r = await _get_redis()
    try:
        raw = await r.hgetall(_registry_key(session_id))
        displays = []
        for value in raw.values():
            try:
                displays.append(json.loads(value))
            except json.JSONDecodeError:
                continue
        return displays
    finally:
        await r.close()


async def get_display(session_id: int, display_id: str) -> Optional[Dict]:
    r = await _get_redis()
    try:
        value = await r.hget(_registry_key(session_id), display_id)
        if not value:
            return None
        return json.loads(value)
    finally:
        await r.close()


async def upsert_display(session_id: int, display_id: str, updates: Dict) -> Dict:
    r = await _get_redis()
    try:
        current_raw = await r.hget(_registry_key(session_id), display_id)
        current = json.loads(current_raw) if current_raw else None
        merged = _merge_display(current, {"display_id": display_id, **updates})
        await r.hset(_registry_key(session_id), display_id, json.dumps(merged))
        return merged
    finally:
        await r.close()


async def approve_display(session_id: int, display_id: str, role: str, approved_by: str) -> Dict:
    updates = {
        "status": "approved",
        "role": role,
        "approved_by": approved_by,
        "approved_at": int(time.time())
    }
    return await upsert_display(session_id, display_id, updates)


async def set_display_status(session_id: int, display_id: str, status: str) -> Dict:
    return await upsert_display(session_id, display_id, {"status": status})


async def count_protected(session_id: int) -> int:
    displays = await list_displays(session_id)
    return sum(1 for d in displays if d.get("role") == "protected" and d.get("status") in ["approved", "connected"])
