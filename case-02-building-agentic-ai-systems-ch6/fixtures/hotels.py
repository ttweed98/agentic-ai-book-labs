"""Corrected hotel search fixture for Chapter 6.

Returns hotel options for a location and a pair of stay dates.

Replaces the book's `find_hotels` stub, which echoed its check-in and
check-out dates back without validating them, gave a bare `price` that
was ambiguous between per-night and per-stay, declared no currency,
never computed the number of nights or a stay total, and described
location in prose that nothing could compare.

Closes:
    DES-6   parameters echoed but never validated
    DES-9   prices with no declared currency
    DES-10  no totals computed anywhere
    DES-8b  trip length disagreed between workers, unchecked
"""

import datetime


def find_hotels(
    location: str,
    check_in: str,
    check_out: str,
) -> dict:
    """Search hotels in a location for a pair of stay dates.
    
    Args:
        location: City name, e.g. "Paris".
        check_in: Arrival date, ISO 8601, e.g. "2025-05-07".
        check_out: Departure date, ISO 8601, e.g. "2025-05-14".
    
    Returns:
        A dict with "nights" and a list of "hotels". Each hotel carries
        a nightly rate, a stay total, and a declared currency. `nights`
        is derived from the two dates, never passed in.
    """
    if location != "Paris":
        return {
            "hotels": [],
            "note": (
                f"No hotels for {location}. "
                "This fixture covers Paris only."
            ),
        }
    
    arrive = datetime.date.fromisoformat(check_in)
    depart = datetime.date.fromisoformat(check_out)
    today = datetime.date.today()

    if arrive < today:
        return {
            "hotels": [],
            "count": 0,
            "note": f"Check-in {check_in} is in the past. Today is {today}.",
        }
        
    nights = (depart - arrive).days
    
    if nights < 1:
        return {
            "hotels": [],
            "note": (
                f"Check-out {check_out} is not after check-in "
                f"{check_in}."
            ),
        }
        
    def hotel(
        *,
        name: str,
        nightly_rate: int,
        rating: float,
        location: str,
        near: str,
        distance_km: float,
        amenities: list[str],
    ) -> dict:
        """Build one hotel record with a computed stay total.
        
        Args:
            name: Hotel name.
            nightly_rate: Room rate per night, in `currency`.
            rating: Guest rating out of 5.
            location: Neighbourhood, as the book gave it.
            near: The landmark `distance_km` is measured from.
            distance_km: Distance from `near`, in kilometres.
            amenities: Amenities present at the property.
        
        Returns:
            A dict for one hotel. `stay_total` is derived from
            `nightly_rate` and `nights`, never typed by hand.
        """
        return {
            "name": name,
            "currency": "USD",
            "nightly_rate": nightly_rate,
            "stay_total": nightly_rate * nights,
            "rating": rating,
            "location": location,
            "near": near,
            "distance_km": distance_km,
            "amenities": amenities,
        }

    hotels = [
        hotel(
            name="Paris Marriott Champs Elysees",
            nightly_rate=450,
            rating=4.5,
            location="Central Paris",
            near="Eiffel Tower",
            distance_km=2.1,
            amenities=["Spa", "Restaurant", "Room Service", "Wifi"],
        ),
        hotel(
            name="Citadines Saint-Germain-des-Prés",
            nightly_rate=320,
            rating=4.2,
            location="Saint-Germain",
            near="Eiffel Tower",
            distance_km=3.4,
            amenities=["Kitchenette", "Laundry", "Wifi"],
        ),
        hotel(
            name="Ibis Paris Eiffel Tower",
            nightly_rate=380,
            rating=4.0,
            location="Near Eiffel Tower",
            near="Eiffel Tower",
            distance_km=0.6,
            amenities=["Restaurant", "Bar", "Wifi"],
        ),
    ]

    return {
        "nights": nights,
        "check_in": check_in,
        "check_out": check_out,
        "count": len(hotels),
        "hotels": hotels,
    }