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

- **No second task list on `Pet` yet:** The review noted that the UML shows Pet → Task from both sides. For now we keep a single link `Task → Pet` only, to avoid keeping `pet.tasks` and `task.pet` in sync manually; we can add `Pet.tasks` or a repository later if the app needs fast “all tasks for this pet” queries.

- **Scheduler left as stubs:** `build_daily_plan` and `detect_conflicts` remain unimplemented until scheduling rules are defined, so we do not pretend a policy exists yet.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
