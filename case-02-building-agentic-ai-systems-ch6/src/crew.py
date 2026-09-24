"""The Chapter 6 coordinator/worker/delegator travel crew, corrected.

Follows the book's design: a coordinator writes a plan, and a delegator
(the manager) hands the work to four specialist workers. Changes from
the book are limited to closing numbered findings in findings/.
"""

import asyncio
from textwrap import dedent

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

from src.tools import (
    find_activities,
    find_hotels,
    find_transportation,
    search_flights,
)

load_dotenv()  # reads OPENAI_API_KEY from .env, which is never committed

LLM = "gpt-4o"  # the baseline's model, so the two runs are comparable

flight_booking_worker = Agent(
    role="Flight Booking Specialist",
    goal="Find and book the optimal flights for the traveler",
    backstory="""You are an experienced flight booking specialist with extensive knowledge of airlines,
    routes, and pricing strategies. You excel at finding the best flight options balancing cost,
    convenience, and comfort according to the traveler's preferences.""",
    verbose=True,
    allow_delegation=False,
    tools=[search_flights],
    llm=LLM,
    max_iter=1,
    max_retry_limit=3,
)

hotel_booking_worker = Agent(
    role="Hotel Accommodation Expert",
    goal="Secure the ideal hotel accommodations for the traveler",
    backstory="""You have worked in the hospitality industry for over a decade and have a deep knowledge
    of hotel chains, boutique accommodations, and local lodging options worldwide. You're skilled at
    matching travelers with accommodations that meet their budget, location preferences, and amenity requirements.""",
    verbose=True,
    allow_delegation=False,
    tools=[find_hotels],
    llm=LLM,
    max_iter=1,
    max_retry_limit=3,
)

activity_planning_worker = Agent(
    role="Activities and Excursions Planner",
    goal="Curate personalized activities and experiences for the traveler",
    backstory="""You are a well-traveled activities coordinator with insider knowledge of attractions,
    tours, and unique experiences across numerous destinations. You're passionate about creating
    memorable itineraries that align with traveler' interests, whether they seek adventure, culture,
    relaxation, or culinary experiences.""",
    verbose=True,
    allow_delegation=False,
    tools=[find_activities],
    llm=LLM,
    max_tier=1,
    max_retry_limit=3,
)

transportation_worker = Agent(
    role="Local Transportation Coordinator",
    goal="Arrange efficient and convenient local transportation",
    backstory="""You specialize in local transportation logistics across global destinations. Your expertise
    covers public transit systems, priavte transfers, rental services, and navigation, ensuring travelers
    can move smoothly between destinations and activities.""",
    verbose=True,
    allow_delegation=False,
    tools=[find_transportation],
    llm=LLM,
    max_iter=1,
    max_retry_limit=3,
)

flight_search_task = Task(
    description="""
    Use the search_flights tool to find flight options from origin to destination.
    Review the returned JSON data and recommend the best option based on the traveler's priorities, if any.
    
    Compare the available options and recommended choice best meets their needs.
    """,
    agent=flight_booking_worker,
    expected_output="A flight itinerary for booking based on the traveler's preferences.",  
)

hotel_search_task = Task(
    description="""
    Use the find_hotels tool to search for accommodations in the destination.
    Review the returned JSON data and recommend the best option considering budget.
    
    Explain why your recommended choice is the best match for this traveler.
    """,
    agent=hotel_booking_worker,
    expected_output="A hotel recommendation based on the traveler's preferences and budget."    
)

activity_planning_task = Task(
    description="""
    Use the find_activities tool to identify options in the destination for each day of the entire trip duration.
    The traveler's interests are: {activity_interests} with a {activity_pace} pace preference.
    
    Create a day-by-day plan using the returned JSON data, ensuring activities flow logically and match the traveler's interests.
    """,
    agent=activity_planning_worker,
    expected_output="A day-by-day activity plan that matches the traveler's interests and pace preferences.",
)

transportation_plannning_task = Task(
    description="""
    Use the find_transportation tool to identify options at the destination for:
    1. Airport to hotel transfer
    2. Transportation between daily activities
    3. Hotel to airport transfer
    
    Consider the traveler's preferences where  possible.
    
    ased on the returned JSON data, recommend the best transportation options for each segment of their trip.
    """,
    agent=transportation_worker,
    expected_output="A transportation plan covering all necessary transfers during the trip.", 
)