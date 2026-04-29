from __future__ import annotations

from typing import Protocol

from src.api.models import ConversationState


class ConversationStore(Protocol):
    def get_or_create(self, conversation_id: str | None) -> ConversationState: ...

    def get(self, conversation_id: str) -> ConversationState | None: ...

    def save(self, state: ConversationState) -> None: ...

