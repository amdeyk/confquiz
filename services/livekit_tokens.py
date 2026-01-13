import json
import time
from typing import Dict, Optional

from jose import jwt

from config import settings


def create_livekit_token(
    identity: str,
    room: str,
    *,
    name: Optional[str] = None,
    can_publish: bool = False,
    can_subscribe: bool = True,
    can_publish_data: bool = True,
    metadata: Optional[Dict] = None
) -> str:
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise ValueError("LiveKit credentials are not configured")

    exp = int(time.time()) + settings.livekit_token_ttl_seconds
    grant = {
        "video": {
            "room": room,
            "roomJoin": True,
            "canPublish": can_publish,
            "canSubscribe": can_subscribe,
            "canPublishData": can_publish_data
        }
    }

    payload = {
        "iss": settings.livekit_api_key,
        "sub": identity,
        "name": name or identity,
        "exp": exp,
        **grant
    }

    if metadata is not None:
        payload["metadata"] = json.dumps(metadata)

    return jwt.encode(payload, settings.livekit_api_secret, algorithm="HS256")
