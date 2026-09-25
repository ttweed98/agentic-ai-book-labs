# Agentic AI Book Labs

Working rebuilds of the labs from books and courses on agentic AI, built
while learning. Each case keeps the source's design, runs the original
first, records what was wrong, and then fixes it. Every change is tied to
a numbered finding.

| Case | Source | What it builds |
| --- | --- | --- |
| [Case 02](case-02-building-agentic-ai-systems-ch6/) | *Building Agentic AI Systems*, Chapter 6 (Biswas and Talukdar, Packt) | A coordinator / worker / delegator travel planner with structured outputs and reconciliation checks |

## How each case is built

1. Run the original lab unmodified and record every defect as a numbered finding.
2. Write predictions before every run, and score them after.
3. Change only what closes a finding.
4. Keep the evidence: run logs and outputs live in each case's `findings/` folder.

Case 01, an agentic network-operations assistant, lives in its own repository.