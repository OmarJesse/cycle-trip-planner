from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from src.agent.runtime import Runtime
from src.api.deps import get_runtime
from src.api.schemas import ChatRequest, ChatResponse, ToolCallView


router = APIRouter(tags=["v1"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, response: Response, rt: Runtime = Depends(get_runtime)) -> ChatResponse:
    state = rt.store.get_or_create(req.conversation_id)
    result, updated = rt.orchestrator_v1.handle_turn(
        state=state,
        user_message=req.message,
        preferences_override=req.preferences,
    )
    rt.store.save(updated)

    if result.upstream_failure:
        response.status_code = status.HTTP_502_BAD_GATEWAY

    tool_calls = [
        ToolCallView(name=t.name, input=t.input, output=t.output, is_error=t.is_error)
        for t in result.tool_calls
    ]
    return ChatResponse(
        conversation_id=updated.conversation_id,
        reply=result.reply,
        tool_calls=tool_calls,
        rounds=result.rounds,
        truncated=result.truncated,
        error=result.error,
    )
