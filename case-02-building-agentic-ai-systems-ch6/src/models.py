"""Structured outputs for the Case 02 crew.

Each worker task returns one of these models instead of prose, so the
reconciliation checks can read fields rather than parse paragraphs.
Fields are limited to what a check needs.
"""

from datetime import date, datetime, time
from typing import Literal

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

class HotelChoice(BaseModel):
    """The chosen hotel, copied from find_hotels."""

    name: str
    nightly_rate: float
    stay_total: float = Field(
        description="stay_total for the whole stay, exactly as the tool returned it"
    )
    check_in: date
    check_out: date
    distance_km: float = Field(
        description="distance_km from the Eiffel Tower, exactly as the tool returned it"
    )

class ActivityItem(BaseModel):
    """One scheduled activity, copied from find_activities."""

    day: date
    start_time: time = Field(description="Local Paris time the activity starts, HH:MM")
    name: str = Field(description="Exact activity name from the tool")
    pace: Literal["relaxed", "active"]
    price: float
    group_size: int
    duration_minutes: int


class ActivityPlan(BaseModel):
    """The day-by-day plan: tool activities, plus unpriced suggestions kept apart."""

    activities: list[ActivityItem]
    suggestions: list[str] = Field(
        description="Ideas with no tool behind them and no price. May be empty."
    )

class TransportLeg(BaseModel):
    """One route used in the plan, copied from find_transportation."""

    destination: str = Field(description="Exact destination name from the tool")
    from_station: str
    line: str
    price: float = Field(description="Price in USD for ONE ride, as the tool returned it")
    group_size: int
    rides: int = Field(description="How many times this route is ridden in the plan; a round trip is 2")


class TransportPlan(BaseModel):
    """Every route the plan uses."""

    legs: list[TransportLeg]