import asyncio
import time
from typing import Optional, Dict
import redis.asyncio as redis
from config import settings


class TimerService:
    def __init__(self):
        self.redis_url = settings.redis_url
        self.running_timers: Dict[int, asyncio.Task] = {}

    async def get_redis(self):
        return await redis.from_url(self.redis_url, decode_responses=True)

    async def start_timer(
        self,
        session_id: int,
        duration_ms: int,
        fastest_finger: bool = False
    ):
        """Start a timer for a session"""
        r = await self.get_redis()

        # Set initial timer state
        timer_key = f"timer:{session_id}"
        start_epoch = int(time.time() * 1000)

        await r.hset(timer_key, mapping={
            "state": "counting",
            "start_epoch": str(start_epoch),
            "duration_ms": str(duration_ms),
            "remaining_ms": str(duration_ms),
            "fastest_finger": str(fastest_finger).lower()
        })

        # Start background task for countdown
        if session_id in self.running_timers:
            self.running_timers[session_id].cancel()

        task = asyncio.create_task(self._countdown(session_id, duration_ms))
        self.running_timers[session_id] = task

    async def _countdown(self, session_id: int, duration_ms: int):
        """Background task that counts down and publishes updates"""
        r = await self.get_redis()
        timer_key = f"timer:{session_id}"
        channel = f"timer:tick:{session_id}"

        start_time = time.time()
        end_time = start_time + (duration_ms / 1000)

        try:
            while True:
                current_time = time.time()
                remaining_ms = int((end_time - current_time) * 1000)

                if remaining_ms <= 0:
                    # Timer expired
                    await r.hset(timer_key, mapping={
                        "state": "stopped",
                        "remaining_ms": "0"
                    })
                    await r.publish(channel, "0")
                    break

                # Update remaining time
                await r.hset(timer_key, "remaining_ms", str(remaining_ms))

                # Publish tick
                await r.publish(channel, str(remaining_ms))

                # Sleep for 100ms
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            # Timer was cancelled
            pass
        finally:
            if session_id in self.running_timers:
                del self.running_timers[session_id]

    async def pause_timer(self, session_id: int):
        """Pause the timer"""
        r = await self.get_redis()
        timer_key = f"timer:{session_id}"

        # Get current remaining time
        timer_data = await r.hgetall(timer_key)
        if not timer_data or timer_data.get("state") != "counting":
            return False

        # Update state
        await r.hset(timer_key, "state", "paused")

        # Cancel countdown task
        if session_id in self.running_timers:
            self.running_timers[session_id].cancel()
            del self.running_timers[session_id]

        return True

    async def resume_timer(self, session_id: int):
        """Resume a paused timer"""
        r = await self.get_redis()
        timer_key = f"timer:{session_id}"

        timer_data = await r.hgetall(timer_key)
        if not timer_data or timer_data.get("state") != "paused":
            return False

        remaining_ms = int(timer_data.get("remaining_ms", 0))
        if remaining_ms <= 0:
            return False

        # Update state
        await r.hset(timer_key, "state", "counting")

        # Restart countdown with remaining time
        task = asyncio.create_task(self._countdown(session_id, remaining_ms))
        self.running_timers[session_id] = task

        return True

    async def reset_timer(self, session_id: int):
        """Reset/stop the timer"""
        r = await self.get_redis()
        timer_key = f"timer:{session_id}"

        # Cancel task
        if session_id in self.running_timers:
            self.running_timers[session_id].cancel()
            del self.running_timers[session_id]

        # Delete from Redis
        await r.delete(timer_key)

        return True

    async def get_timer_state(self, session_id: int) -> Optional[dict]:
        """Get current timer state"""
        r = await self.get_redis()
        timer_key = f"timer:{session_id}"

        timer_data = await r.hgetall(timer_key)
        if not timer_data:
            return None

        return {
            "state": timer_data.get("state"),
            "remaining_ms": int(timer_data.get("remaining_ms", 0)),
            "duration_ms": int(timer_data.get("duration_ms", 0)),
            "fastest_finger": timer_data.get("fastest_finger") == "true"
        }


# Global instance
timer_service = TimerService()
