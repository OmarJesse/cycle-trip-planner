from __future__ import annotations

from dataclasses import dataclass

from src.agent.providers.factory import build_provider
from src.agent.v1_orchestrator import AgentOrchestrator
from src.config.settings import Settings
from src.state.memory import InMemoryConversationStore
from src.tools.builtins import build_registry


@dataclass(frozen=True)
class Runtime:
    settings: Settings
    store: InMemoryConversationStore
    orchestrator: AgentOrchestrator


def build_runtime() -> Runtime:
    settings = Settings()
    store = InMemoryConversationStore.create()
    registry = build_registry()
    provider = build_provider(settings)
    orchestrator = AgentOrchestrator(settings=settings, provider=provider, registry=registry)
    return Runtime(settings=settings, store=store, orchestrator=orchestrator)

