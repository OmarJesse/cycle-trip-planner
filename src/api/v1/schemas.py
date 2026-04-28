from __future__ import annotations

from pydantic import BaseModel, Field

from src.api.models import DayPlan, TripPreferences


class ChatV1Request(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1)
    preferences: TripPreferences | None = None


class ChatV1Response(BaseModel):
    conversation_id: str
    reply: str
    plan: list[DayPlan] | None = None

