from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass

from src.api.models import ConversationState
from src.state.base import ConversationStore


@dataclass
class InMemoryConversationStore(ConversationStore):
    _lock: threading.Lock
    _by_id: dict[str, ConversationState]

    @classmethod
    def create(cls) -> "InMemoryConversationStore":
        return cls(_lock=threading.Lock(), _by_id={})

    def get_or_create(self, conversation_id: str | None) -> ConversationState:
        with self._lock:
            cid = conversation_id or uuid.uuid4().hex
            if cid not in self._by_id:
                self._by_id[cid] = ConversationState(conversation_id=cid)
            return self._by_id[cid]

    def save(self, state: ConversationState) -> None:
        with self._lock:
            self._by_id[state.conversation_id] = state

