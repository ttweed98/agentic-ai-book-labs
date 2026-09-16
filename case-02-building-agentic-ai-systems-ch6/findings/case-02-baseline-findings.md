# CASE 02 — BASELINE RUN FINDINGS
**Subject:** `Building-Agentic-AI-Systems/Chapter06/Chapter_06.ipynb` (Biswas & Talukdar, Packt, April 2025)
**Run date:** 2026-09-14
**Environment:** Eve-Ng NUC · Python 3.10 · crewai 1.15.17 · `llm = "gpt-4o"` · OpenAI API
**Purpose:** establish the before-state. What the book's coordinator/worker/delegator architecture does when given a real request, recorded before any correction is written.

---

## 0. HOW TO READ THIS

Findings are sorted into two classes and the distinction is load-bearing:

- **ENV** — the notebook has aged. Stale dependency, moved API, retired model. Fix silently; these say nothing about the architecture.
- **DES** — the design produces a wrong or unsupported result. These survive every dependency fix. **These are the finding.**

A third column is noted where relevant: whether the failure is **loud** (raises, stops) or **quiet** (produces confident, readable, wrong output). Quiet failures are the dangerous class and this run is full of them.

The run completed end to end. Nothing raised. **Every design defect below is in output that reads as a finished, professional travel plan.**

---

## 1. THE REQUEST (unchanged, as published in cell 16)

```
Traveler Alex Johnson, Paris from New York, anniversary, 7 days, 2 people.
- Total budget ~$8000, with hotel budget being $300.
- Direct flights preferred, morning departure if possible.
- Hotel in Paris under $400 with wifi preferred. Check in 5/7/2025, checkout 5/14/2025.
- Activities moderate pace with some relaxation time built in.
- Mix of walking and public transit, occasional taxis for evening outings.
```

---

## 2. ENVIRONMENT FINDINGS

| id | finding |
| --- | --- |
| ENV-1 | `requirements.txt` contains one line: `Faker`. It does not install crewai, langchain-openai, or anything else the notebook needs. Real dependencies are inline `!pip install` in cell 1. |
| ENV-2 | `SETUP.md` instructs the reader to navigate to a `notebooks` directory. No such directory exists; chapters live in `Chapter02/`…`Chapter08/`. |
| ENV-3 | `SETUP.md`'s Colab badge points at `Chapter_02.ipynb` at repo root. The file is at `Chapter02/Chapter_02.ipynb`. |
| ENV-4 | Book written against crewai 0.x; installed version is 1.15.17 — a major version ahead. Semantics differ (see DES-1 note). |
| ENV-5 | `llm = "gpt-4o"` is hardcoded. April 2025 model pin. |
| ENV-6 | Request dates are 5/7/2025–5/14/2025 — in the past as of this run. |
| ENV-7 | Coordinator output renders as `$8000.Thehotelbudgetisabout$300` — paired `$` triggers Markdown LaTeX math mode and swallows the spaces. The budget statement is unreadable at exactly the point where budget is stated. |

---

## 3. DESIGN FINDINGS

### DES-1 — Template variables never substituted ★★★ QUIET

`activity_planning_task.description` (cell 11) contains `{activity_interests}` and `{activity_pace}`. CrewAI interpolates these from `inputs` at kickoff. Cell 20 calls:

```python
full_itinerary = await delegator_crew.kickoff_async()   # no inputs
```

**Observed:** the literal string reached the model —

```
The traveler's interests are: {activity_interests} with a {activity_pace} pace preference.
```

**It did not crash.** The model inferred plausible values and wrote a full seven-day itinerary "suited for a moderate pace, matching their interests." The output asserts a match to interests the system was never given.

⇒ **The worst failure class in the run: a missing input that produces confident output instead of an error.**

*Note: the four task descriptions seen executing are NOT the ones in cell 11. `planning=True` had CrewAI's planner rewrite them with numbered steps 1–9/1–10. The planner independently added "confirm the destination city and any available stay dates before using the tool" — the framework partially patching the book's own gap.*

### DES-2 — Flight records carry no date ★★★ QUIET

