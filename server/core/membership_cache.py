import time
from typing import Tuple

# Simple in-memory TTL cache for membership checks
class MembershipCache:
    def __init__(self, ttl_seconds: int = 15):
        self.ttl = ttl_seconds
        self._store: dict[Tuple[int, str], Tuple[bool, float]] = {}

    def get(self, group_id: int, username: str):
        key = (group_id, username)
        entry = self._store.get(key)
        if not entry:
            return None
        value, ts = entry
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        return value

    def set(self, group_id: int, username: str, is_member: bool):
        key = (group_id, username)
        self._store[key] = (is_member, time.time())

    def invalidate(self, group_id: int, username: str):
        key = (group_id, username)
        self._store.pop(key, None)


membership_cache = MembershipCache()
