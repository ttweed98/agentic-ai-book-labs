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

### DES-12 — Every tool has two names

Each tool is registered under a sentence, e.g.
`@tool("Search for available flights between cities")`, while the task
text tells the agent to "Use the search_flights tool". In the baseline
run the planner bridged the two, restating the task with the long name,
but nothing guarantees it will. The authors' note on the delegator cell
reports failed tool invocations and blames smaller models; the name
mismatch is a candidate contributor, not a proven cause.

Found 2026-09-24 while reading the baseline tool definitions, not during
the baseline run itself.

**Fix:** register each tool under the name the task text uses, e.g.
`@tool("search_flights")`. Closed in `src/tools.py`. Whether
tool-call failures drop is to be observed in the corrected run.
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

## Middle run — corrected fixtures + DES-1 only

### Input change
The book's request is used word for word except the dates: 5/7/2025 and
5/14/2025 became 11/2/2026 and 11/9/2026, because the fixtures refuse past
dates. The $300 / $400 hotel-budget contradiction is kept on purpose (DES-5).

### Predictions (written before running)
- P-M1 Dates: every tool call uses a 2026 date.
- P-M2 Budget: the plan uses the $400 hotel budget, not $300. The request
  gives both values.
- Open question (not a prediction): how the agent handles "moderate" when
  the fixture tags activities only `relaxed` or `active`.

### Results (scored after running, 2026-09-25)

Run: crewai 1.15.17, gpt-4o. Log: `findings/middle-run-2026-09-25.log`.
One run only: evidence, not a pattern.

**Predictions**
- P-M1 Dates: CONFIRMED. Every tool call used a 2026 date.
- P-M2 Budget: CONFIRMED. The hotel step used "$400 per night"; $300 never
  appears, and the chosen hotel ($320) is over the traveler's $300 line.
- Moderate (open question): ANSWERED. The planner restated the docstring
  ("mix relaxed and active") and the plan mixed both tags.

**Closed, with evidence in the log**
- DES-1: the activity task shows the interests and pace, not braces.
- DES-3: arrival 7:15 AM on 3 Nov (next day), computed by the fixture.
- DES-4: "Direct" read from the `stops` field.

**Observed**
- M-1 Workers never ran: every block is "Travel Planning Delegator".
- M-2 Tool docstrings reappear as the planner's numbered steps.
- M-3 Transport missed on 4 invented names, then retried with exact names
  from the `note` and recovered 3.
- M-4 Transport routes start at Bir-Hakeim and are labelled "From Hotel";
  the chosen hotel is in Saint-Germain, 3.4 km away. Unreconciled.
- M-5 The hotel night of 2 Nov is paid but unused: the flight lands on
  3 Nov. Unreconciled (DES-8b).
- M-6 The morning-departure preference was traded for price, stated openly.
- M-7 The final output is only the last task (activities): no assembled
  itinerary and no total (DES-10 open).
- M-8 All 8 catalogue items were used once, and every price and duration
  matches the fixture. After day 4 the plan gives unpriced generic
  suggestions instead of inventing priced items.

**Environment**
- E-M1 CrewAI prompted interactively for tracing mid-run (20 s timeout),
  then saved "tracing disabled".
- E-M2 A typo in a task name inside `delegate_plan` passed every import
  check and failed only at run time, after the coordinator had already run.

### Smoke test: FlightChoice on the flight task (2026-09-25)

Log: `findings/smoke-test-2026-09-25.log`.

**Predictions (made before running)**
- P-S1 Delta chosen again: FALSIFIED. Air France ($850, 10:30 AM
  departure) won; the morning preference beat price, the reverse of the
  middle run. Two runs, two choices; the cause is not established.
- P-S2 FlightChoice ignored under the hierarchical process: FALSIFIED.
  `tasks_output[0].pydantic` returned a populated FlightChoice. Both
  times parsed as timezone-aware datetimes and match the fixture.

**Observed**
- S-1 Air France lands at 00:00 on 3 Nov, so the 2 Nov hotel night is
  used (arrival around 01:30). R2 must test "arrives before the next
  morning", not "dates are equal".
- S-2 The activity plan says "Morning: Arrival and check-in" on 3 Nov.
  The plane lands at midnight and check-in is 2 Nov. The prose
  contradicts the structured flight data; R1 would still pass, because
  it checks activity start times, not narrative lines.

### Structured run (2026-09-25)

Log: `findings/structured-run-2026-09-25.log`. Output: `findings/itinerary.json`.

- P-R1 ActivityPlan is the weakest: first run, RIGHT TASK, WRONG CAUSE.
  All four outputs validated; the run then crashed saving the activity
  output, because CrewAI's CrewJSONEncoder cannot serialize datetime.time
  (E-S1). Fixed by using one `starts_at` datetime. Rerun: all four valid.
- M-7 closed: the four outputs are assembled in code into one Itinerary.
- R-1 Air France chosen for the third run running; Citadines again.
- R-2 Transport tried the hotel's name as a destination (miss), then
  planned only the airport: 0 of 12 activities routed. Transport runs
  before activities exist.
- R-3 Four activities repeated (Louvre, Seine cruise, Montmartre, picnic).
- R-4 Dinner cruise and Eiffel dinner both scheduled at 15:00. No check
  covers plausibility of times.
- Hand-computed expected results for this file: R1 pass, R6 pass,
  R7 fail (M-4), R3 total $5,291 against an $8,000 budget.

### Reconciliation (2026-09-25)

`python -m src.reconcile` against `findings/itinerary.json`:

| Check | Result |
| --- | --- |
| R1 flight buffers | PASS |
| R2 hotel dates | PASS |
| R3 budget | PASS: $5,291 against $8,000; $320/night against $400 |
| R4 traceability | PASS |
| R5 fixture names | PASS |
| R6 pace mix | PASS |
| R7 transport origin | FAIL: routes start 3.4 km from the Citadines (M-4) |

Expected results were computed by hand before the checks existed; the
report matched all seven. Every check was also shown failing on
purpose (activity inside the buffer, Delta's 07:15 arrival, a hotel at
0.6 km, an all-relaxed plan, a typo in `transportation.py`, a
fabricated $60 price).

Status: DES-10 and M-7 closed. DES-7 and DES-8 are detected, not
prevented: the checks report, the crew does not re-plan.