`search_flights` accepts a `date` parameter and never uses it. Returned flights have `departure_time` and `arrival_time` but **no date field**. Two of three options arrive the next day, with nothing in the data saying so.

Hotels echo `check_in`/`check_out` into every record; flights discard theirs. **Cross-component date reconciliation is impossible in principle, not by omission.**

Also: `search_flights`'s docstring documents `origin` and `destination` but omits `date` — the ignored parameter is also the undocumented one, which is how it survived review.

### DES-3 — Every flight arrival time is wrong by one hour ★★ QUIET

```
Air France   10:30 AM JFK + 7h30m  →  12:00 AM CDG    data says 11:00 PM
Delta         5:30 PM JFK + 7h45m  →   7:15 AM CDG    data says  6:15 AM
United        8:45 PM EWR + 7h55m  →  10:40 AM CDG    data says  9:40 AM
```

NYC→Paris in May is a six-hour offset; all three were computed at five. Consistent, so one mistake applied three times. **No agent checks that departure + duration = arrival**, so it passes through untouched and the wrong arrival time is then used downstream to justify decisions (see DES-8).

### DES-4 — Stated preference silently unevaluable ★★★ QUIET

The request says **direct flights preferred**. The planner's own rewritten step 3 instructs the agent to extract "stops." **There is no stops field in the fixture.**

Air France was recommended on morning departure alone. **Nothing anywhere reports that "direct" could not be assessed.** A constraint the traveler stated was dropped without a decline, a flag, or a mention.

### DES-5 — Contradictory budget carried forward unreconciled ★★ QUIET

The request contains both "hotel budget being $300" and "hotel under $400." The coordinator reproduced **both** — $300/night in the overview, $400/night in the preference details — without noticing they conflict.

The hotel worker used $400, selected Citadines at $320, and justified it as "well within the budget limit of $400 per night." **Against the $300 figure it is over.** The stricter constraint disappeared with nobody declining it.

### DES-6 — Tools ignore their own parameters ★★ QUIET

| tool | accepts | uses |
| --- | --- | --- |
| `search_flights` | origin, destination, date | none — returns a fixed list |
| `find_hotels` | location, check_in, check_out | check_in, check_out (echoed only) |
| `find_activities` | location, date, preferences | none |
| `find_transportation` | location, origin, destination | none |

`find_activities` ships with the comment `# Implement actual activity search logic here` — a TODO published in the book.

### DES-7 — Identical tool results, invented differentiation ★★★ QUIET

**Transportation:** called three times (airport→hotel, between activities, hotel→airport). **All three returned byte-identical JSON**, because the tool ignores `origin` and `destination`. The agent then wrote three *different* recommendations with distinct reasoning.

**Activities:** called **seven times**, once per trip day. **All seven returned the same three items** — Eiffel Tower, Louvre, Seine Cruise.

The resulting itinerary contains Tuileries, Luxembourg Gardens, Musée d'Orsay, Montmartre, a spa, and a leisurely breakfast. **Only Days 1 and 2 use returned data. Six of seven days are fabricated from model training data** — while the planner's step 10 explicitly instructed "using only the returned data to support each recommendation."

⇒ **The instruction to ground in data was present and had no effect.** Nothing verifies that output traces to tool results.

*One honesty signal exists and nothing consumes it: three invented activities are costed "To be checked on-site" or "To be arranged directly." The model marked its own fabrications as unpriced.*

### DES-8 — ★★★THE CENTRAL FINDING: no reconciliation across workers

Two arithmetic contradictions in one run. Both are the thesis.

**(a) Activity scheduled before arrival.**
Recommended flight lands **11:00 PM, May 7**. Day 1 of the itinerary is the **Seine River Dinner Cruise, 7:30 PM, May 7** — three and a half hours before the plane touches down.

The arrival time was not unavailable. **The transportation worker used the 11 PM arrival on the same run** to justify a taxi ("the arrival time around 11:00 PM should generally see lighter traffic"). Two workers had the same fact; one reasoned from it, one contradicted it, and nothing compared them.

