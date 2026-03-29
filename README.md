# PawPal+

**PawPal+** is a pet care planning assistant: a Python backend (`pawpal_system.py`) plus a **Streamlit** UI (`app.py`) and a **CLI** demo (`main.py`). It helps a busy owner track pets and tasks, see **today’s plan** under a **time budget**, and get **warnings** when tasks overlap or exceed available minutes.

---

## Features

The scheduler and domain model implement the following behaviors:

| Feature | What it does |
|--------|----------------|
| **Sorting by time** | `Scheduler.sort_by_time` orders pending tasks by clock time using `Task.due` or optional `time_str` (`HH:MM`), normalized to minutes from midnight so mixed inputs sort chronologically. |
| **Filtering** | `Scheduler.filter_tasks` narrows tasks by **status** (e.g. pending) and/or **pet name** for tables and views. |
| **Greedy daily plan** | `Scheduler.build_daily_plan` sorts candidates by **priority** (then duration/title), packs tasks into `Owner.available_minutes`, and returns **planner notes** explaining inclusions and skips. |
| **Budget conflict detection** | `Scheduler.detect_conflicts` compares total **pending** duration to the owner’s daily minute budget. |
| **Time overlap warnings** | `Scheduler.detect_time_overlaps` finds **overlapping intervals** (or identical start times) on a given **calendar day** and returns **warning strings only**—no exceptions. |
| **Daily / weekly recurrence** | Completing a **daily** or **weekly** task stored on a pet queues a **new pending** `Task` with the next due (`timedelta` +1 day or +1 week). |
| **Recurrence expansion** | `Task.instances_for_date` expands **daily** / **weekly** / one-off rules when building the day’s candidate list. |
| **Session-backed UI** | Streamlit keeps one `Owner` in `st.session_state` so pets and tasks persist across interactions in the same browser tab. |
| **JSON persistence** | `Owner.save_to_json` / `Owner.load_from_json` serialize pets and tasks to **`data.json`** (plain `json` module — no marshmallow required for this schema). |
| **Next available slot** | `Scheduler.next_available_slot` finds the earliest start time in a day window (default 06:00–22:00) where a **duration** fits without overlapping timed pending tasks. |
| **Priority + time ordering** | `Scheduler.sort_by_priority_then_time` and `Task.priority_emoji` / `priority_label` support UI and CLI labeling (🔴 / 🟡 / 🟢). |

**UI (Streamlit):** smart views show **pending tasks sorted by priority then time**, **overlap** and **budget** callouts, optional **time** and **repeat** when adding tasks, a **next 30‑minute opening** hint, **priority emoji** columns, and a **generated plan** with an expander to compare **priority order** vs **clock order**.

---

## Optional extensions (implemented)

| Extension | Notes |
|-----------|--------|
| **Advanced algorithm** | **Next available slot** scans merged busy intervals for the first gap that fits a requested duration (see `Scheduler.next_available_slot`). Implemented with Cursor Agent mode: add method + tests + CLI/UI surfacing. |
| **Data persistence** | `data.json` in the working directory; app **loads** on startup if present and **saves** after each run. Complex graphs use **nested dicts** (no circular JSON refs). For marshmallow/dataclasses-json, see Copilot docs — plain dicts kept the dependency list small. |
| **Priority + UI** | `sort_by_priority_then_time` complements **priority-first greedy** `build_daily_plan`. |
| **CLI formatting** | `main.py` uses **`tabulate`** for rounded tables (`pip install tabulate`). |

---

## Scenario

A busy pet owner needs help staying consistent with pet care. PawPal+ can:

- Track care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Respect constraints (time available, priority)
- Produce a daily plan and short explanations for what was included or skipped

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_streamlit_demo.png" target="_blank"><img src='/course_images/ai110/pawpal_streamlit_demo.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

*Replace `pawpal_streamlit_demo.png` with your own screenshot filename after you upload it to your course media folder.*

**Run the app locally:**

```bash
pip install -r requirements.txt
streamlit run app.py
```

**CLI demo (terminal tables + scheduler output):**

```bash
python main.py
```

---

## Architecture (UML)

- **Raster overview:** `uml_final.png` (repo root)
- **Mermaid source:** `docs/uml_final.mmd` — full diagram and notes in `docs/pawpal-class-diagram.md`
- Export a fresh PNG from the [Mermaid Live Editor](https://mermaid.live) if CLI rendering (`mmdc`) is unavailable.

---

## Testing PawPal+

```bash
python -m pytest
```

Use `python -m pytest -v` for per-test names. The suite in `tests/test_pawpal.py` covers wiring, **filter/sort**, **recurrence**, **overlap** edge cases, and **empty** graphs.

**Confidence (reliability):** ★★★★☆ **(4 / 5)** — Core logic is well covered; remaining risk is end-to-end UI automation and very large task lists.

---

## Project layout

| Path | Role |
|------|------|
| `pawpal_system.py` | Domain: `Owner`, `Pet`, `Task`, `Scheduler` |
| `app.py` | Streamlit UI |
| `main.py` | CLI demo |
| `tests/test_pawpal.py` | Pytest suite |
| `docs/` | UML Mermaid sources |

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Model the domain (UML), then implement `pawpal_system.py`.
2. Verify with `main.py` and `pytest`.
3. Connect the UI in `app.py` and refine labels and warnings for real users.
4. Update diagrams (`docs/uml_final.mmd`, `uml_final.png`) to match the code you ship.

---

## Module 2 (course) checklist

- Let a user enter owner + pet info  
- Add tasks (duration + priority; optional time + recurrence)  
- Generate a daily plan with explanations  
- Tests for the most important scheduling behaviors  
