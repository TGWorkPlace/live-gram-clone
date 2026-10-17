"""
cache.py — pure in-memory relay state. Nothing is ever written to disk or a DB;
everything here disappears when the process restarts.
"""
import hashlib
import os
from collections import OrderedDict
from typing import Optional, Tuple

from config import CACHE_SIZE


class LRU(OrderedDict):
    """Tiny size-bounded dict that evicts the oldest entry first."""

    def __init__(self, maxsize: int):
        super().__init__()
        self.maxsize = maxsize

    def put(self, key, value):
        self[key] = value
        self.move_to_end(key)
        while len(self) > self.maxsize:
            self.popitem(last=False)


class RelayCache:
    def __init__(self, size: int):
        # User the admin is currently talking to (None until someone writes in)
        self.connected: Optional[int] = None
        self._salt = os.urandom(8)

        # admin-chat message id  -> (user_id, original message id in user's chat)
        self.admin_view = LRU(size)
        # (user_id, user message id) -> message id of its copy in admin chat
        self.user_view = LRU(size)
        # admin's own message id -> (user_id, delivered message id in user's chat)
        self.delivered = LRU(size)
        # (user_id, delivered message id) -> admin's own message id
        self.delivered_rev = LRU(size)

    # -- identity -----------------------------------------------------------
    def alias(self, user_id: int) -> str:
        """Anonymous per-run label so the admin can tell users apart."""
        h = hashlib.blake2s(self._salt + str(user_id).encode(), digest_size=3)
        return "User #" + h.hexdigest().upper()

    # -- linking ------------------------------------------------------------
    def link_user_msg(self, user_id: int, user_msg_id: int, admin_copy_id: int):
        self.admin_view.put(admin_copy_id, (user_id, user_msg_id))
        self.user_view.put((user_id, user_msg_id), admin_copy_id)

    def link_admin_msg(self, admin_msg_id: int, user_id: int, delivered_id: int):
        self.delivered.put(admin_msg_id, (user_id, delivered_id))
        self.delivered_rev.put((user_id, delivered_id), admin_msg_id)

    # -- reply resolution ---------------------------------------------------
    def resolve_admin_reply(self, replied_id: Optional[int]) -> Optional[Tuple[int, int]]:
        """Admin replied to a message → (user_id, message id to reply to in user's chat)."""
        if not replied_id:
            return None
        if replied_id in self.admin_view:
            return self.admin_view[replied_id]
        if replied_id in self.delivered:
            return self.delivered[replied_id]
        return None

    def resolve_user_reply(self, user_id: int, replied_id: Optional[int]) -> Optional[int]:
        """User replied to a message → message id to reply to in admin chat."""
        if not replied_id:
            return None
        return self.user_view.get((user_id, replied_id)) or self.delivered_rev.get(
            (user_id, replied_id)
        )


cache = RelayCache(CACHE_SIZE)
