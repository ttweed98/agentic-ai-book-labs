"""Corrected flight search fixture for Chapter 6.

Returns round-trip flight offers for a route and date pair.

Replaces the book's `search_flights` stub, which accepted a `date`
argument and discarded it, returned clock times with no date attached,
stored a `duration` that disagreed with its own departure and arrival
times by one hour on every record, and gave no currency or stop count.

Closes:
    DES-2   flight records carry no date
    DES-3   arrival times wrong by one hour on all three records
    DES-4   "direct flights preferred" not evaluable, no stops field
    DES-6   `date` parameter accepted and ignored
    DES-9   prices with no declared currency
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def search_flights(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str,
) -> dict:
    """Search round-trip flights between two airports.
    
    Args:
        origin: IATA code of the departure airport, e.g. "JFK".
        destination: IATA code of the arrival airport, e.g. "CDG".
        depart_date: Outbound date, ISO 8601, e.g. "2025-05-07".
        return_date: Return date, ISO 8601, e.g. "2025-05-14".
    
    Returns:
        A dict with one key, "offers", holding a list of round-trip
        offers. Each offer has a single price covering both legs.
    """
    def leg(
        *,
        origin_code: str,
        origin_tz: str,
        destination_code: str,
        destination_tz: str,
        depart_local: str,
        hours: float,
        stops: int,
    ) -> dict:
        """Build one flight leg with a computed arrival time.
        
        Args:
            origin_code: IATA code of this leg's departure airport.
            origin_tz: IANA timezone of the departure airport,
                e.g. "America/New_York".
            destination_code: IATA code of this leg's arrival airport.
            destination_tz: IANA timezone of the arrival airport,
                e.g. "Europe/Paris".
            depart_local: Local departure time, ISO 8601, no offset.
            hours: Time in the air.
            stops: Number of intermediate stops. 0 is a direct flight.
        
        Returns:
            A dict for one leg. `arrives_at` is derived from
            `departs_at` and `hours`, never typed by hand.
        """
        dep = datetime.fromisoformat(depart_local).replace(
            tzinfo=ZoneInfo(origin_tz)
        )
        arr = (dep + timedelta(hours=hours)).astimezone(
            ZoneInfo(destination_tz)
        )
        return {
            "from": origin_code,
            "to": destination_code,
            "departs_at": dep.isoformat(),
            "arrives_at": arr.isoformat(),
            "stops": stops,
        }

    ny_airports = {"JFK", "EWR"}
        
    if origin not in ny_airports or destination != "CDG":
        return {
            "offers": [],
            "note": (
                f"No routes for {origin}-{destination}. "
                "This fixture covers JFK/EWR to CDG only."
            ),
        }  
        
    offers = [
        {
            "carrier": "Air France",
            "flight_numbers": ["AF 007", "AF 008"],
            "currency": "USD",
            "price_per_person": 850,
            "legs": [
                leg(
                    origin_code="JFK",
                    origin_tz="America/New_York",
                    destination_code="CDG",
                    destination_tz="Europe/Paris",
                    depart_local=f"{depart_date}T10:30:00",
                    hours=7.5,
                    stops=0,
                ),
                leg(
                    origin_code="CDG",
                    origin_tz="Europe/Paris",
                    destination_code="JFK",
                    destination_tz="America/New_York",
                    depart_local=f"{return_date}T13:00:00",
                    hours=8.5,
                    stops=0,
                ),
            ],
        },
        {
            "carrier": "Delta Air Lines",
            "flight_numbers": ["DL 264", "DL 265"],
            "currency": "USD",
            "price_per_person": 780,
            "legs": [
                leg(
                    origin_code="JFK",
                    origin_tz="America/New_York",
                    destination_code="CDG",
                    destination_tz="Europe/Paris",
                    depart_local=f"{depart_date}T17:30:00",
                    hours=7.75,
                    stops=0,
                ),
                leg(
                    origin_code="CDG",
                    origin_tz="Europe/Paris",
                    destination_code="JFK",
                    destination_tz="America/New_York",
                    depart_local=f"{return_date}T10:15:00",
                    hours=8.25,
                    stops=0,
                ),
            ],
        },
        {
            "carrier": "United Airlines",
            "flight_numbers": ["UA 57", "UA 58"],
            "currency": "USD",
            "price_per_person": 920,
            "legs": [
                leg(
                    origin_code="EWR",
                    origin_tz="America/New_York",
                    destination_code="CDG",
                    destination_tz="Europe/Paris",
                    depart_local=f"{depart_date}T20:45:00",
                    hours=7.9,
                    stops=1,
                ),
                leg(
                    origin_code="CDG",
                    origin_tz="Europe/Paris",
                    destination_code="EWR",
                    destination_tz="America/New_York",
                    depart_local=f"{return_date}T11:30:00",
                    hours=8.6,
                    stops=1,
                ),
            ],
        },
    ]
    return {"offers": offers}