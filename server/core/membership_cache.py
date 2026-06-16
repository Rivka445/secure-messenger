import time
from typing import Tuple

"""In-memory TTL membership cache.

This lightweight helper stores boolean membership flags for (group_id, username)
pairs with a timestamp. It is intended to avoid repeated DB lookups for
short-lived membership checks.
"""


class MembershipCache:
    def __init__(self, ttl_seconds: int = 15) -> None:
        """Create a MembershipCache with TTL in seconds."""
        self.ttl = ttl_seconds
        self._store: dict[Tuple[int, str], Tuple[bool, float]] = {}

    def get(self, group_id: int, username: str) -> bool | None:
        """Return cached membership boolean or None if missing/expired."""
        key = (group_id, username)
        entry = self._store.get(key)
        if not entry:
            return None
        value, ts = entry
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        return value

    def set(self, group_id: int, username: str, is_member: bool) -> None:
        """Store a membership boolean with current timestamp."""
        key = (group_id, username)
        self._store[key] = (is_member, time.time())

    def invalidate(self, group_id: int, username: str) -> None:
        """Remove a cached membership entry if present."""
        key = (group_id, username)
        self._store.pop(key, None)

    def invalidate_group(self, group_id: int) -> None:
        """Remove all cached entries for a specific group."""
        keys_to_remove = [k for k in self._store.keys() if k[0] == group_id]
        for key in keys_to_remove:
            self._store.pop(key, None)


membership_cache = MembershipCache()
