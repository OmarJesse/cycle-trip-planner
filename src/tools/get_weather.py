from __future__ import annotations

import hashlib
from pydantic import BaseModel, Field


class GetWeatherInput(BaseModel):
    location: str = Field(min_length=2)
    month: str = Field(min_length=3, description="Month name like 'June'")


class GetWeatherOutput(BaseModel):
    location: str
    month: str
    avg_high_c: int
    avg_low_c: int
    rainfall_mm: int
    summary: str


def get_weather(inp: GetWeatherInput) -> GetWeatherOutput:
    h = int(hashlib.sha256(f"{inp.location}|{inp.month}".encode("utf-8")).hexdigest()[:8], 16)
    avg_high = 16 + (h % 12)  # 16..27
    avg_low = avg_high - (6 + (h % 3))  # -6..-8 delta
    rain = 35 + (h % 70)  # 35..104
    summary = f"Typical {inp.month} weather: mild to warm, with a chance of rain."
    return GetWeatherOutput(
        location=inp.location,
        month=inp.month,
        avg_high_c=avg_high,
        avg_low_c=avg_low,
        rainfall_mm=rain,
        summary=summary,
    )

