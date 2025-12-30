from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set
import json
import asyncio
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # {session_id: {role: [websocket, websocket, ...]}}
        self.active_connections: Dict[int, Dict[str, Set[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, session_id: int, role: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        if role not in self.active_connections[session_id]:
            self.active_connections[session_id][role] = set()
        self.active_connections[session_id][role].add(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int, role: str):
        if session_id in self.active_connections:
            if role in self.active_connections[session_id]:
                self.active_connections[session_id][role].discard(websocket)

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
    """WebSocket for main display screen"""
    await manager.connect(websocket, session_id, "display")
    try:
        while True:
            data = await websocket.receive_text()
            # Display is typically receive-only
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, "display")


@router.websocket("/team/{session_id}")
async def websocket_team(websocket: WebSocket, session_id: int, token: str = Query(...)):
    """WebSocket for team clients with buzzer support"""
    # TODO: Validate token and extract team_id
    await manager.connect(websocket, session_id, "team")

    try:
        while True:
            message = await websocket.receive_json()

            # Handle buzz event
            if message.get("action") == "buzz":
                team_id = message.get("team_id")
                device_id = message.get("device_id")

                # Process buzz (integrate with Redis)
                timestamp = datetime.utcnow().isoformat()

                # Broadcast buzz to all relevant clients
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "buzzer.update",
                        "team_id": team_id,
                        "timestamp": timestamp
                    },
                    role="qm"
                )

                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "buzzer.update",
                        "team_id": team_id,
                        "timestamp": timestamp
                    },
                    role="display"
                )

                # Send confirmation to team
                await websocket.send_json({
                    "event": "buzz.confirmed",
                    "timestamp": timestamp
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, "team")


# Helper function to broadcast events (can be called from other modules)
async def broadcast_event(session_id: int, event: dict, role: str = None):
    """Utility function to broadcast events from other parts of the app"""
    await manager.broadcast_to_session(session_id, event, role)
