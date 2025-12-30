import time
from typing import List, Dict, Optional
import redis.asyncio as redis
from config import settings


class BuzzerService:
    def __init__(self):
        self.redis_url = settings.redis_url

    async def get_redis(self):
        return await redis.from_url(self.redis_url, decode_responses=True)

    async def register_buzz(
        self,
        session_id: int,
        team_id: int,
        device_id: str
    ) -> Dict:
        """Register a buzz from a team"""
        r = await self.get_redis()

        # Check if buzzers are locked
        lock_key = f"buzzer:lock:{session_id}"
        if await r.exists(lock_key):
            return {
                "success": False,
                "reason": "buzzers_locked",
                "placement": None
            }

        # Use sorted set with timestamp as score for ordering
        buzzer_key = f"buzzer:{session_id}"
        timestamp = time.time()
        member = f"{team_id}:{device_id}"

        # Add to sorted set (only if not exists)
        added = await r.zadd(buzzer_key, {member: timestamp}, nx=True)

        if not added:
            # Already buzzed
            rank = await r.zrank(buzzer_key, member)
            placement = rank + 1 if rank is not None else None
            return {
                "success": False,
                "reason": "already_buzzed",
                "placement": placement
            }

        # Get placement
        rank = await r.zrank(buzzer_key, member)
        placement = rank + 1 if rank is not None else 1

        # Check if this is the first buzz
        first_key = f"buzzer:first:{session_id}"
        is_first = await r.setnx(first_key, f"{team_id}:{device_id}")

        return {
            "success": True,
            "placement": placement,
            "timestamp": timestamp,
            "is_first": bool(is_first)
        }

    async def get_buzz_queue(self, session_id: int) -> List[Dict]:
        """Get current buzz queue"""
        r = await self.get_redis()
        buzzer_key = f"buzzer:{session_id}"

        # Get all buzzes ordered by timestamp
        buzzes = await r.zrange(buzzer_key, 0, -1, withscores=True)

        queue = []
        for i, (member, timestamp) in enumerate(buzzes):
            team_id, device_id = member.split(":", 1)
            queue.append({
                "team_id": int(team_id),
                "device_id": device_id,
                "placement": i + 1,
                "timestamp": timestamp
            })

        return queue

    async def lock_buzzers(self, session_id: int):
        """Lock buzzers (prevent new buzzes)"""
        r = await self.get_redis()
        lock_key = f"buzzer:lock:{session_id}"
        await r.set(lock_key, "1")

    async def unlock_buzzers(self, session_id: int):
        """Unlock buzzers and clear queue"""
        r = await self.get_redis()

        # Remove lock
        lock_key = f"buzzer:lock:{session_id}"
        await r.delete(lock_key)

        # Clear queue
        buzzer_key = f"buzzer:{session_id}"
        await r.delete(buzzer_key)

        # Clear first marker
        first_key = f"buzzer:first:{session_id}"
        await r.delete(first_key)

    async def is_locked(self, session_id: int) -> bool:
        """Check if buzzers are locked"""
        r = await self.get_redis()
        lock_key = f"buzzer:lock:{session_id}"
        return bool(await r.exists(lock_key))

    async def clear_queue(self, session_id: int):
        """Clear buzz queue without unlocking"""
        r = await self.get_redis()
        buzzer_key = f"buzzer:{session_id}"
        first_key = f"buzzer:first:{session_id}"

        await r.delete(buzzer_key)
        await r.delete(first_key)


# Global instance
buzzer_service = BuzzerService()
