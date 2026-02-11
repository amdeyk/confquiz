from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set, Optional
import json
import asyncio
from datetime import datetime
import redis.asyncio as redis
from config import settings
from services.display_registry import get_display, set_display_status, upsert_display
from services.livekit_tokens import create_livekit_token

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # {session_id: {role: [websocket, websocket, ...]}}
        self.active_connections: Dict[int, Dict[str, Set[WebSocket]]] = {}
        # Track which team_id each websocket belongs to: {websocket: team_id}
        self.team_websocket_map: Dict[WebSocket, int] = {}
        # Track display websocket mapping
        self.display_websocket_map: Dict[str, WebSocket] = {}
        self.display_id_map: Dict[WebSocket, str] = {}
        # Track background timer subscription tasks
        self.timer_tasks: Dict[int, asyncio.Task] = {}
        # Track buzzer heartbeat tasks
        self.buzzer_heartbeat_tasks: Dict[int, asyncio.Task] = {}
        # Track score heartbeat tasks
        self.score_heartbeat_tasks: Dict[int, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, session_id: int, role: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        if role not in self.active_connections[session_id]:
            self.active_connections[session_id][role] = set()
        self.active_connections[session_id][role].add(websocket)

        # Start timer subscription for this session if not already running
        if session_id not in self.timer_tasks:
            self.timer_tasks[session_id] = asyncio.create_task(
                self._subscribe_to_timer_ticks(session_id)
            )

        # Start buzzer heartbeat for this session if not already running
        if session_id not in self.buzzer_heartbeat_tasks:
            self.buzzer_heartbeat_tasks[session_id] = asyncio.create_task(
                self._broadcast_buzzer_heartbeat(session_id)
            )

        # Start score heartbeat for this session if not already running
        if session_id not in self.score_heartbeat_tasks:
            self.score_heartbeat_tasks[session_id] = asyncio.create_task(
                self._broadcast_score_heartbeat(session_id)
            )

    def register_team_connection(self, websocket: WebSocket, team_id: int):
        """Register which team_id a websocket belongs to"""
        self.team_websocket_map[websocket] = team_id

    def register_display_connection(self, websocket: WebSocket, display_id: str):
        """Register which display_id a websocket belongs to"""
        self.display_websocket_map[display_id] = websocket
        self.display_id_map[websocket] = display_id

    async def send_to_display(self, display_id: str, message: dict):
        """Send a message to a specific display if connected"""
        websocket = self.display_websocket_map.get(display_id)
        if not websocket:
            return
        try:
            await websocket.send_json(message)
        except:
            pass

    def get_online_team_ids(self, session_id: int) -> Set[int]:
        """Get set of team_ids that are currently online for a session"""
        online_teams = set()
        if session_id in self.active_connections:
            if "team" in self.active_connections[session_id]:
                for ws in self.active_connections[session_id]["team"]:
                    if ws in self.team_websocket_map:
                        online_teams.add(self.team_websocket_map[ws])
        return online_teams

    def disconnect(self, websocket: WebSocket, session_id: int, role: str):
        if session_id in self.active_connections:
            if role in self.active_connections[session_id]:
                self.active_connections[session_id][role].discard(websocket)

                # Clean up team mapping if this was a team connection
                if websocket in self.team_websocket_map:
                    del self.team_websocket_map[websocket]

                # Clean up display mapping if this was a display connection
                if websocket in self.display_id_map:
                    display_id = self.display_id_map.pop(websocket)
                    self.display_websocket_map.pop(display_id, None)

                # If no more connections for this session, stop background tasks
                has_connections = any(
                    len(connections) > 0
                    for connections in self.active_connections[session_id].values()
                )
                if not has_connections:
                    # Stop timer subscription
                    if session_id in self.timer_tasks:
                        self.timer_tasks[session_id].cancel()
                        del self.timer_tasks[session_id]

                    # Stop buzzer heartbeat
                    if session_id in self.buzzer_heartbeat_tasks:
                        self.buzzer_heartbeat_tasks[session_id].cancel()
                        del self.buzzer_heartbeat_tasks[session_id]

                    # Stop score heartbeat
                    if session_id in self.score_heartbeat_tasks:
                        self.score_heartbeat_tasks[session_id].cancel()
                        del self.score_heartbeat_tasks[session_id]

                    del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: int, message: dict, role: str = None):
        """Broadcast to specific role or all roles in session"""
        if session_id not in self.active_connections:
            return

        if role:
            # Broadcast to specific role
            if role in self.active_connections[session_id]:
                for connection in self.active_connections[session_id][role].copy():
                    try:
                        await connection.send_json(message)
                    except:
                        self.disconnect(connection, session_id, role)
        else:
            # Broadcast to all roles
            for role_key in self.active_connections[session_id]:
                for connection in self.active_connections[session_id][role_key].copy():
                    try:
                        await connection.send_json(message)
                    except:
                        self.disconnect(connection, session_id, role_key)

    async def _subscribe_to_timer_ticks(self, session_id: int):
        """Background task to subscribe to Redis timer ticks and forward to WebSocket clients"""
        r = None
        pubsub = None
        try:
            r = await redis.from_url(settings.redis_url, decode_responses=True)
            pubsub = r.pubsub()

            channel = f"timer:tick:{session_id}"
            await pubsub.subscribe(channel)

            # Listen for timer tick messages
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=2.0
                    )
                    if message and message['type'] == 'message':
                        try:
                            remaining_ms = int(message['data'])
                            # Broadcast timer tick to all connected clients with timeout
                            await asyncio.wait_for(
                                self.broadcast_to_session(
                                    session_id,
                                    {
                                        "event": "timer.tick",
                                        "remaining_ms": remaining_ms,
                                        "state": "counting"
                                    }
                                ),
                                timeout=0.5
                            )
                        except (ValueError, KeyError):
                            pass  # Ignore malformed messages
                        except asyncio.TimeoutError:
                            print(f"Broadcast timeout in timer tick for session {session_id}")
                except asyncio.TimeoutError:
                    # Timeout waiting for message - just continue
                    pass
                except Exception as e:
                    print(f"Error in timer subscription for session {session_id}: {e}")

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            # Task was cancelled, cleanup
            pass
        finally:
            # Cleanup Redis connection
            if pubsub:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except:
                    pass
            if r:
                try:
                    await r.close()
                except:
                    pass

    async def _broadcast_buzzer_heartbeat(self, session_id: int):
        """Background task to periodically broadcast buzzer state to all clients"""
        r = None
        try:
            r = await redis.from_url(settings.redis_url, decode_responses=True)

            while True:
                try:
                    # Read buzzer state with timeout to prevent blocking
                    buzzer_lock_key = f"buzzer:lock:{session_id}"
                    buzzer_queue_key = f"buzzer:{session_id}"
                    first_buzzer_key = f"buzzer:first:{session_id}"

                    # Wrap Redis operations in timeout (1 second max)
                    try:
                        is_locked, queue_members, first_buzzer_team_id = await asyncio.wait_for(
                            asyncio.gather(
                                r.get(buzzer_lock_key),
                                r.zrange(buzzer_queue_key, 0, -1, withscores=True),
                                r.get(first_buzzer_key)
                            ),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        print(f"Redis timeout in buzzer heartbeat for session {session_id}")
                        continue  # Skip this heartbeat cycle

                    # Build buzzer queue data with team names
                    buzzer_queue = []
                    if queue_members:
                        # Get database session to fetch team names
                        from database import get_async_session_maker
                        from models import Team, TeamSession
                        from sqlalchemy import select

                        # Extract all team_ids FIRST (avoid N+1 query)
                        team_ids = []
                        member_data = []
                        for index, (member, score) in enumerate(queue_members):
                            parts = member.split(':', 1)
                            team_id = int(parts[0]) if len(parts) > 0 else None
                            device_id = parts[1] if len(parts) > 1 else "default"
                            if team_id:
                                team_ids.append(team_id)
                                member_data.append((team_id, device_id, score, index + 1))

                        # Fetch ALL team names in ONE query with timeout
                        async_session = get_async_session_maker()
                        try:
                            async with async_session() as db:
                                result = await asyncio.wait_for(
                                    db.execute(
                                        select(Team.id, Team.name)
                                        .join(TeamSession, TeamSession.team_id == Team.id)
                                        .where(
                                            TeamSession.session_id == session_id,
                                            Team.id.in_(team_ids)
                                        )
                                    ),
                                    timeout=1.0
                                )
                                team_names = {team_id: name for team_id, name in result.all()}
                        except asyncio.TimeoutError:
                            print(f"Database timeout in buzzer heartbeat for session {session_id}")
                            team_names = {}  # Fallback to empty names

                        # Build queue with fetched names
                        for team_id, device_id, score, placement in member_data:
                            buzzer_queue.append({
                                "team_id": team_id,
                                "team_name": team_names.get(team_id, f"Team {team_id}"),
                                "device_id": device_id,
                                "timestamp": score,
                                "placement": placement
                            })

                    # Broadcast buzzer state to all clients
                    buzzer_state = {
                        "event": "buzzer.status",
                        "locked": bool(is_locked),
                        "queue": buzzer_queue,
                        "first_buzzer_team_id": int(first_buzzer_team_id) if first_buzzer_team_id else None,
                        "total_buzzers": len(buzzer_queue)
                    }

                    await self.broadcast_to_session(session_id, buzzer_state)

                except Exception as e:
                    # Log error but continue heartbeat
                    print(f"Error in buzzer heartbeat for session {session_id}: {e}")
                    import traceback
                    traceback.print_exc()

                # Wait 5 seconds before next heartbeat (reduced frequency to prevent blocking)
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            # Task was cancelled, cleanup
            pass
        finally:
            # Cleanup Redis connection
            if r:
                try:
                    await r.close()
                except:
                    pass

    async def _broadcast_score_heartbeat(self, session_id: int):
        """Background task to periodically broadcast score state to all clients"""
        try:
            while True:
                try:
                    # Get online team IDs for this session
                    online_team_ids = self.get_online_team_ids(session_id)

                    # Get database session to fetch scores
                    from database import get_async_session_maker
                    from models import Team, TeamSession, Score
                    from sqlalchemy import select

                    async_session = get_async_session_maker()
                    try:
                        async with async_session() as db:
                            # Fetch only online teams' scores with timeout
                            result = await asyncio.wait_for(
                                db.execute(
                                    select(
                                        Team.id,
                                        Team.name,
                                        Score.total
                                    )
                                    .join(TeamSession, TeamSession.team_id == Team.id)
                                    .outerjoin(Score, Score.team_session_id == TeamSession.id)
                                    .where(
                                        TeamSession.session_id == session_id,
                                        Team.id.in_(online_team_ids) if online_team_ids else False
                                    )
                                    .order_by(Score.total.desc().nulls_last(), Team.name)
                                ),
                                timeout=1.0
                            )

                            teams = result.all()
                    except asyncio.TimeoutError:
                        print(f"Database timeout in score heartbeat for session {session_id}")
                        teams = []  # Fallback to empty scores

                    # Build scores list
                    scores = []
                    for index, (team_id, team_name, total) in enumerate(teams):
                        scores.append({
                            "team_id": team_id,
                            "team_name": team_name,
                            "total": total or 0,
                            "rank": index + 1
                        })

                    # Broadcast score state to all clients
                    score_state = {
                        "event": "score.status",
                        "scores": scores,
                        "total_teams": len(scores),
                        "online_teams": len(online_team_ids)
                    }

                    await self.broadcast_to_session(session_id, score_state)

                except Exception as e:
                    # Log error but continue heartbeat
                    print(f"Error in score heartbeat for session {session_id}: {e}")
                    import traceback
                    traceback.print_exc()

                # Wait 5 seconds before next heartbeat (reduced frequency to prevent blocking)
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            # Task was cancelled, cleanup
            pass


manager = ConnectionManager()


@router.websocket("/admin/{session_id}")
async def websocket_admin(websocket: WebSocket, session_id: int, token: str = Query(...)):
    """WebSocket for admin dashboard"""
    # TODO: Validate token and permissions
    await manager.connect(websocket, session_id, "admin")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle admin commands if needed
            await websocket.send_json({"event": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, "admin")


@router.websocket("/qm/{session_id}")
async def websocket_quiz_master(websocket: WebSocket, session_id: int, token: str = Query(...)):
    """WebSocket for quiz master"""
    # TODO: Validate token and permissions
    await manager.connect(websocket, session_id, "qm")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle QM commands
            await websocket.send_json({"event": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, "qm")


@router.websocket("/display/{session_id}")
async def websocket_display(websocket: WebSocket, session_id: int):
    """WebSocket for main display screen with WebRTC support"""
    await manager.connect(websocket, session_id, "display")
    try:
        while True:
            message = await websocket.receive_json()

            if message.get("type") == "display-join":
                display_id = message.get("display_id")
                user_agent = message.get("user_agent")
                if not display_id:
                    continue

                manager.register_display_connection(websocket, display_id)

                existing = await get_display(session_id, display_id)
                role = existing.get("role") if existing else None
                if not role:
                    role = "normal"

                registry = await upsert_display(
                    session_id,
                    display_id,
                    {
                        "status": "approved",
                        "role": role,
                        "user_agent": user_agent
                    }
                )

                try:
                    room_name = f"{settings.livekit_room_prefix}-{session_id}"
                    token = create_livekit_token(
                        identity=display_id,
                        room=room_name,
                        can_publish=False,
                        can_subscribe=True,
                        metadata={"role": role, "display_id": display_id, "session_id": session_id}
                    )
                    await manager.send_to_display(display_id, {
                        "event": "display.approved",
                        "display_id": display_id,
                        "role": role,
                        "token": token,
                        "livekit_url": settings.livekit_url,
                        "room_name": room_name
                    })
                    await manager.broadcast_to_session(
                        session_id,
                        {
                            "event": "display.approved",
                            "display_id": display_id,
                            "role": role,
                            "status": registry.get("status")
                        },
                        role="admin"
                    )
                except ValueError as error:
                    await manager.send_to_display(display_id, {
                        "event": "display.error",
                        "message": str(error)
                    })

            # Handle display telemetry updates (health checks)
            elif message.get("type") in ["display-telemetry", "display-status"]:
                display_id = message.get("display_id")
                if not display_id:
                    continue

                updates = {
                    "status": "connected",
                    "metrics": {
                        "resolution": message.get("resolution"),
                        "frameRate": message.get("frameRate"),
                        "bitrate": message.get("bitrate"),
                        "packetLoss": message.get("packetLoss"),
                        "jitter": message.get("jitter")
                    }
                }
                registry = await upsert_display(session_id, display_id, updates)

                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "display.status",
                        "display_id": display_id,
                        "status": registry.get("status"),
                        "role": registry.get("role"),
                        "resolution": registry.get("metrics", {}).get("resolution"),
                        "frameRate": registry.get("metrics", {}).get("frameRate"),
                        "bitrate": registry.get("metrics", {}).get("bitrate"),
                        "packetLoss": registry.get("metrics", {}).get("packetLoss"),
                        "jitter": registry.get("metrics", {}).get("jitter"),
                        "last_seen": registry.get("last_seen")
                    },
                    role="presenter"
                )
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "display.status",
                        "display_id": display_id,
                        "status": registry.get("status"),
                        "role": registry.get("role"),
                        "resolution": registry.get("metrics", {}).get("resolution"),
                        "frameRate": registry.get("metrics", {}).get("frameRate"),
                        "bitrate": registry.get("metrics", {}).get("bitrate"),
                        "packetLoss": registry.get("metrics", {}).get("packetLoss"),
                        "jitter": registry.get("metrics", {}).get("jitter"),
                        "last_seen": registry.get("last_seen")
                    },
                    role="admin"
                )

            # Handle WebRTC answer from display
            elif message.get("type") == "answer":
                # Forward answer back to presenter
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "webrtc.answer",
                        "sdp": message.get("sdp"),
                        "display_id": message.get("display_id")
                    },
                    role="presenter"
                )

            elif message.get("type") == "ice-candidate":
                # Forward ICE candidate to presenter
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "webrtc.ice.display",
                        "candidate": message.get("candidate"),
                        "display_id": message.get("display_id")
                    },
                    role="presenter"
                )

    except WebSocketDisconnect:
        if websocket in manager.display_id_map:
            display_id = manager.display_id_map.get(websocket)
            if display_id:
                await set_display_status(session_id, display_id, "disconnected")
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "display.status",
                        "display_id": display_id,
                        "status": "disconnected"
                    },
                    role="admin"
                )
        manager.disconnect(websocket, session_id, "display")


