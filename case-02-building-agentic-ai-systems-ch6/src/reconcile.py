"""Reconciliation checks over an assembled Itinerary.

Plain Python, no model calls. Each check reads the structured itinerary
and reports pass or fail with a reason. Detection only: nothing here
changes the plan.
"""

from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import math

from pydantic import BaseModel

from src.models import Itinerary

PARTY_SIZE = 2  # the request: "7 days and 2 people"
BUDGET_TOTAL = 8000  # the request: "total budget is about $8000"
HOTEL_NIGHTLY_LIMIT = 400  # D1: Tony's call between the request's $300 and $400
BUFFER = timedelta(hours=2)  # R1: after landing, and before the return departure
PARIS = ZoneInfo("Europe/Paris")  # activity start times are local Paris time


def load_itinerary(path: str = "findings/itinerary.json") -> Itinerary:
    """Read a saved itinerary and validate it back into the models."""
    return Itinerary.model_validate_json(Path(path).read_text())

class CheckResult(BaseModel):
    """The outcome of one check."""

    check: str
    passed: bool
    detail: str


def check_budget(itinerary: Itinerary) -> CheckResult:
    """R3 (DES-10): trip total against the budget, hotel rate against D1."""
    flights = itinerary.flight.price_per_person * PARTY_SIZE
    hotel = itinerary.hotel.stay_total
    activities = sum(
        math.ceil(PARTY_SIZE / a.group_size) * a.price
        for a in itinerary.activities.activities
    )
    transport = sum(
        leg.rides * math.ceil(PARTY_SIZE / leg.group_size) * leg.price
        for leg in itinerary.transport.legs
    )
    total = flights + hotel + activities + transport
    rate_ok = itinerary.hotel.nightly_rate <= HOTEL_NIGHTLY_LIMIT
    return CheckResult(
        check="R3 budget",
        passed=total <= BUDGET_TOTAL and rate_ok,
        detail=(
            f"flights {flights:.2f} + hotel {hotel:.2f} + activities {activities:.2f}"
            f" + transport {transport:.2f} = {total:.2f} against {BUDGET_TOTAL};"
            f" hotel {itinerary.hotel.nightly_rate:.2f}/night against {HOTEL_NIGHTLY_LIMIT}"
        ),
    )