from __future__ import annotations

from pydantic import BaseModel, Field


class POIMockSettings(BaseModel):
    mock_poi_categories: list[str] = Field(
        default_factory=lambda: ["sights", "food", "bike_shops", "nature", "museums"],
        alias="MOCK_POI_CATEGORIES",
    )
    mock_poi_default_limit: int = Field(default=6, ge=1, le=20, alias="MOCK_POI_DEFAULT_LIMIT")
