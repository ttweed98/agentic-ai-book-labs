"""CrewAI tool wrappers for the Case 02 fixtures.

The fixtures in fixtures/ are plain Python and know nothing about CrewAI.
This file is the only place they become tools the model can call, so the
docstrings here are what the model reads to decide when and how to call them.
"""

from crewai.tools import tool

from fixtures import activities, flights, hotels, transportation


@tool("search_flights")
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
        depart_date: Outbound date as YYYY-MM-DD. Must not be in the past.
        return_date: Return date as YYYY-MM-DD, after depart_date.
    
    Returns:
        A dict with "offers" and "count". Each offer has a carrier, flight
        numbers, a per-person price in USD, and legs with ISO departure and
        arrival times and a number of stops. When nothing matches, "offers"
        is empty, "count" is 0, and "note" explains why.
    """
    return flights.search_flights(
        origin=origin,
        destination=destination,
        depart_date=depart_date,
        return_date=return_date,
    )


@tool("find_hotels")
def find_hotels(
    location: str,
    check_in: str,
    check_out: str,
) -> dict:
    """Search hotels in a city for a pair of stay dates.
    
    Args:
        location: City name, e.g. "Paris".
        check_in: Check-in date as YYYY-MM-DD. Must not be in the past.
        check_out: Check-out date as YYYY-MM-DD, after check_in.
        
    Returns:
        On success, a dict with "hotels", "count", "nights", "check_in" and
        "check_out". Each hotel has a name, a nightly rate and a total for
        the whole stay in USD, a rating, amenities, and its distance in km
        from the Eiffel Tower. When nothing matches, "hotels' is empty,
        "count" is 0, and "note" explains why.
    """
    return hotels.find_hotels(
        location=location,
        check_in=check_in,
        check_out=check_out,
    )


@tool("find_activities")
def find_activities(
    location: str,
    date: str,
    preferences: str,
) -> dict:
    """List every activity in a city, each tagged by pace.
    
    Args:
        location: City name, e.g. "Paris".
        date: Day of the activity as YYYY-MM-DD. Must not be in the past.
        preferences: The traveller's stated preferences. Echoed back
            unchanged; the list is NOT filtered by them.
    
    Returns:
        On success, a dict with "activities" and "count". The same full
        catalogue comes back for any valid date. Each activity has a name,
        a pace of "relaxed" or "active", a price in USD, and a group_size:
        the price covers group_size people, so a party of 2 needs
        2 / group_size bookings. There is no "moderate" tag: a moderate
        day mixes both. When nothing matches, "activities" is empty,
        "count" is 0, and "note" explains why.
    """
    return activities.find_activities(
        location=location,
        date=date,
        preferences=preferences,
    )


@tool("find_transportation")
def find_transportation(
    location: str,
    origin: str,
    destination: str,
) -> dict:
    """Find the metro or train route to one destination in a city.
    
    Args:
        location: City name, e.g. "Paris".
        origin: Where the trip starts. Echoed back but NOT used: every
            route starts at Bir-Hakeim station, by the Eiffel Tower.
        destination: The exact name of an activity, or "Airport".
    
    Returns:
        A dict with "routes" and "count". A route has a line, the stations
        it runs between, a duration in minutes, and a price in USD that
        covers group_size people for ONE ride; a round trip is two rides.
        If the destination is not an exact match, "routes" is empty,
        "count" is 0, and "note" lists every destination that is covered.
        Retry with one of those names.
    """
    return transportation.find_transportation(
        location=location,
        origin=origin,
        destination=destination,
    )
