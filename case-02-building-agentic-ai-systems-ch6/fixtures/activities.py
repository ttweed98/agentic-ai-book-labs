"""Corrected activity search fixture for Chapter 6.
Returns the whole activity catalogue for a location, with a count.

Replaces the book's `find_activities` stub, which accepted a location,
a date and preferences, used none of them, and returned the same three
activities on every call -- so seven calls produced seven identical
answers and nothing noticed the repetition.

Prices are illustrative, not live.

Closes:
    DES-6   parameters accepted but never used
    DES-7   identical results, invented differentiation
    DES-9   prices with no declared currency
"""


import datetime


def find_activities(
    location: str,
    date: str,
    preferences: str,
) -> dict:
    """List every activity in a location, tagged by pace.
    
    Args:
        location: City name, e.g. "Paris".
        date: Day of the activity, ISO 8601, e.g. "2026-11-02".
            Must not be in the past.
        preferences: The traveller's pace, as given in the request,
            e.g. "moderate". Echoed back, not used to filter.
    
    Returns:
        A dict with the full catalogue under "activities" and its size
        under "count". Each activity carries a `pace` tag, either
        "relaxed" or "active". Nothing is filtered: choosing is the
        agent's job, and the count shows how much it has to choose from.
    """
    if location != "Paris":
        return {
            "activities": [],
            "count": 0,
            "note": (
                f"No activities for {location}. "
                "This fixture covers Paris only."
            ),
        }
    
    day = datetime.date.fromisoformat(date)
    today = datetime.date.today()
    
    if day < today:
        return {
            "activities": [],
            "count": 0,
            "note": f"Date {date} is in the past. Today is {today}.",
        }
    
    def activity(
        *,
        name: str,
        pace: str,
        price: int,
        group_size: str,
        duration_minutes: int,
    ) -> dict:
        """Build one activity record.
        
        Args:
                name: Activity name.
                pace: "relaxed" or "active".
                price: Price in `currency`. 0 means free, not unknown.
                group_size: How many people `price` covers. 1 = per person.
                duration_minutes: How long the activity takes.
        
        Returns:
            A dict for one activity.
        
        Raises:
            ValueError: If `pace` is not "relaxed" or "active".
        """
        if pace not in ("relaxed", "active"):
            raise ValueError(f"Unknown pace {pace!r} for {name}.")
        
        
        return {
            "name": name,
            "currency": "USD",
            "pace": pace,
            "price": price,
            "group_size": group_size,
            "duration_minutes": duration_minutes,
        }
        
    activities = [
        # relaxed
        activity(
            name="Seine River Dinner Cruise",
            pace="relaxed",
            price=90,
            group_size=1,
            duration_minutes=75,
        ),
        activity(
            name="Dinner at Eiffel Tower",
            pace="relaxed",
            price=90,
            group_size=1,
            duration_minutes=105,
        ),
        activity(
            name="Couples Hammam and Spa",
            pace="relaxed",
            price=140,
            group_size=2,
            duration_minutes=90,
        ),
        activity(
            name="Picnic in the Luxembourg Gardens",
            pace="relaxed",
            price=0,
            group_size=1,
            duration_minutes=120,
        ),
        # active
        activity(
            name="Eiffel Tower Summit Visit",
            pace="active",
            price=65,
            group_size=1,
            duration_minutes=120,
        ),
        activity(
            name="Louvre Guided Visit",
            pace="active",
            price=85,
            group_size=1,
            duration_minutes=180,
        ),
        activity(
            name="Catacombs Tour",
            pace="active",
            price=35,
            group_size=1,
            duration_minutes=90,
        ),
        activity(
            name="Montmartre Walking Tour",
            pace="active",
            price=30,
            group_size=1,
            duration_minutes=150,
        ),
    ]
    return {
        "location": location,
        "date": date,
        "preferences": preferences,
        "count": len(activities),
        "activities": activities,
    }