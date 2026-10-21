# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner plan daily care tasks for one or more pets. It picks the most important tasks that fit the owner's available time, orders them through the day, flags scheduling conflicts, handles recurring tasks, and explains its choices.

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

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py   # the web app
python main.py         # CLI demo
python -m pytest       # test suite
```

### Project structure

| File | Purpose |
|------|---------|
| `pawpal_system.py` | Logic layer: `Task`, `Pet`, `Owner`, `Scheduler` |
| `app.py` | Streamlit UI wired to the logic layer |
| `main.py` | CLI demo script |
| `tests/test_pawpal.py` | Automated test suite (40 tests) |
| `diagrams/uml.mmd` | UML class diagram (Mermaid) |
| `reflection.md` | Design and AI-collaboration reflection |

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

The logic layer lives in `pawpal_system.py` and is made of four classes:

- **`Task`**: one care activity (title, category, duration, priority, preferred time, frequency, completed). It validates its own data on creation and can mark itself complete or apply edits.
- **`Pet`**: a pet's profile plus its list of tasks. `add_task` tags each task with the pet's name so the plan can say who a task is for.
- **`Owner`**: the user's name, daily time budget (`available_minutes`), preferred categories, and pets. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`**: the planner. `generate_plan()` reads tasks from `Owner.get_all_tasks()` (so it covers every pet), drops completed ones, picks tasks by priority (ties go to preferred categories, then earlier time, then shorter tasks) until the time budget runs out, and returns the chosen tasks in time order. `explain_plan()` says why each task was scheduled or skipped.

`main.py` is a CLI demo that builds an owner with two pets and prints today's schedule. Run it with `python main.py`.

## 🖥️ Sample Output

Output of `python main.py`:

```
Daily plan for Mochi (Dog):
  07:30 — Morning walk (30 min) [priority: high]
  18:00 — Evening walk (30 min) [priority: medium]

Daily plan for Luna (Cat):
  08:00 — Breakfast (10 min) [priority: high]
  12:00 — Litter box (10 min) [priority: medium]
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

The 40 tests in `tests/test_pawpal.py` cover:

- **Task and pet basics:** marking tasks complete, adding tasks to a pet, rejecting invalid data (blank title, non-positive duration, unknown frequency or priority), and `edit()` re-validating its changes.
- **Sorting:** `sort_by_time()` returns tasks in chronological order, sorts by day before time, puts untimed tasks last, keeps insertion order for ties, and doesn't modify the input list.
- **Filtering:** by pet, by completion status, by both, with an unknown pet name, and with no filters.
- **Recurring tasks:** completing a daily task creates one due tomorrow, weekly tasks come back in 7 days, one-off tasks don't recur, completing a task twice doesn't create duplicates, overdue tasks recur from today, and the next occurrence stays out of today's plan but appears in tomorrow's.
- **Conflict detection:** flags duplicate times across pets and within one pet. Completed tasks, untimed tasks, and the same time on different days are ignored.
- **Plan generation:** stays within the time budget, picks higher priority first, breaks ties with the owner's preferences, includes overdue tasks, returns the plan in time order, and handles empty cases (no pets, a pet with no tasks, zero minutes available).

Output of a successful run:

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\codepath\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 40 items

tests\test_pawpal.py ........................................            [100%]

============================= 40 passed in 0.09s ==============================
```

**Confidence Level: ★★★★☆ (4/5).** Every core behavior and the edge cases I could think of are tested and pass. Writing these tests also caught two real bugs in recurrence: completing a task twice created duplicate occurrences, and overdue tasks recurred into the past. It isn't 5 stars because conflict detection only catches exact start-time matches (not overlapping durations), and the Streamlit UI is only checked by hand.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Orders tasks by due date, then preferred time, using `sorted()` with a lambda key. Tasks with no preferred time go last. `generate_plan()` uses it to show the final plan in time order. |
| Priority selection | `Scheduler.generate_plan()` | Picks pending tasks due today (or overdue) by priority. Ties go to the owner's preferred categories, then earlier time, then shorter duration. Tasks that don't fit in the remaining minutes are skipped and explained. |
| Filtering | `Scheduler.filter_tasks(pet_name=, completed=, due_on=)` | Returns tasks that match every filter given. Leave a filter out to ignore it, e.g. `filter_tasks(pet_name="Luna", completed=False)`. |
| Conflict handling | `Scheduler.detect_conflicts()` | Groups pending tasks by (due date, start time) and returns one warning string per shared slot instead of raising an error. Only exact start-time matches count, not overlapping durations. The app shows these as warnings above the schedule. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a `daily` or `weekly` task adds a fresh copy to the same pet, due `timedelta(days=1)` or `timedelta(weeks=1)` later. `once` tasks don't recur. Future occurrences stay out of today's plan. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. **Start the app** with `streamlit run app.py` and open the local URL it prints (usually http://localhost:8501).
2. **Set up the owner.** In the *Owner* section, enter your name, how many minutes you have for pet care today, and (optionally) your preferred task categories, such as `exercise`. Preferred categories win ties between tasks of equal priority.
3. **Add your pets.** In the *Pets* section, enter each pet's name, species, and age, then click **Add pet**. The pets table updates right away and shows how many tasks each pet has. Duplicate or blank names are rejected with an error message.
4. **Add care tasks.** In the *Tasks* section, choose which pet the task is for, then enter a title, duration, category, priority, frequency (`daily`, `weekly`, or `once`), and optionally a preferred time. Click **Add task**. The tasks table lists every task across all pets, sorted by date and time.
5. **Generate the schedule.** Click **Generate schedule**. PawPal+ picks the highest-priority tasks that fit in your available time and shows a *Daily plan* for each pet in time order.
6. **Check warnings and reasoning.** If two tasks share the same time slot, a yellow conflict warning appears above the plan. Expand **Why this plan?** to see why each task was scheduled or skipped (for example, "needs 20 min but only 10 min left").
7. **Try the CLI demo (optional).** Run `python main.py` to see sorting, filtering, conflict detection, and recurring tasks in the terminal.
