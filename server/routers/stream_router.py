import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from server.core.auth import require_auth
from server.core.broadcaster import broadcaster
from server.repositories import GroupRepository
from server.dependencies import get_group_repo
from server.core.membership_cache import membership_cache

log = logging.getLogger(__name__)
router = APIRouter(tags=["stream"])


@router.get("/stream")
async def message_stream(username: str = Depends(require_auth), group_repo: GroupRepository = Depends(get_group_repo)) -> StreamingResponse:
    """
    Server-Sent Events (SSE) endpoint that streams messages to an authenticated user.

    This endpoint subscribes the current user to the central broadcaster queue and
    yields messages over an HTTP event-stream. Only messages where the user is the
    sender or the recipient are sent to the client. Timestamps on messages are
    converted to ISO strings if they are not already strings.

    Parameters:
    - username: the authenticated username provided by the `require_auth` dependency

    Returns:
    - StreamingResponse: a FastAPI StreamingResponse configured for "text/event-stream"
    """
    queue = await broadcaster.subscribe()

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE-formatted strings for messages relevant to `username`.

        Yields strings in the SSE format, for example: 'data: {...}\n\n'. The
        generator listens on the broadcaster queue until cancelled, at which
        point it will unsubscribe the queue.
        """
        try:
            while True:
                message: Dict[str, Any] = await queue.get()
                # direct messages keep existing behavior
                if message.get("type") == "group":
                    group_id = message.get("group_id")
                    if group_id is None:
                        continue
                    # check cache first
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
        finally:
            await broadcaster.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
