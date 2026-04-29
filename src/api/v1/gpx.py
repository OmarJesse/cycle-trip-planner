from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from src.agent.orchestration.blocks import block_attr
from src.agent.runtime import Runtime
from src.api.deps import get_runtime
from src.api.gpx import GPX_MEDIA_TYPE, gpx_filename, route_to_gpx
from src.tools.get_route import GetRouteOutput
from src.tools.names import ToolName


router = APIRouter(prefix="/conversations", tags=["v1"])


@router.get("/{conversation_id}/route.gpx")
def export_route_gpx(conversation_id: str, rt: Runtime = Depends(get_runtime)) -> Response:
    state = rt.store.get(conversation_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    route = extract_latest_route(state.messages)
    if route is None:
        raise HTTPException(
            status_code=404,
            detail="No route has been planned yet for this conversation.",
        )

    return Response(
        content=route_to_gpx(route),
        media_type=GPX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{gpx_filename(route)}"'},
    )


def extract_latest_route(history: list[dict[str, Any]]) -> GetRouteOutput | None:
    """Walk the conversation in reverse, find the most recent successful get_route tool call,
    and return its parsed output. Returns None if no get_route has been made (or the latest one errored)."""

    tool_use_id_for_route: str | None = None
    for msg in reversed(history):
        if msg.get("role") != "assistant":
            continue
        for block in _content_blocks(msg):
            if block_attr(block, "type") != "tool_use":
                continue
            if block_attr(block, "name") != ToolName.GET_ROUTE.value:
                continue
            tool_use_id_for_route = block_attr(block, "id")
            break
        if tool_use_id_for_route:
            break

    if not tool_use_id_for_route:
        return None

    for msg in history:
        if msg.get("role") != "user":
            continue
        for block in _content_blocks(msg):
            if block_attr(block, "type") != "tool_result":
                continue
            if block_attr(block, "tool_use_id") != tool_use_id_for_route:
                continue
            if block_attr(block, "is_error"):
                return None
            return _parse_route_result(block)

    return None


def _content_blocks(msg: dict[str, Any]) -> list[Any]:
    content = msg.get("content")
    return content if isinstance(content, list) else []


def _parse_route_result(block: Any) -> GetRouteOutput | None:
    inner = block_attr(block, "content")
    if not isinstance(inner, list):
        return None
    for part in inner:
        if block_attr(part, "type") != "text":
            continue
        text = block_attr(part, "text") or ""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        try:
            return GetRouteOutput.model_validate(payload)
        except Exception:
            continue
    return None
