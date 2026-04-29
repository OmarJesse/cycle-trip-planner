from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from src.api.models import ConversationState
from src.state.base import ConversationStore


@dataclass
class _Entry:
    state: ConversationState
    last_access: float


@dataclass
class InMemoryConversationStore(ConversationStore):
    max_age_seconds: int
    max_count: int
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _by_id: dict[str, _Entry] = field(default_factory=dict)
    _last_sweep: float = 0.0

    @classmethod
    def create(cls, *, max_age_seconds: int, max_count: int) -> "InMemoryConversationStore":
        return cls(max_age_seconds=max_age_seconds, max_count=max_count)

    def get_or_create(self, conversation_id: str | None) -> ConversationState:
        with self._lock:
            now = time.monotonic()
            self._evict_locked(now)

            cid = conversation_id or uuid.uuid4().hex
            entry = self._by_id.get(cid)
            if entry is None:
                entry = _Entry(state=ConversationState(conversation_id=cid), last_access=now)
                self._by_id[cid] = entry
                self._enforce_capacity_locked()
            else:
                entry.last_access = now
            return entry.state

    def get(self, conversation_id: str) -> ConversationState | None:
        with self._lock:
            now = time.monotonic()
            self._evict_locked(now)
            entry = self._by_id.get(conversation_id)
            if entry is None:
                return None
            entry.last_access = now
            return entry.state

    def save(self, state: ConversationState) -> None:
        with self._lock:
            now = time.monotonic()
            self._evict_locked(now)
            self._by_id[state.conversation_id] = _Entry(state=state, last_access=now)
            self._enforce_capacity_locked()

    def _evict_locked(self, now: float) -> None:
        if now - self._last_sweep < self.max_age_seconds:
            return
        cutoff = now - self.max_age_seconds
        self._by_id = {cid: e for cid, e in self._by_id.items() if e.last_access >= cutoff}
        self._last_sweep = now

    def _enforce_capacity_locked(self) -> None:
        overflow = len(self._by_id) - self.max_count
        if overflow <= 0:
            return
        ordered = sorted(self._by_id.items(), key=lambda kv: kv[1].last_access)
        for cid, _ in ordered[:overflow]:
            del self._by_id[cid]
