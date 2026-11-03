from typing import Dict, Set
from fastapi import WebSocket # pyright: ignore[reportMissingImports]


class ConnectionManager:
    def __init__(self) -> None:
        self.job_rooms: Dict[int, Set[WebSocket]] = {}

    async def join_job_room(self, job_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.job_rooms.setdefault(job_id, set()).add(websocket)

    def leave_job_room(self, job_id: int, websocket: WebSocket) -> None:
        room = self.job_rooms.get(job_id)
        if room and websocket in room:
            room.remove(websocket)
            if not room:
                del self.job_rooms[job_id]

    async def broadcast_to_job(self, job_id: int, message: dict) -> None:
        room = self.job_rooms.get(job_id, set())
        dead = []
        for ws in room:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            room.discard(ws)


manager = ConnectionManager()