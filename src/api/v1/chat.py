from __future__ import annotations

from fastapi import APIRouter, Depends

from src.agent.runtime import Runtime
from src.api.v1.dependencies import get_runtime
from src.api.v1.schemas import ChatV1Request, ChatV1Response


router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.post("/chat", response_model=ChatV1Response)
def chat(req: ChatV1Request, rt: Runtime = Depends(get_runtime)) -> ChatV1Response:
    state = rt.store.get_or_create(req.conversation_id)
    reply, updated = rt.orchestrator.handle_turn(
        state=state,
        user_message=req.message,
        preferences_override=req.preferences,
    )
    rt.store.save(updated)

    plan = updated.last_plan if rt.settings.include_structured_plan else None
    return ChatV1Response(conversation_id=updated.conversation_id, reply=reply, plan=plan)

