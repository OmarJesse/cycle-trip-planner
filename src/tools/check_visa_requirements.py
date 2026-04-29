from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.config.runtime import get_settings


class VisaRequirementsInput(BaseModel):
    nationality: str = Field(min_length=2, description="Traveler nationality, e.g. 'Canadian'")
    destination_country: str = Field(min_length=2, description="Destination country, e.g. 'Denmark'")
    stay_days: int = Field(default=14, ge=1, le=365)


class VisaRequirementsOutput(BaseModel):
    nationality: str
    destination_country: str
    stay_days: int
    requirement: Literal["unknown", "likely_not_required", "may_be_required"]
    notes: str


def check_visa_requirements(inp: VisaRequirementsInput) -> VisaRequirementsOutput:
    s = get_settings()
    dest = inp.destination_country.lower()

    if dest in set(s.mock_visa_schengen_countries) and inp.stay_days <= s.mock_visa_max_days_no_visa:
        requirement = "likely_not_required"
        notes = "Based on simplified Schengen rules; confirm with the official consulate."
    else:
        requirement = "may_be_required"
        notes = "Outside the simplified ruleset; confirm with the official consulate."

    return VisaRequirementsOutput(
        nationality=inp.nationality,
        destination_country=inp.destination_country,
        stay_days=inp.stay_days,
        requirement=requirement,
        notes=notes,
    )