@router.websocket("/team/{session_id}")
async def websocket_team(websocket: WebSocket, session_id: int, token: str = Query(...)):
    """WebSocket for team clients with buzzer support"""
    # Validate token and extract team_id
    from jose import jwt, JWTError
    from config import settings as app_settings

    try:
        payload = jwt.decode(token, app_settings.secret_key, algorithms=[app_settings.algorithm])
        team_id = payload.get("team_id")

        if team_id is None:
            await websocket.close(code=1008, reason="Invalid token: missing team_id")
            return
    except JWTError as e:
        await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
        return

    await manager.connect(websocket, session_id, "team")

    # Register this team's connection for online tracking
    manager.register_team_connection(websocket, team_id)

    try:
        while True:
            message = await websocket.receive_json()

            # Handle buzz event
            if message.get("action") == "buzz":
                # Use team_id from JWT token (already validated above)
                device_id = message.get("device_id", "default")

                # Connect to Redis
                r = await redis.from_url(settings.redis_url, decode_responses=True)

                try:
                    # Enforce 1-second cooldown between accepted buzzes (auto-unlock)
                    buzzer_lock_key = f"buzzer:lock:{session_id}"

                    # Check if team already buzzed
                    buzzer_queue_key = f"buzzer:{session_id}"

                    # Get current timestamp for scoring
                    import time
                    timestamp_score = time.time()

                    # Create member key (team_id:device_id)
                    member_key = f"{team_id}:{device_id}"

                    # Check if team already buzzed using sorted set
                    existing_buzz = await r.zscore(buzzer_queue_key, member_key)

                    if existing_buzz is not None:
                        # Team already in queue
                        await websocket.send_json({
                            "event": "buzz.rejected",
                            "reason": "Already buzzed"
                        })
                        continue

                    # Acquire cooldown lock (1 second) to auto-unlock after press
                    lock_acquired = await r.set(buzzer_lock_key, "1", nx=True, ex=1)
                    if not lock_acquired:
                        ttl = await r.ttl(buzzer_lock_key)
                        if ttl is None or ttl < 0:
                            await r.expire(buzzer_lock_key, 1)
                        await websocket.send_json({
                            "event": "buzz.rejected",
                            "reason": "Buzzer cooling down"
                        })
                        continue

                    # Add to buzzer queue using sorted set (timestamp as score for ordering)
                    added = await r.zadd(buzzer_queue_key, {member_key: timestamp_score}, nx=True)
                    if not added:
                        await r.delete(buzzer_lock_key)
                        await websocket.send_json({
                            "event": "buzz.rejected",
                            "reason": "Already buzzed"
                        })
                        continue

                    # Get placement (rank in the queue)
                    placement = await r.zrank(buzzer_queue_key, member_key)
                    placement = placement + 1 if placement is not None else 1

                    # Set as first buzzer if queue was empty
                    first_buzzer_key = f"buzzer:first:{session_id}"
                    queue_size = await r.zcard(buzzer_queue_key)
                    if queue_size == 1:
                        await r.set(first_buzzer_key, str(team_id))

                    timestamp = datetime.utcnow().isoformat()

                    # Broadcast buzz to all clients
                    buzz_event = {
                        "event": "buzzer.update",
                        "team_id": team_id,
                        "timestamp": timestamp,
                        "placement": placement,
                        "total_buzzers": queue_size
                    }

                    await manager.broadcast_to_session(session_id, buzz_event, role="qm")
                    await manager.broadcast_to_session(session_id, buzz_event, role="display")
                    await manager.broadcast_to_session(session_id, buzz_event, role="team")

                    # Send explicit confirmation to buzzing team with placement
                    await websocket.send_json({
                        "event": "buzz.confirmed",
                        "timestamp": timestamp,
                        "placement": placement,
                        "total_buzzers": queue_size,
                        "message": f"You are #{placement} in the queue!"
                    })

                finally:
                    await r.close()

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, "team")


