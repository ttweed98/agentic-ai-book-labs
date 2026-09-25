"""Structured outputs for the Case 02 crew.

Each worker task returns one of these models instead of prose, so the
reconciliation checks can read fields rather than parse paragraphs.
Fields are limited to what a check needs.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class FlightChoice(BaseModel):
    """The chosen round-trip flight offer, copied from search_flights."""

    carrier: str
    flight_numbers: list[str]
    price_per_person: float
    outbound_arrives_at: datetime = Field(
        description="arrives_at of the outbound leg, exactly as the tool returned it"
    )
    return_departs_at: datetime = Field(
        description="departs_at of the return leg, exactly as the tool returned it"
    )