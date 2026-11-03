from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect # pyright: ignore[reportMissingImports]
from jose import JWTError # pyright: ignore[reportMissingModuleSource]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.user import User
from app.database.session import get_db
from app.core.security import decode_access_token
from app.logics.connection_manager import manager
from app.logics.job_message_service import get_chat_job

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/jobs/{job_id}")
async def job_updates(
    websocket: WebSocket,
    job_id: int,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not token:
        await websocket.close(code=4401, reason="Authentication required")
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", ""))
    except (JWTError, TypeError, ValueError):
        await websocket.close(code=4401, reason="Invalid token")
        return

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            await websocket.close(code=4401, reason="User not found")
            return
        try:
            get_chat_job(db, job_id, user)
        except HTTPException:
            await websocket.close(code=4403, reason="Access denied")
            return
    finally:
        db.close()

    await manager.join_job_room(job_id, websocket)
    try:
        while True:
            event = await websocket.receive()
            if event["type"] == "websocket.disconnect":
                break
            if event.get("text") is not None or event.get("bytes") is not None:
                await websocket.close(code=4400, reason="Send chat messages through the authenticated chat API")
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.leave_job_room(job_id, websocket)