# Helper function to broadcast events (can be called from other modules)
async def broadcast_event(session_id: int, event: dict, role: str = None):
    """Utility function to broadcast events from other parts of the app"""
    await manager.broadcast_to_session(session_id, event, role)


async def broadcast_settings_update(setting_key: str, setting_value: str):
    """Broadcast settings update to all connected clients"""
    # Broadcast to all sessions
    for session_id in manager.active_connections.keys():
        await manager.broadcast_to_session(
            session_id,
            {
                "event": "settings.update",
                "setting_key": setting_key,
                "setting_value": setting_value
            }
        )


@router.websocket("/presenter/{session_id}")
async def websocket_presenter(websocket: WebSocket, session_id: int, token: str = Query(...)):
    """WebSocket for presenter with WebRTC signaling support"""
    # TODO: Validate token and permissions
    await manager.connect(websocket, session_id, "presenter")

    try:
        while True:
            message = await websocket.receive_json()

            # Handle WebRTC signaling messages
            if message.get("type") == "offer":
                # Presenter is offering to start screen sharing
                # Broadcast offer to all display clients
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "webrtc.offer",
                        "sdp": message.get("sdp"),
                        "presenter_id": message.get("presenter_id")
                    },
                    role="display"
                )

            elif message.get("type") == "ice-candidate":
                # Forward ICE candidate to display clients
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "webrtc.ice",
                        "candidate": message.get("candidate"),
                        "presenter_id": message.get("presenter_id")
                    },
                    role="display"
                )

            elif message.get("action") == "start-presenting":
                # Notify all clients that presenter has started
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "presenter.started",
                        "presenter_id": message.get("presenter_id")
                    }
                )

            elif message.get("action") == "stop-presenting":
                # Notify all clients that presenter has stopped
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "presenter.stopped",
                        "presenter_id": message.get("presenter_id")
                    }
                )

            elif message.get("action") == "status-update":
                # Forward presenter status to admin dashboard
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "presenter.status",
                        "presenter_id": message.get("presenter_id"),
                        "is_presenting": message.get("is_presenting"),
                        "webrtc_state": message.get("webrtc_state"),
                        "ice_state": message.get("ice_state"),
                        "frame_rate": message.get("frame_rate"),
                        "resolution": message.get("resolution"),
                        "bitrate": message.get("bitrate"),
                        "codec": message.get("codec"),
                        "bitrate_cap": message.get("bitrate_cap"),
                        "fps_cap": message.get("fps_cap"),
                        "fec": message.get("fec"),
                        "rtx": message.get("rtx"),
                        "bandwidth_locked": message.get("bandwidth_locked")
                    },
                    role="admin"
                )
                # Presenter heartbeat for displays (independent of buzzer/score heartbeats)
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "presenter.heartbeat",
                        "presenter_id": message.get("presenter_id"),
                        "is_presenting": message.get("is_presenting"),
                        "webrtc_state": message.get("webrtc_state"),
                        "frame_rate": message.get("frame_rate"),
                        "resolution": message.get("resolution"),
                        "bitrate": message.get("bitrate")
                    },
                    role="display"
                )

    except WebSocketDisconnect:
        # Presenter disconnected, notify all clients
        await manager.broadcast_to_session(
            session_id,
            {"event": "presenter.disconnected"}
        )
        manager.disconnect(websocket, session_id, "presenter")
