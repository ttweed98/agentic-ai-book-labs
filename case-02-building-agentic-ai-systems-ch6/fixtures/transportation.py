"""Corrected transportation fixture for Chapter 6.

Returns one metro route per destination, from a fixed origin station.

Replaces the book's `find_transportation` stub, which accepted a
location, an origin and a destination, used none of them, and returned
the same four options with a hardcoded metro route on every call. Three
calls in one run returned byte-identical JSON: the agent wrote three
different recommendations from it and invented the differences.

Stations, fares and durations are illustrative, not live. Every trip
starts at Bir-Hakeim, the station nearest the Eiffel Tower, which is
where the hotels in `hotels.py` are measured from.

Closes:
    DES-6   parameters accepted but never used
    DES-7   identical results, invented differentiation
    DES-9   prices with no declared currency
"""

ORIGIN_STATION = "Bir-Hakeim"
FARE_USD = 2.75


def find_transportation(
    location: str,
    origin: str,
    destination: str,
) -> dict:
    """Find the metro route to a destination.
    
    Args:
        location: City name, e.g. "Paris".
        origin: Starting point, as the book gave it. Echoed back, not
            used: every trip starts at ORIGIN_STATION.
        destination: Where the traveller is going, e.g. "Louvre
            Guided Visit". Matched against the routes below.
    
    Returns:
        A dict with the matching route under "routes" and its size
        under "count". `count` is 0 with a "note" when the destination
        is not one this fixture covers.
    """
    if location != "Paris":
        return {
            "location": location,
            "origin": origin,
            "destination": destination,
            "count": 0,
            "note": (
                f"No transportation for {location}. "
                "This fixture covers Paris only."
            ),
            "routes": [],
        }
    
    def route(
        *,
        destination: str,
        station: str,
        line: str,
        duration_minutes: int,
    ) -> dict:
        """Build one route record.
        
        Args:
            destination: The place this route serves.
            station: The station nearest that place.
            line: The metro or RER line to take.
            duration_minutes: Travel time from ORIGIN_STATION.
        
        Returns:
            A dict for one one-way trip. `price` is a single fare;
            a return trip is two of them.
        """
        return {
            "destination": destination,
            "from_station": ORIGIN_STATION,
            "to_station": station,
            "line": line,
            "currency": "USD",
            "price": FARE_USD,
            "group_size": 1,
            "duration_minutes": duration_minutes,
        }
    
    routes = [
        route(
            destination="Eiffel Tower Summit Visit",
            station="Bir-Hakeim",
            line="6",
            duration_minutes=0,
        ),
        route(
            destination="Dinner at Eiffel Tower",
            station="Bir-Hakeim",
            line="6",
            duration_minutes=0,
        ),
        route(
            destination="Louvre Guided Visit",
            station="Palais Royal - Musee du Louvre",
            line="1",
            duration_minutes=25,
        ),
        route(
            destination="Catacombs Tour",
            station="Denfert-Rochereau",
            line="6",
            duration_minutes=18,
        ),
        route(
            destination="Picnic in the Luxembourg Gardens",
            station="Odeon",
            line="4",
            duration_minutes=22,
        ),
        route(
            destination="Montmartre Walking Tour",
            station="Anvers",
            line="2",
            duration_minutes=35,
        ),
        route(
            destination="Seine River Dinner Cruise",
            station="Alma - Marceau",
            line="9",
            duration_minutes=12,
        ),
        route(
            destination="Couples Hammam and Spa",
            station="Grands Boulevards",
            line="8",
            duration_minutes=28,
        ),
        route(
            destination="Airport",
            station="Charles de Gaulle T2",
            line="RER B",
            duration_minutes=55,
        ),
    ]
    
    for candidate in routes:
        if candidate["destination"] == destination:
            return  {
                "location": location,
                "origin": origin,
                "destination": destination,
                "count": 1,
                "routes": [candidate],
            }
            
    return {
        "location": location,
        "origin": origin,
        "destination": destination,
        "count": 0,
        "note": (
            f"No route to {destination!r} in this fixture. "
            f"Covered: {[r['destination'] for r in routes]}"
        ),
        "routes": [],
    }
    