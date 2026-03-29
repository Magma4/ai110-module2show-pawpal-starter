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

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

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
