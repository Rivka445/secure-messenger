import asyncio
import json
import logging
import queue as std_queue

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from server.core.auth import decode_access_token
from server.core.broadcaster import broadcaster
from server.repositories import GroupRepository
from server.dependencies import get_group_repo
from server.core.membership_cache import membership_cache

log = logging.getLogger(__name__)
router = APIRouter(tags=["stream"])

_optional_bearer = HTTPBearer(auto_error=False)


def _resolve_username(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    token: str | None = Query(default=None),
) -> str:
    """Resolve authenticated username from Bearer header or ?token= query param.

    Bearer header takes priority. Falls back to ?token= for browser EventSource
    clients that cannot set custom headers (known trade-off: token appears in logs).
    """
    if credentials:
        return decode_access_token(credentials.credentials)
    if token:
        return decode_access_token(token)
    raise HTTPException(status_code=403, detail="Not authenticated")


@router.get("/stream")
async def message_stream(
    username: str = Depends(_resolve_username),
    group_repo: GroupRepository = Depends(get_group_repo),
):
    q: std_queue.Queue = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    message = await asyncio.to_thread(q.get, True, 1.0)
                except std_queue.Empty:
                    yield ': keepalive\n\n'
                    continue

                if message.get("type") == "group":
                    group_id = message.get("group_id")
                    if group_id is None:
                        continue
                    cached = membership_cache.get(group_id, username)
                    if cached is None:
                        is_mem = await asyncio.to_thread(group_repo.is_member, group_id, username)
                        membership_cache.set(group_id, username, is_mem)
                    else:
                        is_mem = cached
                    if not is_mem:
                        continue
                else:
                    if not (message.get("sender") == username or message.get("recipient") == username):
                        continue

                if not isinstance(message.get("created_at"), str):
                    message["created_at"] = message["created_at"].isoformat()
                yield f"data: {json.dumps(message)}\n\n"
        except asyncio.CancelledError:
            log.info(f"Stream closed for user: {username}")
            raise
        finally:
            broadcaster.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})
