from typing import List
from fastapi import APIRouter, Depends, status

from server.schemas import (
    CreateGroupRequest,
    GroupResponse,
    JoinRequestBody,
    JoinRequestResponse,
    GroupMessageRequest,
)
from server.core.auth import require_auth
from server.services.group_service import GroupService
from server.dependencies import get_group_service, get_message_service, get_group_repo
from server.services import IMessageService

router = APIRouter(tags=["groups"])


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    body: CreateGroupRequest,
    username: str = Depends(require_auth),
    service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    """Create a new group. The authenticated user becomes the owner and an initial member."""
    g = service.create_group(username, body.name, body.join_password)
    return GroupResponse(**g)


@router.post("/groups/{group_id}/join", response_model=JoinRequestResponse, status_code=status.HTTP_201_CREATED)
def request_join(
    group_id: int,
    body: JoinRequestBody,
    username: str = Depends(require_auth),
    service: GroupService = Depends(get_group_service),
) -> JoinRequestResponse:
    """Request to join a group. If the group has a password, provide it in the body."""
    r = service.request_join(group_id, username, body.password, body.message)
    return JoinRequestResponse(**r)


@router.get("/groups/{group_id}/join-requests", response_model=List[JoinRequestResponse])
def list_join_requests(
    group_id: int,
    username: str = Depends(require_auth),
    group_repo = Depends(get_group_repo),
) -> List[JoinRequestResponse]:
    """List pending join requests for a group. Only the group owner should call this."""
    # Simple enforcement: verify caller is owner
    group = group_repo.get_by_id(group_id)
    if not group:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="group not found")
    if group.owner != username:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="only owner can list requests")
    reqs = group_repo.list_join_requests(group_id)
    return [JoinRequestResponse(**r.__dict__) for r in reqs]


@router.post("/groups/{group_id}/join-requests/{request_id}/approve", response_model=JoinRequestResponse)
def approve_request(
    group_id: int,
    request_id: int,
    username: str = Depends(require_auth),
    service: GroupService = Depends(get_group_service),
) -> JoinRequestResponse:
    """Approve a pending join request. Only the group owner can approve."""
    r = service.approve_request(request_id, username)
    return JoinRequestResponse(**r)


@router.post("/groups/{group_id}/join-requests/{request_id}/reject", response_model=JoinRequestResponse)
def reject_request(
    group_id: int,
    request_id: int,
    username: str = Depends(require_auth),
    service: GroupService = Depends(get_group_service),
) -> JoinRequestResponse:
    """Reject a pending join request. Only the group owner can reject."""
    r = service.reject_request(request_id, username)
    return JoinRequestResponse(**r)


@router.post("/groups/{group_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_group_message(
    group_id: int,
    body: GroupMessageRequest,
    username: str = Depends(require_auth),
    message_service: IMessageService = Depends(get_message_service),
    group_repo = Depends(get_group_repo),
):
    """Send a message to a group. Uses MessageService.send_to_group under the hood."""
    # delegate to message service which will raise appropriate HTTP exceptions
    return await message_service.send_to_group(username, group_id, body.content, group_repo)
