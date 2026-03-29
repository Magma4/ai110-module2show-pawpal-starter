# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The logic layer in `pawpal_system.py` adds lightweight “intelligence” on top of the core model:

- **Sort by time** — `Scheduler.sort_by_time` orders tasks by clock time using `due` or optional `time_str` (`HH:MM`), so morning and evening work appear in a sensible order.
- **Filter** — `Scheduler.filter_tasks` narrows lists by **status** (e.g. pending) and/or **pet name** for dashboards and CLI demos.
- **Recurring follow-ups** — Completing a **daily** or **weekly** task that lives on a pet’s list queues a **new pending** task with the next due date (`timedelta` for +1 day or +1 week).
- **Time overlap warnings** — `Scheduler.detect_time_overlaps` compares intervals on a chosen day and returns **warning strings** (never crashes) when two tasks overlap or share the same start time.
- **Budget conflicts** — `Scheduler.detect_conflicts` still flags when total pending minutes exceed the owner’s available time.

Try the CLI demo with `python main.py` and the automated checks with `python -m pytest`.

## Testing PawPal+

Run the test suite from the project root:

```bash
python -m pytest
```

Use `python -m pytest -v` to print each test name as it runs.

The suite in `tests/test_pawpal.py` exercises **owner / pet / task** relationships, **filtering** by status and pet name, **chronological sorting** (`sort_by_time`), **daily and weekly recurrence** (next occurrence after `mark_complete`), **time overlap detection** (duplicate starts, partial overlap, back-to-back non-overlap, done tasks skipped), and **empty** edge cases (no pets, empty plan).

**Confidence level (reliability):** ★★★★☆ **(4 / 5)** — Domain logic and scheduler edge cases are well covered by automated tests; remaining gaps include full Streamlit interaction tests and very large task lists in performance scenarios.

## Architecture (UML)

- **Raster overview:** `uml_final.png` (repo root)
- **Mermaid source:** `docs/uml_final.mmd` and the narrative in `docs/pawpal-class-diagram.md` (export via [Mermaid Live Editor](https://mermaid.live) if you need a new PNG; CLI `mmdc` requires a working Chromium/Puppeteer setup)

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
