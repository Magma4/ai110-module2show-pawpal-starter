# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

From the PawPal+ scenario, three core actions a user should be able to perform are:

1. **Set up who they care for** — Enter and maintain basic owner and pet information so the system knows which pets belong to which household and can attach tasks to the right animal.

2. **Define and maintain care tasks** — Add, edit, or remove tasks such as feedings, walks, medications, grooming, or vet appointments, including details the scheduler needs (for example duration and priority) so routines stay accurate over time.

3. **See and act on a daily plan** — View a prioritized schedule for the day that fits available time and constraints, and understand why certain tasks were ordered or chosen so the owner can follow through confidently.

**Building blocks (objects, attributes, methods)**

| Object | Information to hold (attributes) | Actions (methods) |
|--------|-------------------------------|---------------------|
| **Owner** | Name or identifier; contact or display label; optional preferences (e.g., default walk length, quiet hours); **available time** for scheduling (e.g., minutes free today, or start/end window). | Register or update profile; set or query available time and preferences; list pets they manage (or hold references to `Pet` instances). |
| **Pet** | Name; species or type; optional age or notes; **link to owner**; optional care flags (e.g., medication needs). | Create/update profile; associate with an owner; expose identity for attaching tasks. |
| **Task** | Title or category (walk, feeding, medication, appointment, etc.); **duration** (minutes); **priority** (numeric or enum); linked **pet**; optional scheduled datetime or “due today” flag; optional recurrence rule (daily, weekly, etc.) or reference to a recurrence pattern; status (pending, done, skipped). | Create/edit/cancel; compare or expose sort keys for scheduling; mark complete; expand recurring rules into concrete instances for a given date. |
| **Scheduler** (or **DailyPlanner**) | References to **tasks** for the day, **owner** constraints (time budget), and optionally **pets** for grouping or fairness. May hold internal scratch state while planning. | **Build a daily plan**: sort or order tasks by priority and time fit; **detect conflicts** (e.g., total duration exceeds available time); drop or defer low-priority items with an explanation; output an ordered list with **reasoning** (why this order, what was skipped). |
| **Plan** or **ScheduleResult** (optional value object) | Ordered list of planned task references or copies; optional **messages** explaining tradeoffs; timestamps or slots if the UI shows a timeline. | Serialize for display; iterate tasks in order; attach human-readable rationale strings. |

Together, **Owner** and **Pet** model *who* is involved; **Task** models *what* must happen; **Scheduler** + **Plan** model *how the day is ordered* under constraints.

**a. Initial design**

The initial UML centers on four classes and two composition-style relationships: **Owner** owns many **Pets**, and each **Pet** has many **Tasks**. **Scheduler** depends on **Owner** and **Task** (it reads the owner’s time budget and a flat list of tasks) rather than owning the whole object graph.

- **`Owner`** — Holds identity (`name`), how much time is available for care today (`available_minutes`), optional `preferences` (e.g., quiet hours, defaults), and a list of `pets`. It is responsible for registering the household, updating available time, and listing pets so the UI or CLI can show who is in scope.

- **`Pet`** — Holds `name`, `species`, optional `notes`, and a back-reference `owner`. It represents the animal receiving care and is the anchor for tasks (`Task.pet`). Responsibility is profile updates and tying each pet to exactly one owner in the domain model.

- **`Task`** — Holds what to do (`title`, `category`), scheduling inputs (`duration_minutes`, `priority`), optional `due` and `recurrence`, `status`, and which `pet` it belongs to. It supports lifecycle (`mark_complete`), ordering for the planner (`sort_key`), and future expansion of recurring rules (`instances_for_date`).

- **`Scheduler`** — Stateless service class (for now) with `build_daily_plan(owner, tasks)` returning ordered tasks plus explanation strings, and `detect_conflicts` for messages when time or priorities clash. It encapsulates algorithmic behavior so entities stay thin.

**AI review of `pawpal_system.py` (Copilot-style)** — Reviewer checked whether the skeleton matches relationships and where logic might pile up later. Findings: (1) Owner ↔ Pet was not automatically wired when creating pets, so `register_pet` (or equivalent) helps keep “owns” consistent; (2) methods that return collections should return real empty lists/tuples, not implicit `None`, so callers and tests behave predictably; (3) **Scheduler** is the natural place for sorting and conflict logic—if that method grows too large, split helpers (e.g., sort vs. explain) in a later iteration; (4) recurring expansion in `Task.instances_for_date` could be expensive if called repeatedly—batching or caching could matter when that feature is implemented.

**b. Design changes**

Yes — small refinements after the review, still aligned with the same UML.

- **Owner–Pet wiring:** Added `register_pet(pet)` so assigning an owner and appending to `pets` happens in one place, matching the “Owner has Pets” relationship and avoiding a half-linked `Pet` with no owner in `pets`.

- **Concrete behavior for thin methods:** Implemented `set_available_time` and `list_pets` with straightforward field reads/writes; implemented `mark_complete` and a minimal `sort_key` so ordering has a defined key before the full scheduler exists.

- **`Pet.tasks` added later:** The implementation now keeps `tasks` on `Pet` with `add_task` / `remove_task` synchronized with `Task.pet`, so the object graph matches the UML and the UI can list tasks per pet.

