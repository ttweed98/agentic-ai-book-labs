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

from src.models import ActivityPlan, FlightChoice, HotelChoice, Itinerary, TransportPlan

load_dotenv()  # reads OPENAI_API_KEY from .env, which is never committed

LLM = "gpt-4o"  # the baseline's model, so the two runs are comparable

#  The  book's request, word for word, except the dates: the book's were in
#  2025, and the fixtures refuse past dates. The $300/$400 hotel budget
#  contradiction is kept on purpose; it is the evidence for DES-5/
REQUEST = """Traveler Alex Johnson is planning to travel to Paris from New York for his anniversary for 7 days and 2 people.
- His total budget is about $8000, with hotel budget being $300.
- Direct flights preferred, morning departure if possible.
- Hotel in Paris under $400 with wifi preferred. Check in at 11/2/2026 and checkout at 11/9/2026
- Activities in paris should be moderate pace with some relaxation time built in
- Mix of walking and public transit, with occasional taxis for evening outings
"""

# DES-1: values for the activity tasks's {activity_interests} and
# {activity_pace}, taken from the request's own wording rather than
# extracted by an agent, so no retelling sits between request and task.
ACTIVITY_INTERESTS = "an anniversary trip with some relaxation time built in"
ACTIVITY_PACE = "moderate"

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
    output_pydantic=FlightChoice,
)

hotel_search_task = Task(
    description="""
    Use the find_hotels tool to search for accommodations in the destination.
    Review the returned JSON data and recommend the best option considering budget.
    
    Explain why your recommended choice is the best match for this traveler.
    """,
    agent=hotel_booking_worker,
    expected_output="A hotel recommendation based on the traveler's preferences and budget.",
    output_pydantic=HotelChoice,
)

activity_planning_task = Task(
    description="""
    Use the find_activities tool to identify options in the destination for each day of the entire trip duration.
    The traveler's interests are: {activity_interests} with a {activity_pace} pace preference.
    
    Create a day-by-day plan using the returned JSON data, ensuring activities flow logically and match the traveler's interests.
    """,
    agent=activity_planning_worker,
    expected_output="A day-by-day activity plan that matches the traveler's interests and pace preferences.",
    output_pydantic=ActivityPlan,
)

transportation_planning_task = Task(
    description="""
    Use the find_transportation tool to identify options at the destination for:
    1. Airport to hotel transfer
    2. Transportation between daily activities
    3. Hotel to airport transfer
    
    Consider the traveler's preferences where  possible.
    
    Based on the returned JSON data, recommend the best transportation options for each segment of their trip.
    """,
    agent=transportation_worker,
    expected_output="A transportation plan covering all necessary transfers during the trip.",
    output_pydantic=TransportPlan,
)

coordinator_agent = Agent(
    role="Coordinator Agent",
    goal="Ensure cohesive travel plans and maintain high customer satisfaction",
    backstory="""A seasoned travel industry veteran with 15 years of experience in luxury travel planning
    and project management. Known for orchestrating seamless multi-destination trips for high-profile cleitns
    and managing complex itineraries across different time zones and cultures.
    """,
    verbose=False,
    llm=LLM,
    max_iter=1,
    max_retry_limit=3,
)

async def coordinate_request(traveler_request):
    coordinator_to_delegator_task= Task(
        description=dedent(f"""\
            As the Coordinator Agent, you've received a travel planning request/
            
            Traveler request:
            {traveler_request}
            
            Create a clear, concise travel planning steps for this trip. Only plan
            for the things requested by the traveler, DO NOT assume or add things not requested. Provide a
            short overview, followed by the steps required for flight booking, hotel booking, activities,
            and local transportation.
            
            Your output should be a step-by-step plan along with preference details that the Delegator Agent
            can use to effectively assign tasks to the specialist workers. Do not provide any summary or mention
            "Delegator" or "coordinator".
            """),
            expected_output="A detailed step-by-step travel plan for the delegator agent",
            agent=coordinator_agent,
    )
    
    # Execute the coodinator's initial planning task
    coordinator_crew = Crew(
        agents=[coordinator_agent],
        tasks=[coordinator_to_delegator_task],
        verbose=False, #True if you want to see detailed execution
        process=Process.sequential,
    )
    coordinator_plan = await coordinator_crew.kickoff_async(inputs={"traveler_request": traveler_request})
    print("\n=== Coordinator Planning Complete ===\n")
    return coordinator_plan

async def delegate_plan(plan, activity_interests, activity_pace):
    delegator_goal = f"""
        Effectively distribute travel planning tasks to specialized workers to create a detailed booking itinerary
        for the plan below:

        {plan}

        Based on this plan, your goal is to create a detailed booking itinerary and trip plan for the user that includes
        flight booking & cost recommendation, hotels and hotel cost, activities and local transportation options
        and recommendations.
        """

    delegator_agent = Agent(
        role="Travel Planning Delegator",
        goal=delegator_goal,
        backstory="""You are an expert project manager with a talent for breaking down travel planning into
        component tasks and assigning them to the right specialists. You understand each worker's strengths
        and ensure they have the information needed to excel. You track progress, resolve bottlenecks, and
        ensure all elements of the trip are properly addressed.""",
        verbose=True,
        allow_delegation=True,
        llm=LLM,
    )

    # Execute the delegator's task assignment
    delegator_crew = Crew(
        agents=[flight_booking_worker, hotel_booking_worker, transportation_worker, activity_planning_worker],
        tasks=[flight_search_task, hotel_search_task, transportation_planning_task, activity_planning_task],
        verbose=False,
        manager_agent=delegator_agent,
        process=Process.hierarchical,
        planning=True,
        full_output=True,
    )

    # DES-1: the book called kickoff_async() with no inputs, so the activity
    # task's {activity_interests} and {activity_pace} reached the model as
    # literal text.
    full_itinerary = await delegator_crew.kickoff_async(
        inputs={
            "activity_interests": activity_interests,
            "activity_pace": activity_pace,
        }
    )
    print("\n=== Delegator Task Complete ===\n")
    return full_itinerary

async def main():
    plan = await coordinate_request(REQUEST)
    result = await delegate_plan(plan, ACTIVITY_INTERESTS, ACTIVITY_PACE)

    outputs = result.tasks_output
    itinerary = Itinerary(
        flight=outputs[0].pydantic,
        hotel=outputs[1].pydantic,
        transport=outputs[2].pydantic,
        activities=outputs[3].pydantic,
    )

    with open("findings/itinerary.json", "w") as f:
        f.write(itinerary.model_dump_json(indent=2))
    print(itinerary.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())