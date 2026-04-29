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


def _normalize(value: str) -> str:
    return value.strip().lower().rstrip(".")


def check_visa_requirements(inp: VisaRequirementsInput) -> VisaRequirementsOutput:
    s = get_settings()
    dest = _normalize(inp.destination_country)
    nat = _normalize(inp.nationality)

    schengen = {_normalize(c) for c in s.mock_visa_schengen_countries}
    visa_free_nats = {_normalize(n) for n in s.mock_visa_schengen_visa_free_nationalities}

    is_schengen_dest = dest in schengen
    is_visa_free_nat = nat in visa_free_nats
    short_stay = inp.stay_days <= s.mock_visa_max_days_no_visa

    if is_schengen_dest and is_visa_free_nat and short_stay:
        requirement = "likely_not_required"
        notes = (
            f"Based on simplified Schengen rules, {inp.nationality} travelers typically do not need a visa "
            f"for stays up to {s.mock_visa_max_days_no_visa} days. Confirm with the official consulate."
        )
    elif is_schengen_dest and not is_visa_free_nat:
        requirement = "may_be_required"
        notes = (
            f"{inp.destination_country} is in the Schengen area, but {inp.nationality} nationals are not in "
            "the simplified visa-free list. A short-stay Schengen visa is likely required — confirm with the consulate."
        )
    elif is_schengen_dest and not short_stay:
        requirement = "may_be_required"
        notes = (
            f"Stays beyond {s.mock_visa_max_days_no_visa} days in the Schengen area typically require a long-stay "
            "national visa or residence permit. Confirm with the official consulate."
        )
    else:
        requirement = "may_be_required"
        notes = "Outside the simplified Schengen ruleset; confirm with the official consulate."

    return VisaRequirementsOutput(
        nationality=inp.nationality,
        destination_country=inp.destination_country,
        stay_days=inp.stay_days,
        requirement=requirement,
        notes=notes,
    )
