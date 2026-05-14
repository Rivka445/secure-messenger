from fastapi import APIRouter, Depends, status
from server.schemas import SendMessageRequest, MessageResponse
from server.services import IMessageService
from server.dependencies import get_message_service
from server.core.auth import require_auth
from typing import List

router = APIRouter(tags=["messages"])


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    body: SendMessageRequest,
    username: str = Depends(require_auth),
    service: IMessageService = Depends(get_message_service),
) -> MessageResponse:
    """Endpoint to send a message from the authenticated user.

    Returns a `MessageResponse` representing the stored message (plaintext content).
    """
    return await service.send(username, body.recipient, body.content)


@router.get("/messages", response_model=List[MessageResponse])
def get_messages(
    username: str = Depends(require_auth),
    service: IMessageService = Depends(get_message_service),
) -> List[MessageResponse]:
    """Retrieve all messages for the authenticated user."""
    return service.get_messages(username)
