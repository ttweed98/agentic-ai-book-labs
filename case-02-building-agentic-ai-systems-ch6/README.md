# Case 02 — Building Agentic AI Systems, Chapter 6, corrected

A working rebuild of the coordinator / worker / delegator travel planner from
Chapter 6 of *Building Agentic AI Systems* (Anjanava Biswas and Wrick Talukdar,
Packt). It keeps the book's design and fixes the defects found by running the
chapter's notebook as published.

This is a learning build: the goal is a design other learners can follow, not a
production system. Every change from the book is tied to a numbered finding in
`findings/`.

## What changed from the book

| Finding | Problem in the book | Fix here |
| --- | --- | --- |
| DES-1 | Task placeholders `{activity_interests}` and `{activity_pace}` reached the model as literal text | Values passed in `inputs` at kickoff |
| DES-2, DES-3 | Flight records had no dates; arrival times were wrong | Full ISO timestamps; arrivals computed with `zoneinfo` |
| DES-4 | "Direct flights preferred" could not be evaluated | A `stops` field on every leg |
| DES-6 | Tools accepted parameters and ignored them | Parameters honoured, or named as ignored in the docstring |
| DES-9 | Prices had no declared currency | `currency` on every price |
| DES-10 | Nothing in the plan was ever totalled | Total computed in code from structured output |
| DES-12 | Each tool had two names (task text vs registration) | One name, used in both places |
| DES-7 | Plans included invented items and prices | Detected: every priced item is checked against the fixtures |
| DES-8 | Nothing reconciled one worker's output against another's | Detected: flight, hotel and transport cross-checks |

"Detected" means the checks report the problem; the crew does not re-plan. DES-5
(the request's contradictory hotel budget) and DES-11 (worker isolation) are
documented but not fixed.

## How it works

1. **Fixtures** (`fixtures/`) stand in for the book's four tool stubs. They
   return consistent, checkable data. Prices are illustrative, not live.
2. **Tools** (`src/tools.py`) wrap the fixtures for CrewAI. The docstrings are
   what the model reads, so each one describes what its fixture actually returns.
3. **The crew** (`src/crew.py`) is the book's Chapter 6 crew, word for word
   where possible: a coordinator writes a plan, and a manager hands the work to
   four specialist workers under CrewAI's hierarchical process.
4. **Output models** (`src/models.py`) make each task return structured data
   instead of prose. The four results are assembled in code into one
   `Itinerary` and saved to `findings/itinerary.json`.
5. **Reconciliation** (`src/reconcile.py`) runs seven plain-Python checks over
   the itinerary. No model calls.

| Check | What it catches |
| --- | --- |
| R1 flight buffers | Activities within 2 hours of landing or of the return departure |
| R2 hotel dates | Hotel nights that do not match the flights |
| R3 budget | Trip total over $8,000, or hotel over $400 a night |
| R4 traceability | Any flight, hotel, activity or route not returned by a fixture |
| R5 fixture names | An activity with no transport route under the same exact name |
| R6 pace mix | A "moderate" plan without both relaxed and active activities |
| R7 transport origin | Routes that start far from the chosen hotel |

## Results

| Run | What changed | Result |
| --- | --- | --- |
| Baseline | The book's notebook, unmodified | Eleven design findings; most of the week's activities invented, with prices |
| Middle run | Corrected fixtures and inputs at kickoff | Every priced item traced to a fixture; no total; nothing reconciled |
| Structured run | Output models, assembly and checks | Full itinerary; total $5,291; six checks pass, R7 fails |

R7's failure is real: every route in the fixture starts at Bir-Hakeim, and the
chosen hotel is 3.4 km away. The checks catch only what they check. Repeated
activities, implausible times and prose that contradicts the data all pass
them. See `findings/case-02-baseline-findings.md` for every finding,
prediction and result.

One behaviour worth knowing: under CrewAI's hierarchical process the manager
agent ran every task itself. The four workers were never used.

## Running it

Requires Python 3.10+ and an OpenAI API key. Runs are billed to your key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in this folder containing one line:

```
OPENAI_API_KEY=your-key-here
```

`.env` is in `.gitignore`; never commit it.

Run everything from this folder:

```bash
python -m src.crew        # runs the crew, saves findings/itinerary.json, prints the check report
python -m src.reconcile   # re-checks the saved itinerary; no API calls
```

CrewAI may ask whether to view execution traces during a run. Answering no, or
letting it time out, disables the prompt for future runs.

## Layout

```
fixtures/     corrected stand-ins for the book's four tool stubs
src/
  tools.py      CrewAI tool wrappers
  crew.py       the Chapter 6 crew, plus inputs at kickoff and assembly
  models.py     Pydantic output models and Itinerary
  reconcile.py  the seven checks
findings/
  case-02-baseline-findings.md   every finding, prediction and result
  chapter-06-baseline-run.ipynb  the book's notebook, run unmodified
  *.log                          the three run logs
  itinerary.json                 the structured run's output
requirements.txt  crewai==1.15.17, the version the baseline ran on
```

## Versions

CrewAI 1.15.17 (pinned so every run is comparable with the baseline), model
`gpt-4o`, Python 3.10. The book's original code is at
[PacktPublishing/Building-Agentic-AI-Systems](https://github.com/PacktPublishing/Building-Agentic-AI-Systems).
