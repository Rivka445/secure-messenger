from typing import Optional, List
from sqlalchemy.orm import Session
import logging
from server.models import Group, GroupMember, GroupJoinRequest, GroupMessage
from server.core.membership_cache import membership_cache

log = logging.getLogger(__name__)


class IGroupRepository:
    def get_by_id(self, group_id: int) -> Optional[Group]: ...
    def create(self, name: str, owner: str, join_password_hash: Optional[str]) -> Group: ...
    def add_member(self, group_id: int, username: str, role: str = "member") -> GroupMember: ...
    def remove_member(self, group_id: int, username: str) -> None: ...
    def is_member(self, group_id: int, username: str) -> bool: ...
    def get_members(self, group_id: int) -> List[GroupMember]: ...


class GroupRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, group_id: int) -> Optional[Group]:
        return self._db.query(Group).filter(Group.id == group_id).first()

    def create(self, name: str, owner: str, join_password_hash: Optional[str]) -> Group:
        group = Group(name=name, owner=owner, join_password_hash=join_password_hash)
        self._db.add(group)
        self._db.commit()
        self._db.refresh(group)
        log.info("Created group %s (id=%s) owner=%s", name, group.id, owner)
        return group

    def add_member(self, group_id: int, username: str, role: str = "member") -> GroupMember:
        member = GroupMember(group_id=group_id, username=username, role=role)
        self._db.add(member)
        self._db.commit()
        self._db.refresh(member)
        # Invalidate membership cache for this user/group so consumers see updated state
        try:
            membership_cache.invalidate(group_id, username)
        except Exception:
            # membership cache is ephemeral; ignore cache errors
            pass
        log.info("Added member %s to group %s (role=%s)", username, group_id, role)
        return member

    def remove_member(self, group_id: int, username: str) -> None:
        self._db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.username == username).delete()
        self._db.commit()
        try:
            membership_cache.invalidate(group_id, username)
        except Exception:
            pass
        log.info("Removed member %s from group %s", username, group_id)

    def is_member(self, group_id: int, username: str) -> bool:
        return self._db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.username == username).first() is not None

    def get_members(self, group_id: int) -> List[GroupMember]:
        return self._db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

    def create_group_message(self, group_id: int, sender: str, ciphertext: str) -> GroupMessage:
        msg = GroupMessage(group_id=group_id, sender=sender, ciphertext=ciphertext)
        self._db.add(msg)
        self._db.commit()
        self._db.refresh(msg)
        return msg

    # Join request methods
    def create_join_request(self, group_id: int, username: str, message: str | None, provided_password_ok: bool):
        req = GroupJoinRequest(group_id=group_id, username=username, message=message, provided_password_ok=provided_password_ok)
        self._db.add(req)
        self._db.commit()
        self._db.refresh(req)
        return req

    def list_join_requests(self, group_id: int):
        return self._db.query(GroupJoinRequest).filter(GroupJoinRequest.group_id == group_id, GroupJoinRequest.status == "pending").all()

    def get_join_request(self, request_id: int):
        return self._db.query(GroupJoinRequest).filter(GroupJoinRequest.id == request_id).first()

    def update_join_request_status(self, request_id: int, status: str, processed_by: str | None = None):
        req = self.get_join_request(request_id)
        if not req:
            return None
        req.status = status
        req.processed_by = processed_by
        from datetime import datetime, timezone
        req.processed_at = datetime.now(timezone.utc)
        self._db.add(req)
        self._db.commit()
        self._db.refresh(req)
        return req
