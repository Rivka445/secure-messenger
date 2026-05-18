from typing import List
from fastapi import APIRouter, Depends, status

from server.schemas import (
    CreateGroupRequest,
    GroupResponse,
    JoinGroupRequest,
    JoinGroupResponse,
    GroupMessageRequest,
    MessageResponse,
)
from server.core.auth import require_auth
from server.services.group_service import GroupService
from server.dependencies import get_group_service, get_message_service, get_group_repo
from server.services import IMessageService
from server.repositories import GroupRepository

router = APIRouter(tags=["groups"])


@router.get("/groups/my", response_model=List[GroupResponse])
def my_groups(
    username: str = Depends(require_auth),
    group_repo: GroupRepository = Depends(get_group_repo),
) -> List[GroupResponse]:
    """Return all groups the authenticated user is a member of."""
    return group_repo.get_groups_for_user(username)


@router.get("/groups", response_model=List[GroupResponse])
def list_groups(
    username: str = Depends(require_auth),
    group_repo: GroupRepository = Depends(get_group_repo),
) -> List[GroupResponse]:
    """Return all existing groups."""
    from server.models import Group
    return group_repo._db.query(Group).order_by(Group.id).all()

@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    body: CreateGroupRequest,
    username: str = Depends(require_auth),
    service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    """Create a new group. The authenticated user becomes the owner and an initial member."""
    g = service.create_group(username, body.name, body.join_password)
    return GroupResponse(**g)


@router.post("/groups/{group_id}/join", response_model=JoinGroupResponse)
def join_group(
    group_id: int,
    body: JoinGroupRequest,
    username: str = Depends(require_auth),
    service: GroupService = Depends(get_group_service),
) -> JoinGroupResponse:
    """Join a group immediately. If the group has a password, provide it in the body."""
    result = service.join_group(group_id, username, body.password)
    return JoinGroupResponse(**result)


@router.get("/groups/{group_id}/messages")
def get_group_messages(
    group_id: int,
    username: str = Depends(require_auth),
    group_repo: GroupRepository = Depends(get_group_repo),
):
    """Return message history for a group. Caller must be a member."""
    from fastapi import HTTPException
    if not group_repo.is_member(group_id, username):
        raise HTTPException(status_code=403, detail="not a member")
    msgs = group_repo.get_group_messages(group_id)
    result = []
    for m in msgs:
        try:
            from server.core.crypto import decrypt
            content = decrypt(m.ciphertext)
        except Exception:
            content = "[message unavailable]"
        result.append({"id": m.id, "group_id": m.group_id, "sender": m.sender, "content": content, "created_at": m.created_at})
    return result


@router.post("/groups/{group_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_group_message(
    group_id: int,
    body: GroupMessageRequest,
    username: str = Depends(require_auth),
    message_service: IMessageService = Depends(get_message_service),
    group_repo: GroupRepository = Depends(get_group_repo),
) -> MessageResponse:
    """Send a message to a group.

    The endpoint delegates to MessageService.send_to_group which persists the
    encrypted group message and publishes a plaintext notification to subscribers.
    """
    # delegate to message service which will raise appropriate HTTP exceptions
    return await message_service.send_to_group(username, group_id, body.content, group_repo)
