from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional


class TripPreferences(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    daily_km: Optional[int] = Field(default=None, ge=20, le=300)
    month: Optional[str] = None
    lodging_preference: Literal["camping", "hostel", "hotel", "mixed"] = "mixed"
    hostel_every_n_nights: Optional[int] = Field(default=None, ge=1, le=30)
    nationality: Optional[str] = None
    stay_days: Optional[int] = Field(default=None, ge=1, le=365)
    notes: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    start: str
    end: str
    distance_km: float
    elevation_gain_m: int
    difficulty: Literal["easy", "moderate", "hard"]
    weather_summary: str
    sleep: str
    highlights: list[str] = Field(default_factory=list)


class ConversationState(BaseModel):
    conversation_id: str
    preferences: TripPreferences = Field(default_factory=TripPreferences)
    messages: list[dict] = Field(default_factory=list)

