from typing import Optional
import logging
import asyncio

from server.repositories.group_repository import GroupRepository
from server.core.auth import hash_password, verify_password
from server.core.membership_cache import membership_cache
from server import exceptions as app_exceptions

log = logging.getLogger(__name__)
# Note: schemas for GroupRequest/GroupResponse can be added in server/schemas when desired.


class GroupService:
    def __init__(self, group_repo: GroupRepository):
        self._groups = group_repo

    def create_group(self, owner: str, name: str, join_password: Optional[str] = None) -> dict:
        # create and add owner
        join_hash = None
        if join_password:
            join_hash = hash_password(join_password)
        group = self._groups.create(name, owner, join_hash)
        # add owner as member
        self._groups.add_member(group.id, owner, role="owner")
        try:
            membership_cache.invalidate(group.id, owner)
        except Exception:
            log.debug("Failed to invalidate membership cache for %s in %s", owner, group.id)
        log.info("Created group %s (id=%s) by owner=%s", name, group.id, owner)
        # include created_at so response_model (GroupResponse) can validate
        return {
            "id": group.id,
            "name": group.name,
            "owner": group.owner,
            "created_at": group.created_at,
        }

    def join_group(self, group_id: int, username: str, password: Optional[str]) -> dict:
        """Join a group immediately if password is correct."""
        group = self._groups.get_by_id(group_id)
        if not group:
            raise app_exceptions.NotFoundError("group not found")
        
        if self._groups.is_member(group_id, username):
            raise app_exceptions.BadRequestError("already a member")
        
        # Check password
        if group.join_password_hash:
            if not password:
                raise app_exceptions.UnauthorizedError("password required")
            if not verify_password(password, group.join_password_hash):
                raise app_exceptions.UnauthorizedError("incorrect password")
        
        # Add member immediately
        self._groups.add_member(group_id, username)
        try:
            membership_cache.invalidate(group_id, username)
        except Exception:
            log.debug("Failed to invalidate membership cache for %s in %s", username, group_id)
        
        log.info("User %s joined group %s", username, group_id)
        return {"success": True, "message": "joined successfully"}
