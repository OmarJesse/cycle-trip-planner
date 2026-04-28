from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.models import ChatRequest, ChatResponse
from src.api.v1.dependencies import get_runtime
from src.agent.runtime import Runtime


router = APIRouter(prefix="/api/v0", tags=["v0"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, rt: Runtime = Depends(get_runtime)) -> ChatResponse:
    state = rt.store.get_or_create(req.conversation_id)
    reply, updated = rt.orchestrator.handle_turn(state=state, user_message=req.message)
    rt.store.save(updated)
    return ChatResponse(conversation_id=updated.conversation_id, reply=reply)

