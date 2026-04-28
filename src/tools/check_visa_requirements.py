from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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
    # Mock, intentionally conservative.
    # We assume Schengen-like rules for many EU trips; in real integration we'd use a policy DB/API.
    dest = inp.destination_country.lower()
    nat = inp.nationality.lower()

    if dest in {"netherlands", "denmark", "germany", "belgium", "france", "sweden", "norway"} and inp.stay_days <= 90:
        requirement = "unknown" if nat.strip() == "" else "likely_not_required"
        notes = "Mock result. For many nationalities, short stays (<=90 days) in Schengen area may not require a visa, but verify officially."
    else:
        requirement = "may_be_required"
        notes = "Mock result. Visa requirements vary by nationality and destination; verify with official government sources."

    return VisaRequirementsOutput(
        nationality=inp.nationality,
        destination_country=inp.destination_country,
        stay_days=inp.stay_days,
        requirement=requirement,
        notes=notes,
    )

