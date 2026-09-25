"""Reconciliation checks over an assembled Itinerary.

Plain Python, no model calls. Each check reads the structured itinerary
and reports pass or fail with a reason. Detection only: nothing here
changes the plan.
"""

from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import math

from pydantic import BaseModel

from src.models import Itinerary

from fixtures import activities as activity_fixture
from fixtures import flights as flight_fixture
from fixtures import hotels as hotel_fixture
from fixtures import transportation as transport_fixture

PARTY_SIZE = 2  # the request: "7 days and 2 people"
BUDGET_TOTAL = 8000  # the request: "total budget is about $8000"
HOTEL_NIGHTLY_LIMIT = 400  # D1: Tony's call between the request's $300 and $400
BUFFER = timedelta(hours=2)  # R1: after landing, and before the return departure
PARIS = ZoneInfo("Europe/Paris")  # activity start times are local Paris time
FIRST_NIGHT_CUTOFF = time(6, 0)  # S-1: arriving before this, the first night still counts
WALKING_DISTANCE_KM = 1.0  # R7: Ibis (0.6 km) passes; Marriott (2.1) and Citadines (3.4) do not
TRIP_START = "2026-11-02"  # the request's check-in date, shifted to 2026
TRIP_END = "2026-11-09"  # the request's check-out date, shifted to 2026


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

def check_flight_buffers(itinerary: Itinerary) -> CheckResult:
    """R1 (DES-8a): no activity within BUFFER of landing or of the return departure."""
    earliest = itinerary.flight.outbound_arrives_at + BUFFER
    latest_end = itinerary.flight.return_departs_at - BUFFER
    problems = []
    for a in itinerary.activities.activities:
        start = a.starts_at if a.starts_at.tzinfo else a.starts_at.replace(tzinfo=PARIS)
        end = start + timedelta(minutes=a.duration_minutes)
        if start < earliest:
            problems.append(f"{a.name} starts {start:%d %b %H:%M}, before {earliest:%d %b %H:%M}")
        if end > latest_end:
            problems.append(f"{a.name} ends {end:%d %b %H:%M}, after {latest_end:%d %b %H:%M}")
    return CheckResult(
        check="R1 flight buffers",
        passed=not problems,
        detail="; ".join(problems) or "all activities clear of both buffers",
    )

def check_hotel_dates(itinerary: Itinerary) -> CheckResult:
    """R2 (DES-8b): hotel check-in and check-out line up with the flights."""
    hotel = itinerary.hotel
    arrival = itinerary.flight.outbound_arrives_at.astimezone(PARIS)
    departure = itinerary.flight.return_departs_at.astimezone(PARIS)
    first_night_ends = datetime.combine(
        hotel.check_in + timedelta(days=1), FIRST_NIGHT_CUTOFF, tzinfo=PARIS
    )
    problems = []
    if arrival.date() < hotel.check_in:
        problems.append(f"arrives {arrival:%d %b %H:%M}, before check-in on {hotel.check_in:%d %b}")
    if arrival > first_night_ends:
        problems.append(f"arrives {arrival:%d %b %H:%M}: the {hotel.check_in:%d %b} night is paid but unused")
    if departure.date() != hotel.check_out:
        problems.append(f"departs {departure:%d %b}, but check-out is {hotel.check_out:%d %b}")
    return CheckResult(
        check="R2 hotel dates",
        passed=not problems,
        detail="; ".join(problems) or "hotel dates match the flights",
    )

def check_transport_origin(itinerary: Itinerary) -> CheckResult:
    """R7 (DES-8, M-4): routes start within walking distance of the hotel.

    Every fixture route starts at Bir-Hakeim, by the Eiffel Tower, and the
    hotel's distance_km is measured from the Eiffel Tower.
    """
    hotel = itinerary.hotel
    stations = sorted({leg.from_station for leg in itinerary.transport.legs})
    if not stations:
        return CheckResult(check="R7 transport origin", passed=True, detail="no routes to check")
    if hotel.distance_km <= WALKING_DISTANCE_KM:
        return CheckResult(
            check="R7 transport origin",
            passed=True,
            detail=f"{hotel.name} is {hotel.distance_km} km from {', '.join(stations)}",
        )
    return CheckResult(
        check="R7 transport origin",
        passed=False,
        detail=(
            f"routes start at {', '.join(stations)} by the Eiffel Tower; "
            f"{hotel.name} is {hotel.distance_km} km away"
        ),
    )

def check_pace_mix(itinerary: Itinerary) -> CheckResult:
    """R6 (DES-7): a moderate plan contains both relaxed and active activities."""
    paces = {a.pace for a in itinerary.activities.activities}
    missing = {"relaxed", "active"} - paces
    return CheckResult(
        check="R6 pace mix",
        passed=not missing,
        detail=f"missing: {', '.join(sorted(missing))}" if missing else "both relaxed and active present",
    )

def check_fixture_names() -> CheckResult:
    """R5 (DES-7): every activity has a transport route under the same exact name."""
    catalogue = activity_fixture.find_activities(
        location="Paris", date=TRIP_START, preferences="any"
    )["activities"]
    missing = []
    for item in catalogue:
        routes = transport_fixture.find_transportation(
            location="Paris", origin="Hotel", destination=item["name"]
        )
        if routes["count"] == 0:
            missing.append(item["name"])
    return CheckResult(
        check="R5 fixture names",
        passed=not missing,
        detail=f"no route for: {', '.join(missing)}" if missing else "every activity has a route",
    )

def check_traceability(itinerary: Itinerary) -> CheckResult:
    """R4 (DES-7): every chosen item matches what a fixture actually returned."""
    problems = []

    offers = flight_fixture.search_flights(
        origin="JFK", destination="CDG", depart_date=TRIP_START, return_date=TRIP_END
    )["offers"]
    f = itinerary.flight
    if not any(o["carrier"] == f.carrier and o["price_per_person"] == f.price_per_person for o in offers):
        problems.append(f"flight: {f.carrier} at {f.price_per_person} is not a fixture offer")

    hotels = hotel_fixture.find_hotels(location="Paris", check_in=TRIP_START, check_out=TRIP_END)["hotels"]
    h = itinerary.hotel
    if not any(x["name"] == h.name and x["stay_total"] == h.stay_total for x in hotels):
        problems.append(f"hotel: {h.name} at {h.stay_total} is not a fixture hotel")

    catalogue = {
        x["name"]: x
        for x in activity_fixture.find_activities(
            location="Paris", date=TRIP_START, preferences="any"
        )["activities"]
    }
    for a in itinerary.activities.activities:
        item = catalogue.get(a.name)
        if item is None or item["price"] != a.price or item["group_size"] != a.group_size:
            problems.append(f"activity: {a.name} at {a.price} is not in the catalogue")

    for leg in itinerary.transport.legs:
        routes = transport_fixture.find_transportation(
            location="Paris", origin="Hotel", destination=leg.destination
        )["routes"]
        if not any(r["from_station"] == leg.from_station and r["price"] == leg.price for r in routes):
            problems.append(f"transport: {leg.destination} from {leg.from_station} is not a fixture route")

    return CheckResult(
        check="R4 traceability",
        passed=not problems,
        detail="; ".join(problems) or "every item matches a fixture result",
    )