- **Scheduler fully implemented:** `build_daily_plan`, `detect_conflicts`, `sort_by_time`, `filter_tasks`, and `detect_time_overlaps` were added incrementally after the skeleton phase, with tests and CLI verification before the Streamlit polish.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers **(1) owner time budget** (`available_minutes`), **(2) task priority and duration** (via `sort_key` for greedy packing), **(3) calendar-day relevance** (`instances_for_date`, `plan_date`), and **(4) optional clock times** for sorting and overlap checks (`due`, `time_str`). **Preferences** on `Owner` are modeled but not heavily weighted in code yet.

**Priority order:** Fitting the **daily minute budget** while preferring **higher priority** tasks first was chosen as the main tradeoff for `build_daily_plan` because it matches how an overwhelmed owner thinks (“do the important stuff if time runs out”). **Clock-based ordering** is surfaced separately (`sort_by_time`) so the UI can show “when things ideally happen” without changing the greedy policy.

**b. Tradeoffs**

**Tradeoff: pairwise overlap scan vs. a single sweep**

`detect_time_overlaps` compares every pair of tasks that have a clock time on the plan day using `itertools.combinations` (O(n²) in the number of timed tasks). A more advanced approach is to sort intervals by start time and sweep once (O(n log n)), which scales better with many tasks.

**Why this is reasonable here:** A typical owner has a small number of timed tasks per day, so clarity and a few lines of code matter more than asymptotic savings. The method only **returns warning strings** and never raises, so the UI stays safe even if the list grows. The check also treats **interval overlap** (shared minutes), not only identical start times—but tasks **without** a `due` or `time_str` for that day are skipped, so “floating” tasks never get a false overlap.

**Readability vs. “Pythonic” compression:** Nested `for i/j` loops could be replaced by `combinations` alone; keeping the overlap condition `(s1 < e2 and s2 < e1) or (s1 == s2)` explicit preserves the half-open interval rule and the “same instant” edge case for zero-length blocks without hiding logic in a one-liner.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI (including VS Code **Copilot** Chat and inline prompts) to **brainstorm UML**, **scaffold dataclasses and method stubs**, **draft pytest cases**, **suggest Mermaid syntax**, and **review** overlap and recurrence edge cases. The most helpful prompts were **file-scoped** (`#file:pawpal_system.py`) and **behavior-specific** (“what edge cases for overlap on the same day?”), because they grounded suggestions in real code instead of generic Python trivia.

**b. Judgment and verification — VS Code Copilot**

**Which Copilot features were most effective for the scheduler?**

- **Chat with codebase context** — Quick checks on where to put overlap logic (on `Scheduler` vs `Task`) and how to return **warnings** instead of raising.
- **Inline / selection edits** — Small refactors (e.g., `itertools.combinations`, `timedelta` for next due) with immediate diff review.
- **Generate tests** — Starting points for `pytest` cases, which I then tightened with concrete dates and assertions.

**One AI suggestion I rejected or modified**

Early on, Copilot sometimes suggested **duplicating** a full `tasks` list on both `Pet` and `Owner` without a single source of truth. I **rejected** keeping only free-floating tasks and instead standardized on **`Pet.add_task`** + **`Owner.all_tasks()`** so relationships stay consistent. I verified by **running tests** and **stepping through `main.py`** after each change.

**How separate chat sessions helped**

Using **different chats for design vs implementation vs testing** reduced context mixing: one thread kept UML and naming stable, another focused on **pytest** failures, and another on **Streamlit** session state. That made it easier to **paste errors** and **accept or reject** suggestions without losing the architectural thread.

**Lead architect with powerful AI**

The model is fast at boilerplate and alternatives, but **I** own **constraints, public APIs, and tradeoffs** (e.g., greedy priority vs chronological display). Being the lead architect means **directing** Copilot with precise files and goals, **verifying** with tests and demos, and **rejecting** clever code that obscures behavior—speed without judgment would have produced a larger, harder-to-trust scheduler.

---

## 4. Testing and Verification

**a. What you tested**

I tested **owner/pet/task wiring**, **`filter_tasks`**, **`sort_by_time`** (including mixed `due` and `time_str`), **daily/weekly recurrence** after `mark_complete`, **time overlaps** (duplicate start, partial overlap, adjacent non-overlap, done tasks ignored), **empty owner/plan**, and **`detect_conflicts`** indirectly through behavior. These matter because they guard the **behaviors users see** in both **CLI** and **Streamlit**, and because scheduler bugs are subtle (off-by-one days, half-open intervals).

**b. Confidence**

I am **reasonably confident** (about **4/5**) that the scheduler matches intent for small household task counts. If I had more time, I would add **property-based tests** for overlap, **Streamlit integration** smoke tests, and scenarios with **many pets** and **time zones** if `due` ever stores non-local datetimes.

---

## 5. Reflection

**a. What went well**

The **separation** of `pawpal_system.py` from UI made it possible to **prove** behavior in **pytest** and **`main.py`** before polishing Streamlit. The **warning-only** conflict API kept the app resilient.

**b. What you would improve**

I would add **explicit time slots** (start/end) for each planned task, **edit/remove task** flows in the UI, and **persistence** (file or DB) so session loss on refresh does not drop data.

**c. Key takeaway**

Designing with AI works best when I treat the model as a **strong junior implementer**: I supply **architecture, invariants, and tests**; AI accelerates drafting, but **I** decide what “correct” means and prove it before shipping.
