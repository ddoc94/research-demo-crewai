"""Schemas for structured task output. Forces shape rather than asking for it."""

from typing import Literal

from pydantic import BaseModel, Field


class Finding(BaseModel):
    type: Literal["DEVELOPMENT", "RISK", "CAPITAL"]
    statement: str = Field(
        ...,
        description="One sentence. Write NOT ESTABLISHED if this type could not be sourced.",
    )
    url: str = Field(..., description="The URL retrieved. Empty string if not established.")
    date: str = Field(..., description="Source date, YYYY-MM-DD. Empty string if not established.")
    provenance: Literal["COMPANY-ISSUED", "INDEPENDENT", ""] = Field(
        ..., description="Empty string if not established."
    )

    @property
    def established(self) -> bool:
        return self.statement.strip().upper() != "NOT ESTABLISHED" and bool(self.url.strip())


class CompanySummary(BaseModel):
    company_name: str = "UNKNOWN"
    year_founded: str = "UNKNOWN"
    primary_industry: str = "UNKNOWN"
    headquarters_country: str = "UNKNOWN"
    public_or_private: str = "UNKNOWN"
    products_services: str = "UNKNOWN"


class ResearchOutput(BaseModel):
    """What the researcher returns."""

    summary: CompanySummary
    findings: list[Finding] = Field(
        ..., description="Exactly three items, one of each type.", min_length=3, max_length=3
    )


class VerifiedOutput(BaseModel):
    """What the verifier returns."""

    summary: CompanySummary
    findings: list[Finding] = Field(..., min_length=3, max_length=3)
    verification_notes: list[str] = Field(
        default_factory=list,
        description="One short line per change made. Empty if nothing changed.",
    )
    verified_count: int = Field(
        ..., description="How many findings survived verification, 0 to 3.", ge=0, le=3
    )