**(b) Trip length disputed between workers.**
Hotel worker booked **May 7 → May 14**, printed "Total Stay Price: $2,240" for seven nights. Activity worker planned **May 7 → May 13**, seven days. The itinerary ends one day before the trip does.

⇒ `Process.hierarchical` **does** pass prior outputs forward as context — information flow is not the problem. **Nothing checks the outputs against each other.** Context is available and unverified.

### DES-9 — Undeclared mixed currency ★★ QUIET

Flights 850/780/920 and hotels 450/320/380 read as USD. Transportation 1.90 / 22.50 / 7.50 / 12.00 with a "Paris Visite" pass are Euro. **No currency field anywhere.** Any total across these is meaningless, and the agents render all of them with `$`.

### DES-10 — Nothing is ever totalled ★★★ QUIET

The request states a total budget of $8000 for 2 people. **No component sums anything. No stage compares any total to the budget.**

Hotel alone: $2,240. Flights at 2 × $850: $1,700. Activities per person: $120 + $65 + $85 + $12, doubled. Three days carry no price at all because they were invented. **The plan cannot be checked against the one hard constraint the traveler gave.**

### DES-11 — Workers structurally isolated ★ STRUCTURAL

All four workers set `allow_delegation=False` under `Process.hierarchical`. No worker can query another. Combined with DES-8, the only path between workers is context the manager passes forward, which nothing validates.

---

## 4. SCORING OF PRE-RUN PREDICTIONS

Recorded before execution, scored after. Two were wrong and the corrections matter.

| prediction | verdict |
| --- | --- |
| Cell 22 crashes on unsubstituted template vars | **PARTIAL** — vars did not substitute (confirmed) but produced degraded output, not a crash. Worse outcome than predicted. |
| Flight data has no date → reconciliation impossible | **CONFIRMED** (DES-2) |
| Direct-flight preference cannot be evaluated | **CONFIRMED** (DES-4) |
| Unused parameters in tools | **CONFIRMED** (DES-6) |
| Mixed undeclared currency | **CONFIRMED** (DES-9) |
| `max_iter=1` starves the tool loop | **FALSIFIED** — tools were called and results returned. crewai 1.x iterates differently from 0.x. |
| "The plan never arrives at the workers" | **FALSIFIED** — hierarchical process passes prior outputs as context. The transportation worker named the hotel and used the flight arrival time. **The defect is not missing context; it is unverified context.** |

★**The second falsification sharpened the thesis.** "No reconciliation step" is more precise than "no information flow," and the run demonstrates it with numbers rather than asserting it.

---

## 5. WHAT THE CORRECTED BUILD MUST FIX

Derived from the findings above, and deliberately small. Ordered by what each one buys.

1. **Pass inputs at kickoff.** Closes DES-1.
2. **Add `date` and `stops` to flight records; fix the arrival arithmetic.** Closes DES-2, DES-3, DES-4.
3. **Declare currency on every price.** Closes DES-9.
4. **Make tools honour their parameters,** or return an explicit "not supported" rather than a fixed list. Closes DES-6, DES-7.
5. **One reconciliation pass over worker outputs** — arrival vs. first activity, trip length vs. hotel nights, sum vs. budget. Closes DES-8, DES-10.
6. **Ground the output:** anything not traceable to a tool result is marked or dropped. Closes the fabrication half of DES-7.

⚠**Everything on this list is a defect closure. Nothing on it is a new feature.** The scope discipline that governs the rebuild: *if it does not close a numbered finding above, it does not go in.*

---

## 6. WHAT THIS REPLACES

The earlier spec-driven approach (FLT-01…PLN-10, six ranking tables, forty-nine rules against the real AutoCon trip) produced a genuine finding — a specification breaking repeatedly under its own arithmetic, with the budget forced from $4,000 to $5,800. **That finding stands and needs no code to support it.**

It is superseded as an *implementation* target because it was building a production-scale rule engine when the lab's purpose is a student-legible correction of a published chapter. Other learners have this book; a diff against Chapter 6 is legible to them in a way that forty-nine bespoke rules is not.

`spec/` and `origin/conference_travel.md` are retained as the record of that experiment.