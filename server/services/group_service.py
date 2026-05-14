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
        return {"id": group.id, "name": group.name, "owner": group.owner}

    def request_join(self, group_id: int, username: str, password: Optional[str], message: Optional[str]) -> dict:
        group = self._groups.get_by_id(group_id)
        if not group:
            raise app_exceptions.NotFoundError("group not found")
        provided_ok = False
        if group.join_password_hash:
            if not password:
                provided_ok = False
            else:
                provided_ok = verify_password(password, group.join_password_hash)
        else:
            provided_ok = True
        req = self._groups.create_join_request(group_id, username, message, provided_ok)
        log.info("User %s requested to join group %s (request_id=%s)", username, group_id, req.id)
        return {"id": req.id, "status": req.status}

    def approve_request(self, request_id: int, approver: str) -> dict:
        req = self._groups.get_join_request(request_id)
        if not req:
            raise app_exceptions.NotFoundError("request not found")
        # Only group owner/admin should approve — simple check
        group = self._groups.get_by_id(req.group_id)
        if group.owner != approver:
            raise app_exceptions.ForbiddenError("only owner can approve")
        # add member
        self._groups.add_member(req.group_id, req.username)
        try:
            membership_cache.invalidate(req.group_id, req.username)
        except Exception:
            log.debug("Failed to invalidate cache after approving request %s", request_id)
        updated = self._groups.update_join_request_status(request_id, "approved", processed_by=approver)
        log.info("Join request %s approved by %s", request_id, approver)
        return {"id": updated.id, "status": updated.status}

    def reject_request(self, request_id: int, approver: str) -> dict:
        req = self._groups.get_join_request(request_id)
        if not req:
            raise app_exceptions.NotFoundError("request not found")
        group = self._groups.get_by_id(req.group_id)
        if group.owner != approver:
            raise app_exceptions.ForbiddenError("only owner can reject")
        updated = self._groups.update_join_request_status(request_id, "rejected", processed_by=approver)
        log.info("Join request %s rejected by %s", request_id, approver)
        return {"id": updated.id, "status": updated.status}
